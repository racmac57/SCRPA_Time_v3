#!/usr/bin/env python3
"""
SCRPA Python File Organization Script
==================================

This script organizes all .py files in the SCRPA_Time_v2 directory:
- Keep files in 01_scripts/ where they are (these are the current working scripts)
- Move all other .py files to a new 02_old_tools/ directory for archival

Author: Claude Code Assistant
Date: 2025-01-27
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Tuple
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('py_file_organization.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def find_all_py_files(root_dir: Path) -> Tuple[List[Path], List[Path]]:
    """
    Find all .py files in the directory structure.
    
    Returns:
        Tuple of (files_to_keep, files_to_move)
    """
    files_to_keep = []  # Files in 01_scripts/
    files_to_move = []  # All other .py files
    
    # Find all .py files recursively
    for py_file in root_dir.rglob("*.py"):
        # Check if file is within 01_scripts directory
        try:
            relative_path = py_file.relative_to(root_dir)
            if relative_path.parts[0] == "01_scripts":
                files_to_keep.append(py_file)
            else:
                files_to_move.append(py_file)
        except ValueError:
            # File is not within root_dir, skip
            continue
    
    return files_to_keep, files_to_move

def create_old_tools_directory(root_dir: Path) -> Path:
    """Create the 02_old_tools directory if it doesn't exist."""
    old_tools_dir = root_dir / "02_old_tools"
    old_tools_dir.mkdir(exist_ok=True)
    logger.info(f"Created/verified directory: {old_tools_dir}")
    return old_tools_dir

def move_files_to_old_tools(files_to_move: List[Path], old_tools_dir: Path, root_dir: Path):
    """
    Move files to 02_old_tools/, preserving relative directory structure.
    """
    moved_count = 0
    
    for file_path in files_to_move:
        try:
            # Calculate relative path from root
            relative_path = file_path.relative_to(root_dir)
            
            # Create destination path in 02_old_tools/
            dest_path = old_tools_dir / relative_path
            
            # Create parent directories if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle filename conflicts
            if dest_path.exists():
                # Add timestamp to filename
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                stem = dest_path.stem
                suffix = dest_path.suffix
                dest_path = dest_path.parent / f"{stem}_{timestamp}{suffix}"
            
            # Move the file
            shutil.move(str(file_path), str(dest_path))
            logger.info(f"Moved: {relative_path} -> {dest_path.relative_to(root_dir)}")
            moved_count += 1
            
        except Exception as e:
            logger.error(f"Failed to move {file_path}: {e}")
    
    return moved_count

def main():
    """Main execution function."""
    # Define root directory
    root_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
    
    if not root_dir.exists():
        logger.error(f"Root directory does not exist: {root_dir}")
        return 1
    
    logger.info(f"Starting Python file organization in: {root_dir}")
    
    # Find all .py files
    files_to_keep, files_to_move = find_all_py_files(root_dir)
    
    logger.info(f"Found {len(files_to_keep)} files to keep in 01_scripts/")
    logger.info(f"Found {len(files_to_move)} files to move to 02_old_tools/")
    
    # Create 02_old_tools directory
    old_tools_dir = create_old_tools_directory(root_dir)
    
    # Move files
    if files_to_move:
        logger.info("Moving files to 02_old_tools/...")
        moved_count = move_files_to_old_tools(files_to_move, old_tools_dir, root_dir)
        logger.info(f"Successfully moved {moved_count} files")
    else:
        logger.info("No files to move")
    
    # Summary report
    logger.info("\n" + "="*50)
    logger.info("ORGANIZATION COMPLETE")
    logger.info("="*50)
    logger.info(f"Files kept in 01_scripts/: {len(files_to_keep)}")
    logger.info(f"Files moved to 02_old_tools/: {len(files_to_move)}")
    
    # List files to keep
    if files_to_keep:
        logger.info("\nFiles remaining in 01_scripts/:")
        for file_path in sorted(files_to_keep):
            relative_path = file_path.relative_to(root_dir)
            logger.info(f"  - {relative_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())