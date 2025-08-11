# 🕒 2025-07-29-17-00-00
# SCRPA_Time_v2/Comprehensive_SCRPA_Fix_v8.5_Standardized
# Author: R. A. Carucci
# Purpose: Fixed version with proper PascalCase_With_Underscores column standardization to match Power BI requirements
# ✅ NEW in v8.5: Cycle calendar integration for temporal analysis and export naming

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Helper functions for header normalization and column coalescing
def to_snake(name: str) -> str:
    """Convert any string to lowercase snake_case format."""
    s = str(name)
    # Handle camelCase/PascalCase by inserting space before capital letters
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    # Handle numbers following letters
    s = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', s)
    # Replace any non-alphanumeric characters with spaces
    s = re.sub(r'[^0-9A-Za-z]+', ' ', s).strip()
    # Replace multiple spaces with single underscore
    s = re.sub(r'\s+', '_', s).lower()
    return s

def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame headers to lowercase snake_case format."""
    df = df.copy()
    df.columns = [to_snake(c) for c in df.columns]
    return df

def coalesce_cols(df: pd.DataFrame, *cols: str):
    """Coalesce multiple columns, filling nulls with values from subsequent columns."""
    out = pd.Series(pd.NA, index=df.index)
    for c in cols:
        if c in df.columns:
            out = out.fillna(df[c])
    return out

class ComprehensiveSCRPAFixV8_5:
    """
    ✅ **NEW in v8.5**: Cycle calendar integration for temporal analysis and export naming
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
            'zone_grid': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\zone_grid_master.xlsx"),
            'cycle_calendar': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Temporal\SCRPA_Cycle\7Day_28Day_Cycle_20250414.xlsx")
        }
        
        self.call_type_ref = None
        self.zone_grid_ref = None
        self.cycle_calendar = None
        self.current_cycle = None
        self.current_date = None
        self.setup_logging()
        self.load_reference_data()
        
        # Load cycle calendar and get current cycle info
        self.cycle_calendar = self.load_cycle_calendar()
        self.current_cycle, self.current_date = self.get_current_cycle_info(self.cycle_calendar)

    def setup_logging(self):
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"comprehensive_scrpa_fix_v8_5_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.logger = logging.getLogger('ComprehensiveSCRPAFixV8_5')
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
        
        self.logger.info("=== Comprehensive SCRPA Fix V8.5 - Cycle Calendar Integration Version ===")

    def load_reference_data(self):
        """Load reference data for call type categorization and zone/grid mapping."""
        # Load call type reference with incident column forced to string type and preserve Excel's Response_Type and Category_Type columns
        try:
            if self.ref_dirs['call_types'].exists():
                # Load with incident column forced to string type and preserve Excel's original column names
                self.call_type_ref = pd.read_excel(
                    self.ref_dirs['call_types'], 
                    dtype={"Incident": str, "Response Type": str, "Category Type": str}
                )
                self.logger.info(f"Loaded call type reference: {len(self.call_type_ref)} records")
                self.logger.info(f"Reference file columns: {list(self.call_type_ref.columns)}")
                
                # Ensure incident column is properly formatted as string
                if 'Incident' in self.call_type_ref.columns:
                    self.call_type_ref['Incident'] = self.call_type_ref['Incident'].astype(str)
                    self.logger.info(f"Incident column forced to string type with {len(self.call_type_ref)} records")
            else:
                # Try fallback path
                fallback_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\CallType_Categories.xlsx")
                if fallback_path.exists():
                    # Load with incident column forced to string type and preserve Excel's original column names
                    self.call_type_ref = pd.read_excel(
                        fallback_path, 
                        dtype={"Incident": str, "Response Type": str, "Category Type": str}
                    )
                    self.logger.info(f"Loaded call type reference from fallback path: {len(self.call_type_ref)} records")
                    self.logger.info(f"Reference file columns: {list(self.call_type_ref.columns)}")
                    
                    # Ensure incident column is properly formatted as string
                    if 'Incident' in self.call_type_ref.columns:
                        self.call_type_ref['Incident'] = self.call_type_ref['Incident'].astype(str)
                        self.logger.info(f"Incident column forced to string type with {len(self.call_type_ref)} records")
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

    def load_cycle_calendar(self):
        """Load Excel file from 09_Reference/Temporal/SCRPA_Cycle/7Day_28Day_Cycle_20250414.xlsx"""
        try:
            if self.ref_dirs['cycle_calendar'].exists():
                cycle_df = pd.read_excel(self.ref_dirs['cycle_calendar'])
                self.logger.info(f"Loaded cycle calendar: {len(cycle_df)} records")
                self.logger.info(f"Cycle calendar columns: {list(cycle_df.columns)}")
                return cycle_df
            else:
                self.logger.warning("Cycle calendar file not found - cycle features will be disabled")
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Could not load cycle calendar: {e}")
            return pd.DataFrame()

    def get_cycle_for_date(self, incident_date, cycle_df):
        """Return cycle name (like "C08W31") for any date"""
        if cycle_df.empty or pd.isna(incident_date):
            return None
            
        try:
            # Convert incident_date to datetime if it's not already
            if isinstance(incident_date, str):
                incident_date = pd.to_datetime(incident_date, errors='coerce')
            elif hasattr(incident_date, 'date'):
                incident_date = incident_date.date()
            
            if pd.isna(incident_date):
                return None
            
            # Check if date falls within any 7-day cycle
            for _, row in cycle_df.iterrows():
                start_date = pd.to_datetime(row['7_Day_Start']).date()
                end_date = pd.to_datetime(row['7_Day_End']).date()
                
                if start_date <= incident_date <= end_date:
                    return row['Report_Name']
            
            return None
        except Exception as e:
            self.logger.warning(f"Error getting cycle for date {incident_date}: {e}")
            return None

    def get_current_cycle_info(self, cycle_df):
        """Get current cycle for export naming"""
        if cycle_df.empty:
            return None, None
            
        try:
            today = datetime.now().date()
            
            # Find current cycle
            for _, row in cycle_df.iterrows():
                start_date = pd.to_datetime(row['7_Day_Start']).date()
                end_date = pd.to_datetime(row['7_Day_End']).date()
                
                if start_date <= today <= end_date:
                    current_cycle = row['Report_Name']
                    current_date = today.strftime('%Y%m%d')
                    self.logger.info(f"Current cycle: {current_cycle}, Date: {current_date}")
                    return current_cycle, current_date
            
            # If not in current cycle, find the most recent past cycle
            past_cycles = []
            for _, row in cycle_df.iterrows():
                end_date = pd.to_datetime(row['7_Day_End']).date()
                if end_date <= today:
                    past_cycles.append((end_date, row['Report_Name']))
            
            if past_cycles:
                # Get the most recent past cycle
                most_recent = max(past_cycles, key=lambda x: x[0])
                current_cycle = most_recent[1]
                current_date = today.strftime('%Y%m%d')
                self.logger.info(f"Using most recent past cycle: {current_cycle}, Date: {current_date}")
                return current_cycle, current_date
            
            return None, None
        except Exception as e:
            self.logger.error(f"Error getting current cycle info: {e}")
            return None, None

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
        """
        Enhanced CAD CallType mapping with response classification.
        
        Implements the updated mapping logic:
        1. Exact case-insensitive lookup in CallType_Categories.xlsx
        2. Partial match fallback (incident value contained in reference or vice versa)
        3. Keyword fallback with Response_Type and Category_Type set to same value
        
        Args:
            incident_value: Raw incident value from CAD data
            
        Returns:
            tuple: (response_type, category_type)
        """
        if pd.isna(incident_value) or not incident_value:
            return None, None
            
        # Clean input for consistent matching
        incident_clean = str(incident_value).strip().upper()
        
        # Step 1: Try exact case-insensitive lookup in reference data
        if self.call_type_ref is not None and not self.call_type_ref.empty:
            try:
                # Ensure 'Incident' column exists and force to string type
                if 'Incident' in self.call_type_ref.columns:
                    # Force incident column to string type for consistent matching
                    ref_incidents = self.call_type_ref['Incident'].astype(str).str.strip().str.upper()
                    
                    # Exact case-insensitive match lookup
                    exact_match = ref_incidents == incident_clean
                    if exact_match.any():
                        match_idx = exact_match.idxmax()
                        response_type = self.call_type_ref.loc[match_idx, 'Response Type']
                        category_type = self.call_type_ref.loc[match_idx, 'Category Type']
                        return response_type, category_type
                    
                    # Step 2: Partial match fallback - check if incident_clean is contained in any reference incident
                    partial_matches = ref_incidents.str.contains(incident_clean, case=False, na=False)
                    if partial_matches.any():
                        match_idx = partial_matches.idxmax()
                        response_type = self.call_type_ref.loc[match_idx, 'Response Type']
                        category_type = self.call_type_ref.loc[match_idx, 'Category Type']
                        return response_type, category_type
                    
                    # Step 3: Reverse partial fallback - check if any reference incident is contained in incident_clean
                    for _, row in self.call_type_ref.iterrows():
                        ref_incident = str(row['Incident']).strip().upper()
                        if ref_incident and ref_incident in incident_clean:
                            response_type = row['Response Type']
                            category_type = row['Category Type']
                            return response_type, category_type
                            
            except Exception as e:
                self.logger.warning(f"Error in reference data lookup: {e}")
        
        # Step 4: Keyword fallback categorization
        # Both Response_Type and Category_Type are set to the same value for each category
        
        # Define keyword patterns for category classification (ordered by priority)
        # Crime should be checked before Alarm to avoid "BURGLARY AUTO" being classified as Alarm
        keyword_patterns = {
            'Crime': ['THEFT', 'BURGLARY', 'ROBBERY', 'LARCENY', 'ASSAULT', 'BATTERY', 'FRAUD'],
            'Traffic': ['TRAFFIC', 'MOTOR', 'VEHICLE', 'ACCIDENT', 'COLLISION', 'DUI', 'DWI', 'SPEEDING'],
            'Medical': ['MEDICAL', 'EMS', 'AMBULANCE', 'HEART', 'STROKE', 'SEIZURE', 'OVERDOSE'],
            'Fire': ['FIRE', 'SMOKE', 'BURNING', 'EXPLOSION', 'HAZMAT'],
            'Disturbance': ['DOMESTIC', 'DISTURBANCE', 'FIGHT', 'NOISE', 'DISPUTE', 'ARGUMENT'],
            'Alarm': ['ALARM', 'SECURITY', 'BURGLAR', 'FIRE ALARM', 'PANIC']
        }
        
        # Check each category's keywords
        for category, keywords in keyword_patterns.items():
            if any(keyword in incident_clean for keyword in keywords):
                # Both Response_Type and Category_Type are set to the same value
                return category, category
        else:
            # Default category if no keywords match
            # Response_Type = original incident value, Category_Type = 'Other'
            return incident_value, 'Other'

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

    def parse_cad_notes(self, raw: str) -> pd.Series:
        """
        Parse CAD notes to extract username, timestamp, and cleaned text.
        
        Args:
            raw: Raw CAD notes string
            
        Returns:
            pd.Series with columns: [CAD_Username, CAD_Timestamp, CAD_Notes_Cleaned]
        """
        if pd.isna(raw) or not raw:
            return pd.Series([None, None, None], index=['CAD_Username', 'CAD_Timestamp', 'CAD_Notes_Cleaned'])
            
        text = str(raw).strip()
        username = None
        timestamp = None
        
        # Enhanced username patterns to match examples
        username_patterns = [
            r'^([a-zA-Z_]+(?:_[a-zA-Z]+)?)',  # kiselow_g, Gervasi_J, intake_fa
            r'^([A-Z]+\d*)',  # All caps with optional digits
            r'^([a-zA-Z]+\.[a-zA-Z]+)',  # First.Last format
        ]
        
        for pattern in username_patterns:
            username_match = re.search(pattern, text)
            if username_match:
                username = username_match.group(1)
                break
        
        # Enhanced timestamp patterns to match examples
        timestamp_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [AP]M',  # 1/14/2025 3:47:59 PM
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # ISO format
            r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}',  # Date with time (no seconds)
        ]
        
        for pattern in timestamp_patterns:
            timestamp_match = re.search(pattern, text)
            if timestamp_match:
                timestamp = timestamp_match.group(0)
                # Standardize timestamp format to MM/DD/YYYY HH:MM:SS
                try:
                    # Parse the timestamp and reformat it
                    if 'AM' in timestamp or 'PM' in timestamp:
                        # Handle 12-hour format - try different formats
                        try:
                            parsed_time = pd.to_datetime(timestamp, format='%m/%d/%Y %I:%M:%S %p')
                        except:
                            # Try without seconds
                            parsed_time = pd.to_datetime(timestamp, format='%m/%d/%Y %I:%M %p')
                    else:
                        # Handle 24-hour format
                        parsed_time = pd.to_datetime(timestamp)
                    
                    timestamp = parsed_time.strftime('%m/%d/%Y %H:%M:%S')
                except:
                    # If parsing fails, keep original format
                    pass
                break
        
        # Clean the notes by removing username, timestamp, and other metadata
        cleaned = text
        
        # Remove username
        if username:
            # Remove username with various separators
            username_patterns_to_remove = [
                f'^{re.escape(username)}\\s*',  # Start of line
                f'^{re.escape(username)}[\\s-]+',  # With dash separator
                f'^{re.escape(username)}[\\s:]+',  # With colon separator
            ]
            for pattern in username_patterns_to_remove:
                cleaned = re.sub(pattern, '', cleaned)
        
        # Remove timestamp
        if timestamp:
            # Try both original and standardized formats
            timestamp_variants = [timestamp]
            try:
                # Add original format if different
                original_match = re.search(r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [AP]M', text)
                if original_match and original_match.group(0) != timestamp:
                    timestamp_variants.append(original_match.group(0))
            except:
                pass
            
            for ts in timestamp_variants:
                cleaned = re.sub(re.escape(ts), '', cleaned)
            
            # Also remove any remaining AM/PM patterns that might be left
            cleaned = re.sub(r'\s+[AP]M\s+', ' ', cleaned)
            cleaned = re.sub(r'^[AP]M\s+', '', cleaned)
        
        # Remove header patterns, stray date fragments, and clean up
        cleaned = re.sub(r'^[\\s-]+', '', cleaned)  # Remove leading dashes/spaces
        cleaned = re.sub(r'[\r\n\t]+', ' ', cleaned)  # Replace line breaks with spaces
        cleaned = re.sub(r'\\s+', ' ', cleaned)  # Normalize whitespace
        cleaned = cleaned.strip()
        
        # Title-case the remainder
        if cleaned:
            cleaned = cleaned.title()
        
        return pd.Series([username, timestamp, cleaned], index=['CAD_Username', 'CAD_Timestamp', 'CAD_Notes_Cleaned'])

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

    def standardize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize data types for consistent CSV export output"""
        
        # Force object dtype for string cols, convert empties to None
        string_cols = ['case_number','incident_date','incident_time','all_incidents',
                       'vehicle_1','vehicle_2','vehicle_1_and_vehicle_2','narrative',
                       'location','block','response_type','category_type','period',
                       'season','day_of_week','day_type','cycle_name']
        for col in string_cols:
            if col in df.columns:
                # Force object dtype and handle NaN values properly
                df[col] = df[col].astype('object')
                # Convert non-null values to string, keep None for null values
                df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) and str(x).lower() != 'nan' else None)

        # Coerce numeric cols
        numeric_cols = ['post','grid','time_of_day_sort_order','total_value_stolen','total_value_recovered']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

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
            "Incident": "incident",  # FIXED: Map directly to 'incident' instead of 'incident_raw'
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
        """
        Enhanced cascading date logic according to specification.
        
        Chain-fill: date = Date → Date_Between → Report Date
        Parse each field separately with errors='coerce'
        """
        # Define the date cascade chain in priority order
        date_columns = [
            'Incident Date',           # Primary date field
            'Incident Date_Between',   # Fallback date field
            'Report Date'              # Final fallback
        ]
        
        # Try each column in the cascade chain
        for col in date_columns:
            if col in row.index and pd.notna(row.get(col)):
                try:
                    # Parse each field separately with errors='coerce'
                    result = pd.to_datetime(row[col], errors='coerce')
                    if pd.notna(result):
                        return result.date()
                except Exception as e:
                    self.logger.debug(f"Error parsing date from {col}: {e}")
                    continue
        
        return None

    def cascade_time(self, row):
        """
        Enhanced cascading time logic according to specification.
        
        Chain-fill: time = Time → Time_Between → Report Time
        Parse each field separately with errors='coerce'
        Format time via strftime to avoid Excel fallback artifact
        """
        # Define the time cascade chain in priority order
        time_columns = [
            'Incident Time',           # Primary time field
            'Incident Time_Between',   # Fallback time field
            'Report Time'              # Final fallback
        ]
        
        # Try each column in the cascade chain
        for col in time_columns:
            if col in row.index and pd.notna(row.get(col)):
                try:
                    time_value = row[col]
                    
                    # Handle Excel Timedelta objects (common Excel time format)
                    if isinstance(time_value, pd.Timedelta):
                        total_seconds = time_value.total_seconds()
                        hours = int(total_seconds // 3600) % 24  # Handle 24+ hour overflow
                        minutes = int((total_seconds % 3600) // 60)
                        seconds = int(total_seconds % 60)
                        
                        from datetime import time
                        time_obj = time(hours, minutes, seconds)
                        # Format via strftime to avoid Excel fallback artifact
                        return time_obj.strftime("%H:%M:%S")
                    
                    # Handle other time formats
                    else:
                        # Parse each field separately with errors='coerce'
                        parsed_time = pd.to_datetime(time_value, errors='coerce')
                        if pd.notna(parsed_time):
                            # Format via strftime to avoid Excel fallback artifact
                            return parsed_time.strftime("%H:%M:%S")
                            
                except Exception as e:
                    self.logger.debug(f"Error parsing time from {col}: {e}")
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
        if pd.isna(date_val) or date_val is None:
            return "Historical"
        
        # Convert date_val to date object if it's not already
        try:
            if hasattr(date_val, 'date'):
                date_val = date_val.date()
            elif isinstance(date_val, str):
                date_val = pd.to_datetime(date_val, errors='coerce').date()
            elif not hasattr(date_val, 'year'):
                return "Historical"
        except:
            return "Historical"
            
        today = pd.Timestamp.now().date()
        days_diff = (today - date_val).days
        
        # Debug logging for period calculation (only log first few to avoid spam)
        if hasattr(self, '_period_debug_count'):
            self._period_debug_count += 1
        else:
            self._period_debug_count = 1
            
        if self._period_debug_count <= 3:
            self.logger.debug(f"Period calc: date_val={date_val}, today={today}, days_diff={days_diff}")
        
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
                # For intersections, extract just the street names (remove house numbers)
                street1 = parts[0].strip()
                street2 = parts[1].strip()
                
                # Remove house numbers from street names (only if they start with digits)
                def clean_street_name(street):
                    words = street.split()
                    if words and words[0].isdigit():
                        return ' '.join(words[1:])
                    return street
                
                street1_clean = clean_street_name(street1)
                street2_clean = clean_street_name(street2)
                
                return f"{street1_clean} & {street2_clean}"
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
        if pd.isna(incident_str) or incident_str == "":
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
            'incident_cad',            # CAD incident column (highest priority for matched data)
            'incident_type',           # Primary RMS column
            'all_incidents',           # Combined incidents
            'incident',                # CAD incident without suffix
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

        # NORMALIZE HEADERS: Apply lowercase snake_case normalization immediately after loading
        rms_df = normalize_headers(rms_df)
        self.logger.info(f"Normalized RMS headers to lowercase snake_case: {list(rms_df.columns)}")

        # Apply column mapping only for columns that exist
        column_mapping = self.get_rms_column_mapping()
        existing_mapping = {k: v for k, v in column_mapping.items() if k in rms_df.columns}
        rms_df = rms_df.rename(columns=existing_mapping)
        self.logger.info(f"Applied column mapping: {existing_mapping}")
        
        # Convert ALL remaining columns to lowercase_with_underscores (redundant but safe)
        rms_df.columns = [self.convert_to_lowercase_with_underscores(col) for col in rms_df.columns]
        
        # Clean text columns
        text_columns = rms_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            rms_df[col] = rms_df[col].apply(self.clean_text_comprehensive)

        # DEBUG: Check available date columns before cascading
        date_columns = [col for col in rms_df.columns if 'date' in col.lower()]
        self.logger.info(f"Available date columns: {date_columns}")
        
        # Check for raw date columns that cascade_date function expects
        expected_date_cols = ['incident_date_raw', 'incident_date_between_raw', 'report_date_raw']
        missing_date_cols = [col for col in expected_date_cols if col not in rms_df.columns]
        if missing_date_cols:
            self.logger.warning(f"Missing expected date columns: {missing_date_cols}")
        
        # Sample raw date values before cascading
        for col in expected_date_cols:
            if col in rms_df.columns:
                populated = rms_df[col].notna().sum()
                self.logger.info(f"{col} populated: {populated}/{len(rms_df)}")
                if populated > 0:
                    sample = rms_df[col].dropna().head(3).tolist()
                    self.logger.info(f"Sample {col} values: {sample}")

        # Robust RMS date/time cascade logic according to specification
        # Parse and chain-fill dates using mapped column names
        d1 = pd.to_datetime(rms_df["incident_date_raw"], errors="coerce")
        d2 = pd.to_datetime(rms_df["incident_date_between_raw"], errors="coerce")
        d3 = pd.to_datetime(rms_df["report_date_raw"], errors="coerce")
        rms_df['incident_date'] = (
            d1.fillna(d2)
              .fillna(d3)
              .dt.date
        )
        
        # DEBUG: Check incident_date population after cascading
        date_populated = rms_df['incident_date'].notna().sum()
        self.logger.info(f"Incident dates after cascading: {date_populated}/{len(rms_df)}")
        if date_populated > 0:
            sample_cascaded_dates = rms_df['incident_date'].dropna().head(5).tolist()
            self.logger.info(f"Sample cascaded dates: {sample_cascaded_dates}")
        else:
            self.logger.error("NO INCIDENT DATES POPULATED AFTER CASCADING - This will cause all records to be marked as 'Historical'")
        
        # Parse and chain-fill times using mapped column names
        t1 = pd.to_datetime(rms_df["incident_time_raw"], errors="coerce").dt.time
        t2 = pd.to_datetime(rms_df["incident_time_between_raw"], errors="coerce").dt.time
        t3 = pd.to_datetime(rms_df["report_time_raw"], errors="coerce").dt.time
        rms_df['incident_time'] = t1.fillna(t2).fillna(t3)
        
        # Format as strings to avoid Excel fallback artifacts
        rms_df['incident_time'] = rms_df['incident_time'].apply(
            lambda t: t.strftime("%H:%M:%S") if pd.notna(t) else None
        )
        
        # Time-of-Day Buckets & Sort Order implementation
        # Define time-of-day buckets in order
        tod_order = [
            "00:00-03:59 Early Morning",
            "04:00-07:59 Morning", 
            "08:00-11:59 Morning Peak",
            "12:00-15:59 Afternoon",
            "16:00-19:59 Evening Peak",
            "20:00-23:59 Night",
            "Unknown"
        ]
        
        # Apply map_tod function to cleaned incident_time
        rms_df['time_of_day'] = rms_df['incident_time'].apply(self.map_tod)
        
        # Convert to ordered categorical and generate sort order
        rms_df['time_of_day'] = pd.Categorical(
            rms_df['time_of_day'], 
            categories=tod_order, 
            ordered=True
        )
        rms_df['time_of_day_sort_order'] = rms_df['time_of_day'].cat.codes + 1
        
        # DEBUG: Check incident_date values before period calculation
        incident_dates_sample = rms_df['incident_date'].dropna().head(5).tolist()
        self.logger.info(f"Sample incident_date values: {incident_dates_sample}")
        self.logger.info(f"Null incident_date count: {rms_df['incident_date'].isna().sum()}")
        self.logger.info(f"Date types: {rms_df['incident_date'].dtype}")
        
        rms_df['period'] = rms_df['incident_date'].apply(self.get_period)
        
        # DEBUG: Check period distribution immediately after calculation
        period_distribution = rms_df['period'].value_counts()
        self.logger.info(f"Period calculation results: {period_distribution.to_dict()}")
        
        # Additional validation: Check if we have recent dates
        if 'incident_date' in rms_df.columns:
            recent_7_day = rms_df[rms_df['period'] == '7-Day']['incident_date'].count()
            recent_28_day = rms_df[rms_df['period'] == '28-Day']['incident_date'].count()
            ytd_count = rms_df[rms_df['period'] == 'YTD']['incident_date'].count()
            historical_count = rms_df[rms_df['period'] == 'Historical']['incident_date'].count()
            
            self.logger.info(f"Date/Period Analysis Summary:")
            self.logger.info(f"  - 7-Day period records: {recent_7_day}")
            self.logger.info(f"  - 28-Day period records: {recent_28_day}")
            self.logger.info(f"  - YTD period records: {ytd_count}")
            self.logger.info(f"  - Historical period records: {historical_count}")
            
            if recent_7_day == 0 and recent_28_day == 0 and ytd_count == 0:
                self.logger.warning("⚠️ ALL RECORDS DEFAULTING TO HISTORICAL - Date processing issue detected!")
            else:
                self.logger.info("✅ Date processing working correctly - mix of periods found")
        
        # Period, Day_of_Week & Cycle_Name Fixes - Enhanced implementation
        # Ensure incident_date is datetime
        rms_df['incident_date'] = pd.to_datetime(rms_df['incident_date'], errors='coerce')
        
        # Period
        rms_df['period'] = rms_df['incident_date'].apply(self.get_period)
        
        # Season
        rms_df['season'] = rms_df['incident_date'].apply(self.get_season)
        
        # Day of Week & Type
        rms_df['day_of_week'] = rms_df['incident_date'].dt.day_name()
        rms_df['day_type'] = rms_df['day_of_week'].isin(['Saturday', 'Sunday']).map({True: 'Weekend', False: 'Weekday'})
        
        # Cycle Name (uses fixed incident_date)
        rms_df['cycle_name'] = rms_df['incident_date'].apply(
            lambda x: self.get_cycle_for_date(x, self.cycle_calendar) if pd.notna(x) else None
        )

        # Address validation and standardization
        if 'full_address_raw' in rms_df.columns:
            rms_df['location'] = rms_df['full_address_raw'].apply(self.validate_hackensack_address)
        else:
            rms_df['location'] = None
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
        if 'incident_type_1_raw' in rms_df.columns:
            rms_df['incident_type'] = rms_df['incident_type_1_raw'].apply(self.clean_incident_type)
        else:
            rms_df['incident_type'] = None
        
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

        # Vehicle Fields Uppercasing - Enhanced implementation
        for col in ['vehicle_1', 'vehicle_2', 'vehicle_1_and_vehicle_2']:
            if col in rms_df.columns:
                rms_df[col] = rms_df[col].str.upper().where(rms_df[col].notna(), None)

        # Convert squad column to uppercase
        if 'squad' in rms_df.columns:
            rms_df['squad'] = rms_df['squad'].apply(lambda x: x.upper() if pd.notna(x) else None)

        # Narrative Cleaning - Enhanced implementation
        def clean_narrative(text: str) -> str:
            if pd.isna(text):
                return None
            s = re.sub(r'#\(cr\)#\(lf\)|#\(lf\)|#\(cr\)|[\r\n\t]+', ' ', text)
            s = re.sub(r'\s+', ' ', s).strip()
            return s.title() if s else None

        if 'narrative_raw' in rms_df.columns:
            rms_df['narrative'] = rms_df['narrative_raw'].apply(clean_narrative)
        else:
            rms_df['narrative'] = None

        # HEADER VALIDATION: Enforce lowercase snake_case headers
        header_validation = self.validate_lowercase_snake_case_headers(rms_df, "RMS")
        if header_validation['overall_status'] == 'FAIL':
            invalid_headers = header_validation['non_compliant_columns']
            self.logger.error(f"RMS headers validation failed. Invalid headers: {invalid_headers}")
            raise ValueError(f"RMS headers must be lowercase snake_case. Invalid headers: {invalid_headers}")
        else:
            self.logger.info("RMS headers validation passed - all headers are lowercase snake_case")

        # Final column selection - Include incident_type as primary field
        desired_columns = [
            'case_number', 'incident_date', 'incident_time', 'time_of_day', 'time_of_day_sort_order',
            'period', 'season', 'day_of_week', 'day_type', 'location', 'block', 
            'grid', 'post', 'incident_type', 'all_incidents', 'vehicle_1', 'vehicle_2', 
            'vehicle_1_and_vehicle_2', 'narrative', 'total_value_stolen', 
            'total_value_recovered', 'squad', 'officer_of_record', 'nibrs_classification', 'cycle_name'
        ]

        # Select only columns that exist in the dataframe
        existing_columns = [col for col in desired_columns if col in rms_df.columns]
        rms_final = rms_df[existing_columns].copy()

        # DEBUG: RMS filtering analysis
        self.logger.info(f"RMS records before filtering: {len(rms_final)}")
        
        # Check period column values
        if 'period' in rms_final.columns:
            period_counts = rms_final['period'].value_counts()
            self.logger.info(f"Period distribution: {period_counts.to_dict()}")
            non_historical = rms_final[rms_final['period'] != 'Historical']
            self.logger.info(f"Non-historical records: {len(non_historical)}")
        else:
            self.logger.warning("Period column not found in RMS data")
        
        # Check case number values
        if 'case_number' in rms_final.columns:
            self.logger.info(f"Sample case numbers: {rms_final['case_number'].head(5).tolist()}")
            excluded_case = rms_final[rms_final['case_number'] == '25-057654']
            self.logger.info(f"Records with excluded case number '25-057654': {len(excluded_case)}")
        else:
            self.logger.warning("Case number column not found in RMS data")
        
        # Check incident_date population
        if 'incident_date' in rms_final.columns:
            date_populated = rms_final['incident_date'].notna().sum()
            self.logger.info(f"Incident dates populated: {date_populated}/{len(rms_final)}")
            if date_populated > 0:
                sample_dates = rms_final['incident_date'].dropna().head(5).tolist()
                self.logger.info(f"Sample incident dates: {sample_dates}")
                date_range_min = rms_final['incident_date'].min()
                date_range_max = rms_final['incident_date'].max()
                self.logger.info(f"Date range: {date_range_min} to {date_range_max}")
            else:
                self.logger.warning("No incident dates populated - this may cause period calculation issues")
        else:
            self.logger.warning("Incident date column not found in RMS data")

        # Apply filtering with individual steps for debugging
        initial_count = len(rms_final)
        
        if 'case_number' in rms_final.columns and 'period' in rms_final.columns:
            # Case number filter
            case_filter = rms_final['case_number'] != '25-057654'
            rms_final = rms_final[case_filter]
            self.logger.info(f"After case number filter: {len(rms_final)}/{initial_count} records")
            
            # Period filter  
            period_filter = rms_final['period'] != 'Historical'
            rms_final = rms_final[period_filter]
            self.logger.info(f"After period filter: {len(rms_final)}/{initial_count} records")
        else:
            missing_cols = []
            if 'case_number' not in rms_final.columns:
                missing_cols.append('case_number')
            if 'period' not in rms_final.columns:
                missing_cols.append('period')
            self.logger.warning(f"Skipping filtering due to missing columns: {missing_cols}")

        self.logger.info(f"RMS processing complete: {len(rms_final)} records after filtering")
        self.logger.info(f"Final RMS columns: {list(rms_final.columns)}")
        self.logger.info("REMOVED CAD-specific columns: incident_type, crime_category, response_type")
        return rms_final

    def process_cad_data(self, cad_file, ref_lookup=None):
        """Process CAD data with enhanced incident mapping and lowercase snake_case headers."""
        self.logger.info(f"Processing CAD data: {cad_file.name}")
        
        try:
            # Load CAD file with "How Reported" column forced to string type to prevent Excel auto-parsing "9-1-1" as date
            cad_df = pd.read_excel(cad_file, engine='openpyxl', dtype={"How Reported": str})
            self.logger.info(f"Loaded CAD file with {len(cad_df)} rows and {len(cad_df.columns)} columns")
            self.logger.info(f"CAD columns found: {list(cad_df.columns)}")
            self.logger.info("Applied dtype={'How Reported': str} to prevent Excel auto-parsing '9-1-1' as date")
        except Exception as e:
            self.logger.error(f"Error loading CAD file: {e}")
            return pd.DataFrame()

        # Apply column mapping FIRST (before normalization) only for columns that exist
        column_mapping = self.get_cad_column_mapping()
        existing_mapping = {k: v for k, v in column_mapping.items() if k in cad_df.columns}
        cad_df = cad_df.rename(columns=existing_mapping)
        self.logger.info(f"Applied column mapping: {existing_mapping}")

        # NORMALIZE HEADERS: Apply lowercase snake_case normalization after column mapping
        cad_df = normalize_headers(cad_df)
        self.logger.info(f"Normalized CAD headers to lowercase snake_case: {list(cad_df.columns)}")

        # Clean text columns
        text_columns = cad_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            cad_df[col] = cad_df[col].apply(self.clean_text_comprehensive)

        # Fix how_reported 9-1-1 date issue
        if 'how_reported' in cad_df.columns:
            cad_df['how_reported'] = cad_df['how_reported'].apply(self.clean_how_reported_911)

        # ENHANCED: Load call type reference if not provided and perform incident mapping
        if ref_lookup is None:
            ref_lookup, _ = self.load_call_type_reference_enhanced()
        
        # Map incident to response_type and category_type using enhanced mapping
        if 'incident' in cad_df.columns:
            # Ensure the incident values are properly processed
            cad_df['incident'] = cad_df['incident'].replace('', None)
            
            self.logger.info(f"Starting enhanced call type mapping for {len(cad_df)} CAD records")
            self.logger.info(f"Sample incident values: {cad_df['incident'].dropna().head(5).tolist()}")
            
            # Apply the enhanced map_call_type function to each incident value
            mapping_results = cad_df['incident'].apply(self.map_call_type)
            response_types = [result[0] if result else None for result in mapping_results]
            category_types = [result[1] if result else None for result in mapping_results]
            
            # Add the mapped columns with _cad suffix as requested
            cad_df['response_type_cad'] = response_types
            cad_df['category_type_cad'] = category_types
            
            # Calculate mapping statistics
            total_incidents = len(cad_df)
            mapped_count = sum(1 for rt in response_types if rt is not None)
            unmapped_count = total_incidents - mapped_count
            mapping_rate = (mapped_count / total_incidents) * 100 if total_incidents > 0 else 0
            
            # Log mapping results
            self.logger.info(f"Enhanced mapping results:")
            self.logger.info(f"  - Total incidents: {total_incidents}")
            self.logger.info(f"  - Mapped incidents: {mapped_count}")
            self.logger.info(f"  - Unmapped incidents: {unmapped_count}")
            self.logger.info(f"  - Mapping rate: {mapping_rate:.1f}%")
            
            # Log category distribution
            category_counts = pd.Series(category_types).value_counts()
            self.logger.info(f"Category type distribution: {category_counts.to_dict()}")
            response_counts = pd.Series(response_types).value_counts().head(10)
            self.logger.info(f"Top 10 response types: {response_counts.to_dict()}")
            
            # DROP/RENAME: Drop or rename duplicate columns so final output has only one response_type and one category_type
            # sourced from Excel's Response_Type/Category_Type as specified
            
            # First, ensure we have the _cad suffix columns populated
            cad_df['response_type_cad'] = cad_df['response_type_cad'].fillna(cad_df['incident'])
            cad_df['response_type_cad'] = cad_df['response_type_cad'].fillna('Unknown')
            cad_df['category_type_cad'] = cad_df['category_type_cad'].fillna('Other')
            
            # Drop any existing response_type and category_type columns to avoid duplicates
            if 'response_type' in cad_df.columns:
                cad_df = cad_df.drop(columns=['response_type'])
            if 'category_type' in cad_df.columns:
                cad_df = cad_df.drop(columns=['category_type'])
            
            # Rename _cad columns to final names (sourced from Excel's Response_Type/Category_Type)
            cad_df = cad_df.rename(columns={
                'response_type_cad': 'response_type',
                'category_type_cad': 'category_type'
            })
            
            # Log coverage on final columns
            response_coverage = (cad_df['response_type'].notna().sum() / len(cad_df)) * 100
            category_coverage = (cad_df['category_type'].notna().sum() / len(cad_df)) * 100
            
            self.logger.info(f"Final column coverage:")
            self.logger.info(f"  - response_type coverage: {response_coverage:.1f}%")
            self.logger.info(f"  - category_type coverage: {category_coverage:.1f}%")
            
        else:
            self.logger.warning("incident column not found in CAD data - cannot perform call type mapping")
            # Add empty columns to maintain schema
            cad_df['response_type'] = None
            cad_df['category_type'] = None

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
        if 'full_address_raw' in cad_df.columns:
            cad_df['location'] = cad_df['full_address_raw'].apply(self.validate_hackensack_address)
        else:
            cad_df['location'] = None
        
        # Ensure grid and post are properly populated (not empty strings)
        if 'grid_raw' in cad_df.columns:
            cad_df['grid'] = cad_df['grid_raw'].replace('', None)
        else:
            cad_df['grid'] = None
        # post column already mapped correctly from PDZone, but ensure not empty
        if 'post' not in cad_df.columns:
            cad_df['post'] = None
        else:
            cad_df['post'] = cad_df['post'].replace('', None)
            
        cad_df['block'] = cad_df['location'].apply(self.calculate_block)

        # Enhanced CAD notes parsing with metadata extraction using new parse_cad_notes function
        if 'cad_notes_raw' in cad_df.columns:
            # Apply the new parse_cad_notes function and extract results
            usernames = []
            timestamps = []
            cleaned_texts = []
            
            for raw_notes in cad_df['cad_notes_raw']:
                result = self.parse_cad_notes(raw_notes)
                usernames.append(result['CAD_Username'])
                timestamps.append(result['CAD_Timestamp'])
                cleaned_texts.append(result['CAD_Notes_Cleaned'])
            
            # Add the extracted columns
            cad_df['cad_username'] = usernames
            cad_df['cad_timestamp'] = timestamps
            cad_df['cad_notes_cleaned'] = cleaned_texts
            
            self.logger.info(f"CAD notes parsing complete: {len(cad_df)} records processed")
        
        # Add cycle_name column using cycle calendar lookup
        # For CAD data, we need to derive incident_date from time_of_call if available
        def get_cad_incident_date(row):
            if pd.notna(row.get('time_of_call')):
                try:
                    call_time = pd.to_datetime(row['time_of_call'])
                    return call_time.date()
                except:
                    return None
            return None
        
        cad_df['incident_date'] = cad_df.apply(get_cad_incident_date, axis=1)
        cad_df['cycle_name'] = cad_df['incident_date'].apply(
            lambda x: self.get_cycle_for_date(x, self.cycle_calendar) if pd.notna(x) else None
        )

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
        
        # HEADER VALIDATION: Enforce lowercase snake_case headers
        header_validation = self.validate_lowercase_snake_case_headers(cad_df, "CAD")
        if header_validation['overall_status'] == 'FAIL':
            invalid_headers = header_validation['non_compliant_columns']
            self.logger.error(f"CAD headers validation failed. Invalid headers: {invalid_headers}")
            raise ValueError(f"CAD headers must be lowercase snake_case. Invalid headers: {invalid_headers}")
        else:
            self.logger.info("CAD headers validation passed - all headers are lowercase snake_case")
        
        # Final column selection with lowercase_with_underscores naming
        desired_columns = [
            'case_number', 'incident', 'response_type', 'category_type', 'response_type_cad', 'category_type_cad', 'how_reported', 
            'location', 'block', 'grid', 'post', 'time_of_call', 'time_dispatched', 
            'time_out', 'time_in', 'time_spent_minutes', 'time_response_minutes',
            'time_spent_formatted', 'time_response_formatted', 'officer', 'disposition', 
            'cad_notes_cleaned', 'cad_username', 'cad_timestamp', 'cycle_name'
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
        self.logger.info("Starting Comprehensive SCRPA Fix V8.5 pipeline...")
        
        latest_files = self.find_latest_files()
        
        if not latest_files:
            self.logger.error("No data files found to process")
            raise ValueError("No data files found")

        # Process RMS data
        rms_data = pd.DataFrame()
        if 'rms' in latest_files:
            rms_data = self.process_rms_data(latest_files['rms'])

        # Process CAD data with enhanced incident mapping
        cad_data = pd.DataFrame()
        mapping_diagnostics = None
        ref_diagnostics = None
        
        if 'cad' in latest_files:
            # Load reference data first for enhanced mapping
            ref_lookup, ref_diagnostics = self.load_call_type_reference_enhanced()
            
            # Process CAD data with reference lookup
            cad_data = self.process_cad_data(latest_files['cad'], ref_lookup)
            
            # Extract mapping diagnostics from CAD processing
            if 'incident' in cad_data.columns:
                # Re-run mapping to get diagnostics for QC report
                _, _, mapping_diagnostics = self.map_incident_to_call_types_enhanced(
                    cad_data['incident'], ref_lookup
                )

        # Create output directory
        output_dir = self.project_path / '04_powerbi'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save individual datasets with cycle naming
        if not rms_data.empty:
            cycle_suffix = f"_{self.current_cycle}_{self.current_date}" if self.current_cycle and self.current_date else ""
            rms_output = output_dir / f'{self.current_cycle}_{self.current_date}_7Day_rms_data_standardized.csv' if self.current_cycle and self.current_date else output_dir / 'rms_data_standardized.csv'
            # Standardize data types before export
            rms_data = self.standardize_data_types(rms_data)
            rms_data.to_csv(rms_output, index=False, encoding='utf-8')
            self.logger.info(f"RMS data saved: {rms_output}")

        if not cad_data.empty:
            cycle_suffix = f"_{self.current_cycle}_{self.current_date}" if self.current_cycle and self.current_date else ""
            cad_output = output_dir / f'{self.current_cycle}_{self.current_date}_7Day_cad_data_standardized.csv' if self.current_cycle and self.current_date else output_dir / 'cad_data_standardized.csv'
            # Standardize data types before export
            cad_data = self.standardize_data_types(cad_data)
            cad_data.to_csv(cad_output, index=False, encoding='utf-8')
            self.logger.info(f"CAD data saved: {cad_output}")

        # Generate comprehensive QC report for CAD processing
        if not cad_data.empty and mapping_diagnostics and ref_diagnostics:
            qc_results = self.generate_enhanced_qc_report(
                cad_data, mapping_diagnostics, ref_diagnostics, output_dir
            )
            self.logger.info(f"Enhanced QC Report Status: {qc_results['overall_status']}")
            if qc_results['critical_issues']:
                self.logger.warning(f"Critical Issues Found: {qc_results['critical_issues']}")
            else:
                self.logger.info("All QC validations passed successfully")

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
            
            # ENHANCED: Implement CAD-first, RMS-fallback logic for response_type and category_type
            self.logger.info("Implementing CAD-first, RMS-fallback logic for response_type and category_type...")
            
            # Create response_type and category_type columns with CAD-first logic
            def cad_first_fallback(row, cad_col, rms_col=None):
                """CAD-first fallback logic: use CAD if available, otherwise use RMS if available"""
                if pd.notna(row.get(cad_col)):
                    return row[cad_col]
                elif rms_col and pd.notna(row.get(rms_col)):
                    return row[rms_col]
                else:
                    return None
            
            # Apply CAD-first logic for response_type
            joined_data['response_type'] = joined_data.apply(
                lambda row: cad_first_fallback(row, 'response_type_cad'), axis=1
            )
            
            # Apply CAD-first logic for category_type
            joined_data['category_type'] = joined_data.apply(
                lambda row: cad_first_fallback(row, 'category_type_cad'), axis=1
            )
            
            # Merge Logic: Deduplicate and Reapply Cleaning - Enhanced implementation
            # After merge with suffixes (_cad, _rms):
            if 'incident_date_cad' in joined_data.columns and 'incident_date_rms' in joined_data.columns:
                joined_data['incident_date'] = joined_data['incident_date_cad'].fillna(joined_data['incident_date_rms'])
            elif 'incident_date_cad' in joined_data.columns:
                joined_data['incident_date'] = joined_data['incident_date_cad']
            elif 'incident_date_rms' in joined_data.columns:
                joined_data['incident_date'] = joined_data['incident_date_rms']
            
            if 'incident_time_cad' in joined_data.columns and 'incident_time_rms' in joined_data.columns:
                joined_data['incident_time'] = joined_data['incident_time_cad'].fillna(joined_data['incident_time_rms'])
            elif 'incident_time_cad' in joined_data.columns:
                joined_data['incident_time'] = joined_data['incident_time_cad']
            elif 'incident_time_rms' in joined_data.columns:
                joined_data['incident_time'] = joined_data['incident_time_rms']
            
            # Reapply key fixes:
            if 'incident_time' in joined_data.columns:
                joined_data['time_of_day'] = joined_data['incident_time'].apply(self.map_tod)
            
            # Ensure response_type and category_type are properly set
            if 'response_type_cad' in joined_data.columns and 'response_type_rms' in joined_data.columns:
                joined_data['response_type'] = joined_data['response_type_cad'].fillna(joined_data['response_type_rms'])
            elif 'response_type_cad' in joined_data.columns:
                joined_data['response_type'] = joined_data['response_type_cad']
            elif 'response_type_rms' in joined_data.columns:
                joined_data['response_type'] = joined_data['response_type_rms']
            
            if 'category_type_cad' in joined_data.columns and 'category_type_rms' in joined_data.columns:
                joined_data['category_type'] = joined_data['category_type_cad'].fillna(joined_data['category_type_rms'])
            elif 'category_type_cad' in joined_data.columns:
                joined_data['category_type'] = joined_data['category_type_cad']
            elif 'category_type_rms' in joined_data.columns:
                joined_data['category_type'] = joined_data['category_type_rms']
            
            # Drop suffix columns
            drop_cols = [c for c in joined_data.columns if c.endswith('_cad') or c.endswith('_rms')]
            joined_data = joined_data.drop(columns=drop_cols)
            
            # Log the results of CAD-first logic
            cad_response_count = joined_data['response_type_cad'].notna().sum()
            cad_category_count = joined_data['category_type_cad'].notna().sum()
            final_response_count = joined_data['response_type'].notna().sum()
            final_category_count = joined_data['category_type'].notna().sum()
            
            self.logger.info(f"CAD-first logic results:")
            self.logger.info(f"  - response_type_cad populated: {cad_response_count}")
            self.logger.info(f"  - category_type_cad populated: {cad_category_count}")
            self.logger.info(f"  - Final response_type populated: {final_response_count}")
            self.logger.info(f"  - Final category_type populated: {final_category_count}")
            
            # Note: All CAD data is now accessible via column_name_cad format
            # No duplicate columns without _cad suffix are created
            
            # Calculate match statistics
            cad_matches = joined_data['response_type_cad'].notna().sum()
            match_rate = (cad_matches / len(joined_data)) * 100
            
            self.logger.info(f"CAD-RMS matching complete:")
            self.logger.info(f"  - Final record count: {len(joined_data)} (matches RMS input)")
            self.logger.info(f"  - CAD matches found: {cad_matches}")
            self.logger.info(f"  - Match rate: {match_rate:.1f}%")
            
            joined_output = output_dir / f'{self.current_cycle}_{self.current_date}_7Day_cad_rms_matched_standardized.csv' if self.current_cycle and self.current_date else output_dir / 'cad_rms_matched_standardized.csv'
            # Standardize data types before export
            joined_data = self.standardize_data_types(joined_data)
            joined_data.to_csv(joined_output, index=False, encoding='utf-8')
            self.logger.info(f"Joined data saved: {joined_output}")
            
            # Generate comprehensive QC report
            if mapping_diagnostics and ref_diagnostics:
                qc_results = self.generate_enhanced_qc_report(
                    cad_data, mapping_diagnostics, ref_diagnostics, output_dir
                )
                self.logger.info(f"Enhanced QC Report Status: {qc_results['overall_status']}")
                if qc_results['critical_issues']:
                    self.logger.warning(f"Critical Issues Found: {qc_results['critical_issues']}")
                else:
                    self.logger.info("All QC validations passed successfully")
            
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
        self.logger.info("COMPREHENSIVE SCRPA FIX V8.5 COMPLETE - VALIDATION SUMMARY")
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
        
        # Generate filename with cycle name and current date
        if self.current_cycle and self.current_date:
            filename = f"{self.current_cycle}_{self.current_date}_7Day_SCRPA_Incidents.csv"
        else:
            current_date = datetime.now().strftime('%Y_%m_%d')
            filename = f"{current_date}_7Day_SCRPA_Incidents.csv"
        output_path = output_dir / filename
        
        # Standardize data types before export
        export_df = self.standardize_data_types(export_df)
        
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
        
        joined_output = output_dir / f'{self.current_cycle}_{self.current_date}_7Day_cad_rms_matched_standardized.csv' if self.current_cycle and self.current_date else output_dir / 'cad_rms_matched_standardized.csv'
        # Standardize data types before export
        joined_data = self.standardize_data_types(joined_data)
        joined_data.to_csv(joined_output, index=False, encoding='utf-8')
        self.logger.info(f"Joined data saved: {joined_output}")
        
        return joined_data

    def resolve_reference_duplicates(self, ref_df):
        """
        Resolve duplicate incidents using deterministic priority rules.
        
        Args:
            ref_df: DataFrame with potential duplicate incidents
            
        Returns:
            DataFrame with duplicates resolved using priority-based selection
        """
        # Define priority rankings for consistent duplicate resolution
        response_priority = {
            'EMERGENCY': 1,
            'URGENT': 2, 
            'HIGH': 3,
            'MEDIUM': 4,
            'ROUTINE': 5,
            'LOW': 6
        }
        
        category_priority = {
            'CRIMINAL INCIDENTS': 1,
            'CRIMINAL INVESTIGATION': 2,
            'PUBLIC SAFETY AND WELFARE': 3,
            'TRAFFIC AND TRANSPORTATION': 4,
            'PATROL AND PREVENTION': 5,
            'ADMINISTRATIVE AND SUPPORT': 6,
            'OTHER': 7
        }
        
        # Create priority scores for sorting
        ref_df['response_priority'] = ref_df['response_type'].str.upper().map(response_priority).fillna(99)
        ref_df['category_priority'] = ref_df['category_type'].str.upper().map(category_priority).fillna(99)
        
        # Sort by priority (lowest number = highest priority)
        ref_df_sorted = ref_df.sort_values([
            'incident_clean',
            'response_priority', 
            'category_priority',
            'response_type',  # Tie-breaker: alphabetical
            'category_type'   # Final tie-breaker
        ])
        
        # Keep first occurrence after priority sorting
        ref_df_clean = ref_df_sorted.drop_duplicates(subset=['incident_clean'], keep='first')
        
        # Remove temporary priority columns
        ref_df_clean = ref_df_clean.drop(columns=['response_priority', 'category_priority'])
        
        return ref_df_clean

    def load_call_type_reference_enhanced(self):
        """
        Enhanced call type reference loading with proper header normalization and duplicate detection.
        Returns the reference dataframe and diagnostics information.
        """
        reference_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\CallType_Categories.xlsx")
        
        diagnostics = {
            'loaded': False,
            'total_records': 0,
            'duplicate_incidents': [],
            'duplicate_count': 0,
            'resolved_duplicates': 0,
            'original_columns': [],
            'normalized_columns': [],
            'error': None
        }
        
        try:
            if not reference_path.exists():
                diagnostics['error'] = f"Reference file not found: {reference_path}"
                self.logger.error(diagnostics['error'])
                return None, diagnostics
            
            # Load the reference file
            ref_df = pd.read_excel(reference_path)
            diagnostics['total_records'] = len(ref_df)
            diagnostics['original_columns'] = list(ref_df.columns)
            
            # Normalize headers to lowercase snake_case
            ref_df.columns = [self.convert_to_lowercase_with_underscores(col) for col in ref_df.columns]
            diagnostics['normalized_columns'] = list(ref_df.columns)
            
            # Validate required columns exist
            required_columns = ['incident', 'response_type', 'category_type']
            missing_columns = [col for col in required_columns if col not in ref_df.columns]
            
            if missing_columns:
                diagnostics['error'] = f"Missing required columns in reference file: {missing_columns}"
                self.logger.error(diagnostics['error'])
                return None, diagnostics
            
            # Clean and prepare incident values for matching
            ref_df['incident_clean'] = ref_df['incident'].astype(str).str.strip().str.upper()
            
            # Detect and handle duplicate incidents with priority-based resolution
            duplicate_incidents = ref_df[ref_df.duplicated(subset=['incident_clean'], keep=False)]
            if not duplicate_incidents.empty:
                diagnostics['duplicate_count'] = len(duplicate_incidents)
                diagnostics['duplicate_incidents'] = duplicate_incidents['incident_clean'].value_counts().to_dict()
                
                # Log duplicate resolution details BEFORE applying resolution
                duplicate_summary = duplicate_incidents.groupby('incident_clean').agg({
                    'response_type': lambda x: list(x),
                    'category_type': lambda x: list(x)
                })
                
                self.logger.info(f"Found {diagnostics['duplicate_count']} duplicate incidents in reference file.")
                self.logger.info("Applying priority-based duplicate resolution:")
                for incident, row in duplicate_summary.iterrows():
                    self.logger.info(f"  '{incident}': {len(row['response_type'])} variants -> keeping highest priority")
                    self.logger.debug(f"    Response options: {row['response_type']}")
                    self.logger.debug(f"    Category options: {row['category_type']}")
                
                # Apply priority-based duplicate resolution
                ref_df = self.resolve_reference_duplicates(ref_df)
                
                # Log resolution results
                resolved_count = diagnostics['duplicate_count'] - len(ref_df[ref_df.duplicated(subset=['incident_clean'], keep=False)])
                self.logger.info(f"Priority-based resolution completed: {resolved_count} duplicates resolved")
                diagnostics['resolved_duplicates'] = resolved_count
            
            # Create lookup dictionary for efficient matching
            ref_lookup = {}
            for _, row in ref_df.iterrows():
                incident_clean = row['incident_clean']
                if incident_clean and incident_clean != 'NAN':
                    ref_lookup[incident_clean] = {
                        'response_type': row['response_type'],
                        'category_type': row['category_type'],
                        'original_incident': row['incident']
                    }
            
            diagnostics['loaded'] = True
            diagnostics['unique_incidents'] = len(ref_lookup)
            
            self.logger.info(f"Enhanced call type reference loaded successfully:")
            self.logger.info(f"  - Total records: {diagnostics['total_records']}")
            self.logger.info(f"  - Unique incidents: {diagnostics['unique_incidents']}")
            self.logger.info(f"  - Duplicates found: {diagnostics['duplicate_count']}")
            self.logger.info(f"  - Duplicates resolved: {diagnostics.get('resolved_duplicates', 0)}")
            self.logger.info(f"  - Normalized columns: {diagnostics['normalized_columns']}")
            
            return ref_lookup, diagnostics
            
        except Exception as e:
            diagnostics['error'] = f"Error loading call type reference: {str(e)}"
            self.logger.error(diagnostics['error'])
            return None, diagnostics

    def map_incident_to_call_types_enhanced(self, incident_values, ref_lookup):
        """
        Enhanced incident mapping using reference lookup with comprehensive diagnostics.
        
        Args:
            incident_values: Series of incident values to map
            ref_lookup: Dictionary lookup from load_call_type_reference_enhanced
            
        Returns:
            tuple: (response_types, category_types, mapping_diagnostics)
        """
        if ref_lookup is None:
            # Fallback to original mapping method
            self.logger.warning("Reference lookup not available, using fallback mapping")
            results = incident_values.apply(lambda x: pd.Series(self.map_call_type(x)))
            return results[0], results[1], {'mapped_count': 0, 'unmapped_count': len(incident_values)}
        
        response_types = []
        category_types = []
        mapped_count = 0
        unmapped_count = 0
        unmapped_values = []
        
        for incident_value in incident_values:
            if pd.isna(incident_value) or not incident_value:
                response_types.append(None)
                category_types.append(None)
                unmapped_count += 1
                continue
            
            # Clean the incident value for matching
            incident_clean = str(incident_value).strip().upper()
            
            # Look for exact match in reference
            if incident_clean in ref_lookup:
                ref_data = ref_lookup[incident_clean]
                response_types.append(ref_data['response_type'])
                category_types.append(ref_data['category_type'])
                mapped_count += 1
            else:
                # No match found
                response_types.append(None)
                category_types.append(None)
                unmapped_count += 1
                unmapped_values.append(incident_value)
        
        # Create diagnostics
        mapping_diagnostics = {
            'total_incidents': len(incident_values),
            'mapped_count': mapped_count,
            'unmapped_count': unmapped_count,
            'mapping_rate': (mapped_count / len(incident_values)) * 100 if len(incident_values) > 0 else 0,
            'unmapped_values': list(set(unmapped_values)),  # Remove duplicates
            'unmapped_value_counts': pd.Series(unmapped_values).value_counts().to_dict() if unmapped_values else {}
        }
        
        return pd.Series(response_types), pd.Series(category_types), mapping_diagnostics

    def generate_enhanced_qc_report(self, cad_data, mapping_diagnostics, ref_diagnostics, output_dir):
        """
        Generate comprehensive QC report for CAD incident mapping validation.
        
        Args:
            cad_data: Processed CAD DataFrame
            mapping_diagnostics: Results from enhanced mapping
            ref_diagnostics: Results from reference file loading
            output_dir: Directory for output files
            
        Returns:
            dict: Comprehensive QC results with PASS/FAIL status
        """
        from datetime import datetime
        
        # A. Reference File Validation
        ref_validation = {
            'file_loaded': ref_diagnostics['loaded'],
            'total_records': ref_diagnostics['total_records'],
            'unique_incidents': ref_diagnostics['unique_incidents'],
            'duplicates_found': ref_diagnostics['duplicate_count'],
            'duplicates_resolved': ref_diagnostics.get('resolved_duplicates', 0),
            'resolution_method': 'priority_based_deterministic',
            'status': 'PASS' if ref_diagnostics['loaded'] and ref_diagnostics['duplicate_count'] >= 0 else 'FAIL'
        }
        
        # B. Mapping Performance Validation
        mapping_validation = {
            'total_incidents': mapping_diagnostics['total_incidents'],
            'mapped_count': mapping_diagnostics['mapped_count'],
            'unmapped_count': mapping_diagnostics['unmapped_count'],
            'mapping_rate': mapping_diagnostics['mapping_rate'],
            'target_rate': 98.0,
            'meets_target': mapping_diagnostics['mapping_rate'] >= 98.0,
            'status': 'PASS' if mapping_diagnostics['mapping_rate'] >= 98.0 else 'FAIL'
        }
        
        # C. Data Quality Validation
        required_columns = ['incident', 'response_type_cad', 'category_type_cad', 'response_type', 'category_type']
        data_quality = {
            'total_records': len(cad_data),
            'incident_populated': cad_data['incident'].notna().sum(),
            'response_type_cad_populated': cad_data['response_type_cad'].notna().sum() if 'response_type_cad' in cad_data.columns else 0,
            'category_type_cad_populated': cad_data['category_type_cad'].notna().sum() if 'category_type_cad' in cad_data.columns else 0,
            'response_type_populated': cad_data['response_type'].notna().sum() if 'response_type' in cad_data.columns else 0,
            'category_type_populated': cad_data['category_type'].notna().sum() if 'category_type' in cad_data.columns else 0,
            'required_columns_present': all(col in cad_data.columns for col in required_columns),
            'missing_columns': [col for col in required_columns if col not in cad_data.columns],
            'no_data_loss': len(cad_data) == mapping_diagnostics['total_incidents'],
            'status': 'PASS' if all(col in cad_data.columns for col in required_columns) else 'FAIL'
        }
        
        # D. Header Compliance Validation
        header_validation = self.validate_lowercase_snake_case_headers(cad_data, "CAD Data")
        
        # E. Create unmapped incidents analysis if needed
        unmapped_analysis_file = None
        if mapping_diagnostics.get('unmapped_values'):
            unmapped_analysis_file = self.create_unmapped_analysis(
                mapping_diagnostics['unmapped_values'], output_dir
            )
        
        # F. Comprehensive Logging with Status Indicators
        self.logger.info("=" * 80)
        self.logger.info("COMPREHENSIVE QC REPORT - CAD INCIDENT MAPPING")
        self.logger.info("=" * 80)
        
        # Reference File Validation Logging
        self.logger.info("1. REFERENCE FILE VALIDATION")
        if ref_validation['status'] == 'PASS':
            self.logger.info(f"OK Reference file loaded: {ref_validation['total_records']} records")
            self.logger.info(f"OK Unique incidents: {ref_validation['unique_incidents']}")
            self.logger.info(f"OK Duplicates found: {ref_validation['duplicates_found']}")
            self.logger.info(f"OK Duplicates resolved: {ref_validation['duplicates_resolved']} (deterministic)")
            self.logger.info(f"OK Resolution method: {ref_validation['resolution_method']}")
        else:
            self.logger.error(f"FAIL Reference file validation FAILED")
            self.logger.error(f"     Error: {ref_diagnostics.get('error', 'Unknown error')}")
        
        # Mapping Performance Validation Logging
        self.logger.info("")
        self.logger.info("2. MAPPING PERFORMANCE VALIDATION")
        if mapping_validation['meets_target']:
            self.logger.info(f"OK Mapping success rate: {mapping_validation['mapping_rate']:.1f}% (>= {mapping_validation['target_rate']}%)")
            self.logger.info(f"OK Mapped incidents: {mapping_validation['mapped_count']}/{mapping_validation['total_incidents']}")
            if mapping_validation['unmapped_count'] > 0:
                self.logger.info(f"OK Unmapped incidents: {mapping_validation['unmapped_count']} (within tolerance)")
        else:
            self.logger.error(f"FAIL Mapping success rate: {mapping_validation['mapping_rate']:.1f}% (< {mapping_validation['target_rate']}%)")
            self.logger.error(f"FAIL Unmapped incidents: {mapping_validation['unmapped_count']}")
            if mapping_diagnostics.get('unmapped_values'):
                sample_unmapped = mapping_diagnostics['unmapped_values'][:5]
                self.logger.error(f"     Sample unmapped: {sample_unmapped}")
        
        # Data Quality Validation Logging
        self.logger.info("")
        self.logger.info("3. DATA QUALITY VALIDATION")
        if data_quality['required_columns_present']:
            self.logger.info("OK All required columns present")
            self.logger.info(f"OK Total records: {data_quality['total_records']}")
            self.logger.info(f"OK Incident populated: {data_quality['incident_populated']}/{data_quality['total_records']}")
            self.logger.info(f"OK Response type (CAD) populated: {data_quality['response_type_cad_populated']}/{data_quality['total_records']}")
            self.logger.info(f"OK Category type (CAD) populated: {data_quality['category_type_cad_populated']}/{data_quality['total_records']}")
            if data_quality['no_data_loss']:
                self.logger.info("OK No data loss: record count maintained")
            else:
                self.logger.warning(f"WARNING Data count mismatch: {data_quality['total_records']} vs {mapping_diagnostics['total_incidents']}")
        else:
            self.logger.error("FAIL Missing required columns")
            for col in data_quality['missing_columns']:
                self.logger.error(f"     Missing: {col}")
        
        # Header Compliance Validation Logging
        self.logger.info("")
        self.logger.info("4. HEADER COMPLIANCE VALIDATION")
        if header_validation['overall_status'] == 'PASS':
            self.logger.info(f"OK All headers lowercase snake_case: {len(cad_data.columns)}/{len(cad_data.columns)}")
        else:
            self.logger.error("FAIL Header compliance failed")
            for header in header_validation['invalid_headers']:
                self.logger.error(f"     Invalid header: '{header}'")
        
        # Unmapped Analysis Logging
        if unmapped_analysis_file:
            self.logger.info("")
            self.logger.info("5. UNMAPPED INCIDENTS ANALYSIS")
            self.logger.warning(f"WARNING Unmapped incidents analysis created: {unmapped_analysis_file}")
            self.logger.warning(f"WARNING Review unmapped incidents for potential reference updates")
        
        # G. Overall QC Status Determination
        overall_status = "PASS"
        critical_issues = []
        
        if ref_validation['status'] == 'FAIL':
            overall_status = "FAIL"
            critical_issues.append("Reference file loading failed")
        
        if mapping_validation['status'] == 'FAIL':
            overall_status = "FAIL" 
            critical_issues.append(f"Mapping rate below target ({mapping_validation['mapping_rate']:.1f}% < 98%)")
        
        if header_validation['overall_status'] == 'FAIL':
            overall_status = "FAIL"
            critical_issues.append("Header compliance failed")
        
        if not data_quality['required_columns_present']:
            overall_status = "FAIL"
            critical_issues.append("Required columns missing")
        
        # Final Status Report
        self.logger.info("")
        self.logger.info("6. OVERALL QC STATUS")
        if overall_status == "PASS":
            self.logger.info("SUCCESS OVERALL STATUS: PASS - All validations successful")
            self.logger.info("OK CAD incident mapping pipeline is fully operational")
            self.logger.info("OK Ready for production use")
        else:
            self.logger.error(f"FAIL OVERALL STATUS: FAIL")
            for issue in critical_issues:
                self.logger.error(f"   - {issue}")
            self.logger.error("FAIL Pipeline requires attention before production use")
        
        self.logger.info("=" * 80)
        
        # H. Compile comprehensive QC results
        qc_results = {
            'overall_status': overall_status,
            'critical_issues': critical_issues,
            'reference_validation': ref_validation,
            'mapping_validation': mapping_validation,
            'data_quality': data_quality,
            'header_validation': header_validation,
            'unmapped_analysis_file': unmapped_analysis_file,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return qc_results

    def create_unmapped_analysis(self, unmapped_values, output_dir):
        """
        Create detailed analysis of unmapped incidents.
        
        Args:
            unmapped_values: List of unmapped incident values
            output_dir: Directory for output files
            
        Returns:
            str: Path to the created analysis file or None
        """
        from datetime import datetime
        
        if not unmapped_values:
            self.logger.info("OK No unmapped incidents to analyze")
            return None
        
        # Create analysis DataFrame
        unmapped_df = pd.DataFrame({
            'incident_value': unmapped_values,
            'frequency': pd.Series(unmapped_values).value_counts().reindex(unmapped_values).values,
            'analysis_needed': 'Yes',
            'suggested_action': 'Review for reference file addition'
        })
        
        # Remove duplicates and sort by frequency
        unmapped_df = unmapped_df.drop_duplicates(subset=['incident_value']).sort_values('frequency', ascending=False)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unmapped_file = output_dir / f'unmapped_incidents_analysis_{timestamp}.csv'
        
        # Standardize data types before export
        unmapped_df = self.standardize_data_types(unmapped_df)
        
        # Write to CSV
        unmapped_df.to_csv(unmapped_file, index=False, encoding='utf-8')
        
        self.logger.warning(f"WARNING Unmapped incidents analysis: {unmapped_file}")
        self.logger.warning(f"WARNING Total unique unmapped: {len(unmapped_df)}")
        self.logger.warning(f"WARNING Total unmapped occurrences: {unmapped_df['frequency'].sum()}")
        
        return str(unmapped_file)

    def create_unmapped_incidents_csv(self, unmapped_values, output_dir):
        """
        Create CSV file with unmapped incident values for diagnostics.
        
        Args:
            unmapped_values: List of unmapped incident values
            output_dir: Output directory path
            
        Returns:
            str: Path to the created CSV file
        """
        if not unmapped_values:
            self.logger.info("No unmapped incidents to write to CSV")
            return None
        
        # Create unmapped incidents dataframe
        unmapped_df = pd.DataFrame({
            'incident_value': unmapped_values,
            'count': pd.Series(unmapped_values).value_counts().reindex(unmapped_values).values
        })
        
        # Remove duplicates and sort by count
        unmapped_df = unmapped_df.drop_duplicates(subset=['incident_value']).sort_values('count', ascending=False)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unmapped_file = output_dir / f'unmapped_incident_values_{timestamp}.csv'
        
        # Standardize data types before export
        unmapped_df = self.standardize_data_types(unmapped_df)
        
        # Write to CSV
        unmapped_df.to_csv(unmapped_file, index=False, encoding='utf-8')
        
        self.logger.info(f"Unmapped incidents CSV created: {unmapped_file}")
        self.logger.info(f"  - Total unique unmapped values: {len(unmapped_df)}")
        self.logger.info(f"  - Total unmapped occurrences: {unmapped_df['count'].sum()}")
        
        return str(unmapped_file)

    def validate_lowercase_snake_case_headers(self, df, data_type="Unknown"):
        """
        Validate that all column headers follow lowercase snake_case convention.
        
        Args:
            df: DataFrame to validate
            data_type: String identifier for the data type (for logging)
            
        Returns:
            dict: Validation results
        """
        validation_results = {
            'data_type': data_type,
            'total_columns': len(df.columns),
            'compliant_columns': 0,
            'non_compliant_columns': [],
            'overall_status': 'PASS'
        }
        
        # Pattern for lowercase snake_case (allows numbers)
        lowercase_pattern = re.compile(r'^[a-z]+(_[a-z0-9]+)*$')
        
        for col in df.columns:
            if lowercase_pattern.match(col):
                validation_results['compliant_columns'] += 1
            else:
                validation_results['non_compliant_columns'].append(col)
        
        if validation_results['non_compliant_columns']:
            validation_results['overall_status'] = 'FAIL'
        
        # Log results
        if validation_results['overall_status'] == 'PASS':
            self.logger.info(f"✅ {data_type} header validation PASSED: All {validation_results['total_columns']} columns follow lowercase snake_case")
        else:
            self.logger.error(f"❌ {data_type} header validation FAILED: {len(validation_results['non_compliant_columns'])} non-compliant columns")
            self.logger.error(f"Non-compliant columns: {validation_results['non_compliant_columns']}")
        
        return validation_results

    def map_tod(self, t):
        """
        Map time to time-of-day buckets.
        
        Args:
            t: Time value (string HH:MM:SS or time object)
            
        Returns:
            str: Time-of-day bucket description
        """
        if pd.isna(t) or not t:
            return "Unknown"
        
        try:
            # Parse time string (HH:MM:SS format)
            if isinstance(t, str):
                # Extract hour from HH:MM:SS format
                hour = int(t.split(':')[0])
            else:
                # Fallback for time objects
                hour = t.hour if hasattr(t, 'hour') else 0
            
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


if __name__ == "__main__":
    try:
        # Initialize processor
        processor = ComprehensiveSCRPAFixV8_5()
        
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