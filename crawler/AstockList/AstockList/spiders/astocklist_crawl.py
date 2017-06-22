#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scrapy.conf import settings
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from AstockList.items import AstockListItem
from scrapy.linkextractors import LinkExtractor
import sys


reload(sys)
sys.setdefaultencoding('utf-8')


class AstockListSpider(CrawlSpider):

    name = "AstockList"
    allowed_domains = ["app.finance.ifeng.com"]
    rules = [
        Rule(LinkExtractor(
            allow=(r"http://app.finance.ifeng.com/list/stock.php\?t=[hs]a&f=chg_pct&o=desc&p=\d+")),
            callback='parse_page',
            follow=True),
    ]

    def __init__(self, *args, **kwargs):
        super(AstockListSpider, self).__init__(*args, **kwargs)
        self.base_url = "http://app.finance.ifeng.com/"
        self.start_urls = ["http://app.finance.ifeng.com/list/stock.php?t=ha&p=1",
                           "http://app.finance.ifeng.com/list/stock.php?t=sa&p=1"]

    def parse_page(self, response):
        sel = Selector(response)
        rows = sel.xpath('//table/tr')
        for row in rows:
            item = AstockListItem()
            if row.xpath('td') and row.xpath('td/a/text()').extract()[0].isdigit():
                item['name'] = row.xpath('td[2]/a/text()').extract()[0]
                item['code'] = row.xpath('td[1]/a/text()').extract()[0]
                yield item
