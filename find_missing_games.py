import json

with open("inventory.json", "r", encoding="utf-8") as f:
    inventory = json.load(f)

with open("catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)

catalog_slugs = set()
for game in catalog.get("games", []):
    slug = game.get("game_slug")
    if slug:
        catalog_slugs.add(slug)

inventory_paths = set()
for item in inventory:
    url = item.get("url", "")
    if "lotteryusa.com/" not in url:
        continue

    path = url.split("lotteryusa.com/")[-1].strip("/")
    if not path:
        continue

    parts = path.split("/")

    if len(parts) >= 2:
        inventory_paths.add((parts[0], parts[1]))
    elif len(parts) == 1:
        inventory_paths.add((parts[0], None))

print("=== Juegos en catalog.json ===")
print(len(catalog_slugs))

print("\n=== Posibles juegos encontrados en inventory.json ===")
possible_games = sorted([x for x in inventory_paths if x[1] not in (None, "year", "numbers", "jackpots", "archive", "prizes", "odds", "how-to-play", "faq", "faqs", "winners", "annuity-cash-converter", "annuity-payment-schedule", "history", "jackpot-tax", "double-play", "power-play", "cash-value")])

for state_slug, game_slug in possible_games[:500]:
    print(f"{state_slug} / {game_slug}")

print("\n=== Juegos probablemente faltantes en catalog ===")
missing = []
for state_slug, game_slug in possible_games:
    if game_slug and game_slug not in catalog_slugs:
        missing.append((state_slug, game_slug))

for state_slug, game_slug in missing[:300]:
    print(f"{state_slug} / {game_slug}")

print(f"\nTotal posibles faltantes: {len(missing)}")