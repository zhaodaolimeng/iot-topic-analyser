# -*- coding: utf-8 -*-
"""
Created on Tue Sep 20 22:48:59 2016

@author: limeng
"""

import pandas as pd
import numpy as np
import pickle

'''
查询测试
=======
输入查询语句q，返回一个所有文档的打分列表（打分最高的文档）
使用DMR的结果，使用tags作为查询词，看是否能命中原始的条目，返回不同文档的打分情况
计算每个文档的打分计算为两部分，即：
由BM25生成的打分权值 + 由q和d之间主题分布的KL距离所生成的打分权值

dmr.state样例，其中：
#doc source pos typeindex type topic
0 NA 0 0 park 29
0 NA 1 1 lights 22
0 NA 2 2 music 6
0 NA 3 3 sweden 6
0 NA 4 4 true 22
1 NA 0 5 ocean 16
1 NA 1 6 buoy 16
1 NA 2 7 cap 25
1 NA 3 6 buoy 16
1 NA 4 5 ocean 16
...
其中typeindex为不同词的序号，type为词本身的类别
对于新的查询，对于查询中的每一个词，在词库中查找对应的词，生成对应的多项分布
'''

DMR_STATE_FILE = 'output/dmr.state'
query_str = 'this is a temperature test'

dmr_state_type = {
    '#doc':np.int64, 
    'source': np.str, 
    'pos' : np.int64,
    'typeindex' : np.int64,
    'type' : np.str,
    'topic' : np.int64}
df = pd.read_csv(DMR_STATE_FILE, delimiter=' ', 
                 dtype=dmr_state_type, header=0)

terms = df[['type','topic']].drop_duplicates()
term_dict = terms.set_index('type').to_dict()['topic']

# 计算查询q的主题向量分布
topic_num = df[['topic']].max()[0] + 1
q_topic_vector = [1] * topic_num # 初始为1是为了smoothing
for query_term in query_str.split(' '):
    if query_term in term_dict:
        q_topic_vector[term_dict[query_term]] += 1

# 计算q主题向量和d主题向量之间的KL距离
def KL_dist(vq, vd):
    vq = np.array(vq)    
    vd = np.array(vd)
    vq = vq / np.sum(vq)
    vd = vd / np.sum(vd)
    return 1-0.5*sum((vq-vd)*np.log(vq/vd))
    
# 对于每个文档d，计算文档的主题向量
document_num = df[['#doc']].max()[0] + 1
rank_doc = []
for i in range(document_num):
    d_topic_vector = [1] * topic_num
    for idx,row in df.loc[df['#doc']==i].iterrows():
        d_topic_vector[row['topic']] += 1
    rank_doc.append(KL_dist(q_topic_vector, d_topic_vector))
    if i % 1000 == 0:
        print('doc=' + str(i))

pickle.dump(rank_doc, open( "step4_rank_doc.pickle", "wb" ))

# 越大说明q与d越接近
# 直接检查texts.txt中文件的对应内容
maxv = max(rank_doc)



