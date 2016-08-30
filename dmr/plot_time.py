# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 22:58:00 2016

@author: limeng


时间-主题曲线
x轴为时间线，y轴为指定主题在文档中出现的概率
计算方式：统计同一个时间标签的所有文档，计算他们属于不同主题的混合概率

"""

import numpy as np
import matplotlib.pyplot as plt

TOPIC_K = 15

# 读出每个词对应的主题内容
# {doc: {word : topic}}
word_topic_mapping = dict()
with open('output/dmr.state', 'r') as f:
    next(f)
    for line in f:
        record = line.split()
        idx = record[0]
        if idx not in word_topic_mapping:
            word_topic_mapping[idx] = dict()
        word_topic_mapping[idx][record[-2]] = int(record[-1])

print('Extract topic for each word ...')

# 统计特定主题在不同时间段出现的频率
# {timestamp : {topic : cnt}}
timestamp_topic_mapping = dict()
with open('output/features.txt', 'r') as f:
    for idx, line in enumerate(f):
        # lbloc_28_35 lbtime=2
        timestamp = int(line.split()[1].split('=')[-1])
        if timestamp not in timestamp_topic_mapping:
            topic_list = np.zeros(TOPIC_K)
        # 对于每个文档，计算主题分布，并累加到对应的位置上
        parr = np.zeros(TOPIC_K)
        if str(idx) not in word_topic_mapping:
            continue
        for word, word_topic in word_topic_mapping[str(idx)].items():
            parr[word_topic] += 1
        parr = parr / np.sum(parr)
        topic_list = topic_list + parr
        timestamp_topic_mapping[timestamp] = topic_list

print('Topic for each position ...')

# 归一化
topic_list = [[0 for i in range(len(timestamp_topic_mapping))] for j in range(TOPIC_K)]
time_list = []
tmp_map = dict()
time_cnt = 0
for time, topic_arr in timestamp_topic_mapping.items():
    tmp_map[time] = topic_arr / np.sum(topic_arr)
    time_list.append(time)
    upper_line = 0
    for idx in range(TOPIC_K):
        upper_line += tmp_map[time][idx]
        topic_list[idx][time_cnt] = upper_line
    time_cnt += 1
    
timestamp_topic_mapping = tmp_map
print('Normalization ...')

fig = plt.figure()
ax = fig.add_subplot(111)

color_list = ['#F0F8FF', '#FAEBD7', '#00FFFF', '#7FFFD4', 
              '#F0FFFF', '#F5F5DC', '#FFE4C4', '#0000FF',]

ax.fill_between(time_list, 0, topic_list[0], facecolor=color_list[0], alpha=.7)
for idx in range(TOPIC_K - 1):
    ax.fill_between(time_list, 
                    topic_list[idx],
                    topic_list[idx + 1], 
                    facecolor=color_list[idx + 1], alpha=.7)
#    ax.fill_between(time_list, 0, topic_list[idx], facecolor="#CC6666", alpha=.7)
#    ax.plot(topic_list[idx], label = 'topic:' + str(idx))

#ax1.fill_between(x, y_stack[0,:], y_stack[1,:], facecolor="#1DACD6", alpha=.7)
#ax1.fill_between(x, y_stack[1,:], y_stack[2,:], facecolor="#6E5160")

plt.show()

   
