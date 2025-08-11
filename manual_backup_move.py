#!/usr/bin/env python3
"""
Manual Migration Backup File Mover
==================================

Simple script to move migration backup files manually.
"""

import os
import shutil
from pathlib import Path

def main():
    # Directories
    source_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts")
    target_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\02_old_tools\migration_backups")
    
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created target directory: {target_dir}")
    
    # Find migration backup files
    backup_files = list(source_dir.glob("migration_backup_*.py"))
    print(f"Found {len(backup_files)} migration backup files")
    
    # Move files
    moved_count = 0
    for file_path in backup_files:
        try:
            dest_path = target_dir / file_path.name
            
            # Handle conflicts
            counter = 1
            while dest_path.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                dest_path = target_dir / f"{stem}_conflict_{counter}{suffix}"
                counter += 1
            
            # Move file
            shutil.move(str(file_path), str(dest_path))
            moved_count += 1
            
            if moved_count % 50 == 0:
                print(f"Moved {moved_count} files...")
                
        except Exception as e:
            print(f"Error moving {file_path.name}: {e}")
    
    print(f"Successfully moved {moved_count}/{len(backup_files)} files")
    
    # Verify remaining files
    remaining = list(source_dir.glob("migration_backup_*.py"))
    print(f"Remaining migration backup files in source: {len(remaining)}")
    
    # Count clean files in source
    all_py_files = list(source_dir.glob("*.py"))
    clean_files = [f for f in all_py_files if not f.name.startswith("migration_backup")]
    print(f"Clean working files in 01_scripts/: {len(clean_files)}")

if __name__ == "__main__":
    main()