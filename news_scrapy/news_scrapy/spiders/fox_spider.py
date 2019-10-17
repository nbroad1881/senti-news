import scrapy
import json

class MySpider(scrapy.Spider):
	name = 'fox'

	start_urls = ['https://api.foxnews.com/v1/content/search?q=bernie%20AND%20sanders&fields=date,description,title,url,image,type,taxonomy&section.path=fnc&type=article&min_date=2019-10-01&max_date=2019-10-17&start=0&callback=angular.callbacks._0&cb=2019101792'
	]

	def parse(self, response):
		txt = response.text
		# print(type(txt), txt[:20])
		jtext = json.loads(txt[21:-1])
		docs = jtext['response']['docs']
		for d in docs:
			print(d['date'],' -> ',d['url'])