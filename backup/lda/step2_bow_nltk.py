# -*- coding: utf-8 -*-

# 1. Read descriptions from feed_t
# 2. Generate desc_map(doc_id, desc_list) and xively_set
# 3. Generate bag of words based on desc_map and xively_set

import mysql.connector
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import words
from nltk.corpus import wordnet
from nltk.corpus.reader import NOUN
from nltk.corpus import stopwords

conn = mysql.connector.connect(user='root',
                               password='ictwsn',
                               host='127.0.0.1',
                               database='curiosity_lda')

tokenizer = RegexpTokenizer(r'\w+')
english_words = set(words.words())
# english_words = set(list(wordnet.synsets(wordnet.NOUN)))
stop_words = set(stopwords.words('english'))
meaningless_words = set(['san', 'de', 'much', 
                 'dose', 'id', 'every',
                 'data', 'code', 'real',
                 'always', 'love', 'feed',
                 'first', 'via', 'used',
                 'get', 'use', 'may',
                 'see', 'twitter', 'follow',
                 'design', 'technology', 'developer',
                 'work', 'information', 'time',
                 'level', 'per', 'number',
                 'stopped', 'making',
                 'twitter', 'www',
                 'hour','h','average','two','one','day','m'])
                 
bad_words = set(['are', 'or', 'in', 'i', 'a',
                 'at', 'no', 'it', 'will', 'be',
                 'can', 's', 'de', 'now' ,'here', 'as'])

# 'd', 'h', 'm' are very much likely to be extended to 'day', 'hour', 'minutes'
# target_words = english_words - stop_words - bad_words
bad_words.union(stop_words)
bad_words.union(meaningless_words)

desc_map = dict()
xively_word2idx = dict()
xively_idx2word = []
xively_set = set()

# Words clean
try:
    cursor = conn.cursor()
    cursor.execute("""
       select id,rawtext from feed_t where iana='en' and rawtext <>''
    """)
    result = cursor.fetchall()
    for (id,description) in result:        
        raw_list = tokenizer.tokenize(description.lower())
        word_list = [i for i in raw_list 
            if wordnet.synsets(i, NOUN) and i not in bad_words and not i.isdigit()]
        if len(word_list)== 0:
            continue
        for word in word_list:
            xively_set.add(word)
        desc_map[str(id)] = word_list

finally:
    conn.close()
print('Words clean done!')

# Make a "word-to-index" mapping
xively_idx2word = [0 for x in range(len(xively_set))]
for idx_word, word in enumerate(xively_set):
    xively_word2idx[word] = idx_word
    xively_idx2word[idx_word] = word
    idx_word += 1
print('Words to index done!')

# create bag of words of xively descriptions
id_list = [0 for x in range(len(desc_map))]
bag_of_words = [[0 for x in range(len(xively_set))] for y in range(len(desc_map))]
print('Bag of words allocation done!')

for idx_word, (id, word_list) in enumerate(desc_map.iteritems()):
    id_list[idx_word] = id
    for word in word_list:
        bag_of_words[idx_word][xively_word2idx[word]] += 1
    idx_word += 1
print('Bag of words computation done!')

# create words vector space
corpus = []
for doc in bag_of_words:
    newlist = []
    for idx, words_cnt in enumerate(doc):
        if words_cnt != 0:
            newlist.append((idx, words_cnt))
    corpus.append(newlist)
print('Words vector computation done!')

# pickle.dump(id_list, open("id_list.p", "wb" ))
# pickle.dump(bag_of_words, open("bag_of_words.p", "wb"))
