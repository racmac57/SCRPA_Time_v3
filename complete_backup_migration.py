#!/usr/bin/env python3
"""
Complete Migration Backup File Processor
========================================

Performs all requested operations:
1. Move migration_backup_*.py files to 02_old_tools/
2. Count files in both directories
3. Generate duplicate report for 01_scripts/
4. Provide comprehensive summary

Author: Claude Code Assistant
Date: 2025-01-27
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict
import logging
from datetime import datetime

class CompleteMigrationProcessor:
    def __init__(self):
        self.root_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        self.source_dir = self.root_dir / "01_scripts"
        self.target_dir = self.root_dir / "02_old_tools"
        
        # Setup logging
        log_file = self.root_dir / "complete_migration_log.txt"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.results = {
            'files_moved': [],
            'move_errors': [],
            'source_count_before': 0,
            'source_count_after': 0,
            'target_count_before': 0,
            'target_count_after': 0,
            'duplicates_found': [],
            'clean_files_remaining': []
        }
    
    def count_migration_files(self, directory: Path) -> int:
        """Count migration_backup_*.py files in a directory."""
        if not directory.exists():
            return 0
        
        count = 0
        for file_path in directory.rglob("migration_backup_*.py"):
            count += 1
        return count
    
    def step1_move_migration_files(self):
        """Step 1: Move all migration_backup_*.py files to 02_old_tools/"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 1: MOVING MIGRATION BACKUP FILES")
        self.logger.info("=" * 60)
        
        # Count files before move
        self.results['source_count_before'] = self.count_migration_files(self.source_dir)
        self.results['target_count_before'] = self.count_migration_files(self.target_dir)
        
        self.logger.info(f"Before move:")
        self.logger.info(f"  Source (01_scripts/): {self.results['source_count_before']} files")
        self.logger.info(f"  Target (02_old_tools/): {self.results['target_count_before']} files")
        
        # Create target directory structure
        migration_target = self.target_dir / "migration_backups"
        migration_target.mkdir(parents=True, exist_ok=True)
        
        # Find and move files
        backup_files = list(self.source_dir.rglob("migration_backup_*.py"))
        self.logger.info(f"Found {len(backup_files)} migration backup files to move")
        
        moved_count = 0
        for file_path in backup_files:
            try:
                # Calculate relative path from source
                relative_path = file_path.relative_to(self.source_dir)
                
                # Create destination in migration_backups subfolder
                dest_path = migration_target / relative_path
                
                # Create parent directories
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Handle naming conflicts
                if dest_path.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    stem = dest_path.stem
                    suffix = dest_path.suffix
                    dest_path = dest_path.parent / f"{stem}_moved_{timestamp}{suffix}"
                
                # Move file
                shutil.move(str(file_path), str(dest_path))
                self.results['files_moved'].append({
                    'source': str(relative_path),
                    'destination': str(dest_path.relative_to(self.target_dir))
                })
                moved_count += 1
                
                if moved_count % 50 == 0:
                    self.logger.info(f"Progress: {moved_count}/{len(backup_files)} files moved")
                
            except Exception as e:
                self.results['move_errors'].append({
                    'file': str(file_path.relative_to(self.source_dir)),
                    'error': str(e)
                })
                self.logger.error(f"Failed to move {file_path.name}: {e}")
        
        self.logger.info(f"Move completed: {moved_count}/{len(backup_files)} files moved successfully")
        return moved_count
    
    def step2_recount_files(self):
        """Step 2: Re-count migration files in both directories"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 2: RE-COUNTING FILES")
        self.logger.info("=" * 60)
        
        self.results['source_count_after'] = self.count_migration_files(self.source_dir)
        self.results['target_count_after'] = self.count_migration_files(self.target_dir)
        
        self.logger.info(f"After move:")
        self.logger.info(f"  Source (01_scripts/): {self.results['source_count_after']} files")
        self.logger.info(f"  Target (02_old_tools/): {self.results['target_count_after']} files")
        
        # Calculate changes
        source_reduction = self.results['source_count_before'] - self.results['source_count_after']
        target_increase = self.results['target_count_after'] - self.results['target_count_before']
        
        self.logger.info(f"Changes:")
        self.logger.info(f"  Source reduction: {source_reduction} files")
        self.logger.info(f"  Target increase: {target_increase} files")
        
        if source_reduction == target_increase and self.results['source_count_after'] == 0:
            self.logger.info("✅ Move appears successful - all files transferred")
        else:
            self.logger.warning("⚠️ File counts don't match expected results")
    
    def step3_analyze_duplicates(self):
        """Step 3: Generate duplicate report for remaining files in 01_scripts/"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 3: ANALYZING DUPLICATES IN 01_scripts/")
        self.logger.info("=" * 60)
        
        if not self.source_dir.exists():
            self.logger.error("Source directory does not exist")
            return
        
        # Get all remaining Python files
        py_files = list(self.source_dir.glob("*.py"))
        self.logger.info(f"Found {len(py_files)} Python files remaining in 01_scripts/")
        
        # Group by filename for duplicate detection
        filename_groups = defaultdict(list)
        for file_path in py_files:
            filename_groups[file_path.name].append(file_path)
        
        # Find duplicates
        duplicates = {name: paths for name, paths in filename_groups.items() if len(paths) > 1}
        
        if duplicates:
            self.logger.info(f"Found {len(duplicates)} sets of duplicate filenames:")
            for filename, paths in duplicates.items():
                self.logger.info(f"  📄 {filename} ({len(paths)} copies)")
                for path in paths:
                    self.logger.info(f"    - {path}")
                self.results['duplicates_found'].append({
                    'filename': filename,
                    'count': len(paths),
                    'paths': [str(p) for p in paths]
                })
        else:
            self.logger.info("✅ No duplicate filenames found in 01_scripts/")
        
        # List all clean files
        clean_files = [f.name for f in py_files if not f.name.startswith("migration_backup")]
        self.results['clean_files_remaining'] = sorted(clean_files)
        
        self.logger.info(f"Clean working files in 01_scripts/: {len(clean_files)}")
        for filename in self.results['clean_files_remaining'][:10]:  # Show first 10
            self.logger.info(f"  ✅ {filename}")
        if len(clean_files) > 10:
            self.logger.info(f"    ... and {len(clean_files) - 10} more files")
    
    def step4_generate_summary(self):
        """Step 4: Generate comprehensive summary"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 4: COMPREHENSIVE SUMMARY")
        self.logger.info("=" * 60)
        
        # Movement summary
        files_moved = len(self.results['files_moved'])
        move_errors = len(self.results['move_errors'])
        
        self.logger.info("MIGRATION BACKUP FILE MOVEMENT:")
        self.logger.info(f"  Files successfully moved: {files_moved}")
        self.logger.info(f"  Move errors: {move_errors}")
        self.logger.info(f"  Files in 01_scripts/ before: {self.results['source_count_before']}")
        self.logger.info(f"  Files in 01_scripts/ after: {self.results['source_count_after']}")
        self.logger.info(f"  Files in 02_old_tools/ before: {self.results['target_count_before']}")
        self.logger.info(f"  Files in 02_old_tools/ after: {self.results['target_count_after']}")
        
        # Duplicate analysis
        self.logger.info("")
        self.logger.info("DUPLICATE ANALYSIS:")
        if self.results['duplicates_found']:
            self.logger.info(f"  Duplicate sets found: {len(self.results['duplicates_found'])}")
            for dup in self.results['duplicates_found']:
                self.logger.info(f"    - {dup['filename']}: {dup['count']} copies")
        else:
            self.logger.info("  ✅ No duplicates found in 01_scripts/")
        
        # Active project files
        self.logger.info("")
        self.logger.info("ACTIVE PROJECT FILES:")
        self.logger.info(f"  Clean working files: {len(self.results['clean_files_remaining'])}")
        self.logger.info("  Key working files include:")
        
        # Highlight important files
        important_files = ['main.py', 'config.py', 'logger.py', 'arcpy_dynamic_folder_script.py', 
                          'Hybrid_Dynamic_Folder_Script.py', 'Updated_Weekly_Crime_Report.py']
        
        for filename in important_files:
            if filename in self.results['clean_files_remaining']:
                self.logger.info(f"    ✅ {filename}")
        
        # Overall status
        self.logger.info("")
        self.logger.info("OVERALL STATUS:")
        if (self.results['source_count_after'] == 0 and 
            files_moved > 0 and 
            move_errors == 0):
            self.logger.info("  🟢 SUCCESS: All migration backups moved, 01_scripts/ contains only active files")
        elif self.results['source_count_after'] == 0 and files_moved > 0:
            self.logger.info("  🟡 PARTIAL SUCCESS: Backups moved but some errors occurred")
        else:
            self.logger.info("  🔴 INCOMPLETE: Migration backups may still remain in 01_scripts/")
    
    def generate_report(self) -> str:
        """Generate final report"""
        report = []
        report.append("COMPLETE MIGRATION BACKUP PROCESSING REPORT")
        report.append("=" * 60)
        report.append(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Add all the results to report
        report.append("1. FILE MOVEMENT RESULTS")
        report.append("-" * 30)
        report.append(f"Files moved: {len(self.results['files_moved'])}")
        report.append(f"Move errors: {len(self.results['move_errors'])}")
        report.append("")
        
        report.append("2. FILE COUNTS")
        report.append("-" * 30)
        report.append(f"01_scripts/ before: {self.results['source_count_before']}")
        report.append(f"01_scripts/ after: {self.results['source_count_after']}")
        report.append(f"02_old_tools/ before: {self.results['target_count_before']}")
        report.append(f"02_old_tools/ after: {self.results['target_count_after']}")
        report.append("")
        
        report.append("3. DUPLICATE ANALYSIS")
        report.append("-" * 30)
        if self.results['duplicates_found']:
            for dup in self.results['duplicates_found']:
                report.append(f"Duplicate: {dup['filename']} ({dup['count']} copies)")
        else:
            report.append("No duplicates found")
        report.append("")
        
        report.append("4. CLEAN FILES REMAINING")
        report.append("-" * 30)
        for filename in self.results['clean_files_remaining']:
            report.append(f"- {filename}")
        
        return '\n'.join(report)
    
    def run_complete_process(self):
        """Execute all steps in order"""
        self.logger.info("🚀 STARTING COMPLETE MIGRATION BACKUP PROCESSING")
        self.logger.info(f"Working directory: {self.root_dir}")
        
        try:
            # Execute all steps
            self.step1_move_migration_files()
            self.step2_recount_files()
            self.step3_analyze_duplicates()
            self.step4_generate_summary()
            
            # Generate final report
            report = self.generate_report()
            
            # Save report
            report_file = self.root_dir / "complete_migration_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.logger.info(f"📄 Complete report saved to: {report_file}")
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"Fatal error during processing: {e}")
            raise

def main():
    """Main execution function"""
    processor = CompleteMigrationProcessor()
    results = processor.run_complete_process()
    return 0

if __name__ == "__main__":
    sys.exit(main())