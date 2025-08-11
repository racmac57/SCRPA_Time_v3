#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_syntax.py

Simple script to validate Python syntax of the PBIX configuration scripts.
"""

import ast
import sys
from pathlib import Path

def validate_python_syntax(file_path):
    """Validate Python syntax of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Try to parse the AST
        ast.parse(source_code)
        return True, None
        
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    except UnicodeDecodeError as e:
        return False, f"UnicodeDecodeError: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Validate syntax of all Python files."""
    print("=" * 60)
    print("PYTHON SYNTAX VALIDATION")
    print("=" * 60)
    
    current_dir = Path(__file__).parent
    
    # Files to validate
    files_to_check = [
        "update_pbix_parameter.py",
        "configure_scrpa_pbix.py",
        "pbix_automation_examples.py"
    ]
    
    all_valid = True
    
    for filename in files_to_check:
        file_path = current_dir / filename
        
        if not file_path.exists():
            print(f"WARNING: {filename} not found")
            continue
        
        print(f"\\nValidating {filename}...")
        
        is_valid, error_message = validate_python_syntax(file_path)
        
        if is_valid:
            print(f"SUCCESS: {filename} - Syntax is valid")
        else:
            print(f"ERROR: {filename} - {error_message}")
            all_valid = False
    
    print("\\n" + "=" * 60)
    if all_valid:
        print("SUCCESS: All Python files have valid syntax!")
    else:
        print("ERROR: Some files have syntax errors")
    print("=" * 60)
    
    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())