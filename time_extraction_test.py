# URGENT TEST: Time Extraction Validation
# Date: 2025-07-30
# Purpose: Test the fixed time cascade function with real RMS data

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from fixed_time_cascade_function import FixedTimeCascadeProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_time_extraction():
    """
    CRITICAL TEST: Validate time extraction fix with real RMS data
    
    This test will:
    1. Load the actual RMS file
    2. Apply the fixed cascade function
    3. Validate time extraction results
    4. Compare with original buggy behavior
    """
    print("=" * 80)
    print("URGENT: Testing Time Cascade Function Fix")
    print("=" * 80)
    
    # Initialize the fixed processor
    processor = FixedTimeCascadeProcessor()
    
    # Path to actual RMS data
    rms_file = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\05_Exports\2025_07_29_13_02_46_SCRPA_RMS.xlsx")
    
    if not rms_file.exists():
        print(f"ERROR: RMS file not found: {rms_file}")
        return False
    
    print(f"Testing with file: {rms_file.name}")
    print()
    
    try:
        # Test the FIXED processing
        print("TESTING FIXED PROCESSOR...")
        print("-" * 40)
        
        fixed_df = processor.process_rms_data_fixed(rms_file)
        
        if fixed_df.empty:
            print("ERROR: Fixed processor returned empty DataFrame")
            return False
        
        # Validate results
        print("VALIDATION RESULTS:")
        print("-" * 40)
        
        total_rows = len(fixed_df)
        time_extracted = fixed_df['Incident_Time'].notna().sum()
        time_percentage = (time_extracted / total_rows) * 100 if total_rows > 0 else 0
        
        print(f"Total rows processed: {total_rows}")
        print(f"Times extracted: {time_extracted}")
        print(f"Success rate: {time_percentage:.1f}%")
        print()
        
        if time_extracted == 0:
            print("CRITICAL: NO TIMES EXTRACTED - Fix failed!")
            
            # Debug: Check what's in the raw data
            print("\nDEBUG: Analyzing raw data...")
            raw_df = pd.read_excel(rms_file, engine='openpyxl')
            print(f"Raw columns: {list(raw_df.columns)}")
            
            # Check for time columns
            time_cols = [col for col in raw_df.columns if 'time' in col.lower()]
            print(f"Time-related columns: {time_cols}")
            
            for col in time_cols:
                non_null = raw_df[col].notna().sum()
                print(f"  {col}: {non_null} non-null values")
                if non_null > 0:
                    sample = raw_df[col].dropna().head(3).tolist()
                    print(f"    Sample values: {sample}")
            
            return False
            
        else:
            print("SUCCESS: Time extraction working!")
            
            # Show sample extracted times
            sample_times = fixed_df['Incident_Time'].dropna().head(5).tolist()
            print(f"Sample extracted times: {sample_times}")
            
            # Test time of day calculation
            time_of_day_known = fixed_df[fixed_df['Time_Of_Day'] != 'Unknown'].shape[0]
            tod_percentage = (time_of_day_known / total_rows) * 100 if total_rows > 0 else 0
            
            print(f"Time of day calculated: {time_of_day_known} ({tod_percentage:.1f}%)")
            
            # Show time of day distribution
            tod_dist = fixed_df['Time_Of_Day'].value_counts()
            print("\nTime of day distribution:")
            for time_period, count in tod_dist.head(10).items():
                print(f"  {time_period}: {count}")
        
        print()
        print("=" * 80)
        
        # Compare with current processed output
        print("COMPARING WITH CURRENT PROCESSED OUTPUT...")
        print("-" * 40)
        
        current_file = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\rms_data_standardized.csv")
        
        if current_file.exists():
            current_df = pd.read_csv(current_file)
            current_time_extracted = current_df['Incident_Time'].notna().sum()
            current_percentage = (current_time_extracted / len(current_df)) * 100 if len(current_df) > 0 else 0
            
            print(f"CURRENT (buggy) output:")
            print(f"  Times extracted: {current_time_extracted} out of {len(current_df)} ({current_percentage:.1f}%)")
            
            print(f"FIXED output:")
            print(f"  Times extracted: {time_extracted} out of {total_rows} ({time_percentage:.1f}%)")
            
            improvement = time_percentage - current_percentage
            print(f"IMPROVEMENT: {improvement:+.1f} percentage points")
            
            if improvement > 0:
                print("Fix shows improvement!")
            else:
                print("Fix needs more work")
        
        return time_extracted > 0
        
    except Exception as e:
        print(f"ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cascade_function_directly():
    """
    Test the cascade function directly with sample data
    """
    print("\nDIRECT FUNCTION TEST:")
    print("-" * 40)
    
    processor = FixedTimeCascadeProcessor()
    
    # Create test data with different column name scenarios
    test_cases = [
        # Case 1: Mapped column names (should work)
        {
            'Case_Number': '25-000001',
            'Incident_Time_Raw': '14:30:00',
            'Incident_Time_Between_Raw': None,
            'Report_Time_Raw': '15:00:00'
        },
        
        # Case 2: Raw column names (should work with fix)
        {
            'Case Number': '25-000002',
            'Incident Time': '09:45:00',
            'Incident Time_Between': None,
            'Report Time': '10:15:00'
        },
        
        # Case 3: Mixed scenario
        {
            'Case_Number': '25-000003',
            'Incident Time': '22:15:00',  # Raw name
            'Incident_Time_Between_Raw': '22:30:00',  # Mapped name
        },
        
        # Case 4: No time data
        {
            'Case_Number': '25-000004',
            'Incident_Time_Raw': None,
            'Incident_Time_Between_Raw': None,
            'Report_Time_Raw': None
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case.get('Case_Number', test_case.get('Case Number'))}")
        
        # Create a pandas Series to simulate a row
        row = pd.Series(test_case)
        
        # Test the fixed cascade function
        extracted_time = processor.cascade_time_fixed(row)
        time_of_day = processor.get_time_of_day(extracted_time)
        
        print(f"  Input columns: {list(test_case.keys())}")
        print(f"  Extracted time: {extracted_time}")
        print(f"  Time of day: {time_of_day}")
        print()

if __name__ == "__main__":
    print("Starting time extraction validation tests...")
    
    # Run the main test
    success = test_time_extraction()
    
    # Run direct function test
    test_cascade_function_directly()
    
    if success:
        print("\nTIME EXTRACTION FIX VALIDATED!")
        print("The fixed cascade function successfully extracts time values.")
        print("Ready to deploy to production script.")
    else:
        print("\nTIME EXTRACTION FIX FAILED!")
        print("Further debugging required.")
    
    print("\nRecommendation:")
    print("Replace the cascade_time function in Comprehensive_SCRPA_Fix_v8.0_Standardized.py")
    print("with the cascade_time_FIXED function from fixed_time_cascade_function.py")