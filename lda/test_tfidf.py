# -*- coding: utf-8 -*-
"""
Created on Sat Apr 16 22:09:21 2016

@author: limeng
"""
import logging
from gensim import corpora, models, similarities

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# corpus are vectors of words
"""
corpus = [[(0, 1.0), (1, 1.0), (2, 1.0)],
           [(2, 1.0), (3, 1.0), (4, 1.0), (5, 1.0), (6, 1.0), (8, 1.0)],
           [(1, 1.0), (3, 1.0), (4, 1.0), (7, 1.0)],
           [(0, 1.0), (4, 2.0), (7, 1.0)],
           [(3, 1.0), (5, 1.0), (6, 1.0)],
           [(9, 1.0)],
           [(9, 1.0), (10, 1.0)],
           [(9, 1.0), (10, 1.0), (11, 1.0)],
           [(8, 1.0), (10, 1.0), (11, 1.0)]]

tfidf = models.TfidfModel(corpus)
vec = [(0, 1), (4, 1)]

index = similarities.SparseMatrixSimilarity(tfidf[corpus], num_features=12)
sims = index[tfidf[vec]]
"""

tfidf = models.TfidfModel(corpus)
index = similarities.SparseMatrixSimilarity(tfidf[corpus], num_features=12)
vec = [(0, 1), (4, 1)]
sims = index[tfidf[vec]] # BUGGY with real world dataset
print(list(enumerate(sims)))

"""
vec = [(0, 1), (4, 1)]
sims = index[tfidf[vec]] # BUGGY with real world dataset
print(list(enumerate(sims)))
"""
