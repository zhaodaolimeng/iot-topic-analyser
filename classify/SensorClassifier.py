"""
生产环境模型
"""
import math
import pywt
import numpy as np
import networkx as nx
import datetime as dt
from scipy.interpolate import interp1d
from scipy.stats import variation, linregress
from sklearn.ensemble import RandomForestClassifier


def fetch_raw_datapoints(db_conn, tuple_list):
    """
    从数据库读取指定(feedid,streamid)对应的数据序列
    该方法放到这里是因为sql connection在类中无法被序列化
    """
    series_dict = dict()  # 每个(feedid, datastreamid)对应一个(time_at, val)的list
    cursor = db_conn.cursor()
    for f_id, s_id in tuple_list:
        cursor.execute("""
            select feedid, datastreamid, time_at, val from datapoint_t
            where feedid=%s and datastreamid=%s
        """, (f_id, s_id))
        series_dict[(f_id, s_id)] = [(time_at, val) for _, _, time_at, val in cursor.fetchall()]
    return series_dict


class SensorClassifier:

    def __init__(self):
        self.model = None
        self.index2name = {}
        self.name2index = {}
        self.start_timestamp = dt.datetime.strptime("2016-12-04 00:00:00", "%Y-%m-%d %H:%M:%S").timestamp()

    def train_model(self, label_dict, raw_series_dict):

        print("Compute features for each datastream...")
        feature_dict = self.compute_feature(raw_series_dict)
        print("Features created! Start modeling...")

        all_tuple = [fs_tuple for fs_tuple, v in feature_dict.items()]
        all_feature = [feature_dict[fs_tuple] for fs_tuple in all_tuple]
        all_label = [label_dict[fs_tuple] for fs_tuple in all_tuple]

        self.model = RandomForestClassifier(n_estimators=100)
        self.model.fit(all_feature, all_label)
        self.index2name = self.model.classes_  # 概率对应位置的标签
        self.name2index = {cls: idx for idx, cls in enumerate(self.model.classes_)}

    def pred(self, X):
        result_proba = self.model.predict_proba(X).tolist()
        sensor_choice = [np.argmax(p) for p in result_proba]
        predict_labels = [self.index2name[idx] for idx in sensor_choice]
        return predict_labels

    @staticmethod
    def magic(x, threshold=200):
        return x / abs(x) * (threshold + math.log(abs(x - threshold + 1))) if abs(x) > threshold else x

    def compute_feature(self, series_dict):
        f_dict = dict()
        for fd_tuple, series in series_dict.items():
            feature = self.compute_feature_single(series)
            if feature is not None:
                f_dict[fd_tuple] = feature
        return f_dict

    def compute_feature_single(self, series):
        """
        特征由以下构成：
        (1) 小波分解，得到的ac和dc计算得到小波系数（能量？好像还有一个系数？）
        (2) 线性回归计算得到的回归系数（整体趋势）
        (3) 不同数值的分布
        (4) 最高点到最低点的斜率，以及其他点对于该直线的回归系数（每天的周期性）
        (5) 充分利用昼夜特征，即两个最低点之间的距离（如果是周期的，则该值应当是1440）
        :return f_dict: 每个序列的特征向量
        """
        if len(series) < 20:
            return None
        len_of_2days = 1440 * 2
        feature = []
        samples = []
        # 对数据进行插值
        tlist = [(series[i][0].timestamp() - self.start_timestamp) / 60 for i in range(len(series))]
        vlist = [series[i][1] for i in range(len(series))]
        tlist = [0] + tlist + [len_of_2days]
        vlist = [vlist[0]] + vlist + [vlist[-1]]
        try:
            interp_f = interp1d(tlist, vlist)
            for cur_time in range(0, len_of_2days, 10):
                v = interp_f(cur_time)  # 每十分钟进行一次采样
                samples.append(self.magic(v))
        except ValueError:
            print("Too few points...")
            return None

        # 常规参数
        sample_np = np.array(samples)
        s_ave = np.average(sample_np)
        feature.append(s_ave)
        feature.append(variation(sample_np))
        feature.append(np.min(sample_np))
        feature.append(np.max(sample_np))

        # 小波系数
        w_coeff = pywt.wavedec(samples, 'haar', level=5)
        feature.append(np.linalg.norm(w_coeff[0]))
        feature.append(np.linalg.norm(w_coeff[1]))
        feature.append(np.linalg.norm(w_coeff[2]))
        feature.append(np.linalg.norm(w_coeff[3]))
        feature.append(np.linalg.norm(w_coeff[4]))

        # 对于均值的zero cross
        zc = [i for i in range(1, sample_np.size - 1) if (sample_np[i] - s_ave) * (sample_np[i - 1] - s_ave) > 0]
        feature.append(len(zc))

        # 一阶回归之后的整体趋势
        slope, intercept, r_value, p_value, std_err = linregress(sample_np.tolist(), list(range(len(sample_np))))
        feature.append(slope)
        feature.append(intercept)
        feature.append(r_value)
        feature.append(p_value)
        feature.append(std_err)

        # 检查数据有效性
        is_invalid = False
        for f in feature:
            if math.isnan(f) or math.isinf(f):
                is_invalid = True
                break
        if is_invalid:
            print("Invalid value ...")
            return None
        return feature

    @staticmethod
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

    def adjust_sensor_choice(self, sensor_proba, type_target, portion_lambda=0.01, rounding_scale=10):
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

    def result_refine(self, tuples, sensor_p, choices, max_iter=3):
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
                group_cnt_dict[tuples[i][0]] = [0] * n_types
            cnt = group_cnt_dict[tuples[i][0]]
            cnt[choices[i]] += 1

        for k, v in group_cnt_dict.items():
            group_id.append(k)
            group_p.append(np.asarray(v) / np.sum(v))

        print('group_id, group_p prepared!')

        for run_once in range(max_iter):
            cluster_label, mu_list = self.kmeans(group_p, max_iter=10)  # 执行一次聚类
            print('k-means done!')

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

                choice = self.adjust_sensor_choice(sensor_proba, mu_list[cluster])
                for inner_idx, sensor_idx in enumerate(sensor_id_list):
                    choices[sensor_idx] = choice[inner_idx]

            print('Adjust done!')

        return choices

    pass
