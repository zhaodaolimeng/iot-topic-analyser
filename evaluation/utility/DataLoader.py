# -*- coding: utf-8 -*-
"""
特征数据准备：
    create table features_t (
        feedid bigint(20),
        streamid varchar(50),
        doc text,  -- 一个datastream对应的文本描述，使用feed的description和datastream的id进行拼接得到
        iana varchar(20),
        location_type varchar(50),
        created date
    );
"""
import mysql.connector as c
from utils.OpenstreetApi import location_type
from utils.DMRHelper import is_english


def trim_concat(s_arr):
    return ". ".join(["" if s is None else s for s in s_arr])


def gather_text(doc_dict, conn):
    print("Loading datastream_t ...")
    cnt = 0
    cursor.execute("select feedid, streamid, tags from datastream_t")
    for f_id, streamid, streamtags in cursor.fetchall():
        cnt += 1
        if cnt % 1000 == 0:
            print(cnt)
        if f_id in doc_dict:
            doc = doc_dict[f_id] + '. ' + streamid + '. ' + streamtags
            if is_english(doc):
                cursor.execute("""
                    insert into features_t (feedid, streamid, doc)
                    values (%s, %s, %s)
                """, (f_id, streamid, doc))
                conn.commit()


def gather_features(geo_dict, conn):
    print("update location_type ... ")
    for f_id, value in geo_dict.items():
        lat, lng, created_time = value
        ltype = location_type(lat, lng)
        cursor.execute("""
            update features_t set
                location_type = %s, created = %s
            where feedid = %s
        """, (ltype, created_time, f_id))
        conn.commit()


if __name__ == "__main__":

    db_conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161226')
    cursor = db_conn.cursor()
    cursor.execute("""
        select id, description, device_name, title, tags, lat, lng, created
        from feed_t where lat is not null and lng is not null
    """)
    d_dict = {}
    g_dict = {}
    for feed_id, description, device_name, title, tags, \
        lat, lng, created_time in cursor.fetchall():
        d_dict[feed_id] = trim_concat([description, device_name, title, tags])
        g_dict[feed_id] = (lat, lng, created_time)

    gather_text(d_dict, db_conn)
    # gather_features(g_dict, db_conn)
