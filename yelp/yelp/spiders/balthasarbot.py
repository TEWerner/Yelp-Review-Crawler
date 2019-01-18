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
#scrapy crawl <spider name> -o file.csv
class BalthasarbotSpider(scrapy.Spider):
    name = 'balthasarbot'
    allowed_domains = ['yelp.de','yelp.com']
    #start_urls = ['http://https://www.yelp.com/biz/restaurant-balthasar-paderborn/']
    start_urls = ["https://www.yelp.com/search?find_desc=&find_loc=Paderborn&ns=1"]
    #start_urls = ["https://www.yelp.com/search?find_desc=&find_loc=Paderborn&ns=1","https://www.yelp.com/biz/argentina-paderborn-2?osq=argentina"]
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
        restaurant_reviews = {} # the key is the name of the restaurants and the items are a tuples with the reviews
        # TODO: search for example each city to get a list of restaurants (disjoint lists at best)
        yield scrapy.Request(
            response.urljoin(response.url),
            callback=self.parse_search_result,
            meta={'results':restaurant_reviews}     #TODO:  This dict is empty for new Requests, and is usually populated by different Scrapy components
        )
        #restaurant_reviews = response.meta.get('results')
        #self.driver.quit()  # if we quit at this / any point the request will fail

        #yield restaurant_reviews
    def parse_search_result(self, response):
        # TODO: The restaurant passing needs to be dynamically
        restaurant_reviews = response.meta.get('results')
        for l in response.xpath("//*/h3/a"):
            #RESTAURANT_SELECTOR = l.xpath("/@href").extract()
            RESTAURANT_LINK = "https://www.yelp.com" + l.xpath("./@href").extract()[0]
            #response.meta['page'] = 1
            yield scrapy.Request(
                response.urljoin(RESTAURANT_LINK),
                callback=self.parse_restaurant,
                meta = {'results': {}, 'page': 1}
            )

    def parse_restaurant(self, response):
        self.driver.get(response.url)
        restaurant_reviews = response.meta.get('results')
        page = response.meta.get('page') # current page
        wait = WebDriverWait(self.driver, 10)
        rev = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.review-sidebar")))
        #res = response.replace(body=self.driver.page_source)
        response = response.replace(body=self.driver.page_source)
        #open_in_browser(response)

        if page == 1:
            try:
                name = response.css(
                    "h1.biz-page-title.embossed-text-white::text").extract_first().strip()
                # if name == None:
                #     raise TypeError('Name is None.')
                restaurant_reviews[name] = []
            except AttributeError:
                name = response.css(
                    "h1.biz-page-title.embossed-text-white.shortenough::text").extract_first().strip()
                restaurant_reviews[name] = []
            except TypeError:
                name = response.css(
                    "h1.biz-page-title.embossed-text-white::text").extract_first().strip()
                restaurant_reviews[name] = []
        else:
            try:
                name = response.css(
                    "h1.biz-page-title.embossed-text-white::text").extract_first().strip()
            except AttributeError:
                name = response.css(
                    "h1.biz-page-title.embossed-text-white.shortenough::text").extract_first().strip()

        #restaurant_reviews[name] = []
        reviews = [] # getting the reviews
        for i, r in enumerate(response.css("div.review-content > p").extract()):
            reviews.append(self.cleanhtml(r))
        ratings = [] # getting the ratings of the reviews
        for i, r in enumerate(response.xpath('//*[@class="biz-rating biz-rating-large clearfix"]//*/@title').extract()):
            ratings.append(r.strip())
        pictures = [] # see if images exist
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
                pictures.append("No picture found")

        for i, r in enumerate(reviews):
            try:
                #try:
                    #name = response.css("h1.biz-page-title.embossed-text-white::text").extract_first().strip()
                restaurant_reviews[name].append((ratings[i],r,pictures[i]))
                #except TypeError:
                    #name = response.css("h1.biz-page-title.embossed-text-white.shortenough::text").extract_first().strip()
                    #restaurant_reviews[name].append((ratings[i],r,pictures[i]))
            except TypeError:
                print("Do nothing or to do")
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

        #open_in_browser(response) #   useful to see what Scrapy sees

        # NEXT_PAGE_SELECTOR = 'a.tab-link.js-dropdown-link.tab-link--dropdown.js-tab-link--dropdown ::attr(href)'
        #response.meta['results'] = restaurant_reviews
        time.sleep(3)
        if next_page:
            #response.meta['page'] = page + 1
            yield scrapy.Request(
                response.urljoin(next_page),
                # res.urljoin(next_page),
                callback=self.parse_restaurant,
                meta={'page': page+1,
                      'results':restaurant_reviews}
                )
        elif 'de' in response.xpath('.//*[@class="tab-link js-dropdown-link tab-link--dropdown js-tab-link--dropdown"]/@data-lang').extract():
            ger_page = response.xpath('.//*[@class="tab-link js-dropdown-link tab-link--dropdown js-tab-link--dropdown" and @data-lang="de"]/@href').extract_first()
            #response.meta['page'] = page + 1
            #response.meta['results'] = results
            #response.meta['page'] = 1
            yield scrapy.Request(
                response.urljoin(ger_page),
                callback=self.parse_restaurant,
                meta={'page': page+1,   # we continue counting pages
                      'results':restaurant_reviews}
            )
        else:
            #results['German'] = response.xpath('.//*[@class="tab-link js-dropdown-link tab-link--dropdown js-tab-link--dropdown"]/@data-lang').extract_first()
            #results['link'] = response.xpath('.//*[@class="tab-link js-dropdown-link tab-link--dropdown js-tab-link--dropdown" and @data-lang="de"]/@href').extract()
            yield restaurant_reviews