import json
import os
import re
import scrapy


def clean_token(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def clean_tokens(tokens):
    return [clean_token(t) for t in tokens if clean_token(t)]


BONUS_BALL_RULES = {
    # game_slug: number of main balls before bonus ball
    "powerball": 5,
    "mega-millions": 5,
    "cash4life": 5,
    "millionaire-for-life": 5,
    "lucky-for-life": 5,
    # state-specific
    "cash-5:new-jersey": 4,
}


def get_bonus_rule(game_slug, state_slug):
    state_key = f"{game_slug}:{state_slug}" if state_slug else game_slug
    if state_key in BONUS_BALL_RULES:
        return BONUS_BALL_RULES[state_key]
    return BONUS_BALL_RULES.get(game_slug)


def parse_draw_section(tokens, main_ball_count=5):
    nums = [t for t in tokens if t.isdigit()]
    main_numbers = nums[:main_ball_count]
    bonus_number = nums[main_ball_count] if len(nums) > main_ball_count else None
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

    main_parsed = parse_draw_section(main_section, main_ball_count=5) if main_section else {
        "main_numbers": [],
        "bonus_number": None,
        "multiplier": None,
    }

    double_parsed = parse_draw_section(double_section, main_ball_count=5) if double_section else {
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


def parse_bonus_ball_game(latest_card, response, game_slug, state_slug):
    main_ball_count = get_bonus_rule(game_slug, state_slug)

    # 1) principales del latest card
    nums = latest_card.css("li.c-ball::text").getall()
    nums = [clean_token(x) for x in nums if clean_token(x).isdigit()]

    # 2) bonus explícito en latest card
    explicit_bonus = latest_card.css("li.c-result__bonus::text").get()
    explicit_bonus = clean_token(explicit_bonus) if explicit_bonus else None
    if explicit_bonus and not explicit_bonus.isdigit():
        explicit_bonus = None

    # 3) fallback global para bonus explícito
    if not explicit_bonus:
        explicit_bonus = response.css("ul.c-result li.c-result__bonus::text").get()
        explicit_bonus = clean_token(explicit_bonus) if explicit_bonus else None
        if explicit_bonus and not explicit_bonus.isdigit():
            explicit_bonus = None

    # Caso ideal: 5 principales + bonus separado explícito
    if main_ball_count and len(nums) >= main_ball_count and explicit_bonus:
        return {
            "main_numbers": nums[:main_ball_count],
            "bonus_number": explicit_bonus,
        }

    # Fallback: si la lista ya trae la bonus incluida
    if main_ball_count and len(nums) >= main_ball_count + 1:
        return {
            "main_numbers": nums[:main_ball_count],
            "bonus_number": nums[main_ball_count],
        }

    # Fallback global de bolas
    global_nums = response.css("ul.c-result li.c-ball::text").getall()
    global_nums = [clean_token(x) for x in global_nums if clean_token(x).isdigit()]

    if main_ball_count and len(global_nums) >= main_ball_count and explicit_bonus:
        return {
            "main_numbers": global_nums[:main_ball_count],
            "bonus_number": explicit_bonus,
        }

    if main_ball_count and len(global_nums) >= main_ball_count + 1:
        return {
            "main_numbers": global_nums[:main_ball_count],
            "bonus_number": global_nums[main_ball_count],
        }

    return {
        "main_numbers": nums or global_nums,
        "bonus_number": explicit_bonus,
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

        fast_game_slugs_env = os.getenv("FAST_GAME_SLUGS", "").strip()
        fast_game_slugs = {
            slug.strip() for slug in fast_game_slugs_env.split(",") if slug.strip()
        }

        for game in catalog.get("games", []):
            game_slug = game.get("game_slug")

            if fast_game_slugs and game_slug not in fast_game_slugs:
                continue

            if game_slug in {"powerball", "mega-millions"}:
                target_url = game.get("url") or game.get("numbers_url")
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

        next_draw_date = None
        next_draw_time = None
        next_estimated_jackpot = None

        all_text = clean_tokens(response.css("*::text").getall())

        for i, token in enumerate(all_text):
            lower = token.lower()

            if "next draw" in lower:
                if i + 1 < len(all_text):
                    possible = all_text[i + 1].strip()
                    if possible and len(possible) < 80:
                        next_draw_date = possible

            if "today at" in lower or "tomorrow at" in lower:
                next_draw_time = token.strip()

            if (
                "est. jackpot" in lower
                or "estimated jackpot" in lower
                or "next est. jackpot" in lower
            ):
                if i + 1 < len(all_text):
                    possible = all_text[i + 1].strip()
                    if possible:
                        next_estimated_jackpot = possible

        latest_card = response.xpath("(//div[contains(@class,'c-draw-card')])[1]")

        draw_date_parts = latest_card.css(".c-draw-card__date *::text").getall()
        draw_date = " ".join(x.strip() for x in draw_date_parts if x.strip())

        secondary_draws = []
        main_numbers = []
        bonus_number = None
        multiplier = None

        game_slug = response.meta.get("game_slug")
        state_slug = response.meta.get("state_slug")

        if game_slug == "powerball":
            parsed_powerball = split_powerball_latest_card(latest_card)
            main_numbers = parsed_powerball["main_numbers"]
            bonus_number = parsed_powerball["bonus_number"]
            multiplier = parsed_powerball["multiplier"]
            secondary_draws = parsed_powerball["secondary_draws"]

        elif get_bonus_rule(game_slug, state_slug):
            parsed_bonus_game = parse_bonus_ball_game(
                latest_card, response, game_slug, state_slug
            )
            main_numbers = parsed_bonus_game["main_numbers"]
            bonus_number = parsed_bonus_game["bonus_number"]

            multiplier = latest_card.css("li.c-result__multiplier::text").get()
            if not multiplier:
                multiplier = response.css("li.c-result__multiplier::text").get()

        else:
            main_numbers = latest_card.css("li.c-ball::text").getall()
            bonus_number = latest_card.css("li.c-result__bonus::text").get()
            multiplier = latest_card.css("li.c-result__multiplier::text").get()

        jackpot_parts = latest_card.css(".c-draw-card__prize *::text").getall()
        jackpot = " ".join(x.strip() for x in jackpot_parts if x.strip())

        if not main_numbers and not get_bonus_rule(game_slug, state_slug):
            main_numbers = response.css("ul.c-result li.c-ball::text").getall()

        if not bonus_number and not get_bonus_rule(game_slug, state_slug):
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
            "next_draw_date": next_draw_date,
            "next_draw_time": next_draw_time,
            "next_estimated_jackpot": next_estimated_jackpot,
        }