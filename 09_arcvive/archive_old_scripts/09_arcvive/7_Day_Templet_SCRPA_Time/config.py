#🕒 2025-06-17-23-10-00
# SCRPA_Time/config.py
# Author: R. A. Carucci
# Purpose: Define configuration constants, dynamic path utilities, SQL pattern mappings, and validation for SCRPA chart and map automation.

import os
from datetime import datetime, timedelta

# --- Static Configuration Paths ---
REPORT_BASE_DIR = r"C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\_Hackensack_Data_Repository\\GIS_Tools\\SCRPA_Reports"
POWERPOINT_TEMPLATES = {
    "7-Day": r"C:\\Templates\\SCRPA_7Day_Template.pptx",
    "28-Day": r"C:\\Templates\\SCRPA_28Day_Template.pptx",
    "YTD": r"C:\\Templates\\SCRPA_YTD_Template.pptx"
}

# --- Crime Type Folder Mapping ---
CRIME_FOLDER_MAPPING = {
    "Robbery": "Robbery",
    "Burglary Auto": "Burglary_Auto",
    "Sexual Offenses": "Sexual_Offenses",
    "MV Theft": "MV_Theft"
}

# --- SQL Pattern Definitions ---
def get_sql_pattern_for_crime(crime_type):
    patterns = {
        "Robbery": "ROBBERY",
        "Burglary Auto": ["BURGLARY", "AUTO"],
        "Sexual Offenses": "SEXUAL",
        "MV Theft": "VEHICLE THEFT"
    }
    return patterns.get(crime_type)

# --- Time Period Helpers ---
def get_7day_period_dates(report_date):
    end = report_date
    start = report_date - timedelta(days=7)
    return (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))

def get_28day_period_dates(report_date):
    end = report_date
    start = report_date - timedelta(days=28)
    return (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))

def get_ytd_period_dates(report_date):
    start = report_date.replace(month=1, day=1)
    return (start.strftime("%Y-%m-%d"), report_date.strftime("%Y-%m-%d"))

# --- Output Directory Utilities ---
def get_crime_type_folder(crime_type, report_date):
    folder_name = CRIME_FOLDER_MAPPING.get(crime_type, crime_type.replace(" ", "_")).strip()
    return os.path.join(REPORT_BASE_DIR, folder_name, report_date)

def get_correct_folder_name(crime_type):
    """
    Get sanitized folder name for a given crime type.
    """
    return CRIME_FOLDER_MAPPING.get(crime_type, crime_type.replace(" ", "_").strip())

def get_output_folder(report_date):
    return os.path.join(REPORT_BASE_DIR, "_Generated", report_date)

def get_excel_report_name(report_date):
    return f"ALL_CADS_SCRPA_{report_date}.xlsx"

# --- Logging Support ---
def log_incident_summary(crime_type, report_date_str, total, counts, labels, period):
    log_path = os.path.join(REPORT_BASE_DIR, "summary_log.csv")
    header = not os.path.exists(log_path)
    with open(log_path, "a") as f:
        if header:
            f.write("Date,Crime,Period,Total," + ",".join(labels) + "\n")
        f.write(f"{report_date_str},{crime_type},{period},{total}," + ",".join(map(str, counts)) + "\n")

# --- PowerPoint Embed Hook ---
def embed_chart_into_ppt(crime_type, period_label, image_path):
    # Placeholder: actual implementation lives elsewhere
    pass

# --- Path Validation ---
def validate_all_paths():
    paths = [REPORT_BASE_DIR] + list(POWERPOINT_TEMPLATES.values())
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(f"Missing required paths: {missing}")
    return True
