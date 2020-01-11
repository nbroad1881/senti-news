import logging
import json
import os
from datetime import datetime, timedelta
from dateutil.parser import isoparse
from abc import ABC, abstractmethod

from dotenv import load_dotenv
import scrapy
import requests
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
from sentinews.database.database import add_row_to_db, get_session

load_dotenv()
logging.basicConfig(level=logging.INFO)
# todo: use urllib for posts
ENDPOINT = os.environ.get('ENDPOINT')
PORT = os.environ.get('PORT')
USER = os.environ.get('USERNAME')
PW = os.environ.get('PASSWORD')
DBNAME = os.environ.get('DBNAME')
DATABASE_URL = f"postgres://{USER}:{PW}@{ENDPOINT}:{PORT}/{DBNAME}"


# 'postgresql://nicholasbroad:@localhost:5432/nicholasbroad'


# todo: have an interactive QUERY
#     database for text documents

class ArticleSource(ABC):
    CANDIDATE_DICT = {
        '1': 'Donald Trump',
        '2': 'Joe Biden',
        '3': 'Elizabeth Warren',
        '4': 'Bernie Sanders',
        '5': 'Kamala Harris',
        '6': 'Pete Buttigieg'
    }

    def __init__(self, interactive):
        self.session = get_session(DATABASE_URL)
        self.articles_logged = 0
        self.interactive = interactive or False

    @abstractmethod
    def ask_for_query(self, *args, **kwargs):
        pass

    @abstractmethod
    def form_query(self, *args, **kwargs):
        pass

    @abstractmethod
    def make_api_call(self, *args, **kwargs):
        pass

    def store_info(self, url, date, title, news_co, text):
        logged = add_row_to_db(self.session, url, date, title, news_co, text)
        if logged:
            self.articles_logged += 1
            logging.info(f"Stored #{self.articles_logged} in db: {url}, {date}, {title}")

    def improper_title(self, title):
        names = ['trump', 'biden', 'warren', 'sanders', 'harris', 'buttigieg']
        return sum([1 if name in title.lower() else 0 for name in names]) != 1


class NYT(scrapy.Spider, ArticleSource):
    NEWS_CO = 'New York Times'

    # todo: handle rate
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 2
    }

    name = 'NYT'

    def __init__(self, **kwargs):
        ArticleSource.__init__(self, **kwargs)

    def ask_for_query(self):
        if self.interactive:
            query = input("Which candidate?\n"
                          "1. Donald Trump\n"
                          "2. Joe Biden\n"
                          "3. Elizabeth Warren\n"
                          "4. Bernie Sanders\n"
                          "5. Kamala Harris\n"
                          "6. Pete Buttigieg\n")
            if query not in self.CANDIDATE_DICT:
                return self.ask_for_query()
            candidate = self.CANDIDATE_DICT[query]
            begin_date = input('What is the oldest date? (YYYYMMDD): ')
            end_date = input('What is the newest date? (YYYYMMDD or nothing for today\'s date): ')
            end_date = end_date if len(end_date > 1) else datetime.utcnow().isoformat()[:10]
            return candidate, begin_date, end_date
        today = datetime.utcnow().isoformat()[:10]
        one_day = timedelta(days=1)
        yesterday = (datetime.utcnow() - one_day).isoformat()[:10]
        return list(self.CANDIDATE_DICT.values()), yesterday, today

    def start_requests(self):
        query, begin_date, end_date = self.ask_for_query()
        all_urls = []
        all_info = []
        if self.interactive:
            for p in range(5):
                api_url = self.form_query(query=query, page=p, begin_date=begin_date, end_date=end_date)
                urls, info = self.make_api_call(api_url)

                if urls is not None:
                    all_urls.extend(urls)
                    all_info.extend(info)
        else:
            for q in query:
                api_url = self.form_query(query=q, page=0, begin_date=begin_date, end_date=end_date)
                urls, info = self.make_api_call(api_url)

                if urls is not None:
                    all_urls.extend(urls)
                    all_info.extend(info)

        for url, info in zip(all_urls, all_info):
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs=dict(info=info))

    # todo: not violate LSP
    def parse(self, response, info):
        # todo: check for bad responses

        soup = BeautifulSoup(response.text, 'html.parser')
        texts = []
        for paragraphs in soup.select('section.meteredContent p'):
            texts.append(paragraphs.text)
        body = ' '.join(texts)

        self.store_info(url=info['url'], date=info['date'], title=info['title'], news_co=self.NEWS_CO, text=body)

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
                    'date': date,
                    'title': title,
                })

            return start_urls, info
        logging.debug(f'Response status code:{response.status_code}')
        return None, None

    @staticmethod
    def form_query(query, page, begin_date='20190301', end_date='20191001', sort='newest'):
        return ''.join([f'https://api.nytimes.com/svc/search/v2/articlesearch.json?q={query}',
                        f'&facet=true&page={str(page)}&begin_date={begin_date}&end_date={end_date}',
                        f'&facet_fields=document_type&fq=article',
                        f'&sort={sort}&api-key=nSc6ri8B5W6boFhjJ6SuYpQmLN8zQuV7'])

    def start_crawl(self, **kwargs):
        process = CrawlerProcess()
        process.crawl(self, **kwargs)


class CNN(scrapy.Spider, ArticleSource):
    RESULTS_SIZE = 100
    NUM_PAGES = 5
    NEWS_CO = 'CNN'
    name = 'CNN'

    def __init__(self, **kwargs):
        ArticleSource.__init__(self, **kwargs)

    def ask_for_query(self):
        if self.interactive:
            query = input("Which candidate?\n"
                          "1. Donald Trump\n"
                          "2. Joe Biden\n"
                          "3. Elizabeth Warren\n"
                          "4. Bernie Sanders\n"
                          "5. Kamala Harris\n"
                          "6. Pete Buttigieg\n")
            if query not in self.CANDIDATE_DICT:
                return self.ask_for_query()
            candidate = self.CANDIDATE_DICT[query].replace(' ', '%20')
            begin_date = input('What is the oldest date? (YYYYMMDD): ') + "T00:00:00Z"
            end_date = input('What is the newest date? (YYYYMMDD or nothing for today\'s date): ')
            if len(end_date) > 1:
                end_date = end_date + "T23:59:59Z"
            else:
                end_date = datetime.utcnow().isoformat(timespec='seconds') + 'Z'
            return candidate, begin_date, end_date
        else:
            today = datetime.utcnow().isoformat() + 'Z'
            one_day = timedelta(days=1)
            yesterday = (datetime.utcnow() - one_day).isoformat() + 'Z'
            return list(self.CANDIDATE_DICT.values()), yesterday, today

    def start_requests(self):
        query, begin_date, end_date = self.ask_for_query()
        if self.interactive:
            for p in range(self.NUM_PAGES):
                url = self.form_query(query, page=p)
                yield scrapy.Request(url=url, callback=self.parse,
                                     cb_kwargs=dict(begin_date=begin_date, end_date=end_date))
        else:
            for q in query:
                for p in range(self.NUM_PAGES):
                    url = self.form_query(q, page=p)
                    yield scrapy.Request(url=url, callback=self.parse,
                                         cb_kwargs=dict(begin_date=begin_date, end_date=end_date))

    def parse(self, response, begin_date, end_date):

        articles = json.loads(response.text)['result']
        for a in articles:
            if a['type'] != 'article':
                continue

            url = a['url']
            date = a['firstPublishDate']
            title = a['headline']
            body = a['body']

            if self.improper_title(title):
                continue

            article_datetime = isoparse(date)
            begin_datetime = isoparse(begin_date)
            end_datetime = isoparse(end_date)

            if article_datetime < begin_datetime or article_datetime > end_datetime:
                continue

            self.store_info(url, date, title, self.NEWS_CO, body)

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

    def form_query(self, query, page):
        return f'https://search.api.cnn.io/content?size={self.RESULTS_SIZE}' \
               f'&q={query}&type=article&sort=newest&page={page}&from={str(page * self.RESULTS_SIZE)}'


class FOX(scrapy.Spider, ArticleSource):
    PAGE_SIZE = 10
    NUM_PAGES = 10

    NEWS_CO = 'FOX News'
    name = 'Fox'

    def __init__(self, **kwargs):
        ArticleSource.__init__(self, **kwargs)

    def ask_for_query(self):
        query = input("Which candidate?\n"
                      "1. Donald Trump\n"
                      "2. Joe Biden\n"
                      "3. Elizabeth Warren\n"
                      "4. Bernie Sanders\n"
                      "5. Kamala Harris\n"
                      "6. Pete Buttigieg\n")
        if query not in self.CANDIDATE_DICT:
            return self.ask_for_query()
        candidate = self.CANDIDATE_DICT[query].replace(' ', '+')
        begin_date = input('What is the oldest date? (YYYYMMDD): ')
        begin_date = '-'.join([begin_date[:4], begin_date[4:6], begin_date[6:8]])
        end_date = input('What is the newest date? (YYYYMMDD or nothing for today): ')
        if len(end_date) > 1:
            end_date = '-'.join([end_date[:4], end_date[4:6], end_date[6:8]])
        else:
            end_date = datetime.utcnow().isoformat()[:10]
        return [candidate], begin_date, end_date

    def start_requests(self):
        if self.interactive:
            queries, min_date, max_date = self.ask_for_query()
        else:
            today = datetime.utcnow().isoformat()[:10]
            one_day = timedelta(days=1)
            yesterday = (datetime.utcnow() - one_day).isoformat()[:10]
            queries, min_date, max_date = list(self.CANDIDATE_DICT.values()), yesterday, today

        all_urls, all_info = [], []
        for query in queries:
            for start in range(0,
                               self.PAGE_SIZE * self.NUM_PAGES,
                               self.PAGE_SIZE):
                api_url = self.form_query(query, min_date=min_date, max_date=max_date, start=start)
                urls, info = self.make_api_call(api_url)

                all_urls.extend(urls)
                all_info.extend(info)

        for url, info in zip(all_urls, all_info):
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs=dict(info=info))

    def parse(self, response, info):

        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.select('div.article-body p')
        texts = []
        for p in paragraphs:
            if not p.find('em') and not p.find('strong') and not p.find('span'):
                texts.append(p.text)

        body = ' '.join(texts)

        self.store_info(url=info['url'], date=info['date'], title=info['title'], news_co=self.NEWS_CO, text=body)

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
                    'date': d['date'],
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

    @staticmethod
    def form_query(query, min_date, max_date, start):
        return ''.join([f'https://api.foxnews.com/v1/content/search?q={query}',
                        f'&fields=date,description,title,url,image,type,taxonomy',
                        f'&section.path=fnc&type=article&min_date={min_date}',
                        f'&max_date={max_date}&start={start}&callback=angular.callbacks._0&cb=',
                        '112'])


def start_process(spider, **kwargs):
    process = CrawlerProcess()
    process.crawl(spider, **kwargs)
    process.start()


def get_recent_articles():
    process = CrawlerProcess()
    process.crawl(NYT, interactive=False)
    process.crawl(CNN, interactive=False)
    process.crawl(FOX, interactive=False)
    process.start()


if __name__ == "__main__":

    choice = input("Which news company would you like to scrape?\n"
                   "1. CNN\n"
                   "2. Fox News\n"
                   "3. NYTimes\n"
                   "4. (in future) Debug Mode\n")
    session = get_session(os.environ.get('DATABASE_URL'))
    if int(choice) == 1:
        start_process(CNN, interactive=True)
    elif int(choice) == 2:
        start_process(FOX, interactive=True)
    elif int(choice) == 3:
        start_process(NYT, interactive=True)
    else:
        pass
    session.close()
