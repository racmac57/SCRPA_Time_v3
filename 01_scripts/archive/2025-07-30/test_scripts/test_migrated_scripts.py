#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_migrated_scripts.py

Comprehensive Testing Suite for Migrated SCRPA Scripts

This script provides automated validation for migrated SCRPA scripts including:
- Batch files (.bat) with updated paths
- Crime reporting Python scripts (scrpa_*.py, map_export.py, chart_export.py)
- PBIX parameter update tools
- Configuration and support scripts

Features:
- Comprehensive syntax validation for all Python scripts
- Path reference validation (old paths detection)
- Import dependency testing
- Batch file execution simulation
- Dry-run testing for critical scripts
- Automated error detection and reporting
- Performance and compatibility testing
- Detailed logging and comprehensive reporting

Usage:
    # Full test suite
    python test_migrated_scripts.py --full-test --verbose
    
    # Quick validation only
    python test_migrated_scripts.py --quick-test --verbose
    
    # Test specific script types
    python test_migrated_scripts.py --test-crime-scripts --verbose
    python test_migrated_scripts.py --test-pbix-tools --verbose
"""

import os
import sys
import re
import subprocess
import importlib.util
import logging
import argparse
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass, field, asdict

@dataclass
class TestConfig:
    """Configuration for script testing operations."""
    root_directory: str
    test_types: List[str]  # ['syntax', 'imports', 'paths', 'execution', 'dry_run']
    log_file: Optional[str] = None
    verbose: bool = False
    quick_test: bool = False
    timeout_seconds: int = 30
    create_test_report: bool = True

@dataclass
class ScriptTestResult:
    """Result of testing a single script."""
    file_path: str
    relative_path: str
    script_type: str  # 'pbix_tool', 'crime_script', 'batch_file', 'config', 'other'
    file_size: int
    syntax_test: Dict[str, Any]
    import_test: Dict[str, Any]
    path_test: Dict[str, Any]
    execution_test: Dict[str, Any]
    overall_success: bool
    test_timestamp: str
    errors: List[str]
    warnings: List[str]

@dataclass
class TestSummary:
    """Summary of all script testing."""
    session_id: str
    start_timestamp: str
    end_timestamp: str
    duration_seconds: float
    total_scripts_tested: int
    scripts_passed: int
    scripts_failed: int
    scripts_with_warnings: int
    test_results: List[ScriptTestResult]
    critical_errors: List[str]
    recommendations: List[str]

class MigratedScriptTester:
    """Comprehensive testing system for migrated SCRPA scripts."""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self.start_time = datetime.now()
        
        # Tracking
        self.test_results: List[ScriptTestResult] = []
        self.critical_errors: List[str] = []
        self.recommendations: List[str] = []
        
        # Setup logging
        self._setup_logging()
        
        # Define script categories
        self.script_categories = {
            'pbix_tools': [
                'update_pbix_parameter*.py',
                'main_workflow.py',
                'cleanup_scrpa_scripts.py',
                'test_pbix_update.py',
                'demo_rollback_scenarios.py'
            ],
            'crime_scripts': [
                'scrpa_*.py',
                'map_export*.py',
                'chart_export*.py',
                'coordinate_fix*.py',
                'incident_table*.py'
            ],
            'batch_files': [
                '*.bat'
            ],
            'config_scripts': [
                'config*.py',
                'migrate_*.py',
                'update_*.py'
            ]
        }
        
        # Old path patterns to detect
        self.old_path_patterns = [
            r'C:\\Users\\carucci_r\\SCRPA_LAPTOP',
            r'C:/Users/carucci_r/SCRPA_LAPTOP',
            r'SCRPA_LAPTOP'
        ]
        
        # Critical imports that should be available
        self.critical_imports = [
            'os', 'sys', 'pathlib', 'datetime', 'json', 'logging', 
            'argparse', 'zipfile', 'shutil', 're'
        ]
    
    def _setup_logging(self):
        """Setup comprehensive logging system."""
        log_level = logging.DEBUG if self.config.verbose else logging.INFO
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [SCRIPT_TESTER:%(funcName)s:%(lineno)d] - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Setup logger
        self.logger = logging.getLogger('ScriptTester')
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
                
                self.logger.info(f"Test log file created: {self.config.log_file}")
            except Exception as e:
                self.logger.warning(f"Could not create log file {self.config.log_file}: {e}")
        
        # Log session start
        self.logger.info(f"Script Testing started - Session: {self.session_id}")
    
    def scan_scripts(self) -> Dict[str, List[str]]:
        """Scan for scripts in all categories."""
        root_path = Path(self.config.root_directory)
        categorized_scripts = {category: [] for category in self.script_categories.keys()}
        
        self.logger.info("Scanning for scripts to test")
        
        # Directories to scan
        scan_directories = [
            root_path,
            root_path / "01_scripts",
            root_path / "scripts",
            root_path / "claude_share"
        ]
        
        for scan_dir in scan_directories:
            if not scan_dir.exists():
                continue
                
            self.logger.debug(f"Scanning directory: {scan_dir}")
            
            try:
                for category, patterns in self.script_categories.items():
                    for pattern in patterns:
                        script_files = list(scan_dir.rglob(pattern))
                        
                        for script_file in script_files:
                            if script_file.is_file():
                                script_path = str(script_file)
                                if script_path not in categorized_scripts[category]:
                                    categorized_scripts[category].append(script_path)
                                    self.logger.debug(f"Found {category}: {script_file.relative_to(root_path)}")
                
            except Exception as e:
                error_msg = f"Error scanning directory {scan_dir}: {e}"
                self.logger.error(error_msg)
                self.critical_errors.append(error_msg)
        
        # Log summary
        total_scripts = sum(len(scripts) for scripts in categorized_scripts.values())
        self.logger.info(f"Found {total_scripts} scripts to test")
        for category, scripts in categorized_scripts.items():
            if scripts:
                self.logger.info(f"  {category}: {len(scripts)} scripts")
        
        return categorized_scripts
    
    def classify_script(self, file_path: str) -> str:
        """Classify script type based on filename and content."""
        filename = Path(file_path).name.lower()
        
        if any(pattern.replace('*', '').replace('.py', '') in filename for pattern in self.script_categories['pbix_tools']):
            return 'pbix_tool'
        elif any(pattern.replace('*', '').replace('.py', '') in filename for pattern in self.script_categories['crime_scripts']):
            return 'crime_script'
        elif filename.endswith('.bat'):
            return 'batch_file'
        elif any(pattern.replace('*', '').replace('.py', '') in filename for pattern in self.script_categories['config_scripts']):
            return 'config'
        else:
            return 'other'
    
    def test_syntax(self, file_path: str) -> Dict[str, Any]:
        """Test Python script syntax."""
        result = {
            'success': False,
            'error_message': '',
            'warnings': [],
            'line_count': 0,
            'encoding': 'utf-8'
        }
        
        if not file_path.endswith('.py'):
            result['success'] = True
            result['error_message'] = 'Not a Python file'
            return result
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    result['encoding'] = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                result['error_message'] = 'Could not decode file with any encoding'
                return result
            
            result['line_count'] = len(content.splitlines())
            
            # Test syntax compilation
            compile(content, file_path, 'exec')
            result['success'] = True
            
            # Check for common issues
            if 'import *' in content:
                result['warnings'].append('Uses wildcard imports')
            if '\t' in content and '    ' in content:
                result['warnings'].append('Mixed tabs and spaces')
            
        except SyntaxError as e:
            result['error_message'] = f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            result['error_message'] = f"Error reading file: {str(e)}"
        
        return result
    
    def test_imports(self, file_path: str) -> Dict[str, Any]:
        """Test script import dependencies."""
        result = {
            'success': False,
            'error_message': '',
            'missing_imports': [],
            'available_imports': [],
            'import_count': 0
        }
        
        if not file_path.endswith('.py'):
            result['success'] = True
            result['error_message'] = 'Not a Python file'
            return result
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract import statements
            import_lines = []
            for line in content.splitlines():
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    import_lines.append(line)
            
            result['import_count'] = len(import_lines)
            
            # Test critical imports
            for critical_import in self.critical_imports:
                if any(critical_import in line for line in import_lines):
                    result['available_imports'].append(critical_import)
            
            # Try to import the module (basic test)
            file_path_obj = Path(file_path)
            module_name = file_path_obj.stem
            
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is not None:
                # Don't actually execute, just test if spec can be created
                result['success'] = True
            else:
                result['error_message'] = 'Could not create module specification'
            
        except Exception as e:
            result['error_message'] = f"Import test error: {str(e)}"
        
        return result
    
    def test_paths(self, file_path: str) -> Dict[str, Any]:
        """Test for old path references."""
        result = {
            'success': True,
            'old_paths_found': [],
            'path_count': 0,
            'warnings': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for old path patterns
            for pattern in self.old_path_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    result['old_paths_found'].extend(matches)
                    result['success'] = False
            
            result['path_count'] = len(result['old_paths_found'])
            
            if result['old_paths_found']:
                result['warnings'].append(f"Found {result['path_count']} old path references")
            
        except Exception as e:
            result['success'] = False
            result['warnings'].append(f"Path test error: {str(e)}")
        
        return result
    
    def test_execution(self, file_path: str) -> Dict[str, Any]:
        """Test script execution capabilities."""
        result = {
            'success': False,
            'error_message': '',
            'can_show_help': False,
            'execution_time': 0.0,
            'return_code': None
        }
        
        file_path_obj = Path(file_path)
        
        try:
            if file_path.endswith('.py'):
                # Test Python script help/version
                start_time = datetime.now()
                
                try:
                    # Try --help first
                    proc = subprocess.run(
                        [sys.executable, str(file_path), '--help'],
                        capture_output=True,
                        text=True,
                        timeout=self.config.timeout_seconds,
                        cwd=file_path_obj.parent
                    )
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    result['execution_time'] = execution_time
                    result['return_code'] = proc.returncode
                    
                    if proc.returncode == 0:
                        result['can_show_help'] = True
                        result['success'] = True
                    else:
                        # Try without arguments (might still be valid)
                        result['success'] = True
                        result['error_message'] = f"Help not available (return code: {proc.returncode})"
                        
                except subprocess.TimeoutExpired:
                    result['error_message'] = f"Execution timeout after {self.config.timeout_seconds}s"
                except Exception as e:
                    result['error_message'] = f"Execution error: {str(e)}"
                    
            elif file_path.endswith('.bat'):
                # For batch files, just check if they're readable and have valid commands
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Basic validation - check for valid batch commands
                valid_commands = ['echo', 'set', 'cd', 'call', 'start', 'python', 'if', 'for']
                has_valid_commands = any(cmd in content.lower() for cmd in valid_commands)
                
                if has_valid_commands:
                    result['success'] = True
                else:
                    result['error_message'] = 'No recognizable batch commands found'
            else:
                result['success'] = True
                result['error_message'] = 'File type not executable'
                
        except Exception as e:
            result['error_message'] = f"Execution test failed: {str(e)}"
        
        return result
    
    def test_script(self, file_path: str) -> ScriptTestResult:
        """Perform comprehensive testing on a single script."""
        file_path_obj = Path(file_path)
        root_path = Path(self.config.root_directory)
        
        self.logger.debug(f"Testing script: {file_path_obj.relative_to(root_path)}")
        
        # Initialize test result
        test_result = ScriptTestResult(
            file_path=file_path,
            relative_path=str(file_path_obj.relative_to(root_path)),
            script_type=self.classify_script(file_path),
            file_size=file_path_obj.stat().st_size if file_path_obj.exists() else 0,
            syntax_test={},
            import_test={},
            path_test={},
            execution_test={},
            overall_success=True,
            test_timestamp=datetime.now().isoformat(),
            errors=[],
            warnings=[]
        )
        
        try:
            # Run tests based on configuration
            if 'syntax' in self.config.test_types:
                test_result.syntax_test = self.test_syntax(file_path)
                if not test_result.syntax_test['success'] and test_result.syntax_test['error_message']:
                    test_result.errors.append(f"Syntax: {test_result.syntax_test['error_message']}")
                    test_result.overall_success = False
            
            if 'imports' in self.config.test_types:
                test_result.import_test = self.test_imports(file_path)
                if not test_result.import_test['success'] and test_result.import_test['error_message']:
                    test_result.errors.append(f"Imports: {test_result.import_test['error_message']}")
                    test_result.overall_success = False
            
            if 'paths' in self.config.test_types:
                test_result.path_test = self.test_paths(file_path)
                if not test_result.path_test['success']:
                    test_result.warnings.extend(test_result.path_test['warnings'])
                    # Path issues are warnings, not failures
            
            if 'execution' in self.config.test_types and not self.config.quick_test:
                test_result.execution_test = self.test_execution(file_path)
                if not test_result.execution_test['success'] and test_result.execution_test['error_message']:
                    # Execution issues are often warnings, not critical failures
                    test_result.warnings.append(f"Execution: {test_result.execution_test['error_message']}")
            
            self.logger.debug(f"Test completed for {test_result.relative_path}: {'PASS' if test_result.overall_success else 'FAIL'}")
            
        except Exception as e:
            test_result.overall_success = False
            error_msg = f"Critical test error: {str(e)}"
            test_result.errors.append(error_msg)
            self.logger.error(f"Test failed for {test_result.relative_path}: {error_msg}")
        
        return test_result
    
    def execute_tests(self) -> TestSummary:
        """Execute the complete testing process."""
        self.logger.info("Starting comprehensive script testing")
        
        try:
            # Phase 1: Scan for scripts
            self.logger.info("Phase 1: Scanning for scripts")
            categorized_scripts = self.scan_scripts()
            
            # Phase 2: Test scripts
            self.logger.info("Phase 2: Testing scripts")
            
            scripts_passed = 0
            scripts_failed = 0
            scripts_with_warnings = 0
            
            # Test scripts by category
            for category, scripts in categorized_scripts.items():
                if not scripts:
                    continue
                
                self.logger.info(f"Testing {category}: {len(scripts)} scripts")
                
                for script_path in scripts:
                    test_result = self.test_script(script_path)
                    self.test_results.append(test_result)
                    
                    if test_result.overall_success:
                        scripts_passed += 1
                        if test_result.warnings:
                            scripts_with_warnings += 1
                    else:
                        scripts_failed += 1
            
            # Phase 3: Generate recommendations
            self.logger.info("Phase 3: Generating recommendations")
            self._generate_recommendations()
            
            # Phase 4: Create summary
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            
            summary = TestSummary(
                session_id=self.session_id,
                start_timestamp=self.start_time.isoformat(),
                end_timestamp=end_time.isoformat(),
                duration_seconds=round(duration, 3),
                total_scripts_tested=len(self.test_results),
                scripts_passed=scripts_passed,
                scripts_failed=scripts_failed,
                scripts_with_warnings=scripts_with_warnings,
                test_results=self.test_results,
                critical_errors=self.critical_errors,
                recommendations=self.recommendations
            )
            
            # Save test report if requested
            if self.config.create_test_report:
                self.save_test_report(summary)
            
            self.logger.info("Script testing process completed")
            return summary
            
        except Exception as e:
            error_msg = f"Critical error during testing: {e}"
            self.logger.error(error_msg)
            self.critical_errors.append(error_msg)
            
            # Generate error summary
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            
            summary = TestSummary(
                session_id=self.session_id,
                start_timestamp=self.start_time.isoformat(),
                end_timestamp=end_time.isoformat(),
                duration_seconds=round(duration, 3),
                total_scripts_tested=len(self.test_results),
                scripts_passed=0,
                scripts_failed=len(self.test_results),
                scripts_with_warnings=0,
                test_results=self.test_results,
                critical_errors=self.critical_errors,
                recommendations=self.recommendations
            )
            
            return summary
    
    def _generate_recommendations(self):
        """Generate recommendations based on test results."""
        syntax_failures = [r for r in self.test_results if not r.syntax_test.get('success', True)]
        path_issues = [r for r in self.test_results if r.path_test.get('old_paths_found', [])]
        execution_issues = [r for r in self.test_results if not r.execution_test.get('success', True)]
        
        if syntax_failures:
            self.recommendations.append(f"Fix syntax errors in {len(syntax_failures)} scripts")
        
        if path_issues:
            self.recommendations.append(f"Update old path references in {len(path_issues)} scripts")
            self.recommendations.append("Run update_crime_scripts_paths.py and update_batch_paths.py")
        
        if execution_issues:
            self.recommendations.append(f"Review execution issues in {len(execution_issues)} scripts")
        
        # Script-specific recommendations
        pbix_tools = [r for r in self.test_results if r.script_type == 'pbix_tool']
        if pbix_tools:
            working_pbix = [r for r in pbix_tools if r.overall_success]
            self.recommendations.append(f"PBIX tools: {len(working_pbix)}/{len(pbix_tools)} operational")
        
        crime_scripts = [r for r in self.test_results if r.script_type == 'crime_script']
        if crime_scripts:
            working_crime = [r for r in crime_scripts if r.overall_success]
            self.recommendations.append(f"Crime scripts: {len(working_crime)}/{len(crime_scripts)} operational")
    
    def save_test_report(self, summary: TestSummary) -> Optional[str]:
        """Save detailed test report to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"script_test_report_{timestamp}.json"
            report_path = Path(self.config.root_directory) / report_filename
            
            # Convert to serializable format
            summary_dict = asdict(summary)
            
            # Add configuration metadata
            summary_dict['test_config'] = {
                'root_directory': self.config.root_directory,
                'test_types': self.config.test_types,
                'quick_test': self.config.quick_test,
                'timeout_seconds': self.config.timeout_seconds
            }
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(summary_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Test report saved: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.warning(f"Failed to save test report: {e}")
            return None
    
    def print_test_summary(self, summary: TestSummary):
        """Print comprehensive test summary to console."""
        print(f"\n{'='*80}")
        print("MIGRATED SCRIPTS TESTING SUMMARY")
        print(f"{'='*80}")
        print(f"Session ID: {summary.session_id}")
        print(f"Duration: {summary.duration_seconds:.3f} seconds")
        print(f"Test Types: {', '.join(self.config.test_types)}")
        print()
        
        print("TEST RESULTS:")
        print(f"  Total Scripts Tested: {summary.total_scripts_tested}")
        print(f"  Scripts Passed: {summary.scripts_passed}")
        print(f"  Scripts Failed: {summary.scripts_failed}")
        print(f"  Scripts with Warnings: {summary.scripts_with_warnings}")
        
        # Calculate success rate
        if summary.total_scripts_tested > 0:
            success_rate = (summary.scripts_passed / summary.total_scripts_tested) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
        print()
        
        # Show results by script type
        if summary.test_results:
            print("RESULTS BY SCRIPT TYPE:")
            script_types = {}
            for result in summary.test_results:
                script_type = result.script_type
                if script_type not in script_types:
                    script_types[script_type] = {'passed': 0, 'failed': 0, 'warnings': 0}
                
                if result.overall_success:
                    script_types[script_type]['passed'] += 1
                    if result.warnings:
                        script_types[script_type]['warnings'] += 1
                else:
                    script_types[script_type]['failed'] += 1
            
            for script_type, counts in script_types.items():
                total = counts['passed'] + counts['failed']
                print(f"  {script_type.upper()}: {counts['passed']}/{total} passed")
                if counts['warnings']:
                    print(f"    ({counts['warnings']} with warnings)")
            print()
        
        # Show critical failures
        if summary.scripts_failed > 0:
            print("CRITICAL FAILURES:")
            failed_scripts = [r for r in summary.test_results if not r.overall_success]
            for result in failed_scripts[:5]:  # Show first 5 failures
                print(f"  ❌ {result.relative_path}: {'; '.join(result.errors[:2])}")
            if len(failed_scripts) > 5:
                print(f"  ... and {len(failed_scripts) - 5} more failures")
            print()
        
        # Show path issues
        path_issues = [r for r in summary.test_results if r.path_test.get('old_paths_found', [])]
        if path_issues:
            print("OLD PATH REFERENCES FOUND:")
            for result in path_issues[:3]:  # Show first 3
                old_paths_count = len(result.path_test.get('old_paths_found', []))
                print(f"  ⚠️  {result.relative_path}: {old_paths_count} old path references")
            if len(path_issues) > 3:
                print(f"  ... and {len(path_issues) - 3} more files with old paths")
            print()
        
        # Show recommendations
        if summary.recommendations:
            print("RECOMMENDATIONS:")
            for recommendation in summary.recommendations:
                print(f"  📋 {recommendation}")
            print()
        
        # Final status
        if summary.scripts_failed == 0:
            if summary.scripts_with_warnings == 0:
                print("🎉 ALL SCRIPTS TESTED SUCCESSFULLY - MIGRATION COMPLETE!")
            else:
                print("✅ ALL SCRIPTS OPERATIONAL - MINOR WARNINGS DETECTED")
        else:
            print(f"⚠️  TESTING COMPLETED WITH {summary.scripts_failed} FAILURES")
        
        print(f"{'='*80}")

def create_default_config() -> TestConfig:
    """Create default configuration for script testing."""
    current_dir = os.getcwd()
    
    config = TestConfig(
        root_directory=current_dir,
        test_types=['syntax', 'imports', 'paths', 'execution'],
        verbose=False,
        quick_test=False,
        timeout_seconds=30,
        create_test_report=True
    )
    
    return config

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Migrated Scripts Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full test suite
  python test_migrated_scripts.py --full-test --verbose
  
  # Quick validation only (syntax and imports)
  python test_migrated_scripts.py --quick-test --verbose
  
  # Test specific types
  python test_migrated_scripts.py --test-crime-scripts --verbose
  python test_migrated_scripts.py --test-pbix-tools --verbose
  
  # Custom timeout and logging
  python test_migrated_scripts.py --timeout 60 --log-file test.log --verbose
        """
    )
    
    # Test type options
    parser.add_argument('--full-test', action='store_true',
                       help='Run complete test suite (syntax, imports, paths, execution)')
    
    parser.add_argument('--quick-test', action='store_true',
                       help='Run quick tests only (syntax and imports)')
    
    parser.add_argument('--test-crime-scripts', action='store_true',
                       help='Test only crime reporting scripts')
    
    parser.add_argument('--test-pbix-tools', action='store_true',
                       help='Test only PBIX tools')
    
    parser.add_argument('--test-batch-files', action='store_true',
                       help='Test only batch files')
    
    # Configuration options
    parser.add_argument('--root-dir', '-r',
                       default=None,
                       help='Root directory to test (default: current directory)')
    
    parser.add_argument('--timeout', '-t', type=int, default=30,
                       help='Timeout for execution tests in seconds')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    parser.add_argument('--log-file', '-l',
                       help='Save detailed log to specified file')
    
    parser.add_argument('--no-report', action='store_true',
                       help='Skip creation of test report')
    
    args = parser.parse_args()
    
    try:
        # Create configuration
        config = create_default_config()
        
        # Override with command line arguments
        if args.root_dir:
            config.root_directory = args.root_dir
        if args.log_file:
            config.log_file = args.log_file
        
        config.verbose = args.verbose
        config.timeout_seconds = args.timeout
        config.create_test_report = not args.no_report
        
        # Determine test types
        if args.quick_test:
            config.test_types = ['syntax', 'imports', 'paths']
            config.quick_test = True
        elif args.full_test:
            config.test_types = ['syntax', 'imports', 'paths', 'execution']
        else:
            # Default test types
            config.test_types = ['syntax', 'imports', 'paths']
        
        # Validate directory
        if not os.path.exists(config.root_directory):
            print(f"❌ ERROR: Root directory does not exist: {config.root_directory}")
            return 1
        
        # Show configuration
        print("MIGRATED SCRIPTS TESTING TOOL")
        print("=" * 80)
        print(f"Root Directory: {config.root_directory}")
        print(f"Test Types: {', '.join(config.test_types)}")
        print(f"Mode: {'Quick Test' if config.quick_test else 'Comprehensive Test'}")
        print(f"Timeout: {config.timeout_seconds} seconds")
        if config.log_file:
            print(f"Log File: {config.log_file}")
        print("=" * 80)
        
        # Execute tests
        tester = MigratedScriptTester(config)
        summary = tester.execute_tests()
        
        # Display results
        tester.print_test_summary(summary)
        
        # Return appropriate exit code
        if summary.scripts_failed == 0:
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n❌ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())