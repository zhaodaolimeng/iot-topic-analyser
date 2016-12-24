# -*- coding: utf-8 -*-
"""
特征数据准备，调用google reverse geo-encoding
create table feature_t(feedid bigint, created date, location_type varchar(50));
"""

if __name__ == "__main__":

    import mysql.connector as c
    from utils.ReverseGeo import reverse_geoencoding

    conn = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161204')
    cursor = conn.cursor()
    cursor.execute("select feedid from translation_t")

    print("Start fetching ...")
    f_list = cursor.fetchall()

    for tuple in f_list:
        feed_id = tuple[0]
        cursor = conn.cursor()
        cursor.execute("select lat, lng, created from feed_t where id = %s", tuple)
        lat, lng, created_time = cursor.fetchone()
        location_type = reverse_geoencoding(lat, lng)
        print(str(feed_id) + " done! Type = " + location_type)

        cursor = conn.cursor()
        cursor.execute("""
            insert into feature_t (feedid, created, location_type) values(%s, %s, %s)
        """, (feed_id, created_time, location_type))
        conn.commit()
