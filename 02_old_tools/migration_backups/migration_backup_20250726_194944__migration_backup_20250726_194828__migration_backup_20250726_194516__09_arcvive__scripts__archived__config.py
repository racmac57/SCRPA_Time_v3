import os
from datetime import timedelta

# Only export these categories
CRIME_TYPES = [
    "Motor Vehicle Theft",
    "Burglary - Comm & Res",
    "Burglary Auto",
    "Sexual Offenses",
    "Robbery"
]

# New mapping of logical names → ArcGIS layer names
LAYER_NAME_MAP = {
    "Motor Vehicle Theft": "MV Theft",
    "Burglary Auto": "Burglary - Auto",
    "Burglary - Comm & Res": "Burglary - Comm & Res",
    "Sexual Offenses": "Sexual Offenses",
    "Robbery": "Robbery"
}

# Used to build SQL WHERE clause based on crime type
def get_sql_pattern_for_crime(crime_type):
    patterns = {
        "Motor Vehicle Theft": ["Motor Vehicle Theft"],
        "Burglary Auto": ["Burglary - Auto"],
        "Burglary - Comm & Res": ["Burglary - Residence", "Burglary - Commercial"],
        "Sexual Offenses": ["Sexual"],
        "Robbery": ["Robbery"]
    }
    return patterns.get(crime_type)

# Date calculations
def get_7day_period_dates(report_date):
    start_date = report_date - timedelta(days=6)
    return start_date, report_date

def get_28day_period_dates(report_date):
    start_date = report_date - timedelta(days=27)
    return start_date, report_date

def get_ytd_period_dates(report_date):
    start_date = report_date.replace(month=1, day=1)
    return start_date, report_date

# Folder naming based on type and date
def get_crime_type_folder(crime_type, report_date_str):
    root = os.path.join(
        r"C:\Users\carucci_r\OneDrive - City of Hackensack\_Hackensack_Data_Repository\GIS_Tools\Scripts\ScriptsTimeSCRPATemplet\7_day_crime_report_tool_scripts\SCRPA_Reports",
        f"C06W21_{report_date_str}"
    )
    safe_folder = crime_type.replace(" ", "_").replace("&", "and")
    return os.path.join(root, safe_folder)
