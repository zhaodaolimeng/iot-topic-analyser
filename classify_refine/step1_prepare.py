# -*- coding: utf-8 -*-

if __name__ == "__main__":
    
    import pickle
    import mysql.connector as c
    from sklearn.ensemble import RandomForestClassifier
    from utils.dataset import Dataset
    
    FILE_FEATURE = "../classify/step1_feature2.pickle"
    FILE_PREPARE = "prepare.pickle"
    
    '''
    只用有人工标注标签的数据进行实验
    '''
    def load_dataset():
        
        xively_series = pickle.load(open(FILE_FEATURE, "rb"))
        id_label_dict = dict()
        
        for idx, l in enumerate(xively_series['labels']):
            id_label_dict[l] = xively_series['X'][idx]

        dataset_labeled = Dataset()
        conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_v3')
        cursor = conn.cursor()
        cursor.execute('''
            select feedid, datastreamid, labels as label
            from datastream_labeled_t where labels is not null
        ''', conn)
        
        result_list = cursor.fetchall()
        for (feedid, datastreamid, label) in result_list:
            id_str = str(feedid) + ',' + datastreamid
            dataset_labeled.add_item(id_str, id_label_dict[id_str], str(label))
            
        conn.close()
        return dataset_labeled
        
    
    dataset_labeled = load_dataset()
    test_set, train_set = dataset_labeled.data_split()

    rfc = RandomForestClassifier(n_estimators=100)
    rfc.fit(train_set.X, train_set.y)
    preds = rfc.predict(train_set.X)
    test_proba = rfc.predict_proba(test_set.X).tolist()
    
    class_dict = dict()
    for idx, cls in enumerate(rfc.classes_):
        class_dict[cls] = idx
    
    # 测试集部分概率向量中，对应的位置直接为1
    for i in range(train_set.size):
        arr = [0.0]*len(class_dict)
        arr[class_dict[train_set.y[i]]] = 1.0
        test_proba.append(arr)
        
    # 合并数据集
    test_set.data_merge(train_set)
    result_dict = dict()
    result_dict['dataset'] = test_set
    test_set.p = test_proba
    test_set.name2index = class_dict
    
    pickle.dump(result_dict, open(FILE_PREPARE, 'wb'))
