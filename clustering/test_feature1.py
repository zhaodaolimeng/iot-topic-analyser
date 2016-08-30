# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 08:58:53 2016

@author: limeng
"""

# 尝试使用DBSCAN方法
# 抽取小波系数、不同窗口大小的均值作为特征

# 从数据库中读取
import mysql.connector as c
import numpy as np
from scipy import signal

conn = c.connect(user='root', password='ictwsn', host='127.0.0.1', database='curiosity_v1')

time_dict = {
    '1minute': 60, 
    '1hour': 60*60, 
    '1day': 24*60*60,
    '1month': 30*24*60*60,
    '1year': 365*24*60*60 }

duration_map = {
    '1minute': 0, 
    '1hour': 2, 
    '1day': 4,
    '1month': 6,
    '1year': 8 }

'''
每个feedid和datastreamid对应的序列特征
'''

feature_feed = []
feature_datastream = []
features = []  # 共10位，分别对应5类时间窗口，每个窗口具有两个特征

try:
    cursor = conn.cursor()

    # 读取datastreamid列表
    cursor.execute('''
        select feedid,datastreamid
        from datapoint_t group by feedid,datastreamid
    ''')
    print('Data read done!')
    
    for (feedid, datastreamid) in cursor.fetchall():
        
        cursor.execute('''
            select feedid,datastreamid,duration
            from datapoint_t
            where 
                datapoint_t.feedid = %s and 
                datapoint_t.datastreamid = %s 
            group by duration
        ''', (feedid, datastreamid))
        
        # 对于每个时间窗口
        feature_list = [0]*10
        for (feedid, datastreamid, duration) in cursor.fetchall():
            cursor.execute('''
                select feedid,datastreamid,unix_timestamp(time_at) as timeat,duration,val 
                from datapoint_t
                where 
                    datapoint_t.feedid = %s and 
                    datapoint_t.datastreamid = %s and 
                    datapoint_t.duration = %s
            ''', (feedid, datastreamid,duration))
        
            result = cursor.fetchall()
            timelist = []
            vallist = [] # 时间戳与数值
            
            # 获取每个序列的datapoints
            for (feedid, datastreamid, timeat, duration, val) in result:
                timelist.append(timeat)
                vallist.append(val)
            
            # 抽取特征，均值和方差
            mval = 0
            sval = 0
            if isinstance(vallist[0], str):
                continue
            mval = sum(vallist)
            mval /= len(vallist)
            for i in range(0, len(timelist)):
                sval += (vallist[i] - mval)**2
            sval /= len(vallist)
            feature_list[duration_map[duration]] = mval
            feature_list[duration_map[duration] + 1] = sval
            
        feature_feed.append(feedid)
        feature_datastream.append(datastreamid)
        features.append(feature_list)
        print("feedid="+str(feedid)+", datastreamid="+str(datastreamid)+", DONE!")
        
finally:
    conn.close()

print('Feature Extraction Done!')




