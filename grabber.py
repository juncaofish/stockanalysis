# -*- coding=utf-8 -*-

import json
import re

import requests

from settings import Headers, HFQ_URL, TIMEOUT_SEC


def grab_stock_rt(_stockid):
    url = 'http://hq.sinajs.cn/list=%s' % _stockid
    r = requests.get(url, headers=Headers)
    regex = re.compile(r'\=\"(.*)\"\;')
    m = regex.search(r.text)
    info = m.group(0)
    info = info.split(',')
    return [eval(info[1]), eval(info[3]), eval(info[4]), eval(info[5]), eval(info[8]) / 100, info[30]]


def grab_hfq_price(stock_code):
    payload = {'symbol': stock_code, 'type': 'hfq'}
    try:
        r = requests.get(HFQ_URL, headers=Headers, params=payload, timeout=TIMEOUT_SEC)
        text = r.text[1:-1]
        text = text.replace('{_', '{"').replace('total', '"total"').replace('data', '"data"') \
            .replace(':"', '":"').replace('",_', '","').replace('_', '-')
        json_data = json.loads(text, encoding='utf-8')
        return json_data['data']
    except requests.exceptions.Timeout:
        return None
