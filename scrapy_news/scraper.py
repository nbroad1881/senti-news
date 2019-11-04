import csv
import datetime
import logging
import json
import time
import pathlib
from abc import ABC, abstractmethod

import scrapy
import requests
from scrapy.crawler import CrawlerProcess

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
    article_source = None

    def __init__(self, article_source, start_urls=None):
        """
        Initialize the spider.

        :type start_urls: List(str)
        """

        self.article_source = article_source
        # self.start_urls = [] if start_urls is None else start_urls
        # self.unique_ids = set() if unique_ids is None else unique_ids

        logging.debug("Spider initialized.")

    def parse(self, response):
        """
        Parses the response and yields Request objects.
        """

        logging.info("Parsing started")

        self.article_source.parse(response)

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

class ArticleSource(ABC):

    @abstractmethod
    def scrape(self, response):
        pass

    @abstractmethod
    def get_unique_ids(self):
        pass

    @abstractmethod
    def set_unique_ids(self):
        pass

    @abstractmethod
    def store_article(self):
        pass

    @abstractmethod
    def form_query(self):
        pass


class NYT(scrapy.Spider):
    UNIQUE_IDS_PATH = pathlib.Path('NYT_unique_ids.csv')
    ARTICLE_TEXT_PATH = pathlib.Path('../saved_texts/NYT/texts')
    ARTICLE_INFO_PATH = pathlib.Path('../saved_texts/NYT/info')
    TESTING_QUERY = 'https://api.nytimes.com/svc/search/v2/articlesearch.json?begin_date=20191001&end_date=20191031' \
                    '&facet=true&facet_fields=document_type&fq=article&q=biden&sort=newest&api-key' \
                    '=nSc6ri8B5W6boFhjJ6SuYpQmLN8zQuV7 '

    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 6
    }

    def __init__(self):
        self.unique_ids = self.get_unique_ids()

    @staticmethod
    def ask_for_query():
        query = input('What is the query? (e.g. biden, sanders, warren): ')
        begin_date = input('What is the oldest date? (YYYYMMDD): ')
        end_date = input('What is the newest date? (YYYYMMDD): ')
        return query, begin_date, end_date

    def start_requests(self):
        query, begin_date, end_date = self.ask_for_query()
        all_urls = []
        all_info = []
        for p in range(10):
            api_url = self.form_query(query=query, page=p, begin_date=begin_date, end_date=end_date)
            urls, info = self.make_api_call(api_url)

            if urls is not None:
                all_urls.extend(urls)
                all_info.extend(info)

        for url, info in zip(all_urls, all_info):
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs=dict(id_=info['id']))

    def parse(self, response, id_):
        # todo: check for bad responses
        body = ' '.join(response.xpath('//section[contains(@name, "articleBody")]//text()').getall())
        self.store_article(body, id_)
        self.set_unique_ids()

    def make_api_call(self, api_url):
        logging.debug(f'api_url:{api_url}')
        response = requests.get(api_url)
        if response.status_code == 200:
            start_urls = []
            info = []
            for doc in json.loads(response.text)['response']['docs']:
                url = doc['web_url']
                date = doc['pub_date']
                id_ = doc['_id']
                title = doc['headline']['main']
                doc_type = doc['document_type']
                source = doc['source']
                material_type = doc['type_of_material']

                # Id has many slashes that are unnecessary and make storing files harder
                id_ = id_[id_.rindex('/') + 1:]
                if id_ in self.unique_ids:
                    continue
                self.unique_ids.add(id_)

                start_urls.append(url)
                info.append({
                    'url': url,
                    'date': date,
                    'id': id_,
                    'title': title,
                    'doc_type': doc_type,
                    'source': source,
                    'material_type': material_type
                })

                logging.debug(f'url:{url}\n'
                              f'date:{date}\n'
                              f'id:{id_}\n'
                              f'title:{title}\n'
                              f'doc_type:{doc_type}\n'
                              f'source:{source}\n'
                              f'material_type:{material_type}\n')
            return start_urls, info
        logging.debug(f'Response status code:{response.status_code}')
        return None, None

    def get_unique_ids(self):
        try:
            with open(self.UNIQUE_IDS_PATH, 'r') as file:
                reader = csv.reader(file)
                return set(next(reader))
        except FileNotFoundError:
            logging.debug('No unique id file, return empty set')
            return set()

    def set_unique_ids(self):
        with open(self.UNIQUE_IDS_PATH, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(list(self.unique_ids))

    def store_article(self, text, id_):
        with open(self.ARTICLE_TEXT_PATH / f'{id_}.txt', 'w') as file:
            file.write(text)

    def store_info(self, info):
        with open(self.ARTICLE_INFO_PATH, 'a') as file:
            logging.debug(f'Wrote NYT article ({info["id"]}) to file')
            writer = csv.writer(file)
            writer.writerow([info['url'],
                             info['date'],
                             info['id'],
                             info['title'],
                             info['doc_type'],
                             info['source'],
                             info['material_type']])

    @staticmethod
    def form_query(query, page, begin_date='20190301', end_date='20191001', sort='newest'):
        return ''.join([f'https://api.nytimes.com/svc/search/v2/articlesearch.json?q={query}',
                        f'&facet=true&page={str(page)}&begin_date={begin_date}&end_date={end_date}',
                        f'&facet_fields=document_type&fq=article',
                        f'&sort={sort}&api-key=nSc6ri8B5W6boFhjJ6SuYpQmLN8zQuV7'])


class CNN(scrapy.Spider):
    UNIQUE_IDS_PATH = pathlib.Path('CNN_unique_ids.csv')
    ARTICLE_TEXT_PATH = pathlib.Path('../saved_texts/CNN/texts')
    ARTICLE_INFO_PATH = pathlib.Path('../saved_texts/CNN/text_info')
    CNN_RESULTS_SIZE = 100

    # TESTING_QUERY = 'https://api.nytimes.com/svc/search/v2/articlesearch.json?begin_date=20191001&end_date=20191031' \
    #                 '&facet=true&facet_fields=document_type&fq=article&q=biden&sort=newest&api-key' \
    #                 '=nSc6ri8B5W6boFhjJ6SuYpQmLN8zQuV7 '

    def __init__(self):
        self.unique_ids = self.get_unique_ids()

    @staticmethod
    def ask_for_query():
        query = input('What is the query? (e.g. biden, sanders, warren): ')
        return query

    def start_requests(self):
        query = self.ask_for_query()
        api_url = self.form_query(query, page=1)
        num_results = self.make_api_call(api_url)

        for p in range(1, num_results // self.CNN_RESULTS_SIZE):
            url = self.form_query(query, page=p)
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        articles = json.loads(response.text)['result']
        for a in articles:
            if a['type'] != 'article' or a['_id'] in self.unique_ids:
                continue
            info = {
                "date": a['firstPublishDate'],
                "title": a['headline'],
                "url": a['url'],
                'id': a['_id']
            }
            self.unique_ids.add(info['id'])
            self.store_article(a['body'], info['id'])
            self.store_info(info)
            self.set_unique_ids()

    def make_api_call(self, api_url):
        """
        Calls CNN API and returns the number of results.
        Using requests library would be sufficient, but for
        consistency Scrapy will be used.
        :param api_url:
        :return:
        """
        response = requests.get(api_url)
        if response.status_code == 200:
            logging.debug('Request accepted (200)')
            return json.loads(response.text)['meta']['of']
        else:
            logging.debug(f'Request denied ({response.status_code})')

    def get_unique_ids(self):
        """
        Ids should be comma delimited with no line breaks
        :return: set of ids or empty set if file not found
        """
        try:
            with open(self.UNIQUE_IDS_PATH, 'r') as file:
                reader = csv.reader(file)
                return set(next(reader))
        except FileNotFoundError:
            logging.debug('No unique id file, return empty set')
            return set()

    def set_unique_ids(self):
        with open(self.UNIQUE_IDS_PATH, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(list(self.unique_ids))

    def store_article(self, text, id_):
        with open(self.ARTICLE_TEXT_PATH / f'{id_}.txt', 'w') as file:
            file.write(text)

    def store_info(self, info):
        with open(self.ARTICLE_INFO_PATH / "CNN_INFO.csv", 'a') as file:
            logging.debug(f'Wrote CNN article ({info["id"]}) to file')
            writer = csv.writer(file)
            writer.writerow([info['url'],
                             info['date'],
                             info['id'],
                             info['title']])

    def form_query(self, query, page):
        return f'https://search.api.cnn.io/content?size={self.CNN_RESULTS_SIZE}' \
               f'&q={query}&type=article&sort=relevance&page={page}&from={str(page * self.CNN_RESULTS_SIZE)}'


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


if __name__ == "__main__":

    response = input("Which news company would you like to scrape?\n"
                     "1. CNN\n"
                     "2. Fox News\n"
                     "3. NYTimes\n"
                     "4. (in future) Debug Mode\n")
    process = CrawlerProcess()
    if int(response) == 1:
        process.crawl(CNN)
    elif int(response) == 2:
        fox_news()
    elif int(response) == 3:
        process.crawl(NYT)
    else:
        pass
    try:
        process.start()
    finally:
        pass
