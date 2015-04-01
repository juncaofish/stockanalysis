# -*- coding=utf-8 -*-
import os
import re
import time
from datetime import datetime,timedelta,date
import requests
from lxml import etree
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
from operator import itemgetter, div, sub
from StockList import stock
import pushybullet as pb
from PyFetion import *

font = FontProperties(fname=r"c:\windows\fonts\simsun.ttc", size=14) 
M5clr  = '#0000CC'
M10clr = '#FFCC00'
M20clr = '#CC6699'
M30clr = '#009966'
DMAclr = '#000000'
AMAclr = '#FF0033'
DIFclr = '#0066FF'
VARclr = '#3300FF'
EXP1clr = '#FF00FF'
EXP2clr = '#3300CC'
RuleFolders = [u'RuleCross',u'RuleKiss',u'RuleGoldBar',u'RuleDoubleQuantity']
Headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.111 Safari/537.36'}

def grabRealTimeStock(_stockid):
	url = 'http://hq.sinajs.cn/list=%s'%_stockid
	r = requests.get(url, headers = Headers)
	regx = re.compile(r'\=\"(.*)\"\;');
	m =  regx.search(r.text)
	info = m.group(0)
	infos = info.split(',')
	# Return Open/Close/High/Low/volume/Date
	return [eval(infos[1]),eval(infos[3]),eval(infos[4]),eval(infos[5]),eval(infos[8])/100,infos[30]] 

def mkFolder():	
	currentpath  = os.path.realpath(__file__)
	basedir = os.path.dirname(currentpath)
	folder = datetime.today().strftime('%Y%m%d')
	folderpath =os.path.join(basedir, folder)
	if not os.path.exists(folderpath):
		os.mkdir(folderpath)
	for item in RuleFolders:
		subfolder = os.path.join(folderpath, item)
		if not os.path.exists(subfolder):
			os.mkdir(subfolder)
	return folderpath,folder

def pushStocks(list, title):
	API_KEY = "pdaXjHTgQJ9s5sZRdfi93BMTz4CjICGl"
	try:
		api = pb.PushBullet(API_KEY)
		device = api['LGE Nexus 4']
		# print device.nickname
		push = pb.ListPush(list, title)
		api.push(push, device)
		return True
	except Exception as e:
		pass
		return False
		
def pushwithFetion(msg, sendto):
	phone = PyFetion('13788976646', 'a5214496','TCP',debug=False)
	phone.login(FetionHidden)
	for item in sendto:
		phone.send_sms(msg.encode('utf-8'),item)
	
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
	
def StockGrab(_stockid, begin_date , end_date_str):
	url = 'http://biz.finance.sina.com.cn/stock/flash_hq/kline_data.php?symbol=%s&end_date=%s&begin_date=%s' 
	_url = url%(_stockid, end_date_str, begin_date)
	r = requests.get(_url, headers = Headers)
	page = etree.fromstring(r.text.encode('utf-8'))
	contents = page.xpath(u'/control/content')
	items = [[eval(content.attrib['o']),eval(content.attrib['c']),eval(content.attrib['h']),eval(content.attrib['l']),eval(content.attrib['v']),content.attrib['d']] for content in contents]
	todaydate = date.today().strftime('%Y-%m-%d')
	if todaydate != items[-1][-1]:
		latest = grabRealTimeStock(_stockid)
		if latest[-1] == todaydate:
			items.append(latest)		
	return items

def StockQuery(stockname): 
	m = re.match(r'\d{6}', stockname)
	stockid = stockname if m else stock.get(stockname)
	stockname = stock.get(stockname) if m else stockname
	stock_pre = 'sh' if stockid[0] == '6' else 'sz'
	stockid = stock_pre + stockid
	return stockname.decode('utf-8'), stockid	
	
def GetColumn(Array, column):
	return [itemgetter(column)(row) for row in Array]

def GetPart(indices, List):
	return [List[idx] for idx in indices]
	
	
def MovingAverage(Array, idx, width):
	length = len(Array)
	if type(Array[0]) == type([]):
		return [sum([itemgetter(idx)(elem) for elem in Array[i-width+1:i+1]])/float(width) if i >= width-1 else Array[i][idx] for i in xrange(length)]
	else: 
		return [sum( Array[i-width+1:i+1] if i >= width-1 else (Array[0:i]+[Array[i]]*(width-i)))/float(width) for i in xrange(length)]
	
def CalcExpMA(List, Period):
	length = len(List)
	def ExpMA(List, n, N):
		return List[0] if n == 0 else (List[n]*2.0 + (N - 1.0)*ExpMA(List, n-1,N))/( N +1.0)
	ExpMA = [ExpMA(List,i,Period) for i in xrange(length)]
	# ExpMA2 = [ExpMA(List,i,50) for i in xrange(length)]
	return ExpMA
		
def RisingPercent(Array):
	length = len(Array)
	return [100.0*(itemgetter(1)(Array[i]) - itemgetter(1)(Array[i-1]))/itemgetter(1)(Array[i-1]) if i >=1 else 0 for i in xrange(length)]
	
def CalcVar(Array):
	Var = [np.var(GetColumn(Array, i)) for i in xrange(len(Array[0]))]
	return Var
	
def NormVol(List):
	return [10.0*elem/max(List) for elem in List]

def FindZero(List):
	L_S1 = List[1:]+[List[-1]]
	npList = np.array(List)
	npL_S1 = np.array(L_S1)
	multi = npList*npL_S1
	indices = list((multi < 0).nonzero()[0])	
	return indices
	
def FindClose(List):
	eps = 0.02
	npList = np.array(List)
	indices = list((abs(npList)<eps).nonzero()[0])
	return indices
	
def CalcDiff(List):
	List1 = List[1:]+[List[-1]]
	List2 = [List[0]]+List[0:-1]
	Diff = list(np.array(map(sub, List1, List2))*5.0)
	return Diff

def CalcInteg(List):
	return [sum(List[0:i+1]) for i,elem in enumerate(List)]
	
def GetStockList():		
	return [id for id, sname in stock.items() if re.match(r'\d{6}', id)]

def CalcMA(Array):
	MA1 = MovingAverage(Array, 1, 1)
	MA5 = MovingAverage(Array, 1, 5)
	MA10 = MovingAverage(Array, 1, 10)
	MA20 = MovingAverage(Array, 1, 20)
	MA30 = MovingAverage(Array, 1, 30)
	VAR = CalcVar( [MA1,MA5, MA10, MA20, MA30] )	
	MACluster = {'MA1':MA1, 'MA5':MA5, 'MA10':MA10, 'MA20':MA20, 'MA30':MA30, 'VAR':VAR}
	return MACluster

def CalcDMA(Array, Short = 5, Long = 89, Middle = 34):
	DMA = map(sub, MovingAverage(Array, 1, Short) , MovingAverage(Array, 1, Long))
	AMA = MovingAverage(DMA, 0, Middle)
	DIF = map(sub, DMA , AMA)
	# DMACluster = {'DMA':DMA, 'AMA':AMA, 'DIF':DIF}
	return DMA, AMA, DIF

def RuleGoldBar(Prices, Volumes,_date, check = True):
	RecentP = Prices[-5:]
	RecentV = Volumes[-5:]
	C0 = CheckDate(_date) if check else True
	C1 = RecentP[4]>RecentP[3]>RecentP[2]>RecentP[1]
	C2 = RecentV[4]<RecentV[3]<RecentV[2]<RecentV[1]
	C3 = (RecentP[1]-RecentP[0])/RecentP[0]>0.09
	Rule = False not in [C0,C1,C2,C3]
	return Rule
	
def RuleGoldCross(DMA, AMA, zeros, last_ndx, _date, check = True):
	DIF = map(sub, DMA , AMA)
	DIFF = CalcDiff(DIF)
	AMADIFF = CalcDiff(AMA)
	C0 = CheckDate(_date) if check else True
	C1 = DIF[last_ndx]>0
	C2 = sum(DIF[zeros[0]:zeros[1]])>0
	C3 = sum(DIF[zeros[1]:zeros[2]])<0
	C4 = sum(DIF[zeros[0]:zeros[2]])>0
	C5 = last_ndx - zeros[2] < 2
	C6 = ((zeros[1] - zeros[0]) - 2*(zeros[2] - zeros[1]))>0
	C7 = (zeros[2] - zeros[1]) < 10
	C8 = AMADIFF[last_ndx] > 0
	Rule = False not in [C0,C1,C2,C3,C4,C5,C6,C7,C8]
	return Rule	
	
def RuleGoldKiss(DMA, AMA, zero, Close, last_ndx, _date, check = True):
	DIF = map(sub, DMA , AMA)	
	DIFF = CalcDiff(DIF)
	AMADIFF = CalcDiff(AMA)
	DFZeros = FindZero(DIFF)
	C0 = CheckDate(_date) if check else True
	C1 = 0<DIF[last_ndx]<0.03*Close[last_ndx] # Last day DMA Less than Close_price*1.5%
	C2 = 0<DIF[DFZeros[-1]]<0.02*Close[DFZeros[-1]] # Kiss day DMA Less than Close_price*1%
	C3 = sum(DIF[zero:]) > 0
	C4 = 4<(last_ndx - zero)<60 and (last_ndx - DFZeros[-1])<2 # Last DMA Cross day within 9 weeks, Kiss day within 1 week
	C5 = DIFF[zero] > 0
	C6 = DIFF[last_ndx] >= 0
	C7 = AMADIFF[last_ndx] > 0
	Rule = False not in [C0,C1,C2,C3,C4,C5,C6,C7]	
	return Rule	

def RuleDoubleQuantity(Prices, Volumes,_date, check = True):
	RecentP = Prices[-4:]
	RecentV = Volumes[-33:]
	MeanV = np.mean(RecentV[0:30])
	MaxIndx = max( (v, i) for i, v in enumerate(RecentV) )[1]	
	C0 = CheckDate(_date) if check else True
	C1 = False not in [ R>2.0*MeanV for R in RecentV[-3:]]
	C2 = MaxIndx >= 30
	C3 = RecentP[1] > RecentP[0] and RecentP[3] > RecentP[1]
	Rule = False not in [C0,C1,C2,C3]	
	return Rule	
	
def RuleEXPMA(List, last_ndx, _date):
	EXP1 = CalcExpMA(List,10)
	EXP2 = CalcExpMA(List,50)
	DIFEXP = map(sub, EXP1, EXP2)
	EXPZeros = FindZero(DIFEXP)	
	C0 = CheckDate(_date)
	C1 = DIFEXP[last_ndx]>0
	C2 = (last_ndx - EXPZeros[-1])<5
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

def GoldSeeker(heart, begin_date_str, end_date_str):
	Result = []
	start = datetime.now()
	baseFolder, folder = mkFolder()
	for num,id in enumerate(heart):
		temp = datetime.now()		
		try:
			stockname, stockid = StockQuery(id)
			items = StockGrab(stockid, begin_date_str,end_date_str )		
			datex = GetColumn(items, 5)		
			MACluster = CalcMA(items)		
			[DMA, AMA, DIF] = CalcDMA(items)		
			zero_ndx = FindZero(DIF)
			zero_pts = GetPart(zero_ndx, DIF)
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
			

			Cross = RuleGoldCross(DMA, AMA, zero_ndx[-3:], idx[-1], datex[-1])
			Kiss = RuleGoldKiss(DMA, AMA, zero_ndx[-1], Close, idx[-1], datex[-1])		
			GoldBar = RuleGoldBar(Close, Volumes, datex[-1])
			DoubleQuantity = RuleDoubleQuantity(Close, Volumes, datex[-1])
			for ndx,item in enumerate([Cross, Kiss, GoldBar,DoubleQuantity]):
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
					plt.plot(idx,DMA, DMAclr, AMA, AMAclr ,DIF, DIFclr)
					#plt.plot(idx, DMACluster['DIFF'],'g')
					#plt.plot(idx, CalcDiff(DMACluster['DIFF']),'k')
					plt.plot(zero_ndx[-3:], zero_pts[-3:], 'ro')			
					plt.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)				
					ax = plt.gca()
					ax.autoscale(enable=True, axis='both', tight=True)			
					ax.set_xticklabels( emp[0::step], rotation=75, fontsize='small')
					ax.set_xlim([id_start,idx[-1]])				
					ax.set_ylim(min(DIF[id_start:] + AMA[id_start:] + DMA[id_start:]),\
					max(DIF[id_start:] + AMA[id_start:]+ DMA[id_start:]))
					
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
					goldstock = '%s - %s - %s'%(stockname,stockid,RuleFolder[4:])
					Result.append(goldstock)
					try:
						plt.savefig('%s/%s/%s%s.png'%(baseFolder,RuleFolder,stockid+stockname,datex[zero_ndx[-1]]), dpi=100)
					except:
						plt.savefig('%s/%s/%s%s.png'%(baseFolder,RuleFolder,stockid+stockname[1:],datex[zero_ndx[-1]]), dpi=100)
					plt.clf()				
			print 'Complete %s: %s - %s, Elapsed Time: %s'%(num, stockname,stockid,temp-start)		
		except Exception as e:
			print str(e)+ ' when grabing stock:' + str(id)
	return Result, folder

if __name__ == '__main__':
	heart = GetStockList()
	begin_date = '20140101'
	end_date = date.today().strftime('%Y%m%d')
	Result, folder = GoldSeeker(heart, begin_date, end_date)
	pushStocks(Result,folder)
	pushwithFetion('\n'.join(Result),['13788976646']) # ,'13601621490'
			
