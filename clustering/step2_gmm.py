# -*- coding: utf-8 -*-

# Author: Ron Weiss <ronweiss@gmail.com>, Gael Varoquaux
# License: BSD 3 clause

# $Id$

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
import pickle
import itertools
import mysql.connector as c

from sklearn import datasets
from sklearn.cross_validation import StratifiedKFold
from sklearn.externals.six.moves import xrange
from sklearn import mixture

np.random.seed(0)

#FIXME!
COMPONENT = 12

def repeatlist(it, count):
    return itertools.islice(itertools.cycle(it), count)

color_str = ['r', 'g', 'b', 'c', 'm']
color_iter = list(repeatlist(color_str, COMPONENT))

xively_series = pickle.load(open("step1_feature2.pickle", "rb"))
X = np.array(xively_series['X'])
X = X[:, 0:25]

def make_ellipses(gmm, ax):
    # cool but useless
    for n, color in enumerate(color_iter):
        v, w = np.linalg.eigh(gmm._get_covars()[n][:2, :2])
        u = w[0] / np.linalg.norm(w[0])
        angle = np.arctan2(u[1], u[0])
        angle = 180 * angle / np.pi  # convert to degrees
        v *= 9
        ell = mpl.patches.Ellipse(gmm.means_[n][:2], v[0], v[1],
                                  180 + angle, color=color)
        ell.set_clip_box(ax.bbox)
        ell.set_alpha(0.5)
        ax.add_artist(ell)

'''
两种聚类方法
=====================
'''

'''
# DPGMM    
classifier = mixture.DPGMM(n_components=COMPONENT, covariance_type='tied', 
                           init_params='wc', n_iter=20)
classifier.fit(X)
h1 = plt.subplot(1, 2, 2)
make_ellipses(classifier, h)
y_pred = classifier.predict(X)
for n, color in enumerate(color_iter):
    data = X[y_pred == n]
    plt.plot(data[:, 0], data[:, 1], 'x', color=color)

plt.show()
'''


# GMM
classifier = mixture.GMM(n_components=COMPONENT, covariance_type='tied', 
                         init_params='wc', n_iter=20)
classifier.fit(X)
h = plt.subplot(1, 2, 1)
make_ellipses(classifier, h)
y_pred = classifier.predict(X)
for n, color in enumerate(color_iter):
    data = X[y_pred == n]
    plt.plot(data[:, 0], data[:, 1], 'x', color=color)

   
'''
聚类正确性检查
========================
Precise, Recall
'''
db = c.connect(user='root', password='ictwsn', 
                     host='127.0.0.1', database='curiosity_v3')
df = pd.read_sql('''
    select feedid, datastreamid, labels as true_label 
    from datastream_labeled_t where labels is not null
''', db)
true_label = []
pred_label = []

for idx, L in enumerate(xively_series['labels']):
    p = L.split(',', 1)
    selector = ((df['feedid'] == int(p[0])) & (df['datastreamid'] == p[1]))
    if selector.any():
        # orzorzorzorzorzorz
        true_label.append(df['true_label'][df[selector].index].tolist()[0])
        pred_label.append(y_pred[idx])

# 对每个生成的类进行统计，计算每个类的混杂度
# {pred_label: {true_label: cnt}}
pred_dict = dict()
for pidx, pred in enumerate(pred_label):
    if pred not in pred_dict:
        pred_dict[pred] = dict()
    if true_label[pidx] not in pred_dict[pred]:
        pred_dict[pred][true_label[pidx]] = 1
    pred_dict[pred][true_label[pidx]] += 1

for _,sub_dict in pred_dict.items():
    sumc = 0.0
    maxc = 0.0
    for _, v1 in sub_dict.items():
        sumc += v1
        maxc = max(maxc, v1)
    print('P = ' + str(maxc/sumc))

# 对每个标注的类进行统计，计算类的混杂度
true_dict = dict()
for pidx, true in enumerate(true_label):
    if true not in true_dict:
        true_dict[true] = dict()
    if pred_label[pidx] not in true_dict[true]:
        true_dict[true][pred_label[pidx]] = 1
    true_dict[true][pred_label[pidx]] += 1

for _,sub_dict in true_dict.items():
    sumc = 0.0
    maxc = 0.0
    for _, v1 in sub_dict.items():
        sumc += v1
        maxc = max(maxc, v1)
    print('R = ' + str(maxc/sumc))


