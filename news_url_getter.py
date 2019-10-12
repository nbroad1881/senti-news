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

start_date = '2019-09-27'
end_date = '2019-10-03'

for c in candidates:
	url_dict[c] = []
	all_articles = newsapi.get_everything(q=c,from_param=start_date,to=end_date,
						sources=','.join(srcs), page_size=100)
	
	for a in all_articles['articles']:
		if a['content'] != None:
			url_dict[c].append(a['url'])

	filename = c.replace(' ','-')+'-' +start_date+end_date[-3:]+'.csv'
	with open(filename,'w') as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(url_dict[c])
