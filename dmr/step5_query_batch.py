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
'''
all_dict = pickle.load(open(SOURCE_FILE, 'rb'))

def compute_score(all_dict):
    tags_map = all_dict['tags_map']
    all_dict = pickle.load(open(INDEX_FILE, 'rb'))
    dmr_querier = all_dict['dmr_querier']
    bm25_querier = all_dict['bm25_querier']
    dscore_list = []
    bscore_list = []
    feedid_list = []
    print('Start to compute bm25, dmr score ... ')
    count = 0
    for feedid, tset in tags_map.items():
        dscore = np.array(dmr_querier.DMRScore(list(tset)))
        bscore = np.array(bm25_querier.BM25Score(list(tset)))
        dscore_list.append(dscore)
        bscore_list.append(bscore)
        feedid_list.append(feedid)
        count += 1
        if count % 100 == 0:
            print(count)
    
    print('Done!')
    print('=================================')
    pickle.dump(dscore_list, open('step5_dscore_list.pickle','wb'))
    pickle.dump(bscore_list, open('step5_bscore_list.pickle','wb'))
    print('Data saved!')
    return dscore_list, bscore_list, feedid_list

dscore_list, bscore_list, feedid_list = compute_score(all_dict)

'''
步骤四，计算每个条目中不同的方法对应的排名情况
=================================
得到打分序列之后，看feedid对应的序列在打分中为多少名，名次越前说明准确
'''
def compute_rank(dscore_list, bscore_list, feedid_list):
    drank_list = []
    brank_list = []
    feed_list = all_dict['feed_list']
    print('Start to compute rank ... ')
    count = 0
    for i in range(len(dscore_list)):
        dscore = dscore_list[i]
        bscore = bscore_list[i]    
        feedid = feedid_list[i]
        f_idx = next(i for i in range(len(feed_list)) if feed_list[i]==str(feedid))
        drank = sum(i > dscore[f_idx] for i in dscore)
        drank_list.append(drank)
        f_idx = next(i for i in range(len(feed_list)) if feed_list[i]==str(feedid))
        brank = sum(i > bscore[f_idx] for i in bscore)
        brank_list.append(brank)
        
        count += 1
        if count % 1000 == 0:
            print(count)
    print('Done!')
    print('The average rank of BM25 is ' + str(np.mean(brank_list)))
    print('The average rank of DMR is ' + str(np.mean(drank_list)))
    print('=================================')

# compute_rank(dscore_list, bscore_list, feedid_list)

def compute_mrank(all_dict, bscore_list, dscore_list, feedid_list, beta=0.01):
    mrank_list = []
    feed_list = all_dict['feed_list']
    print('Start to compute mixed score ... ')
    count = 0
    for i in range(len(dscore_list)):
        feed_list_length = len(feed_list)
        dscore = dscore_list[i]
        bscore = bscore_list[i]
        feedid = feedid_list[i]
        
        # mscore = (dscore - np.min(dscore)) * (bscore - np.min(bscore))
        # mscore = (dscore - np.min(dscore)) * beta +  (bscore - np.min(bscore)) * (1-beta)
        mscore = np.log(dscore - np.min(dscore))* beta +  np.log(bscore - np.min(bscore)) * (1-beta)
        f_idx = next(i for i in range(feed_list_length) if feed_list[i]==str(feedid))
        mrank = sum(i > mscore[f_idx] for i in mscore)
        
        count += 1
        if count % 1000 == 0:
            print(count)
        mrank_list.append(mrank)
    print('The average rank of Mixed Method is ' + str(np.mean(mrank_list)))
    return mrank_list


betas = [0, 0.01, 0.1, 0.2, 0.5, 0.8, 1.0]
for i in range(len(betas)):
    compute_mrank(all_dict, bscore_list, dscore_list, feedid_list, beta=betas[i])


