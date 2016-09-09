# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 19:06:44 2016

@author: limeng
"""
import mysql.connector as c
import pandas as pd
import numpy as np
import os
import shutil

'''
选择部分数据进行可视化
=====================
'''

db = c.connect(user='root', password='ictwsn', 
                     host='127.0.0.1', database='curiosity_v3')

## feedid = 35485 and datastreamid = 0
#df = pd.read_sql('''
#    select time_at, val from datapoint_t 
#    where feedid = %(f)s and datastreamid = %(d)s
#''', db, params = {'f':19774, 'd':10})
#
#df['time_at'] = df.time_at.astype(np.int64)
#df['val'] = df.val.astype(np.float)
#df.plot(x='time_at',y='val')

# 选取不同的种类
types = pd.read_sql('''
    select labels, count(*) as cnt 
    from datastream_labeled_t where labels is not null
    group by labels order by cnt
''', db)

for _, row in types.iterrows():
    label = str(row['labels'])
    print("Label = " + label)
    
    dir_path = 'output/' + label
    
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)
    
    serie_entry = pd.read_sql('''
        select feedid, datastreamid 
        from datastream_labeled_t where labels = %(label)s
    ''', db, params = {'label': label})
    
    for _, row0 in serie_entry.iterrows():
        de = pd.read_sql('''
            select * from datapoint_t 
            where feedid = %(f)s and datastreamid = %(d)s
        ''', db, params = {'f': row0['feedid'], 
                           'd' : row0['datastreamid']})
        
        de['time_at'] = de.time_at.astype(np.int64)
        de['val'] = de.val.astype(np.float)
        
        filepath = 'output/' + str(label) + '/' + \
                str(row0['feedid']) + '-' + str(row0['datastreamid'] + '.png')
        print('Plot at path = ' + filepath)
        
        ax = de.plot(x='time_at',y='val')
        fig = ax.get_figure()
        fig.savefig(filepath)
        
db.close()

