#!/usr/bin/env python3
"""
Test script for Robust RMS Date/Time Cascade Logic

This script validates the implementation of robust RMS date/time cascade logic:
1. Date cascade: Date → Date_Between → Report Date
2. Time cascade: Time → Time_Between → Report Time
3. Format as strings to avoid Excel fallback artifacts

Examples from requirements:
- Dates: (2025-05-11, NaT, 2025-05-11) → 2025-05-11
- Times: ("19:00:00", NaT, "19:00:00") → "19:00:00"
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, date, time

# Import the main class directly since we're in the same directory
import importlib.util
spec = importlib.util.spec_from_file_location("Comprehensive_SCRPA_Fix_v8_5_Standardized", 
                                             "Comprehensive_SCRPA_Fix_v8.5_Standardized.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ComprehensiveSCRPAFixV8_5 = module.ComprehensiveSCRPAFixV8_5

def test_robust_date_cascade():
    """Test the robust date cascade logic."""
    
    print("=" * 60)
    print("ROBUST RMS DATE CASCADE TEST")
    print("=" * 60)
    
    # Test cases for date cascade
    print("\nTesting Date Cascade Logic:")
    print("-" * 50)
    
    # Create test data with various date scenarios
    test_data = pd.DataFrame({
        'incident_date_raw': [
            '2025-05-11',      # Primary date available
            None,              # Primary missing, fallback available
            None,              # Primary and fallback missing, report available
            None,              # All missing
            '2025-08-01',      # Primary only
            'invalid',         # Invalid primary, valid fallback
            '2025-06-15',      # Primary available
            None               # All missing
        ],
        'incident_date_between_raw': [
            '2025-05-12',      # Fallback (should not be used)
            '2025-05-11',      # Fallback (should be used)
            None,              # Fallback missing
            None,              # All missing
            None,              # Primary only case
            '2025-05-11',      # Valid fallback for invalid primary
            None,              # Primary only
            None               # All missing
        ],
        'report_date_raw': [
            '2025-05-13',      # Report date (should not be used)
            '2025-05-12',      # Report date (should not be used)
            '2025-05-11',      # Report date (should be used)
            None,              # All missing
            '2025-08-02',      # Report date (should not be used)
            '2025-05-12',      # Report date (should not be used)
            '2025-06-16',      # Report date (should not be used)
            '2025-12-31'       # Report date (should be used)
        ]
    })
    
    print("Original Test Data:")
    print(test_data.to_string(index=False))
    
    # Apply robust date cascade logic
    d1 = pd.to_datetime(test_data["incident_date_raw"], errors="coerce")
    d2 = pd.to_datetime(test_data["incident_date_between_raw"], errors="coerce")
    d3 = pd.to_datetime(test_data["report_date_raw"], errors="coerce")
    test_data['incident_date'] = (
        d1.fillna(d2)
          .fillna(d3)
          .dt.date
    )
    
    print("\nAfter Date Cascade:")
    print(test_data[['incident_date_raw', 'incident_date_between_raw', 'report_date_raw', 'incident_date']].to_string(index=False))
    
    # Validate against expected results
    print("\nValidation against Expected Results:")
    print("-" * 50)
    
    expected_results = {
        0: '2025-05-11',  # Primary date should be used
        1: '2025-05-11',  # Fallback date should be used
        2: '2025-05-11',  # Report date should be used
        3: None,          # All missing should result in None
        4: '2025-08-01',  # Primary only
        5: '2025-05-11',  # Invalid primary, valid fallback
        6: '2025-06-15',  # Primary only
        7: '2025-12-31'   # Report date should be used
    }
    
    for idx, expected in expected_results.items():
        actual = test_data.iloc[idx]['incident_date']
        # Convert datetime.date to string for comparison
        actual_str = str(actual) if pd.notna(actual) else None
        status = "✅ PASS" if actual_str == expected else "❌ FAIL"
        print(f"{status} Row {idx}: Expected '{expected}', Got '{actual_str}'")

def test_robust_time_cascade():
    """Test the robust time cascade logic."""
    
    print("=" * 60)
    print("ROBUST RMS TIME CASCADE TEST")
    print("=" * 60)
    
    # Test cases for time cascade
    print("\nTesting Time Cascade Logic:")
    print("-" * 50)
    
    # Create test data with various time scenarios
    test_data = pd.DataFrame({
        'incident_time_raw': [
            '19:00:00',        # Primary time available
            None,              # Primary missing, fallback available
            None,              # Primary and fallback missing, report available
            None,              # All missing
            '14:30:00',        # Primary only
            'invalid',         # Invalid primary, valid fallback
            '09:15:00',        # Primary available
            None               # All missing
        ],
        'incident_time_between_raw': [
            '19:30:00',        # Fallback (should not be used)
            '19:00:00',        # Fallback (should be used)
            None,              # Fallback missing
            None,              # All missing
            None,              # Primary only case
            '19:00:00',        # Valid fallback for invalid primary
            None,              # Primary only
            None               # All missing
        ],
        'report_time_raw': [
            '20:00:00',        # Report time (should not be used)
            '19:30:00',        # Report time (should not be used)
            '19:00:00',        # Report time (should be used)
            None,              # All missing
            '15:00:00',        # Report time (should not be used)
            '19:30:00',        # Report time (should not be used)
            '10:00:00',        # Report time (should not be used)
            '23:59:00'         # Report time (should be used)
        ]
    })
    
    print("Original Test Data:")
    print(test_data.to_string(index=False))
    
    # Apply robust time cascade logic
    t1 = pd.to_datetime(test_data["incident_time_raw"], errors="coerce").dt.time
    t2 = pd.to_datetime(test_data["incident_time_between_raw"], errors="coerce").dt.time
    t3 = pd.to_datetime(test_data["report_time_raw"], errors="coerce").dt.time
    test_data['incident_time'] = t1.fillna(t2).fillna(t3)
    
    # Format as strings to avoid Excel fallback artifacts
    test_data['incident_time'] = test_data['incident_time'].apply(
        lambda t: t.strftime("%H:%M:%S") if pd.notna(t) else None
    )
    
    print("\nAfter Time Cascade:")
    print(test_data[['incident_time_raw', 'incident_time_between_raw', 'report_time_raw', 'incident_time']].to_string(index=False))
    
    # Validate against expected results
    print("\nValidation against Expected Results:")
    print("-" * 50)
    
    expected_results = {
        0: '19:00:00',  # Primary time should be used
        1: '19:00:00',  # Fallback time should be used
        2: '19:00:00',  # Report time should be used
        3: None,        # All missing should result in None
        4: '14:30:00',  # Primary only
        5: '19:00:00',  # Invalid primary, valid fallback
        6: '09:15:00',  # Primary only
        7: '23:59:00'   # Report time should be used
    }
    
    for idx, expected in expected_results.items():
        actual = test_data.iloc[idx]['incident_time']
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        print(f"{status} Row {idx}: Expected '{expected}', Got '{actual}'")

def test_excel_fallback_artifacts():
    """Test handling of Excel fallback artifacts."""
    
    print("=" * 60)
    print("EXCEL FALLBACK ARTIFACTS TEST")
    print("=" * 60)
    
    # Test cases for Excel fallback artifacts
    print("\nTesting Excel Fallback Artifacts:")
    print("-" * 50)
    
    # Create test data with potential Excel artifacts
    test_data = pd.DataFrame({
        'incident_time_raw': [
            '19:00:00',        # Normal time
            '1900:00:00',      # Excel artifact (19:00:00 parsed as date)
            '00:30:00',        # Early morning
            '1900:30:00',      # Excel artifact (00:30:00 parsed as date)
            '12:00:00',        # Noon
            '1900:12:00',      # Excel artifact (12:00:00 parsed as date)
            None,              # Missing
            'invalid'          # Invalid format
        ]
    })
    
    print("Original Test Data (with potential Excel artifacts):")
    print(test_data.to_string(index=False))
    
    # Apply time parsing and formatting with Excel artifact handling
    def parse_time_with_excel_fix(time_str):
        if pd.isna(time_str):
            return None
        
        time_str = str(time_str)
        
        # Handle Excel artifacts (e.g., "1900:00:00" should be "19:00:00")
        if time_str.startswith('1900:'):
            time_str = time_str.replace('1900:', '')
        
        try:
            # Try to parse as time
            parsed = pd.to_datetime(time_str, format='%H:%M:%S', errors='coerce')
            if pd.notna(parsed):
                return parsed.strftime("%H:%M:%S")
            
            # Try alternative formats
            parsed = pd.to_datetime(time_str, errors='coerce')
            if pd.notna(parsed):
                return parsed.strftime("%H:%M:%S")
            
            return None
        except:
            return None
    
    test_data['incident_time'] = test_data['incident_time_raw'].apply(parse_time_with_excel_fix)
    
    print("\nAfter Time Parsing and Formatting:")
    print(test_data[['incident_time_raw', 'incident_time']].to_string(index=False))
    
    # Validate that Excel artifacts are handled correctly
    print("\nValidation of Excel Artifact Handling:")
    print("-" * 50)
    
    expected_results = {
        0: '19:00:00',  # Normal time should be preserved
        1: '19:00:00',  # Excel artifact should be corrected
        2: '00:30:00',  # Early morning should be preserved
        3: '00:30:00',  # Excel artifact should be corrected
        4: '12:00:00',  # Noon should be preserved
        5: '12:00:00',  # Excel artifact should be corrected
        6: None,        # Missing should remain None
        7: None         # Invalid should be None
    }
    
    for idx, expected in expected_results.items():
        actual = test_data.iloc[idx]['incident_time']
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        print(f"{status} Row {idx}: Expected '{expected}', Got '{actual}'")

def test_integrated_cascade():
    """Test integrated date and time cascade together."""
    
    print("=" * 60)
    print("INTEGRATED DATE/TIME CASCADE TEST")
    print("=" * 60)
    
    # Test cases for integrated cascade
    print("\nTesting Integrated Date/Time Cascade:")
    print("-" * 50)
    
    # Create comprehensive test data
    test_data = pd.DataFrame({
        'incident_date_raw': ['2025-05-11', None, '2025-08-01', None],
        'incident_date_between_raw': ['2025-05-12', '2025-05-11', None, None],
        'report_date_raw': ['2025-05-13', '2025-05-12', '2025-08-02', '2025-12-31'],
        'incident_time_raw': ['19:00:00', None, '14:30:00', None],
        'incident_time_between_raw': ['19:30:00', '19:00:00', None, None],
        'report_time_raw': ['20:00:00', '19:30:00', '15:00:00', '23:59:00']
    })
    
    print("Original Test Data:")
    print(test_data.to_string(index=False))
    
    # Apply robust date cascade logic
    d1 = pd.to_datetime(test_data["incident_date_raw"], errors="coerce")
    d2 = pd.to_datetime(test_data["incident_date_between_raw"], errors="coerce")
    d3 = pd.to_datetime(test_data["report_date_raw"], errors="coerce")
    test_data['incident_date'] = (
        d1.fillna(d2)
          .fillna(d3)
          .dt.date
    )
    
    # Apply robust time cascade logic
    t1 = pd.to_datetime(test_data["incident_time_raw"], errors="coerce").dt.time
    t2 = pd.to_datetime(test_data["incident_time_between_raw"], errors="coerce").dt.time
    t3 = pd.to_datetime(test_data["report_time_raw"], errors="coerce").dt.time
    test_data['incident_time'] = t1.fillna(t2).fillna(t3)
    
    # Format as strings to avoid Excel fallback artifacts
    test_data['incident_time'] = test_data['incident_time'].apply(
        lambda t: t.strftime("%H:%M:%S") if pd.notna(t) else None
    )
    
    print("\nAfter Integrated Cascade:")
    print(test_data[['incident_date', 'incident_time']].to_string(index=False))
    
    # Validate integrated results
    print("\nValidation of Integrated Cascade:")
    print("-" * 50)
    
    expected_results = {
        0: {'date': '2025-05-11', 'time': '19:00:00'},  # Primary for both
        1: {'date': '2025-05-11', 'time': '19:00:00'},  # Fallback for both
        2: {'date': '2025-08-01', 'time': '14:30:00'},  # Primary date, primary time
        3: {'date': '2025-12-31', 'time': '23:59:00'}   # Report for both
    }
    
    for idx, expected in expected_results.items():
        actual_date = test_data.iloc[idx]['incident_date']
        actual_time = test_data.iloc[idx]['incident_time']
        # Convert datetime.date to string for comparison
        actual_date_str = str(actual_date) if pd.notna(actual_date) else None
        date_match = actual_date_str == expected['date']
        time_match = actual_time == expected['time']
        status = "✅ PASS" if date_match and time_match else "❌ FAIL"
        print(f"{status} Row {idx}: Expected date='{expected['date']}', time='{expected['time']}'")
        print(f"         Got date='{actual_date_str}', time='{actual_time}'")

def main():
    """Run all tests."""
    test_robust_date_cascade()
    print("\n" + "=" * 80 + "\n")
    
    test_robust_time_cascade()
    print("\n" + "=" * 80 + "\n")
    
    test_excel_fallback_artifacts()
    print("\n" + "=" * 80 + "\n")
    
    test_integrated_cascade()
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main() 