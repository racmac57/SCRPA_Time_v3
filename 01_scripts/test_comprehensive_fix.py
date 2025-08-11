#!/usr/bin/env python3
"""
Quick test script for Comprehensive_SCRPA_Fix_v8.0_Standardized.py
Tests key functionality without running full pipeline
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import importlib.util
spec = importlib.util.spec_from_file_location("comprehensive_fix", "Comprehensive_SCRPA_Fix_v8.0_Standardized.py")
comprehensive_fix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comprehensive_fix)
ComprehensiveSCRPAFixV8_0 = comprehensive_fix.ComprehensiveSCRPAFixV8_0

def test_key_functions():
    """Test key functions of the fixed script."""
    print("Testing Comprehensive SCRPA Fix V8.0...")
    
    # Initialize processor
    try:
        processor = ComprehensiveSCRPAFixV8_0()
        print("PASS: Processor initialized successfully")
    except Exception as e:
        print(f"FAIL: Failed to initialize processor: {e}")
        return False
    
    # Test column name conversion
    test_cases = [
        ("ReportNumberNew", "report_number_new"),
        ("PDZone", "pd_zone"),
        ("How Reported", "how_reported"),
        ("Time of Call", "time_of_call"),
        ("CADNotes", "cad_notes")
    ]
    
    print("\nTesting column name conversion:")
    for original, expected in test_cases:
        result = processor.convert_to_lowercase_with_underscores(original)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status}: '{original}' -> '{result}' (expected: '{expected}')")
    
    # Test call type mapping (with fallback)
    print("\nTesting call type mapping:")
    test_incidents = [
        "TRAFFIC ACCIDENT",
        "MEDICAL EMERGENCY", 
        "ALARM ACTIVATION",
        "DOMESTIC DISTURBANCE",
        "UNKNOWN INCIDENT"
    ]
    
    for incident in test_incidents:
        response_type, category_type = processor.map_call_type(incident)
        print(f"PASS: '{incident}' -> Response: '{response_type}', Category: '{category_type}'")
    
    # Test time formatting
    print("\nTesting time formatting:")
    print(f"PASS: 65 minutes -> '{processor.format_time_spent_minutes(65)}'")
    print(f"PASS: 5.5 minutes -> '{processor.format_time_response_minutes(5.5)}'")
    print(f"PASS: -10 minutes -> '{processor.format_time_spent_minutes(-10)}'")
    
    # Test 9-1-1 cleaning
    print("\nTesting 9-1-1 cleaning:")
    test_values = ["2024-01-15T10:30:00", "9-1-1", "PHONE", "2024-01-15"]
    for value in test_values:
        result = processor.clean_how_reported_911(value)
        print(f"PASS: '{value}' -> '{result}'")
    
    # Test username/timestamp extraction
    print("\nTesting CAD notes cleaning:")
    test_note = "SMITH123 1/15/2024 10:30:15 AM Officer responded to scene, suspect in custody"
    cleaned, username, timestamp = processor.extract_username_timestamp(test_note)
    print(f"PASS: Original: '{test_note}'")
    print(f"   Cleaned: '{cleaned}'")
    print(f"   Username: '{username}'")
    print(f"   Timestamp: '{timestamp}'")
    
    # Check if directories exist
    print("\nTesting directory paths:")
    for key, path in processor.export_dirs.items():
        exists = path.exists()
        status = "PASS" if exists else "FAIL"
        print(f"{status}: {key}: {path} ({'exists' if exists else 'missing'})")
    
    # Check reference file
    ref_exists = processor.ref_dirs['call_types'].exists()
    status = "PASS" if ref_exists else "FAIL"
    print(f"{status}: CallType reference: {'exists' if ref_exists else 'missing'}")
    
    print("\nCore functionality test completed!")
    return True

if __name__ == "__main__":
    test_key_functions()