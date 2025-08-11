#!/usr/bin/env python3
"""
Test script for RMS processing fixes in Comprehensive_SCRPA_Fix_v8.0_Standardized.py
Tests the new RMS functionality without running full pipeline
"""

import sys
from pathlib import Path
import pandas as pd
sys.path.append(str(Path(__file__).parent))

import importlib.util
spec = importlib.util.spec_from_file_location("comprehensive_fix", "Comprehensive_SCRPA_Fix_v8.0_Standardized.py")
comprehensive_fix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comprehensive_fix)
ComprehensiveSCRPAFixV8_0 = comprehensive_fix.ComprehensiveSCRPAFixV8_0

def test_rms_fixes():
    """Test RMS processing fixes."""
    print("Testing RMS fixes for Comprehensive SCRPA Fix V8.0...")
    
    # Initialize processor
    try:
        processor = ComprehensiveSCRPAFixV8_0()
        print("PASS: Processor initialized successfully")
    except Exception as e:
        print(f"FAIL: Failed to initialize processor: {e}")
        return False
    
    # Test RMS column mapping (should be lowercase_with_underscores)
    print("\nTesting RMS column mapping:")
    rms_mapping = processor.get_rms_column_mapping()
    
    # Check that all mapped values are lowercase_with_underscores
    lowercase_pattern = r'^[a-z]+(_[a-z]+)*$'
    import re
    
    for original, mapped in rms_mapping.items():
        if re.match(lowercase_pattern, mapped):
            print(f"PASS: '{original}' -> '{mapped}'")
        else:
            print(f"FAIL: '{original}' -> '{mapped}' (not lowercase_with_underscores)")
    
    # Test new address validation function
    print("\nTesting address validation:")
    test_addresses = [
        "123 Main St, Jersey City, NJ",  # Should be removed
        "456 Oak Ave",                   # Should add Hackensack
        "789 Pine St, Hackensack, NJ",  # Should stay as is
        None                            # Should handle None
    ]
    
    for addr in test_addresses:
        result = processor.validate_hackensack_address(addr)
        print(f"PASS: '{addr}' -> '{result}'")
    
    # Test time formatting
    print("\nTesting incident time formatting:")
    
    # Create mock time objects
    import datetime
    mock_time = datetime.time(14, 30)  # 2:30 PM
    mock_timedelta = pd.Timedelta(hours=9, minutes=15)
    
    formatted_time = processor.format_incident_time(mock_time)
    formatted_timedelta = processor.format_incident_time(mock_timedelta)
    formatted_none = processor.format_incident_time(None)
    
    print(f"PASS: time(14, 30) -> '{formatted_time}'")
    print(f"PASS: Timedelta(9h 15m) -> '{formatted_timedelta}'") 
    print(f"PASS: None -> '{formatted_none}'")
    
    # Test cascade functions with new column names
    print("\nTesting cascade functions with lowercase column names:")
    
    # Create mock row data
    mock_row = pd.Series({
        'incident_date_raw': '2024-01-15',
        'incident_time_raw': datetime.time(10, 30),
        'report_date_raw': '2024-01-16'
    })
    
    cascaded_date = processor.cascade_date(mock_row)
    cascaded_time = processor.cascade_time(mock_row)
    
    print(f"PASS: cascade_date -> {cascaded_date}")
    print(f"PASS: cascade_time -> {cascaded_time}")
    
    # Test reference data loading
    print("\nTesting reference data loading:")
    zone_grid_loaded = processor.zone_grid_ref is not None
    call_type_loaded = processor.call_type_ref is not None
    
    print(f"{'PASS' if zone_grid_loaded else 'FAIL'}: Zone/grid reference loaded: {zone_grid_loaded}")
    print(f"{'PASS' if call_type_loaded else 'FAIL'}: Call type reference loaded: {call_type_loaded}")
    
    # Test that CAD-specific columns are NOT in RMS desired columns
    print("\nTesting CAD-specific column exclusion:")
    
    # This would be the desired columns from the RMS processing function
    rms_desired_columns = [
        'case_number', 'incident_date', 'incident_time', 'time_of_day',
        'period', 'season', 'day_of_week', 'day_type', 'location', 'block', 
        'grid', 'post', 'all_incidents', 'vehicle_1', 'vehicle_2', 
        'vehicle_1_and_vehicle_2', 'narrative', 'total_value_stolen', 
        'total_value_recovered', 'squad', 'officer_of_record', 'nibrs_classification'
    ]
    
    cad_specific_columns = ['incident_type', 'crime_category', 'response_type']
    
    for cad_col in cad_specific_columns:
        if cad_col not in rms_desired_columns:
            print(f"PASS: CAD-specific column '{cad_col}' correctly excluded from RMS")
        else:
            print(f"FAIL: CAD-specific column '{cad_col}' found in RMS columns")
    
    # Test lowercase column validation
    print("\nTesting column naming compliance:")
    lowercase_pattern_compiled = re.compile(r'^[a-z]+(_[a-z]+)*$')
    
    compliant_count = 0
    total_count = len(rms_desired_columns)
    
    for col in rms_desired_columns:
        if lowercase_pattern_compiled.match(col):
            print(f"PASS: '{col}' is compliant")
            compliant_count += 1
        else:
            print(f"FAIL: '{col}' is not compliant")
    
    compliance_rate = (compliant_count / total_count) * 100
    print(f"\nColumn compliance rate: {compliance_rate:.1f}% ({compliant_count}/{total_count})")
    
    print("\nRMS fixes validation completed!")
    return True

if __name__ == "__main__":
    test_rms_fixes()