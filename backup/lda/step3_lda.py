# -*- coding: utf-8 -*-
"""
Created on Sun Apr 17 16:44:21 2016

@author: limeng
"""

import gensim.models.ldamodel as lda

ldamodel = lda.LdaModel(corpus, id2word=dictionary, alpha='auto', num_topics=30)

# 输出主题
print(ldamodel.show_topics(num_topics=30, num_words=5))

# 输出指定文档的主题分布
# ldamodel.get_document_topics(dictionary.doc2bow(documents[1].lower().split()))
print(ldamodel.get_document_topics(corpus[0]))


"""
import numpy as np
import lda
# import pickle

def print_topics(topic_word, vocab):
    n_top_words = 4
    for i, topic_dist in enumerate(topic_word):
        topic_words = vocab[np.argsort(topic_dist)][:-n_top_words:-1]
        print('Topic {}: {}'.format(i, ' '.join(topic_words)))


print('Loading dataset...')
# Dataset from step 2
X = np.array(bag_of_words)
vocab = np.array(xively_idx2word)
# vocab = lda.datasets.load_reuters_vocab()

print('Creating model...')
model = lda.LDA(n_topics=12, n_iter=1000, random_state=1)

print('Fit model...')
model.fit(X)  # model.fit_transform(X) is also available

print('Fit done!')
# model.components_ also works
print_topics(model.topic_word_, vocab)

# pickle
"""
