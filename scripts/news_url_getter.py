from newsapi import NewsApiClient
import csv
import json

with open('config.json', 'r') as j_file:
    j = json.load(j_file)
    key = j['API-Key']

newsapi = NewsApiClient(api_key=key)

candidates = ['Joe Biden',
              'Elizabeth Warren',
              'Bernie Sanders',
              'Pete Buttigieg',
              'Kamala Harris']

srcs = ['the-new-york-times',
        'cnn',
        'fox-news']

url_dict = {}

start_date = '2019-09-23'
end_date = '2019-09-23'
dt = '2019-09-3'

urls = set()

for n in range(0, 1, 1):
    for c in candidates:
        all_articles = newsapi.get_everything(q=c, from_param=dt + str(n), to=dt + str(n),
                                              sources=','.join(srcs), page_size=100)

        total_results = all_articles['totalResults']
        print(dt + str(n), '- total results for', c, '=', total_results)
        urls.update([a['url'] for a in all_articles['articles']])

    # for p in range(2,total_results//100+1,1):
    # 	all_articles = newsapi.get_everything(q=c,from_param=start_date,to=end_date,
    # 						sources=','.join(srcs), page_size=100, page=p)
    # 	urls.update([a['url'] for a in all_articles['articles']])
    # print(p)
    filename = 'urls/all-' + dt + str(n) + '.csv'
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(list(urls))
    print("final count =", len(urls))
