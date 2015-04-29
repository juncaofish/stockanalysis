# -*- coding=utf-8 -*-
import os
import re
import time
import requests
import pushybullet as pb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from lxml import etree
from datetime import datetime,timedelta,date
from operator import itemgetter, div, sub
from StockList import stock
from PyFetion import *
from PhoneList import Targets

font = FontProperties(fname=r"c:\windows\fonts\simsun.ttc", size=14) 
M5clr  = '#0000CC'
M10clr = '#FFCC00'
M20clr = '#CC6699'
M30clr = '#009966'
DDDclr = '#000000'
AMAclr = '#FF0033'
DMAclr = '#0066FF'
VARclr = '#3300FF'
EXP1clr = '#FF00FF'
EXP2clr = '#3300CC'
RuleFolders = [u'RuleDmacrs',u'RuleDmakis',u'RuleGoldbar',u'RuleDblQaty',u'RuleTwine']
Headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.111 Safari/537.36'}

def GetIndustry(_stockid):
	data =  pd.read_csv(os.path.join(BaseDir(), r'data\all.csv'), dtype={'code':'object'}, encoding='GBK')
	industry = data.ix[data.code==_stockid,['industry']].values[0][0]
	return industry

def BaseDir():
	currentpath  = os.path.realpath(__file__)
	basedir = os.path.dirname(currentpath)
	return basedir
	
def CreateFolder():
	dailyfolder = os.path.join(BaseDir(), 'daily')
	if not os.path.exists(dailyfolder):
		os.mkdir(dailyfolder)	
	folder = datetime.today().strftime('%Y%m%d')
	folderpath = os.path.join(dailyfolder, folder)
	if not os.path.exists(folderpath):
		os.mkdir(folderpath)
	for item in RuleFolders:
		subfolder = os.path.join(folderpath, item)
		if not os.path.exists(subfolder):
			os.mkdir(subfolder)
	return folderpath,folder

def PushwithPb(_list, _title):
	KEY = "pdaXjHTgQJ9s5sZRdfi93BMTz4CjICGl"
	try:
		api = pb.PushBullet(KEY)
		device = api['LGE Nexus 4']
		# print device.nickname
		push = pb.ListPush(_list, _title)
		api.push(push, device)
	except Exception as e:
		print str(e) + ' when pushing msg with pushbullet.'
		
def PushwithFetion(_msglist, _sendto):
	phone = PyFetion('13788976646', 'a5214496','TCP',debug=False)
	phone.login(FetionHidden)
	idx = 1
	try:
		while len(_msglist)>10:
			sendlist = _msglist[0:10]
			phone.send_sms('\n'.join([str(idx)+':']+sendlist), _sendto)
			_msglist = _msglist[10:]
			idx += 1
			time.sleep(5)
		phone.send_sms('\n'.join([str(idx)+':']+_msglist), _sendto)	
	except Exception as e:
		print str(e) + ' when pushing the msg with Fetion.'
	
def CheckDate(_date):
	today = date.today()
	yesterday = today - timedelta(days=1)
	flag = _date in [today.strftime('%Y-%m-%d'),yesterday.strftime('%Y-%m-%d')]
	return flag

def ConvStrToDate(_str):
	ymd = time.strptime(_str,'%Y%m%d')
	return date(*ymd[0:3])
	
def ConvDateToStr(_date):	
	return _date.strftime('%Y%m%d')
	
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
	items = [[eval(content.attrib['o']),eval(content.attrib['c']),eval(content.attrib['h']),eval(content.attrib['l']),eval(content.attrib['v']),content.attrib['d']] for content in contents]
	todaydate = date.today().strftime('%Y-%m-%d')
	if todaydate != items[-1][-1] and _grabReal:
		latest = GrabRealTimeStock(_stockid)
		if latest[-1] == todaydate:
			items.append(latest)		
	return items

def StockQuery(_stockname): 
	m = re.match(r'\d{6}', _stockname)
	stockid = _stockname if m else stock.get(_stockname)
	stockname = stock.get(_stockname) if m else _stockname
	stockloc = 'sh' if stockid[0] == '6' else 'sz'
	stockid = stockloc + stockid
	return stockname.decode('utf-8'), stockid	
	
def GetColumn(_array, _column):
	return [itemgetter(_column)(row) for row in _array]

def GetPart(_indices, _list):
	return [_list[idx] for idx in _indices]	
	
def MovingAverage(_array, _idx, _width):
	length = len(_array)
	if length < _width:
		raise Exception("The width exceeds maximum length of stocks ")
	else:
		if type(_array[0]) == type([]):
			return [sum([itemgetter(_idx)(elem) for elem in _array[i-_width+1:i+1]])/float(_width) if i >= _width-1 else _array[i][_idx] for i in xrange(length)]
		else: 
			return [sum( _array[i-_width+1:i+1] if i >= _width-1 else (_array[0:i]+[_array[i]]*(_width-i)))/float(_width) for i in xrange(length)]
	
def CalcExpMA(_list, _period):
	length = len(_list)
	def ExpMA(_list, n, N):
		return _list[0] if n == 0 else (_list[n]*2.0 + (N - 1.0)*ExpMA(_list, n-1,N))/( N +1.0)
	ExpMA = [ExpMA(_list,i,_period) for i in xrange(length)]
	# ExpMA2 = [ExpMA(List,i,50) for i in xrange(length)]
	return ExpMA
		
def RisingPercent(_array):
	length = len(_array)
	return [100.0*(itemgetter(1)(_array[i]) - itemgetter(1)(_array[i-1]))/itemgetter(1)(_array[i-1]) if i >=1 else 0 for i in xrange(length)]
	
def CalcVar(_array):
	varvalue = [np.var(GetColumn(_array, i)) for i in xrange(len(_array[0]))]
	return varvalue
	
def NormVol(_list):
	return [10.0*elem/max(_list) for elem in _list]

def FindZero(_list):
	L_S1 = _list[1:]+[_list[-1]]
	npList = np.array(_list)
	npL_S1 = np.array(L_S1)
	multi = npList*npL_S1
	indices = list((multi < 0).nonzero()[0])
	indices = [index if abs(_list[index])<abs(_list[index+1]) else index+1 for index in indices]
	return indices
	
def FindClose(_list):
	eps = 0.02
	npList = np.array(_list)
	indices = list((abs(npList)<eps).nonzero()[0])
	return indices
	
def CalcDiff(_list):
	L1 = _list[1:]+[_list[-1]]
	L2 = [_list[0]]+_list[0:-1]
	Diff = list(np.array(map(sub, L1, L2))*5.0)
	return Diff

def CalcInteg(_list):
	return [sum(_list[0:i+1]) for i,elem in enumerate(_list)]
	
def GetStockList():		
	return [id for id, sname in stock.items() if re.match(r'\d{6}', id)]

def CalcMA(_array):
	MA1 = MovingAverage(_array, 1, 1)
	MA5 = MovingAverage(_array, 1, 5)
	MA10 = MovingAverage(_array, 1, 10)
	MA20 = MovingAverage(_array, 1, 20)
	MA30 = MovingAverage(_array, 1, 30)
	VAR = CalcVar( [MA1,MA5, MA10, MA20, MA30] )	
	MACluster = {'MA1':MA1, 'MA5':MA5, 'MA10':MA10, 'MA20':MA20, 'MA30':MA30, 'VAR':VAR}
	return MACluster

def CalcDMA(_array, Short = 5, Long = 89, Middle = 34):
	DDD = map(sub, MovingAverage(_array, 1, Short) , MovingAverage(_array, 1, Long))
	AMA = MovingAverage(DDD, 0, Middle)
	DMA = map(sub, DDD , AMA)
	# DMACluster = {'DMA':DMA, 'AMA':AMA, 'DIF':DIF}
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
	
def RuleGoldCross(DDD, AMA, _zeroNdxs, _lastNdx, _date, _check = True):
	DMA = map(sub, DDD , AMA)
	DIFF = CalcDiff(DMA)
	C0 = CheckDate(_date) if _check else True
	C1 = DMA[_lastNdx]>0
	C2 = sum(DMA[_zeroNdxs[0]:_zeroNdxs[1]])>0
	C3 = sum(DMA[_zeroNdxs[1]:_zeroNdxs[2]])<=0
	C4 = sum(DMA[_zeroNdxs[0]:_zeroNdxs[2]])>0
	C5 = _lastNdx - _zeroNdxs[2] < 2
	C6 = ((_zeroNdxs[1] - _zeroNdxs[0]) - 2*(_zeroNdxs[2] - _zeroNdxs[1]))>0
	C7 = (_zeroNdxs[2] - _zeroNdxs[1]) < 8
	C8 = AMA[_zeroNdxs[2]] - AMA[_zeroNdxs[1]] >= 0 or AMA[_zeroNdxs[2]] - AMA[_zeroNdxs[0]] > 0
	Rule = False not in [C0,C1,C2,C3,C4,C5,C6,C7,C8]
	return Rule	
	
def RuleGoldKiss(DDD, AMA, _zeroNdx, Close, _lastNdx, _date, _check = True):
	DMA = map(sub, DDD , AMA)
	DIFF = CalcDiff(DMA)
	AMADIFF = CalcDiff(AMA)
	DFZeros = FindZero(DIFF)
	DMAAfterZero = DMA[_zeroNdx:]
	MaxDMA, MaxIndx = max( (v, i) for i, v in enumerate(DMAAfterZero) )		
	C0 = CheckDate(_date) if _check else True
	C1 = 0<DMA[_lastNdx]<0.04*Close[_lastNdx] # Last day DMA Less than Close_price*1.5%
	C2 = 0<DMA[DFZeros[-1]]<0.02*Close[DFZeros[-1]] # Kiss day DMA Less than Close_price*1%
	C3 = MaxDMA > 0.03*Close[_zeroNdx+MaxIndx]
	C4 = 5<=(_lastNdx - _zeroNdx)<=60 and (_lastNdx - DFZeros[-1])<=1 # Last DMA Cross day within 9 weeks, Kiss day within 1 week
	C5 = DIFF[_zeroNdx] > 0
	C6 = DIFF[_lastNdx] >= 0
	C7 = AMADIFF[_lastNdx] > 0 or AMA[DFZeros[-1]]-AMA[_zeroNdx] >0
	C8 = sum(DMA[_zeroNdx:]) > 0
	Rule = False not in [C0,C1,C2,C3,C4,C5,C6,C7,C8]	
	return Rule	

def RuleGoldTwine(DDD, AMA, Close, _date, _check=True):
	DMA = map(sub, DDD, AMA)
	Recent = DMA[-10:]
	threshold = 0.02
	C0 = CheckDate(_date) if _check else True
	C1 = False not in [abs(item) < threshold*price for item, price in zip(Recent,Close)]
	Rule = False not in [C0, C1]
	return Rule
	
def RuleGoldWave(DDD, AMA, _zeroNdx, Close, _lastNdx, _date, _check = True):
	pass	

def RuleDoubleQuantity(_prices, _volumes, _date, _check = True):
	RecentP = _prices[-4:]
	RecentV = _volumes[-33:]
	MeanV = np.mean(RecentV[0:30])
	MaxIndx = max( (v, i) for i, v in enumerate(RecentV) )[1]	
	C0 = CheckDate(_date) if _check else True
	C1 = False not in [ R>2.0*MeanV for R in RecentV[-3:]]
	C2 = MaxIndx >= 30
	C3 = RecentP[1] > RecentP[0] and RecentP[3] > RecentP[1]
	C4 = 0.07<= (RecentP[3] - RecentP[0])/RecentP[0] <=0.1
	Rule = False not in [C0,C1,C2,C3,C4]	
	return Rule	
	
def RuleEXPMA(_list, _lastNdx, _date):
	EXP1 = CalcExpMA(_list,10)
	EXP2 = CalcExpMA(_list,50)
	DIFEXP = map(sub, EXP1, EXP2)
	EXPZeros = FindZero(DIFEXP)	
	C0 = CheckDate(_date)
	C1 = DIFEXP[_lastNdx]>0
	C2 = (_lastNdx - EXPZeros[-1])<5
	Rule = False not in [C0,C1,C2]
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
	MA = MovingAverage(Close,0,N)
	# MA = CalcExpMA(Close, N)
	SM = map(lambda x,y:(x-y)**2, Close, MA)
	MD = [(sum(SM[i-N+1:i+1] if i >= N-1 else (SM[0:i]+[SM[i]]*(N-i)))/float(N))**0.5 for i in xrange(length)]
	UP = map(lambda x,y:x+y*k, MA, MD)
	DN = map(lambda x,y:x-y*k, MA, MD)
	b = map(lambda x,y,z:(x-z)/(float(y-z) if y!=z else 1.0), Close, UP, DN)
	Band = map(lambda x,y,z:(x-z)/(float(y) if y!=0 else 1.0), UP, MD, DN)
	return MA, UP, DN, b, Band

def GoldSeeker(_stocks, _beginDateStr, _endDateStr):
	Result = []
	start = datetime.now()
	baseFolder, folder = CreateFolder()
	for num,id in enumerate(_stocks):
		temp = datetime.now()		
		try:
			stockname, stockid = StockQuery(id)
			items = GrabStock(stockid, _beginDateStr, _endDateStr)		
			datex = GetColumn(items, 5)		
			MACluster = CalcMA(items)		
			[DDD, AMA, DMA] = CalcDMA(items)		
			zero_ndx = FindZero(DMA)
			zero_pts = GetPart(zero_ndx, DMA)
			length = len(items)
			idx = xrange(length)
			emp = ['']*length
			Open = GetColumn(items, 0)			
			Close = GetColumn(items, 1)
			High = GetColumn(items, 2)
			Low = GetColumn(items, 3)
			Volumes = GetColumn(items, 4)
			Vol = NormVol(Volumes)
			# MA, UP, DN, b, Band = CalcBoll(Close)
			# plt.subplot(2, 1, 1)
			# plt.stem(idx, MACluster['VAR'], linefmt=VARclr, markerfmt=" ", basefmt=" ")
			# plt.plot(idx,MACluster['MA5'], M5clr ,MACluster['MA10'], M10clr ,MACluster['MA20'], M20clr ,MACluster['MA30'], M30clr ,DMACluster['DMA'], DMAclr, DMACluster['AMA'], AMAclr ,DMACluster['DIF'], DIFclr)
			# plt.plot(idx, DMACluster['DIFF'],'g')
			# #plt.plot(idx, CalcDiff(DMACluster['DIFF']),'k')
			# plt.plot(zero_ndx[-3:], zero_pts[-3:], 'ro')
			# plt.plot(small_ndx[-3:], small_pts[-3:],'g*')

			# Draw Percent
			# up_index = [i for i,per in enumerate(Percent) if per>=0]
			# dn_index = [i for i,per in enumerate(Percent) if per<0]
			# plt.bar(up_index, GetPart(up_index,Percent),color='r',edgecolor='r')
			# plt.bar(dn_index, GetPart(dn_index,Percent),color='g',edgecolor='g')	
			# plt.plot(idx, [10]*len(idx),'r--')
			# plt.plot(idx, [-10]*len(idx),'g--')

			# Draw Vol-fig
			# plt.bar(rise_index, GetPart(rise_index,Vol),bottom=-20,color='r',edgecolor='r')
			# plt.bar(fall_index, GetPart(fall_index,Vol),bottom=-20,color='g',edgecolor='g')			

			Cross = RuleGoldCross(DDD, AMA, zero_ndx[-3:], idx[-1], datex[-1])
			Kiss = RuleGoldKiss(DDD, AMA, zero_ndx[-1], Close, idx[-1], datex[-1])		
			GoldBar = RuleGoldBar(Close, Volumes, datex[-1])
			DbleQuty = RuleDoubleQuantity(Close, Volumes, datex[-1])
			Twine = RuleGoldTwine(DDD, AMA, Close, datex[-1])
			for ndx,item in enumerate([Cross, Kiss, GoldBar,DbleQuty,Twine]):
				if item:
					RuleFolder = RuleFolders[ndx]				
					Percent = RisingPercent(items)
					Rise = map(sub, Close , Open)
					rise_index = [i for i,per in enumerate(Rise) if per>=0]
					fall_index = [i for i,per in enumerate(Rise) if per<0]

					step = 5
					lookback = 55
					id_start = idx[-1]-lookback if idx[-1]>lookback else idx[0]
					plt.subplot(3, 1, 1)			
					# plt.plot(idx,MA, 'b' ,UP, 'r',DN,'g')
					
					# Draw K-fig 
					rise_index = [i for i,per in enumerate(Rise) if per>=0]
					fall_index = [i for i,per in enumerate(Rise) if per<0]
					plt.vlines(rise_index, GetPart(rise_index,Low), GetPart(rise_index,High), edgecolor='red', linewidth=1, label='_nolegend_') 
					plt.vlines(rise_index, GetPart(rise_index,Open), GetPart(rise_index,Close), edgecolor='red', linewidth=4, label='_nolegend_')
					plt.vlines(fall_index, GetPart(fall_index,Low), GetPart(fall_index,High), edgecolor='green', linewidth=1, label='_nolegend_') 
					plt.vlines(fall_index, GetPart(fall_index,Open), GetPart(fall_index,Close), edgecolor='green', linewidth=4, label='_nolegend_')	
					plt.title(stockname, fontproperties=font)	
					
					plt.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)		
					ax = plt.gca()		
					ax.autoscale(enable=True, axis='both', tight=True)
					ax.set_xticklabels( emp[0::step], rotation=75, fontsize='small')
					ax.set_xlim([id_start,idx[-1]])				
					ax.set_ylim(min(Close[id_start:]), max(Close[id_start:]))
					
					plt.subplot(3, 1, 2)
					plt.stem(idx, MACluster['VAR'], linefmt=VARclr, markerfmt=" ", basefmt=" ")
					plt.plot(idx,DDD, DDDclr, AMA, AMAclr ,DMA, DMAclr)
					#plt.plot(idx, DMACluster['DIFF'],'g')
					#plt.plot(idx, CalcDiff(DMACluster['DIFF']),'k')
					plt.plot(zero_ndx[-3:], zero_pts[-3:], 'ro')			
					plt.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)				
					ax = plt.gca()
					ax.autoscale(enable=True, axis='both', tight=True)			
					ax.set_xticklabels( emp[0::step], rotation=75, fontsize='small')
					ax.set_xlim([id_start,idx[-1]])				
					ax.set_ylim(min(DMA[id_start:] + AMA[id_start:] + DDD[id_start:]),\
					max(DMA[id_start:] + AMA[id_start:]+ DDD[id_start:]))
					
					plt.subplot(3, 1, 3)
					plt.bar(rise_index, GetPart(rise_index,Vol),bottom=-20,color='r',edgecolor='r',align="center")
					plt.bar(fall_index, GetPart(fall_index,Vol),bottom=-20,color='g',edgecolor='g',align="center")				
					plt.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)		
					plt.xticks(np.arange(len(idx))[0::step], emp[0::step])
					ax = plt.gca()	
					ax.autoscale(enable=True, axis='both', tight=True)
					ax.set_xticklabels(datex[0::step], rotation=75, fontsize='small')
					ax.set_xlim([id_start,idx[-1]])				
					# plt.show()
					goldstock = '{0:8}- {1} {2}({3})'.format(RuleFolder[4:],stockid[2:],stockname.encode('utf-8'),GetIndustry(stockid[2:]).encode('utf-8'))
					Result.append((goldstock,AMA[-1]))
					try:
						plt.savefig('%s/%s/%s%s.png'%(baseFolder,RuleFolder,stockid+stockname,datex[zero_ndx[-1]]), dpi=100)
					except:
						plt.savefig('%s/%s/%s%s.png'%(baseFolder,RuleFolder,stockid+stockname[1:],datex[zero_ndx[-1]]), dpi=100)
					plt.clf()				
			print 'Complete %s: %s - %s, Elapsed Time: %s'%(num, stockname,stockid,temp-start)
		except Exception as e:
			print str(e)+ ' when grabing stock:' + str(id)
	return Result, folder

def SortList(_tupleList):
	OrderedResult = sorted(_tupleList, key=itemgetter(1))
	AMAOrderedResult = map(itemgetter(0), OrderedResult)
	OrderedResult = sorted(AMAOrderedResult,key=lambda x:x[0:4])
	return OrderedResult

if __name__ == '__main__':
	stocks = GetStockList()
	begin = '20140101'
	end = date.today().strftime('%Y%m%d')
	result, folder = GoldSeeker(stocks, begin, end)
	OrderedResult = SortList(result)	
	for key,value in Targets.items():
		if value == 'A':
			PushwithFetion(OrderedResult,key)
			PushwithPb(OrderedResult,folder)
		elif value == 'D':
			FilteredResult = [item for item in OrderedResult if item[0]=='D']
			PushwithFetion(FilteredResult,key)
		elif value == 'M':
			FilteredResult = [item for item in OrderedResult if item[1]=='m']
			PushwithFetion(FilteredResult,key)
		else:
			print 'No message pushed for this contact.'
