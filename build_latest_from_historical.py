import json
from collections import defaultdict

INPUT_FILE = "historical_draws_clean.json"
OUTPUT_FILE = "latest_results.json"


def group_key(item):
    return (
        item.get("state_slug"),
        item.get("game_slug"),
        item.get("source_url") or item.get("base_url"),
    )


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

grouped = defaultdict(list)

for item in data:
    if item.get("game_slug"):
        grouped[group_key(item)].append(item)

latest_results = []

for key, rows in grouped.items():
    rows = sorted(rows, key=lambda x: x.get("row_index", 999999))
    first = rows[0]

    latest_results.append({
        "source_url": first.get("source_url"),
        "base_url": first.get("source_url") or first.get("base_url"),
        "year_url": first.get("source_url"),
        "page_title": first.get("game_name"),
        "game_type": first.get("game_type"),
        "state_slug": first.get("state_slug"),
        "state_name": first.get("state_name"),
        "game_slug": first.get("game_slug"),
        "game_name": first.get("game_name"),
        "draw_date": first.get("draw_date"),
        "main_numbers": first.get("main_numbers", []),
        "bonus_label": first.get("bonus_label"),
        "bonus_number": first.get("bonus_number"),
        "multiplier": first.get("multiplier"),
        "secondary_draws": first.get("secondary_draws", []),
        "jackpot": first.get("prize_text") or first.get("jackpot"),
    })

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(latest_results, f, indent=2, ensure_ascii=False)

print(f"Archivo creado: {OUTPUT_FILE}")
print(f"Juegos procesados: {len(latest_results)}")