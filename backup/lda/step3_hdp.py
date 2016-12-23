# -*- coding: utf-8 -*-
"""
Created on Sat Apr 16 22:14:04 2016

@author: limeng
"""
import numpy as np
import gensim.models.hdpmodel as hdp
from gensim import models

hdpmodel = hdp.HdpModel(corpus, id2word=dictionary, alpha=100, gamma=0.01)

# 将生成的hdp转换成为lda进行使用
hdp_ldamodel = models.LdaModel(id2word=hdpmodel.id2word,
                               num_topics=len(hdpmodel.lda_alpha), 
                               alpha=hdpmodel.lda_alpha, 
                               eta=hdpmodel.m_eta) 
hdp_ldamodel.expElogbeta = np.array(hdpmodel.lda_beta, dtype=np.float32)

# 输出主题列表
hdpmodel.print_topics(topics=20, topn=5)

# 输出文本文件的主题分布
hdp_ldamodel.get_document_topics(corpus[0])
hdp_ldamodel.show_topics(num_topics=20, num_words=5)
hdp_ldamodel.show_topic(0)
