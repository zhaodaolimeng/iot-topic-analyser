# -*- coding: utf-8 -*-
"""
Created on Thu Apr 14 19:57:13 2016

@author: limeng
"""

# 文件将从feed_t中识别每个条目对应的语言，填写iana标志位

import mysql.connector as c
import langid

conn = c.connect(user='root', password='ictwsn', host='127.0.0.1', database='curiosity_lda')

try:
    cursor = conn.cursor()
    cursor.execute('select id,description from feed_t')
    result = cursor.fetchall()

    for (id,description) in result:
        if not description:
            continue
        iana, _ = langid.classify(description)
        print(str(id) + str('\t') + iana + str('\t') + description)
        cursor.execute('update feed_t set iana = %s where id = %s', (iana, id))
        conn.commit()

finally:
    conn.close()

print('Words clean done!')

# 数据库之后会执行如下操作：
# insert into document_t(document) select description from feed_t where iana = 'en'
# update feed_t left join document_t on description = document set feed_t.docid = document_t.id;
