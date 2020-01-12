import logging

from scrapy.exceptions import DropItem

from sentinews.database import DataBase


# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


class ScrapingPipeline(object):

    def process_item(self, item, spider):
        return item


class NewsItemPipeline:

    def __init__(self):
        self.db = DataBase()

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        self.db.close_session()
        logging.info(f"Logged {spider.articles_logged} articles")

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_item(self, item, spider):
        result = self.db.add_row(
            url=item['url'],
            datetime=item['datetime'],
            title=item['title'],
            news_co=item['news_co'],
            text=item['text']
        )
        if result:
            result_string = 'successfully added'
        else:
            result_string = 'not added'

        raise DropItem(f'{item["title"]} {result_string}')

