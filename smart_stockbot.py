# -*- coding=utf-8 -*-
import os
import sys
import re
import time
import json
import requests
import logging
import traceback
import itertools
import multiprocessing
from logging.handlers import TimedRotatingFileHandler
import numpy as np
from lxml import etree
from datetime import datetime, timedelta, date
from operator import itemgetter, div, sub
from pushtarget import targets
from stockinfo import StockType, StockInfo
import settings

base_dir = os.path.dirname(os.path.realpath(__file__))
start_date = settings.start_date
end_date = date.today().strftime('%Y%m%d')
rule_dirs = settings.RuleFolders
Headers = settings.Headers
stock_info = StockInfo()


def CreateFolder():
	dailyfolder = os.path.join(base_dir, 'daily')
	if not os.path.exists(dailyfolder):
		os.mkdir(dailyfolder)	
	folder = datetime.today().strftime('%Y%m%d')
	folderpath = os.path.join(dailyfolder, folder)
	if not os.path.exists(folderpath):
		os.mkdir(folderpath)
	for item in rule_dirs:
		subfolder = os.path.join(folderpath, item)
		if not os.path.exists(subfolder):
			os.mkdir(subfolder)
	return folderpath, folder


def SetLogger(logger, dir, logName):
	if not os.path.exists(dir):
		os.makedirs(dir)
	logFileName = os.path.join(dir, logName)
	logHandler = TimedRotatingFileHandler(logFileName, when="midnight")
	logHandler.suffix = "%Y%m%d_%H%M%S.log"
	logFormatter = logging.Formatter('%(asctime)-12s:%(message)s')
	logHandler.setFormatter(logFormatter)
	streamHandle = logging.StreamHandler()
	streamHandle.setFormatter(logFormatter)
	logger.addHandler(logHandler)
	logger.addHandler(streamHandle)
	logger.setLevel(logging.WARNING)
	return logger


def push_to_mailbox(_msglist, _sendto):
	global logger
	import smtplib  
	from email.MIMEText import MIMEText  
	from email.Utils import formatdate  
	from email.Header import Header 
	smtpHost = 'smtp.sina.cn'
	fromMail = username = 'nuggetstock@sina.com'  
	password = 'welcome'
	subject  = u'[%s] 自动推荐'%datetime.today().strftime('%Y/%m/%d')
	body     = '\n'.join(_msglist) 
	mail = MIMEText(body,'plain','utf-8')  
	mail['Subject'] = Header(subject,'utf-8')  
	mail['From'] = fromMail  
	mail['To'] = _sendto
	mail['Date'] = formatdate() 
	try:  
		smtp = smtplib.SMTP_SSL(smtpHost)  
		smtp.ehlo()  
		smtp.login(username,password)
		smtp.sendmail(fromMail,_sendto,mail.as_string())  
		smtp.close()  
		logger.warning('Push to %s successfully.'%_sendto)
	except Exception as e:  
		logger.warning(str(e) + ' when pushing the msg with Mail.')
		
def CheckDate(_date):
	today = date.today()
	yesterday = today - timedelta(days=1)
	flag = _date in [today.strftime('%Y-%m-%d'),yesterday.strftime('%Y-%m-%d')]
	return flag

def GrabRealTimeStock(_stockid):
	url = 'http://hq.sinajs.cn/list=%s'%_stockid
	r = requests.get(url, headers = Headers)
	regx = re.compile(r'\=\"(.*)\"\;');
	m =  regx.search(r.text)
	info = m.group(0)
	infos = info.split(',')
	# Return Open/Close/High/Low/volume/Date
	return [eval(infos[1]),eval(infos[3]),eval(infos[4]),eval(infos[5]),eval(infos[8])/100,infos[30]] 
	
def GrabStock(_stockid, _begin , _end, _grabReal = False):
	Url = 'http://biz.finance.sina.com.cn/stock/flash_hq/kline_data.php?symbol=%s&end_date=%s&begin_date=%s' 
	_url = Url%(_stockid, _end, _begin)
	r = requests.get(_url, headers = Headers)
	page = etree.fromstring(r.text.encode('utf-8'))
	contents = page.xpath(u'/control/content')
	items = [[	float(content.attrib['o']), 
				float(content.attrib['c']), 
				float(content.attrib['h']), 
				float(content.attrib['l']), 
				float(content.attrib['v']),
				content.attrib['d']] for content in contents]
	todaydate = date.today().strftime('%Y-%m-%d')
	if todaydate != items[-1][-1] and _grabReal:
		latest = GrabRealTimeStock(_stockid)
		if latest[-1] == todaydate:
			items.append(latest)		
	return np.array(items)
	
def fast_moving_average(x, N):
     return np.convolve(x, np.ones((N,))/N, 'full')[:1-N]

	
def CalcExpMA(_list, _period):
	length = len(_list)
	def ExpMA(_list, n, N):
		return _list[0] if n == 0 else (_list[n]*2.0 + (N - 1.0)*ExpMA(_list, n-1,N))/( N +1.0)
	ExpMA = [ExpMA(_list,i,_period) for i in xrange(length)]
	return ExpMA
		
def detect_zero_points(_array):
	cross = np.roll(_array, -1) * _array
	indices = (cross < 0).nonzero()[0]
	return indices
	
def FindClose(_list):
	eps = 0.02
	npList = np.array(_list)
	indices = list((abs(npList)<eps).nonzero()[0])
	return indices
	
def calc_diff(_array):
	return np.hstack(([1],np.diff(_array)))*5

def CalcInteg(_list):
	return [sum(_list[0:i+1]) for i,elem in enumerate(_list)]
	
def calc_DMA(_close, Short = 5, Long = 89, Middle = 34):
	DDD = fast_moving_average(_close, Short) - fast_moving_average(_close, Long)
	AMA = fast_moving_average(DDD, Middle)
	DMA = DDD - AMA
	return DDD, AMA, DMA

def RuleGoldBar(_prices, _volumes, _date, _check = True):
	RecentP = _prices[-5:]
	RecentV = _volumes[-5:]
	C0 = CheckDate(_date) if _check else True
	C1 = RecentP[4]>RecentP[3]>RecentP[2]>RecentP[1]
	C2 = RecentV[4]<RecentV[3]<RecentV[2]<RecentV[1]
	C3 = (RecentP[1]-RecentP[0])/RecentP[0]>0.09
	Rule = False not in [C0,C1,C2,C3]
	return Rule
	
def RuleGoldCross(DDD, AMA, zero_indicies, cur_date, _check = True):
	DMA = DDD - AMA
	last_index = DDD.shape[0] - 1
	C0 = CheckDate(cur_date) if _check else True
	C1 = DMA[last_index]>0
	if zero_indicies.shape[0] < 3:
		C2 = C3 = C4 = C5 = C6 = C7 = C8 = False
	else:
		C2 = np.sum(DMA[zero_indicies[0]:zero_indicies[1]])>0
		C3 = np.sum(DMA[zero_indicies[1]:zero_indicies[2]])<=0
		C4 = np.sum(DMA[zero_indicies[0]:zero_indicies[2]])>0
		C5 = last_index - zero_indicies[-1] <= 2
		C6 = ((zero_indicies[1] - zero_indicies[0]) - 2*(zero_indicies[2] - zero_indicies[1]))>0
		C7 = (zero_indicies[2] - zero_indicies[1]) < 8
		C8 = AMA[zero_indicies[2]] - AMA[zero_indicies[1]] >= 0 or AMA[zero_indicies[2]] - AMA[zero_indicies[0]] > 0
	Rule = np.all([C0,C1,C2,C3,C4,C5,C6,C7,C8])
	return Rule

def RuleGoldKiss(DDD, AMA, zero_indx, Close, cur_date, _check = True):
	last_indx = DDD.shape[0] - 1
	DMA = DDD - AMA
	DIFF = calc_diff(DMA)
	AMADIFF = calc_diff(AMA)
	diff_zeros = detect_zero_points(DIFF)
	dma_after_zero = DMA[zero_indx:]
	MaxDMA, MaxDMAIndx = np.max(dma_after_zero), np.argmax(dma_after_zero), 
	C0 = CheckDate(cur_date) if _check else True
	C1 = 0<DMA[last_indx] < settings.KISS_THRESH1*Close[last_indx] # Last day DMA Less than Close_price*1.5%
	C2 = 0<DMA[diff_zeros[-1]]< settings.KISS_THRESH2*Close[diff_zeros[-1]] # Kiss day DMA Less than Close_price*10%
	C3 = MaxDMA > settings.KISS_THRESH3*Close[zero_indx+MaxDMAIndx]
	C4 = 5<=(last_indx - zero_indx)<=120 and (last_indx - diff_zeros[-1])<=2 # Last DMA Cross day within 9 weeks, Kiss day within 1 week
	C5 = DIFF[zero_indx] > 0
	C6 = DIFF[last_indx] >= 0
	C7 = AMADIFF[last_indx] > 0 or AMA[diff_zeros[-1]]-AMA[zero_indx] >0
	C8 = sum(DMA[zero_indx:]) > 0
	Rule = np.all([C0,C1,C2,C3,C4,C5,C6,C7,C8])
	return Rule	

def RuleGoldTwine(DDD, AMA, Close, _date, _check=True):
	DMA = DDD - AMA
	Recent = DMA[-16:]
	threshold = 0.01
	C0 = CheckDate(_date) if _check else True
	C1 = False not in [abs(item) < threshold*price for item, price in zip(Recent,Close)]
	Rule = False not in [C0, C1]
	return Rule
	
def RuleGoldWave(DDD, AMA, _zeroNdx, Close, _lastNdx, _date, _check = True):
	pass	

def RuleEXPMA(_list, _lastNdx, _date):
	EXP1 = CalcExpMA(_list,10)
	EXP2 = CalcExpMA(_list,50)
	DIFEXP = map(sub, EXP1, EXP2)
	EXPZeros = detect_zero_points(DIFEXP)	
	C0 = CheckDate(_date)
	C1 = DIFEXP[_lastNdx]>0
	C2 = (_lastNdx - EXPZeros[-1])<5
	Rule = False not in [C0,C1,C2]
	return Rule

def RuleMultiArrange(_close, _date):
	MA5  = fast_moving_average(_close, 5 )
	MA13 = fast_moving_average(_close, 13)
	MA21 = fast_moving_average(_close, 21)
	MA34 = fast_moving_average(_close, 34)
	MA55 = fast_moving_average(_close, 55)
	C0 = CheckDate(_date)
	C1 = MA5[-1] > MA13[-1] > MA21[-1] > MA34[-1] > MA55[-1]
	C2 = MA5[-2] > MA13[-2] > MA21[-2] > MA34[-2] > MA55[-2]
	C3 = MA5[-3] > MA13[-3] > MA21[-3] > MA34[-3] > MA55[-3]
	Rule = False not in [C0, C1,not C2, not C3]
	return Rule	
	
def CalcBoll(Close,N=89, k=2):
# Bollinger Bands consist of:
# an N-period moving average (MA)
# an upper band at K times an N-period standard deviation above the moving average (MA + Kσ)
# a lower band at K times an N-period standard deviation below the moving average (MA − Kσ)
# %b = (last − lowerBB) / (upperBB − lowerBB)
# Bandwidth tells how wide the Bollinger Bands are on a normalized basis. Writing the same symbols as before, and middleBB for the moving average, or middle Bollinger Band:
# Bandwidth = (upperBB − lowerBB) / middleBB
	length = len(Close)
	MA = fast_moving_average(Close, N).tolist()
	# MA = CalcExpMA(Close, N)
	SM = map(lambda x,y:(x-y)**2, Close, MA)
	MD = [(sum(SM[i-N+1:i+1] if i >= N-1 else (SM[0:i]+[SM[i]]*(N-i)))/float(N))**0.5 for i in xrange(length)]
	UP = map(lambda x,y:x+y*k, MA, MD)
	DN = map(lambda x,y:x-y*k, MA, MD)
	b = map(lambda x,y,z:(x-z)/(float(y-z) if y!=z else 1.0), Close, UP, DN)
	Band = map(lambda x,y,z:(x-z)/(float(y) if y!=0 else 1.0), UP, MD, DN)
	return MA, UP, DN, b, Band

def GrabHFQPrice(_stockid):
	hfqUrl = 'http://vip.stock.finance.sina.com.cn/api/json.php/BasicStockSrv.getStockFuQuanData'
	payload = {'symbol': _stockid,'type': 'hfq'}
	r = requests.get(hfqUrl, headers = Headers, params = payload)
	text = r.text[1:-1]
	text = text.replace('{_', '{"')
	text = text.replace('total', '"total"')
	text = text.replace('data', '"data"')
	text = text.replace(':"', '":"')
	text = text.replace('",_', '","')
	text = text.replace('_', '-')
	jdata = json.loads(text, encoding = 'utf-8')
	return jdata['data']


def GoldSeeker(stock_code, start_date, end_date, _num, _figure = False):
	global logger	
	results = ()
	try:
		# 1. Query stockid/stockname
		stockname = stock_info.get_stock_name(stock_code)
		stockcode = stock_info.get_stock_with_prefix(stock_code)

		# 2. Fetch Open/Close/High/Low/Volumn info of specified stock
		data = GrabStock(stockcode, start_date, end_date)

		# 3. Check if stock is on suspension.
		date_colume = data[:,-1]
		if not CheckDate(date_colume[-1]):
			logger.warning('Suspension%4s:%4s:%s'%(_num, stockname+(4-len(stockname))*'  ', stockcode))
			return ()

		# 4. Get houfuquan price to calculate DMA
		hfq_price = GrabHFQPrice(stock_code)
		hfq_close = np.array(map(lambda d: float(hfq_price[d]), date_colume))
		[DDD, AMA, DMA] = calc_DMA(hfq_close)		
		zero_ndx = detect_zero_points(DMA)
		if zero_ndx.shape[0] < 3:
			logger.warning('Newstock(<89d) %4s:%4s:%s'%(_num, stockname+(4-len(stockname))*'  ', stockcode))
			return ()

		volumes = data[:, 4]
		Cross = RuleGoldCross(DDD, AMA, zero_ndx[-3:], date_colume[-1])
		Kiss = RuleGoldKiss(DDD, AMA, zero_ndx[-1], hfq_close, date_colume[-1])		
		GoldBar = RuleGoldBar(hfq_close, volumes, date_colume[-1])
		Twine = RuleGoldTwine(DDD, AMA, hfq_close, date_colume[-1])
		MultiArr = RuleMultiArrange(hfq_close, date_colume[-1])
		category = ['']
		for index, item in enumerate([Cross, Kiss, GoldBar, Twine, MultiArr]):
			if item:
				RuleFolder = rule_dirs[index]
				# if _figure:
				# 	GenerateFigure(Open, Close, items)
				goldstock = '{0:8}- {1} {2}({3})'.format(RuleFolder[4:],stockcode[2:],stockname.encode('utf-8'), stock_info.get_stock_industry(stockcode[2:]).encode('utf-8'))
				category.append(RuleFolder[4:])
				results = (goldstock,AMA[-1])
		logger.warning('Complete%6s:%4s:%s %s'%(_num, stockname+(4-len(stockname))*'  ', stockcode, '@'.join(category)))
	except Exception as e:
		logger.error('Error: %s when processing %s..'%(e, stockcode)) # 
		print traceback.format_exc()

	return results

def sort_by_ama(_tupleList):
	OrderedResult = sorted(_tupleList, key=itemgetter(1))
	AMAOrderedResult = map(itemgetter(0), OrderedResult)
	OrderedResult = sorted(AMAOrderedResult,key=lambda x:x[0:4])
	return OrderedResult

def push_notifier(stocks, targets):
	if stocks:
		for target in targets:
			if   target['type'] == 'A':
				candidates = stocks
			elif target['type'] == 'D':
				candidates = [item for item in stocks if item[0]=='D']
			elif target['type'] == 'm':
				candidates = [item for item in stocks if item[1]=='m']
			else:
				candidates = [':( Sorry. Keep you money in your pocket safely. No stocks to push today.'] 		
			push_to_mailbox(candidates, target['mail'])
			time.sleep(2)

def mp_analyze( stocks ):
	result = []
	pool = multiprocessing.Pool(processes = 3)
	for index, stock in enumerate(stocks):
    		result.append(pool.apply_async(GoldSeeker, (stock, start_date, end_date, index,)))
	pool.close()
	pool.join()
	return [res.get() for res in result if res.get()]

log_ts = datetime.now().strftime('%Y%m%d_%H%M')
log_file = 'StockBot_%s.log' % log_ts
log_dir = os.path.join(base_dir, "logs")
logger = logging.getLogger('stock_bot')
logger = SetLogger(logger, log_dir, log_file)	

if __name__ == '__main__':
	baseFolder, folder = CreateFolder()
	stocks = stock_info.get_stocks()
	results = mp_analyze(stocks)
	resort_results = sort_by_ama(results)
	push_notifier(resort_results, targets)
