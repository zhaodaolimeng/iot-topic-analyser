"""
1. 网络流中前后两层的权重配比lambda的实验
2. K-means中的K对结果的影响
"""
from evaluation.parameters.DataLoader import *
from sklearn.ensemble import RandomForestClassifier

if __name__ == "__main__":

    np.random.seed(0)
    all_tuple, all_label, all_feature = prepare_data()
    n_fold = 10
    n_per_fold = int(len(all_tuple) / n_fold)

    # 对于K-means中的参数K
    print("Test parameters in K-means ... ")
    for k in range(2, 20, 2):
        print('For k = ' + str(k))
        for i in range(n_fold):
            test_tuple, test_label, test_feature, train_tuple, train_label, train_feature = \
                slice_dataset(all_tuple, all_feature, all_label, n_per_fold, i)

            rfc = RandomForestClassifier(n_estimators=100)
            rfc.fit(train_feature, train_label)

            index2name = rfc.classes_  # 概率对应位置的标签
            name2index = {cls: idx for idx, cls in enumerate(rfc.classes_)}
            result_proba = rfc.predict_proba(test_feature).tolist()

            # 1. 使用常规方法
            sensor_choice = [np.argmax(p) for p in result_proba]
            y_before = [index2name[idx] for idx in sensor_choice]
            acc_before = compute_acc(test_label, y_before)
            # 2. 使用常规方法+优化
            y_after = predict_with_different_parameters(
                all_tuple, train_label, i, n_per_fold, index2name, name2index, result_proba, _k=10, _lambda=0.01)

            acc_after = compute_acc(test_label, y_after)
            print(str(acc_before) + ', ' + str(acc_after))

