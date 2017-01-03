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


if __name__ == '__main__':

    random.seed(0)
    conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161226')
    w_dir = 'output/'
    file_text = 'text.in'
    file_features = 'features.in'
    cached_model_result = w_dir + 'test3_cached_model.pickle'
    cached_feature_result = w_dir + 'test3_cached_feature.pickle'
    final_result = w_dir + 'test3_result.pickle'

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
        # 使用Classifier对这些feedid进行标签补全，结果以dict的形式存入extends_dict
        print("Fetch all from features_t...")
        cursor = conn.cursor()
        cursor.execute("select feedid,streamid from features_t")
        tuple_list = [(feedid, streamid) for feedid, streamid in cursor.fetchall()]
        raw_dict = fetch_raw_datapoints(conn, tuple_list)
        feature_dict = sc.compute_feature(raw_dict)
        extends_dict = {fs_tuple: sc.pred(feature)[0] for fs_tuple, feature in feature_dict.items()}
        pickle.dump(extends_dict, open(cached_feature_result, 'wb'))

    for short_rate in range(np.arange(0.1, 1, 0.1)):
        # TODO 截断原始doc作为新的数据集
        pass

