"""
使用不完整描述标签进行描述信息进行补全
为了保证对比因素单一，未命中的标签标记为unknown
"""
import os
import random
import pickle
import numpy as np
import pandas as pd
import mysql.connector as c

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
    cached_feature_result = w_dir + 'test2_cached_feature.pickle'
    final_result = w_dir + 'test2_result.pickle'

    with codecs.open(settings.DEFINITIONS_ROOT + '/resource/stopwords.txt', 'r') as f:
        stoplist = set(f.read().split())

    if os.path.exists(cached_feature_result):
        extends_dict = pickle.load(open(cached_feature_result, 'rb'))
    else:
        # 训练分类器
        sc = SensorClassifier()
        print("Train classifier for label generation...")
        label_df = pd.read_sql("select * from manual_label_t where label!=''", conn)
        train_label_dict = {(val['feed_id'], val['stream_id']): val['label'] for _, val in label_df.iterrows()}
        train_raw_dict = fetch_raw_datapoints(conn, list(train_label_dict.keys()))
        sc.train_model(train_label_dict, train_raw_dict)

        # 使用Classifier对这些feedid进行标签补全，结果以dict的形式存入extends_dict
        print("Fetch all from features_t...")
        cursor = conn.cursor()
        cursor.execute("select feedid,streamid from features_t")
        tuple_list = [(feedid, streamid) for feedid, streamid in cursor.fetchall()]
        raw_dict = fetch_raw_datapoints(conn, tuple_list)
        feature_dict = sc.compute_feature(raw_dict)
        extends_dict = {fs_tuple: sc.pred(feature)[0] for fs_tuple, feature in feature_dict.items()}
        pickle.dump(extends_dict, open(cached_feature_result, 'wb'))

    result_complement = []
    for label_completeness in np.arange(0.2, 1.2, 0.2):
        print('For rate = ' + str(label_completeness))
        # 从extends_dict中随机选取一部分数据，其他的标签均使用unknown表示
        subset_extends_dict = {}
        total_ext_length = len(extends_dict)
        subset_length = int(label_completeness * total_ext_length)
        choice_set = set(np.random.choice(total_ext_length, subset_length, replace=False))
        cnt = 0
        for k, v in extends_dict.items():
            if cnt in choice_set:
                subset_extends_dict[k] = v
            else:
                subset_extends_dict[k] = 'unknown'
            cnt += 1

        print("Compute the rate for complement values...")
        f_list, regular_set = fetch_and_save_feature(
            w_dir + file_text, w_dir + file_features, conn, extends_dict=extends_dict, selector=None)
        bm25 = BM25(file_text, work_dir=w_dir)
        dmr = DMR(file_text, file_features, topic_num=20, work_dir=w_dir)

        # 计算rank
        cursor = conn.cursor()
        cursor.execute("select id, tags from feed_t where tags is not null")
        d_result = []
        f_set = set(f_list)
        cnt = 0
        for fid, tags in cursor.fetchall():
            if fid not in f_set:
                continue
            query_list = [w for w in trim_str(tags, stoplist) if w in regular_set]
            if len(query_list) == 0:
                continue
            cnt += 1
            if cnt % 10 != 0:
                continue
            dscore = dmr.optimized_score(query_list, bm25)
            # 检查fid在rank的位置
            print(fid)
            f_idx = f_list.index(fid)
            d_rank = len([score for score in dscore if score > dscore[f_idx]])
            d_result.append(d_rank)
        result_complement.append(d_result)

    pickle.dump(result_complement, open(final_result, 'wb'))
