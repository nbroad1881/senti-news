import os
from datetime import datetime as dt
import logging

import pandas as pd
from dotenv import load_dotenv
from newsapi.newsapi_client import NewsApiClient

load_dotenv()
logging.basicConfig(level=logging.INFO)

news_api = NewsApiClient(api_key=os.environ.get('NEWS_API_KEY'))

CANDIDATES = ['Donald Trump', 'Joe Biden', 'Bernie Sanders', 'Elizabeth Warren', 'Kamala Harris', 'Pete Buttigieg']
qinTitle = '('+') OR ('.join(CANDIDATES) + ')'
PAGE_SIZE = 100
MAX_DAYS_BACK = 30

CANDIDATE_DICT = {
    '1': 'Donald Trump',
    '2': 'Joe Biden',
    '3': 'Elizabeth Warren',
    '4': 'Bernie Sanders',
    '5': 'Kamala Harris',
    '6': 'Pete Buttigieg'
}

SOURCES = ['abc-news', "al-jazeera-english", "australian-financial-review", 'associated-press', "axios", 'bbc-news',
           "bloomberg", "breitbart-news", "business-insider", "business-insider-uk", "buzzfeed", 'cbc-news', 'cnbc',
           'cnn', "entertainment-weekly", "financial-post", "fortune", 'fox-news', "independent", "mashable",
           "medical-news-today", 'msnbc', 'nbc-news', "national-geographic", "national-review", "new-scientist",
           "news-com-au", "new-york-magazine", "next-big-future", "nfl-news", "the-globe-and-mail", "the-irish-times",
           "the-jerusalem-post", "the-lad-bible", "the-times-of-india", "the-verge", "wired", 'newsweek', 'politico',
           'reuters', 'the-hill', "the-hindu", 'the-american-conservative', 'the-huffington-post', "the-new-york-times"
                                                                                                   'the-wall-street-journal',
           'the-washington-post', 'the-washington-times', 'time', 'usa-today', 'vice-news']


class NewsAPIScraper:

    def __init__(self):
        pass

    @staticmethod
    def get_num_results(candidate):
        from_param = dt.date.today() - dt.timedelta(days=MAX_DAYS_BACK)
        first_call = news_api.get_everything(q=candidate,
                                             language='en',
                                             sources=','.join(SOURCES),
                                             sort_by='relevancy',
                                             from_param=from_param,
                                             page=1,
                                             page_size=1)
        if first_call['status'] == 'ok':
            return first_call['totalResults']
        return None

    def start(self, candidate):
        num_results = self.get_num_results(candidate)
        num_iterations = (num_results // PAGE_SIZE) + 1

        # todo: have a way to determine how many steps to break it into
        df = pd.DataFrame(columns=['URL', 'Datetime', 'Title', 'News_Co', 'Text'])

        for days_back in range(MAX_DAYS_BACK, 1, -1):
            from_param = dt.date.today() - dt.timedelta(days=days_back)
            to_param = from_param + dt.timedelta(days=1)
            # todo: handle rateLimited error
            all_articles = news_api.get_everything(q=candidate,
                                                   language='en',
                                                   sources=','.join(SOURCES),
                                                   from_param=from_param.isoformat(),
                                                   to=to_param.isoformat(),
                                                   sort_by='relevancy',
                                                   page=1,
                                                   page_size=PAGE_SIZE,
                                                   qintitle=qinTitle)
            self.articles_to_df(all_articles, df)


    def articles_to_df(self, articles, df):
        for article in articles:
            df.append({
                'URL': article.get('url'),
                'Datetime': article.get('publishedAt'),
                'Title': article.get('title'),
                'News_Co': article.get('source').get('name'),
                'Text': article.get('content')
            }, ignore_index=True)
