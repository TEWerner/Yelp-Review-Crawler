# -*- coding: utf-8 -*-
import scrapy
from selenium import webdriver
from scrapy.utils.response import open_in_browser
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re
import time

class BalthasarbotSpider(scrapy.Spider):
    name = 'balthasarbot'
    allowed_domains = ['yelp.de','yelp.com']
    #start_urls = ['http://https://www.yelp.com/biz/restaurant-balthasar-paderborn/']
    #start_urls = ['https://www.yelp.com/biz/restaurant-balthasar-paderborn/']
    start_urls = ["https://www.yelp.de/biz/argentina-paderborn-2"]
    cleanr = re.compile('<.*?>')

    def cleanhtml(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

    def __init__(self):
        options = Options()
        options.headless = True
        self.driver = webdriver.Chrome("C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe")
    def scroll_until_loaded(self):
        check_height = self.driver.execute_script("return document.body.scrollHeight;")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                self.wait.until(
                    lambda driver: self.driver.execute_script("return document.body.scrollHeight;") > check_height)
                check_height = self.driver.execute_script("return document.body.scrollHeight;")
            except TimeoutException:
                break
    def parse(self, response):
        self.driver.get(response.url)
        wait = WebDriverWait(self.driver, 10)
        rev = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.review-sidebar")))
        res = response.replace(body=self.driver.page_source)

        reviews = dict()
        for i,r in enumerate(response.css("div.review-content > p").extract()):
            reviews [str(i+1)] = self.cleanhtml(r)
        ratings = dict()
        for i,r in enumerate(response.css("div.i-stars.i-stars--regular-5.rating-large ::text").extract()):
            ratings [str(i+1)] = r
        #NEXT_PAGE_SELECTOR = 'a.tab-link.js-dropdown-link.tab-link--dropdown.js-tab-link--dropdown ::attr(href)'

        NEXT_PAGE_SELECTOR = '.u-decoration-none.next.pagination-links_anchor ::attr(href)'
        next_page = response.css(NEXT_PAGE_SELECTOR).extract_first()
        yield {"title" : response.css("h1.biz-page-title.embossed-text-white::text").extract_first().strip(),
               #"review 1st" : res.css("div.review-content.p.de::text").extract()
               #"review 1st" : res.css("#super-container > div > div > div.column.column-alpha.main-section > "
               #                       "div:nth-child(3) > div.feed > div.review-list > ul > li:nth-child(2) > "
               #                       "div > div.review-wrapper > div.review-content > p").extract(),
               #"review 2nd" : res.css("div.review-content > p").extract_first(),
               #"review 3rd" : res.css("div.review-content > p").extract(),
               #"review 4th" : res.css("div.review-content > p::text").extract()
               "reviews" : reviews,
               "Next page is" : (str(next_page), bool(next_page))
               }

        #open_in_browser(response)

        #NEXT_PAGE_SELECTOR = 'a.tab-link.js-dropdown-link.tab-link--dropdown.js-tab-link--dropdown ::attr(href)'

        self.driver.quit()
        # time.sleep(10)
        # if next_page:
        #     yield scrapy.Request(
        #         response.urljoin(next_page),
        #         #res.urljoin(next_page),
        #         callback=self.parse
        #     )
