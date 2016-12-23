# -*- coding: utf-8 -*-

import pickle
import os
import math
import pywt
import numpy as np
import pandas as pd
import datetime as dt
import mysql.connector as c
from scipy.interpolate import interp1d
from scipy.stats import variation, linregress


def magic(x, threshold=200):
    return x/abs(x)*(threshold + math.log(abs(x - threshold + 1))) if abs(x) > threshold else x


def fetch_raw_datapoints(conn, labeled):
    """
    在使用该方法进行逐一查找之前，必须对表datapoint_t的feedid和datastreamid增加索引
    从manual_label_t表获得feed_id和stream_id，对应手工标记label；
    原始的序列数据需要通过feed_id和stream_id从datapoint_t中进行查找
    """
    series_dict = dict()  # 每个(feedid, datastreamid)对应一个(time_at, val)的list
    cursor = conn.cursor()

    for f_id, s_id in labeled:
        # print('Fetching feedid = ' + str(f_id) + ', datastreamid = ' + str(s_id))
        cursor.execute("""
            select feedid, datastreamid, time_at, val from datapoint_t
            where feedid=%s and datastreamid=%s
        """, (f_id, s_id))
        series_dict[(f_id, s_id)] = [(time_at, val) for _, _, time_at, val in cursor.fetchall()]

    return series_dict


def compute_feature(series_dict):
    """
    特征由以下构成：
    (1) 小波分解，得到的ac和dc计算得到小波系数（能量？好像还有一个系数？）
    (2) 线性回归计算得到的回归系数（整体趋势）
    (3) 不同数值的分布
    (4) 最高点到最低点的斜率，以及其他点对于该直线的回归系数（每天的周期性）
    (5) 充分利用昼夜特征，即两个最低点之间的距离（如果是周期的，则该值应当是1440）
    :param series_dict:
    :return f_dict: 每个序列的特征向量
    """

    len_of_2days = 1440 * 2
    f_dict = dict()
    black_list = []

    for fd_tuple, series in series_dict.items():
        feature = []
        samples = []

        # 对数据进行插值
        tlist = [(series[i][0].timestamp() - START_TIMESTAMP)/60 for i in range(len(series))]
        vlist = [series[i][1] for i in range(len(series))]
        tlist = [0] + tlist + [len_of_2days]
        vlist = [vlist[0]] + vlist + [vlist[-1]]

        # print(fd_tuple)
        try:
            interp_f = interp1d(tlist, vlist)
            for cur_time in range(0, len_of_2days, 10):
                v = interp_f(cur_time)  # 每十分钟进行一次采样
                samples.append(magic(v))
        except ValueError:
            print('Detect error!')
            black_list.append(fd_tuple)
            continue

        # 常规参数
        sample_np = np.array(samples)
        s_ave = np.average(sample_np)
        feature.append(s_ave)
        feature.append(variation(sample_np))
        feature.append(np.min(sample_np))
        feature.append(np.max(sample_np))

        # 小波系数
        w_coeff = pywt.wavedec(samples, 'haar', level=5)
        feature.append(np.linalg.norm(w_coeff[0]))
        feature.append(np.linalg.norm(w_coeff[1]))
        feature.append(np.linalg.norm(w_coeff[2]))
        feature.append(np.linalg.norm(w_coeff[3]))
        feature.append(np.linalg.norm(w_coeff[4]))

        # 对于均值的zero cross
        zc = [i for i in range(1, sample_np.size-1) if (sample_np[i] - s_ave)*(sample_np[i-1] - s_ave) > 0]
        feature.append(len(zc))

        # 一阶回归之后的整体趋势
        slope, intercept, r_value, p_value, std_err = linregress(sample_np.tolist(), list(range(len(sample_np))))
        feature.append(slope)
        feature.append(intercept)
        feature.append(r_value)
        feature.append(p_value)
        feature.append(std_err)

        # 以最大值作为分裂两部分数据的依据
        # 分别计算两部分数据的最小值，作为单日数据截断的依据
        # TODO 如何认定是以天为周期的？
        # maxv_idx = np.argmax(sample_np)
        # minv_idx = np.argmax(-sample_np)
        # feature.append()

        # 检查数据有效性
        is_invalid = False
        for f in feature:
            if math.isnan(f) or math.isinf(f):
                is_invalid = True
                break
        if not is_invalid:
            f_dict[fd_tuple] = feature

    return f_dict


if __name__ == "__main__":

    np.random.seed(0)

    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    START_TIMESTAMP = dt.datetime.strptime("2016-12-04 00:00:00", TIME_FORMAT).timestamp()
    PICKLE_LOADED_FROM_DB = 'p_raw_series_dict.pickle'
    PICKLE_FEATURES = 'p_label_feature.pickle'

    db_conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161204')
    print('Fetch labeled streams ...')
    label_df = pd.read_sql("select * from manual_label_t where label!=''", db_conn)
    label_dict = {(val['feed_id'], val['stream_id']): val['label'] for _, val in label_df.iterrows()}

    if os.path.isfile(PICKLE_LOADED_FROM_DB):
        raw_series_dict = pickle.load(open(PICKLE_LOADED_FROM_DB, 'rb'))
    else:
        # 数据集有变动时要删除同目录下的两个pickle文件
        raw_series_dict = fetch_raw_datapoints(db_conn, label_dict)
        pickle.dump(raw_series_dict, open(PICKLE_LOADED_FROM_DB, 'wb'))

    print("Compute features for each datastream...")
    feature_dict = compute_feature(raw_series_dict)

    l_swap_dict = dict()
    for fs_tuple, f_list in feature_dict.items():
        l_swap_dict[fs_tuple] = label_dict[fs_tuple]

    result = {'label_dict': l_swap_dict, 'feature_dict': feature_dict}
    pickle.dump(result, open(PICKLE_FEATURES, 'wb'))
    print('Length of label_dict = ' + str(len(l_swap_dict)))
    print('Length of feature_dict = ' + str(len(feature_dict)))
