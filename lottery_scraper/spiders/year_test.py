import scrapy


class YearTestSpider(scrapy.Spider):
    name = "year_test"
    allowed_domains = ["lotteryusa.com"]
    start_urls = [
        "https://www.lotteryusa.com/powerball/year/"
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "ROBOTSTXT_OBEY": True,
        "FEEDS": {
            "year_test.json": {
                "format": "json",
                "overwrite": True,
                "indent": 2,
            }
        },
    }

    def parse(self, response):
        title = response.css("title::text").get(default="").strip()

        # 1) guarda info general
        yield {
            "type": "page_info",
            "source_url": response.url,
            "title": title,
            "tables_found": len(response.css("table")),
            "links_found": len(response.css("a")),
            "forms_found": len(response.css("form")),
        }

        # 2) primeras 20 filas de cualquier tabla
        rows = response.css("table tr")
        for i, row in enumerate(rows[:20]):
            cells = row.css("th::text, td::text, th *::text, td *::text").getall()
            clean_cells = [x.strip() for x in cells if x.strip()]
            yield {
                "type": "table_row",
                "row_index": i,
                "cells": clean_cells,
                "source_url": response.url,
            }

        # 3) primeros 40 enlaces para inspeccionar
        for i, a in enumerate(response.css("a")[:40]):
            href = a.attrib.get("href")
            text = " ".join(a.css("*::text, ::text").getall()).strip()
            if href or text:
                yield {
                    "type": "link",
                    "link_index": i,
                    "text": text,
                    "href": href,
                    "source_url": response.url,
                }

        # 4) primeros 30 textos visibles "útiles"
        texts = response.css("body ::text").getall()
        clean_texts = []
        for t in texts:
            t = t.strip()
            if t and len(t) < 120:
                clean_texts.append(t)

        for i, t in enumerate(clean_texts[:30]):
            yield {
                "type": "text_sample",
                "text_index": i,
                "text": t,
                "source_url": response.url,
            }