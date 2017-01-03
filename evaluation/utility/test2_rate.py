"""
在不同补全率下，验证查询结果
"""

import os
import random
import pickle
import mysql.connector as c
import numpy as np
import pandas as pd

from classify.SensorClassifier import SensorClassifier, fetch_raw_datapoints
from lib.BM25 import BM25
from lib.DMR import DMR
from utils.DMRHelper import *


if __name__ == '__main__':

    random.seed(0)
    conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161226')
    w_dir = 'output/'
    file_text = 'text.in'
    file_features = 'features.in'
    cached_model_result = w_dir + 'test2_cached_model.pickle'
    cached_feature_result = w_dir + 'test2_cached_feature.pickle'
    final_result = w_dir + 'test2_result.pickle'

    with codecs.open(settings.DEFINITIONS_ROOT + '/resource/stopwords.txt', 'r') as f:
        stoplist = set(f.read().split())

    if os.path.exists(cached_model_result):
        sc = pickle.load(open(cached_model_result, 'rb'))
    else:
        # 训练分类器
        sc = SensorClassifier()
        print("Train classifier for label generation...")
        label_df = pd.read_sql("select * from manual_label_t where label!=''", conn)
        train_label_dict = {(val['feed_id'], val['stream_id']): val['label'] for _, val in label_df.iterrows()}
        train_raw_dict = fetch_raw_datapoints(conn, list(train_label_dict.keys()))
        sc.train_model(train_label_dict, train_raw_dict)
        pickle.dump(sc, open(cached_model_result, 'wb'))

    if os.path.exists(cached_feature_result):
        extends_dict = pickle.load(open(cached_feature_result, 'rb'))
    else:
        # 使用Classifier对这些feedid进行标签补全，结果以dict的形式存入extends_dictz
        print("Fetch all from features_t...")
        cursor = conn.cursor()
        cursor.execute("select feedid,streamid from features_t")
        tuple_list = [(feedid, streamid) for feedid, streamid in cursor.fetchall()]
        raw_dict = fetch_raw_datapoints(conn, tuple_list)
        feature_dict = sc.compute_feature(raw_dict)
        extends_dict = {fs_tuple: sc.pred(feature)[0] for fs_tuple, feature in feature_dict.items()}
        pickle.dump(extends_dict, open(cached_feature_result, 'wb'))

    # 使用不同的补全率extends_rate，测试时只使用extends_dict中对应的tuple
    rate_result = []
    for rate in list(np.arange(0.1, 1.0, 0.1)):
        tmp_dict = {}
        tmp_query_list = []
        cnt = 0
        for k, v in extends_dict.items():
            tmp_dict[k] = v
            tmp_query_list.append(k[0])
            cnt += 1
            if cnt > len(extends_dict)*rate:
                break
        print("rate=" + str(rate))
        f_list, regular_set = fetch_and_save_feature_enhanced(w_dir + file_text, w_dir + file_features, conn, tmp_dict)

        # 测试不同补全效果下的命中率
        dmr = DMR(file_text, file_features, topic_num=20, work_dir=w_dir)
        bm25 = BM25(file_text, work_dir=w_dir)
        cursor = conn.cursor()
        cursor.execute("select id, tags from feed_t where tags is not null")

        d_result = []
        b_result = []
        f_set = set(f_list)
        tmp_query_set = set(tmp_query_list)
        cnt = 0
        for fid, tags in cursor.fetchall():
            if fid not in f_set or fid not in tmp_query_set:
                continue
            query_list = [w for w in trim_str(tags, stoplist) if w in regular_set]
            if len(query_list) == 0:
                continue
            dscore = dmr.optimized_score(query_list, bm25)
            bscore = bm25.bm25_score(query_list)

            # 检查fid在rank的位置
            print(fid)
            f_idx = f_list.index(fid)
            d_rank = len([score for score in dscore if score > dscore[f_idx]])
            b_rank = len([score for score in bscore if score > bscore[f_idx]])
            d_result.append(d_rank)
            b_result.append(b_rank)
        rate_result.append((d_result,b_result))
    pickle.dump(rate_result, open(final_result, 'wb'))
