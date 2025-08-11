# 🕒 2025-06-22-17-00-00
# Police_Data_Analysis/main_robbery_debug.py
# Author: R. A. Carucci
# Purpose: Focused Robbery map debugging with corrected function calls

import sys
import logging
import time
from datetime import datetime

# Import actual functions from your existing modules
from map_export import export_maps
from chart_export import export_chart
from incident_table_automation import export_incident_table_data_with_autofit, create_incident_table_placeholder
from config import get_sql_pattern_for_crime, get_crime_type_folder, get_7day_period_dates, APR_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CRIME_TYPES = [
    "Robbery"  # Single focus for debugging
]

def log_crime_sql_debug(crime_type, report_date):
    """Enhanced SQL debugging with layer extent checking"""
    try:
        import arcpy
        
        start_date, end_date = get_7day_period_dates(report_date)
        logging.info(f"📅 Date range: {start_date} to {end_date}")

        # Build SQL filter exactly like map_export.py does
        sql_pattern = get_sql_pattern_for_crime(crime_type)
        logging.info(f"🔍 SQL Pattern for {crime_type}: {sql_pattern}")
        
        if isinstance(sql_pattern, list):
            conditions = [f"calltype LIKE '%{p}%'" for p in sql_pattern]
            crime_condition = f"({' OR '.join(conditions)})"
        else:
            crime_condition = f"calltype LIKE '%{sql_pattern}%'"

        start_timestamp = f"{start_date.strftime('%Y-%m-%d')} 00:00:00.000"
        end_timestamp = f"{end_date.strftime('%Y-%m-%d')} 23:59:59.999"
        
        sql_filter = (
            f"{crime_condition} AND disposition LIKE '%See Report%' "
            f"AND calldate >= timestamp '{start_timestamp}' "
            f"AND calldate <= timestamp '{end_timestamp}'"
        )
        
        logging.info(f"🔎 COMPLETE SQL Filter:\n{sql_filter}")

        # Test against actual layer
        aprx = arcpy.mp.ArcGISProject(APR_PATH)
        map_obj = aprx.listMaps()[0]
        
        # Find Robbery 7-Day layer
        robbery_layer = None
        for lyr in map_obj.listLayers():
            if "Robbery" in lyr.name and "7-Day" in lyr.name:
                robbery_layer = lyr
                break
        
        if robbery_layer:
            logging.info(f"✅ Found layer: {robbery_layer.name}")
            
            # Check layer extent
            desc = arcpy.Describe(robbery_layer)
            logging.info(f"📐 Layer extent: {desc.extent}")
            
            # Apply filter and count
            original_query = robbery_layer.definitionQuery
            robbery_layer.definitionQuery = sql_filter
            
            try:
                count = int(arcpy.GetCount_management(robbery_layer).getOutput(0))
                logging.info(f"📊 Feature count after SQL filter: {count}")
                
                if count > 0:
                    logging.info(f"📍 Sample coordinates for {count} features:")
                    with arcpy.da.SearchCursor(robbery_layer, ["SHAPE@XY", "calldate", "calltype"]) as cursor:
                        for i, row in enumerate(cursor):
                            logging.info(f"  {i+1}. XY: {row[0]}, Date: {row[1]}, Type: {row[2]}")
                            if i >= 2:  # Show max 3 records
                                break
                else:
                    logging.warning("❌ ZERO FEATURES found with SQL filter!")
                    logging.info("🔍 Testing without date filter...")
                    
                    # Test without date filter
                    simple_filter = f"{crime_condition} AND disposition LIKE '%See Report%'"
                    robbery_layer.definitionQuery = simple_filter
                    simple_count = int(arcpy.GetCount_management(robbery_layer).getOutput(0))
                    logging.info(f"📊 Features without date filter: {simple_count}")
                    
            finally:
                # Always restore original query
                robbery_layer.definitionQuery = original_query
                
        else:
            logging.error("❌ Robbery 7-Day layer NOT FOUND in project!")
            logging.info("📋 Available layers:")
            for lyr in map_obj.listLayers():
                logging.info(f"  - {lyr.name}")
        
        del aprx

    except Exception as e:
        logging.error(f"❌ SQL debugging failed: {e}")
        import traceback
        traceback.print_exc()

def process_robbery_debug(crime_type, report_date, report_date_str):
    """Process Robbery with enhanced debugging"""
    start_time = time.time()
    logging.info(f"\n🚨 DEBUGGING: {crime_type}")
    logging.info("=" * 50)

    # Step 1: SQL Analysis
    log_crime_sql_debug(crime_type, report_date)
    
    # Step 2: Get proper output folder
    try:
        output_folder = get_crime_type_folder(crime_type, report_date_str)
        logging.info(f"📁 Output folder: {output_folder}")
    except Exception as e:
        logging.error(f"❌ Failed to get output folder: {e}")
        return

    # Step 3: Run map export with debugging
    logging.info("\n🗺️ Running map export...")
    try:
        success_map = export_maps(crime_type, output_folder, sys.argv)
        if success_map:
            logging.info("✅ Map export completed")
        else:
            logging.error("❌ Map export failed")
    except Exception as e:
        logging.error(f"❌ Map export crashed: {e}")
        import traceback
        traceback.print_exc()

    # Step 4: Run chart export
    logging.info("\n📊 Running chart export...")
    try:
        success_chart = export_chart(crime_type)
        if success_chart:
            logging.info("✅ Chart export completed")
        else:
            logging.error("❌ Chart export failed")
    except Exception as e:
        logging.error(f"❌ Chart export crashed: {e}")

    # Step 5: Run incident table export  
    logging.info("\n📋 Running incident table export...")
    try:
        success_table = export_incident_table_data_with_autofit(crime_type, report_date)
        if not success_table:
            logging.warning(f"⚠️ Creating placeholder for {crime_type}")
            placeholder_path = f"{output_folder}/{crime_type.replace(' ', '_')}_IncidentTable_Placeholder.png"
            create_incident_table_placeholder(crime_type, placeholder_path)
    except Exception as e:
        logging.error(f"❌ Incident table export crashed: {e}")

    duration = time.time() - start_time
    logging.info(f"\n⏱️ Robbery debugging completed in {duration:.2f} seconds")
    logging.info("=" * 50)

def main(report_date_str):
    try:
        report_date = datetime.strptime(report_date_str, "%Y_%m_%d").date()
    except Exception as e:
        logging.error(f"❌ Invalid date format. Use YYYY_MM_DD. Error: {e}")
        return

    logging.info(f"🚦 ROBBERY DEBUGGING SESSION - {report_date_str}")
    logging.info(f"🎯 Focus: Fix missing Robbery map icons")
    
    batch_start = time.time()

    # Process only Robbery
    for crime_type in CRIME_TYPES:
        process_robbery_debug(crime_type, report_date, report_date_str)

    total_time = time.time() - batch_start
    logging.info(f"\n🏁 Robbery debug session completed in {total_time:.2f} seconds")
    logging.info("📋 Check logs above for SQL filter and feature count results")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        logging.error("Usage: python main_robbery_debug.py <YYYY_MM_DD>")
        logging.info("Example: python main_robbery_debug.py 2025_06_03")
