#!/usr/bin/env python3
"""
Test script for enhanced CAD incident mapping functionality.
This script tests the key components of the enhanced CAD processing.
"""

import pandas as pd
import sys
from pathlib import Path

# Add the current directory to the path to import the main script
sys.path.append(str(Path(__file__).parent))

from Comprehensive_SCRPA_Fix_v8_5_Standardized import ComprehensiveSCRPAFixV8_5

def test_enhanced_functionality():
    """Test the enhanced CAD incident mapping functionality."""
    print("🧪 Testing Enhanced CAD Incident Mapping Functionality")
    print("=" * 60)
    
    try:
        # Initialize the processor
        processor = ComprehensiveSCRPAFixV8_5()
        
        # Test 1: Reference file loading
        print("\n1. Testing reference file loading...")
        ref_lookup, ref_diagnostics = processor.load_call_type_reference_enhanced()
        
        if ref_diagnostics['loaded']:
            print(f"✅ Reference file loaded successfully")
            print(f"   - Total records: {ref_diagnostics['total_records']}")
            print(f"   - Unique incidents: {ref_diagnostics['unique_incidents']}")
            print(f"   - Duplicates removed: {ref_diagnostics['duplicate_count']}")
        else:
            print(f"❌ Reference file loading failed: {ref_diagnostics['error']}")
            return False
        
        # Test 2: Incident mapping
        print("\n2. Testing incident mapping...")
        test_incidents = [
            "TRAFFIC ACCIDENT",
            "BURGLARY ALARM",
            "MEDICAL EMERGENCY",
            "UNKNOWN INCIDENT TYPE",
            None,
            ""
        ]
        
        response_types, category_types, mapping_diagnostics = processor.map_incident_to_call_types_enhanced(
            pd.Series(test_incidents), ref_lookup
        )
        
        print(f"✅ Incident mapping test completed")
        print(f"   - Total incidents: {mapping_diagnostics['total_incidents']}")
        print(f"   - Mapped incidents: {mapping_diagnostics['mapped_count']}")
        print(f"   - Unmapped incidents: {mapping_diagnostics['unmapped_count']}")
        print(f"   - Mapping rate: {mapping_diagnostics['mapping_rate']:.1f}%")
        
        # Test 3: Header validation
        print("\n3. Testing header validation...")
        test_df = pd.DataFrame({
            'case_number': [1, 2, 3],
            'incident': ['test1', 'test2', 'test3'],
            'response_type_cad': ['type1', 'type2', 'type3'],
            'category_type_cad': ['cat1', 'cat2', 'cat3']
        })
        
        validation_results = processor.validate_lowercase_snake_case_headers(test_df, "Test Data")
        
        if validation_results['overall_status'] == 'PASS':
            print(f"✅ Header validation PASSED")
        else:
            print(f"❌ Header validation FAILED")
            print(f"   - Non-compliant columns: {validation_results['non_compliant_columns']}")
        
        # Test 4: Unmapped incidents CSV creation
        print("\n4. Testing unmapped incidents CSV creation...")
        test_output_dir = Path(__file__).parent / 'test_output'
        test_output_dir.mkdir(exist_ok=True)
        
        unmapped_csv_path = processor.create_unmapped_incidents_csv(
            ['UNKNOWN1', 'UNKNOWN2', 'UNKNOWN3'], test_output_dir
        )
        
        if unmapped_csv_path:
            print(f"✅ Unmapped incidents CSV created: {unmapped_csv_path}")
        else:
            print(f"❌ Failed to create unmapped incidents CSV")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_column_mapping():
    """Test the CAD column mapping functionality."""
    print("\n🔧 Testing CAD Column Mapping")
    print("-" * 40)
    
    try:
        processor = ComprehensiveSCRPAFixV8_5()
        
        # Test the column mapping
        column_mapping = processor.get_cad_column_mapping()
        
        # Check that "Incident" maps to "incident"
        if column_mapping.get("Incident") == "incident":
            print("✅ CAD column mapping correctly maps 'Incident' to 'incident'")
        else:
            print(f"❌ CAD column mapping incorrect: 'Incident' maps to '{column_mapping.get('Incident')}'")
            return False
        
        # Test header conversion
        test_headers = ["Incident", "Response Type", "Category Type", "How Reported"]
        converted_headers = [processor.convert_to_lowercase_with_underscores(h) for h in test_headers]
        
        expected_headers = ["incident", "response_type", "category_type", "how_reported"]
        
        if converted_headers == expected_headers:
            print("✅ Header conversion working correctly")
        else:
            print(f"❌ Header conversion failed")
            print(f"   Expected: {expected_headers}")
            print(f"   Got: {converted_headers}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Column mapping test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Enhanced CAD Incident Mapping Tests")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_column_mapping()
    test2_passed = test_enhanced_functionality()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Column Mapping Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Enhanced Functionality Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! Enhanced CAD incident mapping is ready for production.")
    else:
        print("\n⚠️ Some tests failed. Please review the errors above.")
    
    print("\n📝 Next Steps:")
    print("1. Run the main script: python Comprehensive_SCRPA_Fix_v8.5_Standardized.py")
    print("2. Check the generated QC reports")
    print("3. Verify the output CSV files have correct headers and data") 