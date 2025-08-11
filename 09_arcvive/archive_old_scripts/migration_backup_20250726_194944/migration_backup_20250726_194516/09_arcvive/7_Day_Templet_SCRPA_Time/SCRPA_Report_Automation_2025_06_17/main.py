#!/usr/bin/env python3
#"""
#Weekly Crime Report Automation - Hackensack Police Department
#Author: R. Carucci
#Purpose: Automated crime report generation with Excel integration
#Last Updated: 2025-06-10
#Version: 4.0 - Excel integration with crime subfolder organization
#"""

import os
import sys
import datetime
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

def initialize_arcgis_license():
    """Initialize ArcGIS Pro Basic (ArcView) license only."""
    try:
        import arcpy
        license_type = "ArcView"  # Basic level you have
        status = arcpy.CheckProduct(license_type)
        if status in ("Available", "AlreadyInitialized"):
            arcpy.SetProduct(license_type)
            print(f"✅ ArcGIS License initialized: {license_type}")
            return
        raise RuntimeError("ArcGIS Basic license (ArcView) is not available.")
    except Exception as e:
        print(f"❌ ArcGIS license initialization failed: {e}")
        sys.exit(1)

def generate_summary_report(results, output_folder):
    """Generate a comprehensive summary report."""
    summary_file = Path(output_folder) / "processing_summary.txt"

    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("Hackensack PD Crime Analysis Processing Summary\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Analysis Date: {datetime.datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("Excel Integration: ENABLED\n")
            f.write("Crime Subfolder Organization: ENABLED\n\n")
            for item in results:
                f.write(f"- {item}\n")
            f.write("\nStatus: COMPLETE\n")
    except Exception as e:
        print(f"[ERROR] Failed to write summary report: {e}")
        logging.error(f"Failed to write summary report: {e}")

def setup_logging():
    log_file = Path("crime_analysis.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return log_file

def run_main():
    setup_logging()
    initialize_arcgis_license()

    from config import CRIME_FOLDER_MAPPING, get_correct_folder_name, get_excel_report_name, REPORT_BASE_DIR, validate_all_paths, POWERPOINT_TEMPLATES
    from map_export import generate_map
    from chart_export import export_chart

    if len(sys.argv) != 7:
        print("Usage: main.py <generate_map> <export_charts> <export_reports> <day_span> <debug> <YYYY_MM_DD>")
        sys.exit(1)

    export_maps_flag = sys.argv[1].lower() == 'true'
    export_charts_flag = sys.argv[2].lower() == 'true'
    export_reports_flag = sys.argv[3].lower() == 'true'
    day_span = int(sys.argv[4])
    debug = sys.argv[5].lower() == 'true'
    date_arg = datetime.datetime.strptime(sys.argv[6], "%Y_%m_%d").date()

    logging.info("Arguments parsed successfully")
    logging.info(f"Export Maps: {export_maps_flag}, Export Charts: {export_charts_flag}, Export Reports: {export_reports_flag}, Day Span: {day_span}, Debug: {debug}, Date: {date_arg}")

    if not validate_all_paths():
        sys.exit("Configuration validation failed.")

    folder_name = get_correct_folder_name(date_arg)
    output_folder = Path(REPORT_BASE_DIR) / folder_name
    output_folder.mkdir(parents=True, exist_ok=True)
    for folder in CRIME_FOLDER_MAPPING.values():
        (output_folder / folder).mkdir(exist_ok=True)
    logging.info(f"Output folder: {output_folder}")

    results = []
    for crime_type in CRIME_FOLDER_MAPPING:
        logging.info(f"Processing: {crime_type}")
        if export_maps_flag:
            success = export_maps(crime_type, output_folder, sys.argv)
            results.append(f"{crime_type} Maps: {'Success' if success else 'Failed'}")
        if export_charts_flag:
            success = export_chart(crime_type)
            results.append(f"{crime_type} Charts: {'Success' if success else 'Failed'}")
        if export_reports_flag:
            results.append(f"{crime_type} Reports: Not Implemented")

    generate_summary_report(results, output_folder)
    print("\n✔️ Report generation completed.")

if __name__ == "__main__":
    run_main()
