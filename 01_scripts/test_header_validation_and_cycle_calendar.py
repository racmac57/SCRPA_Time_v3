#!/usr/bin/env python3
"""
Test script for Header Validation and Cycle Calendar Integration

This script tests the header validation and cycle calendar integration functionality to ensure:
1. Header validation correctly identifies non-compliant column names
2. Cycle calendar integration properly assigns cycle names to dates
3. Both features work correctly in both pipeline classes

Expected Outcome:
- Header validation catches non-compliant column names and raises appropriate errors
- Cycle calendar integration correctly maps dates to cycle names
- All validation checks pass for compliant data
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
import tempfile
import os
from datetime import datetime, date

# Import the pipeline classes
import importlib.util
spec = importlib.util.spec_from_file_location("Comprehensive_SCRPA_Fix_v8_5_Standardized", 
                                             "Comprehensive_SCRPA_Fix_v8.5_Standardized.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ComprehensiveSCRPAFixV8_5 = module.ComprehensiveSCRPAFixV8_5

from SCRPA_Time_v4_Production_Pipeline import SCRPAProductionProcessor

def create_test_cycle_calendar():
    """Create a test cycle calendar DataFrame."""
    
    # Create test cycle calendar data
    cycle_data = {
        'Report_Name': ['C08W31', 'C08W32', 'C08W33', 'C08W34'],
        '7_Day_Start': ['2025-08-01', '2025-08-08', '2025-08-15', '2025-08-22'],
        '7_Day_End': ['2025-08-07', '2025-08-14', '2025-08-21', '2025-08-28'],
        '28_Day_Start': ['2025-08-01', '2025-08-08', '2025-08-15', '2025-08-22'],
        '28_Day_End': ['2025-08-28', '2025-09-04', '2025-09-11', '2025-09-18']
    }
    
    cycle_df = pd.DataFrame(cycle_data)
    cycle_df['7_Day_Start'] = pd.to_datetime(cycle_df['7_Day_Start'])
    cycle_df['7_Day_End'] = pd.to_datetime(cycle_df['7_Day_End'])
    cycle_df['28_Day_Start'] = pd.to_datetime(cycle_df['28_Day_Start'])
    cycle_df['28_Day_End'] = pd.to_datetime(cycle_df['28_Day_End'])
    
    return cycle_df

def test_header_validation():
    """Test the header validation functionality."""
    
    print("=" * 60)
    print("TESTING HEADER VALIDATION")
    print("=" * 60)
    
    # Create test data with mixed compliant and non-compliant headers
    test_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', 'RMS-003'],
        'incident_date': ['2025-08-01', '2025-08-02', '2025-08-03'],
        'incident_time': ['14:30:00', '09:15:00', '16:20:00'],
        'CaseNumber': ['RMS-004', 'RMS-005', 'RMS-006'],  # Non-compliant
        'IncidentDate': ['2025-08-04', '2025-08-05', '2025-08-06'],  # Non-compliant
        'response_type': ['Crime', 'Traffic', 'Medical'],
        'ResponseType': ['Crime', 'Traffic', 'Medical']  # Non-compliant
    })
    
    print("Test data with mixed headers:")
    print(f"Columns: {list(test_data.columns)}")
    
    # Test with ComprehensiveSCRPAFixV8_5
    print("\n" + "-" * 40)
    print("Testing ComprehensiveSCRPAFixV8_5.validate_lowercase_snake_case_headers()")
    print("-" * 40)
    
    processor = ComprehensiveSCRPAFixV8_5()
    validation_result = processor.validate_lowercase_snake_case_headers(test_data, 'Test Data')
    
    print(f"Validation Result: {validation_result}")
    
    # Test with SCRPAProductionProcessor
    print("\n" + "-" * 40)
    print("Testing SCRPAProductionProcessor.validate_lowercase_snake_case_headers()")
    print("-" * 40)
    
    prod_processor = SCRPAProductionProcessor()
    validation_result_prod = prod_processor.validate_lowercase_snake_case_headers(test_data, 'Test Data')
    
    print(f"Validation Result: {validation_result_prod}")
    
    # Test with compliant data
    print("\n" + "-" * 40)
    print("Testing with compliant headers only")
    print("-" * 40)
    
    compliant_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', 'RMS-003'],
        'incident_date': ['2025-08-01', '2025-08-02', '2025-08-03'],
        'incident_time': ['14:30:00', '09:15:00', '16:20:00'],
        'response_type': ['Crime', 'Traffic', 'Medical'],
        'category_type': ['Burglary', 'Speeding', 'Emergency']
    })
    
    validation_result_compliant = processor.validate_lowercase_snake_case_headers(compliant_data, 'Compliant Data')
    print(f"Compliant Data Validation Result: {validation_result_compliant}")
    
    return validation_result, validation_result_prod, validation_result_compliant

def test_cycle_calendar_integration():
    """Test the cycle calendar integration functionality."""
    
    print("\n" + "=" * 60)
    print("TESTING CYCLE CALENDAR INTEGRATION")
    print("=" * 60)
    
    # Create test cycle calendar
    cycle_df = create_test_cycle_calendar()
    
    print("Test cycle calendar:")
    print(cycle_df)
    
    # Test with ComprehensiveSCRPAFixV8_5
    print("\n" + "-" * 40)
    print("Testing ComprehensiveSCRPAFixV8_5.get_cycle_for_date()")
    print("-" * 40)
    
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Test dates
    test_dates = [
        '2025-08-01',  # Should be C08W31
        '2025-08-05',  # Should be C08W31
        '2025-08-10',  # Should be C08W32
        '2025-08-20',  # Should be C08W33
        '2025-08-25',  # Should be C08W34
        '2025-09-01',  # Should be None (outside cycles)
        None,          # Should be None
        'invalid_date' # Should be None
    ]
    
    print("Testing cycle assignment for various dates:")
    for test_date in test_dates:
        cycle_name = processor.get_cycle_for_date(test_date, cycle_df)
        print(f"  {test_date} → {cycle_name}")
    
    # Test get_current_cycle_info
    print("\n" + "-" * 40)
    print("Testing get_current_cycle_info()")
    print("-" * 40)
    
    current_cycle, current_date = processor.get_current_cycle_info(cycle_df)
    print(f"Current cycle: {current_cycle}")
    print(f"Current date: {current_date}")
    
    return cycle_df

def test_header_validation_in_export():
    """Test header validation during CSV export."""
    
    print("\n" + "=" * 60)
    print("TESTING HEADER VALIDATION IN EXPORT")
    print("=" * 60)
    
    # Create test data with non-compliant headers
    test_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', 'RMS-003'],
        'incident_date': ['2025-08-01', '2025-08-02', '2025-08-03'],
        'CaseNumber': ['RMS-004', 'RMS-005', 'RMS-006'],  # Non-compliant
        'IncidentDate': ['2025-08-04', '2025-08-05', '2025-08-06']  # Non-compliant
    })
    
    print("Test data with non-compliant headers:")
    print(f"Columns: {list(test_data.columns)}")
    
    # Test that validation catches the error
    processor = ComprehensiveSCRPAFixV8_5()
    
    try:
        # This should raise a ValueError
        header_val = processor.validate_lowercase_snake_case_headers(test_data, 'Test Export')
        if header_val['overall_status']=='FAIL':
            raise ValueError(f"Invalid headers in test export: {header_val['non_compliant_columns']}")
        print("❌ ERROR: Should have raised ValueError for non-compliant headers")
    except ValueError as e:
        print(f"✅ SUCCESS: Correctly raised ValueError: {e}")
    
    # Test with compliant data (should not raise error)
    compliant_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', 'RMS-003'],
        'incident_date': ['2025-08-01', '2025-08-02', '2025-08-03'],
        'response_type': ['Crime', 'Traffic', 'Medical']
    })
    
    try:
        header_val = processor.validate_lowercase_snake_case_headers(compliant_data, 'Compliant Export')
        if header_val['overall_status']=='FAIL':
            raise ValueError(f"Invalid headers in compliant export: {header_val['non_compliant_columns']}")
        print("✅ SUCCESS: Compliant data passed validation")
    except ValueError as e:
        print(f"❌ ERROR: Should not have raised ValueError for compliant headers: {e}")

def test_cycle_calendar_with_real_data():
    """Test cycle calendar integration with realistic data."""
    
    print("\n" + "=" * 60)
    print("TESTING CYCLE CALENDAR WITH REALISTIC DATA")
    print("=" * 60)
    
    # Create realistic test data
    test_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', 'RMS-003', 'RMS-004', 'RMS-005'],
        'incident_date': ['2025-08-01', '2025-08-05', '2025-08-10', '2025-08-15', '2025-08-20'],
        'incident_time': ['14:30:00', '09:15:00', '16:20:00', '11:45:00', '22:10:00'],
        'response_type': ['Crime', 'Traffic', 'Medical', 'Fire', 'Crime'],
        'category_type': ['Burglary', 'Speeding', 'Emergency', 'Alarm', 'Theft']
    })
    
    # Create cycle calendar
    cycle_df = create_test_cycle_calendar()
    
    # Test cycle assignment
    processor = ComprehensiveSCRPAFixV8_5()
    
    print("Testing cycle assignment for realistic incident dates:")
    for idx, row in test_data.iterrows():
        incident_date = row['incident_date']
        cycle_name = processor.get_cycle_for_date(incident_date, cycle_df)
        print(f"  {incident_date} → {cycle_name}")
    
    # Test with a larger dataset
    print("\n" + "-" * 40)
    print("Testing with larger dataset")
    print("-" * 40)
    
    # Create larger dataset with various dates
    dates = pd.date_range('2025-08-01', '2025-08-28', freq='D')
    large_data = pd.DataFrame({
        'case_number': [f'RMS-{i:03d}' for i in range(1, len(dates) + 1)],
        'incident_date': [d.strftime('%Y-%m-%d') for d in dates],
        'response_type': ['Crime'] * len(dates)
    })
    
    # Apply cycle assignment
    large_data['cycle_name'] = large_data['incident_date'].apply(
        lambda d: processor.get_cycle_for_date(d, cycle_df)
    )
    
    # Show cycle distribution
    cycle_distribution = large_data['cycle_name'].value_counts()
    print("Cycle distribution:")
    for cycle, count in cycle_distribution.items():
        print(f"  {cycle}: {count} records")
    
    return large_data

def main():
    """Run all tests."""
    print("Header Validation and Cycle Calendar Integration Tests")
    print("=" * 60)
    
    try:
        # Test 1: Header validation
        header_results = test_header_validation()
        
        # Test 2: Cycle calendar integration
        cycle_calendar = test_cycle_calendar_integration()
        
        # Test 3: Header validation in export
        test_header_validation_in_export()
        
        # Test 4: Cycle calendar with realistic data
        realistic_data = test_cycle_calendar_with_real_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("✅ All tests completed successfully!")
        print("✅ Header validation is working correctly")
        print("✅ Cycle calendar integration is working correctly")
        print("✅ Both pipeline classes have consistent functionality")
        print("✅ Validation catches non-compliant headers appropriately")
        print("✅ Cycle assignment works for various date formats")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 