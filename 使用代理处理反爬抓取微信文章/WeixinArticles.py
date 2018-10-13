#coding:utf8
import requests
from urllib.parse import urlencode

from lxml.etree import XMLSyntaxError
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
import pymongo
from .config import *




client = pymongo.MongoClient(MONGO_URL,connect=False)
db = client[MONGO_DB]

base_url = 'https://weixin.sogou.com/weixin?'

headers = {
    'Cookie': 'IPLOC=CN5101; SUID=465971763320910A000000005BB8C171; ld=Ukllllllll2bmGVelllllVmcZg9lllllNXVBSkllll9lllllxklll5@@@@@@@@@@; SUV=1538834802059054; SNUID=9484ACAADDD8A5CB7267FC9EDD376FBC; ABTEST=0|1539413702|v1; weixinIndexVisited=1; sct=1; JSESSIONID=aaad0IhiqCXhUb62I9Hzw',
    'Host': 'weixin.sogou.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
}




proxy = None



def get_proxy():
    try:
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None

def get_html(url,count=1):
    print('开始爬取',url)
    print('尝试次数：',count)
    global proxy
    if count >= MAX_COUNT:
        print('请求次数超过限制！')
        return None
    try:
        if proxy:
            proxies = {
                'http': 'http://' + proxy
            }
            response = requests.get(url, allow_redirects=False, headers=headers, proxies=proxies)
        else:
            response = requests.get(url, allow_redirects=False, headers=headers)
        if response.status_code == 200:
            return response.text
        if response.status_code == 302:
            print(302)
            proxy = get_proxy()
            if proxy:
                print('使用代理：',proxy)
                # count += 1
                # return get_html(url,count)
                return get_html(url)
            else:
                print('获取代理失败！')
                return None
    except ConnectionError as e:
        print('发生错误！',e.args)
        proxy = get_proxy()
        count += 1
        return get_html(url,count)

def get_index(keyword,page):
    data = {
        'query':keyword,
        'type': 2,
        'page': page
    }
    queries = urlencode(data)
    url = base_url + queries
    html = get_html(url)
    return html

def parse_index(html):
    doc = pq(html)
    items = doc('.news-box .news-list li .txt-box h3 a').items()
    for item in items:
        yield item.attr('href')

def get_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None

def parse_detail(html):
    try:
        doc = pq(html)
        title = doc('.rich_media_title').text()
        content = doc('.rich_media_contant').text()
        date = doc('#post-date').text()
        nickname = doc('#js_profile_qrcode > div > strong').text()
        wechat = doc('#js_profile_qrcode > div > p:nth-child(3) > span').text()
        return {
            'title': title,
            'content': content,
            'date': date,
            'nickname': nickname,
            'wechat': wechat
        }
    except XMLSyntaxError:
        return None

def save_to_mongo(data):
    if db['articles'].update({'title':data['title']},{'$set':data},True):
        print('Saved To Mongo',data['title'])
    else:
        print('Saved To Mongo Failed',data['title'])

def main():
    for page in range(1,101):
        html = get_index(KEYWORD,page)
        if html:
            article_urls = parse_index(html)
            for article_url in article_urls:
                article_html = get_detail(article_url)
                if article_html:
                    article_data = parse_detail(article_html)
                    print(article_data)
                    if article_data:
                        save_to_mongo(article_data)

if __name__ == '__main__':
    main()