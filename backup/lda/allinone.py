# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 10:29:06 2016

@author: limeng
"""

"""
执行step3_lda中的lda主题提取方法，调整主题数目k，看对similarity的影响
输入：
输出：不同的主题数目k下的similarity

"""

import gensim.models.ldamodel as lda

max_test_num = 2;
simlist = []

for num_of_topics in range(1,16):
    sims = [];
    for num_of_test in range(max_test_num):
        ldamodel = lda.LdaModel(corpus, id2word=dictionary, alpha='auto', num_topics=num_of_topics)
        sim = similarity(corpus_tag, dictionary_tag, corpus, ldamodel)
        print('Topic K=',num_of_topics, ', Test #', num_of_test,' done! sim=',sim)
        sims.append(sim)
    simlist.append(sims)
