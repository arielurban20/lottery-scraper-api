import json
import os
import re
import scrapy


def clean_token(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def clean_tokens(tokens):
    return [clean_token(t) for t in tokens if clean_token(t)]


def parse_draw_section(tokens):
    nums = [t for t in tokens if t.isdigit()]
    main_numbers = nums[:5]
    bonus_number = nums[5] if len(nums) > 5 else None
    multiplier = next((t for t in tokens if "power play" in t.lower()), None)
    return {
        "main_numbers": main_numbers,
        "bonus_number": bonus_number,
        "multiplier": multiplier,
    }


def split_powerball_latest_card(latest_card):
    tokens = clean_tokens(latest_card.css("*::text").getall())
    lower_tokens = [t.lower() for t in tokens]

    def find_index(label):
        for idx, value in enumerate(lower_tokens):
            if value == label:
                return idx
        return -1

    main_idx = find_index("main draw")
    double_idx = find_index("double play")

    main_section = []
    double_section = []

    if main_idx != -1:
        end_main = double_idx if double_idx != -1 else len(tokens)
        main_section = tokens[main_idx + 1:end_main]

    if double_idx != -1:
        end_double = len(tokens)
        stop_labels = {
            "prizes",
            "did i win?",
            "see more numbers",
            "powerball tools",
            "next powerball draw",
            "next est. jackpot",
            "add to favorites",
        }
        for i in range(double_idx + 1, len(tokens)):
            if lower_tokens[i] in stop_labels:
                end_double = i
                break
        double_section = tokens[double_idx + 1:end_double]

    main_parsed = parse_draw_section(main_section) if main_section else {
        "main_numbers": [],
        "bonus_number": None,
        "multiplier": None,
    }

    double_parsed = parse_draw_section(double_section) if double_section else {
        "main_numbers": [],
        "bonus_number": None,
        "multiplier": None,
    }

    secondary_draws = []
    if double_parsed["main_numbers"]:
        secondary_draws.append({
            "draw_type": "double-play",
            "main_numbers": double_parsed["main_numbers"],
            "bonus_number": double_parsed["bonus_number"],
        })

    return {
        "main_numbers": main_parsed["main_numbers"],
        "bonus_number": main_parsed["bonus_number"],
        "multiplier": main_parsed["multiplier"],
        "secondary_draws": secondary_draws,
    }


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
            game_slug = game.get("game_slug")

            if game_slug == "powerball":
                target_url = "https://www.lotteryusa.com/powerball/"
            elif game_slug == "mega-millions":
                target_url = "https://www.lotteryusa.com/mega-millions/"
            else:
                target_url = game.get("numbers_url") or game.get("url")

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

        latest_card = response.xpath("(//div[contains(@class,'c-draw-card')])[1]")

        draw_date_parts = latest_card.css(".c-draw-card__date *::text").getall()
        draw_date = " ".join(x.strip() for x in draw_date_parts if x.strip())

        secondary_draws = []

        if response.meta.get("game_slug") == "powerball":
            parsed_powerball = split_powerball_latest_card(latest_card)
            main_numbers = parsed_powerball["main_numbers"]
            bonus_number = parsed_powerball["bonus_number"]
            multiplier = parsed_powerball["multiplier"]
            secondary_draws = parsed_powerball["secondary_draws"]
        else:
            main_numbers = latest_card.css("li.c-ball::text").getall()
            bonus_number = latest_card.css("li.c-result__bonus::text").get()
            multiplier = latest_card.css("li.c-result__multiplier::text").get()

        jackpot_parts = latest_card.css(".c-draw-card__prize *::text").getall()
        jackpot = " ".join(x.strip() for x in jackpot_parts if x.strip())

        if not main_numbers:
            main_numbers = response.css("ul.c-result li.c-ball::text").getall()

        if not bonus_number:
            bonus_number = response.css("ul.c-result li.c-result__bonus::text").get()

        if not multiplier:
            multiplier = response.css("ul.c-result li.c-result__multiplier::text").get()

        if not draw_date:
            possible_date_parts = response.css(
                ".c-draw-card_date::text, .c-draw-card_date *::text"
            ).getall()
            draw_date = " ".join(x.strip() for x in possible_date_parts if x.strip())

        if not jackpot:
            possible_jackpot_parts = response.css(
                ".c-draw-card_prize::text, .c-draw-card_prize *::text"
            ).getall()
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
            "secondary_draws": secondary_draws,
            "jackpot": jackpot,
        }