#coding:utf8

import json
import re
from urllib.parse import urlencode
import os
import pymongo
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from hashlib import md5
from multiprocessing import Pool
from config import *




client = pymongo.MongoClient(MONGO_URL,connect=False)
db = client[MONGO_DB]

# ajax请求获取数据
def get_page_index(offset,keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab': 3,
        'from': 'search_tab'
    }
    headers = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 BIDUBrowser/8.7 Safari/537.36'}

    url = 'https://www.toutiao.com/search_content/?' + urlencode(data)
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.text
        return response.status_code
    except RequestException:
        print('请求索引页出错！')
        return None

# 解析获得的JSON数据,获取图集页面url
def parse_page_index(html):
    data = json.loads(html)
    if data and 'data' in data.keys():
        for item in data.get('data'):
            yield item.get('article_url')

# 获取图集页面源码
def get_page_detail(url):
    headers = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 BIDUBrowser/8.7 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.text
        return response.status_code
    except RequestException:
        print('请求详情页出错！', url)
        return None

# 爬取详情页数据
def parse_page_detail(html,url):
    soup = BeautifulSoup(html,'lxml')
    title = soup.select('title')[0].get_text()
    images_pattern = re.compile('galleryInfo.*?gallery: JSON.parse\("(.*?)"\)',re.S)
    result = re.search(images_pattern,html)
    if result:
        str = result.group(1)
        # 反转义，去掉反斜杠
        str1 = re.sub(r'\\', '', str)
        # 将json格式字符串转换为python对象
        data = json.loads(str1)
        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')
            images = [item.get('url') for item in sub_images if item.get('url')]
            for image in images:
                download_image(image)
            return {
                'images': images,
                'url': url,
                'title': title
            }

# 写入MongoDB
def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('成功将数据存储到MongoDB！',result)
        return True
    return False

# 下载图片
def download_image(url):
    print('正在下载',url)
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 BIDUBrowser/8.7 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            save_image(response.content)
        return response.status_code
    except RequestException:
        print('请求图片出错！', url)
        return None

# 保存图片
def save_image(content):
    file_path = '{0}/images/{1}.{2}'.format(os.getcwd(),md5(content).hexdigest(),'jpg')
    if not os.path.exists(file_path):
        with open(file_path,'wb') as f:
            f.write(content)
            f.close()

def main(offset):
    html = get_page_index(offset,KEYWORD)
    for url in parse_page_index(html):
        if not url:
            continue
        html = get_page_detail(url)
        if html:
            result = parse_page_detail(html,url)
            if result:
                save_to_mongo(result)

if __name__ == '__main__':
    groups = [i*20 for i in range(GROUP_START,GROUP_END+1)]
    pool = Pool()
    pool.map(main,groups)