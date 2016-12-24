# -*- coding: utf-8 -*-

import hashlib
import time
import requests
import langid
import json


def baidu_translate(q):
    """
    调用百度翻译
    :param q:
    :return:
    """
    appid = '20160901000027920'
    secret_key = 'pCa6vXL65ZddoC1cinrk'
    uri = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
    salt = 35000

    # 检查是否是英文，如果不是英文则使用百度翻译
    iana, _ = langid.classify(q)
    if iana == 'la' and "Cost UK Gateway" in q:
        iana = 'en'  # FIXME dirty hack

    if iana == 'en':
        print("EN detected, skip.")
        return q, iana

    print(iana + " detected, fire translation post ...")
    ret = ''
    while len(q) > 0:
        input_str = ''
        if len(q) > 1500:
            input_str = q[0:1500]
            q = q[1500:]
        else:
            input_str = q
            q = ''

        sign = (appid + input_str + str(salt) + secret_key).encode('utf-8')
        m1 = hashlib.md5()
        m1.update(sign)
        sign = m1.hexdigest()

        data = {
            'appid': appid,
            'q': input_str,
            'from': 'auto',
            'to': 'en',
            'salt': salt,
            'sign': sign
        }
        r = requests.post(uri, data)
        data = json.loads(r.text)

        # 某些内容可能出现无法翻译
        try:
            ret += data['trans_result'][0]['dst']
        except Exception as ex:
            print(ex)
            return '', iana
        time.sleep(1)
        print(ret[:500 if len(ret) > 500 else len(ret) - 1])

    return ret, iana
