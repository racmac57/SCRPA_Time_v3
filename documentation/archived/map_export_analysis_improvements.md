# 🕒 2025-06-22-01-25-00
# Police_Data_Analysis/map_export_clean_fixed
# Author: R. A. Carucci
# Purpose: Clean, fixed map_export.py with proper structure, Excel integration, and improved symbology preservation

import arcpy
import os
import glob
import logging
from datetime import datetime, timedelta, date
from config import APR_PATH, SYM_LAYER_PATH, SUFFIXES, get_7day_period_dates, get_standardized_filename, get_crime_type_folder, get_sql_pattern_for_crime
from PIL import Image, ImageDraw, ImageFont

print("✅ map_export.py loaded successfully")

def validate_config():
    """
    Validate configuration parameters.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
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
    """
    Sanitize text for use in filenames.
    
    Args:
        text (str): Text to sanitize
        
    Returns:
        str: Sanitized text safe for filenames
    """
    # Replace problematic characters for filenames
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
    """
    Create ENHANCED placeholder image with 7-day period information.
    
    Args:
        crime_type (str): Name of crime type
        output_path (str): Path to save the placeholder image
        start_date (date): Start date of 7-day period
        end_date (date): End date of 7-day period
        
    Returns:
        bool: True if successful
    """
    try:
        # Image dimensions (converted from inches at 200 DPI)
        # 5.74" x 4.44" at 200 DPI = 1148 x 888 pixels
        width = 1148
        height = 888
        
        # Create white background
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a system font, fallback to default
        try:
            # Try common Windows fonts
            title_font = ImageFont.truetype("arial.ttf", 48)
            subtitle_font = ImageFont.truetype("arial.ttf", 36)
            text_font = ImageFont.truetype("arial.ttf", 32)
            period_font = ImageFont.truetype("arial.ttf", 28)
        except:
            try:
                title_font = ImageFont.truetype("calibri.ttf", 48)
                subtitle_font = ImageFont.truetype("calibri.ttf", 36)
                text_font = ImageFont.truetype("calibri.ttf", 32)
                period_font = ImageFont.truetype("calibri.ttf", 28)
            except:
                # Fallback to default font
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
                period_font = ImageFont.load_default()
        
        # Calculate text content
        title_text = crime_type
        subtitle_text = "Weekly Incident Report"
        main_text = "0 incidents recorded (7-day period)"
        
        # Add period information if available
        if start_date and end_date:
            period_text = f"Period: {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"
        else:
            period_text = "7-Day Analysis Period"
        
        # Get text bounding boxes for centering
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        main_bbox = draw.textbbox((0, 0), main_text, font=text_font)
        period_bbox = draw.textbbox((0, 0), period_text, font=period_font)
        
        title_width = title_bbox[2] - title_bbox[0]
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        main_width = main_bbox[2] - main_bbox[0]
        period_width = period_bbox[2] - period_bbox[0]
        
        # Center positions
        title_x = (width - title_width) // 2
        subtitle_x = (width - subtitle_width) // 2
        main_x = (width - main_width) // 2
        period_x = (width - period_width) // 2
        
        # Vertical positions
        title_y = height // 4
        subtitle_y = height // 2 - 70
        main_y = height // 2 - 10
        period_y = height // 2 + 30
        
        # Draw text
        draw.text((title_x, title_y), title_text, fill='black', font=title_font)
        draw.text((subtitle_x, subtitle_y), subtitle_text, fill='#666666', font=subtitle_font)
        draw.text((main_x, main_y), main_text, fill='#333333', font=text_font)
        draw.text((period_x, period_y), period_text, fill='#0066CC', font=period_font)
        
        # Add a subtle border
        border_color = '#CCCCCC'
        draw.rectangle([10, 10, width-10, height-10], outline=border_color, width=2)
        
        # Save the image
        img.save(output_path, 'PNG', dpi=(200, 200))
        arcpy.AddMessage(f"✅ Created ENHANCED placeholder image with period info: {output_path}")
        
        return True
        
    except Exception as e:
        arcpy.AddError(f"❌ Error creating enhanced placeholder image: {e}")
        return False

def debug_layer_properties(layer):
    """Debug function to examine layer symbology properties"""
    try:
        arcpy.AddMessage(f"🔍 DEBUG: Examining {layer.name}")
        
        # Check if layer has symbology
        if hasattr(layer, 'symbology'):
            sym = layer.symbology
            arcpy.AddMessage(f"🔍 Symbology type: {type(sym)}")
            
            # Check renderer
            if hasattr(sym, 'renderer'):
                arcpy.AddMessage(f"🔍 Renderer type: {type(sym.renderer)}")
                
                # Check symbol
                if hasattr(sym.renderer, 'symbol'):
                    symbol = sym.renderer.symbol
                    arcpy.AddMessage(f"🔍 Symbol type: {type(symbol)}")
                    
                    # Check color
                    try:
                        color = symbol.color
                        arcpy.AddMessage(f"🔍 Current color: {color}")
                    except:
                        arcpy.AddMessage(f"🔍 Could not read color property")
                    
                    # Check size
                    try:
                        size = symbol.size
                        arcpy.AddMessage(f"🔍 Current size: {size}")
                    except:
                        arcpy.AddMessage(f"🔍 Could not read size property")
        
    except Exception as e:
        arcpy.AddMessage(f"🔍 DEBUG error: {e}")

def export_maps(crime_type, output_folder, args):
    """
    Export crime maps showing ONLY 7-Day incidents using Excel-based periods.
    Creates enhanced placeholder images for crime types with 0 7-day incidents.
    Organizes files in crime-specific subfolders.
    
    Args:
        crime_type (str): Type of crime to map
        output_folder (str): Base directory (will create crime-specific subfolder)
        args (list): Arguments list where args[6] contains date in format "YYYY_MM_DD"
        
    Returns:
        bool: True if successful, False otherwise
    """
    aprx = None
    
    try:
        # Validate configuration first
        if not validate_config():
            return False
            
        logging.info(f"🗺️ Starting Excel-based 7-Day map export for: {crime_type}")
        
        # Get date from args
        try:
            date_str = args[6]  # YYYY_MM_DD format
            target_date = datetime.strptime(date_str, "%Y_%m_%d").date()
            arcpy.AddMessage(f"📅 Using date from args: {target_date}")
        except (IndexError, TypeError, ValueError):
            target_date = date.today()
            date_str = target_date.strftime("%Y_%m_%d")
            
        # Create crime-specific output folder using Excel naming
        crime_output_folder = get_crime_type_folder(crime_type, date_str)
        os.makedirs(crime_output_folder, exist_ok=True)
        arcpy.AddMessage(f"📁 Crime-specific folder: {crime_output_folder}")
        
        # Get standardized filename prefix
        filename_prefix = get_standardized_filename(crime_type)
        
        # Load ArcGIS Pro project
        aprx = arcpy.mp.ArcGISProject(APR_PATH)
        arcpy.AddMessage(f"✅ Loaded ArcGIS Pro project: {APR_PATH}")
        
        # Get layout and map objects
        layouts = aprx.listLayouts("Crime Report Legend")
        if not layouts:
            arcpy.AddError("❌ Layout 'Crime Report Legend' not found")
            available_layouts = [layout.name for layout in aprx.listLayouts()]
            arcpy.AddError(f"Available layouts: {available_layouts}")
            return False
            
        layout = layouts[0]
        arcpy.AddMessage(f"✅ Found layout: {layout.name}")
        
        # Get map frame
        map_frames = layout.listElements("MAPFRAME_ELEMENT")
        if not map_frames:
            arcpy.AddError("❌ No map frame elements found in layout")
            return False
            
        map_frame = map_frames[0]
        map_obj = map_frame.map
        arcpy.AddMessage(f"✅ Found map: {map_obj.name}")

        # Store original layer states for restoration
        original_states = {}
        for lyr in map_obj.listLayers():
            original_states[lyr.name] = {
                'visible': lyr.visible,
                'transparency': lyr.transparency
            }

        # Hide all layers initially
        layer_count = 0
        for lyr in map_obj.listLayers():
            lyr.visible = False
            layer_count += 1
        arcpy.AddMessage(f"🔄 Hidden {layer_count} layers initially")

        # Show base layers
        base_layers = [
            "City Boundaries",
            "OpenStreetMap Light Gray Canvas Reference", 
            "Light Gray Canvas (for Export)",
            "World Light Gray Canvas Base",
            "OpenStreetMap",
            "Streets"
        ]
        
        base_layers_found = 0
        for lyr in map_obj.listLayers():
            if any(base_name in lyr.name for base_name in base_layers):
                lyr.visible = True
                lyr.transparency = 0
                base_layers_found += 1
                arcpy.AddMessage(f"✅ Enabled base layer: {lyr.name}")
        
        arcpy.AddMessage(f"✅ Enabled {base_layers_found} base layers")

        # Get Excel-based 7-day period dates
        start_date, end_date = get_7day_period_dates(target_date)
        
        if not start_date or not end_date:
            arcpy.AddError(f"❌ Could not determine Excel 7-day period for {target_date}")
            return False
            
        arcpy.AddMessage(f"📅 Excel 7-Day period: {start_date} to {end_date}")

        # Show available layers for debugging
        all_layers = [lyr.name for lyr in map_obj.listLayers()]
        arcpy.AddMessage(f"📋 Available layers: {all_layers}")

        # Find and configure ONLY the 7-Day layer
        layer_name = f"{crime_type} 7-Day"
        target_layer = None
        
        for lyr in map_obj.listLayers():
            if lyr.name == layer_name:
                target_layer = lyr
                break
        
        if not target_layer:
            arcpy.AddWarning(f"❌ 7-Day layer not found: {layer_name}")
            # Create enhanced placeholder and return
            export_filename = f"{filename_prefix}_Map.png"
            export_path = os.path.join(crime_output_folder, export_filename)
            success = create_placeholder_image(crime_type, export_path, start_date, end_date)
            return success
        
        # Show only the 7-Day layer
        target_layer.visible = True
        target_layer.transparency = 0  # Full opacity for single layer
        arcpy.AddMessage(f"✅ Configured 7-Day layer: {target_layer.name}")

        # Apply definition query if supported using Excel dates
        if target_layer.supports("DEFINITIONQUERY"):
            filter_sql = build_sql_filter_7day_excel(crime_type, start_date, end_date)
            
            if filter_sql:
                arcpy.AddMessage(f"🔎 Excel-based SQL for 7-Day {layer_name}: {filter_sql}")
                target_layer.definitionQuery = filter_sql
                arcpy.AddMessage(f"✅ Applied Excel-based query to {target_layer.name}")
                
                # Log feature count
                try:
                    feature_count = int(arcpy.GetCount_management(target_layer).getOutput(0))
                    arcpy.AddMessage(f"📊 7-Day features: {feature_count}")
                    
                    # If no features, create enhanced placeholder instead of map
                    if feature_count == 0:
                        arcpy.AddMessage(f"📋 No 7-day incidents for {crime_type}, creating placeholder")
                        export_filename = f"{filename_prefix}_Map.png"
                        export_path = os.path.join(crime_output_folder, export_filename)
                        success = create_placeholder_image(crime_type, export_path, start_date, end_date)
                        
                        # Restore original layer states
                        restore_layer_states(map_obj, original_states)
                        return success
                        
                except Exception as e:
                    arcpy.AddWarning(f"⚠️ Could not get feature count: {e}")
            else:
                arcpy.AddWarning(f"⚠️ Could not build SQL filter for {crime_type}")

        # Debug layer properties before symbology changes
        debug_layer_properties(target_layer)
        
        # Apply ENHANCED symbology to the 7-Day layer
        apply_symbology_enhanced(target_layer, layer_name)
        
        # Debug layer properties after symbology changes
        debug_layer_properties(target_layer)

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
        # Clean up ArcGIS Pro project
        if aprx:
            try:
                del aprx
                arcpy.AddMessage("🧹 Cleaned up ArcGIS Pro project reference")
            except Exception as e:
                arcpy.AddWarning(f"⚠️ Could not clean up project reference: {e}")

def apply_symbology_enhanced(layer, layer_name):
    """
    Apply ENHANCED symbology - PRESERVE original colors, enhance visibility only
    """
    try:
        if any(crime in layer_name for crime in ["Robbery", "MV Theft", "Burglary", "Sexual Offenses"]):
            arcpy.AddMessage(f"🎨 Enhancing symbology for {layer_name}")
            
            # Debug current state
            try:
                current_color = layer.symbology.renderer.symbol.color
                arcpy.AddMessage(f"🎨 Preserving current color: {current_color}")
            except:
                arcpy.AddMessage(f"🎨 Using default color scheme")
            
            # Enhance size only, preserve color
            try:
                sym = layer.symbology
                if hasattr(sym, 'renderer') and hasattr(sym.renderer, 'symbol'):
                    # Store current color
                    original_color = None
                    try:
                        original_color = sym.renderer.symbol.color
                    except:
                        pass
                    
                    # Enhance size for visibility
                    if hasattr(sym.renderer.symbol, 'size'):
                        sym.renderer.symbol.size = 10
                        
                        # Restore original color if we had one
                        if original_color:
                            try:
                                sym.renderer.symbol.color = original_color
                            except:
                                pass
                        
                        layer.symbology = sym
                        arcpy.AddMessage(f"✅ Enhanced {layer_name} (preserved original color)")
                        return
            except Exception as e:
                arcpy.AddWarning(f"⚠️ Symbology enhancement failed: {e}")
            
            arcpy.AddMessage(f"💡 Using default symbology for {layer_name}")
        else:
            arcpy.AddMessage(f"💡 Skipping symbology for non-crime layer: {layer_name}")
    except Exception as e:
        arcpy.AddWarning(f"❌ Symbology error on {layer_name}: {str(e)}")

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
        # Format dates for SQL (using timestamp format)
        start_timestamp = f"{start_date.strftime('%Y-%m-%d')} 00:00:00.000"
        end_timestamp = f"{end_date.strftime('%Y-%m-%d')} 23:59:59.999"
        
        arcpy.AddMessage(f"📅 Excel-based 7-Day filter period: {start_date} to {end_date}")
        arcpy.AddMessage(f"🔍 Start timestamp: {start_timestamp}")
        arcpy.AddMessage(f"🔍 End timestamp: {end_timestamp}")
        
    except Exception as e:
        arcpy.AddError(f"❌ Error formatting Excel dates: {e}")
        return None
    
    # Base conditions for Excel-based 7-day period
    base_conditions = f"disposition LIKE '%See Report%' AND calldate >= timestamp '{start_timestamp}' AND calldate <= timestamp '{end_timestamp}'"
    
    # Get pattern from config
    pattern = get_sql_pattern_for_crime(crime_type)
    arcpy.AddMessage(f"💡 Using pattern for {crime_type}: {pattern}")
    
    # Build crime condition based on pattern type
    if isinstance(pattern, list):
        conditions = []
        for p in pattern:
            conditions.append(f"calltype LIKE '%{p}%'")
        crime_condition = f"({' OR '.join(conditions)})"
    else:
        crime_condition = f"calltype LIKE '%{pattern}%'"
    
    sql_filter = f'{crime_condition} AND {base_conditions}'
    
    arcpy.AddMessage(f"🔎 Final Excel-based SQL filter: {sql_filter}")
    return sql_filter

def build_sql_filter_7day(crime_type, start_date):
    """
    Legacy function - now uses Excel integration.
    """
    try:
        # Convert start_date string to date object if needed
        if isinstance(start_date, str):
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_date_obj = start_date
            
        # Calculate target date (report due date) 
        target_date = start_date_obj + timedelta(days=7)
        
        # Get Excel-based period
        excel_start, excel_end = get_7day_period_dates(target_date)
        
        if excel_start and excel_end:
            return build_sql_filter_7day_excel(crime_type, excel_start, excel_end)
        else:
            # Fallback to original method
            return build_sql_filter_7day_excel(crime_type, start_date_obj, start_date_obj + timedelta(days=6))
            
    except Exception as e:
        arcpy.AddError(f"❌ Error in legacy SQL filter: {e}")
        return None

def build_sql_filter(crime_type, start_date):
    """
    Legacy function - redirects to Excel-based 7-day version for compatibility.
    """
    return build_sql_filter_7day(crime_type, start_date)

def restore_layer_states(map_obj, original_states):
    """
    Restore all layers to their original visibility and transparency states.
    
    Args:
        map_obj: ArcPy map object
        original_states (dict): Dictionary of original layer states
    """
    try:
        for lyr in map_obj.listLayers():
            if lyr.name in original_states:
                lyr.visible = original_states[lyr.name]['visible']
                lyr.transparency = original_states[lyr.name]['transparency']
        arcpy.AddMessage("✅ Restored original layer states")
    except Exception as e:
        arcpy.AddWarning(f"⚠️ Error restoring layer states: {e}")

def apply_symbology(layer, layer_name):
    """
    Legacy function - redirects to enhanced version.
    """
    apply_symbology_enhanced(layer, layer_name)

def update_legend_visibility_7day(layout, map_obj, target_layer):
    """
    Update legend to show only the 7-Day layer.
    
    Args:
        layout: ArcPy layout object
        map_obj: ArcPy map object  
        target_layer: The 7-Day layer to show in legend
    """
    try:
        # Find legend element (case-insensitive search)
        legend = None
        for elm in layout.listElements("LEGEND_ELEMENT"):
            if elm.name.strip().lower() == "mainlegend":
                legend = elm
                break
                
        if not legend:
            arcpy.AddWarning("⚠️ Legend element 'mainlegend' not found")
            return
        
        arcpy.AddMessage(f"✅ Found legend with {len(legend.items)} items")
        
        # Disable syncLayerVisibility so we can control legend manually
        legend.syncLayerVisibility = False
        arcpy.AddMessage(f"🔧 Disabled syncLayerVisibility for manual control")
        
        # Hide all legend items first
        for item in legend.items:
            item.visible = False
        
        # Show only the 7-Day layer in legend
        shown_count = 0
        for item in legend.items:
            if item.name == target_layer.name:
                item.visible = True
                shown_count += 1
                arcpy.AddMessage(f"✅ Showing in legend: {item.name}")
        
        arcpy.AddMessage(f"🎯 Legend updated: {shown_count} items shown (7-Day only)")
        
    except Exception as e:
        arcpy.AddWarning(f"❌ Legend update error: {str(e)}")

def update_legend_visibility(layout, map_obj, suffix_layers):
    """
    Legacy function - redirects to 7-day version.
    """
    if suffix_layers:
        # Find the 7-Day layer from suffix_layers
        for key, layer in suffix_layers:
            if "7-Day" in key:
                update_legend_visibility_7day(layout, map_obj, layer)
                break

def cleanup_patch_elements(layout):
    """
    Remove patch elements from layout.
    
    Args:
        layout: ArcPy layout object
    """
    try:
        elements_to_remove = []
        for elm in layout.listElements("PICTURE_ELEMENT"):
            if "hackensack" in elm.name.lower() or "patch" in elm.name.lower():
                elements_to_remove.append(elm)
                
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
        # Ensure output folder exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            arcpy.AddMessage(f"📁 Created output folder: {output_folder}")
        else:
            arcpy.AddMessage(f"📁 Using existing output folder: {output_folder}")
            
        # Clean up old map files with standardized pattern
        cleanup_pattern = os.path.join(output_folder, f"{filename_prefix}_Map*.png")
        old_files = glob.glob(cleanup_pattern)
        
        removed_count = 0
        for file_path in old_files:
            try:
                os.remove(file_path)
                arcpy.AddMessage(f"🧹 Deleted old export: {os.path.basename(file_path)}")
                removed_count += 1
            except Exception as e:
                arcpy.AddWarning(f"⚠️ Could not delete old map file {file_path}: {str(e)}")
        
        if removed_count > 0:
            arcpy.AddMessage(f"✅ Cleaned up {removed_count} old map files")

        # Export new map with standardized filename
        export_filename = f"{filename_prefix}_Map.png"
        export_path = os.path.join(output_folder, export_filename)
        
        # Export with error handling
        arcpy.AddMessage(f"🖼️ Exporting Excel-based 7-Day map to: {export_path}")
        layout.exportToPNG(export_path, resolution=200)
        
        # Verify export was successful
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