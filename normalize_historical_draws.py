import json
import re

INPUT_FILE = "historical_draws_raw.json"
OUTPUT_FILE = "historical_draws_clean.json"

MONTH_NAMES = {
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
}

DAY_NAMES = {
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday"
}


def is_month_row(cells):
    if len(cells) != 1:
        return False
    text = cells[0].strip().lower()
    return any(month in text for month in MONTH_NAMES) and any(char.isdigit() for char in text)


def is_header_row(cells):
    joined = " ".join(cells).lower()
    return "date" in joined and "result" in joined


def starts_with_day_name(text):
    text = text.strip().lower()
    return any(text.startswith(day) for day in DAY_NAMES)


def clean_text(text):
    return re.sub(r"\s+", " ", text.replace("\n", " ")).strip()


def extract_draw_date(cells):
    if not cells:
        return None, cells

    if len(cells) >= 2 and starts_with_day_name(cells[0]):
        draw_date = clean_text(f"{cells[0]} {cells[1]}")
        return draw_date, cells[2:]

    if starts_with_day_name(cells[0]):
        return clean_text(cells[0]), cells[1:]

    return None, cells


def normalize_row(item):
    cells = [clean_text(x) for x in item.get("cells", []) if clean_text(x)]
    if not cells:
        return None

    if is_header_row(cells):
        return None

    if is_month_row(cells):
        return None

    draw_date, rest = extract_draw_date(cells)
    if not draw_date:
        return None

    numbers = []
    bonus_label = None
    bonus_number = None
    multiplier = None
    prize_parts = []

    i = 0
    while i < len(rest):
        token = rest[i]

        # números normales
        if token.isdigit():
            numbers.append(token)
            i += 1
            continue

        # bonus tipo PB / MB / CB
        if token in {"PB", "MB", "CB"}:
            bonus_label = token

            # saltar ":" si aparece
            if i + 1 < len(rest) and rest[i + 1] == ":":
                if i + 2 < len(rest):
                    bonus_number = rest[i + 2]
                    i += 3
                    continue
            elif i + 1 < len(rest):
                bonus_number = rest[i + 1]
                i += 2
                continue

        # multiplicadores
        if "power play" in token.lower() or "megaplier" in token.lower() or "multiplier" in token.lower():
            multiplier = token
            i += 1
            continue

        # evitar texto de draws especiales dentro de la misma fila
        if token.lower() in {"main draw", "double play"}:
            i += 1
            continue

        prize_parts.append(token)
        i += 1

    return {
        "source_url": item.get("source_url"),
        "game_type": item.get("game_type"),
        "state_slug": item.get("state_slug"),
        "state_name": item.get("state_name"),
        "game_slug": item.get("game_slug"),
        "game_name": item.get("game_name"),
        "draw_date": draw_date,
        "main_numbers": numbers,
        "bonus_label": bonus_label,
        "bonus_number": bonus_number,
        "multiplier": multiplier,
        "prize_text": clean_text(" ".join(prize_parts)) if prize_parts else None,
        "row_index": item.get("row_index"),
    }


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    clean = []
    skipped = 0

    for item in raw:
        normalized = normalize_row(item)
        if normalized:
            clean.append(normalized)
        else:
            skipped += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)

    print(f"Archivo limpio creado: {OUTPUT_FILE}")
    print(f"Filas crudas: {len(raw)}")
    print(f"Filas limpias: {len(clean)}")
    print(f"Filas omitidas: {skipped}")

    print("\nPrimeros 10 registros limpios:\n")
    for row in clean[:10]:
        print(row)


if __name__ == "__main__":
    main()