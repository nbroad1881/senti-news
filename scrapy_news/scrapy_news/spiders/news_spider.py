import scrapy
import csv
date = '2019-09-26'

class News(scrapy.Spider):
    name = "news"

    def __init__(self):
        self.path_to_html = 'search.html'
        self.html_file = open(self.path_to_html, 'w')
    

    def start_requests(self):
        
        yield scrapy.Request(url='https://www.cnn.com/',
                    callback=self.parse)
        
        # filename = '/Users/nicholasbroad/scrapy/tutorial/urls/all-{}.csv'.format(date)

        # with open(filename,'r') as file:
        #     reader = csv.reader(file)
        #     urls = next(reader)

        # # key_bad_words = ['/video', '/podcasts']
        # for url in urls:
        #     # if not any([elem in url for elem in key_bad_words]):
        #     yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.html_file.write(response.text)
        self.html_file.close()
        # if 'foxnews.com' in response._url:
        #     text = ' '.join(response.xpath('.//div[@class="article-body"]//p//text()').getall())
        # elif 'nytimes.com' in response._url:
        #     text = ' '.join(response.xpath('.//section[@name="articleBody"]//text()').getall())
        # elif 'cnn.com' in response._url:
        #     text = ' '.join(response.xpath('.//div[contains(@class,"zn-body__paragraph")]//text()').getall())
        # else:
        #     text = ''
        # with open('text-{}.csv'.format(date),'a') as file:
        #     writer = csv.writer(file)
        #     writer.writerow([text]) 


#bbc response.xpath('.//div[@class="story-body__inner"]//p//text()').getall()
#cnn response.xpath('//p[contains(@class,"zn-body__paragraph") and not(contains(@class,"zn-body__footer"))]//text() | //div[contains(@class,"zn-body__paragraph")]/text() | //a[parent::div[contains(@class,"zn-body__paragraph")]]/text()').getall()   
#nyt response.xpath('//section[contains(@name, "articleBody")]//text()').getall()
#fox response.xpath('//div[(@class="article-body")]//p/text()|//div[@class="article-body"]//p/a/text()').getall()

 

#unicode.normalize()