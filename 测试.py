#coding:utf8

import selenium
from selenium import webdriver

driver = webdriver.PhantomJS(executable_path='E:/phantomjs-2.1.1-windows/bin/phantomjs.exe')
driver.get('http://www.baidu.com')
driver.page_source