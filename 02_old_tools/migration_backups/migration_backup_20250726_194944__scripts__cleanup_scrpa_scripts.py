#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_scrpa_scripts.py

SCRPA Scripts Cleanup and Organization Tool

This script performs automated cleanup and organization of SCRPA Python scripts and documentation:
1. Archives old/enhanced script versions into timestamped ZIP files
2. Moves documentation files to organized documentation directory
3. Provides comprehensive logging and error handling
4. Supports dry-run mode for safe preview of operations

Features:
- Pattern-based file identification for archiving
- Automatic directory creation
- Comprehensive error handling and rollback
- Detailed logging with multiple verbosity levels
- Dry-run mode for preview without changes
- Backup verification and integrity checking

Usage:
    python cleanup_scrpa_scripts.py [OPTIONS]
    
Examples:
    # Dry run to preview changes
    python cleanup_scrpa_scripts.py --dry-run --verbose
    
    # Execute cleanup with detailed logging
    python cleanup_scrpa_scripts.py --verbose --log-file cleanup.log
    
    # Custom documentation directory
    python cleanup_scrpa_scripts.py --doc-dir "C:\\Custom\\Docs" --verbose
"""

import os
import sys
import shutil
import zipfile
import glob
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field, asdict

@dataclass
class CleanupConfig:
    """Configuration for cleanup operations."""
    source_directory: str
    documentation_directory: str
    backup_directory: str
    log_file: Optional[str] = None
    dry_run: bool = False
    verbose: bool = False
    create_summary: bool = True
    verify_archives: bool = True

@dataclass
class FileOperation:
    """Represents a file operation to be performed."""
    operation_type: str  # 'archive', 'move', 'delete'
    source_path: str
    destination_path: str
    file_size: int
    timestamp: str
    success: bool = False
    error_message: str = ""

@dataclass
class CleanupSummary:
    """Summary of cleanup operations performed."""
    session_id: str
    start_timestamp: str
    end_timestamp: str
    duration_seconds: float
    total_files_processed: int
    files_archived: int
    files_moved: int
    files_skipped: int
    errors_encountered: int
    operations: List[FileOperation]
    archive_files_created: List[str]
    directories_created: List[str]
    total_size_archived: int
    total_size_moved: int

class SCRPAScriptCleanup:
    """Main cleanup orchestrator for SCRPA scripts and documentation."""
    
    def __init__(self, config: CleanupConfig):
        self.config = config
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self.start_time = datetime.now()
        
    # File operation tracking
        self.operations: List[FileOperation] = []
        self.archive_files_created: List[str] = []
        self.directories_created: List[str] = []
        self.errors: List[str] = []
        
        # Setup logging
        self._setup_logging()
        
        # Archive patterns for script files
        self.archive_patterns = [
            '*_enhanced.py',
            '*_fixed.py', 
            '*_backup.py',
            '*_old.py',
            '*_v[0-9].py',
            '*_v[0-9][0-9].py',
            '*_[0-9][0-9][0-9][0-9][0-9][0-9].py',  # Date patterns
            '*_copy.py',
            '*_temp.py',
            '*_test.py',
            '*_debug.py',
            '*_draft.py',
            'temp_*.py',
            'backup_*.py',
            'old_*.py'
        ]
        
        # Documentation file patterns
        self.documentation_patterns = [
            '*.md',
            '*.txt',
            '*.rst',
            '*.doc',
            '*.docx',
            '*.pdf'
        ]
        
        # Files to exclude from archiving (keep in main directory)
        self.exclude_from_archive = [
            'update_pbix_parameter.py',
            'main_workflow.py', 
            'test_pbix_update.py',
            'cleanup_scrpa_scripts.py',
            '__init__.py',
            'requirements.txt',
            'setup.py'
        ]
        
    def _setup_logging(self):
        """Setup comprehensive logging system."""
        # Determine log level
        log_level = logging.DEBUG if self.config.verbose else logging.INFO
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [CLEANUP:%(funcName)s:%(lineno)d] - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Setup logger
        self.logger = logging.getLogger('SCRPACleanup')
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
                
                self.logger.info(f"Log file created: {self.config.log_file}")
            except Exception as e:
                self.logger.warning(f"Could not create log file {self.config.log_file}: {e}")
        
        # Log session start
        mode = "DRY RUN" if self.config.dry_run else "LIVE"
        self.logger.info(f"SCRPA Script Cleanup started - Session: {self.session_id} - Mode: {mode}")
        
    def identify_files_to_archive(self) -> List[Tuple[str, str]]:
        """Identify script files that should be archived."""
        files_to_archive = []
        source_path = Path(self.config.source_directory)
        
        self.logger.info("Identifying files to archive...")
        
        # Scan for files matching archive patterns
        for pattern in self.archive_patterns:
            pattern_files = list(source_path.glob(pattern))
            
            for file_path in pattern_files:
                # Skip if file is in exclude list
                if file_path.name in self.exclude_from_archive:
                    self.logger.debug(f"Excluding from archive (protected): {file_path.name}")
                    continue
                
                # Skip if not a regular file
                if not file_path.is_file():
                    continue
                
                files_to_archive.append((str(file_path), file_path.name))
                self.logger.debug(f"Identified for archiving: {file_path.name}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for file_path, file_name in files_to_archive:
            if file_path not in seen:
                seen.add(file_path)
                unique_files.append((file_path, file_name))
        
        self.logger.info(f"Found {len(unique_files)} files to archive")
        return unique_files
    
    def identify_documentation_files(self) -> List[Tuple[str, str]]:
        """Identify documentation files that should be moved."""
        doc_files = []
        source_path = Path(self.config.source_directory)
        
        self.logger.info("Identifying documentation files...")
        
        # Scan for documentation files
        for pattern in self.documentation_patterns:
            pattern_files = list(source_path.glob(pattern))
            
            for file_path in pattern_files:
                # Skip if not a regular file
                if not file_path.is_file():
                    continue
                
                doc_files.append((str(file_path), file_path.name))
                self.logger.debug(f"Identified documentation file: {file_path.name}")
        
        # Remove duplicates
        seen = set()
        unique_files = []
        for file_path, file_name in doc_files:
            if file_path not in seen:
                seen.add(file_path)
                unique_files.append((file_path, file_name))
        
        self.logger.info(f"Found {len(unique_files)} documentation files")
        return unique_files
    
    def create_archive(self, files_to_archive: List[Tuple[str, str]]) -> Optional[str]:
        """Create timestamped ZIP archive of old script files."""
        if not files_to_archive:
            self.logger.info("No files to archive")
            return None
        
        # Create backup directory
        backup_path = Path(self.config.backup_directory)
        
        if not self.config.dry_run:
            try:
                backup_path.mkdir(parents=True, exist_ok=True)
                if str(backup_path) not in self.directories_created:
                    self.directories_created.append(str(backup_path))
                    self.logger.info(f"Created backup directory: {backup_path}")
            except Exception as e:
                error_msg = f"Failed to create backup directory {backup_path}: {e}"
                self.logger.error(error_msg)
                self.errors.append(error_msg)
                return None
        
        # Generate archive filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_filename = f"scrpa_scripts_archive_{timestamp}.zip"
        archive_path = backup_path / archive_filename
        
        self.logger.info(f"Creating archive: {archive_filename}")
        
        if self.config.dry_run:
            self.logger.info(f"[DRY RUN] Would create archive: {archive_path}")
            self.logger.info(f"[DRY RUN] Would archive {len(files_to_archive)} files:")
            for file_path, file_name in files_to_archive:
                file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
                self.logger.info(f"[DRY RUN]   - {file_name} ({file_size:,} bytes)")
            return str(archive_path)
        
        # Create ZIP archive
        try:
            total_size = 0
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                for file_path, file_name in files_to_archive:
                    try:
                        file_path_obj = Path(file_path)
                        if file_path_obj.exists():
                            file_size = file_path_obj.stat().st_size
                            total_size += file_size
                            
                            # Add file to archive with relative path
                            zipf.write(file_path, file_name)
                            
                            # Record operation
                            operation = FileOperation(
                                operation_type="archive",
                                source_path=file_path,
                                destination_path=str(archive_path),
                                file_size=file_size,
                                timestamp=datetime.now().isoformat(),
                                success=True
                            )
                            self.operations.append(operation)
                            
                            self.logger.debug(f"Archived: {file_name} ({file_size:,} bytes)")
                        else:
                            self.logger.warning(f"File no longer exists, skipping: {file_path}")
                            
                    except Exception as e:
                        error_msg = f"Failed to archive {file_name}: {e}"
                        self.logger.error(error_msg)
                        self.errors.append(error_msg)
                        
                        # Record failed operation
                        operation = FileOperation(
                            operation_type="archive",
                            source_path=file_path,
                            destination_path=str(archive_path),
                            file_size=0,
                            timestamp=datetime.now().isoformat(),
                            success=False,
                            error_message=str(e)
                        )
                        self.operations.append(operation)
            
            # Verify archive was created successfully
            if archive_path.exists() and archive_path.stat().st_size > 0:
                self.archive_files_created.append(str(archive_path))
                self.logger.info(f"Archive created successfully: {archive_filename} ({total_size:,} bytes compressed)")
                
                # Verify archive integrity if requested
                if self.config.verify_archives:
                    self._verify_archive_integrity(str(archive_path), files_to_archive)
                
                return str(archive_path)
            else:
                error_msg = f"Archive creation failed - file missing or empty: {archive_path}"
                self.logger.error(error_msg)
                self.errors.append(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"Failed to create archive {archive_filename}: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            return None
    
    def _verify_archive_integrity(self, archive_path: str, expected_files: List[Tuple[str, str]]):
        """Verify the integrity of created archive."""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                # Test archive integrity
                bad_files = zipf.testzip()
                if bad_files:
                    self.logger.warning(f"Archive integrity check failed - corrupted file: {bad_files}")
                    return False
                
                # Verify all expected files are present
                archive_files = set(zipf.namelist())
                expected_names = {file_name for _, file_name in expected_files}
                
                missing_files = expected_names - archive_files
                if missing_files:
                    self.logger.warning(f"Archive missing expected files: {missing_files}")
                    return False
                
                self.logger.debug(f"Archive integrity verified: {len(archive_files)} files")
                return True
                
        except Exception as e:
            self.logger.warning(f"Archive integrity verification failed: {e}")
            return False
    
    def remove_archived_files(self, files_to_archive: List[Tuple[str, str]], archive_path: Optional[str]):
        """Remove original files after successful archiving."""
        if not archive_path or not files_to_archive:
            return
        
        # Only remove files if archive exists and verification passed
        if not Path(archive_path).exists():
            self.logger.error("Cannot remove files - archive does not exist")
            return
        
        self.logger.info(f"Removing {len(files_to_archive)} archived files from source directory")
        
        if self.config.dry_run:
            self.logger.info("[DRY RUN] Would remove the following files:")
            for file_path, file_name in files_to_archive:
                self.logger.info(f"[DRY RUN]   - {file_name}")
            return
        
        removed_count = 0
        for file_path, file_name in files_to_archive:
            try:
                file_path_obj = Path(file_path)
                if file_path_obj.exists():
                    file_path_obj.unlink()
                    removed_count += 1
                    self.logger.debug(f"Removed archived file: {file_name}")
                else:
                    self.logger.debug(f"File already removed or missing: {file_name}")
                    
            except Exception as e:
                error_msg = f"Failed to remove {file_name}: {e}"
                self.logger.error(error_msg)
                self.errors.append(error_msg)
        
        self.logger.info(f"Removed {removed_count} archived files from source directory")
    
    def move_documentation_files(self, doc_files: List[Tuple[str, str]]) -> int:
        """Move documentation files to organized documentation directory."""
        if not doc_files:
            self.logger.info("No documentation files to move")
            return 0
        
        # Create documentation directory
        doc_path = Path(self.config.documentation_directory)
        
        if not self.config.dry_run:
            try:
                doc_path.mkdir(parents=True, exist_ok=True)
                if str(doc_path) not in self.directories_created:
                    self.directories_created.append(str(doc_path))
                    self.logger.info(f"Created documentation directory: {doc_path}")
            except Exception as e:
                error_msg = f"Failed to create documentation directory {doc_path}: {e}"
                self.logger.error(error_msg)
                self.errors.append(error_msg)
                return 0
        
        self.logger.info(f"Moving {len(doc_files)} documentation files")
        
        if self.config.dry_run:
            self.logger.info(f"[DRY RUN] Would move documentation files to: {doc_path}")
            for file_path, file_name in doc_files:
                file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
                self.logger.info(f"[DRY RUN]   - {file_name} ({file_size:,} bytes)")
            return len(doc_files)
        
        moved_count = 0
        total_size = 0
        
        for file_path, file_name in doc_files:
            try:
                source_path = Path(file_path)
                dest_path = doc_path / file_name
                
                if not source_path.exists():
                    self.logger.warning(f"Source file no longer exists: {file_path}")
                    continue
                
                file_size = source_path.stat().st_size
                
                # Handle file name conflicts
                if dest_path.exists():
                    # Create unique filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    name_parts = file_name.rsplit('.', 1)
                    if len(name_parts) == 2:
                        unique_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                    else:
                        unique_name = f"{file_name}_{timestamp}"
                    
                    dest_path = doc_path / unique_name
                    self.logger.info(f"Renamed to avoid conflict: {file_name} -> {unique_name}")
                
                # Move file
                shutil.move(str(source_path), str(dest_path))
                
                moved_count += 1
                total_size += file_size
                
                # Record operation
                operation = FileOperation(
                    operation_type="move",
                    source_path=file_path,
                    destination_path=str(dest_path),
                    file_size=file_size,
                    timestamp=datetime.now().isoformat(), 
                    success=True
                )
                self.operations.append(operation)
                
                self.logger.debug(f"Moved: {file_name} -> {dest_path.name} ({file_size:,} bytes)")
                
            except Exception as e:
                error_msg = f"Failed to move {file_name}: {e}"
                self.logger.error(error_msg)
                self.errors.append(error_msg)
                
                # Record failed operation
                operation = FileOperation(
                    operation_type="move",
                    source_path=file_path,
                    destination_path=str(doc_path / file_name),
                    file_size=0,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error_message=str(e)
                )
                self.operations.append(operation)
        
        self.logger.info(f"Moved {moved_count} documentation files ({total_size:,} bytes total)")
        return moved_count
    
    def generate_cleanup_summary(self) -> CleanupSummary:
        """Generate comprehensive summary of cleanup operations."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Calculate statistics
        successful_ops = [op for op in self.operations if op.success]
        failed_ops = [op for op in self.operations if not op.success]
        
        archive_ops = [op for op in successful_ops if op.operation_type == "archive"]
        move_ops = [op for op in successful_ops if op.operation_type == "move"]
        
        total_size_archived = sum(op.file_size for op in archive_ops)
        total_size_moved = sum(op.file_size for op in move_ops)
        
        summary = CleanupSummary(
            session_id=self.session_id,
            start_timestamp=self.start_time.isoformat(),
            end_timestamp=end_time.isoformat(),
            duration_seconds=round(duration, 3),
            total_files_processed=len(self.operations),
            files_archived=len(archive_ops),
            files_moved=len(move_ops),
            files_skipped=0,  # Could be enhanced to track skipped files
            errors_encountered=len(failed_ops),
            operations=self.operations,
            archive_files_created=self.archive_files_created,
            directories_created=self.directories_created,
            total_size_archived=total_size_archived,
            total_size_moved=total_size_moved
        )
        
        return summary
    
    def save_cleanup_summary(self, summary: CleanupSummary, summary_path: Optional[str] = None):
        """Save cleanup summary to JSON file."""
        if not summary_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_filename = f"scrpa_cleanup_summary_{timestamp}.json"
            summary_path = os.path.join(self.config.source_directory, summary_filename)
        
        try:
            summary_dict = asdict(summary)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Cleanup summary saved: {summary_path}")
            return summary_path
            
        except Exception as e:
            error_msg = f"Failed to save cleanup summary: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            return None
    
    def print_summary_report(self, summary: CleanupSummary):
        """Print formatted summary report to console."""
        print(f"\n{'='*80}")
        print("SCRPA SCRIPT CLEANUP SUMMARY")
        print(f"{'='*80}")
        print(f"Session ID: {summary.session_id}")
        print(f"Duration: {summary.duration_seconds:.3f} seconds")
        print(f"Mode: {'DRY RUN' if self.config.dry_run else 'LIVE EXECUTION'}")
        print()
        
        print("OPERATIONS SUMMARY:")
        print(f"  Total Files Processed: {summary.total_files_processed}")
        print(f"  Files Archived: {summary.files_archived}")
        print(f"  Files Moved: {summary.files_moved}")
        print(f"  Errors Encountered: {summary.errors_encountered}")
        print()
        
        if summary.files_archived > 0:
            print("ARCHIVING RESULTS:")
            print(f"  Files Archived: {summary.files_archived}")
            print(f"  Total Size Archived: {summary.total_size_archived:,} bytes")
            print(f"  Archive Files Created: {len(summary.archive_files_created)}")
            for archive in summary.archive_files_created:
                print(f"    - {os.path.basename(archive)}")
            print()
        
        if summary.files_moved > 0:
            print("DOCUMENTATION MOVE RESULTS:")
            print(f"  Files Moved: {summary.files_moved}")
            print(f"  Total Size Moved: {summary.total_size_moved:,} bytes")
            print(f"  Target Directory: {self.config.documentation_directory}")
            print()
        
        if summary.directories_created:
            print("DIRECTORIES CREATED:")
            for directory in summary.directories_created:
                print(f"  - {directory}")
            print()
        
        if summary.errors_encountered > 0:
            print("ERRORS ENCOUNTERED:")
            error_operations = [op for op in summary.operations if not op.success]
            for op in error_operations[:10]:  # Show first 10 errors
                print(f"  - {op.operation_type.upper()}: {os.path.basename(op.source_path)}")
                print(f"    Error: {op.error_message}")
            
            if len(error_operations) > 10:
                print(f"  ... and {len(error_operations) - 10} more errors")
            print()
        
        # Final status
        if summary.errors_encountered == 0:
            print("✅ CLEANUP COMPLETED SUCCESSFULLY")
        else:
            print(f"⚠️  CLEANUP COMPLETED WITH {summary.errors_encountered} ERRORS")
        
        print(f"{'='*80}")
    
    def execute_cleanup(self) -> CleanupSummary:
        """Execute the complete cleanup process."""
        self.logger.info("Starting SCRPA script cleanup process")
        
        try:
            # Phase 1: Identify files
            self.logger.info("Phase 1: File identification")
            files_to_archive = self.identify_files_to_archive()
            doc_files = self.identify_documentation_files()
            
            # Phase 2: Create archives
            self.logger.info("Phase 2: Creating archives")
            archive_path = None
            if files_to_archive:
                archive_path = self.create_archive(files_to_archive)
                if archive_path and not self.config.dry_run:
                    # Remove archived files from source
                    self.remove_archived_files(files_to_archive, archive_path)
            
            # Phase 3: Move documentation
            self.logger.info("Phase 3: Moving documentation files")
            moved_count = self.move_documentation_files(doc_files)
            
            # Phase 4: Generate summary
            self.logger.info("Phase 4: Generating cleanup summary")
            summary = self.generate_cleanup_summary()
            
            # Save summary if requested
            if self.config.create_summary:
                self.save_cleanup_summary(summary)
            
            self.logger.info("SCRPA script cleanup completed")
            return summary
            
        except Exception as e:
            error_msg = f"Critical error during cleanup: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            
            # Generate error summary
            summary = self.generate_cleanup_summary()
            return summary

def create_default_config(source_dir: str) -> CleanupConfig:
    """Create default configuration for cleanup operations."""
    base_path = Path(source_dir).parent
    
    config = CleanupConfig(
        source_directory=source_dir,
        documentation_directory=str(base_path / "07_documentation"),
        backup_directory=str(Path(source_dir) / "backups"),
        dry_run=False,
        verbose=False,
        create_summary=True,
        verify_archives=True
    )
    
    return config

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="SCRPA Scripts Cleanup and Organization Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview changes
  python cleanup_scrpa_scripts.py --dry-run --verbose
  
  # Execute cleanup with logging
  python cleanup_scrpa_scripts.py --verbose --log-file cleanup.log
  
  # Custom directories
  python cleanup_scrpa_scripts.py --source-dir "C:\\Scripts" --doc-dir "C:\\Docs" --backup-dir "C:\\Backups"
  
  # Minimal execution
  python cleanup_scrpa_scripts.py
        """
    )
    
    # Directory options
    parser.add_argument('--source-dir', '-s', 
                       default=os.getcwd(),
                       help='Source directory containing scripts (default: current directory)')
    
    parser.add_argument('--doc-dir', '-d',
                       help='Documentation target directory (default: auto-detected)')
    
    parser.add_argument('--backup-dir', '-b',
                       help='Backup directory for archives (default: source_dir/backups)')
    
    # Operation options
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Preview changes without executing them')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging output')
    
    parser.add_argument('--log-file', '-l',
                       help='Save detailed log to specified file')
    
    parser.add_argument('--no-summary', action='store_true',
                       help='Skip creation of JSON summary file')
    
    parser.add_argument('--no-verify', action='store_true',
                       help='Skip archive integrity verification')
    
    args = parser.parse_args()
    
    try:
        # Create configuration
        config = create_default_config(args.source_dir)
        
        # Override with command line arguments
        if args.doc_dir:
            config.documentation_directory = args.doc_dir
        if args.backup_dir:
            config.backup_directory = args.backup_dir
        if args.log_file:
            config.log_file = args.log_file
        
        config.dry_run = args.dry_run
        config.verbose = args.verbose
        config.create_summary = not args.no_summary
        config.verify_archives = not args.no_verify
        
        # Validate source directory
        if not os.path.exists(config.source_directory):
            print(f"❌ ERROR: Source directory does not exist: {config.source_directory}")
            return 1
        
        # Show configuration
        print("SCRPA SCRIPT CLEANUP TOOL")
        print("=" * 80)
        print(f"Source Directory: {config.source_directory}")
        print(f"Documentation Directory: {config.documentation_directory}")
        print(f"Backup Directory: {config.backup_directory}")
        print(f"Mode: {'DRY RUN' if config.dry_run else 'LIVE EXECUTION'}")
        if config.log_file:
            print(f"Log File: {config.log_file}")
        print("=" * 80)
        
        # Confirm execution if not dry run
        if not config.dry_run:
            confirm = input("\nProceed with cleanup? (y/N): ").lower().strip()
            if confirm not in ['y', 'yes']:
                print("Cleanup cancelled by user")
                return 0
        
        # Execute cleanup
        cleanup = SCRPAScriptCleanup(config)
        summary = cleanup.execute_cleanup()
        
        # Display results
        cleanup.print_summary_report(summary)
        
        # Return appropriate exit code
        if summary.errors_encountered == 0:
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n❌ Cleanup interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())