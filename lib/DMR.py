# -*- coding: utf-8 -*-
"""
Created on Fri Sep 23 21:20:26 2016

@author: limeng
"""

import pandas as pd
import numpy as np
import subprocess as sp
import codecs
import gzip


class DMR(object):

    def __init__(self, input_text, input_features, work_dir, topic_num=20):
        """
        训练DMR模型，提供查询方法
        :param input_text:
        :param input_features:
        :param topic_num:
        """
        self.working_directory = work_dir
        self.word_dict = dict()
        self.vd_list = []  # 读入的每个文档的主题分布

        mallet_instance = 'mallet.instance'
        output_runtime = 'runtime.txt'
        dmr_state_compressed = 'dmr.state.gz'
        dmr_state = 'dmr.state.txt'
        dmr_topic = 'dmr-topics.txt'

        # 生成mallet.instance
        print('Create instance.mallet...')
        print(self.working_directory)
        print(input_text)
        print(input_features)
        sp.check_call(['mallet', 'run', 'cc.mallet.topics.tui.DMRLoader',
                       input_text, input_features, mallet_instance],
                      stdout=sp.PIPE, shell=True, cwd=self.working_directory)
        # 生成dmr.parameters和dmr.state.gz
        print('Create topic index...')
        with codecs.open(self.working_directory + output_runtime, 'w', 'utf-8') as f:
            sp.check_call(['mallet', 'run', 'cc.mallet.topics.DMRTopicModel',
                           mallet_instance, str(topic_num)],
                          shell=True, stdout=f, cwd=self.working_directory)

        # 解压dmr.state.gz
        print('Unzip dmr state file...')
        with gzip.open(work_dir + dmr_state_compressed, 'rb') as fin:
            with open(work_dir + dmr_state, 'wb') as fout:
                fout.write(fin.read())

        print('Starting to build index ... ')
        df = pd.read_csv(
            work_dir + dmr_state,
            delimiter=' ',
            dtype={'#doc': np.int64, 'source': np.str, 'pos': np.int64,
                   'typeindex': np.int64, 'type': np.str, 'topic': np.int64},
            header=0)

        # 读入每个文档对应的主题
        print('Start to load document-topic file ...')
        df_doc2topic = pd.read_csv(work_dir + dmr_topic, delimiter=' ', header=None, skiprows=1)
        for idx, row in df_doc2topic.iterrows():
            vd = [0.0] * topic_num
            for i in range(topic_num):
                vd[int(row[2 + i*2])] = row[3 + i*2]
            self.vd_list.append(vd)

        # 每个词属于不同主题的次数
        print('Start to compute topic vector ...')
        for idx, row in df.iterrows():
            if row['type'] not in self.word_dict:
                self.word_dict[row['type']] = [1] * topic_num
            self.word_dict[row['type']][row['topic']] += 1
            if idx % 10000 == 0:
                print(idx)
        print('Topic vector compute done!')

    def dmr_score(self, query_list, alpha=0.0000001):
        """
        主题模型查询
        计算查询q的主题向量分布
        """
        # vq = [self.word_dict[query_term] for query_term in query_list if query_term in self.word_dict]
        # vq = np.array(vq)
        # vq /= np.sum(vq)
        # rank_doc = []
        # for vd in self.vd_list:
        #     vd = np.array(vd) + alpha
        #     vd /= np.sum(vd)
        #     rank_doc.append(1-0.5*sum((vq-vd)*np.log(vq/vd)))
        # return rank_doc
        vq = [1.0] * len(self.vd_list[0])  # 防止ValueError
        for query_term in query_list:
            if query_term in self.word_dict:
                vq = map(sum, zip([vq, self.word_dict[query_term]]))
                vq = self.word_dict[query_term]

        vq = np.array(vq)
        vq /= np.sum(vq)
        rank_doc = []
        for vd in self.vd_list:
            vd = np.array(vd) + alpha
            vd /= np.sum(vd)
            rank_doc.append(1 - 0.5 * sum((vq - vd) * np.log(vq / vd)))
        return rank_doc

    def optimized_score(self, query_list, bm25, beta=0.4):
        """
        与bm25方法进行混合查询
        :param bm25:
        :param beta:
        :return:
        """
        dscore = np.array(self.dmr_score(query_list))
        bscore = np.array(bm25.bm25_score(query_list))
        return np.log(dscore - np.min(dscore)) * beta + np.log(bscore - np.min(bscore)) * (1 - beta)
