# -*- coding: utf-8 -*-
"""
Created on Fri Nov 18 17:19:28 2016

@author: limeng
"""

import numpy as np

"""

Type Adjustment

不同应用包含的传感器的类别是有明显区别的
尝试使用这些信息对rf的结果进行优化

模型构建为：

alpha->theta->z<-w

alpha 模型超参数
theta 应用的类别
z 每个应用中传感器的真实类别
w 每个应用中传感器的类别分布（rf的输出结果）

模型输出为z，即每个传感器的预测类别
"""

class TA:
    
    """
    corpus结构为{feedid:{sensorid:p}}
    K为主题个数
    alpha为Dirichlet分布的超参数
    
    当sensorid为已观测设备时，统一起见仍构造成分布的形式
    """    
    def __init__(self, corpus, K=10, alpha=0.1):
        self.corpus = corpus
        self.n_topics = K
        self.alpha = len(corpus)/K # 使用建议值，另一种方法是使用EM进行估计
        
        self.topics = {} # 每个sensor的分类指派
        self._init()
    
    """
    文档中每个单词的指派z进行随机取值
    """
    def _init(self):
        
        n_docs = len(self.corpus)
        self.nmz = np.zeros((n_docs, self.n_topics)) # 文档m中属于主题z的词个数
        
        
        
        # 保存(m,i)与feed，sensor的名称对应关系
        self.idx2feed = dict() 
        self.idx2sensor = dict()
        
        for m, (feedid, s_dict) in enumerate(self.corpus.items()):
            self.idx2feed[m] = feedid
            for i, (sensorid, phi) in enumerate(s_dict.items()):
                self.idx2sensor = sensorid
                z = np.random.randint(self.n_topics)
                self.topics[(m,i)] = z

                self.nmz[m,z] += 1
                self.nm[m] += 1
                self.nzw[z,w] += 1
                self.nz[z] += 1
                self.topics[(m,i)] = z
        pass
    
    """
    主方法，使用gibbs sampling
    对于每个应用的每个sensor，更新条件概率分布
    """
    def run(self, max_iter):
        
        for iter_cnt in range(max_iter=100):
            for m in self.feedid_list:
                for i in self.sensorid_list:
                    p = self._conditional_distribution(m, i)
                    z = self._sample_index(p) # 采样一个主题
                    self.topics[(m, i)] = z
                    
        pass
    
    """
    p(z_i|z_~i, phi) 
    m,i指第m个文档的第i个词，phi表示该词对应的类别分布，返回一个表示主题分布的向量
    """
    def _conditional_distribution(self, m, i):
        
        left = self.topics[(m,i)] # 数据维度为 Kx1，表示文档m词i对应的主题号
        right = (self.nmz[m,:] + self.alpha) / \
                (self.nm[m] + self.alpha * self.n_topics)
        p_z = left * right
        # normalize to obtain probabilities
        p_z /= np.sum(p_z)
        return p_z
        
    """
    从以p为参数的多项式分布中进行采样
    输入表示多项分布的参数向量，返回采样的序号
    """
    def _sample_index(self, p):
        return np.random.multinomial(1, p).argmax()
    
    """
    计算相似度
    以“与RF结果之间的相似度”+“结构惩罚”为打分标准
    """
    def _log_likehood():
        #TODO ???
        
        pass
    
    """
    输出预测结果
    """
    def print_z(self):
        #TODO z为每个sensor的预测标签
        for m in self.topics:
            print('doc=' + str(m) + ': ')
            for i in m:
                print(self.topics[(m.i)] + '\t')
            print('\n')
        pass
    
    
if __name__ == "__main__":
    
    import pickle
    import mysql.connector as c
    from sklearn.ensemble import RandomForestClassifier
    
    """
    使用cross validation判定的分类准确率只有不到60%：
    1. 读入带标签的900条数据（标签数目需要扩充，#TODO）
    2. 使用90%作为训练，10%作为测试，得到测试集的分布
    3. 用所有的数据训练推断的方法
    4. 使用推断的方法、结合分类结果进行预测    
    """
    
    def load_dataset_with_labels(all_id, all_X):
    
        id_X_dict = dict()
        id_list = []
        X_list = []
        y_list = []
        
        for idx in range(len(all_id)):
            id_X_dict[all_id[idx]] = all_X[idx]
    
        # 从数据库读取label，形成训练集与测试集
        conn = c.connect(user='root', password='ictwsn', 
                       host='127.0.0.1', database='curiosity_v3')
        cursor = conn.cursor()
        cursor.execute('''
            select feedid, datastreamid, labels as label
            from datastream_labeled_t
            where labels is not null
        ''', conn)
        
        result_list = cursor.fetchall()
        for (feedid, datastreamid, label) in result_list:
            id_list.append(str(feedid) + ',' + datastreamid)
            y_list.append(label)
        conn.close()
    
        for id_str in id_list:
            X_list.append(id_X_dict[id_str])

        # 90%作为训练，10%作为测试
        test_X = []
        test_y = []
        test_id = []

        train_X = []
        train_y = []
        train_id = []
    
        interval = int(len(id_list)/10)
        for idx in range(interval):
            test_X.append(X_list[idx])
            test_y.append(y_list[idx])
            test_id.append(id_list[idx])
            
        for idx in range(interval, len(y_list)):
            train_X.append(X_list[idx])
            train_y.append(y_list[idx])
            train_id.append(id_list[idx])
            
        # 使用RF训练数据
        rfc = RandomForestClassifier(n_estimators=100)
        rfc.fit(train_X, train_y)
        
        class_dict = dict()
        for idx, cls in enumerate(rfc.classes_):
            class_dict[cls] = idx
        
        test_proba = rfc.predict_proba(test_X) 
        
        train_proba = []
        class_num = len(test_proba[0])

        for y in train_y:
            distribution = [0.0]*class_num
            distribution[class_dict[y]] = 1.0
            train_proba.append(distribution)
            
        input_id = test_id + train_id
        input_proba = []
        for l in test_proba:
            input_proba.append(l)
        for l in train_proba:
            input_proba.append(l)
            
        rf_wrapper_dict = dict()
        for idx,i in enumerate(input_id):
            feedid, sensorid = i.split(',', 1)
            if feedid not in rf_wrapper_dict:
                fdict = dict()
                fdict[sensorid] = input_proba[idx]
                rf_wrapper_dict[feedid] = fdict
            else:
                rf_wrapper_dict[feedid][sensorid] = input_proba[idx]
                
        return rf_wrapper_dict, test_proba, test_y, rfc.classes_

        
    xively_series = pickle.load(open("step1_feature2.pickle", "rb"))
    all_id = xively_series['labels'] # 包含feedid和datastreamid拼接而来的list
    all_X = xively_series['X']

    rf_wrapper_dict, test_proba, test_y, cls_label = load_dataset_with_labels(all_id, all_X)
    
        
    ta = TA(rf_wrapper_dict)
    ta.run()
    ta.print_z()
    
