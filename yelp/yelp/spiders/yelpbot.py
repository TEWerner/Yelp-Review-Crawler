# -*- coding: utf-8 -*-
import scrapy


class YelpbotSpider(scrapy.Spider):
    name = 'yelpbot' # Name of the spider
    allowed_domains = ['https://www.yelp.com/']
    start_urls = ['http://https://www.yelp.com//']

    def parse(self, response):
        pass
