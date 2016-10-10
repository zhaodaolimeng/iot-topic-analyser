# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 11:05:12 2016

@author: limeng
"""

'''
补充文本描述后对结果的影响
================
预期x轴为补充文本的比例，y轴为精度；
实验组为原始文本描述+生成文本描述，呈现生成文本的比例；
对照组为原始文本描述+空描述，呈现空描述比例
'''

from sklearn.ensemble import RandomForestClassifier
import DMR_wrapper as dmr
import sys
import os
import time
import pickle
import codecs
import gzip
import numpy as np
import subprocess as sp

sys.path.insert(0, '../tfidf/')
sys.path.insert(0, '../classify/')
import BM25 as bm25
import step1_feature2 as feature_extraction
import step2_rf as classification
import mysql.connector as db


FEATURE_FILE = '../classify/step1_feature2.pickle'
TAGS_MAP_FILE = 'step2_generate_data.pickle'
SRC_DIR = 'output/'
SRC_ID = 'feedid.txt'
SRC_TEXT = 'texts.txt'
SRC_FEATURE = 'features.txt'

TMP_DIR = 'output_complete/'
ID = 'feedid.txt'
TEXT = 'texts.txt'
FEATURE = 'features.txt'
MALLET_INPUT = 'instance.mallet'
DMR_STATE_GZIP = 'dmr.state.gz'
DMR_STATE = 'dmr.state'
DMR_TOPIC = 'dmr-topics.txt'

conn = db.connect(user='root', password='ictwsn', 
                   host='127.0.0.1', database='curiosity_v3')

'''
对比不同修复率下的查询精度
========================
在执行该步骤前，需要执行classify/step1_feature2.py生成特征
从datastream_labeled_t中读取特征
'''
def build_corpus(ratio):
    
    print('Read features...')
    if not os.path.isfile(FEATURE_FILE):
        feed_dict = feature_extraction.get_feeddict()
        feature_extraction.save_result(feed_dict)
    
    xively_dict = pickle.load(open(FEATURE_FILE,'rb'))
    features, concat_labels = xively_dict['X'], xively_dict['labels']
    
    # 使用有标签的数据进行训练
    X_train, y_train, _, _, _ = classification.load_data(features, concat_labels)
    rfc = RandomForestClassifier(n_estimators=100)
    rfc.fit(X_train, y_train)
    
    # 该步骤读出信息的条目数与输入的条目数不匹配
    X_test, y_test, label_type, feedid_list, datastreamid_list = \
        classification.load_data(features, concat_labels, TRAINNING=False)

    # 统计datastream_labeled_t中参与补全的文档中的feedid
    print('Predict labels...')
    preds = rfc.predict(X_test)
    feed_label_dict = dict()
    for idx, feedid in enumerate(feedid_list):
        feedid = str(feedid)
        if feedid not in feed_label_dict:
            feed_label_dict[feedid] = ' ' + preds[idx]
        else:
            feed_label_dict[feedid] += ' ' + preds[idx]
    
    return feed_label_dict

    
def save_as_files(feed_label_dict):
    # 读入原始的texts.txt文件，该文件使用description+tags拼接
    with codecs.open(SRC_DIR + SRC_ID, 'r') as f:
        id_list = f.read().splitlines()
    with codecs.open(SRC_DIR + SRC_TEXT, 'r') as f:
        text_list = f.read().splitlines()
    with codecs.open(SRC_DIR + SRC_FEATURE, 'r') as f:
        dmr_feature_list = f.read().splitlines()
    
    # 对于每个补全生成的text，都需要重新计算用于dmr输入的feature，即经纬度、时间信息
    # 直接从数据库中读取对应的时间和位置信息
    corpus_list = []
    count = 0
    
    adhoc_feature_dict = dict()
    cursor = conn.cursor()
    cursor.execute("""
        select id, created, lat, lng from feed_t 
        where length(lat)>0 and length(lng)>0 and length(created)>0
    """, conn)
    for (feedid, created, lat, lng) in cursor.fetchall():
        lat = int((90+float(lat)) / 10)
        lng = int((180+float(lng)) / 10)
        epoch = int(time.mktime(time.strptime('2007.01.01', '%Y.%m.%d')))
        create_time = int(created.timestamp() - epoch)
        lb_time = str(int(create_time / (3600*24*30*6)))
        feature_str = 'lat=' + str(lat) + ' lng=' + str(lng) + ' lbtime=' + lb_time+'\n'
        adhoc_feature_dict[feedid] = feature_str
    
    for (feedid, text) in feed_label_dict.items():
        count += 1
        if feedid in adhoc_feature_dict:
            corpus_list.append({'i': feedid, 't': text, 'f': adhoc_feature_dict[feedid]})
        if count >= int(len(id_list) * ratio):
            break

    for i in range(len(id_list)):
        corpus_list.append({'i': id_list[i], 't': text_list[i], 'f':dmr_feature_list[i]})
    
    # 将生成的文本写入到临时文件夹output_complete
    with codecs.open(TMP_DIR + ID, 'w', 'utf-8') as fi:
        with codecs.open(TMP_DIR + TEXT, 'w', 'utf-8') as ft:
            with codecs.open(TMP_DIR + FEATURE, 'w', 'utf-8') as ff:
                for i in range(len(corpus_list)):
                    fi.write(corpus_list[i]['i'] + '\n')
                    ft.write(corpus_list[i]['t'] + '\n')
                    ff.write(corpus_list[i]['f'] + '\n')


#FIXME 检查tags_map读取是否正确
def calculate_accuracy(tags_map):
    
    with codecs.open(SRC_DIR + SRC_ID, 'r') as f:
        src_feedid = f.read().splitlines()
    with codecs.open(SRC_DIR + SRC_TEXT, 'r') as f:
        src_text = f.read().splitlines()
    
    # 调用mallet
    print('Calling mallet to create instance.mallet...')
    sp.call(['mallet', 'run', 'cc.mallet.topics.tui.DMRLoader', 
             TEXT, FEATURE, MALLET_INPUT], shell=True, cwd=TMP_DIR)
    print('Calling mallet to create topic index...')
    sp.call(['mallet', 'run', 'cc.mallet.topics.DMRTopicModel',
             MALLET_INPUT, '30'], shell=True, cwd=TMP_DIR)

    # 解压结果文件
    print('Unzip dmr state file...')
    with gzip.open(TMP_DIR + DMR_STATE_GZIP, 'rb') as fin:
        with open(TMP_DIR + DMR_STATE, 'wb') as fout:
            fout.write(fin.read())
    
    # 创建索引
    dmr_querier = dmr.DMR_wapper(TMP_DIR + DMR_STATE, TMP_DIR + DMR_TOPIC, TMP_DIR + TEXT)
    bm25_querier = bm25.BM25(TMP_DIR + TEXT, delimiter=' ')
    
    # 使用tags查询
    count = 0
    beta = 0.4
    mrank = 0.0
    
    for feedid, tset in tags_map.items():
        if int(feedid) >= len(src_text):
            continue
        dscore = np.array(dmr_querier.DMRScore(list(tset)))
        bscore = np.array(bm25_querier.BM25Score(list(tset)))
        mscore = np.log(dscore - np.min(dscore))* beta +  np.log(bscore - np.min(bscore)) * (1-beta)
        
        f_idx = next(i for i in range(len(src_feedid)) if src_feedid[i]==str(feedid))
        mrank += sum(i > mscore[f_idx] for i in mscore)
        
        count += 1
        if count % 500 == 0:
            print(count)
    
    print('The average rank of MIXED is ' + str(mrank/count))
    return mrank/count

if __name__ == "__main__":
    
    accuracy_list = []
    ratios = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    all_dict = pickle.load(open(TAGS_MAP_FILE, 'rb'))
    tags_map = all_dict['tags_map']
    
    for ratio in ratios:
        feed_label_dict = build_corpus(ratio)
        save_as_files(feed_label_dict)
        accuracy_list.append(calculate_accuracy(tags_map))
        
    pickle.dump(accuracy_list, open('step5_complete.pickle', 'wb'))
    
    

