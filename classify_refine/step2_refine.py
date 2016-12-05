# -*- coding: utf-8 -*-

import pickle
import numpy as np
from .refiner import RfRefiner

if __name__ == "__main__":

    np.random.seed(0)  # 设定随机种子

    FILE_PREPARE = "prepare.pickle"
    test_set = pickle.load(open(FILE_PREPARE, "rb"))['dataset']

    def compute_acc(y, y_test):
        acc = len([c for idx, c in enumerate(y) if c == y_test[idx]])
        return 1.0 * acc / len(y)

    # 加载标签y
    y_trans = test_set.name2index
    index2name = dict()
    for k, v in test_set.name2index.items():
        index2name[v] = k

    # 获得仅使用Random Forest得到的结果
    test_size = int(test_set.size/10)  # 前1/10的数据为测试数据
    y_oracle = test_set.y[:test_size]

    rf_idx = [np.argmax(plist) for plist in test_set.p[:test_size]]
    y_before = [index2name[idx] for idx in rf_idx]
    print(compute_acc(y_oracle, y_before))

    refine = RfRefiner(test_set)
    sensor_choice = refine.run_once()
    y_after = [index2name[idx] for idx in sensor_choice[:test_size]]
    print(compute_acc(y_oracle, y_after))
