#!/usr/bin/env python3
"""
cleanup_extended_flattened.py

Archive any .py outside 01_scripts/ into archive_old_scripts/,
using extended-length paths and truncated, hashed filenames.
"""

import os
import shutil
import logging
import hashlib
from pathlib import Path

# --- CONFIGURATION ---
ROOT = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
SCRIPTS_DIR = ROOT / "01_scripts"
ARCHIVE_DIR = ROOT / "archive_old_scripts"
EXCLUDE_TOP_LEVEL = {SCRIPTS_DIR.name, "02_notebooks", "Validation_Outputs", ARCHIVE_DIR.name}
LOG_FILE = ROOT / "cleanup_extended.log"
MAX_NAME_LEN = 100  # max filename length in chars
# ----------------------

# Windows UNC prefix for extended paths
UNC_PREFIX = "\\\\?\\"  # equivalent to \\?\


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


def use_extended(path: Path) -> str:
    """Return a Windows extended-length path string."""
    p = str(path)
    if p.startswith(UNC_PREFIX):
        return p
    return UNC_PREFIX + p


def should_archive(py_path: Path) -> bool:
    """True if .py is outside SCRIPTS_DIR and not in excluded folders."""
    try:
        py_path.relative_to(SCRIPTS_DIR)
        return False
    except ValueError:
        top = py_path.relative_to(ROOT).parts[0]
        return top not in EXCLUDE_TOP_LEVEL


def make_archive_name(py_path: Path) -> Path:
    """
    Build a truncated, hashed filename based on the original relative path.
    E.g., scripts/old/foo.py → foo_<hash>.py
    """
    rel_bytes = py_path.relative_to(ROOT).as_posix().encode('utf-8')
    short_hash = hashlib.sha1(rel_bytes).hexdigest()[:8]
    base = py_path.stem
    ext = py_path.suffix
    # Construct name and truncate if needed
    name = f"{base}_{short_hash}{ext}"
    if len(name) > MAX_NAME_LEN:
        # ensure unique but shorten
        name = f"{base[:MAX_NAME_LEN- (len(ext)+9)]}_{short_hash}{ext}"
    return ARCHIVE_DIR / name


def move_file(src: Path, dst: Path):
    # Ensure archive dir exists
    ARCHIVE_DIR.mkdir(exist_ok=True)
    try:
        # Try extended-length move
        shutil.move(use_extended(src), use_extended(dst))
        logging.info(f"Moved: {src.name} → {dst.name}")
    except Exception as e:
        logging.error(f"Failed to move {src} → {dst}: {e}")


def main():
    setup_logging()
    logging.info(f"Starting extended cleanup under {ROOT}")

    for dirpath, _, files in os.walk(ROOT):
        for fname in files:
            if not fname.lower().endswith('.py'):
                continue
            full_path = Path(dirpath) / fname
            if should_archive(full_path):
                target = make_archive_name(full_path)
                move_file(full_path, target)

    logging.info("Extended cleanup complete.")


if __name__ == '__main__':
    main()
