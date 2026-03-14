import re
import scrapy
from urllib.parse import urljoin, urlparse


class InventorySpider(scrapy.Spider):
    name = "inventory"
    allowed_domains = ["lotteryusa.com"]
    start_urls = [
        "https://www.lotteryusa.com/",
        "https://www.lotteryusa.com/powerball/",
        "https://www.lotteryusa.com/mega-millions/",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "ROBOTSTXT_OBEY": True,
        "FEEDS": {
            "inventory.json": {
                "format": "json",
                "overwrite": True,
                "indent": 2,
            }
        },
    }

    seen_urls = set()

    def parse(self, response):
        current_url = response.url
        if current_url in self.seen_urls:
            return
        self.seen_urls.add(current_url)

        title = response.css("title::text").get(default="").strip()

        csv_links = response.xpath("//a[contains(translate(., 'CSV', 'csv'), 'csv')]/@href").getall()
        txt_links = response.xpath("//a[contains(translate(., 'TXT', 'txt'), 'txt')]/@href").getall()

        yield {
            "url": current_url,
            "title": title,
            "csv_links": [urljoin(current_url, x) for x in csv_links],
            "txt_links": [urljoin(current_url, x) for x in txt_links],
        }

        for href in response.css("a::attr(href)").getall():
            if not href:
                continue

            abs_url = urljoin(current_url, href)
            parsed = urlparse(abs_url)

            if parsed.netloc not in ["www.lotteryusa.com", "lotteryusa.com"]:
                continue

            if abs_url in self.seen_urls:
                continue

            path = parsed.path.lower()

            interesting = any(
                token in path for token in [
                    "/powerball",
                    "/mega-millions",
                    "/year",
                    "/numbers",
                    "/results",
                    "/jackpots",
                    "/pick-3",
                    "/pick-4",
                    "/cash-5",
                    "/lotto",
                    "/daily",
                    "/midday",
                    "/evening",
                    "/cash4life",
                    "/cash-4-life",
                ]
            )

            state_like = re.fullmatch(r"/[a-z\\-]+/?", path) is not None

            if interesting or state_like:
                yield response.follow(abs_url, callback=self.parse)