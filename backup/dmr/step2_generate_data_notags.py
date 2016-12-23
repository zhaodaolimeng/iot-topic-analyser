# -*- coding: utf-8 -*-
"""
Created on Sat Sep 24 17:29:52 2016

@author: limeng
"""

import re
import codecs
import pickle
import mysql.connector as c


FEEDID_FILE = 'output/feedid.txt'
TEXTS_FILE = 'output/texts.txt'
TEXTS_NOTAG_FILE = 'output_notags/texts.txt'


conn = c.connect(user='root', password='ictwsn', 
               host='127.0.0.1', database='curiosity_v3')
cursor = conn.cursor()
cursor.execute("""
    select id, tags from feed_t where length(tags) > 0
""", conn)
feed_list = []
with codecs.open(FEEDID_FILE, 'r') as f:
    feed_list = f.read().splitlines()
    
# 从db中的feed_t读取全部(feedid, tags)
feed_set = set(feed_list)
tags_map = dict()
for (idx, tags) in cursor.fetchall():
    if str(idx) not in feed_set:
        continue
    tags = tags.replace('\n', ' ')
    tags = re.sub(r"http\S+", "", tags)
    tags = re.sub(r"\d+", "", tags)
    tags = re.sub(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]', ' ', tags)
    tlist = [w for w in tags.lower().split() if len(w)>1]
    tset = set([x for x in tlist if x is not ' '])
    tags_map[idx] = tset

# 从texts.txt中读取(feedid, doc)
# 由于step1是将tags合并到doc再进行翻译，所以要先剔除tags的影响
text_list = []
fout = codecs.open(TEXTS_NOTAG_FILE, 'w')
with codecs.open(TEXTS_FILE, 'rb') as f:
    text_list = f.read().splitlines() 
    for i in range(len(text_list)):
        feedid = int(feed_list[i])
        line = text_list[i]
        tlist = line.decode('ascii').split(' ')
        if feedid in tags_map:
            word_list = [x for x in tlist if x not in tags_map[feedid]]
        else:
            word_list = [x for x in tlist]
        fout.write(' '.join(word_list) + '\n')

all_dict = dict()
all_dict['tags_map'] = tags_map
all_dict['text_list'] = text_list
all_dict['feed_list'] = feed_list
pickle.dump(all_dict, open('step2_generate_data_notags.pickle', 'wb'))
