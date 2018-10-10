#coding:utf8

import requests
import re

headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 BIDUBrowser/8.7 Safari/537.36'}
content = requests.get('https://book.douban.com/',headers = headers,timeout = 30).text
pattern = re.compile('<li.*?cover.*?href="(.*?)".*?title="(.*?)".*?more-meta.*?author">(.*?)</span>.*?year">(.*?)</span>.*?</li>',re.S)
results = re.findall(pattern, content)
for result in results:
    url,name,author,date = result
    author = re.sub('\s', '', author)
    date = re.sub('\s', '', date)
    print(url,name,author,date)

