# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import json

import logging
import requests
from requests.exceptions import ConnectionError
from scrapy.exceptions import IgnoreRequest


class CookiesMiddleware():

    def __init__(self,cookies_pool_url):
        self.logger = logging.getLogger(__name__)
        self.cookies_pool_url = cookies_pool_url

    # 从Cookies池中获取Cookies
    def _get_random_cookies(self):
        try:
            response = requests.get(self.cookies_pool_url)
            if response.status_code == 200:
                return json.loads(response.text)
        except ConnectionError:
            return None

    # 将cookies池的url配置到全局的settings.py里
    @classmethod
    def from_crawler(cls,crawler):
        return cls(
            cookies_pool_url = crawler.settings.get('COOKIES_POOL_URL')
        )

    # 检测是否拿到Cookies，并在request中替换
    def process_request(self,request,spider):
        cookies = self._get_random_cookies()
        if cookies:
            request.cookies = cookies
            self.logger.debug('使用Cookies' + json.dumps(cookies))
        else:
            self.logger.debug('没有获取到Cookies!')

    # 对封号等一些情况的处理
    def process_response(self, request, response, spider):
        if  response.status in [300,301,302,303]:
            try:
                redirect_url = response.headers['location']
                if 'passport' in redirect_url:
                    self.logger.debug('需要新的Cookies!')
                elif 'weibo.cn/security' in redirect_url:
                    self.logger.debug('此账号已被封禁!')
                request.cookies = self._get_random_cookies()
                return request
            except:
                raise IgnoreRequest
        elif response.status in [414]:
            return request
        else:
            return response
