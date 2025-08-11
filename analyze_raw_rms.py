#!/usr/bin/env python3
"""
Analyze raw RMS Excel data to find source columns
"""

import pandas as pd
from pathlib import Path

def analyze_raw_rms():
    """Analyze raw RMS Excel data"""
    print("=== RAW RMS EXCEL ANALYSIS ===")
    
    rms_excel = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\05_Exports\2025_08_01_19_38_12_SCRPA_RMS.xlsx")
    
    if not rms_excel.exists():
        print(f"ERROR: Raw RMS Excel not found: {rms_excel}")
        return
    
    try:
        # Read the Excel file
        df = pd.read_excel(rms_excel)
        
        print(f"Raw RMS Excel found: {rms_excel}")
        print(f"Total rows: {len(df)}")
        print(f"Total columns: {len(df.columns)}")
        
        print("\n=== RAW RMS COLUMNS ===")
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2d}. '{col}'")
        
        print("\n=== LOOKING FOR ADDRESS/LOCATION COLUMNS ===")
        address_candidates = [col for col in df.columns if any(keyword in col.lower() for keyword in ['address', 'location', 'place', 'street'])]
        for col in address_candidates:
            print(f"  - '{col}'")
            sample_values = df[col].dropna().head(3).tolist()
            print(f"    Sample: {sample_values}")
        
        print("\n=== LOOKING FOR TIME COLUMNS ===")
        time_candidates = [col for col in df.columns if any(keyword in col.lower() for keyword in ['time', 'date', 'occurred', 'reported'])]
        for col in time_candidates:
            print(f"  - '{col}'")
            sample_values = df[col].dropna().head(3).tolist()
            print(f"    Sample: {sample_values}")
        
        print("\n=== SAMPLE RAW DATA ===")
        print(df.head(2).to_string())
        
    except Exception as e:
        print(f"ERROR reading raw RMS Excel: {e}")

if __name__ == "__main__":
    analyze_raw_rms()