import logging
import json
from datetime import datetime, timedelta
from dateutil.parser import isoparse
from abc import ABC, abstractmethod
import os
from urllib.parse import quote

from dotenv import load_dotenv
import scrapy
from sentinews.scraping.scraping.items import NewsItem
import requests
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

load_dotenv()
logging.basicConfig(level=logging.DEBUG)


"""
api_scraper.py contains 1 abstract ArticleSource and 3 subclasses: NYT, CNN, FOX
Each will use scrapy to search the APIs of NYT, CNN, and FOX for news articles.
The query will contain presidential candidate names.
Parse turns each result into a NewsItem.
Every NewsItem will be sent through the item pipeline (NewsItemPipeline).
NewsItemPipeline will then send the result to the database
"""

DEFAULT_NUM_DAYS_BACK = 7
DEFAULT_UPTO_DATE = datetime.utcnow()
CANDIDATES = ['Donald Trump', 'Joe Biden', 'Bernie Sanders', 'Elizabeth Warren', 'Kamala Harris', 'Pete Buttigieg']


# todo: have an interactive QUERY database for text documents
class ArticleSource(ABC):
    CANDIDATE_DICT = {
        '1': 'Donald Trump',
        '2': 'Joe Biden',
        '3': 'Elizabeth Warren',
        '4': 'Bernie Sanders',
        '5': 'Kamala Harris',
        '6': 'Pete Buttigieg',
        '7': ''
    }

    def __init__(self, interactive, past_date=None, upto_date=None):
        self.articles_logged = 0
        self.interactive = interactive or False
        self.upto_date = upto_date or DEFAULT_UPTO_DATE
        self.past_date = past_date or self.upto_date - timedelta(days=DEFAULT_NUM_DAYS_BACK)

    def ask_for_query(self, *args, **kwargs):
        option = self.ask_for_candidate()
        while option not in self.CANDIDATE_DICT:
            print('Not valid selection. Try again.')
            option = self.ask_for_candidate()
        input_past_date = self.ask_for_date(past=True)
        while not self.is_valid_date(input_past_date):
            print('Not valid date. Try again.')
        input_upto_date = self.ask_for_date(past=False)
        while not self.is_valid_date(input_upto_date):
            print('Not valid date. Try again.')
            input_upto_date = self.ask_for_date(past=False)
        self.past_date = input_past_date
        self.upto_date = input_upto_date

        if option == '7':
            return [quote(c) for c in CANDIDATES]

        return [quote(self.CANDIDATE_DICT[option])]

    @staticmethod
    def ask_for_candidate():
        return input("Which candidate?\n"
                     "1. Donald Trump\n"
                     "2. Joe Biden\n"
                     "3. Elizabeth Warren\n"
                     "4. Bernie Sanders\n"
                     "5. Kamala Harris\n"
                     "6. Pete Buttigieg\n"
                     "7. All candidates\n")

    @staticmethod
    def ask_for_date(past=False):
        time_word = 'past' if past else 'most recent'
        return input(f'What is the {time_word} date? (YYYYMMDD): ')

    @staticmethod
    def is_valid_date(date_string):
        return isinstance(date_string, str) and len(date_string) == 8 and date_string.isdigit()

    @abstractmethod
    def make_api_query(self, *args, **kwargs):
        pass

    @abstractmethod
    def make_api_call(self, *args, **kwargs):
        pass

    @abstractmethod
    def make_date_strings(self):
        pass

    @staticmethod
    def improper_title(title):
        names = ['trump', 'biden', 'warren', 'sanders', 'harris', 'buttigieg']
        return sum([1 if name in title.lower() else 0 for name in names]) != 1


class NYT(scrapy.Spider, ArticleSource):
    NEWS_CO = 'The New York Times'

    # todo: handle rate
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 2
    }

    name = 'NYT'

    def __init__(self, **kwargs):
        ArticleSource.__init__(self, **kwargs)

    def start_requests(self):
        all_urls = []
        all_info = []
        if self.interactive:
            query = self.ask_for_query()
        else:
            query = [quote(c) for c in CANDIDATES]
        for q in query:
            for p in range(5):
                api_url = self.make_api_query(query=q, page=p)
                urls, info = self.make_api_call(api_url)

                if urls is not None:
                    all_urls.extend(urls)
                    all_info.extend(info)

        for url, info in zip(all_urls, all_info):
            yield scrapy.Request(url=url, callback=self.parse_request, cb_kwargs=dict(info=info))

    def parse_request(self, response, info):
        # todo: check for bad responses

        soup = BeautifulSoup(response.text, 'html.parser')
        texts = []
        for paragraphs in soup.select('section.meteredContent p'):
            texts.append(paragraphs.text)
        body = ' '.join(texts)

        item = NewsItem()
        item['url'] = info['url']
        item['datetime'] = info['datetime']
        item['title'] = info['title']
        item['news_co'] = self.NEWS_CO
        item['text'] = body
        yield item

    def make_api_call(self, api_url):
        logging.debug(f'api_url:{api_url}')
        response = requests.get(api_url)
        if response.status_code == 200:
            start_urls = []
            info = []
            for doc in json.loads(response.text)['response']['docs']:
                url = doc['web_url']
                date = doc['pub_date']
                title = doc['headline']['main']

                if self.improper_title(title):
                    continue

                start_urls.append(url)
                info.append({
                    'url': url,
                    'datetime': date,
                    'title': title,
                })

            return start_urls, info
        logging.debug(f'Response status code:{response.status_code}')
        return None, None

    # todo: use fq to filter results to have name in title
    # https://developer.nytimes.com/docs/articlesearch-product/1/overview
    def make_api_query(self, query, page, sort='newest'):
        begin_date, end_date = self.make_date_strings()
        return f'https://api.nytimes.com/svc/search/v2/articlesearch.json?q={query}' \
               f'&facet=true&page={page}&begin_date={begin_date}&end_date={end_date}' \
               f'&facet_fields=document_type&fq=article' \
               f'&sort={sort}&api-key=nSc6ri8B5W6boFhjJ6SuYpQmLN8zQuV7'

    def start_crawl(self, **kwargs):
        process = CrawlerProcess()
        process.crawl(self, **kwargs)

    def make_date_strings(self):
        return self.past_date.strftime('%Y%m%d'), self.upto_date.strftime('%Y%m%d')


class CNN(scrapy.Spider, ArticleSource):
    RESULTS_SIZE = 100
    NUM_PAGES = 5
    NEWS_CO = 'CNN'
    name = 'CNN'

    def __init__(self, **kwargs):
        ArticleSource.__init__(self, **kwargs)

    def start_requests(self):

        if self.interactive:
            query = self.ask_for_query()
        else:
            query = [quote(c) for c in CANDIDATES]
        for q in query:
            for p in range(self.NUM_PAGES):
                url = self.make_api_query(q, page=p)
                yield scrapy.Request(url=url, callback=self.parse_request)

    def parse_request(self, response):

        articles = json.loads(response.text)['result']
        for a in articles:
            if a['type'] != 'article':
                continue

            url = a['url']
            date_time = a['firstPublishDate']
            title = a['headline']
            body = a['body']

            if self.improper_title(title):
                continue

            article_datetime = isoparse(date_time)

            if not (self.past_date < article_datetime < self.upto_date):
                continue

            item = NewsItem()
            item['url'] = url
            item['datetime'] = date_time
            item['title'] = title
            item['news_co'] = self.NEWS_CO
            item['text'] = body
            yield item

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

    def make_api_query(self, query, page):
        return f'https://search.api.cnn.io/content?size={self.RESULTS_SIZE}' \
               f'&q={query}&type=article&sort=newest&page={page}' \
               f'&from={str(page * self.RESULTS_SIZE)}'

    def make_date_strings(self):
        return self.past_date.isoformat() + 'Z', self.upto_date.isoformat() + 'Z'


class FOX(scrapy.Spider, ArticleSource):
    PAGE_SIZE = 10
    NUM_PAGES = 10

    NEWS_CO = 'Fox News'
    name = 'Fox'

    def __init__(self, **kwargs):
        ArticleSource.__init__(self, **kwargs)

    def start_requests(self):
        if self.interactive:
            query = self.ask_for_query()
        else:
            query = [quote(c) for c in CANDIDATES]

        all_urls, all_info = [], []
        for q in query:
            for start in range(0,
                               self.PAGE_SIZE * self.NUM_PAGES,
                               self.PAGE_SIZE):
                api_url = self.make_api_query(q, start=start)
                urls, info = self.make_api_call(api_url)

                all_urls.extend(urls)
                all_info.extend(info)

        for url, info in zip(all_urls, all_info):
            yield scrapy.Request(url=url, callback=self.parse_request, cb_kwargs=dict(info=info))

    def parse_request(self, response, info):

        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.select('div.article-body p')
        texts = []
        for p in paragraphs:
            if not p.find('em') and not p.find('strong') and not p.find('span'):
                texts.append(p.text)

        body = ' '.join(texts)

        item = NewsItem()
        item['url'] = info['url']
        item['datetime'] = info['datetime']
        item['title'] = info['title']
        item['news_co'] = self.NEWS_CO
        item['text'] = body
        yield item

    def make_api_call(self, api_url):
        """
        Calls FOX API .
        Using the requests library would be sufficient, but for
        consistency Scrapy will be used. Requests used once to get
        the urls and info.
        :param api_url:
        :return:
        """
        response = requests.get(api_url)
        if response.status_code == 200:
            urls, infos = [], []

            text = json.loads(response.text[21:-1])['response']
            for d in text['docs']:
                info = {
                    'datetime': d['date'],
                    'title': d['title'],
                    'url': d['url'][0],
                }
                if self.improper_title(info['title']):
                    continue

                urls.append(info['url'])
                infos.append(info)
            return urls, infos
        else:
            return None

    def make_api_query(self, query, start):
        min_date, max_date = self.make_date_strings()
        return f'https://api.foxnews.com/v1/content/search?q={query}' \
               f'&fields=date,description,title,url,image,type,taxonomy' \
               f'&section.path=fnc&type=article&min_date={min_date}' \
               f'&max_date={max_date}&start={start}&callback=angular.callbacks._0&cb=112'

    def make_date_strings(self):
        return self.past_date.strftime('%Y-%m-%d'), self.upto_date.strftime('%Y-%m-%d')


def start_process(spider, **kwargs):
    process = CrawlerProcess()
    process.crawl(spider, **kwargs)
    process.start()


def get_recent_articles():
    settings_file_path = 'scraping.settings'  # The path seen from root, ie. from main.py
    os.environ.setdefault('SCRAPY_SETTINGS_MODULE', settings_file_path)
    process = CrawlerProcess(get_project_settings())
    process.crawl(NYT, interactive=False)
    process.crawl(CNN, interactive=False)
    process.crawl(FOX, interactive=False)
    process.start()


if __name__ == "__main__":
    choice = input("Which news company would you like to scrape?\n"
                   "1. NYTimes\n"
                   "2. CNN\n"
                   "3. Fox News\n"
                   "4. (in future) Debug Mode\n")
    if choice == '1':
        start_process(NYT, interactive=True)
    elif choice == '2':
        start_process(CNN, interactive=True)
    elif choice == '3':
        start_process(FOX, interactive=True)
    else:
        pass
