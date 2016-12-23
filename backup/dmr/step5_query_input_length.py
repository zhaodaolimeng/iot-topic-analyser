# -*- coding: utf-8 -*-
"""
Created on Mon Sep 26 23:11:07 2016

@author: limeng
"""

'''
语料数量对查询结果的影响
======================
该实验是为了说明前期进行描述补充的意义
每次如果不能直接执行的话，需要手动运行mallet
读入texts.txt、feedid.txt、step2.pickle，对于其中内容进行切分
'''

import pickle
import codecs
import gzip
import subprocess as sp
import DMR_wrapper as dmr
import sys
import numpy as np
sys.path.insert(0, '../tfidf/')
import BM25 as bm25

TAGS_MAP_FILE = 'step2_generate_data.pickle'
SRC_ID = 'output/feedid.txt'
SRC_TEXT = 'output/texts.txt'
SRC_FEATURE = 'output/features.txt'

TMP_DIR = 'output_slice/'
ID = 'feedid.txt'
TEXT = 'texts.txt'
FEATURE = 'features.txt'
MALLET_INPUT = 'instance.mallet'
DMR_STATE_GZIP = 'dmr.state.gz'
DMR_STATE = 'dmr.state'
DMR_TOPIC = 'dmr-topics.txt'


def compare_by_range(tags_map, src_text, src_feedid, src_feature):
    
    print('Scale of Input = ' + str(len(src_text)))
    
    # 将切片的数据输出为文件
    with codecs.open(TMP_DIR + ID, 'w', 'utf-8') as fi:
        with codecs.open(TMP_DIR + TEXT, 'w', 'utf-8') as ft:
            with codecs.open(TMP_DIR + FEATURE, 'w', 'utf-8') as ff:
                for i in range(len(src_text)):
                    fi.write(src_feedid[i] + '\n')
                    ft.write(src_text[i] + '\n')
                    ff.write(src_feature[i] + '\n')
    
    # 调用mallet
    sp.call(['mallet', 'run', 'cc.mallet.topics.tui.DMRLoader', 
             TEXT, FEATURE, MALLET_INPUT], shell=True, cwd=TMP_DIR)
    sp.call(['mallet', 'run', 'cc.mallet.topics.DMRTopicModel',
             MALLET_INPUT, '30'], shell=True, cwd=TMP_DIR)

    # 解压结果文件
    with gzip.open(TMP_DIR + DMR_STATE_GZIP, 'rb') as fin:
        with open(TMP_DIR + DMR_STATE, 'wb') as fout:
            fout.write(fin.read())
    
    # 创建索引
    dmr_querier = dmr.DMR_wapper(TMP_DIR + DMR_STATE, TMP_DIR + DMR_TOPIC, TMP_DIR + TEXT)
    bm25_querier = bm25.BM25(TMP_DIR + TEXT, delimiter=' ')
    
    # 使用tags查询
    count = 0
    beta = 0.4
    drank = 0.0
    brank = 0.0
    mrank = 0.0
    
    for feedid, tset in tags_map.items():
        
        if int(feedid) >= len(src_text):
            continue
        dscore = np.array(dmr_querier.DMRScore(list(tset)))
        bscore = np.array(bm25_querier.bm25_score(list(tset)))
        mscore = np.log(dscore - np.min(dscore))* beta +  np.log(bscore - np.min(bscore)) * (1-beta)
        
        f_idx = next(i for i in range(len(src_feedid)) if src_feedid[i]==str(feedid))
        drank += sum(i > dscore[f_idx] for i in dscore)
        f_idx = next(i for i in range(len(src_feedid)) if src_feedid[i]==str(feedid))
        brank += sum(i > bscore[f_idx] for i in bscore)
        f_idx = next(i for i in range(len(src_feedid)) if src_feedid[i]==str(feedid))
        mrank += sum(i > mscore[f_idx] for i in mscore)
        
        count += 1
        if count % 500 == 0:
            print(count)
    
    print('The average rank of DMR is ' + str(drank/count))
    print('The average rank of BM25 is ' + str(brank/count))
    print('The average rank of MIXED is ' + str(mrank/count))
    
    return drank/count, brank/count, mrank/count
    
    
def run_comparsion(pieces = 10):
    
    all_dict = pickle.load(open(TAGS_MAP_FILE, 'rb'))
    tags_map = all_dict['tags_map']
    text_list = []
    id_list = []
    feature_list = []
    
    with codecs.open(SRC_ID, 'r') as f:
        id_list = f.read().splitlines()
    with codecs.open(SRC_TEXT, 'r') as f:
        text_list = f.read().splitlines()
    with codecs.open(SRC_FEATURE, 'r') as f:
        feature_list = f.read().splitlines()
    
    rank_list = []
    last_index = int(len(id_list)/10)
    while last_index < len(id_list):
        rank_dict = dict()
        rank_dict['dr'], rank_dict['br'], rank_dict['mr'] = \
        compare_by_range(tags_map, text_list[:last_index], 
                         id_list[:last_index], feature_list[:last_index])
        last_index += int(len(id_list)/10)
        rank_list.append(rank_dict)
    
    return rank_list

if __name__ == "__main__":
    
    rank_list = run_comparsion()
    pickle.dump(rank_list, open('step5_query_input_length.pickle', 'wb'))
    
