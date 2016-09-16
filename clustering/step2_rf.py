# -*- coding: utf-8 -*-
"""
Created on Fri Sep  9 21:18:47 2016

@author: limeng
"""
import pickle
import numpy as np
import pandas as pd
import mysql.connector as c

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

np.random.seed(0)

xively_series = pickle.load(open("step1_feature2.pickle", "rb"))

db = c.connect(user='root', password='ictwsn', 
               host='127.0.0.1', database='curiosity_v3')
df = pd.read_sql('''
    select feedid, datastreamid, labels as true_label 
    from datastream_labeled_t where labels is not null
''', db)

X = []
y = []
label_names = []

for idx, L in enumerate(xively_series['labels']):
    p = L.split(',', 1)
    selector = ((df['feedid'] == int(p[0])) & (df['datastreamid'] == p[1]))
    if selector.any():
        X.append(xively_series['X'][idx])
        y_label = df['true_label'][df[selector].index].tolist()[0] 
        y.append(y_label)
        if y_label not in label_names:
            label_names.append(y_label)


# 使用所有数据作为训练集和测试集
rfc = RandomForestClassifier(n_estimators=100)
f = rfc.fit(X, y)
X_test = X
y_test = y
preds = rfc.predict(X_test)
cnt = 0
for i in range(len(preds)):
    if preds[i] == y[i]:
        cnt += 1

print('Accuracy = ' + str(100*cnt/len(preds)))
print('=====================')


# 使用10折交叉验证
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


FOLD_NUM = 10
X_list = list(chunks(X, int(len(X)/FOLD_NUM)))
y_list = list(chunks(y, int(len(y)/FOLD_NUM)))

fold_sum = 0

total_cm = np.empty(shape=(0,0))

for i in range(FOLD_NUM):
    x_test = X_list[i]
    y_test = y_list[i]
    x_train = []
    y_train = []
    
    for j in range(FOLD_NUM):
        if j == i:
            continue
        x_train = x_train + X_list[j]
        y_train = y_train + y_list[j]

    f = rfc.fit(x_train, y_train)
    preds = rfc.predict(x_test)
    
    cnt = 0
    for j in range(len(preds)):
        if preds[j] == y_test[j]:
            cnt += 1
    
    fold_sum += 100*cnt/len(preds)
    print('fold = ' + str(i) + ', Accuracy = ' + str(100*cnt/len(preds) ))
    
    # 计算整体的混淆矩阵
    cm = confusion_matrix(y_test, preds, label_names)
    cm = np.asarray(cm)
    if total_cm.shape == (0,0):
        total_cm = np.zeros(shape = cm.shape)
    total_cm += cm
    
    
fig = plt.figure()
ax = fig.add_subplot(111)
cax = ax.matshow(total_cm.tolist())
fig.colorbar(cax)
ax.set_xticklabels([''] + label_names, rotation=90)
ax.set_yticklabels([''] + label_names)
ax.xaxis.set_major_locator(MultipleLocator(1))
ax.yaxis.set_major_locator(MultipleLocator(1))
plt.tight_layout()
plt.xlabel('Predicted')
plt.ylabel('True')
plt.show()

print('=====================')
print('Overall accuracy = ' + str(fold_sum/FOLD_NUM))
