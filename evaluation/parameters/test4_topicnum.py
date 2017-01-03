"""
主题数目对结果的影响
"""
import random
import pickle
import mysql.connector as c

from lib.BM25 import BM25
from lib.DMR import DMR
from utils.DMRHelper import *


if __name__ == '__main__':

    random.seed(0)
    conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161226')
    w_dir = 'output/'
    file_text = 'text.in'
    file_features = 'features.in'
    final_result = w_dir + 'test4_result.pickle'

    with codecs.open(settings.DEFINITIONS_ROOT + '/resource/stopwords.txt', 'r') as f:
        stoplist = set(f.read().split())

    cursor = conn.cursor()
    cursor.execute("select id, tags from feed_t where tags is not null")
    query_tuples = cursor.fetchall()

    result_topic = []
    for topic_num in [2, 3, 4, 5, 10, 20, 40, 50, 100, 200]:
        # dmr + 未补全的效果
        print("Topic number = " + str(topic_num) + " ...")
        f_list, regular_set = fetch_and_save_feature(w_dir + file_text, w_dir + file_features, conn)
        bm25 = BM25(file_text, work_dir=w_dir)
        dmr = DMR(file_text, file_features, topic_num=topic_num, work_dir=w_dir)

        d_result = []
        f_set = set(f_list)
        cnt = 0
        for fid, tags in query_tuples:
            cnt += 1
            if cnt % 10 != 0:
                continue
            if fid not in f_set:
                continue
            query_list = [w for w in trim_str(tags, stoplist) if w in regular_set]
            if len(query_list) == 0:
                continue
            dscore = dmr.optimized_score(query_list, bm25)

            # 检查fid在rank的位置
            print(fid)
            f_idx = f_list.index(fid)
            d_rank = len([score for score in dscore if score > dscore[f_idx]])
            d_result.append(d_rank)
        result_topic.append(d_result)

    pickle.dump(result_topic, open(final_result, 'wb'))
