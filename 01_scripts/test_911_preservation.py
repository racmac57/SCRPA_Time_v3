#!/usr/bin/env python3
"""
Test script for "9-1-1" Preservation in how_reported Column

This script demonstrates the implementation of preserving "9-1-1" as text in the how_reported column:
1. Use pd.read_excel(..., dtype={"How Reported": str}) to prevent Excel auto-parsing
2. Apply clean_how_reported_911() to normalize variants back to "9-1-1"

Examples from requirements:
| Raw "How Reported" | Imported Value (string) | After clean_how_reported_911 |
| ------------------ | ----------------------- | ------------------------------- |
| "9-1-1"           | "9-1-1"                 | "9-1-1"                        |
| "2001-09-01"      | "2001-09-01"            | "9-1-1"                        |
| "911"             | "911"                   | "9-1-1"                        |
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

def test_911_preservation():
    """Test the 9-1-1 preservation functionality."""
    
    print("=" * 60)
    print("9-1-1 PRESERVATION IN how_reported COLUMN TEST")
    print("=" * 60)
    
    # Initialize the processor
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Test cases from the requirements
    test_cases = [
        "9-1-1",
        "2001-09-01", 
        "911",
        "9/1/1",
        "09/01/2001",
        "2001-09-01 00:00:00",
        "9-1-1",
        "Other Method"
    ]
    
    print("\nTesting clean_how_reported_911 function:")
    print("-" * 50)
    
    for how_reported in test_cases:
        cleaned = processor.clean_how_reported_911(how_reported)
        print(f"Raw 'How Reported': '{how_reported}'")
        print(f"  → After clean_how_reported_911: '{cleaned}'")
        print()
    
    # Test with a mock Excel-like scenario
    print("\nTesting with Mock Excel Data:")
    print("-" * 50)
    
    # Create mock data that simulates what Excel might produce
    mock_data = {
        'ReportNumberNew': ['CAD-001', 'CAD-002', 'CAD-003', 'CAD-004', 'CAD-005'],
        'How Reported': ['9-1-1', '2001-09-01', '911', '9/1/1', 'Other Method'],
        'Incident': ['BURGLARY AUTO', 'medical assist', 'unknown code', 'TRAFFIC ACCIDENT', 'FIRE ALARM']
    }
    
    # Create DataFrame
    mock_df = pd.DataFrame(mock_data)
    print(f"Mock DataFrame created with {len(mock_df)} records")
    print(f"Original 'How Reported' values: {mock_df['How Reported'].tolist()}")
    
    # Apply the cleaning function
    mock_df['how_reported_cleaned'] = mock_df['How Reported'].apply(processor.clean_how_reported_911)
    
    print(f"\nAfter applying clean_how_reported_911:")
    print(mock_df[['How Reported', 'how_reported_cleaned']].to_string(index=False))
    
    # Validate against expected results
    print("\nValidation against Expected Results:")
    print("-" * 50)
    
    expected_results = {
        '9-1-1': '9-1-1',
        '2001-09-01': '9-1-1',
        '911': '9-1-1',
        '9/1/1': '9-1-1',
        'Other Method': 'Other Method'
    }
    
    for raw_value, expected_cleaned in expected_results.items():
        actual_cleaned = processor.clean_how_reported_911(raw_value)
        
        status = "✅ PASS" if actual_cleaned == expected_cleaned else "❌ FAIL"
        
        print(f"{status} '{raw_value}':")
        print(f"  Expected: '{expected_cleaned}'")
        print(f"  Actual:   '{actual_cleaned}'")
        print()
    
    # Test the dtype parameter simulation
    print("\nTesting dtype={'How Reported': str} Simulation:")
    print("-" * 50)
    
    # Simulate what happens when we use dtype={"How Reported": str}
    # This would prevent Excel from converting "9-1-1" to a date
    print("When using dtype={'How Reported': str} in pd.read_excel():")
    print("  - Excel will NOT auto-parse '9-1-1' as date")
    print("  - '9-1-1' will remain as string '9-1-1'")
    print("  - Date-like strings will be preserved as strings")
    print("  - clean_how_reported_911() will still normalize variants to '9-1-1'")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_911_preservation() 