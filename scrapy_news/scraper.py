import scrapy
from scrapy.crawler import CrawlerProcess
import json
import datetime
import sys
import requests


# todo: have an interactive query
#     database for text documents
class NewsSpider(scrapy.Spider):
    """Spider to grab news text
    """
    name = 'scrape-news'

    def __init__(self, start_urls=[]):
        super().__init__()
        self.start_urls = start_urls

    # print(sys.argv)
    # start_urls = [
    #     'https://search.api.cnn.io/content?size=100&q=biden%20%7C%20sanders%20%7C%20warren%20%7C%20buttigieg%20%7C'
    #     '%20harris&category=us&type=article&sort=newest',
    #     'https://api.foxnews.com/v1/content/search?q=buttigieg%20|%20harris%20|%20sanders&ss=fn&section.path=fnc'
    #     '/politics&type=story&min_date=2019-10-22&max_date=2019-10-23&start=0&callback=angular.callbacks._0&cb'
    #     '=2019101792',
    #
    # ]

    def parse(self, response):
        if('angular' in response.text[:30]):
            fox_urls = get_fox_urls(response)
            # scrape_fox(fox_urls)
        print('HELLO'.center(50, '*'))
        print(response.url)


def form_fox_query(q, min_date, max_date, start):
    s_1 = 'https://api.foxnews.com/v1/content/search?q='
    q = q
    s_2 = '&fields=date,description,title,url,image,type,taxonomy&section.path=fnc&type=article&min_date='
    min_dt = min_date
    s_3 = '&max_date='
    max_dt = max_date
    s_4 = '&start='
    start = str(start)
    s_5 = '&callback=angular.callbacks._0&cb=20191024112'
    return ''.join([s_1, q, s_2, min_dt, s_3, max_dt, s_4, start, s_5])


# todo: writes text to file
def scrape_nyt(response):
    title = response.xpath('./head/title//text()').get()
    body = response.xpath('//section[contains(@name, "articleBody")]//text()').getall()


# For cnn, you can go to the next page by appending on '&from={}&page=2'
# In the brackets should be the number put as the value for size in
# the original query.

# todo: loop the correct number of times according to num_results
#   and come up with a way to check for duplicate articles
#   have support for date in the query
def scrape_cnn():
    url = 'https://search.api.cnn.io/content?size=100&q=biden%20%7C%20sanders%20%7C%20warren%20%7C%20buttigieg%20%7C' \
          '%20harris&category=us&type=article&sort=newest'
    response = requests.get(url)
    if response.status_code == 200:
        articles = json.loads(response.text)['result']
        with open('cnn_articles.txt', 'a') as f:
            num_results = None
            for a in articles:
                if num_results is None:
                    num_results = json.loads(response.text)['meta']['of']
                if a.type != 'article':
                    pass
                    # skip over
                f.write(a['_id'] + '\n')
                f.write(a['body'] + '\n')
                f.write(a['url'] + '\n')
                f.write(a['firstPublishDate'] + '\n')
                f.write(a['headline'] + '\n')


def get_fox_urls(response):
    try:
        text = response.text[21:]
        if len(text) < 0:
            print(f'Response was not usual length \n{text}')
            return ''
    except TypeError:
        print(f'Response text was not a string object but of type {type(text)}')
        return ''
    res = json.loads(text)
    n_results = res['numFound']
    urls = [n_results]
    for d in res['docs']:
        dt = d['date']
        title = d['title']
        url = d['url']
        urls.append((dt, title, url))
    return urls


today = datetime.date.today().isoformat()

if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(NewsSpider, start_urls=[form_fox_query(q='biden', '2019-01-01', '2019-10-10', start=0)])
    process.start()
