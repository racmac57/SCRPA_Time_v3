# 🕒 2025-01-28-00-15-00
# SCRPA_Place_and_Time/main_complete_final
# Author: R. A. Carucci
# Purpose: Complete main.py with auto-chain functionality for seamless workflow

import sys
import logging
import time
import os
import glob
import shutil
from pathlib import Path
from datetime import datetime as dt_datetime, date as dt_date
import arcpy

# Initialize ArcGIS Pro license
try:
    # Check available license types
    if arcpy.CheckProduct("ArcInfo") == "Available":
        arcpy.CheckOutExtension("ArcInfo")
        logging.info("✅ ArcInfo license initialized")
    elif arcpy.CheckProduct("ArcEditor") == "Available":
        arcpy.CheckOutExtension("ArcEditor")
        logging.info("✅ ArcEditor license initialized")
    elif arcpy.CheckProduct("ArcView") == "Available":
        arcpy.CheckOutExtension("ArcView")
        logging.info("✅ ArcView license initialized")
    else:
        logging.error("❌ No ArcGIS license available")
        sys.exit(1)
except Exception as e:
    logging.error(f"❌ License initialization failed: {e}")
    sys.exit(1)

print("OK DateTime imported correctly as dt_datetime and dt_date")

def debug_mode(target_date_str=None):
    """Enhanced debug mode with Excel patching and comprehensive testing"""
    if target_date_str is None:
        target_date_str = "2025_06_24"
    
    print(f"\nDEBUG MODE ACTIVE")
    print("=" * 60)
    print(f"Target Date: {target_date_str}")
    
    try:
        target_date = dt_datetime.strptime(target_date_str, "%Y_%m_%d").date()
        
        from config import (
            get_excel_report_name, get_correct_folder_name, get_output_folder,
            get_7day_period_dates, validate_all_paths, CRIME_TYPES, REPORT_BASE_DIR
        )
        
        print(f"\nEXCEL INTEGRATION TEST")
        print("-" * 40)
        
        report_name = get_excel_report_name(target_date)
        print(f"Excel Report Name: {report_name}")
        
        folder_name = get_correct_folder_name(target_date)
        print(f"Folder Name: {folder_name}")
        
        start_date, end_date = get_7day_period_dates(target_date)
        print(f"7-Day Period: {start_date} to {end_date}")
        
        output_path = get_output_folder(target_date_str)
        print(f"Output Path: {output_path}")
        
        print(f"\nPATH VALIDATION")
        print("-" * 40)
        paths_valid = validate_all_paths()
        
        print(f"\nCRIME TYPES")
        print("-" * 40)
        print(f"Count: {len(CRIME_TYPES)}")
        for i, crime_type in enumerate(CRIME_TYPES, 1):
            print(f"  {i}. {crime_type}")
        
        print(f"\nDEBUG SUMMARY")
        print("=" * 60)
        
        checks = [
            (report_name is not None, f"Excel lookup: {report_name}"),
            (start_date is not None and end_date is not None, f"Date range valid"),
            (os.path.exists(output_path), f"Output folder exists"),
            (paths_valid, "All config paths valid")
        ]
        
        all_passed = True
        for passed, description in checks:
            status = "✅ OK" if passed else "❌ FAILED"
            print(f"{status} {description}")
            all_passed &= passed
        
        print(f"\nOVERALL STATUS: {'READY' if all_passed else 'ISSUES DETECTED'}")
        return all_passed
        
    except Exception as e:
        print(f"Debug mode failed: {e}")
        logging.error(f"Debug mode failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_mode():
    """Validation mode - check all folders and templates exist"""
    print(f"\nVALIDATION MODE")
    print("=" * 60)
    
    try:
        from config import validate_all_paths, POWERPOINT_TEMPLATES, CRIME_TYPES
        
        print(f"Checking all config paths...")
        paths_valid = validate_all_paths()
        
        print(f"\nPowerPoint Templates:")
        for name, path in POWERPOINT_TEMPLATES.items():
            exists = os.path.exists(path) if path else False
            status = "✅ OK" if exists else "❌ FAILED"
            print(f"{status} {name}: {path}")
        
        print(f"\nCrime Types Configuration:")
        print(f"Total: {len(CRIME_TYPES)}")
        for crime_type in CRIME_TYPES:
            print(f"  • {crime_type}")
        
        print(f"\nVALIDATION SUMMARY")
        print("-" * 40)
        overall_valid = paths_valid and any(os.path.exists(p) for p in POWERPOINT_TEMPLATES.values() if p)
        status = "SYSTEM READY" if overall_valid else "ISSUES DETECTED - CONTINUING ANYWAY"
        print(f"{status}")
        
        return overall_valid
        
    except Exception as e:
        print(f"Validation failed: {e}")
        logging.error(f"Validation failed: {e}")
        return False

# Check for debug/validation modes FIRST
if "--debug" in sys.argv:
    custom_date = None
    debug_index = sys.argv.index("--debug")
    if debug_index + 1 < len(sys.argv) and not sys.argv[debug_index + 1].startswith("-"):
        custom_date = sys.argv[debug_index + 1]
    
    success = debug_mode(custom_date)
    sys.exit(0 if success else 1)

elif "--validate" in sys.argv:
    success = validate_mode()
    sys.exit(0 if success else 1)

def check_and_import_dependencies():
    """Check and import all required dependencies with detailed error reporting"""
    missing_modules = []
    
    try:
        import arcpy
        logging.info("✅ ArcPy imported successfully")
    except ImportError as e:
        logging.error(f"ERROR: ArcPy import failed: {e}")
        logging.error("Ensure you're running in ArcGIS Pro Python environment")
        missing_modules.append("arcpy")
    
    try:
        from pptx import Presentation
        from pptx.util import Inches
        logging.info("✅ python-pptx imported successfully")
    except ImportError as e:
        logging.error(f"ERROR: python-pptx import failed: {e}")
        logging.error("Install with: pip install python-pptx")
        missing_modules.append("python-pptx")
    
    try:
        import pandas as pd
        logging.info("✅ pandas imported successfully")
    except ImportError as e:
        logging.warning(f"WARNING: pandas import failed: {e}")
        logging.warning("Some features will be limited without pandas")
    
    try:
        import matplotlib.pyplot as plt
        logging.info("✅ matplotlib imported successfully")
    except ImportError as e:
        logging.warning(f"WARNING: matplotlib import failed: {e}")
        logging.warning("Auto-fit charts will be limited without matplotlib")
    
    try:
        from PIL import Image
        logging.info("✅ PIL imported successfully")
    except ImportError as e:
        logging.warning(f"WARNING: PIL import failed: {e}")
        logging.warning("Placeholder images will be limited without PIL")
    
    return missing_modules

# Check dependencies first
missing_deps = check_and_import_dependencies()
if missing_deps:
    logging.error(f"Critical dependencies missing: {missing_deps}")
    if 'arcpy' in missing_deps:
        logging.error("Cannot run without ArcPy - exiting")
        sys.exit(1)

# Import config
try:
    from config import (
        get_crime_type_folder, get_7day_period_dates, CRIME_FOLDER_MAPPING, POWERPOINT_TEMPLATES,
        CRIME_TYPES, REPORT_BASE_DIR, get_correct_folder_name, get_standardized_filename, get_output_folder
    )
    logging.info("✅ config imported successfully")
except ImportError as e:
    logging.error(f"ERROR: config import failed: {e}")
    logging.error("config.py is required - cannot continue")
    sys.exit(1)

def import_local_modules():
    """Import local modules with fallback handling"""
    modules_status = {}
    
    try:
        from map_export import export_maps
        modules_status['map_export'] = True
        logging.info("✅ map_export imported successfully")
    except ImportError as e:
        logging.error(f"ERROR: map_export import failed: {e}")
        modules_status['map_export'] = False
        def export_maps(crime_type, output_folder, args):
            logging.error(f"Map export unavailable for {crime_type}")
            return False
    
    try:
        from chart_export import export_chart
        modules_status['chart_export'] = True
        logging.info("✅ chart_export imported successfully")
    except ImportError as e:
        logging.warning(f"WARNING: chart_export import failed: {e}")
        modules_status['chart_export'] = False
        def export_chart(crime_type):
            logging.warning(f"Chart export skipped for {crime_type} - chart_export.py not available")
            return True
    
    try:
        from incident_table_automation import export_incident_table_data_with_autofit, create_incident_table_placeholder
        modules_status['incident_table'] = True
        logging.info("✅ incident_table_automation imported successfully")
    except ImportError as e:
        logging.warning(f"WARNING: incident_table_automation import failed: {e}")
        modules_status['incident_table'] = False
        def export_incident_table_data_with_autofit(crime_type, target_date):
            logging.warning(f"Incident table export skipped for {crime_type}")
            return True
        def create_incident_table_placeholder(crime_type, output_path):
            logging.warning(f"Incident table placeholder skipped for {crime_type}")
            return True
    
    return modules_status, export_maps, export_chart, export_incident_table_data_with_autofit, create_incident_table_placeholder

modules_status, export_maps, export_chart, export_incident_table_data_with_autofit, create_incident_table_placeholder = import_local_modules()
from pptx import Presentation
from pptx.util import Inches

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

POWERPOINT_COORDINATES = {
    'chart': {'left': 0.5, 'top': 2.8, 'width': 5.84, 'height': 4.00},
    'map': {'left': 6.8, 'top': 2.8, 'width': 5.60, 'height': 4.03},
    'table': {'left': 6.8, 'top': 0.8, 'width': 8.33, 'height': 1.98}
}

def get_date_string():
    """Helper to get current date string"""
    return dt_date.today().strftime("%Y_%m_%d")

def parse_date_string(date_str):
    """Parse date string to date object"""
    try:
        if isinstance(date_str, str):
            return dt_datetime.strptime(date_str, "%Y_%m_%d").date()
        elif isinstance(date_str, dt_date):
            return date_str
        elif isinstance(date_str, dt_datetime):
            return date_str.date()
        else:
            return dt_date.today()
    except:
        return dt_date.today()

def auto_complete_remaining_components(crime_types, report_date_str, successful_maps):
    """
    Automatically generate charts and tables for crime types with successful maps
    """
    print(f"\n🔄 AUTO-COMPLETING REMAINING COMPONENTS")
    print("=" * 60)
    
    # Only process crime types that had successful maps
    target_crimes = [crime for crime in crime_types if successful_maps.get(crime, False)]
    
    if not target_crimes:
        print("❌ No successful maps found - skipping auto-completion")
        return {}
    
    print(f"📊 Auto-generating charts and tables for {len(target_crimes)} crime types...")
    
    results = {
        'charts': {},
        'tables': {},
        'powerpoint': False
    }
    
    # Generate charts for successful map crimes
    if modules_status.get('chart_export', False):
        print(f"\n📈 GENERATING CHARTS")
        print("-" * 30)
        
        for crime_type in target_crimes:
            print(f"Processing chart for {crime_type}...")
            try:
                chart_success = export_chart(crime_type)
                results['charts'][crime_type] = chart_success
                status = "✅ SUCCESS" if chart_success else "❌ FAILED"
                print(f"  {status}: {crime_type} chart")
            except Exception as e:
                print(f"  ❌ ERROR: {crime_type} chart failed - {e}")
                results['charts'][crime_type] = False
    else:
        print("⚠️ Chart export not available - skipping charts")
    
    # Generate tables for successful map crimes
    if modules_status.get('incident_table', False):
        print(f"\n📋 GENERATING INCIDENT TABLES")
        print("-" * 30)
        
        target_date = dt_datetime.strptime(report_date_str, "%Y_%m_%d").date()
        
        for crime_type in target_crimes:
            print(f"Processing table for {crime_type}...")
            try:
                table_success = export_incident_table_data_with_autofit(crime_type, target_date)
                if not table_success:
                    # Create placeholder if no data
                    crime_folder = get_crime_type_folder(crime_type, report_date_str)
                    filename_prefix = get_standardized_filename(crime_type)
                    placeholder_path = os.path.join(crime_folder, f"{filename_prefix}_IncidentTable_Placeholder.png")
                    table_success = create_incident_table_placeholder(crime_type, placeholder_path)
                
                results['tables'][crime_type] = table_success
                status = "✅ SUCCESS" if table_success else "❌ FAILED"
                print(f"  {status}: {crime_type} table")
            except Exception as e:
                print(f"  ❌ ERROR: {crime_type} table failed - {e}")
                results['tables'][crime_type] = False
    else:
        print("⚠️ Table export not available - skipping tables")
    
    # Auto-assemble PowerPoint if we have components
    print(f"\n🎯 AUTO-ASSEMBLING POWERPOINT")
    print("-" * 30)
    
    try:
        output_folder = get_output_folder(report_date_str)
        ppt_success = auto_assemble_powerpoint_final(output_folder, target_crimes, report_date_str)
        results['powerpoint'] = ppt_success
        status = "✅ SUCCESS" if ppt_success else "❌ FAILED"
        print(f"  {status}: PowerPoint assembly")
    except Exception as e:
        print(f"  ❌ ERROR: PowerPoint assembly failed - {e}")
        results['powerpoint'] = False
    
    # Summary report
    print(f"\n📊 AUTO-COMPLETION SUMMARY")
    print("=" * 50)
    
    chart_success_count = sum(1 for success in results['charts'].values() if success)
    table_success_count = sum(1 for success in results['tables'].values() if success)
    
    print(f"Charts completed: {chart_success_count}/{len(target_crimes)}")
    print(f"Tables completed: {table_success_count}/{len(target_crimes)}")
    print(f"PowerPoint: {'✅ SUCCESS' if results['powerpoint'] else '❌ FAILED'}")
    
    return results

def auto_assemble_powerpoint_final(output_folder, crime_types, report_date_str):
    """Final PowerPoint assembly - overlays new images on existing template"""
    try:
        ppt_files = glob.glob(os.path.join(output_folder, "*.pptx"))
        if not ppt_files:
            logging.error(f"No PowerPoint file found in: {output_folder}")
            return False
            
        ppt_file = ppt_files[0]
        logging.info(f"Loading PowerPoint: {os.path.basename(ppt_file)}")
        
        try:
            prs = Presentation(ppt_file)
            logging.info(f"PowerPoint loaded successfully - {len(prs.slides)} slides found")
        except Exception as e:
            logging.error(f"PowerPoint file appears corrupted: {e}")
            return False
        
        slides_processed = 0
        for i, crime_type in enumerate(crime_types):
            if i >= len(prs.slides):
                logging.warning(f"No slide available for {crime_type} (slide {i+1}), skipping")
                continue
                
            slide = prs.slides[i]
            crime_output_folder = get_crime_type_folder(crime_type, report_date_str)
            filename_prefix = get_standardized_filename(crime_type)
            
            logging.info(f"Processing slide {i+1}: {crime_type}")
            
            try:
                chart_left = Inches(POWERPOINT_COORDINATES['chart']['left'])
                chart_top = Inches(POWERPOINT_COORDINATES['chart']['top'])
                chart_width = Inches(POWERPOINT_COORDINATES['chart']['width'])
                chart_height = Inches(POWERPOINT_COORDINATES['chart']['height'])
                
                map_left = Inches(POWERPOINT_COORDINATES['map']['left'])
                map_top = Inches(POWERPOINT_COORDINATES['map']['top'])
                map_width = Inches(POWERPOINT_COORDINATES['map']['width'])
                map_height = Inches(POWERPOINT_COORDINATES['map']['height'])
                
                table_left = Inches(POWERPOINT_COORDINATES['table']['left'])
                table_top = Inches(POWERPOINT_COORDINATES['table']['top'])
                table_width = Inches(POWERPOINT_COORDINATES['table']['width'])
                table_height = Inches(POWERPOINT_COORDINATES['table']['height'])
            except Exception as e:
                logging.error(f"Error setting coordinates: {e}")
                continue
            
            # Add chart
            chart_path = os.path.join(crime_output_folder, f"{filename_prefix}_Chart.png")
            if os.path.exists(chart_path):
                try:
                    slide.shapes.add_picture(chart_path, chart_left, chart_top, chart_width, chart_height)
                    logging.info(f"  ✅ Added chart: {filename_prefix}_Chart.png")
                except Exception as e:
                    logging.error(f"  Failed to add chart: {e}")
            
            # Add map
            map_path = os.path.join(crime_output_folder, f"{filename_prefix}_Map.png")
            if os.path.exists(map_path):
                try:
                    slide.shapes.add_picture(map_path, map_left, map_top, map_width, map_height)
                    logging.info(f"  ✅ Added map: {filename_prefix}_Map.png")
                except Exception as e:
                    logging.error(f"  Failed to add map: {e}")
            
            # Add incident table
            table_paths = [
                os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable_AutoFit.png"),
                os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable.png"),
                os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable_Placeholder.png")
            ]
            
            for table_path in table_paths:
                if os.path.exists(table_path):
                    try:
                        slide.shapes.add_picture(table_path, table_left, table_top, table_width, table_height)
                        logging.info(f"  ✅ Added incident table: {os.path.basename(table_path)}")
                        break
                    except Exception as e:
                        logging.error(f"  Failed to add incident table: {e}")
            
            slides_processed += 1
        
        try:
            prs.save(ppt_file)
            logging.info(f"PowerPoint assembly completed: {os.path.basename(ppt_file)}")
            return True
        except Exception as e:
            logging.error(f"Failed to save PowerPoint: {e}")
            return False
        
    except Exception as e:
        logging.error(f"PowerPoint assembly failed: {e}")
        return False

def process_crime_type(crime_type, report_date, report_date_str, generate_map=True, generate_chart=True, generate_table=True):
    """Process a single crime type with enhanced error handling"""
    start_time = time.time()
    logging.info(f"\n{'='*50}")
    logging.info(f"PROCESSING: {crime_type}")
    logging.info(f"{'='*50}")

    success = True
    errors = []

    try:
        output_folder = get_crime_type_folder(crime_type, report_date_str)
        logging.info(f"Output folder: {output_folder}")
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)
            logging.info(f"Created output folder: {output_folder}")
            
    except Exception as e:
        logging.error(f"Failed to get/create output folder: {e}")
        return False

    if generate_map and modules_status.get('map_export', False):
        logging.info("\nRunning map export...")
        try:
            success_map = export_maps(crime_type, output_folder, sys.argv)
            if success_map:
                logging.info("Map export completed successfully")
            else:
                logging.error("Map export failed")
                errors.append("Map export failed")
            success &= success_map
        except Exception as e:
            logging.error(f"Map export crashed: {e}")
            errors.append(f"Map export crashed: {e}")
            success = False
    elif generate_map:
        logging.error("Map export requested but map_export.py not available")
        errors.append("Map export unavailable")
        success = False

    if generate_chart and modules_status.get('chart_export', False):
        logging.info("\nRunning chart export...")
        try:
            success_chart = export_chart(crime_type)
            if success_chart:
                logging.info("Chart export completed successfully")
            else:
                logging.error("Chart export failed")
                errors.append("Chart export failed")
            success &= success_chart
        except Exception as e:
            logging.error(f"Chart export crashed: {e}")
            errors.append(f"Chart export crashed: {e}")
            success = False
    elif generate_chart:
        logging.warning("Chart export skipped - chart_export.py not available")

    if generate_table and modules_status.get('incident_table', False):
        logging.info("\nRunning incident table export...")
        try:
            success_table = export_incident_table_data_with_autofit(crime_type, report_date)
            if not success_table:
                logging.warning(f"Creating placeholder for {crime_type}")
                placeholder_path = os.path.join(output_folder, f"{get_standardized_filename(crime_type)}_IncidentTable_Placeholder.png")
                success_table = create_incident_table_placeholder(crime_type, placeholder_path)
                if success_table:
                    logging.info("Placeholder created successfully")
                else:
                    logging.error("Placeholder creation failed")
                    errors.append("Placeholder creation failed")
            else:
                logging.info("Incident table export completed successfully")
            success &= success_table
        except Exception as e:
            logging.error(f"Incident table export crashed: {e}")
            errors.append(f"Incident table crashed: {e}")
            success = False
    elif generate_table:
        logging.warning("Incident table export skipped - incident_table_automation.py not available")

    duration = time.time() - start_time
    logging.info(f"\nPROCESSING SUMMARY FOR {crime_type}")
    logging.info(f"Duration: {duration:.2f} seconds")
    logging.info(f"Success: {'YES' if success else 'NO'}")
    
    if errors:
        logging.info(f"Errors encountered:")
        for error in errors:
            logging.info(f"  • {error}")
    
    return success

def create_output_folder_and_copy_template(report_date_str):
    """Create output folder and copy PowerPoint template with enhanced error handling"""
    try:
        output_folder = get_output_folder(report_date_str)
        logging.info(f"Creating output folder: {output_folder}")
        
        os.makedirs(output_folder, exist_ok=True)
        if not os.path.exists(output_folder):
            logging.error(f"Failed to create output folder: {output_folder}")
            return None
        
        template_path = POWERPOINT_TEMPLATES.get("7day") or POWERPOINT_TEMPLATES.get("main")
        if template_path and os.path.exists(template_path):
            folder_name = get_correct_folder_name(report_date_str)
            dest_ppt = os.path.join(output_folder, f"{folder_name}.pptx")
            
            try:
                shutil.copy2(template_path, dest_ppt)
                logging.info(f"Copied PowerPoint template: {os.path.basename(dest_ppt)}")
                
                if not os.path.exists(dest_ppt):
                    logging.error(f"PowerPoint copy verification failed: {dest_ppt}")
                    return None
                    
            except Exception as e:
                logging.error(f"Failed to copy PowerPoint template: {e}")
                return None
        else:
            logging.error(f"PowerPoint template not found: {template_path}")
            
        return output_folder
        
    except Exception as e:
        logging.error(f"Failed to create output folder: {e}")
        return None

def validate_system_readiness():
    """Validate system is ready to run"""
    logging.info("\nVALIDATING SYSTEM READINESS")
    logging.info("=" * 50)
    
    issues = []
    
    missing_modules = [name for name, status in modules_status.items() if not status]
    if missing_modules:
        issues.append(f"Missing modules: {missing_modules}")
    
    try:
        if not CRIME_TYPES:
            issues.append("No crime types defined")
    except Exception as e:
        issues.append(f"Cannot access CRIME_TYPES: {e}")
    
    if issues:
        logging.warning("SYSTEM READINESS ISSUES:")
        for issue in issues:
            logging.warning(f"  • {issue}")
        logging.warning("Proceeding with limited functionality...")
    else:
        logging.info("SYSTEM READY")
    
    return len(issues) == 0

def main(generate_maps=True, generate_charts=True, generate_tables=True, max_features=30, debug_mode=False, report_date_str=None):
    """Main processing function with enhanced error handling and auto-completion"""
    batch_start = time.time()
    overall_success = True
    crime_results = {}
    successful_maps = {}
    
    try:
        if report_date_str is None:
            report_date_str = get_date_string()
        
        report_date = parse_date_string(report_date_str)
        
        logging.info(f"\nCRIME ANALYSIS SESSION STARTING")
        logging.info(f"Date: {report_date_str}")
        logging.info(f"Parameters:")
        logging.info(f"  • Maps: {generate_maps}")
        logging.info(f"  • Charts: {generate_charts}")
        logging.info(f"  • Tables: {generate_tables}")
        logging.info(f"  • Max Features: {max_features}")
        logging.info(f"  • Debug Mode: {debug_mode}")

        system_ready = validate_system_readiness()
        if not system_ready:
            logging.warning("System has issues but continuing...")

        output_folder = create_output_folder_and_copy_template(report_date_str)
        if not output_folder:
            logging.error("Failed to create output folder - cannot continue")
            return False

        logging.info(f"\nPROCESSING {len(CRIME_TYPES)} CRIME TYPES")
        logging.info("=" * 60)
        
        for i, crime_type in enumerate(CRIME_TYPES, 1):
            logging.info(f"\n[{i}/{len(CRIME_TYPES)}] Starting {crime_type}")
            
            success = process_crime_type(
                crime_type, 
                report_date, 
                report_date_str, 
                generate_map=generate_maps, 
                generate_chart=generate_charts, 
                generate_table=generate_tables
            )
            
            crime_results[crime_type] = success
            overall_success &= success
            
            # Track successful maps for auto-completion
            if generate_maps and success:
                successful_maps[crime_type] = True
                
            logging.info(f"[{i}/{len(CRIME_TYPES)}] {crime_type}: {'SUCCESS' if success else 'FAILED'}")

        # AUTO-COMPLETION LOGIC
        # If maps were generated but charts/tables weren't, auto-complete them
        auto_complete_needed = (
            generate_maps and 
            not generate_charts and 
            not generate_tables and
            any(successful_maps.values())
        )
        
        if auto_complete_needed:
            logging.info(f"\n🚀 AUTO-COMPLETION TRIGGERED")
            logging.info("Maps completed successfully - auto-generating charts and tables...")
            
            auto_results = auto_complete_remaining_components(CRIME_TYPES, report_date_str, successful_maps)
            
            # Update overall success based on auto-completion
            if auto_results:
                chart_success = all(auto_results['charts'].values()) if auto_results['charts'] else True
                table_success = all(auto_results['tables'].values()) if auto_results['tables'] else True
                ppt_success = auto_results.get('powerpoint', False)
                
                # Consider auto-completion successful if majority of components worked
                auto_success = sum([chart_success, table_success, ppt_success]) >= 2
                overall_success = overall_success and auto_success
        
        # STANDARD POWERPOINT ASSEMBLY (if not auto-completed)
        elif not auto_complete_needed:
            logging.info(f"\nASSEMBLING POWERPOINT PRESENTATION")
            logging.info("=" * 50)
            
            try:
                success_ppt = auto_assemble_powerpoint_final(output_folder, CRIME_TYPES, report_date_str)
                if success_ppt:
                    logging.info("PowerPoint assembly completed successfully")
                else:
                    logging.error("PowerPoint assembly failed")
                    overall_success = False
            except Exception as e:
                logging.error(f"PowerPoint assembly crashed: {e}")
                import traceback
                logging.error(traceback.format_exc())
                overall_success = False

        total_time = time.time() - batch_start
        logging.info(f"\nSESSION COMPLETE")
        logging.info("=" * 60)
        logging.info(f"Total time: {total_time:.2f} seconds")
        logging.info(f"Overall success: {'SUCCESS' if overall_success else 'FAILED'}")
        logging.info(f"Output folder: {output_folder}")
        
        logging.info(f"\nCRIME TYPE RESULTS:")
        for crime_type, success in crime_results.items():
            status = "SUCCESS" if success else "FAILED"
            logging.info(f"  • {crime_type}: {status}")
        
        successful_crimes = sum(1 for success in crime_results.values() if success)
        logging.info(f"\nSUCCESS RATE: {successful_crimes}/{len(CRIME_TYPES)} crime types")
        
        # AUTO-COMPLETION SUMMARY
        if auto_complete_needed and 'auto_results' in locals():
            logging.info(f"\nAUTO-COMPLETION RESULTS:")
            if auto_results.get('charts'):
                chart_count = sum(1 for success in auto_results['charts'].values() if success)
                logging.info(f"  • Charts: {chart_count}/{len(auto_results['charts'])}")
            if auto_results.get('tables'):
                table_count = sum(1 for success in auto_results['tables'].values() if success)
                logging.info(f"  • Tables: {table_count}/{len(auto_results['tables'])}")
            logging.info(f"  • PowerPoint: {'SUCCESS' if auto_results.get('powerpoint') else 'FAILED'}")
        
        return overall_success
        
    except Exception as e:
        logging.error(f"Main function failed: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    if len(sys.argv) >= 7:
        try:
            result = main(
                generate_maps=sys.argv[1].lower() == 'true',
                generate_charts=sys.argv[2].lower() == 'true',
                generate_tables=sys.argv[3].lower() == 'true',
                max_features=int(sys.argv[4]),
                debug_mode=sys.argv[5].lower() == 'true',
                report_date_str=sys.argv[6]
            )
            exit_code = 0 if result else 1
            logging.info(f"Exiting with code: {exit_code}")
            sys.exit(exit_code)
        except ValueError as e:
            logging.error(f"Invalid argument values: {e}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            import traceback
            logging.error(traceback.format_exc())
            sys.exit(1)
    else:
        print("USAGE ERROR")
        print("Usage options:")
        print("  python main.py --debug [YYYY_MM_DD]     # Debug mode with optional date")
        print("  python main.py --validate               # Validation mode only")
        print("  python main.py true true false 30 false YYYY_MM_DD  # Full processing")
        print("\nExamples:")
        print("  python main.py --debug")
        print("  python main.py --debug 2025_06_24")
        print("  python main.py --validate")
        print("  python main.py true true false 30 false 2025_06_24")
        print("\nAUTO-COMPLETION MODE:")
        print("  python main.py true false false 30 false YYYY_MM_DD  # Maps only, auto-completes charts/tables")
        sys.exit(1)