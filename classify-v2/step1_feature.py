# -*- coding: utf-8 -*-

import pickle
import numpy as np
import datetime as dt
import mysql.connector as c
from scipy.interpolate import interp1d

START_TIMESTAMP = dt.datetime.strptime("2016/08/01", "%Y/%m/%d").timestamp()
conn = c.connect(user='root', password='ictwsn',
                 host='127.0.0.1', database='curiosity_v3')

'''
值域变换
'''


def magic(x):
    threshold = 200
    if x > threshold:
        return threshold + np.log(x - threshold + 1)
    elif x <= threshold and x >= -threshold:
        return x
    else:
        return -threshold - np.log(-x + threshold - 1)


'''
特征提取
=============
输入一天的时间点，输出特征，如果val域中本身是非数字型的，则返回空序列
特征向量形如：
[0-5] 时间趋势向量，每4个小时形成一个bin，每隔bin为数值均值
[6-11] 每个bin中的方差
[11-31] 值域趋势向量，统计一天的数值分布
'''


def build_feature(plist):
    tlist = []  # 以分钟为单位
    vlist = []
    timezone = 0

    for time, val, lng in plist:
        try:
            timezone = int((float(lng) + 7.5) / 15)
            tlist.append((time.timestamp() - START_TIMESTAMP) / 60)
            vlist.append(float(val))
        except (ValueError, TypeError):
            # 时区无法转换会导致趋势无意义
            return []

    # 使用时区数据进行拼接，对于timezone>0，序列值整体后移
    t_tail = []
    t_head = []
    v_tail = []
    v_head = []
    if timezone > 0:
        for i in range(len(tlist)):
            if tlist[i] > 1440 - timezone * 60:
                t_tail.append(tlist[i] - 1440 + timezone * 60)
                v_tail.append(vlist[i])
            else:
                t_head.append(tlist[i] + timezone * 60)
                v_head.append(vlist[i])
    else:
        for i in range(len(tlist)):
            if tlist[i] < -timezone * 60:
                t_tail.append(tlist[i] + 1440 + timezone * 60)
                v_tail.append(vlist[i])
            else:
                t_head.append(tlist[i] + timezone * 60)
                v_head.append(vlist[i])

    tlist = t_tail + t_head;
    vlist = v_tail + v_head;

    # 在list的最前和最后加入一个点
    tlist = [0] + tlist + [1440]
    vlist = [vlist[0]] + vlist + [vlist[-1]]

    '''
    # 如果时间间隔过大，或开始时间和结束时间有问题
    # 原本计划直接删除该条数据
    '''
    # 使用插值方法进行数据清洗，之后进行采样
    f = interp1d(tlist, vlist)
    features = []

    samples = []  # 从0时刻开始，每隔10分钟一个样点
    cur_time = 0
    samples.append(magic(vlist[0]))
    while cur_time < 1440:
        cur_time += 10
        v = f(cur_time)
        if v.size == 1:
            v = v.item()
        samples.append(magic(v))

    average = 0.0
    d = 0.0
    for s in samples:
        average += s
    average /= len(samples)
    for s in samples:
        d += (s - average) ** 2

    # 最大值、最小值、方差
    features.append(max(samples))
    features.append(min(samples))
    features.append(average)
    features.append(d / len(samples))

    # 使用3个bin
    f_trend = []
    for i in range(3):
        bin_avg = 0
        bin_d = 0.0
        bin_max = samples[i * 48]
        bin_min = samples[i * 48]

        for j in range(48):
            bin_avg += samples[i * 48 + j]
            bin_max = max(bin_max, samples[i * 48 + j])
            bin_min = min(bin_min, samples[i * 48 + j])
        bin_avg /= 48

        for j in range(48):
            bin_d += (bin_avg - samples[i * 48 + j]) ** 2
        f_trend.append(bin_avg)
        f_trend.append(bin_d)
        f_trend.append(bin_max)
        f_trend.append(bin_min)

    features += f_trend

    # 以10分钟为间隔，4个小时24个数据点
    # 求均值、方差、最大值、最小值，作为趋势的bin，数据需要进行规范化
    f_trend = []
    for i in range(6):
        bin_avg = 0
        bin_d = 0.0
        bin_max = samples[i * 24]
        bin_min = samples[i * 24]

        for j in range(24):
            bin_avg += samples[i * 24 + j]
            bin_max = max(bin_max, samples[i * 24 + j])
            bin_min = min(bin_min, samples[i * 24 + j])
        bin_avg /= 24

        for j in range(24):
            bin_d += (bin_avg - samples[i * 24 + j]) ** 2
        f_trend.append(bin_avg)
        f_trend.append(bin_d)
        f_trend.append(bin_max)
        f_trend.append(bin_min)

    features += f_trend

    #    # 将值域分为20个bin，数值统计不同值域下的分布
    #    val_domain = [0.0]*20
    #    for sample in samples:
    #        try:
    #            val_domain[10 + int(sample/3)] += 1
    #        except (ValueError, TypeError, IndexError):
    #            # 当超过值域时，不进行处理
    #            return []
    #    features += val_domain

    return features


def get_feeddict():
    FETCH_SCALE = 100000
    feed_dict = dict()

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
    ds_dict = dict()

    while len(resultlist) != 0:
        for (feedid, datastreamid, time_at, val) in resultlist:
            if old_feedid != '' and \
                    (old_datastreamid != datastreamid or feedid != old_feedid):

                #                print('Build features for feedid = ' + str(feedid) + \
                #                    ' datastreamid = ' + str(datastreamid))
                binlist = build_feature(plist)
                #                print('Feature done! size = ' + str(len(binlist)))
                plist = []
                if len(binlist) != 0:
                    ds_dict[old_datastreamid] = binlist
                if feedid != old_feedid:
                    feed_dict[old_feedid] = ds_dict
                    ds_dict = dict()

            plist.append((time_at, val, lng_dict[feedid]))
            old_datastreamid = datastreamid
            old_feedid = feedid

        print('Starting to fetch!')
        resultlist = cursor.fetchmany(FETCH_SCALE)
        print('Fetch done!')

    # 剔除无元素的条目
    feed_dict = dict((k, v) for k, v in feed_dict.items() if v)
    return feed_dict


def save_result(feed_dict):
    labels_true = []
    features = []
    for feed_key, ds_dict in feed_dict.items():
        for ds_key, flist in ds_dict.items():
            labels_true.append(str(feed_key) + ',' + str(ds_key))
            features.append(flist)

    xively_series = dict()
    xively_series['X'] = features
    xively_series['labels'] = labels_true
    return xively_series


if __name__ == "__main__":
    # 计算特征向量
    feed_dict = get_feeddict()

    # 使用pickle进行存储
    xively_series = save_result(feed_dict)
    print('Start to dump data!')
    pickle.dump(xively_series, open("step1_feature2.pickle", "wb"))
    print('Raw Data Done!')
