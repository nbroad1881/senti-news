import json
import time
import os

import requests
from dateutil.parser import isoparse
from datetime import datetime, timezone, timedelta
import logging
from dotenv import load_dotenv
from newsapi import NewsApiClient

from sentinews.models import VaderAnalyzer, TextBlobAnalyzer, LSTMAnalyzer, analyze_title

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

CANDIDATES = ['Donald Trump', 'Joe Biden', 'Bernie Sanders', 'Elizabeth Warren', 'Kamala Harris', 'Pete Buttigieg',
              'Michael Bloomberg', 'Andrew Yang', 'Tom Steyer']

LAST_NAMES = ['trump', 'biden', 'sanders', 'warren', 'harris', 'buttigieg', 'yang', 'bloomberg', 'steyer']

print("Loading sentiment analyzers...")
analyzers = [
    VaderAnalyzer(),
    TextBlobAnalyzer(),
    LSTMAnalyzer(),
]
print("Loaded!")

DB_API_URL = 'http://0.0.0.0:5000/article/'


class BaseNews:

    def __init__(self, start_date, end_date, num_steps):
        self.start_date = start_date
        self.end_date = end_date
        self.increment = (end_date - start_date) / num_steps
        self.num_steps = num_steps
        self.articles_logged = 0

    @staticmethod
    def improper_title(title):
        """
        Checks if the 'title'
        :param title:
        :type title:
        :return:
        :rtype:
        """
        return sum([1 if name in title.lower() else 0 for name in LAST_NAMES]) != 1

    def post_article_to_db(self, article_info, scores):
        payload = {**article_info, **scores}
        header = {
            'password': os.environ['AUTH_PASSWORD'],
        }
        response = requests.post(DB_API_URL, params=payload, headers=header)
        logging.info(f"Made POST request to database API, response code: {response.status_code}")
        if response.status_code == 201:
            self.articles_logged += 1

    def get_articles_logged(self):
        return self.articles_logged


class CNN(BaseNews):
    RESULTS_SIZE = 100
    PAGE_LIMIT = 15
    NEWS_CO = 'CNN'

    def start(self):
        for q in CANDIDATES:
            for p in range(self.PAGE_LIMIT):
                url = self.create_api_query(q, page=p)
                response = requests.get(url)
                if response.status_code == 200:
                    for article in json.loads(response.text)['result']:
                        self.extract_information(article)

    def create_api_query(self, query, page):
        """
        Returns string that will be called by the API
        :param query: candidate
        :type query: str
        :param page: page to start on
        :type page: str or int
        :return: query string
        :rtype: str
        """
        return f'https://search.api.cnn.io/content?size={self.RESULTS_SIZE}' \
               f'&q={query}&type=article&sort=newest&page={page}' \
               f'&from={str(page * self.RESULTS_SIZE)}'

    def extract_information(self, article):

        # Pull information from article
        article_info = {
            'url': article['url'],
            'datetime': isoparse(article['firstPublishDate']),
            'title': article['headline'],
            'text': article['body'],
            'news_co': self.NEWS_CO,
        }

        # Check if title has one and only one candidate name
        if self.improper_title(article_info['title']):
            return None

        scores = analyze_title(analyzers, article_info['title'])
        self.post_article_to_db(article_info=article_info, scores=scores)


class NYT(BaseNews):
    """
        Class designed to pull information from The New York Times' API.
        https://developer.nytimes.com/docs/articlesearch-product/1/overview

        """
    NEWS_CO = 'The New York Times'  # news company name
    name = 'nyt'  # spider name
    PAGE_LIMIT = 15

    def start(self):

        for n in range(self.num_steps):
            self.end_date = self.start_date + self.increment

            for q in CANDIDATES:
                for p in range(self.PAGE_LIMIT):
                    url = self.create_api_query(q, page=p)
                    response = requests.get(url)

                    # NYT API only allows 10 requests per minute
                    time.sleep(10)
                    code = response.status_code
                    logging.info(f"Response code: {code}")
                    if code == 200:
                        for article in json.loads(response.text)['response']['docs']:
                            self.extract_information(article)
                    if code == 429:
                        logging.info("Too many requests")

            self.start_date += self.increment

    def create_api_query(self, query, page, sort='newest'):
        """
        Since the url is a very long string, most of it the exact same for each request,
         this method makes it easier to create the api url.
        :param query: candidate to search for
        :type query: str
        :param page: which page number to start on
        :type page: str or int
        :param sort: how to sort results: newest or relevance
        :type sort: str
        :return: the whole api url to be called
        :rtype: str
        """
        # Turn datetime objects to correct string representation
        begin_date, end_date = self.make_date_strings()

        # todo: incorporate fq=headline:("name")
        #   also fq=section_name:("Opinion")
        #  document_type:("article")

        return f'https://api.nytimes.com/svc/search/v2/articlesearch.json?q={query}' \
               f'&facet=true&page={page}&begin_date={begin_date}&end_date={end_date}' \
               f'&facet_fields=document_type&fq=article' \
               f'&sort={sort}&api-key={os.environ["NYT_API_KEY"]}'

    def make_date_strings(self):
        """
        Format custom date for NYT from instance variable start and end dates
        e.g. 20200101
        :return: date string
        :rtype: str
        """
        return self.start_date.strftime('%Y%m%d'), self.end_date.strftime('%Y%m%d')

    def extract_information(self, article):

        title = article['headline']['main']

        # Check if title has one and only one candidate name
        if self.improper_title(title):
            logging.info(f"Bad title: {title}")
            return None

        article_info = {
            'url': article['web_url'],
            'datetime': isoparse(article['pub_date']),
            'title': title,
            'news_co': self.NEWS_CO,
            'text': '',
        }

        scores = analyze_title(analyzers, title)
        self.post_article_to_db(article_info=article_info, scores=scores)


class FOX(BaseNews):
    """"
    Class designed to pull information from Fox News' API.
    Queries the API with one or all candidates, extracts the
    url, title, datetime, and text and sends it to NewsItemPipeline.
    """
    # Number of results on a page
    PAGE_SIZE = 10
    # Number of pages to go through
    PAGE_LIMIT = 20

    NEWS_CO = 'Fox News'

    def start(self):

        for n in range(self.num_steps):
            self.end_date = self.start_date + self.increment

            for query in CANDIDATES:
                for start in range(0,
                                   self.PAGE_SIZE * self.PAGE_LIMIT,
                                   self.PAGE_SIZE):
                    url = self.create_api_query(query, start=start)
                    response = requests.get(url)
                    code = response.status_code
                    logging.info(f"Response code: {code}")
                    if code == 200:
                        for article in json.loads(response.text[21:-1])['response']['docs']:
                            self.extract_information(article)
                    if code == 429:
                        logging.info("Too many requests")

            self.start_date += self.increment

    def create_api_query(self, query, start):
        """
        Create string to be sent as a query to the API.
        :param query: candidate
        :type query: str
        :param start: the number of the article to start on
        :type start: str or int
        :return: query string
        :rtype: str
        """
        min_date, max_date = self.make_date_strings()
        return f'https://api.foxnews.com/v1/content/search?q={query}' \
               f'&fields=date,description,title,url,image,type,taxonomy' \
               f'&sort=latest&section.path=fnc/politics,fnc/opinion,fnc/us&type=article' \
               f'&min_date={min_date}&max_date={max_date}&start={start}&' \
               f'callback=angular.callbacks._0&cb=112'

    def make_date_strings(self):
        """
        Format custom date for Fox from instance variable start and end dates
        e.g. 2020-01-01
        :return: date string
        :rtype: str
        """
        return self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d')

    def extract_information(self, article):
        title = article['title']
        logging.info(f"Checking:  {title}")
        if self.improper_title(title):
            return

        article_info = {
            'datetime': article['date'],
            'title': title,
            'url': article['url'][0],
            'news_co': self.NEWS_CO,
            'text': '',
        }

        scores = analyze_title(analyzers, title)
        self.post_article_to_db(article_info=article_info, scores=scores)


class NEWSAPI(BaseNews):
    news_client = NewsApiClient(api_key=os.environ['NEWS_API_KEY'])

    PAGE_SIZE = 100
    QUERY = '(' + ') OR ('.join(CANDIDATES) + ')'
    SORT_BY = 'relevancy'
    LANG = 'en'
    PAGE_NUM = 1  # with free version, can't go past page 1
    SOURCES = ','.join(['cnn', 'fox-news', 'the-new-york-times'])

    def start(self):

        for i in range(self.num_steps):
            self.end_date = self.start_date + self.increment

            results = self.news_client.get_everything(page=self.PAGE_NUM,
                                                      from_param=self.start_date,
                                                      page_size=self.PAGE_SIZE,
                                                      qintitle=self.QUERY,
                                                      language=self.LANG,
                                                      sources=self.SOURCES,
                                                      sort_by=self.SORT_BY)

            if results['status'] == 'ok':
                for article in results['articles']:
                    self.extract_information(article)

            self.start_date += self.increment

    def extract_information(self, article):
        title = article['title']
        logging.info(f"Checking:  {title}")
        if self.improper_title(title):
            return

        article_info = {
            'url': article['url'],
            'datetime': isoparse(article['publishedAt']),
            'title': article.get('title', ''),
            'news_co': article.get('source').get('name', '') if article.get('source') else '',
            'text': article.get('content', ''),
        }

        scores = analyze_title(analyzers, title)
        self.post_article_to_db(article_info=article_info, scores=scores)


if __name__ == '__main__':
    num_divides = 100
    today = datetime.now(tz=timezone.utc)
    start_date = today - timedelta(days=7)

    choice = input("Which API would you like to use?\n"
                   "1. NYTimes\n"
                   "2. CNN\n"
                   "3. Fox News\n"
                   "4. NewsAPIs\n")
    if choice == '1':
        api_choice = NYT(start_date=start_date, end_date=today, num_steps=num_divides)
    elif choice == '2':
        api_choice = CNN(start_date=start_date, end_date=today, num_steps=num_divides)
    elif choice == '3':
        api_choice = FOX(start_date=start_date, end_date=today, num_steps=num_divides)
    elif choice == '4':
        api_choice = NEWSAPI(start_date=start_date, end_date=today, num_steps=num_divides)
    else:
        import sys

        sys.exit(0)

    api_choice.start()