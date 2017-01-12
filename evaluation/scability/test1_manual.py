"""
使用label_mapping_t表中指定的三种粒度的描述对结果进行补全
以最终查询rank作为标准
"""
import random
import pickle
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
    cached_model_result = w_dir + 'test2_cached_model.pickle'
    cached_feature_result = w_dir + 'test2_cached_feature.pickle'
    final_result = w_dir + 'test1_result.pickle'

    with codecs.open(settings.DEFINITIONS_ROOT + '/resource/stopwords.txt', 'r') as f:
        stoplist = set(f.read().split())

    cursor = conn.cursor()
    cursor.execute("select origin_label, level1_label, level2_label from label_mapping_t")
    label_trans_dict = {olabel: [olabel, level1, level2] for olabel, level1, level2 in cursor.fetchall()}

    rank_result = []
    for level in range(len(next(iter(label_trans_dict.values())))):

        # 对于每种标签方式，对应训练分类器
        sc = SensorClassifier()
        print("Train classifier for label generation...")
        label_df = pd.read_sql("select * from manual_label_t where label!=''", conn)

        train_label_dict = {(val['feed_id'], val['stream_id']): label_trans_dict[val['label']][level]
                            for _, val in label_df.iterrows()}
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

        # 生成索引
        print("fetch files ...")
        fid_list, regular_set = fetch_and_save_feature(
            w_dir + file_text, w_dir + file_features, conn, extends_dict, selector=3)
        print("build index ...")
        dmr = DMR(file_text, file_features, topic_num=20, work_dir=w_dir)
        bm25 = BM25(file_text, work_dir=w_dir)

        # 查询测试
        cursor = conn.cursor()
        cursor.execute("select id, tags from feed_t where tags is not null")
        d_result = []
        b_result = []

        tmp_query_list = []
        for fs_tuple, label in extends_dict.items():
            tmp_query_list.append(fs_tuple[0])
        tmp_query_set = set(tmp_query_list)

        f_set = set(fid_list)
        for fid, tags in cursor.fetchall():
            if fid not in f_set or fid not in tmp_query_set:
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
        rank_result.append((d_result, b_result))

    pickle.dump(rank_result, open(final_result, 'wb'))
