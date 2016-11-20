# -*- coding: utf-8 -*-
"""
Created on Fri Sep 23 21:20:26 2016

@author: limeng
"""

import pandas as pd
import numpy as np

'''
用于查询的DMR模型
================
通过Mallet生成的每个文档中每个单词主题号（dmr.state.gz）、
每个文档的主题分布（doc-topic.txt）响应用户查询。

state_file 为从dmr.state.gz中解压出的文本文件，内容形式为doc-word-topic三元组
topic_file 为调用mallet中printDocumentTopics方法得到的每个文档的主题分布
doc_file 原始文档输入text.txt，未使用
'''
class DMR_wapper(object):
    
    def __init__(self, state_file, topic_file):
        self.DMR_STATE_FILE = state_file
        self.DMR_TOPICS_FILE = topic_file
        self.word_dict = dict()
        self.vd_list = []  # 读入的每个文档的主题分布
        self.build_index()
        
    '''
    初始化索引
    '''
    def build_index(self):
        print('Starting to build index ... ')
        df = pd.read_csv(self.DMR_STATE_FILE, delimiter=' ', 
          dtype={
            '#doc':np.int64, 
            'source': np.str, 
            'pos' : np.int64,
            'typeindex' : np.int64,
            'type' : np.str,
            'topic' : np.int64}, header=0)
        # 计算每个文档对应的主题向量
        TOPIC_NUM = df[['topic']].max()[0] + 1
        
        # 读入每个文档对应的主题
        print('Start to load document-topic file ...')
        df_doc2topic = pd.read_csv(self.DMR_TOPICS_FILE, delimiter=' ', header=None, skiprows=1)
        for idx,row in df_doc2topic.iterrows():
            vd = [0.0] * TOPIC_NUM
            for i in range(TOPIC_NUM):
                vd[int(row[2 + i*2])] = row[3 + i*2]
            self.vd_list.append(vd)
        
        # 每个词属于不同主题的次数
        print('Start to compute topic vector ...')
        for idx, row in df.iterrows():
            if row['type'] not in self.word_dict:
                self.word_dict[row['type']] = [1] * TOPIC_NUM
            self.word_dict[row['type']][row['topic']] += 1
            if idx%10000==0:
                print(idx)
        print('Topic vector compute done!')
    

    '''
    返回所有document的主题向量
    主题k的概率=(主题k在文档m中的出现次数+alpha_k)/(文档m的词个数+alpha_k)
    '''
    def dmr_document_vector(self, alpha):
        
        
        
        pass
        
    '''
    主题模型查询
    '''
    def dmr_score(self, query_list, alpha=0.0000001):
        # 计算查询q的主题向量分布
        vq = [1.0] * len(self.vd_list[0]) # 防止ValueError
        for query_term in query_list:
            if query_term in self.word_dict:
                vq = map(sum, zip([vq, self.word_dict[query_term]]))
                vq = self.word_dict[query_term]

        vq = np.array(vq)
        vq = vq / np.sum(vq)
        rank_doc = []
        for vd in self.vd_list:
            vd = np.array(vd) + alpha
            vd = vd / np.sum(vd)
            rank_doc.append(1-0.5*sum((vq-vd)*np.log(vq/vd)))
        return rank_doc