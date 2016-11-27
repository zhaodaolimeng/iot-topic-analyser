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
    def __init__(self, dataset, K=10, alpha=0.1):
        self.K = K  # K-means参数
        self.sensor_choice = [] # 分类信息，待优化的项
        self.sensor_p = dataset.p
        self.n_types = len(dataset.p[0])
        
        self.feedid = []
        self.sensorid = []
        
        for L in dataset.labels:
            self.feedid.append(L.split(',', 1)[0])
            self.sensorid.append(L.split(',', 1)[1])
            
        
        for p in dataset.p:
            self.sensor_choice.append(np.argmax(p))
        
        pass
    
    """
    根据sensor_choice计算group_prob
    对于每个分组，统计组内的sensor类型的数目
    """
    def update_group_prob(self, feedid, sensor_choice):
        
        old_f = feedid[0]
        group_p = []
        group_id = []
        counter = [0]*self.n_types
        for i, f in enumerate(feedid):
            if old_f == f:
                counter[sensor_choice[i]] += 1
            else:
                group_id.append(old_f)
                group_p.append(np.asarray(counter)/np.sum(counter))
                counter = [0]*self.n_types
                old_f = f
        group_id.append(old_f)
        group_p.append(np.asarray(counter)/np.sum(counter))
        
        return group_p, group_id
    

    """
    进行一次聚类+一次sensor_choice的优化
    """
    def run_once(self):
        
        group_prob, _ = self.update_group_prob(self.feedid, self.sensor_choice)
        
        # 执行一次聚类
        cluster_label, mu_list = self.kmeans(group_prob, max_iter=100)
        
        # 找到每个组对应的sensor的id
        group_sensor_dict = dict()
        for idx, f in enumerate(self.feedid):
            group_sensor_dict[f] = self.sensorid[idx] \
                if len(group_sensor_dict[f]) == 0 else group_sensor_dict[f] + self.sensorid[idx]
        
        # 每个组可计算得到一个偏差值，每个点是一个组，每个组的sensor是?
        for idx, cluster in enumerate(cluster_label):
            difference = self.group_p[idx] - mu_list[cluster]
            
            sensor_proba = []
            sensor_choice = []
            
            for sensor_idx in group_sensor_dict[self.group_id[idx]]:
                sensor_proba.append(self.sensor_p[sensor_idx])
                sensor_choice.append(self/sensor_choice[sensor_idx])

            self.adjust_sensor_choice(sensor_proba, sensor_choice, difference)
        
        pass
        
    """
    X为每个组中sensor_choice的比例，组个数 * sensor_choice类别数
    cluster_label为每个组属于的cluster的编号，组数目 * 1
    mu_list为每个cluster对应的坐标值，cluster数目 * sensor_choice类别数
    """
    def kmeans(self, X, max_iter=1000):
        
        cluster_label = [0]*len(X)
        mu_list = np.random.rand(len(X), len(X[0]))  # 每个聚类的中心K*27
        mu_list /= np.matrix(np.sum(mu_list, axis=1)).T

        for i in range(max_iter):
            
            # 对于每个点，计算到不同的mu的距离
            for i, x in enumerate(X):
                distance = np.asarray([sum((mu-x)**2) for mu in mu_list])
                cluster_label[i] = distance.argmax()
                
            # 更新mu
            mu_count = [0]*len(X)
            mu_sum = np.zeros((len(X), len(X[0])))
            
            for i, x in enumerate(X):
                mu_sum[cluster_label[i]] += x
                mu_count[cluster_label[i]] += 1
            mu_list = (mu_sum.T/mu_count).T
            
        return cluster_label, mu_list

    
    """
    输入：
    sensor_proba为组中所有sensor类别的rf判定值，sensor个数 * sensor_choice的类别数
    choice为组中每个sensor的当前选择值，组中sensor个数 * 1  
    difference为组中不同sensor选择的偏差值，sensor_choice的类别数 * 1
    输出：
    
    """
    def adjust_sensor_choice(self, sensor_proba, choice, difference):
        
        
        
        
        
        pass
    
if __name__ == "__main__":
    
    import pickle
    
    FILE_PREPARE = "prepare.pickle"
    test_set = pickle.load(open(FILE_PREPARE, "rb"))['dataset']
    
    refine = Rf_Refiner(test_set)
    
    refine.run_once()
    
    """
    group_list = ['']*len(test_set.labels)
    sensor_list = ['']*len(test_set.labels)
    
    for i, label_str in enumerate(test_set.labels):
        group_list[i], sensor_list[i] = label_str.split(',', 1)
    
    # for i, label_str in enumerate(test_set.labels):
        
    """
    