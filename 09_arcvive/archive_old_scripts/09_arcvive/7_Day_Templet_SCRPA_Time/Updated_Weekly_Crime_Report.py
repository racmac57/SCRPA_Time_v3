#!/usr/bin/env python3
#"""
#Weekly Crime Report Automation - Hackensack Police Department
#Author: R. Carucci
#Purpose: Automated crime report generation with chart export capabilities
#Last Updated: 2025-05-30
#"""

import sys
import os
import datetime
from pathlib import Path
import logging
from typing import List, Optional

# Third-party imports
try:
    import arcpy
    from fpdf import FPDF
    import pandas as pd
except ImportError as e:
    print(f"Critical import error: {e}")
    print("Please ensure ArcGIS Pro Python environment is properly configured")
    sys.exit(1)

# Local imports - import your existing modules
try:
    from config import CRIME_TYPES, SUFFIXES, validate_configuration, get_sanitized_filename
    from logger import log_action, log_error_with_details, log_crime_analysis, log_data_export
    from map_export import export_maps
    from chart_export import export_chart
    from table_export import export_tables
    from report_packager import package_report
    from args_parser import parse_args_legacy
except ImportError as e:
    print(f"Local module import error: {e}")
    print("Please ensure all required modules are in the Python path")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crime_report_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_report_name_from_date(target_date_str):
    """
    Load Excel file and return the corresponding Report_Name for the given date.
    
    Args:
        target_date_str (str): Date in format 'YYYY_MM_DD' (e.g., '2025_05_13')
    
    Returns:
        str: Report_Name (e.g., 'C05W19') or fallback name if not found
    """
    # Updated with correct Excel file path
    excel_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\InBox\GIS_Tools\7Day_28Day_Cycle_20250414.xlsx"
    
    try:
        # Load the Excel file
        df = pd.read_excel(excel_path, sheet_name="7Day_28Day_250414")
        
        # Convert Report_Due_Date column to datetime
        df['Report_Due_Date'] = pd.to_datetime(df['Report_Due_Date'])
        
        # Convert target date from 'YYYY_MM_DD' to datetime
        target_date = pd.to_datetime(target_date_str.replace('_', '-'))
        
        # Find matching record
        match = df[df['Report_Due_Date'].dt.date == target_date.date()]
        
        if not match.empty:
            report_name = match.iloc[0]['Report_Name']
            logger.info(f"Found Report_Name: {report_name} for date: {target_date_str}")
            arcpy.AddMessage(f"Found Report_Name: {report_name} for date: {target_date_str}")
            log_crime_analysis(f"Dynamic folder name: {report_name} for {target_date_str}")
            return report_name
        else:
            logger.warning(f"No matching Report_Name for date: {target_date_str}")
            arcpy.AddWarning(f"No matching Report_Name for date: {target_date_str}")
            return f"UNKNOWN_{target_date_str}"
            
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        arcpy.AddError(f"Error reading Excel file: {e}")
        log_error_with_details("Excel file read failed", e)
        return f"ERROR_{target_date_str}"

def get_crime_type_subfolder(crime_type):
    """
    Convert crime type name to a clean subfolder name.
    
    Args:
        crime_type (str): Crime type name (e.g., "MV Theft", "Burglary - Auto")
    
    Returns:
        str: Clean subfolder name (e.g., "Motor_Vehicle_Theft", "Burglary_Auto")
    """
    # Define mapping of crime types to folder names
    crime_type_mapping = {
        'mv theft': 'Motor_Vehicle_Theft',
        'motor vehicle theft': 'Motor_Vehicle_Theft',
        'burglary - auto': 'Burglary_Auto',
        'burglary auto': 'Burglary_Auto',
        'burglary - comm & res': 'Burglary_Commercial_Residential',
        'burglary comm & res': 'Burglary_Commercial_Residential',
        'burglary commercial': 'Burglary_Commercial_Residential',
        'burglary residential': 'Burglary_Commercial_Residential',
        'robbery': 'Robbery',
        'sexual offenses': 'Sexual_Offenses',
        'sex offenses': 'Sexual_Offenses',
        'assault': 'Assault',
        'domestic violence': 'Domestic_Violence',
        'drugs': 'Drugs',
        'vandalism': 'Vandalism',
        'fraud': 'Fraud',
        'theft': 'Theft',
        'weapons': 'Weapons'
    }
    
    # Convert to lowercase for matching
    crime_lower = crime_type.lower().strip()
    
    # Check for matches in the mapping
    for key, value in crime_type_mapping.items():
        if key in crime_lower:
            return value
    
    # If no match found, create a clean folder name
    clean_name = crime_type.replace(' - ', '_').replace(' & ', '_').replace(' ', '_').replace('-', '_')
    return clean_name

def create_dynamic_folder_structure(base_folder: str, date_str: str, crime_types: List[str]) -> str:
    """
    Create the main folder and crime-type subfolders using dynamic naming.
    
    Args:
        base_folder (str): Base reports folder path
        date_str (str): Date in YYYY_MM_DD format
        crime_types (List[str]): List of crime types to create subfolders for
    
    Returns:
        str: Path to the main folder created
    """
    try:
        # Get the report name from Excel based on date
        report_name = get_report_name_from_date(date_str)
        
        # Create main folder name: ReportName_Date (e.g., C05W22_2025_05_27)
        main_folder_name = f"{report_name}_{date_str}"
        main_folder_path = os.path.join(base_folder, main_folder_name)
        
        # Create main folder
        Path(main_folder_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created main folder: {main_folder_path}")
        arcpy.AddMessage(f"Created main folder: {main_folder_path}")
        log_data_export(f"Created dynamic folder: {main_folder_name}")
        
        # Create subfolders for each crime type
        created_subfolders = []
        for crime_type in crime_types:
            subfolder_name = get_crime_type_subfolder(crime_type)
            subfolder_path = os.path.join(main_folder_path, subfolder_name)
            
            Path(subfolder_path).mkdir(parents=True, exist_ok=True)
            created_subfolders.append(subfolder_name)
            logger.info(f"Created subfolder: {subfolder_path}")
        
        arcpy.AddMessage(f"Created {len(created_subfolders)} crime type subfolders: {', '.join(created_subfolders)}")
        log_data_export(f"Created {len(created_subfolders)} crime subfolders")
        
        return main_folder_path
        
    except Exception as e:
        logger.error(f"Error creating dynamic folder structure: {e}")
        arcpy.AddError(f"Error creating dynamic folder structure: {e}")
        log_error_with_details("Dynamic folder creation failed", e)
        # Fallback to simple date-based folder
        fallback_folder = os.path.join(base_folder, f"Reports_{date_str}")
        Path(fallback_folder).mkdir(parents=True, exist_ok=True)
        return fallback_folder

def validate_environment():
    """Validate that the environment is properly set up for automation."""
    try:
        # Check ArcGIS Pro license
        if arcpy.CheckProduct("ArcInfo") not in ["Available", "AlreadyInitialized"]:
            raise RuntimeError("ArcGIS Pro Advanced license not available")
        
        # Check required extensions
        if arcpy.CheckExtension("Spatial") != "Available":
            raise RuntimeError("Spatial Analyst extension not available")
        
        # Validate configuration
        is_valid, issues = validate_configuration()
        if not is_valid:
            logger.warning("Configuration validation issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        
        logger.info("Environment validation successful")
        return True
        
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return False

def run_all_reports(main_folder_path: str, crime_types: List[str], chart_suffixes: List[str], args):
    """
    Run all report generation using existing modules with organized output.
    
    Args:
        main_folder_path (str): Path to the main output folder
        crime_types (List[str]): List of crime types to process
        chart_suffixes (List[str]): Chart suffixes from config
        args: Parsed arguments
    """
    try:
        log_crime_analysis("Starting comprehensive report generation")
        
        successful_exports = 0
        failed_exports = 0
        
        for crime_type in crime_types:
            try:
                logger.info(f"Processing crime type: {crime_type}")
                arcpy.AddMessage(f"Processing: {crime_type}")
                
                # Get the crime-type specific subfolder
                subfolder_name = get_crime_type_subfolder(crime_type)
                crime_output_folder = os.path.join(main_folder_path, subfolder_name)
                
                # Ensure subfolder exists
                Path(crime_output_folder).mkdir(exist_ok=True)
                
                crime_success = True
                
                # 1. Export Maps (if not dry run)
                if not args.dry_run:
                    try:
                        logger.info(f"Exporting maps for {crime_type}")
                        map_success = export_maps(crime_type, crime_output_folder, sys.argv)
                        if not map_success:
                            logger.warning(f"Map export failed for {crime_type}")
                            crime_success = False
                        else:
                            log_data_export(f"Maps exported for {crime_type}")
                    except Exception as e:
                        logger.error(f"Map export error for {crime_type}: {e}")
                        log_error_with_details(f"Map export failed for {crime_type}", e)
                        crime_success = False
                
                # 2. Export Charts (if not dry run)
                if not args.dry_run:
                    try:
                        logger.info(f"Exporting charts for {crime_type}")
                        # Note: chart_export saves to its configured directory by default
                        # You may need to modify chart_export to accept output folder parameter
                        chart_success = export_chart(crime_type)
                        if not chart_success:
                            logger.warning(f"Chart export failed for {crime_type}")
                            crime_success = False
                        else:
                            log_data_export(f"Charts exported for {crime_type}")
                    except Exception as e:
                        logger.error(f"Chart export error for {crime_type}: {e}")
                        log_error_with_details(f"Chart export failed for {crime_type}", e)
                        crime_success = False
                
                # 3. Export Tables (if not dry run)
                if not args.dry_run:
                    try:
                        logger.info(f"Exporting tables for {crime_type}")
                        table_result = export_tables(crime_type, crime_output_folder)
                        if table_result['status'] != 'success':
                            logger.warning(f"Table export had issues for {crime_type}: {table_result.get('status')}")
                        else:
                            log_data_export(f"Tables exported for {crime_type}")
                    except Exception as e:
                        logger.error(f"Table export error for {crime_type}: {e}")
                        log_error_with_details(f"Table export failed for {crime_type}", e)
                        crime_success = False
                
                # 4. Package Reports (if not dry run)
                if not args.dry_run:
                    try:
                        logger.info(f"Packaging report for {crime_type}")
                        package_success = package_report(crime_type, crime_output_folder, args)
                        if not package_success:
                            logger.warning(f"Report packaging failed for {crime_type}")
                        else:
                            log_data_export(f"Report packaged for {crime_type}")
                    except Exception as e:
                        logger.error(f"Report packaging error for {crime_type}: {e}")
                        log_error_with_details(f"Report packaging failed for {crime_type}", e)
                
                # Track results
                if crime_success:
                    successful_exports += 1
                    arcpy.AddMessage(f"✅ Completed: {crime_type}")
                else:
                    failed_exports += 1
                    arcpy.AddWarning(f"⚠️ Issues with: {crime_type}")
                
            except Exception as e:
                failed_exports += 1
                logger.error(f"Critical error processing {crime_type}: {e}")
                arcpy.AddError(f"Critical error processing {crime_type}: {e}")
                log_error_with_details(f"Critical error for {crime_type}", e)
        
        # Summary
        total_types = len(crime_types)
        arcpy.AddMessage(f"Report generation complete: {successful_exports}/{total_types} successful")
        log_crime_analysis(f"Report generation summary: {successful_exports}/{total_types} successful")
        
        if failed_exports > 0:
            arcpy.AddWarning(f"{failed_exports} crime types had errors - check logs")
        
    except Exception as e:
        logger.error(f"Critical error in run_all_reports: {e}")
        arcpy.AddError(f"Critical error in run_all_reports: {e}")
        log_error_with_details("run_all_reports failed", e)
        raise

def create_dry_run_summary(main_folder_path: str, crime_types: List[str]) -> str:
    """Create a dry run summary PDF."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Weekly Crime Report DRY RUN Summary", ln=1)
        
        pdf.set_font("Arial", "", 12)
        pdf.ln(5)
        
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf.cell(0, 8, f"Generated: {timestamp}", ln=1)
        pdf.ln(5)
        
        pdf.multi_cell(0, 8, 
            "This report summarizes simulated actions for the weekly crime report automation. "
            "No actual files were generated, modified, or sent during this dry run.")
        
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, f"Target Folder: {os.path.basename(main_folder_path)}", ln=1)
        pdf.ln(3)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Crime Types to Process:", ln=1)
        pdf.set_font("Arial", "", 10)
        
        for crime_type in crime_types:
            subfolder_name = get_crime_type_subfolder(crime_type)
            pdf.cell(0, 6, f"• {crime_type} → {subfolder_name}/", ln=1)
        
        # Ensure output directory exists
        Path(main_folder_path).mkdir(parents=True, exist_ok=True)
        
        pdf_path = os.path.join(main_folder_path, f"DRY_RUN_Summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        pdf.output(pdf_path)
        
        logger.info(f"DRY RUN summary PDF generated at: {pdf_path}")
        return pdf_path
        
    except Exception as e:
        logger.error(f"Failed to create dry run summary: {e}")
        raise

def main():
    """Main execution function for the crime report automation."""
    logger.info("Starting Weekly Crime Report Automation with Dynamic Folders")
    log_action("Weekly Crime Report Automation started", "SYSTEM")
    
    try:
        # Validate environment
        if not validate_environment():
            logger.error("Environment validation failed - exiting")
            sys.exit(1)
        
        # Parse command line arguments using your existing parser
        args = parse_args_legacy()
        
        logger.info(f"Arguments: report={args.report}, email={args.email}, "
                   f"archive={args.archive}, archive_days={args.archive_days}, "
                   f"dry_run={args.dry_run}, date={args.date}")
        
        # Get crime types from config
        crime_types = CRIME_TYPES
        
        # Get chart suffixes from config
        chart_suffixes = SUFFIXES
        
        # Set base folder for reports
        base_folder = r"C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reports"
        
        # Ensure base folder exists
        Path(base_folder).mkdir(parents=True, exist_ok=True)
        
        # Create dynamic folder structure based on date
        if args.date:
            main_folder_path = create_dynamic_folder_structure(base_folder, args.date, crime_types)
            logger.info(f"Using dynamic folder structure: {main_folder_path}")
        else:
            # Fallback to base folder if no date provided
            main_folder_path = base_folder
            logger.warning("No date provided - using base folder without dynamic structure")
        
        # Execute report generation if requested
        if args.report:
            logger.info("Starting report generation")
            try:
                run_all_reports(main_folder_path, crime_types, chart_suffixes, args)
                log_action("Report generation completed successfully", "REPORT")
            except Exception as e:
                log_error_with_details("Report generation failed", e)
                raise
        
        # Generate dry run summary if in dry run mode
        if args.dry_run:
            logger.info("Generating dry run summary")
            try:
                summary_path = create_dry_run_summary(main_folder_path, crime_types)
                arcpy.AddMessage(f"DRY RUN summary PDF generated at: {summary_path}")
            except Exception as e:
                log_error_with_details("Failed to generate dry run summary", e)
        
        logger.info("Weekly Crime Report Automation completed successfully")
        log_action("Weekly Crime Report Automation completed", "SYSTEM")
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}")
        log_error_with_details("Fatal error in crime report automation", e)
        sys.exit(1)

if __name__ == '__main__':
    main()