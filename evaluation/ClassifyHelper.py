import numpy as np
import networkx as nx


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


def result_refine(tuples, sensor_p, choices, max_iter=3, _mu=10, _lambda=0.01):
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

    for run_once in range(max_iter):
        cluster_label, mu_list = kmeans(group_p, n_mu=_mu, max_iter=10)  # 执行一次聚类

        group_dict = dict()  # 找到每个组对应的sensor的id
        for idx, f in enumerate(feedid):
            if f not in group_dict:
                group_dict[f] = []
            group_dict[f].append(idx)

        for idx, cluster in enumerate(cluster_label):
            sensor_proba = []  # 当前组每个节点的分布 n*len(features[0])
            sensor_id_list = []
            for sensor_idx in group_dict[group_id[idx]]:
                sensor_proba.append(sensor_p[sensor_idx])
                sensor_id_list.append(sensor_idx)

            choice = adjust_sensor_choice(sensor_proba, mu_list[cluster], portion_lambda=_lambda)
            for inner_idx, sensor_idx in enumerate(sensor_id_list):
                choices[sensor_idx] = choice[inner_idx]

    return choices


def compute_acc(y, y_test):
    acc = len([c_y for idx_y, c_y in enumerate(y) if c_y == y_test[idx_y]])
    return 1.0 * acc / len(y)