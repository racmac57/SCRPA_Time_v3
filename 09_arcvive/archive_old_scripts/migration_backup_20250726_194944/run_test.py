#!/usr/bin/env python3
import os
import sys
import subprocess

# Change to the correct directory
os.chdir(r'C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2')

# Execute the test script
try:
    result = subprocess.run([sys.executable, 'test_scripts_operability.py'], 
                          capture_output=True, text=True, timeout=300)
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    print(f"\nReturn code: {result.returncode}")
except Exception as e:
    print(f"Error executing test: {e}")