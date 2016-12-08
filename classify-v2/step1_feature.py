# -*- coding: utf-8 -*-

import pickle
import numpy as np
import datetime as dt
from scipy.interpolate import interp1d

START_TIMESTAMP = dt.datetime.strptime("2016/12/07", "%Y/%m/%d").timestamp()


def magic(x, threshold=200):
    return x/abs(x)*(threshold + np.log(abs(x - threshold + 1))) if abs(x) > threshold else x


def series_align(l_dict, s_dict):
    """
    :param s_dict: 每个元素为一个tuple，其中的两个元素分别为time_list和value_list
    :param l_dict: 对应longitude的值
    :return result_dict: 对应的数据序列
    返回一个dict，其中每个元素为一个对齐后的list
    """
    result_dict = []
    for fd_tuple, lng in l_dict.items():
        shift = int(float(lng)) / 15
        start_time = 24 - shift if shift > 0 else -shift
        end_time = start_time + 24
        vl = s_dict[fd_tuple][0]
        tl = s_dict[fd_tuple][1]
        # TODO 时间比较
        result_dict[fd_tuple] = [(t, vl[i]) for i, t in enumerate(tl) if t > start_time and t < end_time]

    return result_dict


def order_label(l_dict):
    """
    每个label位具有多个文本标签，将前后顺序调整为一致的
    :param l_dict: 每个stream对应的标签
    :return ordered_label_dict: 顺序修改过的标签
    """
    result_dict = dict()
    for fd_tuple, labels in l_dict.items():
        l_list = labels.split(' ')
        result_dict[fd_tuple] = ''.join(sorted(l_list))
    return  result_dict

if __name__ == "__main__":
    """
    输入：标签、数值序列、经度信息
    输出：特征向量
    ============================
    1. 使用longitude进行数据对齐
    2. 对于每个stream生成特征向量，之前的方法包括：
    (1) 四个不同的bin的均值、方差
    (2) 不同数值的分布
    3. 形成train_x, train_y, item_name
    """
    datasource = pickle.load(open('step0_prepare.pickle', 'rb'))

    # 序列截断
    aligned_series_dict = series_align(datasource['lng_dict'], datasource['series_dict'])

    # 整理手工标签
    ordered_label_dict = order_label(datasource['label_dict'])

    # 计算特征向量

    # 使用pickle进行存储
