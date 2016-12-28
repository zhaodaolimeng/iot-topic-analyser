import pickle
from random import shuffle
from sklearn.ensemble import RandomForestClassifier
from evaluation.ClassifyHelper import *


def prepare_data():
    raw_dict = pickle.load(open('../../classify/p_label_feature.pickle', 'rb'))
    label_dict = raw_dict['label_dict']
    feature_dict = raw_dict['feature_dict']
    _tuple = [fs_tuple for fs_tuple, v in label_dict.items()]
    _label = [label_dict[fs_tuple] for fs_tuple in _tuple]
    _feature = [feature_dict[fs_tuple] for fs_tuple in _tuple]
    bundle = [(_tuple[i], _label[i], _feature[i]) for i in range(len(_tuple))]
    shuffle(bundle)   # 随机化
    for i in range(len(bundle)):
        _tuple[i] = bundle[i][0]
        _label[i] = bundle[i][1]
        _feature[i] = bundle[i][2]
    return _tuple, _label, _feature


def slice_dataset(tuples, features, labels, _num_per_fold, _idx):
    _test_tuple = tuples[_idx * _num_per_fold:(_idx + 1) * _num_per_fold]
    _test_label = labels[_idx * _num_per_fold:(_idx + 1) * _num_per_fold]
    _test_feature = features[_idx * _num_per_fold:(_idx + 1) * _num_per_fold]
    _train_tuple = tuples[0:_idx * _num_per_fold] + tuples[(_idx + 1) * _num_per_fold:]
    _train_label = labels[0:_idx * _num_per_fold] + labels[(_idx + 1) * _num_per_fold:]
    _train_feature = features[0:_idx * _num_per_fold] + features[(_idx + 1) * _num_per_fold:]
    return _test_tuple, _test_label, _test_feature, _train_tuple, _train_label, _train_feature


def predict_with_different_parameters(
        _all_tuple, _label, _idx, _num_per_fold,
        _index2name, _name2index, _result_proba,
        _max_iter=3, _k=10, _lambda=0.01):
    test_proba = []
    for ii in range(_idx * _num_per_fold):
        arr = [0.0] * len(_index2name)
        arr[_name2index[_label[ii]]] = 1.0
        test_proba.append(arr)
    test_proba += _result_proba
    for ii in range(_idx * _num_per_fold, len(_label)):
        arr = [0.0] * len(_index2name)
        arr[_name2index[_label[ii]]] = 1.0
        test_proba.append(arr)
    _choice = [np.argmax(p) for p in test_proba]
    _choice = result_refine(_all_tuple, test_proba, _choice, max_iter=_max_iter, _mu=_k, _lambda=_lambda)  # 结果优化
    preds = [_index2name[idx] for idx in _choice[_idx * _num_per_fold:(_idx + 1) * _num_per_fold]]
    return preds
