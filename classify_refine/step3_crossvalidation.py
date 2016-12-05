# -*- coding: utf-8 -*-

if __name__ == "__main__":

    import pickle
    import numpy as np
    import mysql.connector as c
    from sklearn.ensemble import RandomForestClassifier
    from utils.dataset import Dataset
    from classify_refine.refiner import RfRefiner

    def load_dataset():

        xively_series = pickle.load(open("../classify/step1_feature2.pickle", "rb"))
        id_label_dict = {l: xively_series['X'][i_l] for i_l, l in enumerate(xively_series['labels'])}
        labeled = Dataset()

        conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_v3')
        cursor = conn.cursor()
        cursor.execute('''select feedid, datastreamid, labels as label
            from datastream_labeled_t where labels is not null''', conn)
        result_list = cursor.fetchall()
        for (feedid, datastreamid, label) in result_list:
            id_str = str(feedid) + ',' + datastreamid
            labeled.add_item(id_str, id_label_dict[id_str], str(label))
        conn.close()

        return labeled

    def compute_acc(y, y_test):
        acc = len([c_y for idx_y, c_y in enumerate(y) if c_y == y_test[idx_y]])
        return 1.0 * acc / len(y)

    dataset_labeled = load_dataset()  # 读入数据

    np.random.seed(0)  # K-means中的随机种子
    fold_num = 10
    for fold_cnt in range(fold_num):

        test_set, train_set = dataset_labeled.data_split(fold_num, fold_cnt)
        print('Fold = ' + str(fold_cnt) + '\ttest = ' + str(test_set.size) + '\ttrain = ' + str(train_set.size))

        # 使用分类预测结果
        rfc = RandomForestClassifier(n_estimators=100)
        rfc.fit(train_set.X, train_set.y)
        preds = rfc.predict(train_set.X)
        test_proba = rfc.predict_proba(test_set.X).tolist()
        class_dict = {cls: i_cls for i_cls, cls in enumerate(rfc.classes_)}
        index2name = rfc.classes_

        # 测试集部分概率向量中，对应的位置直接为1
        for i in range(train_set.size):
            arr = [0.0] * len(class_dict)
            arr[class_dict[train_set.y[i]]] = 1.0
            test_proba.append(arr)

        # 合并数据集
        test_set.data_merge(train_set)
        test_set.p = test_proba

        # 获得仅使用Random Forest得到的结果
        test_size = int(test_set.size/fold_num)  # 前1/10的数据为测试数据
        y_oracle = test_set.y[:test_size]

        rf_idx = [np.argmax(plist) for plist in test_set.p[:test_size]]
        y_before = [index2name[idx] for idx in rf_idx]
        print(compute_acc(y_oracle, y_before))

        refine = RfRefiner(test_set)
        for i in range(3):
            sensor_choice = refine.run_once()

        y_after = [index2name[idx] for idx in sensor_choice[:test_size]]
        print(compute_acc(y_oracle, y_after))
