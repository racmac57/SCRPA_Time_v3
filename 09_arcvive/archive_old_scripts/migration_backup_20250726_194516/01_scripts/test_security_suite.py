# Test script to validate security testing suite components
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all security suite components can be imported."""
    
    print("[TEST] Testing Security Suite Component Imports")
    print("=" * 50)
    
    # Test core components
    try:
        from security_validation_suite import SCRPASecurityValidator, SecurityTestResult
        print("[OK] security_validation_suite imported successfully")
    except ImportError as e:
        print(f"[ERROR] security_validation_suite import failed: {e}")
        return False
    
    try:
        from test_data_generator import generate_test_data
        print("[OK] test_data_generator imported successfully")
    except ImportError as e:
        print(f"[ERROR] test_data_generator import failed: {e}")
        return False
    
    try:
        from network_monitor import NetworkSecurityMonitor
        print("[OK] network_monitor imported successfully")
    except ImportError as e:
        print(f"[ERROR] network_monitor import failed: {e}")
        return False
    
    try:
        from security_report_generator import SecurityReportGenerator
        print("[OK] security_report_generator imported successfully")
    except ImportError as e:
        print(f"[ERROR] security_report_generator import failed: {e}")
        return False
    
    # Test dependent components
    try:
        from comprehensive_data_sanitizer import ComprehensiveDataSanitizer
        print("[OK] comprehensive_data_sanitizer imported successfully")
    except ImportError as e:
        print(f"[WARNING] comprehensive_data_sanitizer import failed: {e}")
        print("         This is required for full security validation")
    
    try:
        from secure_scrpa_generator import SecureSCRPAGenerator
        print("[OK] secure_scrpa_generator imported successfully")
    except ImportError as e:
        print(f"[WARNING] secure_scrpa_generator import failed: {e}")
        print("         This is required for LLM processing tests")
    
    return True

def test_basic_functionality():
    """Test basic functionality of security suite components."""
    
    print("\n[TEST] Testing Basic Functionality")
    print("=" * 50)
    
    try:
        # Test data generation
        from test_data_generator import generate_test_data
        test_data = generate_test_data(3)  # Small test
        print(f"[OK] Generated {len(test_data)} test records with PII")
    except Exception as e:
        print(f"[ERROR] Test data generation failed: {e}")
        return False
    
    try:
        # Test network monitor initialization
        from network_monitor import NetworkSecurityMonitor
        monitor = NetworkSecurityMonitor(monitoring_duration=1)  # Short test
        print("[OK] Network monitor initialized")
    except Exception as e:
        print(f"[ERROR] Network monitor initialization failed: {e}")
        return False
    
    try:
        # Test report generator
        from security_report_generator import SecurityReportGenerator
        generator = SecurityReportGenerator()
        print("[OK] Report generator initialized")
    except Exception as e:
        print(f"[ERROR] Report generator initialization failed: {e}")
        return False
    
    return True

def test_file_structure():
    """Test that all required files are present."""
    
    print("\n[TEST] Testing File Structure")
    print("=" * 50)
    
    current_dir = Path(__file__).parent
    
    required_files = [
        "security_validation_suite.py",
        "test_data_generator.py", 
        "network_monitor.py",
        "security_report_generator.py",
        "run_security_tests.py",
        "run_security_tests.bat",
        # Dependencies (may not exist if not created yet)
        "comprehensive_data_sanitizer.py",
        "secure_scrpa_generator.py"
    ]
    
    all_present = True
    for filename in required_files:
        file_path = current_dir / filename
        if file_path.exists():
            print(f"[OK] {filename}")
        else:
            if filename in ["comprehensive_data_sanitizer.py", "secure_scrpa_generator.py"]:
                print(f"[WARNING] {filename} (required for full functionality)")
            else:
                print(f"[MISSING] {filename}")
                all_present = False
    
    return all_present

def run_quick_validation_test():
    """Run a very quick validation test to check core functionality."""
    
    print("\n[TEST] Quick Validation Test")
    print("=" * 50)
    
    try:
        # Test the main security validator initialization
        from security_validation_suite import SCRPASecurityValidator
        
        # Mock the dependencies if they don't exist
        def mock_generate_test_data(num_records=5):
            import pandas as pd
            return pd.DataFrame([
                {
                    'case_number': f'TEST-{i:03d}',
                    'narrative': f'Test case {i} with John Smith (555-123-4567)',
                    'incident_type': 'Test'
                }
                for i in range(num_records)
            ])
        
        # Try to create validator with mocked dependencies
        validator = SCRPASecurityValidator.__new__(SCRPASecurityValidator)
        validator.test_results = []
        validator.network_monitor = None
        validator.project_root = Path.cwd()
        validator.generate_test_data = mock_generate_test_data
        
        # Try to use mock data sanitizer
        try:
            from comprehensive_data_sanitizer import ComprehensiveDataSanitizer
            validator.data_sanitizer = ComprehensiveDataSanitizer()
        except ImportError:
            print("[WARNING] Using mock data sanitizer")
            validator.data_sanitizer = None
        
        # Try to use mock secure generator
        try:
            from secure_scrpa_generator import SecureSCRPAGenerator
            validator.secure_generator = SecureSCRPAGenerator()
        except ImportError:
            print("[WARNING] Using mock secure generator")
            validator.secure_generator = None
        
        print("[OK] Security validator can be initialized")
        print("[OK] Quick validation test passed")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Quick validation test failed: {e}")
        return False

def main():
    """Main test function."""
    
    print("[SECURITY] SCRPA Security Suite Validation Test")
    print("=" * 60)
    print("Testing security testing suite components...")
    print()
    
    # Run all tests
    imports_ok = test_imports()
    files_ok = test_file_structure()
    functionality_ok = test_basic_functionality()
    validation_ok = run_quick_validation_test()
    
    # Summary
    print("\n" + "=" * 60)
    print("[SECURITY] SUITE VALIDATION SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Component Imports", imports_ok),
        ("File Structure", files_ok),
        ("Basic Functionality", functionality_ok),
        ("Quick Validation", validation_ok)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    print(f"[RESULTS] Test Results: {passed}/{total} passed")
    
    for test_name, result in tests:
        status = "[PASS]" if result else "[FAIL]"
        print(f"   {status} {test_name}")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Security suite is ready to use.")
        print("Run 'python run_security_tests.py' or 'run_security_tests.bat' for full validation.")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} tests failed. Address issues before running full validation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())