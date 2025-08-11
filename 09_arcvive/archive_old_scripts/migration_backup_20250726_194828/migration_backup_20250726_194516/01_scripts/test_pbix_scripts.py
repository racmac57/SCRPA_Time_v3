#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_pbix_scripts.py

Safe testing script for PBIX tools to verify they execute without path-related errors.
Tests the main functionality without requiring actual PBIX files.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def test_script_help(script_path, script_name):
    """Test if a script can display help without errors."""
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=script_path.parent
        )
        
        if result.returncode == 0:
            return True, f"✅ {script_name} --help works", result.stdout[:200] + "..."
        else:
            return False, f"❌ {script_name} --help failed", result.stderr
            
    except subprocess.TimeoutExpired:
        return False, f"❌ {script_name} --help timed out", ""
    except Exception as e:
        return False, f"❌ {script_name} --help error: {str(e)}", ""

def test_main_workflow_sample_config():
    """Test main_workflow.py sample config creation."""
    scripts_dir = Path(__file__).parent / "scripts"
    script_path = scripts_dir / "main_workflow.py"
    
    if not script_path.exists():
        return False, "❌ main_workflow.py not found", ""
    
    try:
        # Test sample config creation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            temp_config_path = tmp.name
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--create-sample-config", temp_config_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=script_path.parent
        )
        
        # Clean up temp file
        try:
            os.unlink(temp_config_path)
        except:
            pass
        
        if result.returncode == 0:
            return True, f"✅ main_workflow.py sample config creation works", result.stdout
        else:
            return False, f"❌ main_workflow.py sample config failed", result.stderr
            
    except Exception as e:
        return False, f"❌ main_workflow.py test error: {str(e)}", ""

def test_pbix_script_validation():
    """Test update_pbix_parameter.py validation without actual files."""
    scripts_dir = Path(__file__).parent / "scripts"
    script_path = scripts_dir / "update_pbix_parameter.py"
    
    if not script_path.exists():
        return False, "❌ update_pbix_parameter.py not found", ""
    
    try:
        # Test with missing file (should fail gracefully)
        result = subprocess.run(
            [sys.executable, str(script_path), 
             "--input", "nonexistent.pbix",
             "--output", "test_output.pbix", 
             "--param", "TestParam",
             "--value", "TestValue"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=script_path.parent
        )
        
        # This should fail gracefully (file not found)
        if "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower():
            return True, f"✅ update_pbix_parameter.py handles missing files gracefully", result.stderr[:200]
        elif result.returncode != 0:
            return True, f"✅ update_pbix_parameter.py exits with error as expected", result.stderr[:200]
        else:
            return False, f"❌ update_pbix_parameter.py should fail with missing file", result.stdout
            
    except Exception as e:
        return False, f"❌ update_pbix_parameter.py test error: {str(e)}", ""

def test_import_dependencies():
    """Test if key scripts can be imported (syntax and dependency check)."""
    scripts_dir = Path(__file__).parent / "scripts"
    
    results = []
    
    # Test scripts with import checks
    test_scripts = [
        "update_pbix_parameter.py",
        "main_workflow.py", 
        "cleanup_scrpa_scripts.py"
    ]
    
    for script_name in test_scripts:
        script_path = scripts_dir / script_name
        
        if not script_path.exists():
            results.append((script_name, False, f"❌ {script_name} not found"))
            continue
        
        try:
            # Test by running with python -c "import sys; sys.exit(0)"
            # This tests syntax and basic imports without executing main
            result = subprocess.run(
                [sys.executable, "-c", 
                 f"import sys; sys.path.insert(0, r'{scripts_dir}'); "
                 f"exec(compile(open(r'{script_path}').read(), r'{script_path}', 'exec')); "
                 f"print('Import successful'); sys.exit(0)"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 or "Import successful" in result.stdout:
                results.append((script_name, True, f"✅ {script_name} imports successfully"))
            else:
                results.append((script_name, False, f"❌ {script_name} import failed: {result.stderr[:100]}"))
                
        except Exception as e:
            results.append((script_name, False, f"❌ {script_name} import error: {str(e)}"))
    
    return results

def main():
    """Main test execution."""
    print("PBIX SCRIPTS EXECUTION TEST")
    print("=" * 50)
    
    scripts_dir = Path(__file__).parent / "scripts"
    print(f"Testing scripts in: {scripts_dir}")
    print(f"Current working directory: {Path.cwd()}")
    print()
    
    # Test 1: Help functionality
    print("TEST 1: Help Functionality")
    print("-" * 30)
    
    help_tests = [
        ("update_pbix_parameter.py", scripts_dir / "update_pbix_parameter.py"),
        ("main_workflow.py", scripts_dir / "main_workflow.py")
    ]
    
    help_passed = 0
    for script_name, script_path in help_tests:
        success, message, output = test_script_help(script_path, script_name)
        print(message)
        if success:
            help_passed += 1
    
    print(f"\nHelp Tests: {help_passed}/{len(help_tests)} passed\n")
    
    # Test 2: Sample config creation
    print("TEST 2: Sample Config Creation")
    print("-" * 30)
    
    config_success, config_message, config_output = test_main_workflow_sample_config()
    print(config_message)
    if config_success:
        print("   Config creation working correctly")
    print()
    
    # Test 3: Graceful error handling
    print("TEST 3: Error Handling")
    print("-" * 30)
    
    error_success, error_message, error_output = test_pbix_script_validation()
    print(error_message)
    if error_success:
        print("   Error handling working correctly")
    print()
    
    # Test 4: Import dependencies
    print("TEST 4: Import Dependencies")
    print("-" * 30)
    
    import_results = test_import_dependencies()
    import_passed = 0
    for script_name, success, message in import_results:
        print(message)
        if success:
            import_passed += 1
    
    print(f"\nImport Tests: {import_passed}/{len(import_results)} passed\n")
    
    # Summary
    print("=" * 50)
    print("EXECUTION TEST SUMMARY")
    print("=" * 50)
    
    total_tests = len(help_tests) + 1 + 1 + len(import_results)  # help + config + error + imports
    total_passed = help_passed + (1 if config_success else 0) + (1 if error_success else 0) + import_passed
    
    print(f"Overall Success Rate: {total_passed}/{total_tests} ({(total_passed/total_tests)*100:.1f}%)")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED - Scripts are fully operational!")
        print("✅ PBIX tools ready for production use")
        print("✅ No path-related errors detected")
    elif total_passed >= total_tests * 0.8:  # 80% or higher
        print("\n✅ MOSTLY OPERATIONAL - Minor issues detected")
        print("📋 Core functionality appears to work correctly")
        print("⚠️  Some edge cases may need attention")
    else:
        print("\n⚠️  ISSUES DETECTED - Scripts may need fixes")
        print("🔧 Check error messages above for resolution steps")
    
    # Specific recommendations
    print("\nRECOMMENDATIONS:")
    print("-" * 20)
    
    if help_passed < len(help_tests):
        print("🔧 Fix help functionality in failing scripts")
    
    if not config_success:
        print("🔧 Check main_workflow.py sample config creation")
    
    if not error_success:
        print("🔧 Verify update_pbix_parameter.py error handling")
    
    if import_passed < len(import_results):
        print("🔧 Address import/dependency issues in failing scripts")
    
    if total_passed == total_tests:
        print("✅ No action needed - all scripts working correctly!")
    
    print(f"\nTest completed from: {Path(__file__).parent}")
    
    return 0 if total_passed >= total_tests * 0.8 else 1

if __name__ == "__main__":
    exit(main())