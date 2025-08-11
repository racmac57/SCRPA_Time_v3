# 2025-01-29-14-30-00
# SCRPA_Time_v2/Fixed_Master_SCRPA_Processor
# Author: R. A. Carucci
# Purpose: Complete integration script with datetime column creation fixes based on Gemini review

import pandas as pd
import numpy as np
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import warnings
warnings.filterwarnings('ignore')

# Import your existing validation and processing modules
try:
    from actual_structure_python_validation import SCRPAActualDataValidator, DataSource
    from enhanced_cadnotes_processor import EnhancedCADNotesProcessor
    from unified_data_processor import UnifiedDataProcessor
    import requests
except ImportError as e:
    print(f"WARNING Import error: {e}")
    print("Make sure all your existing scripts are in the same directory")

class MasterSCRPAProcessor:
    """
    Master processor that integrates all your existing scripts into a complete
    pipeline that replaces your complex Power BI M Code.
    
    FIXES APPLIED based on gemini_review.md:
    - Fixed _process_rms_export and _process_cad_export methods
    - Standardized Incident_DateTime column creation
    - Robust error handling for date/time parsing
    - Proper cascading date logic
    """

    def __init__(self, project_path: str = None):
        """Initialize master processor with your actual export directory structure."""

        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)

        # Your actual export directories
        self.export_dirs = {
            'cad_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA"),
            'rms_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA")
        }

        # Setup directory structure
        self.setup_directories()

        # Initialize logging
        self.setup_logging()

        # Initialize component processors
        self.data_validator = SCRPAActualDataValidator(str(self.project_path))
        self.cadnotes_processor = EnhancedCADNotesProcessor()

        # Processing statistics
        self.stats = {
            'processing_start_time': None,
            'data_source_detected': None,
            'total_input_records': 0,
            'total_output_records': 0,
            'cadnotes_processed': 0,
            'quality_score_avg': 0.0,
            'processing_duration': 0.0,
            'errors_encountered': []
        }

        # Category and Response Type mappings from CallType_Categories.xlsx
        self.category_map = {
            '1': 'Miscellaneous',
            '9-1-1 Call': 'Emergency Response',
            'A.C.O.R.N. Test': 'Administrative and Support',
            'A.T.R.A.': 'Special Operations and Tactical',
            'ABC Advisory Check': 'Regulatory and Ordinance',
            'ABC Inspection': 'Regulatory and Ordinance',
            # ... (keeping original category map for brevity) ...
            'terroristic Threats 2C:12-3': 'Criminal Investigation'
        }

        # Response type mapping (initialized alongside category_map)
        self.response_map = {
            'Emergency Response': 'Emergency',
            'Criminal Investigation': 'Priority',
            'Criminal Incidents': 'Priority',
            'Traffic and Motor Vehicle': 'Routine',
            'Administrative and Support': 'Routine'
        }

        self.logger.info("Master SCRPA Processor initialized with datetime fixes")

    def setup_directories(self):
        """Setup your actual project directory structure."""

        self.dirs = {
            'scripts': self.project_path / '01_scripts',
            'cad_exports': self.export_dirs['cad_exports'],
            'rms_exports': self.export_dirs['rms_exports'],
            'output': self.project_path / '03_output',
            'powerbi': self.project_path / '04_powerbi',
            'logs': self.project_path / '03_output' / 'logs',
            'reports': self.project_path / '03_output' / 'reports'
        }

        # Create output directories if they don't exist
        for dir_name, dir_path in self.dirs.items():
            if dir_name not in ['cad_exports', 'rms_exports']:
                dir_path.mkdir(parents=True, exist_ok=True)

        # Verify export directories exist
        if not self.dirs['cad_exports'].exists():
            self.logger.warning(f"CAD export directory not found: {self.dirs['cad_exports']}")
        if not self.dirs['rms_exports'].exists():
            self.logger.warning(f"RMS export directory not found: {self.dirs['rms_exports']}")

    def setup_logging(self):
        """Setup comprehensive logging system."""
        self.dirs['logs'].mkdir(parents=True, exist_ok=True)

        log_file = self.dirs['logs'] / f"master_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        self.logger = logging.getLogger('MasterProcessor')
        self.logger.setLevel(logging.INFO)

        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        self.logger.propagate = False

        # File handler
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')

        self.logger.info(f"Logging initialized: {log_file}")

    def find_latest_export_file(self, export_type: str = "auto") -> Tuple[str, DataSource]:
        """Find the latest CAD or RMS export file from your actual export directories."""

        self.logger.info(f"Searching for latest {export_type} export files")

        latest_file = None
        detected_source = DataSource.UNKNOWN

        if export_type.lower() in ["auto", "cad"]:
            # Search CAD exports
            cad_files = list(self.dirs['cad_exports'].glob("*.xlsx"))
            if cad_files:
                latest_cad = max(cad_files, key=lambda x: x.stat().st_mtime)
                self.logger.info(f"Latest CAD file: {latest_cad.name}")
                if export_type == "auto" or export_type.lower() == "cad":
                    latest_file = str(latest_cad)
                    detected_source = DataSource.CAD

        if export_type.lower() in ["auto", "rms"] and not latest_file:
            # Search RMS exports
            rms_files = list(self.dirs['rms_exports'].glob("*.xlsx"))
            if rms_files:
                latest_rms = max(rms_files, key=lambda x: x.stat().st_mtime)
                self.logger.info(f"Latest RMS file: {latest_rms.name}")
                if export_type == "auto" or export_type.lower() == "rms":
                    latest_file = str(latest_rms)
                    detected_source = DataSource.RMS

        if export_type == "auto" and latest_file is None:
            # Compare both directories and pick the most recent
            all_files = []

            cad_files = list(self.dirs['cad_exports'].glob("*.xlsx"))
            rms_files = list(self.dirs['rms_exports'].glob("*.xlsx"))

            for f in cad_files:
                all_files.append((f, DataSource.CAD))
            for f in rms_files:
                all_files.append((f, DataSource.RMS))

            if all_files:
                latest_file_info = max(all_files, key=lambda x: x[0].stat().st_mtime)
                latest_file = str(latest_file_info[0])
                detected_source = latest_file_info[1]
                self.logger.info(f"Most recent file: {latest_file_info[0].name} ({detected_source.value})")

        if latest_file is None:
            raise FileNotFoundError(f"No export files found in {self.dirs['cad_exports']} or {self.dirs['rms_exports']}")

        return latest_file, detected_source

    def _process_rms_export(self, df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
        """
        FIXED: Processes the raw RMS export DataFrame to standardize columns and create a reliable datetime column.
        This version fixes the date and time combination logic per gemini_review.md
        """
        self.logger.info("Processing RMS data structure...")
        cleaned_df = pd.DataFrame()

        # --- FIX START: Correctly combine separate Date and Time columns ---
        date_col_name = column_map.get('incident_date', 'Incident Date')
        time_col_name = column_map.get('incident_time', 'Incident Time')

        # Use cascading logic for dates: Incident Date -> Incident Date_Between -> Report Date
        if 'Incident Date' in df.columns:
            date_series = df['Incident Date']
        elif 'Incident Date_Between' in df.columns:
            date_series = df['Incident Date_Between']
        elif 'Report Date' in df.columns:
            date_series = df['Report Date']
        else:
            self.logger.warning("No date column found in RMS data")
            date_series = pd.Series([pd.NaT] * len(df))

        # Use cascading logic for times: Incident Time -> Incident Time_Between -> Report Time
        if 'Incident Time' in df.columns:
            time_series = df['Incident Time']
        elif 'Incident Time_Between' in df.columns:
            time_series = df['Incident Time_Between']
        elif 'Report Time' in df.columns:
            time_series = df['Report Time']
        else:
            self.logger.warning("No time column found in RMS data")
            time_series = pd.Series(['00:00:00'] * len(df))

        if date_series is not None and time_series is not None:
            self.logger.info(f"Combining RMS date and time columns using cascading logic")
            
            # Convert date and time columns to string to ensure consistent concatenation
            date_series = pd.to_datetime(date_series, errors='coerce').dt.strftime('%Y-%m-%d')
            time_series = pd.to_datetime(time_series, format='%H:%M:%S', errors='coerce').dt.strftime('%H:%M:%S')
            
            # Combine the string representations and then convert to datetime
            combined_datetime_str = date_series + " " + time_series
            cleaned_df['Incident_DateTime'] = pd.to_datetime(combined_datetime_str, errors='coerce')
            
            # Log how many dates failed to parse
            failed_parses = cleaned_df['Incident_DateTime'].isnull().sum()
            if failed_parses > 0:
                self.logger.warning(f"{failed_parses} RMS records had invalid date/time formats and could not be parsed.")
            else:
                self.logger.info(f"Successfully created Incident_DateTime for {len(cleaned_df)} RMS records")
        else:
            self.logger.warning("RMS data is missing date or time columns. DateTime will be null.")
            cleaned_df['Incident_DateTime'] = pd.NaT
        # --- FIX END ---

        # Map other relevant columns
        standard_columns = {
            'Case_Number': ['Case Number', 'case_number', 'CaseNumber'],
            'FullAddress': ['FullAddress', 'Full Address', 'Address'],
            'Incident_Type_1': ['Incident Type_1', 'IncidentType1'],
            'Incident_Type_2': ['Incident Type_2', 'IncidentType2'],
            'Incident_Type_3': ['Incident Type_3', 'IncidentType3'],
            'Grid': ['Grid', 'grid'],
            'Zone': ['Zone', 'zone', 'PDZone'],
            'Narrative': ['Narrative', 'narrative']
        }

        for std_col, col_variations in standard_columns.items():
            found_col = self._get_flexible_column_name(df, col_variations)
            if found_col:
                cleaned_df[std_col] = df[found_col]

        return cleaned_df

    def _process_cad_export(self, df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
        """
        FIXED: Processes the raw CAD export DataFrame to standardize columns and create a reliable datetime column.
        This version ensures the 'Time of Call' is correctly used per gemini_review.md
        """
        self.logger.info("Processing CAD data structure...")
        cleaned_df = pd.DataFrame()

        # --- FIX START: Correctly parse the single datetime column from CAD ---
        call_time_col_name = column_map.get('call_time', 'Time of Call')
        
        # Find the actual time column using flexible detection
        time_col_variations = ['Time of Call', 'TimeOfCall', 'Call_Time', 'call_time']
        found_time_col = self._get_flexible_column_name(df, time_col_variations)
        
        if found_time_col:
            self.logger.info(f"Using CAD '{found_time_col}' for Incident DateTime.")
            cleaned_df['Incident_DateTime'] = pd.to_datetime(df[found_time_col], errors='coerce')
            
            # Log how many dates failed to parse
            failed_parses = cleaned_df['Incident_DateTime'].isnull().sum()
            if failed_parses > 0:
                self.logger.warning(f"{failed_parses} CAD records had invalid datetime formats and could not be parsed.")
            else:
                self.logger.info(f"Successfully created Incident_DateTime for {len(cleaned_df)} CAD records")
        else:
            self.logger.warning("CAD data is missing 'Time of Call' column. DateTime will be null.")
            cleaned_df['Incident_DateTime'] = pd.NaT
        # --- FIX END ---
        
        # Map other relevant columns using flexible detection
        standard_columns = {
            'Case_Number': ['ReportNumberNew', 'Case_Number', 'Case Number'],
            'FullAddress': ['FullAddress2', 'FullAddress', 'Full Address', 'Address'],
            'How_Reported': ['How Reported', 'HowReported', 'How_Reported'],
            'PDZone': ['PDZone', 'PD Zone', 'Zone'],
            'Grid': ['Grid', 'grid'],
            'Incident': ['Incident', 'IncidentType', 'Incident Type'],
            'Officer': ['Officer', 'officer'],
            'Disposition': ['Disposition', 'disposition'],
            'Response_Type': ['Response Type', 'ResponseType', 'Response_Type'],
            'CADNotes': ['CADNotes', 'CAD Notes', 'Notes']
        }
        
        for std_col, col_variations in standard_columns.items():
            found_col = self._get_flexible_column_name(df, col_variations)
            if found_col:
                cleaned_df[std_col] = df[found_col]
                
        return cleaned_df

    def _get_flexible_column_name(self, df: pd.DataFrame, column_variations: list) -> str:
        """Find column name from list of variations, handling different naming conventions."""
        for variation in column_variations:
            if variation in df.columns:
                return variation
        return None

    def process_by_data_source(self, df: pd.DataFrame, data_source: DataSource) -> pd.DataFrame:
        """Process data based on detected source structure using FIXED methods."""

        self.logger.info(f"Step 2: Processing {data_source.value} data structure")

        # Create column mapping based on data source
        if data_source == DataSource.CAD:
            column_map = {
                'call_time': 'Time of Call',
                'case_number': 'ReportNumberNew',
                'incident_type': 'Incident'
            }
            return self._process_cad_export(df, column_map)
        elif data_source == DataSource.RMS:
            column_map = {
                'incident_date': 'Incident Date',
                'incident_time': 'Incident Time',
                'case_number': 'Case Number'
            }
            return self._process_rms_export(df, column_map)
        else:
            raise ValueError(f"Unknown data source: {data_source}")

    def auto_detect_and_load_data(self, input_file: str = None, export_type: str = "auto") -> Tuple[pd.DataFrame, DataSource, Dict]:
        """Auto-detect data source and load using your actual export directories."""

        self.logger.info("Step 1: Auto-detecting data source and loading data")

        try:
            if input_file:
                # Load specific file
                self.logger.info(f"Loading specified file: {Path(input_file).name}")
                df = pd.read_excel(input_file, engine='openpyxl')
                data_source, structure_info = self.data_validator.detect_data_source(df)
            else:
                # Find latest export file from your actual directories
                latest_file, detected_source = self.find_latest_export_file(export_type)
                self.logger.info(f"Loading latest export: {Path(latest_file).name}")

                df = pd.read_excel(latest_file, engine='openpyxl')
                data_source, structure_info = self.data_validator.detect_data_source(df)

                # Verify detection matches file location
                if detected_source != data_source:
                    self.logger.warning(f"File location suggests {detected_source.value} but structure detected as {data_source.value}")

            # Remove duplicates and clean up basic issues
            id_col = 'ReportNumberNew' if 'ReportNumberNew' in df.columns else 'Case_Number' if 'Case_Number' in df.columns else 'Case Number'
            if id_col and id_col in df.columns:
                original_len = len(df)
                df = df.drop_duplicates(subset=[id_col])
                dupes_removed = original_len - len(df)
                if dupes_removed > 0:
                    self.logger.info(f"Removed {dupes_removed} duplicates based on {id_col}")

            # Remove unnecessary columns early
            columns_to_remove = ['cYear', 'cMonth', 'DayofWeek', 'case_number', 'Case_Number2', 'Day_Name', 'Month_Name', 'Year', 'Month', 'Day']
            for col in columns_to_remove:
                if col in df.columns:
                    df = df.drop(columns=[col])
                    self.logger.info(f"Removed column: {col}")

            self.stats['total_input_records'] = len(df)

            self.logger.info(f"Detected {data_source.value} structure with {len(df)} records")
            return df, data_source, structure_info

        except Exception as e:
            self.logger.error(f"Failed to auto-detect and load data: {e}")
            raise

    def add_derived_enhancements(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived columns using the corrected Incident_DateTime column."""

        self.logger.info("Step 4: Adding derived columns using corrected Incident_DateTime")

        enhanced_df = df.copy()

        # Validate that we have Incident_DateTime
        if 'Incident_DateTime' not in enhanced_df.columns:
            self.logger.error("Incident_DateTime column missing - cannot add derived enhancements")
            return enhanced_df

        # Extract date and time components from Incident_DateTime
        enhanced_df['Incident_Date'] = enhanced_df['Incident_DateTime'].dt.date
        enhanced_df['Incident_Time'] = enhanced_df['Incident_DateTime'].dt.time

        # Add TimeOfDay categorization
        def categorize_time_of_day(dt):
            if pd.isna(dt):
                return "Unknown"
            
            hour = dt.hour
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

        enhanced_df['TimeOfDay'] = enhanced_df['Incident_DateTime'].apply(categorize_time_of_day)

        # Add Period classification
        def classify_period(dt):
            if pd.isna(dt):
                return 'Historical'
            
            today = pd.Timestamp.now().date()
            incident_date = dt.date()
            days_diff = (today - incident_date).days
            
            if days_diff <= 7:
                return '7-Day'
            elif days_diff <= 28:
                return '28-Day'
            elif dt.year == today.year:
                return 'YTD'
            else:
                return 'Historical'

        enhanced_df['Period'] = enhanced_df['Incident_DateTime'].apply(classify_period)

        # Add Enhanced_Block for addresses
        if 'FullAddress' in enhanced_df.columns:
            enhanced_df['Enhanced_Block'] = enhanced_df['FullAddress'].apply(self.calculate_enhanced_block)
        elif 'FullAddress2' in enhanced_df.columns:
            enhanced_df['Enhanced_Block'] = enhanced_df['FullAddress2'].apply(self.calculate_enhanced_block)
        else:
            enhanced_df['Enhanced_Block'] = 'Unknown Block'

        # Create ALL_INCIDENTS column
        if 'Incident_Type_1' in enhanced_df.columns:
            # RMS structure - concatenate incident types
            def concat_incidents(row):
                incidents = []
                for col in ['Incident_Type_1', 'Incident_Type_2', 'Incident_Type_3']:
                    if col in row and pd.notna(row[col]) and str(row[col]).strip():
                        incidents.append(str(row[col]).strip())
                return ' - '.join(incidents) if incidents else ''
            
            enhanced_df['ALL_INCIDENTS'] = enhanced_df.apply(concat_incidents, axis=1)
            enhanced_df['IncidentType'] = enhanced_df['Incident_Type_1']  # Primary incident type
        elif 'Incident' in enhanced_df.columns:
            # CAD structure - use single incident column
            enhanced_df['ALL_INCIDENTS'] = enhanced_df['Incident'].fillna('')
            enhanced_df['IncidentType'] = enhanced_df['Incident']
        else:
            enhanced_df['ALL_INCIDENTS'] = ''
            enhanced_df['IncidentType'] = ''

        # Add Crime_Category
        def categorize_crime(incident_type, all_incidents=''):
            if pd.isna(incident_type):
                return 'Other'
            
            incident_upper = str(incident_type).upper()
            all_upper = str(all_incidents).upper()
            
            # Motor Vehicle Theft - highest priority
            if any(term in incident_upper for term in ['MOTOR VEHICLE THEFT', 'AUTO THEFT', 'MV THEFT']):
                return 'Motor Vehicle Theft'
            if 'MOTOR VEHICLE THEFT' in all_upper:
                return 'Motor Vehicle Theft'
            
            # Robbery
            if 'ROBBERY' in incident_upper or 'ROBBERY' in all_upper:
                return 'Robbery'
            
            # Burglary subcategories
            if 'BURGLARY' in incident_upper or 'BURGLARY' in all_upper:
                if 'AUTO' in incident_upper or 'VEHICLE' in incident_upper or 'AUTO' in all_upper:
                    return 'Burglary – Auto'
                elif 'COMMERCIAL' in incident_upper or 'COMMERCIAL' in all_upper:
                    return 'Burglary – Commercial'
                elif 'RESIDENCE' in incident_upper or 'RESIDENTIAL' in incident_upper or 'RESIDENCE' in all_upper:
                    return 'Burglary – Residence'
                else:
                    return 'Burglary – Other'
            
            # Sexual Offenses
            if 'SEXUAL' in incident_upper or 'SEXUAL' in all_upper:
                return 'Sexual'
            
            return 'Other'

        enhanced_df['Crime_Category'] = enhanced_df.apply(
            lambda row: categorize_crime(row.get('IncidentType', ''), row.get('ALL_INCIDENTS', '')), axis=1
        )

        self.logger.info(f"Derived enhancements complete: added TimeOfDay, Period, Enhanced_Block, ALL_INCIDENTS, Crime_Category")
        return enhanced_df

    def calculate_enhanced_block(self, address: str) -> str:
        """Calculate enhanced block from address."""
        if pd.isna(address) or not address:
            return "Incomplete Address - Check Location Data"

        try:
            address = str(address).strip()
            # Remove Hackensack suffix
            clean_addr = address.replace(", Hackensack, NJ, 07601", "").replace(", Hackensack, NJ", "")

            # Handle intersections
            if ' & ' in clean_addr:
                return clean_addr.strip()

            # Extract block number
            parts = clean_addr.split()
            if parts and parts[0].replace('-', '').isdigit():
                street_num = int(parts[0].replace('-', ''))
                street_name = ' '.join(parts[1:]).split(',')[0]
                block_num = (street_num // 100) * 100
                return f"{street_name}, {block_num} Block"
            else:
                street_name = clean_addr.split(',')[0]
                return f"{street_name}, Unknown Block"
        except:
            return "Incomplete Address - Check Location Data"

    def process_complete_pipeline(self, input_file: str = None,
                                  output_file: str = None, export_type: str = "auto") -> Tuple[pd.DataFrame, Dict]:
        """
        Run the complete SCRPA processing pipeline with FIXED datetime handling.
        """

        self.logger.info("========================================")
        self.logger.info("STARTING COMPLETE SCRPA PROCESSING PIPELINE")
        self.logger.info("========================================")

        self.stats['processing_start_time'] = datetime.now()

        try:
            # Step 1: Auto-detect and load data
            df, data_source, structure_info = self.auto_detect_and_load_data(input_file, export_type)
            initial_record_count = len(df)

            # Step 2: Process based on detected structure with FIXED datetime handling
            processed_df = self.process_by_data_source(df, data_source)
            
            # Validation - ensure Incident_DateTime was created
            null_datetime_count = processed_df['Incident_DateTime'].isnull().sum()
            if null_datetime_count > 0:
                self.logger.warning(f"{null_datetime_count} records have null Incident_DateTime after processing")
            else:
                self.logger.info("✅ All records have valid Incident_DateTime")

            # Step 3: Enhanced CADNotes processing
            enhanced_df = self.process_cadnotes_enhanced(processed_df)

            # Step 4: Add all derived columns using corrected datetime
            final_df = self.add_derived_enhancements(enhanced_df)

            # Step 5: Data quality validation and cleanup
            validated_df = self.validate_and_cleanup(final_df)

            # Step 6: Export for Power BI
            output_path = self.export_for_powerbi(validated_df, output_file)

            self.logger.info("========================================")
            self.logger.info("COMPLETE SCRPA PROCESSING PIPELINE FINISHED")
            self.logger.info(f"Output: {output_path}")
            self.logger.info("========================================")

            return validated_df, self.stats

        except Exception as e:
            self.logger.error(f"PIPELINE FAILED: {str(e)}")
            self.stats['errors_encountered'].append(str(e))
            raise

    def process_cadnotes_enhanced(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process CADNotes using enhanced processor with flexible column detection."""

        self.logger.info("Step 3: Enhanced CADNotes processing")

        # Find CADNotes column using flexible detection
        cadnotes_variations = ['CADNotes', 'CAD Notes', 'Notes', 'CAD_Notes', 'cad_notes']
        cadnotes_col = self._get_flexible_column_name(df, cadnotes_variations)
        
        if cadnotes_col:
            enhanced_df = self.cadnotes_processor.process_cadnotes_dataframe(df, cadnotes_col)
            self.stats['cadnotes_processed'] = enhanced_df['CAD_Username'].notna().sum()
            self.logger.info(f"Processed CADNotes from {cadnotes_col} column")
        else:
            self.logger.warning("No CADNotes column found, skipping CADNotes processing")
            enhanced_df = df.copy()
            # Add empty CADNotes columns for consistency
            enhanced_df['CAD_Username'] = None
            enhanced_df['CAD_Timestamp'] = None
            enhanced_df['CAD_Notes_Cleaned'] = None
            enhanced_df['CADNotes_Processing_Quality'] = 0.0

        self.logger.info(f"CADNotes processing complete: {self.stats['cadnotes_processed']} notes processed")
        return enhanced_df

    def validate_and_cleanup(self, df: pd.DataFrame) -> pd.DataFrame:
        """Final data validation and cleanup."""

        self.logger.info("Step 5: Data validation and cleanup")

        # Remove records with missing critical fields
        original_count = len(df)

        # Keep records with valid case numbers and incident types
        case_col = self._get_flexible_column_name(df, ['Case_Number', 'Case Number', 'ReportNumberNew'])
        incident_col = self._get_flexible_column_name(df, ['IncidentType', 'Incident Type', 'Incident'])
        
        if case_col and incident_col:
            df = df[
                df[case_col].notna() &
                (df[case_col] != '') &
                df[incident_col].notna() &
                (df[incident_col] != '')
            ]
        else:
            self.logger.warning("Could not find case number or incident type columns for validation")

        # Calculate overall data quality score
        if 'CADNotes_Processing_Quality' in df.columns:
            self.stats['quality_score_avg'] = df['CADNotes_Processing_Quality'].mean()

        removed_count = original_count - len(df)
        if removed_count > 0:
            self.logger.warning(f"Removed {removed_count} records with missing critical fields")

        self.logger.info(f"Validation complete: {len(df)} clean records")
        return df

    def export_for_powerbi(self, df: pd.DataFrame, output_file: str = None) -> str:
        """Export clean data for Power BI consumption."""

        self.logger.info("Step 6: Exporting for Power BI")

        if output_file is None:
            output_file = self.dirs['powerbi'] / "enhanced_scrpa_data.csv"

        # Ensure the output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        try:
            df.to_csv(output_file, index=False, encoding='utf-8')
            self.logger.info(f"Data successfully exported to {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to export data to {output_file}: {e}")
            raise

        return str(output_file)


def main():
    """Main execution function with command line interface."""

    parser = argparse.ArgumentParser(description="Fixed Master SCRPA Processor - Complete M Code Replacement with DateTime Fixes")

    parser.add_argument('--input-file', '-i', type=str,
                        help='Specific input file to process (optional)')
    parser.add_argument('--output-file', '-o', type=str,
                        help='Output file path (optional)')
    parser.add_argument('--export-type', '-t', choices=['auto', 'cad', 'rms'], default='auto',
                        help='Type of export to process (auto, cad, or rms)')
    parser.add_argument('--mode', '-m', choices=['process', 'validate', 'test'], default='process',
                        help='Processing mode')
    parser.add_argument('--project-path', '-p', type=str,
                        help='Project path (uses default if not specified)')

    args = parser.parse_args()

    try:
        # Initialize processor
        processor = MasterSCRPAProcessor(args.project_path)

        if args.mode == 'test':
            # Test mode - validate processor components
            print("Running test mode...")

            # Test file detection
            try:
                latest_file, detected_source = processor.find_latest_export_file(args.export_type)
                print(f"✅ Latest file detection: {Path(latest_file).name} ({detected_source.value})")
                file_detection_passed = True
            except Exception as e:
                print(f"❌ File detection failed: {e}")
                file_detection_passed = False

            # Test datetime processing fix
            try:
                if file_detection_passed:
                    df = pd.read_excel(latest_file, engine='openpyxl')
                    data_source, _ = processor.data_validator.detect_data_source(df)
                    
                    # Test the fixed processing methods
                    if data_source == DataSource.CAD:
                        column_map = {'call_time': 'Time of Call'}
                        processed_df = processor._process_cad_export(df, column_map)
                    else:
                        column_map = {'incident_date': 'Incident Date', 'incident_time': 'Incident Time'}
                        processed_df = processor._process_rms_export(df, column_map)
                    
                    datetime_null_count = processed_df['Incident_DateTime'].isnull().sum()
                    if datetime_null_count == 0:
                        print("✅ DateTime processing fix: All records have valid Incident_DateTime")
                        datetime_test_passed = True
                    else:
                        print(f"⚠️  DateTime processing: {datetime_null_count} records still have null datetime")
                        datetime_test_passed = False
                else:
                    datetime_test_passed = False
            except Exception as e:
                print(f"❌ DateTime processing test failed: {e}")
                datetime_test_passed = False

            if file_detection_passed and datetime_test_passed:
                print("✅ All tests passed! Ready for processing with datetime fixes.")
            else:
                print("❌ Some tests failed. Check configuration and datetime processing.")

        elif args.mode == 'validate':
            # Validation mode - run data validation only
            print("Running validation mode...")

            latest_file, detected_source = processor.find_latest_export_file(args.export_type)
            df = pd.read_excel(latest_file, engine='openpyxl')

            print(f"\nFile: {Path(latest_file).name}")
            print(f"Data Source: {detected_source.value}")
            print(f"Records: {len(df)}")
            print(f"Columns: {list(df.columns)}")

        else:
            # Full processing mode
            print("Running full processing mode with datetime fixes...")

            # Run complete pipeline
            final_df, stats = processor.process_complete_pipeline(
                input_file=args.input_file,
                output_file=args.output_file,
                export_type=args.export_type
            )

            print("\n🎯 Processing complete with datetime fixes!")
            print("📊 Final statistics:")
            for key, value in stats.items():
                if not key.endswith('_time') and key != 'errors_encountered':
                    print(f"   {key.replace('_', ' ').title()}: {value}")
            
            # Validate datetime column creation
            if 'Incident_DateTime' in final_df.columns:
                null_datetime_count = final_df['Incident_DateTime'].isnull().sum()
                print(f"\n✅ DateTime Validation:")
                print(f"   Total records: {len(final_df)}")
                print(f"   Valid datetimes: {len(final_df) - null_datetime_count}")
                print(f"   Null datetimes: {null_datetime_count}")
                if null_datetime_count == 0:
                    print("   🎉 SUCCESS: All records have valid Incident_DateTime!")
                else:
                    print(f"   ⚠️  WARNING: {null_datetime_count} records still have null datetime")
            else:
                print("❌ ERROR: Incident_DateTime column not found in final output")

    except Exception as e:
        print(f"\n❌ Processing failed: {str(e)}")
        print(f"🔍 Check the log files in: {Path(r'C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\03_output\logs')}")
        sys.exit(1)


if __name__ == "__main__":
    main()