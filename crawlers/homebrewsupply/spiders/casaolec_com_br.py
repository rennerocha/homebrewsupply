# -*- coding: utf-8 -*-
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from extruct.w3cmicrodata import MicrodataExtractor

from homebrewsupply.loaders import ProductLoader


class CasaolecComBrSpider(CrawlSpider):
    name = 'casaolec.com.br'
    allowed_domains = ['casaolec.com.br']
    start_urls = ['http://casaolec.com.br/']

    rules = (
        # Follow Categories
        Rule(
            LinkExtractor(
                allow_domains='casaolec.com.br',
                restrict_xpaths='//div[@class="sidebar"]//*//ul[contains(@class, "level0")]//li'
            )
        ),

        # Follow Pagination
        Rule(
            LinkExtractor(
                allow_domains='casaolec.com.br',
                restrict_css='.pages'
            )
        ),

        # Follow Products
        Rule(
            LinkExtractor(
                allow_domains='casaolec.com.br',
                restrict_css='.product-item .product-name',
            ),
            callback='parse_product'
        )
    )

    def parse_product(self, response):
        extractor = MicrodataExtractor()
        itemprops = extractor.extract(
            response.body_as_unicode(), response.url)
        properties = itemprops[0].get('properties')

        il = ProductLoader(response=response)

        il.add_value('store', self.name)
        il.add_value('url', response.url)
        il.add_value('category', response.meta.get('category', 'N/A'))

        il.add_value('name', properties.get('name'))
        il.add_value('description', properties.get('description'))

        offers = properties.get('offers', {}).get('properties', {})
        is_available = offers.get('availability') == 'http://schema.org/InStock'

        il.add_value('available', is_available)
        il.add_value('price', offers.get('price'))

        yield il.load_item()