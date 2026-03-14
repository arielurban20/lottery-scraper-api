import json

INPUT_FILE = "historical_draws_raw.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total filas históricas: {len(data)}")

games = {}
for item in data:
    key = (item.get("state_name"), item.get("game_name"))
    games[key] = games.get(key, 0) + 1

print("\nPrimeros 20 juegos con cantidad de filas:\n")
for i, (key, count) in enumerate(games.items()):
    if i >= 20:
        break
    print(f"{key}: {count}")

print("\nPrimeras 10 filas:\n")
for item in data[:10]:
    print({
        "game_name": item.get("game_name"),
        "state_name": item.get("state_name"),
        "row_index": item.get("row_index"),
        "cells": item.get("cells"),
    })