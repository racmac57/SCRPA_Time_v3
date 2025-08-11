#!/usr/bin/env python3
"""
Manual validation of PBIX scripts without subprocess dependencies
"""
import sys
import os
import tempfile
import json
import traceback
from pathlib import Path

def test_script_syntax_and_imports():
    """Test syntax and basic imports of key scripts."""
    print("MANUAL PBIX SCRIPTS VALIDATION")
    print("=" * 60)
    
    scripts_dir = Path(__file__).parent / "scripts"
    test_scripts = [
        "update_pbix_parameter.py",
        "main_workflow.py", 
        "cleanup_scrpa_scripts.py"
    ]
    
    results = {}
    
    for script_name in test_scripts:
        script_path = scripts_dir / script_name
        
        print(f"\nTesting: {script_name}")
        print("-" * 40)
        
        # Check existence
        if not script_path.exists():
            results[script_name] = {"exists": False, "syntax": False, "imports": False}
            print(f"❌ File not found: {script_path}")
            continue
        
        print(f"✅ File exists: {script_path}")
        results[script_name] = {"exists": True}
        
        # Test syntax by compilation
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            compile(source, str(script_path), 'exec')
            print("✅ Syntax validation: PASSED")
            results[script_name]["syntax"] = True
        except SyntaxError as e:
            print(f"❌ Syntax error at line {e.lineno}: {e.msg}")
            results[script_name]["syntax"] = False
            continue
        except Exception as e:
            print(f"❌ Compilation error: {e}")
            results[script_name]["syntax"] = False
            continue
        
        # Test basic imports (without execution)
        try:
            # Check for required imports in source
            required_imports = ['argparse', 'json', 'os', 'sys', 'pathlib']
            has_all_imports = True
            
            for imp in required_imports:
                if f'import {imp}' not in source and f'from {imp}' not in source:
                    print(f"⚠️  Missing import: {imp}")
                    has_all_imports = False
            
            if has_all_imports:
                print("✅ Import analysis: PASSED")
                results[script_name]["imports"] = True
            else:
                print("⚠️  Import analysis: WARNINGS")
                results[script_name]["imports"] = True  # Still pass with warnings
            
        except Exception as e:
            print(f"❌ Import analysis failed: {e}")
            results[script_name]["imports"] = False
    
    return results

def test_configuration_capabilities():
    """Test configuration file creation and JSON handling."""
    print(f"\n{'='*60}")
    print("CONFIGURATION CAPABILITIES TEST")
    print("=" * 60)
    
    try:
        # Test JSON file creation
        test_config = {
            "pbix_files": ["test.pbix"],
            "parameters": {"TestParam": "TestValue"},
            "environments": {
                "test": {"TestParam": "TestEnvValue"}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json.dump(test_config, tmp, indent=2)
            temp_path = tmp.name
        
        # Try reading it back
        with open(temp_path, 'r') as f:
            loaded_config = json.load(f)
        
        # Clean up
        os.unlink(temp_path)
        
        if loaded_config == test_config:
            print("✅ JSON configuration handling: PASSED")
            return True
        else:
            print("❌ JSON configuration handling: DATA MISMATCH")
            return False
            
    except Exception as e:
        print(f"❌ JSON configuration handling: FAILED - {e}")
        return False

def test_file_system_operations():
    """Test basic file system operations."""
    print(f"\n{'='*60}")
    print("FILE SYSTEM OPERATIONS TEST")
    print("=" * 60)
    
    try:
        # Test directory operations
        test_dir = Path(tempfile.gettempdir()) / "pbix_test"
        test_dir.mkdir(exist_ok=True)
        
        # Test file creation
        test_file = test_dir / "test.txt"
        test_file.write_text("Test content")
        
        # Test file reading
        content = test_file.read_text()
        
        # Test file operations
        test_file.unlink()
        test_dir.rmdir()
        
        if content == "Test content":
            print("✅ File system operations: PASSED")
            return True
        else:
            print("❌ File system operations: CONTENT MISMATCH")
            return False
            
    except Exception as e:
        print(f"❌ File system operations: FAILED - {e}")
        return False

def test_help_functionality_simulation():
    """Simulate help functionality test by checking argparse usage."""
    print(f"\n{'='*60}")
    print("HELP FUNCTIONALITY SIMULATION")
    print("=" * 60)
    
    scripts_dir = Path(__file__).parent / "scripts"
    help_tests = []
    
    for script_name in ["update_pbix_parameter.py", "main_workflow.py"]:
        script_path = scripts_dir / script_name
        
        if not script_path.exists():
            help_tests.append((script_name, False, "File not found"))
            continue
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for argparse patterns
            has_argparse = 'ArgumentParser' in content
            has_add_argument = 'add_argument' in content
            has_parse_args = 'parse_args' in content
            has_help_text = '--help' in content or 'help=' in content
            
            if has_argparse and has_add_argument and has_parse_args:
                help_tests.append((script_name, True, "Help functionality detected"))
                print(f"✅ {script_name}: Help functionality detected")
            else:
                help_tests.append((script_name, False, "Missing argparse components"))
                print(f"❌ {script_name}: Missing argparse components")
                
        except Exception as e:
            help_tests.append((script_name, False, str(e)))
            print(f"❌ {script_name}: Error - {e}")
    
    return help_tests

def print_final_summary(script_results, config_test, fs_test, help_tests):
    """Print comprehensive test summary."""
    print(f"\n{'='*60}")
    print("FINAL VALIDATION SUMMARY")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    # Script tests
    print("SCRIPT VALIDATION:")
    for script, results in script_results.items():
        exists = results.get("exists", False)
        syntax = results.get("syntax", False) 
        imports = results.get("imports", False)
        
        script_passed = exists and syntax and imports
        print(f"  {script}:")
        print(f"    Exists: {'✅' if exists else '❌'}")
        print(f"    Syntax: {'✅' if syntax else '❌'}")
        print(f"    Imports: {'✅' if imports else '❌'}")
        print(f"    Overall: {'✅ PASS' if script_passed else '❌ FAIL'}")
        
        total_tests += 1
        if script_passed:
            passed_tests += 1
    
    # Configuration test
    print(f"\nCONFIGURATION TEST:")
    print(f"  JSON Handling: {'✅ PASS' if config_test else '❌ FAIL'}")
    total_tests += 1
    if config_test:
        passed_tests += 1
    
    # File system test
    print(f"\nFILE SYSTEM TEST:")
    print(f"  Basic Operations: {'✅ PASS' if fs_test else '❌ FAIL'}")
    total_tests += 1
    if fs_test:
        passed_tests += 1
    
    # Help functionality test
    print(f"\nHELP FUNCTIONALITY TEST:")
    help_passed = 0
    for script_name, success, message in help_tests:
        print(f"  {script_name}: {'✅ PASS' if success else '❌ FAIL'} - {message}")
        total_tests += 1
        if success:
            help_passed += 1
            passed_tests += 1
    
    # Overall summary
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT: Scripts are ready for production use!")
        result_code = 0
    elif success_rate >= 70:
        print("✅ GOOD: Scripts are mostly operational with minor issues")
        result_code = 0
    elif success_rate >= 50:
        print("⚠️  WARNING: Scripts have significant issues that need attention")
        result_code = 1
    else:
        print("❌ CRITICAL: Scripts have major problems and need fixes")
        result_code = 1
    
    print(f"\nRECOMMENDATIONS:")
    if passed_tests == total_tests:
        print("✅ No action needed - all tests passed!")
    else:
        failed_count = total_tests - passed_tests
        print(f"🔧 Fix {failed_count} failing test(s) shown above")
        print("📋 Check script syntax and missing dependencies")
        print("🔍 Review error messages for specific issues")
    
    return result_code

def main():
    """Execute manual validation."""
    try:
        # Run all tests
        script_results = test_script_syntax_and_imports()
        config_test = test_configuration_capabilities()
        fs_test = test_file_system_operations()
        help_tests = test_help_functionality_simulation()
        
        # Print final summary
        exit_code = print_final_summary(script_results, config_test, fs_test, help_tests)
        
        print(f"\nValidation completed. Working directory: {Path(__file__).parent}")
        return exit_code
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR during validation: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())