# 🕒 2025-06-22-21-55-00
# Police_Data_Analysis/map_export_clean_final
# Author: R. A. Carucci
# Purpose: Clean map export with enhanced symbology, no syntax errors, Excel integration

import arcpy
import os
import glob
import logging
from datetime import datetime, timedelta, date
from config import APR_PATH, SYM_LAYER_PATH, SUFFIXES, get_7day_period_dates, get_standardized_filename, get_crime_type_folder, get_sql_pattern_for_crime
from PIL import Image, ImageDraw, ImageFont

print("✅ map_export.py loaded successfully")

def validate_config():
    """Validate configuration parameters."""
    issues = []
    
    if not APR_PATH:
        issues.append("APR_PATH is not defined in config")
    elif not os.path.exists(APR_PATH):
        issues.append(f"ArcGIS Pro project file not found: {APR_PATH}")
    
    if not SUFFIXES:
        issues.append("SUFFIXES is not defined or empty in config")
    
    if SYM_LAYER_PATH and not os.path.exists(SYM_LAYER_PATH):
        issues.append(f"Symbology layer file not found: {SYM_LAYER_PATH}")
    
    if issues:
        for issue in issues:
            arcpy.AddError(f"❌ Configuration error: {issue}")
        return False
    
    return True

def sanitize_filename(text):
    """Sanitize text for use in filenames."""
    sanitized = (text
                .replace(" ", "_")
                .replace("&", "And")
                .replace("/", "_")
                .replace("\\", "_")
                .replace(":", "_")
                .replace("*", "_")
                .replace("?", "_")
                .replace("\"", "_")
                .replace("<", "_")
                .replace(">", "_")
                .replace("|", "_")
                .replace("-", "_"))
    
    return sanitized

def create_placeholder_image(crime_type, output_path, start_date=None, end_date=None):
    """Create enhanced placeholder image with 7-day period information."""
    try:
        width, height = 1148, 888  # 5.74" x 4.44" at 200 DPI
        
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("arial.ttf", 48)
            subtitle_font = ImageFont.truetype("arial.ttf", 36)
            text_font = ImageFont.truetype("arial.ttf", 32)
            period_font = ImageFont.truetype("arial.ttf", 28)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            period_font = ImageFont.load_default()
        
        title_text = crime_type
        subtitle_text = "Weekly Incident Report"
        main_text = "0 incidents recorded (7-day period)"
        period_text = f"Period: {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}" if start_date and end_date else "7-Day Analysis Period"
        
        # Calculate text positions for centering
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        main_bbox = draw.textbbox((0, 0), main_text, font=text_font)
        period_bbox = draw.textbbox((0, 0), period_text, font=period_font)
        
        title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
        subtitle_x = (width - (subtitle_bbox[2] - subtitle_bbox[0])) // 2
        main_x = (width - (main_bbox[2] - main_bbox[0])) // 2
        period_x = (width - (period_bbox[2] - period_bbox[0])) // 2
        
        title_y = height // 4
        subtitle_y = height // 2 - 70
        main_y = height // 2 - 10
        period_y = height // 2 + 30
        
        draw.text((title_x, title_y), title_text, fill='black', font=title_font)
        draw.text((subtitle_x, subtitle_y), subtitle_text, fill='#666666', font=subtitle_font)
        draw.text((main_x, main_y), main_text, fill='#333333', font=text_font)
        draw.text((period_x, period_y), period_text, fill='#0066CC', font=period_font)
        
        draw.rectangle([10, 10, width-10, height-10], outline='#CCCCCC', width=2)
        
        img.save(output_path, 'PNG', dpi=(200, 200))
        arcpy.AddMessage(f"✅ Created enhanced placeholder: {output_path}")
        
        return True
        
    except Exception as e:
        arcpy.AddError(f"❌ Error creating placeholder: {e}")
        return False

def apply_symbology_enhanced(layer, layer_name):
    """Apply crime-specific symbology with proper colors (CODE_20250622_006)."""
    logging.info(f"🎨 Applying enhanced symbology to: {layer_name}")
    
    try:
        sym = layer.symbology
        
        if not hasattr(sym, 'renderer'):
            logging.warning(f"⚠️ Layer {layer_name} has no renderer")
            return
        
        # Crime-specific color mapping
        crime_colors = {
            "Robbery": {'RGB': [0, 0, 0, 100]},         # Black
            "MV Theft": {'RGB': [255, 255, 0, 100]},    # Yellow  
            "Burglary": {'RGB': [255, 0, 0, 100]},      # Red
            "Sexual Offenses": {'RGB': [128, 0, 128, 100]} # Purple
        }
        
        # Determine crime type from layer name
        crime_type = next((crime for crime in crime_colors.keys() if crime in layer_name), "Default")
        
        if hasattr(sym, 'renderer') and hasattr(sym.renderer, 'symbol'):
            symbol = sym.renderer.symbol
            symbol.color = crime_colors.get(crime_type, {'RGB': [255, 0, 0, 100]})
            symbol.size = 8
            
            if hasattr(symbol, 'style'):
                symbol.style = 'STYLE_CIRCLE'
            
            layer.symbology = sym
            logging.info(f"✅ Symbology applied to {layer_name}: {crime_type} color")
        else:
            logging.warning(f"⚠️ Cannot modify symbology for {layer_name}")
            
    except Exception as e:
        logging.error(f"❌ Failed to apply symbology to {layer_name}: {e}")
        
        try:
            # Fallback symbology
            if "Robbery" in layer_name:
                layer.symbology.renderer.symbol.color = {'RGB': [0, 0, 0, 100]}
            else:
                layer.symbology.renderer.symbol.color = {'RGB': [255, 255, 0, 100]}
            layer.symbology.renderer.symbol.size = 8
            logging.info(f"✅ Fallback symbology applied to {layer_name}")
        except Exception as fallback_error:
            logging.error(f"❌ Fallback symbology failed for {layer_name}: {fallback_error}")

def export_maps(crime_type, output_folder, args):
    """
    Export crime maps showing ONLY 7-Day incidents using Excel-based periods.
    Enhanced with symbology fixes and map extent adjustments.
    """
    aprx = None
    
    try:
        if not validate_config():
            return False
            
        logging.info(f"🗺️ Starting map export for: {crime_type}")
        
        try:
            date_str = args[6]
            target_date = datetime.strptime(date_str, "%Y_%m_%d").date()
            arcpy.AddMessage(f"📅 Using date: {target_date}")
        except (IndexError, TypeError, ValueError):
            target_date = date.today()
            date_str = target_date.strftime("%Y_%m_%d")
            
        crime_output_folder = get_crime_type_folder(crime_type, date_str)
        os.makedirs(crime_output_folder, exist_ok=True)
        arcpy.AddMessage(f"📁 Output folder: {crime_output_folder}")
        
        filename_prefix = get_standardized_filename(crime_type)
        
        aprx = arcpy.mp.ArcGISProject(APR_PATH)
        arcpy.AddMessage(f"✅ Loaded project: {APR_PATH}")
        
        layouts = aprx.listLayouts("Crime Report Legend")
        if not layouts:
            arcpy.AddError("❌ Layout 'Crime Report Legend' not found")
            return False
            
        layout = layouts[0]
        arcpy.AddMessage(f"✅ Found layout: {layout.name}")
        
        map_frames = layout.listElements("MAPFRAME_ELEMENT")
        if not map_frames:
            arcpy.AddError("❌ No map frame elements found")
            return False
            
        map_frame = map_frames[0]
        map_obj = map_frame.map
        arcpy.AddMessage(f"✅ Found map: {map_obj.name}")

        # Store original layer states
        original_states = {}
        for lyr in map_obj.listLayers():
            original_states[lyr.name] = {'visible': lyr.visible, 'transparency': lyr.transparency}
        
        # Hide all layers initially
        for lyr in map_obj.listLayers():
            lyr.visible = False
        arcpy.AddMessage(f"🔄 Hidden {len(map_obj.listLayers())} layers")

        # Show base layers
        base_layers = ["City Boundaries", "OpenStreetMap", "Streets", "Light Gray Canvas"]
        for lyr in map_obj.listLayers():
            if any(base_name in lyr.name for base_name in base_layers):
                lyr.visible = True
                lyr.transparency = 0
                arcpy.AddMessage(f"✅ Enabled base layer: {lyr.name}")

        # Get Excel-based 7-day period dates
        start_date, end_date = get_7day_period_dates(target_date)
        if not start_date or not end_date:
            arcpy.AddError(f"❌ Could not determine Excel 7-day period for {target_date}")
            return False
            
        arcpy.AddMessage(f"📅 Excel 7-Day period: {start_date} to {end_date}")

        # Find and configure ONLY the 7-Day layer
        layer_name = f"{crime_type} 7-Day"
        target_layer = None
        
        for lyr in map_obj.listLayers():
            if lyr.name == layer_name:
                target_layer = lyr
                break
        
        if not target_layer:
            arcpy.AddWarning(f"❌ 7-Day layer not found: {layer_name}")
            export_filename = f"{filename_prefix}_Map.png"
            export_path = os.path.join(crime_output_folder, export_filename)
            success = create_placeholder_image(crime_type, export_path, start_date, end_date)
            return success
        
        target_layer.visible = True
        target_layer.transparency = 0
        arcpy.AddMessage(f"✅ Configured layer: {target_layer.name}")

        # CODE_20250622_007: Adjust map extent to include all features
        try:
            layer_extent = arcpy.Describe(target_layer).extent
            map_frame.camera.setExtent(layer_extent)
            arcpy.AddMessage(f"✅ Adjusted map extent")
        except Exception as e:
            arcpy.AddWarning(f"⚠️ Could not adjust map extent: {e}")

        # Apply definition query if supported
        if target_layer.supports("DEFINITIONQUERY"):
            filter_sql = build_sql_filter_7day_excel(crime_type, start_date, end_date)
            
            if filter_sql:
                arcpy.AddMessage(f"🔎 SQL filter: {filter_sql}")
                target_layer.definitionQuery = filter_sql
                arcpy.AddMessage(f"✅ Applied query to {target_layer.name}")
                
                try:
                    feature_count = int(arcpy.GetCount_management(target_layer).getOutput(0))
                    arcpy.AddMessage(f"📊 Features found: {feature_count}")
                    
                    if feature_count == 0:
                        arcpy.AddMessage(f"📋 No incidents for {crime_type}, creating placeholder")
                        export_filename = f"{filename_prefix}_Map.png"
                        export_path = os.path.join(crime_output_folder, export_filename)
                        success = create_placeholder_image(crime_type, export_path, start_date, end_date)
                        restore_layer_states(map_obj, original_states)
                        return success
                        
                except Exception as e:
                    arcpy.AddWarning(f"⚠️ Could not get feature count: {e}")
            else:
                arcpy.AddWarning(f"⚠️ Could not build SQL filter for {crime_type}")

        # Apply enhanced symbology
        apply_symbology_enhanced(target_layer, layer_name)

        # Update legend to show only 7-Day layer
        update_legend_visibility_7day(layout, map_obj, target_layer)

        # Clean up patch elements
        cleanup_patch_elements(layout)

        # Export the map
        success = export_map_to_png(layout, crime_type, crime_output_folder, filename_prefix)
        
        # Restore original layer states
        restore_layer_states(map_obj, original_states)
        
        if success:
            arcpy.AddMessage(f"✅ Map export completed for {crime_type}")
        
        return success
        
    except Exception as e:
        arcpy.AddError(f"❌ Critical error in export_maps: {str(e)}")
        logging.error(f"Critical error in export_maps for {crime_type}: {e}", exc_info=True)
        return False
    finally:
        if aprx:
            try:
                del aprx
                arcpy.AddMessage("🧹 Cleaned up project reference")
            except Exception as e:
                arcpy.AddWarning(f"⚠️ Could not clean up project: {e}")

def build_sql_filter_7day_excel(crime_type, start_date, end_date):
    """Build SQL filter for 7-Day period using Excel dates."""
    try:
        start_timestamp = f"{start_date.strftime('%Y-%m-%d')} 00:00:00.000"
        end_timestamp = f"{end_date.strftime('%Y-%m-%d')} 23:59:59.999"
        
        arcpy.AddMessage(f"📅 Filter period: {start_date} to {end_date}")
        
    except Exception as e:
        arcpy.AddError(f"❌ Error formatting dates: {e}")
        return None
    
    base_conditions = f"disposition LIKE '%See Report%' AND calldate >= timestamp '{start_timestamp}' AND calldate <= timestamp '{end_timestamp}'"
    pattern = get_sql_pattern_for_crime(crime_type)
    arcpy.AddMessage(f"💡 Pattern for {crime_type}: {pattern}")
    
    if isinstance(pattern, list):
        conditions = [f"calltype LIKE '%{p}%'" for p in pattern]
        crime_condition = f"({' OR '.join(conditions)})"
    else:
        crime_condition = f"calltype LIKE '%{pattern}%'"
    
    sql_filter = f'{crime_condition} AND {base_conditions}'
    arcpy.AddMessage(f"🔎 Final SQL filter: {sql_filter}")
    return sql_filter

def restore_layer_states(map_obj, original_states):
    """Restore all layers to their original visibility and transparency states."""
    try:
        for lyr in map_obj.listLayers():
            if lyr.name in original_states:
                lyr.visible = original_states[lyr.name]['visible']
                lyr.transparency = original_states[lyr.name]['transparency']
        arcpy.AddMessage("✅ Restored original layer states")
    except Exception as e:
        arcpy.AddWarning(f"⚠️ Error restoring layer states: {e}")

def update_legend_visibility_7day(layout, map_obj, target_layer):
    """Update legend to show only the 7-Day layer."""
    try:
        legend = None
        for elm in layout.listElements("LEGEND_ELEMENT"):
            if elm.name.strip().lower() == "mainlegend":
                legend = elm
                break
        
        if not legend:
            arcpy.AddWarning("⚠️ Legend element 'mainlegend' not found")
            return
        
        arcpy.AddMessage(f"✅ Found legend with {len(legend.items)} items")
        legend.syncLayerVisibility = False
        
        for item in legend.items:
            item.visible = False
        
        shown_count = 0
        for item in legend.items:
            if item.name == target_layer.name:
                item.visible = True
                shown_count += 1
                arcpy.AddMessage(f"✅ Showing in legend: {item.name}")
        
        arcpy.AddMessage(f"🎯 Legend updated: {shown_count} items shown")
        
    except Exception as e:
        arcpy.AddWarning(f"❌ Legend update error: {str(e)}")

def cleanup_patch_elements(layout):
    """Remove patch elements from layout."""
    try:
        elements_to_remove = []
        for elm in layout.listElements("PICTURE_ELEMENT"):
            if "hackensack" in elm.name.lower() or "patch" in elm.name.lower():
                elements_to_remove.append(elm)
        
        if not elements_to_remove:
            arcpy.AddMessage("💡 No patch elements found")
            return
                
        for elm in elements_to_remove:
            try:
                layout.removeElement(elm)
                arcpy.AddMessage(f"🧹 Removed patch element: {elm.name}")
            except Exception as e:
                arcpy.AddWarning(f"❌ Failed to remove {elm.name}: {str(e)}")
                
        arcpy.AddMessage(f"✅ Patch cleanup completed: {len(elements_to_remove)} elements")
                
    except Exception as e:
        arcpy.AddWarning(f"❌ Patch cleanup failed: {str(e)}")

def export_map_to_png(layout, crime_type, output_folder, filename_prefix):
    """Export layout to PNG file with standardized naming."""
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            arcpy.AddMessage(f"📁 Created output folder: {output_folder}")
        
        # Clean up old map files
        cleanup_pattern = os.path.join(output_folder, f"{filename_prefix}_Map*.png")
        old_files = glob.glob(cleanup_pattern)
        
        for file_path in old_files:
            try:
                os.remove(file_path)
                arcpy.AddMessage(f"🧹 Deleted old file: {os.path.basename(file_path)}")
            except Exception as e:
                arcpy.AddWarning(f"⚠️ Could not delete {file_path}: {str(e)}")
        
        export_filename = f"{filename_prefix}_Map.png"
        export_path = os.path.join(output_folder, export_filename)
        
        arcpy.AddMessage(f"🖼️ Exporting map to: {export_path}")
        layout.exportToPNG(export_path, resolution=200)
        
        if os.path.exists(export_path):
            file_size = os.path.getsize(export_path)
            arcpy.AddMessage(f"✅ Map exported: {export_path} ({file_size:,} bytes)")
            return True
        else:
            arcpy.AddError(f"❌ Export file not created: {export_path}")
            return False
        
    except Exception as e:
        arcpy.AddError(f"❌ Export failed: {str(e)}")
        logging.error(f"Map export failed for {crime_type}: {e}", exc_info=True)
        return False

# Legacy function compatibility
def apply_symbology(layer, layer_name):
    """Legacy function - redirects to enhanced version."""
    apply_symbology_enhanced(layer, layer_name)

def build_sql_filter_7day(crime_type, start_date):
    """Legacy function - now uses Excel integration."""
    try:
        if isinstance(start_date, str):
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_date_obj = start_date
            
        target_date = start_date_obj + timedelta(days=7)
        excel_start, excel_end = get_7day_period_dates(target_date)
        
        if excel_start and excel_end:
            return build_sql_filter_7day_excel(crime_type, excel_start, excel_end)
        else:
            return build_sql_filter_7day_excel(crime_type, start_date_obj, start_date_obj + timedelta(days=6))
            
    except Exception as e:
        arcpy.AddError(f"❌ Error in legacy SQL filter: {e}")
        return None

def build_sql_filter(crime_type, start_date):
    """Legacy function - redirects to Excel-based version."""
    return build_sql_filter_7day(crime_type, start_date)

def update_legend_visibility(layout, map_obj, suffix_layers):
    """Legacy function - redirects to 7-day version."""
    if suffix_layers:
        for key, layer in suffix_layers:
            if "7-Day" in key:
                update_legend_visibility_7day(layout, map_obj, layer)
                break❌ Failed to apply symbology to {layer_name}: {e}")
        
        try:
            logging.info(f"🔄 Attempting fallback symbology for {layer_name}")
            layer.symbology.renderer.symbol.color = {'RGB': [0, 0, 0, 100]} if "Robbery" in layer_name else {'RGB': [255, 255, 0, 100]}
            layer.symbology.renderer.symbol.size = 8
            logging.info(f"✅ Fallback symbology applied to {layer_name}")
        except Exception as fallback_error:
            logging.error(f"❌ Fallback symbology also failed for {layer_name}: {fallback_error}")

def export_maps(crime_type, output_folder, args):
    """
    Export crime maps showing ONLY 7-Day incidents using Excel-based periods.
    Enhanced with symbology fixes and map extent adjustments.
    
    Args:
        crime_type (str): Type of crime to map
        output_folder (str): Base directory (will create crime-specific subfolder)
        args (list): Arguments list where args[6] contains date in format "YYYY_MM_DD"
        
    Returns:
        bool: True if successful, False otherwise
    """
    aprx = None
    
    try:
        if not validate_config():
            return False
            
        logging.info(f"🗺️ Starting Excel-based 7-Day map export for: {crime_type}")
        
        try:
            date_str = args[6]
            target_date = datetime.strptime(date_str, "%Y_%m_%d").date()
            arcpy.AddMessage(f"📅 Using date from args: {target_date}")
        except (IndexError, TypeError, ValueError):
            target_date = date.today()
            date_str = target_date.strftime("%Y_%m_%d")
            
        crime_output_folder = get_crime_type_folder(crime_type, date_str)
        os.makedirs(crime_output_folder, exist_ok=True)
        arcpy.AddMessage(f"📁 Crime-specific folder: {crime_output_folder}")
        
        filename_prefix = get_standardized_filename(crime_type)
        
        aprx = arcpy.mp.ArcGISProject(APR_PATH)
        arcpy.AddMessage(f"✅ Loaded ArcGIS Pro project: {APR_PATH}")
        
        layouts = aprx.listLayouts("Crime Report Legend")
        if not layouts:
            arcpy.AddError("❌ Layout 'Crime Report Legend' not found")
            available_layouts = [layout.name for layout in aprx.listLayouts()]
            arcpy.AddError(f"Available layouts: {available_layouts}")
            return False
            
        layout = layouts[0]
        arcpy.AddMessage(f"✅ Found layout: {layout.name}")
        
        map_frames = layout.listElements("MAPFRAME_ELEMENT")
        if not map_frames:
            arcpy.AddError("❌ No map frame elements found in layout")
            return False
            
        map_frame = map_frames[0]
        map_obj = map_frame.map
        arcpy.AddMessage(f"✅ Found map: {map_obj.name}")

        # Store original layer states
        original_states = {lyr.name: {'visible': lyr.visible, 'transparency': lyr.transparency} for lyr in map_obj.listLayers()}
        
        # Hide all layers initially
        for lyr in map_obj.listLayers():
            lyr.visible = False
        arcpy.AddMessage(f"🔄 Hidden {len(map_obj.listLayers())} layers initially")

        # Show base layers
        base_layers = ["City Boundaries", "OpenStreetMap Light Gray Canvas Reference", "Light Gray Canvas (for Export)", "World Light Gray Canvas Base", "OpenStreetMap", "Streets"]
        for lyr in map_obj.listLayers():
            if any(base_name in lyr.name for base_name in base_layers):
                lyr.visible = True
                lyr.transparency = 0
                arcpy.AddMessage(f"✅ Enabled base layer: {lyr.name}")

        # Get Excel-based 7-day period dates
        start_date, end_date = get_7day_period_dates(target_date)
        if not start_date or not end_date:
            arcpy.AddError(f"❌ Could not determine Excel 7-day period for {target_date}")
            return False
            
        arcpy.AddMessage(f"📅 Excel 7-Day period: {start_date} to {end_date}")

        # Find and configure ONLY the 7-Day layer
        layer_name = f"{crime_type} 7-Day"
        target_layer = next((lyr for lyr in map_obj.listLayers() if lyr.name == layer_name), None)
        
        if not target_layer:
    def cleanup_patch_elements(layout):
    """
    Remove patch elements from layout.
    """
    try:
        elements_to_remove = [elm for elm in layout.listElements("PICTURE_ELEMENT") if "hackensack" in elm.name.lower() or "patch" in elm.name.lower()]
        if not elements_to_remove:
            arcpy.AddMessage("💡 No patch elements found to remove")
            return
                
        for elm in elements_to_remove:
            try:
                layout.removeElement(elm)
                arcpy.AddMessage(f"🧹 Removed patch element: {elm.name}")
            except Exception as e:
                arcpy.AddWarning(f"❌ Failed to remove patch element {elm.name}: {str(e)}")
                
        arcpy.AddMessage(f"✅ Patch cleanup completed: {len(elements_to_remove)} elements processed")
                
    except Exception as e:
        arcpy.AddWarning(f"❌ Patch cleanup failed: {str(e)}")

def export_map_to_png(layout, crime_type, output_folder, filename_prefix):
    """
    Export layout to PNG file with standardized naming.
    
    Args:
        layout: ArcPy layout object
        crime_type (str): Type of crime for logging
        output_folder (str): Output directory
        filename_prefix (str): Standardized filename prefix
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            arcpy.AddMessage(f"📁 Created output folder: {output_folder}")
        else:
            arcpy.AddMessage(f"📁 Using existing output folder: {output_folder}")
            
        # Clean up old map files
        cleanup_pattern = os.path.join(output_folder, f"{filename_prefix}_Map*.png")
        old_files = glob.glob(cleanup_pattern)
        
        for file_path in old_files:
            try:
                os.remove(file_path)
                arcpy.AddMessage(f"🧹 Deleted old export: {os.path.basename(file_path)}")
            except Exception as e:
                arcpy.AddWarning(f"⚠️ Could not delete old map file {file_path}: {str(e)}")
        
        export_filename = f"{filename_prefix}_Map.png"
        export_path = os.path.join(output_folder, export_filename)
        
        arcpy.AddMessage(f"🖼️ Exporting Excel-based 7-Day map to: {export_path}")
        layout.exportToPNG(export_path, resolution=200)
        
        if os.path.exists(export_path):
            file_size = os.path.getsize(export_path)
            arcpy.AddMessage(f"✅ Excel-based 7-Day map exported successfully: {export_path} ({file_size:,} bytes)")
            return True
        else:
            arcpy.AddError(f"❌ Export file was not created: {export_path}")
            return False
        
    except Exception as e:
        arcpy.AddError(f"❌ Export failed: {str(e)}")
        logging.error(f"Map export failed for {crime_type}: {e}", exc_info=True)
        return False

# Legacy function compatibility
def apply_symbology(layer, layer_name):
    """Legacy function - redirects to enhanced version."""
    apply_symbology_enhanced(layer, layer_name)

def build_sql_filter_7day(crime_type, start_date):
    """Legacy function - now uses Excel integration."""
    try:
        if isinstance(start_date, str):
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_date_obj = start_date
            
        target_date = start_date_obj + timedelta(days=7)
        excel_start, excel_end = get_7day_period_dates(target_date)
        
        if excel_start and excel_end:
            return build_sql_filter_7day_excel(crime_type, excel_start, excel_end)
        else:
            return build_sql_filter_7day_excel(crime_type, start_date_obj, start_date_obj + timedelta(days=6))
            
    except Exception as e:
        arcpy.AddError(f"❌ Error in legacy SQL filter: {e}")
        return None

def build_sql_filter(crime_type, start_date):
    """Legacy function - redirects to Excel-based 7-day version for compatibility."""
    return build_sql_filter_7day(crime_type, start_date)

def update_legend_visibility(layout, map_obj, suffix_layers):
    """Legacy function - redirects to 7-day version."""
    if suffix_layers:
        for key, layer in suffix_layers:
            if "7-Day" in key:
                update_legend_visibility_7day(layout, map_obj, layer)
                break 7-Day layer not found: {layer_name}")
            export_filename = f"{filename_prefix}_Map.png"
            export_path = os.path.join(crime_output_folder, export_filename)
            success = create_placeholder_image(crime_type, export_path, start_date, end_date)
            return success
        
        target_layer.visible = True
        target_layer.transparency = 0
        arcpy.AddMessage(f"✅ Configured 7-Day layer: {target_layer.name}")

        # CODE_20250622_007: Adjust map extent to include all features
        if target_layer:
            try:
                layer_extent = arcpy.Describe(target_layer).extent
                map_frame.camera.setExtent(layer_extent)
                arcpy.AddMessage(f"✅ Adjusted map extent to: {layer_extent}")
            except Exception as e:
                arcpy.AddWarning(f"⚠️ Could not adjust map extent: {e}")

        # Apply definition query if supported
        if target_layer.supports("DEFINITIONQUERY"):
            filter_sql = build_sql_filter_7day_excel(crime_type, start_date, end_date)
            
            if filter_sql:
                arcpy.AddMessage(f"🔎 Excel-based SQL for 7-Day {layer_name}: {filter_sql}")
                target_layer.definitionQuery = filter_sql
                arcpy.AddMessage(f"✅ Applied Excel-based query to {target_layer.name}")
                
                try:
                    feature_count = int(arcpy.GetCount_management(target_layer).getOutput(0))
                    arcpy.AddMessage(f"📊 7-Day features: {feature_count}")
                    
                    if feature_count == 0:
                        arcpy.AddMessage(f"📋 No 7-day incidents for {crime_type}, creating placeholder")
                        export_filename = f"{filename_prefix}_Map.png"
                        export_path = os.path.join(crime_output_folder, export_filename)
                        success = create_placeholder_image(crime_type, export_path, start_date, end_date)
                        restore_layer_states(map_obj, original_states)
                        return success
                        
                except Exception as e:
                    arcpy.AddWarning(f"⚠️ Could not get feature count: {e}")
            else:
                arcpy.AddWarning(f"⚠️ Could not build SQL filter for {crime_type}")

        # Apply enhanced symbology
        apply_symbology_enhanced(target_layer, layer_name)

        # Update legend to show only 7-Day layer
        update_legend_visibility_7day(layout, map_obj, target_layer)

        # Clean up patch elements
        cleanup_patch_elements(layout)

        # Export the map
        success = export_map_to_png(layout, crime_type, crime_output_folder, filename_prefix)
        
        # Restore original layer states
        restore_layer_states(map_obj, original_states)
        
        if success:
            arcpy.AddMessage(f"✅ Excel-based 7-Day map export completed successfully for {crime_type}")
        
        return success
        
    except Exception as e:
        arcpy.AddError(f"❌ Critical error in export_maps: {str(e)}")
        logging.error(f"Critical error in export_maps for {crime_type}: {e}", exc_info=True)
        return False
    finally:
        if aprx:
            try:
                del aprx
                arcpy.AddMessage("🧹 Cleaned up ArcGIS Pro project reference")
            except Exception as e:
                arcpy.AddWarning(f"⚠️ Could not clean up project reference: {e}")

def build_sql_filter_7day_excel(crime_type, start_date, end_date):
    """
    Build SQL filter for 7-Day period using Excel dates from config.
    
    Args:
        crime_type (str): Type of crime
        start_date (date): Start date from Excel
        end_date (date): End date from Excel
    
    Returns:
        str: SQL filter string or None if invalid
    """
    try:
        start_timestamp = f"{start_date.strftime('%Y-%m-%d')} 00:00:00.000"
        end_timestamp = f"{end_date.strftime('%Y-%m-%d')} 23:59:59.999"
        
        arcpy.AddMessage(f"📅 Excel-based 7-Day filter period: {start_date} to {end_date}")
        
    except Exception as e:
        arcpy.AddError(f"❌ Error formatting Excel dates: {e}")
        return None
    
    base_conditions = f"disposition LIKE '%See Report%' AND calldate >= timestamp '{start_timestamp}' AND calldate <= timestamp '{end_timestamp}'"
    pattern = get_sql_pattern_for_crime(crime_type)
    arcpy.AddMessage(f"💡 Using pattern for {crime_type}: {pattern}")
    
    if isinstance(pattern, list):
        conditions = [f"calltype LIKE '%{p}%'" for p in pattern]
        crime_condition = f"({' OR '.join(conditions)})"
    else:
        crime_condition = f"calltype LIKE '%{pattern}%'"
    
    sql_filter = f'{crime_condition} AND {base_conditions}'
    arcpy.AddMessage(f"🔎 Final Excel-based SQL filter: {sql_filter}")
    return sql_filter

def restore_layer_states(map_obj, original_states):
    """
    Restore all layers to their original visibility and transparency states.
    """
    try:
        for lyr in map_obj.listLayers():
            if lyr.name in original_states:
                lyr.visible = original_states[lyr.name]['visible']
                lyr.transparency = original_states[lyr.name]['transparency']
        arcpy.AddMessage("✅ Restored original layer states")
    except Exception as e:
        arcpy.AddWarning(f"⚠️ Error restoring layer states: {e}")

def update_legend_visibility_7day(layout, map_obj, target_layer):
    """
    Update legend to show only the 7-Day layer.
    """
    try:
        legend = next((elm for elm in layout.listElements("LEGEND_ELEMENT") if elm.name.strip().lower() == "mainlegend"), None)
        if not legend:
            arcpy.AddWarning("⚠️ Legend element 'mainlegend' not found")
            return
        
        arcpy.AddMessage(f"✅ Found legend with {len(legend.items)} items")
        legend.syncLayerVisibility = False
        
        for item in legend.items:
            item.visible = False
        
        shown_count = 0
        for item in legend.items:
            if item.name == target_layer.name:
                item.visible = True
                shown_count += 1
                arcpy.AddMessage(f"✅ Showing in legend: {item.name}")
        
        arcpy.AddMessage(f"🎯 Legend updated: {shown_count} items shown (7-Day only)")
        
    except Exception as e:
        arcpy.AddWarning(f"❌