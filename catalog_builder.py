import json
from urllib.parse import urlparse

INPUT_FILE = "inventory.json"
OUTPUT_FILE = "catalog.json"

VALID_STATE_SLUGS = {
    "alabama", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "district-of-columbia", "florida", "georgia", "idaho", "illinois",
    "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland",
    "massachusetts", "michigan", "minnesota", "mississippi", "missouri",
    "montana", "nebraska", "new-hampshire", "new-jersey", "new-mexico",
    "new-york", "north-carolina", "north-dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "puerto-rico", "rhode-island", "south-carolina",
    "south-dakota", "tennessee", "texas", "virgin-islands", "virginia",
    "washington", "west-virginia", "wisconsin", "wyoming"
}

MULTISTATE_GAMES = {
    "powerball",
    "mega-millions",
    "cash4life",
    "cash-4-life",
    "lotto-america",
    "lucky-for-life",
    "2by2",
    "gimme-5",
    "gimme5",
    "tri-state-megabucks",
    "tri-state-megabucks-plus",
    "megabucks",
    "millionaire-for-life",
}

INVALID_ROOT_SLUGS = {
    "news",
    "faqs",
    "topics",
    "couriers",
    "about-us",
    "contact-us",
    "glossary",
    "lottery-predictions",
    "play-online",
    "search",
    "where-to",
    "whereto",
    "xs-and-os",
    "cookies",
    "copyright-policy",
    "privacy-policy",
    "register",
}

INVALID_GAME_SLUGS = {
    "jackpots",
    "numbers",
    "year",
    "results",
    "prizes",
    "odds",
    "how-to-play",
    "faq",
    "faqs",
    "winners",
    "annuity-cash-converter",
    "annuity-payment-schedule",
    "history",
    "jackpot-tax",
    "double-play",
    "power-play",
    "cash-value",
    "archive",
    "drawing",
    "drawings",
}

def slug_to_name(slug: str) -> str:
    return slug.replace("-", " ").title()

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    states = {}
    games_map = {}

    for item in data:
        url = item.get("url", "")
        title = item.get("title", "")

        if "lotteryusa.com/" not in url:
            continue

        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if not path:
            continue

        parts = path.split("/")
        root = parts[0]

        if root in INVALID_ROOT_SLUGS:
            continue

        # Caso: juego multistate directo /powerball/
        if len(parts) == 1 and root in MULTISTATE_GAMES:
            key = ("multistate", None, root)

            if key not in games_map:
                games_map[key] = {
                    "type": "multistate",
                    "state_slug": None,
                    "state_name": None,
                    "game_slug": root,
                    "game_name": slug_to_name(root),
                    "url": f"{parsed.scheme}://{parsed.netloc}/{root}/",
                    "title": title,
                    "year_url": None,
                    "numbers_url": None,
                    "jackpots_url": None,
                }
            continue

        # Caso: subpágina de multistate /powerball/year/
        if root in MULTISTATE_GAMES and len(parts) >= 2:
            key = ("multistate", None, root)

            if key not in games_map:
                games_map[key] = {
                    "type": "multistate",
                    "state_slug": None,
                    "state_name": None,
                    "game_slug": root,
                    "game_name": slug_to_name(root),
                    "url": f"{parsed.scheme}://{parsed.netloc}/{root}/",
                    "title": title,
                    "year_url": None,
                    "numbers_url": None,
                    "jackpots_url": None,
                }

            extra = parts[1]
            if extra == "year":
                games_map[key]["year_url"] = url
            elif extra == "numbers":
                games_map[key]["numbers_url"] = url
            elif extra == "jackpots":
                games_map[key]["jackpots_url"] = url

            continue

        # Caso: estado /california/
        if len(parts) == 1 and root in VALID_STATE_SLUGS:
            if root not in states:
                states[root] = {
                    "slug": root,
                    "name": slug_to_name(root),
                    "url": f"{parsed.scheme}://{parsed.netloc}/{root}/",
                }
            continue

        # Caso: /estado/juego/
        if len(parts) >= 2 and root in VALID_STATE_SLUGS:
            state_slug = root
            game_slug = parts[1]

            if game_slug in INVALID_GAME_SLUGS:
                continue

            if state_slug not in states:
                states[state_slug] = {
                    "slug": state_slug,
                    "name": slug_to_name(state_slug),
                    "url": f"{parsed.scheme}://{parsed.netloc}/{state_slug}/",
                }

            key = ("state_game", state_slug, game_slug)

            if key not in games_map:
                games_map[key] = {
                    "type": "state_game",
                    "state_slug": state_slug,
                    "state_name": slug_to_name(state_slug),
                    "game_slug": game_slug,
                    "game_name": slug_to_name(game_slug),
                    "url": f"{parsed.scheme}://{parsed.netloc}/{state_slug}/{game_slug}/",
                    "title": title,
                    "year_url": None,
                    "numbers_url": None,
                    "jackpots_url": None,
                }

            if len(parts) >= 3:
                extra = parts[2]
                if extra == "year":
                    games_map[key]["year_url"] = url
                elif extra == "numbers":
                    games_map[key]["numbers_url"] = url
                elif extra == "jackpots":
                    games_map[key]["jackpots_url"] = url

    result = {
        "states": sorted(states.values(), key=lambda x: x["name"]),
        "games": sorted(games_map.values(), key=lambda x: ((x["state_name"] or ""), x["game_name"]))
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Catálogo creado en: {OUTPUT_FILE}")
    print(f"Estados encontrados: {len(result['states'])}")
    print(f"Juegos encontrados: {len(result['games'])}")

if __name__ == "__main__":
    main()