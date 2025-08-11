# 🕒 2025-06-17-23-10-00
# SCRPA_Time/map_export.py
# Author: R. A. Carucci
# Purpose: Export maps for SCRPA reports using dynamic crime-type SQL filters and save to appropriate report folders.

import arcpy
import os
from config import get_crime_type_folder, get_sql_pattern_for_crime

def generate_map(crime_type, report_date_str):
    aprx_path = r"C:\GIS\SCRPA_Map_Project.aprx"
    mxd_name = crime_type.replace(" ", "_") + "_Map"
    output_folder = get_crime_type_folder(crime_type, report_date_str)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    sql_filter = build_definition_query(crime_type)

    aprx = arcpy.mp.ArcGISProject(aprx_path)
    maps = [m for m in aprx.listMaps() if m.name == mxd_name]
    if not maps:
        raise ValueError(f"Map '{mxd_name}' not found in {aprx_path}")
    map_obj = maps[0]

    for lyr in map_obj.listLayers():
        if lyr.supports("DEFINITIONQUERY"):
            lyr.definitionQuery = sql_filter

    layout = aprx.listLayouts()[0]
    export_path = os.path.join(output_folder, f"{mxd_name}.png")
    layout.exportToPNG(export_path, 300)
    print(f"✅ Exported map for {crime_type} to {export_path}")

def build_definition_query(crime_type):
    pattern = get_sql_pattern_for_crime(crime_type)
    if isinstance(pattern, list):
        return " AND ".join([f"calltype LIKE '%{term}%'" for term in pattern]) + " AND disposition LIKE '%See Report%'"
    elif isinstance(pattern, str):
        return f"calltype LIKE '%{pattern}%' AND disposition LIKE '%See Report%'"
    else:
        raise ValueError(f"No valid SQL pattern defined for {crime_type}")
