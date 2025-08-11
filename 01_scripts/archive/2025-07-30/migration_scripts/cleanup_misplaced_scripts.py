#!/usr/bin/env python3
"""
cleanup_misplaced_scripts_flattened.py

Moves any Python scripts outside 01_scripts/ into archive_old_scripts/,
flattening their original relative paths into the filename to avoid deep nesting.
"""

import os
import shutil
import logging
from pathlib import Path

# === CONFIGURATION ===
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
# =====================

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
    # Skip any file under 01_scripts/ or under excluded top-level dirs
    try:
        py_path.relative_to(SCRIPTS_DIR)
        return False
    except ValueError:
        top = py_path.relative_to(ROOT).parts[0]
        return top not in EXCLUDE_TOP_LEVEL

def flatten_archive_name(py_path: Path) -> Path:
    """
    Turn ROOT/a/b/c/script.py → ARCHIVE_DIR/a__b__c__script.py
    """
    rel = py_path.relative_to(ROOT)
    flat_name = "__".join(rel.parts)
    return ARCHIVE_DIR / flat_name

def move_file(src: Path, dst: Path):
    try:
        dst.parent.mkdir(exist_ok=True)
    except Exception:
        pass  # single-level ARCHIVE_DIR always exists or is created
    shutil.move(str(src), str(dst))
    logging.info(f"Moved: {src} → {dst.name}")

def main():
    setup_logging()
    logging.info(f"Starting flattened cleanup under {ROOT}")
    
    ARCHIVE_DIR.mkdir(exist_ok=True)

    for dirpath, _, filenames in os.walk(ROOT):
        for fname in filenames:
            if not fname.lower().endswith(".py"):
                continue
            full = Path(dirpath) / fname
            if should_archive(full):
                target = flatten_archive_name(full)
                move_file(full, target)

    logging.info("Flattened cleanup complete.")

if __name__ == "__main__":
    main()
