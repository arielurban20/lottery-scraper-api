import json
from urllib.parse import urlparse

INPUT_FILE = "cwf_generated.json"
OUTPUT_FILE = "catalog.json"

INVALID_ROOTS = {
    "about-us", "authors", "contact-us", "cookies", "copyright-policy",
    "daily-games", "faqs", "jackpots", "login", "lottery-predictions",
    "news", "numbers", "play-online", "privacy-policy", "quick-picks",
    "register", "search", "topics", "where-to", "whereto", "xs-and-os",
}

INVALID_EXTRA_SEGMENTS = {
    "annuity-cash-converter",
    "annuity-payment-schedule",
    "cash-value",
    "combinations",
    "double-play",
    "faq",
    "faqs",
    "history",
    "how-to-play",
    "jackpot-tax",
    "jackpots",
    "numbers",
    "odds",
    "power-play",
    "prizes",
    "promos",
    "quick-picks",
    "results",
    "winners",
}

WEEKDAY_SEGMENTS = {
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday"
}

def slug_to_name(slug: str) -> str:
    return slug.replace("-", " ").title()

def load_urls():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [u["loc"] for u in data["urlset"]["url"] if "loc" in u]

def main():
    urls = load_urls()

    states = {}
    games = {}

    for url in urls:
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if not path:
            continue

        parts = path.split("/")
        root = parts[0]

        if root in INVALID_ROOTS:
            continue

        # Caso 1: raíz tipo /powerball/ o /gimme-5/
        if len(parts) == 1:
            games[("multistate", None, root)] = {
                "type": "multistate",
                "state_slug": None,
                "state_name": None,
                "game_slug": root,
                "game_name": slug_to_name(root),
                "url": f"{parsed.scheme}://{parsed.netloc}/{root}/",
                "title": slug_to_name(root),
                "year_url": None,
            }
            continue

        # Caso 2: /powerball/year
        if len(parts) == 2 and parts[1] == "year" and root not in WEEKDAY_SEGMENTS:
            key = ("multistate", None, root)
            if key not in games:
                games[key] = {
                    "type": "multistate",
                    "state_slug": None,
                    "state_name": None,
                    "game_slug": root,
                    "game_name": slug_to_name(root),
                    "url": f"{parsed.scheme}://{parsed.netloc}/{root}/",
                    "title": slug_to_name(root),
                    "year_url": None,
                }
            games[key]["year_url"] = url
            continue

        # Caso 3: /estado/
        if len(parts) == 1:
            states[root] = {
                "slug": root,
                "name": slug_to_name(root),
                "url": f"{parsed.scheme}://{parsed.netloc}/{root}/",
            }
            continue

        # Ignorar días sueltos /estado/monday
        if len(parts) == 2 and parts[1] in WEEKDAY_SEGMENTS:
            if root not in states:
                states[root] = {
                    "slug": root,
                    "name": slug_to_name(root),
                    "url": f"{parsed.scheme}://{parsed.netloc}/{root}/",
                }
            continue

        # Caso 4: /estado/juego/
        if len(parts) >= 2:
            state_slug = root
            game_slug = parts[1]

            if game_slug in INVALID_EXTRA_SEGMENTS or game_slug in WEEKDAY_SEGMENTS:
                continue

            if state_slug not in states:
                states[state_slug] = {
                    "slug": state_slug,
                    "name": slug_to_name(state_slug),
                    "url": f"{parsed.scheme}://{parsed.netloc}/{state_slug}/",
                }

            key = ("state_game", state_slug, game_slug)

            if key not in games:
                games[key] = {
                    "type": "state_game",
                    "state_slug": state_slug,
                    "state_name": slug_to_name(state_slug),
                    "game_slug": game_slug,
                    "game_name": slug_to_name(game_slug),
                    "url": f"{parsed.scheme}://{parsed.netloc}/{state_slug}/{game_slug}/",
                    "title": slug_to_name(game_slug),
                    "year_url": None,
                }

            if len(parts) >= 3 and parts[2] == "year":
                games[key]["year_url"] = url

    result = {
        "states": sorted(states.values(), key=lambda x: x["name"]),
        "games": sorted(
            games.values(),
            key=lambda x: ((x["state_name"] or ""), x["game_name"], x["game_slug"])
        ),
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Catálogo creado: {OUTPUT_FILE}")
    print(f"Estados: {len(result['states'])}")
    print(f"Juegos: {len(result['games'])}")

if __name__ == "__main__":
    main()