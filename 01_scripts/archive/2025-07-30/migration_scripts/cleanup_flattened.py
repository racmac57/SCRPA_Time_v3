#!/usr/bin/env python3
"""
cleanup_flattened.py

Flattened archive of misplaced .py files to avoid deep nesting Windows errors.
"""

import os
import shutil
import logging
from pathlib import Path

# === CONFIG ===
ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
SCRIPTS_DIR = ROOT / "01_scripts"
ARCHIVE_DIR = ROOT / "archive_old_scripts"
EXCLUDE_TOP_LEVEL = {
    SCRIPTS_DIR.name,
    "02_notebooks",
    "Validation_Outputs",
    ARCHIVE_DIR.name
}
LOG_FILE = ROOT / "cleanup_flattened.log"
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

def should_archive(py_path: Path) -> bool:
    # Only archive .py files outside of 01_scripts and top‑level excludes
    try:
        py_path.relative_to(SCRIPTS_DIR)
        return False
    except ValueError:
        top = py_path.relative_to(ROOT).parts[0]
        return top not in EXCLUDE_TOP_LEVEL

def flatten_name(py_path: Path) -> Path:
    """
    Convert e.g. folder1/folder2/script.py 
    → archive_old_scripts/folder1__folder2__script.py
    """
    rel = py_path.relative_to(ROOT)
    flat = "__".join(rel.parts)
    return ARCHIVE_DIR / flat

def main():
    setup_logging()
    logging.info(f"Starting flattened cleanup under {ROOT}")

    # Ensure archive directory exists
    ARCHIVE_DIR.mkdir(exist_ok=True)

    for dirpath, _, filenames in os.walk(ROOT):
        for fname in filenames:
            if not fname.lower().endswith(".py"):
                continue
            full = Path(dirpath) / fname
            if should_archive(full):
                dest = flatten_name(full)
                try:
                    shutil.move(str(full), str(dest))
                    logging.info(f"Moved: {full.name} → {dest.name}")
                except Exception as e:
                    logging.error(f"Failed to move {full} → {dest}: {e}")

    logging.info("Flattened cleanup complete.")

if __name__ == "__main__":
    main()
