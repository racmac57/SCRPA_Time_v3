# 🕒 2025-06-25-15-45-30
# SCRPA Crime Analysis/config.py
# Author: R. A. Carucci
# Purpose: Updated configuration file with improved error handling and data validation

import os
from datetime import datetime, timedelta

# Report configuration
REPORT_CYCLES = {
    '7Day': {
        'name': '7-Day',
        'days_back': 7,
        'filter_field': 'Cycle',
        'filter_value': '7-Day'
    },
    '28Day': {
        'name': '28-Day', 
        'days_back': 28,
        'filter_field': 'Cycle',
        'filter_value': '28-Day'
    },
    'YTD': {
        'name': 'Year-to-Date',
        'days_back': None,
        'filter_field': 'Cycle', 
        'filter_value': 'YTD'
    }
}

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# Ensure directories exist
for directory in [DATA_DIR, OUTPUT_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

# Data validation settings
DATA_VALIDATION = {
    'required_fields': [
        'ReportNumberNew', 'Incident', 'FullAddress2', 
        'Time of Call', 'PDZone', 'Grid', 'Cycle'
    ],
    'zone_range': (1, 9),  # Valid police zones
    'null_tolerance': 0.1,  # Allow up to 10% null values
    'min_records_for_mapping': 1
}

# Mapping configuration
MAPPING_CONFIG = {
    'coordinate_system': 3424,  # NAD83 NJ State Plane
    'grid_coordinates': {
        # Grid reference system - update these with actual coordinates
        'A1': (580000, 120000), 'A2': (581000, 120000), 'A3': (582000, 120000),
        'B1': (580000, 121000), 'B2': (581000, 121000), 'B3': (582000, 121000),
        'C1': (580000, 122000), 'C2': (581000, 122000), 'C3': (582000, 122000),
        'D1': (580000, 123000), 'D2': (581000, 123000), 'D3': (582000, 123000),
        'E1': (580000, 124000), 'E2': (581000, 124000), 'E3': (582000, 124000),
        'F1': (580000, 125000), 'F2': (581000, 125000), 'F3': (582000, 125000),
        'G1': (580000, 126000), 'G2': (581000, 126000), 'G3': (582000, 126000),
        'H1': (580000, 127000), 'H2': (581000, 127000), 'H3': (582000, 127000),
        'I1': (583000, 120000), 'I2': (583000, 121000), 'I3': (583000, 122000),
        'J1': (584000, 120000), 'J2': (584000, 121000), 'J3': (584000, 122000),
        'K1': (585000, 120000), 'K2': (585000, 121000), 'K3': (585000, 122000),
    },
    'zone_centroids': {
        # Zone centroid coordinates - update with actual values
        5: (580500, 120500),
        6: (581500, 120500), 
        7: (582500, 120500),
        8: (583500, 120500),
        9: (584500, 120500)
    },
    'symbol_settings': {
        'color': [255, 0, 0, 100],  # Red with transparency
        'size': 8,
        'outline_color': [0, 0, 0, 255],  # Black outline
        'outline_width': 1
    }
}

# Chart configuration
CHART_CONFIG = {
    'figure_size': (10, 6),
    'dpi': 300,
    'style': 'seaborn-v0_8',
    'colors': {
        'primary': 'steelblue',
        'secondary': 'lightcoral', 
        'time_periods': ['#FFD700', '#FF8C00', '#4169E1']  # Gold, Orange, Blue
    },
    'time_periods': {
        'Day': (6, 14),    # 6am to 2pm
        'Evening': (14, 22),  # 2pm to 10pm
        'Night': (22, 6)   # 10pm to 6am (next day)
    }
}

# Incident categorization
INCIDENT_CATEGORIES = {
    'Violent Crimes': [
        'Robbery', 'Sexual Assault', 'Assault', 'Homicide', 
        'Domestic Violence', 'Aggravated Assault'
    ],
    'Property Crimes': [
        'Burglary', 'Motor Vehicle Theft', 'Theft', 'Vandalism',
        'Breaking and Entering', 'Larceny'
    ],
    'Drug Crimes': [
        'Drug Possession', 'Drug Distribution', 'Drug Manufacturing',
        'CDS', 'Controlled Substance'
    ],
    'Traffic': [
        'DWI', 'Traffic Violation', 'Motor Vehicle Accident',
        'Reckless Driving', 'Hit and Run'
    ],
    'Other': []  # Catch-all for uncategorized
}

# Error handling
ERROR_CONFIG = {
    'max_retries': 3,
    'retry_delay': 1,  # seconds
    'log_errors': True,
    'create_placeholders': True,
    'fallback_to_zone_centroids': True
}

# Report formatting
REPORT_FORMAT = {
    'title_template': "SCRPA Crime Analysis Report - {cycle} Period",
    'subtitle_template': "Generated on {date}",
    'footer_template': "Hackensack Police Department | Principal Analyst: R. A. Carucci",
    'date_format': "%B %d, %Y at %I:%M %p"
}

def get_cycle_dates(cycle_type):
    """
    Calculate the date range for a given cycle type
    """
    today = datetime.now().date()
    
    if cycle_type.upper() == '7DAY':
        start_date = today - timedelta(days=7)
        return start_date, today
    elif cycle_type.upper() == '28DAY':
        start_date = today - timedelta(days=28)
        return start_date, today
    elif cycle_type.upper() == 'YTD':
        start_date = datetime(today.year, 1, 1).date()
        return start_date, today
    else:
        raise ValueError(f"Unknown cycle type: {cycle_type}")

def validate_data_file(file_path):
    """
    Basic validation of data file existence and format
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    if not file_path.endswith(('.csv', '.xlsx', '.xlsm')):
        raise ValueError(f"Unsupported file format: {file_path}")
    
    return True

def get_output_paths(cycle_type, base_output_dir=None):
    """
    Generate standardized output file paths
    """
    if base_output_dir is None:
        base_output_dir = OUTPUT_DIR
    
    cycle_lower = cycle_type.lower()
    
    return {
        'zone_chart': os.path.join(base_output_dir, f"zone_chart_{cycle_lower}.png"),
        'time_chart': os.path.join(base_output_dir, f"time_chart_{cycle_lower}.png"),
        'incident_chart': os.path.join(base_output_dir, f"incident_chart_{cycle_lower}.png"),
        'crime_map': os.path.join(base_output_dir, f"crime_map_{cycle_lower}.png"),
        'data_csv': os.path.join(base_output_dir, f"crime_data_{cycle_lower}.csv"),
        'summary': os.path.join(base_output_dir, f"summary_{cycle_lower}.txt")
    }

# Debug settings
DEBUG = {
    'verbose_logging': True,
    'save_intermediate_files': True,
    'skip_cleanup': False,
    'test_mode': False
}

# Version info
VERSION = "2.1.0"
LAST_UPDATED = "2025-06-25"
AUTHOR = "R. A. Carucci"

print(f"SCRPA Crime Analysis Configuration Loaded - Version {VERSION}")
print(f"Last Updated: {LAST_UPDATED}")
print(f"Output Directory: {OUTPUT_DIR}")
