#!/usr/bin/env python3
"""
Migration Backup File Mover
===========================

Moves all migration_backup_*.py files from 01_scripts/ to 02_old_tools/
while preserving subfolder structure and providing detailed logging.

Author: Claude Code Assistant
Date: 2025-01-27
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Dict
import logging
from datetime import datetime

class MigrationBackupMover:
    def __init__(self):
        self.root_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        self.source_dir = self.root_dir / "01_scripts"
        self.target_dir = self.root_dir / "02_old_tools"
        
        # Setup logging
        log_file = self.root_dir / "migration_backup_move.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.move_results = {
            'files_found': [],
            'files_moved': [],
            'files_failed': [],
            'directories_created': [],
            'total_size_moved': 0
        }
    
    def find_migration_backup_files(self) -> List[Path]:
        """Find all migration_backup_*.py files in the source directory."""
        backup_files = []
        
        if not self.source_dir.exists():
            self.logger.error(f"Source directory does not exist: {self.source_dir}")
            return backup_files
        
        # Search for migration backup files
        for file_path in self.source_dir.rglob("migration_backup_*.py"):
            backup_files.append(file_path)
            self.move_results['files_found'].append(str(file_path.relative_to(self.source_dir)))
        
        self.logger.info(f"Found {len(backup_files)} migration backup files")
        return backup_files
    
    def create_target_structure(self):
        """Create the target directory structure."""
        try:
            self.target_dir.mkdir(exist_ok=True)
            self.logger.info(f"Created/verified target directory: {self.target_dir}")
            
            # Create migration_backups subdirectory for organization
            migration_backups_dir = self.target_dir / "migration_backups"
            migration_backups_dir.mkdir(exist_ok=True)
            self.move_results['directories_created'].append(str(migration_backups_dir))
            self.logger.info(f"Created migration backups directory: {migration_backups_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to create target structure: {e}")
            raise
    
    def move_file(self, source_file: Path) -> bool:
        """Move a single file to the target directory."""
        try:
            # Calculate relative path from source directory
            relative_path = source_file.relative_to(self.source_dir)
            
            # Create destination path in migration_backups subdirectory
            dest_path = self.target_dir / "migration_backups" / relative_path
            
            # Create parent directories if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if not dest_path.parent in [Path(d) for d in self.move_results['directories_created']]:
                self.move_results['directories_created'].append(str(dest_path.parent))
            
            # Handle filename conflicts
            if dest_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stem = dest_path.stem
                suffix = dest_path.suffix
                dest_path = dest_path.parent / f"{stem}_moved_{timestamp}{suffix}"
                self.logger.warning(f"File conflict resolved with timestamp: {dest_path.name}")
            
            # Get file size before moving
            file_size = source_file.stat().st_size
            
            # Move the file
            shutil.move(str(source_file), str(dest_path))
            
            # Log success
            self.move_results['files_moved'].append({
                'source': str(relative_path),
                'destination': str(dest_path.relative_to(self.target_dir)),
                'size': file_size
            })
            self.move_results['total_size_moved'] += file_size
            
            self.logger.info(f"Moved: {relative_path} -> {dest_path.relative_to(self.target_dir)}")
            return True
            
        except Exception as e:
            self.move_results['files_failed'].append({
                'file': str(source_file.relative_to(self.source_dir)),
                'error': str(e)
            })
            self.logger.error(f"Failed to move {source_file.name}: {e}")
            return False
    
    def move_all_files(self, backup_files: List[Path]) -> Dict:
        """Move all backup files to the target directory."""
        self.logger.info(f"Starting to move {len(backup_files)} files...")
        
        success_count = 0
        for i, file_path in enumerate(backup_files, 1):
            if i % 50 == 0:  # Progress indicator
                self.logger.info(f"Progress: {i}/{len(backup_files)} files processed")
            
            if self.move_file(file_path):
                success_count += 1
        
        self.logger.info(f"Move operation completed: {success_count}/{len(backup_files)} files moved successfully")
        return self.move_results
    
    def generate_report(self) -> str:
        """Generate a detailed report of the move operation."""
        report = []
        report.append("MIGRATION BACKUP FILE MOVE REPORT")
        report.append("=" * 50)
        report.append(f"Operation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Source Directory: {self.source_dir}")
        report.append(f"Target Directory: {self.target_dir}")
        report.append("")
        
        # Summary statistics
        total_found = len(self.move_results['files_found'])
        total_moved = len(self.move_results['files_moved'])
        total_failed = len(self.move_results['files_failed'])
        total_size_mb = self.move_results['total_size_moved'] / (1024 * 1024)
        
        report.append("SUMMARY")
        report.append("-" * 20)
        report.append(f"Files Found:        {total_found}")
        report.append(f"Files Moved:        {total_moved}")
        report.append(f"Files Failed:       {total_failed}")
        report.append(f"Success Rate:       {total_moved/total_found*100:.1f}%" if total_found > 0 else "N/A")
        report.append(f"Total Size Moved:   {total_size_mb:.2f} MB")
        report.append(f"Directories Created: {len(self.move_results['directories_created'])}")
        report.append("")
        
        # Failed files (if any)
        if self.move_results['files_failed']:
            report.append("FAILED MOVES")
            report.append("-" * 20)
            for failure in self.move_results['files_failed']:
                report.append(f"❌ {failure['file']}")
                report.append(f"   Error: {failure['error']}")
            report.append("")
        
        # Sample of moved files
        if self.move_results['files_moved']:
            report.append("SAMPLE MOVED FILES (first 10)")
            report.append("-" * 30)
            for i, moved_file in enumerate(self.move_results['files_moved'][:10]):
                report.append(f"✅ {moved_file['source']}")
                report.append(f"   -> {moved_file['destination']}")
                report.append(f"   Size: {moved_file['size']/1024:.1f} KB")
            
            if len(self.move_results['files_moved']) > 10:
                report.append(f"   ... and {len(self.move_results['files_moved']) - 10} more files")
            report.append("")
        
        # Directory structure created
        if self.move_results['directories_created']:
            report.append("DIRECTORIES CREATED")
            report.append("-" * 25)
            for directory in self.move_results['directories_created']:
                report.append(f"📁 {directory}")
            report.append("")
        
        return '\n'.join(report)
    
    def verify_move_completion(self) -> Dict:
        """Verify that files were moved successfully."""
        verification = {
            'remaining_backup_files': 0,
            'moved_files_exist': 0,
            'verification_passed': False
        }
        
        # Check if any migration backup files remain in source
        remaining_files = list(self.source_dir.rglob("migration_backup_*.py"))
        verification['remaining_backup_files'] = len(remaining_files)
        
        # Check if moved files exist in target
        existing_moved_files = 0
        for moved_file in self.move_results['files_moved']:
            target_path = self.target_dir / moved_file['destination']
            if target_path.exists():
                existing_moved_files += 1
        verification['moved_files_exist'] = existing_moved_files
        
        # Determine if verification passed
        verification['verification_passed'] = (
            verification['remaining_backup_files'] == 0 and
            verification['moved_files_exist'] == len(self.move_results['files_moved'])
        )
        
        return verification

def main():
    """Main execution function."""
    print("🚀 MIGRATION BACKUP FILE MOVER")
    print("=" * 40)
    
    # Create mover instance
    mover = MigrationBackupMover()
    
    try:
        # Find backup files
        backup_files = mover.find_migration_backup_files()
        
        if not backup_files:
            print("No migration backup files found to move.")
            return 0
        
        # Create target structure
        mover.create_target_structure()
        
        # Move files
        results = mover.move_all_files(backup_files)
        
        # Verify completion
        verification = mover.verify_move_completion()
        
        # Generate and display report
        report = mover.generate_report()
        print(report)
        
        # Display verification results
        print("VERIFICATION RESULTS")
        print("-" * 25)
        print(f"Remaining backup files in source: {verification['remaining_backup_files']}")
        print(f"Moved files exist in target: {verification['moved_files_exist']}")
        print(f"Verification: {'✅ PASSED' if verification['verification_passed'] else '❌ FAILED'}")
        
        # Save report
        report_file = mover.root_dir / "migration_backup_move_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            f.write("\n\nVERIFICATION RESULTS\n")
            f.write(f"Remaining backup files: {verification['remaining_backup_files']}\n")
            f.write(f"Moved files exist: {verification['moved_files_exist']}\n")
            f.write(f"Verification passed: {verification['verification_passed']}\n")
        
        print(f"\n📄 Report saved to: {report_file}")
        
        return 0 if verification['verification_passed'] else 1
        
    except Exception as e:
        mover.logger.error(f"Fatal error during move operation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())