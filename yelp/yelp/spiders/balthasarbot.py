# -*- coding: utf-8 -*-
import scrapy
from selenium import webdriver
from scrapy.selector import Selector
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
        self.options = Options()
        self.options.headless = True
        #self.options.set_headless(headless=True)
        self.driver = webdriver.Chrome(options=self.options, executable_path="C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe")
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
        restaurant_reviews = {}
    # TODO: The restaurant passing needs to be dynamically
        yield scrapy.Request(
            response.urljoin(response.url),
            callback=self.parse_restaurant,
            meta={'page': 1, 'results':restaurant_reviews}
        )
        #yield response.meta.get('results')
    def parse_restaurant(self, response):
        results = response.meta.get('results')
        page = response.meta.get('page') # current page

        wait = WebDriverWait(self.driver, 10)
        rev = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.review-sidebar")))
        res = response.replace(body=self.driver.page_source)
        # open_in_browser(response)
        if page == 1:
            results[response.css("h1.biz-page-title.embossed-text-white::text").extract_first().strip()] = []
        reviews = []
        for i, r in enumerate(response.css("div.review-content > p").extract()):
            reviews.append(self.cleanhtml(r))
        ratings = []
        #for i, r in enumerate(response.xpath('//*[@class="i-stars i-stars--regular-5 rating-large"]/@title').extract()):
        for i, r in enumerate(response.xpath('//*[@class="biz-rating biz-rating-large clearfix"]//*/@title').extract()):
            ratings.append(r.strip())
        pictures = []
        content = response.xpath('.//*[@class="review-content"]')
        for div in content:
            pic = div.xpath(".//ul/li/div/a/@href")
            #pic = div.xpath('//*[@class="biz-shim js-lightbox-media-link js-analytics-click"]/@href')
            #pic = Selector(text=div.extract()).xpath('//*[contains(@class, "biz-shim js-lightbox-media-link js-analytics-click")]')
            if pic:
                pictures.append("Picture found")
                    #div.xpath('//a[@class="biz-shim js-lightbox-media-link js-analytics-click"]/@href').extract())
                #pictures.append(div.css(' > p').extract()))
            else:
                pictures.append("Picture not found")
        for i, r in enumerate(reviews):
            try:
                results[response.css("h1.biz-page-title.embossed-text-white::text").extract_first().strip()].append((ratings[i],r,pictures[i]))
            except IndexError:
                results[response.css("h1.biz-page-title.embossed-text-white::text").extract_first().strip()].append((ratings[i],r))
        NEXT_PAGE_SELECTOR = '.u-decoration-none.next.pagination-links_anchor ::attr(href)'
        next_page = response.css(NEXT_PAGE_SELECTOR).extract_first()

        page_content = {"title": response.css("h1.biz-page-title.embossed-text-white::text").extract_first().strip(),
                        # "review 1st" : res.css("div.review-content.p.de::text").extract()
                        # "review 1st" : res.css("#super-container > div > div > div.column.column-alpha.main-section > "
                        #                       "div:nth-child(3) > div.feed > div.review-list > ul > li:nth-child(2) > "
                        #                       "div > div.review-wrapper > div.review-content > p").extract(),
                        # "review 2nd" : res.css("div.review-content > p").extract_first(),
                        # "review 3rd" : res.css("div.review-content > p").extract(),
                        # "review 4th" : res.css("div.review-content > p::text").extract()
                        "page number": page,
                        "reviews": reviews,
                        "ratings": ratings,
                        "Next page is": (str(next_page), bool(next_page))
                        }

        # open_in_browser(response) #   useful to see what Scrapy sees

        # NEXT_PAGE_SELECTOR = 'a.tab-link.js-dropdown-link.tab-link--dropdown.js-tab-link--dropdown ::attr(href)'

        # self.driver.quit() # if we quit at this point the request will fail
        time.sleep(5)
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                # res.urljoin(next_page),
                callback=self.parse_restaurant,
                meta={'page': page+1, 'results':results}
                )
        else:
            yield results
