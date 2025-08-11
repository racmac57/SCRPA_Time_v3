#!/usr/bin/env python3
"""
Simple test runner for the updated CAD notes tests.
Validates that the tests work with the existing 01_scripts processors.
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the test functions
try:
    from test_cadnotes import (
        test_username_and_timestamp_extraction,
        test_enhanced_processor_validation,
        test_empty_cadnotes_handling,
        test_complex_cadnotes_parsing,
        test_data_quality_scoring
    )
    print("✅ Successfully imported all test functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def run_test(test_func, test_name):
    """Run a single test function and report results."""
    try:
        print(f"\n🧪 Running {test_name}...")
        test_func()
        print(f"✅ {test_name} PASSED")
        return True
    except Exception as e:
        print(f"❌ {test_name} FAILED: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all tests and report summary."""
    print("=" * 60)
    print("🚀 RUNNING UPDATED CAD NOTES TESTS")
    print("=" * 60)
    
    tests = [
        (test_username_and_timestamp_extraction, "Username and Timestamp Extraction"),
        (test_enhanced_processor_validation, "Enhanced Processor Validation"),
        (test_empty_cadnotes_handling, "Empty CADNotes Handling"),
        (test_complex_cadnotes_parsing, "Complex CADNotes Parsing"),
        (test_data_quality_scoring, "Data Quality Scoring")
    ]
    
    passed = 0
    failed = 0
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Tests Passed: {passed}")
    print(f"❌ Tests Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! The integration is working correctly.")
        print("The claude_share tests now successfully work with the existing 01_scripts processors.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review the errors above.")
        print("The integration may need additional adjustments.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)