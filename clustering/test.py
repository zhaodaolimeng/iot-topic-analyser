# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 16:48:33 2016

@author: limeng
"""

import pickle
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


'''

#############################################################################
# heatmap plot

feed_dict = pickle.load(open("raw.pickle", "rb"))
labels_true = []
features = []

for feed_key, datastream_dict in feed_dict.items():
    for ds_key, plist in datastream_dict.items():
        if np.isnan(plist).any():
            continue
        labels_true.append(str(feed_key) + ',' + str(ds_key))
        features.append(plist)

def magic(x):
    FILTER = 1
    if x>FILTER:
        return FILTER + np.log(x)
    elif x<=FILTER and x>=-FILTER:
        return x
    else:
        return -FILTER - np.log(-x)

for i in range(len(features)):
    for j in range(len(features[0])):
        features[i][j] = magic(features[i][j]) # 规范化

X = np.array(features)
plt.plot(X[:,0], X[:,1], 'o')
heatmap, xedges, yedges = np.histogram2d(X[:,1], X[:,0], bins=50)
heatmap = heatmap[::-1, :] # historgram的y轴是反向的
extent = [yedges[0], yedges[-1], xedges[0], xedges[-1]]

plt.clf()
plt.imshow(heatmap, extent=extent)
plt.show()
'''

'''
#############################################################################
# 3D plot

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(X[:,0], X[:,1], X[:,2])
ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_zlabel('Z Label')
plt.show()
'''
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pickle
import itertools

from sklearn import datasets
from sklearn.cross_validation import StratifiedKFold
from sklearn.externals.six.moves import xrange
from sklearn import mixture


def bicycle(iterable, repeat=1):
    for item in itertools.cycle(iterable):
        for _ in xrange(repeat):
            yield item

c = bicycle([1,2,3,4], 2)
for i in c:
    print(i)
