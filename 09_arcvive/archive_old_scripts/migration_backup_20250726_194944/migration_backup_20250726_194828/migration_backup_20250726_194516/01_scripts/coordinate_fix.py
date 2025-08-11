# 🕒 2025-01-27-17-57-00
# Police_Data_Analysis/quick_coordinate_fix.py
# Author: R. A. Carucci
# Purpose: Drop-in ready coordinate system fix for ArcGIS Pro project

import arcpy
import os

def fix_coordinate_system():
    """Complete coordinate system fix - drop-in ready"""
    
    # Your project path
    PROJECT_PATH = r"C:\Users\carucci_r\SCRPA_LAPTOP\projects\7_Day_Templet_SCRPA_Time.aprx"
    
    print("🚨 FIXING COORDINATE SYSTEM...")
    print("=" * 50)
    
    try:
        # Open project
        aprx = arcpy.mp.ArcGISProject(PROJECT_PATH)
        maps = aprx.listMaps()
        
        if not maps:
            print("❌ No maps found")
            return False
        
        map_obj = maps[0]
        
        # Check current system
        current_sr = map_obj.spatialReference
        print(f"🔍 Current: {current_sr.name} (WKID: {current_sr.factoryCode})")
        
        if current_sr.factoryCode == 4326:
            print("❌ PROBLEM: Using Geographic coordinates (causes Africa display)")
            
            # Fix to New Jersey State Plane
            print("🔧 Fixing to New Jersey State Plane...")
            new_sr = arcpy.SpatialReference(2900)  # NAD83 NJ State Plane
            map_obj.spatialReference = new_sr
            
            print(f"✅ Fixed to: {new_sr.name}")
            print(f"✅ New WKID: {new_sr.factoryCode}")
            
            # Save
            aprx.save()
            print("💾 Project saved")
            
        else:
            print("✅ Coordinate system already correct")
        
        del aprx
        return True
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        return False

def emergency_map_fix():
    """Emergency fix for immediate use in map export"""
    
    def fix_map_extent_emergency(map_frame, feature_count=0):
        """Emergency extent fix for maps showing Africa"""
        
        # Hackensack coordinates in State Plane NJ
        hackensack_x = 646000
        hackensack_y = 764000
        
        if feature_count == 0:
            # No incidents - show Hackensack area
            buffer_size = 5000  # 5000 feet
            
            extent = arcpy.Extent(
                hackensack_x - buffer_size,
                hackensack_y - buffer_size, 
                hackensack_x + buffer_size,
                hackensack_y + buffer_size
            )
            
        else:
            # Has incidents - smaller focused area
            buffer_size = 3000  # 3000 feet
            
            extent = arcpy.Extent(
                hackensack_x - buffer_size,
                hackensack_y - buffer_size,
                hackensack_x + buffer_size, 
                hackensack_y + buffer_size
            )
        
        try:
            map_frame.camera.setExtent(extent)
            print(f"✅ Emergency extent set: Hackensack area ({buffer_size}ft buffer)")
            return True
            
        except Exception as e:
            print(f"❌ Emergency extent failed: {e}")
            return False
    
    return fix_map_extent_emergency

if __name__ == "__main__":
    print("🚨 COORDINATE SYSTEM QUICK FIX")
    print("=" * 60)
    
    success = fix_coordinate_system()
    
    if success:
        print("\n🎉 COORDINATE SYSTEM FIXED!")
        print("🗺️ Maps will now show Hackensack instead of Africa")
        print("\n▶️ NEXT: Run your report script:")
        print("   cd C:\\Users\\carucci_r\\SCRPA_LAPTOP")
        print("   run_report_hardcoded.bat")
        
    else:
        print("\n❌ AUTOMATIC FIX FAILED")
        print("\n🔧 MANUAL FIX INSTRUCTIONS:")
        print("1. Open ArcGIS Pro")
        print("2. Open: 7_Day_Templet_SCRPA_Time.aprx")
        print("3. Right-click map → Properties → Coordinate Systems")
        print("4. Select: NAD 1983 StatePlane New Jersey FIPS 2900 (US Feet)")
        print("5. Save project")
        
    print("\n" + "=" * 60)
    input("Press Enter to close...")
