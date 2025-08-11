#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_enhanced_pbix.py

Test script for the enhanced PBIX parameter updater.
Tests various scenarios and validation capabilities.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import zipfile
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from update_pbix_parameter_enhanced import PBIXParameterUpdater

class PBIXTester:
    """Test suite for enhanced PBIX parameter updater."""
    
    def __init__(self):
        self.test_results = []
        self.test_dir = None
        
    def setup_test_environment(self):
        """Create test environment with sample files."""
        self.test_dir = tempfile.mkdtemp(prefix="pbix_test_")
        print(f"Test directory: {self.test_dir}")
        
        # Create a mock PBIX file structure
        self.create_mock_pbix()
        
    def create_mock_pbix(self):
        """Create a mock PBIX file for testing."""
        mock_pbix_path = os.path.join(self.test_dir, "test_report.pbix")
        
        # Create temporary directory for PBIX contents
        with tempfile.TemporaryDirectory() as temp_contents:
            # Create standard PBIX files
            with open(os.path.join(temp_contents, "Version"), "w") as f:
                f.write("1.0")
            
            with open(os.path.join(temp_contents, "Metadata"), "w") as f:
                f.write('{"version": "1.0"}')
                
            with open(os.path.join(temp_contents, "Settings"), "w") as f:
                f.write("{}")
            
            # Create mock DataMashup with parameters
            datamashup_content = '''
let
    BasePath = "C:\\Old\\Path\\Data",
    ServerName = "localhost",
    DatabaseName = "CrimeDB",
    Source = Excel.Workbook(File.Contents(BasePath & "\\data.xlsx")),
    Table1 = Source{[Item="Sheet1",Kind="Sheet"]}[Data]
in
    Table1
'''
            
            with open(os.path.join(temp_contents, "DataMashup"), "w", encoding="latin1") as f:
                f.write(datamashup_content)
            
            # Create ZIP file (PBIX)
            with zipfile.ZipFile(mock_pbix_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                for root, _, files in os.walk(temp_contents):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, temp_contents)
                        zip_out.write(full_path, rel_path)
        
        return mock_pbix_path
    
    def run_test(self, test_name, test_func):
        """Run a single test and record results."""
        print(f"\n🧪 Running test: {test_name}")
        try:
            result = test_func()
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}")
            self.test_results.append({
                'name': test_name,
                'status': 'PASS' if result else 'FAIL',
                'details': getattr(result, 'details', None) if hasattr(result, 'details') else None
            })
            return result
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.test_results.append({
                'name': test_name,
                'status': 'ERROR',
                'error': str(e)
            })
            return False
    
    def test_input_validation(self):
        """Test input file validation."""
        updater = PBIXParameterUpdater(verbose=False)
        
        # Test with mock PBIX
        mock_pbix_path = os.path.join(self.test_dir, "test_report.pbix")
        validation = updater.validate_input_file(mock_pbix_path)
        
        # Check validation results
        checks = [
            validation['file_exists'],
            validation['is_pbix'],
            validation['is_valid_zip'],
            validation['datamashup_found'],
            len(validation['parameters_detected']) > 0,
            len(validation['errors']) == 0
        ]
        
        print(f"   - File exists: {'✅' if validation['file_exists'] else '❌'}")
        print(f"   - Valid PBIX: {'✅' if validation['is_pbix'] else '❌'}")
        print(f"   - DataMashup found: {'✅' if validation['datamashup_found'] else '❌'}")
        print(f"   - Parameters detected: {len(validation['parameters_detected'])}")
        
        return all(checks)
    
    def test_parameter_detection(self):
        """Test parameter detection in DataMashup."""
        updater = PBIXParameterUpdater(verbose=False)
        
        mock_pbix_path = os.path.join(self.test_dir, "test_report.pbix")
        validation = updater.validate_parameter_exists(mock_pbix_path, "BasePath")
        
        checks = [
            validation['parameter_found'],
            validation['current_value'] == "C:\\Old\\Path\\Data",
            len(validation['errors']) == 0
        ]
        
        print(f"   - Parameter found: {'✅' if validation['parameter_found'] else '❌'}")
        print(f"   - Current value: {validation['current_value']}")
        
        return all(checks)
    
    def test_path_validation(self):
        """Test path validation."""
        updater = PBIXParameterUpdater(verbose=False)
        
        input_path = os.path.join(self.test_dir, "test_report.pbix")
        output_path = os.path.join(self.test_dir, "test_report_updated.pbix")
        
        validation = updater.validate_paths(input_path, output_path)
        
        checks = [
            validation['input_accessible'],
            validation['output_writable'],
            validation['paths_different'],
            len(validation['errors']) == 0
        ]
        
        print(f"   - Input accessible: {'✅' if validation['input_accessible'] else '❌'}")
        print(f"   - Output writable: {'✅' if validation['output_writable'] else '❌'}")
        print(f"   - Paths different: {'✅' if validation['paths_different'] else '❌'}")
        
        return all(checks)
    
    def test_parameter_update(self):
        """Test actual parameter update functionality."""
        updater = PBIXParameterUpdater(verbose=False)
        
        input_path = os.path.join(self.test_dir, "test_report.pbix")
        output_path = os.path.join(self.test_dir, "test_report_updated.pbix")
        new_value = "C:\\New\\Path\\Data"
        
        result = updater.process_pbix_with_validation(
            input_path, output_path, "BasePath", new_value
        )
        
        checks = [
            result['success'],
            len(result['errors']) == 0,
            os.path.exists(output_path),
            result.get('post_validation', {}).get('value_matches', False)
        ]
        
        print(f"   - Update successful: {'✅' if result['success'] else '❌'}")
        print(f"   - Output file created: {'✅' if os.path.exists(output_path) else '❌'}")
        print(f"   - Value matches: {'✅' if result.get('post_validation', {}).get('value_matches', False) else '❌'}")
        print(f"   - Errors: {len(result['errors'])}")
        
        return all(checks)
    
    def test_invalid_file_handling(self):
        """Test handling of invalid files."""
        updater = PBIXParameterUpdater(verbose=False)
        
        # Test with non-existent file
        validation = updater.validate_input_file("nonexistent.pbix")
        
        checks = [
            not validation['file_exists'],
            len(validation['errors']) > 0
        ]
        
        print(f"   - Correctly detects missing file: {'✅' if not validation['file_exists'] else '❌'}")
        print(f"   - Reports errors: {'✅' if len(validation['errors']) > 0 else '❌'}")
        
        return all(checks)
    
    def test_backup_creation(self):
        """Test backup creation functionality."""
        updater = PBIXParameterUpdater(verbose=False)
        
        input_path = os.path.join(self.test_dir, "test_report.pbix")
        backup_path = updater.create_backup(input_path)
        
        checks = [
            backup_path is not None,
            os.path.exists(backup_path) if backup_path else False,
            updater.backup_created
        ]
        
        print(f"   - Backup created: {'✅' if backup_path else '❌'}")
        print(f"   - Backup file exists: {'✅' if os.path.exists(backup_path) if backup_path else False else '❌'}")
        
        return all(checks)
    
    def test_report_generation(self):
        """Test validation report generation."""
        updater = PBIXParameterUpdater(verbose=False)
        
        # Create a sample result
        sample_result = {
            'success': True,
            'pre_validation': {'input_file': {'file_exists': True}},
            'post_validation': {'value_matches': True},
            'processing_log': ['Test log entry'],
            'errors': []
        }
        
        report_path = os.path.join(self.test_dir, "test_report.txt")
        report_content = updater.generate_validation_report(sample_result, report_path)
        
        checks = [
            len(report_content) > 0,
            os.path.exists(report_path),
            "VALIDATION REPORT" in report_content
        ]
        
        print(f"   - Report generated: {'✅' if len(report_content) > 0 else '❌'}")
        print(f"   - Report file saved: {'✅' if os.path.exists(report_path) else '❌'}")
        
        return all(checks)
    
    def run_all_tests(self):
        """Run all test cases."""
        print("🚀 STARTING ENHANCED PBIX PARAMETER UPDATER TESTS")
        print("=" * 70)
        
        # Setup test environment
        self.setup_test_environment()
        
        # Run individual tests
        tests = [
            ("Input File Validation", self.test_input_validation),
            ("Parameter Detection", self.test_parameter_detection),
            ("Path Validation", self.test_path_validation),
            ("Parameter Update", self.test_parameter_update),
            ("Invalid File Handling", self.test_invalid_file_handling),
            ("Backup Creation", self.test_backup_creation),
            ("Report Generation", self.test_report_generation)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
        
        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {total - passed} ❌")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        # Detailed results
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"  {status_icon} {result['name']}: {result['status']}")
            if result['status'] == 'ERROR':
                print(f"     Error: {result['error']}")
        
        # Cleanup
        if self.test_dir and os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
                print(f"\n🧹 Cleaned up test directory: {self.test_dir}")
            except Exception as e:
                print(f"\n⚠️  Could not clean up test directory: {e}")
        
        return passed == total

def main():
    """Main test execution."""
    tester = PBIXTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())