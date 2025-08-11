#!/usr/bin/env python3
"""
DEBUG ACTUAL PIPELINE EXECUTION
Find where the implementation is failing in the real pipeline
"""

import sys
import os
import pandas as pd
import logging
from pathlib import Path

# Setup debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - PIPELINE_DEBUG - %(message)s')
logger = logging.getLogger('pipeline_debug')

# Add scripts path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '01_scripts'))

def debug_actual_pipeline_execution():
    """Debug the actual pipeline execution with real data"""
    print("="*80)
    print("DEBUGGING ACTUAL PIPELINE EXECUTION")
    print("="*80)
    
    try:
        # Import with full path
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "SCRPA_Time_v3_Production_Pipeline", 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '01_scripts', 'SCRPA_Time_v3_Production_Pipeline.py')
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        SCRPAProductionPipeline = module.SCRPAProductionPipeline
        
        # Initialize pipeline
        pipeline = SCRPAProductionPipeline()
        print("Pipeline initialized successfully")
        
        # Find actual input files
        input_dir = Path(pipeline.config['input_dir'])
        print(f"Looking for input files in: {input_dir}")
        
        cad_files = list(input_dir.glob("*cad_data_standardized.csv"))
        rms_files = list(input_dir.glob("*rms_data_standardized.csv"))
        
        print(f"Found CAD files: {[f.name for f in cad_files]}")
        print(f"Found RMS files: {[f.name for f in rms_files]}")
        
        if not cad_files or not rms_files:
            print("NO INPUT FILES FOUND - Cannot test actual pipeline")
            return
        
        # Use most recent files
        cad_path = max(cad_files, key=lambda p: p.stat().st_mtime)
        rms_path = max(rms_files, key=lambda p: p.stat().st_mtime)
        
        print(f"Using CAD file: {cad_path.name}")
        print(f"Using RMS file: {rms_path.name}")
        
        # Load raw data
        print("\n" + "="*60)
        print("LOADING RAW DATA")
        print("="*60)
        
        cad_df_raw = pd.read_csv(cad_path)
        rms_df_raw = pd.read_csv(rms_path)
        
        print(f"Raw CAD data: {len(cad_df_raw)} rows, {len(cad_df_raw.columns)} columns")
        print(f"Raw RMS data: {len(rms_df_raw)} rows, {len(rms_df_raw.columns)} columns")
        
        # Check for how_reported column in CAD
        if 'How Reported' in cad_df_raw.columns:
            print(f"\nRAW CAD 'How Reported' sample values:")
            sample_values = cad_df_raw['How Reported'].dropna().head(10).tolist()
            for val in sample_values:
                print(f"  {repr(val)}")
        
        # Check for CAD notes
        cad_notes_col = None
        for col in ['CADNotes', 'CAD Notes', 'cad_notes', 'Notes']:
            if col in cad_df_raw.columns:
                cad_notes_col = col
                break
        
        if cad_notes_col:
            print(f"\nRAW CAD '{cad_notes_col}' sample values:")
            sample_notes = cad_df_raw[cad_notes_col].dropna().head(5).tolist()
            for note in sample_notes:
                print(f"  {repr(note[:100])}...")
        
        # Process data through v8.5 pipeline
        print("\n" + "="*60)
        print("PROCESSING THROUGH v8.5 PIPELINE")
        print("="*60)
        
        # Process CAD data
        print("\nProcessing CAD data...")
        cad_processed = pipeline.process_cad_data_v85(cad_df_raw.copy())
        print(f"Processed CAD data: {len(cad_processed)} rows, {len(cad_processed.columns)} columns")
        
        # Check results of how_reported processing
        if 'how_reported' in cad_processed.columns:
            print(f"\nPROCESSED 'how_reported' values:")
            sample_processed = cad_processed['how_reported'].value_counts().head(10)
            print(sample_processed)
            
            # Check for 9-1-1 specifically
            nine_one_one_count = (cad_processed['how_reported'] == '9-1-1').sum()
            print(f"Count of '9-1-1' values: {nine_one_one_count}")
        
        # Check CAD notes processing
        if 'cad_notes_cleaned' in cad_processed.columns:
            print(f"\nCAD NOTES PROCESSING RESULTS:")
            # Handle both raw and processed data
            notes_cols = ['cad_notes_cleaned', 'cad_notes_username', 'cad_notes_timestamp']
            if 'cad_notes_raw' in cad_processed.columns:
                notes_cols.insert(0, 'cad_notes_raw')
            
            available_cols = [col for col in notes_cols if col in cad_processed.columns]
            cleaned_samples = cad_processed[available_cols].dropna().head(3)
            
            for i, row in cleaned_samples.iterrows():
                if 'cad_notes_raw' in row.index:
                    print(f"  Original: {repr(str(row['cad_notes_raw'])[:50])}...")
                print(f"  Cleaned:  {repr(str(row['cad_notes_cleaned'])[:50])}")
                print(f"  Username: {repr(row['cad_notes_username'])}")
                print(f"  Timestamp: {repr(row['cad_notes_timestamp'])}")
                print()
        
        # Process RMS data
        print("\nProcessing RMS data...")
        rms_processed = pipeline.process_rms_data_v85(rms_df_raw.copy())
        print(f"Processed RMS data: {len(rms_processed)} rows, {len(rms_processed.columns)} columns")
        
        # Check cascade results
        if 'incident_date' in rms_processed.columns and 'incident_time' in rms_processed.columns:
            print(f"\nCASCADE RESULTS:")
            date_populated = rms_processed['incident_date'].notna().sum()
            time_populated = rms_processed['incident_time'].notna().sum()
            print(f"incident_date populated: {date_populated}/{len(rms_processed)} ({(date_populated/len(rms_processed)*100):.1f}%)")
            print(f"incident_time populated: {time_populated}/{len(rms_processed)} ({(time_populated/len(rms_processed)*100):.1f}%)")
            
            # Show sample cascade results
            available_cols = [col for col in ['incident_date', 'incident_time'] if col in rms_processed.columns]
            if available_cols:
                sample_cascade = rms_processed[available_cols].head(5)
                print("\nSample cascade results:")
                print(sample_cascade)
                
                # Check incident_time values specifically
                if 'incident_time' in rms_processed.columns:
                    time_sample = rms_processed['incident_time'].dropna().head(5)
                    print(f"\nSample incident_time values:")
                    for i, time_val in enumerate(time_sample):
                        print(f"  {i+1}: {repr(time_val)} (type: {type(time_val)})")
                else:
                    print("\nincident_time column not found")
        
        # Check coalesced fields
        if 'incident_type' in rms_processed.columns:
            incident_type_populated = rms_processed['incident_type'].notna().sum()
            print(f"incident_type populated: {incident_type_populated}/{len(rms_processed)} ({(incident_type_populated/len(rms_processed)*100):.1f}%)")
        
        if 'all_incidents' in rms_processed.columns:
            all_incidents_populated = rms_processed['all_incidents'].notna().sum()
            print(f"all_incidents populated: {all_incidents_populated}/{len(rms_processed)} ({(all_incidents_populated/len(rms_processed)*100):.1f}%)")
        
        print("\n" + "="*80)
        print("PIPELINE EXECUTION DEBUG COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"PIPELINE DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_actual_pipeline_execution()