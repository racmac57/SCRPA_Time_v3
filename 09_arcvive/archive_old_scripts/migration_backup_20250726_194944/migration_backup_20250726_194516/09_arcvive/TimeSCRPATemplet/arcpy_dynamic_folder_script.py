import arcpy
import os
import sys
import argparse
import pandas as pd
from datetime import datetime

def get_report_name_from_date(target_date_str):
    """
    Load Excel file and return the corresponding Report_Name for the given date.
    
    Args:
        target_date_str (str): Date in format 'YYYY_MM_DD' (e.g., '2025_05_13')
    
    Returns:
        str: Report_Name (e.g., 'C05W19') or fallback name if not found
    """
    excel_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reference\7Day_28Day_Cycle_20250414.xlsx"
    
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
            arcpy.AddMessage(f"Found Report_Name: {report_name} for date: {target_date_str}")
            return report_name
        else:
            arcpy.AddWarning(f"No matching Report_Name for date: {target_date_str}")
            return f"UNKNOWN_{target_date_str}"
            
    except Exception as e:
        arcpy.AddError(f"Error reading Excel file: {e}")
        return f"ERROR_{target_date_str}"

def setup_map_and_layouts(aprx_path):
    """Setup ArcGIS Pro project and return map and layout objects."""
    try:
        aprx = arcpy.mp.ArcGISProject(aprx_path)
        
        # Get the first map (assuming single map project)
        maps = aprx.listMaps()
        if not maps:
            raise Exception("No maps found in the project")
        current_map = maps[0]
        
        # Get all layouts
        layouts = aprx.listLayouts()
        if not layouts:
            raise Exception("No layouts found in the project")
        
        return aprx, current_map, layouts
        
    except Exception as e:
        arcpy.AddError(f"Error setting up project: {e}")
        return None, None, None

def update_map_extent_and_definition_queries(current_map, args):
    """Update map extent and definition queries based on arguments."""
    try:
        # Update extent if provided
        if hasattr(args, 'extent') and args.extent:
            # Parse extent: "xmin,ymin,xmax,ymax"
            extent_coords = [float(x.strip()) for x in args.extent.split(',')]
            if len(extent_coords) == 4:
                extent = arcpy.Extent(*extent_coords)
                current_map.defaultCamera.setExtent(extent)
                arcpy.AddMessage(f"Map extent updated to: {args.extent}")
        
        # Update definition queries if provided
        if hasattr(args, 'definition_query') and args.definition_query:
            for layer in current_map.listLayers():
                if hasattr(layer, 'definitionQuery'):
                    layer.definitionQuery = args.definition_query
                    arcpy.AddMessage(f"Definition query updated for layer {layer.name}: {args.definition_query}")
        
        # Update date-based queries
        if hasattr(args, 'date') and args.date:
            # Convert date format for SQL queries
            formatted_date = args.date.replace('_', '-')
            
            # Example: Update layers with date-based definition queries
            for layer in current_map.listLayers():
                if hasattr(layer, 'definitionQuery') and 'DATE' in layer.name.upper():
                    # Customize this logic based on your specific layer naming and field conventions
                    date_query = f"DATE_FIELD = '{formatted_date}'"
                    layer.definitionQuery = date_query
                    arcpy.AddMessage(f"Date-based query applied to {layer.name}: {date_query}")
                    
    except Exception as e:
        arcpy.AddError(f"Error updating map properties: {e}")

def get_crime_type_from_layout_name(layout_name):
    """
    Extract crime type from layout name to determine subfolder.
    
    Args:
        layout_name (str): Name of the layout (e.g., "Burglary Auto Layout")
    
    Returns:
        str: Crime type subfolder name (e.g., "Burglary_Auto")
    """
    # Define mapping of layout names to crime type folders
    crime_type_mapping = {
        'burglary auto': 'Burglary_Auto',
        'burglary': 'Burglary_Auto',  # fallback
        'motor vehicle theft': 'Motor_Vehicle_Theft',
        'mv theft': 'Motor_Vehicle_Theft',  # common abbreviation
        'vehicle theft': 'Motor_Vehicle_Theft',  # fallback
        'theft': 'Theft',
        'robbery': 'Robbery',
        'assault': 'Assault',
        'domestic violence': 'Domestic_Violence',
        'drugs': 'Drugs',
        'vandalism': 'Vandalism',
        'fraud': 'Fraud',
        'weapon': 'Weapons',
        'weapons': 'Weapons'
    }
    
    # Convert layout name to lowercase for matching
    layout_lower = layout_name.lower()
    
    # Check for matches in the mapping
    for key, value in crime_type_mapping.items():
        if key in layout_lower:
            return value
    
    # If no match found, create a clean folder name from layout name
    # Remove common layout suffixes and clean up the name
    clean_name = layout_name.replace(' Layout', '').replace(' Map', '').replace('_Layout', '').replace('_Map', '')
    clean_name = clean_name.replace(' ', '_').replace('-', '_')
    
    return clean_name

def export_layout(layout, main_output_path, layout_name, args):
    """Export a single layout to the appropriate crime-type subfolder."""
    try:
        # Get crime type subfolder name
        crime_type = get_crime_type_from_layout_name(layout_name)
        
        # Create crime-type specific subfolder
        crime_subfolder = os.path.join(main_output_path, crime_type)
        if not os.path.exists(crime_subfolder):
            os.makedirs(crime_subfolder)
            arcpy.AddMessage(f"Created crime type subfolder: {crime_subfolder}")
        
        # Create filename based on layout name and date
        safe_date = args.date.replace('_', '-') if hasattr(args, 'date') and args.date else datetime.now().strftime('%Y-%m-%d')
        filename = f"{layout_name}_{safe_date}.pdf"
        full_path = os.path.join(crime_subfolder, filename)
        
        # Export the layout
        layout.exportToPDF(full_path, resolution=300, image_quality="BEST")
        arcpy.AddMessage(f"Exported: {full_path}")
        
        return True, full_path, crime_type
        
    except Exception as e:
        arcpy.AddError(f"Error exporting {layout_name}: {e}")
        return False, None, None

def run_all_layouts(aprx, current_map, layouts, args):
    """Export all layouts to dynamically generated folder path with crime-type subfolders."""
    try:
        # Get the report name from the Excel file based on the date
        report_name = get_report_name_from_date(args.date)
        
        # Create safe date string for folder name (keep underscores as requested)
        safe_date = args.date if hasattr(args, 'date') and args.date else datetime.now().strftime('%Y_%m_%d')
        
        # Create dynamic folder name using report name from Excel
        folder_name = f"{report_name}_{safe_date}"
        
        # Full main output path
        base_output_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reports"
        main_output_path = os.path.join(base_output_path, folder_name)
        
        # Create main directory if it doesn't exist
        if not os.path.exists(main_output_path):
            os.makedirs(main_output_path)
            arcpy.AddMessage(f"Created main directory: {main_output_path}")
        
        # Track exports by crime type
        exports_by_crime_type = {}
        successful_exports = 0
        failed_exports = 0
        
        # Export all layouts
        for layout in layouts:
            success, export_path, crime_type = export_layout(layout, main_output_path, layout.name, args)
            if success:
                successful_exports += 1
                if crime_type not in exports_by_crime_type:
                    exports_by_crime_type[crime_type] = []
                exports_by_crime_type[crime_type].append(export_path)
            else:
                failed_exports += 1
        
        # Summary message
        arcpy.AddMessage(f"Export complete! Main folder: {folder_name}")
        arcpy.AddMessage(f"Successful exports: {successful_exports}")
        if failed_exports > 0:
            arcpy.AddWarning(f"Failed exports: {failed_exports}")
        
        # Log subfolder summary
        arcpy.AddMessage("Subfolders created:")
        for crime_type, files in exports_by_crime_type.items():
            arcpy.AddMessage(f"  {crime_type}: {len(files)} file(s)")
            
        return main_output_path
        
    except Exception as e:
        arcpy.AddError(f"Error in run_all_layouts: {e}")
        return None

def run_specific_layout(aprx, current_map, layouts, layout_name, args):
    """Export a specific layout to dynamically generated folder path with crime-type subfolder."""
    try:
        # Find the specified layout
        target_layout = None
        for layout in layouts:
            if layout.name.lower() == layout_name.lower():
                target_layout = layout
                break
        
        if not target_layout:
            arcpy.AddError(f"Layout '{layout_name}' not found. Available layouts: {[l.name for l in layouts]}")
            return None
        
        # Get the report name from the Excel file based on the date
        report_name = get_report_name_from_date(args.date)
        
        # Create safe date string for folder name (keep underscores as requested)
        safe_date = args.date if hasattr(args, 'date') and args.date else datetime.now().strftime('%Y_%m_%d')
        
        # Create dynamic folder name using report name from Excel
        folder_name = f"{report_name}_{safe_date}"
        
        # Full main output path
        base_output_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reports"
        main_output_path = os.path.join(base_output_path, folder_name)
        
        # Create main directory if it doesn't exist
        if not os.path.exists(main_output_path):
            os.makedirs(main_output_path)
            arcpy.AddMessage(f"Created main directory: {main_output_path}")
        
        # Export the specific layout
        success, export_path, crime_type = export_layout(target_layout, main_output_path, target_layout.name, args)
        
        if success:
            arcpy.AddMessage(f"Successfully exported {layout_name} to: {export_path}")
            arcpy.AddMessage(f"Crime type subfolder: {crime_type}")
        else:
            arcpy.AddError(f"Failed to export {layout_name}")
            
        return export_path if success else None
        
    except Exception as e:
        arcpy.AddError(f"Error in run_specific_layout: {e}")
        return None

def main():
    """Main function to handle command line arguments and execute appropriate functions."""
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(description='Export ArcGIS Pro layouts with dynamic folder naming')
        parser.add_argument('--mode', choices=['all', 'specific'], required=True,
                          help='Export mode: all layouts or specific layout')
        parser.add_argument('--layout', type=str,
                          help='Name of specific layout to export (required if mode=specific)')
        parser.add_argument('--date', type=str, required=True,
                          help='Date in format YYYY_MM_DD (e.g., 2025_05_13)')
        parser.add_argument('--extent', type=str,
                          help='Map extent as "xmin,ymin,xmax,ymax"')
        parser.add_argument('--definition_query', type=str,
                          help='Definition query to apply to layers')
        parser.add_argument('--aprx_path', type=str,
                          default=r"C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\SCRPA_TIME_Based.aprx",
                          help='Path to ArcGIS Pro project file')
        
        # Parse arguments
        args = parser.parse_args()
        
        # Validate arguments
        if args.mode == 'specific' and not args.layout:
            arcpy.AddError("Layout name is required when mode is 'specific'")
            return
        
        # Validate date format
        try:
            datetime.strptime(args.date, '%Y_%m_%d')
        except ValueError:
            arcpy.AddError("Date must be in format YYYY_MM_DD (e.g., 2025_05_13)")
            return
        
        arcpy.AddMessage(f"Starting export process...")
        arcpy.AddMessage(f"Mode: {args.mode}")
        arcpy.AddMessage(f"Date: {args.date}")
        if args.layout:
            arcpy.AddMessage(f"Layout: {args.layout}")
        
        # Setup ArcGIS Pro project
        aprx, current_map, layouts = setup_map_and_layouts(args.aprx_path)
        if not aprx:
            return
        
        # Update map properties
        update_map_extent_and_definition_queries(current_map, args)
        
        # Execute based on mode
        if args.mode == 'all':
            result_path = run_all_layouts(aprx, current_map, layouts, args)
        else:  # specific
            result_path = run_specific_layout(aprx, current_map, layouts, args.layout, args)
        
        if result_path:
            arcpy.AddMessage(f"Process completed successfully!")
        else:
            arcpy.AddError("Process failed!")
            
    except Exception as e:
        arcpy.AddError(f"Unexpected error in main: {e}")
    
    finally:
        # Clean up
        try:
            if 'aprx' in locals():
                del aprx
        except:
            pass

if __name__ == "__main__":
    main()
