import scrapy


class LotteryusaSpider(scrapy.Spider):
    name = "lotteryusa"
    allowed_domains = ["lotteryusa.com"]
    start_urls = ["https://www.lotteryusa.com/powerball/"]

    def parse(self, response):
        title = response.css("title::text").get(default="").strip()

        draw_date = response.css(".c-draw-card__date ::text").getall()
        draw_date = " ".join([x.strip() for x in draw_date if x.strip()])

        main_numbers = response.css("ul.c-result li.c-ball::text").getall()
        bonus_number = response.css("ul.c-result li.c-result__bonus::text").get()
        multiplier = response.css("ul.c-result li.c-result__multiplier::text").get()

        jackpot = response.css(".c-draw-card__prize ::text").getall()
        jackpot = " ".join([x.strip() for x in jackpot if x.strip()])

        yield {
            "page": response.url,
            "title": title,
            "draw_date": draw_date,
            "main_numbers": main_numbers,
            "powerball": bonus_number,
            "power_play": multiplier,
            "jackpot": jackpot,
        }