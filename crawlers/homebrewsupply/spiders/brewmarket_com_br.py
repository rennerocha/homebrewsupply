# -*- coding: utf-8 -*-
import scrapy

from extruct.w3cmicrodata import MicrodataExtractor

from homebrewsupply.loaders import ProductLoader


class BrewmarketComBrSpider(scrapy.Spider):
    name = 'brewmarket.com.br'
    allowed_domains = ['brewmarket.com.br']
    start_urls = ['https://brewmarket.com.br/']

    def parse(self, response):
        categories_urls = response.css(
            '.menu-top #verticalmenu .row ul a::attr(href)').extract()
        for category_url in categories_urls:
            yield scrapy.Request(
                response.urljoin(category_url),
                callback=self.parse_category)

    def _get_category_name(self, url):
        if 'maltes' in url:
            return 'malts'
        elif 'lupulos' in url:
            return 'hops'
        elif 'leveduras' in url:
            return 'yeast'
        elif 'auxiliares' in url:
            return 'extra'
        elif 'equipamentos' in url:
            return 'equipments'
        else:
            return 'N/A'

    def parse_category(self, response):
        category = self._get_category_name(response.url)

        products_urls = response.css(
            '.category-products ._item a.product-image::attr(href)').extract()
        for product_url in products_urls:
            yield scrapy.Request(
                response.urljoin(product_url),
                meta={'category': category},
                callback=self.parse_product)

        next_page_url = response.css(
            '.button-next a::attr(href)').extract_first()
        if next_page_url:
            yield scrapy.Request(
                response.urljoin(next_page_url),
                callback=self.parse_category)

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

        import ipdb; ipdb.set_trace()
        il.add_css('description', '#tab-description *::text')

        yield il.load_item()