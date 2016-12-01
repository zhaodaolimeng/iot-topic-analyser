# -*- coding: utf-8 -*-
"""
Created on Thu Nov 24 12:00:48 2016

@author: limeng
"""

import numpy as np
import networkx as nx

"""
rf可为每个sensor生成一个标签的分布
每个feed由多个sensor构成，且有一个主题（产品的类型）
目标是从sensor的标签分布中找到一个合适的赋值

为每个sensor输出一组新的概率
"""


class RfRefiner(object):
    """
    dataset {feedid:{sensorid:[prob]}
    """

    def __init__(self, dataset, k=10):
        self.K = k  # K-means参数
        self.sensor_choice = []  # 分类信息，待优化的项
        self.sensor_p = dataset.p
        self.n_types = len(dataset.p[0])

        self.feedid = []
        self.sensorid = []

        self.group_p = []
        self.group_id = []

        for L in dataset.labels:
            self.feedid.append(L.split(',', 1)[0])
            self.sensorid.append(L.split(',', 1)[1])

        for p in dataset.p:
            self.sensor_choice.append(np.argmax(p))

        self.group_p, self.group_id = self.update_group_prob(self.feedid, self.sensor_choice)

        pass

    """
    根据sensor_choice计算group_prob
    对于每个分组，统计组内的sensor类型的数目
    """

    def update_group_prob(self, feedid, sensor_choice):

        old_f = feedid[0]
        group_p = []
        group_id = []
        counter = [0] * self.n_types
        for i, f in enumerate(feedid):
            if old_f == f:
                counter[sensor_choice[i]] += 1
            else:
                group_id.append(old_f)
                group_p.append(np.asarray(counter) / np.sum(counter))
                counter = [0] * self.n_types
                counter[sensor_choice[i]] += 1
                old_f = f
        group_id.append(old_f)
        group_p.append(np.asarray(counter) / np.sum(counter))

        return group_p, group_id

    """
    进行一次聚类+一次sensor_choice的优化
    """

    def run_once(self):

        # 执行一次聚类
        cluster_label, mu_list = self.kmeans(self.group_p, max_iter=10)

        # 找到每个组对应的sensor的id
        group_dict = dict()
        for idx, f in enumerate(self.feedid):
            if f not in group_dict:
                group_dict[f] = []
            group_dict[f].append(idx)

        # 得到每个组对应的sensor的分布sensor_proba
        for idx, cluster in enumerate(cluster_label):
            sensor_proba = []  # 当前组每个节点的分布 n*len(features[0])
            for sensor_idx in group_dict[self.group_id[idx]]:

                sensor_proba.append(self.sensor_p[sensor_idx])
            self.adjust_sensor_choice(sensor_proba, mu_list[cluster])

        pass

    """
    X为每个组中sensor_choice的比例，组个数 * sensor_choice类别数
    cluster_label为每个组属于的cluster的编号，组数目 * 1
    mu_list为每个cluster对应的坐标值，cluster数目 * sensor_choice类别数
    """
    @staticmethod
    def kmeans(features, n_mu=10, max_iter=10):

        cluster_label = [0] * len(features)
        mu_list = np.random.rand(n_mu, len(features[0]))  # 每个聚类的中心K*27
        mu_list /= np.matrix(np.sum(mu_list, axis=1)).T

        for iter_times in range(max_iter):

            # 对于每个点，计算到不同的mu的距离
            for i, x in enumerate(features):
                distance = np.asarray([sum((mu - x) ** 2) for mu in mu_list])
                cluster_label[i] = distance.argmin()

            # 更新mu
            mu_count = [0] * n_mu
            mu_sum = np.zeros((n_mu, len(features[0])))

            for i, x in enumerate(features):
                mu_sum[cluster_label[i]] += x
                mu_count[cluster_label[i]] += 1

            for idx, mu_feature in enumerate(mu_list):
                if mu_count[idx] != 0:
                    mu_list[idx] = mu_sum[idx]/mu_count[idx]

        return cluster_label, mu_list

    """
    输入：
    sensor_proba为组中所有sensor类别的rf判定值，sensor个数 * sensor_choice的类别数
    choice为组中每个sensor的当前选择值，组中sensor个数 * 1  
    difference为组中不同sensor选择的偏差值，sensor_choice的类别数 * 1
    输出：
    每个sensor的输出边
    """
    @staticmethod
    def adjust_sensor_choice(sensor_proba, type_target, portion_lambda=1, rounding_scale=10):

        """
        sensor_proba为第一层节点
        type_target为第二层节点
        :rtype: object
        """
        n_sensors = len(sensor_proba)
        graph_edge = []
        for idx, p_si in enumerate(sensor_proba):
            graph_edge.append((0, 1+idx, {'capacity': 1, 'weight': 0}))
            for idx_t, _ in enumerate(type_target):
                if p_si[idx_t] != 0:
                    st = {'capacity': 1, 'weight': 1.0/p_si[idx_t]}
                    graph_edge.append((1+idx, 1+idx_t+n_sensors, st))

        for idx_t, t in enumerate(type_target):
            s = sum(type_target)
            if t != 0:
                st = {'capacity': n_sensors, 'weight': 1.0*portion_lambda*s/t}
                graph_edge.append((1+n_sensors + idx_t, 1 + n_sensors + len(type_target), st))

        # 当weight和capacity为浮点数时方法失效，所以将权重进行rounding
        min_weight = min([e[2]['weight'] for e in graph_edge if e[2]['weight'] > 0])
        ratio = rounding_scale/min_weight
        for e in graph_edge:
            e[2]['weight'] = int(ratio*e[2]['weight'])

        G = nx.DiGraph()
        G.add_edges_from(graph_edge)
        flow_dict = nx.max_flow_min_cost(G, 0, 1 + n_sensors + len(type_target))
        print(flow_dict)

        pass


if __name__ == "__main__":
    import pickle

    FILE_PREPARE = "prepare.pickle"
    test_set = pickle.load(open(FILE_PREPARE, "rb"))['dataset']

    refine = RfRefiner(test_set)

    refine.run_once()

    """
    group_list = ['']*len(test_set.labels)
    sensor_list = ['']*len(test_set.labels)
    
    for i, label_str in enumerate(test_set.labels):
        group_list[i], sensor_list[i] = label_str.split(',', 1)
    
    # for i, label_str in enumerate(test_set.labels):
        
    """
