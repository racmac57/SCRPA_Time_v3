#!/usr/bin/env python3
"""
Direct execution of PBIX test script without subprocess issues
"""
import sys
import os
from pathlib import Path
import tempfile
import json

# Set up paths
test_dir = Path(__file__).parent
scripts_dir = test_dir / "scripts"
print(f"Test directory: {test_dir}")
print(f"Scripts directory: {scripts_dir}")
print(f"Scripts directory exists: {scripts_dir.exists()}")

# Check if scripts exist
scripts_to_check = [
    "update_pbix_parameter.py",
    "main_workflow.py", 
    "cleanup_scrpa_scripts.py"
]

print("\nSCRIPT EXISTENCE CHECK:")
print("-" * 40)
for script in scripts_to_check:
    script_path = scripts_dir / script
    exists = script_path.exists()
    print(f"{script}: {'✅ EXISTS' if exists else '❌ NOT FOUND'}")
    if exists:
        try:
            # Try to read first few lines to check for syntax issues
            with open(script_path, 'r', encoding='utf-8') as f:
                first_lines = [f.readline() for _ in range(5)]
            print(f"  First line: {first_lines[0].strip()}")
        except Exception as e:
            print(f"  Error reading: {e}")

# Test 1: Try importing the scripts to check for syntax errors
print("\nIMPORT SYNTAX TEST:")
print("-" * 40)

for script in scripts_to_check:
    script_path = scripts_dir / script
    if script_path.exists():
        try:
            # Add scripts directory to path temporarily
            sys.path.insert(0, str(scripts_dir))
            
            # Try to compile the script
            with open(script_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            compiled = compile(source_code, str(script_path), 'exec')
            print(f"{script}: ✅ SYNTAX OK")
            
        except SyntaxError as e:
            print(f"{script}: ❌ SYNTAX ERROR - Line {e.lineno}: {e.msg}")
        except Exception as e:
            print(f"{script}: ❌ COMPILE ERROR - {str(e)}")
        finally:
            # Remove from path
            if str(scripts_dir) in sys.path:
                sys.path.remove(str(scripts_dir))

# Test 2: Check for required dependencies
print("\nDEPENDENCY CHECK:")
print("-" * 40)

required_modules = ['argparse', 'json', 'pathlib', 'shutil', 'tempfile', 'zipfile']
for module in required_modules:
    try:
        __import__(module)
        print(f"{module}: ✅ AVAILABLE")
    except ImportError:
        print(f"{module}: ❌ MISSING")

# Test 3: Check if we can create temp files (for config test)
print("\nTEMP FILE TEST:")
print("-" * 40)
try:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        temp_path = tmp.name
        tmp.write('{"test": "value"}')
    
    # Try to read it back
    with open(temp_path, 'r') as f:
        data = json.load(f)
    
    os.unlink(temp_path)
    print("Temp file operations: ✅ WORKING")
except Exception as e:
    print(f"Temp file operations: ❌ ERROR - {e}")

# Test 4: Check working directory and permissions
print("\nFILE SYSTEM TEST:")
print("-" * 40)
print(f"Current working directory: {os.getcwd()}")
print(f"Test directory writable: {'✅ YES' if os.access(test_dir, os.W_OK) else '❌ NO'}")
print(f"Scripts directory readable: {'✅ YES' if os.access(scripts_dir, os.R_OK) else '❌ NO'}")

# Test 5: Manual help test simulation
print("\nMANUAL HELP TEST SIMULATION:")
print("-" * 40)

help_scripts = ["update_pbix_parameter.py", "main_workflow.py"]
for script in help_scripts:
    script_path = scripts_dir / script
    if script_path.exists():
        try:
            # Read the script and look for argparse usage
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            has_argparse = 'argparse' in content or 'ArgumentParser' in content
            has_help = '--help' in content or 'add_help' in content
            has_main = 'if __name__' in content and '__main__' in content
            
            print(f"{script}:")
            print(f"  Has argparse: {'✅' if has_argparse else '❌'}")
            print(f"  Has help: {'✅' if has_help else '❌'}")
            print(f"  Has main guard: {'✅' if has_main else '❌'}")
            
        except Exception as e:
            print(f"{script}: ❌ ERROR reading - {e}")

print("\n" + "=" * 50)
print("DIRECT TEST EXECUTION COMPLETE")
print("=" * 50)
print("This test checked script existence, syntax, dependencies,")
print("and file system operations without subprocess calls.")
print("Review the results above for any issues that need fixing.")