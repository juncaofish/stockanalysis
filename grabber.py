# -*- coding=utf-8 -*-

import json
import re

import requests
from requests.adapters import HTTPAdapter

from settings import Headers, HFQ_URL, TIMEOUT_SEC
from helper import yesterday, today

s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=3))


def grab_stock_rt(_stockid):
    url = 'http://hq.sinajs.cn/list=%s' % _stockid
    r = requests.get(url, headers=Headers)
    regex = re.compile(r'\=\"(.*)\"\;')
    m = regex.search(r.text)
    info = m.group(0)
    info = info.split(',')
    return [eval(info[1]), eval(info[3]), eval(info[4]), eval(info[5]), eval(info[8]) / 100,
            info[30]]


def grab_hfq_price(stock_code):
    payload = {'symbol': stock_code, 'type': 'hfq'}
    try:
        r = s.get(HFQ_URL, headers=Headers, params=payload, timeout=TIMEOUT_SEC)
        text = r.text[1:-1]
        text = text.replace('{_', '{"').replace('total', '"total"').replace('data', '"data"') \
            .replace(':"', '":"').replace('",_', '","').replace('_', '-')
        json_data = json.loads(text, encoding='utf-8')
        return json_data['data']
    except requests.exceptions.Timeout:
        return None


def dapan(code='sh000001'):
    url = 'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
    payload = {'param': '{code},day,{start},{end},2,hfq'.format(code=code,
                                                                start=yesterday,
                                                                end=today)}
    try:
        r = s.get(url, headers=Headers, params=payload, timeout=TIMEOUT_SEC)
        result = r.json()
        data = result['data'][code]['day']
        close = eval(data[-1][2])
        pre_close = eval(data[0][2])
        percent = (close - pre_close) / pre_close
        code_data = {'code': code, 'close': close, 'percent': percent}
        return code_data
    except requests.exceptions.Timeout:
        return None


if __name__ == '__main__':
    print(dapan())
