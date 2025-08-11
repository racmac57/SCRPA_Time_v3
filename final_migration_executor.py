#!/usr/bin/env python3
"""
Final Migration Executor
========================

Executes the complete migration backup file organization and provides
comprehensive analysis as requested:

1. Move all migration_backup_*.py from 01_scripts/ to 02_old_tools/
2. Count files in both directories 
3. Generate duplicate report for 01_scripts/
4. Provide summary of operation

Author: Claude Code Assistant
Date: 2025-01-27
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import logging
from datetime import datetime

class FinalMigrationExecutor:
    def __init__(self):
        self.root_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        self.source_dir = self.root_dir / "01_scripts"
        self.target_dir = self.root_dir / "02_old_tools"
        
        # Setup logging
        self.setup_logging()
        
        self.results = {
            'files_moved': 0,
            'move_errors': 0,
            'source_before': 0,
            'source_after': 0,
            'target_before': 0,
            'target_after': 0,
            'duplicates_found': [],
            'clean_files': [],
            'operation_successful': False
        }
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_file = self.root_dir / "final_migration_log.txt"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, mode='w'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def count_migration_files(self, directory: Path) -> int:
        """Count migration_backup_*.py files in directory and subdirectories"""
        if not directory.exists():
            return 0
        
        count = 0
        migration_files = []
        for file_path in directory.rglob("migration_backup_*.py"):
            count += 1
            migration_files.append(file_path)
        
        return count, migration_files
    
    def step1_execute_move(self):
        """Step 1: Move all migration backup files"""
        self.logger.info("=" * 80)
        self.logger.info("STEP 1: MOVING ALL MIGRATION BACKUP FILES")
        self.logger.info("=" * 80)
        
        # Count before move
        self.results['source_before'], source_files = self.count_migration_files(self.source_dir)
        self.results['target_before'], _ = self.count_migration_files(self.target_dir)
        
        self.logger.info(f"BEFORE MOVE:")
        self.logger.info(f"  📁 01_scripts/: {self.results['source_before']} migration backup files")
        self.logger.info(f"  📁 02_old_tools/: {self.results['target_before']} migration backup files")
        
        if self.results['source_before'] == 0:
            self.logger.info("✅ No migration backup files found to move")
            return
        
        # Create target directory structure
        migration_target = self.target_dir / "migration_backups"
        migration_target.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"📁 Created target directory: {migration_target}")
        
        # Move files
        moved_count = 0
        error_count = 0
        
        self.logger.info(f"🚀 Starting move of {len(source_files)} files...")
        
        for i, file_path in enumerate(source_files, 1):
            try:
                # Calculate relative path
                relative_path = file_path.relative_to(self.source_dir)
                dest_path = migration_target / relative_path
                
                # Create parent directories
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Handle conflicts with timestamp
                if dest_path.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    stem = dest_path.stem
                    suffix = dest_path.suffix
                    dest_path = dest_path.parent / f"{stem}_moved_{timestamp}{suffix}"
                
                # Move file
                shutil.move(str(file_path), str(dest_path))
                moved_count += 1
                
                # Progress reporting
                if i % 25 == 0 or i == len(source_files):
                    self.logger.info(f"  Progress: {i}/{len(source_files)} files processed ({moved_count} moved)")
                
            except Exception as e:
                error_count += 1
                self.logger.error(f"  ❌ Failed to move {file_path.name}: {e}")
        
        self.results['files_moved'] = moved_count
        self.results['move_errors'] = error_count
        
        self.logger.info(f"📊 MOVE COMPLETED:")
        self.logger.info(f"  ✅ Files moved: {moved_count}")
        self.logger.info(f"  ❌ Errors: {error_count}")
        
        return moved_count > 0
    
    def step2_recount_files(self):
        """Step 2: Re-count files in both directories"""
        self.logger.info("=" * 80)
        self.logger.info("STEP 2: RE-COUNTING FILES AFTER MOVE")
        self.logger.info("=" * 80)
        
        # Count after move
        self.results['source_after'], _ = self.count_migration_files(self.source_dir)
        self.results['target_after'], _ = self.count_migration_files(self.target_dir)
        
        self.logger.info(f"AFTER MOVE:")
        self.logger.info(f"  📁 01_scripts/: {self.results['source_after']} migration backup files")
        self.logger.info(f"  📁 02_old_tools/: {self.results['target_after']} migration backup files")
        
        # Calculate changes
        source_reduction = self.results['source_before'] - self.results['source_after']
        target_increase = self.results['target_after'] - self.results['target_before']
        
        self.logger.info(f"CHANGES:")
        self.logger.info(f"  📉 Source reduction: {source_reduction} files")
        self.logger.info(f"  📈 Target increase: {target_increase} files")
        
        # Validate move success
        move_successful = (
            self.results['source_after'] == 0 and
            source_reduction > 0 and
            target_increase > 0
        )
        
        if move_successful:
            self.logger.info("  ✅ Move appears successful - all migration backups transferred")
        else:
            self.logger.warning("  ⚠️ Move may be incomplete - some files may remain")
        
        self.results['operation_successful'] = move_successful
        return move_successful
    
    def step3_analyze_duplicates(self):
        """Step 3: Analyze remaining files for duplicates"""
        self.logger.info("=" * 80)
        self.logger.info("STEP 3: DUPLICATE ANALYSIS IN CLEANED 01_scripts/")
        self.logger.info("=" * 80)
        
        if not self.source_dir.exists():
            self.logger.error("❌ Source directory does not exist")
            return
        
        # Get all remaining Python files
        py_files = list(self.source_dir.glob("*.py"))
        self.logger.info(f"📄 Found {len(py_files)} Python files remaining in 01_scripts/")
        
        # Categorize files
        clean_files = []
        backup_files = []
        
        for file_path in py_files:
            if file_path.name.startswith("migration_backup_"):
                backup_files.append(file_path)
            else:
                clean_files.append(file_path)
        
        self.logger.info(f"  ✅ Clean files: {len(clean_files)}")
        self.logger.info(f"  🔄 Remaining backups: {len(backup_files)}")
        
        # Analyze duplicates by base filename
        filename_groups = defaultdict(list)
        for file_path in py_files:
            # Extract base filename (remove prefixes)
            base_name = file_path.name
            if base_name.startswith("scripts__"):
                base_name = base_name[9:]  # Remove "scripts__" prefix
            elif base_name.startswith("migration_backup_"):
                # Extract the actual filename from backup naming
                parts = base_name.split("__")
                if len(parts) > 1:
                    base_name = parts[-1]  # Get the last part (actual filename)
            
            filename_groups[base_name].append(file_path)
        
        # Find duplicates
        duplicates = {name: paths for name, paths in filename_groups.items() if len(paths) > 1}
        
        if duplicates:
            self.logger.info(f"📋 DUPLICATE SETS FOUND: {len(duplicates)}")
            for base_name, paths in duplicates.items():
                self.logger.info(f"  🔄 {base_name}: {len(paths)} copies")
                for path in paths:
                    file_type = "BACKUP" if "migration_backup" in path.name else "CLEAN"
                    self.logger.info(f"    - {path.name} ({file_type})")
                
                self.results['duplicates_found'].append({
                    'base_name': base_name,
                    'count': len(paths),
                    'files': [p.name for p in paths]
                })
        else:
            self.logger.info("✅ NO DUPLICATES FOUND - All files are unique")
        
        # Store clean files list
        self.results['clean_files'] = sorted([f.name for f in clean_files])
        
        # Show clean files
        if clean_files:
            self.logger.info(f"📝 CLEAN WORKING FILES ({len(clean_files)}):")
            for clean_file in sorted(clean_files, key=lambda x: x.name):
                self.logger.info(f"  ✅ {clean_file.name}")
        
        return len(duplicates)
    
    def step4_generate_summary(self):
        """Step 4: Generate comprehensive summary"""
        self.logger.info("=" * 80)
        self.logger.info("STEP 4: COMPREHENSIVE OPERATION SUMMARY")
        self.logger.info("=" * 80)
        
        # Migration summary
        self.logger.info("🔄 MIGRATION BACKUP FILE MOVEMENT:")
        self.logger.info(f"  Files moved successfully: {self.results['files_moved']}")
        self.logger.info(f"  Move errors encountered: {self.results['move_errors']}")
        self.logger.info(f"  Source files before: {self.results['source_before']}")
        self.logger.info(f"  Source files after: {self.results['source_after']}")
        self.logger.info(f"  Target files before: {self.results['target_before']}")
        self.logger.info(f"  Target files after: {self.results['target_after']}")
        
        # Duplicate analysis
        self.logger.info("")
        self.logger.info("📋 DUPLICATE ANALYSIS:")
        if self.results['duplicates_found']:
            self.logger.info(f"  Duplicate sets remaining: {len(self.results['duplicates_found'])}")
            for dup in self.results['duplicates_found']:
                self.logger.info(f"    - {dup['base_name']}: {dup['count']} copies")
        else:
            self.logger.info("  ✅ No duplicates found in 01_scripts/")
        
        # Active project status
        self.logger.info("")
        self.logger.info("📁 01_scripts/ DIRECTORY STATUS:")
        self.logger.info(f"  Clean working files: {len(self.results['clean_files'])}")
        self.logger.info(f"  Migration backups remaining: {self.results['source_after']}")
        
        if self.results['source_after'] == 0:
            self.logger.info("  ✅ SUCCESS: Contains only active project scripts")
        else:
            self.logger.info("  ⚠️ WARNING: Still contains migration backup files")
        
        # Key working files
        important_files = ['main.py', 'config.py', 'logger.py', 'arcpy_dynamic_folder_script.py',
                          'Hybrid_Dynamic_Folder_Script.py', 'Updated_Weekly_Crime_Report.py']
        
        self.logger.info("")
        self.logger.info("🔑 KEY WORKING FILES STATUS:")
        for filename in important_files:
            if filename in self.results['clean_files']:
                self.logger.info(f"  ✅ {filename} - Present")
            else:
                self.logger.info(f"  ❓ {filename} - Not found in clean files")
        
        # Overall operation status
        self.logger.info("")
        self.logger.info("🎯 OVERALL OPERATION STATUS:")
        if self.results['operation_successful'] and len(self.results['duplicates_found']) == 0:
            self.logger.info("  🟢 COMPLETE SUCCESS: All backups moved, no duplicates, clean workspace")
        elif self.results['operation_successful']:
            self.logger.info("  🟡 PARTIAL SUCCESS: Backups moved but some duplicates remain")
        else:
            self.logger.info("  🔴 INCOMPLETE: Migration backups may still remain in 01_scripts/")
        
        return self.results['operation_successful']
    
    def generate_final_report(self):
        """Generate final detailed report"""
        report = []
        report.append("FINAL MIGRATION BACKUP PROCESSING REPORT")
        report.append("=" * 80)
        report.append(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Working Directory: {self.root_dir}")
        report.append("")
        
        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 40)
        if self.results['operation_successful']:
            report.append("✅ MIGRATION COMPLETED SUCCESSFULLY")
        else:
            report.append("⚠️ MIGRATION INCOMPLETE")
        
        report.append(f"Backup files moved: {self.results['files_moved']}")
        report.append(f"Clean working files: {len(self.results['clean_files'])}")
        report.append(f"Duplicates remaining: {len(self.results['duplicates_found'])}")
        report.append("")
        
        # Detailed Results
        report.append("DETAILED RESULTS")
        report.append("-" * 40)
        report.append("1. FILE MOVEMENT:")
        report.append(f"   Source before: {self.results['source_before']}")
        report.append(f"   Source after: {self.results['source_after']}")
        report.append(f"   Target before: {self.results['target_before']}")
        report.append(f"   Target after: {self.results['target_after']}")
        report.append(f"   Files moved: {self.results['files_moved']}")
        report.append(f"   Errors: {self.results['move_errors']}")
        report.append("")
        
        report.append("2. DUPLICATE ANALYSIS:")
        if self.results['duplicates_found']:
            for dup in self.results['duplicates_found']:
                report.append(f"   {dup['base_name']}: {dup['count']} copies")
        else:
            report.append("   No duplicates found")
        report.append("")
        
        report.append("3. CLEAN FILES IN 01_scripts/:")
        for filename in self.results['clean_files']:
            report.append(f"   - {filename}")
        
        return '\n'.join(report)
    
    def execute_complete_process(self):
        """Execute all steps in sequence"""
        self.logger.info("🚀 STARTING FINAL MIGRATION BACKUP PROCESSING")
        self.logger.info(f"📁 Working Directory: {self.root_dir}")
        self.logger.info(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Execute all steps
            self.step1_execute_move()
            self.step2_recount_files()
            self.step3_analyze_duplicates()
            success = self.step4_generate_summary()
            
            # Generate and save final report
            final_report = self.generate_final_report()
            
            report_file = self.root_dir / "final_migration_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(final_report)
            
            self.logger.info(f"📄 Final report saved to: {report_file}")
            self.logger.info(f"📅 End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"💥 Fatal error during processing: {e}")
            raise

def main():
    """Main execution function"""
    try:
        executor = FinalMigrationExecutor()
        results = executor.execute_complete_process()
        
        # Return appropriate exit code
        return 0 if results['operation_successful'] else 1
        
    except Exception as e:
        print(f"💥 Script execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())