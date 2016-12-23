# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 15:00:06 2016

@author: limeng
"""

import logging
import numpy as np
import gensim
import random

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
random.seed(11091987)           #set random seed


# load id->word mapping (the dictionary)
id2word =  gensim.corpora.Dictionary.load_from_text('output/dict.dict')
corpus = gensim.corpora.MmCorpus('output/dtm.mtx')

print(id2word)
print(corpus)

# shuffle corpus
cp = list(corpus)
random.shuffle(cp)

# split into 80% training and 20% test sets
p = int(len(cp) * .8)
cp_train = cp[0:p]
cp_test = cp[p:]

import time

# num topics
topic_cnt_list=[10,20,30,50,100,200]

for topic_cnt in topic_cnt_list:
    start_time = time.time()
    lda = gensim.models.ldamodel.LdaModel(corpus=cp_train, id2word=id2word, num_topics=topic_cnt,
                                          update_every=1, chunksize=1000, passes=2)
    elapsed = time.time() - start_time
    print('Training time: %.4f' % elapsed, end=' || ')
    
    # print(lda.show_topics(topics=-1, topn=10, formatted=True))
    # print(ldamodel.show_topics(num_topics=30, num_words=5))
    print('Perplexity: ', topic_cnt, end=' || ')
    # perplex = lda.log_perplexity(cp_test);
    perplex = lda.bound(cp_test)
    # print('Perplexity: %.4f' % perplex)
    perplex_word = np.exp2(- perplex / sum(cnt for document in cp_test for _, cnt in document))
    print('Per-word Perplexity: %.4f' % perplex_word)
    # print('Elapsed time: %.4f' % (time.time() - start_time))
