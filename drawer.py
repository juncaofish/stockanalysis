#! /usr/bin/env python
# -*- encoding: utf-8 -*-

from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt


class FigureConf():
    Font = FontProperties(fname=r"c:\windows\fonts\simsun.ttc", size=14)
    M5clr = '#0000CC'
    M10clr = '#FFCC00'
    M20clr = '#CC6699'
    M30clr = '#009966'
    DDDclr = '#000000'
    AMAclr = '#FF0033'
    DMAclr = '#0066FF'
    VARclr = '#3300FF'
    EXP1clr = '#FF00FF'
    EXP2clr = '#3300CC'


def GenerateFigure(_open, _close, _items):
    def GetPart(_indices, _list):
        return [_list[idx] for idx in _indices]
        # GenerateFigure(Open, Close, items)
        # ==================Ignore Figure==========#
        Percent = RisingPercent(items)
        Rise = map(sub, Close, Open)
        rise_index = [i for i, per in enumerate(Rise) if per >= 0]
        fall_index = [i for i, per in enumerate(Rise) if per < 0]

        step = 5
        lookback = 55
        id_start = idx[-1] - lookback if idx[-1] > lookback else idx[0]
        plt.subplot(3, 1, 1)

        # Draw K-fig
        rise_index = [i for i, per in enumerate(Rise) if per >= 0]
        fall_index = [i for i, per in enumerate(Rise) if per < 0]
        plt.vlines(rise_index, GetPart(rise_index, Low), GetPart(rise_index, High), edgecolor='red', linewidth=1,
                   label='_nolegend_')
        plt.vlines(rise_index, GetPart(rise_index, Open), GetPart(rise_index, Close), edgecolor='red', linewidth=4,
                   label='_nolegend_')
        plt.vlines(fall_index, GetPart(fall_index, Low), GetPart(fall_index, High), edgecolor='green', linewidth=1,
                   label='_nolegend_')
        plt.vlines(fall_index, GetPart(fall_index, Open), GetPart(fall_index, Close), edgecolor='green', linewidth=4,
                   label='_nolegend_')
        plt.title(stockname, fontproperties=FigureConf.Font)

        plt.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)
        ax = plt.gca()
        ax.autoscale(enable=True, axis='both', tight=True)
        ax.set_xticklabels(emp[0::step], rotation=75, fontsize='small')
        ax.set_xlim([id_start, idx[-1]])
        ax.set_ylim(min(Close[id_start:]), max(Close[id_start:]))

        plt.subplot(3, 1, 2)
        plt.stem(idx, MACluster['VAR'], linefmt=VARclr, markerfmt=" ", basefmt=" ")
        plt.plot(idx, DDD, DDDclr, AMA, AMAclr, DMA, DMAclr)
        plt.plot(zero_ndx[-3:], zero_pts[-3:], 'ro')
        plt.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)
        ax = plt.gca()
        ax.autoscale(enable=True, axis='both', tight=True)
        ax.set_xticklabels(emp[0::step], rotation=75, fontsize='small')
        ax.set_xlim([id_start, idx[-1]])
        ax.set_ylim(min(DMA[id_start:] + AMA[id_start:] + DDD[id_start:]), \
                    max(DMA[id_start:] + AMA[id_start:] + DDD[id_start:]))

        plt.subplot(3, 1, 3)
        plt.bar(rise_index, GetPart(rise_index, Vol), bottom=-20, color='r', edgecolor='r', align="center")
        plt.bar(fall_index, GetPart(fall_index, Vol), bottom=-20, color='g', edgecolor='g', align="center")
        plt.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)
        plt.xticks(np.arange(len(idx))[0::step], emp[0::step])
        ax = plt.gca()
        ax.autoscale(enable=True, axis='both', tight=True)
        ax.set_xticklabels(datex[0::step], rotation=75, fontsize='small')
        ax.set_xlim([id_start, idx[-1]])
        # # plt.show()
        try:
            plt.savefig('%s/%s/%s%s.png' % (baseFolder, RuleFolder, stockid + stockname, datex[zero_ndx[-1]]), dpi=100)
        except:
            plt.savefig('%s/%s/%s%s.png' % (baseFolder, RuleFolder, stockid + stockname[1:], datex[zero_ndx[-1]]),
                        dpi=100)
        plt.clf()
