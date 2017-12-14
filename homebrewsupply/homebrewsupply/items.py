# -*- coding: utf-8 -*-
import scrapy


class Product(scrapy.Item):

    url = scrapy.Field()
    name = scrapy.Field()
    description = scrapy.Field()
    category = scrapy.Field()
    price = scrapy.Field()
    unit = scrapy.Field()
    available = scrapy.Field()
    store = scrapy.Field()
