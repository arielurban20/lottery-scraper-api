import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
HISTORICAL_PATH = BASE_DIR / "historical_draws_clean.json"
RAW_LATEST_PATH = BASE_DIR / "latest_results_raw.json"
OUTPUT_PATH = BASE_DIR / "latest_results.json"

SPECIAL_RAW_KEYS = {
    "powerball",
    "mega-millions",
    "cash4life",
    "millionaire-for-life",
    "lucky-for-life",
    "cash-5:new-jersey",
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def make_key(item):
    game_slug = item.get("game_slug")
    state_slug = item.get("state_slug")
    if state_slug:
        return f"{game_slug}:{state_slug}"
    return game_slug


def normalize_raw_item(item):
    return {
        "source_url": item.get("source_url"),
        "base_url": item.get("base_url"),
        "numbers_url": item.get("numbers_url"),
        "year_url": item.get("year_url"),
        "page_title": item.get("page_title"),
        "game_type": item.get("game_type"),
        "state_slug": item.get("state_slug"),
        "state_name": item.get("state_name"),
        "game_slug": item.get("game_slug"),
        "game_name": item.get("game_name"),
        "draw_date": item.get("draw_date"),
        "main_numbers": item.get("main_numbers") or [],
        "bonus_number": item.get("bonus_number"),
        "multiplier": item.get("multiplier"),
        "secondary_draws": item.get("secondary_draws") or [],
        "jackpot": item.get("jackpot"),
        "next_draw_date": item.get("next_draw_date"),
        "next_draw_time": item.get("next_draw_time"),
        "next_estimated_jackpot": item.get("next_estimated_jackpot"),
    }


def normalize_historical_item(item):
    return {
        "source_url": item.get("source_url"),
        "base_url": item.get("base_url"),
        "numbers_url": item.get("numbers_url"),
        "year_url": item.get("year_url"),
        "page_title": item.get("page_title"),
        "game_type": item.get("game_type"),
        "state_slug": item.get("state_slug"),
        "state_name": item.get("state_name"),
        "game_slug": item.get("game_slug"),
        "game_name": item.get("game_name"),
        "draw_date": item.get("draw_date"),
        "main_numbers": item.get("main_numbers") or [],
        "bonus_number": item.get("bonus_number"),
        "multiplier": item.get("multiplier"),
        "secondary_draws": item.get("secondary_draws") or [],
        "jackpot": item.get("jackpot"),
        "next_draw_date": item.get("next_draw_date"),
        "next_draw_time": item.get("next_draw_time"),
        "next_estimated_jackpot": item.get("next_estimated_jackpot"),
    }


def main():
    historical = load_json(HISTORICAL_PATH, [])
    raw_latest = load_json(RAW_LATEST_PATH, [])

    latest_by_key = {}

    for item in historical:
        key = make_key(item)
        if key not in latest_by_key:
            latest_by_key[key] = normalize_historical_item(item)

    for item in raw_latest:
        key = make_key(item)
        if key in SPECIAL_RAW_KEYS:
            latest_by_key[key] = normalize_raw_item(item)
        elif key not in latest_by_key:
            latest_by_key[key] = normalize_raw_item(item)

    latest_results = list(latest_by_key.values())

    latest_results.sort(
        key=lambda x: (
            x.get("game_slug") or "",
            x.get("state_slug") or "",
            x.get("state_name") or "",
        )
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(latest_results, f, ensure_ascii=False, indent=2)

    print(f"Archivo creado: {OUTPUT_PATH.name}")
    print(f"Juegos procesados: {len(latest_results)}")


if __name__ == "__main__":
    main()