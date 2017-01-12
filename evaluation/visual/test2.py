"""
空间属性可视化

空间位置已经转换成某个特定位置的类别
使用雷达图，挑选几个典型的主题和典型的位置类别进行展示
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
    random.seed(0)
    conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161226')
    w_dir = "output/"
    file_id = 'id.in'
    file_text = 'text.in'
    file_features = 'features.in'
    cached_result = w_dir + 'test2_cached.pickle'
    rank_result = w_dir + 'test2_result.pickle'
    topic_num = 10

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
        location_feature = [int(line.split('_')[2].split(' ')[0]) for line in f]
    location_mapping = {}
    for idx, _ in enumerate(fid_list):
        doc_topic_vec = dmr.get_doc_topic(idx)
        if location_feature[idx] not in location_mapping:
            location_mapping[location_feature[idx]] = doc_topic_vec
        else:
            location_mapping[location_feature[idx]] += doc_topic_vec

    for time_key, topic_vec in collections.OrderedDict(sorted(location_mapping.items())).items():
        location_mapping[time_key] = topic_vec / np.sum(topic_vec)
        print(location_mapping[time_key])

    pickle.dump(location_mapping, open(rank_result, 'wb'))

