"""
测试短文本对结果的影响
"""
import os
import random
import pickle
import numpy as np
import mysql.connector as c
import pandas as pd

from classify.SensorClassifier import SensorClassifier, fetch_raw_datapoints
from lib.BM25 import BM25
from lib.DMR import DMR
from utils.DMRHelper import *


def query_test(connection, flist, rset):
    cursor = conn.cursor()
    cursor.execute("select id, tags from feed_t where tags is not null")
    d_result = []
    b_result = []
    f_set = set(flist)
    cnt = 0
    for fid, tags in cursor.fetchall():
        if fid not in f_set:
            continue
        cnt += 1
        if cnt % 10 != 0:
            continue
        query_list = [w for w in trim_str(tags, stoplist) if w in rset]
        if len(query_list) == 0:
            continue
        dscore = dmr.optimized_score(query_list, bm25)
        bscore = bm25.bm25_score(query_list)
        # 检查fid在rank的位置
        f_idx = flist.index(fid)
        d_rank = len([score for score in dscore if score > dscore[f_idx]])
        b_rank = len([score for score in bscore if score > bscore[f_idx]])
        d_result.append(d_rank)
        b_result.append(b_rank)
    return d_result, b_result


if __name__ == '__main__':

    random.seed(0)
    conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161226')
    w_dir = 'output/'
    file_text = 'text.in'
    file_features = 'features.in'
    final_result = w_dir + 'test3_result.pickle'

    with codecs.open(settings.DEFINITIONS_ROOT + '/resource/stopwords.txt', 'r') as f:
        stoplist = set(f.read().split())

    result_list = []

    print("fetch files ...")
    fid_list, regular_set = fetch_and_save_feature(
        w_dir + file_text, w_dir + file_features, conn, extends_dict=None, selector=3)
    print("build index ...")
    dmr = DMR(file_text, file_features, topic_num=20, work_dir=w_dir)
    bm25 = BM25(file_text, work_dir=w_dir)
    result_list.append(query_test(conn, fid_list, regular_set))  # 首先验证文档完整时查询的准确率

    for short_rate in np.arange(0.4, 1.2, 0.2):

        fid_list, regular_set = fetch_and_save_feature(
            w_dir + file_text, w_dir + file_features, conn, extends_dict=None, selector=3)  # 恢复完整文档

        print("Reform document ... ")
        regular_set = set()  # 截断可能导致regular_set的变化
        min_num_of_words = 2
        new_tmp_file = w_dir + 'tmp.in'
        with codecs.open(new_tmp_file, 'w') as tf:
            with codecs.open(w_dir + file_text, 'r') as f:
                for line in f.readlines():
                    words = line.split()
                    newline = words[:max(int(len(words) * short_rate), min_num_of_words)]
                    regular_set |= set(newline)
                    tf.write(' '.join(newline) + '\n')
        os.remove(w_dir + file_text)
        os.rename(new_tmp_file, w_dir + file_text)

        print("build index with reformed input ...")
        dmr = DMR(file_text, file_features, topic_num=20, work_dir=w_dir)
        bm25 = BM25(file_text, work_dir=w_dir)
        result_list.append(query_test(conn, fid_list, regular_set))

    pickle.dump(result_list, open(final_result, 'wb'))
