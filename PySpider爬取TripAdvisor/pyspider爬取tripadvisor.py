#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2018-10-14 17:17:02
# Project: TripAdvisor

from pyspider.libs.base_handler import *
import pymongo


class Handler(BaseHandler):
    crawl_config = {
    }

    client = pymongo.MongoClient('localhost', connect=False)
    db = client['tripadvisor']

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl(
            'https://www.tripadvisor.cn/Attractions-g186338-Activities-London_England.html#ATTRACTION_SORT_WRAPPER',
            callback=self.index_page)

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('.listing_title a').items():
            self.crawl(each.attr.href, callback=self.detail_page)

        next = response.doc('#FILTERED_LIST > div.al_border.deckTools.btm > div > div > a').attr.href
        self.crawl(next, callback=self.index_page)

    @config(priority=2)
    def detail_page(self, response):

        url = response.url
        name = response.doc('.h1').text()
        tag = response.doc('.attractionCategories > div').text()
        rating = response.doc('a > .reviewCount').text()
        address = response.doc('.contactInfo > .address > span > span').text()
        phone = response.doc('.contact > .is-hidden-mobile > div').text()
        duration = response.doc('#component_3 > div > div:nth-child(3) > div').text()

        return {
            'url': url,
            'name': name,
            'tag': tag,
            'rating': rating,
            'address': address,
            'phone': phone,
            'duration': duration
        }

    def on_result(self, result):
        if result:
            self.save_to_mongo(result)

    def save_to_mongo(self, result):
        if self.db['london'].insert(result):
            print('已存入MongoDB', result)