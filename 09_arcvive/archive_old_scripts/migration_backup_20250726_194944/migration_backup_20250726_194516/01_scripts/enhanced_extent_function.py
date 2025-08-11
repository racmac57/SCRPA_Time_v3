# 🕒 2025-01-27-23-15-00
# SCRPA_Place_and_Time/enhanced_extent_function.py
# Author: R. A. Carucci
# Purpose: Enhanced map extent calculation with coordinate system validation and projection handling

import arcpy

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
            arcpy.AddWarning(f"   Layer: {layer_sr.name}")
            arcpy.AddWarning(f"   Map: {map_sr.name}")
            arcpy.AddMessage("🔁 Proceeding with automatic projection handling...")
        
        # Hackensack, NJ coordinates - determine based on map coordinate system
        if map_sr.factoryCode == 2900:  # NAD83 / New Jersey (US Feet)
            # State Plane coordinates in feet
            hackensack_center_x = 646000
            hackensack_center_y = 764000
            unit_name = "feet"
        elif map_sr.factoryCode == 4326:  # Geographic WGS84
            # Lat/Lon coordinates
            hackensack_center_x = -74.0434  # Longitude
            hackensack_center_y = 40.8859   # Latitude
            unit_name = "degrees"
        else:
            # Try to use State Plane as default, project if needed
            arcpy.AddWarning(f"⚠️ Unexpected coordinate system: {map_sr.name}")
            hackensack_center_x = 646000
            hackensack_center_y = 764000
            unit_name = "feet"
        
        arcpy.AddMessage(f"📍 Using Hackensack center: {hackensack_center_x}, {hackensack_center_y} ({unit_name})")
        
        if incident_count == 0:
            # No incidents - show Hackensack city area
            if unit_name == "feet":
                buffer_size = 8000  # 8000 feet = ~1.5 miles
            else:  # degrees
                buffer_size = 0.015  # ~1 mile in degrees
            
            new_extent = arcpy.Extent(
                hackensack_center_x - buffer_size,
                hackensack_center_y - buffer_size,
                hackensack_center_x + buffer_size,
                hackensack_center_y + buffer_size
            )
            
            arcpy.AddMessage("📍 No incidents - focused on Hackensack city area")
            
        else:
            # Get actual incident extent (ArcPy handles projection automatically)
            incident_extent = arcpy.Describe(target_layer).extent
            
            # Log incident extent for debugging
            arcpy.AddMessage(f"📊 Incident extent: {incident_extent.XMin:.0f}, {incident_extent.YMin:.0f} to {incident_extent.XMax:.0f}, {incident_extent.YMax:.0f}")
            
            if incident_count == 1:
                # Single incident - tight zoom around incident
                center_x = (incident_extent.XMin + incident_extent.XMax) / 2
                center_y = (incident_extent.YMin + incident_extent.YMax) / 2
                
                if unit_name == "feet":
                    buffer_size = 4000  # 4000 feet = ~0.75 miles
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
            # Ensure extent is within reasonable Hackensack area (feet)
            max_width = 15000   # Max 15000 feet (~2.8 miles)
            max_height = 15000
            min_width = 6000    # Min 6000 feet (~1.1 miles)
            min_height = 6000
        else:  # degrees
            # Ensure extent is within reasonable Hackensack area (degrees)
            max_width = 0.025   # Max ~1.7 miles
            max_height = 0.025
            min_width = 0.01    # Min ~0.7 miles
            min_height = 0.01
        
        # Apply maximum constraints
        if new_extent.width > max_width:
            center_x = (new_extent.XMin + new_extent.XMax) / 2
            new_extent = arcpy.Extent(
                center_x - max_width/2,
                new_extent.YMin,
                center_x + max_width/2,
                new_extent.YMax
            )
            arcpy.AddMessage("📏 Width constrained to Hackensack area")
        
        if new_extent.height > max_height:
            center_y = (new_extent.YMin + new_extent.YMax) / 2
            new_extent = arcpy.Extent(
                new_extent.XMin,
                center_y - max_height/2,
                new_extent.XMax,
                center_y + max_height/2
            )
            arcpy.AddMessage("📏 Height constrained to Hackensack area")
        
        # Apply minimum constraints (for symbology visibility)
        if new_extent.width < min_width:
            center_x = (new_extent.XMin + new_extent.XMax) / 2
            new_extent = arcpy.Extent(
                center_x - min_width/2,
                new_extent.YMin,
                center_x + min_width/2,
                new_extent.YMax
            )
            arcpy.AddMessage("📏 Width expanded for symbology visibility")
        
        if new_extent.height < min_height:
            center_y = (new_extent.YMin + new_extent.YMax) / 2
            new_extent = arcpy.Extent(
                new_extent.XMin,
                center_y - min_height/2,
                new_extent.XMax,
                center_y + min_height/2
            )
            arcpy.AddMessage("📏 Height expanded for symbology visibility")
        
        # Apply the calculated extent
        map_frame.camera.setExtent(new_extent)
        
        # Log final extent details with coordinate system awareness
        if unit_name == "feet":
            width_miles = new_extent.width / 5280
            height_miles = new_extent.height / 5280
            arcpy.AddMessage(f"✅ Final extent: {width_miles:.1f} x {height_miles:.1f} miles")
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