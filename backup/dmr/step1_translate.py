# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 09:40:05 2016

@author: limeng
"""

import mysql.connector as c
import utils.translator as lang
import pickle
import functools

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

        q = ''
        for s in doclist:
            if s is None:
                q += ''
            else:
                q += str(s) + '. '

        # q = functools.reduce(lambda x,y: str(x)+str(y) if y is not None else '', doclist)
        
        doc = lang.baidu_translate(q)
        if len(doc) == 0:
            continue
        cursor.execute('update feed_translate_t set doc = %s where feedid = %s', (doc, feedid))
        conn.commit()
        
    return feed_result
    

feed_result = translate_docs()
print('Start to dump data!')
pickle.dump(feed_result, open("step1_translate.pickle", "wb"))
print('Raw Data Done!')
