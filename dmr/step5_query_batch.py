# -*- coding: utf-8 -*-
"""
Created on Fri Sep 23 12:05:20 2016

@author: limeng
"""

'''
查询准确度验证实验
=================
将tags作为查询输入，看返回的rank中该tags位于多少位，能侧面反映查询的命中率
'''
import pickle
import numpy as np

SOURCE_FILE = 'step2_generate_data_notags.pickle'
INDEX_FILE = 'step4_indexing.pickle'

'''
步骤一，形成不包含tags的语料
==========================
执行step2_generate_data_notags.py，从texts.txt中剔除tags所包含的单词
每个对应的feedid，从db读取对应的tags，输出目录为output_notags
'''

'''
步骤二，在后台执行mallet工具中的命令
=============================
cp ouput/features.txt output_notags.txt
cd output_notags/
mallet run cc.mallet.topics.tui.DMRLoader texts.txt features.txt instance.mallet
mallet run cc.mallet.topics.DMRTopicModel instance.mallet 30
'''

'''
步骤三，计算每个包含tags的feedid对应的文档的搜索打分
============================
使用pickle读出BM25和DMR打分模型，对于tags_map中的每个query调用查询
得到打分序列之后，看feedid对应的序列在打分中为多少名，名次越前说明准确
'''
all_dict = pickle.load(open(SOURCE_FILE, 'rb'))
tags_map = all_dict['tags_map']
feed_list = all_dict['feed_list']
all_dict = pickle.load(open(INDEX_FILE, 'rb'))
dmr_querier = all_dict['dmr_querier']
bm25_querier = all_dict['bm25_querier']

drank_list = []
brank_list = []
mrank_list = []

count = 0
for feedid, tset in tags_map.items():
    dscore = np.array(dmr_querier.DMRScore(list(tset)))
    f_idx = next(i for i in range(len(feed_list)) if feed_list[i]==str(feedid))
    drank = sum(i > dscore[f_idx] for i in dscore)
    drank_list.append(drank)
    
    bscore = np.array(bm25_querier.BM25Score(list(tset)))
    f_idx = next(i for i in range(len(feed_list)) if feed_list[i]==str(feedid))
    brank = sum(i > bscore[f_idx] for i in bscore)
    brank_list.append(brank)
    
    mscore = (dscore - np.min(dscore)) * (bscore - np.min(bscore))
    f_idx = next(i for i in range(len(feed_list)) if feed_list[i]==str(feedid))
    mrank = sum(i > mscore[f_idx] for i in mscore)
    mrank_list.append(mrank)
    
#    print(str(drank) +'\t' + str(brank) + '\t' + str(mrank))
    
    count += 1
    if count % 500 == 0:
        print(count)

pickle.dump(drank_list, open('step5_drank_list.pickle','wb'))
pickle.dump(brank_list, open('step5_brank_list.pickle','wb'))

print('The average rank of BM25 is ' + str(np.mean(brank_list)))
print('The average rank of DMR is ' + str(np.mean(drank_list)))
print('The average rank of Mixed Method is ' + str(np.mean(mrank_list)))
