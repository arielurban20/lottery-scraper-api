import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
BACKUP_DIR = ROOT / "backups"

FILES_TO_BACKUP = [
    "catalog.json",
    "latest_results.json",
    "historical_draws_clean.json",
    "number_stats.json",
]

def main():
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")

    run_dir = BACKUP_DIR / stamp
    run_dir.mkdir(exist_ok=True)

    copied = 0
    for filename in FILES_TO_BACKUP:
        src = ROOT / filename
        if src.exists():
            shutil.copy2(src, run_dir / filename)
            copied += 1

    print(f"Backup created at: {run_dir}")
    print(f"Files copied: {copied}")

if __name__ == "__main__":
    main()