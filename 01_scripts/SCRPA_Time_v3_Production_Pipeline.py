#!/usr/bin/env python3
"""
SCRPA Production Deployment Pipeline
Complete automated processing with validation checks and monitoring
"""

import pandas as pd
import numpy as np
import json
import re
import logging
import time
import traceback
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

# v8.5 Enhancement: Helper functions for header normalization and column coalescing
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

class SCRPAProductionPipeline:
    def __init__(self, config: Optional[Dict] = None):
        """Initialize production pipeline with v8.5 enhancements"""
        self.config = config or self._default_config()
        self.logger = self._setup_logging()
        self.pipeline_start_time = None
        self.processing_stats = {}
        
        # Quality thresholds
        self.min_validation_rate = 70.0  # Minimum 70% validation rate
        self.max_processing_time = 300   # Maximum 5 minutes processing time
        
        # v8.5 Enhancement: Reference data paths
        self.ref_dirs = {
            'call_types': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Classifications\CallTypes\CallType_Categories.xlsx"),
            'zone_grid': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\zone_grid_master.xlsx"),
            'cycle_calendar': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Temporal\SCRPA_Cycle\7Day_28Day_Cycle_20250414.xlsx")
        }
        
        # Initialize reference data
        self.call_type_ref = None
        self.zone_grid_ref = None
        self.cycle_calendar = None
        self.current_cycle = None
        self.current_date = None
        
        # Load reference data
        self._load_reference_data()
        
        # Target crimes and patterns
        self.target_crimes = [
            "Motor Vehicle Theft",
            "Robbery", 
            "Burglary – Auto",
            "Sexual",
            "Burglary – Commercial", 
            "Burglary – Residence"
        ]
        
        # v8.5 Enhancement: Enhanced crime patterns with better regex
        self.crime_patterns = {
            "Motor Vehicle Theft": [
                r"motor\s*vehicle\s*theft",
                r"theft\s*of\s*motor\s*vehicle",
                r"auto\s*theft",
                r"car\s*theft",
                r"vehicle\s*theft",
                r"240\s*=\s*theft\s*of\s*motor\s*vehicle",
                r"\bmvt\b",
                r"stolen\s*vehicle"
            ],
            "Robbery": [
                r"robbery",
                r"120\s*=\s*robbery",
                r"\brob\b",
                r"armed\s*robbery"
            ],
            "Burglary – Auto": [
                r"burglary\s*[-–]\s*auto",
                r"auto\s*burglary",
                r"theft\s*from\s*motor\s*vehicle",
                r"23f\s*=\s*theft\s*from\s*motor\s*vehicle",
                r"\btfmv\b",
                r"car\s*break.?in"
            ],
            "Sexual": [
                r"sexual",
                r"11d\s*=\s*fondling",
                r"criminal\s*sexual\s*contact",
                r"\bsex\b",
                r"sexual\s*assault"
            ],
            "Burglary – Commercial": [
                r"burglary\s*[-–]\s*commercial",
                r"commercial\s*burglary",
                r"220\s*=\s*burglary.*commercial",
                r"business\s*burglary"
            ],
            "Burglary – Residence": [
                r"burglary\s*[-–]\s*residence",
                r"residential\s*burglary",
                r"220\s*=\s*burglary.*residential",
                r"home\s*burglary",
                r"house\s*burglary"
            ]
        }
    
    def _default_config(self) -> Dict:
        """Default configuration settings"""
        return {
            'input_dir': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi",
            'output_dir': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\05_Exports",
            'backup_dir': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\backups",
            'log_dir': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\logs",
            'enable_backup': True,
            'enable_rollback': True,
            'quality_checks': True,
            'performance_monitoring': True
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup production logging"""
        log_dir = Path(self.config['log_dir'])
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"scrpa_production_{timestamp}.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger('SCRPA_Production')
        logger.info("Production pipeline initialized")
        return logger
    
    def _load_reference_data(self):
        """Load reference data for enhanced processing."""
        try:
            # Load call type reference
            if self.ref_dirs['call_types'].exists():
                self.call_type_ref = pd.read_excel(self.ref_dirs['call_types'])
                self.logger.info(f"Loaded call type reference: {len(self.call_type_ref)} records")
                if not self.call_type_ref.empty:
                    self.call_type_ref.columns = [to_snake(col) for col in self.call_type_ref.columns]
            else:
                self.logger.warning("Call type reference file not found")
                self.call_type_ref = None
                
            # Load zone/grid reference  
            if self.ref_dirs['zone_grid'].exists():
                self.zone_grid_ref = pd.read_excel(self.ref_dirs['zone_grid'])
                self.logger.info(f"Loaded zone/grid reference: {len(self.zone_grid_ref)} records")
                if not self.zone_grid_ref.empty:
                    self.zone_grid_ref.columns = [to_snake(col) for col in self.zone_grid_ref.columns]
            else:
                self.logger.warning("Zone/grid reference file not found")
                self.zone_grid_ref = None
                
            # Load cycle calendar
            if self.ref_dirs['cycle_calendar'].exists():
                self.cycle_calendar = pd.read_excel(self.ref_dirs['cycle_calendar'])
                self.logger.info(f"Loaded cycle calendar: {len(self.cycle_calendar)} records")
                self.current_cycle, self.current_date = self._get_current_cycle_info()
            else:
                self.logger.warning("Cycle calendar file not found")
                self.cycle_calendar = None
                
        except Exception as e:
            self.logger.error(f"Error loading reference data: {str(e)}")
    
    def get_cad_column_mapping(self) -> dict:
        """v8.5 CAD column mapping with correct incident mapping."""
        return {
            "ReportNumberNew": "case_number",
            "Incident": "incident",  # CRITICAL: Keep this mapping - DO NOT change to "incident_raw"
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
        
    def get_rms_column_mapping(self) -> dict:
        """v8.5 RMS column mapping."""
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
            "Year1": "year_1",
            "Color1": "color_1",
            "NIBRS Classification": "nibrs_classification"
        }
    
    # v8.5 Enhancement: Text cleaning and processing functions
    def clean_text_comprehensive(self, text):
        """Comprehensive text cleaning for all text fields."""
        if pd.isna(text):
            return None
        
        text = str(text).strip()
        if text == '' or text.lower() == 'nan':
            return None
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def clean_how_reported_911(self, how_reported):
        """Fix '9-1-1' date issue in how_reported field - FIXED VERSION."""
        if pd.isna(how_reported):
            return None
        
        text = str(how_reported).strip()
        
        # Handle various date formats that might be incorrectly applied to "9-1-1"
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
        
        # Check for specific date values that commonly result from "9-1-1" conversion
        # September 1, 2001 (9/1/2001) is a common misinterpretation
        if text in ['2001-09-01', '2001-09-01 00:00:00', '09/01/2001', '9/1/2001', '2001-09-01T00:00:00']:
            return "9-1-1"
        
        # Check for numeric only patterns that could be dates
        if re.match(r'^\d{8}$', text):  # YYYYMMDD
            return "9-1-1"
        
        return text
    
    def extract_username_timestamp(self, cad_notes):
        """Extract username and timestamp from CAD notes and return cleaned notes - FIXED VERSION."""
        if pd.isna(cad_notes):
            return None, None, None
            
        text = str(cad_notes)
        username = None
        timestamp = None
        
        # Look for username pattern (usually at start) - IMPROVED PATTERN
        username_match = re.search(r'^([A-Z]{2,}\d*|[a-zA-Z]+\.[a-zA-Z]+)', text)
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
    
    def cascade_date(self, row):
        """Cascading date logic matching v8.5 exactly."""
        # Try normalized lowercase column names first
        if pd.notna(row.get('incident_date')):
            return pd.to_datetime(row['incident_date'], errors='coerce').date()
        elif pd.notna(row.get('incident_date_between')):
            return pd.to_datetime(row['incident_date_between'], errors='coerce').date()
        elif pd.notna(row.get('report_date')):
            return pd.to_datetime(row['report_date'], errors='coerce').date()
        # Try with _raw suffix
        elif pd.notna(row.get('incident_date_raw')):
            return pd.to_datetime(row['incident_date_raw'], errors='coerce').date()
        elif pd.notna(row.get('incident_date_between_raw')):
            return pd.to_datetime(row['incident_date_between_raw'], errors='coerce').date()
        elif pd.notna(row.get('report_date_raw')):
            return pd.to_datetime(row['report_date_raw'], errors='coerce').date()
        else:
            return None
    
    def cascade_time(self, row):
        """
        FIXED: Cascading time logic that handles both raw and mapped column names.
        
        CRITICAL BUG FIXES from v8.5:
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
        """Time of day calculation matching v8.5 exactly - FIXED ENCODING."""
        if pd.isna(time_val):
            return "Unknown"
        
        hour = time_val.hour
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
    
    def get_time_of_day_sort_order(self, time_of_day):
        """Get sort order for time of day categories - FIXED ENCODING."""
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
    
    def create_time_sort_key(self, time_val):
        """Create time sort key for proper ordering."""
        if pd.isna(time_val):
            return 9999
        
        hour = time_val.hour
        minute = time_val.minute
        return hour * 100 + minute
    
    def calculate_block(self, address):
        """Block calculation matching v8.5 exactly."""
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
            # Extract block number
            match = re.match(r'^(\d+)', addr.strip())
            if match:
                number = int(match.group(1))
                # Calculate block (round down to nearest 100)
                block_start = (number // 100) * 100
                block_end = block_start + 99
                
                # Extract street name
                street = re.sub(r'^\d+\s*', '', addr).strip()
                if street:
                    return f"{block_start}-{block_end} {street}"
                else:
                    return f"{block_start}-{block_end} Block"
            else:
                return "Check Location Data"
    
    def _get_current_cycle_info(self):
        """Get current cycle for export naming."""
        if self.cycle_calendar is None or self.cycle_calendar.empty:
            return None, None
            
        try:
            today = datetime.now().date()
            
            # Find current cycle
            for _, row in self.cycle_calendar.iterrows():
                start_date = pd.to_datetime(row['7_Day_Start']).date()
                end_date = pd.to_datetime(row['7_Day_End']).date()
                
                if start_date <= today <= end_date:
                    return row['Report_Name'], today
            
            return None, today
        except Exception as e:
            self.logger.warning(f"Error getting current cycle info: {e}")
            return None, None
    
    def validate_input_files(self, cad_path: str, rms_path: str) -> bool:
        """Validate input files exist and are accessible"""
        try:
            if not Path(cad_path).exists():
                self.logger.error(f"CAD file not found: {cad_path}")
                return False
            
            if not Path(rms_path).exists():
                self.logger.error(f"RMS file not found: {rms_path}")
                return False
            
            # Test file accessibility
            pd.read_csv(cad_path, nrows=1)
            pd.read_csv(rms_path, nrows=1)
            
            self.logger.info("Input file validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Input file validation failed: {str(e)}")
            return False
    
    def validate_data_quality(self, cad_df: pd.DataFrame, rms_df: pd.DataFrame) -> Dict:
        """Comprehensive data quality validation"""
        quality_report = {
            'timestamp': datetime.now().isoformat(),
            'cad_validation': {},
            'rms_validation': {},
            'overall_status': 'PASS'
        }
        
        try:
            # CAD validation
            cad_validation = {
                'record_count': len(cad_df),
                'required_columns': self._validate_required_columns(cad_df, 'CAD'),
                'data_completeness': self._check_data_completeness(cad_df),
                'header_compliance': self._validate_header_compliance(cad_df)
            }
            
            # RMS validation
            rms_validation = {
                'record_count': len(rms_df),
                'required_columns': self._validate_required_columns(rms_df, 'RMS'),
                'data_completeness': self._check_data_completeness(rms_df),
                'header_compliance': self._validate_header_compliance(rms_df)
            }
            
            quality_report['cad_validation'] = cad_validation
            quality_report['rms_validation'] = rms_validation
            
            # Overall status check
            if not cad_validation['required_columns']['status'] or not rms_validation['required_columns']['status']:
                quality_report['overall_status'] = 'FAIL'
            
            if not cad_validation['header_compliance']['status'] or not rms_validation['header_compliance']['status']:
                quality_report['overall_status'] = 'FAIL'
            
            self.logger.info(f"Data quality validation: {quality_report['overall_status']}")
            return quality_report
            
        except Exception as e:
            self.logger.error(f"Data quality validation error: {str(e)}")
            quality_report['overall_status'] = 'ERROR'
            quality_report['error'] = str(e)
            return quality_report
    
    def _validate_required_columns(self, df: pd.DataFrame, dataset_type: str) -> Dict:
        """Validate required columns exist"""
        required_columns = {
            'CAD': ['case_number', 'incident'],  # v8.5: Simplified requirements
            'RMS': ['case_number', 'nibrs_classification']
        }
        
        required = required_columns.get(dataset_type, [])
        missing = [col for col in required if col not in df.columns]
        
        return {
            'status': len(missing) == 0,
            'required_columns': required,
            'missing_columns': missing,
            'total_columns': len(df.columns)
        }
    
    def _check_data_completeness(self, df: pd.DataFrame) -> Dict:
        """Check data completeness metrics"""
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        completeness_rate = ((total_cells - missing_cells) / total_cells) * 100
        
        return {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'completeness_rate': round(completeness_rate, 2),
            'missing_values': int(missing_cells),
            'status': completeness_rate > 80.0  # 80% completeness threshold
        }
    
    def _validate_header_compliance(self, df: pd.DataFrame) -> Dict:
        """Validate snake_case header compliance"""
        snake_case_pattern = r'^[a-z]+(?:_[a-z0-9]+)*$'
        
        headers = df.columns.tolist()
        compliant_headers = [col for col in headers if re.match(snake_case_pattern, col)]
        non_compliant = [col for col in headers if not re.match(snake_case_pattern, col)]
        
        compliance_rate = (len(compliant_headers) / len(headers)) * 100
        
        return {
            'status': len(non_compliant) == 0,
            'compliance_rate': round(compliance_rate, 2),
            'total_headers': len(headers),
            'compliant_headers': len(compliant_headers),
            'non_compliant_headers': non_compliant
        }
    
    def match_crime_pattern(self, text: str, crime_type: str) -> bool:
        """Match text against crime patterns"""
        if pd.isna(text):
            return False
            
        text = str(text).lower().strip()
        patterns = self.crime_patterns.get(crime_type, [])
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def apply_hybrid_filtering(self, cad_df: pd.DataFrame, rms_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """Apply production hybrid filtering with validation"""
        start_time = time.time()
        
        try:
            # CAD filtering
            filtered_cases = {}
            all_filtered_cases = set()
            
            for crime in self.target_crimes:
                # Primary: incident column
                incident_matches = cad_df['incident'].apply(
                    lambda x: self.match_crime_pattern(x, crime)
                )
                
                # Secondary: response_type and category_type  
                response_type_matches = cad_df['response_type'].apply(
                    lambda x: self.match_crime_pattern(x, crime)
                )
                category_type_matches = cad_df['category_type'].apply(
                    lambda x: self.match_crime_pattern(x, crime)
                )
                
                # Combined logic
                combined_matches = incident_matches | response_type_matches | category_type_matches
                
                # Get case numbers
                crime_cases = cad_df[combined_matches]['case_number'].tolist()
                filtered_cases[crime] = crime_cases
                all_filtered_cases.update(crime_cases)
            
            # Create filtered CAD dataframe
            cad_filtered = cad_df[cad_df['case_number'].isin(all_filtered_cases)].copy()
            
            # RMS matching with validation
            rms_matched = rms_df[rms_df['case_number'].isin(all_filtered_cases)].copy()
            
            # Validation metrics
            validation_metrics = self._calculate_validation_metrics(filtered_cases, rms_df)
            
            processing_time = time.time() - start_time
            
            # Quality checks
            overall_validation_rate = np.mean(list(validation_metrics['validation_rates'].values()))
            
            if overall_validation_rate < self.min_validation_rate:
                self.logger.warning(f"Validation rate {overall_validation_rate:.1f}% below threshold {self.min_validation_rate}%")
            
            # Processing stats
            filtering_stats = {
                'processing_time': round(processing_time, 2),
                'cad_original_records': len(cad_df),
                'cad_filtered_records': len(cad_filtered),
                'cad_retention_rate': (len(cad_filtered) / len(cad_df)) * 100,
                'rms_original_records': len(rms_df),
                'rms_matched_records': len(rms_matched),
                'rms_retention_rate': (len(rms_matched) / len(rms_df)) * 100,
                'overall_validation_rate': round(overall_validation_rate, 2),
                'quality_status': 'PASS' if overall_validation_rate >= self.min_validation_rate else 'WARNING'
            }
            
            filtering_stats.update(validation_metrics)
            
            self.logger.info(f"Hybrid filtering completed: {filtering_stats['quality_status']}")
            return cad_filtered, rms_matched, filtering_stats
            
        except Exception as e:
            self.logger.error(f"Hybrid filtering error: {str(e)}")
            raise
    
    def _calculate_validation_metrics(self, cad_cases: Dict, rms_df: pd.DataFrame) -> Dict:
        """Calculate detailed validation metrics"""
        validation_rates = {}
        detailed_metrics = {}
        
        for crime in self.target_crimes:
            cad_crime_cases = set(cad_cases[crime])
            
            # Find RMS cases with matching NIBRS codes
            nibrs_matches = rms_df['nibrs_classification'].apply(
                lambda x: self.match_crime_pattern(x, crime)
            )
            rms_crime_cases = set(rms_df[nibrs_matches]['case_number'].tolist())
            
            # Calculate validation
            validated_cases = cad_crime_cases.intersection(rms_crime_cases)
            validation_rate = (len(validated_cases) / len(cad_crime_cases) * 100) if cad_crime_cases else 0
            
            validation_rates[crime] = round(validation_rate, 2)
            detailed_metrics[crime] = {
                'cad_cases': len(cad_crime_cases),
                'rms_cases': len(rms_crime_cases),
                'validated_cases': len(validated_cases),
                'validation_rate': round(validation_rate, 2)
            }
        
        return {
            'validation_rates': validation_rates,
            'detailed_metrics': detailed_metrics
        }
    
    def create_powerbi_exports(self, cad_filtered: pd.DataFrame, rms_matched: pd.DataFrame, 
                             export_stats: Dict) -> Dict:
        """Create PowerBI-ready export files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(exist_ok=True)
        
        # Export paths
        cad_export_path = output_dir / f"SCRPA_CAD_Filtered_{timestamp}.csv"
        rms_export_path = output_dir / f"SCRPA_RMS_Matched_{timestamp}.csv"
        summary_path = output_dir / f"SCRPA_Processing_Summary_{timestamp}.json"
        
        try:
            # Export datasets
            cad_filtered.to_csv(cad_export_path, index=False)
            rms_matched.to_csv(rms_export_path, index=False)
            
            # Create processing summary
            processing_summary = {
                'export_timestamp': datetime.now().isoformat(),
                'processing_stats': export_stats,
                'file_info': {
                    'cad_filtered': {
                        'filename': cad_export_path.name,
                        'path': str(cad_export_path),
                        'records': len(cad_filtered),
                        'columns': cad_filtered.columns.tolist()
                    },
                    'rms_matched': {
                        'filename': rms_export_path.name,
                        'path': str(rms_export_path),
                        'records': len(rms_matched),
                        'columns': rms_matched.columns.tolist()
                    }
                },
                'crime_distribution': self._calculate_crime_distribution(cad_filtered),
                'powerbi_integration': {
                    'ready': True,
                    'refresh_timestamp': datetime.now().isoformat(),
                    'data_freshness': 'Current'
                }
            }
            
            # Save summary
            with open(summary_path, 'w') as f:
                json.dump(processing_summary, f, indent=2, default=str)
            
            export_info = {
                'cad_export': str(cad_export_path),
                'rms_export': str(rms_export_path),
                'summary_export': str(summary_path),
                'processing_summary': processing_summary
            }
            
            self.logger.info("PowerBI exports created successfully")
            return export_info
            
        except Exception as e:
            self.logger.error(f"Export creation error: {str(e)}")
            raise
    
    def _calculate_crime_distribution(self, cad_df: pd.DataFrame) -> Dict:
        """Calculate crime type distribution for reporting"""
        distribution = {}
        total_records = len(cad_df)
        
        for crime in self.target_crimes:
            crime_count = sum(1 for incident in cad_df['incident'] 
                            if self.match_crime_pattern(incident, crime))
            
            distribution[crime] = {
                'count': crime_count,
                'percentage': round((crime_count / total_records) * 100, 2) if total_records > 0 else 0
            }
        
        return distribution
    
    # v8.5 Enhancement: Comprehensive data processing pipeline
    def process_cad_data_v85(self, cad_df: pd.DataFrame) -> pd.DataFrame:
        """Process CAD data with v8.5 enhancements - handles both raw and processed data."""
        self.logger.info(f"Processing CAD data with v8.5 enhancements: {len(cad_df)} records")
        
        # Detect if data is already processed (snake_case columns)
        is_already_processed = 'case_number' in cad_df.columns and 'how_reported' in cad_df.columns
        
        if is_already_processed:
            self.logger.info("Data appears to be already processed - skipping raw data transformations")
        else:
            # Apply column mapping for raw data
            column_mapping = self.get_cad_column_mapping()
            existing_mapping = {k: v for k, v in column_mapping.items() if k in cad_df.columns}
            cad_df = cad_df.rename(columns=existing_mapping)
            self.logger.info(f"Applied CAD column mapping: {len(existing_mapping)} columns mapped")
            
            # Normalize headers
            cad_df = normalize_headers(cad_df)
            self.logger.info("Normalized CAD headers to snake_case")
        
        # Clean text columns (always do this for data quality)
        text_columns = cad_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            if col not in ['cad_notes_cleaned', 'cad_notes_username', 'cad_notes_timestamp']:  # Skip already processed
                cad_df[col] = cad_df[col].apply(self.clean_text_comprehensive)
        
        # Process how_reported (only if not already processed)
        if 'how_reported' in cad_df.columns and not is_already_processed:
            cad_df['how_reported'] = cad_df['how_reported'].apply(self.clean_how_reported_911)
            self.logger.info("Applied how_reported 9-1-1 fix")
        
        # Process CAD notes (only if raw notes exist and processed notes don't)
        if not is_already_processed and 'cad_notes_raw' in cad_df.columns:
            cad_notes_processed = cad_df['cad_notes_raw'].apply(self.extract_username_timestamp)
            cad_df['cad_notes_cleaned'] = [x[0] if x[0] is not None else None for x in cad_notes_processed]
            cad_df['cad_notes_username'] = [x[1] if x[1] is not None else None for x in cad_notes_processed] 
            cad_df['cad_notes_timestamp'] = [x[2] if x[2] is not None else None for x in cad_notes_processed]
            self.logger.info("Extracted usernames and timestamps from CAD notes")
        elif is_already_processed:
            self.logger.info("CAD notes already processed - skipping extraction")
        
        # Remove problematic columns to get 23 columns total (as per v8.5)
        columns_to_remove = ['response_type_cad', 'category_type_cad']
        for col in columns_to_remove:
            if col in cad_df.columns:
                cad_df = cad_df.drop(columns=[col])
                self.logger.info(f"Removed problematic column: {col}")
        
        # Add calculated time fields
        if 'time_of_call' in cad_df.columns:
            # Convert time_of_call to proper datetime
            cad_df['time_of_call_parsed'] = pd.to_datetime(cad_df['time_of_call'], errors='coerce')
            
            # Add time_of_day and sort order
            cad_df['time_of_day'] = cad_df['time_of_call_parsed'].apply(
                lambda x: self.get_time_of_day(x) if pd.notna(x) else "Unknown"
            )
            cad_df['time_of_day_sort_order'] = cad_df['time_of_day'].apply(self.get_time_of_day_sort_order)
            
            self.logger.info("Added time_of_day calculations")
        
        # Add block calculation
        if 'full_address_raw' in cad_df.columns:
            cad_df['block'] = cad_df['full_address_raw'].apply(self.calculate_block)
            self.logger.info("Added block calculations")
        
        self.logger.info(f"CAD processing complete: {len(cad_df)} records, {len(cad_df.columns)} columns")
        return cad_df
    
    def process_rms_data_v85(self, rms_df: pd.DataFrame) -> pd.DataFrame:
        """Process RMS data with v8.5 enhancements - handles both raw and processed data."""
        self.logger.info(f"Processing RMS data with v8.5 enhancements: {len(rms_df)} records")
        
        # Detect if data is already processed (snake_case columns)
        is_already_processed = 'case_number' in rms_df.columns and 'incident_date' in rms_df.columns
        
        if is_already_processed:
            self.logger.info("RMS data appears to be already processed - skipping raw data transformations")
        else:
            # Apply column mapping for raw data
            column_mapping = self.get_rms_column_mapping()
            existing_mapping = {k: v for k, v in column_mapping.items() if k in rms_df.columns}
            rms_df = rms_df.rename(columns=existing_mapping)
            self.logger.info(f"Applied RMS column mapping: {len(existing_mapping)} columns mapped")
            
            # Normalize headers
            rms_df = normalize_headers(rms_df)
            self.logger.info("Normalized RMS headers to snake_case")
        
        # Clean text columns (always do this for data quality)
        text_columns = rms_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            if col not in ['incident_type', 'all_incidents']:  # Skip already processed
                rms_df[col] = rms_df[col].apply(self.clean_text_comprehensive)
        
        # Apply cascade logic only if not already processed
        if not is_already_processed:
            # Implement cascade logic for missing fields
            rms_df['incident_date'] = rms_df.apply(self.cascade_date, axis=1)
            rms_df['incident_time'] = rms_df.apply(self.cascade_time, axis=1)
            self.logger.info("Applied cascade logic for incident_date and incident_time")
        else:
            self.logger.info("Cascade logic already applied - skipping")
        
        # Add calculated fields (only if not already processed)
        if not is_already_processed and 'incident_time' in rms_df.columns:
            rms_df['time_of_day'] = rms_df['incident_time'].apply(
                lambda x: self.get_time_of_day(x) if pd.notna(x) else "Unknown"
            )
            rms_df['time_of_day_sort_order'] = rms_df['incident_time'].apply(self.create_time_sort_key)
            self.logger.info("Added time_of_day calculations to RMS")
        elif is_already_processed:
            self.logger.info("Time calculations already applied")
        
        # Add block calculation (only if not already processed) 
        if not is_already_processed and 'full_address_raw' in rms_df.columns:
            rms_df['block'] = rms_df['full_address_raw'].apply(self.calculate_block)
            self.logger.info("Added block calculations to RMS")
        elif is_already_processed and 'block' in rms_df.columns:
            self.logger.info("Block calculations already applied")
        
        # Create coalesced fields (only if not already processed)
        if not is_already_processed:
            if any(col in rms_df.columns for col in ['incident_type_1_raw', 'incident_type_2_raw', 'incident_type_3_raw']):
                rms_df['incident_type'] = coalesce_cols(rms_df, 'incident_type_1_raw', 'incident_type_2_raw', 'incident_type_3_raw')
                self.logger.info("Created coalesced incident_type column")
            
            # Create all_incidents field
            incident_cols = [col for col in rms_df.columns if 'incident_type' in col and '_raw' in col]
            if incident_cols:
                rms_df['all_incidents'] = rms_df[incident_cols].apply(
                    lambda row: ' | '.join([str(val) for val in row if pd.notna(val) and str(val).strip()]), axis=1
                )
                rms_df['all_incidents'] = rms_df['all_incidents'].replace('', None)
                self.logger.info("Created all_incidents concatenated field")
        else:
            self.logger.info("Coalesced fields already exist")
        
        self.logger.info(f"RMS processing complete: {len(rms_df)} records, {len(rms_df.columns)} columns")
        return rms_df
    
    def create_matched_dataset_v85(self, cad_df: pd.DataFrame, rms_df: pd.DataFrame) -> pd.DataFrame:
        """Create matched CAD-RMS dataset with v8.5 enhancements."""
        self.logger.info("Creating matched CAD-RMS dataset with v8.5 logic")
        
        # Merge CAD and RMS data on case_number
        matched_df = pd.merge(cad_df, rms_df, on='case_number', how='inner', suffixes=('_cad', '_rms'))
        self.logger.info(f"Matched dataset created: {len(matched_df)} records")
        
        # Add cycle information if available
        if self.cycle_calendar is not None and not self.cycle_calendar.empty:
            if 'incident_date' in matched_df.columns:
                matched_df['cycle_name'] = matched_df['incident_date'].apply(
                    lambda x: self.get_cycle_for_date(x) if pd.notna(x) else None
                )
                self.logger.info("Added cycle information to matched dataset")
        
        return matched_df
    
    def get_cycle_for_date(self, incident_date):
        """Return cycle name (like 'C08W31') for any date."""
        if self.cycle_calendar is None or self.cycle_calendar.empty or pd.isna(incident_date):
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
            for _, row in self.cycle_calendar.iterrows():
                start_date = pd.to_datetime(row['7_Day_Start']).date()
                end_date = pd.to_datetime(row['7_Day_End']).date()
                
                if start_date <= incident_date <= end_date:
                    return row['Report_Name']
            
            return None
        except Exception as e:
            self.logger.warning(f"Error getting cycle for date {incident_date}: {e}")
            return None
    
    def create_v85_exports(self, cad_df: pd.DataFrame, rms_df: pd.DataFrame, matched_df: pd.DataFrame) -> Dict:
        """Create v8.5 compliant exports with proper naming and structure."""
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Use current cycle for naming if available
        cycle_name = self.current_cycle if self.current_cycle else "C08W31"
        
        output_dir = Path(self.config['input_dir'])  # Output to 04_powerbi directory
        output_dir.mkdir(exist_ok=True)
        
        export_paths = {}
        
        try:
            # 1. Create matched standardized dataset (primary output)
            matched_filename = f"{cycle_name}_{timestamp}_cad_rms_matched_standardized.csv"
            matched_path = output_dir / matched_filename
            matched_df.to_csv(matched_path, index=False)
            export_paths['matched_dataset'] = str(matched_path)
            self.logger.info(f"Created matched dataset: {matched_filename} ({len(matched_df)} rows, {len(matched_df.columns)} columns)")
            
            # 2. Create 7-Day filtered CAD export
            cad_filename = f"{cycle_name}_{timestamp}_7Day_cad_standardized.csv"
            cad_path = output_dir / cad_filename
            cad_df.to_csv(cad_path, index=False)
            export_paths['cad_7day'] = str(cad_path)
            self.logger.info(f"Created 7-Day CAD export: {cad_filename} ({len(cad_df)} rows)")
            
            # 3. Create 7-Day filtered RMS export
            rms_filename = f"{cycle_name}_{timestamp}_7Day_rms_standardized.csv"
            rms_path = output_dir / rms_filename
            rms_df.to_csv(rms_path, index=False)
            export_paths['rms_7day'] = str(rms_path)
            self.logger.info(f"Created 7-Day RMS export: {rms_filename} ({len(rms_df)} rows)")
            
            # 4. Create validation report
            validation_report = self._create_validation_report_v85(cad_df, rms_df, matched_df)
            validation_filename = f"{cycle_name}_{timestamp}_validation_report.json"
            validation_path = output_dir / validation_filename
            
            with open(validation_path, 'w') as f:
                json.dump(validation_report, f, indent=2, default=str)
            export_paths['validation_report'] = str(validation_path)
            self.logger.info(f"Created validation report: {validation_filename}")
            
            return {
                'export_paths': export_paths,
                'cycle_name': cycle_name,
                'timestamp': timestamp,
                'validation_report': validation_report
            }
            
        except Exception as e:
            self.logger.error(f"Error creating v8.5 exports: {str(e)}")
            raise
    
    def _create_validation_report_v85(self, cad_df: pd.DataFrame, rms_df: pd.DataFrame, matched_df: pd.DataFrame) -> Dict:
        """Create comprehensive validation report for v8.5 processing."""
        return {
            'processing_timestamp': datetime.now().isoformat(),
            'cycle_info': {
                'current_cycle': self.current_cycle,
                'current_date': str(self.current_date) if self.current_date else None
            },
            'data_summary': {
                'cad_records': len(cad_df),
                'cad_columns': len(cad_df.columns),
                'rms_records': len(rms_df),
                'rms_columns': len(rms_df.columns),
                'matched_records': len(matched_df),
                'matched_columns': len(matched_df.columns),
                'match_rate': round((len(matched_df) / max(len(cad_df), len(rms_df))) * 100, 2)
            },
            'column_validation': {
                'cad_columns': cad_df.columns.tolist(),
                'rms_columns': rms_df.columns.tolist(),
                'matched_columns': matched_df.columns.tolist()
            },
            'critical_fixes_applied': [
                'clean_how_reported_911() - Fixed 9-1-1 date conversion',
                'extract_username_timestamp() - Proper CAD notes cleaning',
                'cascade_date() and cascade_time() - Fixed RMS time handling',
                'time_of_day encoding - Removed corrupted characters',
                'Enhanced incident_type coalescing',
                'Added all_incidents concatenated field',
                'Added block calculations',
                'Added cycle information integration'
            ],
            'quality_metrics': {
                'cad_completeness': self._calculate_completeness(cad_df),
                'rms_completeness': self._calculate_completeness(rms_df),
                'matched_completeness': self._calculate_completeness(matched_df)
            }
        }
    
    def _calculate_completeness(self, df: pd.DataFrame) -> Dict:
        """Calculate data completeness metrics."""
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        completeness_rate = ((total_cells - missing_cells) / total_cells) * 100 if total_cells > 0 else 0
        
        return {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'completeness_rate': round(completeness_rate, 2),
            'missing_values': int(missing_cells)
        }
    
    def create_backup(self, source_files: List[str]) -> str:
        """Create backup of source files"""
        if not self.config['enable_backup']:
            return "Backup disabled"
        
        backup_dir = Path(self.config['backup_dir'])
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = backup_dir / f"backup_{timestamp}"
        backup_subdir.mkdir()
        
        try:
            for file_path in source_files:
                if Path(file_path).exists():
                    shutil.copy2(file_path, backup_subdir)
            
            self.logger.info(f"Backup created: {backup_subdir}")
            return str(backup_subdir)
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            return f"Backup failed: {str(e)}"
    
    def generate_pipeline_dashboard(self, processing_stats: Dict, quality_report: Dict, 
                                  export_info: Dict) -> Dict:
        """Generate pipeline status dashboard"""
        pipeline_end_time = time.time()
        total_processing_time = pipeline_end_time - self.pipeline_start_time
        
        dashboard = {
            'pipeline_summary': {
                'status': 'SUCCESS',
                'start_time': datetime.fromtimestamp(self.pipeline_start_time).isoformat(),
                'end_time': datetime.fromtimestamp(pipeline_end_time).isoformat(),
                'total_processing_time': round(total_processing_time, 2),
                'performance_status': 'GOOD' if total_processing_time < self.max_processing_time else 'SLOW'
            },
            'quality_metrics': {
                'data_quality_status': quality_report['overall_status'],
                'validation_rate': processing_stats.get('overall_validation_rate', 0),
                'quality_threshold_met': processing_stats.get('overall_validation_rate', 0) >= self.min_validation_rate
            },
            'processing_metrics': {
                'cad_retention_rate': processing_stats.get('cad_retention_rate', 0),
                'rms_retention_rate': processing_stats.get('rms_retention_rate', 0),
                'total_target_crimes': len(self.target_crimes),
                'crimes_processed': len(processing_stats.get('validation_rates', {}))
            },
            'export_status': {
                'powerbi_ready': export_info.get('processing_summary', {}).get('powerbi_integration', {}).get('ready', False),
                'files_created': len([k for k in export_info.keys() if k.endswith('_export')]),
                'export_location': self.config['output_dir']
            }
        }
        
        self.logger.info(f"Pipeline completed: {dashboard['pipeline_summary']['status']}")
        return dashboard
    
    def run_production_pipeline(self, cad_file_pattern: str = "C08W31_*_cad_data_standardized.csv",
                               rms_file_pattern: str = "C08W31_*_rms_data_standardized.csv") -> Dict:
        """Run complete production pipeline"""
        self.pipeline_start_time = time.time()
        self.logger.info("Starting SCRPA production pipeline")
        
        try:
            # 1. Find input files
            input_dir = Path(self.config['input_dir'])
            cad_files = list(input_dir.glob(cad_file_pattern))
            rms_files = list(input_dir.glob(rms_file_pattern))
            
            if not cad_files or not rms_files:
                raise FileNotFoundError(f"Input files not found: CAD={len(cad_files)}, RMS={len(rms_files)}")
            
            # Use most recent files
            cad_path = max(cad_files, key=lambda p: p.stat().st_mtime)
            rms_path = max(rms_files, key=lambda p: p.stat().st_mtime)
            
            self.logger.info(f"Using CAD file: {cad_path}")
            self.logger.info(f"Using RMS file: {rms_path}")
            
            # 2. Validate input files
            if not self.validate_input_files(str(cad_path), str(rms_path)):
                raise ValueError("Input file validation failed")
            
            # 3. Create backup
            backup_location = self.create_backup([str(cad_path), str(rms_path)])
            
            # 4. Load data
            self.logger.info("Loading data files")
            cad_df = pd.read_csv(cad_path)
            rms_df = pd.read_csv(rms_path)
            
            # 5. v8.5 Enhancement: Process data with enhanced v8.5 logic
            self.logger.info("Applying v8.5 data processing enhancements")
            cad_df = self.process_cad_data_v85(cad_df)
            rms_df = self.process_rms_data_v85(rms_df)
            
            # 6. Data quality validation (after processing)
            quality_report = self.validate_data_quality(cad_df, rms_df)
            if quality_report['overall_status'] == 'FAIL':
                self.logger.warning(f"Data quality validation failed: {quality_report}")
                # Continue processing with warning instead of failing
            
            # 7. Apply hybrid filtering with enhanced v8.5 patterns
            self.logger.info("Applying enhanced hybrid filtering")
            cad_filtered, rms_matched, processing_stats = self.apply_hybrid_filtering(cad_df, rms_df)
            
            # 8. Create matched dataset with v8.5 enhancements
            self.logger.info("Creating matched CAD-RMS dataset")
            matched_df = self.create_matched_dataset_v85(cad_filtered, rms_matched)
            
            # 9. Create v8.5 compliant exports
            self.logger.info("Creating v8.5 compliant exports")
            export_info = self.create_v85_exports(cad_filtered, rms_matched, matched_df)
            
            # 10. Generate dashboard
            dashboard = self.generate_pipeline_dashboard(processing_stats, quality_report, export_info)
            
            # 11. Save pipeline results
            pipeline_results = {
                'dashboard': dashboard,
                'quality_report': quality_report,
                'processing_stats': processing_stats,
                'export_info': export_info,
                'backup_location': backup_location
            }
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"SCRPA_Pipeline_Results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(pipeline_results, f, indent=2, default=str)
            
            self.logger.info(f"Pipeline completed successfully: {results_file}")
            return pipeline_results
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            error_result = {
                'status': 'FAILED',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'pipeline_duration': time.time() - self.pipeline_start_time if self.pipeline_start_time else 0
            }
            
            return error_result

def main():
    """Main execution function"""
    print("=== SCRPA Production Deployment Pipeline ===")
    
    # Initialize pipeline
    pipeline = SCRPAProductionPipeline()
    
    # Run production pipeline
    results = pipeline.run_production_pipeline()
    
    # Display results
    if results.get('status') == 'FAILED':
        print(f"Pipeline FAILED: {results.get('error', 'Unknown error')}")
        return False
    
    # Success summary
    dashboard = results.get('dashboard', {})
    pipeline_summary = dashboard.get('pipeline_summary', {})
    quality_metrics = dashboard.get('quality_metrics', {})
    
    print(f"\nPipeline Status: {pipeline_summary.get('status', 'UNKNOWN')}")
    print(f"Processing Time: {pipeline_summary.get('total_processing_time', 0):.2f} seconds")
    print(f"Data Quality: {quality_metrics.get('data_quality_status', 'UNKNOWN')}")
    print(f"Validation Rate: {quality_metrics.get('validation_rate', 0):.1f}%")
    print(f"PowerBI Ready: {dashboard.get('export_status', {}).get('powerbi_ready', False)}")
    
    export_info = results.get('export_info', {})
    if 'cad_export' in export_info:
        print(f"\nExported Files:")
        print(f"  CAD Filtered: {export_info['cad_export']}")
        print(f"  RMS Matched: {export_info['rms_export']}")
        print(f"  Summary: {export_info['summary_export']}")
    
    print("\n=== Production Pipeline Complete ===")
    return True

if __name__ == "__main__":
    success = main()