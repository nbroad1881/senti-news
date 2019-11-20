import os
from datetime import datetime

from dotenv import load_dotenv
from newsapi.newsapi_client import NewsApiClient

load_dotenv()

news_api = NewsApiClient(api_key=os.environ.get('NEWS_API_KEY'))

CANDIDATES = ['Donald Trump', 'Joe Biden', 'Bernie Sanders', 'Elizabeth Warren', 'Kamala Harris', 'Pete Buttigieg']
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


class NewsAPIScraper:

    def __init__(self):
        pass

    def get_titles(self, candidate):
        first_call = news_api.get_everything(q=candidate,
                                             language='en',
                                             sort_by='relevancy',
                                             page=1,
                                             page_size=1)
        if first_call['status'] == 'ok':
            num_results = first_call['totalResults']

        for days_back in range(MAX_DAYS_BACK, 1, -1):
            from_param = datetime.date.today() - datetime.timedelta(days=days_back)
            to_param = from_param + datetime.timedelta(days=1)
            # todo: handle rateLimited error
            all_articles = news_api.get_everything(q=candidate,
                                                   language='en',
                                                   from_param=from_param.isoformat(),
                                                   to=to_param.isoformat(),
                                                   sort_by='relevancy',
                                                   page=1,
                                                   page_size=PAGE_SIZE)
