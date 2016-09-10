# -*- coding: utf-8 -*-
"""
Created on Sun Sep  4 10:58:29 2016
@author: limeng
"""

import pickle
import numpy as np
import datetime as dt
import mysql.connector as c
from scipy.interpolate import interp1d

# 虽然从2016/08/01开始，但已经确保所有设备的部署超过1年时间
START_TIMESTAMP = dt.datetime.strptime("2016/08/01", "%Y/%m/%d").timestamp()
conn = c.connect(user='root', password='ictwsn', 
                     host='127.0.0.1', database='curiosity_v3')
                     
'''
值域变换
'''
def magic(x):
    if x>1:
        return 1 + np.log(x)
    elif x<=1 and x>=-1:
        return x
    else:
        return -1 - np.log(-x)

'''
数据清理
=============
找到有效数据，尽可能通过地理经度，拼接成具有一天趋势的序列
'''
def build_feature(plist):
    tlist = [] # 以分钟为单位
    vlist = []
    timezone = 0

    for time, val, lng in plist:
        try:
            timezone = int((float(lng) + 7.5) / 15)
            tlist.append((time.timestamp() - START_TIMESTAMP)/60)
            vlist.append(float(val))
        except (ValueError, TypeError):
            return []
    
    # 使用时区数据进行拼接，对于timezone>0，序列值整体后移
    t_tail = []
    t_head = []
    v_tail = []
    v_head = []
    if timezone > 0:
        for i in range(len(tlist)):
            if tlist[i] > 1440 - timezone*60:
                t_tail.append(tlist[i] - 1440 + timezone*60)
                v_tail.append(vlist[i])
            else:
                t_head.append(tlist[i] + timezone*60)
                v_head.append(vlist[i])
    else:
        for i in range(len(tlist)):
            if tlist[i] < -timezone*60:
                t_tail.append(tlist[i] + 1440 + timezone*60)
                v_tail.append(vlist[i])
            else:
                t_head.append(tlist[i] + timezone*60)
                v_head.append(vlist[i])
                
    # 在list的最前和最后加入一个点
    tlist = [0] + t_tail + t_head + [1440]
    vlist = [v_tail[0]] + v_tail + v_head + [v_head[-1]]
    
    '''
    # 如果时间间隔过大，或开始时间和结束时间有问题
    # 原本计划直接删除该条数据
    '''
    # 使用插值方法进行数据清洗，之后进行采样
    f = interp1d(tlist, vlist)
    samples = [] # 从0时刻开始，每隔10分钟一个样点
    cur_time = 0
    samples.append(magic(vlist[0]))
    while cur_time < 1440:
        cur_time += 10
        samples.append(magic(f(cur_time)))
    
    return samples


def get_feeddict():
    
    FETCH_SCALE = 100000
    feed_raw_dict = dict()
    
    # 需要使用时区信息，将每天的数据进行对齐，才能正常分析序列特征
    cursor = conn.cursor()
    cursor.execute('select id, lng from feed_t')
    
    lng_dict = dict()
    for (id, lng) in cursor.fetchall():
        lng_dict[id] = lng
        
    print('Starting to fetch!')
    cursor.execute('''
        select feedid, datastreamid, time_at, val from datapoint_daily_t
    ''')
    
    resultlist = cursor.fetchmany(FETCH_SCALE)
    print('Fetch done!')
    plist = []
    
    old_datastreamid = ''
    old_feedid = ''
    ds_raw_dict = dict()
    
    while len(resultlist) != 0:
        for (feedid, datastreamid, time_at, val) in resultlist:
            if old_feedid != '' and \
                (old_datastreamid != datastreamid or feedid != old_feedid) :
                
                print('Build features for feedid = ' + str(feedid) + \
                    ' datastreamid = ' + str(datastreamid))
                rawlist, binlist = build_feature(plist)
                print('Feature done! size = ' + str(len(binlist)))
                
                plist = []
                if len(binlist) != 0:
                    ds_raw_dict[old_datastreamid] = rawlist
                
                if feedid != old_feedid:
                    feed_raw_dict[old_feedid] = ds_raw_dict
                    ds_raw_dict = dict()

            plist.append((time_at, val, lng_dict[feedid]))
            old_datastreamid = datastreamid
            old_feedid = feedid

        print('Starting to fetch!')
        resultlist = cursor.fetchmany(FETCH_SCALE)
        print('Fetch done!')
    return feed_raw_dict

# 计算特征向量
feed_raw_dict = get_feeddict()

# 剔除无元素的条目
feed_raw_dict = dict((k, v) for k, v in feed_raw_dict.items() if v)

print('Start to dump data!')
pickle.dump(feed_raw_dict, open( "raw.pickle", "wb" ))
print('Raw Data Done!')
