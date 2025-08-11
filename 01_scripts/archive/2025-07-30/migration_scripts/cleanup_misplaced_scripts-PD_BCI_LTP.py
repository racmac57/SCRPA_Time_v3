#!/usr/bin/env python3
"""
cleanup_misplaced_scripts.py

Enhanced: moves any Python scripts outside 01_scripts/ into archive_old_scripts/,
preserving folder structure. Falls back to copy+delete on Windows errors.
"""

import os
import shutil
import logging
from pathlib import Path

# === CONFIGURATION ===
ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
SCRIPTS_DIR = ROOT / "01_scripts"
ARCHIVE_DIR = ROOT / "archive_old_scripts"
EXCLUDE_DIRS = {
    SCRIPTS_DIR.name,
    "02_notebooks",
    "Validation_Outputs",
    ARCHIVE_DIR.name
}
LOG_FILE = ROOT / "cleanup_misplaced_scripts.log"
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
    """
    Return True if this .py file should be archived:
    - Not under SCRIPTS_DIR
    - Not in any excluded top-level directory
    """
    try:
        py_path.relative_to(SCRIPTS_DIR)
        return False
    except ValueError:
        top = py_path.relative_to(ROOT).parts[0]
        return top not in EXCLUDE_DIRS

def archive_target(py_path: Path) -> Path:
    """Build archive path preserving relative structure."""
    rel = py_path.relative_to(ROOT)
    return ARCHIVE_DIR / rel

def move_with_fallback(src: Path, dst: Path):
    """
    Attempt os.rename (via shutil.move). On failure, fallback to copy2 + remove.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(src), str(dst))
        logging.info(f"Moved: {src} → {dst}")
    except Exception as e:
        logging.warning(f"Rename failed ({e}), attempting copy+delete…")
        try:
            shutil.copy2(str(src), str(dst))
            src.unlink()  # delete original
            logging.info(f"Copied+deleted: {src} → {dst}")
        except Exception as e2:
            logging.error(f"Copy+delete also failed: {e2}")

def main():
    setup_logging()
    logging.info(f"Starting cleanup under {ROOT}")

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    for dirpath, _, files in os.walk(ROOT):
        for fname in files:
            if not fname.lower().endswith(".py"):
                continue
            full = Path(dirpath) / fname
            if should_archive(full):
                target = archive_target(full)
                move_with_fallback(full, target)

    logging.info("Cleanup complete.")

if __name__ == "__main__":
    main()
