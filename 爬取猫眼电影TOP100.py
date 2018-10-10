#coding:utf8

import requests
from requests.exceptions import RequestException
import re
import json
from multiprocessing import Pool

# 获取一页的源码
def get_one_page(url):
    try:
        # 注意：增加headers，模拟浏览器访问，否则会被网站反爬机制阻止，状态码返回403
        headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 BIDUBrowser/8.7 Safari/537.36'}
        response = requests.get(url,headers = headers,timeout = 30)
        if response.status_code == 200:
            return response.text
        return response.status_code
    except RequestException:
        return None

# 解析一页
def parse_one_page(html):
    pattern = re.compile('<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name"><a.*?>(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>',re.S)
    results = re.findall(pattern,html)
    for result in results:
        yield {
            'index': result[0],
            'image': result[1],
            'title': result[2],
            'actor': result[3].strip()[3:],
            'time': result[4].strip()[5:],
            'score': result[5]+result[6]
        }

# 将爬取的数据存储到文件中
def write_to_file(content):
    with open('猫眼电影TOP100.txt','a',encoding='utf-8') as f:
        f.write(json.dumps(content,ensure_ascii=False) + '\n')
        f.close()

def main(offset):
    url = 'http://maoyan.com/board/4?offset='+str(offset)
    html = get_one_page(url)
    for item in parse_one_page(html):
        print(item)
        write_to_file(item)

if __name__ == '__main__':
    # 多进程并行实现喵爪！
    pool = Pool()
    pool.map(main,[i*10 for i in range(10)])