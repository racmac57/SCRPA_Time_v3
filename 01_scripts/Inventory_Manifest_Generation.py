#!/usr/bin/env python3
"""
Generate a CSV manifest of all Python scripts under SCRPA_Time_v2,
including their last modification time and whether they import arcpy.
"""

import csv
import os
from datetime import datetime

ROOT = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
OUT_CSV = "script_manifest.csv"

def scan_scripts(root_dir):
    rows = []
    for dirpath, _, files in os.walk(root_dir):
        for fname in files:
            if fname.lower().endswith(".py"):
                full = os.path.join(dirpath, fname)
                mtime = os.path.getmtime(full)
                with open(full, "r", errors="ignore") as f:
                    text = f.read(4096)
                uses_arcpy = "import arcpy" in text or "from arcpy" in text
                rows.append({
                    "path": os.path.relpath(full, root_dir),
                    "modified": datetime.fromtimestamp(mtime).isoformat(),
                    "uses_arcpy": uses_arcpy
                })
    return rows

if __name__ == "__main__":
    manifest = scan_scripts(ROOT)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path","modified","uses_arcpy"])
        w.writeheader()
        w.writerows(manifest)
    print(f"Wrote {len(manifest)} entries to {OUT_CSV}")
