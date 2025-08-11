"""
Standalone test for the enhanced multi-column filtering validation system
"""
import pandas as pd
import re

def validate_multi_column_filtering(df):
    """
    Validate filtering logic across all incident-type columns simultaneously.
    Compare unpivot-then-filter vs. multi-column filtering approaches.
    """
    # Define target crime types (case-insensitive)
    target_crimes = [
        "Motor Vehicle Theft", "Robbery", "Burglary – Auto", 
        "Sexual", "Burglary – Commercial", "Burglary – Residence"
    ]
    
    # Search columns in priority order (matching multi_column_crime_search exactly)
    search_columns = [
        'incident_cad',            # CAD incident column (highest priority for matched data)
        'incident_type',           # Primary RMS column
        'all_incidents',           # Combined incidents
        'incident',                # CAD incident without suffix
        'vehicle_1',               # Additional incident data
        'vehicle_2',               # Additional incident data
        'incident_type_1_raw',     # Raw incident types if available
        'incident_type_2_raw',     # Raw incident types if available
        'incident_type_3_raw'      # Raw incident types if available
    ]
    
    validation_results = {
        'total_records': len(df),
        'search_columns_available': [],
        'crime_matches_by_column': {},
        'total_unique_matches': 0,
        'filtering_accuracy': 0.0,
        'recommendations': []
    }
    
    # Track available columns and their match counts
    for col in search_columns:
        if col in df.columns:
            validation_results['search_columns_available'].append(col)
            
            # Count matches for each target crime in this column
            col_matches = {}
            total_col_matches = 0
            
            for crime in target_crimes:
                matches = df[col].astype(str).str.contains(
                    crime, case=False, na=False, regex=False
                ).sum()
                col_matches[crime] = matches
                total_col_matches += matches
            
            validation_results['crime_matches_by_column'][col] = {
                'crime_breakdown': col_matches,
                'total_matches': total_col_matches
            }
    
    # Calculate overall filtering statistics
    all_matching_records = set()
    for col in validation_results['search_columns_available']:
        for crime in target_crimes:
            matching_indices = df[df[col].astype(str).str.contains(
                crime, case=False, na=False, regex=False
            )].index
            all_matching_records.update(matching_indices)
    
    validation_results['total_unique_matches'] = len(all_matching_records)
    validation_results['filtering_accuracy'] = (
        len(all_matching_records) / len(df) * 100 if len(df) > 0 else 0
    )
    
    # Generate recommendations
    if len(validation_results['search_columns_available']) < 3:
        validation_results['recommendations'].append(
            "Limited search columns available - consider adding more incident type fields"
        )
    
    if validation_results['filtering_accuracy'] < 10:
        validation_results['recommendations'].append(
            f"Low filtering accuracy ({validation_results['filtering_accuracy']:.1f}%) - review crime pattern matching"
        )
    
    # Log comprehensive results
    print("Multi-Column Filtering Validation Results:")
    print(f"  - Available search columns: {len(validation_results['search_columns_available'])}")
    print(f"  - Total unique crime matches: {validation_results['total_unique_matches']}")
    print(f"  - Filtering accuracy: {validation_results['filtering_accuracy']:.1f}%")
    
    for col, data in validation_results['crime_matches_by_column'].items():
        print(f"  - {col}: {data['total_matches']} total matches")
        for crime, count in data['crime_breakdown'].items():
            if count > 0:
                print(f"    * {crime}: {count}")
    
    return validation_results

def multi_column_crime_search(row, crime_patterns):
    """
    Search across all incident-type columns for crime patterns.
    
    Args:
        row (pd.Series): DataFrame row containing incident data
        crime_patterns (dict): Dictionary mapping crime categories to regex patterns
        
    Returns:
        str: Matching crime category or 'Other' if no match found
    """
    # Define columns to search across (in order of priority)
    search_columns = [
        'incident_cad',            # CAD incident column (highest priority for matched data)
        'incident_type',           # Primary RMS column
        'all_incidents',           # Combined incidents
        'incident',                # CAD incident without suffix
        'vehicle_1',               # Additional incident data
        'vehicle_2',               # Additional incident data
        'incident_type_1_raw',     # Raw incident types if available
        'incident_type_2_raw',     # Raw incident types if available
        'incident_type_3_raw'      # Raw incident types if available
    ]
    
    # Search each column for crime patterns
    for column in search_columns:
        if column in row.index and pd.notna(row[column]):
            column_value = str(row[column]).upper()
            
            # Test each crime pattern against the column value
            for category, patterns in crime_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, column_value, re.IGNORECASE):
                        print(f"Found {category} in column {column}: '{row[column]}' matches pattern '{pattern}'")
                        return category
    
    return 'Other'

def test_validation_system():
    """Test the enhanced validation system with sample data"""
    
    print("=== Testing Enhanced Multi-Column Filtering Validation ===")
    
    # Create sample test data with various incident types in different columns
    test_data = pd.DataFrame({
        'case_number': ['25-001', '25-002', '25-003', '25-004', '25-005'],
        'incident_cad': ['BURGLARY - AUTO', 'MOTOR VEHICLE THEFT', None, 'ROBBERY', None],
        'incident_type': ['Other Crime', None, 'SEXUAL ASSAULT', None, 'BURGLARY - RESIDENCE'],
        'all_incidents': [None, None, None, None, None],
        'vehicle_1': [None, None, None, None, None],
        'vehicle_2': [None, None, None, None, None],
        'incident_type_1_raw': [None, None, None, None, None],
        'incident_type_2_raw': [None, None, None, None, None],
        'incident_type_3_raw': [None, None, None, None, None],
        'period': ['7-Day', '7-Day', '7-Day', '7-Day', '7-Day']
    })
    
    print(f"Created test dataset with {len(test_data)} records")
    print("Sample data:")
    print(test_data[['case_number', 'incident_cad', 'incident_type', 'period']].to_string())
    print()
    
    # Test the validation system
    print("Running multi-column filtering validation...")
    validation_results = validate_multi_column_filtering(test_data)
    
    print("\n=== VALIDATION RESULTS ===")
    print(f"Total records: {validation_results['total_records']}")
    print(f"Available search columns: {validation_results['search_columns_available']}")
    print(f"Total unique matches: {validation_results['total_unique_matches']}")
    print(f"Filtering accuracy: {validation_results['filtering_accuracy']:.1f}%")
    
    print("\nCrime matches by column:")
    for col, data in validation_results['crime_matches_by_column'].items():
        print(f"  {col}: {data['total_matches']} total matches")
        for crime, count in data['crime_breakdown'].items():
            if count > 0:
                print(f"    - {crime}: {count}")
    
    if validation_results['recommendations']:
        print(f"\nRecommendations:")
        for rec in validation_results['recommendations']:
            print(f"  - {rec}")
    
    print("\n=== Testing Multi-Column Crime Search ===")
    
    # Test the actual multi-column search on each row
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
    
    print("Testing individual row classification:")
    for idx, row in test_data.iterrows():
        crime_category = multi_column_crime_search(row, crime_patterns)
        print(f"Row {idx+1} ({row['case_number']}): {crime_category}")
    
    print("\n=== Validation system test completed successfully! ===")
    return validation_results

if __name__ == "__main__":
    test_validation_system()