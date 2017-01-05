"""
测试metadata的影响
生成三组不同的mallet.instance
分别对应是否使用时间和地点属性
"""
import os
import pickle
import random
import mysql.connector as c

from lib.BM25 import BM25
from lib.DMR import DMR
from utils.DMRHelper import *

if __name__ == '__main__':
    random.seed(0)
    conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161226')
    w_dir = "output/"
    file_text = 'text.in'
    file_features = 'features.in'
    rank_result = w_dir + 'test4_result.pickle'

    if not os.path.exists(w_dir):
        os.makedirs(w_dir)
    with codecs.open(settings.DEFINITIONS_ROOT + '/resource/stopwords.txt', 'r') as f:
        stoplist = set(f.read().split())

    selector_list = [0, 1, 2, 3]
    result_list = []
    for sel in selector_list:

        print("fetch files ...")
        fid_list, regular_set = fetch_and_save_feature(
            w_dir + file_text, w_dir + file_features, conn, extends_dict=None, selector=sel)
        print("build index ...")
        dmr = DMR(file_text, file_features, topic_num=20, work_dir=w_dir)
        bm25 = BM25(file_text, work_dir=w_dir)

        cursor = conn.cursor()
        cursor.execute("select id, tags from feed_t where tags is not null")
        d_result = []
        b_result = []
        f_set = set(fid_list)
        cnt = 0
        for fid, tags in cursor.fetchall():
            if fid not in f_set:
                continue
            cnt += 1
            if cnt % 10 != 0:
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

            # print(str(d_rank) + ',' + str(b_rank))
            d_result.append(d_rank)
            b_result.append(b_rank)
        result_list.append((d_result, b_result))

    pickle.dump(result_list, open(rank_result, 'wb'))
