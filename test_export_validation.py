"""
Test script for the comprehensive export consistency validation system
"""
import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime

def test_export_validation():
    """Test the comprehensive export validation system with existing CSV files"""
    
    print("=== Testing Comprehensive Export Consistency Validation ===")
    
    # Find existing CSV files to test
    output_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi")
    csv_files = list(output_dir.glob("*.csv"))
    
    if not csv_files:
        print("No CSV files found for testing")
        return
    
    print(f"Found {len(csv_files)} CSV files for validation:")
    for file in csv_files:
        print(f"  - {file.name}")
    
    # Create a standalone version of the validation functions for testing
    def validate_powerbi_readiness(file_path):
        """Standalone version of validate_powerbi_readiness for testing"""
        issues = []
        
        try:
            df = pd.read_csv(file_path)
            
            # Check for problematic characters in headers
            for col in df.columns:
                if any(char in col for char in [' ', '-', '.', '(', ')', '[', ']', '!', '@', '#', '%', '^', '&', '*']):
                    issues.append(f"Header contains special characters: '{col}' (use lowercase_snake_case)")
            
            # Check for extremely long column names (Power BI limit ~128 chars)
            for col in df.columns:
                if len(col) > 100:
                    issues.append(f"Column name too long: '{col}' ({len(col)} chars, recommend <100)")
            
            # Check for reserved words or problematic column names
            reserved_words = ['date', 'time', 'year', 'month', 'day', 'table', 'column', 'row', 'value', 'index']
            for col in df.columns:
                if col.lower() in reserved_words:
                    issues.append(f"Column name may conflict with Power BI reserved word: '{col}'")
            
            # Check for mixed data types that cause Power BI issues
            for col in df.columns:
                if df[col].dtype == 'object' and len(df) > 0:
                    # Sample values to check for mixed types
                    non_null_values = df[col].dropna().head(50)
                    if len(non_null_values) > 0:
                        numeric_count = 0
                        string_count = 0
                        
                        for val in non_null_values:
                            try:
                                float(str(val))
                                numeric_count += 1
                            except:
                                string_count += 1
                        
                        # If we have both numeric and string values, flag as potential issue
                        if numeric_count > 0 and string_count > 0:
                            ratio = min(numeric_count, string_count) / max(numeric_count, string_count)
                            if ratio > 0.1:  # More than 10% minority type
                                issues.append(f"Column '{col}' has mixed numeric/string values (may cause import issues)")
            
            # Check for extremely wide tables (Power BI performs better with <100 columns)
            if len(df.columns) > 100:
                issues.append(f"Table very wide ({len(df.columns)} columns, consider splitting or reducing)")
            
            # Check for extremely large files (>100MB can be slow in Power BI)
            file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            if file_size_mb > 100:
                issues.append(f"Large file size ({file_size_mb:.1f}MB, may impact Power BI performance)")
            
            # Check for completely empty columns
            empty_columns = [col for col in df.columns if df[col].isna().all()]
            if empty_columns:
                issues.append(f"Completely empty columns found: {', '.join(empty_columns[:5])}")
            
        except Exception as e:
            issues.append(f"Error reading file for Power BI validation: {e}")
        
        return issues

    def validate_lowercase_snake_case_headers(df, file_name):
        """Standalone version for testing"""
        lowercase_pattern = re.compile(r'^[a-z]+(_[a-z0-9]+)*$')
        
        compliant_columns = []
        non_compliant_columns = []
        
        for col in df.columns:
            if lowercase_pattern.match(col):
                compliant_columns.append(col)
            else:
                non_compliant_columns.append(col)
        
        return {
            'overall_status': 'PASS' if len(non_compliant_columns) == 0 else 'FAIL',
            'total_columns': len(df.columns),
            'compliant_columns': compliant_columns,
            'non_compliant_columns': non_compliant_columns
        }

    # Test validation on each file
    validation_results = {
        'validation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S EST'),
        'files_validated': [],
        'header_compliance': {},
        'data_type_consistency': {},
        'cross_file_compatibility': {},
        'powerbi_readiness': {},
        'overall_status': 'PASS',
        'issues_found': [],
        'recommendations': []
    }
    
    file_schemas = {}
    
    print("\\n" + "=" * 70)
    print("COMPREHENSIVE EXPORT CONSISTENCY VALIDATION")
    print("=" * 70)
    
    # Validate each file
    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            file_name = file_path.name
            
            validation_results['files_validated'].append(file_name)
            print(f"Analyzing: {file_name} ({len(df)} rows, {len(df.columns)} columns)")
            
            # Header compliance check
            header_val = validate_lowercase_snake_case_headers(df, file_name)
            validation_results['header_compliance'][file_name] = header_val
            
            if header_val['overall_status'] == 'PASS':
                print(f"  PASS Headers: All {header_val['total_columns']} columns follow lowercase_snake_case")
            else:
                print(f"  WARNING Headers: {len(header_val['non_compliant_columns'])} non-compliant columns")
                validation_results['issues_found'].append(
                    f"{file_name}: Non-compliant headers: {header_val['non_compliant_columns']}"
                )
            
            # Data type analysis
            data_type_info = {
                'total_columns': len(df.columns),
                'total_rows': len(df),
                'string_columns': [],
                'numeric_columns': [],
                'datetime_columns': [],
                'mixed_type_columns': [],
                'null_percentage_by_column': {},
                'data_quality_issues': []
            }
            
            for col in df.columns:
                col_dtype = df[col].dtype
                non_null_count = df[col].notna().sum()
                null_percentage = ((len(df) - non_null_count) / len(df)) * 100 if len(df) > 0 else 0
                data_type_info['null_percentage_by_column'][col] = round(null_percentage, 1)
                
                if col_dtype == 'object':
                    data_type_info['string_columns'].append({
                        'column': col,
                        'dtype': str(col_dtype),
                        'null_percentage': null_percentage
                    })
                elif pd.api.types.is_numeric_dtype(col_dtype):
                    data_type_info['numeric_columns'].append({
                        'column': col,
                        'dtype': str(col_dtype),
                        'null_percentage': null_percentage
                    })
                elif pd.api.types.is_datetime64_any_dtype(col_dtype):
                    data_type_info['datetime_columns'].append({
                        'column': col,
                        'dtype': str(col_dtype),
                        'null_percentage': null_percentage
                    })
                else:
                    data_type_info['mixed_type_columns'].append({
                        'column': col,
                        'dtype': str(col_dtype),
                        'null_percentage': null_percentage
                    })
                
                # Flag columns with high null percentages
                if null_percentage > 50:
                    data_type_info['data_quality_issues'].append(
                        f"Column '{col}' has high null percentage: {null_percentage:.1f}%"
                    )
            
            validation_results['data_type_consistency'][file_name] = data_type_info
            file_schemas[file_name] = df.dtypes.to_dict()
            
            # Log data type summary
            print(f"  Data Types: {len(data_type_info['string_columns'])} string, " +
                  f"{len(data_type_info['numeric_columns'])} numeric, " +
                  f"{len(data_type_info['datetime_columns'])} datetime, " +
                  f"{len(data_type_info['mixed_type_columns'])} mixed")
            
            if data_type_info['data_quality_issues']:
                print(f"  WARNING Data Quality Issues: {len(data_type_info['data_quality_issues'])}")
                for issue in data_type_info['data_quality_issues'][:3]:  # Show first 3
                    print(f"    - {issue}")
            
            # Power BI readiness check
            powerbi_issues = validate_powerbi_readiness(file_path)
            validation_results['powerbi_readiness'][file_name] = {
                'ready': len(powerbi_issues) == 0,
                'issues': powerbi_issues
            }
            
            if powerbi_issues:
                print(f"  WARNING Power BI Issues: {len(powerbi_issues)}")
                for issue in powerbi_issues[:3]:  # Show first 3
                    print(f"    - {issue}")
                validation_results['issues_found'].extend([f"{file_name}: {issue}" for issue in powerbi_issues])
            else:
                print(f"  PASS Power BI Ready: No import issues detected")
            
        except Exception as e:
            error_msg = f"Error validating {file_path}: {e}"
            validation_results['issues_found'].append(error_msg)
            print(f"ERROR {error_msg}")
    
    # Cross-file compatibility analysis
    if len(file_schemas) > 1:
        print("Cross-File Compatibility Analysis:")
        
        # Find common columns across files
        all_columns = set()
        for schema in file_schemas.values():
            all_columns.update(schema.keys())
        
        common_columns = all_columns
        for schema in file_schemas.values():
            common_columns = common_columns.intersection(set(schema.keys()))
        
        print(f"  Total unique columns across all files: {len(all_columns)}")
        print(f"  Common columns across all files: {len(common_columns)}")
        
        # Check data type consistency for common columns
        inconsistent_columns = []
        for col in common_columns:
            col_types = {}
            for file_name, schema in file_schemas.items():
                col_types[file_name] = str(schema[col])
            
            # Check if all files have same data type for this column
            unique_types = set(col_types.values())
            is_consistent = len(unique_types) == 1
            
            if not is_consistent:
                inconsistent_columns.append(col)
                validation_results['issues_found'].append(
                    f"Inconsistent data types for column '{col}': {col_types}"
                )
        
        if inconsistent_columns:
            print(f"  WARNING Inconsistent data types in {len(inconsistent_columns)} common columns:")
            for col in inconsistent_columns[:5]:  # Show first 5
                print(f"    - {col}")
        else:
            print(f"  PASS All common columns have consistent data types")
    
    # Determine overall status
    if validation_results['issues_found']:
        validation_results['overall_status'] = 'FAIL' if any('Error' in issue for issue in validation_results['issues_found']) else 'WARNING'
    else:
        validation_results['overall_status'] = 'PASS'
    
    # Final summary
    print("=" * 70)
    print("EXPORT CONSISTENCY VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Overall Status: {validation_results['overall_status']}")
    print(f"Files Validated: {len(validation_results['files_validated'])}")
    print(f"Issues Found: {len(validation_results['issues_found'])}")
    print(f"Power BI Ready Files: {sum(1 for v in validation_results['powerbi_readiness'].values() if v['ready'])}/{len(validation_results['powerbi_readiness'])}")
    print("=" * 70)
    
    print("\\n=== Export validation test completed successfully! ===")
    return validation_results

if __name__ == "__main__":
    test_export_validation()