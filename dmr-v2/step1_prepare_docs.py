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
from subprocess import PIPE, CalledProcessError, Popen


STOP_WORDS = 'stopwords.txt'
FILE_FEATURES = 'features.txt'
FILE_TEXT = 'texts.txt'
FILE_FEEDID = 'id.txt'
FILE_SENSORID = 'sensor.txt'
MALLET_INSTANCE = 'mallet.instance'

DIR = 'output/'

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
    
    ft = codecs.open(DIR + FILE_TEXT, 'w', 'utf-8')
    ff = codecs.open(DIR + FILE_FEATURES, 'w', 'utf-8')
    fidf = codecs.open(DIR + FILE_FEEDID, 'w', 'utf-8')
    fids = codecs.open(DIR + FILE_SENSORID, 'w', 'utf-8')
    
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
    
    # 生成mallet.instance
    print('Create instance.mallet...')
    cmd = ['mallet', 'run', 'cc.mallet.topics.tui.DMRLoader', 
             FILE_TEXT, FILE_FEATURES, MALLET_INSTANCE]
             
    p = sp.Popen(cmd, stdout=sp.PIPE, shell=True, cwd=DIR)
    out, err = p.communicate()
    print(out)
    
    # 生成dmr.parameters和dmr.state.gz
    print('Create topic index...')
    p = sp.Popen(['mallet', 'run', 'cc.mallet.topics.DMRTopicModel',
             MALLET_INSTANCE, '30'], shell=True, stdout=sp.PIPE, cwd=DIR)
    out, err = p.communicate()
    print(out)
    
    #TODO 从out的最后几行读出主题号对应的：alpha值、主题数目信息
    
    
    pass

    
def tail( f, lines=20 ):
    total_lines_wanted = lines

    BLOCK_SIZE = 1024
    f.seek(0, 2)
    block_end_byte = f.tell()
    lines_to_go = total_lines_wanted
    block_number = -1
    blocks = [] # blocks of size BLOCK_SIZE, in reverse order starting
                # from the end of the file
    while lines_to_go > 0 and block_end_byte > 0:
        if (block_end_byte - BLOCK_SIZE > 0):
            # read the last block we haven't yet read
            f.seek(block_number*BLOCK_SIZE, 2)
            blocks.append(f.read(BLOCK_SIZE))
        else:
            # file too small, start from begining
            f.seek(0,0)
            # only read what was not read
            blocks.append(f.read(block_end_byte))
        lines_found = blocks[-1].count('\n')
        lines_to_go -= lines_found
        block_end_byte -= BLOCK_SIZE
        block_number -= 1
    all_read_text = ''.join(reversed(blocks))
    return '\n'.join(all_read_text.splitlines()[-total_lines_wanted:])

    

build_input()
call_dmr()
