# 🕒 2025-01-27-23-58-00
# SCRPA_Fix/map_export_function_fix
# Author: R. A. Carucci
# Purpose: Fix the missing export_maps_for_crime_type function

# ADD THIS TO YOUR map_export.py file

def export_maps_for_crime_type(crime_type, output_folder, args):
    """
    Export maps for a specific crime type using Excel-based 7-day periods.
    
    Args:
        crime_type (str): Crime type to export
        output_folder (str): Output directory path
        args: Command line arguments
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"[MAP EXPORT] Starting map export for {crime_type}")
        
        # Validate configuration first
        if not validate_config():
            return False
            
        # Get target date from args
        target_date = args[6] if len(args) > 6 else "2025_06_03"
        
        # Parse date
        try:
            from datetime import datetime
            target_date_obj = datetime.strptime(target_date, "%Y_%m_%d").date()
        except ValueError:
            print(f"[ERROR] Invalid date format: {target_date}")
            return False
            
        # Get Excel-based 7-day period
        start_date, end_date = get_7day_period_dates(target_date_obj)
        if not start_date or not end_date:
            print(f"[ERROR] Could not determine 7-day period for {target_date}")
            return False
            
        print(f"[MAP EXPORT] Using Excel 7-day period: {start_date} to {end_date}")
        
        # Initialize ArcGIS
        import arcpy
        
        # Set workspace and check license
        arcpy.env.overwriteOutput = True
        
        # Open the ArcGIS Pro project
        if not os.path.exists(APR_PATH):
            print(f"[ERROR] ArcGIS Pro project not found: {APR_PATH}")
            return False
            
        # Open project
        aprx = arcpy.mp.ArcGISProject(APR_PATH)
        print(f"[SUCCESS] Opened ArcGIS Pro project: {APR_PATH}")
        
        # Get layouts
        layouts = aprx.listLayouts()
        if not layouts:
            print("[ERROR] No layouts found in ArcGIS Pro project")
            return False
            
        # Use first layout or find specific one
        layout = layouts[0]
        for l in layouts:
            if "7_Day" in l.name or "SCRPA" in l.name:
                layout = l
                break
                
        print(f"[SUCCESS] Using layout: {layout.name}")
        
        # Get map frame
        map_frames = layout.listElements("MAPFRAME_ELEMENT")
        if not map_frames:
            print("[ERROR] No map frame found in layout")
            return False
            
        map_frame = map_frames[0]
        map_obj = map_frame.map
        print(f"[SUCCESS] Using map: {map_obj.name}")
        
        # Hide all layers initially
        for lyr in map_obj.listLayers():
            lyr.visible = False
            
        # Show base layers
        base_layer_names = [
            "City Boundaries",
            "OpenStreetMap", 
            "Light Gray Canvas",
            "Streets",
            "World Light Gray"
        ]
        
        base_layers_found = 0
        for lyr in map_obj.listLayers():
            if any(base_name.lower() in lyr.name.lower() for base_name in base_layer_names):
                lyr.visible = True
                lyr.transparency = 0
                base_layers_found += 1
                print(f"[SUCCESS] Enabled base layer: {lyr.name}")
                
        if base_layers_found == 0:
            print("[WARNING] No base layers found - map may be blank")
            
        # Find and show crime-specific 7-day layer
        target_layer_name = f"{crime_type} 7-Day"
        target_layer = None
        
        for lyr in map_obj.listLayers():
            if target_layer_name.lower() in lyr.name.lower():
                target_layer = lyr
                lyr.visible = True
                lyr.transparency = 0
                print(f"[SUCCESS] Enabled crime layer: {lyr.name}")
                break
                
        if not target_layer:
            print(f"[WARNING] Crime layer not found: {target_layer_name}")
            print("[INFO] Available layers:")
            for lyr in map_obj.listLayers():
                print(f"  - {lyr.name}")
            
        # Set up export
        sanitized_crime_type = sanitize_filename(crime_type)
        filename_prefix = get_standardized_filename(crime_type)
        
        # Ensure output folder exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"[SUCCESS] Created output folder: {output_folder}")
            
        # Export map
        export_filename = f"{filename_prefix}_Map.png"
        export_path = os.path.join(output_folder, export_filename)
        
        print(f"[EXPORT] Exporting map to: {export_path}")
        
        # Perform export
        layout.exportToPNG(export_path, resolution=200)
        
        # Verify export
        if os.path.exists(export_path):
            file_size = os.path.getsize(export_path)
            print(f"[SUCCESS] Map exported: {export_path} ({file_size:,} bytes)")
            return True
        else:
            print(f"[ERROR] Export failed - file not created: {export_path}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Map export failed for {crime_type}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        try:
            del aprx
        except:
            pass

# Also add this wrapper function for backward compatibility
def export_maps(crime_type, output_folder, args):
    """Wrapper function for backward compatibility"""
    return export_maps_for_crime_type(crime_type, output_folder, args)