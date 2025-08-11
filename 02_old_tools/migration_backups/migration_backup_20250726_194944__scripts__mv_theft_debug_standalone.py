# 🕒 2025-01-27-23-00-00
# SCRPA_Place_and_Time/mv_theft_debug_standalone
# Author: R. A. Carucci
# Purpose: Standalone debug script for MV Theft chart data issue

import arcpy
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def debug_mv_theft_data():
    """Debug why MV Theft chart shows empty despite having 3 incidents"""
    
    try:
        from config import APR_PATH, get_sql_pattern_for_crime, get_7day_period_dates, CRIME_SQL_PATTERNS
        
        print("🔍 MV THEFT CHART DEBUG")
        print("=" * 50)
        
        # Get the correct 7-day period for 2025-06-24
        target_date = datetime.strptime("2025_06_24", "%Y_%m_%d").date()
        start_date, end_date = get_7day_period_dates(target_date)
        
        print(f"Target Date: {target_date}")
        print(f"7-Day Period: {start_date} to {end_date}")
        
        # Check current SQL pattern
        current_pattern = CRIME_SQL_PATTERNS.get("MV Theft", "NOT FOUND")
        print(f"Current SQL Pattern: '{current_pattern}'")
        
        # Load ArcGIS Pro project
        aprx = arcpy.mp.ArcGISProject(APR_PATH)
        maps = aprx.listMaps()
        map_obj = maps[0]
        
        # Find MV Theft 7-Day layer
        mv_theft_layer = None
        for lyr in map_obj.listLayers():
            if "MV Theft 7-Day" in lyr.name:
                mv_theft_layer = lyr
                break
        
        if not mv_theft_layer:
            print("❌ MV Theft 7-Day layer not found!")
            print("Available layers:")
            for lyr in map_obj.listLayers():
                print(f"  - {lyr.name}")
            return False
        
        print(f"✅ Found layer: {mv_theft_layer.name}")
        
        # Test different SQL patterns
        test_patterns = [
            "AUTO THEFT",
            "MOTOR VEHICLE THEFT", 
            "VEHICLE THEFT",
            "MV THEFT",
            "THEFT AUTO",
            "THEFT MOTOR VEHICLE",
            "MOTOR VEHICLE",
            "AUTO"
        ]
        
        print(f"\n🧪 TESTING SQL PATTERNS:")
        print("-" * 30)
        
        original_query = mv_theft_layer.definitionQuery
        
        for pattern in test_patterns:
            try:
                # Build test SQL
                crime_condition = f"calltype LIKE '%{pattern}%'"
                start_timestamp = f"{start_date.strftime('%Y-%m-%d')} 00:00:00.000"
                end_timestamp = f"{end_date.strftime('%Y-%m-%d')} 23:59:59.999"
                
                test_sql = f"{crime_condition} AND disposition LIKE '%See Report%' AND calldate >= timestamp '{start_timestamp}' AND calldate <= timestamp '{end_timestamp}'"
                
                # Apply test filter
                mv_theft_layer.definitionQuery = test_sql
                
                # Get count
                feature_count = int(arcpy.GetCount_management(mv_theft_layer).getOutput(0))
                
                status = "✅ MATCH!" if feature_count > 0 else "❌ No data"
                print(f"{status} '{pattern}' → {feature_count} incidents")
                
                # If we found data, show details
                if feature_count > 0:
                    print(f"    Sample records:")
                    with arcpy.da.SearchCursor(mv_theft_layer, ["calldate", "calltype"]) as cursor:
                        for i, row in enumerate(cursor):
                            if i >= 3:  # Show max 3 samples
                                break
                            calldate = row[0]
                            calltype = row[1]
                            print(f"      {i+1}. {calldate} - {calltype}")
                
            except Exception as e:
                print(f"❌ Error testing '{pattern}': {e}")
        
        # Restore original query
        mv_theft_layer.definitionQuery = original_query
        del aprx
        
        print(f"\n💡 SOLUTION:")
        print(f"Update config.py with the pattern that shows '✅ MATCH!'")
        print(f"Example:")
        print(f"CRIME_SQL_PATTERNS = {{")
        print(f"    'MV Theft': 'CORRECT_PATTERN_HERE',")
        print(f"    # ... other patterns")
        print(f"}}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_mv_theft_data()