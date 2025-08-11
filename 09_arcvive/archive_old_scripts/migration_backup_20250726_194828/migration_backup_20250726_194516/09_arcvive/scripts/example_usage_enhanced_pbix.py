#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
example_usage_enhanced_pbix.py

Example usage of the enhanced PBIX parameter updater.
Demonstrates various use cases and validation features.
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from update_pbix_parameter_enhanced import PBIXParameterUpdater

def example_basic_update():
    """Example: Basic parameter update with full validation."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Parameter Update")
    print("=" * 60)
    
    # Example paths (adjust these for your actual files)
    input_pbix = "SCRPA_Time_v2.pbix"  # Your source PBIX file
    output_pbix = "SCRPA_Time_v2_updated.pbix"  # Output file
    
    # Check if input file exists
    if not os.path.exists(input_pbix):
        print(f"❌ Input file not found: {input_pbix}")
        print("   Please update the path to point to your actual PBIX file")
        return False
    
    try:
        # Create updater with verbose output
        updater = PBIXParameterUpdater(verbose=True)
        
        # Process with full validation
        result = updater.process_pbix_with_validation(
            input_pbix=input_pbix,
            output_pbix=output_pbix,
            param_name="BasePath",
            new_value=r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
        )
        
        # Generate and save validation report
        report_path = "validation_report.txt"
        report_content = updater.generate_validation_report(result, report_path)
        
        print("\n" + "=" * 60)
        print("RESULT:")
        print("=" * 60)
        
        if result['success']:
            print("✅ Parameter update completed successfully!")
            print(f"📁 Output file: {output_pbix}")
            print(f"📋 Validation report: {report_path}")
        else:
            print("❌ Parameter update failed!")
            print("Errors:")
            for error in result['errors']:
                print(f"  - {error}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def example_pre_validation_only():
    """Example: Pre-validation only (check file without updating)."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Pre-Validation Only")
    print("=" * 60)
    
    input_pbix = "SCRPA_Time_v2.pbix"
    
    if not os.path.exists(input_pbix):
        print(f"❌ Input file not found: {input_pbix}")
        return False
    
    try:
        updater = PBIXParameterUpdater(verbose=False)
        
        # Validate input file
        print("🔍 Validating input file...")
        input_validation = updater.validate_input_file(input_pbix)
        
        print(f"✅ File exists: {input_validation['file_exists']}")
        print(f"✅ Valid PBIX: {input_validation['is_pbix']}")
        print(f"✅ Valid ZIP: {input_validation['is_valid_zip']}")
        print(f"✅ DataMashup found: {input_validation['datamashup_found']}")
        print(f"📍 DataMashup location: {input_validation.get('datamashup_location', 'Not found')}")
        print(f"🔧 Parameters detected: {len(input_validation['parameters_detected'])}")
        
        for param in input_validation['parameters_detected']:
            print(f"   • {param['name']}: {param['value']}")
        
        if input_validation['errors']:
            print("❌ Validation errors:")
            for error in input_validation['errors']:
                print(f"   - {error}")
        
        # Check specific parameter
        print("\n🔍 Checking BasePath parameter...")
        param_validation = updater.validate_parameter_exists(input_pbix, "BasePath")
        
        if param_validation['parameter_found']:
            print(f"✅ Parameter 'BasePath' found")
            print(f"📄 Current value: {param_validation['current_value']}")
        else:
            print("❌ Parameter 'BasePath' not found")
            if param_validation['errors']:
                for error in param_validation['errors']:
                    print(f"   - {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def example_batch_update():
    """Example: Update multiple parameters in sequence."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Batch Parameter Update")
    print("=" * 60)
    
    input_pbix = "SCRPA_Time_v2.pbix"
    
    if not os.path.exists(input_pbix):
        print(f"❌ Input file not found: {input_pbix}")
        return False
    
    # Parameters to update
    parameters = {
        "BasePath": r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2",
        "ServerName": "localhost",
        "DatabaseName": "SCRPA_CrimeDB"
    }
    
    try:
        updater = PBIXParameterUpdater(verbose=True)
        
        # Start with original file
        current_file = input_pbix
        
        for i, (param_name, param_value) in enumerate(parameters.items(), 1):
            print(f"\n🔧 Updating parameter {i}/{len(parameters)}: {param_name}")
            
            # Output file for this step
            output_file = f"SCRPA_Time_v2_step_{i}.pbix"
            
            # Update parameter
            result = updater.process_pbix_with_validation(
                input_pbix=current_file,
                output_pbix=output_file,
                param_name=param_name,
                new_value=param_value
            )
            
            if result['success']:
                print(f"✅ Successfully updated {param_name}")
                current_file = output_file  # Use output as input for next step
            else:
                print(f"❌ Failed to update {param_name}")
                for error in result['errors']:
                    print(f"   - {error}")
                break
        else:
            # All parameters updated successfully
            final_output = "SCRPA_Time_v2_batch_updated.pbix"
            if current_file != final_output:
                os.rename(current_file, final_output)
            
            print(f"\n✅ All parameters updated successfully!")
            print(f"📁 Final output: {final_output}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Batch update error: {e}")
        return False

def example_error_handling():
    """Example: Demonstrate error handling for various scenarios."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Error Handling Scenarios")
    print("=" * 60)
    
    updater = PBIXParameterUpdater(verbose=False)
    
    # Test 1: Non-existent file
    print("🧪 Test 1: Non-existent file")
    result = updater.validate_input_file("nonexistent.pbix")
    print(f"   Expected failure: {'✅' if not result['file_exists'] else '❌'}")
    
    # Test 2: Invalid extension
    print("🧪 Test 2: Invalid file extension")
    # Create temporary text file
    temp_file = "test.txt"
    with open(temp_file, 'w') as f:
        f.write("test")
    
    result = updater.validate_input_file(temp_file)
    print(f"   Expected failure: {'✅' if not result['is_pbix'] else '❌'}")
    
    # Clean up
    os.remove(temp_file)
    
    # Test 3: Valid PBIX but non-existent parameter
    input_pbix = "SCRPA_Time_v2.pbix"
    if os.path.exists(input_pbix):
        print("🧪 Test 3: Non-existent parameter")
        result = updater.validate_parameter_exists(input_pbix, "NonExistentParameter")
        print(f"   Expected failure: {'✅' if not result['parameter_found'] else '❌'}")
    
    print("✅ Error handling tests completed")
    return True

def main():
    """Run all examples."""
    print("🚀 ENHANCED PBIX PARAMETER UPDATER - USAGE EXAMPLES")
    print("=" * 80)
    
    examples = [
        ("Basic Parameter Update", example_basic_update),
        ("Pre-Validation Only", example_pre_validation_only),
        ("Batch Parameter Update", example_batch_update),
        ("Error Handling", example_error_handling)
    ]
    
    results = []
    
    for example_name, example_func in examples:
        print(f"\n▶️  Running: {example_name}")
        try:
            success = example_func()
            results.append((example_name, success))
        except Exception as e:
            print(f"❌ Example failed with error: {e}")
            results.append((example_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("EXAMPLES SUMMARY")
    print("=" * 80)
    
    for example_name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {example_name}")
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {successful}/{total} examples completed successfully")
    
    return 0 if successful == total else 1

if __name__ == "__main__":
    exit(main())