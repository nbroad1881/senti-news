# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapingItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class NewsItem(scrapy.Item):
    url = scrapy.Field()
    datetime = scrapy.Field()
    title = scrapy.Field()
    news_co = scrapy.Field()
    text = scrapy.Field()