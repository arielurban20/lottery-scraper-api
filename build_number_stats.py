import json
from collections import Counter, defaultdict

INPUT_FILE = "historical_draws_clean.json"
OUTPUT_FILE = "number_stats.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

stats = defaultdict(lambda: {
    "draw_count": 0,
    "main_counter": Counter(),
    "bonus_counter": Counter(),
})

for item in data:
    key = (
        item.get("state_slug"),
        item.get("state_name"),
        item.get("game_slug"),
        item.get("game_name"),
    )

    stats[key]["draw_count"] += 1

    for n in item.get("main_numbers", []):
        stats[key]["main_counter"][str(n)] += 1

    bonus = item.get("bonus_number")
    if bonus:
        stats[key]["bonus_counter"][str(bonus)] += 1

result = []

for key, value in stats.items():
    state_slug, state_name, game_slug, game_name = key

    most_main = value["main_counter"].most_common(20)
    least_main = sorted(value["main_counter"].items(), key=lambda x: (x[1], int(x[0])))[:20]

    most_bonus = value["bonus_counter"].most_common(20)
    least_bonus = sorted(value["bonus_counter"].items(), key=lambda x: (x[1], int(x[0])))[:20]

    result.append({
        "state_slug": state_slug,
        "state_name": state_name,
        "game_slug": game_slug,
        "game_name": game_name,
        "draw_count": value["draw_count"],
        "most_frequent_main": [{"number": n, "count": c} for n, c in most_main],
        "least_frequent_main": [{"number": n, "count": c} for n, c in least_main],
        "most_frequent_bonus": [{"number": n, "count": c} for n, c in most_bonus],
        "least_frequent_bonus": [{"number": n, "count": c} for n, c in least_bonus],
    })

result.sort(key=lambda x: ((x["state_name"] or ""), x["game_name"] or ""))

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Archivo creado: {OUTPUT_FILE}")
print(f"Juegos analizados: {len(result)}")

print("\nPrimeros 5 juegos:\n")
for row in result[:5]:
    print({
        "game_name": row["game_name"],
        "state_name": row["state_name"],
        "draw_count": row["draw_count"],
        "most_frequent_main": row["most_frequent_main"][:5],
        "least_frequent_main": row["least_frequent_main"][:5],
    })