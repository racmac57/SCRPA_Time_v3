#!/usr/bin/env python3
"""
Quick Python File Organizer
===========================
Move .py files that are NOT in 01_scripts/ to 02_old_tools/
"""

import os
import shutil
from pathlib import Path

def main():
    root_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
    
    # Files to move (from root directory)
    root_py_files = [
        "restore_archived_scripts.py",
        "restore_everything.py",
        "organize_py_files.py"
    ]
    
    # Create 02_old_tools directory
    old_tools_dir = root_dir / "02_old_tools"
    old_tools_dir.mkdir(exist_ok=True)
    print(f"Created directory: {old_tools_dir}")
    
    # Move files from root
    moved_count = 0
    for filename in root_py_files:
        source = root_dir / filename
        if source.exists():
            dest = old_tools_dir / filename
            try:
                shutil.move(str(source), str(dest))
                print(f"Moved: {filename}")
                moved_count += 1
            except Exception as e:
                print(f"Error moving {filename}: {e}")
    
    print(f"\nMoved {moved_count} files to 02_old_tools/")
    
    # Count files remaining in 01_scripts/
    scripts_dir = root_dir / "01_scripts"
    if scripts_dir.exists():
        py_files_in_scripts = list(scripts_dir.glob("*.py"))
        print(f"Files remaining in 01_scripts/: {len(py_files_in_scripts)}")
        
        # Show clean files (excluding migration backups)
        clean_files = [f for f in py_files_in_scripts if not f.name.startswith("migration_backup")]
        print(f"Clean working files in 01_scripts/: {len(clean_files)}")
        
        print("\nClean working files:")
        for f in sorted(clean_files):
            print(f"  - {f.name}")

if __name__ == "__main__":
    main()