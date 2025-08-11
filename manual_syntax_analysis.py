#!/usr/bin/env python3
"""
Manual Syntax and Import Analysis Script
=======================================
This script manually performs the analysis since the original script couldn't be executed.
"""

import ast
import os
import sys
from pathlib import Path
import re
from datetime import datetime

def analyze_file(file_path):
    """Analyze a single Python file for syntax and imports."""
    result = {
        'file': file_path.name,
        'path': str(file_path),
        'syntax_valid': False,
        'syntax_error': None,
        'has_arcpy': False,
        'imports': [],
        'file_size': 0
    }
    
    try:
        # Get file size
        result['file_size'] = file_path.stat().st_size
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Check syntax
        try:
            ast.parse(content)
            result['syntax_valid'] = True
        except SyntaxError as e:
            result['syntax_error'] = f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            result['syntax_error'] = f"Parse error: {e}"
        
        # Extract imports
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        result['imports'].append(f"import {module_name}")
                        if 'arcpy' in module_name.lower():
                            result['has_arcpy'] = True
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result['imports'].append(f"from {node.module} import ...")
                        if 'arcpy' in node.module.lower():
                            result['has_arcpy'] = True
        except:
            # Fallback to regex search
            import_lines = re.findall(r'^(import\s+\S+|from\s+\S+\s+import)', content, re.MULTILINE)
            result['imports'] = import_lines
        
        # Check for arcpy references in content
        if not result['has_arcpy']:
            if re.search(r'\barcpy\b', content, re.IGNORECASE):
                result['has_arcpy'] = True
    
    except Exception as e:
        result['syntax_error'] = f"File read error: {e}"
    
    return result

def main():
    scripts_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts")
    
    # Get all Python files, excluding backup files
    all_py_files = list(scripts_dir.glob("*.py"))
    
    # Filter out backup files
    core_files = []
    backup_files = []
    
    for py_file in all_py_files:
        if ("migration_backup_" in py_file.name or 
            py_file.name.startswith("scripts__") or
            "__" in py_file.name):
            backup_files.append(py_file)
        else:
            core_files.append(py_file)
    
    print("PYTHON SYNTAX AND IMPORT ANALYSIS REPORT")
    print("=" * 60)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directory: {scripts_dir}")
    print(f"Total Python files found: {len(all_py_files)}")
    print(f"Core files (non-backup): {len(core_files)}")
    print(f"Backup files: {len(backup_files)}")
    print()
    
    # Analyze core files
    syntax_valid = []
    syntax_errors = []
    arcpy_users = []
    
    print("ANALYZING CORE FILES:")
    print("-" * 40)
    
    for py_file in sorted(core_files):
        print(f"Checking: {py_file.name}")
        result = analyze_file(py_file)
        
        if result['syntax_valid']:
            syntax_valid.append(result)
            print(f"  ✅ Valid syntax")
        else:
            syntax_errors.append(result)
            print(f"  ❌ SYNTAX ERROR: {result['syntax_error']}")
        
        if result['has_arcpy']:
            arcpy_users.append(result)
            print(f"  🗺️  USES ARCPY")
        
        if result['imports']:
            print(f"  📦 Imports: {len(result['imports'])} modules")
        
        print(f"  📄 Size: {result['file_size']} bytes")
        print()
    
    # Generate summary
    print("\nSUMMARY")
    print("-" * 20)
    print(f"Core Files Analyzed: {len(core_files)}")
    print(f"Syntax Valid: {len(syntax_valid)}")
    print(f"Syntax Errors: {len(syntax_errors)}")
    print(f"ArcPy Dependencies: {len(arcpy_users)}")
    if core_files:
        success_rate = len(syntax_valid) / len(core_files) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    # Detailed error report
    if syntax_errors:
        print(f"\nSYNTAX ERRORS ({len(syntax_errors)} files)")
        print("-" * 30)
        for result in syntax_errors:
            print(f"❌ {result['file']}")
            print(f"   Error: {result['syntax_error']}")
            print(f"   Size: {result['file_size']} bytes")
            print()
    
    # ArcPy dependencies
    if arcpy_users:
        print(f"ARCPY DEPENDENCIES ({len(arcpy_users)} files)")
        print("-" * 30)
        for result in arcpy_users:
            print(f"🗺️  {result['file']}")
            # Show relevant imports
            arcpy_imports = [imp for imp in result['imports'] if 'arcpy' in imp.lower()]
            if arcpy_imports:
                for imp in arcpy_imports[:3]:  # Show first 3
                    print(f"   {imp}")
                if len(arcpy_imports) > 3:
                    print(f"   ... and {len(arcpy_imports) - 3} more")
            print()
    
    # Clean files
    clean_files = [r for r in syntax_valid if not r['has_arcpy']]
    if clean_files:
        print(f"CLEAN FILES (No ArcPy, Valid Syntax): {len(clean_files)}")
        print("-" * 30)
        for result in clean_files:
            print(f"✅ {result['file']} ({len(result['imports'])} imports)")
    
    print(f"\nReport completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()