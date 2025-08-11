#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_batch_paths.py

Comprehensive Batch File Path Update Tool

This script scans all .bat files in the current directory and subfolders for 
references to outdated paths (specifically "C:\\Users\\carucci_r\\SCRPA_LAPTOP\\scripts")
and replaces them with new root or relative paths.

Features:
- Comprehensive scanning of all .bat files in directory tree
- Multiple path replacement strategies (absolute, relative, environment-based)
- Dry-run mode for safe preview of operations
- Automatic backup creation before modifications
- Detailed logging and error handling
- Pattern-based replacement with context awareness
- Validation of path updates
- Comprehensive reporting and summary

Usage:
    # Dry run to preview changes
    python update_batch_paths.py --dry-run --verbose
    
    # Execute updates with backups
    python update_batch_paths.py --create-backups --verbose
    
    # Custom root directory
    python update_batch_paths.py --new-root "C:\\Custom\\Path" --verbose
"""

import os
import re
import shutil
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field, asdict

@dataclass
class PathUpdateConfig:
    """Configuration for batch path update operations."""
    root_directory: str
    new_root_path: str
    backup_directory: str = "batch_file_backups"
    log_file: Optional[str] = None
    dry_run: bool = False
    verbose: bool = False
    create_backups: bool = True
    use_relative_paths: bool = True
    validate_updates: bool = True
    create_summary_report: bool = True

@dataclass
class PathReplacement:
    """Represents a path replacement operation."""
    original_path: str
    new_path: str
    replacement_type: str  # 'absolute', 'relative', 'environment'
    context: str
    line_number: int
    success: bool = False
    error_message: str = ""

@dataclass
class BatchFileUpdate:
    """Represents updates to a single batch file."""
    file_path: str
    relative_path: str
    file_size: int
    backup_created: bool
    backup_path: str
    replacements: List[PathReplacement]
    total_replacements: int
    successful_replacements: int
    failed_replacements: int
    update_timestamp: str
    success: bool = False
    error_message: str = ""

@dataclass
class UpdateSummary:
    """Summary of all batch file updates."""
    session_id: str
    start_timestamp: str
    end_timestamp: str
    duration_seconds: float
    total_files_scanned: int
    files_needing_updates: int
    files_successfully_updated: int
    files_failed: int
    total_replacements_made: int
    backups_created: int
    file_updates: List[BatchFileUpdate]
    errors: List[str]
    warnings: List[str]

class BatchPathUpdater:
    """Comprehensive batch file path update system."""
    
    def __init__(self, config: PathUpdateConfig):
        self.config = config
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self.start_time = datetime.now()
        
        # Tracking
        self.file_updates: List[BatchFileUpdate] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Setup logging
        self._setup_logging()
        
        # Path patterns to find and replace
        self.old_path_patterns = [
            r'C:\\Users\\carucci_r\\SCRPA_LAPTOP\\scripts',
            r'C:\Users\carucci_r\SCRPA_LAPTOP\scripts',
            r'"C:\\Users\\carucci_r\\SCRPA_LAPTOP\\scripts"',
            r'"C:\Users\carucci_r\SCRPA_LAPTOP\scripts"',
            r'C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects',
            r'C:\Users\carucci_r\SCRPA_LAPTOP\projects',
            r'"C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects"',
            r'"C:\Users\carucci_r\SCRPA_LAPTOP\projects"',
            r'C:\\Users\\carucci_r\\SCRPA_LAPTOP',
            r'C:\Users\carucci_r\SCRPA_LAPTOP',
            r'"C:\\Users\\carucci_r\\SCRPA_LAPTOP"',
            r'"C:\Users\carucci_r\SCRPA_LAPTOP"'
        ]
        
        # Replacement strategies
        self.replacement_strategies = {
            'scripts': {
                'relative': './scripts',
                'absolute': os.path.join(self.config.new_root_path, 'scripts'),
                'environment': '%SCRPA_ROOT%\\scripts'
            },
            'projects': {
                'relative': './09_arcvive',
                'absolute': os.path.join(self.config.new_root_path, '09_arcvive'),
                'environment': '%SCRPA_ROOT%\\09_arcvive'
            },
            'root': {
                'relative': '.',
                'absolute': self.config.new_root_path,
                'environment': '%SCRPA_ROOT%'
            }
        }
    
    def _setup_logging(self):
        """Setup comprehensive logging system."""
        log_level = logging.DEBUG if self.config.verbose else logging.INFO
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [BATCH_UPDATER:%(funcName)s:%(lineno)d] - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Setup logger
        self.logger = logging.getLogger('BatchPathUpdater')
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if self.config.log_file:
            try:
                log_path = Path(self.config.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(self.config.log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(detailed_formatter)
                self.logger.addHandler(file_handler)
                
                self.logger.info(f"Log file created: {self.config.log_file}")
            except Exception as e:
                self.logger.warning(f"Could not create log file {self.config.log_file}: {e}")
        
        # Log session start
        mode = "DRY RUN" if self.config.dry_run else "LIVE UPDATE"
        self.logger.info(f"Batch Path Update started - Session: {self.session_id} - Mode: {mode}")
    
    def scan_batch_files(self) -> List[str]:
        """Scan for all .bat files in the directory tree."""
        root_path = Path(self.config.root_directory)
        batch_files = []
        
        self.logger.info(f"Scanning for .bat files in: {root_path}")
        
        try:
            # Find all .bat files recursively
            bat_files = list(root_path.rglob("*.bat"))
            
            for bat_file in bat_files:
                if bat_file.is_file():
                    batch_files.append(str(bat_file))
                    self.logger.debug(f"Found batch file: {bat_file.relative_to(root_path)}")
            
            self.logger.info(f"Found {len(batch_files)} batch files")
            return batch_files
            
        except Exception as e:
            error_msg = f"Error scanning for batch files: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            return []
    
    def analyze_batch_file(self, file_path: str) -> List[PathReplacement]:
        """Analyze a batch file for path references that need updating."""
        replacements = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()
                
                # Check each pattern
                for pattern in self.old_path_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Determine replacement type based on context
                        replacement_type, new_path = self._determine_replacement(line, pattern)
                        
                        replacement = PathReplacement(
                            original_path=pattern,
                            new_path=new_path,
                            replacement_type=replacement_type,
                            context=line.strip(),
                            line_number=line_num
                        )
                        replacements.append(replacement)
                        
                        self.logger.debug(f"Found replacement needed in {Path(file_path).name}:{line_num}")
        
        except Exception as e:
            error_msg = f"Error analyzing {file_path}: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
        
        return replacements
    
    def _determine_replacement(self, line: str, pattern: str) -> Tuple[str, str]:
        """Determine the appropriate replacement strategy for a path."""
        line_lower = line.lower()
        
        # Determine what type of path we're dealing with
        if 'scripts' in pattern.lower():
            path_type = 'scripts'
        elif 'projects' in pattern.lower():
            path_type = 'projects'
        else:
            path_type = 'root'
        
        # Choose replacement strategy
        if self.config.use_relative_paths:
            replacement_type = 'relative'
            new_path = self.replacement_strategies[path_type]['relative']
        else:
            replacement_type = 'absolute'
            new_path = self.replacement_strategies[path_type]['absolute']
        
        # Handle quoted paths
        if pattern.startswith('"') and pattern.endswith('"'):
            new_path = f'"{new_path}"'
        
        return replacement_type, new_path
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """Create backup of batch file before modification."""
        if not self.config.create_backups:
            return None
        
        try:
            file_path_obj = Path(file_path)
            backup_dir = Path(self.config.root_directory) / self.config.backup_directory
            
            # Create backup directory
            if not self.config.dry_run:
                backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{file_path_obj.stem}_backup_{timestamp}{file_path_obj.suffix}"
            backup_path = backup_dir / backup_filename
            
            if not self.config.dry_run:
                shutil.copy2(file_path, backup_path)
                self.logger.debug(f"Backup created: {backup_path}")
            else:
                self.logger.debug(f"[DRY RUN] Would create backup: {backup_path}")
            
            return str(backup_path)
            
        except Exception as e:
            self.logger.warning(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def update_batch_file(self, file_path: str, replacements: List[PathReplacement]) -> BatchFileUpdate:
        """Update a single batch file with path replacements."""
        file_path_obj = Path(file_path)
        root_path = Path(self.config.root_directory)
        
        # Create file update record
        file_update = BatchFileUpdate(
            file_path=file_path,
            relative_path=str(file_path_obj.relative_to(root_path)),
            file_size=file_path_obj.stat().st_size if file_path_obj.exists() else 0,
            backup_created=False,
            backup_path="",
            replacements=replacements,
            total_replacements=len(replacements),
            successful_replacements=0,
            failed_replacements=0,
            update_timestamp=datetime.now().isoformat()
        )
        
        try:
            self.logger.info(f"Updating batch file: {file_update.relative_path}")
            
            # Create backup
            backup_path = self.create_backup(file_path)
            if backup_path:
                file_update.backup_created = True
                file_update.backup_path = backup_path
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            
            # Apply replacements
            for replacement in replacements:
                try:
                    # Use regex replacement with case-insensitive matching
                    pattern_escaped = re.escape(replacement.original_path)
                    new_content = re.sub(pattern_escaped, replacement.new_path, content, flags=re.IGNORECASE)
                    
                    if new_content != content:
                        content = new_content
                        replacement.success = True
                        file_update.successful_replacements += 1
                        self.logger.debug(f"Replaced: {replacement.original_path} -> {replacement.new_path}")
                    else:
                        replacement.error_message = "Pattern not found for replacement"
                        file_update.failed_replacements += 1
                        
                except Exception as e:
                    replacement.success = False
                    replacement.error_message = str(e)
                    file_update.failed_replacements += 1
                    self.logger.error(f"Failed to replace {replacement.original_path}: {e}")
            
            # Write updated content
            if content != original_content:
                if not self.config.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Validate if requested
                    if self.config.validate_updates:
                        self._validate_batch_file_update(file_path, file_update)
                    
                    self.logger.info(f"Updated {file_update.successful_replacements} paths in {file_update.relative_path}")
                else:
                    self.logger.info(f"[DRY RUN] Would update {file_update.successful_replacements} paths in {file_update.relative_path}")
                
                file_update.success = True
            else:
                self.logger.info(f"No changes needed for {file_update.relative_path}")
                file_update.success = True
                
        except Exception as e:
            file_update.success = False
            file_update.error_message = str(e)
            error_msg = f"Failed to update {file_update.relative_path}: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
        
        return file_update
    
    def _validate_batch_file_update(self, file_path: str, file_update: BatchFileUpdate):
        """Validate that batch file updates were applied correctly."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check that old paths are no longer present
            for pattern in self.old_path_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    warning_msg = f"Old path pattern still found in {file_update.relative_path}: {pattern}"
                    self.logger.warning(warning_msg)
                    self.warnings.append(warning_msg)
            
            self.logger.debug(f"Validation completed for {file_update.relative_path}")
            
        except Exception as e:
            self.logger.warning(f"Validation failed for {file_path}: {e}")
    
    def execute_updates(self) -> UpdateSummary:
        """Execute the complete batch file update process."""
        self.logger.info("Starting batch file path update process")
        
        try:
            # Phase 1: Scan for batch files
            self.logger.info("Phase 1: Scanning for batch files")
            batch_files = self.scan_batch_files()
            
            if not batch_files:
                self.logger.warning("No batch files found to process")
            
            # Phase 2: Analyze and update files
            self.logger.info("Phase 2: Analyzing and updating files")
            
            files_needing_updates = 0
            files_successfully_updated = 0
            files_failed = 0
            total_replacements = 0
            backups_created = 0
            
            for file_path in batch_files:
                # Analyze file for needed replacements
                replacements = self.analyze_batch_file(file_path)
                
                if replacements:
                    files_needing_updates += 1
                    
                    # Update the file
                    file_update = self.update_batch_file(file_path, replacements)
                    self.file_updates.append(file_update)
                    
                    # Update counters
                    total_replacements += file_update.successful_replacements
                    
                    if file_update.backup_created:
                        backups_created += 1
                    
                    if file_update.success:
                        files_successfully_updated += 1
                    else:
                        files_failed += 1
            
            # Phase 3: Generate summary
            self.logger.info("Phase 3: Generating update summary")
            
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            
            summary = UpdateSummary(
                session_id=self.session_id,
                start_timestamp=self.start_time.isoformat(),
                end_timestamp=end_time.isoformat(),
                duration_seconds=round(duration, 3),
                total_files_scanned=len(batch_files),
                files_needing_updates=files_needing_updates,
                files_successfully_updated=files_successfully_updated,
                files_failed=files_failed,
                total_replacements_made=total_replacements,
                backups_created=backups_created,
                file_updates=self.file_updates,
                errors=self.errors,
                warnings=self.warnings
            )
            
            # Save summary report if requested
            if self.config.create_summary_report:
                self.save_summary_report(summary)
            
            self.logger.info("Batch file path update process completed")
            return summary
            
        except Exception as e:
            error_msg = f"Critical error during batch update: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            
            # Generate error summary
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            
            summary = UpdateSummary(
                session_id=self.session_id,
                start_timestamp=self.start_time.isoformat(),
                end_timestamp=end_time.isoformat(),
                duration_seconds=round(duration, 3),
                total_files_scanned=0,
                files_needing_updates=0,
                files_successfully_updated=0,
                files_failed=0,
                total_replacements_made=0,
                backups_created=0,
                file_updates=self.file_updates,
                errors=self.errors,
                warnings=self.warnings
            )
            
            return summary
    
    def save_summary_report(self, summary: UpdateSummary) -> Optional[str]:
        """Save detailed summary report to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"batch_path_update_summary_{timestamp}.json"
            report_path = Path(self.config.root_directory) / report_filename
            
            # Convert to serializable format
            summary_dict = asdict(summary)
            
            # Add configuration metadata
            summary_dict['update_config'] = {
                'root_directory': self.config.root_directory,
                'new_root_path': self.config.new_root_path,
                'dry_run': self.config.dry_run,
                'use_relative_paths': self.config.use_relative_paths,
                'create_backups': self.config.create_backups
            }
            
            if not self.config.dry_run:
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(summary_dict, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Summary report saved: {report_path}")
                return str(report_path)
            else:
                self.logger.info(f"[DRY RUN] Would save summary report: {report_path}")
                return str(report_path)
                
        except Exception as e:
            self.logger.warning(f"Failed to save summary report: {e}")
            return None
    
    def print_update_summary(self, summary: UpdateSummary):
        """Print comprehensive update summary to console."""
        print(f"\n{'='*80}")
        print("BATCH FILE PATH UPDATE SUMMARY")
        print(f"{'='*80}")
        print(f"Session ID: {summary.session_id}")
        print(f"Duration: {summary.duration_seconds:.3f} seconds")
        print(f"Mode: {'DRY RUN' if self.config.dry_run else 'LIVE UPDATE'}")
        print()
        
        print("UPDATE RESULTS:")
        print(f"  Total Files Scanned: {summary.total_files_scanned}")
        print(f"  Files Needing Updates: {summary.files_needing_updates}")
        print(f"  Files Successfully Updated: {summary.files_successfully_updated}")
        print(f"  Files Failed: {summary.files_failed}")
        print(f"  Total Path Replacements: {summary.total_replacements_made}")
        print(f"  Backups Created: {summary.backups_created}")
        print()
        
        # Show updated files
        if summary.file_updates:
            print("FILES UPDATED:")
            for file_update in summary.file_updates:
                status = "✅" if file_update.success else "❌"
                print(f"  {status} {file_update.relative_path}: {file_update.successful_replacements} replacements")
                
                if self.config.verbose and file_update.replacements:
                    for replacement in file_update.replacements[:3]:  # Show first 3 replacements
                        if replacement.success:
                            print(f"    ✓ Line {replacement.line_number}: {replacement.original_path} -> {replacement.new_path}")
                    if len(file_update.replacements) > 3:
                        print(f"    ... and {len(file_update.replacements) - 3} more replacements")
            print()
        
        # Show warnings
        if summary.warnings:
            print("WARNINGS:")
            for warning in summary.warnings[:5]:  # Show first 5 warnings
                print(f"  ⚠️  {warning}")
            if len(summary.warnings) > 5:
                print(f"  ... and {len(summary.warnings) - 5} more warnings")
            print()
        
        # Show errors
        if summary.errors:
            print("ERRORS:")
            for error in summary.errors[:5]:  # Show first 5 errors
                print(f"  ❌ {error}")
            if len(summary.errors) > 5:
                print(f"  ... and {len(summary.errors) - 5} more errors")
            print()
        
        # Final status
        if summary.files_failed == 0:
            print("✅ BATCH PATH UPDATE COMPLETED SUCCESSFULLY")
        else:
            print(f"⚠️  BATCH PATH UPDATE COMPLETED WITH {summary.files_failed} FAILURES")
        
        print(f"{'='*80}")

def create_default_config() -> PathUpdateConfig:
    """Create default configuration for batch path updates."""
    current_dir = os.getcwd()
    
    config = PathUpdateConfig(
        root_directory=current_dir,
        new_root_path=current_dir,
        backup_directory="batch_file_backups",
        dry_run=False,
        verbose=False,
        create_backups=True,
        use_relative_paths=True,
        validate_updates=True,
        create_summary_report=True
    )
    
    return config

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Batch File Path Update Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview changes
  python update_batch_paths.py --dry-run --verbose
  
  # Execute updates with backups and detailed logging
  python update_batch_paths.py --create-backups --verbose --log-file update.log
  
  # Use absolute paths instead of relative
  python update_batch_paths.py --use-absolute-paths --verbose
  
  # Custom new root path
  python update_batch_paths.py --new-root "C:\\Custom\\Path" --verbose
        """
    )
    
    # Directory options
    parser.add_argument('--root-dir', '-r',
                       default=None,
                       help='Root directory to scan (default: current directory)')
    
    parser.add_argument('--new-root', '-n',
                       default=None,
                       help='New root path for replacements (default: current directory)')
    
    # Operation options
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Preview changes without executing them')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    parser.add_argument('--log-file', '-l',
                       help='Save detailed log to specified file')
    
    parser.add_argument('--create-backups', '-b', action='store_true', default=True,
                       help='Create backups before modifying files (default: True)')
    
    parser.add_argument('--no-backups', action='store_true',
                       help='Skip backup creation')
    
    parser.add_argument('--use-absolute-paths', action='store_true',
                       help='Use absolute paths instead of relative paths')
    
    parser.add_argument('--no-validation', action='store_true',
                       help='Skip validation of updates')
    
    parser.add_argument('--no-summary', action='store_true',
                       help='Skip creation of summary report')
    
    args = parser.parse_args()
    
    try:
        # Create configuration
        config = create_default_config()
        
        # Override with command line arguments
        if args.root_dir:
            config.root_directory = args.root_dir
        if args.new_root:
            config.new_root_path = args.new_root
        if args.log_file:
            config.log_file = args.log_file
        
        config.dry_run = args.dry_run
        config.verbose = args.verbose
        config.create_backups = not args.no_backups and args.create_backups
        config.use_relative_paths = not args.use_absolute_paths
        config.validate_updates = not args.no_validation
        config.create_summary_report = not args.no_summary
        
        # Validate directories
        if not os.path.exists(config.root_directory):
            print(f"❌ ERROR: Root directory does not exist: {config.root_directory}")
            return 1
        
        # Show configuration
        print("BATCH FILE PATH UPDATE TOOL")
        print("=" * 80)
        print(f"Root Directory: {config.root_directory}")
        print(f"New Root Path: {config.new_root_path}")
        print(f"Mode: {'DRY RUN' if config.dry_run else 'LIVE UPDATE'}")
        print(f"Path Type: {'Relative' if config.use_relative_paths else 'Absolute'}")
        print(f"Create Backups: {'Yes' if config.create_backups else 'No'}")
        print(f"Validate Updates: {'Yes' if config.validate_updates else 'No'}")
        if config.log_file:
            print(f"Log File: {config.log_file}")
        print("=" * 80)
        
        # Confirm execution if not dry run
        if not config.dry_run:
            confirm = input("\nProceed with batch file updates? (y/N): ").lower().strip()
            if confirm not in ['y', 'yes']:
                print("Batch update cancelled by user")
                return 0
        
        # Execute updates
        updater = BatchPathUpdater(config)
        summary = updater.execute_updates()
        
        # Display results
        updater.print_update_summary(summary)
        
        # Return appropriate exit code
        if summary.files_failed == 0:
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n❌ Batch update interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())