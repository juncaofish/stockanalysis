# -*- coding=utf-8 -*-
import os
from SARobot import StockGrab, StockQuery
import re
import time
from datetime import datetime,date
import requests
from lxml import etree
import matplotlib.pyplot as plt

_dirname = r'C:\Users\jcao.APAC\Documents\GitHub\stockanalysis\analysis20150323'
id = '002304'
currentpath  = os.path.realpath(__file__)
basedir = os.path.dirname(currentpath)
stockname, stockid = StockQuery(id)
folderpath =os.path.join(basedir, 'analysis20150323\\'+stockid)
files = os.listdir(folderpath)
for item in files:
	dirpath = os.path.join(folderpath, item)
	pngs = os.listdir(dirpath)
	# codes = [png.split()[1].split('.')[0] for png in pngs]
	dates = [png.split()[1].split('.')[0] for png in pngs]
	print dates

reg = 's[h|z]?\d{6}'
_dirname = r'C:\Users\jcao.APAC\Documents\GitHub\stockanalysis\20150226\RuleKiss'
Headers = {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'}
url = 'http://biz.finance.sina.com.cn/stock/flash_hq/kline_data.php?symbol={0}&end_date={1}&begin_date={2}' 	
files = os.listdir(_dirname)

def FileCreateTime(file):
	AbsPath = os.path.join(_dirname,file)
	TimeStr = datetime.fromtimestamp(os.path.getmtime(AbsPath)).strftime('%Y%m%d')
	return TimeStr

dates = map(FileCreateTime, files)

codes = filter(lambda x:x is not '', map(lambda item: re.search(reg,item) and re.search(reg,item).group(0) or '', files))
today = date.today().strftime('%Y%m%d')
# p = dict(zip(codes, dates))
urls = [url.format(code, today, date) for code, date in zip(codes,dates)]

items = zip(codes, dates, urls)

d = {}
for code,date,link in items:
	r = requests.get(link, headers = Headers)
	page = etree.fromstring(r.text.encode('utf-8'))
	contents = page.xpath(u'/control/content')
	closePrices = [eval(content.attrib['c']) for content in contents]
	d[code] = closePrices
	idx = xrange(len(closePrices))
	plt.plot(idx,closePrices,'r-o')
plt.show()




