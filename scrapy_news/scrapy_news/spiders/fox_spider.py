import scrapy
import json

class MySpider(scrapy.Spider):
	name = 'fox'
	search_q = '%20'.join(['bernie','sanders'])
	min_date = '2019-08-01' #yyyy-mm-dd
	max_date = '2019-10-01'
	start_num = '1'

	base = 'https://api.foxnews.com/v1/content/search?q='+search_q+'&fields=date,description,title,url,image,type,taxonomy&section.path=fnc&type=article&min_date='+\
	min_date+'&max_date='+max_date+'&start={}&callback=angular.callbacks._0&cb=2019101792'

	start_urls = []
	for n in range(0,100,10):
		start_urls.append(base.format(n))

	def parse(self, response):
		txt = response.text
		jtext = json.loads(txt[21:-1])
		docs = jtext['response']['docs']

		with open('afox_urls.txt','a') as f:

			for d in docs:
				text = d['title'] + '\n' + d['date'] + '\n' + d['url'][0] + '\n'
				print(text)
				f.write(text)

# RESPONSE STRUCTURE
# JSON_TEXT
# 	-> response 
# 			-> numFound : number
# 			-> docs (list)
# 				-> date
# 				-> description
# 				-> image
# 					-> url
# 					-> credit
# 					-> caption
# 				-> taxonomy (list)
# 					-> path
# 					-> url
# 					-> adTag
# 				-> title
# 				-> type
# 				-> url (list)
