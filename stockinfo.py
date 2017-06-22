#! /usr/bin/env python
# -*- encoding: utf-8 -*-

import json
import pandas as pd


class StockType:
    SH = 'SH'
    SZ = 'SZ'
    CY = 'CY'


class StockInfo(object):

    def __init__(self, path='data/data.json'):
        with open(path) as f:
            self.stock = json.load(f)
        self.industry_info = pd.read_csv('data/all.csv',
                                         dtype={'code': 'object'},
                                         encoding='GBK')

    def get_stocks_dict(self):
        return self.stock

    def get_stocks(self):
        return self.stock.keys()

    def get_stock_name(self, stock_code):
        return self.stock.get(stock_code)

    def get_stock_with_prefix(self, stock_code):
        prefix = StockType.SH if stock_code.startswith('6') else StockType.SZ
        return prefix + stock_code

    def get_stock_industry(self, stock_code):
        try:
            industry = self.industry_info.ix[
                self.industry_info.code == stock_code,
                ['industry']].values[0][0]
        except Exception:
            industry = "NoData"
        return industry


def main():
    stock_info = StockInfo()
    assert stock_info.get_stock_with_prefix('002440') == "SZ002440"
    assert stock_info.get_stock_name('002440').encode("utf-8") == "闰土股份"
    assert stock_info.get_stock_industry('002440') == "染料涂料"

if __name__ == '__main__':
    main()
