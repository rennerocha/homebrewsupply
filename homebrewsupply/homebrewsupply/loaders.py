from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose, TakeFirst

from homebrewsupply.items import Product


def join_strings(values):
    new_values = []
    for value in values:
        value = value.strip()
        if value != '':
            new_values.append(value)
    return '\n'.join(new_values)


class ProductLoader(ItemLoader):

    default_item_class = Product
    default_output_processor = TakeFirst()

    description_in = Compose(join_strings)