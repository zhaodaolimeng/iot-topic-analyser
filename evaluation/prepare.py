# -*- coding: utf-8 -*-
"""
特征数据准备，调用google reverse geo-encoding
create table feature_t(feedid bigint, created date, location_type varchar(50));
insert into features_t (feedid) select id from feed_t as T;
"""
import functools as ft
import mysql.connector as c
import pandas as pd
import utils.Translator as trans
import collections
from utils.OpenstreetApi import location_type


def update_location_type(conn):
    cursor = conn.cursor()
    print("Loading feedid ...")
    query_set = set()
    cursor.execute("select feedid, location_type from features_t where location_type is NULL")
    for feed_id,_ in cursor.fetchall():
        query_set.add(feed_id)

    cursor.execute("select id, lat, lng, created from feed_t")
    for feed_id, lat, lng, created_time in cursor.fetchall():
        if feed_id not in query_set:
            continue
        l_type = location_type(lat, lng)
        print(str(feed_id) + "= " + l_type)
        cursor.execute("""
            update features_t set
            created = %s, location_type = %s where feedid = %s
        """, (created_time, l_type, feed_id))
        conn.commit()


def update_translation(conn):
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
        ) as ds_desc_t where feed_t.id = ds_desc_t.feedid
    """, conn)
    rawtext_dict = {val['feedid']:
                        ft.reduce(lambda x, y: x + ("" if y is None else str(y)) + ". ",
                                  ["", val['d'], val['dn'], val['ex'], val['t'], val['gd']])
                    for _, val in label_df.iterrows()}

    print("Fetch done, total result = " + str(len(rawtext_dict)))
    print("Start to translate ... ")

    for feed_id, desc in collections.OrderedDict(sorted(rawtext_dict.items())).items():
        # if feed_id < 343203114:
        #     continue

        print(desc[:100 if len(desc) > 100 else len(desc) - 1])
        ret, iana = trans.baidu_translate(desc)
        print("Feedid = " + str(feed_id) + " done! Length = " + str(len(ret)))
        ret = ret.replace("'", " ").replace('"', " ").replace("\n", " ")

        cursor = conn.cursor()
        cursor.execute("""
            insert into translation_t (feedid, iana, translated) values(%s, %s, %s)
        """, (feed_id, iana, ret))
        conn.commit()


if __name__ == "__main__":

    db_conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161226')
    update_location_type(db_conn)
    # update_translation(db_conn)

