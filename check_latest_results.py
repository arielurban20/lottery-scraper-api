import json

INPUT_FILE = "latest_results.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

good = []
bad = []

for item in data:
    main_numbers = item.get("main_numbers") or []
    draw_date = item.get("draw_date") or ""

    if main_numbers and draw_date.strip():
        good.append(item)
    else:
        bad.append(item)

print(f"Total registros: {len(data)}")
print(f"Con datos buenos: {len(good)}")
print(f"Con datos vacíos o incompletos: {len(bad)}")

print("\nPrimeros 15 incompletos:\n")
for item in bad[:15]:
    print({
        "game_name": item.get("game_name"),
        "state_name": item.get("state_name"),
        "source_url": item.get("source_url"),
        "base_url": item.get("base_url"),
        "numbers_url": item.get("numbers_url"),
        "draw_date": item.get("draw_date"),
        "main_numbers": item.get("main_numbers"),
        "bonus_number": item.get("bonus_number"),
        "multiplier": item.get("multiplier"),
    })