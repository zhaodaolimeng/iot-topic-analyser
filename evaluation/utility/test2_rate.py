"""
在不同补全率下，验证查询结果
"""

import random
import mysql.connector as c

if __name__ == '__main__':

    random.seed(0)
    conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161204')
    file_text = 'output/text.txt'
    file_features = 'output/features.txt'


