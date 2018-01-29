# -*- coding: utf-8 -*-
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from extruct.w3cmicrodata import MicrodataExtractor

from homebrewsupply.loaders import ProductLoader


class BrewmarketComBrSpider(CrawlSpider):
    name = 'brewmarket.com.br'
    allowed_domains = ['brewmarket.com.br']
    start_urls = ['https://www.brewmarket.com.br/']

    rules = (
        # Follow Categories
        Rule(
            LinkExtractor(
                allow_domains='brewmarket.com.br',
                restrict_css='.menu-top #verticalmenu .row ul li'
            )
        ),

        # Follow Pagination
        Rule(
            LinkExtractor(
                allow_domains='brewmarket.com.br',
                restrict_css='.pager ol li a'
            )
        ),

        # Follow Products
        Rule(
            LinkExtractor(
                allow_domains='brewmarket.com.br',
                restrict_css='#products-grid ._item .product-name a'
            ),
            callback='parse_product'
        ),
    )

    def parse_product(self, response):
        extractor = MicrodataExtractor()
        itemprops = extractor.extract(
            response.body_as_unicode(), response.url)

        il = ProductLoader(response=response)
        il.add_value('store', self.name)
        il.add_value('url', response.url)
        il.add_value('category', response.meta.get('category', 'N/A'))

        il.add_value('name', itemprops[0]['properties']['name'])

        offer_details = itemprops[0]['properties']['offerDetails']['properties']
        il.add_value('price', offer_details.get('price'))

        is_available = bool(response.css('.in-stock').re('Em estoque'))
        il.add_value('available', is_available)

        il.add_css('description', '#tab-description *::text')

        yield il.load_item()