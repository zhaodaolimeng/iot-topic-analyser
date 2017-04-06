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
import collections

from lib.BM25 import BM25
from lib.DMR import DMR
from utils.DMRHelper import *

if __name__ == '__main__':

    # 重新训练
    random.seed(0)
    conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161226')
    w_dir = "output/"
    file_id = 'id.in'
    file_text = 'text.in'
    file_features = 'features.in'

    cached_result = w_dir + 'test1_cached.pickle'
    rank_result = w_dir + 'test1_result.pickle'
    topic_num = 20

    if not os.path.exists(w_dir):
        os.makedirs(w_dir)
    with codecs.open(settings.DEFINITIONS_ROOT + '/resource/stopwords.txt', 'r') as f:
        stoplist = set(f.read().split())

    if os.path.exists(cached_result):
        fid_list, regular_set, dmr, bm25 = pickle.load(open(cached_result, 'rb'))
    else:
        print("fetch files ...")
        # fid_list的顺序和feature.in和text.in是对应的
        fid_list, regular_set = fetch_and_save_feature(
            w_dir + file_text, w_dir + file_features, conn, extends_dict=None, selector=3, id_file=w_dir + file_id)
        print("build index ...")
        dmr = DMR(file_text, file_features, topic_num=topic_num, work_dir=w_dir)
        bm25 = BM25(file_text, work_dir=w_dir)
        pickle.dump((fid_list, regular_set, dmr, bm25), open(cached_result, 'wb'))

    # 计算每个文档的主题，按时间统计不同主题的占比
    # time_mapping[time_feature[docid]] = doc_topic_vec
    with codecs.open(w_dir + file_features, 'r') as f:
        time_feature = [int(line.split('=')[-1][:-1]) for line in f]
    time_mapping = {}
    for idx, _ in enumerate(fid_list):
        doc_topic_vec = dmr.get_doc_topic(idx)
        if time_feature[idx] not in time_mapping:
            time_mapping[time_feature[idx]] = doc_topic_vec
        else:
            time_mapping[time_feature[idx]] += doc_topic_vec

    for time_key, topic_vec in collections.OrderedDict(sorted(time_mapping.items())).items():
        time_mapping[time_key] = topic_vec / np.sum(topic_vec)
        print(time_mapping[time_key])

    pickle.dump(time_mapping, open(rank_result, 'wb'))
