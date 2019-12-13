# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class JdItem(scrapy.Item):
    # define the fields for your item here like:
    sku = scrapy.Field()
    name = scrapy.Field()
    detail = scrapy.Field()
    image = scrapy.Field()
    other_type = scrapy.Field()
    price = scrapy.Field()
    p_type = scrapy.Field()
    crawl_date = scrapy.Field()
    sku_slave_typeid = scrapy.Field()
    jetso = scrapy.Field()
    pass