# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


RULE_DIRS = [u'RuleDmacrs', u'RuleDmakis', u'RuleTwine', u'RuleMultiArr']
Headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.104 Safari/537.36'}
HFQ_URL = 'http://vip.stock.finance.sina.com.cn/api/json.php/BasicStockSrv.getStockFuQuanData'
TIMEOUT_SEC = 10
start_date = '20150101'

TIMESTAMP_FMT = "%Y-%m-%d"
INTERVAL = 200

KISS_THRESH1 = 0.08  # Last day DMA Less than Close_price*15%
KISS_THRESH2 = 0.05 # Kiss day DMA Less than Close_price*10%
KISS_THRESH3 = 0.1