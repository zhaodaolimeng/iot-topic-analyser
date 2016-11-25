# -*- coding: utf-8 -*-
"""
Created on Thu Nov 24 12:00:48 2016

@author: limeng
"""

import numpy as np

"""
rf可为每个sensor生成一个标签的分布
每个feed由多个sensor构成，且有一个主题（产品的类型）
目标是从sensor的标签分布中找到一个合适的赋值

为每个sensor输出一组新的概率
"""

class Rf_Refiner(object):
    
    """
    dataset {feedid:{sensorid:[prob]}
    """
    def __init__(self, dataset, ntypes, K=10, alpha=0.1):
        self.K = K  # K-means参数
        self.group_id = []
        self.group_prob = []
        self.new_sensor_proba = []  # 通过该优化方法得到的结果
        self.n_types = ntypes
        
        for k, v in dataset.items():
            self.group_id.append(k)
            sum_proba = [0.0] * self.n_types
            for kk, vv in v.items():
                sum_proba = list(map(sum, zip(sum_proba, vv)))
            t = sum(sum_proba)
            self.group_prob.append([x/t for x in sum_proba])
        pass
    

    def run_once(self):
        
        cluster_label, mu_list = self.kmeans(1)
        
        
        
        
    
    def kmeans(self, max_iter=1000):
        
        cluster_label = [0]*len(self.group_id)
        mu_list = np.random.rand(self.K, self.n_types)
        mu_list /= np.matrix(np.sum(mu_list, axis=1)).T

        for i in range(max_iter):
            
            # 对于每个点，计算到不同的mu的距离
            for i, x in enumerate(self.group_prob):
                distance = np.asarray([sum((mu-x)**2) for mu in mu_list])
                cluster_label[i] = distance.argmax()
                
            # 更新mu
            mu_count = [0]*self.K
            mu_sum = np.zeros((self.K, self.n_types))
            
            for i, x in enumerate(self.group_prob):
                mu_sum[cluster_label[i]] += x
                mu_count[cluster_label[i]] += 1
            mu_list = mu_sum.T/mu_count
            mu_list = mu_list.T
            
        self.mu_list = mu_list # 保存中点
        return cluster_label, mu_list

        
    def adjust_probability(self):
        
        #TODO 根据每个点到对应类的mu的距离获得一个残差，根据残差调用调整的子过程
        
        
        
        
        pass
    
if __name__ == "__main__":
    
    import pickle
    
    FILE_PREPARE = "prepare.pickle"
    
    def load_file():
        test_set = pickle.load(open(FILE_PREPARE, "rb"))['dataset']
        dataset_dict = dict()
        for i, label_str in enumerate(test_set.labels):
            group_str, sensor_str = label_str.split(',', 1)
            group_dict = dataset_dict[group_str] if group_str in dataset_dict else dict()
            group_dict[sensor_str] = test_set.p[i]
            dataset_dict[group_str] = group_dict
        
        n_types = len(test_set.p[0])
        return n_types, dataset_dict
    
    n_types, dataset_dict = load_file()
    refine = Rf_Refiner(dataset_dict, n_types)
    cluster_label, mu_list = refine.kmeans(max_iter=1)
    
    """
    group_list = ['']*len(test_set.labels)
    sensor_list = ['']*len(test_set.labels)
    
    for i, label_str in enumerate(test_set.labels):
        group_list[i], sensor_list[i] = label_str.split(',', 1)
    
    # for i, label_str in enumerate(test_set.labels):
        
    """
    