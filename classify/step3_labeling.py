# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 15:13:47 2016

@author: limeng
"""

'''
导出数据到数据库，并进行标注
create table datastream_label_t(
	feedid long,
	datastreamid long,
	label varchar(100)
);
'''

import pickle
import mysql.connector as c

xively_series = pickle.load(open("feature2.pickle", "rb"))


conn = c.connect(user='root', password='ictwsn', 
                     host='127.0.0.1', database='curiosity_v3')
cursor = conn.cursor()

try:
    for L in xively_series['labels']:
        f,d = L.split(',')
        cursor.execute('''
            insert into dsl_temp(feedid, datastreamid) 
            values (%s,%s)
        ''', (f, d))
        conn.commit()
    
    conn.close()
except Exception as e:
   print(e)

