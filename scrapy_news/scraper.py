import scrapy
from scrapy.crawler import CrawlerProcess
import json
import datetime
import csv
import requests

CNN_RESULTS_SIZE = 100
DEM_CANDIDATES = ['biden', 'warren', 'sanders', 'harris', 'buttigieg']


# todo: have an interactive query
#     database for text documents
def scrape_fox(response, date='', title=''):
    with open('fox_articles.csv', 'a') as f:
        writer = csv.writer(f)
        writer.writerow([date, title, ' '.join(response.xpath('//div[(@class="article-body")]//p/text()|//div['
                                                              '@class="article-body"]//p/a/text()').getall())])


class NewsSpider(scrapy.Spider):
    """Spider to grab news article text
    """
    name = 'scrape-news'

    def __init__(self, start_urls=[], unq_ids=set()):
        """

        :type start_urls: List(str)
        """
        super().__init__()
        self.start_urls = start_urls
        self.unq_ids = unq_ids

    def parse(self, response):
        if 'angular' in response.text[:30]:
            d = json.loads(response.text[21:-1])
            fox_info = get_fox_info(d['response'])
            for d, t, u, i in fox_info:
                if u[0] in self.unq_ids or i != 'article':
                    continue
                yield scrapy.Request(u[0], callback=scrape_fox, cb_kwargs=dict(date=d, title=t))
                self.unq_ids.add(u[0])


#   i.e the 2nd page starts at start=10, 3rd page at start=20
def form_fox_query(q, min_date, max_date, start):
    s_1 = 'https://api.foxnews.com/v1/content/search?q='
    q = q
    s_2 = '&fields=date,description,title,url,image,type,taxonomy&section.path=fnc&type=article&min_date='
    min_dt = min_date
    s_3 = '&max_date='
    max_dt = max_date
    s_4 = '&start='
    start = str(start)
    s_5 = '&callback=angular.callbacks._0&cb='
    dt_today = datetime.date.today().isoformat().replace('-', '')
    s_6 = '112'
    return ''.join([s_1, q, s_2, min_dt, s_3, max_dt, s_4, start, s_5, dt_today, s_6])


# todo: writes text to file
def scrape_nyt(response):
    title = response.xpath('./head/title//text()').get()
    body = response.xpath('//section[contains(@name, "articleBody")]//text()').getall()


def scrape_cnn(unq_ids, _from=0, name=''):
    """Searches cnn for name, saving articles that are not in the unique
    id set. Ordered by newest, rather than by relevance. Relevance produces
    results from 2017 first"""
    url = f'https://search.api.cnn.io/content?size={CNN_RESULTS_SIZE}' \
          f'&q={name}&type=article&sort=newest&from={str(_from)}'
    response = requests.get(url)
    if response.status_code == 200:
        print(f'Request accepted ({name}), from={_from}')
        if _from > 1000:
            return
        articles = json.loads(response.text)['result']
        num_results = json.loads(response.text)['meta']['of']
        with open('../texts/cnn_articles.csv', 'a') as f:
            writer = csv.writer(f)
            for a in articles:
                if a['type'] != 'article' or a['_id'] in unq_ids:
                    continue
                writer.writerow([a['firstPublishDate'], a['headline'], a['url'], a['_id'], a['body']])
                unq_ids.add(a['_id'])
        if _from + CNN_RESULTS_SIZE < num_results:
            scrape_cnn(unq_ids, _from=_from + CNN_RESULTS_SIZE, name=name)


def get_unique_cnn_ids():
    """Returns a set of unique cnn article ids"""
    try:
        with open('cnn_ids.csv', 'r') as f:
            reader = csv.reader(f)
            ids = set()
            for row in reader:
                ids.update(row)
            return ids
    except FileNotFoundError:
        print('cnn_ids.csv does not exist yet, returning empty set')
        return set()


def get_unique_fox_ids():
    """Returns a set of unique fox article ids.
    There are no actual id tag for fox articles,
    so this treats each url as a unique id
    """
    try:
        with open('fox_ids.csv', 'r') as f:
            reader = csv.reader(f)
            ids = set()
            for row in reader:
                ids.update(row)
            return ids
    except FileNotFoundError:
        print('fox_ids.csv does not exist yet, returning empty set')
        return set()


def set_unique_cnn_ids(unq_ids):
    """Stores the unique article ids in a csv
    Always overwrites"""
    with open('cnn_ids.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(list(unq_ids))


def set_unique_fox_ids(unq_ids):
    """Stores the unique article urls in a csv
    Always overwrites"""
    with open('fox_ids.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(list(unq_ids))


def get_fox_info(res):
    """Pulls date, title, and url from API response"""
    urls = []
    for d in res['docs']:
        dt = d['date']
        title = d['title']
        url = d['url']
        _type = d['type']
        urls.append((dt, title, url, _type))
    return urls


def cnn():
    cnn_ids = get_unique_cnn_ids()
    for c in DEM_CANDIDATES:
        scrape_cnn(unq_ids=cnn_ids, name=c)
    set_unique_cnn_ids(cnn_ids)


def fox_news():
    process = CrawlerProcess()
    process.crawl(NewsSpider, start_urls=[form_fox_query('biden', '2019-01-01', '2019-10-10', 0)])
    process.start()


if __name__ == "__main__":

    response = input("Which news company would you like to scrape?\n"
                     "1. CNN\n2. Fox News\n3. NYTimes\n4. All of the above")
    if int(response) == 1:
        cnn()
    elif int(response) == 2:
        fox_news()
    elif int(response) == 3:
        pass
    elif int(response) == 4:
        pass
