import json
from collections import defaultdict

RAW_INPUT = "latest_results_raw.json"
HIST_INPUT = "historical_draws_clean.json"
OUTPUT_FILE = "latest_results.json"

SPECIAL_RAW_GAMES = {"powerball", "mega-millions"}


def clean_num_list(values):
    out = []
    for v in values or []:
        s = str(v).strip()
        if s.isdigit():
            out.append(s)
    return out


def group_key(item):
    return (
        item.get("state_slug"),
        item.get("game_slug"),
    )


def build_from_historical_row(row):
    return {
        "source_url": row.get("source_url"),
        "base_url": row.get("source_url"),
        "numbers_url": None,
        "year_url": row.get("source_url"),
        "page_title": row.get("game_name"),
        "game_type": row.get("game_type"),
        "state_slug": row.get("state_slug"),
        "state_name": row.get("state_name"),
        "game_slug": row.get("game_slug"),
        "game_name": row.get("game_name"),
        "draw_date": row.get("draw_date"),
        "main_numbers": clean_num_list(row.get("main_numbers")),
        "bonus_number": (
            str(row.get("bonus_number")).strip()
            if row.get("bonus_number") not in (None, "")
            else None
        ),
        "multiplier": row.get("multiplier"),
        "secondary_draws": [],
        "jackpot": row.get("prize_text") or row.get("jackpot") or "",
    }


def build_from_raw_row(row):
    return {
        "source_url": row.get("source_url"),
        "base_url": row.get("base_url"),
        "numbers_url": row.get("numbers_url"),
        "year_url": row.get("year_url"),
        "page_title": row.get("page_title"),
        "game_type": row.get("game_type"),
        "state_slug": row.get("state_slug"),
        "state_name": row.get("state_name"),
        "game_slug": row.get("game_slug"),
        "game_name": row.get("game_name"),
        "draw_date": row.get("draw_date"),
        "main_numbers": clean_num_list(row.get("main_numbers")),
        "bonus_number": (
            str(row.get("bonus_number")).strip()
            if row.get("bonus_number") not in (None, "")
            else None
        ),
        "multiplier": row.get("multiplier"),
        "secondary_draws": row.get("secondary_draws") or [],
        "jackpot": row.get("jackpot") or "",
    }


with open(HIST_INPUT, "r", encoding="utf-8") as f:
    historical = json.load(f)

grouped_hist = defaultdict(list)
for row in historical:
    if row.get("game_slug"):
        grouped_hist[group_key(row)].append(row)

latest_results = []

# Base principal: todos los juegos salen de históricos limpios
for key, rows in grouped_hist.items():
    rows_sorted = sorted(rows, key=lambda x: x.get("row_index", 999999))
    first = rows_sorted[0]
    latest_results.append(build_from_historical_row(first))

# Overlay: juegos especiales salen del latest raw scrapeado
try:
    with open(RAW_INPUT, "r", encoding="utf-8") as f:
        raw_latest = json.load(f)

    raw_map = {}
    for row in raw_latest:
        game_slug = row.get("game_slug")
        if game_slug in SPECIAL_RAW_GAMES:
            raw_map[group_key(row)] = build_from_raw_row(row)

    merged = []
    for row in latest_results:
        key = group_key(row)
        if key in raw_map:
            merged.append(raw_map[key])
        else:
            merged.append(row)

    latest_results = merged

except FileNotFoundError:
    pass

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(latest_results, f, indent=2, ensure_ascii=False)

print(f"Archivo creado: {OUTPUT_FILE}")
print(f"Juegos procesados: {len(latest_results)}")