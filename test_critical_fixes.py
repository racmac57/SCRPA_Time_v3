#!/usr/bin/env python3
"""
Test script to validate all critical v8.5 fixes are working correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '01_scripts'))

from SCRPA_Time_v3_Production_Pipeline import SCRPAProductionPipeline
import pandas as pd
from datetime import time

def test_critical_fixes():
    """Test all critical fixes implemented in v8.5 integration."""
    print("=== CRITICAL FIXES VALIDATION TEST ===")
    
    try:
        pipeline = SCRPAProductionPipeline()
        print("Pipeline initialized successfully")
        
        # Test 1: clean_how_reported_911 fix
        print("\n1. Testing clean_how_reported_911() fixes:")
        test_dates = ['2001-09-01', '2001-09-01 00:00:00', '9/1/2001', '2019-09-01', '911', '9-1-1']
        for date_val in test_dates:
            result = pipeline.clean_how_reported_911(date_val)
            status = "PASS" if result == "9-1-1" and date_val in ['2001-09-01', '2001-09-01 00:00:00', '9/1/2001', '2019-09-01'] else "PASS" if result == date_val else "FAIL"
            print(f"   {date_val} -> {result} [{status}]")
        
        # Test 2: extract_username_timestamp fix
        print("\n2. Testing extract_username_timestamp() fixes:")
        test_notes = [
            'SMITH123 7/29/2024 2:15:30 PM: Officer responded to scene',
            'JOHN.DOE 2024-07-29 14:15:30 Multiple units dispatched',
            'Simple note without username or timestamp'
        ]
        for note in test_notes:
            cleaned, username, timestamp = pipeline.extract_username_timestamp(note)
            print(f"   Original: {note}")
            print(f"   Cleaned: {cleaned}")
            print(f"   Username: {username}, Timestamp: {timestamp}")
            print()
        
        # Test 3: time_of_day encoding fix
        print("3. Testing time_of_day encoding fixes:")
        test_times = [time(8, 30), time(14, 45), time(22, 15)]
        for test_time in test_times:
            result = pipeline.get_time_of_day(test_time)
            has_encoding_issue = any(ord(c) > 127 for c in result)
            status = "FAIL" if has_encoding_issue else "PASS"
            print(f"   {test_time} -> {result} [{status}]")
        
        # Test 4: Column mappings
        print("\n4. Testing v8.5 column mappings:")
        cad_mapping = pipeline.get_cad_column_mapping()
        rms_mapping = pipeline.get_rms_column_mapping()
        
        incident_mapping_correct = cad_mapping.get("Incident") == "incident"
        print(f"   CAD Incident mapping: {cad_mapping.get('Incident')} [{'PASS' if incident_mapping_correct else 'FAIL'}]")
        print(f"   CAD columns mapped: {len(cad_mapping)}")
        print(f"   RMS columns mapped: {len(rms_mapping)}")
        
        # Test 5: Reference data loading
        print("\n5. Testing reference data loading:")
        print(f"   Call type reference: {'LOADED' if pipeline.call_type_ref is not None else 'NOT FOUND'}")
        print(f"   Zone/grid reference: {'LOADED' if pipeline.zone_grid_ref is not None else 'NOT FOUND'}")
        print(f"   Cycle calendar: {'LOADED' if pipeline.cycle_calendar is not None else 'NOT FOUND'}")
        
        print("\n=== ALL CRITICAL FIXES TESTED ===")
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_critical_fixes()
    if success:
        print("Test completed successfully!")
    else:
        print("Test failed!")
        sys.exit(1)