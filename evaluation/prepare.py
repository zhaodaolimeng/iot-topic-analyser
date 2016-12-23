# -*- coding: utf-8 -*-
"""
数据准备，调用百度翻译
"""

if __name__ == "__main__":

    import mysql.connector as c
    import pandas as pd
    import utils.translator as trans
    import functools as ft
    import collections

    db_conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161204')

    # 将feed_t.description、datastream_t.tags、datastream_t.streamid统一进行拼接
    print("Start fetching ...")
    label_df = pd.read_sql("""
        select
            id as feedid,
            feed_t.description as d,
            feed_t.device_name as dn,
            feed_t.exposure as ex,
            feed_t.title as t,
            ds_desc_t.group_desc as gd
        from feed_t, (
            SELECT feedid, GROUP_CONCAT(concat(streamid, '. ', tags) SEPARATOR '. ') as group_desc
            FROM datastream_t GROUP BY feedid
        ) as ds_desc_t
        where feed_t.id = ds_desc_t.feedid
    """, db_conn)
    rawtext_dict = {val['feedid']:
                  ft.reduce(lambda x, y: x + ("" if y is None else str(y)) + ". ",
                            ["", val['d'], val['dn'], val['ex'], val['t'], val['gd']])
                    for _, val in label_df.iterrows()}

    print("Fetch done, total result = " + str(len(rawtext_dict)))
    print("Start to translate ... ")

    # result_dict = dict()
    for feed_id, desc in collections.OrderedDict(sorted(rawtext_dict.items())).items():

        if feed_id < 118495:
            continue

        print(desc[:100 if len(desc) > 100 else len(desc) - 1])

        ret, iana = trans.baidu_translate(desc)
        print("Feedid = " + str(feed_id) + " done! Length = " + str(len(ret)))

        ret = ret.replace("'", " ").replace('"', " ").replace("\n", " ")
        cursor = db_conn.cursor()
        cursor.execute("""
            insert into translation_t (feedid, iana, translated) values(%s, %s, %s)
        """, (feed_id, iana, ret))
        db_conn.commit()

    # pickle.dump(open('translate_result.pickle', 'wb'), result_dict)
    print("All translation done!")
