import csv
import datetime
import logging
import json
import time

import scrapy
import requests
from scrapy.crawler import CrawlerProcess

CNN_RESULTS_SIZE = 100
DEM_CANDIDATES = ['biden', 'warren', 'sanders', 'harris', 'buttigieg']
NYT_ARTICLES_CSV = 'nyt_articles.csv'
CNN_ARTICLES_CSV = '../saved_texts/cnn_articles.csv'

logging.basicConfig(level=logging.INFO)


# todo: have an interactive query
#     database for text documents

class NewsSpider(scrapy.Spider):
    """
    Spider to grab news article text.
    """

    name = 'scrape-news'
    FOX_ARTICLES_CSV = 'fox_articles.csv'

    # TODO: Do not use mutable objects as default values
    def __init__(self, start_urls=None, unique_ids=None):
        """
        Initialize the spider.

        :type start_urls: List(str)
        """

        self.start_urls = [] if start_urls is None else start_urls
        self.unique_ids = set() if unique_ids is None else unique_ids

        logging.debug("Spider initialized.")

    def parse(self, response):
        """
        Parses the response and yields Request objects.
        """

        logging.info("Parsing started")

        if 'angular' in response.text[:30]:
            logging.debug("Scraping Fox info.")
            fox_info = get_fox_info(json.loads(response.text[21:-1])['response'])

            for date, title, url, id_ in fox_info:
                if url[0] in self.unique_ids or id_ != 'article':
                    continue
                yield scrapy.Request(
                    url[0],
                    callback=self.scrape_fox,
                    cb_kwargs=dict(date=date, title=title)
                )
                self.unique_ids.add(url[0])

        elif 'New York Times' in response.text[:100]:
            logging.debug("Scraping NYT.")
            nyt_info = get_nyt_info(json.loads(response.text)['response']['docs'])
            for url, dt, _id in nyt_info:
                print(f'url:{url}\ndate:{dt}\nid:{_id}')
                time.sleep(6)
                yield scrapy.Request(url, callback=scrape_nyt, cb_kwargs=dict(date=dt, _id=_id))

        logging.info("Parsing done")

    def scrape_fox(self, response, date='', title=''):
        """
        #TODO
        """

        with open(self.FOX_ARTICLES_CSV, 'a') as f:
            writer = csv.writer(f)

            article_text = ' '.join(response.xpath(
                '//div[(@class="article-body")]//p/text()|'
                '//div[@class="article-body"]//p/a/text()'
            ).getall())

            writer.writerow([date, title, article_text])


#   i.e the 2nd page starts at start=10, 3rd page at start=20
def form_fox_query(q, min_date, max_date, start):
    return ''.join([
        f'https://api.foxnews.com/v1/content/search?q={q}',
        f'&fields=date,description,title,url,image,type,taxonomy&section.path=fnc&type=article&min_date={min_date}',
        f'&max_date={max_date}&start={str(start)}&callback=angular.callbacks._0&cb=',
        datetime.date.today().isoformat().replace('-', ''),
        '112'])


# TODO: Suggestion - implement a subclass for each news provider of a generic news provider interface class

# import abc
#
# class ArticleSource:
#
#    @abc.abstractmethod
#    def scrape(response):
#        pass

# class SchoolNewspaper(ArticleSource):


def scrape_nyt(response, date, _id):
    # TODO: See above
    title = response.xpath('./head/title//text()').get()
    body = response.xpath('//section[contains(@name, "articleBody")]//text()').getall()
    with open(NYT_ARTICLES_CSV, 'a') as file:
        logging.debug(f'Wrote NYT article ({_id}) to file')
        writer = csv.writer(file)
        writer.writerow([date, title, _id, ' '.join(body)])


def scrape_cnn(unique_ids, _from=0, name=''):
    # TODO: See above
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

        with open(CNN_ARTICLES_CSV, 'a') as f:
            writer = csv.writer(f)
            for a in articles:
                if a['type'] != 'article' or a['_id'] in unique_ids:
                    continue
                writer.writerow([a['firstPublishDate'], a['headline'], a['url'], a['_id'], a['body']])
                unique_ids.add(a['_id'])

        if _from + CNN_RESULTS_SIZE < num_results:
            scrape_cnn(unique_ids, _from=_from + CNN_RESULTS_SIZE, name=name)


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


def set_unique_cnn_ids(unique_ids):
    """Stores the unique article ids in a csv
    Always overwrites"""
    with open('cnn_ids.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(list(unique_ids))


def set_unique_fox_ids(unique_ids):
    """Stores the unique article urls in a csv
    Always overwrites"""
    with open('fox_ids.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(list(unique_ids))


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
        scrape_cnn(unique_ids=cnn_ids, name=c)
    set_unique_cnn_ids(cnn_ids)


def fox_news():
    dt_today = datetime.date.today().isoformat()

    unique_ids = get_unique_fox_ids()
    try:
        for c in DEM_CANDIDATES:
            start = form_fox_query('biden', '2019-01-01', dt_today, 0)
            r = requests.get(start).text
            j = json.loads(r[21:-1])
            num_results = j['response']['numFound']
            num_results = 1000 if num_results > 1000 else num_results
            start_urls = [form_fox_query(c, '2019-03-01', dt_today, n) for n in range(0, num_results, 10)]
            process = CrawlerProcess()
            process.crawl(NewsSpider, start_urls=start_urls, unique_ids=unique_ids)
            process.start()
            set_unique_fox_ids(unique_ids)
    except Exception as e:
        print(e)
        set_unique_fox_ids(unique_ids)


def form_nyt_query(query, page, begin_date='20190301', end_date='20191001', sort='newest'):
    # TODO: this can be a one-liner!
    return ''.join([f'https://api.nytimes.com/svc/search/v2/articlesearch.json?q={query}',
                    f'&face=true&page={str(page)}&begin_date={begin_date}&end_date={end_date}',
                    f'fq=document_type%3Aarticle%20AND%20type_of_material%3ANews',
                    f'&sort={sort}&api-key=nSc6ri8B5W6boFhjJ6SuYpQmLN8zQuV7'])


# todo: have parameter be how many days back from today
#   the search should be. subtract from datetime object
def nyt():
    for c in DEM_CANDIDATES:
        date_today = datetime.date.today().isoformat().replace('-', '')
        url = form_nyt_query(query=c, end_date=date_today, page=0)
        r = requests.get(url)
        num_results = json.loads(r.text)['response']['meta']['hits']
        num_results = 1000 if num_results > 1000 else num_results
        start_urls = [form_nyt_query(query=c, end_date=date_today, page=n) for n in range(num_results // 10)]
        process = CrawlerProcess(settings={
            'CONCURRENT_REQUESTS': 2,
            'DOWNLOAD_DELAY': 6
        })
        process.crawl(NewsSpider, start_urls=start_urls)
        process.start()


def get_nyt_info(docs):
    info = []
    for d in docs:
        url = d['web_url']
        dt = d['pub_date']
        _id = d['_id']
        info.append((url, dt, _id))
    return info


if __name__ == "__main__":

    response = input("Which news company would you like to scrape?\n"
                     "1. CNN\n"
                     "2. Fox News\n"
                     "3. NYTimes\n"
                     "4. All of the above\n")
    if int(response) == 1:
        cnn()
    elif int(response) == 2:
        fox_news()
    elif int(response) == 3:
        nyt()
    elif int(response) == 4:
        pass
