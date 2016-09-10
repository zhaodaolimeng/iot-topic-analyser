# -*- coding: utf-8 -*-
"""
Created on Fri Sep  9 21:18:47 2016

@author: limeng
"""
import pickle
import numpy as np
import pandas as pd
import mysql.connector as c

import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import calibration_curve

np.random.seed(0)

xively_series = pickle.load(open("feature2.pickle", "rb"))

db = c.connect(user='root', password='ictwsn', 
                     host='127.0.0.1', database='curiosity_v3')
df = pd.read_sql('''
    select feedid, datastreamid, labels as true_label 
    from datastream_labeled_t where labels is not null
''', db)

X = []
y = []

for idx, L in enumerate(xively_series['labels']):
    p = L.split(',', 1)
    selector = ((df['feedid'] == int(p[0])) & (df['datastreamid'] == p[1]))
    if selector.any():
        X.append(xively_series['X'][idx])
        y.append(df['true_label'][df[selector].index].tolist()[0])

rfc = RandomForestClassifier(n_estimators=100)
f = rfc.fit(X, y)
X_test = X
y_test = y

preds = rfc.predict(X_test)
# pd.crosstab(y, preds, rownames=['actual'], colnames=['preds'])

cnt = 0
for i in range(len(preds)):
    if preds[i] == y[i]:
        cnt += 1
        
print(str(100*cnt/len(preds)))

