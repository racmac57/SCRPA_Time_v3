#!/usr/bin/env python3
"""
restore_from_archive.py

Restore all hashed .py files from archive_old_scripts/ back into 01_scripts/
by stripping the "_<8‑hex>" suffix from each filename.
"""

import re
import shutil
import logging
from pathlib import Path

# === CONFIGURATION ===
ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
SCRIPTS_DIR = ROOT / "01_scripts"
ARCHIVE_DIR = ROOT / "archive_old_scripts"
LOG_FILE = ROOT / "restore_from_archive.log"
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
    logging.info("Starting restore from archive…")

    if not ARCHIVE_DIR.exists():
        logging.error(f"Archive directory not found: {ARCHIVE_DIR}")
        return

    # Pattern: base_<8 hex>.py
    pattern = re.compile(r"^(?P<base>.+)_([0-9a-f]{8})\.py$", re.IGNORECASE)

    for archived in ARCHIVE_DIR.glob("*.py"):
        m = pattern.match(archived.name)
        if not m:
            logging.warning(f"Skipping file with unexpected name: {archived.name}")
            continue

        original_name = f"{m.group('base')}.py"
        dest = SCRIPTS_DIR / original_name
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.move(str(archived), str(dest))
            logging.info(f"Restored: {archived.name} → 01_scripts/{original_name}")
        except Exception as e:
            logging.error(f"Failed to restore {archived.name}: {e}")

    logging.info("Restore complete. Check 01_scripts/ for your files.")

if __name__ == "__main__":
    main()
