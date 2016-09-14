# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 00:16:54 2016
@author: limeng

时序数据特征提取:
从数据库中一次读出后将所有的都进行计算，原则是尽可能多地提取特征
选取了不同的时间窗，但不保证所有的时间窗都有对应的数据：
'1minute', '1hour', '1week', '1day', '1month', '1year'
特征包括：均值、方差、最大值、最小值
"""

import mysql.connector as c
import numpy as np
import pickle

conn = c.connect(user='root', password='ictwsn', 
                 host='127.0.0.1', database='curiosity_v2')

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

##############################################################################
# 从数据库中读取特征，直接计算均值和方差等24维数据
# feed_dict的存储结构为：{'feedid' : {'datastreamid' : [feature_list]}}

def read_data_from_db():
    feed_dict = dict()
    DIMENSION = 24 # 24个特征维度
    try:
        cursor = conn.cursor()
        cursor.execute('''
            select feedid,datastreamid,duration,time_at,val
            from datapoint_daily_t order by feedid,datastreamid,duration 
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
                if cur_feedid != feedid or cur_datastreamid != datastreamid \
                    or cur_duration != duration:
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
                            print('Feedid = ' + str(feedid) + ' Done!')
                    
            resultlist = cursor.fetchmany(1000)
            
    finally:
        conn.close()
    return feed_dict

##############################################################################
# 补全缺失

def fix_blank_value(feed_dict):
    dead_feed = [] # 存储即将删除的数据
    dead_ds = []
    for feed_key, datastream_dict in feed_dict.items():
        for ds_key, plist in datastream_dict.items():
            m = 0.0
            s = 0.0
            maxv = 0.0
            minv = 0.0
            cnt = 0
            length = int(len(plist)/4)
            for i in range(0, length):
                if plist[i*4] != 0.0:
                    m += plist[i*4]
                    s += plist[i*4 + 1]
                    maxv += plist[i*4 + 2]
                    minv += plist[i*4 + 3]
                    cnt += 1
            if m == 0.0 or maxv >= 10**10 or minv<=-10**10:
                dead_feed.append(feed_key)
                dead_ds.append(ds_key)
            else:
                for i in range(0, length):
                    if plist[i*4] == 0.0:
                        plist[i*4] = m/cnt
                        plist[i*4 + 1] = s/cnt 
                        # 这里意义不明，按理来说时间间隔应该会影响但没办法
                        plist[i*4 + 2] = maxv/cnt
                        plist[i*4 + 3] = minv/cnt
    
    for i in range(len(dead_feed)):
        feed_dict[dead_feed[i]].pop(dead_ds[i])
        if len(feed_dict[dead_feed[i]]) == 0:
            feed_dict.pop(dead_feed[i])
    return feed_dict

##############################################################################
# 放缩，改变数据倍率
    
def magic(x):
    magic_block = 1
    if x>magic_block:
        return magic_block + np.log(x)
    elif x<=1 and x>=-magic_block:
        return x
    else:
        return -magic_block - np.log(-x)

def scale_transform(feed_dict):
    labels_true = []
    features = []
    for feed_key, datastream_dict in feed_dict.items():
        for ds_key, plist in datastream_dict.items():
            if np.isnan(plist).any():
                continue
            labels_true.append(str(feed_key) + ',' + str(ds_key))
            features.append(plist)
    for i in range(len(features)):
        for j in range(len(features[0])):
            features[i][j] = magic(features[i][j]) # 规范化
    return labels_true, features

##############################################################################
# main

print('Loading data from database ... ')
feed_dict = read_data_from_db()

print('Fixing blank data ... ')
feed_dict = fix_blank_value(feed_dict)
pickle.dump(feed_dict, open( "raw.pickle", "wb" ))

print('Add log ... ')
labels_true, features = scale_transform(feed_dict)
xively_series = dict()
xively_series['X'] = features
xively_series['labels'] = labels_true

print('Start to dump data!')
pickle.dump(xively_series, open( "step1_feature1.pickle", "wb" ))
print('Raw Data Done!')

