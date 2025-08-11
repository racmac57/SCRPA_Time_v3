#!/usr/bin/env python3
"""
restore_everything.py

Moves **all** .py files from archive_old_scripts/ back into 01_scripts/,
preserving their filenames. Overwrites only if necessary.
"""

import shutil
import logging
from pathlib import Path

# === CONFIG ===
ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
SCRIPTS_DIR = ROOT / "01_scripts"
ARCHIVE_DIR = ROOT / "archive_old_scripts"
LOG_FILE = ROOT / "restore_everything.log"
# ==============

def setup_logging():
    logging.basicConfig(
        filename=LOG_FILE,
        filemode='w',
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logging.getLogger().addHandler(console)

def main():
    setup_logging()
    logging.info("Starting full restore from archive_old_scripts/…")

    if not ARCHIVE_DIR.exists():
        logging.error(f"Archive directory not found: {ARCHIVE_DIR}")
        return

    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    for archived in ARCHIVE_DIR.glob("*.py"):
        dest = SCRIPTS_DIR / archived.name
        try:
            shutil.move(str(archived), str(dest))
            logging.info(f"Restored: {archived.name} → 01_scripts/{archived.name}")
        except Exception as e:
            logging.error(f"Failed to restore {archived.name}: {e}")

    logging.info("Full restore complete. Check 01_scripts/ for all files.")

if __name__ == "__main__":
    main()
