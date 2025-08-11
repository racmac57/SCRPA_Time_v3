#!/usr/bin/env python3
"""
Test various address scenarios for zone/grid backfill system
"""

import pandas as pd
from zone_grid_backfill_enhanced import ZoneGridBackfiller, AddressNormalizer, ZoneGridMatcher

def test_address_normalization():
    """Test address normalization functions"""
    print("=== TESTING ADDRESS NORMALIZATION ===")
    
    normalizer = AddressNormalizer()
    
    test_cases = [
        ("State Street & Banta Place", "State St / Banta Pl"),
        ("Summit Avenue", "Summit Ave"),
        ("FIRST   STREET", "First St"),
        ("Main St / Washington St", "Main St / Washington St"),
        ("North Elm Street", "N Elm St"),
        ("South Park Avenue", "S Park Ave")
    ]
    
    print("Address Normalization Tests:")
    for original, expected_pattern in test_cases:
        normalized = normalizer.normalize_street_name(original)
        intersection_slash, intersection_amp = normalizer.convert_intersection_format(original)
        
        print(f"Original: {original}")
        print(f"Normalized: {normalized}")
        print(f"Intersection formats: {intersection_slash} | {intersection_amp}")
        print()

def test_matching_strategies():
    """Test different matching strategies"""
    print("=== TESTING MATCHING STRATEGIES ===")
    
    # Load zone/grid data
    base_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
    backfiller = ZoneGridBackfiller(base_path)
    
    test_addresses = [
        "309 Lookout Avenue, Hackensack, NJ, 07601",  # Should match "Lookout Avenue"
        "First Street, Hackensack, NJ",  # Should match "First Street"
        "State St & Banta Pl",  # Should match intersection format
        "PROSPECT AVENUE",  # Case variation
        "Cedar Ave",  # Abbreviation variation
        "Main Street & Washington Street",  # Intersection with full names
        "Unknown Street, Hackensack, NJ",  # Should not match
        "River St",  # Abbreviation test
    ]
    
    print("Matching Strategy Tests:")
    for address in test_addresses:
        match_result = backfiller.matcher.match_address(address)
        print(f"Address: {address}")
        print(f"Match Type: {match_result.get('match_type')}")
        print(f"Grid: {match_result.get('grid')}, Zone: {match_result.get('zone')}")
        print(f"Confidence: {match_result.get('confidence', 0):.2f}")
        print(f"Matched Reference: {match_result.get('matched_reference', 'N/A')}")
        print()

def test_backfill_with_sample_data():
    """Test backfill with controlled sample data"""
    print("=== TESTING BACKFILL WITH SAMPLE DATA ===")
    
    # Create sample test data with missing Grid/Zone values
    test_data = pd.DataFrame({
        'address': [
            "309 Lookout Avenue, Hackensack, NJ, 07601",
            "135 First Street, Hackensack, NJ, 07601", 
            "State Street & Banta Place",
            "Unknown Avenue, Hackensack, NJ",
            "Cedar Avenue, Hackensack, NJ",
            "Main St / Washington St"
        ],
        'grid': [None, "G1", None, None, None, None],
        'zone': [None, None, None, None, "Zone2", None],
        'case_id': ['TEST001', 'TEST002', 'TEST003', 'TEST004', 'TEST005', 'TEST006']
    })
    
    base_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
    backfiller = ZoneGridBackfiller(base_path)
    
    print("Before Backfill:")
    print(f"Grid missing: {test_data['grid'].isna().sum()}/{len(test_data)}")
    print(f"Zone missing: {test_data['zone'].isna().sum()}/{len(test_data)}")
    print()
    
    # Perform backfill
    enhanced_data = backfiller.backfill_dataframe(
        test_data, 
        address_column='address',
        grid_column='grid',
        zone_column='zone'
    )
    
    print("After Backfill:")
    print(f"Grid missing: {enhanced_data['grid'].isna().sum()}/{len(enhanced_data)}")
    print(f"Zone missing: {enhanced_data['zone'].isna().sum()}/{len(enhanced_data)}")
    print()
    
    print("Detailed Results:")
    for _, row in enhanced_data.iterrows():
        print(f"Case: {row['case_id']}")
        print(f"Address: {row['address']}")
        print(f"Grid: {row['grid']}, Zone: {row['zone']}")
        print()
    
    # Get match statistics
    match_stats = backfiller.matcher.get_match_statistics()
    print("Match Statistics:")
    for key, value in match_stats.items():
        print(f"{key}: {value}")

def run_comprehensive_test():
    """Run all test scenarios"""
    print("STARTING COMPREHENSIVE ADDRESS BACKFILL TESTING")
    print("=" * 60)
    
    try:
        test_address_normalization()
        test_matching_strategies()
        test_backfill_with_sample_data()
        
        print("=" * 60)
        print("[SUCCESS] ALL TESTS COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        print(f"[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_comprehensive_test()