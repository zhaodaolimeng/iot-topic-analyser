# -*- coding: utf-8 -*-
"""
数据无缺失时DMR和TFIDF的Rank对比
每次输入为所有的数据集，以feed_t.title作为输入
"""
from utils.TextCleaner import string_trim
import lib.BM25 as b
import lib.DMR as d
import codecs
import random
import pickle
import mysql.connector as c


def fetch_description(desc_file, connection):
    """
    生成DMR的输入文件
    :param desc_file:
    :return:
    """
    cursor = connection.cursor()
    cursor.execute("select feedid, translated from translation_t", connection)
    fid_list = []
    with codecs.open(desc_file, 'r') as ft:
        result = cursor.fetchmany(10000)
        while len(result) != 0:
            for feedid, translated in result:
                trimmed = string_trim(translated)
                if len(trimmed)>0:
                    ft.write(trimmed)
                    fid_list.append(feedid)
            result = cursor.fetchmany(10000)
    return fid_list


def fetch_feature_and_save_to_file(feed_ids, features_file, connection):
    cursor = connection.cursor()
    cursor.execute('select feedid, lat, lng, created from feed_t')
    result = cursor.fetchall()
    # TODO features加工
    pass

if __name__ == '__main__':

    random.seed(0)
    conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161204')
    file_text = 'output/text.txt'
    file_features = 'output/features.txt'

    fid_list = fetch_description(file_text, conn)
    fetch_feature_and_save_to_file(fid_list, file_features, conn)

    bm25 = b.BM25(file_text)
    dmr = d.DMR(file_text, file_features, topic_num=30)

    cursor = conn.cursor()
    cursor.execute("select id, title from feed_t where title is not null")
    result = cursor.fetchall()

    d_result = []
    b_result = []

    for fid, title in result:
        query = string_trim(title)
        query_list = query.split(" ")
        dscore = dmr.optimized_score(query_list, bm25)
        bscore = bm25.bm25_score(query_list)

        # 检查fid在rank的位置
        f_idx = fid_list.index(fid)
        d_result.append(len([score for score in dscore if score > dscore[f_idx]]))
        b_result.append(len([score for score in bscore if score > bscore[f_idx]]))

    pickle.dump((d_result, b_result), open('test1_result.pickle', 'wb'))
