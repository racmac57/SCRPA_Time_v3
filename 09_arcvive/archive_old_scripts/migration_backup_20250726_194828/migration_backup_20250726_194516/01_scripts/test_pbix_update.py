#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_pbix_update.py

Comprehensive test script for PBIX parameter updates with full process validation,
step-by-step monitoring, and rollback capabilities.

Features:
- Full process testing (import → validate → update → verify)
- Step-by-step validation with detailed logging
- Automatic rollback on failures
- Backup management and restoration
- Transaction-like behavior for PBIX operations
- Comprehensive error reporting and recovery

Usage:
    python test_pbix_update.py --pbix "SCRPA_Time_v2.pbix" --test-all
    python test_pbix_update.py --pbix "report.pbix" --param "BasePath" --value "C:\\New\\Path"
    python test_pbix_update.py --rollback-test
"""

import os
import sys
import shutil
import json
import tempfile
import zipfile
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from contextlib import contextmanager

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from update_pbix_parameter_enhanced import PBIXParameterUpdater, PBIXValidationError
except ImportError:
    print("❌ ERROR: Could not import update_pbix_parameter_enhanced.py")
    print("   Make sure the enhanced PBIX updater script is in the same directory")
    sys.exit(1)

@dataclass
class TestStep:
    """Represents a single test step with validation."""
    name: str
    description: str
    status: str = "pending"  # pending, running, success, failed, skipped
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class BackupInfo:
    """Information about a backup file."""
    original_path: str
    backup_path: str
    timestamp: datetime
    file_size: int
    checksum: Optional[str] = None

class PBIXTestManager:
    """Comprehensive PBIX testing and rollback manager."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_steps: List[TestStep] = []
        self.backups: List[BackupInfo] = []
        self.temp_files: List[str] = []
        self.rollback_enabled = True
        self.test_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_dir = None
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize updater
        self.updater = PBIXParameterUpdater(verbose=verbose)
        
    def setup_logging(self):
        """Setup comprehensive logging."""
        log_filename = f"pbix_test_{self.test_session_id}.log"
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
        )
        
        # Setup file handler
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO if self.verbose else logging.WARNING)
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[file_handler, console_handler]
        )
        
        self.log_file = log_filename
        
    def add_test_step(self, name: str, description: str) -> TestStep:
        """Add a new test step."""
        step = TestStep(name=name, description=description)
        self.test_steps.append(step)
        return step
    
    @contextmanager
    def test_step_context(self, step: TestStep):
        """Context manager for executing a test step with timing and error handling."""
        step.status = "running"
        step.start_time = datetime.now()
        
        self.logger.info(f"🔧 Starting: {step.name}")
        if self.verbose:
            print(f"🔧 {step.name}: {step.description}")
        
        try:
            yield step
            step.status = "success"
            self.logger.info(f"✅ Completed: {step.name}")
            if self.verbose:
                print(f"   ✅ Success")
                
        except Exception as e:
            step.status = "failed"
            step.errors.append(str(e))
            self.logger.error(f"❌ Failed: {step.name} - {e}")
            if self.verbose:
                print(f"   ❌ Failed: {e}")
            raise
            
        finally:
            step.end_time = datetime.now()
            if step.start_time:
                step.duration = (step.end_time - step.start_time).total_seconds()
    
    def create_backup(self, file_path: str, backup_dir: Optional[str] = None) -> BackupInfo:
        """Create a backup of a file with detailed tracking."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")
        
        # Create backup directory if not specified
        if backup_dir is None:
            backup_dir = os.path.join(os.path.dirname(file_path), f"backups_{self.test_session_id}")
        
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename
        original_path = Path(file_path)
        timestamp = datetime.now()
        backup_filename = f"{original_path.stem}_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}{original_path.suffix}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy file
        shutil.copy2(file_path, backup_path)
        
        # Create backup info
        backup_info = BackupInfo(
            original_path=str(original_path.resolve()),
            backup_path=str(Path(backup_path).resolve()),
            timestamp=timestamp,
            file_size=os.path.getsize(backup_path)
        )
        
        self.backups.append(backup_info)
        self.logger.info(f"📦 Backup created: {backup_path}")
        
        return backup_info
    
    def rollback_from_backup(self, backup_info: BackupInfo) -> bool:
        """Restore a file from its backup."""
        try:
            if not os.path.exists(backup_info.backup_path):
                self.logger.error(f"Backup file not found: {backup_info.backup_path}")
                return False
            
            # Remove current file if it exists
            if os.path.exists(backup_info.original_path):
                os.remove(backup_info.original_path)
            
            # Restore from backup
            shutil.copy2(backup_info.backup_path, backup_info.original_path)
            
            self.logger.info(f"🔄 Restored from backup: {backup_info.original_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
            return False
    
    def rollback_all_backups(self) -> int:
        """Rollback all created backups."""
        success_count = 0
        
        self.logger.info(f"🔄 Starting rollback of {len(self.backups)} backups...")
        
        for backup_info in reversed(self.backups):  # Rollback in reverse order
            if self.rollback_from_backup(backup_info):
                success_count += 1
        
        self.logger.info(f"🔄 Rollback completed: {success_count}/{len(self.backups)} successful")
        return success_count
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during testing."""
        cleaned = 0
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    if os.path.isdir(temp_file):
                        shutil.rmtree(temp_file)
                    else:
                        os.remove(temp_file)
                    cleaned += 1
            except Exception as e:
                self.logger.warning(f"Could not clean up {temp_file}: {e}")
        
        if cleaned > 0:
            self.logger.info(f"🧹 Cleaned up {cleaned} temporary files")
    
    def validate_pbix_import(self, pbix_path: str) -> Dict[str, Any]:
        """Validate PBIX file can be imported and analyzed."""
        step = self.add_test_step("validate_import", f"Validate PBIX import: {os.path.basename(pbix_path)}")
        
        with self.test_step_context(step):
            # Basic file validation
            if not os.path.exists(pbix_path):
                raise FileNotFoundError(f"PBIX file not found: {pbix_path}")
            
            # Use enhanced updater validation
            validation_result = self.updater.validate_input_file(pbix_path)
            step.details['validation'] = validation_result
            
            # Check critical validations
            critical_checks = [
                ('file_exists', 'File exists'),
                ('is_pbix', 'Valid PBIX format'),
                ('is_valid_zip', 'Valid ZIP structure'),
                ('datamashup_found', 'DataMashup file found')
            ]
            
            for check_key, check_name in critical_checks:
                if not validation_result.get(check_key, False):
                    raise PBIXValidationError(f"Critical validation failed: {check_name}")
            
            # Log warnings for non-critical issues
            if validation_result['errors']:
                for error in validation_result['errors']:
                    step.warnings.append(error)
            
            step.details['file_size'] = validation_result['file_size']
            step.details['datamashup_location'] = validation_result['datamashup_location']
            step.details['parameters_found'] = len(validation_result['parameters_detected'])
            
            return validation_result
    
    def validate_parameter_exists(self, pbix_path: str, param_name: str) -> Dict[str, Any]:
        """Validate that a specific parameter exists in the PBIX."""
        step = self.add_test_step("validate_parameter", f"Validate parameter '{param_name}' exists")
        
        with self.test_step_context(step):
            param_validation = self.updater.validate_parameter_exists(pbix_path, param_name)
            step.details['parameter_validation'] = param_validation
            
            if not param_validation['parameter_found']:
                raise PBIXValidationError(f"Parameter '{param_name}' not found in PBIX file")
            
            step.details['current_value'] = param_validation['current_value']
            step.details['parameter_pattern'] = param_validation['parameter_pattern']
            
            return param_validation
    
    def perform_parameter_update(self, input_path: str, output_path: str, 
                                param_name: str, new_value: str) -> Dict[str, Any]:
        """Perform the actual parameter update with validation."""
        step = self.add_test_step("parameter_update", f"Update parameter '{param_name}' to '{new_value}'")
        
        with self.test_step_context(step):
            # Create backup before update
            backup_info = self.create_backup(input_path)
            step.details['backup_created'] = backup_info.backup_path
            
            # Perform update using enhanced updater
            update_result = self.updater.process_pbix_with_validation(
                input_pbix=input_path,
                output_pbix=output_path,
                param_name=param_name,
                new_value=new_value
            )
            
            step.details['update_result'] = update_result
            
            if not update_result['success']:
                # Update failed, prepare for rollback
                step.errors.extend(update_result['errors'])
                raise PBIXValidationError(f"Parameter update failed: {'; '.join(update_result['errors'])}")
            
            # Add output file to temp files for cleanup if needed
            self.temp_files.append(output_path)
            
            return update_result
    
    def validate_output_file(self, output_path: str, expected_param_value: str, param_name: str) -> Dict[str, Any]:
        """Validate the output file was created correctly."""
        step = self.add_test_step("validate_output", f"Validate output file: {os.path.basename(output_path)}")
        
        with self.test_step_context(step):
            # Check file exists
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"Output file was not created: {output_path}")
            
            # Validate output file structure
            output_validation = self.updater.validate_input_file(output_path)
            step.details['output_validation'] = output_validation
            
            if output_validation['errors']:
                step.warnings.extend(output_validation['errors'])
            
            # Validate parameter was updated correctly
            param_check = self.updater.validate_parameter_exists(output_path, param_name)
            step.details['parameter_check'] = param_check
            
            if not param_check['parameter_found']:
                raise PBIXValidationError(f"Parameter '{param_name}' not found in output file")
            
            if param_check['current_value'] != expected_param_value:
                raise PBIXValidationError(
                    f"Parameter value mismatch. Expected: '{expected_param_value}', "
                    f"Found: '{param_check['current_value']}'"
                )
            
            step.details['output_file_size'] = output_validation['file_size']
            step.details['verified_parameter_value'] = param_check['current_value']
            
            return output_validation
    
    def run_full_pbix_test(self, pbix_path: str, param_name: str, new_value: str, 
                          output_path: Optional[str] = None) -> Dict[str, Any]:
        """Run complete PBIX parameter update test with full validation."""
        
        self.logger.info(f"🚀 Starting full PBIX test session: {self.test_session_id}")
        print(f"🚀 FULL PBIX PARAMETER UPDATE TEST")
        print(f"📋 Session ID: {self.test_session_id}")
        print(f"📁 Input: {pbix_path}")
        print(f"🔧 Parameter: {param_name} = {new_value}")
        print("=" * 80)
        
        # Generate output path if not provided
        if output_path is None:
            input_path = Path(pbix_path)
            output_path = str(input_path.parent / f"{input_path.stem}_updated_{self.test_session_id}{input_path.suffix}")
        
        test_result = {
            'session_id': self.test_session_id,
            'success': False,
            'input_file': pbix_path,
            'output_file': output_path,
            'parameter_name': param_name,
            'parameter_value': new_value,
            'steps_completed': 0,
            'total_steps': 4,
            'rollback_performed': False,
            'backups_created': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Step 1: Validate PBIX Import
            import_validation = self.validate_pbix_import(pbix_path)
            test_result['steps_completed'] = 1
            
            # Step 2: Validate Parameter Exists
            param_validation = self.validate_parameter_exists(pbix_path, param_name)
            test_result['steps_completed'] = 2
            test_result['original_parameter_value'] = param_validation['current_value']
            
            # Step 3: Perform Parameter Update
            update_result = self.perform_parameter_update(pbix_path, output_path, param_name, new_value)
            test_result['steps_completed'] = 3
            test_result['backups_created'] = len(self.backups)
            
            # Step 4: Validate Output
            output_validation = self.validate_output_file(output_path, new_value, param_name)
            test_result['steps_completed'] = 4
            
            # All steps completed successfully
            test_result['success'] = True
            test_result['output_file_size'] = output_validation['file_size']
            
            self.logger.info("✅ Full PBIX test completed successfully!")
            print("\n✅ ALL TESTS PASSED!")
            
        except Exception as e:
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ PBIX test failed: {e}")
            print(f"\n❌ TEST FAILED: {e}")
            
            # Perform rollback if enabled
            if self.rollback_enabled and self.backups:
                try:
                    print("\n🔄 PERFORMING ROLLBACK...")
                    rollback_count = self.rollback_all_backups()
                    test_result['rollback_performed'] = True
                    test_result['rollback_success_count'] = rollback_count
                    
                    if rollback_count == len(self.backups):
                        print("✅ Rollback completed successfully")
                        self.logger.info("✅ Rollback completed successfully")
                    else:
                        print(f"⚠️  Partial rollback: {rollback_count}/{len(self.backups)} successful")
                        self.logger.warning(f"Partial rollback: {rollback_count}/{len(self.backups)} successful")
                        
                except Exception as rollback_error:
                    print(f"❌ Rollback failed: {rollback_error}")
                    self.logger.error(f"Rollback failed: {rollback_error}")
                    test_result['rollback_error'] = str(rollback_error)
        
        # Collect warnings from all steps
        for step in self.test_steps:
            test_result['warnings'].extend(step.warnings)
        
        return test_result
    
    def run_rollback_test(self, pbix_path: str) -> Dict[str, Any]:
        """Test rollback functionality specifically."""
        
        self.logger.info(f"🔄 Starting rollback test session: {self.test_session_id}")
        print(f"🔄 ROLLBACK FUNCTIONALITY TEST")
        print(f"📋 Session ID: {self.test_session_id}")
        print(f"📁 Test file: {pbix_path}")
        print("=" * 80)
        
        rollback_result = {
            'session_id': self.test_session_id,
            'success': False,
            'test_file': pbix_path,
            'backups_created': 0,
            'rollbacks_successful': 0,
            'steps': [],
            'errors': []
        }
        
        try:
            # Step 1: Create multiple backups
            step1 = self.add_test_step("create_backups", "Create test backups")
            with self.test_step_context(step1):
                if not os.path.exists(pbix_path):
                    raise FileNotFoundError(f"Test file not found: {pbix_path}")
                
                # Create multiple backups to test the system
                backup1 = self.create_backup(pbix_path)
                backup2 = self.create_backup(pbix_path)  # Second backup of same file
                
                rollback_result['backups_created'] = len(self.backups)
                step1.details['backups'] = [b.backup_path for b in self.backups]
            
            # Step 2: Modify original file (simulate failure scenario)
            step2 = self.add_test_step("simulate_failure", "Simulate file modification/corruption")
            with self.test_step_context(step2):
                # Create a temporary "corrupted" version
                temp_content = "This is corrupted content to test rollback"
                with open(pbix_path, 'w') as f:
                    f.write(temp_content)
                
                step2.details['modification'] = "File deliberately corrupted for rollback test"
            
            # Step 3: Test rollback functionality
            step3 = self.add_test_step("test_rollback", "Test rollback restoration")
            with self.test_step_context(step3):
                rollback_count = self.rollback_all_backups()
                rollback_result['rollbacks_successful'] = rollback_count
                
                # Verify file was restored
                if os.path.exists(pbix_path):
                    # Check if it's a valid PBIX again
                    validation = self.updater.validate_input_file(pbix_path)
                    if validation['is_valid_zip'] and validation['is_pbix']:
                        step3.details['restoration_verified'] = True
                    else:
                        raise Exception("File restored but not valid PBIX format")
                else:
                    raise Exception("File was not restored after rollback")
            
            rollback_result['success'] = True
            print("\n✅ ROLLBACK TEST PASSED!")
            self.logger.info("✅ Rollback test completed successfully!")
            
        except Exception as e:
            rollback_result['errors'].append(str(e))
            print(f"\n❌ ROLLBACK TEST FAILED: {e}")
            self.logger.error(f"❌ Rollback test failed: {e}")
        
        return rollback_result
    
    def generate_test_report(self, test_result: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Generate comprehensive test report."""
        
        report_lines = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Header
        report_lines.extend([
            "=" * 100,
            "PBIX PARAMETER UPDATE - COMPREHENSIVE TEST REPORT",
            "=" * 100,
            f"Timestamp: {timestamp}",
            f"Session ID: {test_result.get('session_id', 'Unknown')}",
            f"Test Result: {'✅ SUCCESS' if test_result.get('success', False) else '❌ FAILURE'}",
            ""
        ])
        
        # Test Summary
        report_lines.extend([
            "TEST SUMMARY:",
            "-" * 50,
            f"Input File: {test_result.get('input_file', 'N/A')}",
            f"Output File: {test_result.get('output_file', 'N/A')}",
            f"Parameter: {test_result.get('parameter_name', 'N/A')}",
            f"New Value: {test_result.get('parameter_value', 'N/A')}",
            f"Steps Completed: {test_result.get('steps_completed', 0)}/{test_result.get('total_steps', 0)}",
            f"Backups Created: {test_result.get('backups_created', 0)}",
            f"Rollback Performed: {'Yes' if test_result.get('rollback_performed', False) else 'No'}",
            ""
        ])
        
        # Step-by-step results
        report_lines.extend([
            "DETAILED STEP RESULTS:",
            "-" * 50
        ])
        
        for i, step in enumerate(self.test_steps, 1):
            status_icon = {
                'success': '✅',
                'failed': '❌', 
                'running': '🔄',
                'pending': '⏳',
                'skipped': '⏭️'
            }.get(step.status, '❓')
            
            report_lines.append(f"{i}. {step.name}: {status_icon} {step.status.upper()}")
            report_lines.append(f"   Description: {step.description}")
            
            if step.duration:
                report_lines.append(f"   Duration: {step.duration:.2f} seconds")
            
            if step.details:
                report_lines.append("   Details:")
                for key, value in step.details.items():
                    if isinstance(value, dict):
                        report_lines.append(f"     {key}: {json.dumps(value, indent=6)}")
                    else:
                        report_lines.append(f"     {key}: {value}")
            
            if step.errors:
                report_lines.append("   Errors:")
                for error in step.errors:
                    report_lines.append(f"     ❌ {error}")
            
            if step.warnings:
                report_lines.append("   Warnings:")
                for warning in step.warnings:
                    report_lines.append(f"     ⚠️  {warning}")
            
            report_lines.append("")
        
        # Backup information
        if self.backups:
            report_lines.extend([
                "BACKUP INFORMATION:",
                "-" * 50
            ])
            
            for i, backup in enumerate(self.backups, 1):
                report_lines.extend([
                    f"{i}. Backup created: {backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                    f"   Original: {backup.original_path}",
                    f"   Backup: {backup.backup_path}",
                    f"   Size: {backup.file_size:,} bytes",
                    ""
                ])
        
        # Error summary
        if test_result.get('errors'):
            report_lines.extend([
                "ERROR SUMMARY:",
                "-" * 50
            ])
            for error in test_result['errors']:
                report_lines.append(f"❌ {error}")
            report_lines.append("")
        
        # Warning summary
        if test_result.get('warnings'):
            report_lines.extend([
                "WARNING SUMMARY:",
                "-" * 50
            ])
            for warning in test_result['warnings']:
                report_lines.append(f"⚠️  {warning}")
            report_lines.append("")
        
        # Recommendations
        report_lines.extend([
            "RECOMMENDATIONS:",
            "-" * 50
        ])
        
        if test_result.get('success'):
            report_lines.extend([
                "✅ Test completed successfully",
                "✅ PBIX parameter update process is working correctly",
                "✅ Backup and rollback systems are functional"
            ])
        else:
            report_lines.extend([
                "❌ Test failed - review error details above",
                "🔧 Check PBIX file format and parameter existence",
                "🔧 Verify file permissions and disk space",
                "🔧 Test with a simpler PBIX file if issues persist"
            ])
        
        report_lines.extend([
            "",
            "=" * 100,
            f"End of Report - Generated: {timestamp}",
            "=" * 100
        ])
        
        report_content = "\n".join(report_lines)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"📋 Test report saved to: {output_file}")
        
        return report_content
    
    def cleanup(self):
        """Clean up test resources."""
        self.cleanup_temp_files()
        
        # Log final cleanup
        self.logger.info(f"🧹 Test session {self.test_session_id} cleanup completed")
        print(f"📋 Full test log available: {self.log_file}")

def main():
    """Main test execution function."""
    parser = argparse.ArgumentParser(description="Comprehensive PBIX Parameter Update Test Suite")
    
    parser.add_argument('--pbix', '-f', required=True, help="Path to PBIX file to test")
    parser.add_argument('--param', '-p', default="BasePath", help="Parameter name to test (default: BasePath)")
    parser.add_argument('--value', '-v', help="New parameter value (auto-generated if not provided)")
    parser.add_argument('--output', '-o', help="Output PBIX file path (auto-generated if not provided)")
    parser.add_argument('--test-all', action='store_true', help="Run all test scenarios")
    parser.add_argument('--rollback-test', action='store_true', help="Run rollback functionality test")
    parser.add_argument('--report', '-r', help="Save test report to file (auto-generated if not provided)")
    parser.add_argument('--no-rollback', action='store_true', help="Disable automatic rollback on failure")
    parser.add_argument('--verbose', '-v', action='store_true', help="Enable verbose output")
    parser.add_argument('--keep-temp', action='store_true', help="Keep temporary files for inspection")
    
    args = parser.parse_args()
    
    # Validate required file
    if not os.path.exists(args.pbix):
        print(f"❌ ERROR: PBIX file not found: {args.pbix}")
        return 1
    
    try:
        # Create test manager
        test_manager = PBIXTestManager(verbose=args.verbose)
        test_manager.rollback_enabled = not args.no_rollback
        
        # Generate default values if not provided
        if not args.value:
            args.value = f"C:\\Test\\Path\\{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if not args.report:
            args.report = f"pbix_test_report_{test_manager.test_session_id}.txt"
        
        # Determine which tests to run
        if args.rollback_test:
            # Run rollback-specific test
            test_result = test_manager.run_rollback_test(args.pbix)
        else:
            # Run full parameter update test
            test_result = test_manager.run_full_pbix_test(
                pbix_path=args.pbix,
                param_name=args.param,
                new_value=args.value,
                output_path=args.output
            )
        
        # Generate and save report
        report_content = test_manager.generate_test_report(test_result, args.report)
        
        # Print summary
        print("\n" + "=" * 80)
        print("FINAL TEST SUMMARY")
        print("=" * 80)
        print(f"Session ID: {test_result.get('session_id')}")
        print(f"Result: {'✅ SUCCESS' if test_result.get('success') else '❌ FAILURE'}")
        print(f"Steps: {test_result.get('steps_completed', 0)}/{test_result.get('total_steps', 0)}")
        print(f"Backups: {test_result.get('backups_created', 0)}")
        print(f"Rollback: {'Yes' if test_result.get('rollback_performed') else 'No'}")
        print(f"Report: {args.report}")
        
        # Cleanup unless keeping temp files
        if not args.keep_temp:
            test_manager.cleanup()
        else:
            print(f"🗂️  Temporary files preserved for inspection")
        
        return 0 if test_result.get('success') else 1
        
    except Exception as e:
        print(f"\n❌ CRITICAL TEST FAILURE: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())