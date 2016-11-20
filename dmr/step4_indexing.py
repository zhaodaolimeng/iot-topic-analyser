# -*- coding: utf-8 -*-
"""
Created on Thu Sep 22 10:56:19 2016

@author: limeng
"""

'''
构建索引
===========
输入：
features.txt，用于训练DMR的metadata
texts.txt，文档
feedid.txt，文档对应的id
dmr.state，DMR模型每个文档BoW中每个词对应的主题号
dmr-topics.txt，每个文档的主题向量
dmr-topwords.txt，每个主题出现频率最高的词
dmr.parameters，DMR模型的先验参数
输出：
step4_indexing.pickle，包含：
bm25，BM25模型实例
vd_list，每个文档的主题向量
word_dict，每个词的主题向量
'''

import numpy as np
import pickle
import codecs
import os.path
import DMR_wrapper as dmr

import sys
sys.path.insert(0, '../tfidf/')
import BM25 as bm25

DMR_STATE_FILE = 'output/dmr.state'
DMR_TOPICS_FILE = 'output/dmr-topics.txt'
DOCUMENT_FILE = 'output/texts.txt' # 两种方法统一的输入文件

#DMR_STATE_FILE = 'output_notags/dmr.state'
#DMR_TOPICS_FILE = 'output_notags/dmr-topics.txt'
#DOCUMENT_FILE = 'output_notags/texts.txt'

INDEX_FILE = 'step4_indexing.pickle' # 输出模型

# 显示前10个结果
def show_top10(scores):
    top10idx = reversed(sorted(range(len(scores)), key=lambda i: scores[i])[-10:])
    docs_list = []
    with codecs.open(DOCUMENT_FILE, 'r', 'utf-8') as f:
        docs_list = f.read().splitlines()
    for idx in top10idx:
        print(str(idx) + " --> " + str(scores[idx]) + " = " + docs_list[idx])

if os.path.isfile(INDEX_FILE) :
    all_dict = pickle.load(open(INDEX_FILE, "rb"))
    dmr_querier = all_dict['dmr_querier']
    bm25_querier = all_dict['bm25_querier']
else:
    dmr_querier = dmr.DMR_wapper(DMR_STATE_FILE, DMR_TOPICS_FILE, DOCUMENT_FILE)
    bm25_querier = bm25.BM25(DOCUMENT_FILE, delimiter=' ')
    print('Dumping data ...')
    all_dict = dict()
    all_dict['dmr_querier'] = dmr_querier
    all_dict['bm25_querier'] = bm25_querier
    pickle.dump(all_dict, open( "step4_indexing.pickle", "wb" ))
    print('Dump done ...')

query_str = 'counter temperature'
print('=======================')
b_scores = bm25_querier.BM25Score(query_str.split())
show_top10(b_scores)
print('=======================')
d_scores = dmr_querier.dmr_score(query_str.split(), alpha=0.0001)
show_top10(d_scores)
print('=======================')
# mix_score = np.array(d_scores) * np.array(b_scores)
beta = 0.4
mix_score = np.log(d_scores - np.min(d_scores))* beta +  np.log(b_scores - np.min(b_scores)) * (1-beta)

show_top10(mix_score.tolist())

