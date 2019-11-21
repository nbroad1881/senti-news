import csv
import logging
import pathlib
import datetime

from newsapi.newsapi_client import NewsApiClient

logging.basicConfig(level=logging.INFO)

# Init
newsapi = NewsApiClient(api_key='f725be960d5c4ed9937f84cef2620702')

candidates = ['Joe Biden', 'Bernie Sanders', 'Elizabeth Warren', 'Kamala Harris', 'Pete Buttigieg']
PAGE_SIZE = 100
NEWSAPI_CSV = pathlib.Path('NEWSAPI.csv')
NEWSAPI_NEW_CSV = pathlib.Path('NEWSAPI_NEW.csv')
SOURCE_GROUP_SIZE = 6

all_sources = ['abc-news', 'associated-press', 'bbc-news', 'cbc-news', 'cnbc', 'cnn', 'fox-news', 'msnbc', 'nbc-news',
               'newsweek', 'politico', 'reuters,the-hill,the-american-conservative', 'the-huffington-post',
               'the-wall-street-journal', 'the-washington-post', 'the-washington-times', 'time,usa-today', 'vice-news']


def append_all_info(filepath):
    if filepath.is_file():
        with open(filepath, 'r') as csv_file:
            reader = csv.reader(csv_file)
            unique_urls = set([row[0] for row in reader])
    else:
        unique_urls = set()
    with open(filepath, 'a') as csv_file:
        writer = csv.writer(csv_file)
        for candidate in candidates:
            first_call = newsapi.get_everything(q=candidate,
                                                sources=''.join(all_sources),
                                                language='en',
                                                sort_by='relevancy',
                                                page=1,
                                                page_size=1)
            if first_call['status'] == 'ok':
                num_results = first_call['totalResults']
                counter = 0
                logging.info(f'Number of results for {candidate} = {num_results}')
                for index in range(0, len(all_sources), SOURCE_GROUP_SIZE):
                    sources = all_sources[index:SOURCE_GROUP_SIZE]
                    for days_back in range(30, 1, -1):
                        from_param = datetime.date.today() - datetime.timedelta(days=days_back)
                        to_param = from_param + datetime.timedelta(days=1)
                        # todo: handle rateLimited error
                        all_articles = newsapi.get_everything(q=candidate,
                                                              sources=','.join(sources),
                                                              language='en',
                                                              from_param=from_param.isoformat(),
                                                              to=to_param.isoformat(),
                                                              sort_by='relevancy',
                                                              page=1,
                                                              page_size=PAGE_SIZE)

                        for article in all_articles['articles']:
                            url = article['url']
                            if url not in unique_urls:
                                logging.info(f'logging (#{counter}) = {article["title"]}')
                                counter += 1
                                unique_urls.add(url)
                                writer.writerow([url,
                                                 article['title'],
                                                 article['source']['id'],
                                                 article['source']['name'],
                                                 f'q={candidate}',
                                                 article['description'],
                                                 article['publishedAt'],
                                                 article['content']])


def remove_duplicates(old_filepath, new_filepath):
    to_new_file = []
    with open(old_filepath, 'r') as file:
        reader = csv.reader(file)
        unique_urls = set()
        for row in reader:
            if row[0] not in unique_urls:
                unique_urls.add(row[0])
                to_new_file.append(row)

    with open(new_filepath, 'w') as file:
        writer = csv.writer(file)
        for row in to_new_file:
            writer.writerow(row)


if __name__ == '__main__':
    append_all_info(NEWSAPI_CSV)
    # remove_duplicates(NEWSAPI_CSV, NEWSAPI_NEW_CSV)
