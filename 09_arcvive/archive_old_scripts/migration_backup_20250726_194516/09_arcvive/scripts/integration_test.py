# 🕒 2025-06-21-18-25-00
# Police_Data_Analysis/integration_verification_test
# Author: R. A. Carucci
# Purpose: Comprehensive test script to verify all Excel integration components and identify issues

import os
import sys
from datetime import date, datetime
from pathlib import Path

def test_imports():
    """Test all critical imports"""
    print("🧪 TESTING IMPORTS")
    print("=" * 40)
    
    try:
        from config import (
            get_excel_report_name, 
            get_correct_folder_name, 
            get_7day_period_dates,
            get_crime_type_folder,
            get_standardized_filename,
            CRIME_FOLDER_MAPPING,
            validate_all_paths
        )
        print("✅ All config imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_excel_integration():
    """Test Excel lookup functions"""
    print("\n🧪 TESTING EXCEL INTEGRATION")
    print("=" * 40)
    
    from config import get_excel_report_name, get_correct_folder_name, get_7day_period_dates
    
    # Test date: June 10, 2025 (should be C06W23)
    test_date = date(2025, 6, 10)
    
    # Test Excel report name lookup
    report_name = get_excel_report_name(test_date)
    print(f"📋 Excel report name for {test_date}: {report_name}")
    
    # Test folder name generation
    folder_name = get_correct_folder_name(test_date)
    print(f"📁 Folder name: {folder_name}")
    
    # Test 7-day period calculation
    start_date, end_date = get_7day_period_dates(test_date)
    print(f"📊 7-Day period: {start_date} to {end_date}")
    
    # Validation checks
    checks = [
        (report_name == "C06W23", f"Report name should be C06W23, got: {report_name}"),
        ("C06W23_2025_06_10_7Day" in folder_name, f"Folder should contain C06W23_2025_06_10_7Day, got: {folder_name}"),
        (start_date == date(2025, 6, 3), f"Start date should be 2025-06-03, got: {start_date}"),
        (end_date == date(2025, 6, 9), f"End date should be 2025-06-09, got: {end_date}")
    ]
    
    print("\n🔍 VALIDATION RESULTS:")
    all_passed = True
    for check_passed, message in checks:
        status = "✅" if check_passed else "❌"
        print(f"{status} {message}")
        if not check_passed:
            all_passed = False
    
    return all_passed

def test_crime_folder_mapping():
    """Test crime type folder mapping"""
    print("\n🧪 TESTING CRIME FOLDER MAPPING")
    print("=" * 40)
    
    from config import CRIME_FOLDER_MAPPING, get_standardized_filename, get_crime_type_folder
    
    test_date_str = "2025_06_10"
    
    print(f"📊 Found {len(CRIME_FOLDER_MAPPING)} crime types:")
    for crime_type, folder_mapping in CRIME_FOLDER_MAPPING.items():
        standardized = get_standardized_filename(crime_type)
        crime_folder = get_crime_type_folder(crime_type, test_date_str)
        
        print(f"  🚔 {crime_type}")
        print(f"     📁 Folder mapping: {folder_mapping}")
        print(f"     📝 Standardized: {standardized}")
        print(f"     📂 Full path: {crime_folder}")
        print()
    
    return True

def test_path_validation():
    """Test path validation"""
    print("\n🧪 TESTING PATH VALIDATION")
    print("=" * 40)
    
    from config import validate_all_paths
    
    return validate_all_paths()

def test_sql_patterns():
    """Test SQL pattern generation"""
    print("\n🧪 TESTING SQL PATTERNS")
    print("=" * 40)
    
    from config import get_sql_pattern_for_crime, CRIME_FOLDER_MAPPING
    
    for crime_type in CRIME_FOLDER_MAPPING.keys():
        pattern = get_sql_pattern_for_crime(crime_type)
        print(f"🔍 {crime_type}: {pattern}")
    
    return True

def test_date_scenarios():
    """Test multiple date scenarios"""
    print("\n🧪 TESTING MULTIPLE DATE SCENARIOS")
    print("=" * 40)
    
    from config import get_excel_report_name, get_7day_period_dates
    
    test_dates = [
        date(2025, 6, 10),  # Should be C06W23
        date(2025, 6, 17),  # Should be C06W24
        date(2025, 6, 3),   # Should be C06W22 or similar
    ]
    
    for test_date in test_dates:
        print(f"\n📅 Testing {test_date}:")
        report_name = get_excel_report_name(test_date)
        start_date, end_date = get_7day_period_dates(test_date)
        print(f"   📋 Report: {report_name}")
        print(f"   📊 Period: {start_date} to {end_date}")
    
    return True

def test_arcgis_project_access():
    """Test ArcGIS Pro project access"""
    print("\n🧪 TESTING ARCGIS PROJECT ACCESS")
    print("=" * 40)
    
    try:
        from config import APR_PATH
        print(f"📁 ArcGIS Pro project path: {APR_PATH}")
        
        if os.path.exists(APR_PATH):
            print("✅ ArcGIS Pro project file exists")
            
            # Try to load with arcpy if available
            try:
                import arcpy
                aprx = arcpy.mp.ArcGISProject(APR_PATH)
                maps = aprx.listMaps()
                print(f"✅ Successfully loaded project with {len(maps)} maps")
                
                # List some layers
                if maps:
                    map_obj = maps[0]
                    layers = map_obj.listLayers()
                    print(f"✅ Found {len(layers)} layers in first map")
                    
                    # Look for crime layers
                    crime_layers = [lyr for lyr in layers if any(crime in lyr.name for crime in ["MV Theft", "Burglary", "Robbery"])]
                    print(f"✅ Found {len(crime_layers)} crime-related layers")
                
                del aprx
                return True
                
            except Exception as e:
                print(f"⚠️ Could not load ArcGIS project: {e}")
                return False
        else:
            print("❌ ArcGIS Pro project file not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing ArcGIS project: {e}")
        return False

def test_output_folder_creation():
    """Test output folder creation logic"""
    print("\n🧪 TESTING OUTPUT FOLDER CREATION")
    print("=" * 40)
    
    try:
        from config import get_correct_folder_name, get_crime_type_folder, REPORT_BASE_DIR
        
        test_date = date(2025, 6, 10)
        test_date_str = "2025_06_10"
        
        # Test main folder generation
        main_folder = get_correct_folder_name(test_date)
        print(f"📁 Main folder: {main_folder}")
        
        # Test full path
        full_path = os.path.join(REPORT_BASE_DIR, main_folder)
        print(f"📂 Full path: {full_path}")
        
        # Test crime subfolders
        test_crime = "MV Theft"
        crime_folder = get_crime_type_folder(test_crime, test_date_str)
        print(f"🚔 Crime folder for {test_crime}: {crime_folder}")
        
        # Check if base directory exists
        if os.path.exists(REPORT_BASE_DIR):
            print("✅ Base report directory exists")
        else:
            print(f"❌ Base report directory not found: {REPORT_BASE_DIR}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing folder creation: {e}")
        return False

def generate_test_summary(results):
    """Generate summary of all test results"""
    print("\n" + "=" * 60)
    print("🏁 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"📊 Total tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}")
    print(f"📈 Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Your integration is ready!")
        print("\nNext steps:")
        print("1. Run a full system test with: python main.py true true false 30 false 2025_06_10")
        print("2. Check that folders are created with correct names")
        print("3. Verify maps and charts export to crime subfolders")
    else:
        print("\n⚠️ Some tests failed. Review the issues above before proceeding.")
        print("\nCommon solutions:")
        print("- Check file paths in config.py")
        print("- Ensure Excel file is accessible")
        print("- Verify ArcGIS Pro project loads correctly")
        print("- Check write permissions to output directories")

def main():
    """Run all integration tests"""
    print("🚀 STARTING COMPREHENSIVE INTEGRATION TEST")
    print("🕒 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    # Test functions and their names
    tests = {
        "Import Tests": test_imports,
        "Excel Integration": test_excel_integration, 
        "Crime Folder Mapping": test_crime_folder_mapping,
        "Path Validation": test_path_validation,
        "SQL Patterns": test_sql_patterns,
        "Date Scenarios": test_date_scenarios,
        "ArcGIS Project Access": test_arcgis_project_access,
        "Output Folder Creation": test_output_folder_creation
    }
    
    results = {}
    
    # Run all tests
    for test_name, test_func in tests.items():
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Generate summary
    generate_test_summary(results)

if __name__ == "__main__":
    main()