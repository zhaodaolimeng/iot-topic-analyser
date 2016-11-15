# -*- coding: utf-8 -*-
"""
Created on Sun Nov 13 15:30:16 2016

@author: limeng
"""

import mysql.connector as c
import collections
import langid
import re
import time
import codecs
import subprocess as sp

STOP_WORDS = 'stopwords.txt'
FILE_FEATURES = 'output/features.txt'
FILE_TEXT = 'output/texts.txt'
FILE_FEEDID = 'output/id.txt'
FILE_SENSORID = 'output/sensor.txt'
MALLET_INSTANCE = 'output/mallet.instance'

TMP_DIR = 'output/'

conn = c.connect(user='root', password='ictwsn', 
                     host='127.0.0.1', database='curiosity_v3')

'''
对于每个sensor生成文档，为了便于处理，直接生成一个临时表
'''

def build_input():
    
    feed_map = dict()
    
    print('Building feed_map...')
    
    cursor = conn.cursor()
    cursor.execute('''
        select id, description, device_name, lat, lng, created, iana
        from feed_t 
    ''')
    result = cursor.fetchall()
    
    print('Detecting languages...')
    
    count = 0
    for (feedid, description, device_name, lat, lng, created, iana) in result:
        
        if not description:
            continue
        if iana == '':
            iana, _ = langid.classify(description)
            cursor.execute('update feed_t set iana = %s where id = %s', (iana, feedid))
            conn.commit()
        if iana == 'en' :
            if lat is None or lng is None or created is None or \
                (description is None and device_name is None):
                continue
            
            feed_map[feedid] = dict()
            if description is None:
                description = ''
            if device_name is None:
                device_name = ''
                
            feed_map[feedid]['desc'] = description
            feed_map[feedid]['title'] = device_name
            feed_map[feedid]['lat'] = float(lat)
            feed_map[feedid]['lng'] = float(lng)
            feed_map[feedid]['created'] = created
        
        count+=1
        if count % 1000 == 0:
            print(count)

    with open(STOP_WORDS, 'r') as f:
        stoplist = set(f.read().split())
    
    print('Use feed_map to construct document per sensor...')
    
    ft = codecs.open(FILE_TEXT, 'w', 'utf-8')
    ff = codecs.open(FILE_FEATURES, 'w', 'utf-8')
    fidf = codecs.open(FILE_FEEDID, 'w', 'utf-8')
    fids = codecs.open(FILE_SENSORID, 'w', 'utf-8')
    
    cursor.execute('select feedid, streamid, tags from datastream_t')
    
    result = cursor.fetchmany(1000)
    while len(result) != 0:
        for (fid, sid, tags) in result:
            
            if fid not in feed_map:
                continue
            
            doc = str(feed_map[fid]['desc']) + str(feed_map[fid]['title'])\
                     + ' ' + str(sid) + ' ' + str(tags)

            #TODO 文本清理
            regular_word = collections.defaultdict(int)
            doc = doc.replace('\n', ' ')
            doc = re.sub(r"http\S+", "", doc)
            doc = re.sub(r"\d+", "", doc)
            doc = re.sub(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]', ' ', doc)
            wordlist = [w for w in doc.lower().split() if w not in stoplist and len(w)>1]
            for w in wordlist:
                regular_word[w] += 1

            if len(wordlist) == 0:
                continue
            
            doc = ' '.join(wordlist)
            ft.write(doc + '\n')
            
            #TODO 只用时间作为feature
            epoch = int(time.mktime(time.strptime('2007.01.01', '%Y.%m.%d')))
            create_time = int(feed_map[fid]['created'].timestamp() - epoch)
            lb_time = str(int(create_time / (3600*24*30*6)))
            ff.write(lb_time + '\n')
            fidf.write(str(fid) + '\n')
            fids.write(str(sid) + '\n')
            
        result = cursor.fetchmany(1000)
    
    print('Instance build done!')
    
def call_dmr():
    
    #TODO 生成mallet.instance
    print('Calling mallet to create instance.mallet...')
    sp.call(['mallet', 'run', 'cc.mallet.topics.tui.DMRLoader', 
             FILE_TEXT, FILE_FEATURES, MALLET_INSTANCE], 
             shell=True, cwd=TMP_DIR)
    
    #TODO 生成
    print('Calling mallet to create topic index...')
    sp.call(['mallet', 'run', 'cc.mallet.topics.DMRTopicModel',
             MALLET_INSTANCE, '30'], 
             shell=True, cwd=TMP_DIR)

build_input()
call_dmr()
