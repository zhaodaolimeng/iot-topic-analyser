# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 10:55:22 2016

@author: limeng
"""
 
import http.client
import urllib
import hashlib
import random

appid = '20160901000027920'
secretKey = 'pCa6vXL65ZddoC1cinrk'

 
httpClient = None
myurl = '/api/trans/vip/translate'
q = '''
    ArduinoとEthernetShieldでモニタリング環境構築。
    滋賀県米原市柏原
    木造2F設置宅内24時間弱換気あり
    においセンサーTGS-2450使用
    電圧降下＝においセンサー反応ありです。'''
    
fromLang = 'auto'
toLang = 'en'
salt = random.randint(32768, 65536)

sign = (appid+q+str(salt)+secretKey).encode('utf-8')
m1 = hashlib.md5()
m1.update(sign)

sign = m1.hexdigest()
myurl = myurl + '?appid=' + appid + \
        '&q=' + urllib.parse.quote(q) + \
        '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(salt) + '&sign='+sign
 
try:
    httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
    httpClient.request('GET', myurl)
 
    #response是HTTPResponse对象
    response = httpClient.getresponse()
    print(response.read())
    
except Exception as e:
    print(e)
finally:
    if httpClient:
        httpClient.close()
