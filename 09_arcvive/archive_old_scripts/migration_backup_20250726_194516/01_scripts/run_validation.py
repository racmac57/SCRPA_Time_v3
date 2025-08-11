#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    # Import and run the manual validation
    import manual_validation
    exit_code = manual_validation.main()
    print(f"\nValidation completed with exit code: {exit_code}")
    
except Exception as e:
    print(f"Error running validation: {e}")
    import traceback
    traceback.print_exc()
    exit_code = 1

sys.exit(exit_code)