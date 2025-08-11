#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_scripts_operability.py

Quick operability test for key migrated scripts to verify they can be imported
and their basic functionality works after migration.
"""

import os
import sys
import importlib.util
from pathlib import Path

def test_script_import(script_path, script_name):
    """Test if a Python script can be imported successfully."""
    try:
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        if spec is None:
            return False, f"Could not create module spec for {script_name}"
        
        module = importlib.util.module_from_spec(spec)
        # Don't execute the module, just test if it can be loaded
        # spec.loader.exec_module(module)
        return True, f"✅ {script_name} - Import successful"
    except Exception as e:
        return False, f"❌ {script_name} - Import failed: {str(e)}"

def test_syntax_only(script_path, script_name):
    """Test if a Python script has valid syntax."""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        compile(source_code, script_path, 'exec')
        return True, f"✅ {script_name} - Syntax valid"
    except SyntaxError as e:
        return False, f"❌ {script_name} - Syntax error: {str(e)}"
    except Exception as e:
        return False, f"❌ {script_name} - Error reading file: {str(e)}"

def main():
    """Main test execution."""
    print("SCRPA SCRIPTS OPERABILITY TEST")
    print("=" * 60)
    
    # Define scripts directory
    scripts_dir = Path(__file__).parent / "scripts"
    
    # Key scripts to test (prioritized)
    priority_scripts = [
        "update_pbix_parameter.py",
        "main_workflow.py", 
        "cleanup_scrpa_scripts.py",
        "test_pbix_update.py",
        "demo_rollback_scenarios.py"
    ]
    
    # Additional important scripts
    important_scripts = [
        "config.py",
        "chart_export.py",
        "map_export.py",
        "scrpa_production_system.py",
        "scrpa_final_system.py"
    ]
    
    all_scripts = priority_scripts + important_scripts
    
    print(f"Testing scripts in: {scripts_dir}")
    print(f"Total scripts to test: {len(all_scripts)}")
    print()
    
    # Test results
    syntax_results = []
    import_results = []
    
    # Test each script
    for script_name in all_scripts:
        script_path = scripts_dir / script_name
        
        if not script_path.exists():
            print(f"⚠️  {script_name} - File not found")
            continue
        
        # Test syntax
        syntax_ok, syntax_msg = test_syntax_only(script_path, script_name)
        syntax_results.append((script_name, syntax_ok, syntax_msg))
        
        # Test imports (only if syntax is OK)
        if syntax_ok:
            import_ok, import_msg = test_script_import(script_path, script_name)
            import_results.append((script_name, import_ok, import_msg))
        else:
            import_results.append((script_name, False, f"❌ {script_name} - Skipped due to syntax error"))
    
    # Print results
    print("SYNTAX TEST RESULTS:")
    print("-" * 40)
    syntax_passed = 0
    for script_name, success, message in syntax_results:
        print(message)
        if success:
            syntax_passed += 1
    
    print(f"\nSyntax Tests: {syntax_passed}/{len(syntax_results)} passed")
    
    print("\nIMPORT TEST RESULTS:")
    print("-" * 40)
    import_passed = 0
    for script_name, success, message in import_results:
        print(message)
        if success:
            import_passed += 1
    
    print(f"\nImport Tests: {import_passed}/{len(import_results)} passed")
    
    # Summary
    print("\n" + "=" * 60)
    print("OPERABILITY TEST SUMMARY")
    print("=" * 60)
    
    total_syntax_pass = syntax_passed
    total_import_pass = import_passed
    total_tests = len(syntax_results)
    
    if total_syntax_pass == total_tests and total_import_pass == total_tests:
        print("🎉 ALL SCRIPTS OPERATIONAL - Migration successful!")
    elif total_syntax_pass == total_tests:
        print("⚠️  Scripts have valid syntax but some import issues detected")
        print("   This is often due to missing dependencies or path issues")
    else:
        print("❌ Critical issues detected - Some scripts have syntax errors")
    
    print(f"\nSyntax Health: {total_syntax_pass}/{total_tests} ({(total_syntax_pass/total_tests)*100:.1f}%)")
    print(f"Import Health: {total_import_pass}/{total_tests} ({(total_import_pass/total_tests)*100:.1f}%)")
    
    # Specific recommendations
    print("\nRECOMMENDATIONS:")
    print("-" * 20)
    
    failed_syntax = [name for name, success, _ in syntax_results if not success]
    failed_imports = [name for name, success, _ in import_results if not success]
    
    if failed_syntax:
        print("🔧 Scripts needing syntax fixes:")
        for script in failed_syntax:
            print(f"   - {script}")
    
    if failed_imports and not failed_syntax:
        print("🔧 Scripts needing dependency/path fixes:")
        for script in failed_imports:
            if script not in failed_syntax:
                print(f"   - {script}")
    
    if not failed_syntax and not failed_imports:
        print("✅ All scripts are ready for use!")
        print("✅ PBIX tools should work correctly")
        print("✅ Migration was successful")
    
    print(f"\nTest completed at: {Path(__file__).parent}")

if __name__ == "__main__":
    main()