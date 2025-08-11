#!/usr/bin/env python3
"""
Simple wrapper to execute the move_migration_backups.py script
"""

import sys
import os
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Change to the correct directory
os.chdir(current_dir)

# Import and run the migration mover
try:
    from move_migration_backups import main
    result = main()
    print(f"\nScript execution completed with exit code: {result}")
    sys.exit(result)
except Exception as e:
    print(f"Error executing migration script: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)