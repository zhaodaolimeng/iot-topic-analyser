# -*- coding: utf-8 -*-
"""
Created on Thu Nov 24 15:41:17 2016

@author: limeng
"""


class Dataset(object):
    
    def __init__(self):
        self.labels = []
        self.X = []
        self.y = []
        self.p = []
        self.name2index = dict()
        self.size = 0
        pass
    
    def add_item(self, label, feature_vector, result):
        self.labels.append(label)
        self.X.append(feature_vector)
        self.y.append(result)
        self.size += 1
        pass
    
    '''
    返回一个分割之后的子集
    '''
    def data_split(self, fold_num=10, fold_cnt=0):
        instance_test = Dataset()
        instance_train = Dataset()
        
        chunk_size = self.size/fold_num
        if chunk_size == 0:
            return None
        start_idx = chunk_size * fold_cnt
        
        for i in range(self.size):
            if i < start_idx or i >= start_idx + chunk_size:
                instance_train.add_item(self.labels[i], self.X[i], self.y[i])
            else:
                instance_test.add_item(self.labels[i], self.X[i], self.y[i])
                
        return instance_test, instance_train

    def data_merge(self, instance):
        for i in range(instance.size):
            self.add_item(instance.labels[i], instance.X[i], instance.y[i])
