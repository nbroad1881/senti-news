import os
from datetime import datetime, date, timedelta
from dateutil.parser import isoparse
import logging

import pandas as pd
from dotenv import load_dotenv
from newsapi import NewsApiClient
from sentinews.database.database import DataBase

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

LIMITED_SOURCES = ['bbc-news', "breitbart-news", 'cnn', 'fox-news',
                   'politico', 'reuters', 'the-hill', 'the-american-conservative', 'the-huffington-post',
                   "the-new-york-times", 'the-wall-street-journal', 'the-washington-post', ]


class NewsAPIScraper:

    def __init__(self, limited):
        if limited:
            self.sources = LIMITED_SOURCES
        else:
            self.sources = SOURCES
        self.db = DataBase()

    def get_num_results(self):
        from_param = date.today() - timedelta(days=1)
        logging.info(f"query {QUERY}")
        logging.info(f"from {from_param}")
        logging.info(f"src {','.join(self.sources)}")
        logging.info(f"qintitle {Q_IN_TITLE}")
        first_call = news_api.get_everything(q='DONALD TRUMP',
                                             language='en',
                                             sources=','.join(SOURCES),
                                             sort_by='relevancy',
                                             from_param=from_param,
                                             page=1,
                                             page_size=1,
                                             qintitle=Q_IN_TITLE)
        if first_call['status'] == 'ok':
            logging.info(f'Num results since{from_param} : {first_call["totalResults"]}')
            return first_call['totalResults']
        return None

    def get_titles(self):
        num_results = self.get_num_results()
        num_iterations = (num_results // PAGE_SIZE) + 1

        # todo: have a way to determine how many steps to break it into
        df = pd.DataFrame(columns=['url', 'datetime', 'title', 'news_co', 'text'])

        for hours_back in range(48, 1, -2):
            from_param = datetime.utcnow() - timedelta(hours=hours_back)
            to_param = from_param + timedelta(hours=2)
            # todo: handle rateLimited error
            results = news_api.get_everything(q=QUERY,
                                              language='en',
                                              sources=','.join(self.sources),
                                              from_param=from_param,
                                              to=to_param,
                                              sort_by='relevancy',
                                              page=1,
                                              page_size=PAGE_SIZE,
                                              qintitle=Q_IN_TITLE)
            df = self.articles_to_df(results.get('articles'), df)
            self.dataframe_to_db(df)

    def dataframe_to_db(self, frame):
        for index, row in frame.iterrows():
            result = self.db.add_row(url=row['url'],
                                     datetime=row['datetime'],
                                     title=row['title'],
                                     news_co=row['news_co'],
                                     text=row['text'])
            if result:
                logging.info(f"Added {row['title']} to database")

    def articles_to_df(self, articles, df):
        for article in articles:
            if self.proper_title(article.get('title')):
                df = df.append({
                    'url': article.get('url'),
                    'datetime': isoparse(article.get('publishedAt')),
                    'title': article.get('title'),
                    'news_co': article.get('source').get('name'),
                    'text': article.get('content')
                }, ignore_index=True)
        return df

    @staticmethod
    def proper_title(title):
        """
        Only want one key word in the title.
        :param title: Title string to be checked
        :return: True if it has one key word, false if it has zero or more than one.
        """
        if title is None or len(title) == 0:
            return False
        names = ['trump', 'biden', 'warren', 'sanders', 'harris', 'buttigieg']
        return sum([1 if name in title.lower() else 0 for name in names]) == 1


if __name__ == '__main__':
    napi = NewsAPIScraper(limited=True)
    napi.get_titles()
    napi.db.close_session()