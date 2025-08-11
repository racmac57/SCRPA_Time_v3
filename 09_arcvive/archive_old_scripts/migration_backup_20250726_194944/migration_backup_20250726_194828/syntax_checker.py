#!/usr/bin/env python3
import ast
import os
from pathlib import Path

def check_syntax(script_path):
    """Check if a Python script has valid syntax."""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Try to parse the AST
        ast.parse(source_code)
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"
    except Exception as e:
        return False, f"Read Error: {e}"

# Test key scripts
scripts_dir = Path(r'C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\scripts')

key_scripts = [
    "config.py",
    "update_pbix_parameter.py", 
    "main_workflow.py",
    "chart_export.py",
    "map_export.py",
    "cleanup_scrpa_scripts.py",
    "test_pbix_update.py",
    "demo_rollback_scenarios.py",
    "scrpa_production_system.py",
    "scrpa_final_system.py"
]

print("SYNTAX CHECK RESULTS")
print("=" * 50)

results = []
for script_name in key_scripts:
    script_path = scripts_dir / script_name
    if script_path.exists():
        is_valid, message = check_syntax(script_path)
        status = "✅ PASS" if is_valid else "❌ FAIL"
        results.append((script_name, is_valid, message))
        print(f"{status}: {script_name} - {message}")
    else:
        results.append((script_name, False, "File not found"))
        print(f"❌ FAIL: {script_name} - File not found")

print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)

passed = sum(1 for _, valid, _ in results if valid)
total = len(results)

print(f"Syntax Tests Passed: {passed}/{total}")
print(f"Success Rate: {(passed/total)*100:.1f}%")

if passed == total:
    print("\n🎉 ALL SCRIPTS HAVE VALID SYNTAX!")
    print("✅ Scripts are ready for import testing")
else:
    print(f"\n⚠️  {total-passed} scripts have syntax issues")
    failed = [(name, msg) for name, valid, msg in results if not valid]
    print("Failed scripts:")
    for name, msg in failed:
        print(f"  - {name}: {msg}")