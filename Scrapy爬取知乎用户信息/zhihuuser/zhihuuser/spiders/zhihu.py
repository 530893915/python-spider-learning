# -*- coding: utf-8 -*-
from scrapy import Spider,Request
import json
from zhihuuser.items import UserItem

class ZhihuSpider(Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    start_user = 'excited-vczh'
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'
    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    def start_requests(self):
        # 1.请求user(自身)数据
        yield Request(self.user_url.format(user=self.start_user,include=self.user_query),callback=self.parse_user)
        # 2.请求user的关注列表数据
        yield Request(self.follows_url.format(user=self.start_user,include=self.follows_query,offset=0,limit=20), callback=self.parse_follows)
        # 3.请求user的粉丝列表数据
        yield Request(self.followers_url.format(user=self.start_user,include=self.followers_query,offset=0,limit=20), callback=self.parse_followers)

    def parse_user(self, response):
        # 解析user的详细信息
        result = json.loads(response.text)
        item = UserItem()
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        yield item

        # 获取user的关注列表和粉丝列表，并进行解析
        yield Request(self.follows_url.format(user=result.get('url_token'), include=self.follows_query,offset=0,limit=20),self.parse_follows)
        yield Request(self.followers_url.format(user=result.get('url_token'), include=self.followers_query,offset=0,limit=20),self.parse_followers)

    # 解析关注列表
    def parse_follows(self, response):
        results = json.loads(response.text)

        # 获取关注列表的用户的url_token进行url拼接，传入parse_user开始解析
        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'),include=self.user_query),self.parse_user)

        # 递归调用关注列表下一页(next)，判断是否到了最后一页
        if 'paging' in results.keys() and results.get('paging').get('is_end') is False:
            next_page = results.get('paging').get('next')
            yield Request(next_page,self.parse_follows)

    # 解析粉丝列表
    def parse_followers(self, response):
        results = json.loads(response.text)

        # 获取粉丝列表的用户的url_token进行url拼接，传入parse_user开始解析
        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'),include=self.user_query),self.parse_user)

        # 递归调用粉丝列表的下一页(next)，判断是否到了最后一页
        if 'paging' in results.keys() and results.get('paging').get('is_end') is False:
            next_page = results.get('paging').get('next')
            yield Request(next_page,self.parse_followers)