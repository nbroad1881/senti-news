import logging
import json
from datetime import datetime, timedelta, timezone
from dateutil.parser import isoparse
from abc import ABC, abstractmethod
import os
from urllib.parse import quote
from newsapi import NewsApiClient

from dotenv import load_dotenv
import scrapy
import requests
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from sentinews.scraping.scraping.items import NewsItem
from sentinews.models import VaderAnalyzer, TextBlobAnalyzer, LSTMAnalyzer, analyze_title

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

"""
news_apis.py contains 1 abstract ArticleSource and 3 subclasses: NYT, CNN, FOX
Each will use scrapy to search the APIs of NYT, CNN, and FOX for news articles.
The query will contain presidential candidate names.
Parse turns each result into a NewsItem.
Every NewsItem will be sent through the item pipeline (NewsItemPipeline).
NewsItemPipeline will then send the result to the database
"""

DEFAULT_NUM_DAYS_BACK = 20
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

    API_URL = 'http://0.0.0.0:6000/article/'

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
            datetime_ = isoparse(date_string).replace(tzinfo=timezone.utc)
        except ValueError as error:
            print(error)
            return False
        except TypeError as error:
            print(error)
            return False

        # If date is in the future
        if datetime_ > datetime.now(tz=timezone.utc):
            return False

        # To make sure the passed date_string is after the passed date.
        if after:
            if datetime.now(tz=timezone.utc) > datetime_ > after:
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

    def post_article_to_db(self, article_info, scores):

        payload = {**article_info, **scores}
        response = requests.post(self.API_URL, params=payload)
        logging.info(f"Made POST request to database API, response code: {response.status_code}")


class NYT(scrapy.Spider, ArticleSource):
    """
    Class designed to pull information from The New York Times' API.
    https://developer.nytimes.com/docs/articlesearch-product/1/overview

    """
    NEWS_CO = 'The New York Times'  # news company name
    name = 'nyt'  # spider name
    # todo: change back to 5
    PAGE_LIMIT = 1

    # API is rate-limited to 4,000 requests/day and 10 requests/minute
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'DOWNLOAD_DELAY': 6
    }

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

        # Loop through candidates
        for q in query:
            # Loop through pages up to limit
            for p in range(self.PAGE_LIMIT):
                api_url = self.create_api_query(query=q, page=p)
                urls, info = self.make_api_call(api_url)

                # May return None if failed
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

        # Filling NewsItem with important pieces of information
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
        logging.debug(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            start_urls = []
            info = []
            for doc in json.loads(response.text)['response']['docs']:
                url = doc['web_url']
                date = doc['pub_date']
                title = doc['headline']['main']

                # Check to make sure the title only has one and only one name in it.
                if self.improper_title(title):
                    continue

                start_urls.append(url)
                info.append({
                    'url': url,
                    'datetime': date,
                    'title': title,
                })

            return start_urls, info
        # If status code is not 200, return None, None
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
    name = 'cnn'  # spider name

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
            for p in range(self.PAGE_LIMIT):
                url = self.create_api_query(q, page=p)
                yield scrapy.Request(url=url, callback=self.parse_request)

    def parse_request(self, response):

        # Response.text is a json string
        articles = json.loads(response.text)['result']
        for article in articles:
            # Skip over any result that is not categorized as an article
            if article['type'] != 'article':
                continue

            # Pull information from article
            url = article['url']
            date_time = isoparse(article['firstPublishDate'])
            title = article['headline']
            text = article['body']

            # Check if title has one and only one candidate name
            if self.improper_title(title):
                continue

            # Make sure the article is published in the proper time window
            if not (self.start_date < date_time < self.end_date):
                continue

            # Add information to NewsItem
            item = NewsItem()
            item['url'] = url
            item['datetime'] = date_time
            item['title'] = title
            item['news_co'] = self.NEWS_CO
            item['text'] = text

            # Send item to the NewsItemPipeline
            yield item

    def make_api_call(self):
        """
        Unneeded in CNN. API call done by scrapy as start_requests give the item to parse_request
        """
        pass

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
    name = 'fox'  # spider name

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

            # each result is numbered.
            # The number of pages * the number of results on a page is the number of the last article
            for start in range(0,
                               self.PAGE_SIZE * self.PAGE_LIMIT,
                               self.PAGE_SIZE):

                api_url = self.create_api_query(q, start=start)
                urls, info = self.make_api_call(api_url)

                # Check if api call failed
                if urls is None:
                    continue

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
        # Send to pipeline
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

            # Format of response has an angular callback at beginning.
            # By slice the string this way, it turns into a json string
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
        """
        Format custom date for Fox from instance variable start and end dates
        e.g. 2020-01-01
        :return: date string
        :rtype: str
        """
        return self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d')


class NEWSAPI(ArticleSource):

    news_api = NewsApiClient(api_key=os.environ.get('NEWS_API_KEY2'))

    LAST_NAMES = ['TRUMP', 'BIDEN', 'SANDERS', 'WARREN', 'HARRIS', 'BUTTIGIEG']
    QUERY = '(' + ') OR ('.join(LAST_NAMES) + ')'
    PAGE_SIZE = 100

    NUM_REQUESTS = 50  # Maximum number of queries is 500
    MAX_DAYS_BACK = 30
    EVERYTHING_URL = "https://newsapi.org/v2/everything"
    SOURCES = ','.join(['cnn', 'fox-news', 'the-new-york-times'])
    ALL_SOURCES = ['abc-news', "al-jazeera-english", "australian-financial-review", 'associated-press', "axios",
                   'bbc-news', "bloomberg", "breitbart-news", "business-insider", "business-insider-uk", "buzzfeed",
                   'cbc-news', 'cnbc', 'cnn', "entertainment-weekly", "financial-post", "fortune", 'fox-news',
                   "independent", "mashable", "medical-news-today", 'msnbc', 'nbc-news', "national-geographic",
                   "national-review", "new-scientist", "news-com-au", "new-york-magazine", "next-big-future",
                   "nfl-news", "the-globe-and-mail", "the-irish-times", "the-jerusalem-post", "the-lad-bible",
                   "the-times-of-india", "the-verge", "wired", 'newsweek', 'politico', 'reuters', 'the-hill',
                   "the-hindu", 'the-american-conservative', 'the-huffington-post', "the-new-york-times",
                   'the-wall-street-journal', 'the-washington-post', 'the-washington-times', 'time', 'usa-today',
                   'vice-news']

    def __init__(self, **kwargs):
        ArticleSource.__init__(self, **kwargs)
        # How far back to look
        if (DEFAULT_END_DATE - self.start_date) > timedelta(days=self.MAX_DAYS_BACK):
            logging.info("Can only look 30 days back from today.")
            self.start_date = datetime.now(timezone.utc) - timedelta(self.MAX_DAYS_BACK)
        self.amount_of_time = self.end_date - self.start_date

    def start_requests(self):

        for i in range(self.NUM_REQUESTS):
            time_division = self.amount_of_time / self.NUM_REQUESTS
            self.end_date = self.start_date + time_division
            if self.end_date > DEFAULT_END_DATE:
                self.end_date = DEFAULT_END_DATE
            self.parse(self.news_api.get_everything(q=self.QUERY,
                                                    page=1,
                                                    from_param=self.start_date,
                                                    to=self.end_date,
                                                    page_size=self.PAGE_SIZE,
                                                    qintitle=self.QUERY,
                                                    language='en',
                                                    sources=self.SOURCES,
                                                    sort_by='relevancy'))
            self.start_date += time_division
            self.end_date += time_division

    def parse(self, result):
        if result['status'] == 'ok':
            for article in result['articles']:
                if self.improper_title(article['title']):
                    continue

                try:
                    article_info = {
                        'url': article['url'],
                        'datetime': isoparse(article['publishedAt']),
                        'title': article.get('title', ''),
                        'news_co': article.get['source'].get('name', ''),
                        'text': article.get('content', ''),
                    }
                except KeyError as e:
                    logging.info(f"Article key error({e}): {article['url']}")
                    continue
                except ValueError as e:
                    logging.info(f"Could not parse date {e}: {article['publishedAt']}")
                    continue
                scores = analyze_title(analyzers, article_info['title'])
                self.post_article_to_db(article_info=article_info, scores=scores)

        logging.info(f"Invalid response from NewsAPI: {result}")

    def create_api_query(self, q, page, page_size, qintitle):
        from_param, to_param = self.make_date_strings()
        payload = {
            'q': q,
            'qintitle': qintitle,
            'from': from_param,
            'to': to_param,
            'pageSize': page_size,
            'page': page,
            'sources': self.SOURCES,
            'language': 'en',
            'sortBy': 'relevancy',
        }
        return payload

    def make_api_call(self):
        pass

    def make_date_strings(self, *args, **kwargs):
        str_format = "%Y-%m-%dT%H:%M:%S"
        return datetime.strftime(self.start_date, str_format), datetime.strftime(self.end_date, str_format)

def get_recent_articles():
    """
    Uses all 3 spiders to crawl through recent articles.
    Default time span is
    :return:
    :rtype:
    """
    settings_file_path = 'scraping.scraping.settings'
    os.environ.setdefault('SCRAPY_SETTINGS_MODULE', settings_file_path)
    # del os.environ['SCRAPY_SETTINGS_MODULE']
    process = CrawlerProcess(get_project_settings())
    process.crawl(NYT, interactive=False)
    process.crawl(CNN, interactive=False)
    process.crawl(FOX, interactive=False)
    process.start()


if __name__ == "__main__":
    import sys

    choice = input("Which news company would you like to scrape?\n"
                   "1. NYTimes\n"
                   "2. CNN\n"
                   "3. Fox News\n"
                   "4. All recent articles\n"
                   "5. NEWSAPI\n")

    if choice == '1':
        spider = NYT
    elif choice == '2':
        spider = CNN
    elif choice == '3':
        spider = FOX
    elif choice == '4':
        get_recent_articles()
        sys.exit(0)
    elif choice == '5':
        napi = NEWSAPI(interactive=False)
        napi.start_requests()
        sys.exit(0)
    else:
        sys.exit(0)
    process = CrawlerProcess()
    process.crawl(spider, interactive=True)
    process.start()
