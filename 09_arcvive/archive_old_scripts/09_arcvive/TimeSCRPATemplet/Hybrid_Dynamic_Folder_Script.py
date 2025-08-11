#!/usr/bin/env python3
"""
FIXED Hybrid Dynamic Folder Script - Hackensack Police Department
Author: R. Carucci (with fixes for legend, zoom, and filename issues)
Purpose: Export ArcGIS Pro layouts with proper legend visibility, zoom, and naming
Location: C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\TimeSCRPATemplet\
Last Updated: 2025-05-30
"""

import arcpy
import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_report_name_from_date(target_date_str):
    """Load Excel file and return the corresponding Report_Name for the given date."""
    excel_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\InBox\GIS_Tools\7Day_28Day_Cycle_20250414.xlsx"
    
    try:
        df = pd.read_excel(excel_path, sheet_name="7Day_28Day_250414")
        df['Report_Due_Date'] = pd.to_datetime(df['Report_Due_Date'])
        target_date = pd.to_datetime(target_date_str.replace('_', '-'))
        match = df[df['Report_Due_Date'].dt.date == target_date.date()]
        
        if not match.empty:
            report_name = match.iloc[0]['Report_Name']
            arcpy.AddMessage(f"✅ Found Report_Name: {report_name} for date: {target_date_str}")
            return report_name
        else:
            arcpy.AddWarning(f"⚠️ No matching Report_Name for date: {target_date_str}")
            return f"UNKNOWN_{target_date_str}"
            
    except Exception as e:
        arcpy.AddError(f"❌ Error reading Excel file: {e}")
        return f"ERROR_{target_date_str}"

def get_crime_type_from_layout_name(layout_name):
    """Extract crime type from layout name - FIXED for your exact layout names."""
    # Updated mapping based on your EXACT layout names from diagnostic
    layout_to_crime_mapping = {
        'Crime_Reporting_Layout': 'Motor_Vehicle_Theft',  # Your main layout
        'Burglary - Auto': 'Burglary_Auto',
        'Burglary - Comm & Res': 'Burglary_Commercial_Residential', 
        'Robbery': 'Robbery',
        'Sexual Offenses': 'Sexual_Offenses',
        'Crime Report Legend': 'Crime_Report_Legend'  # Skip this one
    }
    
    # Check for exact matches first (case-sensitive)
    if layout_name in layout_to_crime_mapping:
        crime_type = layout_to_crime_mapping[layout_name]
        arcpy.AddMessage(f"🎯 Exact layout match: '{layout_name}' → {crime_type}")
        return crime_type
    
    # Case-insensitive fallback
    layout_lower = layout_name.lower().strip()
    for layout_key, crime_type in layout_to_crime_mapping.items():
        if layout_key.lower() == layout_lower:
            arcpy.AddMessage(f"🎯 Case-insensitive match: '{layout_name}' → {crime_type}")
            return crime_type
    
    # Fallback: create clean name from layout name
    clean_name = layout_name.replace(' ', '_').replace('-', '_').replace('Layout', '').replace('_Layout', '')
    arcpy.AddMessage(f"🎯 Fallback mapping: '{layout_name}' → {clean_name}")
    return clean_name

def should_skip_layout(layout_name):
    """Determine if a layout should be skipped during export."""
    skip_patterns = [
        'Crime Report Legend',  # This is just the legend, not a crime-specific layout
        'Legend'  # Any layout with just "Legend" in the name
    ]
    
    for pattern in skip_patterns:
        if pattern.lower() in layout_name.lower():
            arcpy.AddMessage(f"⏭️ Skipping layout: {layout_name} (matches skip pattern: {pattern})")
            return True
    
    return False

def get_optimal_extent(current_map):
    """Calculate optimal map extent to fix zoom and rotation issues."""
    try:
        # Find city boundary layer for extent calculation
        city_boundary_layer = None
        for layer in current_map.listLayers():
            layer_name_lower = layer.name.lower()
            if any(keyword in layer_name_lower for keyword in ["city", "boundary", "boundaries"]):
                city_boundary_layer = layer
                arcpy.AddMessage(f"🗺️ Found boundary layer: {layer.name}")
                break
        
        if city_boundary_layer:
            city_extent = city_boundary_layer.getExtent()
            
            # Apply 5% buffer for optimal zoom without clipping
            width = city_extent.XMax - city_extent.XMin
            height = city_extent.YMax - city_extent.YMin
            buffered_extent = arcpy.Extent(
                city_extent.XMin - (width * 0.05),
                city_extent.YMin - (height * 0.05),
                city_extent.XMax + (width * 0.05),
                city_extent.YMax + (height * 0.05)
            )
            
            arcpy.AddMessage(f"✅ Calculated optimal extent with 5% buffer")
            return buffered_extent
        
        arcpy.AddWarning("⚠️ No city boundary layer found for extent calculation")
        return None
        
    except Exception as e:
        arcpy.AddError(f"❌ Error calculating optimal extent: {e}")
        return None

def configure_legend(layout):
    """FIXED: Configure legend visibility - handles both MainLegend and Legend elements."""
    try:
        layout_name = layout.name
        arcpy.AddMessage(f"🔍 Searching for legend in layout: {layout_name}")
        
        legend_element = None
        
        # Method 1: For "Crime Report Legend" layout, look for MainLegend
        if "Crime Report Legend" in layout_name:
            for element in layout.listElements():
                if hasattr(element, 'name') and element.name == "MainLegend":
                    legend_element = element
                    arcpy.AddMessage(f"✅ Found MainLegend in Crime Report Legend layout")
                    break
        
        # Method 2: For individual crime layouts, look for "Legend" element
        else:
            legend_elements = layout.listElements("LEGEND_ELEMENT")
            if legend_elements:
                # Look for element named "Legend"
                for element in legend_elements:
                    if hasattr(element, 'name') and element.name == "Legend":
                        legend_element = element
                        arcpy.AddMessage(f"✅ Found Legend element in {layout_name}")
                        break
                
                # If no "Legend" found, use first legend element
                if not legend_element:
                    legend_element = legend_elements[0]
                    legend_name = getattr(legend_element, 'name', 'unnamed')
                    arcpy.AddMessage(f"✅ Using first legend element: {legend_name}")
        
        # Method 3: Fallback - find any legend-like element
        if not legend_element:
            all_elements = layout.listElements()
            for element in all_elements:
                element_name = getattr(element, 'name', '')
                if 'legend' in element_name.lower():
                    legend_element = element
                    arcpy.AddMessage(f"✅ Found legend by name search: {element_name}")
                    break
        
        if legend_element:
            # Make legend visible
            legend_element.visible = True
            legend_name = getattr(legend_element, 'name', 'unnamed')
            arcpy.AddMessage(f"✅ Legend made visible: {legend_name}")
            
            # Configure legend properties
            try:
                # Disable auto-sync to gain manual control
                if hasattr(legend_element, 'syncLayerVisibility'):
                    legend_element.syncLayerVisibility = False
                    arcpy.AddMessage(f"🔧 Disabled syncLayerVisibility for manual control")
                
                # Show legend item count
                if hasattr(legend_element, 'items'):
                    arcpy.AddMessage(f"📋 Legend has {len(legend_element.items)} items")
                    
                    # Optional: Show only visible layers in legend
                    visible_count = 0
                    for item in legend_element.items:
                        if hasattr(item, 'visible'):
                            if item.visible:
                                visible_count += 1
                    arcpy.AddMessage(f"📋 {visible_count} legend items are visible")
                
            except Exception as e:
                arcpy.AddWarning(f"⚠️ Could not configure legend properties: {e}")
            
            return True
        else:
            arcpy.AddWarning(f"⚠️ No legend element found in layout: {layout_name}")
            
            # Debug: List all elements
            all_elements = layout.listElements()
            element_info = []
            for elem in all_elements:
                elem_name = getattr(elem, 'name', 'unnamed')
                elem_type = elem.__class__.__name__
                element_info.append(f"{elem_type}: {elem_name}")
            arcpy.AddMessage(f"💡 Available elements: {element_info}")
            return False
            
    except Exception as e:
        arcpy.AddError(f"❌ Error configuring legend: {e}")
        return False

def export_layout_with_fixes(layout, main_output_path, layout_name, date_str, current_map=None):
    """FIXED: Export layout with proper naming, legend, and zoom."""
    try:
        # Get crime type subfolder
        crime_type = get_crime_type_from_layout_name(layout_name)
        crime_subfolder = os.path.join(main_output_path, crime_type)
        
        # Create subfolder if it doesn't exist
        if not os.path.exists(crime_subfolder):
            os.makedirs(crime_subfolder)
            arcpy.AddMessage(f"📁 Created crime type subfolder: {crime_subfolder}")
        
        # FIXED: Generate proper filename based on crime type
        safe_date = date_str.replace('_', '-')
        
        # Map layout names to proper filename prefixes
        filename_mappings = {
            'Motor_Vehicle_Theft': 'MV_Theft_Layout',
            'Burglary_Auto': 'Burglary_Auto_Layout',
            'Burglary_Commercial_Residential': 'Burglary_Commercial_Residential_Layout',
            'Robbery': 'Robbery_Layout',
            'Sexual_Offenses': 'Sexual_Offenses_Layout'
        }
        
        # Get proper filename prefix
        filename_prefix = filename_mappings.get(crime_type, f"{crime_type}_Layout")
        filename = f"{filename_prefix}_{safe_date}.png"
        full_path = os.path.join(crime_subfolder, filename)
        
        arcpy.AddMessage(f"📄 Target filename: {filename}")
        
        # FIXED: Set optimal extent if we have map reference
        if current_map:
            # Find map frame in layout
            map_frames = layout.listElements("MAPFRAME_ELEMENT")
            if map_frames:
                map_frame = map_frames[0]
                optimal_extent = get_optimal_extent(current_map)
                
                if optimal_extent:
                    try:
                        map_frame.camera.setExtent(optimal_extent)
                        arcpy.AddMessage(f"✅ Set optimal extent to fix zoom/rotation")
                    except Exception as e:
                        arcpy.AddWarning(f"⚠️ Could not set extent: {e}")
        
        # FIXED: Configure legend
        legend_configured = configure_legend(layout)
        if legend_configured:
            arcpy.AddMessage(f"✅ Legend configured successfully")
        else:
            arcpy.AddWarning(f"⚠️ Legend configuration had issues")
        
        # Refresh layout to apply all changes
        try:
            layout.refresh()
            arcpy.AddMessage(f"🔄 Layout refreshed")
        except Exception as e:
            arcpy.AddWarning(f"⚠️ Could not refresh layout: {e}")
        
        # Export with high quality settings
        arcpy.AddMessage(f"📤 Exporting to: {full_path}")
        layout.exportToPNG(full_path, resolution=300, width=2000, height=1500)
        
        # Verify export success
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path)
            arcpy.AddMessage(f"✅ Export successful: {full_path} ({file_size:,} bytes)")
            return True, full_path, crime_type
        else:
            arcpy.AddError(f"❌ Export file not created: {full_path}")
            return False, None, None
        
    except Exception as e:
        arcpy.AddError(f"❌ Error exporting {layout_name}: {e}")
        logger.error(f"Export error for {layout_name}: {e}")
        return False, None, None

def setup_project_and_map(aprx_path):
    """Setup ArcGIS Pro project and return project, map, and layouts."""
    try:
        aprx = arcpy.mp.ArcGISProject(aprx_path)
        arcpy.AddMessage(f"✅ Loaded project: {aprx_path}")
        
        # Get map
        maps = aprx.listMaps()
        if not maps:
            raise Exception("No maps found in project")
        current_map = maps[0]
        arcpy.AddMessage(f"✅ Using map: {current_map.name}")
        
        # Get layouts
        layouts = aprx.listLayouts()
        if not layouts:
            raise Exception("No layouts found in project")
        arcpy.AddMessage(f"✅ Found {len(layouts)} layouts")
        
        # List available layouts for debugging
        layout_names = [layout.name for layout in layouts]
        arcpy.AddMessage(f"📋 Available layouts: {layout_names}")
        
        return aprx, current_map, layouts
        
    except Exception as e:
        arcpy.AddError(f"❌ Error setting up project: {e}")
        return None, None, None

def main():
    """FIXED Main function with improved error handling and debugging."""
    try:
        arcpy.AddMessage("🚀 Starting FIXED Hybrid Dynamic Folder Script")
        arcpy.AddMessage("=" * 60)
        
        # Parse arguments
        parser = argparse.ArgumentParser(description='Export ArcGIS Pro layouts with FIXES')
        parser.add_argument('--mode', choices=['all', 'specific'], required=True,
                          help='Export mode: all layouts or specific layout')
        parser.add_argument('--layout', type=str,
                          help='Name of specific layout to export')
        parser.add_argument('--date', type=str, required=True,
                          help='Date in format YYYY_MM_DD')
        parser.add_argument('--aprx_path', type=str,
                          default=r"C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\TimeSCRPATemplet\TimeSCRPATemplet.aprx",
                          help='Path to ArcGIS Pro project file')
        parser.add_argument('--format', type=str, default='PNG',
                          help='Export format (PNG or PDF)')
        
        args = parser.parse_args()
        
        # Validate arguments
        if args.mode == 'specific' and not args.layout:
            arcpy.AddError("❌ Layout name required when mode is 'specific'")
            return
        
        # Validate date format
        try:
            datetime.strptime(args.date, '%Y_%m_%d')
        except ValueError:
            arcpy.AddError("❌ Date must be in format YYYY_MM_DD")
            return
        
        # Display settings
        arcpy.AddMessage(f"📅 Date: {args.date}")
        arcpy.AddMessage(f"🎯 Mode: {args.mode}")
        arcpy.AddMessage(f"📁 Project: {os.path.basename(args.aprx_path)}")
        if args.layout:
            arcpy.AddMessage(f"🎨 Layout: {args.layout}")
        
        # Setup project
        aprx, current_map, layouts = setup_project_and_map(args.aprx_path)
        if not aprx:
            return
        
        # Create dynamic folder structure
        report_name = get_report_name_from_date(args.date)
        folder_name = f"{report_name}_{args.date}"
        
        base_output_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reports"
        main_output_path = os.path.join(base_output_path, folder_name)
        
        # Create main folder
        if not os.path.exists(main_output_path):
            os.makedirs(main_output_path)
            arcpy.AddMessage(f"📁 Created main directory: {main_output_path}")
        
        # Create crime-type subfolders
        crime_subfolders = [
            'Motor_Vehicle_Theft', 
            'Burglary_Auto', 
            'Burglary_Commercial_Residential', 
            'Robbery', 
            'Sexual_Offenses'
        ]
        
        for subfolder in crime_subfolders:
            subfolder_path = os.path.join(main_output_path, subfolder)
            Path(subfolder_path).mkdir(exist_ok=True)
        
        arcpy.AddMessage(f"📁 Created {len(crime_subfolders)} crime type subfolders")
        
        # Process layouts - FIXED for your exact layout structure
        successful_exports = 0
        failed_exports = 0
        processed_layouts = []
        
        layouts_to_process = layouts if args.mode == 'all' else [l for l in layouts if l.name == args.layout]
        
        if not layouts_to_process:
            arcpy.AddError(f"❌ No layouts found to process")
            return
        
        # Filter out layouts we should skip
        layouts_to_export = []
        for layout in layouts_to_process:
            if should_skip_layout(layout.name):
                continue
            layouts_to_export.append(layout)
        
        arcpy.AddMessage(f"📋 Processing {len(layouts_to_export)} layouts (skipped {len(layouts_to_process) - len(layouts_to_export)})")
        
        # Export each layout
        for i, layout in enumerate(layouts_to_export, 1):
            try:
                layout_name = layout.name
                arcpy.AddMessage(f"\n[{i}/{len(layouts_to_export)}] Processing: '{layout_name}'")
                
                # Determine the proper filename prefix based on layout name
                crime_type = get_crime_type_from_layout_name(layout_name)
                
                success, export_path, crime_folder = export_layout_with_fixes(
                    layout, main_output_path, layout_name, args.date, current_map
                )
                
                if success:
                    successful_exports += 1
                    processed_layouts.append(f"✅ '{layout_name}' → {crime_folder}")
                    arcpy.AddMessage(f"✅ Successfully exported: '{layout_name}'")
                else:
                    failed_exports += 1
                    processed_layouts.append(f"❌ '{layout_name}' → FAILED")
                    arcpy.AddError(f"❌ Failed to export: '{layout_name}'")
                
            except Exception as e:
                failed_exports += 1
                processed_layouts.append(f"❌ '{layout_name}' → ERROR: {str(e)}")
                arcpy.AddError(f"❌ Error processing '{layout_name}': {e}")
        
        # Final summary
        arcpy.AddMessage("\n" + "=" * 60)
        arcpy.AddMessage("📊 EXPORT SUMMARY")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage(f"📁 Output folder: {folder_name}")
        arcpy.AddMessage(f"✅ Successful exports: {successful_exports}")
        arcpy.AddMessage(f"❌ Failed exports: {failed_exports}")
        arcpy.AddMessage(f"📊 Success rate: {(successful_exports/(successful_exports+failed_exports)*100):.1f}%")
        
        arcpy.AddMessage(f"\n📋 Detailed results:")
        for result in processed_layouts:
            arcpy.AddMessage(f"  {result}")
        
        # Cleanup
        del aprx
        arcpy.AddMessage(f"\n🧹 Cleanup completed")
        
        if successful_exports > 0:
            arcpy.AddMessage(f"\n🎉 Export process completed successfully!")
        else:
            arcpy.AddError(f"\n💥 No successful exports - check issues above")
        
    except Exception as e:
        arcpy.AddError(f"❌ Critical error in main: {e}")
        logger.error(f"Critical error: {e}")

if __name__ == "__main__":
    main()