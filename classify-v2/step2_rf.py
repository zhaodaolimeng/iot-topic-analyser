import pickle
import networkx as nx
import numpy as np
from random import shuffle
from sklearn.ensemble import RandomForestClassifier


def kmeans(features, n_mu=10, max_iter=10):
    cluster_label = [0] * len(features)
    mu_list = np.random.rand(n_mu, len(features[0]))  # 每个聚类的中心K*27
    mu_list /= np.matrix(np.sum(mu_list, axis=1)).T

    for iter_times in range(max_iter):
        for i, x in enumerate(features):
            distance = np.asarray([sum((mu - x) ** 2) for mu in mu_list])
            cluster_label[i] = distance.argmin()

        mu_count = [0] * n_mu
        mu_sum = np.zeros((n_mu, len(features[0])))

        for i, x in enumerate(features):
            mu_sum[cluster_label[i]] += x
            mu_count[cluster_label[i]] += 1

        for idx, mu_feature in enumerate(mu_list):
            if mu_count[idx] != 0:
                mu_list[idx] = mu_sum[idx] / mu_count[idx]
    return cluster_label, mu_list


def adjust_sensor_choice(sensor_proba, type_target, portion_lambda=0.01, rounding_scale=10):
    n_sensors = len(sensor_proba)
    graph_edge = []
    for idx, p_si in enumerate(sensor_proba):
        graph_edge.append((0, 1 + idx, {'capacity': 1, 'weight': 0}))
        for idx_t, _ in enumerate(type_target):
            if p_si[idx_t] != 0:
                st = {'capacity': 1, 'weight': 1.0 / p_si[idx_t]}
                graph_edge.append((1 + idx, 1 + idx_t + n_sensors, st))

    for idx_t, t in enumerate(type_target):
        s = sum(type_target)
        if t != 0:
            st = {'capacity': n_sensors, 'weight': 1.0 * portion_lambda * s / t}
            graph_edge.append((1 + n_sensors + idx_t, 1 + n_sensors + len(type_target), st))

    # 当weight和capacity为浮点数时方法失效，所以将权重进行rounding
    min_weight = min([e[2]['weight'] for e in graph_edge if e[2]['weight'] > 0])
    ratio = rounding_scale / min_weight
    for e in graph_edge:
        e[2]['weight'] = int(ratio * e[2]['weight'])

    graph = nx.DiGraph()
    graph.add_edges_from(graph_edge)
    flow_dict = nx.max_flow_min_cost(graph, 0, 1 + n_sensors + len(type_target))

    choice = []
    for node_idx in range(n_sensors):
        if 1 + node_idx in flow_dict:
            alist = [to for to, c in flow_dict[1 + node_idx].items() if c == 1]
            choice.append(np.argmax(sensor_proba[node_idx]) if len(alist) == 0 else alist[0] - n_sensors - 1)
    return choice


def result_refine(tuples, sensor_p, choices, max_iter=3):
    """
    输入的tuples和其他对应的位全部是乱序的
    返回sensor类型的选择状态sensor_choice
    """
    feedid = [tuples[i][0] for i, _ in enumerate(tuples)]
    n_types = len(sensor_p[0])

    group_p = []  # 存储每个组的概率
    group_id = []  # 存储每个组的id
    group_cnt_dict = dict()
    for i in range(len(tuples)):
        if tuples[i][0] not in group_cnt_dict:
            group_cnt_dict[tuples[i][0]] = [0]*n_types
        cnt = group_cnt_dict[tuples[i][0]]
        cnt[choices[i]] += 1

    for k, v in group_cnt_dict.items():
        group_id.append(k)
        group_p.append(np.asarray(v) / np.sum(v))

    print('group_id, group_p prepared!')

    for run_once in range(max_iter):
        cluster_label, mu_list = kmeans(group_p, max_iter=10)  # 执行一次聚类
        print('k-means done!')

        group_dict = dict()  # 找到每个组对应的sensor的id
        for idx, f in enumerate(feedid):
            if f not in group_dict:
                group_dict[f] = []
            group_dict[f].append(idx)

        for idx, cluster in enumerate(cluster_label):
            sensor_proba = []  #当前组每个节点的分布 n*len(features[0])
            sensor_id_list = []
            for sensor_idx in group_dict[group_id[idx]]:
                sensor_proba.append(sensor_p[sensor_idx])
                sensor_id_list.append(sensor_idx)

            choice = adjust_sensor_choice(sensor_proba, mu_list[cluster])
            for inner_idx, sensor_idx in enumerate(sensor_id_list):
                choices[sensor_idx] = choice[inner_idx]

        print('Adjust done!')

    return choices


def compute_acc(y, y_test):
    acc = len([c_y for idx_y, c_y in enumerate(y) if c_y == y_test[idx_y]])
    return 1.0 * acc / len(y)


raw_dict = pickle.load(open('p_label_feature.pickle', 'rb'))
label_dict = raw_dict['label_dict']
feature_dict = raw_dict['feature_dict']

n_fold = 10
n_per_fold = int(len(label_dict)/n_fold)
all_tuple = [fs_tuple for fs_tuple, v in label_dict.items()]
all_label = [label_dict[fs_tuple] for fs_tuple in all_tuple]
all_feature = [feature_dict[fs_tuple] for fs_tuple in all_tuple]

bundle = [(all_tuple[i], all_label[i], all_feature[i]) for i in range(len(all_tuple))]
shuffle(bundle)
for i in range(len(bundle)):
    all_tuple[i] = bundle[i][0]
    all_label[i] = bundle[i][1]
    all_feature[i] = bundle[i][2]

for i in range(n_fold):
    test_tuple = all_tuple[i * n_per_fold:(i + 1) * n_per_fold]
    test_label = all_label[i * n_per_fold:(i + 1) * n_per_fold]
    test_feature = all_feature[i * n_per_fold:(i + 1) * n_per_fold]
    train_tuple = all_tuple[0:i * n_per_fold] + all_tuple[(i + 1) * n_per_fold:]
    train_label = all_label[0:i * n_per_fold] + all_label[(i + 1) * n_per_fold:]
    train_feature = all_feature[0:i * n_per_fold] + all_feature[(i + 1) * n_per_fold:]

    rfc = RandomForestClassifier(n_estimators=100)
    rfc.fit(train_feature, train_label)

    index2name = rfc.classes_  # 概率对应位置的标签
    name2index = {cls: idx for idx, cls in enumerate(rfc.classes_)}
    test_proba = []
    result_proba = rfc.predict_proba(test_feature).tolist()

    for ii in range(i*n_per_fold):
        arr = [0.0] * len(index2name)
        arr[name2index[train_label[ii]]] = 1.0
        test_proba.append(arr)

    test_proba += result_proba

    for ii in range(i*n_per_fold, len(train_tuple)):
        arr = [0.0] * len(index2name)
        arr[name2index[train_label[ii]]] = 1.0
        test_proba.append(arr)

    sensor_choice = [np.argmax(p) for p in test_proba]
    y_before = [index2name[idx] for idx in sensor_choice]
    print(compute_acc(all_label, y_before))
    sensor_choice = result_refine(all_tuple, test_proba, sensor_choice)  # 结果优化
    y_after = [index2name[idx] for idx in sensor_choice]
    print(compute_acc(all_label, y_after))
