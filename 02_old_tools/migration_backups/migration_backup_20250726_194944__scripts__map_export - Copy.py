# 🕒 2025-01-27-23-50-00
# SCRPA_Place_and_Time/map_export_final_complete
# Author: R. A. Carucci
# Purpose: Final complete production-ready map export with enhanced symbology and coordinate system fixes

import arcpy
import os
import glob
import logging
from datetime import datetime, timedelta, date
from config import APR_PATH, get_7day_period_dates, get_standardized_filename, get_crime_type_folder, get_sql_pattern_for_crime

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
    sanitized = (text
                .replace(" ", "_")
                .replace("&", "And")
                .replace("/", "_")
                .replace("\\", "_")
                .replace(":", "_")
                .replace("*", "_")
                .replace("?", "_")
                .replace('"', "_")
                .replace("<", "_")
                .replace(">", "_")
                .replace("|", "_")
                .replace("-", "_"))
    
    return sanitized

def create_placeholder_image(crime_type, output_path):
    """
    Create a placeholder image for crime types with 0 incidents in 7-day period.
    
    Args:
        crime_type (str): Name of crime type
        output_path (str): Path to save the placeholder image
        
    Returns:
        bool: True if successful
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Image dimensions (converted from inches at 200 DPI)
        # 5.74" x 4.44" at 200 DPI = 1148 x 888 pixels
        width = 1148
        height = 888
        
        # Create white background
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a system font, fallback to default
        try:
            title_font = ImageFont.truetype("arial.ttf", 48)
            subtitle_font = ImageFont.truetype("arial.ttf", 36)
            text_font = ImageFont.truetype("arial.ttf", 32)
        except IOError: # Use IOError for font not found
            try:
                title_font = ImageFont.truetype("calibri.ttf", 48)
                subtitle_font = ImageFont.truetype("calibri.ttf", 36)
                text_font = ImageFont.truetype("calibri.ttf", 32)
            except IOError:
                # Fallback to default font if custom fonts are not found
                logging.warning("System fonts (arial.ttf, calibri.ttf) not found. Using default PIL font.")
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
        
        # Calculate text positions (centered)
        title_text = crime_type
        subtitle_text = "Weekly Incident Report"
        main_text = "0 incidents recorded (7-day period)"
        
        # Get text bounding boxes for centering
        # Use textlength for accurate width calculation before Python 3.10, or textbbox for 3.10+
        try:
            title_width = draw.textlength(title_text, font=title_font)
            subtitle_width = draw.textlength(subtitle_text, font=subtitle_font)
            main_width = draw.textlength(main_text, font=text_font)
        except AttributeError: # Fallback for older Pillow/Python versions
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            main_bbox = draw.textbbox((0, 0), main_text, font=text_font)
            title_width = title_bbox[2] - title_bbox[0]
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            main_width = main_bbox[2] - main_bbox[0]

        # Center positions
        title_x = (width - title_width) // 2
        subtitle_x = (width - subtitle_width) // 2
        main_x = (width - main_width) // 2
        
        # Vertical positions
        title_y = height // 4
        subtitle_y = height // 2 - 50
        main_y = height // 2 + 20
        
        # Draw text
        draw.text((title_x, title_y), title_text, fill='black', font=title_font)
        draw.text((subtitle_x, subtitle_y), subtitle_text, fill='#666666', font=subtitle_font)
        draw.text((main_x, main_y), main_text, fill='#333333', font=text_font)
        
        # Add a subtle border
        border_color = '#CCCCCC'
        draw.rectangle([10, 10, width-10, height-10], outline=border_color, width=2)
        
        # Save the image
        img.save(output_path, 'PNG', dpi=(200, 200))
        arcpy.AddMessage(f"✅ Created placeholder image: {output_path}")
        
        return True
        
    except ImportError:
        arcpy.AddError("❌ PIL (Pillow) library not found. Cannot create placeholder images.")
        arcpy.AddError("   Please install Pillow: pip install Pillow")
        return False
    except Exception as e:
        arcpy.AddError(f"❌ Error creating placeholder image: {e}")
        return False

def calculate_hackensack_focused_extent(target_layer, map_frame):
    """
    Calculate optimal extent focused tightly on Hackensack area with coordinate system validation
    """
    try:
        # Get incident count
        incident_count = int(arcpy.GetCount_management(target_layer).getOutput(0))
        
        # Get spatial reference systems for validation
        layer_sr = arcpy.Describe(target_layer).spatialReference
        map_sr = map_frame.map.spatialReference
        
        arcpy.AddMessage(f"🔍 Layer SR: {layer_sr.name} (WKID: {layer_sr.factoryCode})")
        arcpy.AddMessage(f"🔍 Map SR: {map_sr.name} (WKID: {map_sr.factoryCode})")
        
        # Check for spatial reference mismatch
        if layer_sr.factoryCode != map_sr.factoryCode:
            arcpy.AddWarning(f"⚠️ Spatial reference mismatch detected:")
            arcpy.AddWarning(f"   Layer: {layer_sr.name} (WKID: {layer_sr.factoryCode})")
            arcpy.AddWarning(f"   Map: {map_sr.name} (WKID: {map_sr.factoryCode})")
            arcpy.AddMessage("🔁 Proceeding with automatic projection handling...")
        
        # Hackensack, NJ coordinates - determine based on map coordinate system
        # Preferred: NAD83 / New Jersey (US Feet) - WKID: 2900
        # Common alternative: WGS84 Web Mercator Auxiliary Sphere - WKID: 3857 (often used by base maps)
        # Geographic WGS84 - WKID: 4326 (Lat/Lon)

        hackensack_center_x, hackensack_center_y, unit_name = None, None, None

        if map_sr.factoryCode == 2900:  # NAD83 / New Jersey (US Feet)
            hackensack_center_x = 646000 # Example for Hackensack City Hall in State Plane NJ (feet)
            hackensack_center_y = 764000
            unit_name = "feet"
        elif map_sr.factoryCode == 3857: # WGS84 Web Mercator (often default for online base maps)
            # Coordinates for Hackensack in Web Mercator (meters)
            hackensack_center_x = -8240000 # Approx. Longitude (meters)
            hackensack_center_y = 4850000  # Approx. Latitude (meters)
            unit_name = "meters"
        elif map_sr.factoryCode == 4326: # Geographic WGS84 (Lat/Lon)
            hackensack_center_x = -74.0434 # Longitude
            hackensack_center_y = 40.8859  # Latitude
            unit_name = "degrees"
        else:
            # Fallback for unexpected SR - try to use a default or log error
            arcpy.AddWarning(f"⚠️ Unexpected map coordinate system ({map_sr.name}, WKID: {map_sr.factoryCode}). Using default Hackensack coords in Web Mercator (3857) as a fallback for extent calculation.")
            hackensack_center_x = -8240000 # Fallback to Web Mercator Hackensack
            hackensack_center_y = 4850000
            unit_name = "meters"

        arcpy.AddMessage(f"📍 Using Hackensack center for extent: {hackensack_center_x}, {hackensack_center_y} ({unit_name})")
        
        if incident_count == 0:
            # No incidents - show Hackensack city area
            if unit_name == "feet":
                buffer_size = 8000  # 8000 feet = ~1.5 miles
            elif unit_name == "meters":
                buffer_size = 2500  # 2500 meters = ~1.5 miles
            else:  # degrees (approximate)
                buffer_size = 0.015 # ~1 mile in degrees
            
            new_extent = arcpy.Extent(
                hackensack_center_x - buffer_size,
                hackensack_center_y - buffer_size,
                hackensack_center_x + buffer_size,
                hackensack_center_y + buffer_size
            )
            
            arcpy.AddMessage("📍 No incidents - focused on Hackensack city area")
            
        else:
            # Get actual incident extent (ArcPy handles projection automatically when describing layer extent)
            incident_extent = arcpy.Describe(target_layer).extent
            
            # Log incident extent for debugging
            arcpy.AddMessage(f"📊 Incident extent: {incident_extent.XMin:.0f}, {incident_extent.YMin:.0f} to {incident_extent.XMax:.0f}, {incident_extent.YMax:.0f}")
            
            if incident_count == 1:
                # Single incident - tight zoom around incident
                center_x = (incident_extent.XMin + incident_extent.XMax) / 2
                center_y = (incident_extent.YMin + incident_extent.YMax) / 2
                
                if unit_name == "feet":
                    buffer_size = 4000  # 4000 feet = ~0.75 miles
                elif unit_name == "meters":
                    buffer_size = 1200  # 1200 meters = ~0.75 miles
                else:  # degrees
                    buffer_size = 0.008  # ~0.5 miles in degrees
                
                new_extent = arcpy.Extent(
                    center_x - buffer_size,
                    center_y - buffer_size,
                    center_x + buffer_size,
                    center_y + buffer_size
                )
                
                arcpy.AddMessage(f"📍 Single incident: 0.75-mile focused view")
                
            elif incident_count <= 5:
                # Few incidents - zoom to include all with minimal buffer
                if unit_name == "feet":
                    min_buffer = 3000  # Min 3000 ft
                    buffer_factor = 0.3
                elif unit_name == "meters":
                    min_buffer = 900  # Min 900 meters
                    buffer_factor = 0.3
                else:  # degrees
                    min_buffer = 0.005  # Min buffer in degrees
                    buffer_factor = 0.3
                
                width_buffer = max(incident_extent.width * buffer_factor, min_buffer)
                height_buffer = max(incident_extent.height * buffer_factor, min_buffer)
                
                new_extent = arcpy.Extent(
                    incident_extent.XMin - width_buffer,
                    incident_extent.YMin - height_buffer,
                    incident_extent.XMax + width_buffer,
                    incident_extent.YMax + height_buffer
                )
                
                arcpy.AddMessage(f"📍 Few incidents ({incident_count}): Tight group view")
                
            else:
                # Many incidents - show all with modest buffer
                if unit_name == "feet":
                    min_buffer = 2000  # Min 2000 ft
                    buffer_factor = 0.2
                elif unit_name == "meters":
                    min_buffer = 600  # Min 600 meters
                    buffer_factor = 0.2
                else:  # degrees
                    min_buffer = 0.003  # Min buffer in degrees
                    buffer_factor = 0.2
                
                width_buffer = max(incident_extent.width * buffer_factor, min_buffer)
                height_buffer = max(incident_extent.height * buffer_factor, min_buffer)
                
                new_extent = arcpy.Extent(
                    incident_extent.XMin - width_buffer,
                    incident_extent.YMin - height_buffer,
                    incident_extent.XMax + width_buffer,
                    incident_extent.YMax + height_buffer
                )
                
                arcpy.AddMessage(f"📍 Multiple incidents ({incident_count}): Optimized cluster view")
        
        # Apply coordinate system-specific constraints
        if unit_name == "feet":
            max_size_unit = 15000   # Max 15000 feet (~2.8 miles)
            min_size_unit = 6000    # Min 6000 feet (~1.1 miles)
        elif unit_name == "meters":
            max_size_unit = 4500    # Max 4500 meters (~2.8 miles)
            min_size_unit = 1800    # Min 1800 meters (~1.1 miles)
        else:  # degrees
            max_size_unit = 0.025   # Max ~1.7 miles
            min_size_unit = 0.01    # Min ~0.7 miles
        
        # Apply maximum constraints
        if new_extent.width > max_size_unit:
            center_x = (new_extent.XMin + new_extent.XMax) / 2
            new_extent = arcpy.Extent(
                center_x - max_size_unit/2,
                new_extent.YMin,
                center_x + max_size_unit/2,
                new_extent.YMax
            )
            arcpy.AddMessage("📏 Width constrained to Hackensack area")
        
        if new_extent.height > max_size_unit:
            center_y = (new_extent.YMin + new_extent.YMax) / 2
            new_extent = arcpy.Extent(
                new_extent.XMin,
                center_y - max_size_unit/2,
                new_extent.XMax,
                center_y + max_size_unit/2
            )
            arcpy.AddMessage("📏 Height constrained to Hackensack area")
        
        # Apply minimum constraints (for symbology visibility)
        if new_extent.width < min_size_unit:
            center_x = (new_extent.XMin + new_extent.XMax) / 2
            new_extent = arcpy.Extent(
                center_x - min_size_unit/2,
                new_extent.YMin,
                center_x + min_size_unit/2,
                new_extent.YMax
            )
            arcpy.AddMessage("📏 Width expanded for symbology visibility")
        
        if new_extent.height < min_size_unit:
            center_y = (new_extent.YMin + new_extent.YMax) / 2
            new_extent = arcpy.Extent(
                new_extent.XMin,
                center_y - min_size_unit/2,
                new_extent.XMax,
                center_y + min_size_unit/2
            )
            arcpy.AddMessage("📏 Height expanded for symbology visibility")
        
        # Apply the calculated extent
        map_frame.camera.setExtent(new_extent)
        
        # Log final extent details with coordinate system awareness
        if unit_name == "feet":
            width_miles = new_extent.width / 5280
            height_miles = new_extent.height / 5280
            arcpy.AddMessage(f"✅ Final extent: {width_miles:.1f} x {height_miles:.1f} miles")
        elif unit_name == "meters":
            width_miles = new_extent.width / 1609.34 # meters to miles
            height_miles = new_extent.height / 1609.34
            arcpy.AddMessage(f"✅ Final extent: {width_miles:.1f} x {height_miles:.1f} miles (approx)")
        else:  # degrees
            # Approximate conversion (1 degree ≈ 69 miles at this latitude)
            width_miles = new_extent.width * 69
            height_miles = new_extent.height * 69
            arcpy.AddMessage(f"✅ Final extent: {width_miles:.1f} x {height_miles:.1f} miles (approximate)")
        
        arcpy.AddMessage(f"📊 Optimized for {incident_count} incidents in Hackensack")
        arcpy.AddMessage(f"🎯 Coordinate system: {map_sr.name}")
        
        return True
        
    except Exception as e:
        arcpy.AddError(f"❌ Enhanced extent calculation failed: {e}")
        import traceback
        arcpy.AddError(f"Stack trace: {traceback.format_exc()}")
        return False

def parse_date_string(date_str):
    """Parse date string to date object"""
    try:
        if isinstance(date_str, str):
            return datetime.strptime(date_str, "%Y_%m_%d").date()
        elif isinstance(date_str, date):
            return date_str
        elif isinstance(date_str, datetime):
            return date_str.date()
        else:
            return date.today()
    except:
        return date.today()

def apply_enhanced_crime_symbology(target_layer, crime_type):
    """
    Apply enhanced symbology with forced visibility for all crime types
    """
    try:
        # Force layer to be completely visible
        target_layer.visible = True
        target_layer.transparency = 0
        
        # Remove any scale dependencies that might hide symbols
        try:
            target_layer.minThreshold = 0
            target_layer.maxThreshold = 0
            arcpy.AddMessage("✅ Removed scale dependencies")
        except:
            pass
        
        # Crime-specific symbology settings (RGBA)
        symbology_config = {
            "MV Theft": {
                "color": [255, 255, 0, 255],  # Yellow (R, G, B, A)
                "size": 15,
                "symbol_type": "esriSMSCircle" # Generic symbol type as example
            },
            "Burglary - Auto": {
                "color": [255, 165, 0, 255],  # Orange
                "size": 12,
                "symbol_type": "esriSMSDiamond"
            },
            "Burglary - Comm & Res": {
                "color": [255, 0, 0, 255],    # Red
                "size": 12,
                "symbol_type": "esriSMSSquare"
            },
            "Robbery": {
                "color": [0, 0, 0, 255],      # Black
                "size": 18,
                "symbol_type": "esriSMSCross"
            },
            "Sexual Offenses": {
                "color": [128, 0, 128, 255],  # Purple
                "size": 20,  # Extra large
                "symbol_type": "esriSMSTriangle"
            }
        }
        
        config = symbology_config.get(crime_type, {
            "color": [255, 0, 0, 255],  # Default red
            "size": 15,
            "symbol_type": "esriSMSCircle"
        })
        
        # Apply symbology if layer supports it and is a feature layer
        if target_layer.isFeatureLayer:
            sym_renderer = target_layer.symbology.renderer
            
            # Assuming a SimpleRenderer for direct symbol modification
            if hasattr(sym_renderer, 'symbol'):
                symbol = sym_renderer.symbol
                
                # --- FIX FOR arcpy.Color AttributeError ---
                # Instead of arcpy.Color, directly set RGBA values as a dictionary
                # The 'color' property of an ArcGIS Pro symbol's part generally expects a list of [R, G, B, A]
                # or a dictionary/object that can be interpreted as such.
                # Direct assignment of the RGBA list from config['color'] should work.
                
                # Make sure the color property exists on the symbol or its parts
                if hasattr(symbol, 'color'): # Common for simple marker symbols
                    symbol.color = config["color"]
                    arcpy.AddMessage(f"✅ Applied color {config['color']} for {crime_type} via symbol.color")
                elif hasattr(symbol, 'symbolLayers') and symbol.symbolLayers: # For CIMSymbol (more complex symbols)
                    # This assumes a CIMVectorMarker with a solid fill symbol layer
                    # This is a more robust way to set color for modern symbology
                    for sym_layer in symbol.symbolLayers:
                        if hasattr(sym_layer, 'color'):
                            sym_layer.color = config["color"]
                            arcpy.AddMessage(f"✅ Applied color {config['color']} for {crime_type} via symbolLayer.color")
                            break # Assume first symbol layer carries the color
                else:
                    arcpy.AddWarning(f"⚠️ Could not set color for {crime_type} via direct symbol.color or symbolLayers. No suitable property found.")

                # Set size
                if hasattr(symbol, 'size'):
                    symbol.size = config["size"]
                    arcpy.AddMessage(f"✅ Set symbol size to {config['size']} for {crime_type}")
                
                # Apply the modified symbology back to layer
                target_layer.symbology = sym_renderer # Important step to apply changes
                arcpy.AddMessage(f"✅ Enhanced symbology applied to {crime_type}")
                arcpy.AddMessage(f"   Size: {config['size']}, Color: {config['color']}")
            else:
                arcpy.AddWarning(f"⚠️ Layer {crime_type} renderer does not have a 'symbol' property to modify directly for enhanced symbology.")
        else:
            arcpy.AddWarning(f"⚠️ Layer {crime_type} is not a feature layer (e.g., it might be a Group Layer or Raster Layer), skipping symbology modification.")

        # SPECIAL HANDLING FOR SEXUAL OFFENSES - ensuring visibility
        if crime_type == "Sexual Offenses":
            arcpy.AddMessage(f"🚨 APPLYING SEXUAL OFFENSES ENHANCED VISIBILITY (Visibility attempts)")
            # Force visibility multiple times if needed for complex rendering
            for i in range(3):
                target_layer.visible = True
                target_layer.transparency = 0
                arcpy.AddMessage(f"   Visibility attempt {i + 1}")
        
        # Force refresh by toggling visibility - might help render changes
        target_layer.visible = False
        target_layer.visible = True
        
        # Log current state
        arcpy.AddMessage(f"🔍 Final Layer State:")
        arcpy.AddMessage(f"   Visible: {target_layer.visible}")
        arcpy.AddMessage(f"   Transparency: {target_layer.transparency}")
        
        return True
        
    except Exception as e:
        arcpy.AddError(f"❌ Enhanced symbology failed for {crime_type}: {e}")
        import traceback
        arcpy.AddError(f"Stack trace: {traceback.format_exc()}")
        return False

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
                if hasattr(lyr, 'definitionQuery'):
                    lyr.definitionQuery = original_states[lyr.name].get('definitionQuery', "")
        arcpy.AddMessage("✅ Restored original layer states")
    except Exception as e:
        arcpy.AddWarning(f"⚠️ Error restoring layer states: {e}")

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
            if "legend" in elm.name.lower() or "mainlegend" in elm.name.lower():
                legend = elm
                break
                
        if not legend:
            arcpy.AddWarning("⚠️ Legend element not found")
            # List available elements for debugging
            available_elements = [elm.name for elm in layout.listElements("LEGEND_ELEMENT")]
            arcpy.AddMessage(f"Available legend elements: {available_elements}")
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
            # Need to compare the actual layer associated with the legend item
            if hasattr(item, 'layer') and item.layer is not None and item.layer.name == target_layer.name:
                item.visible = True
                shown_count += 1
                arcpy.AddMessage(f"✅ Showing in legend: {item.name}")
            elif item.name == target_layer.name: # Fallback if item.layer isn't direct match
                 item.visible = True
                 shown_count += 1
                 arcpy.AddMessage(f"✅ Showing in legend (by name fallback): {item.name}")
        
        arcpy.AddMessage(f"🎯 Legend updated: {shown_count} items shown (7-Day only)")
        
    except Exception as e:
        arcpy.AddWarning(f"❌ Legend update error: {str(e)}")

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

def export_map_to_png_fixed(layout, crime_type, output_folder, filename_prefix):
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
        
        arcpy.AddMessage(f"🖼️ Exporting map to: {export_path}")
        
        try:
            # Export with appropriate resolution and without world_file if not needed
            # Set a high resolution for better quality
            layout.exportToPNG(export_path, resolution=300)
            arcpy.AddMessage("✅ Map exported successfully")
            
        except Exception as e:
            arcpy.AddError(f"❌ Map export failed during arcpy.exportToPNG: {str(e)}")
            return False
        
        # Verify export was successful
        if os.path.exists(export_path):
            file_size = os.path.getsize(export_path)
            arcpy.AddMessage(f"✅ Map export verified: {export_path} ({file_size:,} bytes)")
            return True
        else:
            arcpy.AddError(f"❌ Export file was not created: {export_path}")
            return False
        
    except Exception as e:
        arcpy.AddError(f"❌ Export failed: {str(e)}")
        logging.error(f"Map export failed for {crime_type}: {e}", exc_info=True)
        return False

def export_maps(crime_type, output_folder, args):
    """
    Export crime maps showing ONLY 7-Day incidents using Excel-based periods.
    Creates placeholder images for crime types with 0 7-day incidents.
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
            
        logging.info(f"🗺️ Starting map export for: {crime_type}")
        
        # Get date from args
        try:
            date_str = args[6] if len(args) > 6 else date.today().strftime("%Y_%m_%d") # Fallback to today's date string
            target_date = parse_date_string(date_str)
        except (IndexError, TypeError, ValueError) as e:
            logging.warning(f"⚠️ Could not parse date from arguments ({e}). Falling back to today's date.")
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
        layouts = aprx.listLayouts()
        if not layouts:
            arcpy.AddError("❌ No layouts found in project")
            available_layouts = [layout.name for layout in aprx.listLayouts()]
            arcpy.AddError(f"Available layouts: {available_layouts}")
            return False
            
        # Try to find specific layout first, then use first available
        layout = None
        for l in layouts:
            if "Crime Report" in l.name or "Legend" in l.name:
                layout = l
                break
        
        if not layout:
            layout = layouts[0]  # Use first layout
            
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
                'transparency': lyr.transparency,
                'definitionQuery': lyr.definitionQuery if hasattr(lyr, 'definitionQuery') else ""
            }

        # Hide all layers initially
        layer_count = 0
        for lyr in map_obj.listLayers():
            lyr.visible = False
            layer_count += 1
        arcpy.AddMessage(f"🔄 Hidden {layer_count} layers initially")

        # Show base layers (ensure these layers exist in your APRX and are visible/correctly symbolized)
        base_layers_to_enable = [
            "City Boundaries",
            "OpenStreetMap Light Gray Canvas Reference", # This is a common service layer
            "Light Gray Canvas (for Export)",            # Another common service layer
            "World Light Gray Canvas Base",              # Generic name for some base maps
            "OpenStreetMap",                             # Standard OpenStreetMap
            "Streets"                                    # Common name for a streets base map
        ]
        
        base_layers_enabled_count = 0
        for lyr in map_obj.listLayers():
            # Check if any part of the base layer name is in the layer's name
            if any(base_name.lower() in lyr.name.lower() for base_name in base_layers_to_enable):
                lyr.visible = True
                lyr.transparency = 0
                base_layers_enabled_count += 1
                arcpy.AddMessage(f"✅ Enabled base layer: {lyr.name}")
        
        if base_layers_enabled_count == 0:
            arcpy.AddWarning("⚠️ No expected base layers were found or enabled. Map export might be blank.")
            arcpy.AddMessage(f"DEBUG: Available layers in map_obj: {[lyr.name for lyr in map_obj.listLayers()]}")
        else:
            arcpy.AddMessage(f"✅ Enabled {base_layers_enabled_count} base layers")


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
            # List available layers for debugging
            available_layers = [lyr.name for lyr in map_obj.listLayers()]
            arcpy.AddMessage(f"Available layers in map: {available_layers}")
            
            # Create placeholder and return
            export_filename = f"{filename_prefix}_Map.png"
            export_path = os.path.join(crime_output_folder, export_filename)
            success = create_placeholder_image(crime_type, export_path)
            
            # Restore original layer states
            restore_layer_states(map_obj, original_states)
            return success
        
        # Show only the 7-Day layer with enhanced visibility
        target_layer.visible = True
        target_layer.transparency = 0  # Full opacity for single layer
        
        # Apply enhanced symbology (CRITICAL FIX)
        apply_enhanced_crime_symbology(target_layer, crime_type)
        
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
                    
                    # If no features, create placeholder instead of map
                    if feature_count == 0:
                        arcpy.AddMessage(f"📋 No 7-day incidents for {crime_type}, creating placeholder")
                        export_filename = f"{filename_prefix}_Map.png"
                        export_path = os.path.join(crime_output_folder, export_filename)
                        success = create_placeholder_image(crime_type, export_path)
                        
                        # Restore original layer states
                        restore_layer_states(map_obj, original_states)
                        return success
                        
                except Exception as e:
                    arcpy.AddWarning(f"⚠️ Could not get feature count: {e}")
            else:
                arcpy.AddWarning(f"⚠️ Could not build SQL filter for {crime_type}")

        # Apply Hackensack-focused extent calculation
        calculate_hackensack_focused_extent(target_layer, map_frame)

        # Update legend to show only 7-Day layer
        update_legend_visibility_7day(layout, map_obj, target_layer)

        # Clean up patch elements
        cleanup_patch_elements(layout)

        # --- DIAGNOSTIC: Log map frame state before export ---
        arcpy.AddMessage(f"DEBUG MAP EXPORT: Map Frame Name: {map_frame.name}")
        arcpy.AddMessage(f"DEBUG MAP EXPORT: Map Frame Map Name: {map_frame.map.name}")
        arcpy.AddMessage(f"DEBUG MAP EXPORT: Map Frame Map SR: {map_frame.map.spatialReference.name} (WKID: {map_frame.map.spatialReference.factoryCode})")
        arcpy.AddMessage(f"DEBUG MAP EXPORT: Active Layers before export: {[lyr.name for lyr in map_obj.listLayers() if lyr.visible]}")
        # ----------------------------------------------------

        # Export the map with FIXED function
        success = export_map_to_png_fixed(layout, crime_type, crime_output_folder, filename_prefix)
        
        # Restore original layer states
        restore_layer_states(map_obj, original_states)
        
        if success:
            arcpy.AddMessage(f"✅ Map export completed successfully for {crime_type}")
        
        return success
        
    except Exception as e:
        arcpy.AddError(f"❌ Critical error in export_maps for {crime_type}: {str(e)}")
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

# Legacy function support for compatibility
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
