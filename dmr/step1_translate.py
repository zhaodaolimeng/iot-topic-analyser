# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 09:40:05 2016

@author: limeng
"""

import mysql.connector as c
import hashlib
import time
import requests
import langid
import json
import pickle

BAD_RECORD = 'badrecords.txt'
STOP_WORDS = 'stopwords.txt'
FEATURES = 'output/features.txt'
TEXT = 'output/texts.txt'
MIN_TERM_LEN = 3

'''
设备描述文件翻译
===============
Xively平台上的设备描述文件可能由不同的语言构成，这里统一转换成英文以便处理。
对应的数据库表为：

create table feed_translate_t
select
	t0.feedid, t0.ds_list, t0.tags_list, 
	description, tags, device_name, title, 
	created, lat, lng
from feed_t, (
	select
		feedid,
		group_concat(streamid separator ',') as ds_list,
		group_concat(tags separator ',') as tags_list
	from datastream_t group by feedid
) as t0 where feed_t.id = t0.feedid;

alter table feed_translate_t add column `doc` text after feedid;
alter table feed_translate_t add primary key(feedid);
select * from feed_translate_t
'''


def translate_docs():
    conn = c.connect(user='root', password='ictwsn', 
                 host='127.0.0.1', database='curiosity_v3')
                 
    print('Start to fetch from db ... ')
    cursor = conn.cursor()
    cursor.execute("""
        select
            feedid, doc, ds_list, tags_list, 
            description, tags, device_name, title, created, lat, lng
        from feed_translate_t;
    """, conn)

    result = cursor.fetchall()
    boring_line = set()
    with open(BAD_RECORD, 'r') as f:
        for line in f.read().splitlines():
            mylist = line.split(',')
            boring_line |= set(range(int(mylist[0]), int(mylist[1])))
    
    feed_result = []
    for (feedid, doc, ds_list, tags_list,
         description, tags, device_name, title, 
         created, lat, lng) in result:

#        if feedid <= 66139:
#            continue

        if lat is None or lng is None:
            continue

        # 直接在这里进行拼接
        # 测试时需要将tags的内容进行剥离
        doclist = [description, tags, device_name, title, ds_list, tags_list]
        print('Translating feedid = ' + str(feedid))
        print('==========================')
        
        doc = concat_and_translate(doclist)
        if len(doc) == 0:
            continue
        cursor.execute('update feed_translate_t set doc = %s where feedid = %s', (doc, feedid))
        conn.commit()
        
    return feed_result
    

def concat_and_translate(str_list):
    q = ''
    appid = '20160901000027920'
    secretKey = 'pCa6vXL65ZddoC1cinrk'
    salt = 35000
    
    for s in str_list:
        if s is None:
            q += ''
        else:
            q += str(s) + '. '
            
    # 检查是否是英文，如果不是英文则使用百度翻译
    iana, _ = langid.classify(q)
    if iana == 'en':
        return q
    ret = ''
    
    while len(q) > 0:
        input_str = ''
        if len(q) > 1500:
            input_str = q[0:1500]
            q = q[1500:]
        else:
            input_str = q
            q = ''
        
        sign = (appid + input_str + str(salt) + secretKey).encode('utf-8')
        m1 = hashlib.md5()
        m1.update(sign)
        sign = m1.hexdigest()
        
        data={
            'appid': appid, 
            'q': input_str, 
            'from': 'auto',
            'to': 'en',
            'salt': salt,
            'sign': sign
        }
        r = requests.post('http://api.fanyi.baidu.com/api/trans/vip/translate', data)
        data = json.loads(r.text)
        
        # 某些内容可能出现无法翻译
        try:
            ret += data['trans_result'][0]['dst'] 
        except:
            return ''
        time.sleep(1)
    
    print('Translation = ' + ret)    
    return ret

feed_result = translate_docs()
print('Start to dump data!')
pickle.dump(feed_result, open("step1_translate.pickle", "wb"))
print('Raw Data Done!')
