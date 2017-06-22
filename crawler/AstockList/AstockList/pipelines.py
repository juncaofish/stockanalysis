# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import sys
import codecs
import json
reload(sys)
sys.setdefaultencoding('utf8')


class ResultSavePipeline(object):
    def __init__(self):
        self.file = codecs.open('result.json', 'wb', encoding='utf-8')
        self.file.write('[\n')

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + ',\n'
        self.file.write(line.decode("unicode_escape"))
        return item

    def close_spider(self, spider):
        self.file.write(']')
