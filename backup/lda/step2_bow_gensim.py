# -*- coding: utf-8 -*-
"""
Created on Sat Apr 16 23:17:19 2016

@author: limeng
"""

from gensim import corpora
from collections import defaultdict
import re
# import pickle
import mysql.connector as c

# 从document_t中读取信息
def fetch_docs():
    ids = []
    documents = []
    tags = []
    lat_list = []
    lng_list = []
    
    boring_line = set(range(20399, 20405))
    boring_line |= set(range(20937, 21155))
    boring_line |= set(range(21185, 21190))
    boring_line |= set(range(21473, 21482))
    boring_line |= set(range(21568, 21610))
    boring_line |= set(range(21677, 21683))
    boring_line |= set(range(21761, 21773))
    boring_line |= set(range(21886, 21909))
    boring_line |= set(range(21937, 21975))
    boring_line |= set(range(22002, 22206))
    boring_line |= set(range(22226, 22233))
    boring_line |= set(range(22268, 22274))
    boring_line |= set(range(22446, 22456))
    boring_line |= set(range(22976, 22990))
    boring_line |= set(range(23190, 23268))
    boring_line |= set(range(23682, 23870))
    boring_line |= set(range(24043, 24075))
    boring_line |= set(range(24691, 24825))
    boring_line |= set(range(24953, 24971))
    boring_line |= set(range(25074, 25088))
    boring_line |= set(range(26630, 28407))
    
    conn = c.connect(user='root', password='ictwsn', host='127.0.0.1', database='curiosity_lda')
    try:
        cursor = conn.cursor()
        # cursor.execute("select id, document from document_t")
        # cursor.execute("select id, description, tags from feed_t where iana = 'en' and tags<>''")
        cursor.execute("""
            select id, description, tags, lat, lng from feed_t 
            where iana = 'en' and tags<>'' and description <>'' and lat<>'' and lng<>''
        """)
        result = cursor.fetchall()
        for (idx, description, tag, lat, lng) in result:
            if idx in boring_line:
                continue
            ids.append(idx)
            documents.append(description)
            tags.append(tag)
            lat_list.append(float(lat))
            lng_list.append(float(lng))
    finally:
        conn.close()    
    return ids, documents, tags, lat_list, lng_list
    
# 数据集清洗：
# 超链接、无意义的词、只出现一次的词
def clean_dataset(documents):
    
    boring_words = """
        for will a an all of are is was be not and or can as but 
        from to in by on with at now 
        we you me our i it the this that these there any your my
        hour values average two 
        see more bfs test testing please 
        just using near love first 
        data information feed http https www twitter com
        """
    stoplist = set(boring_words.split())

    texts = []
    
    for doc in documents:
        doc = re.sub(r"http\S+", "", doc)
        doc = re.sub(r"\d+", "", doc)    
        doc = re.sub(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]', ' ', doc)
        wordlist = [w for w in doc.lower().split() if w not in stoplist and len(w)>1]
        texts.append(wordlist)

    frequency = defaultdict(int)
    for text in texts:
        for token in text:
            frequency[token] += 1
    texts = [[token for token in text if frequency[token] > 2] for text in texts]

    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    return corpus, dictionary

ids, documents, tags, lat, lng = fetch_docs()
print('Data fetched from database!')

corpus, dictionary = clean_dataset(documents)
corpus_tag, dictionary_tag = clean_dataset(tags)
print('Corpus creation done! len(dictionary) = ', len(dictionary))
# pickle.dump({'documents': documents, 'tags':tags}, open('objs.pickle','w'))
# print('Data dumped at objs.pickle')
dictionary.save_as_text('output/dict.dict')
corpora.mmcorpus.MmCorpus.serialize('output/dtm.mtx', corpus)

