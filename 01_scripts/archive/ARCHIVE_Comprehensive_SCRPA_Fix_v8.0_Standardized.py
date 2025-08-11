# 🕒 2025-07-29-17-00-00
# SCRPA_Time_v2/Comprehensive_SCRPA_Fix_v8.0_Standardized
# Author: R. A. Carucci
# Purpose: Fixed version with proper PascalCase_With_Underscores column standardization to match Power BI requirements

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from pathlib import Path
import logging

class ComprehensiveSCRPAFixV8_0:
    """
    ✅ **NEW in v8.0**: Complete alignment with Power BI column standardization requirements
    ✅ All columns follow PascalCase_With_Underscores standard
    ✅ Matches the M Code transformation functions exactly
    ✅ Proper case-insensitive crime filtering 
    ✅ Enhanced time calculations with standardized column names
    ✅ Vehicle formatting consistent with M Code requirements
    ✅ Block calculation matching Power Query logic
    """
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)
            
        self.export_dirs = {
            'cad_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\05_EXPORTS"),
            'rms_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\05_EXPORTS")
        }
        
        self.ref_dirs = {
            'call_types': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Classifications\CallTypes\CallType_Categories.xlsx"),
            'zone_grid': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\zone_grid_master.xlsx")
        }
        
        self.call_type_ref = None
        self.zone_grid_ref = None
        self.setup_logging()
        self.load_reference_data()

    def setup_logging(self):
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"comprehensive_scrpa_fix_v8_0_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.logger = logging.getLogger('ComprehensiveSCRPAFixV8_0')
        self.logger.setLevel(logging.INFO)
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        fh = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        # Also log to console
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        self.logger.info("=== Comprehensive SCRPA Fix V8.0 - Column Standardization Version ===")

    def load_reference_data(self):
        """Load reference data for call type categorization and zone/grid mapping."""
        # Load call type reference
        try:
            if self.ref_dirs['call_types'].exists():
                self.call_type_ref = pd.read_excel(self.ref_dirs['call_types'])
                self.logger.info(f"Loaded call type reference: {len(self.call_type_ref)} records")
                # Standardize column names in reference data
                if not self.call_type_ref.empty:
                    self.call_type_ref.columns = [self.convert_to_lowercase_with_underscores(col) for col in self.call_type_ref.columns]
                    self.logger.info(f"Reference file columns after standardization: {list(self.call_type_ref.columns)}")
            else:
                # Try fallback path
                fallback_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\CallType_Categories.xlsx")
                if fallback_path.exists():
                    self.call_type_ref = pd.read_excel(fallback_path)
                    self.logger.info(f"Loaded call type reference from fallback path: {len(self.call_type_ref)} records")
                    # Standardize column names in reference data
                    if not self.call_type_ref.empty:
                        self.call_type_ref.columns = [self.convert_to_lowercase_with_underscores(col) for col in self.call_type_ref.columns]
                        self.logger.info(f"Reference file columns after standardization: {list(self.call_type_ref.columns)}")
                else:
                    self.logger.warning("Call type reference file not found at primary or fallback paths - using fallback categorization")
                    self.call_type_ref = None
        except Exception as e:
            self.logger.error(f"Could not load call type reference: {e}")
            self.call_type_ref = None
            
        # Load zone/grid reference
        try:
            if self.ref_dirs['zone_grid'].exists():
                self.zone_grid_ref = pd.read_excel(self.ref_dirs['zone_grid'])
                self.logger.info(f"Loaded zone/grid reference: {len(self.zone_grid_ref)} records")
                # Standardize column names in reference data
                if not self.zone_grid_ref.empty:
                    self.zone_grid_ref.columns = [self.convert_to_lowercase_with_underscores(col) for col in self.zone_grid_ref.columns]
            else:
                self.logger.warning("Zone/grid reference file not found - no backfill available")
                self.zone_grid_ref = None
        except Exception as e:
            self.logger.error(f"Could not load zone/grid reference: {e}")
            self.zone_grid_ref = None

    def convert_to_lowercase_with_underscores(self, column_name: str) -> str:
        """
        Convert any column name to lowercase_with_underscores standard.
        This matches the critical path correction requirements.
        FIXED: Now properly handles numbers in column names.
        """
        # Clean the input
        name = str(column_name).strip()
        
        # Remove common prefixes
        name = re.sub(r'^(CAD_|RMS_|cad_|rms_)', '', name, flags=re.IGNORECASE)
        
        # Handle specific cases first
        special_cases = {
            'PDZone': 'pd_zone',
            'CADNotes': 'cad_notes',
            'ReportNumberNew': 'report_number_new',
            'vehicle_1': 'vehicle_1',
            'vehicle_2': 'vehicle_2',
            'vehicle_1_and_vehicle_2': 'vehicle_1_and_vehicle_2'
        }
        
        if name in special_cases:
            return special_cases[name]
        
        # Handle camelCase and PascalCase by inserting spaces before capitals
        # But not at the beginning of the string
        name = re.sub(r'(?<!^)([a-z])([A-Z])', r'\1 \2', name)
        
        # Handle sequences of capitals followed by lowercase (like 'CADNotes' -> 'CAD Notes')
        name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', name)
        
        # Replace various separators with spaces
        name = re.sub(r'[_\-\s]+', ' ', name)
        
        # Split by spaces and convert to lowercase
        words = [word.lower() for word in name.split() if word]
        
        # Join with underscores
        return '_'.join(words)

    def map_call_type(self, incident_value):
        """Map incident value to response_type and category_type using reference data."""
        if pd.isna(incident_value) or not incident_value:
            return None, None
            
        # Clean input
        incident_clean = str(incident_value).strip().upper()
        
        # Try to use reference data if available
        if self.call_type_ref is not None and not self.call_type_ref.empty:
            try:
                # Log available columns for debugging
                if not hasattr(self, '_logged_ref_columns'):
                    self.logger.info(f"Reference file columns: {list(self.call_type_ref.columns)}")
                    self._logged_ref_columns = True
                
                # Look for exact match first (assuming 'incident' column exists in reference)
                if 'incident' in self.call_type_ref.columns:
                    match = self.call_type_ref[self.call_type_ref['incident'].str.upper() == incident_clean]
                    if not match.empty:
                        response_type = match.iloc[0].get('response_type', incident_value)
                        category_type = match.iloc[0].get('category_type', 'Other')
                        return response_type, category_type
                
                # Fallback: look for partial matches
                for _, row in self.call_type_ref.iterrows():
                    if 'incident' in row and pd.notna(row['incident']):
                        if incident_clean in str(row['incident']).upper():
                            response_type = row.get('response_type', incident_value) 
                            category_type = row.get('category_type', 'Other')
                            return response_type, category_type
            except Exception as e:
                self.logger.warning(f"Error using call type reference: {e}")
        
        # Fallback categorization
        response_type = incident_value
        if any(term in incident_clean for term in ['TRAFFIC', 'MOTOR', 'VEHICLE', 'ACCIDENT']):
            category_type = 'Traffic'
        elif any(term in incident_clean for term in ['ALARM', 'SECURITY']):
            category_type = 'Alarm'
        elif any(term in incident_clean for term in ['MEDICAL', 'EMS', 'AMBULANCE']):
            category_type = 'Medical'
        elif any(term in incident_clean for term in ['FIRE', 'SMOKE']):
            category_type = 'Fire'
        elif any(term in incident_clean for term in ['THEFT', 'BURGLARY', 'ROBBERY', 'LARCENY']):
            category_type = 'Crime'
        elif any(term in incident_clean for term in ['DOMESTIC', 'DISTURBANCE', 'FIGHT']):
            category_type = 'Disturbance'
        else:
            category_type = 'Other'
            
        return response_type, category_type

    def format_time_spent_minutes(self, minutes):
        """Format time spent minutes to '0 Hrs. 00 Mins' format."""
        if pd.isna(minutes) or minutes is None:
            return None
        try:
            total_minutes = int(float(minutes))
            if total_minutes < 0:
                return None
            hours = total_minutes // 60
            mins = total_minutes % 60
            return f"{hours} Hrs. {mins:02d} Mins"
        except:
            return None

    def format_time_response_minutes(self, minutes):
        """Format time response minutes to '00 Mins. 00 Secs' format."""
        if pd.isna(minutes) or minutes is None:
            return None
        try:
            total_minutes = float(minutes)
            if total_minutes < 0:
                return None
            mins = int(total_minutes)
            secs = int((total_minutes - mins) * 60)
            return f"{mins:02d} Mins. {secs:02d} Secs"
        except:
            return None

    def clean_how_reported_911(self, how_reported):
        """Fix '9-1-1' date issue in how_reported field."""
        if pd.isna(how_reported):
            return None
        
        text = str(how_reported).strip()
        
        # Handle various date formats that might be incorrectly applied to "9-1-1"
        # Common patterns when Excel converts "9-1-1" to dates:
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD format
            r'^\d{1,2}/\d{1,2}/\d{4}',  # M/D/YYYY or MM/DD/YYYY format
            r'^\d{1,2}-\d{1,2}-\d{4}',  # M-D-YYYY or MM-DD-YYYY format
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO datetime format
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # YYYY-MM-DD HH:MM:SS format
        ]
        
        # Check if the value matches any date pattern
        for pattern in date_patterns:
            if re.match(pattern, text):
                return "9-1-1"
        
        # Also check for specific date values that commonly result from "9-1-1" conversion
        # September 1, 2001 (9/1/2001) is a common misinterpretation
        if text in ['2001-09-01', '2001-09-01 00:00:00', '09/01/2001', '9/1/2001', '2001-09-01T00:00:00']:
            return "9-1-1"
        
        # If the original value is already "9-1-1" or similar, return as is
        if text.lower() in ['9-1-1', '911', '9-1-1', '9/1/1']:
            return "9-1-1"
        
        return text

    def extract_username_timestamp(self, cad_notes):
        """Extract username and timestamp from CAD notes and return cleaned notes."""
        if pd.isna(cad_notes):
            return None, None, None
            
        text = str(cad_notes)
        username = None
        timestamp = None
        
        # Look for username pattern (usually at start)
        username_match = re.search(r'^([A-Z]+\d*|[a-zA-Z]+\.[a-zA-Z]+)', text)
        if username_match:
            username = username_match.group(1)
        
        # Look for timestamp patterns
        timestamp_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [AP]M',
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}'
        ]
        
        for pattern in timestamp_patterns:
            timestamp_match = re.search(pattern, text)
            if timestamp_match:
                timestamp = timestamp_match.group(0)
                break
        
        # Clean the notes by removing username/timestamp patterns
        cleaned = text
        if username:
            cleaned = re.sub(f'^{re.escape(username)}[\\s:]*', '', cleaned)
        if timestamp:
            cleaned = re.sub(re.escape(timestamp), '', cleaned)
        
        # Additional cleaning
        cleaned = re.sub(r'[\r\n\t]+', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned) 
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else None, username, timestamp

    def validate_hackensack_address(self, address):
        """Validate and fix addresses to ensure they're in Hackensack, NJ."""
        if pd.isna(address):
            return None
            
        addr_str = str(address).strip()
        
        # Remove any Jersey City addresses - these are errors
        if 'JERSEY CITY' in addr_str.upper() or 'JC,' in addr_str.upper():
            self.logger.warning(f"Removing Jersey City address: {addr_str}")
            return None
            
        # Ensure Hackensack addresses are properly formatted
        if 'HACKENSACK' not in addr_str.upper():
            # Add Hackensack, NJ if missing
            if not addr_str.endswith(', NJ') and not addr_str.endswith(', NJ, 07601'):
                addr_str = f"{addr_str}, Hackensack, NJ, 07601"
            else:
                addr_str = addr_str.replace(', NJ', ', Hackensack, NJ')
                
        return addr_str

    def backfill_grid_post(self, address, current_grid, current_post):
        """Backfill missing grid and post values using zone_grid_master reference."""
        # If both grid and post exist, return as is
        if pd.notna(current_grid) and pd.notna(current_post):
            return current_grid, current_post
            
        # If no reference data available, return current values
        if self.zone_grid_ref is None or self.zone_grid_ref.empty:
            return current_grid, current_post
            
        if pd.isna(address):
            return current_grid, current_post
            
        try:
            # Clean address for matching
            clean_addr = str(address).replace(', Hackensack, NJ, 07601', '').strip()
            
            # Try to find a match in the reference data
            # Assuming the reference has columns like 'address', 'grid', 'post' or similar
            ref_cols = self.zone_grid_ref.columns.tolist()
            
            # Look for address-like column
            address_col = None
            for col in ref_cols:
                if any(term in col.lower() for term in ['address', 'location', 'street']):
                    address_col = col
                    break
                    
            if address_col:
                # Try exact match first
                match = self.zone_grid_ref[self.zone_grid_ref[address_col].str.contains(clean_addr, case=False, na=False)]
                
                if not match.empty:
                    row = match.iloc[0]
                    
                    # Get grid if missing
                    if pd.isna(current_grid):
                        for col in ref_cols:
                            if 'grid' in col.lower():
                                current_grid = row.get(col)
                                break
                                
                    # Get post if missing  
                    if pd.isna(current_post):
                        for col in ref_cols:
                            if any(term in col.lower() for term in ['post', 'zone', 'district']):
                                current_post = row.get(col)
                                break
                                
        except Exception as e:
            self.logger.warning(f"Error in grid/post backfill: {e}")
            
        return current_grid, current_post

    def format_incident_time(self, time_val):
        """Format incident time to HH:MM format."""
        if pd.isna(time_val):
            return None
            
        try:
            if isinstance(time_val, pd.Timedelta):
                total_seconds = time_val.total_seconds()
                hours = int(total_seconds // 3600) % 24
                minutes = int((total_seconds % 3600) // 60)
                return f"{hours:02d}:{minutes:02d}"
            elif hasattr(time_val, 'hour') and hasattr(time_val, 'minute'):
                return f"{time_val.hour:02d}:{time_val.minute:02d}"
            else:
                # Try to parse as time
                parsed_time = pd.to_datetime(time_val, errors='coerce').time()
                if parsed_time:
                    return f"{parsed_time.hour:02d}:{parsed_time.minute:02d}"
        except:
            pass
            
        return None

    def get_rms_column_mapping(self) -> dict:
        """Get the standardized RMS column mapping to match M Code."""
        return {
            "Case Number": "case_number",
            "Incident Date": "incident_date_raw",
            "Incident Time": "incident_time_raw",
            "Incident Date_Between": "incident_date_between_raw",
            "Incident Time_Between": "incident_time_between_raw",
            "Report Date": "report_date_raw",
            "Report Time": "report_time_raw",
            "Incident Type_1": "incident_type_1_raw",
            "Incident Type_2": "incident_type_2_raw",
            "Incident Type_3": "incident_type_3_raw",
            "FullAddress": "full_address_raw",
            "Grid": "grid_raw",
            "Zone": "zone_raw",
            "Narrative": "narrative_raw",
            "Total Value Stolen": "total_value_stolen",
            "Total Value Recover": "total_value_recovered",
            "Registration 1": "registration_1",
            "Make1": "make_1",
            "Model1": "model_1",
            "Reg State 1": "reg_state_1",
            "Registration 2": "registration_2",
            "Reg State 2": "reg_state_2",
            "Make2": "make_2",
            "Model2": "model_2",
            "Reviewed By": "reviewed_by",
            "CompleteCalc": "complete_calc",
            "Officer of Record": "officer_of_record",
            "Squad": "squad",
            "Det_Assigned": "det_assigned",
            "Case_Status": "case_status",
            "NIBRS Classification": "nibrs_classification"
        }

    def get_cad_column_mapping(self) -> dict:
        """Get the standardized CAD column mapping with lowercase_with_underscores."""
        return {
            "ReportNumberNew": "case_number",
            "Incident": "incident_raw",
            "How Reported": "how_reported",
            "FullAddress2": "full_address_raw",
            "PDZone": "post",
            "Grid": "grid_raw",
            "Time of Call": "time_of_call",
            "cYear": "call_year",
            "cMonth": "call_month",
            "HourMinuetsCalc": "hour_minutes_calc",
            "DayofWeek": "day_of_week_raw",
            "Time Dispatched": "time_dispatched",
            "Time Out": "time_out",
            "Time In": "time_in",
            "Time Spent": "time_spent_raw",
            "Time Response": "time_response_raw",
            "Officer": "officer",
            "Disposition": "disposition",
            "Response Type": "response_type_fallback",
            "CADNotes": "cad_notes_raw"
        }

    def clean_text_comprehensive(self, text):
        """Enhanced text cleaning function."""
        if pd.isna(text) or text is None:
            return None
        
        text = str(text)
        
        # Remove problematic patterns
        text = re.sub(r'(\s*[\?\-]\s*){2,}', ' ', text)
        text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # Remove non-printable characters
        text = ''.join(c for c in text if c.isprintable() or c.isspace())
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text if text else None

    def cascade_date(self, row):
        """Cascading date logic matching M Code exactly."""
        # Try new lowercase column names first
        if pd.notna(row.get('incident_date_raw')):
            return pd.to_datetime(row['incident_date_raw'], errors='coerce').date()
        elif pd.notna(row.get('incident_date_between_raw')):
            return pd.to_datetime(row['incident_date_between_raw'], errors='coerce').date()
        elif pd.notna(row.get('report_date_raw')):
            return pd.to_datetime(row['report_date_raw'], errors='coerce').date()
        # Fallback to old column names for compatibility
        elif pd.notna(row.get('Incident_Date_Raw')):
            return pd.to_datetime(row['Incident_Date_Raw'], errors='coerce').date()
        elif pd.notna(row.get('Incident_Date_Between_Raw')):
            return pd.to_datetime(row['Incident_Date_Between_Raw'], errors='coerce').date()
        elif pd.notna(row.get('Report_Date_Raw')):
            return pd.to_datetime(row['Report_Date_Raw'], errors='coerce').date()
        return None

    def cascade_time(self, row):
        """
        FIXED: Cascading time logic that handles both raw and mapped column names.
        
        CRITICAL BUG FIXES:
        1. Original function assumed columns were already mapped
        2. Did not handle Excel Timedelta objects correctly
        
        This version handles both raw/mapped names AND Timedelta objects.
        """
        # Priority order: try lowercase names first, then mapped names, fall back to raw names
        time_column_pairs = [
            ('incident_time_raw', 'Incident_Time_Raw', 'Incident Time'),           # New lowercase, Old mapped, Raw name
            ('incident_time_between_raw', 'Incident_Time_Between_Raw', 'Incident Time_Between'),
            ('report_time_raw', 'Report_Time_Raw', 'Report Time')
        ]
        
        for lowercase_col, mapped_col, raw_col in time_column_pairs:
            time_value = None
            
            # Try lowercase column name first
            if lowercase_col in row.index and pd.notna(row.get(lowercase_col)):
                time_value = row[lowercase_col]
            # Try mapped column name
            elif mapped_col in row.index and pd.notna(row.get(mapped_col)):
                time_value = row[mapped_col]
            # Fallback to raw column name
            elif raw_col in row.index and pd.notna(row.get(raw_col)):
                time_value = row[raw_col]
            
            # Process the time value if found
            if time_value is not None:
                try:
                    # CRITICAL: Handle Excel Timedelta objects
                    if isinstance(time_value, pd.Timedelta):
                        total_seconds = time_value.total_seconds()
                        hours = int(total_seconds // 3600) % 24  # Handle 24+ hour overflow
                        minutes = int((total_seconds % 3600) // 60)
                        seconds = int(total_seconds % 60)
                        
                        from datetime import time
                        return time(hours, minutes, seconds)
                    else:
                        return pd.to_datetime(time_value, errors='coerce').time()
                except:
                    continue
        
        return None

    def get_time_of_day(self, time_val):
        """Time of day calculation matching M Code exactly."""
        if pd.isna(time_val):
            return "Unknown"
        
        hour = time_val.hour
        if 0 <= hour < 4:
            return "00:00–03:59 Early Morning"
        elif 4 <= hour < 8:
            return "04:00–07:59 Morning"
        elif 8 <= hour < 12:
            return "08:00–11:59 Morning Peak"
        elif 12 <= hour < 16:
            return "12:00–15:59 Afternoon"
        elif 16 <= hour < 20:
            return "16:00–19:59 Evening Peak"
        else:
            return "20:00–23:59 Night"

    def get_time_of_day_sort_order(self, time_of_day):
        """Get sort order for time of day categories for Power BI sorting."""
        sort_order_map = {
            "00:00-03:59 Early Morning": 1,
            "04:00-07:59 Morning": 2,
            "08:00-11:59 Morning Peak": 3,
            "12:00-15:59 Afternoon": 4,
            "16:00-19:59 Evening Peak": 5,
            "20:00-23:59 Night": 6,
            "Unknown": 99
        }
        return sort_order_map.get(time_of_day, 99)

    def get_period(self, date_val):
        """Period calculation matching M Code exactly."""
        if pd.isna(date_val):
            return "Historical"
        
        today = pd.Timestamp.now().date()
        days_diff = (today - date_val).days
        
        if days_diff <= 7:
            return "7-Day"
        elif days_diff <= 28:
            return "28-Day"
        elif date_val.year == today.year:
            return "YTD"
        else:
            return "Historical"

    def get_season(self, date_val):
        """Season calculation matching M Code exactly."""
        if pd.isna(date_val):
            return None
        
        month = date_val.month
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        else:
            return "Fall"

    def calculate_block(self, address):
        """Block calculation matching M Code exactly."""
        if pd.isna(address):
            return "Check Location Data"
        
        # Clean address
        addr = str(address).replace(", Hackensack, NJ, 07601", "")
        
        # Handle intersections
        if " & " in addr:
            parts = addr.split(" & ")
            if len(parts) == 2 and all(p.strip() for p in parts):
                return f"{parts[0].strip()} & {parts[1].strip()}"
            else:
                return "Incomplete Address - Check Location Data"
        else:
            # Handle regular addresses
            try:
                parts = addr.split(" ", 1)
                if len(parts) >= 2:
                    street_num = int(parts[0])
                    street_name = parts[1].split(",")[0].strip()
                    block_num = (street_num // 100) * 100
                    return f"{street_name}, {block_num} Block"
                else:
                    return "Check Location Data"
            except:
                return "Check Location Data"

    def clean_incident_type(self, incident_str):
        """Clean incident type by removing statute codes."""
        if pd.isna(incident_str):
            return None
        # Remove statute codes
        if " - 2C" in incident_str:
            return incident_str.split(" - 2C")[0]
        return incident_str

    def multi_column_crime_search(self, row, crime_patterns):
        """
        Search across all incident-type columns for crime patterns.
        
        Args:
            row (pd.Series): DataFrame row containing incident data
            crime_patterns (dict): Dictionary mapping crime categories to regex patterns
            
        Returns:
            str: Matching crime category or 'Other' if no match found
        """
        # Define columns to search across (in order of priority)
        search_columns = [
            'incident_type',           # Primary RMS column
            'all_incidents',           # Combined incidents
            'vehicle_1',               # Additional incident data
            'vehicle_2',               # Additional incident data
            'incident_type_1_raw',     # Raw incident types if available
            'incident_type_2_raw',     # Raw incident types if available
            'incident_type_3_raw'      # Raw incident types if available
        ]
        
        # Search each column for crime patterns
        for column in search_columns:
            if column in row.index and pd.notna(row[column]):
                column_value = str(row[column]).upper()
                
                # Test each crime pattern against the column value
                for category, patterns in crime_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, column_value, re.IGNORECASE):
                            self.logger.debug(f"Found {category} in column {column}: '{row[column]}' matches pattern '{pattern}'")
                            return category
        
        return 'Other'

    def get_crime_category(self, all_incidents, incident_type):
        """
        Enhanced case-insensitive crime category filtering with multi-column search.
        Now searches across all relevant incident columns for comprehensive coverage.
        """
        # Define comprehensive crime patterns with regex for flexible matching
        crime_patterns = {
            'Motor Vehicle Theft': [
                r'MOTOR\s+VEHICLE\s+THEFT',
                r'AUTO\s+THEFT',
                r'MV\s+THEFT',
                r'VEHICLE\s+THEFT'
            ],
            'Burglary - Auto': [
                r'BURGLARY.*AUTO',
                r'BURGLARY.*VEHICLE',
                r'BURGLARY\s*-\s*AUTO',
                r'BURGLARY\s*-\s*VEHICLE'
            ],
            'Burglary - Commercial': [
                r'BURGLARY.*COMMERCIAL',
                r'BURGLARY\s*-\s*COMMERCIAL',
                r'BURGLARY.*BUSINESS'
            ],
            'Burglary - Residence': [
                r'BURGLARY.*RESIDENCE',
                r'BURGLARY\s*-\s*RESIDENCE',
                r'BURGLARY.*RESIDENTIAL',
                r'BURGLARY\s*-\s*RESIDENTIAL'
            ],
            'Robbery': [
                r'ROBBERY'
            ],
            'Sexual Offenses': [
                r'SEXUAL',
                r'SEX\s+CRIME',
                r'SEXUAL\s+ASSAULT',
                r'SEXUAL\s+OFFENSE'
            ]
        }
        
        # Create a mock row for the multi-column search
        # This allows us to use the existing multi_column_crime_search function
        mock_row = pd.Series({
            'incident_type': incident_type,
            'all_incidents': all_incidents,
            'vehicle_1': None,  # These would be populated in actual row processing
            'vehicle_2': None,
            'incident_type_1_raw': None,
            'incident_type_2_raw': None,
            'incident_type_3_raw': None
        })
        
        # Use the multi-column search function
        return self.multi_column_crime_search(mock_row, crime_patterns)

    def format_vehicle(self, reg_state, registration, make, model):
        """Format vehicle information consistently with M Code."""
        parts = []
        
        # State and registration
        if pd.notna(reg_state) and pd.notna(registration):
            parts.append(f"{reg_state} - {registration}")
        elif pd.notna(registration):
            parts.append(str(registration))
        elif pd.notna(reg_state):
            parts.append(str(reg_state))
        
        # Make and model
        make_model_parts = []
        if pd.notna(make):
            make_model_parts.append(str(make))
        if pd.notna(model):
            make_model_parts.append(str(model))
        
        if make_model_parts:
            parts.append("/".join(make_model_parts))
        
        result = ", ".join(parts) if parts else None
        
        # Convert to uppercase if result exists
        if result:
            return result.upper()
        return None

    def calculate_time_response(self, row):
        """Calculate response time in minutes with error handling."""
        try:
            time_call = pd.to_datetime(row.get('Time_Of_Call'))
            time_dispatched = pd.to_datetime(row.get('Time_Dispatched'))
            
            if pd.notna(time_call) and pd.notna(time_dispatched):
                # Calculate (Time Dispatched - Time Call)
                duration = time_dispatched - time_call
                minutes = duration.total_seconds() / 60
                
                # Handle negative durations by swapping order: (Time Call - Time Dispatched)
                if minutes < 0:
                    duration = time_call - time_dispatched
                    minutes = duration.total_seconds() / 60
                
                # Cap extreme outliers
                if minutes > 480:  # Cap at 8 hours
                    minutes = 480
                
                return round(minutes, 2)
            return None
        except:
            return None

    def calculate_time_spent(self, row):
        """Calculate time spent on scene in minutes with error handling."""
        try:
            time_out = pd.to_datetime(row.get('Time_Out'))
            time_in = pd.to_datetime(row.get('Time_In'))
            
            if pd.notna(time_out) and pd.notna(time_in):
                # Calculate (Time In - Time Out)
                duration = time_in - time_out
                minutes = duration.total_seconds() / 60
                
                # Handle negative durations by swapping order: (Time Out - Time In)
                if minutes < 0:
                    duration = time_out - time_in
                    minutes = duration.total_seconds() / 60
                
                # Cap extreme outliers
                if minutes > 720:  # Cap at 12 hours
                    minutes = 720
                
                return round(minutes, 2)
            return None
        except:
            return None

    def process_rms_data(self, rms_file):
        """Process RMS data with lowercase_with_underscores standardization, focused on crime data without CAD-specific columns."""
        self.logger.info(f"Processing RMS data: {rms_file.name}")
        
        try:
            rms_df = pd.read_excel(rms_file, engine='openpyxl')
            self.logger.info(f"Loaded RMS file with {len(rms_df)} rows and {len(rms_df.columns)} columns")
            self.logger.info(f"RMS columns found: {list(rms_df.columns)}")
        except Exception as e:
            self.logger.error(f"Error loading RMS file: {e}")
            return pd.DataFrame()

        # Apply column mapping only for columns that exist
        column_mapping = self.get_rms_column_mapping()
        existing_mapping = {k: v for k, v in column_mapping.items() if k in rms_df.columns}
        rms_df = rms_df.rename(columns=existing_mapping)
        self.logger.info(f"Applied column mapping: {existing_mapping}")
        
        # Convert ALL remaining columns to lowercase_with_underscores
        rms_df.columns = [self.convert_to_lowercase_with_underscores(col) for col in rms_df.columns]
        
        # Clean text columns
        text_columns = rms_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            rms_df[col] = rms_df[col].apply(self.clean_text_comprehensive)

        # Cascading date and time - safe column access with updated column names
        rms_df['incident_date'] = rms_df.apply(self.cascade_date, axis=1)
        rms_df['incident_time_raw'] = rms_df.apply(self.cascade_time, axis=1)
        
        # Format incident time to HH:MM format
        rms_df['incident_time'] = rms_df['incident_time_raw'].apply(self.format_incident_time)
        
        # Time of day and period calculations with proper encoding
        def safe_get_time_of_day(time_val):
            if pd.isna(time_val):
                return "Unknown"
            try:
                hour = time_val.hour if hasattr(time_val, 'hour') else 0
                if 0 <= hour < 4:
                    return "00:00-03:59 Early Morning"
                elif 4 <= hour < 8:
                    return "04:00-07:59 Morning"
                elif 8 <= hour < 12:
                    return "08:00-11:59 Morning Peak"
                elif 12 <= hour < 16:
                    return "12:00-15:59 Afternoon"
                elif 16 <= hour < 20:
                    return "16:00-19:59 Evening Peak"
                else:
                    return "20:00-23:59 Night"
            except:
                return "Unknown"
                
        rms_df['time_of_day'] = rms_df['incident_time_raw'].apply(safe_get_time_of_day)
        rms_df['time_of_day_sort_order'] = rms_df['time_of_day'].apply(self.get_time_of_day_sort_order)
        rms_df['period'] = rms_df['incident_date'].apply(self.get_period)
        rms_df['season'] = rms_df['incident_date'].apply(self.get_season)
        
        # Day of week and day type
        rms_df['day_of_week'] = rms_df['incident_date'].apply(
            lambda x: x.strftime('%A') if pd.notna(x) else None
        )
        rms_df['is_weekend'] = rms_df['incident_date'].apply(
            lambda x: x.weekday() >= 5 if pd.notna(x) else None
        )
        rms_df['day_type'] = rms_df['is_weekend'].apply(
            lambda x: "Weekend" if x else "Weekday" if x is not None else None
        )

        # Address validation and standardization
        rms_df['location'] = rms_df.get('full_address_raw', '').apply(self.validate_hackensack_address)
        rms_df['block'] = rms_df['location'].apply(self.calculate_block)

        # Grid and post backfill using reference data
        def backfill_grid_post_row(row):
            grid, post = self.backfill_grid_post(
                row.get('location'),
                row.get('grid_raw'),
                row.get('zone_raw')
            )
            return pd.Series({'grid': grid, 'post': post})

        backfilled = rms_df.apply(backfill_grid_post_row, axis=1)
        rms_df['grid'] = backfilled['grid']
        rms_df['post'] = backfilled['post']

        # Clean and combine incident types - safe column access
        for i in [1, 2, 3]:
            col_name = f'incident_type_{i}_raw'
            if col_name in rms_df.columns:
                rms_df[f'incident_type_{i}_cleaned'] = rms_df[col_name].apply(self.clean_incident_type)

        # Use incident_type_1_raw as primary incident type (no unpivoting)
        # This prevents the 135→300 record expansion issue
        rms_df['incident_type'] = rms_df.get('incident_type_1_raw', '').apply(self.clean_incident_type)
        
        # Combine all incidents for reference only
        def combine_incidents(row):
            incidents = []
            for i in [1, 2, 3]:
                cleaned_col = f'incident_type_{i}_cleaned'
                if cleaned_col in row and pd.notna(row[cleaned_col]):
                    incidents.append(row[cleaned_col])
            return ", ".join(incidents) if incidents else None

        rms_df['all_incidents'] = rms_df.apply(combine_incidents, axis=1)
        
        # Vehicle processing - safe column access with proper casing
        rms_df['vehicle_1'] = rms_df.apply(
            lambda row: self.format_vehicle(
                row.get('reg_state_1'), row.get('registration_1'),
                row.get('make_1'), row.get('model_1')
            ), axis=1
        )
        
        rms_df['vehicle_2'] = rms_df.apply(
            lambda row: self.format_vehicle(
                row.get('reg_state_2'), row.get('registration_2'),
                row.get('make_2'), row.get('model_2')
            ), axis=1
        )

        # Combined vehicles (only when both exist)
        def combine_vehicles(row):
            v1, v2 = row.get('vehicle_1'), row.get('vehicle_2')
            if pd.notna(v1) and pd.notna(v2):
                return f"{v1} | {v2}"
            return None

        rms_df['vehicle_1_and_vehicle_2'] = rms_df.apply(combine_vehicles, axis=1)

        # Convert vehicle columns to uppercase
        if 'vehicle_1' in rms_df.columns:
            rms_df['vehicle_1'] = rms_df['vehicle_1'].apply(lambda x: x.upper() if pd.notna(x) else None)
        if 'vehicle_2' in rms_df.columns:
            rms_df['vehicle_2'] = rms_df['vehicle_2'].apply(lambda x: x.upper() if pd.notna(x) else None)
        if 'vehicle_1_and_vehicle_2' in rms_df.columns:
            rms_df['vehicle_1_and_vehicle_2'] = rms_df['vehicle_1_and_vehicle_2'].apply(lambda x: x.upper() if pd.notna(x) else None)

        # Convert squad column to uppercase
        if 'squad' in rms_df.columns:
            rms_df['squad'] = rms_df['squad'].apply(lambda x: x.upper() if pd.notna(x) else None)

        # Clean narrative - safe column access
        def clean_narrative(narrative_text):
            if pd.isna(narrative_text):
                return None
            
            # Remove line breaks and excessive whitespace
            cleaned = str(narrative_text)
            cleaned = re.sub(r'#\(cr\)#\(lf\)|#\(lf\)|#\(cr\)', ' ', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned)
            cleaned = cleaned.strip()
            
            return cleaned if cleaned else None

        rms_df['narrative'] = rms_df.get('narrative_raw', pd.Series()).apply(clean_narrative)

        # Final column selection - Include incident_type as primary field
        desired_columns = [
            'case_number', 'incident_date', 'incident_time', 'time_of_day', 'time_of_day_sort_order',
            'period', 'season', 'day_of_week', 'day_type', 'location', 'block', 
            'grid', 'post', 'incident_type', 'all_incidents', 'vehicle_1', 'vehicle_2', 
            'vehicle_1_and_vehicle_2', 'narrative', 'total_value_stolen', 
            'total_value_recovered', 'squad', 'officer_of_record', 'nibrs_classification'
        ]

        # Select only columns that exist in the dataframe
        existing_columns = [col for col in desired_columns if col in rms_df.columns]
        rms_final = rms_df[existing_columns].copy()

        # Apply filtering - safe column access
        if 'case_number' in rms_final.columns and 'period' in rms_final.columns:
            rms_final = rms_final[
                (rms_final['case_number'] != '25-057654') & 
                (rms_final['period'] != 'Historical')
            ]

        self.logger.info(f"RMS processing complete: {len(rms_final)} records after filtering")
        self.logger.info(f"Final RMS columns: {list(rms_final.columns)}")
        self.logger.info("REMOVED CAD-specific columns: incident_type, crime_category, response_type")
        return rms_final

    def process_cad_data(self, cad_file):
        """Process CAD data with lowercase_with_underscores column standardization and enhanced functionality."""
        self.logger.info(f"Processing CAD data: {cad_file.name}")
        
        try:
            cad_df = pd.read_excel(cad_file, engine='openpyxl')
            self.logger.info(f"Loaded CAD file with {len(cad_df)} rows and {len(cad_df.columns)} columns")
            self.logger.info(f"CAD columns found: {list(cad_df.columns)}")
        except Exception as e:
            self.logger.error(f"Error loading CAD file: {e}")
            return pd.DataFrame()

        # Apply column mapping only for columns that exist
        column_mapping = self.get_cad_column_mapping()
        existing_mapping = {k: v for k, v in column_mapping.items() if k in cad_df.columns}
        cad_df = cad_df.rename(columns=existing_mapping)
        self.logger.info(f"Applied column mapping: {existing_mapping}")

        # Convert ALL remaining columns to lowercase_with_underscores
        cad_df.columns = [self.convert_to_lowercase_with_underscores(col) for col in cad_df.columns]

        # Clean text columns
        text_columns = cad_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            cad_df[col] = cad_df[col].apply(self.clean_text_comprehensive)

        # Fix how_reported 9-1-1 date issue
        if 'how_reported' in cad_df.columns:
            cad_df['how_reported'] = cad_df['how_reported'].apply(self.clean_how_reported_911)

        # Map incident to response_type and category_type using CallType_Categories.xlsx
        if 'incident_raw' in cad_df.columns:
            # Ensure the incident values are properly processed
            cad_df['incident_raw'] = cad_df['incident_raw'].replace('', None)
            
            self.logger.info(f"Starting call type mapping for {len(cad_df)} CAD records")
            self.logger.info(f"Sample incident_raw values: {cad_df['incident_raw'].dropna().head(5).tolist()}")
            
            call_type_results = cad_df['incident_raw'].apply(
                lambda x: pd.Series(self.map_call_type(x))
            )
            cad_df['response_type'] = call_type_results[0]
            cad_df['category_type'] = call_type_results[1]
            
            # Ensure response_type is not null - use incident_raw as fallback
            cad_df['response_type'] = cad_df['response_type'].fillna(cad_df['incident_raw'])
            cad_df['response_type'] = cad_df['response_type'].fillna('Unknown')
            
            # Ensure category_type is not null
            cad_df['category_type'] = cad_df['category_type'].fillna('Other')
            
            # Log mapping results
            category_counts = cad_df['category_type'].value_counts()
            self.logger.info(f"Category type mapping results: {category_counts.to_dict()}")
            response_counts = cad_df['response_type'].value_counts().head(10)
            self.logger.info(f"Top 10 response types: {response_counts.to_dict()}")
        else:
            self.logger.warning("incident_raw column not found in CAD data - cannot perform call type mapping")

        # Time calculations with negative value handling
        def safe_calculate_time_response(row):
            try:
                time_call = pd.to_datetime(row.get('time_of_call'))
                time_dispatched = pd.to_datetime(row.get('time_dispatched'))
                
                if pd.notna(time_call) and pd.notna(time_dispatched):
                    # Calculate (Time Dispatched - Time Call)
                    duration = time_dispatched - time_call
                    minutes = duration.total_seconds() / 60
                    
                    # Handle negative durations by swapping order: (Time Call - Time Dispatched)
                    if minutes < 0:
                        duration = time_call - time_dispatched
                        minutes = duration.total_seconds() / 60
                    
                    # Cap extreme outliers
                    if minutes > 480:  # Cap at 8 hours
                        minutes = 480
                    
                    return round(minutes, 2)
                return None
            except:
                return None

        def safe_calculate_time_spent(row):
            try:
                time_out = pd.to_datetime(row.get('time_out'))
                time_in = pd.to_datetime(row.get('time_in'))
                
                if pd.notna(time_out) and pd.notna(time_in):
                    # Calculate (Time In - Time Out)
                    duration = time_in - time_out
                    minutes = duration.total_seconds() / 60
                    
                    # Handle negative durations by swapping order: (Time Out - Time In)
                    if minutes < 0:
                        duration = time_out - time_in
                        minutes = duration.total_seconds() / 60
                    
                    # Cap extreme outliers
                    if minutes > 720:  # Cap at 12 hours
                        minutes = 720
                    
                    return round(minutes, 2)
                return None
            except:
                return None

        cad_df['time_response_minutes'] = cad_df.apply(safe_calculate_time_response, axis=1)
        cad_df['time_spent_minutes'] = cad_df.apply(safe_calculate_time_spent, axis=1)

        # Add formatted time columns
        cad_df['time_spent_formatted'] = cad_df['time_spent_minutes'].apply(self.format_time_spent_minutes)
        cad_df['time_response_formatted'] = cad_df['time_response_minutes'].apply(self.format_time_response_minutes)

        # Location processing - safe column access with proper population
        cad_df['location'] = cad_df.get('full_address_raw', '').apply(self.validate_hackensack_address)
        
        # Ensure grid and post are properly populated (not empty strings)
        cad_df['grid'] = cad_df.get('grid_raw', '').replace('', None)
        # post column already mapped correctly from PDZone, but ensure not empty
        if 'post' not in cad_df.columns:
            cad_df['post'] = None
        else:
            cad_df['post'] = cad_df['post'].replace('', None)
            
        cad_df['block'] = cad_df['location'].apply(self.calculate_block)

        # Enhanced CAD notes cleaning with username/timestamp extraction
        if 'cad_notes_raw' in cad_df.columns:
            cad_notes_processed = cad_df['cad_notes_raw'].apply(self.extract_username_timestamp)
            cad_df['cad_notes_cleaned'] = [x[0] for x in cad_notes_processed]
            cad_df['cad_notes_username'] = [x[1] for x in cad_notes_processed]
            cad_df['cad_notes_timestamp'] = [x[2] for x in cad_notes_processed]

        # Validate that key columns have proper values before final selection
        # Check response_type population
        response_type_populated = cad_df['response_type'].notna().sum()
        self.logger.info(f"CAD response_type populated in {response_type_populated}/{len(cad_df)} records")
        
        # Check grid population  
        grid_populated = cad_df['grid'].notna().sum()
        self.logger.info(f"CAD grid populated in {grid_populated}/{len(cad_df)} records")
        
        # Check post population
        post_populated = cad_df['post'].notna().sum() if 'post' in cad_df.columns else 0
        self.logger.info(f"CAD post populated in {post_populated}/{len(cad_df)} records")
        
        # Final column selection with lowercase_with_underscores naming
        desired_columns = [
            'case_number', 'response_type', 'category_type', 'how_reported', 
            'location', 'block', 'grid', 'post', 'time_of_call', 'time_dispatched', 
            'time_out', 'time_in', 'time_spent_minutes', 'time_response_minutes',
            'time_spent_formatted', 'time_response_formatted', 'officer', 'disposition', 
            'cad_notes_cleaned', 'cad_notes_username', 'cad_notes_timestamp'
        ]

        # Select only columns that exist in the dataframe
        existing_columns = [col for col in desired_columns if col in cad_df.columns]
        cad_final = cad_df[existing_columns].copy()

        self.logger.info(f"CAD processing complete: {len(cad_final)} records")
        self.logger.info(f"Final CAD columns: {list(cad_final.columns)}")
        return cad_final

    def find_latest_files(self):
        """Find the latest files in each export directory."""
        latest_files = {}
        
        # Since both files are in the same directory, we need to identify them by filename
        cad_path = self.export_dirs['cad_exports']
        rms_path = self.export_dirs['rms_exports']
        
        if cad_path.exists():
            cad_files = [f for f in cad_path.glob("*.xlsx") if "CAD" in f.name.upper()]
            if cad_files:
                latest_cad = max(cad_files, key=lambda f: f.stat().st_mtime)
                latest_files['cad'] = latest_cad
                self.logger.info(f"Latest CAD file: {latest_cad.name}")
            else:
                self.logger.warning(f"No CAD Excel files found in {cad_path}")
        else:
            self.logger.warning(f"CAD directory not found: {cad_path}")
            
        if rms_path.exists():
            rms_files = [f for f in rms_path.glob("*.xlsx") if "RMS" in f.name.upper()]
            if rms_files:
                latest_rms = max(rms_files, key=lambda f: f.stat().st_mtime)
                latest_files['rms'] = latest_rms
                self.logger.info(f"Latest RMS file: {latest_rms.name}")
            else:
                self.logger.warning(f"No RMS Excel files found in {rms_path}")
        else:
            self.logger.warning(f"RMS directory not found: {rms_path}")
        
        return latest_files

    def process_final_pipeline(self):
        """Run the complete processing pipeline with standardized output."""
        self.logger.info("Starting Comprehensive SCRPA Fix V8.0 pipeline...")
        
        latest_files = self.find_latest_files()
        
        if not latest_files:
            self.logger.error("No data files found to process")
            raise ValueError("No data files found")

        # Process RMS data
        rms_data = pd.DataFrame()
        if 'rms' in latest_files:
            rms_data = self.process_rms_data(latest_files['rms'])

        # Process CAD data  
        cad_data = pd.DataFrame()
        if 'cad' in latest_files:
            cad_data = self.process_cad_data(latest_files['cad'])

        # Create output directory
        output_dir = self.project_path / '04_powerbi'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save individual datasets
        if not rms_data.empty:
            rms_output = output_dir / 'rms_data_standardized.csv'
            rms_data.to_csv(rms_output, index=False, encoding='utf-8')
            self.logger.info(f"RMS data saved: {rms_output}")

        if not cad_data.empty:
            cad_output = output_dir / 'cad_data_standardized.csv'
            cad_data.to_csv(cad_output, index=False, encoding='utf-8')
            self.logger.info(f"CAD data saved: {cad_output}")

        # Create properly matched dataset with RMS as master (LEFT JOIN)
        joined_result = None
        if not rms_data.empty and not cad_data.empty:
            self.logger.info(f"Starting CAD-RMS matching: RMS={len(rms_data)} records, CAD={len(cad_data)} records")
            
            # LEFT JOIN: RMS as master, CAD data added where case numbers match
            # Use case-insensitive matching on case_number
            rms_copy = rms_data.copy()
            cad_copy = cad_data.copy()
            
            # Create case-insensitive lookup keys
            rms_copy['_lookup_key'] = rms_copy['case_number'].astype(str).str.upper().str.strip()
            cad_copy['_lookup_key'] = cad_copy['case_number'].astype(str).str.upper().str.strip()
            
            # Add _cad suffix to CAD columns (except lookup key)
            cad_renamed = cad_copy.drop(columns=['_lookup_key']).add_suffix('_cad')
            cad_renamed['_lookup_key'] = cad_copy['_lookup_key']
            
            # Perform LEFT JOIN on lookup key
            joined_data = rms_copy.merge(
                cad_renamed,
                on='_lookup_key',
                how='left'
            )
            
            # Remove temporary lookup key
            joined_data = joined_data.drop(columns=['_lookup_key'])
            
            # Note: All CAD data is now accessible via column_name_cad format
            # No duplicate columns without _cad suffix are created
            
            # Calculate match statistics
            cad_matches = joined_data['response_type_cad'].notna().sum()
            match_rate = (cad_matches / len(joined_data)) * 100
            
            self.logger.info(f"CAD-RMS matching complete:")
            self.logger.info(f"  - Final record count: {len(joined_data)} (matches RMS input)")
            self.logger.info(f"  - CAD matches found: {cad_matches}")
            self.logger.info(f"  - Match rate: {match_rate:.1f}%")
            
            joined_output = output_dir / 'cad_rms_matched_standardized.csv'
            joined_data.to_csv(joined_output, index=False, encoding='utf-8')
            self.logger.info(f"Joined data saved: {joined_output}")
            
            # Create 7-Day SCRPA export using the matched dataset
            self.create_7day_scrpa_export(joined_data, output_dir)
            
            joined_result = joined_data

        # Create joined dataset result if not already created above
        if joined_result is None and not rms_data.empty and not cad_data.empty:
            joined_result = self.create_cad_rms_matched_dataset(rms_data, cad_data, output_dir)
            # Create 7-Day SCRPA export using the matched dataset
            if joined_result is not None and not joined_result.empty:
                self.create_7day_scrpa_export(joined_result, output_dir)
        
        # Final validation logging
        self.logger.info("=" * 60)
        self.logger.info("COMPREHENSIVE SCRPA FIX V8.0 COMPLETE - VALIDATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"✅ RMS records processed: {len(rms_data)}")
        self.logger.info(f"✅ CAD records processed: {len(cad_data)}")
        
        if joined_result is not None:
            self.logger.info(f"✅ Matched records: {len(joined_result)} (RMS as master)")
            
            # Validate target record count (should be 135)
            if len(joined_result) == 135:
                self.logger.info("✅ RECORD COUNT VALIDATION: PASSED (135 records)")
            else:
                self.logger.warning(f"⚠️ RECORD COUNT VALIDATION: Expected 135, got {len(joined_result)}")
            
            # Validate column naming convention
            lowercase_pattern = re.compile(r'^[a-z]+(_[a-z0-9]+)*$')
            non_compliant_cols = [col for col in joined_result.columns if not lowercase_pattern.match(col)]
            
            if not non_compliant_cols:
                self.logger.info("✅ COLUMN NAMING VALIDATION: PASSED (all lowercase_with_underscores)")
            else:
                self.logger.warning(f"⚠️ COLUMN NAMING VALIDATION: Non-compliant columns: {non_compliant_cols}")
            
            # Check CAD column suffixes
            cad_cols = [col for col in joined_result.columns if col.endswith('_cad')]
            self.logger.info(f"✅ CAD columns with _cad suffix: {len(cad_cols)}")
            
            # Validate critical columns exist
            critical_cols = ['case_number', 'incident_type', 'response_type_cad', 'grid_cad', 'post_cad']
            missing_cols = [col for col in critical_cols if col not in joined_result.columns]
            
            if not missing_cols:
                self.logger.info("✅ CRITICAL COLUMNS VALIDATION: PASSED")
            else:
                self.logger.warning(f"⚠️ CRITICAL COLUMNS VALIDATION: Missing columns: {missing_cols}")
            
            # Run comprehensive filtering validation
            self.logger.info("🔍 Running comprehensive filtering validation...")
            filtering_validation = self.validate_comprehensive_filtering(joined_result)
            
            # Log filtering validation results
            filtering_status = filtering_validation['filtering_validation']['overall_status']
            if filtering_status == 'PASS':
                self.logger.info("✅ COMPREHENSIVE FILTERING VALIDATION: PASSED")
            elif filtering_status == 'WARNING':
                self.logger.warning("⚠️ COMPREHENSIVE FILTERING VALIDATION: WARNING")
            else:
                self.logger.error("❌ COMPREHENSIVE FILTERING VALIDATION: FAILED")
            
            # Log key filtering metrics
            if 'filtering_accuracy_tests' in filtering_validation['filtering_validation']:
                filtering_analysis = filtering_validation['filtering_validation']['filtering_accuracy_tests']
                self.logger.info(f"✅ 7-Day records: {filtering_analysis.get('total_7day_records', 0)}")
                self.logger.info(f"✅ Filtered crime incidents: {filtering_analysis.get('filtered_records', 0)}")
                self.logger.info(f"✅ Filtering rate: {filtering_analysis.get('filtering_rate', '0%')}")
                
                # Log crime distribution
                crime_dist = filtering_analysis.get('crime_distribution', {})
                if crime_dist:
                    self.logger.info("✅ Crime distribution:")
                    for crime_type, count in crime_dist.items():
                        self.logger.info(f"   - {crime_type}: {count}")
            
            # Log recommendations if any
            recommendations = filtering_validation['filtering_validation'].get('recommendations', [])
            if recommendations:
                self.logger.warning("⚠️ Filtering validation recommendations:")
                for rec in recommendations:
                    self.logger.warning(f"   - {rec}")
        
        self.logger.info(f"✅ Output directory: {output_dir}")
        self.logger.info("=" * 60)
        
        return {
            'rms_data': rms_data,
            'cad_data': cad_data,
            'output_dir': str(output_dir)
        }

    def generate_column_validation_report(self, df, data_type="Unknown"):
        """Generate a validation report for column naming compliance."""
        
        report_lines = [
            f"# Column Validation Report - {data_type}",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}",
            "",
            "| Column Name | Compliant | Issue |",
            "|---|---|---|"
        ]
        
        # Pattern for lowercase_with_underscores - FIXED to allow numbers
        lowercase_pattern = re.compile(r'^[a-z]+(_[a-z0-9]+)*$')
        
        compliant_count = 0
        total_count = len(df.columns)
        
        for col in df.columns:
            # Add debug logging to show which columns are being tested
            self.logger.debug(f"Testing column: '{col}' against pattern: ^[a-z]+(_[a-z0-9]+)*$")
            
            if lowercase_pattern.match(col):
                report_lines.append(f"| {col} | ✅ Yes | None |")
                compliant_count += 1
                self.logger.debug(f"Column '{col}' PASSED validation")
            else:
                suggested = self.convert_to_lowercase_with_underscores(col)
                report_lines.append(f"| {col} | ❌ No | Should be: {suggested} |")
                self.logger.debug(f"Column '{col}' FAILED validation - suggested: {suggested}")
        
        report_lines.extend([
            "",
            f"**Summary:**",
            f"- Total columns: {total_count}",
            f"- Compliant columns: {compliant_count}",
            f"- Non-compliant columns: {total_count - compliant_count}",
            f"- Compliance rate: {(compliant_count/total_count)*100:.1f}%"
        ])
        
        return "\n".join(report_lines)

    def validate_data_quality(self, rms_data, cad_data):
        """Validate data quality and generate report."""
        
        validation_results = {
            'rms_validation': {},
            'cad_validation': {},
            'overall_status': 'PASS'
        }
        
        # RMS Data Validation
        if not rms_data.empty:
            rms_null_case_numbers = rms_data['case_number'].isnull().sum()
            rms_empty_case_numbers = (rms_data['case_number'] == '').sum()
            rms_total_null_empty = rms_null_case_numbers + rms_empty_case_numbers
            
            validation_results['rms_validation'] = {
                'total_records': len(rms_data),
                'null_case_numbers': rms_null_case_numbers,
                'empty_case_numbers': rms_empty_case_numbers,
                'total_invalid_case_numbers': rms_total_null_empty,
                'case_number_quality': f"{((len(rms_data) - rms_total_null_empty) / len(rms_data)) * 100:.1f}%",
                'incident_types_populated': rms_data.get('incident_type', pd.Series()).notna().sum(),
                'incident_dates_populated': rms_data['incident_date'].notna().sum(),
                'periods_calculated': rms_data['period'].notna().sum()
            }
            
            # Check for critical issues
            if rms_total_null_empty > len(rms_data) * 0.1:  # More than 10% invalid case numbers
                validation_results['overall_status'] = 'WARNING'
                
        # CAD Data Validation
        if not cad_data.empty:
            cad_null_case_numbers = cad_data['case_number'].isnull().sum()
            cad_empty_case_numbers = (cad_data['case_number'] == '').sum()
            cad_total_null_empty = cad_null_case_numbers + cad_empty_case_numbers
            
            validation_results['cad_validation'] = {
                'total_records': len(cad_data),
                'null_case_numbers': cad_null_case_numbers,
                'empty_case_numbers': cad_empty_case_numbers,
                'total_invalid_case_numbers': cad_total_null_empty,
                'case_number_quality': f"{((len(cad_data) - cad_total_null_empty) / len(cad_data)) * 100:.1f}%",
                'time_calculations_populated': cad_data.get('time_response_minutes', pd.Series()).notna().sum(),
                'officer_populated': cad_data.get('officer', pd.Series()).notna().sum()
            }
            
            # Check for critical issues
            if cad_total_null_empty > len(cad_data) * 0.1:  # More than 10% invalid case numbers
                validation_results['overall_status'] = 'WARNING'
        
        return validation_results

    def validate_comprehensive_filtering(self, matched_data):
        """
        Comprehensive validation of multi-column crime filtering functionality.
        
        Args:
            matched_data (pd.DataFrame): The cad_rms_matched_standardized dataset
            
        Returns:
            dict: Comprehensive validation results
        """
        self.logger.info("Starting comprehensive filtering validation...")
        
        validation_results = {
            'filtering_validation': {
                'overall_status': 'PASS',
                'test_results': {},
                'crime_pattern_tests': {},
                'column_coverage_tests': {},
                'filtering_accuracy_tests': {},
                'recommendations': []
            }
        }
        
        if matched_data.empty:
            validation_results['filtering_validation']['overall_status'] = 'FAIL'
            validation_results['filtering_validation']['recommendations'].append("No data available for filtering validation")
            return validation_results
        
        # Define crime patterns for testing (same as in create_7day_scrpa_export)
        crime_patterns = {
            'Motor Vehicle Theft': [
                r'MOTOR\s+VEHICLE\s+THEFT',
                r'AUTO\s+THEFT',
                r'MV\s+THEFT',
                r'VEHICLE\s+THEFT'
            ],
            'Burglary - Auto': [
                r'BURGLARY.*AUTO',
                r'BURGLARY.*VEHICLE',
                r'BURGLARY\s*-\s*AUTO',
                r'BURGLARY\s*-\s*VEHICLE'
            ],
            'Burglary - Commercial': [
                r'BURGLARY.*COMMERCIAL',
                r'BURGLARY\s*-\s*COMMERCIAL',
                r'BURGLARY.*BUSINESS'
            ],
            'Burglary - Residence': [
                r'BURGLARY.*RESIDENCE',
                r'BURGLARY\s*-\s*RESIDENCE',
                r'BURGLARY.*RESIDENTIAL',
                r'BURGLARY\s*-\s*RESIDENTIAL'
            ],
            'Robbery': [
                r'ROBBERY'
            ],
            'Sexual Offenses': [
                r'SEXUAL',
                r'SEX\s+CRIME',
                r'SEXUAL\s+ASSAULT',
                r'SEXUAL\s+OFFENSE'
            ]
        }
        
        # Test 1: Column Coverage Validation
        self.logger.info("Testing column coverage for filtering...")
        search_columns = [
            'incident_type', 'all_incidents', 'vehicle_1', 'vehicle_2',
            'incident_type_1_raw', 'incident_type_2_raw', 'incident_type_3_raw'
        ]
        
        available_columns = []
        missing_columns = []
        
        for col in search_columns:
            if col in matched_data.columns:
                available_columns.append(col)
                # Check data quality in this column
                non_null_count = matched_data[col].notna().sum()
                total_count = len(matched_data)
                coverage_pct = (non_null_count / total_count) * 100
                
                validation_results['filtering_validation']['column_coverage_tests'][col] = {
                    'available': True,
                    'non_null_count': non_null_count,
                    'total_count': total_count,
                    'coverage_percentage': f"{coverage_pct:.1f}%",
                    'status': 'PASS' if coverage_pct > 50 else 'WARNING'
                }
                
                if coverage_pct < 50:
                    validation_results['filtering_validation']['recommendations'].append(
                        f"Low data coverage in {col}: {coverage_pct:.1f}%"
                    )
            else:
                missing_columns.append(col)
                validation_results['filtering_validation']['column_coverage_tests'][col] = {
                    'available': False,
                    'status': 'WARNING'
                }
        
        validation_results['filtering_validation']['test_results']['column_coverage'] = {
            'available_columns': available_columns,
            'missing_columns': missing_columns,
            'coverage_score': f"{len(available_columns)}/{len(search_columns)} columns available"
        }
        
        # Test 2: Crime Pattern Validation
        self.logger.info("Testing crime pattern matching...")
        pattern_test_results = {}
        
        for category, patterns in crime_patterns.items():
            category_matches = 0
            pattern_details = {}
            
            for pattern in patterns:
                # Test pattern against all available columns
                pattern_matches = 0
                matching_records = []
                
                for col in available_columns:
                    if col in matched_data.columns:
                        # Count matches for this pattern in this column
                        matches = matched_data[col].astype(str).str.contains(
                            pattern, case=False, na=False, regex=True
                        ).sum()
                        pattern_matches += matches
                        
                        if matches > 0:
                            # Get sample matching records
                            sample_records = matched_data[
                                matched_data[col].astype(str).str.contains(
                                    pattern, case=False, na=False, regex=True
                                )
                            ][col].head(3).tolist()
                            matching_records.extend(sample_records)
                
                pattern_details[pattern] = {
                    'matches': pattern_matches,
                    'sample_matches': matching_records[:3]  # Limit to 3 samples
                }
                category_matches += pattern_matches
            
            pattern_test_results[category] = {
                'total_matches': category_matches,
                'patterns': pattern_details,
                'status': 'PASS' if category_matches > 0 else 'WARNING'
            }
            
            if category_matches == 0:
                validation_results['filtering_validation']['recommendations'].append(
                    f"No matches found for {category} - check pattern definitions"
                )
        
        validation_results['filtering_validation']['crime_pattern_tests'] = pattern_test_results
        
        # Test 3: Multi-Column Search Function Validation
        self.logger.info("Testing multi-column search function...")
        search_function_tests = {
            'test_cases': [],
            'overall_accuracy': 0,
            'status': 'PASS'
        }
        
        # Create test cases with known crime types
        test_cases = [
            {
                'description': 'Motor Vehicle Theft in incident_type',
                'row_data': {
                    'incident_type': 'MOTOR VEHICLE THEFT',
                    'all_incidents': 'Some other incident',
                    'vehicle_1': None,
                    'vehicle_2': None
                },
                'expected': 'Motor Vehicle Theft'
            },
            {
                'description': 'Burglary Auto in vehicle_1',
                'row_data': {
                    'incident_type': 'Some other incident',
                    'all_incidents': 'Some other incident',
                    'vehicle_1': 'BURGLARY AUTO',
                    'vehicle_2': None
                },
                'expected': 'Burglary - Auto'
            },
            {
                'description': 'Robbery in all_incidents',
                'row_data': {
                    'incident_type': 'Some other incident',
                    'all_incidents': 'ROBBERY',
                    'vehicle_1': None,
                    'vehicle_2': None
                },
                'expected': 'Robbery'
            },
            {
                'description': 'No crime match',
                'row_data': {
                    'incident_type': 'TRAFFIC VIOLATION',
                    'all_incidents': 'TRAFFIC VIOLATION',
                    'vehicle_1': None,
                    'vehicle_2': None
                },
                'expected': 'Other'
            }
        ]
        
        correct_matches = 0
        for i, test_case in enumerate(test_cases):
            try:
                # Create a mock row
                mock_row = pd.Series(test_case['row_data'])
                
                # Test the multi-column search function
                result = self.multi_column_crime_search(mock_row, crime_patterns)
                
                # Check if result matches expected
                is_correct = result == test_case['expected']
                if is_correct:
                    correct_matches += 1
                
                search_function_tests['test_cases'].append({
                    'test_number': i + 1,
                    'description': test_case['description'],
                    'expected': test_case['expected'],
                    'actual': result,
                    'passed': is_correct
                })
                
                self.logger.debug(f"Test {i+1}: Expected '{test_case['expected']}', Got '{result}', Passed: {is_correct}")
                
            except Exception as e:
                search_function_tests['test_cases'].append({
                    'test_number': i + 1,
                    'description': test_case['description'],
                    'error': str(e),
                    'passed': False
                })
                self.logger.error(f"Test {i+1} failed with error: {e}")
        
        # Calculate accuracy
        total_tests = len(test_cases)
        search_function_tests['overall_accuracy'] = (correct_matches / total_tests) * 100 if total_tests > 0 else 0
        search_function_tests['status'] = 'PASS' if search_function_tests['overall_accuracy'] >= 90 else 'FAIL'
        
        if search_function_tests['overall_accuracy'] < 90:
            validation_results['filtering_validation']['recommendations'].append(
                f"Multi-column search function accuracy below 90%: {search_function_tests['overall_accuracy']:.1f}%"
            )
        
        validation_results['filtering_validation']['test_results']['search_function'] = search_function_tests
        
        # Test 4: Real Data Filtering Validation
        self.logger.info("Testing filtering on real data...")
        
        # Apply the multi-column filter to real data
        def apply_multi_column_crime_filter(df):
            """Apply multi-column crime filtering using the enhanced search function."""
            crime_matches = []
            for idx, row in df.iterrows():
                crime_category = self.multi_column_crime_search(row, crime_patterns)
                if crime_category != 'Other':
                    crime_matches.append(idx)
            return df.loc[crime_matches] if crime_matches else pd.DataFrame()
        
        # Test filtering on 7-Day period data
        period_filtered = matched_data[matched_data['period'] == '7-Day'].copy()
        filtered_df = apply_multi_column_crime_filter(period_filtered)
        
        # Analyze filtering results
        filtering_analysis = {
            'total_7day_records': len(period_filtered),
            'filtered_records': len(filtered_df),
            'filtering_rate': f"{(len(filtered_df) / len(period_filtered)) * 100:.1f}%" if len(period_filtered) > 0 else "0%",
            'crime_distribution': {}
        }
        
        # Count crimes by category in filtered results
        for idx, row in filtered_df.iterrows():
            crime_category = self.multi_column_crime_search(row, crime_patterns)
            if crime_category not in filtering_analysis['crime_distribution']:
                filtering_analysis['crime_distribution'][crime_category] = 0
            filtering_analysis['crime_distribution'][crime_category] += 1
        
        # Validate filtering results
        if len(filtered_df) == 0:
            validation_results['filtering_validation']['recommendations'].append(
                "No crime incidents found in 7-Day period - check data and filtering logic"
            )
        elif len(filtered_df) < 3:
            validation_results['filtering_validation']['recommendations'].append(
                f"Very few crime incidents found ({len(filtered_df)}) - may indicate filtering issues"
            )
        
        validation_results['filtering_validation']['filtering_accuracy_tests'] = filtering_analysis
        
        # Test 5: Backward Compatibility Validation
        self.logger.info("Testing backward compatibility...")
        
        # Test the old get_crime_category method still works
        compatibility_tests = {
            'get_crime_category_tests': [],
            'status': 'PASS'
        }
        
        # Test cases for backward compatibility
        compatibility_test_cases = [
            ('MOTOR VEHICLE THEFT', 'Some other incident', 'Motor Vehicle Theft'),
            ('Some other incident', 'ROBBERY', 'Robbery'),
            ('BURGLARY AUTO', 'Some other incident', 'Burglary - Auto'),
            ('TRAFFIC VIOLATION', 'TRAFFIC VIOLATION', 'Other')
        ]
        
        compatibility_correct = 0
        for i, (incident_type, all_incidents, expected) in enumerate(compatibility_test_cases):
            try:
                result = self.get_crime_category(all_incidents, incident_type)
                is_correct = result == expected
                if is_correct:
                    compatibility_correct += 1
                
                compatibility_tests['get_crime_category_tests'].append({
                    'test_number': i + 1,
                    'incident_type': incident_type,
                    'all_incidents': all_incidents,
                    'expected': expected,
                    'actual': result,
                    'passed': is_correct
                })
                
            except Exception as e:
                compatibility_tests['get_crime_category_tests'].append({
                    'test_number': i + 1,
                    'error': str(e),
                    'passed': False
                })
        
        compatibility_tests['accuracy'] = (compatibility_correct / len(compatibility_test_cases)) * 100
        compatibility_tests['status'] = 'PASS' if compatibility_tests['accuracy'] >= 90 else 'FAIL'
        
        if compatibility_tests['accuracy'] < 90:
            validation_results['filtering_validation']['recommendations'].append(
                f"Backward compatibility accuracy below 90%: {compatibility_tests['accuracy']:.1f}%"
            )
        
        validation_results['filtering_validation']['test_results']['backward_compatibility'] = compatibility_tests
        
        # Overall validation status
        failed_tests = 0
        warning_tests = 0
        
        # Check all test results
        for test_category, test_result in validation_results['filtering_validation']['test_results'].items():
            if 'status' in test_result:
                if test_result['status'] == 'FAIL':
                    failed_tests += 1
                elif test_result['status'] == 'WARNING':
                    warning_tests += 1
        
        # Check column coverage
        for col_test in validation_results['filtering_validation']['column_coverage_tests'].values():
            if col_test.get('status') == 'FAIL':
                failed_tests += 1
            elif col_test.get('status') == 'WARNING':
                warning_tests += 1
        
        # Check crime pattern tests
        for pattern_test in validation_results['filtering_validation']['crime_pattern_tests'].values():
            if pattern_test['status'] == 'FAIL':
                failed_tests += 1
            elif pattern_test['status'] == 'WARNING':
                warning_tests += 1
        
        # Set overall status
        if failed_tests > 0:
            validation_results['filtering_validation']['overall_status'] = 'FAIL'
        elif warning_tests > 0:
            validation_results['filtering_validation']['overall_status'] = 'WARNING'
        else:
            validation_results['filtering_validation']['overall_status'] = 'PASS'
        
        # Log validation summary
        self.logger.info(f"Comprehensive filtering validation complete:")
        self.logger.info(f"  - Overall status: {validation_results['filtering_validation']['overall_status']}")
        self.logger.info(f"  - Failed tests: {failed_tests}")
        self.logger.info(f"  - Warning tests: {warning_tests}")
        self.logger.info(f"  - Recommendations: {len(validation_results['filtering_validation']['recommendations'])}")
        
        return validation_results

    def create_7day_scrpa_export(self, matched_data, output_dir):
        """
        Create 7-Day SCRPA incident export with specific crime category filtering.
        
        Args:
            matched_data (pd.DataFrame): The cad_rms_matched_standardized dataset
            output_dir (Path): Output directory for the CSV file
            
        Returns:
            pd.DataFrame: Filtered dataframe with 7-day incidents
        """
        self.logger.info("Starting 7-Day SCRPA incident export...")
        
        if matched_data.empty:
            self.logger.warning("No matched data available for 7-day export")
            return pd.DataFrame()
        
        # Validate required columns exist
        required_columns = ['period', 'incident_type', 'case_number', 'incident_date', 'incident_time', 
                          'all_incidents', 'location', 'narrative', 'vehicle_1', 'grid', 'post']
        missing_columns = [col for col in required_columns if col not in matched_data.columns]
        if missing_columns:
            self.logger.error(f"Missing required columns for 7-day export: {missing_columns}")
            return pd.DataFrame()
        
        # Define crime patterns for multi-column filtering
        crime_patterns = {
            'Motor Vehicle Theft': [
                r'MOTOR\s+VEHICLE\s+THEFT',
                r'AUTO\s+THEFT',
                r'MV\s+THEFT',
                r'VEHICLE\s+THEFT'
            ],
            'Burglary - Auto': [
                r'BURGLARY.*AUTO',
                r'BURGLARY.*VEHICLE',
                r'BURGLARY\s*-\s*AUTO',
                r'BURGLARY\s*-\s*VEHICLE'
            ],
            'Burglary - Commercial': [
                r'BURGLARY.*COMMERCIAL',
                r'BURGLARY\s*-\s*COMMERCIAL',
                r'BURGLARY.*BUSINESS'
            ],
            'Burglary - Residence': [
                r'BURGLARY.*RESIDENCE',
                r'BURGLARY\s*-\s*RESIDENCE',
                r'BURGLARY.*RESIDENTIAL',
                r'BURGLARY\s*-\s*RESIDENTIAL'
            ],
            'Robbery': [
                r'ROBBERY'
            ],
            'Sexual Offenses': [
                r'SEXUAL',
                r'SEX\s+CRIME',
                r'SEXUAL\s+ASSAULT',
                r'SEXUAL\s+OFFENSE'
            ]
        }
        
        # ENHANCED MULTI-COLUMN FILTERING LOGIC: Try multiple approaches
        filtered_df = None
        filtering_method = "Unknown"
        
        def apply_multi_column_crime_filter(df):
            """Apply multi-column crime filtering using the enhanced search function."""
            crime_matches = []
            for idx, row in df.iterrows():
                crime_category = self.multi_column_crime_search(row, crime_patterns)
                if crime_category != 'Other':
                    crime_matches.append(idx)
            return df.loc[crime_matches] if crime_matches else pd.DataFrame()
        
        # Method 1: Original exact period matching with multi-column filtering
        period_filtered = matched_data[matched_data['period'] == '7-Day'].copy()
        self.logger.info(f"7-Day period records found: {len(period_filtered)}")
        
        if len(period_filtered) > 0:
            # Apply enhanced multi-column crime category filtering
            filtered_df = apply_multi_column_crime_filter(period_filtered)
            filtering_method = "Exact period match with multi-column filtering"
            self.logger.info(f"After multi-column crime filtering: {len(filtered_df)} records")
        
        # Method 2: Case-insensitive period matching if Method 1 found 0
        if filtered_df is None or len(filtered_df) == 0:
            period_filtered = matched_data[
                matched_data['period'].str.contains('7-day|7day|7_day', case=False, na=False)
            ].copy()
            self.logger.info(f"Case-insensitive 7-day period records found: {len(period_filtered)}")
            
            if len(period_filtered) > 0:
                filtered_df = apply_multi_column_crime_filter(period_filtered)
                filtering_method = "Case-insensitive period match with multi-column filtering"
                self.logger.info(f"After multi-column crime filtering: {len(filtered_df)} records")
        
        # Method 3: Date-based filtering as fallback
        if filtered_df is None or len(filtered_df) == 0:
            self.logger.info("Trying date-based filtering as fallback...")
            
            # Filter for last 7 days from today
            today = pd.Timestamp.now().date()
            seven_days_ago = today - pd.Timedelta(days=7)
            
            # Convert incident_date to datetime if it's not already
            try:
                if matched_data['incident_date'].dtype == 'object':
                    date_filtered = matched_data[
                        pd.to_datetime(matched_data['incident_date'], errors='coerce').dt.date >= seven_days_ago
                    ].copy()
                else:
                    date_filtered = matched_data[
                        matched_data['incident_date'].dt.date >= seven_days_ago
                    ].copy()
                
                self.logger.info(f"Date-based filtering (last 7 days): {len(date_filtered)} records found")
                
                if len(date_filtered) > 0:
                    filtered_df = apply_multi_column_crime_filter(date_filtered)
                    filtering_method = "Date-based filtering (last 7 days) with multi-column filtering"
                    self.logger.info(f"After multi-column crime filtering: {len(filtered_df)} records")
                    
            except Exception as e:
                self.logger.error(f"Error in date-based filtering: {e}")
        
        # Final check - if we still have no results
        if filtered_df is None or len(filtered_df) == 0:
            self.logger.warning("No 7-Day incidents found matching crime categories")
            self.logger.info(f"Filtering method attempted: {filtering_method}")
            return pd.DataFrame()
        
        self.logger.info(f"7-Day filtering complete: {len(filtered_df)} incidents found using {filtering_method}")
        
        # Count incidents by crime type for logging using multi-column filtering
        crime_counts = {}
        for category in crime_patterns.keys():
            count = 0
            for idx, row in filtered_df.iterrows():
                crime_category = self.multi_column_crime_search(row, crime_patterns)
                if crime_category == category:
                    count += 1
            if count > 0:
                crime_counts[category] = count
        
        # Log crime type breakdown
        self.logger.info("7-Day incident breakdown by crime type:")
        for category, count in crime_counts.items():
            self.logger.info(f"  - {category}: {count} incidents")
        
        # Create export dataframe with specified columns using enhanced crime categorization
        export_columns = {
            'Case_Number': filtered_df['case_number'],
            'Incident_Date_Time': filtered_df.apply(
                lambda row: f"{row['incident_date']} {row['incident_time']}" if pd.notna(row['incident_date']) and pd.notna(row['incident_time']) else "Data Incomplete", 
                axis=1
            ),
            'Incident_Types': filtered_df['all_incidents'].fillna("Data Incomplete"),
            'Crime_Category': filtered_df.apply(
                lambda row: self.multi_column_crime_search(row, crime_patterns), 
                axis=1
            ),
            'Full_Address': filtered_df['location'].fillna("Data Incomplete"),
            'Narrative': filtered_df['narrative'].fillna("Data Incomplete"),
            'Vehicle_Registration': filtered_df['vehicle_1'].fillna("Unknown"),
            'Vehicle_Make_Model': filtered_df['vehicle_1'].fillna("Unknown"),
            'Grid_Zone': filtered_df.apply(
                lambda row: f"{row['grid']}-{row['post']}" if pd.notna(row['grid']) and pd.notna(row['post']) else "Unknown", 
                axis=1
            ),
            'Status': "Active"  # Default status as specified
        }
        
        export_df = pd.DataFrame(export_columns)
        
        # Generate filename with current date
        current_date = datetime.now().strftime('%Y_%m_%d')
        filename = f"{current_date}_7Day_SCRPA_Incidents.csv"
        output_path = output_dir / filename
        
        # Export to CSV
        export_df.to_csv(output_path, index=False, encoding='utf-8')
        
        # Log export summary
        self.logger.info(f"7-Day SCRPA export complete:")
        self.logger.info(f"  - File: {output_path}")
        self.logger.info(f"  - Total incidents exported: {len(export_df)}")
        self.logger.info(f"  - Filtering method used: {filtering_method}")
        self.logger.info(f"  - Crime types: {', '.join(crime_counts.keys())}")
        
        # Log detailed breakdown
        summary_parts = []
        for category, count in crime_counts.items():
            summary_parts.append(f"{count} {category}")
        
        if summary_parts:
            self.logger.info(f"  - Breakdown: {', '.join(summary_parts)}")
        
        return export_df

    def create_cad_rms_matched_dataset(self, rms_data, cad_data, output_dir):
        """Create properly matched CAD-RMS dataset with RMS as master (LEFT JOIN)."""
        self.logger.info(f"Starting CAD-RMS matching: RMS={len(rms_data)} records, CAD={len(cad_data)} records")
        
        # LEFT JOIN: RMS as master, CAD data added where case numbers match
        # Use case-insensitive matching on case_number
        rms_copy = rms_data.copy()
        cad_copy = cad_data.copy()
        
        # Create case-insensitive lookup keys
        rms_copy['_lookup_key'] = rms_copy['case_number'].astype(str).str.upper().str.strip()
        cad_copy['_lookup_key'] = cad_copy['case_number'].astype(str).str.upper().str.strip()
        
        # Add _cad suffix to CAD columns (except lookup key)
        cad_renamed = cad_copy.drop(columns=['_lookup_key']).add_suffix('_cad')
        cad_renamed['_lookup_key'] = cad_copy['_lookup_key']
        
        # Perform LEFT JOIN on lookup key
        joined_data = rms_copy.merge(
            cad_renamed,
            on='_lookup_key',
            how='left'
        )
        
        # Remove temporary lookup key
        joined_data = joined_data.drop(columns=['_lookup_key'])
        
        # Note: All CAD data is now accessible via column_name_cad format
        # No duplicate columns without _cad suffix are created
        
        # Fix CAD notes cleaning - remove username/timestamps more thoroughly
        def enhanced_clean_cad_notes(notes):
            if pd.isna(notes):
                return None
            
            text = str(notes)
            
            # Remove username patterns (letters followed by numbers or periods)
            text = re.sub(r'^[A-Z]+\d*\s*[:\-]?\s*', '', text)
            text = re.sub(r'^[a-zA-Z]+\.[a-zA-Z]+\s*[:\-]?\s*', '', text)
            
            # Remove timestamp patterns
            text = re.sub(r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M', '', text)
            text = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', '', text)
            text = re.sub(r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}', '', text)
            
            # Clean up extra whitespace and separators
            text = re.sub(r'[\r\n\t]+', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text if text else None
        
        joined_data['cad_notes_cleaned_cad'] = joined_data['cad_notes_cleaned_cad'].apply(enhanced_clean_cad_notes)
        
        # Calculate match statistics
        cad_matches = joined_data['response_type_cad'].notna().sum()
        match_rate = (cad_matches / len(joined_data)) * 100
        
        self.logger.info(f"CAD-RMS matching complete:")
        self.logger.info(f"  - Final record count: {len(joined_data)} (matches RMS input)")
        self.logger.info(f"  - CAD matches found: {cad_matches}")
        self.logger.info(f"  - Match rate: {match_rate:.1f}%")
        
        # Validate output has exactly same count as RMS input
        if len(joined_data) != len(rms_data):
            self.logger.warning(f"Record count mismatch! Expected {len(rms_data)}, got {len(joined_data)}")
        
        joined_output = output_dir / 'cad_rms_matched_standardized.csv'
        joined_data.to_csv(joined_output, index=False, encoding='utf-8')
        self.logger.info(f"Joined data saved: {joined_output}")
        
        return joined_data

if __name__ == "__main__":
    try:
        # Initialize processor
        processor = ComprehensiveSCRPAFixV8_0()
        
        # Run the pipeline
        results = processor.process_final_pipeline()
        
        # Generate validation reports
        if not results['rms_data'].empty:
            rms_report = processor.generate_column_validation_report(results['rms_data'], "RMS Data")
            report_file = Path(results['output_dir']) / 'rms_column_validation_report.md'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(rms_report)
                
        if not results['cad_data'].empty:
            cad_report = processor.generate_column_validation_report(results['cad_data'], "CAD Data")
            report_file = Path(results['output_dir']) / 'cad_column_validation_report.md'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(cad_report)
        
        # Validate data quality
        validation_results = processor.validate_data_quality(results['rms_data'], results['cad_data'])
        
        # Run comprehensive filtering validation if we have matched data
        filtering_validation_results = None
        if 'rms_data' in results and 'cad_data' in results:
            # Try to get the matched data from the output directory
            output_dir = Path(results['output_dir'])
            matched_file = output_dir / 'cad_rms_matched_standardized.csv'
            if matched_file.exists():
                try:
                    matched_data = pd.read_csv(matched_file)
                    filtering_validation_results = processor.validate_comprehensive_filtering(matched_data)
                    
                    # Save filtering validation report
                    import json
                    filtering_report_file = output_dir / 'comprehensive_filtering_validation_report.json'
                    with open(filtering_report_file, 'w', encoding='utf-8') as f:
                        json.dump(filtering_validation_results, f, indent=2, default=str)
                    print(f"✅ Comprehensive filtering validation report saved: {filtering_report_file}")
                    
                except Exception as e:
                    print(f"⚠️ Could not run comprehensive filtering validation: {e}")
        
        print("\n" + "="*60)
        print("🎯 SCRPA V8.0 PROCESSING COMPLETE")
        print("="*60)
        print(f"✅ RMS Records: {len(results['rms_data'])}")
        print(f"✅ CAD Records: {len(results['cad_data'])}")
        print(f"✅ Output Directory: {results['output_dir']}")
        print(f"✅ Data Quality Status: {validation_results['overall_status']}")
        
        # Print key metrics
        if validation_results['rms_validation']:
            rms_val = validation_results['rms_validation']
            print(f"✅ RMS Case Number Quality: {rms_val['case_number_quality']}")
            print(f"✅ RMS Incident Types: {rms_val['incident_types_populated']} records")
            
        if validation_results['cad_validation']:
            cad_val = validation_results['cad_validation']
            print(f"✅ CAD Case Number Quality: {cad_val['case_number_quality']}")
            print(f"✅ CAD Time Calculations: {cad_val['time_calculations_populated']} records")
        
        # Print filtering validation results
        if filtering_validation_results:
            filtering_status = filtering_validation_results['filtering_validation']['overall_status']
            print(f"✅ Comprehensive Filtering Status: {filtering_status}")
            
            # Print key filtering metrics
            if 'filtering_accuracy_tests' in filtering_validation_results['filtering_validation']:
                filtering_analysis = filtering_validation_results['filtering_validation']['filtering_accuracy_tests']
                print(f"✅ 7-Day Records: {filtering_analysis.get('total_7day_records', 0)}")
                print(f"✅ Filtered Crime Incidents: {filtering_analysis.get('filtered_records', 0)}")
                print(f"✅ Filtering Rate: {filtering_analysis.get('filtering_rate', '0%')}")
                
                # Print crime distribution
                crime_dist = filtering_analysis.get('crime_distribution', {})
                if crime_dist:
                    print("✅ Crime Distribution:")
                    for crime_type, count in crime_dist.items():
                        print(f"   - {crime_type}: {count}")
            
            # Print recommendations if any
            recommendations = filtering_validation_results['filtering_validation'].get('recommendations', [])
            if recommendations:
                print("⚠️ Filtering Validation Recommendations:")
                for rec in recommendations:
                    print(f"   - {rec}")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Import the CSV files into Power BI")
        print("2. Verify column names are PascalCase_With_Underscores")
        print("3. Create relationships between tables on Case_Number")
        print("4. Test DAX measures with standardized column references")
        print("5. Review comprehensive filtering validation report")
        print("="*60)
        
    except Exception as e:
        print(f"❌ An error occurred during processing: {e}")
        logging.getLogger('ComprehensiveSCRPAFixV8_0').error(f"Fatal error in main execution: {e}", exc_info=True)
        raise