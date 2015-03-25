# -*- coding=utf-8 -*-
import os
from StockList import stock
from SARobot import StockQuery,ConvDateToStr,Headers,GetStockList
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



def CalcStockRuleRate(stocknum):
	stockname, stockid = StockQuery(stocknum)
	folderpath =os.path.join(basedir, 'analysis\\'+stockid)
	files = os.listdir(folderpath)
	RulePercent = {'name':stockname, 'id':stockid}
	for item in files:
		count = 0
		dirpath = os.path.join(folderpath, item)
		pngs = os.listdir(dirpath)
		# codes = [png.split()[1].split('.')[0] for png in pngs]
		dates = [png.split()[1].split('.')[0] for png in pngs]
		for dateitem in dates:
			begin_date_str = ConvDateToStr(ConvStrToDate(dateitem))
			end_date_str = ConvDateToStr(ConvStrToDate(dateitem) +  timedelta(days=60))		
			link = url.format(stockid, end_date_str,begin_date_str)
			r = requests.get(link, headers = Headers)
			page = etree.fromstring(r.text.encode('utf-8'))
			contents = page.xpath(u'/control/content')[0:period]
			InitPrice = eval(contents[0].attrib['c'])
			closePrice = eval(contents[-1].attrib['c'])
			percent = (closePrice - InitPrice)/InitPrice
			if percent > 0.1:
				count +=1
		try:
			RulePercent[item] = '%.2f%%' % (100.0*count/len(dates))
		except:
			RulePercent[item] = None
	return RulePercent
	
if __name__ == '__main__':
	currentpath  = os.path.realpath(__file__)
	basedir = os.path.dirname(currentpath)
	stockfolders = os.listdir(os.path.join(basedir, 'analysis'))
	period = 20
	stocknums = GetStockList()
	stocknums = [item[2:] for item in stockfolders]
	print stocknums
	for stocknum in stocknums:
		Result = CalcStockRuleRate(stocknum)
		print Result['name'],Result
			# idx = xrange(len(closePrices))
			# plt.plot(idx,closePrices,'r-o')
			# plt.title(stockid+' ' +begin_date_str +' '+ item[4:])
			# plt.show()





