import json
import os
import scrapy


class YearFromCatalogSpider(scrapy.Spider):
    name = "year_from_catalog"
    allowed_domains = ["lotteryusa.com"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "ROBOTSTXT_OBEY": True,
        "FEEDS": {
            "historical_draws_raw.json": {
                "format": "json",
                "overwrite": True,
                "indent": 2,
            }
        },
    }

    def start_requests(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        catalog_path = os.path.join(base_dir, "catalog.json")

        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        for game in catalog.get("games", []):
            year_url = game.get("year_url")
            if not year_url:
                continue

            yield scrapy.Request(
                url=year_url,
                callback=self.parse,
                meta={
                    "game_slug": game.get("game_slug"),
                    "game_name": game.get("game_name"),
                    "state_slug": game.get("state_slug"),
                    "state_name": game.get("state_name"),
                    "game_type": game.get("type"),
                    "base_url": game.get("url"),
                    "year_url": game.get("year_url"),
                }
            )

    def parse(self, response):
        page_title = response.css("title::text").get(default="").strip()

        rows = response.css("table tr")

        for i, row in enumerate(rows):
            cells = row.css("th::text, td::text, th *::text, td *::text").getall()
            clean_cells = [x.strip() for x in cells if x.strip()]

            if not clean_cells:
                continue

            yield {
                "source_url": response.url,
                "page_title": page_title,
                "game_type": response.meta.get("game_type"),
                "state_slug": response.meta.get("state_slug"),
                "state_name": response.meta.get("state_name"),
                "game_slug": response.meta.get("game_slug"),
                "game_name": response.meta.get("game_name"),
                "base_url": response.meta.get("base_url"),
                "year_url": response.meta.get("year_url"),
                "row_index": i,
                "cells": clean_cells,
            }