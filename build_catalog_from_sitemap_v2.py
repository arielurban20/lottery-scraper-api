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

INVALID_SEGMENTS = {
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

WEEKDAYS = {
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday"
}

US_STATE_LIKE = {
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

def slug_to_name(slug: str) -> str:
    return slug.replace("-", " ").title()

with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
    data = json.load(f)

urls = [u["loc"] for u in data["urlset"]["url"] if "loc" in u]

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

    # guardar estados
    if len(parts) == 1 and root in US_STATE_LIKE:
        states[root] = {
            "slug": root,
            "name": slug_to_name(root),
            "url": f"{parsed.scheme}://{parsed.netloc}/{root}/"
        }
        continue

    # ignorar /estado/lunes etc
    if len(parts) == 2 and root in US_STATE_LIKE and parts[1] in WEEKDAYS:
        if root not in states:
            states[root] = {
                "slug": root,
                "name": slug_to_name(root),
                "url": f"{parsed.scheme}://{parsed.netloc}/{root}/"
            }
        continue

    # multistate: /2by2/ o /2by2/year
    if root not in US_STATE_LIKE:
        game_slug = root
        if game_slug in INVALID_SEGMENTS:
            continue

        key = ("multistate", None, game_slug)
        if key not in games:
            games[key] = {
                "type": "multistate",
                "state_slug": None,
                "state_name": None,
                "game_slug": game_slug,
                "game_name": slug_to_name(game_slug),
                "url": f"{parsed.scheme}://{parsed.netloc}/{game_slug}/",
                "title": slug_to_name(game_slug),
                "year_url": None,
            }

        if len(parts) >= 2 and parts[1] == "year":
            games[key]["year_url"] = url
        continue

    # state game: /puerto-rico/pega-2/ o /puerto-rico/pega-2/year
    if len(parts) >= 2 and root in US_STATE_LIKE:
        state_slug = root
        game_slug = parts[1]

        if game_slug in INVALID_SEGMENTS or game_slug in WEEKDAYS:
            continue

        if state_slug not in states:
            states[state_slug] = {
                "slug": state_slug,
                "name": slug_to_name(state_slug),
                "url": f"{parsed.scheme}://{parsed.netloc}/{state_slug}/"
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
    "games": sorted(games.values(), key=lambda x: ((x["state_name"] or ""), x["game_name"], x["game_slug"]))
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Catálogo creado: {OUTPUT_FILE}")
print(f"Estados: {len(result['states'])}")
print(f"Juegos: {len(result['games'])}")