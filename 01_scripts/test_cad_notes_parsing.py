#!/usr/bin/env python3
"""
Test script for CAD Notes Parsing & Metadata Extraction

This script demonstrates the implementation of parse_cad_notes function:
1. Extract username patterns like kiselow_g, Gervasi_J, intake_fa
2. Extract timestamps and standardize to MM/DD/YYYY HH:MM:SS format
3. Clean out header, user, timestamp, stray date fragments, title-case the remainder

Examples from requirements:
| Raw CADNotes                                            | Username     | Timestamp             | Cleaned Text           |
| ------------------------------------------------------- | ------------ | --------------------- | ---------------------- |
| "kiselow_g 1/14/2025 3:47:59 PM Some note text"        | "kiselow_g"  | "01/14/2025 15:47:59" | "Some Note Text"       |
| "Gervasi_J - 02/20/2025 08:05:00 AM\nEvent details..." | "Gervasi_J"  | "02/20/2025 08:05:00" | "Event Details..."     |
| "intake_fa 3/3/2025 12:00:00 PM Additional info here"  | "intake_fa"  | "03/03/2025 12:00:00" | "Additional Info Here" |
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

def test_cad_notes_parsing():
    """Test the CAD notes parsing functionality."""
    
    print("=" * 60)
    print("CAD NOTES PARSING & METADATA EXTRACTION TEST")
    print("=" * 60)
    
    # Initialize the processor
    processor = ComprehensiveSCRPAFixV8_5()
    
    # Test cases from the requirements
    test_cases = [
        "kiselow_g 1/14/2025 3:47:59 PM Some note text",
        "Gervasi_J - 02/20/2025 08:05:00 AM\nEvent details...",
        "intake_fa 3/3/2025 12:00:00 PM Additional info here",
        "SMITH_J 12/25/2024 11:30:00 AM Traffic accident investigation",
        "jones_m 6/15/2025 2:15:30 PM Domestic disturbance call",
        "No username or timestamp - just plain text",
        "",  # Empty string
        None  # None value
    ]
    
    print("\nTesting parse_cad_notes function:")
    print("-" * 50)
    
    for i, raw_notes in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Raw CADNotes: '{raw_notes}'")
        
        # Apply the parse_cad_notes function
        result = processor.parse_cad_notes(raw_notes)
        
        print(f"  → Username: '{result['CAD_Username']}'")
        print(f"  → Timestamp: '{result['CAD_Timestamp']}'")
        print(f"  → Cleaned Text: '{result['CAD_Notes_Cleaned']}'")
    
    # Test with a mock CAD DataFrame
    print("\nTesting with Mock CAD DataFrame:")
    print("-" * 50)
    
    # Create mock CAD data
    mock_cad_data = pd.DataFrame({
        'case_number': ['CAD-001', 'CAD-002', 'CAD-003', 'CAD-004'],
        'cad_notes_raw': [
            "kiselow_g 1/14/2025 3:47:59 PM Some note text",
            "Gervasi_J - 02/20/2025 08:05:00 AM\nEvent details...",
            "intake_fa 3/3/2025 12:00:00 PM Additional info here",
            "No metadata - plain text only"
        ]
    })
    
    print(f"Mock CAD DataFrame created with {len(mock_cad_data)} records")
    print(f"Columns: {list(mock_cad_data.columns)}")
    
    # Apply the parsing function and extract results
    usernames = []
    timestamps = []
    cleaned_texts = []
    
    for raw_notes in mock_cad_data['cad_notes_raw']:
        result = processor.parse_cad_notes(raw_notes)
        usernames.append(result['CAD_Username'])
        timestamps.append(result['CAD_Timestamp'])
        cleaned_texts.append(result['CAD_Notes_Cleaned'])
    
    # Add the extracted columns
    mock_cad_data['cad_username'] = usernames
    mock_cad_data['cad_timestamp'] = timestamps
    mock_cad_data['cad_notes_cleaned'] = cleaned_texts
    
    print(f"\nFinal DataFrame columns: {list(mock_cad_data.columns)}")
    print("\nResults:")
    print(mock_cad_data[['cad_notes_raw', 'cad_username', 'cad_timestamp', 'cad_notes_cleaned']].to_string(index=False))
    
    # Validate against expected results
    print("\nValidation against Expected Results:")
    print("-" * 50)
    
    expected_results = {
        "kiselow_g 1/14/2025 3:47:59 PM Some note text": {
            'username': 'kiselow_g',
            'timestamp': '01/14/2025 15:47:59',
            'cleaned': 'Some Note Text'
        },
        "Gervasi_J - 02/20/2025 08:05:00 AM\nEvent details...": {
            'username': 'Gervasi_J',
            'timestamp': '02/20/2025 08:05:00',
            'cleaned': 'Event Details...'
        },
        "intake_fa 3/3/2025 12:00:00 PM Additional info here": {
            'username': 'intake_fa',
            'timestamp': '03/03/2025 12:00:00',
            'cleaned': 'Additional Info Here'
        }
    }
    
    for raw_notes, expected in expected_results.items():
        actual = processor.parse_cad_notes(raw_notes)
        
        username_match = actual['CAD_Username'] == expected['username']
        timestamp_match = actual['CAD_Timestamp'] == expected['timestamp']
        cleaned_match = actual['CAD_Notes_Cleaned'] == expected['cleaned']
        
        status = "✅ PASS" if username_match and timestamp_match and cleaned_match else "❌ FAIL"
        
        print(f"{status} '{raw_notes[:50]}...':")
        print(f"  Expected: username='{expected['username']}', timestamp='{expected['timestamp']}', cleaned='{expected['cleaned']}'")
        print(f"  Actual:   username='{actual['CAD_Username']}', timestamp='{actual['CAD_Timestamp']}', cleaned='{actual['CAD_Notes_Cleaned']}'")
        print()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_cad_notes_parsing() 