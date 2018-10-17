# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
import time
from weibosearch.items import WeiboItem
import pymongo

# 微博发表时间有三种情况：1、X年X月X日 2、今天XX:XX 3、XX分钟前
# 分别对这三种情况进行处理，统一格式化为X年X月X日
class WeiboPipeline(object):
    def parse_time(self, datetime):
        if re.match('\d+月\d+日',datetime):
            datetime = time.strftime('%Y年',time.localtime()) + datetime
        if re.match('\d+分钟前',datetime):
            minute = re.match('(\d+)',datetime).group(1)
            # 用format进行格式化处理，否则会报错：UnicodeEncodeError: 'locale' codec can't encode character '\u5e74' in position 2: Illegal byte sequence
            datetime = time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}',time.localtime(time.time() - float(minute) * 60)).format(y='年',m='月',d='日',h='时',f='分')
        if re.match('今天.*', datetime):
            datetime = re.match('今天(.*)', datetime).group(1).strip()
            datetime = time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}',time.localtime()).format(y='年',m='月',d='日',h='时',f='分') + '' + datetime
        return datetime

    def process_item(self, item, spider):
        if isinstance(item,WeiboItem):
            if item.get('content'):
                item['content'] = item['content'].lstrip(':').strip()
            if item.get('posted_at'):
                item['posted_at'] = item['posted_at'].strip()
                item['posted_at'] = self.parse_time(item.get('posted_at'))
        return item

class MongoPipeline(object):

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        # 存在就更新，不存在就插入
        self.db[item.table_name].update({'id':item.get('id')},{'$set': dict(item)}, True)
        return item
