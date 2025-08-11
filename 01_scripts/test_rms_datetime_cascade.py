#!/usr/bin/env python3
"""
Test script for RMS Date/Time Cascade Logic

This script demonstrates the implementation of enhanced cascading date and time logic:
1. Date cascade: Date → Date_Between → Report Date
2. Time cascade: Time → Time_Between → Report Time
3. Parse each field separately with errors='coerce'
4. Format time via strftime to avoid Excel fallback artifact

Examples from requirements:
| Incident Date | Incident Date_Between | Report Date | incident_date |
| ------------- | ---------------------- | ----------- | -------------- |
| 2025-05-11    | NaT                    | 2025-05-11  | 2025-05-11     |
| NaT           | 2025-04-13             | 2025-04-13  | 2025-04-13     |
| NaT           | NaT                    | 2025-03-18  | 2025-03-18     |

| Incident Time | Incident Time_Between | Report Time | incident_time |
| ------------- | ---------------------- | ----------- | -------------- |
| 19:00:00      | NaT                    | 19:00:00    | 19:00:00       |
| NaT           | 05:30:00               | 06:34:38    | 05:30:00       |
| NaT           | NaT                    | 09:39:40    | 09:39:40       |
"""

import pandas as pd
import sys
from pathlib import Path

# Import the main class directly since we're in the same directory
import importlib.util
spec = importlib.util.spec_from_file_location("Comprehensive_SCRPA_Fix_v8_5_Standardized", 
                                             "Comprehensive_SCRPA_Fix_v8.5_Standardized.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ComprehensiveSCRPAFixV8_5 = module.ComprehensiveSCRPAFixV8_5

def test_rms_datetime_cascade():
    """Test the RMS date/time cascade functionality."""
    
    print("=" * 60)
    print("RMS DATE/TIME CASCADE LOGIC TEST")
    print("=" * 60)
    
    # Initialize the processor
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Test cases for date cascade
    print("\nTesting Date Cascade Logic:")
    print("-" * 50)
    
    date_test_cases = [
        {
            'Incident Date': '2025-05-11',
            'Incident Date_Between': None,
            'Report Date': '2025-05-11',
            'expected': '2025-05-11'
        },
        {
            'Incident Date': None,
            'Incident Date_Between': '2025-04-13',
            'Report Date': '2025-04-13',
            'expected': '2025-04-13'
        },
        {
            'Incident Date': None,
            'Incident Date_Between': None,
            'Report Date': '2025-03-18',
            'expected': '2025-03-18'
        },
        {
            'Incident Date': None,
            'Incident Date_Between': None,
            'Report Date': None,
            'expected': None
        }
    ]
    
    for i, test_case in enumerate(date_test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Incident Date: '{test_case['Incident Date']}'")
        print(f"  Incident Date_Between: '{test_case['Incident Date_Between']}'")
        print(f"  Report Date: '{test_case['Report Date']}'")
        
        # Create a mock row
        row = pd.Series(test_case)
        
        # Apply the cascade_date function
        result = processor.cascade_date(row)
        
        print(f"  → Expected: '{test_case['expected']}'")
        print(f"  → Actual:   '{result}'")
        
        # Validate result
        if result == test_case['expected'] or (result is None and test_case['expected'] is None):
            print(f"  ✅ PASS")
        else:
            print(f"  ❌ FAIL")
    
    # Test cases for time cascade
    print("\nTesting Time Cascade Logic:")
    print("-" * 50)
    
    time_test_cases = [
        {
            'Incident Time': '19:00:00',
            'Incident Time_Between': None,
            'Report Time': '19:00:00',
            'expected': '19:00:00'
        },
        {
            'Incident Time': None,
            'Incident Time_Between': '05:30:00',
            'Report Time': '06:34:38',
            'expected': '05:30:00'
        },
        {
            'Incident Time': None,
            'Incident Time_Between': None,
            'Report Time': '09:39:40',
            'expected': '09:39:40'
        },
        {
            'Incident Time': None,
            'Incident Time_Between': None,
            'Report Time': None,
            'expected': None
        }
    ]
    
    for i, test_case in enumerate(time_test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Incident Time: '{test_case['Incident Time']}'")
        print(f"  Incident Time_Between: '{test_case['Incident Time_Between']}'")
        print(f"  Report Time: '{test_case['Report Time']}'")
        
        # Create a mock row
        row = pd.Series(test_case)
        
        # Apply the cascade_time function
        result = processor.cascade_time(row)
        
        print(f"  → Expected: '{test_case['expected']}'")
        print(f"  → Actual:   '{result}'")
        
        # Validate result
        if result == test_case['expected'] or (result is None and test_case['expected'] is None):
            print(f"  ✅ PASS")
        else:
            print(f"  ❌ FAIL")
    
    # Test with a mock RMS DataFrame
    print("\nTesting with Mock RMS DataFrame:")
    print("-" * 50)
    
    # Create mock RMS data
    mock_rms_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', 'RMS-003', 'RMS-004'],
        'Incident Date': ['2025-05-11', None, None, None],
        'Incident Date_Between': [None, '2025-04-13', None, None],
        'Report Date': ['2025-05-11', '2025-04-13', '2025-03-18', None],
        'Incident Time': ['19:00:00', None, None, None],
        'Incident Time_Between': [None, '05:30:00', None, None],
        'Report Time': ['19:00:00', '06:34:38', '09:39:40', None]
    })
    
    print(f"Mock RMS DataFrame created with {len(mock_rms_data)} records")
    print(f"Columns: {list(mock_rms_data.columns)}")
    
    # Apply the cascade functions
    mock_rms_data['incident_date'] = mock_rms_data.apply(processor.cascade_date, axis=1)
    mock_rms_data['incident_time'] = mock_rms_data.apply(processor.cascade_time, axis=1)
    
    print(f"\nFinal DataFrame columns: {list(mock_rms_data.columns)}")
    print("\nResults:")
    print(mock_rms_data[['case_number', 'Incident Date', 'Incident Date_Between', 'Report Date', 'incident_date']].to_string(index=False))
    print()
    print(mock_rms_data[['case_number', 'Incident Time', 'Incident Time_Between', 'Report Time', 'incident_time']].to_string(index=False))
    
    # Test time of day calculation
    print("\nTesting Time of Day Calculation:")
    print("-" * 50)
    
    def safe_get_time_of_day(time_val):
        if pd.isna(time_val) or not time_val:
            return "Unknown"
        try:
            # Parse time string (HH:MM:SS format)
            if isinstance(time_val, str):
                # Extract hour from HH:MM:SS format
                hour = int(time_val.split(':')[0])
            else:
                # Fallback for time objects
                hour = time_val.hour if hasattr(time_val, 'hour') else 0
            
            if 0 <= hour < 4:
                return "00:00-03:59 Early Morning"
            elif 4 <= hour < 8:
                return "04:00-07:59 Morning"
            elif 8 <= hour < 12:
                return "08:00-11:59 Morning Peak"
            elif 12 <= hour < 16:
                return "12:00-15:59 Afternoon"
            elif 16 <= hour < 20:
                return "16:00-19:59 Evening Peak"
            else:
                return "20:00-23:59 Night"
        except:
            return "Unknown"
    
    # Add time of day column
    mock_rms_data['time_of_day'] = mock_rms_data['incident_time'].apply(safe_get_time_of_day)
    
    print("\nTime of Day Results:")
    print(mock_rms_data[['case_number', 'incident_time', 'time_of_day']].to_string(index=False))
    
    # Validate against expected results
    print("\nValidation against Expected Results:")
    print("-" * 50)
    
    expected_results = {
        'RMS-001': {
            'date': '2025-05-11',
            'time': '19:00:00',
            'time_of_day': '16:00-19:59 Evening Peak'
        },
        'RMS-002': {
            'date': '2025-04-13',
            'time': '05:30:00',
            'time_of_day': '04:00-07:59 Morning'
        },
        'RMS-003': {
            'date': '2025-03-18',
            'time': '09:39:40',
            'time_of_day': '08:00-11:59 Morning Peak'
        },
        'RMS-004': {
            'date': None,
            'time': None,
            'time_of_day': 'Unknown'
        }
    }
    
    for case_number, expected in expected_results.items():
        row = mock_rms_data[mock_rms_data['case_number'] == case_number].iloc[0]
        
        date_match = str(row['incident_date']) == expected['date'] if expected['date'] else row['incident_date'] is None
        time_match = row['incident_time'] == expected['time'] if expected['time'] else row['incident_time'] is None
        time_of_day_match = row['time_of_day'] == expected['time_of_day']
        
        status = "✅ PASS" if date_match and time_match and time_of_day_match else "❌ FAIL"
        
        print(f"{status} {case_number}:")
        print(f"  Expected: date='{expected['date']}', time='{expected['time']}', time_of_day='{expected['time_of_day']}'")
        print(f"  Actual:   date='{row['incident_date']}', time='{row['incident_time']}', time_of_day='{row['time_of_day']}'")
        print()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_rms_datetime_cascade() 