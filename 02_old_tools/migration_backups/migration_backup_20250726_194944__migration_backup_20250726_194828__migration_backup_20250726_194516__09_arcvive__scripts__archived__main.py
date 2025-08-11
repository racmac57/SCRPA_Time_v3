# main.py
# Author: R. A. Carucci
# Purpose: Orchestrates the SCRPA Report automation process.

import os
import sys
import logging
import datetime
from config import (
    CRIME_TYPES,
    validate_all_paths,
    get_output_folder
)
from map_export import export_maps
from chart_export import export_chart

def run_main():
    print("--------------------------------------------")
    print("📊🗺️ SCRPA Report Automation")
    print("👤📁 Author: R. A. Carucci")
    print("--------------------------------------------")

    if len(sys.argv) < 2:
        date_arg = input("Enter report date (format: YYYY_MM_DD): ").strip()
    else:
        date_arg = sys.argv[1]

    print(f"Running SCRPA report for {date_arg}...")

    try:
        datetime.datetime.strptime(date_arg, "%Y_%m_%d")
    except Exception as e:
        print(f"❌ Invalid date format: {e}")
        return

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    try:
        validate_all_paths()
    except FileNotFoundError as e:
        print(f"❌ Path validation failed: {e}")
        return

    export_maps_flag = True
    export_charts_flag = True
    export_reports_flag = True

    output_folder = get_output_folder(date_arg)
    print(f"Output folder: {output_folder}")
    logging.info(f"Export Maps: {export_maps_flag}, Export Charts: {export_charts_flag}, Export Reports: {export_reports_flag}, Day Span: 7, Debug: False, Date: {date_arg}")

    for crime_type in CRIME_TYPES:
        print(f"Processing: {crime_type}")
        logging.info(f"Processing: {crime_type}")

        if export_maps_flag:
            success = export_maps(crime_type, output_folder, sys.argv)
            if not success:
                logging.warning(f"⚠️ Map export failed for {crime_type}")

        if export_charts_flag:
            for period in ["7-Day", "28-Day", "YTD"]:
                export_chart(crime_type, date_arg, period)

    print("--------------------------------------------")
    print("✅ SCRPA Report Run Complete")
    input("Press any key to continue . . .")

if __name__ == "__main__":
    run_main()
