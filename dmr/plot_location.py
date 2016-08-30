# -*- coding: utf-8 -*-
"""
Created on Sat Jun 25 18:00:23 2016

@author: limeng


"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.colors import LinearSegmentedColormap

DMR_STATE = 'output/dmr.state'
DMR_PARAMETER = 'output/dmr.parameters'
DMR_FEATURES = 'output/features.txt'

TOPIC_K = 8

# 读出每个词对应的主题内容
# {doc: {word : topic}}
word_topic_mapping = dict()
with open(DMR_STATE, 'r') as f:
    next(f)
    for line in f:
        record = line.split()
        idx = record[0]
        if idx not in word_topic_mapping:
            word_topic_mapping[idx] = dict()
        word_topic_mapping[idx][record[-2]] = int(record[-1])

print('Extract topic for each word ...')

# 统计不同位置主题出现的频率
# {position : {topic : cnt}}
position_topic_mapping = dict()
with open(DMR_FEATURES, 'r') as f:
    for idx, line in enumerate(f):
        position = line.split()[0]
        if position not in position_topic_mapping:
            topic_list = np.zeros(TOPIC_K)
        
        # 对于每个文档，计算主题分布，并累加到对应的位置上
        parr = np.zeros(TOPIC_K)
        if str(idx) not in word_topic_mapping:
            continue
        for word, word_topic in word_topic_mapping[str(idx)].items():
            parr[word_topic] += 1
        parr = parr / np.sum(parr)
        topic_list = topic_list + parr
        position_topic_mapping[position] = topic_list

print('Topic for each position ...')

# 归一化
tmp_map = dict()
for loc, topic in position_topic_mapping.items():
    tmp_map[loc] = topic / np.sum(topic)
    
position_topic_mapping = tmp_map
print('Normalization ...')

# 对于所有的地理位置，以中心地点为标记绘制指定主题的热图
for topic_num in range(TOPIC_K):
    # m  = Basemap(projection='ortho',lon_0=0,lat_0=0,resolution='l',\
    #             llcrnrx=-1000*1000,llcrnry=-1000*1000,
    #             urcrnrx=+1150*1000,urcrnry=+1700*1000)
    
    print("Plotting for topic: ", topic_num)
    m = Basemap(llcrnrlon=-180,llcrnrlat=-80,
                urcrnrlon=180,urcrnrlat=80,projection='mill')
    m.drawcoastlines()
    m.drawcountries()
    # m.drawstates()
    
    lon_bins = np.linspace(-180, 180, 72) # 36 bins
    lat_bins = np.linspace(-80, 80, 36) # 72 bins
    density = np.zeros([36, 72])
    
    for x, y in np.ndindex(density.shape):
        loc_str = 'lbloc_' + str(x) + '_' + str(y)
        if loc_str not in position_topic_mapping:
            continue
        density[x][y] = position_topic_mapping[loc_str][topic_num]
    
    lon_bins_2d, lat_bins_2d = np.meshgrid(lon_bins, lat_bins)
    xs, ys = m(lon_bins_2d, lat_bins_2d) # will be plotted using pcolormesh
    
    cdict = {'red':  ( (0.0,  1.0,  1.0),
                       (1.0,  0.9,  1.0) ),
             'green':( (0.0,  1.0,  1.0),
                       (1.0,  0.03, 0.0) ),
             'blue': ( (0.0,  1.0,  1.0),
                       (1.0,  0.16, 0.0) ) }
    custom_map = LinearSegmentedColormap('custom_map', cdict)
    plt.register_cmap(cmap=custom_map)
    
    plt.pcolormesh(xs, ys, density, cmap="custom_map")
    plt.show()
    # xs.shape = (72, 36)
    # ys.shape = (72, 36)

