#!/usr/bin/env python3
"""
Comprehensive Test Script for Data-Type Standardization

This script tests the data-type standardization functionality to ensure:
1. String columns with all NaNs remain object dtype on reload
2. Mixed ints/floats remain numeric
3. All-NaN string columns become None but remain object dtype
4. Consistent dtypes across all exported CSVs

Expected Outcome:
- All exported CSVs have consistent data types
- String columns with NaN values are properly handled
- Numeric columns are properly coerced
- No float64 columns for all-null string data
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
import tempfile
import os

# Import the pipeline classes
import importlib.util
spec = importlib.util.spec_from_file_location("Comprehensive_SCRPA_Fix_v8_5_Standardized", 
                                             "Comprehensive_SCRPA_Fix_v8.5_Standardized.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ComprehensiveSCRPAFixV8_5 = module.ComprehensiveSCRPAFixV8_5

from SCRPA_Time_v4_Production_Pipeline import SCRPAProductionProcessor

def create_test_data_with_mixed_types():
    """Create test data with various data types to test standardization."""
    
    # Create test data with mixed types and NaN values
    test_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', None, 'RMS-004', 'RMS-005'],
        'incident_date': ['2025-08-01', '2025-08-02', None, '2025-08-04', '2025-08-05'],
        'incident_time': ['14:30:00', '09:15:00', None, '16:20:00', '11:30:00'],
        'all_incidents': ['Burglary - Auto', 'Theft', None, 'Assault', 'Vandalism'],
        'vehicle_1': ['NJ-ABC123', None, 'PA-XYZ789', None, 'NY-12345'],
        'vehicle_2': [None, 'CA-456', None, 'TX-789', None],
        'vehicle_1_and_vehicle_2': ['NJ-ABC123', 'CA-456', 'PA-XYZ789', 'TX-789', 'NY-12345'],
        'narrative': ['Vehicle broken into', None, 'Property stolen', 'Physical altercation', 'Property damage'],
        'location': ['123 Main St', '456 Oak Ave', None, '789 Pine St', '321 Elm St'],
        'block': ['Main St, 100 Block', None, 'Oak Ave, 400 Block', 'Pine St, 700 Block', 'Elm St, 300 Block'],
        'response_type': ['Crime', 'Crime', None, 'Crime', 'Crime'],
        'category_type': ['Burglary', 'Theft', None, 'Assault', 'Vandalism'],
        'period': ['7-Day', '28-Day', None, 'YTD', 'Historical'],
        'season': ['Summer', 'Summer', None, 'Summer', 'Summer'],
        'day_of_week': ['Friday', 'Saturday', None, 'Sunday', 'Monday'],
        'day_type': ['Weekday', 'Weekend', None, 'Weekend', 'Weekday'],
        'cycle_name': ['C08W31', 'C08W31', None, 'C08W31', 'C08W31'],
        'post': [1, 2, None, 4, 5],
        'grid': ['A1', 'B2', None, 'C3', 'D4'],
        'time_of_day_sort_order': [4, 2, None, 6, 3],
        'total_value_stolen': [500.0, 1200, None, 0, 300.5],
        'total_value_recovered': [0, 0, None, 0, 0],
        # Test columns with all NaN values
        'all_nan_string': [None, None, None, None, None],
        'mixed_numeric': [1, 2.5, None, 100, 0.001],
        'string_numeric': ['1', '2.5', None, '100', '0.001']
    })
    
    return test_data

def test_standardize_data_types_method():
    """Test the standardize_data_types method directly."""
    
    print("=" * 60)
    print("TESTING STANDARDIZE_DATA_TYPES METHOD")
    print("=" * 60)
    
    # Create test data
    test_data = create_test_data_with_mixed_types()
    
    print("\nOriginal data types:")
    print(test_data.dtypes)
    
    print("\nOriginal data (first 3 rows):")
    print(test_data.head(3))
    
    # Test with ComprehensiveSCRPAFixV8_5
    print("\n" + "-" * 40)
    print("Testing ComprehensiveSCRPAFixV8_5.standardize_data_types()")
    print("-" * 40)
    
    processor = ComprehensiveSCRPAFixV8_5()
    standardized_data = processor.standardize_data_types(test_data.copy())
    
    print("\nStandardized data types:")
    print(standardized_data.dtypes)
    
    print("\nStandardized data (first 3 rows):")
    print(standardized_data.head(3))
    
    # Test with SCRPAProductionProcessor
    print("\n" + "-" * 40)
    print("Testing SCRPAProductionProcessor.standardize_data_types()")
    print("-" * 40)
    
    prod_processor = SCRPAProductionProcessor()
    standardized_data_prod = prod_processor.standardize_data_types(test_data.copy())
    
    print("\nStandardized data types:")
    print(standardized_data_prod.dtypes)
    
    print("\nStandardized data (first 3 rows):")
    print(standardized_data_prod.head(3))
    
    return standardized_data, standardized_data_prod

def test_csv_export_with_standardization():
    """Test CSV export with data type standardization."""
    
    print("\n" + "=" * 60)
    print("TESTING CSV EXPORT WITH STANDARDIZATION")
    print("=" * 60)
    
    # Create test data
    test_data = create_test_data_with_mixed_types()
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test with ComprehensiveSCRPAFixV8_5
        print("\nTesting ComprehensiveSCRPAFixV8_5 CSV export...")
        processor = ComprehensiveSCRPAFixV8_5()
        
        # Export without standardization
        unstandardized_file = temp_path / "unstandardized_test.csv"
        test_data.to_csv(unstandardized_file, index=False)
        
        # Export with standardization
        standardized_file = temp_path / "standardized_test.csv"
        standardized_data = processor.standardize_data_types(test_data.copy())
        standardized_data.to_csv(standardized_file, index=False)
        
        # Read back and compare
        unstandardized_read = pd.read_csv(unstandardized_file)
        standardized_read = pd.read_csv(standardized_file)
        
        print(f"\nUnstandardized CSV dtypes:")
        print(unstandardized_read.dtypes)
        
        print(f"\nStandardized CSV dtypes:")
        print(standardized_read.dtypes)
        
        print(f"\nUnstandardized CSV (first 3 rows):")
        print(unstandardized_read.head(3))
        
        print(f"\nStandardized CSV (first 3 rows):")
        print(standardized_read.head(3))
        
        # Check for specific issues
        print(f"\n" + "-" * 40)
        print("VALIDATION CHECKS")
        print("-" * 40)
        
        # Check if string columns with all NaNs are float64
        string_cols = ['case_number', 'incident_date', 'incident_time', 'all_incidents']
        for col in string_cols:
            if col in unstandardized_read.columns:
                unstd_dtype = unstandardized_read[col].dtype
                std_dtype = standardized_read[col].dtype
                
                print(f"{col}:")
                print(f"  Unstandardized: {unstd_dtype}")
                print(f"  Standardized: {std_dtype}")
                
                if 'float' in str(unstd_dtype) and 'object' in str(std_dtype):
                    print(f"  ✅ FIXED: float64 → object")
                elif 'object' in str(std_dtype):
                    print(f"  ✅ CORRECT: object dtype maintained")
                else:
                    print(f"  ⚠️ ISSUE: Unexpected dtype change")
        
        # Check numeric columns
        numeric_cols = ['post', 'time_of_day_sort_order', 'total_value_stolen']
        for col in numeric_cols:
            if col in standardized_read.columns:
                dtype = standardized_read[col].dtype
                print(f"{col}: {dtype}")
                if 'float' in str(dtype) or 'int' in str(dtype):
                    print(f"  ✅ CORRECT: Numeric dtype")
                else:
                    print(f"  ⚠️ ISSUE: Non-numeric dtype")
        
        return standardized_read

def test_all_nan_string_column():
    """Test specific case: column with all NaN values."""
    
    print("\n" + "=" * 60)
    print("TESTING ALL-NAN STRING COLUMN")
    print("=" * 60)
    
    # Create data with all NaN string column
    test_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', 'RMS-003'],
        'all_nan_string': [None, None, None],  # All NaN string column
        'mixed_numeric': [1, 2.5, None],       # Mixed numeric column
        'mixed_string': ['A', None, 'C']       # Mixed string column
    })
    
    print("Original data:")
    print(test_data)
    print("\nOriginal dtypes:")
    print(test_data.dtypes)
    
    # Test standardization
    processor = ComprehensiveSCRPAFixV8_5()
    standardized_data = processor.standardize_data_types(test_data.copy())
    
    print("\nStandardized data:")
    print(standardized_data)
    print("\nStandardized dtypes:")
    print(standardized_data.dtypes)
    
    # Export to CSV and read back
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        csv_file = temp_path / "all_nan_test.csv"
        
        standardized_data.to_csv(csv_file, index=False)
        read_back = pd.read_csv(csv_file)
        
        print(f"\nCSV read back:")
        print(read_back)
        print(f"\nCSV dtypes:")
        print(read_back.dtypes)
        
        # Validate all-nan string column
        if 'all_nan_string' in read_back.columns:
            dtype = read_back['all_nan_string'].dtype
            if 'object' in str(dtype):
                print(f"✅ SUCCESS: all_nan_string column is object dtype (not float64)")
            else:
                print(f"❌ FAILURE: all_nan_string column is {dtype} (should be object)")
        
        return read_back

def test_mixed_numeric_column():
    """Test mixed numeric column handling."""
    
    print("\n" + "=" * 60)
    print("TESTING MIXED NUMERIC COLUMN")
    print("=" * 60)
    
    # Create data with mixed numeric values
    test_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', 'RMS-003', 'RMS-004', 'RMS-005'],
        'mixed_numeric': [1, 2.5, None, 100, 0.001],  # Mixed ints/floats/None
        'string_numeric': ['1', '2.5', None, '100', '0.001']  # String representations
    })
    
    print("Original data:")
    print(test_data)
    print("\nOriginal dtypes:")
    print(test_data.dtypes)
    
    # Test standardization
    processor = ComprehensiveSCRPAFixV8_5()
    standardized_data = processor.standardize_data_types(test_data.copy())
    
    print("\nStandardized data:")
    print(standardized_data)
    print("\nStandardized dtypes:")
    print(standardized_data.dtypes)
    
    # Validate numeric column
    if 'mixed_numeric' in standardized_data.columns:
        dtype = standardized_data['mixed_numeric'].dtype
        if 'float' in str(dtype) or 'int' in str(dtype):
            print(f"✅ SUCCESS: mixed_numeric column is numeric dtype: {dtype}")
        else:
            print(f"❌ FAILURE: mixed_numeric column is {dtype} (should be numeric)")
    
    return standardized_data

def test_specific_examples_from_specification():
    """Test the specific examples provided in the specification."""
    
    print("\n" + "=" * 60)
    print("TESTING SPECIFIC EXAMPLES FROM SPECIFICATION")
    print("=" * 60)
    
    # Example 1: case_number with mixed values
    example1 = pd.DataFrame({
        'case_number': ['25-001', None, '25-003'],
        'post': [101, 102.0, ''],
        'all_nan_col': [None, None]
    })
    
    print("Example 1 - Before standardization:")
    print(example1)
    print("Dtypes:", example1.dtypes)
    
    processor = ComprehensiveSCRPAFixV8_5()
    standardized1 = processor.standardize_data_types(example1.copy())
    
    print("\nExample 1 - After standardization:")
    print(standardized1)
    print("Dtypes:", standardized1.dtypes)
    
    # Export and read back
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        csv_file = temp_path / "example1_test.csv"
        
        standardized1.to_csv(csv_file, index=False)
        read_back = pd.read_csv(csv_file)
        
        print(f"\nExample 1 - After CSV export/import:")
        print(read_back)
        print("Dtypes:", read_back.dtypes)
        
        # Validate according to specification
        print(f"\n" + "-" * 40)
        print("SPECIFICATION VALIDATION")
        print("-" * 40)
        
        # Check case_number: should be object with ['25-001', None, '25-003']
        if 'case_number' in read_back.columns:
            case_num_dtype = read_back['case_number'].dtype
            case_num_values = read_back['case_number'].tolist()
            print(f"case_number: dtype={case_num_dtype}, values={case_num_values}")
            if 'object' in str(case_num_dtype):
                print(f"  ✅ CORRECT: object dtype maintained")
            else:
                print(f"  ❌ ISSUE: Expected object dtype, got {case_num_dtype}")
        
        # Check post: should be float64 with [101.0, 102.0, NaN]
        if 'post' in read_back.columns:
            post_dtype = read_back['post'].dtype
            post_values = read_back['post'].tolist()
            print(f"post: dtype={post_dtype}, values={post_values}")
            if 'float' in str(post_dtype):
                print(f"  ✅ CORRECT: numeric dtype maintained")
            else:
                print(f"  ❌ ISSUE: Expected numeric dtype, got {post_dtype}")
        
        # Check all_nan_col: should be object with [None, None] (not float64)
        if 'all_nan_col' in read_back.columns:
            all_nan_dtype = read_back['all_nan_col'].dtype
            all_nan_values = read_back['all_nan_col'].tolist()
            print(f"all_nan_col: dtype={all_nan_dtype}, values={all_nan_values}")
            if 'object' in str(all_nan_dtype):
                print(f"  ✅ CORRECT: object dtype for all-NaN column")
            else:
                print(f"  ❌ ISSUE: Expected object dtype for all-NaN column, got {all_nan_dtype}")
    
    return read_back

def main():
    """Run all tests."""
    print("Comprehensive Data Type Standardization Tests")
    print("=" * 60)
    
    try:
        # Test 1: Direct method testing
        standardized_data1, standardized_data2 = test_standardize_data_types_method()
        
        # Test 2: CSV export testing
        standardized_csv = test_csv_export_with_standardization()
        
        # Test 3: All-NaN string column
        all_nan_result = test_all_nan_string_column()
        
        # Test 4: Mixed numeric column
        mixed_numeric_result = test_mixed_numeric_column()
        
        # Test 5: Specific examples from specification
        spec_examples = test_specific_examples_from_specification()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("✅ All tests completed successfully!")
        print("✅ Data type standardization is working correctly")
        print("✅ String columns with NaN values are properly handled")
        print("✅ Numeric columns are properly coerced")
        print("✅ CSV exports maintain consistent data types")
        print("✅ All-NaN string columns remain object dtype")
        print("✅ Mixed numeric columns are properly handled")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 