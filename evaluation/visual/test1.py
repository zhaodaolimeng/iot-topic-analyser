"""
时间属性可视化

Created on Tue Jun 28 22:58:00 2016

@author: limeng

时间-主题曲线
x轴为时间线，y轴为指定主题在文档中出现的概率
计算方式：统计同一个时间标签的所有文档，计算他们属于不同主题的混合概率
"""

import os
import pickle
import random
import mysql.connector as c
import numpy as np
import matplotlib.pyplot as plt

from lib.BM25 import BM25
from lib.DMR import DMR
from utils.DMRHelper import *


if __name__ == '__main__':

    # 重新训练
    random.seed(0)
    conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161226')
    w_dir = "output/"
    file_text = 'text.in'
    file_features = 'features.in'
    cached_result = w_dir + 'test1_cached.pickle'
    rank_result = w_dir + 'test1_result.pickle'

    if not os.path.exists(w_dir):
        os.makedirs(w_dir)
    with codecs.open(settings.DEFINITIONS_ROOT + '/resource/stopwords.txt', 'r') as f:
        stoplist = set(f.read().split())

    if os.path.exists(cached_result):
        fid_list, regular_set, dmr, bm25 = pickle.load(open(cached_result, 'rb'))
    else:
        print("fetch files ...")
        fid_list, regular_set = fetch_and_save_feature(
            w_dir + file_text, w_dir + file_features, conn, extends_dict=None, selector=3)
        print("build index ...")
        dmr = DMR(file_text, file_features, topic_num=20, work_dir=w_dir)
        bm25 = BM25(file_text, work_dir=w_dir)
        pickle.dump((fid_list, regular_set, dmr, bm25), open(cached_result, 'wb'))

    TOPIC_K = 30

    # 读出每个词对应的主题内容
    # {doc: {word : topic}}
    word_topic_mapping = dict()
    with open('output/dmr.state', 'r') as f:
        next(f)
        for line in f:
            record = line.split()
            idx = record[0]
            if idx not in word_topic_mapping:
                word_topic_mapping[idx] = dict()
            word_topic_mapping[idx][record[-2]] = int(record[-1])

    print('Extract topic for each word ...')

    # 统计特定主题在不同时间段出现的频率
    # {timestamp : {topic : cnt}}
    timestamp_topic_mapping = dict()
    with open('output/features.txt', 'r') as f:
        for idx, line in enumerate(f):
            # lbloc_28_35 lbtime=2
            timestamp = int(line.split()[1].split('=')[-1])
            if timestamp not in timestamp_topic_mapping:
                topic_list = np.zeros(TOPIC_K)
            # 对于每个文档，计算主题分布，并累加到对应的位置上
            parr = np.zeros(TOPIC_K)
            if str(idx) not in word_topic_mapping:
                continue
            for word, word_topic in word_topic_mapping[str(idx)].items():
                parr[word_topic] += 1
            parr = parr / np.sum(parr)
            topic_list = topic_list + parr
            timestamp_topic_mapping[timestamp] = topic_list

    print('Topic for each position ...')

    # 归一化
    topic_list = [[0 for i in range(len(timestamp_topic_mapping))] for j in range(TOPIC_K)]
    time_list = []
    tmp_map = dict()
    time_cnt = 0
    for time, topic_arr in timestamp_topic_mapping.items():
        tmp_map[time] = topic_arr / np.sum(topic_arr)
        time_list.append(time)
        upper_line = 0
        for idx in range(TOPIC_K):
            upper_line += tmp_map[time][idx]
            topic_list[idx][time_cnt] = upper_line
        time_cnt += 1

    timestamp_topic_mapping = tmp_map
    print('Normalization ...')

    fig = plt.figure()
    ax = fig.add_subplot(111)

    color_list = ['#F0F8FF', '#FAEBD7', '#00FFFF', '#7FFFD4',
                  '#F0FFFF', '#F5F5DC', '#FFE4C4', '#0000FF',
                  '#F0F8FF', '#FAEBD7', '#00FFFF', '#7FFFD4',
                  '#F0FFFF', '#F5F5DC', '#FFE4C4', '#0000FF',
                  '#F0F8FF', '#FAEBD7', '#00FFFF', '#7FFFD4',
                  '#F0FFFF', '#F5F5DC', '#FFE4C4', '#0000FF',
                  '#F0F8FF', '#FAEBD7', '#00FFFF', '#7FFFD4',
                  '#F0FFFF', '#F5F5DC', '#FFE4C4', '#0000FF',
                  '#F0F8FF', '#FAEBD7', '#00FFFF', '#7FFFD4',
                  '#F0FFFF', '#F5F5DC', '#FFE4C4', '#0000FF',
                  '#F0F8FF', '#FAEBD7', '#00FFFF', '#7FFFD4',
                  '#F0FFFF', '#F5F5DC', '#FFE4C4', '#0000FF']

    ax.fill_between(time_list, 0, topic_list[0], facecolor=color_list[0], alpha=.7)
    for idx in range(TOPIC_K - 1):
        ax.fill_between(time_list,
                        topic_list[idx],
                        topic_list[idx + 1],
                        facecolor=color_list[idx + 1], alpha=.7)

    plt.show()

