import os
from datetime import datetime, date, timedelta
from dateutil.parser import isoparse
import logging

import pandas as pd
from dotenv import load_dotenv
from newsapi import NewsApiClient
from sentinews.database.database import get_session, add_row_to_db

load_dotenv()
logging.basicConfig(level=logging.INFO)

news_api = NewsApiClient(api_key=os.environ.get('NEWS_API_KEY'))

CANDIDATES = ['Donald Trump', 'Joe Biden', 'Bernie Sanders', 'Elizabeth Warren', 'Kamala Harris', 'Pete Buttigieg']
LAST_NAMES = ['TRUMP', 'BIDEN', 'SANDERS', 'WARREN', 'HARRIS', 'BUTTIGIEG']
QUERY = '(' + ') OR ('.join(CANDIDATES) + ')'
Q_IN_TITLE = '(' + ') OR ('.join(LAST_NAMES) + ')'
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
           'reuters', 'the-hill', "the-hindu", 'the-american-conservative', 'the-huffington-post', "the-new-york-times",
           'the-wall-street-journal', 'the-washington-post', 'the-washington-times', 'time', 'usa-today', 'vice-news']

LIMITED_SOURCES = ['bbc-news',"breitbart-news",'cnn','fox-news',
                   'politico','reuters', 'the-hill','the-american-conservative', 'the-huffington-post',
                   "the-new-york-times", 'the-wall-street-journal', 'the-washington-post',]


class NewsAPIScraper:

    def __init__(self, limited):
        if limited:
            self.sources = LIMITED_SOURCES
        else:
            self.sources = SOURCES

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

        for hours_back in range(48, 1, -2):
            from_param = datetime.utcnow() - timedelta(hours=hours_back)
            to_param = from_param + timedelta(hours=2)
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

    @staticmethod
    def dataframe_to_db(frame):
        session = get_session()
        for index, row in frame.iterrows():
            add_row_to_db(session,
                          url=row['url'],
                          datetime=row['datetime'],
                          title=row['title'],
                          news_co=row['news_co'],
                          text=row['text'])
            logging.info(f"Added {row['title']} to database")

    def articles_to_df(self, articles, df):
        for article in articles:
            df.append({
                'URL': article.get('url'),
                'Datetime': article.get('publishedAt'),
                'Title': article.get('title'),
                'News_Co': article.get('source').get('name'),
                'Text': article.get('content')
            }, ignore_index=True)

    @staticmethod
    def no_space(string):
        return string.replace(' ', '%20')


if __name__ == '__main__':
    napi = NewsAPIScraper(limited=True)
    napi.get_titles()