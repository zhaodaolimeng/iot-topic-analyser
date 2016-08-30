# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 22:18:20 2016

@author: limeng
"""

import re
import mysql.connector as c
import collections
import codecs
import time

BAD_RECORD = 'badrecords.txt'
STOP_WORDS = 'stopwords.txt'
FEATURES = 'output/features.txt'
TEXT = 'output/texts.txt'

# 从document_t中读取信息
feed_result = []
boring_line = set()
with open(BAD_RECORD, 'r') as f:
    for line in f.read().splitlines():
        mylist = line.split(',')
        boring_line |= set(range(int(mylist[0]), int(mylist[1])))
with open(STOP_WORDS, 'r') as f:
    stoplist = set(f.read().split())

conn = c.connect(user='root', password='ictwsn', host='127.0.0.1', database='curiosity_lda')
try:
    cursor = conn.cursor()
    cursor.execute("""
        select id, description, tags, lat, lng, created from feed_t 
        where iana = 'en' and tags<>'' and description <>'' and lat<>'' and lng<>''
    """)
    result = cursor.fetchall()
    for (idx, doc, tag, lat, lng, created) in result:
        if idx in boring_line:
            continue
        feed = dict()
        feed['ids'] = idx
        feed['desc'] = doc
        feed['tag'] = tag
        feed['lat'] = float(lat)
        feed['lng'] = float(lng)
        feed['created'] = created
        feed_result.append(feed)
finally:
    conn.close()

print('Data fetched from database!')

regular_word = collections.defaultdict(int)
for feed in feed_result:
    doc = feed['desc']
    doc = doc.replace('\n', ' ')
    doc = re.sub(r"http\S+", "", doc)
    doc = re.sub(r"\d+", "", doc)
    doc = re.sub(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]', ' ', doc)
    wordlist = [w for w in doc.lower().split() if w not in stoplist and len(w)>1]
    for w in wordlist:
        regular_word[w] += 1
    feed['desc'] = ' '.join(wordlist)

print('Total Word Count = ', len([w for w in regular_word if regular_word[w]>3]))

ret = []
for feed in feed_result:
    wordlist =[ w for w in feed['desc'].split() if regular_word[w]>3]
    feed['desc'] = ' '.join(wordlist)
    if len(wordlist)>1:
        ret.append(feed)

# 添加地点\时间标签
#ff = codecs.open(FEATURES, 'w', 'utf-8')
#ft = codecs.open(TEXT, 'w', 'utf-8')

with codecs.open(FEATURES, 'w', 'utf-8') as ff:
    with codecs.open(TEXT, 'w', 'utf-8') as ft:
        for feed in ret:
            if not feed['desc']:
                continue
            lat = int((90+feed['lat']) / 5)
            lng = int((180+feed['lng']) / 5)
            lb_loc = '_' + str(lat) + '_' + str(lng)
            
            epoch = int(time.mktime(time.strptime('2007.01.01', '%Y.%m.%d')))
            create_time = int(feed['created'].timestamp() - epoch)
            lb_time = str(int(create_time / (3600*24*30*6)))
            
            ff.write('lbloc' + lb_loc + ' lbtime=' + lb_time+'\n')
            ft.write(feed['desc']+'\n')

print('Transform lat lng to location label')
