# -*- coding: utf-8 -*-
import json
import logging
import re

import scrapy
from extruct.w3cmicrodata import MicrodataExtractor
from scrapy.loader import ItemLoader

from homebrewsupply.items import Product
from homebrewsupply.loaders import ProductLoader

logger = logging.getLogger()


class UrbanbrewshopComBrSpider(scrapy.Spider):
    name = 'urbanbrewshop.com.br'
    allowed_domains = ['urbanbrewshop.com.br']
    start_urls = ['http://urbanbrewshop.com.br/']

    def parse(self, response):
        categories_urls = response.xpath(
            '//section[@id="nav_menu-2"]//a/@href').extract()
        for category_url in categories_urls:
            logger.debug('Requesting category: {0}'.format(
                category_url))
            yield scrapy.Request(
                response.urljoin(category_url),
                callback=self._process_category)

    def _get_category_name(self, url):
        if 'maltes-adjuntos' in url:
            return 'malts'
        elif 'lupulos' in url:
            return 'hops'
        elif 'leveduras' in url:
            return 'yeast'
        elif 'auxiliares' in url:
            return 'extra'
        else:
            return 'N/A'

    def _process_category(self, response):
        products_urls = response.xpath(
            '//ul[@class="products"]//a/@href').extract()
        category = self._get_category_name(response.url)

        for product_url in products_urls:
            logger.debug('Requesting product: {0}'.format(
                product_url))

            logger.info('Origin: {0} | Product {1} | Category: {2}'.format(
                response.url, product_url, category))

            request = scrapy.Request(
                response.urljoin(product_url),
                callback=self._process_product)
            request.meta['category'] = category
            yield request

        pagination = response.xpath(
            '//span[@class="pagination-meta"]//text()').extract_first()
        if pagination is not None:
            pagination_re = '[^\d]*(?P<start_page>\d*)[^\d]*(?P<end_page>\d*)'
            match = re.match(pagination_re, pagination)

            start_page = match.groupdict().get('start_page')
            end_page = match.groupdict().get('end_page')

            if start_page is not None and end_page is not None:
                start_page, end_page = map(int, [start_page, end_page])

                base_page_url = response.xpath(
                    '//nav[@class="pagination"]/a[contains(@href, "page")]/@href').extract_first()
                if base_page_url is not None:
                    for page in range(start_page, end_page + 1):
                        page_url = re.sub(
                            r'([^\d]*)(\d*)([^\d]*)',
                            r'\g<1>{0}\g<3>'.format(page),
                            base_page_url
                        )
                        logger.debug('Requesting page {0}: {1}'.format(
                            page, page_url))
                        yield scrapy.Request(
                            response.urljoin(page_url),
                            callback=self._process_category)

    def _process_product(self, response):
        extractor = MicrodataExtractor()
        itemprops = extractor.extract(
            response.body_as_unicode(), response.url)

        il = ProductLoader(item=Product())
        il.add_value('store', self.name)
        il.add_value('url', response.url)
        il.add_value('category', response.meta.get('category', 'N/A'))

        product_variations = response.xpath(
            '//form/@data-product_variations').extract_first('[]')
        product_variations = json.loads(product_variations)
        if len(product_variations) > 0:
            variation = product_variations[0]
            il.add_value('price', variation.get('display_price'))
            il.add_value('available', variation.get('is_in_stock', False))

        for item in itemprops:
            if item.get('type') == 'http://schema.org/Product':
                product_props = item.get('properties', {})
                il.add_value('name', product_props.get('name', ''))
                il.add_value('description', product_props.get('description', ''))
                break

        return il.load_item()
