#!/usr/bin/env python3
"""
Quick validation script to check if the imports work correctly.
Run this first to identify any import issues before running the full test suite.
"""

import sys
from pathlib import Path

print("=" * 60)
print("🔍 VALIDATING IMPORTS FOR CAD NOTES TESTS")
print("=" * 60)

# Check current directory
current_dir = Path(__file__).parent
print(f"📁 Current directory: {current_dir}")

# Check if 01_scripts directory exists
scripts_path = current_dir.parent.parent / "01_scripts"
print(f"📁 Scripts directory: {scripts_path}")
print(f"   Exists: {'✅' if scripts_path.exists() else '❌'}")

if scripts_path.exists():
    # List files in 01_scripts
    script_files = list(scripts_path.glob("*.py"))
    print(f"   Python files found: {len(script_files)}")
    for file in script_files:
        print(f"   - {file.name}")

# Add scripts path to Python path
sys.path.insert(0, str(scripts_path))
print(f"📂 Added to Python path: {scripts_path}")

# Try to import the required modules
print("\n🔄 Testing imports...")

try:
    print("   Importing pandas...")
    import pandas as pd
    print("   ✅ pandas imported successfully")
except ImportError as e:
    print(f"   ❌ pandas import failed: {e}")

try:
    print("   Importing enhanced_cadnotes_python...")
    from enhanced_cadnotes_python import EnhancedCADNotesProcessor
    print("   ✅ EnhancedCADNotesProcessor imported successfully")
    
    # Try to create an instance
    print("   Creating processor instance...")
    processor = EnhancedCADNotesProcessor()
    print("   ✅ Processor instance created successfully")
    
    # Check if key methods exist
    methods_to_check = ['process_cadnotes_dataframe', 'validate_against_examples', 'parse_single_cadnote']
    for method_name in methods_to_check:
        if hasattr(processor, method_name):
            print(f"   ✅ Method '{method_name}' found")
        else:
            print(f"   ❌ Method '{method_name}' NOT found")
            
except ImportError as e:
    print(f"   ❌ enhanced_cadnotes_python import failed: {e}")
    print("   Make sure the enhanced_cadnotes_python.py file exists in 01_scripts/")
except Exception as e:
    print(f"   ❌ Error creating processor: {e}")

print("\n" + "=" * 60)
print("📊 IMPORT VALIDATION SUMMARY")
print("=" * 60)

# Final validation
try:
    import pandas as pd
    from enhanced_cadnotes_python import EnhancedCADNotesProcessor
    processor = EnhancedCADNotesProcessor()
    
    print("✅ All imports successful - ready to run tests!")
    print("   You can now run: python run_tests.py")
    
except Exception as e:
    print(f"❌ Import validation failed: {e}")
    print("   Fix the import issues before running tests")
    
print("\n🏁 Validation complete!")