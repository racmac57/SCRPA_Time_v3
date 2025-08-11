#!/usr/bin/env python3
"""
Test script for Time-of-Day Buckets & Sort Order, Block Calculation & Enhancement, and Combine all_incidents from Incident_Type Columns

This script demonstrates the implementation of three new features:
1. Time-of-Day Buckets & Sort Order: Define map_tod(t) buckets, apply to cleaned incident_time, convert to ordered categorical and generate time_of_day_sort_order
2. Block Calculation & Enhancement: Standardize input column to location, implement calculate_block(addr) handling intersections and numeric addresses
3. Combine all_incidents from Incident_Type Columns: Use cleaned columns, strip statute codes and join non-null entries

Examples from requirements:
| incident_time | time_of_day | sort_order |
| -------------- | --------------------------- | ----------- |
| 02:30:00 | "00:00–03:59 Early Morning" | 1 |
| 07:15:00 | "04:00–07:59 Morning" | 2 |
| 14:45:00 | "12:00–15:59 Afternoon" | 4 |

| location | block |
| ---------------------------------- | --------------------- |
| "123 Main St, Hackensack, NJ, ..." | "Main St, 100 Block" |
| "Broad St & Elm St" | "Broad St & Elm St" |
| "Xyz Rd" | "Check Location Data" |

| incident_type_1_cleaned | incident_type_2_cleaned | incident_type_3_cleaned | all_incidents |
| -------------------------- | -------------------------- | -------------------------- | ----------------- |
| "Burglary - Auto" | NaN | NaN | "Burglary - Auto" |
| "Theft" | "Robbery" | NaN | "Theft, Robbery" |
| NaN | NaN | NaN | "" (empty) |
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

def test_time_of_day_buckets():
    """Test the Time-of-Day Buckets & Sort Order functionality."""
    
    print("=" * 60)
    print("TIME-OF-DAY BUCKETS & SORT ORDER TEST")
    print("=" * 60)
    
    # Initialize the processor
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Test cases for time-of-day mapping
    print("\nTesting map_tod function:")
    print("-" * 50)
    
    time_test_cases = [
        ('02:30:00', "00:00-03:59 Early Morning"),
        ('07:15:00', "04:00-07:59 Morning"),
        ('10:45:00', "08:00-11:59 Morning Peak"),
        ('14:45:00', "12:00-15:59 Afternoon"),
        ('18:30:00', "16:00-19:59 Evening Peak"),
        ('22:15:00', "20:00-23:59 Night"),
        ('', "Unknown"),
        (None, "Unknown"),
        ('invalid', "Unknown")
    ]
    
    for time_val, expected in time_test_cases:
        result = processor.map_tod(time_val)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} '{time_val}' → '{result}' (expected: '{expected}')")
    
    # Test with ordered categorical data
    print("\nTesting Ordered Categorical Data:")
    print("-" * 50)
    
    # Define time-of-day buckets in order
    tod_order = [
        "00:00-03:59 Early Morning",
        "04:00-07:59 Morning", 
        "08:00-11:59 Morning Peak",
        "12:00-15:59 Afternoon",
        "16:00-19:59 Evening Peak",
        "20:00-23:59 Night",
        "Unknown"
    ]
    
    # Create test data
    test_times = ['02:30:00', '07:15:00', '14:45:00', '22:15:00', 'invalid']
    test_data = pd.DataFrame({'incident_time': test_times})
    
    # Apply map_tod function
    test_data['time_of_day'] = test_data['incident_time'].apply(processor.map_tod)
    
    # Convert to ordered categorical and generate sort order
    test_data['time_of_day'] = pd.Categorical(
        test_data['time_of_day'], 
        categories=tod_order, 
        ordered=True
    )
    test_data['time_of_day_sort_order'] = test_data['time_of_day'].cat.codes + 1
    
    print("\nResults:")
    print(test_data.to_string(index=False))
    
    # Validate sort order
    print("\nValidation against Expected Results:")
    print("-" * 50)
    
    expected_results = {
        '02:30:00': {'time_of_day': '00:00-03:59 Early Morning', 'sort_order': 1},
        '07:15:00': {'time_of_day': '04:00-07:59 Morning', 'sort_order': 2},
        '14:45:00': {'time_of_day': '12:00-15:59 Afternoon', 'sort_order': 4},
        '22:15:00': {'time_of_day': '20:00-23:59 Night', 'sort_order': 6},
        'invalid': {'time_of_day': 'Unknown', 'sort_order': 7}
    }
    
    for time_val, expected in expected_results.items():
        row = test_data[test_data['incident_time'] == time_val].iloc[0]
        
        time_of_day_match = row['time_of_day'] == expected['time_of_day']
        sort_order_match = row['time_of_day_sort_order'] == expected['sort_order']
        
        status = "✅ PASS" if time_of_day_match and sort_order_match else "❌ FAIL"
        
        print(f"{status} '{time_val}':")
        print(f"  Expected: time_of_day='{expected['time_of_day']}', sort_order={expected['sort_order']}")
        print(f"  Actual:   time_of_day='{row['time_of_day']}', sort_order={row['time_of_day_sort_order']}")
        print()

def test_block_calculation():
    """Test the Block Calculation & Enhancement functionality."""
    
    print("=" * 60)
    print("BLOCK CALCULATION & ENHANCEMENT TEST")
    print("=" * 60)
    
    # Initialize the processor
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Test cases for block calculation
    print("\nTesting calculate_block function:")
    print("-" * 50)
    
    block_test_cases = [
        ("123 Main St, Hackensack, NJ, 07601", "Main St, 100 Block"),
        ("Broad St & Elm St", "Broad St & Elm St"),
        ("Xyz Rd", "Check Location Data"),
        ("456 Oak Ave, Hackensack, NJ, 07601", "Oak Ave, 400 Block"),
        ("789 Pine St & Maple Ave", "Pine St & Maple Ave"),
        ("", "Check Location Data"),
        (None, "Check Location Data"),
        ("123", "Check Location Data"),
        ("Main St", "Check Location Data")
    ]
    
    for location, expected in block_test_cases:
        result = processor.calculate_block(location)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} '{location}' → '{result}' (expected: '{expected}')")
    
    # Test with mock RMS DataFrame
    print("\nTesting with Mock RMS DataFrame:")
    print("-" * 50)
    
    # Create mock RMS data
    mock_rms_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', 'RMS-003', 'RMS-004', 'RMS-005'],
        'full_address_raw': [
            "123 Main St, Hackensack, NJ, 07601",
            "Broad St & Elm St",
            "456 Oak Ave, Hackensack, NJ, 07601",
            "789 Pine St & Maple Ave",
            "Xyz Rd"
        ]
    })
    
    print(f"Mock RMS DataFrame created with {len(mock_rms_data)} records")
    print(f"Columns: {list(mock_rms_data.columns)}")
    
    # Apply address validation and block calculation
    mock_rms_data['location'] = mock_rms_data['full_address_raw'].apply(processor.validate_hackensack_address)
    mock_rms_data['block'] = mock_rms_data['location'].apply(processor.calculate_block)
    
    print(f"\nFinal DataFrame columns: {list(mock_rms_data.columns)}")
    print("\nResults:")
    print(mock_rms_data[['case_number', 'full_address_raw', 'location', 'block']].to_string(index=False))

def test_combine_all_incidents():
    """Test the Combine all_incidents from Incident_Type Columns functionality."""
    
    print("=" * 60)
    print("COMBINE ALL_INCIDENTS FROM INCIDENT_TYPE COLUMNS TEST")
    print("=" * 60)
    
    # Initialize the processor
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Test cases for incident type cleaning
    print("\nTesting clean_incident_type function:")
    print("-" * 50)
    
    incident_test_cases = [
        ("Burglary - Auto - 2C:18-2", "Burglary - Auto"),
        ("Theft - 2C:20-3", "Theft"),
        ("Robbery - 2C:15-1", "Robbery"),
        ("Simple Assault", "Simple Assault"),
        ("", None),
        (None, None)
    ]
    
    for incident_str, expected in incident_test_cases:
        result = processor.clean_incident_type(incident_str)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} '{incident_str}' → '{result}' (expected: '{expected}')")
    
    # Test with mock RMS DataFrame
    print("\nTesting with Mock RMS DataFrame:")
    print("-" * 50)
    
    # Create mock RMS data
    mock_rms_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', 'RMS-003', 'RMS-004'],
        'incident_type_1_raw': [
            "Burglary - Auto - 2C:18-2",
            "Theft - 2C:20-3",
            "Robbery - 2C:15-1",
            None
        ],
        'incident_type_2_raw': [
            None,
            "Robbery - 2C:15-1",
            None,
            "Simple Assault"
        ],
        'incident_type_3_raw': [
            None,
            None,
            "Simple Assault",
            None
        ]
    })
    
    print(f"Mock RMS DataFrame created with {len(mock_rms_data)} records")
    print(f"Columns: {list(mock_rms_data.columns)}")
    
    # Clean incident types
    for i in [1, 2, 3]:
        col_name = f'incident_type_{i}_raw'
        if col_name in mock_rms_data.columns:
            mock_rms_data[f'incident_type_{i}_cleaned'] = mock_rms_data[col_name].apply(processor.clean_incident_type)
    
    # Use incident_type_1_raw as primary incident type
    if 'incident_type_1_raw' in mock_rms_data.columns:
        mock_rms_data['incident_type'] = mock_rms_data['incident_type_1_raw'].apply(processor.clean_incident_type)
    else:
        mock_rms_data['incident_type'] = None
    
    # Combine all incidents
    def combine_incidents(row):
        incidents = []
        for i in [1, 2, 3]:
            cleaned_col = f'incident_type_{i}_cleaned'
            if cleaned_col in row and pd.notna(row[cleaned_col]):
                incidents.append(row[cleaned_col])
        return ", ".join(incidents) if incidents else None
    
    mock_rms_data['all_incidents'] = mock_rms_data.apply(combine_incidents, axis=1)
    
    print(f"\nFinal DataFrame columns: {list(mock_rms_data.columns)}")
    print("\nResults:")
    print(mock_rms_data[['case_number', 'incident_type_1_raw', 'incident_type_2_raw', 'incident_type_3_raw', 'all_incidents']].to_string(index=False))
    
    # Validate against expected results
    print("\nValidation against Expected Results:")
    print("-" * 50)
    
    expected_results = {
        'RMS-001': 'Burglary - Auto',
        'RMS-002': 'Theft, Robbery',
        'RMS-003': 'Robbery, Simple Assault',
        'RMS-004': 'Simple Assault'
    }
    
    for case_number, expected in expected_results.items():
        row = mock_rms_data[mock_rms_data['case_number'] == case_number].iloc[0]
        actual = row['all_incidents']
        
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        
        print(f"{status} {case_number}:")
        print(f"  Expected: '{expected}'")
        print(f"  Actual:   '{actual}'")
        print()

def test_integrated_features():
    """Test all three features together with a comprehensive mock dataset."""
    
    print("=" * 60)
    print("INTEGRATED FEATURES TEST")
    print("=" * 60)
    
    # Initialize the processor
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Create comprehensive mock RMS data
    mock_rms_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', 'RMS-003', 'RMS-004', 'RMS-005'],
        'incident_time': ['02:30:00', '07:15:00', '14:45:00', '22:15:00', 'invalid'],
        'full_address_raw': [
            "123 Main St, Hackensack, NJ, 07601",
            "Broad St & Elm St",
            "456 Oak Ave, Hackensack, NJ, 07601",
            "789 Pine St & Maple Ave",
            "Xyz Rd"
        ],
        'incident_type_1_raw': [
            "Burglary - Auto - 2C:18-2",
            "Theft - 2C:20-3",
            "Robbery - 2C:15-1",
            "Simple Assault",
            None
        ],
        'incident_type_2_raw': [
            None,
            "Robbery - 2C:15-1",
            None,
            None,
            "Theft - 2C:20-3"
        ],
        'incident_type_3_raw': [
            None,
            None,
            "Simple Assault",
            None,
            None
        ]
    })
    
    print(f"Comprehensive Mock RMS DataFrame created with {len(mock_rms_data)} records")
    print(f"Initial columns: {list(mock_rms_data.columns)}")
    
    # Apply all three features
    
    # 1. Time-of-Day Buckets & Sort Order
    tod_order = [
        "00:00-03:59 Early Morning",
        "04:00-07:59 Morning", 
        "08:00-11:59 Morning Peak",
        "12:00-15:59 Afternoon",
        "16:00-19:59 Evening Peak",
        "20:00-23:59 Night",
        "Unknown"
    ]
    
    mock_rms_data['time_of_day'] = mock_rms_data['incident_time'].apply(processor.map_tod)
    mock_rms_data['time_of_day'] = pd.Categorical(
        mock_rms_data['time_of_day'], 
        categories=tod_order, 
        ordered=True
    )
    mock_rms_data['time_of_day_sort_order'] = mock_rms_data['time_of_day'].cat.codes + 1
    
    # 2. Block Calculation & Enhancement
    mock_rms_data['location'] = mock_rms_data['full_address_raw'].apply(processor.validate_hackensack_address)
    mock_rms_data['block'] = mock_rms_data['location'].apply(processor.calculate_block)
    
    # 3. Combine all_incidents from Incident_Type Columns
    for i in [1, 2, 3]:
        col_name = f'incident_type_{i}_raw'
        if col_name in mock_rms_data.columns:
            mock_rms_data[f'incident_type_{i}_cleaned'] = mock_rms_data[col_name].apply(processor.clean_incident_type)
    
    if 'incident_type_1_raw' in mock_rms_data.columns:
        mock_rms_data['incident_type'] = mock_rms_data['incident_type_1_raw'].apply(processor.clean_incident_type)
    else:
        mock_rms_data['incident_type'] = None
    
    def combine_incidents(row):
        incidents = []
        for i in [1, 2, 3]:
            cleaned_col = f'incident_type_{i}_cleaned'
            if cleaned_col in row and pd.notna(row[cleaned_col]):
                incidents.append(row[cleaned_col])
        return ", ".join(incidents) if incidents else None
    
    mock_rms_data['all_incidents'] = mock_rms_data.apply(combine_incidents, axis=1)
    
    print(f"\nFinal DataFrame columns: {list(mock_rms_data.columns)}")
    print("\nComprehensive Results:")
    print(mock_rms_data[['case_number', 'incident_time', 'time_of_day', 'time_of_day_sort_order', 'block', 'all_incidents']].to_string(index=False))
    
    # Summary statistics
    print("\nFeature Summary:")
    print("-" * 50)
    print(f"Time-of-Day Distribution:")
    print(mock_rms_data['time_of_day'].value_counts().to_dict())
    print(f"\nBlock Distribution:")
    print(mock_rms_data['block'].value_counts().to_dict())
    print(f"\nAll Incidents Sample:")
    print(mock_rms_data['all_incidents'].value_counts().to_dict())

def main():
    """Run all tests."""
    test_time_of_day_buckets()
    print("\n" + "=" * 80 + "\n")
    
    test_block_calculation()
    print("\n" + "=" * 80 + "\n")
    
    test_combine_all_incidents()
    print("\n" + "=" * 80 + "\n")
    
    test_integrated_features()
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main() 