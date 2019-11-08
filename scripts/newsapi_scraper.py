import csv
import logging

from newsapi.newsapi_client import NewsApiClient

logging.basicConfig(level=logging.INFO)

# Init
newsapi = NewsApiClient(api_key='f725be960d5c4ed9937f84cef2620702')

candidates = ['Joe Biden', 'Bernie Sanders', 'Elizabeth Warren', 'Kamala Harris', 'Pete Buttigieg']
PAGE_SIZE = 100
NEWSAPI_CSV = 'NEWSAPI.csv'
NEWSAPI_NEW_CSV = 'NEWSAPI_NEW.csv'


def append_all_info():
    with open(NEWSAPI_CSV, 'a') as csv_file:
        writer = csv.writer(csv_file)
        for candidate in candidates:
            first_call = newsapi.get_everything(q=candidate,
                                                sources='abc-news,associated-press,bbc-news,cbc-news,cnbc,cnn,fox-news,'
                                                        'msnbc,nbc-news,newsweek,politico,reuters,the-hill,'
                                                        'the-american-conservative,the-huffington-post,'
                                                        'the-wall-street-journal,the-washington-post,'
                                                        'the-washington-times,time,usa-today,vice-news',
                                                language='en',
                                                sort_by='relevancy',
                                                page=1,
                                                page_size=1)
            if first_call['status'] == 'ok':
                num_results = first_call['totalResults']
                for page in range(num_results // PAGE_SIZE + 1):
                    all_articles = newsapi.get_everything(q=candidate,
                                                          sources='abc-news,associated-press,bbc-news,cbc-news,'
                                                                  'cnbc,cnn,fox-news,msnbc,nbc-news,newsweek,politico,'
                                                                  'reuters,the-hill,the-american-conservative,'
                                                                  'the-huffington-post,the-wall-street-journal,'
                                                                  'the-washington-post,the-washington-times,time,usa-today,'
                                                                  'vice-news',
                                                          language='en',
                                                          sort_by='relevancy',
                                                          page=1,
                                                          page_size=PAGE_SIZE)

                    for article in all_articles['articles']:
                        logging.info(f'type = {type(article)}')
                        writer.writerow([article['url'],
                                         article['source']['id'],
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
    remove_duplicates(NEWSAPI_CSV, NEWSAPI_NEW_CSV)
