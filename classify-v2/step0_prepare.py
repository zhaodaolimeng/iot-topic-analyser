# -*- coding: utf-8 -*-

import pickle
import pandas as pd
import datetime as dt
import mysql.connector as c

"""
功能：
分别从datastream_label_not_zero_t和datapoint_t读出被标记的点的所有信息，存入到pickle；
datastream_label_not_zero_t 从该表可获得feed_id和stream_id，对应手工标记label；
原始的序列数据需要通过feed_id和stream_id从datapoint_t中进行查找；
需要使用原始数据集中设备的longitude信息，以对齐数据序列
"""

START_TIMESTAMP = dt.datetime.strptime("2016/12/04", "%Y/%m/%d").timestamp()
conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161204')

print('Fetch labeled streams ...')
label_df = pd.read_sql("""
    select * from datastream_label_not_zero_t
    where label!='' and lng is not null
""", conn)

label_dict = {(val['feed_id'], val['stream_id']): val['label'] for _, val in label_df.iterrows()}
lng_dict = {(val['feed_id'], val['stream_id']): val['lng'] for _, val in label_df.iterrows()}

print('Fetch datapoint ...')
point_df = pd.read_sql("select * from datapoint_t", conn)

series_dict = dict()
for idx, val in label_df.iterrows():
    points = point_df.loc[(point_df['feedid'] == val['feed_id']) & (point_df['datastreamid'] == val['stream_id'])]
    series_dict[(val['feed_id'], val['stream_id'])] = (points['val'].tolist(), points['time_at'].tolist())
    if idx % 100 == 0:
        print(idx)

"""
这三个dict的key均为(feedid, datastreamid)构成的tuple
series_dict的value由一个value_list和time_list绑定构成
"""
result = {'label_dict': label_dict, 'lng_dict': lng_dict, 'series_dict': series_dict}
pickle.dump(result, open('step0_prepare.pickle', 'wb'))
