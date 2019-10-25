import scrapy
from scrapy.crawler import CrawlerProcess
import json
import datetime
import csv
import requests
import time

CNN_RESULTS_SIZE = 100
DEM_CANDIDATES = ['biden', 'warren', 'sanders', 'harris', 'buttigieg']


# todo: have an interactive query
#     database for text documents
def scrape_fox(response, date='', title=''):
    with open('fox_articles.csv', 'a') as f:
        writer = csv.writer(f)
        writer.writerow([date, title, ' '.join(response.xpath('//div[(@class="article-body")]//p/text()|//div['
                                                              '@class="article-body"]//p/a/text()').getall())])


class NewsSpider(scrapy.Spider):
    """Spider to grab news article text
    """
    name = 'scrape-news'

    def __init__(self, start_urls=[], unq_ids=set()):
        """

        :type start_urls: List(str)
        """
        super().__init__()
        self.start_urls = start_urls
        self.unq_ids = unq_ids

    def parse(self, response):
        if 'angular' in response.text[:30]:
            d = json.loads(response.text[21:-1])
            fox_info = get_fox_info(d['response'])
            for d, t, u, i in fox_info:
                if u[0] in self.unq_ids or i != 'article':
                    continue
                yield scrapy.Request(u[0], callback=scrape_fox, cb_kwargs=dict(date=d, title=t))
                self.unq_ids.add(u[0])
        elif 'New York Times' in response.text[:100]:
            print('scraping nyt')
            d = json.loads(response.text)
            nyt_info = get_nyt_info(d['response']['docs'])
            for url, dt, _id in nyt_info:
                print(f'url:{url}\ndate:{dt}\nid:{_id}')
                time.sleep(6)
                yield scrapy.Request(url, callback=scrape_nyt, cb_kwargs=dict(date=dt, _id=_id))


#   i.e the 2nd page starts at start=10, 3rd page at start=20
def form_fox_query(q, min_date, max_date, start):
    s_1 = 'https://api.foxnews.com/v1/content/search?q='
    q = q
    s_2 = '&fields=date,description,title,url,image,type,taxonomy&section.path=fnc&type=article&min_date='
    min_dt = min_date
    s_3 = '&max_date='
    max_dt = max_date
    s_4 = '&start='
    start = str(start)
    s_5 = '&callback=angular.callbacks._0&cb='
    dt_today = datetime.date.today().isoformat().replace('-', '')
    s_6 = '112'
    return ''.join([s_1, q, s_2, min_dt, s_3, max_dt, s_4, start, s_5, dt_today, s_6])


# todo: writes text to file
def scrape_nyt(response, date, _id):
    title = response.xpath('./head/title//text()').get()
    body = response.xpath('//section[contains(@name, "articleBody")]//text()').getall()
    with open('nyt_articles.csv', 'a') as f:
        print('wrote to file')
        writer = csv.writer(f)
        writer.writerow([date, title, _id, ' '.join(body)])


def scrape_cnn(unq_ids, _from=0, name=''):
    """Searches cnn for name, saving articles that are not in the unique
    id set. Ordered by newest, rather than by relevance. Relevance produces
    results from 2017 first"""
    url = f'https://search.api.cnn.io/content?size={CNN_RESULTS_SIZE}' \
          f'&q={name}&type=article&sort=newest&from={str(_from)}'
    response = requests.get(url)
    if response.status_code == 200:
        print(f'Request accepted ({name}), from={_from}')
        if _from > 1000:
            return
        articles = json.loads(response.text)['result']
        num_results = json.loads(response.text)['meta']['of']
        with open('../texts/cnn_articles.csv', 'a') as f:
            writer = csv.writer(f)
            for a in articles:
                if a['type'] != 'article' or a['_id'] in unq_ids:
                    continue
                writer.writerow([a['firstPublishDate'], a['headline'], a['url'], a['_id'], a['body']])
                unq_ids.add(a['_id'])
        if _from + CNN_RESULTS_SIZE < num_results:
            scrape_cnn(unq_ids, _from=_from + CNN_RESULTS_SIZE, name=name)


def get_unique_cnn_ids():
    """Returns a set of unique cnn article ids"""
    try:
        with open('cnn_ids.csv', 'r') as f:
            reader = csv.reader(f)
            ids = set()
            for row in reader:
                ids.update(row)
            return ids
    except FileNotFoundError:
        print('cnn_ids.csv does not exist yet, returning empty set')
        return set()


def get_unique_fox_ids():
    """Returns a set of unique fox article ids.
    There are no actual id tag for fox articles,
    so this treats each url as a unique id
    """
    try:
        with open('fox_ids.csv', 'r') as f:
            reader = csv.reader(f)
            ids = set()
            for row in reader:
                ids.update(row)
            return ids
    except FileNotFoundError:
        print('fox_ids.csv does not exist yet, returning empty set')
        return set()


def set_unique_cnn_ids(unq_ids):
    """Stores the unique article ids in a csv
    Always overwrites"""
    with open('cnn_ids.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(list(unq_ids))


def set_unique_fox_ids(unq_ids):
    """Stores the unique article urls in a csv
    Always overwrites"""
    with open('fox_ids.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(list(unq_ids))


def get_fox_info(res):
    """Pulls date, title, and url from API response"""
    urls = []
    for d in res['docs']:
        dt = d['date']
        title = d['title']
        url = d['url']
        _type = d['type']
        urls.append((dt, title, url, _type))
    return urls


def cnn():
    cnn_ids = get_unique_cnn_ids()
    for c in DEM_CANDIDATES:
        scrape_cnn(unq_ids=cnn_ids, name=c)
    set_unique_cnn_ids(cnn_ids)


def fox_news():
    dt_today = datetime.date.today().isoformat()

    unq_ids = get_unique_fox_ids()
    try:
        for c in DEM_CANDIDATES:
            start = form_fox_query('biden', '2019-01-01', dt_today, 0)
            r = requests.get(start).text
            j = json.loads(r[21:-1])
            num_results = j['response']['numFound']
            num_results = 1000 if num_results > 1000 else num_results
            start_urls = [form_fox_query(c, '2019-03-01', dt_today, n) for n in range(0, num_results, 10)]
            process = CrawlerProcess()
            process.crawl(NewsSpider, start_urls=start_urls, unq_ids=unq_ids)
            process.start()
            set_unique_fox_ids(unq_ids)
    except Exception as e:
        print('e')
        set_unique_fox_ids(unq_ids)


def form_nyt_query(query, page, begin_date='20190301', end_date='20191001', sort='newest'):
    s_1 = f'https://api.nytimes.com/svc/search/v2/articlesearch.json?q={query}'
    s_2 = f'&face=true&page={str(page)}&begin_date={begin_date}&end_date={end_date}'
    s_3 = f'fq=document_type%3Aarticle%20AND%20type_of_material%3ANews'
    s_4 = f'&sort={sort}&api-key=nSc6ri8B5W6boFhjJ6SuYpQmLN8zQuV7'
    return ''.join([s_1, s_2, s_3, s_4])


# todo: have parameter be how many days back from today
#   the search should be. subtract from datetime object
def nyt():
    for c in DEM_CANDIDATES:
        date_today = datetime.date.today().isoformat().replace('-', '')
        url = form_nyt_query(query=c, end_date=date_today, page=0)
        r = requests.get(url)
        if r.status_code != 200:
            print(f'Request failed:{r.status_code},{url}')
            break
        if r.status_code == 429:
            print(f'Hit limit: {r.status_code}, sleeping')
            while r.status_code == 429:
                print('.', end='')
                time.sleep(10)
                r = requests.get(url)
            print('Retrying')
        num_results = json.loads(r.text)['response']['meta']['hits']
        num_results = 1000 if num_results > 1000 else num_results
        start_urls = [form_nyt_query(query=c, end_date=date_today, page=n) for n in range(num_results // 10)]
        process = CrawlerProcess(settings={
            'CONCURRENT_REQUESTS': 2,
            'DOWNLOAD_DELAY' : 6
        })
        process.crawl(NewsSpider, start_urls=start_urls)
        process.start()


def get_nyt_info(docs):
    info = []
    for d in docs:
        url = d['web_url']
        dt = d['pub_date']
        _id = d['_id']
        info.append((url, dt, _id))
    return info


if __name__ == "__main__":

    response = input("Which news company would you like to scrape?\n"
                     "1. CNN\n2. Fox News\n3. NYTimes\n4. All of the above\n")
    if int(response) == 1:
        cnn()
    elif int(response) == 2:
        fox_news()
    elif int(response) == 3:
        pass
    elif int(response) == 4:
        pass
