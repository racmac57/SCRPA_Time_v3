#!/usr/bin/env python3
"""
DEBUG: RMS Column Structure Analysis
Print actual column names in RMS raw data to identify mapping issues
"""

import pandas as pd
import glob
from pathlib import Path

def debug_rms_columns():
    """Debug actual RMS column structure"""
    print("=== RMS COLUMN STRUCTURE DEBUG ===")
    
    # Find the most recent RMS file
    powerbi_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi")
    rms_files = list(powerbi_dir.glob("*rms_data_standardized.csv"))
    
    if not rms_files:
        print("ERROR: No RMS files found!")
        return
    
    # Use most recent file
    rms_file = max(rms_files, key=lambda p: p.stat().st_mtime)
    print(f"Analyzing RMS file: {rms_file}")
    
    try:
        # Load RMS data
        rms_df = pd.read_csv(rms_file)
        
        print(f"\nTotal RMS records: {len(rms_df)}")
        print(f"Total columns: {len(rms_df.columns)}")
        
        print("\n=== ACTUAL COLUMN NAMES ===")
        for i, col in enumerate(rms_df.columns, 1):
            print(f"{i:2d}. '{col}'")
        
        print("\n=== LOOKING FOR LOCATION COLUMNS ===")
        location_candidates = [col for col in rms_df.columns if 'address' in col.lower() or 'location' in col.lower()]
        print("Location-related columns:")
        for col in location_candidates:
            print(f"  - '{col}'")
            # Show sample values
            sample_values = rms_df[col].dropna().head(3).tolist()
            print(f"    Sample values: {sample_values}")
        
        print("\n=== LOOKING FOR DATE/TIME COLUMNS ===")
        datetime_candidates = [col for col in rms_df.columns if any(keyword in col.lower() for keyword in ['date', 'time', 'occurred', 'reported'])]
        print("Date/Time-related columns:")
        for col in datetime_candidates:
            print(f"  - '{col}'")
            # Show sample values
            sample_values = rms_df[col].dropna().head(3).tolist()
            print(f"    Sample values: {sample_values}")
        
        print("\n=== LOOKING FOR INCIDENT TYPE COLUMNS ===")
        incident_candidates = [col for col in rms_df.columns if any(keyword in col.lower() for keyword in ['incident', 'type', 'classification', 'nibrs'])]
        print("Incident-related columns:")
        for col in incident_candidates:
            print(f"  - '{col}'")
            # Show sample values
            sample_values = rms_df[col].dropna().head(3).tolist()
            print(f"    Sample values: {sample_values}")
        
        print("\n=== SAMPLE DATA PREVIEW ===")
        print(rms_df.head(2).to_string())
        
        # Check for expected columns that might be missing
        print("\n=== COLUMN MAPPING VERIFICATION ===")
        expected_columns = ['case_number', 'incident_type', 'nibrs_classification', 'location', 'FullAddress']
        for expected in expected_columns:
            if expected in rms_df.columns:
                print(f"✓ Found: '{expected}'")
            else:
                print(f"✗ Missing: '{expected}'")
                # Look for similar columns
                similar = [col for col in rms_df.columns if expected.lower() in col.lower() or col.lower() in expected.lower()]
                if similar:
                    print(f"  Similar: {similar}")
        
    except Exception as e:
        print(f"ERROR reading RMS file: {e}")

if __name__ == "__main__":
    debug_rms_columns()