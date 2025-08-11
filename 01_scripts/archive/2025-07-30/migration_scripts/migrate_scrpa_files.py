#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_scrpa_files.py

SCRPA Files Migration Tool

This script migrates Python scripts, Markdown files, and related documentation 
from the SCRPA_LAPTOP\scripts directory to the current directory structure.

Features:
- Moves Python (*.py), Markdown (*.md), Batch (*.bat), and JSON (*.json) files
- Handles conflicts by renaming duplicates with timestamps
- Organized destination structure with appropriate subfolders
- Comprehensive error handling and logging
- Dry-run mode for safe preview of operations
- Optional backup creation before migration
- Progress tracking and detailed reporting

Usage:
    # Dry run to preview migration
    python migrate_scrpa_files.py --dry-run --verbose
    
    # Execute migration with backups
    python migrate_scrpa_files.py --create-backups --verbose
    
    # Custom source and destination
    python migrate_scrpa_files.py --source "C:\Custom\Path" --verbose
"""

import os
import sys
import shutil
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field, asdict

@dataclass
class MigrationConfig:
    """Configuration for file migration operations."""
    source_directory: str
    destination_directory: str
    create_backups: bool = False
    backup_directory: str = "migration_backups"
    log_file: Optional[str] = None
    dry_run: bool = False
    verbose: bool = False
    organize_by_type: bool = True
    handle_conflicts: bool = True
    create_migration_report: bool = True

@dataclass
class FileOperation:
    """Represents a file migration operation."""
    operation_type: str  # 'move', 'copy', 'skip', 'rename'
    source_path: str
    destination_path: str
    file_type: str
    file_size: int
    timestamp: str
    success: bool = False
    error_message: str = ""
    conflict_resolution: str = ""

@dataclass
class MigrationResult:
    """Result of migration operations."""
    session_id: str
    start_timestamp: str
    end_timestamp: str
    duration_seconds: float
    total_files_found: int
    files_migrated: int
    files_skipped: int
    files_failed: int
    conflicts_resolved: int
    backups_created: int
    operations: List[FileOperation]
    errors: List[str]
    warnings: List[str]
    destination_structure: Dict[str, List[str]]

class SCRPAFileMigrator:
    """Comprehensive file migration system for SCRPA scripts and documentation."""
    
    def __init__(self, config: MigrationConfig):
        self.config = config
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self.start_time = datetime.now()
        
        # File operation tracking
        self.operations: List[FileOperation] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.destination_structure: Dict[str, List[str]] = {}
        
        # Setup logging
        self._setup_logging()
        
        # File patterns to migrate
        self.file_patterns = {
            'python': '*.py',
            'markdown': '*.md',
            'batch': '*.bat',
            'json': '*.json',
            'text': '*.txt',
            'config': '*.ini'
        }
        
        # Destination subfolder mapping
        self.destination_mapping = {
            'python': 'scripts',
            'markdown': 'documentation', 
            'batch': 'scripts',
            'json': 'config',
            'text': 'documentation',
            'config': 'config'
        }
        
        # Files to handle specially (core PBIX tools)
        self.priority_files = [
            'update_pbix_parameter.py',
            'main_workflow.py',
            'cleanup_scrpa_scripts.py',
            'test_pbix_update.py',
            'demo_rollback_scenarios.py',
            'USAGE_EXAMPLES.md',
            'README.md'
        ]
        
        # Files to exclude from migration
        self.exclude_patterns = [
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '.git',
            '.gitignore',
            'desktop.ini',
            'Thumbs.db'
        ]
    
    def _setup_logging(self):
        """Setup comprehensive logging system."""
        # Determine log level
        log_level = logging.DEBUG if self.config.verbose else logging.INFO
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [MIGRATION:%(funcName)s:%(lineno)d] - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Setup logger
        self.logger = logging.getLogger('SCRPAMigration')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if self.config.log_file:
            try:
                # Ensure log directory exists
                log_path = Path(self.config.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(self.config.log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(detailed_formatter)
                self.logger.addHandler(file_handler)
                
                self.logger.info(f"Migration log file created: {self.config.log_file}")
            except Exception as e:
                self.logger.warning(f"Could not create log file {self.config.log_file}: {e}")
        
        # Log session start
        mode = "DRY RUN" if self.config.dry_run else "LIVE MIGRATION"
        self.logger.info(f"SCRPA File Migration started - Session: {self.session_id} - Mode: {mode}")
    
    def scan_source_files(self) -> Dict[str, List[Tuple[str, str]]]:
        """Scan source directory for files to migrate."""
        source_path = Path(self.config.source_directory)
        files_by_type = {file_type: [] for file_type in self.file_patterns.keys()}
        
        self.logger.info(f"Scanning source directory: {source_path}")
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {source_path}")
        
        # Scan for each file type
        for file_type, pattern in self.file_patterns.items():
            pattern_files = list(source_path.rglob(pattern))
            
            for file_path in pattern_files:
                # Skip excluded patterns
                if any(exclude in str(file_path) for exclude in self.exclude_patterns):
                    continue
                
                # Skip directories
                if not file_path.is_file():
                    continue
                
                relative_path = file_path.relative_to(source_path)
                files_by_type[file_type].append((str(file_path), str(relative_path)))
                
                self.logger.debug(f"Found {file_type} file: {relative_path}")
        
        # Log summary
        total_files = sum(len(files) for files in files_by_type.values())
        self.logger.info(f"Scan complete: {total_files} files found")
        for file_type, files in files_by_type.items():
            if files:
                self.logger.info(f"  {file_type}: {len(files)} files")
        
        return files_by_type
    
    def create_destination_structure(self):
        """Create destination directory structure."""
        dest_path = Path(self.config.destination_directory)
        
        self.logger.info("Creating destination directory structure")
        
        if not self.config.dry_run:
            try:
                dest_path.mkdir(parents=True, exist_ok=True)
                
                # Create organized subfolders if configured
                if self.config.organize_by_type:
                    for folder in set(self.destination_mapping.values()):
                        folder_path = dest_path / folder
                        folder_path.mkdir(exist_ok=True)
                        self.logger.debug(f"Created directory: {folder_path}")
                
                # Create backup directory if needed
                if self.config.create_backups:
                    backup_path = dest_path / self.config.backup_directory
                    backup_path.mkdir(exist_ok=True)
                    self.logger.info(f"Created backup directory: {backup_path}")
                    
            except Exception as e:
                error_msg = f"Failed to create destination structure: {e}"
                self.logger.error(error_msg)
                self.errors.append(error_msg)
                raise
        else:
            self.logger.info("[DRY RUN] Would create destination directory structure")
    
    def resolve_file_conflict(self, dest_path: Path) -> Tuple[Path, str]:
        """Resolve file naming conflicts by adding timestamps."""
        if not dest_path.exists():
            return dest_path, "no_conflict"
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = dest_path.stem
        suffix = dest_path.suffix
        
        # Try with timestamp
        new_name = f"{stem}_{timestamp}{suffix}"
        new_path = dest_path.parent / new_name
        
        # If still conflicts, add incrementing number
        counter = 1
        while new_path.exists():
            new_name = f"{stem}_{timestamp}_{counter:02d}{suffix}"
            new_path = dest_path.parent / new_name
            counter += 1
        
        self.logger.info(f"Conflict resolved: {dest_path.name} -> {new_path.name}")
        return new_path, f"renamed_to_{new_path.name}"
    
    def determine_destination_path(self, source_file: str, relative_path: str, file_type: str) -> Path:
        """Determine the appropriate destination path for a file."""
        dest_base = Path(self.config.destination_directory)
        source_path = Path(source_file)
        
        # Handle priority files (place in root or special location)
        if source_path.name in self.priority_files:
            if file_type == 'python':
                # Priority Python files go to scripts subfolder
                dest_path = dest_base / "scripts" / source_path.name
            else:
                # Priority documentation goes to documentation subfolder
                dest_path = dest_base / "documentation" / source_path.name
        else:
            # Organize by type if configured
            if self.config.organize_by_type:
                subfolder = self.destination_mapping.get(file_type, 'misc')
                
                # Preserve some directory structure for archived files
                rel_path = Path(relative_path)
                if 'archived' in str(rel_path).lower():
                    dest_path = dest_base / subfolder / "archived" / rel_path.name
                else:
                    dest_path = dest_base / subfolder / rel_path.name
            else:
                # Preserve full relative path
                dest_path = dest_base / relative_path
        
        return dest_path
    
    def create_backup(self, source_file: str) -> Optional[str]:
        """Create backup of source file before migration."""
        if not self.config.create_backups:
            return None
        
        try:
            source_path = Path(source_file)
            backup_dir = Path(self.config.destination_directory) / self.config.backup_directory
            
            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{source_path.stem}_backup_{timestamp}{source_path.suffix}"
            backup_path = backup_dir / backup_filename
            
            if not self.config.dry_run:
                shutil.copy2(source_file, backup_path)
                self.logger.debug(f"Backup created: {backup_path}")
                return str(backup_path)
            else:
                self.logger.debug(f"[DRY RUN] Would create backup: {backup_path}")
                return str(backup_path)
                
        except Exception as e:
            self.logger.warning(f"Failed to create backup for {source_file}: {e}")
            return None
    
    def migrate_file(self, source_file: str, relative_path: str, file_type: str) -> FileOperation:
        """Migrate a single file to the destination."""
        source_path = Path(source_file)
        
        # Create file operation record
        operation = FileOperation(
            operation_type="move",
            source_path=source_file,
            destination_path="",
            file_type=file_type,
            file_size=source_path.stat().st_size if source_path.exists() else 0,
            timestamp=datetime.now().isoformat(),
            success=False
        )
        
        try:
            # Determine destination path
            dest_path = self.determine_destination_path(source_file, relative_path, file_type)
            
            # Ensure destination directory exists
            if not self.config.dry_run:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle conflicts if needed
            if self.config.handle_conflicts and dest_path.exists():
                dest_path, conflict_resolution = self.resolve_file_conflict(dest_path)
                operation.conflict_resolution = conflict_resolution
            
            operation.destination_path = str(dest_path)
            
            # Create backup if requested
            backup_path = self.create_backup(source_file)
            
            # Perform the migration
            if self.config.dry_run:
                self.logger.info(f"[DRY RUN] Would move: {relative_path} -> {dest_path.relative_to(Path(self.config.destination_directory))}")
                operation.success = True
            else:
                # Move the file
                shutil.move(source_file, dest_path)
                operation.success = True
                self.logger.debug(f"Migrated: {relative_path} -> {dest_path.relative_to(Path(self.config.destination_directory))}")
                
                # Track destination structure
                folder = str(dest_path.parent.relative_to(Path(self.config.destination_directory)))
                if folder not in self.destination_structure:
                    self.destination_structure[folder] = []
                self.destination_structure[folder].append(dest_path.name)
        
        except Exception as e:
            operation.success = False
            operation.error_message = str(e)
            error_msg = f"Failed to migrate {relative_path}: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
        
        return operation
    
    def execute_migration(self) -> MigrationResult:
        """Execute the complete file migration process."""
        self.logger.info("Starting SCRPA file migration process")
        
        try:
            # Phase 1: Scan source files
            self.logger.info("Phase 1: Scanning source files")
            files_by_type = self.scan_source_files()
            
            # Phase 2: Create destination structure
            self.logger.info("Phase 2: Creating destination structure")
            self.create_destination_structure()
            
            # Phase 3: Migrate files
            self.logger.info("Phase 3: Migrating files")
            
            migrated_count = 0
            failed_count = 0
            skipped_count = 0
            conflicts_resolved = 0
            backups_created = 0
            
            # Process each file type
            for file_type, files in files_by_type.items():
                if not files:
                    continue
                
                self.logger.info(f"Migrating {len(files)} {file_type} files...")
                
                for source_file, relative_path in files:
                    operation = self.migrate_file(source_file, relative_path, file_type)
                    self.operations.append(operation)
                    
                    if operation.success:
                        migrated_count += 1
                        if operation.conflict_resolution and operation.conflict_resolution != "no_conflict":
                            conflicts_resolved += 1
                    else:
                        failed_count += 1
            
            # Calculate backups created
            backups_created = sum(1 for op in self.operations if self.config.create_backups and op.success)
            
            # Phase 4: Generate migration result
            self.logger.info("Phase 4: Generating migration summary")
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            
            total_files = sum(len(files) for files in files_by_type.values())
            
            migration_result = MigrationResult(
                session_id=self.session_id,
                start_timestamp=self.start_time.isoformat(),
                end_timestamp=end_time.isoformat(),
                duration_seconds=round(duration, 3),
                total_files_found=total_files,
                files_migrated=migrated_count,
                files_skipped=skipped_count,
                files_failed=failed_count,
                conflicts_resolved=conflicts_resolved,
                backups_created=backups_created,
                operations=self.operations,
                errors=self.errors,
                warnings=self.warnings,
                destination_structure=self.destination_structure
            )
            
            # Save migration report if requested
            if self.config.create_migration_report:
                self.save_migration_report(migration_result)
            
            self.logger.info("SCRPA file migration completed")
            return migration_result
            
        except Exception as e:
            error_msg = f"Critical error during migration: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            
            # Generate error result
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            
            migration_result = MigrationResult(
                session_id=self.session_id,
                start_timestamp=self.start_time.isoformat(),
                end_timestamp=end_time.isoformat(),
                duration_seconds=round(duration, 3),
                total_files_found=0,
                files_migrated=0,
                files_skipped=0,
                files_failed=0,
                conflicts_resolved=0,
                backups_created=0,
                operations=self.operations,
                errors=self.errors,
                warnings=self.warnings,
                destination_structure={}
            )
            
            return migration_result
    
    def save_migration_report(self, migration_result: MigrationResult) -> Optional[str]:
        """Save detailed migration report to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"scrpa_migration_report_{timestamp}.json"
            report_path = Path(self.config.destination_directory) / report_filename
            
            # Convert to serializable format
            report_dict = asdict(migration_result)
            
            # Add additional metadata
            report_dict['migration_config'] = {
                'source_directory': self.config.source_directory,
                'destination_directory': self.config.destination_directory,
                'dry_run': self.config.dry_run,
                'create_backups': self.config.create_backups,
                'organize_by_type': self.config.organize_by_type
            }
            
            if not self.config.dry_run:
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report_dict, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Migration report saved: {report_path}")
                return str(report_path)
            else:
                self.logger.info(f"[DRY RUN] Would save migration report: {report_path}")
                return str(report_path)
                
        except Exception as e:
            self.logger.warning(f"Failed to save migration report: {e}")
            return None
    
    def print_migration_summary(self, migration_result: MigrationResult):
        """Print comprehensive migration summary to console."""
        print(f"\n{'='*80}")
        print("SCRPA FILE MIGRATION SUMMARY")
        print(f"{'='*80}")
        print(f"Session ID: {migration_result.session_id}")
        print(f"Duration: {migration_result.duration_seconds:.3f} seconds")
        print(f"Mode: {'DRY RUN' if self.config.dry_run else 'LIVE MIGRATION'}")
        print()
        
        print("MIGRATION RESULTS:")
        print(f"  Total Files Found: {migration_result.total_files_found}")
        print(f"  Files Migrated: {migration_result.files_migrated}")
        print(f"  Files Failed: {migration_result.files_failed}")
        print(f"  Conflicts Resolved: {migration_result.conflicts_resolved}")
        print(f"  Backups Created: {migration_result.backups_created}")
        print()
        
        # Show destination structure
        if migration_result.destination_structure:
            print("DESTINATION STRUCTURE:")
            for folder, files in migration_result.destination_structure.items():
                folder_display = folder if folder != "." else "(root)"
                print(f"  {folder_display}/ ({len(files)} files)")
                if self.config.verbose and files:
                    for file_name in sorted(files)[:5]:  # Show first 5 files
                        print(f"    - {file_name}")
                    if len(files) > 5:
                        print(f"    ... and {len(files) - 5} more files")
            print()
        
        # Show priority files status
        priority_files_migrated = []
        for operation in migration_result.operations:
            if Path(operation.source_path).name in self.priority_files and operation.success:
                priority_files_migrated.append(Path(operation.source_path).name)
        
        if priority_files_migrated:
            print("PRIORITY FILES MIGRATED:")
            for file_name in priority_files_migrated:
                print(f"  ✅ {file_name}")
            print()
        
        # Show errors if any
        if migration_result.errors:
            print("ERRORS ENCOUNTERED:")
            for error in migration_result.errors[:5]:  # Show first 5 errors
                print(f"  ❌ {error}")
            if len(migration_result.errors) > 5:
                print(f"  ... and {len(migration_result.errors) - 5} more errors")
            print()
        
        # Final status
        if migration_result.files_failed == 0:
            print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        else:
            print(f"⚠️  MIGRATION COMPLETED WITH {migration_result.files_failed} FAILURES")
        
        print(f"{'='*80}")

def create_default_config() -> MigrationConfig:
    """Create default migration configuration."""
    current_dir = os.getcwd()
    
    config = MigrationConfig(
        source_directory=r"C:\Users\carucci_r\SCRPA_LAPTOP\scripts",
        destination_directory=current_dir,
        create_backups=False,
        backup_directory="migration_backups",
        dry_run=False,
        verbose=False,
        organize_by_type=True,
        handle_conflicts=True,
        create_migration_report=True
    )
    
    return config

def main():
    """Main migration execution function."""
    parser = argparse.ArgumentParser(
        description="SCRPA Files Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview migration
  python migrate_scrpa_files.py --dry-run --verbose
  
  # Execute migration with backups and detailed logging
  python migrate_scrpa_files.py --create-backups --verbose --log-file migration.log
  
  # Custom source directory
  python migrate_scrpa_files.py --source "C:\\Custom\\Path" --verbose
  
  # Simple migration without organization
  python migrate_scrpa_files.py --no-organize --verbose
        """
    )
    
    # Source and destination options
    parser.add_argument('--source', '-s',
                       default=r"C:\Users\carucci_r\SCRPA_LAPTOP\scripts",
                       help='Source directory containing files to migrate')
    
    parser.add_argument('--destination', '-d',
                       default=None,
                       help='Destination directory (default: current directory)')
    
    # Operation options
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Preview migration without executing')
    
    parser.add_argument('--create-backups', '-b', action='store_true',
                       help='Create backups of source files before migration')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    parser.add_argument('--log-file', '-l',
                       help='Save detailed log to specified file')
    
    parser.add_argument('--no-organize', action='store_true',
                       help='Do not organize files by type into subfolders')
    
    parser.add_argument('--no-conflicts', action='store_true',
                       help='Skip conflict resolution (may overwrite files)')
    
    parser.add_argument('--no-report', action='store_true',
                       help='Skip creation of migration report')
    
    args = parser.parse_args()
    
    try:
        # Create configuration
        config = create_default_config()
        
        # Override with command line arguments
        config.source_directory = args.source
        if args.destination:
            config.destination_directory = args.destination
        if args.log_file:
            config.log_file = args.log_file
        
        config.dry_run = args.dry_run
        config.verbose = args.verbose
        config.create_backups = args.create_backups
        config.organize_by_type = not args.no_organize
        config.handle_conflicts = not args.no_conflicts
        config.create_migration_report = not args.no_report
        
        # Validate source directory
        if not os.path.exists(config.source_directory):
            print(f"❌ ERROR: Source directory does not exist: {config.source_directory}")
            return 1
        
        # Show configuration
        print("SCRPA FILE MIGRATION TOOL")
        print("=" * 80)
        print(f"Source Directory: {config.source_directory}")
        print(f"Destination Directory: {config.destination_directory}")
        print(f"Mode: {'DRY RUN' if config.dry_run else 'LIVE MIGRATION'}")
        print(f"Create Backups: {'Yes' if config.create_backups else 'No'}")
        print(f"Organize by Type: {'Yes' if config.organize_by_type else 'No'}")
        print(f"Handle Conflicts: {'Yes' if config.handle_conflicts else 'No'}")
        if config.log_file:
            print(f"Log File: {config.log_file}")
        print("=" * 80)
        
        # Confirm execution if not dry run
        if not config.dry_run:
            confirm = input("\nProceed with migration? (y/N): ").lower().strip()
            if confirm not in ['y', 'yes']:
                print("Migration cancelled by user")
                return 0
        
        # Execute migration
        migrator = SCRPAFileMigrator(config)
        migration_result = migrator.execute_migration()
        
        # Display results
        migrator.print_migration_summary(migration_result)
        
        # Return appropriate exit code
        if migration_result.files_failed == 0:
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n❌ Migration interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ CRITICAL MIGRATION ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())