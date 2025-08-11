#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_crime_scripts_paths.py

Comprehensive Crime Reporting Scripts Path Update Tool

This script scans Python crime reporting scripts in 01_scripts/ and scripts/ directories
for outdated path references (specifically "C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects")
and replaces them with appropriate new paths for data, output, and project directories.

Features:
- Comprehensive scanning of crime reporting Python scripts (scrpa_*.py, map_export.py, chart_export.py)
- Smart path mapping to new OneDrive structure
- Multiple replacement strategies (data paths, output paths, project paths)
- Dry-run mode for safe preview of operations
- Automatic backup creation before modifications
- Detailed logging and error handling
- Context-aware replacements based on usage patterns
- Validation of path updates
- Comprehensive reporting and summary

Usage:
    # Dry run to preview changes
    python update_crime_scripts_paths.py --dry-run --verbose
    
    # Execute updates with backups
    python update_crime_scripts_paths.py --create-backups --verbose
    
    # Custom data directory
    python update_crime_scripts_paths.py --cad-data-path "C:\\Custom\\CAD\\Path" --verbose
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
class CrimeScriptConfig:
    """Configuration for crime script path update operations."""
    root_directory: str
    cad_data_path: str
    output_base_path: str
    projects_path: str
    backup_directory: str = "crime_scripts_backups"
    log_file: Optional[str] = None
    dry_run: bool = False
    verbose: bool = False
    create_backups: bool = True
    validate_updates: bool = True
    create_summary_report: bool = True

@dataclass
class PathReplacement:
    """Represents a path replacement operation in crime scripts."""
    original_path: str
    new_path: str
    replacement_type: str  # 'data', 'output', 'projects', 'aprx'
    context_line: str
    line_number: int
    variable_name: str
    success: bool = False
    error_message: str = ""

@dataclass
class CrimeScriptUpdate:
    """Represents updates to a single crime script file."""
    file_path: str
    relative_path: str
    script_type: str  # 'scrpa_system', 'map_export', 'chart_export', 'statistical', 'coordinate_fix'
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
class CrimeUpdateSummary:
    """Summary of all crime script updates."""
    session_id: str
    start_timestamp: str
    end_timestamp: str
    duration_seconds: float
    total_files_scanned: int
    files_needing_updates: int
    files_successfully_updated: int
    files_failed: int
    total_path_replacements: int
    backups_created: int
    script_updates: List[CrimeScriptUpdate]
    errors: List[str]
    warnings: List[str]

class CrimeScriptPathUpdater:
    """Comprehensive crime script path update system."""
    
    def __init__(self, config: CrimeScriptConfig):
        self.config = config
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self.start_time = datetime.now()
        
        # Tracking
        self.script_updates: List[CrimeScriptUpdate] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Setup logging
        self._setup_logging()
        
        # Define script patterns to scan
        self.crime_script_patterns = [
            'scrpa_*.py',
            'map_export*.py', 
            'chart_export*.py',
            'coordinate_fix*.py',
            'incident_table*.py',
            '*_crime_*.py',
            '*statistical*.py'
        ]
        
        # Path patterns to find and replace
        self.old_path_patterns = {
            'laptop_projects': [
                r'C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects',
                r'C:/Users/carucci_r/SCRPA_LAPTOP/projects',
                r'"C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects"',
                r'"C:/Users/carucci_r/SCRPA_LAPTOP/projects"',
                r"r'C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects'",
                r'r"C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects"'
            ],
            'laptop_data': [
                r'C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects\\data',
                r'C:/Users/carucci_r/SCRPA_LAPTOP/projects/data',
                r'"C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects\\data"',
                r'"C:/Users/carucci_r/SCRPA_LAPTOP/projects/data"'
            ],
            'laptop_output': [
                r'C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects\\output',
                r'C:/Users/carucci_r/SCRPA_LAPTOP/projects/output',
                r'"C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects\\output"',
                r'"C:/Users/carucci_r/SCRPA_LAPTOP/projects/output"'
            ],
            'laptop_aprx': [
                r'C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects\\7_Day_Templet_SCRPA_Time\.aprx',
                r'C:/Users/carucci_r/SCRPA_LAPTOP/projects/7_Day_Templet_SCRPA_Time.aprx',
                r'"C:\\Users\\carucci_r\\SCRPA_LAPTOP\\projects\\7_Day_Templet_SCRPA_Time\.aprx"',
                r'"C:/Users/carucci_r/SCRPA_LAPTOP/projects/7_Day_Templet_SCRPA_Time.aprx"'
            ]
        }
        
        # New path mappings
        self.new_path_mappings = {
            'data': self.config.cad_data_path,
            'output': self.config.output_base_path,
            'projects': self.config.projects_path,
            'aprx': os.path.join(self.config.projects_path, '7_Day_Templet_SCRPA_Time', '7_Day_Templet_SCRPA_Time.aprx')
        }
    
    def _setup_logging(self):
        """Setup comprehensive logging system."""
        log_level = logging.DEBUG if self.config.verbose else logging.INFO
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [CRIME_UPDATER:%(funcName)s:%(lineno)d] - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Setup logger
        self.logger = logging.getLogger('CrimeScriptUpdater')
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
        self.logger.info(f"Crime Script Path Update started - Session: {self.session_id} - Mode: {mode}")
    
    def scan_crime_scripts(self) -> List[str]:
        """Scan for crime reporting Python scripts in target directories."""
        root_path = Path(self.config.root_directory)
        crime_scripts = []
        
        # Directories to scan
        scan_directories = [
            root_path / "01_scripts",
            root_path / "scripts"
        ]
        
        self.logger.info("Scanning for crime reporting Python scripts")
        
        for scan_dir in scan_directories:
            if not scan_dir.exists():
                self.logger.warning(f"Directory not found: {scan_dir}")
                continue
                
            self.logger.info(f"Scanning directory: {scan_dir}")
            
            try:
                # Find scripts matching our patterns
                for pattern in self.crime_script_patterns:
                    script_files = list(scan_dir.glob(pattern))
                    
                    for script_file in script_files:
                        if script_file.is_file() and script_file.suffix == '.py':
                            crime_scripts.append(str(script_file))
                            self.logger.debug(f"Found crime script: {script_file.relative_to(root_path)}")
                
            except Exception as e:
                error_msg = f"Error scanning directory {scan_dir}: {e}"
                self.logger.error(error_msg)
                self.errors.append(error_msg)
        
        # Remove duplicates
        crime_scripts = list(set(crime_scripts))
        
        self.logger.info(f"Found {len(crime_scripts)} crime reporting scripts")
        return crime_scripts
    
    def classify_script_type(self, file_path: str) -> str:
        """Classify the type of crime script based on filename."""
        filename = Path(file_path).name.lower()
        
        if 'scrpa_' in filename and ('system' in filename or 'production' in filename or 'final' in filename):
            return 'scrpa_system'
        elif 'map_export' in filename:
            return 'map_export'
        elif 'chart_export' in filename:
            return 'chart_export'
        elif 'statistical' in filename:
            return 'statistical'
        elif 'coordinate_fix' in filename:
            return 'coordinate_fix'
        elif 'incident_table' in filename:
            return 'incident_table'
        else:
            return 'other_crime'
    
    def analyze_crime_script(self, file_path: str) -> List[PathReplacement]:
        """Analyze a crime script for path references that need updating."""
        replacements = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Check each pattern category
                for category, patterns in self.old_path_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Determine replacement type and new path
                            replacement_type, new_path, var_name = self._determine_crime_replacement(line, pattern, category)
                            
                            replacement = PathReplacement(
                                original_path=pattern,
                                new_path=new_path,
                                replacement_type=replacement_type,
                                context_line=line.strip(),
                                line_number=line_num,
                                variable_name=var_name
                            )
                            replacements.append(replacement)
                            
                            self.logger.debug(f"Found path replacement needed in {Path(file_path).name}:{line_num}")
        
        except Exception as e:
            error_msg = f"Error analyzing {file_path}: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
        
        return replacements
    
    def _determine_crime_replacement(self, line: str, pattern: str, category: str) -> Tuple[str, str, str]:
        """Determine the appropriate replacement for a crime script path."""
        line_lower = line.lower()
        
        # Extract variable name if possible
        var_match = re.search(r'(\w+)\s*=', line)
        var_name = var_match.group(1) if var_match else "unknown"
        
        # Determine replacement based on category and context
        if category == 'laptop_data' or 'data' in line_lower or 'csv' in line_lower:
            replacement_type = 'data'
            new_path = self.new_path_mappings['data']
        elif category == 'laptop_output' or 'output' in line_lower:
            replacement_type = 'output'
            new_path = self.new_path_mappings['output']
        elif category == 'laptop_aprx' or '.aprx' in line_lower:
            replacement_type = 'aprx'
            new_path = self.new_path_mappings['aprx']
        else:
            replacement_type = 'projects'
            new_path = self.new_path_mappings['projects']
        
        # Preserve quote style and r-string prefix
        if pattern.startswith('r"') or pattern.startswith("r'"):
            if pattern.startswith('r"'):
                new_path = f'r"{new_path}"'
            else:
                new_path = f"r'{new_path}'"
        elif pattern.startswith('"'):
            new_path = f'"{new_path}"'
        elif pattern.startswith("'"):
            new_path = f"'{new_path}'"
        
        return replacement_type, new_path, var_name
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """Create backup of crime script before modification."""
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
    
    def update_crime_script(self, file_path: str, replacements: List[PathReplacement]) -> CrimeScriptUpdate:
        """Update a single crime script with path replacements."""
        file_path_obj = Path(file_path)
        root_path = Path(self.config.root_directory)
        
        # Create script update record
        script_update = CrimeScriptUpdate(
            file_path=file_path,
            relative_path=str(file_path_obj.relative_to(root_path)),
            script_type=self.classify_script_type(file_path),
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
            self.logger.info(f"Updating crime script: {script_update.relative_path} ({script_update.script_type})")
            
            # Create backup
            backup_path = self.create_backup(file_path)
            if backup_path:
                script_update.backup_created = True
                script_update.backup_path = backup_path
            
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
                        script_update.successful_replacements += 1
                        self.logger.debug(f"Replaced {replacement.replacement_type} path: {replacement.variable_name}")
                    else:
                        replacement.error_message = "Pattern not found for replacement"
                        script_update.failed_replacements += 1
                        
                except Exception as e:
                    replacement.success = False
                    replacement.error_message = str(e)
                    script_update.failed_replacements += 1
                    self.logger.error(f"Failed to replace {replacement.original_path}: {e}")
            
            # Write updated content
            if content != original_content:
                if not self.config.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Validate if requested
                    if self.config.validate_updates:
                        self._validate_crime_script_update(file_path, script_update)
                    
                    self.logger.info(f"Updated {script_update.successful_replacements} paths in {script_update.relative_path}")
                else:
                    self.logger.info(f"[DRY RUN] Would update {script_update.successful_replacements} paths in {script_update.relative_path}")
                
                script_update.success = True
            else:
                self.logger.info(f"No changes needed for {script_update.relative_path}")
                script_update.success = True
                
        except Exception as e:
            script_update.success = False
            script_update.error_message = str(e)
            error_msg = f"Failed to update {script_update.relative_path}: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
        
        return script_update
    
    def _validate_crime_script_update(self, file_path: str, script_update: CrimeScriptUpdate):
        """Validate that crime script updates were applied correctly."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check that old paths are no longer present
            for category, patterns in self.old_path_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        warning_msg = f"Old path pattern still found in {script_update.relative_path}: {pattern}"
                        self.logger.warning(warning_msg)
                        self.warnings.append(warning_msg)
            
            self.logger.debug(f"Validation completed for {script_update.relative_path}")
            
        except Exception as e:
            self.logger.warning(f"Validation failed for {file_path}: {e}")
    
    def execute_updates(self) -> CrimeUpdateSummary:
        """Execute the complete crime script update process."""
        self.logger.info("Starting crime script path update process")
        
        try:
            # Phase 1: Scan for crime scripts
            self.logger.info("Phase 1: Scanning for crime reporting scripts")
            crime_scripts = self.scan_crime_scripts()
            
            if not crime_scripts:
                self.logger.warning("No crime scripts found to process")
            
            # Phase 2: Analyze and update scripts
            self.logger.info("Phase 2: Analyzing and updating scripts")
            
            files_needing_updates = 0
            files_successfully_updated = 0
            files_failed = 0
            total_replacements = 0
            backups_created = 0
            
            for script_path in crime_scripts:
                # Analyze script for needed replacements
                replacements = self.analyze_crime_script(script_path)
                
                if replacements:
                    files_needing_updates += 1
                    
                    # Update the script
                    script_update = self.update_crime_script(script_path, replacements)
                    self.script_updates.append(script_update)
                    
                    # Update counters
                    total_replacements += script_update.successful_replacements
                    
                    if script_update.backup_created:
                        backups_created += 1
                    
                    if script_update.success:
                        files_successfully_updated += 1
                    else:
                        files_failed += 1
            
            # Phase 3: Generate summary
            self.logger.info("Phase 3: Generating update summary")
            
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            
            summary = CrimeUpdateSummary(
                session_id=self.session_id,
                start_timestamp=self.start_time.isoformat(),
                end_timestamp=end_time.isoformat(),
                duration_seconds=round(duration, 3),
                total_files_scanned=len(crime_scripts),
                files_needing_updates=files_needing_updates,
                files_successfully_updated=files_successfully_updated,
                files_failed=files_failed,
                total_path_replacements=total_replacements,
                backups_created=backups_created,
                script_updates=self.script_updates,
                errors=self.errors,
                warnings=self.warnings
            )
            
            # Save summary report if requested
            if self.config.create_summary_report:
                self.save_summary_report(summary)
            
            self.logger.info("Crime script path update process completed")
            return summary
            
        except Exception as e:
            error_msg = f"Critical error during crime script update: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            
            # Generate error summary
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            
            summary = CrimeUpdateSummary(
                session_id=self.session_id,
                start_timestamp=self.start_time.isoformat(),
                end_timestamp=end_time.isoformat(),
                duration_seconds=round(duration, 3),
                total_files_scanned=0,
                files_needing_updates=0,
                files_successfully_updated=0,
                files_failed=0,
                total_path_replacements=0,
                backups_created=0,
                script_updates=self.script_updates,
                errors=self.errors,
                warnings=self.warnings
            )
            
            return summary
    
    def save_summary_report(self, summary: CrimeUpdateSummary) -> Optional[str]:
        """Save detailed summary report to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"crime_scripts_update_summary_{timestamp}.json"
            report_path = Path(self.config.root_directory) / report_filename
            
            # Convert to serializable format
            summary_dict = asdict(summary)
            
            # Add configuration metadata
            summary_dict['update_config'] = {
                'root_directory': self.config.root_directory,
                'cad_data_path': self.config.cad_data_path,
                'output_base_path': self.config.output_base_path,
                'projects_path': self.config.projects_path,
                'dry_run': self.config.dry_run,
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
    
    def print_update_summary(self, summary: CrimeUpdateSummary):
        """Print comprehensive update summary to console."""
        print(f"\n{'='*80}")
        print("CRIME SCRIPTS PATH UPDATE SUMMARY")
        print(f"{'='*80}")
        print(f"Session ID: {summary.session_id}")
        print(f"Duration: {summary.duration_seconds:.3f} seconds")
        print(f"Mode: {'DRY RUN' if self.config.dry_run else 'LIVE UPDATE'}")
        print()
        
        print("UPDATE RESULTS:")
        print(f"  Total Scripts Scanned: {summary.total_files_scanned}")
        print(f"  Scripts Needing Updates: {summary.files_needing_updates}")
        print(f"  Scripts Successfully Updated: {summary.files_successfully_updated}")
        print(f"  Scripts Failed: {summary.files_failed}")
        print(f"  Total Path Replacements: {summary.total_path_replacements}")
        print(f"  Backups Created: {summary.backups_created}")
        print()
        
        # Show updated scripts by type
        if summary.script_updates:
            print("SCRIPTS UPDATED BY TYPE:")
            script_types = {}
            for script_update in summary.script_updates:
                script_type = script_update.script_type
                if script_type not in script_types:
                    script_types[script_type] = []
                script_types[script_type].append(script_update)
            
            for script_type, updates in script_types.items():
                print(f"  {script_type.upper()}:")
                for update in updates:
                    status = "✅" if update.success else "❌"
                    print(f"    {status} {update.relative_path}: {update.successful_replacements} paths updated")
                    
                    if self.config.verbose and update.replacements:
                        for replacement in update.replacements[:2]:  # Show first 2 replacements
                            if replacement.success:
                                print(f"      ✓ {replacement.replacement_type}: {replacement.variable_name}")
            print()
        
        # Show warnings
        if summary.warnings:
            print("WARNINGS:")
            for warning in summary.warnings[:3]:  # Show first 3 warnings
                print(f"  ⚠️  {warning}")
            if len(summary.warnings) > 3:
                print(f"  ... and {len(summary.warnings) - 3} more warnings")
            print()
        
        # Show errors
        if summary.errors:
            print("ERRORS:")
            for error in summary.errors[:3]:  # Show first 3 errors
                print(f"  ❌ {error}")
            if len(summary.errors) > 3:
                print(f"  ... and {len(summary.errors) - 3} more errors")
            print()
        
        # Final status
        if summary.files_failed == 0:
            print("✅ CRIME SCRIPTS PATH UPDATE COMPLETED SUCCESSFULLY")
        else:
            print(f"⚠️  CRIME SCRIPTS PATH UPDATE COMPLETED WITH {summary.files_failed} FAILURES")
        
        print(f"{'='*80}")

def create_default_config() -> CrimeScriptConfig:
    """Create default configuration for crime script path updates."""
    current_dir = os.getcwd()
    
    # Define new path structure based on OneDrive organization
    config = CrimeScriptConfig(
        root_directory=current_dir,
        cad_data_path=r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA",
        output_base_path=r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\Reports",
        projects_path=os.path.join(current_dir, "09_arcvive"),
        backup_directory="crime_scripts_backups",
        dry_run=False,
        verbose=False,
        create_backups=True,
        validate_updates=True,
        create_summary_report=True
    )
    
    return config

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Crime Scripts Path Update Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview changes
  python update_crime_scripts_paths.py --dry-run --verbose
  
  # Execute updates with backups and detailed logging
  python update_crime_scripts_paths.py --create-backups --verbose --log-file crime_update.log
  
  # Custom CAD data path
  python update_crime_scripts_paths.py --cad-data-path "C:\\Custom\\CAD\\Path" --verbose
  
  # Custom output directory
  python update_crime_scripts_paths.py --output-path "C:\\Custom\\Output" --verbose
        """
    )
    
    # Directory options
    parser.add_argument('--root-dir', '-r',
                       default=None,
                       help='Root directory to scan (default: current directory)')
    
    parser.add_argument('--cad-data-path', '-c',
                       default=None,
                       help='New CAD data directory path')
    
    parser.add_argument('--output-path', '-o',
                       default=None,
                       help='New output directory path')
    
    parser.add_argument('--projects-path', '-p',
                       default=None,
                       help='New projects directory path')
    
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
        if args.cad_data_path:
            config.cad_data_path = args.cad_data_path
        if args.output_path:
            config.output_base_path = args.output_path
        if args.projects_path:
            config.projects_path = args.projects_path
        if args.log_file:
            config.log_file = args.log_file
        
        config.dry_run = args.dry_run
        config.verbose = args.verbose
        config.create_backups = not args.no_backups and args.create_backups
        config.validate_updates = not args.no_validation
        config.create_summary_report = not args.no_summary
        
        # Validate directories
        if not os.path.exists(config.root_directory):
            print(f"❌ ERROR: Root directory does not exist: {config.root_directory}")
            return 1
        
        # Show configuration
        print("CRIME SCRIPTS PATH UPDATE TOOL")
        print("=" * 80)
        print(f"Root Directory: {config.root_directory}")
        print(f"CAD Data Path: {config.cad_data_path}")
        print(f"Output Path: {config.output_base_path}")
        print(f"Projects Path: {config.projects_path}")
        print(f"Mode: {'DRY RUN' if config.dry_run else 'LIVE UPDATE'}")
        print(f"Create Backups: {'Yes' if config.create_backups else 'No'}")
        print(f"Validate Updates: {'Yes' if config.validate_updates else 'No'}")
        if config.log_file:
            print(f"Log File: {config.log_file}")
        print("=" * 80)
        
        # Confirm execution if not dry run
        if not config.dry_run:
            confirm = input("\nProceed with crime script updates? (y/N): ").lower().strip()
            if confirm not in ['y', 'yes']:
                print("Crime script update cancelled by user")
                return 0
        
        # Execute updates
        updater = CrimeScriptPathUpdater(config)
        summary = updater.execute_updates()
        
        # Display results
        updater.print_update_summary(summary)
        
        # Return appropriate exit code
        if summary.files_failed == 0:
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n❌ Crime script update interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())