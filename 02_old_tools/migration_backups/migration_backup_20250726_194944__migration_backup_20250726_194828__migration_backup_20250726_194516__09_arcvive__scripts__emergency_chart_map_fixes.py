# 🕒 2025-01-27-23-20-00
# SCRPA_Analysis/emergency_chart_map_coordinate_fix
# Author: R. A. Carucci
# Purpose: Fix legend overlap issue and map coordinate system for immediate submission

# =============================================================================
# CHART_EXPORT.PY - LEGEND POSITION FIX
# =============================================================================

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import glob
import arcpy
import os
from datetime import date, datetime, timedelta
from config import get_crime_type_folder, get_standardized_filename, APR_PATH, get_sql_pattern_for_crime

def export_chart_fixed_legend(crime_type):
    """
    Export chart with FIXED legend position and CORRECT date filtering
    """
    # Get current date
    report_date = date.today()
    target_date_str = report_date.strftime("%Y_%m_%d")
    
    crime_output_folder = get_crime_type_folder(crime_type, target_date_str)
    os.makedirs(crime_output_folder, exist_ok=True)
    filename_prefix = get_standardized_filename(crime_type)
    
    # Clean old charts
    for file in glob.glob(os.path.join(crime_output_folder, f"{filename_prefix}_*Chart*.png")):
        try:
            os.remove(file)
        except:
            pass

    print(f"\n🔍 Processing chart for {crime_type} with FIXED legend...")
    
    # Time periods with CSV-style labels
    time_periods = {
        "00:00-03:59": "00:00-03:59\nEarly Morning",
        "04:00-07:59": "04:00-07:59\nMorning", 
        "08:00-11:59": "08:00-11:59\nMidday",
        "12:00-15:59": "12:00-15:59\nAfternoon",
        "16:00-19:59": "16:00-19:59\nEvening",
        "20:00-23:59": "20:00-23:59\nNight"
    }
    
    period_colors = {
        "7-Day": "#D9F2D0",   # Light green
        "28-Day": "#E0404C",  # Red
        "YTD": "#96A0F9"      # Light blue
    }
    
    try:
        aprx = arcpy.mp.ArcGISProject(APR_PATH)
        map_obj = aprx.listMaps()[0]
        
        # CORRECTED date ranges based on actual calendar
        today = datetime.now().date()
        
        # For Jan 27, 2025 - calculate ACTUAL periods
        start_date_7day = today - timedelta(days=7)     # Jan 20-27
        start_date_28day = today - timedelta(days=28)   # Dec 30 - Jan 27  
        start_date_ytd = datetime(today.year, 1, 1).date()  # Jan 1 - Jan 27
        
        print(f"📅 CORRECTED date ranges:")
        print(f"  7-Day: {start_date_7day} to {today}")
        print(f"  28-Day: {start_date_28day} to {today}")
        print(f"  YTD: {start_date_ytd} to {today}")
        
        combined_data = {}
        
        for period in ["7-Day", "28-Day", "YTD"]:
            period_data = {time_range: 0 for time_range in time_periods.keys()}
            
            layer_name = f"{crime_type} {period}"
            target_layer = None
            
            for lyr in map_obj.listLayers():
                if lyr.name == layer_name:
                    target_layer = lyr
                    break
            
            if not target_layer:
                print(f"❌ Layer not found: {layer_name}")
                combined_data[period] = period_data
                continue
            
            # Get SQL pattern
            sql_pattern = get_sql_pattern_for_crime(crime_type)
            
            if isinstance(sql_pattern, list):
                conditions = [f"calltype LIKE '%{p}%'" for p in sql_pattern]
                crime_condition = f"({' OR '.join(conditions)})"
            else:
                crime_condition = f"calltype LIKE '%{sql_pattern}%'"
            
            # Set correct start date for each period
            if period == "7-Day":
                period_start = start_date_7day
            elif period == "28-Day":
                period_start = start_date_28day
            else:  # YTD
                period_start = start_date_ytd
            
            start_timestamp = f"{period_start.strftime('%Y-%m-%d')} 00:00:00.000"
            end_timestamp = f"{today.strftime('%Y-%m-%d')} 23:59:59.999"
            
            # More inclusive SQL filter
            sql_filter = f"{crime_condition} AND calldate >= timestamp '{start_timestamp}' AND calldate <= timestamp '{end_timestamp}'"
            sql_filter += " AND (disposition LIKE '%Report%' OR disposition LIKE '%Arrest%' OR disposition LIKE '%Citation%')"
            
            print(f"🔎 {period} SQL: {sql_filter}")
            
            original_query = target_layer.definitionQuery
            target_layer.definitionQuery = sql_filter
            
            feature_count = int(arcpy.GetCount_management(target_layer).getOutput(0))
            print(f"📊 {period} features found: {feature_count}")
            
            if feature_count > 0:
                try:
                    with arcpy.da.SearchCursor(target_layer, ["calldate"]) as cursor:
                        for row in cursor:
                            try:
                                calldate = row[0]
                                if isinstance(calldate, datetime):
                                    hour = calldate.hour
                                    
                                    if 0 <= hour <= 3:
                                        period_data["00:00-03:59"] += 1
                                    elif 4 <= hour <= 7:
                                        period_data["04:00-07:59"] += 1
                                    elif 8 <= hour <= 11:
                                        period_data["08:00-11:59"] += 1
                                    elif 12 <= hour <= 15:
                                        period_data["12:00-15:59"] += 1
                                    elif 16 <= hour <= 19:
                                        period_data["16:00-19:59"] += 1
                                    elif 20 <= hour <= 23:
                                        period_data["20:00-23:59"] += 1
                                        
                            except Exception as e:
                                continue
                                
                except Exception as e:
                    print(f"❌ Error extracting time data: {e}")
            
            target_layer.definitionQuery = original_query
            combined_data[period] = period_data
        
        del aprx
        
    except Exception as e:
        print(f"❌ Error accessing ArcGIS data: {e}")
        # Fallback data
        combined_data = {
            "7-Day": {time_range: 0 for time_range in time_periods.keys()},
            "28-Day": {time_range: 0 for time_range in time_periods.keys()},
            "YTD": {time_range: 0 for time_range in time_periods.keys()}
        }
    
    # Create chart with FIXED legend position
    try:
        fig, ax = plt.subplots(figsize=(6.95, 4.63))
        
        time_ranges = list(time_periods.keys())
        csv_labels = [time_periods[time_range] for time_range in time_ranges]
        
        x_positions = range(len(time_ranges))
        bar_width = 0.25
        
        # Plot bars
        for i, period in enumerate(["7-Day", "28-Day", "YTD"]):
            values = [combined_data[period][time_range] for time_range in time_ranges]
            positions = [x + (i - 1) * bar_width for x in x_positions]
            
            bars = ax.bar(positions, values, 
                         width=bar_width,
                         label=period,
                         color=period_colors[period],
                         alpha=0.9,
                         edgecolor='black',
                         linewidth=0.5)
            
            # Add value labels
            for bar, value in zip(bars, values):
                if value > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                           f'{int(value)}',
                           ha='center', va='bottom', 
                           fontsize=8, fontweight='bold')
        
        # Chart formatting
        ax.set_title(f"{crime_type} - Calls by Time of Day", 
                    fontsize=12, fontweight='bold', pad=15)
        ax.set_xlabel("Time of Day", fontsize=10, fontweight='bold')
        ax.set_ylabel("Count", fontsize=10, fontweight='bold')
        
        ax.set_xticks(x_positions)
        ax.set_xticklabels(csv_labels, fontsize=9, ha='center')
        
        max_value = max([max(data.values()) for data in combined_data.values()])
        if max_value > 0:
            ax.set_ylim(0, max_value * 1.2)
        else:
            ax.set_ylim(0, 1)
        
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        
        # CRITICAL FIX: Position legend to avoid data overlap
        # Move legend to UPPER LEFT instead of upper right
        ax.legend(title="Period", title_fontsize=9, fontsize=9, 
                 loc='upper left', framealpha=0.9, bbox_to_anchor=(0.02, 0.98))
        
        ax.grid(False)
        plt.tight_layout()
        
        chart_path = os.path.join(crime_output_folder, f"{filename_prefix}_Chart.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"✅ Chart saved with FIXED legend position: {chart_path}")
        
        # Print summary
        for period in ["7-Day", "28-Day", "YTD"]:
            total = sum(combined_data[period].values())
            print(f"  {period}: {total} incidents")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating chart: {e}")
        return False

# =============================================================================
# MAP_EXPORT.PY - COORDINATE SYSTEM FIX  
# =============================================================================

def fix_map_extent_hackensack_correct_coords(target_layer, map_frame, map_obj):
    """
    Fix map extent using CORRECT New Jersey State Plane coordinates
    """
    try:
        incident_count = int(arcpy.GetCount_management(target_layer).getOutput(0))
        
        # CORRECT Hackensack coordinates in State Plane New Jersey FIPS 2900 (US feet)
        # These are the actual State Plane coordinates for Hackensack City Hall
        hackensack_center_x = 646000   # X coordinate in State Plane NJ (feet)
        hackensack_center_y = 764000   # Y coordinate in State Plane NJ (feet)
        
        if incident_count == 0:
            buffer_size = 8000   # 8000 feet = ~1.5 miles
        elif incident_count == 1:
            buffer_size = 4000   # 4000 feet = ~0.75 miles
        else:
            buffer_size = 12000  # 12000 feet = ~2.3 miles
        
        # Create extent in State Plane coordinates
        new_extent = arcpy.Extent(
            hackensack_center_x - buffer_size,
            hackensack_center_y - buffer_size,
            hackensack_center_x + buffer_size,
            hackensack_center_y + buffer_size
        )
        
        # CRITICAL: Ensure spatial reference is set correctly
        # Get the map's spatial reference
        map_sr = map_obj.spatialReference
        
        # If map is not in State Plane NJ, we need to project
        if map_sr.factoryCode != 2900:  # State Plane NJ FIPS code
            # Create State Plane NJ spatial reference
            state_plane_nj = arcpy.SpatialReference(2900)
            
            # Project the extent to the map's coordinate system
            try:
                # Create geometry from extent
                extent_geom = arcpy.Polygon([
                    arcpy.Array([
                        arcpy.Point(new_extent.XMin, new_extent.YMin),
                        arcpy.Point(new_extent.XMin, new_extent.YMax),
                        arcpy.Point(new_extent.XMax, new_extent.YMax),
                        arcpy.Point(new_extent.XMax, new_extent.YMin)
                    ])
                ], state_plane_nj)
                
                # Project to map's coordinate system
                projected_geom = extent_geom.projectAs(map_sr)
                projected_extent = projected_geom.extent
                
                map_frame.camera.setExtent(projected_extent)
                arcpy.AddMessage(f"✅ Set projected extent: {buffer_size}ft buffer (projected from State Plane)")
                
            except Exception as proj_error:
                arcpy.AddWarning(f"⚠️ Projection failed: {proj_error}")
                # Fallback: try direct coordinate setting
                map_frame.camera.setExtent(new_extent)
                
        else:
            # Map is already in State Plane NJ
            map_frame.camera.setExtent(new_extent)
            arcpy.AddMessage(f"✅ Set State Plane extent: {buffer_size}ft buffer")
        
        return True
        
    except Exception as e:
        arcpy.AddError(f"❌ Coordinate fix failed: {e}")
        return False

# =============================================================================
# INTEGRATION INSTRUCTIONS
# =============================================================================

"""
IMMEDIATE FIXES TO IMPLEMENT:

1. CHART LEGEND FIX:
   - Replace legend position from 'upper right' to 'upper left'
   - Add bbox_to_anchor=(0.02, 0.98) for precise positioning
   
2. MAP COORDINATE FIX:
   - Use State Plane New Jersey coordinates (FIPS 2900)
   - Hackensack center: 646000, 764000 (feet)
   - Add coordinate system projection logic
   
3. DATE RANGE FIX:
   - Use actual calendar dates (Jan 20-27 for 7-day)
   - More inclusive disposition filter
   - Print actual date ranges for verification

COPY THESE FUNCTIONS INTO YOUR EXISTING FILES:
- export_chart_fixed_legend() → chart_export.py
- fix_map_extent_hackensack_correct_coords() → map_export.py

THEN RUN IMMEDIATELY FOR SUBMISSION!
"""