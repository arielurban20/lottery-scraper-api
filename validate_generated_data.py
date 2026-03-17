import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FILES = {
    "catalog": ROOT / "catalog.json",
    "latest": ROOT / "latest_results.json",
    "historical": ROOT / "historical_draws_clean.json",
    "stats": ROOT / "number_stats.json",
}

REQUIRED_GAME_SLUGS = {
    "powerball",
    "mega-millions",
    "cash4life",
    "lotto-america",
    "lucky-for-life",
}

def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path.name}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def fail(msg: str):
    print(f"VALIDATION FAILED: {msg}")
    sys.exit(1)

def main():
    try:
        catalog = load_json(FILES["catalog"])
        latest = load_json(FILES["latest"])
        historical = load_json(FILES["historical"])
        stats = load_json(FILES["stats"])
    except Exception as e:
        fail(str(e))

    games = catalog.get("games", [])
    states = catalog.get("states", [])

    if not isinstance(games, list) or len(games) < 100:
        fail("catalog.json has too few games")

    if not isinstance(states, list) or len(states) < 10:
        fail("catalog.json has too few states")

    if not isinstance(latest, list) or len(latest) < 100:
        fail("latest_results.json has too few records")

    if not isinstance(historical, list) or len(historical) < 1000:
        fail("historical_draws_clean.json has too few records")

    if not isinstance(stats, list) or len(stats) < 100:
        fail("number_stats.json has too few records")

    game_slugs = {g.get("game_slug") for g in games if g.get("game_slug")}
    missing = REQUIRED_GAME_SLUGS - game_slugs
    if missing:
        fail(f"Missing important games in catalog: {sorted(missing)}")

    latest_slugs = {r.get("game_slug") for r in latest if r.get("game_slug")}
    missing_latest = REQUIRED_GAME_SLUGS - latest_slugs
    if missing_latest:
        fail(f"Missing important games in latest_results: {sorted(missing_latest)}")

    non_empty_main = 0
    for row in latest:
        nums = row.get("main_numbers")
        if isinstance(nums, list) and len(nums) > 0:
            non_empty_main += 1

    if non_empty_main < 50:
        fail("Too many latest result rows have empty main_numbers")

    print("VALIDATION PASSED")
    print(f"Games: {len(games)}")
    print(f"States: {len(states)}")
    print(f"Latest rows: {len(latest)}")
    print(f"Historical rows: {len(historical)}")
    print(f"Stats rows: {len(stats)}")

if __name__ == "__main__":
    main()