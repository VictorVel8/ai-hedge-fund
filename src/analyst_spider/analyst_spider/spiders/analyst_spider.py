import scrapy
import json

class AnalystSpider(scrapy.Spider):
    name = "analyst_spider"
    custom_settings = {
         'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
     }
    
    nyse_target_prices_dict = {}
    nasdaq_target_prices_dict = {}
    symbol = "AAPL"

    def __init__(self, ticker, *args, **kwargs) :
        super().__init__(*args, **kwargs)
        self.symbol = ticker
    
    def start_requests(self):
        symbol = "SNOW"
        url = f'https://www.marketbeat.com/stocks/NASDAQ/{symbol}/forecast/'
        yield scrapy.Request(url=url, callback=self.parse, meta={"symbol":symbol, "dont_redirect":True, 'handle_httpstatus_list': [301]})


    def parse(self, response):
        if response.status == 301 and "NASDAQ" in response.url:
            # Daca nu gasim pe NASDAQ, cautam si pe NYSE
            yield scrapy.Request(url=f'https://www.marketbeat.com/stocks/NYSE/{response.meta["symbol"]}/forecast/', callback=self.parse, meta=response.meta, dont_filter=True)
        # ultimele 10 rating-uri le luam cu pondere 2, penultimele 10 cu pondere 1. Asta pentru ca ultimele sunt mai recente
        # si pot include anumite analize recente
        analysts_review_rows = response.xpath('//table[@id="history-table"]/tbody/tr')
        i=0
        IMPORTANT_THRESHOLD = 10
        IMPORTANT_FACTOR = 2
        target_prices_sum = 0
        target_prices_cnt = 0
        for review_row in analysts_review_rows:
            cells = review_row.xpath('./td/text()').getall()
            if len(cells) != 6:
                continue
            target_price_str = ""
            if len(cells[4].split("➝")) == 2:
                target_price_str = cells[4].split("➝")[1].strip()
            else:
                target_price_str = cells[4]
            target_price = float(target_price_str.replace("$", ""))

            if i<IMPORTANT_THRESHOLD:
                target_prices_sum += IMPORTANT_FACTOR * target_price
                target_prices_cnt+=IMPORTANT_FACTOR
            else:
                target_prices_sum += target_price
                target_prices_sum+=1

            i+=1
            if i == 2*IMPORTANT_THRESHOLD:
                break
        if target_prices_cnt>0:
            yield {"price":target_prices_sum/target_prices_cnt}
        else:
            yield {"price":0}


    def closed(self, response):
        # if "NASDAQ" in response.url:
        with open("NASDAQ_analysts_review_avg.json", 'w') as json_file:
            json.dump(self.nasdaq_target_prices_dict, json_file, indent=4, default=vars)
        with open("NYSE_analysts_review_avg.json", 'w') as json_file:
                json.dump(self.nyse_target_prices_dict, json_file, indent=4, default=vars)