"""
使用不完整描述标签的进行描述信息进行补全
"""
import random
import pickle
import mysql.connector as c
import pandas as pd

from classify.SensorClassifier import SensorClassifier, fetch_raw_datapoints
from lib.BM25 import BM25
from lib.DMR import DMR
from utils.DMRHelper import *


if __name__ == '__main__':

    random.seed(0)

    pickle.dump(rank_result, open(final_result, 'wb'))
