#!/usr/bin/env python3
"""
Check CAD reference file and RMS processing issues
"""

import pandas as pd
from pathlib import Path

def check_cad_reference():
    """Check CAD reference file structure"""
    print("=== CAD REFERENCE FILE ANALYSIS ===")
    
    ref_file = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\CallType_Categories.xlsx")
    
    if not ref_file.exists():
        print(f"ERROR: Reference file not found: {ref_file}")
        return
    
    try:
        # Read the Excel file
        df = pd.read_excel(ref_file)
        
        print(f"Reference file found: {ref_file}")
        print(f"Total rows: {len(df)}")
        print(f"Total columns: {len(df.columns)}")
        
        print("\n=== REFERENCE FILE COLUMNS ===")
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2d}. '{col}'")
        
        print("\n=== SAMPLE REFERENCE DATA ===")
        print(df.head().to_string())
        
        # Look for key mapping columns
        print("\n=== KEY MAPPING COLUMNS ===")
        key_columns = ['Incident', 'incident', 'CallType', 'Category', 'category_type', 'response_type']
        for col in key_columns:
            if col in df.columns:
                print(f"✓ Found: '{col}'")
                # Show unique values
                unique_vals = df[col].dropna().unique()[:5]
                print(f"  Sample values: {list(unique_vals)}")
            
    except Exception as e:
        print(f"ERROR reading reference file: {e}")

def check_raw_rms_data():
    """Check raw RMS data before processing"""
    print("\n=== RAW RMS DATA ANALYSIS ===")
    
    # Look for raw RMS files
    base_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
    
    # Check different possible locations
    possible_dirs = [
        base_dir / "04_powerbi",
        base_dir,
        base_dir / "01_scripts"
    ]
    
    for check_dir in possible_dirs:
        if check_dir.exists():
            rms_files = list(check_dir.glob("*rms*.csv"))
            if rms_files:
                print(f"Found RMS files in {check_dir}:")
                for f in rms_files:
                    print(f"  - {f.name}")
    
    # Also check if there are any Excel files that might be the raw source
    excel_files = list(base_dir.glob("**/*.xlsx"))
    rms_excel = [f for f in excel_files if 'rms' in f.name.lower()]
    if rms_excel:
        print(f"\nFound RMS Excel files:")
        for f in rms_excel:
            print(f"  - {f}")

if __name__ == "__main__":
    check_cad_reference()
    check_raw_rms_data()