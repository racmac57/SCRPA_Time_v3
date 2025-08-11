"""
Test script for the enhanced 7-Day SCRPA export validation
"""
import pandas as pd
import sys
import os

# Add the scripts directory to path
scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '01_scripts')
sys.path.append(scripts_dir)

def test_7day_export_only():
    """Test just the 7-day export functionality to validate the enhanced system"""
    
    print("=== Testing Enhanced 7-Day SCRPA Export Validation ===")
    
    # Import after adding to path
    try:
        from Comprehensive_SCRPA_Fix_v8_5_Standardized import ComprehensiveSCRPAFixV8_5
        processor = ComprehensiveSCRPAFixV8_5()
        print("Processor initialized successfully")
    except Exception as e:
        print(f"Error initializing processor: {e}")
        return
    
    # Check if we have existing processed data to test with
    try:
        # Look for existing CSV files to test with
        cad_file = None
        rms_file = None
        
        # Check for existing processed files
        project_path = processor.project_path
        for file in project_path.glob("*cad_rms_matched*.csv"):
            print(f"Found potential test file: {file}")
            
            # Try to load the file to test validation
            try:
                test_data = pd.read_csv(file, nrows=10)  # Just load first 10 rows for testing
                print(f"Successfully loaded test data with {len(test_data)} rows")
                print(f"Columns: {list(test_data.columns)}")
                
                # Check if it has the required columns for testing
                required_cols = ['period', 'case_number', 'incident_date']
                if all(col in test_data.columns for col in required_cols):
                    print(f"File {file.name} has required columns for testing")
                    
                    # Load more data for actual testing
                    full_test_data = pd.read_csv(file)
                    print(f"Loaded full test dataset with {len(full_test_data)} records")
                    
                    # Check for 7-Day records
                    seven_day_records = full_test_data[full_test_data['period'] == '7-Day']
                    print(f"Found {len(seven_day_records)} 7-Day period records")
                    
                    if len(seven_day_records) > 0:
                        print("Testing 7-Day export functionality...")
                        
                        # Test the 7-day export method
                        output_dir = project_path / "04_powerbi"
                        result_df = processor.create_7day_scrpa_export(full_test_data, output_dir)
                        
                        print(f"7-Day export completed! Generated {len(result_df)} records")
                        if len(result_df) > 0:
                            print("Sample exported records:")
                            print(result_df[['Case_Number', 'Incident_Types', 'Crime_Category', 'Status']].head())
                        
                        break
                    else:
                        print("No 7-Day records found in this file, trying next...")
                else:
                    print(f"File {file.name} missing required columns: {[col for col in required_cols if col not in test_data.columns]}")
                    
            except Exception as e:
                print(f"Error loading {file}: {e}")
                continue
        
        if not any(file.name.endswith('.csv') and 'cad_rms_matched' in file.name for file in project_path.iterdir()):
            print("No suitable test files found. Try running the full pipeline first to generate test data.")
    
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_7day_export_only()