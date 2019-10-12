import scrapy
import csv

class News(scrapy.Spider):
    name = "news"

    def start_requests(self):
        with open('/urls/Joe-Biden-2019-09-27-03.csv','r') as file:
            reader = csv.reader(file)
            urls = next(reader)

        for url in urls:
            if 'nytimes' in url:
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        text = ' '.join(response.xpath('.//section[@name="articleBody"]//text()').getall())
        print(text)
        with open('biden_test.txt','a') as file:
            file.write(text + '\n')  


