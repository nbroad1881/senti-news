import scrapy
from scrapy.crawler import CrawlerProcess
import json
import datetime
import sys
import requests

class NewsSpider(scrapy.Spider):
    """Spider to grab news text
    """
    name = 'scrape-news'
    print(sys.argv)
    start_urls = [
        'https://search.api.cnn.io/content?size=100&q=biden%20%7C%20sanders%20%7C%20warren%20%7C%20buttigieg%20%7C'
        '%20harris&category=us&type=article&sort=newest',
        'https://api.foxnews.com/v1/content/search?q=buttigieg%20|%20harris%20|%20sanders&ss=fn&section.path=fnc'
        '/politics&type=story&min_date=2019-10-22&max_date=2019-10-23&start=0&callback=angular.callbacks._0&cb'
        '=2019101792',

    ]

    def parse(self, response):
        pass


today = datetime.date.today().isoformat()


process = CrawlerProcess()
process.crawl(NewsSpider)
process.start()


# For cnn, you can go to the next page by appending on '&from={}&page=2'
# In the brackets should be the number put as the value for size in
# the original query.

def form_fox_query(q, min_date, max_date, start):
    s_1 = 'https://api.foxnews.com/v1/content/search?q='
    q = 'biden'
    s_2 = '&fields=date,description,title,url,image,type,taxonomy&section.path=fnc&type=article&min_date='
    min_dt = '2019-01-01'
    s_3 = '&max_date='
    max_dt = '19-10-01'
    s_4 = '&start='
    start = 0
    s_5 = '&callback=angular.callbacks._0&cb=2019101792'
    return ''.join([s_1, q, s_2, min_dt, s_3, max_dt, s_4, start, s_5])


def scrape_nyt(response):
    title = response.xpath('./head/title//text()').get()
    body = response.xpath('//section[contains(@name, "articleBody")]//text()').getall()


def scrape_cnn():
    url = 'https://search.api.cnn.io/content?size=100&q=biden%20%7C%20sanders%20%7C%20warren%20%7C%20buttigieg%20%7C' \
      '%20harris&category=us&type=article&sort=newest'
    response = requests.get(url)
    if response.status_code == 200:
        articles = json.loads(response.text)
        with open('cnn_articles.txt','a') as f:
            for a in articles:
                if a.type != 'article':
                    #skip over
                f.write(a['_id']+'\n')
                f.write(a['body']+'\n')
                f.write(a['url']+'\n')
                f.write(a['firstPublishDate']+'\n')
                f.write(a['headline']+'\n')



