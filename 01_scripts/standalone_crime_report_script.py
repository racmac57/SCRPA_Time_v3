#!/usr/bin/env python3
#"""
#Fixed Standalone Weekly Crime Report Automation - Hackensack Police Department
#Author: R. Carucci
#Purpose: Self-contained script for dynamic folder creation and map exports
#Last Updated: 2025-05-30
#"""

import sys
import os
import datetime
from pathlib import Path
import logging

# Essential imports only
try:
    import arcpy
    import pandas as pd
except ImportError as e:
    print(f"Critical import error: {e}")
    print("Please ensure ArcGIS Pro Python environment is properly configured")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('standalone_crime_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants (self-contained)
CRIME_TYPES = [
    "MV Theft",
    "Burglary - Auto", 
    "Burglary - Comm & Res",
    "Robbery",
    "Sexual Offenses"
]

SUFFIXES = ["7-Day", "28-Day", "YTD"]

APR_PATH = r"C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\TimeSCRPATemplet\TimeSCRPATemplet.aprx"

BASE_LAYERS = [
    "City Boundaries",
    "OpenStreetMap Light Gray Canvas Reference",
    "Light Gray Canvas (for Export)"
]

TRANSPARENCY_LEVELS = [0, 30, 60]  # Most recent = most opaque

# Layout to Crime Type mapping based on your actual layouts
LAYOUT_TO_CRIME_TYPE = {
    'burglary - auto': 'Burglary_Auto',
    'burglary - comm & res': 'Burglary_Commercial_Residential', 
    'robbery': 'Robbery',
    'sexual offenses': 'Sexual_Offenses',
    'crime_reporting_layout': 'Motor_Vehicle_Theft',  # Assuming this is for MV Theft
    'crime report legend': 'Crime_Report_Legend'  # Skip or handle specially
}

def get_report_name_from_date(target_date_str):
    """
    Load Excel file and return the corresponding Report_Name for the given date.
    """
    excel_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\InBox\GIS_Tools\7Day_28Day_Cycle_20250414.xlsx"
    
    try:
        df = pd.read_excel(excel_path, sheet_name="7Day_28Day_250414")
        df['Report_Due_Date'] = pd.to_datetime(df['Report_Due_Date'])
        target_date = pd.to_datetime(target_date_str.replace('_', '-'))
        match = df[df['Report_Due_Date'].dt.date == target_date.date()]
        
        if not match.empty:
            report_name = match.iloc[0]['Report_Name']
            logger.info(f"Found Report_Name: {report_name} for date: {target_date_str}")
            arcpy.AddMessage(f"Found Report_Name: {report_name} for date: {target_date_str}")
            return report_name
        else:
            logger.warning(f"No matching Report_Name for date: {target_date_str}")
            arcpy.AddWarning(f"No matching Report_Name for date: {target_date_str}")
            return f"UNKNOWN_{target_date_str}"
            
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        arcpy.AddError(f"Error reading Excel file: {e}")
        return f"ERROR_{target_date_str}"

def get_crime_type_subfolder(crime_type):
    """Convert crime type name to a clean subfolder name."""
    crime_type_mapping = {
        'mv theft': 'Motor_Vehicle_Theft',
        'motor vehicle theft': 'Motor_Vehicle_Theft',
        'burglary - auto': 'Burglary_Auto',
        'burglary auto': 'Burglary_Auto',
        'burglary - comm & res': 'Burglary_Commercial_Residential',
        'burglary comm & res': 'Burglary_Commercial_Residential',
        'robbery': 'Robbery',
        'sexual offenses': 'Sexual_Offenses',
        'sex offenses': 'Sexual_Offenses'
    }
    
    crime_lower = crime_type.lower().strip()
    for key, value in crime_type_mapping.items():
        if key in crime_lower:
            return value
    
    # Fallback: clean up the name
    clean_name = crime_type.replace(' - ', '_').replace(' & ', '_').replace(' ', '_').replace('-', '_')
    return clean_name

def get_crime_type_from_layout_name(layout_name):
    """
    Extract crime type from layout name based on actual layout names in project.
    """
    layout_lower = layout_name.lower().strip()
    
    # Use the mapping based on your actual layouts
    for key, value in LAYOUT_TO_CRIME_TYPE.items():
        if key in layout_lower:
            return value
    
    # Fallback
    clean_name = layout_name.replace(' ', '_').replace('-', '_')
    return clean_name

def create_dynamic_folder_structure(base_folder, date_str, crime_types):
    """Create the main folder and crime-type subfolders using dynamic naming."""
    try:
        # Get the report name from Excel based on date
        report_name = get_report_name_from_date(date_str)
        
        # Create main folder name: ReportName_Date (e.g., C06W21_2025_05_27)
        main_folder_name = f"{report_name}_{date_str}"
        main_folder_path = os.path.join(base_folder, main_folder_name)
        
        # Create main folder
        Path(main_folder_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created main folder: {main_folder_path}")
        arcpy.AddMessage(f"Created main folder: {main_folder_path}")
        
        # Create subfolders for each crime type
        created_subfolders = []
        for crime_type in crime_types:
            subfolder_name = get_crime_type_subfolder(crime_type)
            subfolder_path = os.path.join(main_folder_path, subfolder_name)
            
            Path(subfolder_path).mkdir(parents=True, exist_ok=True)
            created_subfolders.append(subfolder_name)
            logger.info(f"Created subfolder: {subfolder_path}")
        
        arcpy.AddMessage(f"Created {len(created_subfolders)} crime type subfolders: {', '.join(created_subfolders)}")
        
        return main_folder_path
        
    except Exception as e:
        logger.error(f"Error creating dynamic folder structure: {e}")
        arcpy.AddError(f"Error creating dynamic folder structure: {e}")
        # Fallback to simple date-based folder
        fallback_folder = os.path.join(base_folder, f"Reports_{date_str}")
        Path(fallback_folder).mkdir(parents=True, exist_ok=True)
        return fallback_folder

def build_sql_filter(crime_type, start_date):
    """Build SQL filter based on crime type."""
    try:
        # Validate start_date format
        datetime.datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        arcpy.AddError(f"Invalid date format for SQL filter: {start_date}")
        return None
    
    # Base conditions
    base_conditions = f'"disposition" LIKE \'%See Report%\' AND "calldate" >= date \'{start_date}\''
    
    # Crime type patterns based on your data
    crime_patterns = {
        'MV Theft': 'Motor Vehicle Theft',
        'Burglary - Auto': 'Burglary - Auto',
        'Burglary - Comm & Res': ['Burglary - Residence', 'Burglary - Commercial'],
        'Robbery': 'Robbery',
        'Sexual Offenses': 'Sexual'
    }
    
    pattern = crime_patterns.get(crime_type, crime_type)
    
    # Build crime condition based on pattern type
    if isinstance(pattern, list):
        conditions = []
        for p in pattern:
            conditions.append(f'"calltype" LIKE \'%{p}%\'')
        crime_condition = f"({' OR '.join(conditions)})"
    else:
        crime_condition = f'"calltype" LIKE \'%{pattern}%\''
    
    sql_filter = f'{crime_condition} AND {base_conditions}'
    return sql_filter

def configure_map_for_crime_type(current_map, crime_type, date_str):
    """Configure map layers for a specific crime type."""
    try:
        # Parse date and calculate time periods
        today = datetime.datetime.strptime(date_str, "%Y_%m_%d")
        
        dates = {
            "7-Day": (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
            "28-Day": (today - datetime.timedelta(days=28)).strftime("%Y-%m-%d"),
            "YTD": today.replace(month=1, day=1).strftime("%Y-%m-%d")
        }
        
        # Hide all crime layers first
        for lyr in current_map.listLayers():
            if not any(base_name in lyr.name for base_name in BASE_LAYERS):
                lyr.visible = False
        
        # Show base layers
        for lyr in current_map.listLayers():
            if any(base_name in lyr.name for base_name in BASE_LAYERS):
                lyr.visible = True
                lyr.transparency = 0
        
        # Show only layers for this specific crime type
        for i, suffix in enumerate(SUFFIXES):
            transparency = TRANSPARENCY_LEVELS[i] if i < len(TRANSPARENCY_LEVELS) else 0
            layer_name = f"{crime_type} {suffix}"
            
            # Find the layer
            layer = None
            for lyr in current_map.listLayers():
                if lyr.name == layer_name:
                    layer = lyr
                    break
            
            if layer:
                layer.visible = True
                layer.transparency = transparency
                
                # Apply definition query if supported
                if layer.supports("DEFINITIONQUERY") and suffix in dates:
                    filter_sql = build_sql_filter(crime_type, dates[suffix])
                    if filter_sql:
                        layer.definitionQuery = filter_sql
                        arcpy.AddMessage(f"Applied query to {layer.name}")
                
                arcpy.AddMessage(f"Configured layer: {layer.name} (transparency: {transparency}%)")
            else:
                arcpy.AddWarning(f"Layer not found: {layer_name}")
        
        return True
        
    except Exception as e:
        arcpy.AddError(f"Error configuring map for {crime_type}: {e}")
        return False

def export_single_crime_layout(layout, main_output_path, crime_type, date_str):
    """Export a single crime type layout to its subfolder as PNG."""
    try:
        # Get the correct subfolder
        subfolder_name = get_crime_type_subfolder(crime_type)
        crime_subfolder = os.path.join(main_output_path, subfolder_name)
        
        # Ensure subfolder exists
        Path(crime_subfolder).mkdir(exist_ok=True)
        
        # Create filename
        safe_date = date_str.replace('_', '-')
        filename = f"{crime_type}_{safe_date}.png"  # Changed to PNG
        full_path = os.path.join(crime_subfolder, filename)
        
        # Export as PNG with high resolution
        layout.exportToPNG(full_path, resolution=300, width=2000, height=1500)
        arcpy.AddMessage(f"Exported PNG: {full_path}")
        
        return True, full_path
        
    except Exception as e:
        arcpy.AddError(f"Error exporting {crime_type}: {e}")
        return False, None

def run_individual_crime_exports(main_folder_path, date_str):
    """Export each crime type individually with proper layer configuration."""
    try:
        # Setup ArcGIS Pro project
        aprx = arcpy.mp.ArcGISProject(APR_PATH)
        
        # Get the map
        maps = aprx.listMaps()
        if not maps:
            raise Exception("No maps found in the project")
        current_map = maps[0]
        
        # Get layouts - skip the "Crime Report Legend" layout
        layouts = aprx.listLayouts()
        crime_layouts = [layout for layout in layouts if layout.name != "Crime Report Legend"]
        
        arcpy.AddMessage(f"Found {len(crime_layouts)} crime-specific layouts")
        
        successful_exports = 0
        failed_exports = 0
        
        # Process each crime-specific layout
        for layout in crime_layouts:
            try:
                layout_name = layout.name
                arcpy.AddMessage(f"Processing layout: {layout_name}")
                
                # Determine crime type from layout name
                if layout_name == "Crime_Reporting_Layout":
                    crime_type = "MV Theft"  # Assuming this is for MV Theft
                elif layout_name in CRIME_TYPES:
                    crime_type = layout_name
                else:
                    # Skip if we can't determine crime type
                    arcpy.AddWarning(f"Skipping unknown layout: {layout_name}")
                    continue
                
                # Configure map for this specific crime type
                arcpy.AddMessage(f"Configuring map for: {crime_type}")
                if configure_map_for_crime_type(current_map, crime_type, date_str):
                    
                    # Export the layout
                    success, export_path = export_single_crime_layout(layout, main_folder_path, crime_type, date_str)
                    
                    if success:
                        successful_exports += 1
                        arcpy.AddMessage(f"✅ Successfully exported: {crime_type}")
                    else:
                        failed_exports += 1
                        arcpy.AddError(f"❌ Failed to export: {crime_type}")
                else:
                    failed_exports += 1
                    arcpy.AddError(f"❌ Failed to configure map for: {crime_type}")
                    
            except Exception as e:
                failed_exports += 1
                arcpy.AddError(f"❌ Error processing {layout_name}: {e}")
        
        # Summary
        total_layouts = len(crime_layouts)
        arcpy.AddMessage(f"Export Summary: {successful_exports}/{total_layouts} successful")
        if failed_exports > 0:
            arcpy.AddWarning(f"{failed_exports} exports failed")
        
        # Clean up
        del aprx
        
        return successful_exports > 0
        
    except Exception as e:
        arcpy.AddError(f"Error in run_individual_crime_exports: {e}")
        return False

def main():
    """Main function to handle command line arguments and execute automation."""
    try:
        # Parse command line arguments
        if len(sys.argv) < 7:
            arcpy.AddError("Usage: script.py <report> <email> <archive> <archive_days> <dry_run> <date>")
            return
        
        report = sys.argv[1].lower() == 'true'
        dry_run = sys.argv[5].lower() == 'true'
        date_str = sys.argv[6]
        
        # Validate date format
        try:
            datetime.datetime.strptime(date_str, '%Y_%m_%d')
        except ValueError:
            arcpy.AddError("Date must be in format YYYY_MM_DD (e.g., 2025_05_27)")
            return
        
        arcpy.AddMessage(f"Starting FIXED crime report automation...")
        arcpy.AddMessage(f"Date: {date_str}, Dry Run: {dry_run}")
        
        # Set base folder
        base_folder = r"C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reports"
        
        # Create dynamic folder structure
        main_folder_path = create_dynamic_folder_structure(base_folder, date_str, CRIME_TYPES)
        
        if not main_folder_path:
            arcpy.AddError("Failed to create folder structure")
            return
        
        if dry_run:
            arcpy.AddMessage("DRY RUN: Folder structure created successfully")
            arcpy.AddMessage(f"PNG maps would be exported to crime-specific subfolders in: {main_folder_path}")
            arcpy.AddMessage("Run with dry_run=false to execute PNG map exports")
        else:
            # Run the actual export process
            if report:
                arcpy.AddMessage("Starting individual crime type exports as PNG...")
                success = run_individual_crime_exports(main_folder_path, date_str)
                if success:
                    arcpy.AddMessage("✅ PNG map export completed successfully!")
                else:
                    arcpy.AddError("❌ PNG map export failed")
            else:
                arcpy.AddMessage("Report generation disabled")
        
    except Exception as e:
        arcpy.AddError(f"Unexpected error in main: {e}")
        logger.error(f"Critical error: {e}")

if __name__ == "__main__":
    main()