#! /usr/bin/env python
# -*- encoding: utf-8 -*-

RuleFolders = [u'RuleDmacrs',u'RuleDmakis',u'RuleGoldbar',u'RuleTwine',u'RuleMultiArr']
Headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.104 Safari/537.36'}
start_date = '20150101'

KISS_THRESH1 = 0.1  # Last day DMA Less than Close_price*15%
KISS_THRESH2 = 0.08 # Kiss day DMA Less than Close_price*10%
KISS_THRESH3 = 0.08