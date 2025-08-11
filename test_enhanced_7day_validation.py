"""
Test script for the enhanced 7-Day SCRPA export validation using existing data
"""
import pandas as pd
import numpy as np
import re

def validate_7day_crime_categories_standalone(filtered_df, crime_patterns):
    """
    Standalone version of the validate_7day_crime_categories function for testing
    """
    validation_report = {
        'total_filtered_records': len(filtered_df),
        'crime_category_breakdown': {},
        'validation_details': [],
        'potential_issues': [],
        'column_match_analysis': {},
        'pattern_match_analysis': {}
    }
    
    if filtered_df.empty:
        print("No 7-Day records to validate")
        return validation_report
    
    # Initialize column match tracking
    search_columns = ['incident_type', 'all_incidents', 'vehicle_1', 'vehicle_2', 
                     'incident_cad', 'incident', 'incident_type_1_raw', 
                     'incident_type_2_raw', 'incident_type_3_raw']
    
    for col in search_columns:
        validation_report['column_match_analysis'][col] = {
            'available': col in filtered_df.columns,
            'populated_records': 0,
            'crime_matches': 0,
            'sample_values': []
        }
    
    # Initialize pattern match tracking
    for category in crime_patterns.keys():
        validation_report['pattern_match_analysis'][category] = {
            'total_matches': 0,
            'matching_records': [],
            'pattern_details': {}
        }
    
    def multi_column_crime_search_standalone(row, crime_patterns):
        """Standalone version of multi_column_crime_search for testing"""
        search_columns = ['incident_cad', 'incident_type', 'all_incidents', 'incident', 
                         'vehicle_1', 'vehicle_2', 'incident_type_1_raw', 
                         'incident_type_2_raw', 'incident_type_3_raw']
        
        for column in search_columns:
            if column in row.index and pd.notna(row[column]):
                column_value = str(row[column]).upper()
                
                for category, patterns in crime_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, column_value, re.IGNORECASE):
                            return category
        return 'Other'
    
    # Analyze each filtered record in detail
    for idx, row in filtered_df.iterrows():
        # Get crime category using multi-column search
        crime_category = multi_column_crime_search_standalone(row, crime_patterns)
        
        # Track which column(s) triggered the match
        matching_columns = []
        matching_values = []
        pattern_matches = {}
        
        # Check each search column for matches
        for col in search_columns:
            if col in row.index and pd.notna(row[col]):
                col_value = str(row[col]).upper()
                validation_report['column_match_analysis'][col]['populated_records'] += 1
                
                # Add sample values (limit to 3 unique values per column)
                if len(validation_report['column_match_analysis'][col]['sample_values']) < 3:
                    if row[col] not in validation_report['column_match_analysis'][col]['sample_values']:
                        validation_report['column_match_analysis'][col]['sample_values'].append(row[col])
                
                # Check if this column contains any crime patterns
                for category, patterns in crime_patterns.items():
                    for pattern_idx, pattern in enumerate(patterns):
                        if re.search(pattern, col_value, re.IGNORECASE):
                            matching_columns.append(col)
                            matching_values.append(row[col])
                            validation_report['column_match_analysis'][col]['crime_matches'] += 1
                            
                            # Track pattern matches
                            if category not in pattern_matches:
                                pattern_matches[category] = []
                            pattern_matches[category].append({
                                'pattern': pattern,
                                'column': col,
                                'value': row[col],
                                'pattern_index': pattern_idx
                            })
                            break
        
        # Record detailed validation for this record
        validation_details = {
            'case_number': row.get('case_number', 'Unknown'),
            'incident_date': row.get('incident_date', 'Unknown'),
            'incident_time': row.get('incident_time', 'Unknown'),
            'period': row.get('period', 'Unknown'),
            'crime_category': crime_category,
            'matching_columns': list(set(matching_columns)),
            'matching_values': list(set(matching_values)),
            'pattern_matches': pattern_matches,
            'incident_type': row.get('incident_type', 'None'),
            'all_incidents': row.get('all_incidents', 'None'),
            'incident_cad': row.get('incident_cad', 'None'),
            'location': row.get('location', 'Unknown'),
            'narrative': row.get('narrative', 'None')
        }
        
        validation_report['validation_details'].append(validation_details)
        
        # Count by crime category
        if crime_category not in validation_report['crime_category_breakdown']:
            validation_report['crime_category_breakdown'][crime_category] = 0
        validation_report['crime_category_breakdown'][crime_category] += 1
        
        # Update pattern match analysis
        if crime_category in validation_report['pattern_match_analysis']:
            validation_report['pattern_match_analysis'][crime_category]['total_matches'] += 1
            validation_report['pattern_match_analysis'][crime_category]['matching_records'].append(
                row.get('case_number', 'Unknown')
            )
    
    return validation_report

def test_enhanced_7day_validation():
    """Test the enhanced 7-day validation with real data"""
    
    print("=== Testing Enhanced 7-Day Crime Category Validation ===")
    
    # Load the existing matched data
    matched_data_file = "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\04_powerbi\\C08W31_20250804_7Day_cad_rms_matched_standardized.csv"
    
    try:
        # Load the data
        matched_data = pd.read_csv(matched_data_file)
        print(f"Loaded matched data with {len(matched_data)} records")
        print(f"Columns: {list(matched_data.columns)}")
        
        # Check period distribution
        if 'period' in matched_data.columns:
            period_counts = matched_data['period'].value_counts()
            print(f"Period distribution: {dict(period_counts)}")
            
            # Filter for 7-Day records
            seven_day_records = matched_data[matched_data['period'] == '7-Day'].copy()
            print(f"Found {len(seven_day_records)} 7-Day period records")
            
            if len(seven_day_records) > 0:
                # Define crime patterns (same as in the main script)
                crime_patterns = {
                    'Motor Vehicle Theft': [
                        r'MOTOR\s+VEHICLE\s+THEFT',
                        r'AUTO\s+THEFT',
                        r'MV\s+THEFT',
                        r'VEHICLE\s+THEFT'
                    ],
                    'Burglary - Auto': [
                        r'BURGLARY.*AUTO',
                        r'BURGLARY.*VEHICLE',
                        r'BURGLARY\s*-\s*AUTO',
                        r'BURGLARY\s*-\s*VEHICLE'
                    ],
                    'Burglary - Commercial': [
                        r'BURGLARY.*COMMERCIAL',
                        r'BURGLARY\s*-\s*COMMERCIAL',
                        r'BURGLARY.*BUSINESS'
                    ],
                    'Burglary - Residence': [
                        r'BURGLARY.*RESIDENCE',
                        r'BURGLARY\s*-\s*RESIDENCE',
                        r'BURGLARY.*RESIDENTIAL',
                        r'BURGLARY\s*-\s*RESIDENTIAL'
                    ],
                    'Robbery': [
                        r'ROBBERY'
                    ],
                    'Sexual Offenses': [
                        r'SEXUAL',
                        r'SEX\s+CRIME',
                        r'SEXUAL\s+ASSAULT',
                        r'SEXUAL\s+OFFENSE'
                    ]
                }
                
                print("\\nRunning comprehensive 7-Day crime category validation...")
                
                # Apply multi-column filtering manually for testing
                filtered_records = []
                for idx, row in seven_day_records.iterrows():
                    # Check if record matches any crime pattern
                    found_match = False
                    for category, patterns in crime_patterns.items():
                        for col in ['incident_cad', 'incident_type', 'all_incidents', 'vehicle_1', 'vehicle_2']:
                            if col in row.index and pd.notna(row[col]):
                                col_value = str(row[col]).upper()
                                for pattern in patterns:
                                    if re.search(pattern, col_value, re.IGNORECASE):
                                        filtered_records.append(idx)
                                        found_match = True
                                        break
                                if found_match:
                                    break
                            if found_match:
                                break
                        if found_match:
                            break
                
                # Get filtered dataframe
                if filtered_records:
                    filtered_df = seven_day_records.loc[filtered_records]
                    print(f"After crime pattern filtering: {len(filtered_df)} records")
                    
                    # Run comprehensive validation
                    validation_report = validate_7day_crime_categories_standalone(filtered_df, crime_patterns)
                    
                    print("\\n" + "=" * 60)
                    print("7-DAY CRIME CATEGORY VALIDATION REPORT")
                    print("=" * 60)
                    print(f"Total 7-Day records validated: {validation_report['total_filtered_records']}")
                    
                    # Crime category breakdown
                    print("Crime Category Breakdown:")
                    for category, count in validation_report['crime_category_breakdown'].items():
                        print(f"  - {category}: {count} incidents")
                    
                    # Column analysis
                    print("Column Match Analysis:")
                    for col, analysis in validation_report['column_match_analysis'].items():
                        if analysis['available'] and analysis['populated_records'] > 0:
                            print(f"  - {col}: {analysis['populated_records']} populated, {analysis['crime_matches']} matches")
                            if analysis['sample_values']:
                                sample_str = ", ".join(str(v)[:30] + "..." if len(str(v)) > 30 else str(v) 
                                                     for v in analysis['sample_values'])
                                print(f"    Sample values: {sample_str}")
                    
                    # Detailed record validation
                    print("Detailed Record Validation:")
                    for i, detail in enumerate(validation_report['validation_details'], 1):
                        print(f"  Record {i} - Case {detail['case_number']}:")
                        print(f"    - Date/Time: {detail['incident_date']} {detail['incident_time']}")
                        print(f"    - Crime Category: {detail['crime_category']}")
                        print(f"    - Matching Columns: {detail['matching_columns']}")
                        
                        # Show incident data that triggered the match
                        if detail['incident_type'] and detail['incident_type'] != 'None':
                            print(f"    - Incident Type: {detail['incident_type']}")
                        if detail['incident_cad'] and detail['incident_cad'] != 'None':
                            print(f"    - Incident (CAD): {detail['incident_cad']}")
                        if detail['narrative'] and detail['narrative'] != 'None' and pd.notna(detail['narrative']):
                            narrative_preview = str(detail['narrative'])[:100] + "..." if len(str(detail['narrative'])) > 100 else str(detail['narrative'])
                            print(f"    - Narrative: {narrative_preview}")
                    
                    print("=" * 60)
                    print("=== Enhanced 7-Day validation test completed successfully! ===")
                    
                else:
                    print("No records matched the crime patterns")
            else:
                print("No 7-Day records found in the dataset")
        else:
            print("No 'period' column found in the dataset")
            
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_7day_validation()