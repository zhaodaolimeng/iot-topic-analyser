# -*- coding: utf-8 -*-
"""
数据无缺失时DMR和TFIDF的Rank对比
每次输入为所有的数据集，以feed_t.tags作为输入
"""
from lib.BM25 import BM25
from lib.DMR import DMR
from evaluation.FileHelper import *

import random
import pickle
import os
import mysql.connector as c

if __name__ == '__main__':
    random.seed(0)
    conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161226')
    w_dir = "output_test1/"
    file_text = 'text.in'
    file_features = 'features.in'
    cached_result = 'test1_cached.pickle'
    rank_result = 'test1_result.pickle'

    if not os.path.exists(w_dir):
        os.makedirs(w_dir)
    with codecs.open(settings.DEFINITIONS_ROOT + '/resource/stopwords.txt', 'r') as f:
        stoplist = set(f.read().split())

    if os.path.exists(cached_result):
        fid_list, regular_set, dmr, bm25 = pickle.load(open(cached_result, 'rb'))
    else:
        print("fetch files ...")
        fid_list, regular_set = fetch_and_save_feature(w_dir + file_text, w_dir + file_features, conn)
        print("build index ...")
        dmr = DMR(file_text, file_features, topic_num=20, work_dir=w_dir)
        bm25 = BM25(file_text, work_dir=w_dir)
        pickle.dump((fid_list, regular_set, dmr, bm25), open(cached_result, 'wb'))

    cursor = conn.cursor()
    cursor.execute("select id, tags from feed_t where title is not null")
    d_result = []
    b_result = []
    f_set = set(fid_list)
    for fid, tags in cursor.fetchall():
        if fid not in f_set:
            continue
        query_list = [w for w in trim_str(tags, stoplist) if w in regular_set]
        if len(query_list) == 0:
            continue
        dscore = dmr.optimized_score(query_list, bm25)
        bscore = bm25.bm25_score(query_list)
        # 检查fid在rank的位置
        f_idx = fid_list.index(fid)
        d_rank = len([score for score in dscore if score > dscore[f_idx]])
        b_rank = len([score for score in bscore if score > bscore[f_idx]])
        print(str(d_rank) + ',' + str(b_rank))
        d_result.append(d_rank)
        b_result.append(b_rank)

    pickle.dump((d_result, b_result), open(rank_result, 'wb'))
