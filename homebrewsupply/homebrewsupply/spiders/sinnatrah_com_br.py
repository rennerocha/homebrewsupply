# -*- coding: utf-8 -*-
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from homebrewsupply.loaders import ProductLoader


class SinnatrahComBrSpider(CrawlSpider):
    name = 'sinnatrah.com.br'
    allowed_domains = [
        'sinnatrah.com.br', 'sinnatrahcervejariaescola.commercesuite.com.br']
    start_urls = ['http://loja.sinnatrah.com.br/']

    rules = (
        # Follow Categories
        Rule(LinkExtractor(restrict_css='.menu')),

        # Follow Pagination
        Rule(LinkExtractor(restrict_css='.catalog-header .pagination')),

        # Follow Products
        Rule(
            LinkExtractor(restrict_css='.catalog-content .product'),
            callback='parse_product'
        ),
    )

    def parse_product(self, response):
        il = ProductLoader(response=response)

        il.add_value('store', self.name)
        il.add_value('url', response.url)
        il.add_value('category', response.meta.get('category', 'N/A'))

        il.add_css('name', '.product-name::text')
        il.add_css('description', '#descricao *::text')

        is_available = not bool(response.css('.botao-nao_indisponivel'))
        il.add_value('available', is_available)
        il.add_css('price', '#preco_atual::attr(value)')

        yield il.load_item()