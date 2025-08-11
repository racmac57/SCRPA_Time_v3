# 🕒 2025-01-27-21-30-00
# Police_Data_Analysis/chart_export_fixed
# Author: R. A. Carucci
# Purpose: Updated chart_export.py with fixed legend positioning and Excel integration - FULLY CORRECTED

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import glob
import arcpy
import os
import logging
import sys
from datetime import date, datetime, timedelta
from config import get_crime_type_folder, get_standardized_filename, get_7day_period_dates, get_excel_report_name, APR_PATH, get_sql_pattern_for_crime

print(" chart_export.py loaded successfully with Excel integration")

def export_chart(crime_type):
    """
    Export time-of-day chart with CORRECTED Excel naming, 7-day filtering, and UNIFORM legend positioning
    """
    
    # Get the current date for analysis
    report_date = date.today()
    
    # Get date from command line args if available
    try:
        if len(sys.argv) > 6:
            date_str = sys.argv[6]  # YYYY_MM_DD format
            report_date = datetime.strptime(date_str, "%Y_%m_%d").date()
            print(f" Using input date from args: {report_date}")
    except Exception as e:
        print(f" Using current date: {report_date} (error: {e})")
    
    # Get Excel report info
    report_name = get_excel_report_name(report_date)
    if report_name:
        print(f" Looking for report due on: {report_date}")
        print(f" Exact match found: {report_name}")
    
    target_date_str = report_date.strftime("%Y_%m_%d")
    
    # Get crime-specific output folder using Excel naming
    crime_output_folder = get_crime_type_folder(crime_type, target_date_str)
    os.makedirs(crime_output_folder, exist_ok=True)
    
    # Get standardized filename prefix
    filename_prefix = get_standardized_filename(crime_type)
    
    # Clean old charts
    for file in glob.glob(os.path.join(crime_output_folder, f"{filename_prefix}_*Chart*.png")):
        try:
            os.remove(file)
            print(f" Deleted old chart: {os.path.basename(file)}")
        except:
            pass

    print(f"\n Processing chart for {crime_type} using CORRECTED date: {report_date}")
    
    # Time periods and colors
    time_periods = {
        "00:00-03:59": "Early Morning",
        "04:00-07:59": "Morning", 
        "08:00-11:59": "Midday",
        "12:00-15:59": "Afternoon",
        "16:00-19:59": "Evening",
        "20:00-23:59": "Night"
    }
    
    period_colors = {
        "7-Day": "#D9F2D0",   # Light green
        "28-Day": "#E0404C",  # Red
        "YTD": "#96A0F9"      # Light blue
    }
    
    try:
        # Load ArcGIS Pro project
        aprx = arcpy.mp.ArcGISProject(APR_PATH)
        maps = aprx.listMaps()
        if not maps:
            print(f" No maps found in project")
            return False
            
        map_obj = maps[0]
        print(f" Connected to ArcGIS Pro project")
        
        # Get the corrected 7-day period dates from Excel
        start_date_7day, end_date_7day = get_7day_period_dates(report_date)
        print(f" CORRECTED 7-Day period: {start_date_7day} to {end_date_7day}")
        
        combined_data = {}
        
        # Define CORRECTED timestamp dates for each period
        timestamp_dates = {
            "7-Day": f"{start_date_7day.strftime('%Y-%m-%d')} 00:00:00.000",
            "28-Day": f"{(start_date_7day - timedelta(days=21)).strftime('%Y-%m-%d')} 00:00:00.000",  # Total 28 days
            "YTD": f"{start_date_7day.replace(month=1, day=1).strftime('%Y-%m-%d')} 00:00:00.000"
        }
        
        print(f" Using CORRECTED timestamp dates: {timestamp_dates}")
        
        for period in ["7-Day", "28-Day", "YTD"]:
            print(f"\n Processing {period} data...")
            
            period_data = {time_range: 0 for time_range in time_periods.keys()}
            
            # Find the layer for this period
            layer_name = f"{crime_type} {period}"
            target_layer = None
            
            for lyr in map_obj.listLayers():
                if lyr.name == layer_name:
                    target_layer = lyr
                    break
            
            if not target_layer:
                print(f" Layer not found: {layer_name}")
                combined_data[period] = period_data
                continue
                
            print(f" Found layer: {target_layer.name}")
            
            try:
                # Get SQL pattern for this crime type
                sql_pattern = get_sql_pattern_for_crime(crime_type)
                
                if isinstance(sql_pattern, list):
                    conditions = []
                    for p in sql_pattern:
                        conditions.append(f"calltype LIKE '%{p}%'")
                    crime_condition = f"({' OR '.join(conditions)})"
                else:
                    crime_condition = f"calltype LIKE '%{sql_pattern}%'"
                
                # Build SQL filter with CORRECTED date range
                timestamp = timestamp_dates[period]
                sql_filter = f"{crime_condition} And disposition LIKE '%See Report%' And calldate >= timestamp '{timestamp}'"
                
                # For 7-day, add end date to limit to exact window
                if period == "7-Day":
                    end_timestamp = f"{end_date_7day.strftime('%Y-%m-%d')} 23:59:59.999"
                    sql_filter += f" And calldate <= timestamp '{end_timestamp}'"
                    print(f" 7-Day SQL (with end date): {sql_filter}")
                else:
                    print(f" {period} SQL Filter: {sql_filter}")
                
                # Apply the filter temporarily
                original_query = target_layer.definitionQuery
                target_layer.definitionQuery = sql_filter
                
                # Get feature count
                feature_count = int(arcpy.GetCount_management(target_layer).getOutput(0))
                print(f" {period} features found: {feature_count}")
                
                if feature_count > 0:
                    # Extract real time data from calldate field
                    try:
                        with arcpy.da.SearchCursor(target_layer, ["calldate"]) as cursor:
                            records_processed = 0
                            for row in cursor:
                                try:
                                    calldate = row[0]
                                    
                                    if isinstance(calldate, datetime):
                                        hour = calldate.hour
                                    else:
                                        continue
                                    
                                    # Categorize by time period
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
                                    
                                    records_processed += 1
                                    
                                except Exception as e:
                                    print(f"  ️ Error processing record: {e}")
                                    continue
                            
                            print(f" Processed {records_processed} records with real time data")
                            
                    except Exception as e:
                        print(f" Error extracting time data: {e}")
                        if feature_count > 0:
                            period_data["12:00-15:59"] = feature_count  # Fallback
                
                # Restore original query
                target_layer.definitionQuery = original_query
                
                print(f" {period} time distribution: {period_data}")
                
            except Exception as e:
                print(f" Error processing {period}: {e}")
                continue
            
            combined_data[period] = period_data
        
        # Clean up project reference
        del aprx
        
    except Exception as e:
        print(f" Error accessing ArcGIS data for {crime_type}: {e}")
        
        # Use fallback data if ArcGIS access fails
        combined_data = {
            "7-Day": {time_range: 0 for time_range in time_periods.keys()},
            "28-Day": {time_range: 0 for time_range in time_periods.keys()},
            "YTD": {time_range: 0 for time_range in time_periods.keys()}
        }
    
    # Create the chart
    try:
        fig, ax = plt.subplots(figsize=(6.95, 4.63))
        
        # Prepare data for grouped bars
        time_ranges = list(time_periods.keys())
        time_labels = [f"{time_range}\n{time_periods[time_range]}" for time_range in time_ranges]
        
        # Set up bar positions
        x_positions = range(len(time_ranges))
        bar_width = 0.25
        
        # Plot grouped bars
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
            
            # Add value labels on bars (only for non-zero values)
            for bar, value in zip(bars, values):
                if value > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                           f'{int(value)}',
                           ha='center', va='bottom', 
                           fontsize=8, fontweight='bold')
        
        # Customize the chart
        ax.set_title(f"{crime_type} - Calls by Time of Day", 
                    fontsize=12, fontweight='bold', pad=15)
        ax.set_xlabel("Time of Day", fontsize=10, fontweight='bold')
        ax.set_ylabel("Count", fontsize=10, fontweight='bold')
        
        # Set x-axis
        ax.set_xticks(x_positions)
        ax.set_xticklabels(time_labels, fontsize=9, ha='center')
        
        # Set y-axis
        max_value = max([max(data.values()) for data in combined_data.values()])
        if max_value > 0:
            ax.set_ylim(0, max_value * 1.2)
        else:
            ax.set_ylim(0, 1)
        
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        
        # Configure legend - UNIFORM positioning to avoid data blocking
        ax.legend(title="Period", title_fontsize=9, fontsize=9, 
                 loc='upper left', bbox_to_anchor=(0.02, 0.98), framealpha=0.9)
        
        # Remove grid lines
        ax.grid(False)
        
        # Improve layout
        plt.tight_layout()
        
        # Save chart with standardized filename
        chart_path = os.path.join(crime_output_folder, f"{filename_prefix}_Chart.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f" Chart saved with UNIFORM legend positioning: {chart_path}")
        
        # Print final summary
        print(f"\n Final Chart Data for {crime_type}:")
        for period in ["7-Day", "28-Day", "YTD"]:
            total = sum(combined_data[period].values())
            print(f"  {period}: {total} incidents")
        print(f" CORRECTED 7-Day period analyzed: {start_date_7day} to {end_date_7day}")
        
        return True
        
    except Exception as e:
        print(f" Error creating chart for {crime_type}: {e}")
        import traceback
        traceback.print_exc()
        return False