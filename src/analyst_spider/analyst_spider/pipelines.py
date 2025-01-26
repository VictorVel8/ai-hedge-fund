# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

class AnalystSpiderPipeline:
    average_price = 0
    def process_item(self, item, spider):
        AnalystSpiderPipeline.average_price = item["price"]
        return item
