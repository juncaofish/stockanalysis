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
		[DMA, AMA, DIF] = CalcDMA(items)		
		zero_ndx = FindZero(DIF)
		zero_pts = GetPart(zero_ndx, DIF)
		length = len(items)
		idx = xrange(length)
		emp = ['']*length
		
		Close = GetColumn(items, 1)
		Volumes = GetColumn(items, 4)
		Vol = NormVol(Volumes)

		Cross = RuleGoldCross(DMA, AMA, zero_ndx[-3:], idx[-1], datex[-1], False)
		Kiss = RuleGoldKiss(DMA, AMA, zero_ndx[-1], Close, idx[-1], datex[-1], False)		
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
				plt.plot(idx,DMA, DMAclr, AMA, AMAclr ,DIF, DIFclr)
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
				# goldstock = '%s - %s - %s'%(stockname,stockid,RuleFolder[4:])
				# Result.append(goldstock)
				plt.savefig('%s/%s/%s %s.png'%(baseFolder,RuleFolder,stockid,datex[-1]), dpi=90)
				plt.clf()				
				# print 'Complete %s: %s - %s'%(num, stockname,stockid)		
	except Exception as e:
		print str(e)+ ' when grabing stock:' + str(stockid)

if __name__ == '__main__':
	
	heart = GetStockList()
	start = datetime.now()
	for num,id in enumerate(heart):
		stockname, stockid = StockQuery(id)		
		baseFolder, folder, flag = mkFolder(stockid)
		if not flag:
			try:
				items = GrabStock(stockid, '19910101','20160101')		
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
		print 'Complete %s: %s - %s, Elapsed Time: %s'%(num, stockname,stockid,temp-start)
	# pushStocks(Result,folder)
			
