import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Lottery Scraper API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://lovable.dev",
        "https://www.lovable.dev",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent


def load_json(filename: str):
    file_path = BASE_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {filename}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/")
def root():
    return {
        "message": "Lottery Scraper API running",
        "version": "2.0.0",
        "endpoints": [
            "/api/states",
            "/api/games",
            "/api/latest-results",
            "/api/historical-draws",
            "/api/number-stats",
            "/api/states/{state_slug}/games",
            "/api/states/{state_slug}/latest-results",
            "/api/games/{game_slug}/latest",
            "/api/games/{game_slug}/historical",
            "/api/games/{game_slug}/past-draws",
            "/api/games/{game_slug}/stats",
            "/api/games/{game_slug}/most-frequent",
            "/api/games/{game_slug}/least-frequent",
        ],
    }


@app.get("/api/states")
def get_states():
    data = load_json("catalog.json")
    return data.get("states", [])


@app.get("/api/games")
def get_games(
    state_slug: str | None = Query(default=None),
    game_slug: str | None = Query(default=None),
):
    data = load_json("catalog.json")
    games = data.get("games", [])

    if state_slug:
        games = [g for g in games if g.get("state_slug") == state_slug]

    if game_slug:
        games = [g for g in games if g.get("game_slug") == game_slug]

    return games


@app.get("/api/latest-results")
def get_latest_results(
    state_slug: str | None = Query(default=None),
    game_slug: str | None = Query(default=None),
):
    data = load_json("latest_results.json")

    if state_slug:
        data = [x for x in data if x.get("state_slug") == state_slug]

    if game_slug:
        data = [x for x in data if x.get("game_slug") == game_slug]

    return data


@app.get("/api/historical-draws")
def get_historical_draws(
    state_slug: str | None = Query(default=None),
    game_slug: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=5000),
):
    data = load_json("historical_draws_clean.json")

    if state_slug:
        data = [x for x in data if x.get("state_slug") == state_slug]

    if game_slug:
        data = [x for x in data if x.get("game_slug") == game_slug]

    return data[:limit]


@app.get("/api/number-stats")
def get_number_stats(
    state_slug: str | None = Query(default=None),
    game_slug: str | None = Query(default=None),
):
    data = load_json("number_stats.json")

    if state_slug:
        data = [x for x in data if x.get("state_slug") == state_slug]

    if game_slug:
        data = [x for x in data if x.get("game_slug") == game_slug]

    return data


@app.get("/api/states/{state_slug}/games")
def get_state_games(state_slug: str):
    data = load_json("catalog.json")
    games = [g for g in data.get("games", []) if g.get("state_slug") == state_slug]
    return games


@app.get("/api/states/{state_slug}/latest-results")
def get_state_latest_results(state_slug: str):
    data = load_json("latest_results.json")
    results = [x for x in data if x.get("state_slug") == state_slug]
    return results


@app.get("/api/games/{game_slug}/latest")
def get_game_latest(game_slug: str):
    data = load_json("latest_results.json")
    filtered = [x for x in data if x.get("game_slug") == game_slug]
    if not filtered:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    return filtered


@app.get("/api/games/{game_slug}/historical")
def get_game_historical(game_slug: str, limit: int = Query(default=100, ge=1, le=5000)):
    data = load_json("historical_draws_clean.json")
    filtered = [x for x in data if x.get("game_slug") == game_slug]
    return filtered[:limit]


@app.get("/api/games/{game_slug}/past-draws")
def get_game_past_draws(game_slug: str, limit: int = Query(default=365, ge=1, le=5000)):
    data = load_json("historical_draws_clean.json")
    filtered = [x for x in data if x.get("game_slug") == game_slug]
    return filtered[:limit]


@app.get("/api/games/{game_slug}/stats")
def get_game_stats(game_slug: str):
    data = load_json("number_stats.json")
    filtered = [x for x in data if x.get("game_slug") == game_slug]
    if not filtered:
        raise HTTPException(status_code=404, detail="Estadísticas no encontradas")
    return filtered


@app.get("/api/games/{game_slug}/most-frequent")
def get_game_most_frequent(game_slug: str):
    data = load_json("number_stats.json")
    filtered = [x for x in data if x.get("game_slug") == game_slug]
    if not filtered:
        raise HTTPException(status_code=404, detail="Juego no encontrado")

    return [
        {
            "state_slug": x.get("state_slug"),
            "state_name": x.get("state_name"),
            "game_slug": x.get("game_slug"),
            "game_name": x.get("game_name"),
            "draw_count": x.get("draw_count"),
            "most_frequent_main": x.get("most_frequent_main"),
            "most_frequent_bonus": x.get("most_frequent_bonus"),
        }
        for x in filtered
    ]


@app.get("/api/games/{game_slug}/least-frequent")
def get_game_least_frequent(game_slug: str):
    data = load_json("number_stats.json")
    filtered = [x for x in data if x.get("game_slug") == game_slug]
    if not filtered:
        raise HTTPException(status_code=404, detail="Juego no encontrado")

    return [
        {
            "state_slug": x.get("state_slug"),
            "state_name": x.get("state_name"),
            "game_slug": x.get("game_slug"),
            "game_name": x.get("game_name"),
            "draw_count": x.get("draw_count"),
            "least_frequent_main": x.get("least_frequent_main"),
            "least_frequent_bonus": x.get("least_frequent_bonus"),
        }
        for x in filtered
    ]