# -*- coding: utf-8 -*-
"""
Created on Tue Sep 20 11:22:44 2016
http://lixinzhang.github.io/implementation-of-okapi-bm25-on-python.html

"""
from gensim import corpora
import math
import codecs

# BM25 parameters.
PARAM_K1 = 1.5
PARAM_B = 0.75
EPSILON = 0.25


class BM25(object):

    def __init__(self, docs, work_dir, delimiter=' '):
        self.dictionary = corpora.Dictionary()
        self.DF = {}
        self.delimiter = delimiter
        self.DocTF = []
        self.DocIDF = {}
        self.N = 0
        self.DocAvgLen = 0
        self.docs_location = work_dir + docs
        self.DocLen = []

        self.build_dictionary()
        self.tfidf_generator()

    def build_dictionary(self):
        raw_data = []
        f = codecs.open(self.docs_location, 'r', 'utf-8')
        for line in f:
            raw_data.append(line.strip().split(self.delimiter))
        self.dictionary.add_documents(raw_data)

    def tfidf_generator(self, base=math.e):
        doc_total_len = 0
        f = codecs.open(self.docs_location, 'r', 'utf-8')
        for line in f:
            doc = line.strip().split(self.delimiter)
            doc_total_len += len(doc)
            self.DocLen.append(len(doc))
            bow = dict([(term, freq*1.0/len(doc)) for term, freq in self.dictionary.doc2bow(doc)])
            for term, tf in bow.items():
                if term not in self.DF:
                    self.DF[term] = 0
                self.DF[term] += 1
            self.DocTF.append(bow)
            self.N += 1
        for term in self.DF:
            self.DocIDF[term] = math.log((self.N - self.DF[term] + 0.5) / (self.DF[term] + 0.5), base)
        self.DocAvgLen = doc_total_len / self.N

    def bm25_score(self, query_list, k1=1.5, b=0.75):
        query_bow = self.dictionary.doc2bow(query_list)
        score = []
        for idx, doc in enumerate(self.DocTF):
            common_terms = set(dict(query_bow).keys()) & set(doc.keys())
            tmp_score = []
            doc_terms_len = self.DocLen[idx]
            for term in common_terms:
                upper = (doc[term] * (k1+1))
                below = ((doc[term]) + k1*(1 - b + b*doc_terms_len/self.DocAvgLen))
                tmp_score.append(self.DocIDF[term] * upper / below)
            score.append(sum(tmp_score))
        return score

    def items(self):
        # Return a list [(term_idx, term_desc),]
        items = self.dictionary.items()
        return sorted(items)


if __name__ == '__main__':
    """
    mycorpus.txt:

    Human machine interface for lab abc computer applications
    A survey of user opinion of computer system response time
    The EPS user interface management system
    System and human system engineering testing of EPS
    Relation of user perceived response time to error measurement
    The generation of random binary unordered trees
    The intersection graph of paths in trees
    Graph IV Widths of trees and well quasi ordering
    Graph minors A survey
    """
    
    fn_docs = 'mycorpus.txt'
    bm25 = BM25(fn_docs, delimiter=' ')
    Query = 'The intersection graph of paths in trees survey Graph'
    Query = Query.split()
    scores = bm25.bm25_score(Query)
    print(scores)
