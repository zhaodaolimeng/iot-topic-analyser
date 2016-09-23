# -*- coding: utf-8 -*-
"""
Created on Thu Sep 22 10:56:19 2016

@author: limeng
"""

'''
查询效果对比
===========
'''

import pandas as pd
import numpy as np
import pickle
import codecs
import os.path

import sys
sys.path.insert(0, '../tfidf/')
import BM25 as bm25

DMR_STATE_FILE = 'output/dmr.state'
DMR_TOPICS_FILE = 'output/dmr-topics.txt'
DOCUMENT_FILE = 'output/texts.txt' # 两种方法统一的输入文件

WORD_DICT_SAVE = 'step4_word_dict.pickle'

# 初始化主题索引
df = pd.read_csv(DMR_STATE_FILE, delimiter=' ', 
  dtype={
    '#doc':np.int64, 
    'source': np.str, 
    'pos' : np.int64,
    'typeindex' : np.int64,
    'type' : np.str,
    'topic' : np.int64}, header=0)
terms = df[['type','topic']].drop_duplicates()
term_dict = terms.set_index('type').to_dict()['topic']
bm25 = bm25.BM25(DOCUMENT_FILE, delimiter=' ')

# 计算每个文档对应的主题向量
TOPIC_NUM = df[['topic']].max()[0] + 1
DOCUMENT_NUM = df[['#doc']].max()[0] + 1


print('Start to load document-topic file ...')
# 读入每个文档对应的主题
df_doc2topic = pd.read_csv(DMR_TOPICS_FILE, delimiter=' ', header=None, skiprows=1)

# 每个词属于不同主题的次数
print('Start to compute topic vector ...')


word_dict = dict()
if os.path.isfile(WORD_DICT_SAVE) :
    word_dict = pickle.load(open(WORD_DICT_SAVE, "rb"))
else:
    for idx, row in df.iterrows():
        if row['type'] not in word_dict:
            word_dict[row['type']] = [1] * TOPIC_NUM
        word_dict[row['type']][row['topic']] += 1
        if idx%10000==0:
            print(idx)
    pickle.dump(word_dict, open(WORD_DICT_SAVE, 'wb'))

print('Topic vector compute done!')

'''
关键词查询
=========
'''
def query_BM25(query_str):
    return bm25.BM25Score(query_str.split())

'''
主题模型查询
===========
'''
def query_DMR(query_str):
    # 计算查询q的主题向量分布
#    vq = np.array([1] * TOPIC_NUM) # 初始为1是为了smoothing
#    vq = vq + np.array(word_dict[query_term])
#    vq /= np.sum(vq)
    vq = []
    for query_term in query_str.split(' '):
        if query_term in word_dict:
            vq = word_dict[query_term]

    vq = np.array(vq)
    vq = vq / np.sum(vq)
    
    rank_doc = []
    for idx,row in df_doc2topic.iterrows():
        vd = [0.0] * TOPIC_NUM
        for i in range(TOPIC_NUM):
            vd[int(row[2 + i*2])] = row[3 + i*2]
        vd = np.array(vd) + 0.00001
        vd = vd / np.sum(vd)
        rank_doc.append(1-0.5*sum((vq-vd)*np.log(vq/vd)))
    return rank_doc


# 显示前10个结果
def show_top10(scores):
    top10idx = reversed(sorted(range(len(scores)), key=lambda i: scores[i])[-10:])
    docs_list = []
    with codecs.open(DOCUMENT_FILE, 'r', 'utf-8') as f:
        docs_list = f.read().splitlines()
    for idx in top10idx:
        print(str(idx) + " --> " + str(scores[idx]) + " = " + docs_list[idx])


query_str = 'solar power'
print('=======================')
b_scores = query_BM25(query_str)
show_top10(b_scores)
print('=======================')
d_scores = query_DMR(query_str)
show_top10(d_scores)
print('=======================')
mix_score = np.array(d_scores) * np.array(b_scores)
show_top10(mix_score.tolist())

# 设计一个评分方法，对前20项进行评分
#pickle.dump(rank_doc, open( "step4_rank_doc.pickle", "wb" ))
#maxv = max(rank_doc)
