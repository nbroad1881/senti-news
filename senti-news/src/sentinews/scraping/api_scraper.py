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

from sentinews.scraping.scraping.items import NewsItem
from sentinews.models import VaderAnalyzer, TextBlobAnalyzer, LSTMAnalyzer, analyze_title

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
DEFAULT_END_DATE = datetime.now(timezone.utc)
DEFAULT_START_DATE = DEFAULT_END_DATE - timedelta(days=DEFAULT_NUM_DAYS_BACK)
START_DATE = 1
END_DATE = 2

TRUMP_OPTION = '1'
BIDEN_OPTION = '2'
WARREN_OPTION = '3'
SANDERS_OPTION = '4'
HARRIS_OPTION = '5'
BUTTIGIEG_OPTION = '6'
ALL_CANDIDATES = '7'

CANDIDATES = ['Donald Trump', 'Joe Biden', 'Bernie Sanders', 'Elizabeth Warren', 'Kamala Harris', 'Pete Buttigieg']


analyzers = [
    VaderAnalyzer(),
    TextBlobAnalyzer(),
    LSTMAnalyzer(),
]


# todo: add newsapi into this file
# todo: have an interactive QUERY database for text documents
class ArticleSource(ABC):
    """
    Base abstract class that to be subclassed with specialized spiders.
    Includes implementation for methods used by all subclasses.
    """

    # For selecting the candidate based on the number input
    CANDIDATE_DICT = {
        TRUMP_OPTION: 'Donald Trump',
        BIDEN_OPTION: 'Joe Biden',
        WARREN_OPTION: 'Elizabeth Warren',
        SANDERS_OPTION: 'Bernie Sanders',
        HARRIS_OPTION: 'Kamala Harris',
        BUTTIGIEG_OPTION: 'Pete Buttigieg',
        ALL_CANDIDATES: ''
    }

    def __init__(self, interactive, start_date=None, end_date=None):
        """
        When creating an ArticleSource object, there is a choice between making the process
        interactive. Interactive means that the user will be prompted to input options to
        choose things like candidate, date, news source.
        :param interactive: set to True or False depending on if interactivity is desired
        :type interactive: bool
        :param start_date: When limiting results by date, this is the date that occurred the longer time ago.
        Format should be YYYYMMDD
        :type start_date: str
        :param end_date: This is the date that occurred more recently to today. Format YYYMMDD
        :type end_date: str
        
        Time periods go from (PAST) start_date -> end_date (PRESENT)
        """

        # Keep track of how many articles get sent to database
        self.articles_logged = 0
        self.interactive = interactive or False

        # Check that the start_date is valid, otherwise use default.
        if start_date and self.is_valid_date(start_date):
            self.start_date = isoparse(start_date)
        else:
            self.start_date = DEFAULT_START_DATE

        # Check if end_date is valid and after start_date, otherwise use default
        if end_date and self.is_valid_date(end_date, after=self.start_date):
            self.end_date = isoparse(end_date)
        else:
            self.end_date = DEFAULT_END_DATE

    def ask_for_query(self, *args, **kwargs):
        """
        Combines asking which candidate, a start date and an end date.
        Start and end date get stored as instance variables.
        Will keep asking until user enters valid input.
        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """

        # options starts as the number selected by user, but then when a valid section is selected,
        # it becomes the name of the candidate.
        option = self.ask_for_candidate()
        while option not in self.CANDIDATE_DICT:
            print('Not valid selection. Try again.')
            option = self.ask_for_candidate()

        # Asking for start date
        input_start_date = self.ask_for_date(START_DATE)
        while not self.is_valid_date(input_start_date):
            print('Not valid date. Try again.')
            input_start_date = self.ask_for_date(START_DATE)
        self.start_date = isoparse(input_start_date)

        # Asking for end date
        input_end_date = self.ask_for_date(END_DATE)
        while not self.is_valid_date(input_end_date, after=self.start_date):
            print('Not valid date. Try again.')
            input_end_date = self.ask_for_date(END_DATE)
        self.end_date = isoparse(input_end_date)

        # If they selected all candidates
        if option == ALL_CANDIDATES:
            # quote uses urllib to change spaces and other invalid characters to %xx
            return [quote(c) for c in CANDIDATES]

        # Return a list of a single candidate
        return [quote(self.CANDIDATE_DICT[option])]

    @staticmethod
    def ask_for_candidate():
        """
        Asks user to input a number to select one or all candidates.
        :return: user input
        :rtype: str
        """
        return input("Which candidate?\n"
                     f"{TRUMP_OPTION}. Donald Trump\n"
                     f"{BIDEN_OPTION}. Joe Biden\n"
                     f"{WARREN_OPTION}. Elizabeth Warren\n"
                     f"{SANDERS_OPTION}. Bernie Sanders\n"
                     f"{HARRIS_OPTION}. Kamala Harris\n"
                     f"{BUTTIGIEG_OPTION}. Pete Buttigieg\n"
                     f"{ALL_CANDIDATES}. All candidates\n")

    @staticmethod
    def ask_for_date(choice):
        """
        Asks user to enter a date. Can ask for start or end date.
        :param choice: START_DATE or END_DATE
        :type choice: use constants
        :return: user input
        :rtype: str
        """
        if choice == START_DATE:
            time_word = 'start'
            explanation_word = 'further from'
        elif choice == END_DATE:
            time_word = 'end'
            explanation_word = 'closer to'
        return input(f'What is the {time_word} date, the date that is {explanation_word} today)? '
                     f'\n (YYYYMMDD): ')

    @staticmethod
    def improper_title(title):
        """
        Checks if the 'title'
        :param title:
        :type title:
        :return:
        :rtype:
        """
        names = ['trump', 'biden', 'warren', 'sanders', 'harris', 'buttigieg']
        return sum([1 if name in title.lower() else 0 for name in names]) != 1

    @staticmethod
    def is_valid_date(date_string, after=None):
        """
        Checks if the date_string can be parsed by isoparse() and if the date is not in the future.
        Prints errors if date_string produces ValueError or TypeError
        :param after: if used, the date of the date_string must come after the date passed
        :type after: datetime.datetime
        :param date_string: Date to be checked. Needs to be in ISO format
        :type date_string: str
        :return: True if date_string is able to be parsed and date not in future.
        :rtype: bool
        """

        try:
            datetime_ = isoparse(date_string)
        except ValueError as error:
            print(error)
            return False
        except TypeError as error:
            print(error)
            return False

        # To make sure the passed date_string is after the passed date.
        if after:
            if datetime.utcnow() > datetime_ > after:
                return True
            logging.info(f"{date_string} is not in correct time range")
            return False

        return True

    @abstractmethod
    def create_api_query(self, *args, **kwargs):
        """
        This creates the query that will be used in make_api_call.
        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        pass

    @abstractmethod
    def make_api_call(self, *args, **kwargs):
        """
        Call the API using to get article information such as title or url.
        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        pass

    @abstractmethod
    def make_date_strings(self, *args, **kwargs):
        """
        Each API uses a different date string format.
        This formats the instance variables self.start_date and self.end_date
        to the appropriate string.
        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return: date string
        :rtype: str
        """
        pass

    @staticmethod
    def improper_title(title):
        names = ['trump', 'biden', 'warren', 'sanders', 'harris', 'buttigieg']
        return sum([1 if name in title.lower() else 0 for name in names]) != 1


class NYT(scrapy.Spider, ArticleSource):
    """
    Class designed to pull information from The New York Times' API.
    https://developer.nytimes.com/docs/articlesearch-product/1/overview

    # todo: handle rate
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 2
    }

    name = 'NYT'

    def __init__(self, **kwargs):
        ArticleSource.__init__(self, **kwargs)

    def start_requests(self):
        """
        Over-riding scrapy.Spider's method. Called after starting process.crawl()
        Makes multiple queries for each candidate, going through several pages of results.
        The url and article information is passed to the parse_request function
        :return: yield results to callback method
        :rtype: scrapy.Request
        """
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
        """
        Use BeautifulSoup to pull text content from response and put all information in a NewsItem.
        Yielding the NewsItem sends it to the NewsItemPipeline.
        The pipeline processes and adds it to the database
        :param response: response object from start_requests
        :type response: scrapy.http.response.html.HtmlResponse
        :param info: information such as url, datetime, title for start_requests
        :type info: dict
        :return: item with all article information to the pipeline
        :rtype: sentinews.scraping.scraping.items.NewsItem
        """

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
        """
        Calls the api_url passed to it and returns information if successful.
        Checks for good status code.
        The API contains url, title and date information
        :param api_url: The API's url to call
        :type api_url: str
        :return: list of starting urls for start_requests() and a list of dictionaries of url, title, and date
        :rtype: list, list or None, None if call failed
        """
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
        return f'https://api.nytimes.com/svc/search/v2/articlesearch.json?q={query}' \
               f'&facet=true&page={page}&begin_date={begin_date}&end_date={end_date}' \
               f'&facet_fields=document_type&fq=article' \
               f'&sort={sort}&api-key=nSc6ri8B5W6boFhjJ6SuYpQmLN8zQuV7'

    def start_crawl(self, **kwargs):
        process = CrawlerProcess()
        process.crawl(self, **kwargs)

    def make_date_strings(self):
        """
        Format custom date for NYT from instance variable start and end dates
        e.g. 20200101
        :return: date string
        :rtype: str
        """
        return self.start_date.strftime('%Y%m%d'), self.end_date.strftime('%Y%m%d')


class CNN(scrapy.Spider, ArticleSource):
    """
    Class designed to pull information from CNN's API.
    Scrapy not necessarily needed because CNN gives everything in the API request.
    Scrapy used for consistency and pipelining.
    """
    # todo: change back to 100
    RESULTS_SIZE = 1
    PAGE_LIMIT = 5
    NEWS_CO = 'CNN'
    name = 'CNN'

    def __init__(self, **kwargs):
        ArticleSource.__init__(self, **kwargs)

    def start_requests(self):
        """
        Ask user for query or use all candidates.
        Because CNN essentially gives all the information after the first api call,
        the scrapy.Request is not necessary. However, using parse_requests allows
        for the NewsItemPipeline to be used.
        :return: yield a page of results from the api call
        :rtype: scrapy.Request
        """
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

    def make_date_strings(self):
        """
        Format custom date for CNN from instance variable start and end dates
        e.g. 2020-01-01T13:25:46.947Z
        :return: date string
        :rtype: str
        """
        return self.start_date.isoformat() + 'Z', self.end_date.isoformat() + 'Z'


class FOX(scrapy.Spider, ArticleSource):
    """"
    Class designed to pull information from Fox News' API.
    Queries the API with one or all candidates, extracts the
    url, title, datetime, and text and sends it to NewsItemPipeline.
    """
    # Number of results on a page
    # todo: change back to 10
    PAGE_SIZE = 1
    # PAGE_SIZE = 10
    # Number of pages to go through
    PAGE_LIMIT = 1
    # PAGE_LIMIT = 10

    NEWS_CO = 'Fox News'
    name = 'Fox'

    def __init__(self, **kwargs):
        ArticleSource.__init__(self, **kwargs)

    def start_requests(self):
        """
        Call the API multiple times and pass results to parse_request
        :return:
        :rtype:
        """
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
        """
        Use BeautifulSoup to pull text from the article.
        Put information in NewsItem, yield to NewsItemPipeline
        :param response: response api call from start_requests
        :type response: scrapy.http.response.html.HtmlResponse
        :param info: url, title, date of the article
        :type info: dict
        :return: yield NewsItem to NewsItemPipeline
        :rtype: sentinews.scraping.scraping.items.NewsItem
        """
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
        Calls Fox News  API. This call will return a json response
        that will be parsed to extract url, datetime, and title information.
        If the call fails, returns None, None
        :param api_url: query from create_api_query()
        :return: lists of urls and info dicts or None, None
        :rtype: list, list of dict or None, None
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

        # API call failed
        logging.debug(f"Request failed. {response.status_code}")
        return None, None

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
