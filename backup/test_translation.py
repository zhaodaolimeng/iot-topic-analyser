# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 10:55:22 2016

@author: limeng
"""
 
import http.client
import urllib
import hashlib
import random
import requests

appid = '20160901000027920'
secretKey = 'pCa6vXL65ZddoC1cinrk'

q = '''
    ArduinoとEthernetShieldでモニタリング環境構築。
    滋賀県米原市柏原
    木造2F設置宅内24時間弱換気あり
    においセンサーTGS-2450使用
    電圧降下＝においセンサー反応ありです。'''

def test_get():
    httpClient = None
    myurl = '/api/trans/vip/translate'
        
    q = '这是一个测试'    
    fromLang = 'auto'
    toLang = 'en'
    salt = random.randint(32768, 65536)
    salt = 35000
    
    sign = (appid+q+str(salt)+secretKey).encode('utf-8')
    m1 = hashlib.md5()
    m1.update(sign)
    sign = m1.hexdigest()
    
    print('Sign = ' + sign)
    myurl = myurl + '?appid=' + appid + \
            '&q=' + urllib.parse.quote(q) + \
            '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(salt) + '&sign='+sign
     
    try:
        httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
        httpClient.request('GET', myurl)
        
        print(myurl)
     
        #response是HTTPResponse对象
        response = httpClient.getresponse()
        print(response.read())
        
    except Exception as e:
        print(e)
    finally:
        if httpClient:
            httpClient.close()

# 使用POST请求，请求内容可直接是raw的（必须是raw的，不然md5计算失败）
def test_post():
    q = '这是一个测试'
    appid = '20160901000027920'
    secretKey = 'pCa6vXL65ZddoC1cinrk'
    salt = random.randint(32768, 65536)
    salt = 35000
    
    sign = (appid+q+str(salt)+secretKey).encode('utf-8')
    m1 = hashlib.md5()
    m1.update(sign)
    sign = m1.hexdigest()
#    q_str = urllib.parse.quote(q)
    print('Sign = ' + sign)
    
#    print('Raw text = ' + q_str)
    data={
        'appid': appid, 
        'q': q, 
        'from': 'auto',
        'to': 'en',
        'salt': salt,
        'sign': sign
    }
    myurl = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
    print(myurl)
    
    r = requests.post(myurl, data)
    ret = r.text
    print('Translation = ' + ret)
    print(sign)
    
print("====================")
test_get()
print("====================")
test_post()


