# 🕒 2025-06-21-23-35-00
# Police_Data_Analysis/exact_code_replacements
# Author: R. A. Carucci
# Purpose: Exact code replacements for database field detection and symbology forcing

# =============================================================================
# REPLACEMENT 1: incident_table_automation.py - Database Field Fix
# =============================================================================
# Replace the entire get_7day_incident_details function (starts around line 25)

def get_7day_incident_details(crime_type, target_date):
    """
    Extract detailed incident information for 7-day period - FIXED FIELDS
    
    Args:
        crime_type (str): Type of crime
        target_date (date): Target date for analysis
        
    Returns:
        list: List of incident dictionaries with details
    """
    incidents = []
    
    try:
        # Get Excel-based 7-day period dates
        start_date, end_date = get_7day_period_dates(target_date)
        
        if not start_date or not end_date:
            print(f"❌ Could not determine Excel 7-day period for {target_date}")
            return incidents
            
        print(f"📅 Getting incident details for period: {start_date} to {end_date}")
        
        # Load ArcGIS Pro project
        aprx = arcpy.mp.ArcGISProject(APR_PATH)
        maps = aprx.listMaps()
        
        if not maps:
            print(f"❌ No maps found in project")
            return incidents
            
        map_obj = maps[0]
        
        # Find the 7-Day layer
        layer_name = f"{crime_type} 7-Day"
        target_layer = None
        
        for lyr in map_obj.listLayers():
            if lyr.name == layer_name:
                target_layer = lyr
                break
        
        if not target_layer:
            print(f"❌ 7-Day layer not found: {layer_name}")
            return incidents
        
        # INSPECT AVAILABLE FIELDS FIRST
        print(f"🔍 Inspecting available fields in {layer_name}:")
        try:
            available_fields = [field.name for field in arcpy.ListFields(target_layer)]
            print(f"Available fields: {available_fields}")
        except Exception as e:
            print(f"⚠️ Could not list fields: {e}")
            available_fields = ['calldate', 'calltype', 'disposition']  # Fallback
        
        # DYNAMIC FIELD MAPPING - Find actual field names
        field_mapping = {
            'calldate': 'calldate',
            'location': None,
            'calltype': 'calltype', 
            'disposition': 'disposition'
        }
        
        # Find location field (try multiple variations)
        location_candidates = [
            'block', 'Block', 'BLOCK',
            'location', 'Location', 'LOCATION', 
            'address', 'Address', 'ADDRESS',
            'incident_location', 'Incident_Location',
            'loc', 'Loc', 'LOC',
            'addr', 'Addr', 'ADDR',
            'street', 'Street', 'STREET',
            'incident_address'
        ]
        
        for candidate in location_candidates:
            if candidate in available_fields:
                field_mapping['location'] = candidate
                print(f"✅ Found location field: {candidate}")
                break
        
        if not field_mapping['location']:
            print("⚠️ No text location field found, will use coordinates")
            field_mapping['location'] = 'SHAPE@XY'  # Use coordinate geometry
        
        # Verify other required fields exist
        for field_key, field_name in field_mapping.items():
            if field_name and field_name != 'SHAPE@XY':
                if field_name not in available_fields:
                    print(f"⚠️ Field '{field_name}' not found, looking for alternatives...")
                    
                    # Try variations for calltype
                    if field_key == 'calltype':
                        for alt in ['call_type', 'Call_Type', 'CALL_TYPE', 'type', 'Type']:
                            if alt in available_fields:
                                field_mapping['calltype'] = alt
                                print(f"✅ Using {alt} for calltype")
                                break
                    
                    # Try variations for disposition  
                    elif field_key == 'disposition':
                        for alt in ['disp', 'Disposition', 'DISPOSITION', 'status', 'Status']:
                            if alt in available_fields:
                                field_mapping['disposition'] = alt
                                print(f"✅ Using {alt} for disposition")
                                break
        
        print(f"📋 Final field mapping: {field_mapping}")
        
        # Build SQL filter for 7-day period
        from map_export import build_sql_filter_7day_excel
        filter_sql = build_sql_filter_7day_excel(crime_type, start_date, end_date)
        
        if filter_sql:
            # Apply the filter temporarily
            original_query = target_layer.definitionQuery
            target_layer.definitionQuery = filter_sql
            
            # Extract incident details using corrected field names
            try:
                # Build fields list for cursor
                fields_to_extract = [
                    field_mapping['calldate'],
                    field_mapping['location'], 
                    field_mapping['calltype'],
                    field_mapping['disposition']
                ]
                
                print(f"🔍 Extracting fields: {fields_to_extract}")
                
                with arcpy.da.SearchCursor(target_layer, fields_to_extract) as cursor:
                    for row in cursor:
                        try:
                            calldate = row[0]
                            location_data = row[1]
                            calltype = row[2] if row[2] else "Unknown"
                            disposition = row[3] if row[3] else "Unknown"
                            
                            # Handle different location data types
                            if field_mapping['location'] == 'SHAPE@XY':
                                # Convert coordinates to readable location
                                if location_data and len(location_data) >= 2:
                                    location_str = f"Coordinates: {location_data[1]:.4f}, {location_data[0]:.4f}"
                                else:
                                    location_str = "Location Unknown"
                            else:
                                # Use text location field
                                location_str = str(location_data) if location_data else "Location Unknown"
                            
                            if isinstance(calldate, datetime):
                                # Format the incident details
                                incident = {
                                    'block': location_str,
                                    'incident_date': calldate.strftime('%m/%d/%y'),
                                    'day_of_week': calldate.strftime('%A'),
                                    'time_period': get_time_period_from_hour(calldate.hour),
                                    'time_of_day': calldate.strftime('%H:%M'),
                                    'raw_datetime': calldate,
                                    'vehicle_description': '[MANUAL ENTRY]',
                                    'suspect_description': '[MANUAL ENTRY]',
                                    'narrative_summary': '[MANUAL ENTRY]'
                                }
                                
                                incidents.append(incident)
                                print(f"✅ Processed: {calldate.strftime('%m/%d %H:%M')} at {location_str[:50]}")
                                
                        except Exception as e:
                            print(f"  ⚠️ Error processing record: {e}")
                            continue
                
                # Restore original query
                target_layer.definitionQuery = original_query
                
                # Sort incidents by date/time
                incidents.sort(key=lambda x: x['raw_datetime'])
                
                print(f"✅ Extracted {len(incidents)} incident details for {crime_type}")
                
            except Exception as e:
                print(f"❌ Error extracting incident details: {e}")
                # Ensure query is restored
                try:
                    target_layer.definitionQuery = original_query
                except:
                    pass
                
        # Clean up project reference
        del aprx
        
    except Exception as e:
        print(f"❌ Error accessing incident data for {crime_type}: {e}")
    
    return incidents

# =============================================================================
# REPLACEMENT 2: map_export.py - Symbology Visibility Fix
# =============================================================================
# Replace the apply_symbology_enhanced function (starts around line 241)

def apply_symbology_enhanced(layer, layer_name):
    """
    Apply ENHANCED symbology with FORCED visibility for crime incident layers
    """
    try:
        if any(crime in layer_name for crime in ["Robbery", "MV Theft", "Burglary", "Sexual Offenses"]):
            arcpy.AddMessage(f"🎨 Applying FORCED VISIBLE symbology to {layer_name}")
            
            # STEP 1: Force basic visibility settings
            layer.visible = True
            layer.transparency = 0  # Full opacity
            
            # STEP 2: Get and modify symbology
            try:
                sym = layer.symbology
                arcpy.AddMessage(f"🔍 Current symbology type: {type(sym)}")
                
                # Check if we can modify the renderer
                if hasattr(sym, 'renderer') and sym.renderer:
                    arcpy.AddMessage(f"🔍 Renderer type: {type(sym.renderer)}")
                    
                    # Try to modify symbol properties
                    if hasattr(sym.renderer, 'symbol') and sym.renderer.symbol:
                        try:
                            # FORCE large, bright red symbols for maximum visibility
                            arcpy.AddMessage(f"🎨 Setting symbol properties for {layer_name}")
                            
                            # Set size (make it large)
                            if hasattr(sym.renderer.symbol, 'size'):
                                sym.renderer.symbol.size = 15  # Large size
                                arcpy.AddMessage(f"✅ Set size to 15 for {layer_name}")
                            
                            # Set color (bright red for visibility)
                            if hasattr(sym.renderer.symbol, 'color'):
                                # Try RGB format
                                try:
                                    sym.renderer.symbol.color = {'RGB': [255, 0, 0, 100]}
                                    arcpy.AddMessage(f"✅ Set RGB color for {layer_name}")
                                except:
                                    try:
                                        # Try alternative color format
                                        sym.renderer.symbol.color = [255, 0, 0, 255]  # RGBA
                                        arcpy.AddMessage(f"✅ Set RGBA color for {layer_name}")
                                    except:
                                        arcpy.AddMessage(f"⚠️ Could not set color for {layer_name}")
                            
                            # Apply the modified symbology
                            layer.symbology = sym
                            arcpy.AddMessage(f"✅ Applied modified symbology to {layer_name}")
                            
                        except Exception as e:
                            arcpy.AddMessage(f"⚠️ Symbol modification failed for {layer_name}: {e}")
                    
                    else:
                        arcpy.AddMessage(f"⚠️ No symbol object found for {layer_name}")
                
                else:
                    arcpy.AddMessage(f"⚠️ No renderer found for {layer_name}")
                
            except Exception as e:
                arcpy.AddMessage(f"⚠️ Symbology access failed for {layer_name}: {e}")
            
            # STEP 3: Alternative method - Apply from symbology file
            if SYM_LAYER_PATH and os.path.exists(SYM_LAYER_PATH):
                try:
                    arcpy.AddMessage(f"🎨 Trying symbology file for {layer_name}")
                    sym_layer_file = arcpy.mp.LayerFile(SYM_LAYER_PATH)
                    sym_layers = sym_layer_file.listLayers()
                    
                    if sym_layers:
                        sym_layer = sym_layers[0]
                        arcpy.ApplySymbologyFromLayer_management(layer, sym_layer)
                        arcpy.AddMessage(f"✅ Applied file symbology to {layer_name}")
                        
                        # Still force size and visibility
                        layer.visible = True
                        layer.transparency = 0
                        
                except Exception as e:
                    arcpy.AddMessage(f"⚠️ Symbology file application failed: {e}")
            
            # STEP 4: Force layer refresh and extent check
            try:
                # Check if layer has features
                feature_count = int(arcpy.GetCount_management(layer).getOutput(0))
                arcpy.AddMessage(f"🔍 Layer {layer_name} has {feature_count} features")
                
                if feature_count > 0:
                    # Get layer extent
                    desc = arcpy.Describe(layer)
                    if hasattr(desc, 'extent'):
                        extent = desc.extent
                        arcpy.AddMessage(f"📍 Layer extent: {extent.XMin:.2f}, {extent.YMin:.2f} to {extent.XMax:.2f}, {extent.YMax:.2f}")
                        
                        # Check if extent is valid (not empty)
                        if extent.XMin != extent.XMax and extent.YMin != extent.YMax:
                            arcpy.AddMessage(f"✅ Layer {layer_name} has valid extent")
                        else:
                            arcpy.AddMessage(f"⚠️ Layer {layer_name} has empty extent")
                    
                    # Final visibility confirmation
                    arcpy.AddMessage(f"🎯 Final status for {layer_name}: Visible={layer.visible}, Transparency={layer.transparency}")
                    
                else:
                    arcpy.AddMessage(f"⚠️ Layer {layer_name} has no features to display")
                
            except Exception as e:
                arcpy.AddMessage(f"⚠️ Layer inspection failed for {layer_name}: {e}")
            
            arcpy.AddMessage(f"✅ Symbology enhancement completed for {layer_name}")
            
        else:
            arcpy.AddMessage(f"💡 Skipping symbology for non-crime layer: {layer_name}")
            
    except Exception as e:
        arcpy.AddError(f"❌ Critical symbology error on {layer_name}: {str(e)}")
        arcpy.AddMessage(f"💡 Continuing with default symbology for {layer_name}")

# =============================================================================
# REPLACEMENT 3: Quick Test Function
# =============================================================================
# Add this to the end of incident_table_automation.py for quick testing

def test_field_detection():
    """Quick test function to check field detection"""
    try:
        from datetime import date
        print("🧪 TESTING FIELD DETECTION")
        print("=" * 40)
        
        # Test with MV Theft (has 2 incidents)
        incidents = get_7day_incident_details("MV Theft", date(2025, 6, 10))
        
        if len(incidents) > 0:
            print(f"✅ SUCCESS: Found {len(incidents)} incidents")
            for i, incident in enumerate(incidents[:2]):  # Show first 2
                print(f"  Incident {i+1}:")
                print(f"    Date: {incident['incident_date']}")
                print(f"    Time: {incident['time_of_day']}")
                print(f"    Location: {incident['block'][:60]}")
        else:
            print("❌ No incidents found - check field mapping")
        
        return len(incidents) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_field_detection()

# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================

"""
STEP 1: Replace incident_table_automation.py function
- Open: incident_table_automation.py
- Find: def get_7day_incident_details (around line 25)
- Replace: Entire function with the version above

STEP 2: Replace map_export.py function  
- Open: map_export.py
- Find: def apply_symbology_enhanced (around line 241)
- Replace: Entire function with the version above

STEP 3: Test field detection
- Run: python incident_table_automation.py
- Should show: Available fields and successful extraction

STEP 4: Test full system
- Run: python main.py true true true 30 true 2025_06_10
- Check: No field errors, visible map symbols

EXPECTED RESULTS:
✅ Incident tables extract successfully (no 'block' field errors)
✅ Maps show large red symbols (15px, bright red)
✅ All crime types process without field-related failures
"""