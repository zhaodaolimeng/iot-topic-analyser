# -*- coding: utf-8 -*-
"""
(C) Mathieu Blondel - 2010
License: BSD 3 clause

Implementation of the collapsed Gibbs sampler for
Latent Dirichlet Allocation, as described in

Finding scientifc topics (Griffiths and Steyvers)

方法基于：
https://gist.github.com/mblondel/542786

尝试将时间属性加入到lda中，具体方法请参考文献：
Xuerui Wang, A. M. (2006). Topics over Time: A Non-Markov Continuous-Time 
Model of Topical Trends. KDD, 424–433.

"""

import numpy as np
from scipy.special import gammaln

from gensim import corpora
from collections import defaultdict
import re
import mysql.connector as c
import datetime

def sample_index(p):
    """
    Sample from the Multinomial distribution and return the sample index.
    """
    return np.random.multinomial(1,p).argmax()

def word_indices(vec):
    """
    Turn a document vector of size vocab_size to a sequence
    of word indices. The word indices are between 0 and
    vocab_size-1. The sequence length is equal to the document length.
    """
    for idx in vec.nonzero()[0]:
        for i in range(int(vec[idx])):
            yield idx

def log_multi_beta(alpha, K=None):
    """
    Logarithm of the multinomial beta function.
    """
    if K is None:
        # alpha is assumed to be a vector
        return np.sum(gammaln(alpha)) - gammaln(np.sum(alpha))
    else:
        # alpha is assumed to be a scalar
        return K * gammaln(alpha) - gammaln(K*alpha)

class LdaSampler(object):

    def __init__(self, n_topics, alpha=0.1, beta=0.1):
        """
        n_topics: desired number of topics
        alpha: a scalar (FIXME: accept vector of size n_topics)
        beta: a scalar (FIME: accept vector of size vocab_size)
        """
        self.n_topics = n_topics
        self.alpha = alpha
        self.beta = beta

    def _initialize(self, matrix, timestamp):
        """
        matrix是一个BoW，n_docs x vocab_size
        timestamp对应了每个文档的时间戳，每个时间戳是一个0到1之间的浮点
        """
        n_docs, vocab_size = matrix.shape
        # number of times document m and topic z co-occur
        self.nmz = np.zeros((n_docs, self.n_topics))
        # number of times topic z and word w co-occur
        self.nzw = np.zeros((self.n_topics, vocab_size)) # 
        self.nm = np.zeros(n_docs) # 每个文档的长度
        self.nz = np.zeros(self.n_topics) # 主题数目长度的一个数组，主题一共出现的数目？
        self.topics = {} # 文档中每个词对应的主题
        self.psi1 = np.ones(self.n_topics) # 时间beta分布的参数
        self.psi2 = np.ones(self.n_topics)
        self.time_doc = timestamp

        for m in range(n_docs):
            # i is a number between 0 and doc_length-1
            # w is a number between 0 and vocab_size-1
            for i, w in enumerate(word_indices(matrix[m, :])):
                # choose an arbitrary topic as first topic for word i
                z = np.random.randint(self.n_topics)
                self.nmz[m,z] += 1
                self.nm[m] += 1
                self.nzw[z,w] += 1
                self.nz[z] += 1
                self.topics[(m,i)] = z

    def _conditional_distribution(self, m, w, z):
        
        # Conditional distribution (vector of size n_topics).
        # 原始LDA为：p(z|z_, w)
        # TOT中的LDA为：p(z|z_, w, t)
        
        vocab_size = self.nzw.shape[1]
        left = (self.nmz[m,:] + self.alpha)
        mid = (self.nzw[:,w] + self.beta * vocab_size - 1)
        mid /= sum(self.nzw[:,w] + self.beta - 1)
        
        # print(m,w,z)
        # print(self.time_doc[m], self.psi1[z], self.psi2[z])
        
        # 这里将时间定义为beta分布上的采样
        right = ((1 - self.time_doc[m])**(self.psi1[z]-1)) * \
                (self.time_doc[m]**(self.psi2[z]-1)) / \
                np.random.beta(self.psi1[z], self.psi2[z]);
            
        p_z = left * mid * right;
        p_z /= np.sum(p_z)
        return p_z

    def loglikelihood(self):
        """
        Compute the likelihood that the model generated the data.
        """
        vocab_size = self.nzw.shape[1]
        n_docs = self.nmz.shape[0]
        lik = 0
        for z in range(self.n_topics):
            lik += log_multi_beta(self.nzw[z,:]+self.beta)
            lik -= log_multi_beta(self.beta, vocab_size)
        for m in range(n_docs):
            lik += log_multi_beta(self.nmz[m,:]+self.alpha)
            lik -= log_multi_beta(self.alpha, self.n_topics)
        return lik

    def phi(self):
        """
        Compute phi = p(w|z).
        """
        num = self.nzw + self.beta
        num /= np.sum(num, axis=1)[:, np.newaxis]
        return num

    def run(self, matrix, timestamp, maxiter=50):
        """
        Run the Gibbs sampler.
        """
        n_docs, vocab_size = matrix.shape
        self._initialize(matrix, timestamp)

        for it in range(maxiter):            
            for m in range(n_docs):
                # 对于每个文档m
                for i, w in enumerate(word_indices(matrix[m, :])):
                    # 对于文档m中的每个词
                    z = self.topics[(m,i)] # 获得词(m,i)的主题
                    
                    self.nmz[m,z] -= 1 # 文档m属于主题z的词的个数
                    self.nm[m] -= 1 # 文档的词的个数
                    self.nzw[z,w] -= 1 # 主题z中词w对应的计数
                    self.nz[z] -= 1 # 不同主题的总计数
                    
                    p_z = self._conditional_distribution(m, w, z) # p_z是Gibbs采样得到的分布
                    z = sample_index(p_z) # 从分布p_z中采样一个值作为词(m,i)的主题

                    self.nmz[m,z] += 1
                    self.nm[m] += 1
                    self.nzw[z,w] += 1
                    self.nz[z] += 1
                    
                    self.topics[(m,i)] = z # 文档m中的第i个词，将其主题设定为z

            """
            根据每个主题对应的时间
            更新每个主题与时间的beta函数的两个参数psi1和psi2
            更新时间beta分布的参数psi
            t_z: 主题是z的文档的时间的均值
            s_z: 主题是z的文档的时间的加权方差
            """
            for z in range(self.n_topics):
                t_z = np.sum(self.nmz[:, z] * self.time_doc[:]) / np.sum(self.nmz[:, z])
                left = self.nmz[:,z] / self.nm[:]
                left[np.isnan(left)] = 0
                left /= np.sum(left)
                right = (self.time_doc[:] - t_z) ** 2
                s_z = np.sum(left * right)
                """
                print("=======")
                print(np.isnan(num).any())
                print(np.isnan(div).any())
                print(np.sum(num * div))
                print(t_z)
                print(s_z)
                """
                self.psi1[z] = t_z*(t_z*(1-t_z)/(s_z*s_z)-1)
                self.psi2[z] = (1-t_z)*(t_z*(1-t_z)/(s_z*s_z)-1)
            
            print(self.psi1)
            print(self.psi2)
            # print(0/0)
            yield self.phi()


"""
主函数入口
"""
if __name__ == "__main__":

    # 从document_t中读取信息
    def fetch_docs():
        documents = []
        tags = []
        timetable = []
        conn = c.connect(user='root', password='ictwsn', host='127.0.0.1', database='curiosity_lda')
        try:
            cursor = conn.cursor()
            cursor.execute("""
                select id, description, tags, created 
                from feed_t where iana = 'en' and tags<>''
            """)
            result = cursor.fetchall()
            for (id, description, tag, createdtime) in result:
                documents.append(description)
                tags.append(tag)
                timetable.append((createdtime - datetime.datetime(1970,1,1)).total_seconds())
        finally:
            conn.close()    
        return documents, tags, timetable
        
    # 数据集清洗：
    # 超链接、无意义的词、只出现一次的词
    def clean_dataset(documents):
        
        for doc in documents:
            doc = re.sub(r"http\S+", "", doc);
        
        bad_words = """for will a an all of are is was be not and or can 
            from to in by on with at now 
            we me our i it the this that these any your my 
            0 1 2 3 24 hour values average two s h 
            see more bfs test testing please 
            data information feed http https www twitter com"""
        stoplist = set(bad_words.split())
        
        texts = [[word for word 
                in re.sub(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]', ' ', document.lower()).split()
                if word not in stoplist]
                for document in documents]
    
        frequency = defaultdict(int)
        for text in texts:
            for token in text:
                frequency[token] += 1
        texts = [[token for token in text if frequency[token] > 1] for text in texts]
    
        dictionary = corpora.Dictionary(texts)
        corpus = [dictionary.doc2bow(text) for text in texts]
        return corpus, dictionary
    
    documents, tags, timetable = fetch_docs()
    corpus, dictionary = clean_dataset(documents)
    
    # 将corpus改为BoW的形式
    # max_doc_num = max([pair[0] for pair in l] for l in corpus)[0]
    
    matrix = np.zeros((len(corpus), len(dictionary) + 1))

    m_x = 0;
    for row in corpus:
        for item in row:
            matrix[m_x][item[0]] = item[1]
        m_x += 1;
    timestamp = np.array(timetable)
    timestamp = (timestamp - min(timestamp))/(max(timestamp) - min(timestamp))
    
    N_TOPICS = 10
    sampler = LdaSampler(N_TOPICS)

    for it, phi in enumerate(sampler.run(matrix, timestamp)):
        print("Iteration", it)
        print("Likelihood", sampler.loglikelihood())



