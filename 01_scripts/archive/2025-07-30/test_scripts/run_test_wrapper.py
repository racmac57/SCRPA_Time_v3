#!/usr/bin/env python3
import sys
import os
import subprocess
from pathlib import Path

# Add the current directory to the path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Change to the test directory
os.chdir(current_dir)

# Import and run the test script directly
try:
    import test_pbix_scripts
    exit_code = test_pbix_scripts.main()
    sys.exit(exit_code)
except Exception as e:
    print(f"Error running test: {e}")
    sys.exit(1)