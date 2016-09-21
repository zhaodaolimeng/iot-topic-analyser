# -*- coding: utf-8 -*-
"""
Created on Tue Sep 20 11:22:44 2016

@author: limeng
"""

import math

# BM25 parameters.
PARAM_K1 = 1.5
PARAM_B = 0.75
EPSILON = 0.25

class BM25(object):

    def __init__(self, corpus):
        self.corpus_size = len(corpus)
        self.avgdl = sum(map(lambda x: float(len(x)), corpus)) / self.corpus_size
        self.corpus = corpus
        self.f = []
        self.df = {}  # term在文档中出现的次数
        self.idf = {} # 全部文档数目/包含term的文档数目
        self.initialize()

    def initialize(self):
        for document in self.corpus:
            frequencies = {}
            for word in document:
                if word not in frequencies:
                    frequencies[word] = 0
                frequencies[word] += 1
            self.f.append(frequencies)

            for word, freq in frequencies.items():
                if word not in self.df:
                    self.df[word] = 0
                self.df[word] += 1

        for word, freq in self.df.items():
            self.idf[word] = math.log(self.corpus_size-freq+0.5) - math.log(freq+0.5)

    def get_score(self, document, index, average_idf):
        score = 0
        for word in document:
            if word not in self.f[index]:
                continue
            idf = self.idf[word] if self.idf[word] >= 0 else EPSILON * average_idf
            score += (idf*self.f[index][word]*(PARAM_K1+1)
                      / (self.f[index][word] + 
                      PARAM_K1*(1 - PARAM_B+PARAM_B*self.corpus_size / self.avgdl)))
        return score

    def get_scores(self, document, average_idf):
        scores = []
        for index in range(self.corpus_size):
            score = self.get_score(document, index, average_idf)
            scores.append(score)
        return scores


def get_bm25_weights(corpus):
    bm25 = BM25(corpus)
    average_idf = sum(map(lambda k: float(bm25.idf[k]), bm25.idf.keys())) / len(bm25.idf.keys())

    weights = []
    for doc in corpus:
        scores = bm25.get_scores(doc, average_idf)
        weights.append(scores)

    return weights

if __name__ == '__main__' :
    #mycorpus.txt is as following:


#    fn_docs = 'mycorpus.txt'
    docs = '''Human machine interface for lab abc computer applications 
A survey of user opinion of computer system response time 
The EPS user interface management system 
System and human system engineering testing of EPS 
Relation of user perceived response time to error measurement
The generation of random binary unordered trees
The intersection graph of paths in trees
Graph IV Widths of trees and well quasi ordering
Graph minors A survey'''

    doc_list = docs.split('\n')
    bm25 = BM25(doc_list)
    weight = get_bm25_weights(doc_list)
    
    average_idf = sum(map(lambda k: float(bm25.idf[k]), bm25.idf.keys())) / len(bm25.idf.keys())
    doc = 'Graph minors A survey'
#    doc = 'The intersection graph of paths in trees survey Graph'
    w = bm25.get_scores(doc, average_idf)
    print(w)
    
#    Query = 'The intersection graph of paths in trees survey Graph'
#    Query = Query.split()
#    scores = bm25.BM25Score(Query)
#    tfidf = bm25.TFIDF()
#    print(bm25.Items())
#    for i, tfidfscore in enumerate(tfidf):
#        print(i, tfidfscore)

