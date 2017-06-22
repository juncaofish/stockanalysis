# -*- coding=utf-8 -*-

from SARobot import *

def mkFolder(stockid):
	flag = False
	currentpath  = os.path.realpath(__file__)
	basedir = os.path.dirname(currentpath)
	folder = 'analysis' 
	folderpath =os.path.join(basedir, folder)
	if not os.path.exists(folderpath):
		os.mkdir(folderpath)
	stockpath =os.path.join(folderpath, stockid)
	if not os.path.exists(stockpath):
		os.mkdir(stockpath)
	else:
		flag = True
	for item in RuleFolders:
		subfolder = os.path.join(stockpath, item)
		if not os.path.exists(subfolder):
			os.mkdir(subfolder)
	return stockpath,folder,flag

def AnalyInPeriod(stockid, items):
	try:		
		datex = GetColumn(items, 5)		
		MACluster = CalcMA(items)		
		[DDD, AMA, DMA] = calc_DMA(items)		
		zero_ndx = FindZero(DMA)
		zero_pts = GetPart(zero_ndx, DMA)
		length = len(items)
		idx = xrange(length)
		emp = ['']*length
		
		Close = GetColumn(items, 1)
		Volumes = GetColumn(items, 4)
		Vol = NormVol(Volumes)

		Cross = RuleGoldCross(DDD, AMA, zero_ndx[-3:], idx[-1], datex[-1], False)
		Kiss = RuleGoldKiss(DDD, AMA, zero_ndx[-1], Close, idx[-1], datex[-1], False)		
		GoldBar = RuleGoldBar(Close, Volumes, datex[-1], False)
		DbleQuty = RuleDoubleQuantity(Close, Volumes, datex[-1], False)
		for ndx,item in enumerate([Cross, Kiss, GoldBar,DbleQuty]):
			if item:
				RuleFolder = RuleFolders[ndx]
				Open = GetColumn(items, 0)
				High = GetColumn(items, 2)
				Low = GetColumn(items, 3)
				Percent = RisingPercent(items)
				Rise = map(sub, Close , Open)
				rise_index = [i for i,per in enumerate(Rise) if per>=0]
				fall_index = [i for i,per in enumerate(Rise) if per<0]

				step = 5
				lookback = 55
				id_start = idx[-1]-lookback if idx[-1]>lookback else idx[0]
				plt.subplot(3, 1, 1)						
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
				plt.plot(zero_ndx[-3:], zero_pts[-3:], 'ro')			
				plt.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)				
				ax = plt.gca()
				ax.autoscale(enable=True, axis='both', tight=True)			
				ax.set_xticklabels( emp[0::step], rotation=75, fontsize='small')
				ax.set_xlim([id_start,idx[-1]])				
				ax.set_ylim(min(DDD[id_start:] + AMA[id_start:] + DMA[id_start:]),\
				max(DDD[id_start:] + AMA[id_start:]+ DMA[id_start:]))
				
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
				# goldstock = '%s - %s - %s'%(stockname,stockid,RuleFolder[4:])
				# Result.append(goldstock)
				plt.savefig('%s/%s/%s %s.png'%(baseFolder,RuleFolder,stockid,datex[-1]), dpi=90)
				plt.clf()				
				# print 'Complete %s: %s - %s'%(num, stockname,stockid)		
	except Exception as e:
		print str(e)+ ' when grabing stock:' + str(stockid)

if __name__ == '__main__':
	
	heart = GetStockList()
	a = '600782 600363 002035 002238 002339 600983 600854 300102 300100 600240 002483 002241 600616 600619 600246 600104 601058 002462 002465 002469 600826 000797 600292 603366 002324 600238 600824 600882 002493 600298 300247 000930 600637 300075 002044 002041 600496 600491 600499 002449 600010 000687 603168 300269 300262 603306 002309 600582 300134 002276 002270 600818 600261 002056 600158 601311 600379 000928 000927 000923 002696 600572 600573 600201 600172 601216 002414 600816 002206 002208 600587 002515 600145 600323 002192 002196 000911 600365 000913 002422 002429 000597 002706 600401 603328 601518 600872 300159 600787 600988 300150 300155 002212 002218 600742 600683 002509 300180 600173 002184 600196 600789 600222 000586 000585 600179 002726 000762 300041 300380 300386 600050 300161 300168 300369 600516 002081 002083 002086 002539 002156 002158 300242 000807 300248 002713 002718 000023 000028 300085 600986 300170 300376 300372 300378 002236 002512 600750 002098 002099 000819 000562 000960 000967 000702 000632 600090 600094 600075 300188 300182 300341 603993 300062 002551 600749 000822 000555 000955 000736 000738 000739 600470 300116 300197 300355 300353 002376 002381 002167 600647 600642 000540 600885 600396 600466 002610 600268 000619 000617 600418 603609 300210 300244 300320 002573 002373 600654 600079 002594 600576 000066 000069 300350 300023 002562 600716 002109 002101 002103 002102 002298 002533 002293 600713 002586 600608 600435 002630 600288 600436 000070 600433 300231 002400 300299 300306 300303 300309 600838 600917 300017 300019 600879 000516 603018 000888 600552 600590 300228 601566 300004 300006 300002 002344 000503 000507 000504 002015 600116 000875 603000'
	heart = a.split()
	start = datetime.now()
	for num,id in enumerate(heart):
		stockname, stockid = StockQuery(id)		
		baseFolder, folder, flag = mkFolder(stockid)
		if not flag:
			try:
				items = GrabStock(stockid, '20110101','20160101')		
				datex = GetColumn(items, 5)
				for days,temp_date_str  in enumerate(datex):
					if days<150:
						pass
					else:					
						temp_items = items[days-150:days+1]
						AnalyInPeriod(stockid, temp_items)
			except Exception as e:
				print str(e)+ ' when grabing stock:' + str(stockid)
				
		temp = datetime.now()		
		print 'Complete %s: %s - %s, Elapsed Time: %s'%(num, '',stockid,temp-start)
	# pushStocks(Result,folder)
			
