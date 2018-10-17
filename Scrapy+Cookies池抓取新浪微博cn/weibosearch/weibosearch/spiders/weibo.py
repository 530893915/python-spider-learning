# -*- coding: utf-8 -*-
import re
from scrapy import FormRequest, Spider, Request
from weibosearch.items import WeiboItem


# UnicodeEncodeError: 'gbk' codec can't encode character '\xbb' in position 8530: illegal multibyte sequence
# 报错原因：print()函数自身有限制，不能完全打印所有的unicode字符。
# 解决：改一下python的默认编码成'utf-8'就行了
# https://blog.csdn.net/jim7424994/article/details/22675759
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='gb18030')

class WeiboSpider(Spider):
    name = 'weibo'
    allowed_domains = ['weibo.cn']

    search_url = 'https://weibo.cn/search/mblog'
    max_page = 200

    def start_requests(self):
        # 搜索内容
        keyword = '000001'

        url = '{url}?keyword={keyword}'.format(url=self.search_url,keyword=keyword)
        for page in range(self.max_page + 1):
            data = {
                'mp': str(self.max_page),
                'page': str(page)
            }
            yield FormRequest(url, callback=self.parse_index, formdata=data)

    # 获取每篇微博的详情url(点击评论/详情评论时，会进入到详情页面)
    def parse_index(self, response):
        weibos = response.xpath('//div[@class="c" and contains(@id, "M_")]')
        for weibo in weibos:
            is_forward = bool(weibo.xpath('.//span[@class="cmt"]').extract_first())
            if is_forward:
                detail_url = weibo.xpath('.//a[contains(.,"原文评论[")]//@href').extract_first()
            else:
                detail_url = weibo.xpath('.//a[contains(.,"评论[")]//@href').extract_first()
            yield Request(detail_url, callback=self.parse_detail)

    # 解析抓取需要的数据
    def parse_detail(self,response):
        id =re.search('comment\/(.*?)\?',response.url).group(1)
        url = response.url
        content = ''.join(response.xpath('.//div[@id="M_"]//span[@class="ctt"]//text()').extract())
        comment_count = response.xpath('//span[@class="pms"]//text()').re_first('评论\[(.*?)\]')
        forward_count = response.xpath('//a[contains(.,"转发[")]//text()').re_first('转发\[(.*?)\]')
        like_count = response.xpath('//a[contains(.,"赞[")]').re_first('赞\[(.*?)\]')
        posted_at = response.xpath('//div[@id="M_"]//span[@class="ct"]//text()').extract_first(default=None)
        user = response.xpath('//div[@id="M_"]//div[1]/a/text()').extract_first(default=None)

        weibo_item = WeiboItem()
        for field in weibo_item.fields:
            # 容错处理，防止取值为None时报错
            try:
                weibo_item[field] = eval(field)
            except NameError:
                self.logger.debug('Field is Not Defined' + field)

        yield weibo_item
