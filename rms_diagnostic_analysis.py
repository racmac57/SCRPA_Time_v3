#!/usr/bin/env python3
"""
RMS Data Structure Diagnostic Analysis
Comprehensive diagnosis of RMS data structure and processing issues
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob

def find_all_rms_files():
    """Find all RMS files in the project"""
    print("=== FINDING ALL RMS FILES ===")
    
    base_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
    
    rms_files = {
        'exports': [],
        'powerbi': [],
        'scripts': [],
        'root': []
    }
    
    # Check exports directory
    exports_dir = base_dir / "05_Exports"
    if exports_dir.exists():
        rms_files['exports'] = list(exports_dir.glob("*RMS*.xlsx")) + list(exports_dir.glob("*rms*.csv"))
    
    # Check powerbi directory  
    powerbi_dir = base_dir / "04_powerbi"
    if powerbi_dir.exists():
        rms_files['powerbi'] = list(powerbi_dir.glob("*rms*.csv"))
    
    # Check scripts directory
    scripts_dir = base_dir / "01_scripts"
    if scripts_dir.exists():
        rms_files['scripts'] = list(scripts_dir.glob("*rms*.csv"))
    
    # Check root directory
    rms_files['root'] = list(base_dir.glob("*rms*.csv"))
    
    for location, files in rms_files.items():
        if files:
            print(f"\n{location.upper()} directory:")
            for f in files:
                stat = f.stat()
                print(f"  {f.name} ({stat.st_size:,} bytes, {pd.Timestamp.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')})")
    
    return rms_files

def analyze_raw_rms_export():
    """Analyze the raw RMS export file"""
    print("\n=== ANALYZING RAW RMS EXPORT ===")
    
    # Find the most recent RMS export
    exports_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\05_Exports")
    rms_exports = list(exports_dir.glob("*SCRPA_RMS*.xlsx"))
    
    if not rms_exports:
        print("ERROR: No RMS export files found in 05_Exports/")
        return None
    
    # Use most recent file
    latest_export = max(rms_exports, key=lambda p: p.stat().st_mtime)
    print(f"Analyzing: {latest_export.name}")
    
    try:
        # Load raw export
        raw_df = pd.read_excel(latest_export)
        
        print(f"Raw Export Stats:")
        print(f"  Total rows: {len(raw_df)}")
        print(f"  Total columns: {len(raw_df.columns)}")
        print(f"  File size: {latest_export.stat().st_size:,} bytes")
        
        print(f"\n=== RAW EXPORT COLUMN INVENTORY ===")
        for i, col in enumerate(raw_df.columns, 1):
            non_null_count = raw_df[col].notna().sum()
            null_count = raw_df[col].isna().sum()
            print(f"{i:2d}. '{col}' ({non_null_count} non-null, {null_count} null)")
        
        print(f"\n=== CRITICAL COLUMN ANALYSIS ===")
        
        # Check for location columns
        location_cols = [col for col in raw_df.columns if any(keyword in col.lower() for keyword in ['address', 'location'])]
        print(f"Location columns found: {location_cols}")
        for col in location_cols:
            sample_values = raw_df[col].dropna().head(3).tolist()
            print(f"  {col} samples: {sample_values}")
        
        # Check for time columns
        time_cols = [col for col in raw_df.columns if any(keyword in col.lower() for keyword in ['time', 'date'])]
        print(f"\nTime columns found: {time_cols}")
        for col in time_cols:
            sample_values = raw_df[col].dropna().head(3).tolist()
            print(f"  {col} samples: {sample_values}")
        
        # Check for incident type columns
        incident_cols = [col for col in raw_df.columns if any(keyword in col.lower() for keyword in ['incident', 'type', 'classification'])]
        print(f"\nIncident columns found: {incident_cols}")
        for col in incident_cols:
            sample_values = raw_df[col].dropna().head(3).tolist()
            print(f"  {col} samples: {sample_values}")
        
        # Check for grid/zone/post columns
        location_meta_cols = [col for col in raw_df.columns if any(keyword in col.lower() for keyword in ['grid', 'zone', 'post'])]
        print(f"\nLocation metadata columns found: {location_meta_cols}")
        for col in location_meta_cols:
            sample_values = raw_df[col].dropna().head(3).tolist()
            print(f"  {col} samples: {sample_values}")
        
        print(f"\n=== RAW DATA SAMPLE ===")
        print("First 2 records:")
        print(raw_df.head(2).to_string())
        
        return raw_df, latest_export
        
    except Exception as e:
        print(f"ERROR analyzing raw export: {e}")
        return None, None

def analyze_processed_rms_files():
    """Analyze processed RMS files to identify data loss"""
    print("\n=== ANALYZING PROCESSED RMS FILES ===")
    
    powerbi_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi")
    processed_files = list(powerbi_dir.glob("*rms_data_standardized.csv"))
    
    if not processed_files:
        print("ERROR: No processed RMS files found")
        return []
    
    results = []
    
    for file_path in processed_files[-2:]:  # Analyze last 2 files
        print(f"\nAnalyzing: {file_path.name}")
        
        try:
            processed_df = pd.read_csv(file_path)
            
            print(f"  Records: {len(processed_df)}")
            print(f"  Columns: {len(processed_df.columns)}")
            
            # Check critical columns for null values
            critical_columns = ['location', 'incident_time', 'grid', 'post', 'incident_type']
            
            print(f"  Critical column analysis:")
            for col in critical_columns:
                if col in processed_df.columns:
                    non_null = processed_df[col].notna().sum()
                    null_count = processed_df[col].isna().sum()
                    print(f"    {col}: {non_null} non-null, {null_count} null")
                    
                    # Show sample non-null values if any
                    if non_null > 0:
                        samples = processed_df[col].dropna().head(2).tolist()
                        print(f"      Samples: {samples}")
                else:
                    print(f"    {col}: COLUMN MISSING")
            
            results.append({
                'file': file_path.name,
                'records': len(processed_df),
                'columns': processed_df.columns.tolist()
            })
            
        except Exception as e:
            print(f"  ERROR: {e}")
    
    return results

def compare_raw_vs_processed(raw_df, processed_results):
    """Compare raw vs processed data to identify data loss points"""
    print("\n=== RAW VS PROCESSED COMPARISON ===")
    
    if raw_df is None or not processed_results:
        print("ERROR: Missing data for comparison")
        return
    
    print(f"Raw export records: {len(raw_df)}")
    
    for result in processed_results:
        print(f"Processed file '{result['file']}': {result['records']} records")
        record_loss = len(raw_df) - result['records']
        if record_loss > 0:
            print(f"  ⚠️  RECORD LOSS: {record_loss} records lost ({record_loss/len(raw_df)*100:.1f}%)")
        else:
            print(f"  ✓ No record loss")

def identify_column_mapping_issues(raw_df):
    """Identify specific column mapping issues"""
    print("\n=== COLUMN MAPPING ISSUES ANALYSIS ===")
    
    if raw_df is None:
        print("ERROR: No raw data available")
        return
    
    # Expected mappings based on processing pipeline
    expected_mappings = {
        'case_number': ['Case Number', 'case_number', 'Case_Number'],
        'location': ['FullAddress', 'Full Address', 'location', 'Address'],
        'incident_type': ['Incident Type_1', 'Incident_Type_1', 'incident_type', 'Incident Type'],
        'incident_time': ['Incident Time', 'incident_time', 'Incident_Time'],
        'incident_date': ['Incident Date', 'incident_date', 'Incident_Date'],
        'grid': ['Grid', 'grid'],
        'post': ['Zone', 'Post', 'zone', 'post'],
        'nibrs_classification': ['NIBRS Classification', 'nibrs_classification', 'NIBRS_Classification']
    }
    
    print("Checking expected column mappings:")
    
    for target_col, possible_sources in expected_mappings.items():
        found_sources = [col for col in possible_sources if col in raw_df.columns]
        
        if found_sources:
            source_col = found_sources[0]
            non_null_count = raw_df[source_col].notna().sum()
            print(f"✓ {target_col} ← '{source_col}' ({non_null_count}/{len(raw_df)} non-null)")
            
            # Show data quality
            if non_null_count > 0:
                sample = raw_df[source_col].dropna().iloc[0]
                print(f"    Sample: {sample}")
            else:
                print(f"    ⚠️  ALL VALUES NULL")
        else:
            print(f"✗ {target_col} ← NO MATCHING COLUMN FOUND")
            print(f"    Looking for: {possible_sources}")
            
            # Suggest similar columns
            similar = [col for col in raw_df.columns if any(part.lower() in col.lower() for part in target_col.split('_'))]
            if similar:
                print(f"    Similar columns: {similar}")

def diagnose_data_processing_pipeline():
    """Diagnose the entire data processing pipeline"""
    print("\n=== PIPELINE DIAGNOSIS SUMMARY ===")
    
    # Check if processing scripts exist
    script_files = [
        "scrpa_production_pipeline.py",
        "SCRPA_Time_v3_Production_Pipeline.py", 
        "production_pipeline_validated.py"
    ]
    
    base_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
    
    print("Processing scripts found:")
    for script in script_files:
        script_path = base_dir / script
        if script_path.exists():
            print(f"✓ {script}")
        else:
            print(f"✗ {script}")

def main():
    """Main diagnostic function"""
    print("=== RMS DATA STRUCTURE DIAGNOSTIC ANALYSIS ===")
    print("Identifying root causes of data loss and null values\n")
    
    # 1. Find all RMS files
    rms_files = find_all_rms_files()
    
    # 2. Analyze raw RMS export
    raw_df, raw_file = analyze_raw_rms_export()
    
    # 3. Analyze processed RMS files
    processed_results = analyze_processed_rms_files()
    
    # 4. Compare raw vs processed
    compare_raw_vs_processed(raw_df, processed_results)
    
    # 5. Identify column mapping issues
    identify_column_mapping_issues(raw_df)
    
    # 6. Diagnose pipeline
    diagnose_data_processing_pipeline()
    
    print("\n=== DIAGNOSTIC COMPLETE ===")
    print("Root causes identified. Ready for column mapping fixes.")

if __name__ == "__main__":
    main()