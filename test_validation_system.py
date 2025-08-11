"""
Test script for the enhanced multi-column filtering validation system
"""
import sys
import os
import pandas as pd

# Add the scripts directory to path
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '01_scripts')
sys.path.append(scripts_dir)

from Comprehensive_SCRPA_Fix_v8_5_Standardized import ComprehensiveSCRPAFixV8_5

def test_validation_system():
    """Test the enhanced validation system with sample data"""
    
    print("=== Testing Enhanced Multi-Column Filtering Validation ===")
    
    # Initialize processor
    processor = ComprehensiveSCRPAFixV8_5()
    
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
    validation_results = processor.validate_multi_column_filtering(test_data)
    
    print("\n✅ VALIDATION RESULTS:")
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
        crime_category = processor.multi_column_crime_search(row, crime_patterns)
        print(f"Row {idx+1} ({row['case_number']}): {crime_category}")
    
    print("\n✅ Validation system test completed successfully!")
    return validation_results

if __name__ == "__main__":
    test_validation_system()