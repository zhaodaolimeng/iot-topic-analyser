import datetime as dt
import mysql.connector as c

START_TIMESTAMP = dt.datetime.strptime("2016/12/04", "%Y/%m/%d").timestamp()

conn_1204 = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161204')
conn_1120 = c.connect(user='root', password='ictwsn', host='10.22.0.77', database='curiosity_20161120')

