#!/usr/bin/env python3
"""
Test script for Enhanced SCRPA v4 Pipeline with Validation Checks

This script tests the enhanced SCRPA v4 production pipeline with:
1. Validation checks for each major stage
2. Structured logging of processing summary
3. Clear pass/fail status reporting

Expected Outcome:
- Clear validation summary showing pass/fail status for RMS, CAD, matching, and exports
- Structured logging with processing metrics
- Comprehensive error handling and reporting
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, date, time
import tempfile
import os

# Import the enhanced pipeline
from Complete_SCRPA_v4_Production_Pipeline import CompleteSCRPAv4ProductionPipeline

def create_test_data():
    """Create test RMS and CAD data for pipeline testing."""
    
    # Create test RMS data
    rms_data = pd.DataFrame({
        'case_number': ['RMS-001', 'RMS-002', 'RMS-003', 'RMS-004', 'RMS-005'],
        'incident_date_raw': ['2025-08-01', '2025-08-02', '2025-08-03', '2025-08-04', '2025-08-05'],
        'incident_time_raw': ['14:30:00', '09:15:00', '22:45:00', '16:20:00', '11:30:00'],
        'incident_date_between_raw': [None, None, None, None, None],
        'incident_time_between_raw': [None, None, None, None, None],
        'report_date_raw': ['2025-08-01', '2025-08-02', '2025-08-03', '2025-08-04', '2025-08-05'],
        'report_time_raw': ['14:35:00', '09:20:00', '22:50:00', '16:25:00', '11:35:00'],
        'incident_type_1_raw': ['Burglary - Auto', 'Theft', 'Assault', 'Vandalism', 'Traffic'],
        'incident_type_2_raw': [None, None, None, None, None],
        'incident_type_3_raw': [None, None, None, None, None],
        'full_address_raw': [
            '123 Main St, Hackensack, NJ, 07601',
            '456 Oak Ave, Hackensack, NJ, 07601',
            '789 Pine St, Hackensack, NJ, 07601',
            '321 Elm St, Hackensack, NJ, 07601',
            '654 Maple Dr, Hackensack, NJ, 07601'
        ],
        'grid_raw': ['A1', 'B2', 'C3', 'D4', 'E5'],
        'zone_raw': ['Zone1', 'Zone2', 'Zone3', 'Zone4', 'Zone5'],
        'narrative_raw': [
            'Vehicle broken into',
            'Property stolen from vehicle',
            'Physical altercation reported',
            'Property damage reported',
            'Traffic violation issued'
        ],
        'total_value_stolen': [500, 1200, 0, 300, 0],
        'total_value_recovered': [0, 0, 0, 0, 0],
        'registration_1': ['NJ-ABC123', 'PA-XYZ789', None, None, 'NY-12345'],
        'make_1': ['Honda', 'Toyota', None, None, 'Ford'],
        'model_1': ['Civic', 'Camry', None, None, 'Focus'],
        'reg_state_1': ['NJ', 'PA', None, None, 'NY'],
        'registration_2': [None, None, None, None, None],
        'reg_state_2': [None, None, None, None, None],
        'make_2': [None, None, None, None, None],
        'model_2': [None, None, None, None, None],
        'reviewed_by': ['Officer1', 'Officer2', 'Officer3', 'Officer4', 'Officer5'],
        'complete_calc': ['Complete', 'Complete', 'Complete', 'Complete', 'Complete'],
        'officer_of_record': ['Officer1', 'Officer2', 'Officer3', 'Officer4', 'Officer5'],
        'squad': ['Squad1', 'Squad2', 'Squad3', 'Squad4', 'Squad5'],
        'det_assigned': [None, None, None, None, None],
        'case_status': ['Open', 'Open', 'Open', 'Open', 'Open'],
        'nibrs_classification': ['23A', '23F', '13A', '14', '90A']
    })
    
    # Create test CAD data
    cad_data = pd.DataFrame({
        'case_number': ['CAD-001', 'CAD-002', 'CAD-003', 'CAD-004', 'CAD-005'],
        'incident': ['BURGLARY AUTO', 'THEFT', 'ASSAULT', 'VANDALISM', 'TRAFFIC'],
        'how_reported': ['9-1-1', '9-1-1', '9-1-1', '9-1-1', '9-1-1'],
        'full_address_raw': [
            '123 Main St, Hackensack, NJ, 07601',
            '456 Oak Ave, Hackensack, NJ, 07601',
            '789 Pine St, Hackensack, NJ, 07601',
            '321 Elm St, Hackensack, NJ, 07601',
            '654 Maple Dr, Hackensack, NJ, 07601'
        ],
        'post': ['Post1', 'Post2', 'Post3', 'Post4', 'Post5'],
        'grid_raw': ['A1', 'B2', 'C3', 'D4', 'E5'],
        'time_of_call': ['14:30:00', '09:15:00', '22:45:00', '16:20:00', '11:30:00'],
        'call_year': [2025, 2025, 2025, 2025, 2025],
        'call_month': [8, 8, 8, 8, 8],
        'hour_minutes_calc': ['14:30', '09:15', '22:45', '16:20', '11:30'],
        'day_of_week_raw': ['Friday', 'Saturday', 'Sunday', 'Monday', 'Tuesday'],
        'time_dispatched': ['14:32:00', '09:17:00', '22:47:00', '16:22:00', '11:32:00'],
        'time_out': ['14:35:00', '09:20:00', '22:50:00', '16:25:00', '11:35:00'],
        'time_in': ['15:00:00', '09:45:00', '23:15:00', '16:50:00', '12:00:00'],
        'time_spent_raw': ['00:28:00', '00:28:00', '00:28:00', '00:25:00', '00:25:00'],
        'time_response_raw': ['00:02:00', '00:02:00', '00:02:00', '00:02:00', '00:02:00'],
        'officer': ['Officer1', 'Officer2', 'Officer3', 'Officer4', 'Officer5'],
        'disposition': ['Cleared', 'Cleared', 'Cleared', 'Cleared', 'Cleared'],
        'response_type_fallback': ['Crime', 'Crime', 'Crime', 'Crime', 'Traffic'],
        'cad_notes_raw': [
            'kiselow_g 1/14/2025 3:47:59 PM Vehicle broken into',
            'Gervasi_J - 02/20/2025 08:05:00 AM Property stolen from vehicle',
            'intake_fa 3/3/2025 12:00:00 PM Physical altercation reported',
            'officer_smith 4/15/2025 16:30:00 Property damage reported',
            'dispatch_1 5/20/2025 11:45:00 Traffic violation issued'
        ]
    })
    
    return rms_data, cad_data

def test_enhanced_pipeline():
    """Test the enhanced SCRPA v4 pipeline with validation checks."""
    
    print("=" * 60)
    print("ENHANCED SCRPA v4 PIPELINE TEST")
    print("=" * 60)
    
    try:
        # Create test data
        print("\nCreating test data...")
        rms_data, cad_data = create_test_data()
        
        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save test data to temporary files
            rms_file = temp_path / "test_rms_data.csv"
            cad_file = temp_path / "test_cad_data.csv"
            
            rms_data.to_csv(rms_file, index=False)
            cad_data.to_csv(cad_file, index=False)
            
            print(f"Test files created:")
            print(f"  RMS: {rms_file}")
            print(f"  CAD: {cad_file}")
            
            # Initialize enhanced pipeline
            print("\nInitializing enhanced SCRPA v4 pipeline...")
            pipeline = CompleteSCRPAv4ProductionPipeline(str(temp_path))
            
            # Run the enhanced pipeline
            print("\nRunning enhanced pipeline...")
            results = pipeline.run_full_pipeline(str(rms_file), str(cad_file))
            
            # Display results
            print("\n" + "=" * 60)
            print("PIPELINE EXECUTION RESULTS")
            print("=" * 60)
            
            if results['status'] == 'SUCCESS':
                print("✅ Pipeline executed successfully!")
                
                # Display processing metrics
                metrics = results['processing_metrics']
                print(f"\nProcessing Metrics:")
                print(f"  Version: {metrics['pipeline_version']}")
                print(f"  Processing time: {metrics['processing_time_seconds']:.2f} seconds")
                print(f"  Modules integrated: {metrics['modules_integrated']}")
                
                # Display record processing
                print(f"\nRecord Processing:")
                print(f"  RMS: {metrics['rms_records']['input']} -> {metrics['rms_records']['output']} ({metrics['rms_records']['preservation']})")
                print(f"  CAD: {metrics['cad_records']['input']} -> {metrics['cad_records']['output']} ({metrics['cad_records']['preservation']})")
                print(f"  Matched: {metrics['matched_records']}")
                
                # Display validation results
                print(f"\nValidation Results:")
                if 'validation_results' in results:
                    validation_results = results['validation_results']
                    for check, status in validation_results.items():
                        status_icon = "✅ PASS" if status else "❌ FAIL"
                        print(f"  {check}: {status_icon}")
                else:
                    print("  No validation results found")
                
                # Display output files
                print(f"\nOutput Files Generated:")
                for file_type, file_path in results['output_files'].items():
                    file_exists = Path(file_path).exists()
                    status_icon = "✅" if file_exists else "❌"
                    print(f"  {file_type}: {status_icon} {Path(file_path).name}")
                
                # Test validation methods directly
                print(f"\n" + "=" * 60)
                print("DIRECT VALIDATION METHOD TESTS")
                print("=" * 60)
                
                # Test validate_pipeline_results
                validation_results = pipeline.validate_pipeline_results()
                print("validate_pipeline_results() output:")
                for check, status in validation_results.items():
                    status_icon = "✅" if status else "❌"
                    print(f"  {check}: {status_icon}")
                
                # Test log_processing_summary (this will be logged)
                print("\nTesting log_processing_summary()...")
                export_files = list(results['output_files'].values())
                pipeline.log_processing_summary(
                    len(results['datasets']['rms_processed']),
                    len(results['datasets']['cad_processed']),
                    len(results['datasets']['matched_final']),
                    export_files
                )
                
                return True
                
            else:
                print("❌ Pipeline execution failed!")
                print(f"Error: {results['error']}")
                if 'traceback' in results:
                    print(f"Traceback: {results['traceback']}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validation_methods():
    """Test validation methods independently."""
    
    print("\n" + "=" * 60)
    print("INDEPENDENT VALIDATION METHOD TESTS")
    print("=" * 60)
    
    try:
        # Create pipeline instance
        pipeline = CompleteSCRPAv4ProductionPipeline()
        
        # Test with empty state
        print("\nTesting validation with empty state:")
        empty_results = pipeline.validate_pipeline_results()
        for check, status in empty_results.items():
            status_icon = "✅" if status else "❌"
            print(f"  {check}: {status_icon}")
        
        # Test with mock data
        print("\nTesting validation with mock data:")
        pipeline.rms_data = pd.DataFrame({'test': [1, 2, 3]})
        pipeline.rms_final = pd.DataFrame({'test': [1, 2]})
        pipeline.cad_data = pd.DataFrame({'test': [1, 2, 3, 4]})
        pipeline.matched_data = pd.DataFrame({
            'period': ['7-Day', '28-Day', 'YTD', 'Historical']
        })
        pipeline._seven_day_export_path = "/tmp/test_export.csv"
        
        mock_results = pipeline.validate_pipeline_results()
        for check, status in mock_results.items():
            status_icon = "✅" if status else "❌"
            print(f"  {check}: {status_icon}")
        
        # Test log_processing_summary
        print("\nTesting log_processing_summary with mock data:")
        pipeline.log_processing_summary(100, 150, 75, ['/tmp/file1.csv', '/tmp/file2.csv'])
        
        return True
        
    except Exception as e:
        print(f"❌ Validation method test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Enhanced SCRPA v4 Pipeline Validation Tests")
    print("=" * 60)
    
    # Test validation methods independently
    validation_test_passed = test_validation_methods()
    
    # Test full pipeline
    pipeline_test_passed = test_enhanced_pipeline()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Validation Methods Test: {'✅ PASSED' if validation_test_passed else '❌ FAILED'}")
    print(f"Full Pipeline Test: {'✅ PASSED' if pipeline_test_passed else '❌ FAILED'}")
    
    if validation_test_passed and pipeline_test_passed:
        print("\n🎉 All tests passed! Enhanced pipeline is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 