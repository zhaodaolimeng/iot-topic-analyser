# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 00:16:54 2016

@author: limeng
"""


'''
时序数据特征提取

从数据库中一次读出后将所有的都进行计算，原则是尽可能多地提取特征
选取了不同的时间窗，但不保证所有的时间窗都有对应的数据：
'1minute', '1hour', '1week', '1day', '1month', '1year'
特征包括：均值、方差、最大值、最小值
'''

import mysql.connector as c

conn = c.connect(user='root', password='ictwsn', host='127.0.0.1', database='curiosity_v1')

duration_map = {
    '1minute': 60, 
    '1hour': 60*60, 
    '1day': 24*60*60,
    '1week': 7*24*60*60,
    '1month': 30*24*60*60,
    '1year': 365*24*60*60 }

feature_map = {
    '1minute': 0, 
    '1hour': 4, 
    '1week': 8,
    '1day': 12,
    '1month': 16,
    '1year': 20 }

# 使用两层结构存储结果
# {'feedid' : {'datastreamid' : [feature_list]}}
feed_dict = dict()
DIMENSION = 24 # 24个特征维度

try:
    
    print('Start to load data ... ')
    cursor = conn.cursor()
    cursor.execute('''
        select feedid,datastreamid,duration,time_at,val
        from datapoint_t 
        order by feedid,datastreamid,duration 
    ''')
    
    print('Data Load Done!')
    
    cur_feedid = ''
    cur_datastreamid = ''
    cur_duration = ''
    
    val_tlist = []
    feature_list = [0.0]*DIMENSION  
    datastream_dict = dict()
    resultlist = cursor.fetchmany(1000)
    
    while len(resultlist) != 0:
        print('In resultlist ... ')
        for (feedid,datastreamid,duration,time_at,val) in resultlist:
            
            val_tlist.append(val)
            if cur_feedid != feedid or cur_datastreamid != datastreamid or cur_duration != duration:
                if cur_feedid == '': 
                    # 第一组数据
                    datastream_dict = dict()
                    cur_feedid = feedid
                else:
                    # 计算val_tlist中的均值和方差，按照当前的duration进行赋值
                    # 注意：可能出现数据破损
                    s = 0.0
                    m = 0.0
                    maxv = 0.0
                    minv = 0.0
                    tlist = []
                    for v in val_tlist:
                        try:
                            tlist.append(float(v))
                        except ValueError:
                            continue
                        
                    if len(tlist) != 0:
                        m = sum(tlist) / len(tlist)
                        maxv = max(tlist)
                        minv = min(tlist)
                        for v in tlist:
                            s += (v-m)**2
                        s /= len(tlist)
                    
                    feature_list[feature_map[duration]] = m
                    feature_list[feature_map[duration] + 1] = s
                    feature_list[feature_map[duration] + 2] = maxv
                    feature_list[feature_map[duration] + 3] = minv
                    cur_duration = duration
                    
                    if cur_datastreamid != datastreamid:
                        val_tlist = []
                        datastream_dict[cur_datastreamid] = feature_list
                        cur_datastreamid = datastreamid
                        feature_list = [0.0]*DIMENSION
                    
                    if cur_feedid != feedid:
                        # 一个完整的feedid
                        feed_dict[cur_feedid] = datastream_dict
                        datastream_dict = dict()
                        cur_feedid = feedid
                        print('Feature for feedid = ' + str(feedid) + ' Done!')
                
        resultlist = cursor.fetchmany(1000)
        
finally:
    conn.close()

print('Feature Extraction Done!')

