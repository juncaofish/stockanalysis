# -*- coding=utf-8 -*-
import os
from SARobot import StockQuery,ConvDateToStr,Headers
import re
import time
from datetime import datetime,date,timedelta
import requests
from lxml import etree
import matplotlib.pyplot as plt

url = 'http://biz.finance.sina.com.cn/stock/flash_hq/kline_data.php?symbol={0}&end_date={1}&begin_date={2}' 

def ConvStrToDate(_str):
	ymd = time.strptime(_str,'%Y-%m-%d')
	return date(*ymd[0:3])

stockid = '000099'
currentpath  = os.path.realpath(__file__)
basedir = os.path.dirname(currentpath)
stockname, stockid = StockQuery(stockid)
folderpath =os.path.join(basedir, 'analysis\\'+stockid)
files = os.listdir(folderpath)
for item in files:
	dirpath = os.path.join(folderpath, item)
	pngs = os.listdir(dirpath)
	# codes = [png.split()[1].split('.')[0] for png in pngs]
	dates = [png.split()[1].split('.')[0] for png in pngs]
	for dateitem in dates:
		begin_date_str = ConvDateToStr(ConvStrToDate(dateitem))
		end_date_str = ConvDateToStr(ConvStrToDate(dateitem) +  timedelta(days=28))		
		link = url.format(stockid,  end_date_str,begin_date_str)
		r = requests.get(link, headers = Headers)
		page = etree.fromstring(r.text.encode('utf-8'))
		contents = page.xpath(u'/control/content')
		closePrices = [eval(content.attrib['c']) for content in contents]
		idx = xrange(len(closePrices))
		plt.plot(idx,closePrices,'r-o')
		plt.title(stockid+' ' +begin_date_str +' '+ item[4:])
		plt.show()





