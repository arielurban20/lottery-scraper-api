import json
import os
import scrapy


class LatestFromCatalogSpider(scrapy.Spider):
    name = "latest_from_catalog"
    allowed_domains = ["lotteryusa.com"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "ROBOTSTXT_OBEY": True,
        "FEEDS": {
            "latest_results.json": {
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
            # Elegir la mejor URL disponible
            target_url = (
                game.get("numbers_url")
                or game.get("url")
            )

            if not target_url:
                continue

            yield scrapy.Request(
                url=target_url,
                callback=self.parse,
                meta={
                    "game_slug": game.get("game_slug"),
                    "game_name": game.get("game_name"),
                    "state_slug": game.get("state_slug"),
                    "state_name": game.get("state_name"),
                    "game_type": game.get("type"),
                    "base_url": game.get("url"),
                    "numbers_url": game.get("numbers_url"),
                    "year_url": game.get("year_url"),
                }
            )

    def parse(self, response):
        page_title = response.css("title::text").get(default="").strip()

        # Intento 1: primer bloque tipo c-draw-card
        latest_card = response.xpath("(//div[contains(@class,'c-draw-card')])[1]")

        draw_date_parts = latest_card.css(".c-draw-card__date *::text").getall()
        draw_date = " ".join(x.strip() for x in draw_date_parts if x.strip())

        main_numbers = latest_card.css("li.c-ball::text").getall()
        bonus_number = latest_card.css("li.c-result__bonus::text").get()
        multiplier = latest_card.css("li.c-result__multiplier::text").get()

        jackpot_parts = latest_card.css(".c-draw-card__prize *::text").getall()
        jackpot = " ".join(x.strip() for x in jackpot_parts if x.strip())

        # Intento 2: buscar en cualquier bloque c-result si el primero salió vacío
        if not main_numbers:
            main_numbers = response.css("ul.c-result li.c-ball::text").getall()

        if not bonus_number:
            bonus_number = response.css("ul.c-result li.c-result__bonus::text").get()

        if not multiplier:
            multiplier = response.css("ul.c-result li.c-result__multiplier::text").get()

        # Intento 3: fallback para fecha
        if not draw_date:
            possible_date_parts = response.css(".c-draw-card__date::text, .c-draw-card__date *::text").getall()
            draw_date = " ".join(x.strip() for x in possible_date_parts if x.strip())

        # Intento 4: fallback para jackpot
        if not jackpot:
            possible_jackpot_parts = response.css(".c-draw-card__prize::text, .c-draw-card__prize *::text").getall()
            jackpot = " ".join(x.strip() for x in possible_jackpot_parts if x.strip())

        yield {
            "source_url": response.url,
            "base_url": response.meta.get("base_url"),
            "numbers_url": response.meta.get("numbers_url"),
            "year_url": response.meta.get("year_url"),
            "page_title": page_title,
            "game_type": response.meta.get("game_type"),
            "state_slug": response.meta.get("state_slug"),
            "state_name": response.meta.get("state_name"),
            "game_slug": response.meta.get("game_slug"),
            "game_name": response.meta.get("game_name"),
            "draw_date": draw_date,
            "main_numbers": main_numbers,
            "bonus_number": bonus_number,
            "multiplier": multiplier,
            "jackpot": jackpot,
        }