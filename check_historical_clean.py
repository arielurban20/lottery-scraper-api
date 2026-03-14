import json

INPUT_FILE = "historical_draws_clean.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total registros limpios: {len(data)}")

with_numbers = 0
with_bonus = 0
without_numbers = 0

for item in data:
    if item.get("main_numbers"):
        with_numbers += 1
    else:
        without_numbers += 1

    if item.get("bonus_number"):
        with_bonus += 1

print(f"Con números principales: {with_numbers}")
print(f"Sin números principales: {without_numbers}")
print(f"Con bonus: {with_bonus}")

print("\nPrimeros 10 registros:\n")
for item in data[:10]:
    print({
        "game_name": item.get("game_name"),
        "state_name": item.get("state_name"),
        "draw_date": item.get("draw_date"),
        "main_numbers": item.get("main_numbers"),
        "bonus_label": item.get("bonus_label"),
        "bonus_number": item.get("bonus_number"),
        "multiplier": item.get("multiplier"),
        "prize_text": item.get("prize_text"),
    })