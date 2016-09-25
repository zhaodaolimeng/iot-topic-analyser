# -*- coding: utf-8 -*-
"""
Created on Sun Sep 11 11:34:38 2016

@author: limeng
"""

'''
数据读取和预处理
========
1. 从数据库中读取所有包含文本信息的标志位
2. 将这些文本进行拼接
3. 调用baidu翻译
4. 之后进行正则匹配清洗、去除无意义的词

'''

import re
import mysql.connector as c
import collections
import codecs
import time

BAD_RECORD = 'badrecords.txt'
STOP_WORDS = 'stopwords.txt'
FEATURES = 'output/features.txt'
TEXT = 'output/texts.txt'
FEEDID = 'output/feedid.txt'

MIN_TERM_LEN = 3

def clean_and_concat(str_list):
    ret = ''
    for s in str_list:
        if s is None:
            ret += ''
        else:
            ret += str(s) + '. '
    return ret
    
# 读取数据
def load_data():
    conn = c.connect(user='root', password='ictwsn', 
                 host='127.0.0.1', database='curiosity_v3')
                 
    print('Start to fetch from db ... ')
    cursor = conn.cursor()
    cursor.execute("""
        select
            feedid, doc, created, lat, lng
        from feed_translate_t where length(doc) > 0
    """, c.connect(user='root', password='ictwsn', 
                   host='127.0.0.1', database='curiosity_lda'))

    result = cursor.fetchall()
    boring_line = set()
    with open(BAD_RECORD, 'r') as f:
        for line in f.read().splitlines():
            mylist = line.split(',')
            boring_line |= set(range(int(mylist[0]), int(mylist[1])))
    
    feed_result = []
    for (feedid, doc, created, lat, lng) in result:

        if lat is None or lng is None:
            continue
        try:
            doc.encode('ascii')
        except UnicodeEncodeError:
            print("it was not a ascii-encoded unicode string")
            continue
        
        feed = dict()
        # 直接在这里进行拼接
        feed['feedid'] = feedid
        feed['doc'] = doc
        feed['created'] = created
        feed['lat'] = float(lat)
        feed['lng'] = float(lng)
        feed_result.append(feed)
        
    print('Data fetched from database!')
    return feed_result


def concat_and_clean(feed_result):
    with open(STOP_WORDS, 'r') as f:
        stoplist = set(f.read().split())
        
    # 使用正则匹配，剔除部分数据，同时构造BoW模型
    regular_word = collections.defaultdict(int)
    for feed in feed_result:
        doc = feed['doc']
        doc = doc.replace('\n', ' ')
        doc = re.sub(r"http\S+", "", doc)
        doc = re.sub(r"\d+", "", doc)
        doc = re.sub(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]', ' ', doc)
        wordlist = [w for w in doc.lower().split() if w not in stoplist and len(w)>1]
        for w in wordlist:
            regular_word[w] += 1
        feed['doc'] = ' '.join(wordlist)
    
    print('Total Word Count = ', len([w for w in regular_word if regular_word[w]>3]))
    
    # 剔除过短的词
    ret = []
    for feed in feed_result:
        wordlist =[ w for w in feed['doc'].split() if regular_word[w]>3]
        feed['desc'] = ' '.join(wordlist)
        if len(wordlist)>1:
            ret.append(feed)
    
    return ret


if __name__ == "__main__":    
    docs = load_data()
    selected_docs = concat_and_clean(docs)
    
    # 生成DMR的地点\时间特征向量
    
    ff = codecs.open(FEATURES, 'w', 'utf-8')
    ft = codecs.open(TEXT, 'w', 'utf-8')
    fd = codecs.open(FEEDID, 'w', 'utf-8')
            
    for feed in selected_docs:
        if not feed['desc']:
            continue
        
        lat = int((90+feed['lat']) / 10)
        lng = int((180+feed['lng']) / 10)
        epoch = int(time.mktime(time.strptime('2007.01.01', '%Y.%m.%d')))
        create_time = int(feed['created'].timestamp() - epoch)
        lb_time = str(int(create_time / (3600*24*30*6)))

        ff.write('lat=' + str(lat) 
            + ' lng=' + str(lng) 
            + ' lbtime=' + lb_time+'\n')
        ft.write(feed['desc']+'\n')
        fd.write(str(feed['feedid'])+'\n')
    
    print('Transform lat lng to location label')





