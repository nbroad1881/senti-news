import csv
import logging
import json
import pathlib
from abc import ABC, abstractmethod

import scrapy
import requests
from scrapy.crawler import CrawlerProcess

logging.basicConfig(level=logging.INFO)


# todo: have an interactive query
#     database for text documents

class ArticleSource(ABC):
    DEM_CANDIDATES = ['biden', 'warren', 'sanders', 'harris', 'buttigieg']

    @abstractmethod
    def ask_for_query(self):
        pass

    @abstractmethod
    def get_unique_ids(self):
        pass

    @abstractmethod
    def make_api_call(self):
        pass

    @abstractmethod
    def set_unique_ids(self):
        pass

    @abstractmethod
    def store_article(self):
        pass

    @abstractmethod
    def store_info(self):
        pass

    @abstractmethod
    def form_query(self):
        pass


class NYT(scrapy.Spider, ArticleSource):
    UNIQUE_IDS_PATH = pathlib.Path('')  # empty but implemented in functions to allow for each changes in future
    UNIQUE_IDS_FILE_NAME = "NYT_UNIQUE_IDS.csv"
    ARTICLE_TEXT_PATH = pathlib.Path('../saved_texts/NYT/texts')
    ARTICLE_INFO_PATH = pathlib.Path('../saved_texts/NYT/info')
    INFO_FILE_NAME = "NYT_INFO.csv"
    TESTING_QUERY = 'https://api.nytimes.com/svc/search/v2/articlesearch.json?begin_date=20191001&end_date=20191031' \
                    '&facet=true&facet_fields=document_type&fq=article&q=biden&sort=newest&api-key' \
                    '=nSc6ri8B5W6boFhjJ6SuYpQmLN8zQuV7 '

    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 2
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

    # todo: not violate LSP
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
        if not self.UNIQUE_IDS_PATH.is_dir():
            self.UNIQUE_IDS_PATH.mkdir()
        elif (self.UNIQUE_IDS_PATH / self.UNIQUE_IDS_PATH).is_file():
            with open(self.UNIQUE_IDS_PATH / self.UNIQUE_IDS_FILE_NAME, 'r') as file:
                reader = csv.reader(file)
                return set(next(reader))
        logging.debug('No unique id file, return empty set')
        return set()

    def set_unique_ids(self):
        with open(self.UNIQUE_IDS_PATH / self.UNIQUE_IDS_FILE_NAME, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(list(self.unique_ids))

    def store_article(self, text, id_):
        if not self.ARTICLE_TEXT_PATH.is_dir():
            logging.debug(f'Making directory {self.ARTICLE_TEXT_PATH}')
            self.ARTICLE_TEXT_PATH.mkdir(parents=True)
        with open(self.ARTICLE_TEXT_PATH / f'{id_}.txt', 'w') as file:
            file.write(text)

    def store_info(self, info):
        if not self.ARTICLE_INFO_PATH.is_dir():
            logging.debug(f'Making directory {self.ARTICLE_INFO_PATH}')
            self.ARTICLE_INFO_PATH.mkdir(parents=True)
        with open(self.ARTICLE_INFO_PATH / self.INFO_FILE_NAME, 'a') as file:
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


class CNN(scrapy.Spider, ArticleSource):
    UNIQUE_IDS_PATH = pathlib.Path('')  # empty but implemented in functions to allow for each changes in future
    UNIQUE_IDS_FILE_NAME = "CNN_UNIQUE_IDS.csv"
    ARTICLE_TEXT_PATH = pathlib.Path('../saved_texts/CNN/texts')
    ARTICLE_INFO_PATH = pathlib.Path('../saved_texts/CNN/text_info')
    INFO_FILE_NAME = "CNN_INFO.csv"
    RESULTS_SIZE = 100
    TESTING_QUERY = "https://search.api.cnn.io/content?size=20&q=biden&type=article&sort=relevance&page=0&from=0"

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

        for p in range(1, num_results // self.RESULTS_SIZE):
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
        if not self.UNIQUE_IDS_PATH.is_dir():
            self.UNIQUE_IDS_PATH.mkdir()
        elif (self.UNIQUE_IDS_PATH / self.UNIQUE_IDS_PATH).is_file():
            with open(self.UNIQUE_IDS_PATH / self.UNIQUE_IDS_FILE_NAME, 'r') as file:
                reader = csv.reader(file)
                return set(next(reader))
        logging.debug('No unique id file, return empty set')
        return set()

    def set_unique_ids(self):
        with open(self.UNIQUE_IDS_PATH / self.UNIQUE_IDS_FILE_NAME, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(list(self.unique_ids))

    def store_article(self, text, id_):
        if not self.ARTICLE_TEXT_PATH.is_dir():
            logging.debug(f'Making directory {self.ARTICLE_TEXT_PATH}')
            self.ARTICLE_TEXT_PATH.mkdir(parents=True)
        with open(self.ARTICLE_TEXT_PATH / f'{id_}.txt', 'w') as file:
            file.write(text)

    def store_info(self, info):
        if not self.ARTICLE_INFO_PATH.is_dir():
            logging.debug(f'Making directory {self.ARTICLE_INFO_PATH}')
            self.ARTICLE_INFO_PATH.mkdir(parents=True)
        with open(self.ARTICLE_INFO_PATH / self.INFO_FILE_NAME, 'a') as file:
            logging.debug(f'Wrote CNN article ({info["id"]}) to file')
            writer = csv.writer(file)
            writer.writerow([info['url'],
                             info['date'],
                             info['id'],
                             info['title']])

    def form_query(self, query, page):
        return f'https://search.api.cnn.io/content?size={self.CNN_RESULTS_SIZE}' \
               f'&q={query}&type=article&sort=relevance&page={page}&from={str(page * self.CNN_RESULTS_SIZE)}'


class FOX(scrapy.Spider, ArticleSource):
    UNIQUE_IDS_PATH = pathlib.Path('')  # empty but implemented in functions to allow for each changes in future
    UNIQUE_IDS_FILE_NAME = 'FOX_UNIQUE_IDS.csv'
    ARTICLE_TEXT_PATH = pathlib.Path('../saved_texts/FOX/texts')
    ARTICLE_INFO_PATH = pathlib.Path('../saved_texts/FOX/text_info')
    INFO_FILE_NAME = "FOX_INFO.csv"
    PAGE_SIZE = 10
    NUM_PAGES = 10
    TESTING_QUERY = 'https://api.foxnews.com/v1/content/search?q=biden&fields=date,description,title,url,image,type,' \
                    'taxonomy&section.path=fnc&type=article&min_date=2019-10-10&max_date=2019-10-10&start=0&callback' \
                    '=angular.callbacks._0&cb=112 '

    def __init__(self):
        self.unique_ids = self.get_unique_ids()

    @staticmethod
    def ask_for_query():
        query = input('What is the query? (e.g. biden, sanders, warren): ')
        begin_date = input('What is the oldest date? (YYYYMMDD): ')
        begin_date = '-'.join([begin_date[:4], begin_date[4:6], begin_date[6:8]])
        end_date = input('What is the newest date? (YYYYMMDD): ')
        end_date = '-'.join([end_date[:4], end_date[4:6], end_date[6:8]])
        return query, begin_date, end_date

    def start_requests(self):
        query, min_date, max_date = self.ask_for_query()

        all_urls, all_info = [], []
        for start in range(0,
                           self.PAGE_SIZE * self.NUM_PAGES,
                           self.PAGE_SIZE):
            api_url = self.form_query(query, min_date=min_date, max_date=max_date, start=start)
            urls, info = self.make_api_call(api_url)

            all_urls.extend(urls)
            all_info.extend(info)

        for url, info in zip(all_urls, all_info):
            self.store_info(info)
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs=dict(id_=info['id']))

    def parse(self, response, id_):
        article_text = ' '.join(response.xpath(
            '//div[(@class="article-body")]//p/text()|'
            '//div[@class="article-body"]//p/a/text()'
        ).getall())
        self.store_article(article_text, id_)
        self.set_unique_ids()

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
        logging.debug(f'get request: {api_url}')
        if response.status_code == 200:
            logging.debug('Request accepted (200)')
            urls, infos = [], []

            text = json.loads(response.text[21:-1])['response']
            logging.debug('Request accepted (200)')
            for d in text['docs']:
                info = {
                    'date': d['date'],
                    'title': d['title'],
                    'url': d['url'][0],
                    'type_': d['type'],
                    'id': d['date']
                }
                if info['id'] in self.unique_ids:
                    continue

                self.unique_ids.add(info['id'])

                urls.append(info['url'])
                infos.append(info)
            logging.debug(f'returning urls_ids:{urls}\n{infos}')
            return urls, infos
        else:
            logging.debug(f'Request denied ({response.status_code})')
            return None

    def get_unique_ids(self):
        """
        Ids should be comma delimited with no line breaks
        :return: set of ids or empty set if file not found
        """
        if not self.UNIQUE_IDS_PATH.is_dir():
            self.UNIQUE_IDS_PATH.mkdir()
        elif (self.UNIQUE_IDS_PATH / self.UNIQUE_IDS_PATH).is_file():
            with open(self.UNIQUE_IDS_PATH / self.UNIQUE_IDS_FILE_NAME, 'r') as file:
                reader = csv.reader(file)
                return set(next(reader))
        logging.debug('No unique id file, return empty set')
        return set()

    def set_unique_ids(self):
        with open(self.UNIQUE_IDS_PATH / self.UNIQUE_IDS_FILE_NAME, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(list(self.unique_ids))

    def store_article(self, text, id_):
        if not self.ARTICLE_TEXT_PATH.is_dir():
            logging.debug(f'Making directory {self.ARTICLE_TEXT_PATH}')
            self.ARTICLE_TEXT_PATH.mkdir(parents=True)
        with open(self.ARTICLE_TEXT_PATH / f'{id_}.txt', 'w') as file:
            file.write(text)

    def store_info(self, info):
        if not self.ARTICLE_INFO_PATH.is_dir():
            logging.debug(f'Making directory {self.ARTICLE_INFO_PATH}')
            self.ARTICLE_INFO_PATH.mkdir(parents=True)
        with open(self.ARTICLE_INFO_PATH / self.INFO_FILE_NAME, 'a') as file:
            logging.debug(f'Wrote Fox info ({info["id"]}) to file')
            writer = csv.writer(file)
            writer.writerow([info['url'],
                             info['date'],
                             info['title']])

    @staticmethod
    def form_query(query, min_date, max_date, start):
        return ''.join([f'https://api.foxnews.com/v1/content/search?q={query}',
                        f'&fields=date,description,title,url,image,type,taxonomy',
                        f'&section.path=fnc&type=article&min_date={min_date}',
                        f'&max_date={max_date}&start={start}&callback=angular.callbacks._0&cb=',
                        '112'])


if __name__ == "__main__":

    choice = input("Which news company would you like to scrape?\n"
                   "1. CNN\n"
                   "2. Fox News\n"
                   "3. NYTimes\n"
                   "4. (in future) Debug Mode\n")
    process = CrawlerProcess()
    if int(choice) == 1:
        process.crawl(CNN)
    elif int(choice) == 2:
        process.crawl(FOX)
    elif int(choice) == 3:
        process.crawl(NYT)
    else:
        pass
    try:
        process.start()
    finally:
        pass
