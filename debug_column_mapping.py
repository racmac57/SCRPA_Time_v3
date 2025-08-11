#!/usr/bin/env python3
"""
DEBUG COLUMN MAPPING ISSUE
The functions work but column mapping is failing
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add scripts path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '01_scripts'))

def debug_column_mapping():
    """Debug why column mapping is failing"""
    print("="*80)
    print("DEBUGGING COLUMN MAPPING ISSUE")
    print("="*80)
    
    try:
        # Import pipeline
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "SCRPA_Time_v3_Production_Pipeline", 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '01_scripts', 'SCRPA_Time_v3_Production_Pipeline.py')
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        SCRPAProductionPipeline = module.SCRPAProductionPipeline
        
        pipeline = SCRPAProductionPipeline()
        
        # Load actual data files
        input_dir = Path(pipeline.config['input_dir'])
        cad_files = list(input_dir.glob("*cad_data_standardized.csv"))
        rms_files = list(input_dir.glob("*rms_data_standardized.csv"))
        
        cad_path = max(cad_files, key=lambda p: p.stat().st_mtime)
        rms_path = max(rms_files, key=lambda p: p.stat().st_mtime)
        
        # Load raw data
        cad_df_raw = pd.read_csv(cad_path)
        rms_df_raw = pd.read_csv(rms_path)
        
        print("RAW CAD COLUMNS:")
        for i, col in enumerate(cad_df_raw.columns):
            print(f"  {i+1:2d}. {repr(col)}")
        
        print("\nRAW RMS COLUMNS:")
        for i, col in enumerate(rms_df_raw.columns):
            print(f"  {i+1:2d}. {repr(col)}")
        
        # Check column mappings
        print("\n" + "="*60)
        print("CHECKING COLUMN MAPPINGS")
        print("="*60)
        
        cad_mapping = pipeline.get_cad_column_mapping()
        rms_mapping = pipeline.get_rms_column_mapping()
        
        print("CAD COLUMN MAPPING:")
        for original, mapped in cad_mapping.items():
            exists = original in cad_df_raw.columns
            print(f"  {repr(original)} -> {repr(mapped)} [{'EXISTS' if exists else 'MISSING'}]")
        
        print("\nRMS COLUMN MAPPING:")
        for original, mapped in rms_mapping.items():
            exists = original in rms_df_raw.columns
            print(f"  {repr(original)} -> {repr(mapped)} [{'EXISTS' if exists else 'MISSING'}]")
        
        # Test actual mapping
        print("\n" + "="*60)
        print("TESTING ACTUAL MAPPING LOGIC")
        print("="*60)
        
        # CAD mapping test
        existing_cad_mapping = {k: v for k, v in cad_mapping.items() if k in cad_df_raw.columns}
        print(f"CAD existing mapping: {existing_cad_mapping}")
        
        cad_test = cad_df_raw.copy()
        cad_test = cad_test.rename(columns=existing_cad_mapping)
        print(f"CAD columns after mapping: {list(cad_test.columns)}")
        
        # RMS mapping test
        existing_rms_mapping = {k: v for k, v in rms_mapping.items() if k in rms_df_raw.columns}
        print(f"RMS existing mapping: {existing_rms_mapping}")
        
        rms_test = rms_df_raw.copy()
        rms_test = rms_test.rename(columns=existing_rms_mapping)
        print(f"RMS columns after mapping: {list(rms_test.columns)}")
        
        # Look for critical columns
        print("\n" + "="*60)
        print("SEARCHING FOR CRITICAL COLUMNS")
        print("="*60)
        
        # Look for how_reported equivalents
        how_reported_candidates = [col for col in cad_df_raw.columns if 'report' in col.lower()]
        print(f"How reported candidates: {how_reported_candidates}")
        
        # Look for CAD notes equivalents
        notes_candidates = [col for col in cad_df_raw.columns if 'note' in col.lower() or 'cad' in col.lower()]
        print(f"CAD notes candidates: {notes_candidates}")
        
        # Look for RMS time columns
        time_candidates = [col for col in rms_df_raw.columns if 'time' in col.lower()]
        print(f"RMS time candidates: {time_candidates}")
        
        # Look for RMS date columns
        date_candidates = [col for col in rms_df_raw.columns if 'date' in col.lower()]
        print(f"RMS date candidates: {date_candidates}")
        
        print("\n" + "="*80)
        print("COLUMN MAPPING DEBUG COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"COLUMN MAPPING DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_column_mapping()