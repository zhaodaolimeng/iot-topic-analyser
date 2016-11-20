# -*- coding: utf-8 -*-
"""
Created on Fri Nov 18 17:19:28 2016

@author: limeng
"""

"""
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

class SDF:
    
    """
    rf_dict是dict()结构
    key为feedid，即每个应用的标识
    value为dict()，内容为sensorid和每个sensor对应的分布
    K为主题个数
    alpha为Dirichlet分布的超参数
    
    当sensorid为已观测设备时，统一起见仍构造成分布的形式
    """    
    def __init__(self, rf_dict, K=10, alpha=0.1):
        
        
        
        pass
    
    
    """
    主方法，使用gibbs sampling
    对于每个应用的每个sensor，更新条件概率分布
    """
    def run(self, max_iter):
        
        
        
        pass
    
    
    """
    p(z_i|z_~i, theta)
    每次需要更新
    """
    def conditional_distribution(self):
        
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

        return id_list, X_list, y_list

    
    """
    临时测试前10%的数据
    """
    def test_single(id_list, X_list, y_list):
        # 80%作为训练，20%作为测试
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
        
        return test_proba, test_id, train_proba, train_id

        
    xively_series = pickle.load(open("step1_feature2.pickle", "rb"))
    all_id = xively_series['labels'] # 包含feedid和datastreamid拼接而来的list
    all_X = xively_series['X']

    id_list, X_list, y_list = load_dataset_with_labels(all_id, all_X)
    test_proba, test_id, train_proba, train_id = test_single(id_list, X_list, y_list)
    
    input_id = test_id + train_id
    input_proba = []
    for l in test_proba:
        input_proba.append(l)
    for l in train_proba:
        input_proba.append(l)
    
    rf_wrapper_dict = dict()
    for idx in range(len(input_id)):
        rf_wrapper_dict[input_id[idx]] = {'p': input_proba[idx]}
    
    sdf = SDF(rf_wrapper_dict)
    
    
    
