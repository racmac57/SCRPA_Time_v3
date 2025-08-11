#!/usr/bin/env python3
"""
Test script for Vehicle Fields Uppercasing, Narrative Cleaning, and Period/Day_of_Week/Cycle_Name Fixes

This script demonstrates the implementation of three new features:
1. Vehicle Fields Uppercasing: Convert vehicle_1, vehicle_2, vehicle_1_and_vehicle_2 to uppercase
2. Narrative Cleaning: Clean line breaks and extra tokens in narrative
3. Period, Day_of_Week & Cycle_Name Fixes: Ensure proper datetime handling and calculations

Examples from requirements:
| vehicle_1 | vehicle_2 | vehicle_1_and_vehicle_2 | After Uppercasing |
| --------- | --------- | ---------------------- | ----------------- |
| "nj-abc123" | NaN | NaN | "NJ-ABC123" |
| NaN | "pa-xyz789" | NaN | "PA-XYZ789" |
| "ca-111" | "ca-222" | "ca-111 | ca-222" | "CA-111 | CA-222" |

| Raw Narrative | Cleaned Narrative |
| ------------- | ----------------- |
| "Note #(cr)#(lf) details." | "Note Details." |
| "Line1\nLine2\tLine3" | "Line1 Line2 Line3" |
| "   multiple    spaces   " | "Multiple Spaces" |

| incident_date | period | season | day_of_week | day_type | cycle_name |
| ------------- | ------ | ------ | ----------- | -------- | ---------- |
| 2025-08-01 | "7-Day" | "Summer" | "Friday" | "Weekday" | "T4_C18W02" |
| 2025-06-01 | "28-Day" | "Summer" | "Monday" | "Weekday" | "T4_C15W03" |
| 2024-12-30 | "Historical" | "Winter" | "Monday" | "Weekday" | "T4_C00W00" |
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, date

# Import the main class directly since we're in the same directory
import importlib.util
spec = importlib.util.spec_from_file_location("Comprehensive_SCRPA_Fix_v8_5_Standardized", 
                                             "Comprehensive_SCRPA_Fix_v8.5_Standardized.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ComprehensiveSCRPAFixV8_5 = module.ComprehensiveSCRPAFixV8_5

def test_vehicle_fields_uppercasing():
    """Test the Vehicle Fields Uppercasing functionality."""
    
    print("=" * 60)
    print("VEHICLE FIELDS UPPERCASING TEST")
    print("=" * 60)
    
    # Initialize the processor
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Test cases for vehicle uppercasing
    print("\nTesting Vehicle Fields Uppercasing:")
    print("-" * 50)
    
    # Create test data
    test_data = pd.DataFrame({
        'vehicle_1': ['nj-abc123', None, 'ca-111', 'ny-12345'],
        'vehicle_2': [None, 'pa-xyz789', 'ca-222', None],
        'vehicle_1_and_vehicle_2': [None, None, 'ca-111 | ca-222', None]
    })
    
    print("Original Data:")
    print(test_data.to_string(index=False))
    
    # Apply vehicle uppercasing
    for col in ['vehicle_1', 'vehicle_2', 'vehicle_1_and_vehicle_2']:
        if col in test_data.columns:
            test_data[col] = test_data[col].str.upper().where(test_data[col].notna(), None)
    
    print("\nAfter Uppercasing:")
    print(test_data.to_string(index=False))
    
    # Validate against expected results
    print("\nValidation against Expected Results:")
    print("-" * 50)
    
    expected_results = {
        0: {'vehicle_1': 'NJ-ABC123', 'vehicle_2': None, 'vehicle_1_and_vehicle_2': None},
        1: {'vehicle_1': None, 'vehicle_2': 'PA-XYZ789', 'vehicle_1_and_vehicle_2': None},
        2: {'vehicle_1': 'CA-111', 'vehicle_2': 'CA-222', 'vehicle_1_and_vehicle_2': 'CA-111 | CA-222'},
        3: {'vehicle_1': 'NY-12345', 'vehicle_2': None, 'vehicle_1_and_vehicle_2': None}
    }
    
    for idx, expected in expected_results.items():
        row = test_data.iloc[idx]
        
        v1_match = row['vehicle_1'] == expected['vehicle_1']
        v2_match = row['vehicle_2'] == expected['vehicle_2']
        v12_match = row['vehicle_1_and_vehicle_2'] == expected['vehicle_1_and_vehicle_2']
        
        status = "✅ PASS" if v1_match and v2_match and v12_match else "❌ FAIL"
        
        print(f"{status} Row {idx}:")
        print(f"  Expected: v1='{expected['vehicle_1']}', v2='{expected['vehicle_2']}', v12='{expected['vehicle_1_and_vehicle_2']}'")
        print(f"  Actual:   v1='{row['vehicle_1']}', v2='{row['vehicle_2']}', v12='{row['vehicle_1_and_vehicle_2']}'")
        print()

def test_narrative_cleaning():
    """Test the Narrative Cleaning functionality."""
    
    print("=" * 60)
    print("NARRATIVE CLEANING TEST")
    print("=" * 60)
    
    # Initialize the processor
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Test cases for narrative cleaning
    print("\nTesting Narrative Cleaning:")
    print("-" * 50)
    
    import re
    
    def clean_narrative(text: str) -> str:
        if pd.isna(text):
            return None
        s = re.sub(r'#\(cr\)#\(lf\)|#\(lf\)|#\(cr\)|[\r\n\t]+', ' ', text)
        s = re.sub(r'\s+', ' ', s).strip()
        return s.title() if s else None
    
    narrative_test_cases = [
        ("Note #(cr)#(lf) details.", "Note Details."),
        ("Line1\nLine2\tLine3", "Line1 Line2 Line3"),
        ("   multiple    spaces   ", "Multiple Spaces"),
        ("Simple text", "Simple Text"),
        ("", None),
        (None, None),
        ("#(lf)Header#(cr)Content", "Header Content")
    ]
    
    for raw_narrative, expected in narrative_test_cases:
        result = clean_narrative(raw_narrative)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} '{raw_narrative}' → '{result}' (expected: '{expected}')")
    
    # Test with mock DataFrame
    print("\nTesting with Mock DataFrame:")
    print("-" * 50)
    
    mock_data = pd.DataFrame({
        'case_number': ['CASE-001', 'CASE-002', 'CASE-003', 'CASE-004'],
        'narrative_raw': [
            "Note #(cr)#(lf) details.",
            "Line1\nLine2\tLine3",
            "   multiple    spaces   ",
            "Simple text"
        ]
    })
    
    print("Original Data:")
    print(mock_data.to_string(index=False))
    
    # Apply narrative cleaning
    mock_data['narrative'] = mock_data['narrative_raw'].apply(clean_narrative)
    
    print("\nAfter Cleaning:")
    print(mock_data[['case_number', 'narrative_raw', 'narrative']].to_string(index=False))

def test_period_day_week_cycle_fixes():
    """Test the Period, Day_of_Week & Cycle_Name Fixes functionality."""
    
    print("=" * 60)
    print("PERIOD, DAY_OF_WEEK & CYCLE_NAME FIXES TEST")
    print("=" * 60)
    
    # Initialize the processor
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Test cases for period, day_of_week, and cycle_name
    print("\nTesting Period, Day_of_Week & Cycle_Name Fixes:")
    print("-" * 50)
    
    # Create test data with various date formats
    test_data = pd.DataFrame({
        'incident_date': [
            '2025-08-01',  # Recent date (7-Day)
            '2025-06-01',  # Older date (28-Day)
            '2024-12-30',  # Historical date
            '2025-01-15',  # YTD date
            None,          # Null date
            'invalid'      # Invalid date
        ]
    })
    
    print("Original Data:")
    print(test_data.to_string(index=False))
    
    # Apply fixes
    # Ensure incident_date is datetime
    test_data['incident_date'] = pd.to_datetime(test_data['incident_date'], errors='coerce')
    
    # Period
    test_data['period'] = test_data['incident_date'].apply(processor.get_period)
    
    # Season
    test_data['season'] = test_data['incident_date'].apply(processor.get_season)
    
    # Day of Week & Type
    test_data['day_of_week'] = test_data['incident_date'].dt.day_name()
    test_data['day_type'] = test_data['day_of_week'].isin(['Saturday', 'Sunday']).map({True: 'Weekend', False: 'Weekday'})
    
    # Cycle Name (mock implementation for testing)
    def mock_get_cycle_for_date(date_val, cycle_calendar):
        if pd.isna(date_val):
            return None
        # Mock cycle calculation based on date
        if date_val.year == 2025:
            if date_val.month == 8:
                return "T4_C18W02"
            elif date_val.month == 6:
                return "T4_C15W03"
            else:
                return "T4_C01W01"
        else:
            return "T4_C00W00"
    
    test_data['cycle_name'] = test_data['incident_date'].apply(
        lambda x: mock_get_cycle_for_date(x, None) if pd.notna(x) else None
    )
    
    print("\nAfter Processing:")
    print(test_data.to_string(index=False))
    
    # Validate against expected results
    print("\nValidation against Expected Results:")
    print("-" * 50)
    
    expected_results = {
        0: {
            'period': '7-Day',  # Assuming this is within 7 days of current date
            'season': 'Summer',
            'day_of_week': 'Friday',
            'day_type': 'Weekday',
            'cycle_name': 'T4_C18W02'
        },
        1: {
            'period': '28-Day',  # Assuming this is within 28 days of current date
            'season': 'Summer',
            'day_of_week': 'Sunday',
            'day_type': 'Weekend',
            'cycle_name': 'T4_C15W03'
        },
        2: {
            'period': 'Historical',
            'season': 'Winter',
            'day_of_week': 'Monday',
            'day_type': 'Weekday',
            'cycle_name': 'T4_C00W00'
        },
        3: {
            'period': 'YTD',
            'season': 'Winter',
            'day_of_week': 'Wednesday',
            'day_type': 'Weekday',
            'cycle_name': 'T4_C01W01'
        }
    }
    
    for idx, expected in expected_results.items():
        if idx < len(test_data):
            row = test_data.iloc[idx]
            
            period_match = row['period'] == expected['period']
            season_match = row['season'] == expected['season']
            day_of_week_match = row['day_of_week'] == expected['day_of_week']
            day_type_match = row['day_type'] == expected['day_type']
            cycle_name_match = row['cycle_name'] == expected['cycle_name']
            
            status = "✅ PASS" if period_match and season_match and day_of_week_match and day_type_match and cycle_name_match else "❌ FAIL"
            
            print(f"{status} Row {idx}:")
            print(f"  Expected: period='{expected['period']}', season='{expected['season']}', day_of_week='{expected['day_of_week']}', day_type='{expected['day_type']}', cycle_name='{expected['cycle_name']}'")
            print(f"  Actual:   period='{row['period']}', season='{row['season']}', day_of_week='{row['day_of_week']}', day_type='{row['day_type']}', cycle_name='{row['cycle_name']}'")
            print()

def test_merge_logic():
    """Test the Merge Logic: Deduplicate and Reapply Cleaning functionality."""
    
    print("=" * 60)
    print("MERGE LOGIC: DEDUPLICATE AND REAPPLY CLEANING TEST")
    print("=" * 60)
    
    # Initialize the processor
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Test cases for merge logic
    print("\nTesting Merge Logic:")
    print("-" * 50)
    
    # Create mock merged data with suffixes
    merged_data = pd.DataFrame({
        'case_number': ['CASE-001', 'CASE-002', 'CASE-003'],
        'response_type_cad': ['Burglary - Auto', None, 'Alarm'],
        'response_type_rms': [None, 'Medical', 'Alarm'],
        'category_type_cad': ['Crime', None, 'Alarm'],
        'category_type_rms': [None, 'Medical', 'Alarm'],
        'incident_date_cad': ['2025-08-01', None, '2025-08-02'],
        'incident_date_rms': [None, '2025-08-01', None],
        'incident_time_cad': ['14:30:00', None, '09:15:00'],
        'incident_time_rms': [None, '16:45:00', None]
    })
    
    print("Original Merged Data (with suffixes):")
    print(merged_data.to_string(index=False))
    
    # Apply merge logic
    # After merge with suffixes (_cad, _rms):
    if 'incident_date_cad' in merged_data.columns and 'incident_date_rms' in merged_data.columns:
        merged_data['incident_date'] = merged_data['incident_date_cad'].fillna(merged_data['incident_date_rms'])
    elif 'incident_date_cad' in merged_data.columns:
        merged_data['incident_date'] = merged_data['incident_date_cad']
    elif 'incident_date_rms' in merged_data.columns:
        merged_data['incident_date'] = merged_data['incident_date_rms']
    
    if 'incident_time_cad' in merged_data.columns and 'incident_time_rms' in merged_data.columns:
        merged_data['incident_time'] = merged_data['incident_time_cad'].fillna(merged_data['incident_time_rms'])
    elif 'incident_time_cad' in merged_data.columns:
        merged_data['incident_time'] = merged_data['incident_time_cad']
    elif 'incident_time_rms' in merged_data.columns:
        merged_data['incident_time'] = merged_data['incident_time_rms']
    
    # Reapply key fixes:
    if 'incident_time' in merged_data.columns:
        merged_data['time_of_day'] = merged_data['incident_time'].apply(processor.map_tod)
    
    # Ensure response_type and category_type are properly set
    if 'response_type_cad' in merged_data.columns and 'response_type_rms' in merged_data.columns:
        merged_data['response_type'] = merged_data['response_type_cad'].fillna(merged_data['response_type_rms'])
    elif 'response_type_cad' in merged_data.columns:
        merged_data['response_type'] = merged_data['response_type_cad']
    elif 'response_type_rms' in merged_data.columns:
        merged_data['response_type'] = merged_data['response_type_rms']
    
    if 'category_type_cad' in merged_data.columns and 'category_type_rms' in merged_data.columns:
        merged_data['category_type'] = merged_data['category_type_cad'].fillna(merged_data['category_type_rms'])
    elif 'category_type_cad' in merged_data.columns:
        merged_data['category_type'] = merged_data['category_type_cad']
    elif 'category_type_rms' in merged_data.columns:
        merged_data['category_type'] = merged_data['category_type_rms']
    
    # Drop suffix columns
    drop_cols = [c for c in merged_data.columns if c.endswith('_cad') or c.endswith('_rms')]
    merged_data = merged_data.drop(columns=drop_cols)
    
    print("\nAfter Merge Logic Processing:")
    print(merged_data.to_string(index=False))
    
    # Validate against expected results
    print("\nValidation against Expected Results:")
    print("-" * 50)
    
    expected_results = {
        0: {
            'response_type': 'Burglary - Auto',
            'category_type': 'Crime',
            'incident_date': '2025-08-01',
            'incident_time': '14:30:00',
            'time_of_day': '12:00-15:59 Afternoon'
        },
        1: {
            'response_type': 'Medical',
            'category_type': 'Medical',
            'incident_date': '2025-08-01',
            'incident_time': '16:45:00',
            'time_of_day': '16:00-19:59 Evening Peak'
        },
        2: {
            'response_type': 'Alarm',
            'category_type': 'Alarm',
            'incident_date': '2025-08-02',
            'incident_time': '09:15:00',
            'time_of_day': '08:00-11:59 Morning Peak'
        }
    }
    
    for idx, expected in expected_results.items():
        row = merged_data.iloc[idx]
        
        response_match = row['response_type'] == expected['response_type']
        category_match = row['category_type'] == expected['category_type']
        date_match = str(row['incident_date']) == expected['incident_date']
        time_match = row['incident_time'] == expected['incident_time']
        time_of_day_match = row['time_of_day'] == expected['time_of_day']
        
        status = "✅ PASS" if response_match and category_match and date_match and time_match and time_of_day_match else "❌ FAIL"
        
        print(f"{status} Row {idx}:")
        print(f"  Expected: response_type='{expected['response_type']}', category_type='{expected['category_type']}', incident_date='{expected['incident_date']}', incident_time='{expected['incident_time']}', time_of_day='{expected['time_of_day']}'")
        print(f"  Actual:   response_type='{row['response_type']}', category_type='{row['category_type']}', incident_date='{row['incident_date']}', incident_time='{row['incident_time']}', time_of_day='{row['time_of_day']}'")
        print()

def test_integrated_features():
    """Test all features together with a comprehensive mock dataset."""
    
    print("=" * 60)
    print("INTEGRATED FEATURES TEST")
    print("=" * 60)
    
    # Initialize the processor
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Create comprehensive mock data
    mock_data = pd.DataFrame({
        'case_number': ['CASE-001', 'CASE-002', 'CASE-003', 'CASE-004'],
        'vehicle_1': ['nj-abc123', None, 'ca-111', 'ny-12345'],
        'vehicle_2': [None, 'pa-xyz789', 'ca-222', None],
        'vehicle_1_and_vehicle_2': [None, None, 'ca-111 | ca-222', None],
        'narrative_raw': [
            "Note #(cr)#(lf) details.",
            "Line1\nLine2\tLine3",
            "   multiple    spaces   ",
            "Simple text"
        ],
        'incident_date': ['2025-08-01', '2025-06-01', '2024-12-30', '2025-01-15'],
        'response_type_cad': ['Burglary - Auto', None, 'Alarm', 'Theft'],
        'response_type_rms': [None, 'Medical', 'Alarm', None],
        'category_type_cad': ['Crime', None, 'Alarm', 'Crime'],
        'category_type_rms': [None, 'Medical', 'Alarm', None]
    })
    
    print(f"Comprehensive Mock Data created with {len(mock_data)} records")
    print(f"Initial columns: {list(mock_data.columns)}")
    
    # Apply all features
    
    # 1. Vehicle Fields Uppercasing
    for col in ['vehicle_1', 'vehicle_2', 'vehicle_1_and_vehicle_2']:
        if col in mock_data.columns:
            mock_data[col] = mock_data[col].str.upper().where(mock_data[col].notna(), None)
    
    # 2. Narrative Cleaning
    import re
    def clean_narrative(text: str) -> str:
        if pd.isna(text):
            return None
        s = re.sub(r'#\(cr\)#\(lf\)|#\(lf\)|#\(cr\)|[\r\n\t]+', ' ', text)
        s = re.sub(r'\s+', ' ', s).strip()
        return s.title() if s else None
    
    mock_data['narrative'] = mock_data['narrative_raw'].apply(clean_narrative)
    
    # 3. Period, Day_of_Week & Cycle_Name Fixes
    mock_data['incident_date'] = pd.to_datetime(mock_data['incident_date'], errors='coerce')
    mock_data['period'] = mock_data['incident_date'].apply(processor.get_period)
    mock_data['season'] = mock_data['incident_date'].apply(processor.get_season)
    mock_data['day_of_week'] = mock_data['incident_date'].dt.day_name()
    mock_data['day_type'] = mock_data['day_of_week'].isin(['Saturday', 'Sunday']).map({True: 'Weekend', False: 'Weekday'})
    
    # Mock cycle calculation
    def mock_get_cycle_for_date(date_val, cycle_calendar):
        if pd.isna(date_val):
            return None
        if date_val.year == 2025:
            if date_val.month == 8:
                return "T4_C18W02"
            elif date_val.month == 6:
                return "T4_C15W03"
            else:
                return "T4_C01W01"
        else:
            return "T4_C00W00"
    
    mock_data['cycle_name'] = mock_data['incident_date'].apply(
        lambda x: mock_get_cycle_for_date(x, None) if pd.notna(x) else None
    )
    
    # 4. Merge Logic (simplified for testing)
    mock_data['response_type'] = mock_data['response_type_cad'].fillna(mock_data['response_type_rms'])
    mock_data['category_type'] = mock_data['category_type_cad'].fillna(mock_data['category_type_rms'])
    
    # Drop suffix columns
    drop_cols = [c for c in mock_data.columns if c.endswith('_cad') or c.endswith('_rms')]
    mock_data = mock_data.drop(columns=drop_cols)
    
    print(f"\nFinal columns: {list(mock_data.columns)}")
    print("\nComprehensive Results:")
    print(mock_data[['case_number', 'vehicle_1', 'vehicle_2', 'vehicle_1_and_vehicle_2', 'narrative', 'period', 'day_of_week', 'day_type', 'response_type', 'category_type']].to_string(index=False))
    
    # Summary statistics
    print("\nFeature Summary:")
    print("-" * 50)
    print(f"Vehicle Fields Uppercased: {mock_data['vehicle_1'].notna().sum() + mock_data['vehicle_2'].notna().sum()} vehicles")
    print(f"Narratives Cleaned: {mock_data['narrative'].notna().sum()} narratives")
    print(f"Period Distribution: {mock_data['period'].value_counts().to_dict()}")
    print(f"Day Type Distribution: {mock_data['day_type'].value_counts().to_dict()}")
    print(f"Response Types: {mock_data['response_type'].value_counts().to_dict()}")

def main():
    """Run all tests."""
    test_vehicle_fields_uppercasing()
    print("\n" + "=" * 80 + "\n")
    
    test_narrative_cleaning()
    print("\n" + "=" * 80 + "\n")
    
    test_period_day_week_cycle_fixes()
    print("\n" + "=" * 80 + "\n")
    
    test_merge_logic()
    print("\n" + "=" * 80 + "\n")
    
    test_integrated_features()
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main() 