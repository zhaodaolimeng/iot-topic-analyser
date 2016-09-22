# -*- coding: utf-8 -*-
"""
Created on Thu Sep 22 10:56:19 2016

@author: limeng
"""

'''
查询性能对比
===========
'''

import pandas as pd
import numpy as np
import pickle
import codecs
import sys
sys.path.insert(0, '../tfidf/')
import BM25 as bm25

DMR_STATE_FILE = 'output/dmr.state'
DOCUMENT_FILE = 'output/texts.txt' # 两种方法统一的输入文件

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


def query_BM25(query_str):
    return bm25.BM25Score(query_str.split())
    

def query_DMR(query_str, df):
    # 计算查询q的主题向量分布
    topic_num = df[['topic']].max()[0] + 1
    vq = [1] * topic_num # 初始为1是为了smoothing
    
    for query_term in query_str.split(' '):
        if query_term in term_dict:
            vq[term_dict[query_term]] += 1    
    
    # 对于每个文档d，计算文档的主题向量
    document_num = df[['#doc']].max()[0] + 1
    rank_doc = []
    for i in range(document_num):
        vd = [1] * topic_num
        for idx,row in df.loc[df['#doc']==i].iterrows():
            vd[row['topic']] += 1
        
        vq = np.array(vq)
        vd = np.array(vd)
        vq = vq / np.sum(vq)
        vd = vd / np.sum(vd)
        rank_doc.append(1-0.5*sum((vq-vd)*np.log(vq/vd)))
        
        if i % 1000 == 0:
            print('doc=' + str(i))
    return rank_doc

# 越大说明q与d越接近
# 直接检查texts.txt中文件的对应内容
#pickle.dump(rank_doc, open( "step4_rank_doc.pickle", "wb" ))
#maxv = max(rank_doc)

query_str = 'radiation '
scores = query_BM25(query_str)
top10idx = reversed(sorted(range(len(scores)), key=lambda i: scores[i])[-10:])

docs_list = []
with codecs.open(DOCUMENT_FILE, 'r', 'utf-8') as f:
    docs_list = f.read().splitlines()

for idx in top10idx:
    print(str(idx) + " --> " + str(scores[idx]) + " = " + docs_list[idx])

# 设计一个评分方法，对前20项进行评分

