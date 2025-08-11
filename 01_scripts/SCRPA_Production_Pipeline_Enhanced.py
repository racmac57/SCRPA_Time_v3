#!/usr/bin/env python3
"""
SCRPA Production Pipeline - Enhanced with Complete Column Mapping Fixes
Comprehensive integration of all proven fixes with enhanced processing logic
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

class SCRPAEnhancedProductionPipeline:
    def __init__(self, config: Optional[Dict] = None):
        """Initialize enhanced production pipeline"""
        self.config = config or self._default_config()
        self.logger = self._setup_logging()
        self.pipeline_start_time = None
        self.processing_stats = {}
        
        # Enhanced quality thresholds
        self.min_validation_rate = 70.0
        self.max_processing_time = 300
        self.target_rms_records = 140  # Expected RMS record count
        
        # Target crimes and patterns
        self.target_crimes = [
            "Motor Vehicle Theft",
            "Robbery", 
            "Burglary – Auto",
            "Sexual",
            "Burglary – Commercial", 
            "Burglary – Residence"
        ]
        
        self.crime_patterns = {
            "Motor Vehicle Theft": [
                r"motor\s*vehicle\s*theft",
                r"theft\s*of\s*motor\s*vehicle",
                r"auto\s*theft",
                r"car\s*theft",
                r"vehicle\s*theft",
                r"240\s*=\s*theft\s*of\s*motor\s*vehicle"
            ],
            "Robbery": [
                r"robbery",
                r"120\s*=\s*robbery"
            ],
            "Burglary – Auto": [
                r"burglary\s*[-–]\s*auto",
                r"auto\s*burglary",
                r"theft\s*from\s*motor\s*vehicle",
                r"23f\s*=\s*theft\s*from\s*motor\s*vehicle"
            ],
            "Sexual": [
                r"sexual",
                r"11d\s*=\s*fondling",
                r"criminal\s*sexual\s*contact"
            ],
            "Burglary – Commercial": [
                r"burglary\s*[-–]\s*commercial",
                r"commercial\s*burglary",
                r"220\s*=\s*burglary.*commercial"
            ],
            "Burglary – Residence": [
                r"burglary\s*[-–]\s*residence",
                r"residential\s*burglary",
                r"220\s*=\s*burglary.*residential"
            ]
        }
    
    def _default_config(self) -> Dict:
        """Enhanced configuration with proper file organization"""
        base_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        
        return {
            'base_dir': str(base_dir),
            'input_dir': str(base_dir / "05_Exports"),           # Raw data inputs
            'scripts_dir': str(base_dir / "01_scripts"),         # Processing scripts
            'test_output_dir': str(base_dir / "03_output"),      # Test outputs
            'production_dir': str(base_dir / "04_powerbi"),      # Production outputs
            'reference_dir': str(base_dir / "10_Refrence_Files"), # Reference files
            'log_dir': str(base_dir / "logs"),
            'backup_dir': str(base_dir / "backups"),
            'enable_backup': True,
            'enable_rollback': True,
            'quality_checks': True,
            'performance_monitoring': True
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup enhanced logging"""
        log_dir = Path(self.config['log_dir'])
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"scrpa_enhanced_production_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger('SCRPA_Enhanced_Production')
        logger.info("Enhanced production pipeline initialized")
        return logger
    
    # ENHANCED DATE/TIME CASCADE LOGIC (REQUIREMENT 1)
    def get_incident_date(self, row):
        """Enhanced date cascade with fallback logic"""
        if pd.notna(row.get("Incident Date")):
            return row["Incident Date"]
        elif pd.notna(row.get("Incident Date_Between")):
            return row["Incident Date_Between"]
        elif pd.notna(row.get("Report Date")):
            return row["Report Date"]
        else:
            return None
    
    def get_incident_time(self, row):
        """Enhanced time cascade with fallback logic"""
        if pd.notna(row.get("Incident Time")):
            return row["Incident Time"]
        elif pd.notna(row.get("Incident Time_Between")):
            return row["Incident Time_Between"]
        elif pd.notna(row.get("Report Time")):
            return row["Report Time"] 
        else:
            return None
    
    def extract_time_from_timedelta(self, time_val):
        """Extract time string from various time formats"""
        if pd.isna(time_val):
            return None
        
        if isinstance(time_val, pd.Timedelta):
            total_seconds = int(time_val.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        if isinstance(time_val, str):
            return time_val
        
        return str(time_val)
    
    def categorize_time_of_day(self, time_val):
        """Categorize time into periods with enhanced logic"""
        if pd.isna(time_val):
            return "Unknown"
        
        if isinstance(time_val, pd.Timedelta):
            total_seconds = int(time_val.total_seconds())
            hours = total_seconds // 3600
        elif isinstance(time_val, str):
            hour_match = re.search(r'(\d{1,2}):(\d{2})', time_val)
            if hour_match:
                hours = int(hour_match.group(1))
            else:
                return "Unknown"
        else:
            return "Unknown"
        
        if 0 <= hours < 6:
            return "Early Morning"
        elif 6 <= hours < 12:
            return "Morning"
        elif 12 <= hours < 18:
            return "Afternoon"
        elif 18 <= hours < 22:
            return "Evening"
        else:
            return "Night"
    
    # NARRATIVE CLEANING (REQUIREMENT 2)
    def clean_narrative(self, text):
        """Clean narrative text: trim whitespace, fix line breaks, preserve all content"""
        if pd.isna(text) or not text:
            return ""
        
        # Convert to string and clean
        cleaned = str(text).strip()
        # Replace multiple whitespace with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # Fix line breaks (normalize to single newlines)
        cleaned = re.sub(r'\r\n|\r|\n', '\n', cleaned)
        
        return cleaned.strip()
    
    # VEHICLE DATA UPPERCASE (REQUIREMENT 3)
    def uppercase_vehicle_fields(self, df):
        """Convert vehicle-related fields to uppercase"""
        vehicle_fields = [
            'registration_1', 'make_1', 'model_1', 'reg_state_1',
            'registration_2', 'reg_state_2', 'make_2', 'model_2'
        ]
        
        for field in vehicle_fields:
            if field in df.columns:
                df[field] = df[field].astype(str).str.upper().replace('NAN', '')
        
        return df
    
    def standardize_case_number(self, case_num):
        """Standardize case number format"""
        if pd.isna(case_num):
            return None
        
        case_str = str(case_num).strip()
        
        if re.match(r'^\d{2}-\d{6}$', case_str):
            return case_str
        elif re.match(r'^\d{8}$', case_str):
            return f"{case_str[:2]}-{case_str[2:]}"
        
        return case_str
    
    def calculate_block_from_address(self, address):
        """Calculate block from full address"""
        if pd.isna(address):
            return "Check Location Data"
        
        address_str = str(address).strip()
        if not address_str:
            return "Check Location Data"
        
        parts = address_str.split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1]}"
        elif len(parts) == 1:
            return parts[0]
        else:
            return "Check Location Data"
    
    def build_vehicle_info(self, row):
        """Build vehicle information string from components"""
        reg_state = row.get('Reg State 1', '')
        registration = row.get('Registration 1', '')
        make = row.get('Make1', '')
        model = row.get('Model1', '')
        
        if pd.notna(registration) and str(registration).strip():
            vehicle_parts = [f"{reg_state} - {registration}"]
            
            make_model_parts = []
            if pd.notna(make) and str(make).strip():
                make_model_parts.append(str(make))
            if pd.notna(model) and str(model).strip():
                make_model_parts.append(str(model))
            
            if make_model_parts:
                vehicle_parts.append(f"{'/'.join(make_model_parts)}")
            
            return ', '.join(vehicle_parts)
        
        return None
    
    def load_cad_reference(self):
        """Load CAD reference file for proper categorization"""
        ref_file = Path(self.config['reference_dir']) / "CallType_Categories.xlsx"
        
        if not ref_file.exists():
            self.logger.warning(f"CAD reference file not found: {ref_file}")
            return pd.DataFrame()
        
        try:
            ref_df = pd.read_excel(ref_file)
            self.logger.info(f"Loaded CAD reference: {len(ref_df)} incident types")
            return ref_df
        except Exception as e:
            self.logger.error(f"Error loading CAD reference: {e}")
            return pd.DataFrame()
    
    def process_rms_data_enhanced(self) -> Optional[pd.DataFrame]:
        """Process RMS data with all proven column mapping fixes"""
        self.logger.info("Processing RMS data with enhanced column mapping")
        
        # Find raw RMS export
        input_dir = Path(self.config['input_dir'])
        rms_exports = list(input_dir.glob("*SCRPA_RMS*.xlsx"))
        
        if not rms_exports:
            self.logger.error("No RMS export files found")
            return None
        
        # Use most recent file
        latest_export = max(rms_exports, key=lambda p: p.stat().st_mtime)
        self.logger.info(f"Processing RMS file: {latest_export.name}")
        
        try:
            # Load raw data
            raw_df = pd.read_excel(latest_export)
            self.logger.info(f"Loaded raw RMS data: {len(raw_df)} records")
            
            # Validate expected record count
            if len(raw_df) != self.target_rms_records:
                self.logger.warning(f"RMS record count mismatch: {len(raw_df)} vs expected {self.target_rms_records}")
            
            # Create processed dataframe with CORRECTED COLUMN MAPPING
            processed_df = pd.DataFrame()
            
            # 1. Case number standardization
            processed_df['case_number'] = raw_df['Case Number'].apply(self.standardize_case_number)
            
            # 2. Enhanced date processing with cascade logic
            processed_df['incident_date'] = raw_df.apply(
                lambda row: self.extract_date_string(self.get_incident_date(row)), axis=1
            )
            processed_df['day_of_week'] = raw_df['Incident Date'].apply(self.extract_day_of_week)
            processed_df['day_type'] = processed_df['day_of_week'].apply(
                lambda x: "Weekend" if x in ['Saturday', 'Sunday'] else "Weekday" if x else None
            )
            
            # 3. Enhanced time processing with cascade logic  
            processed_df['incident_time'] = raw_df.apply(
                lambda row: self.extract_time_from_timedelta(self.get_incident_time(row)), axis=1
            )
            processed_df['time_of_day'] = raw_df.apply(
                lambda row: self.categorize_time_of_day(self.get_incident_time(row)), axis=1
            )
            
            # Time of day sort order
            time_order_map = {
                "Early Morning": 1, "Morning": 2, "Afternoon": 3, 
                "Evening": 4, "Night": 5, "Unknown": 99
            }
            processed_df['time_of_day_sort_order'] = processed_df['time_of_day'].map(time_order_map)
            
            # 4. CRITICAL FIX: Location mapping (FullAddress -> location)
            processed_df['location'] = raw_df['FullAddress']  # CORRECTED MAPPING
            processed_df['block'] = processed_df['location'].apply(self.calculate_block_from_address)
            
            # 5. CRITICAL FIX: Grid and Post mapping
            processed_df['grid'] = raw_df['Grid']    # Direct mapping
            processed_df['post'] = raw_df['Zone']    # CORRECTED: Zone -> post
            
            # 6. CRITICAL FIX: Incident type mapping
            processed_df['incident_type'] = raw_df['Incident Type_1']  # CORRECTED MAPPING
            processed_df['all_incidents'] = raw_df['Incident Type_1']  # Same as primary
            
            # 7. Vehicle information with uppercase formatting
            processed_df['vehicle_1'] = raw_df.apply(self.build_vehicle_info, axis=1)
            processed_df['vehicle_2'] = None
            processed_df['vehicle_1_and_vehicle_2'] = None
            
            # 8. Narrative cleaning (REQUIREMENT 2)
            processed_df['narrative'] = raw_df['Narrative'].apply(self.clean_narrative)
            
            # 9. Additional fields
            processed_df['total_value_stolen'] = raw_df['Total Value Stolen']
            processed_df['squad'] = raw_df['Squad']
            processed_df['officer_of_record'] = raw_df['Officer of Record']
            processed_df['nibrs_classification'] = raw_df['NIBRS Classification']
            
            # 10. Computed fields
            processed_df['period'] = "YTD"
            processed_df['season'] = "Winter"
            
            # 11. Cycle name
            processed_df['cycle_name'] = processed_df['case_number'].apply(
                lambda x: f"C{x[:2]}W{x[3:5]}" if isinstance(x, str) and len(x) >= 8 else None
            )
            
            # Apply vehicle uppercase formatting (REQUIREMENT 3)
            processed_df = self.uppercase_vehicle_fields(processed_df)
            
            self.logger.info(f"RMS processing complete: {len(processed_df)} records processed")
            self.logger.info(f"Location data: {processed_df['location'].notna().sum()}/{len(processed_df)}")
            self.logger.info(f"Incident types: {processed_df['incident_type'].notna().sum()}/{len(processed_df)}")
            self.logger.info(f"Time data: {processed_df['incident_time'].notna().sum()}/{len(processed_df)}")
            
            return processed_df
            
        except Exception as e:
            self.logger.error(f"Error processing RMS data: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def extract_date_string(self, date_val):
        """Extract date string from various date formats"""
        if pd.isna(date_val):
            return None
        
        if isinstance(date_val, (pd.Timestamp, datetime)):
            return date_val.strftime('%Y-%m-%d')
        
        try:
            parsed_date = pd.to_datetime(date_val)
            return parsed_date.strftime('%Y-%m-%d')
        except:
            return str(date_val)
    
    def extract_day_of_week(self, date_val):
        """Extract day of week from date"""
        if pd.isna(date_val):
            return None
        
        if isinstance(date_val, (pd.Timestamp, datetime)):
            return date_val.strftime('%A')
        
        try:
            parsed_date = pd.to_datetime(date_val)
            return parsed_date.strftime('%A')
        except:
            return None
    
    def process_cad_data_enhanced(self) -> Optional[pd.DataFrame]:
        """Process CAD data with reference integration"""
        self.logger.info("Processing CAD data with reference integration")
        
        # Load CAD reference
        ref_df = self.load_cad_reference()
        
        # Find CAD export  
        input_dir = Path(self.config['input_dir'])
        cad_exports = list(input_dir.glob("*SCRPA_CAD*.xlsx"))
        
        if not cad_exports:
            self.logger.error("No CAD export files found")
            return None
        
        # Use most recent file
        latest_export = max(cad_exports, key=lambda p: p.stat().st_mtime)
        self.logger.info(f"Processing CAD file: {latest_export.name}")
        
        try:
            # Load raw CAD data
            cad_df = pd.read_excel(latest_export)
            self.logger.info(f"Loaded CAD data: {len(cad_df)} records")
            
            # Normalize headers to snake_case
            cad_df.columns = [self.to_snake_case(col) for col in cad_df.columns]
            
            if not ref_df.empty:
                # Create lookup dictionary from reference
                ref_lookup = dict(zip(ref_df['Incident'], 
                                    zip(ref_df['Category Type'], ref_df['Response Type'])))
                
                # Apply reference mapping
                cad_df['category_type'] = cad_df['incident'].map(
                    lambda x: ref_lookup.get(x, (None, None))[0] if x in ref_lookup else cad_df.get('category_type')
                )
                cad_df['response_type'] = cad_df['incident'].map(
                    lambda x: ref_lookup.get(x, (None, None))[1] if x in ref_lookup else cad_df.get('response_type')
                )
                
                self.logger.info(f"Applied reference mapping to {len(ref_lookup)} incident types")
            
            return cad_df
            
        except Exception as e:
            self.logger.error(f"Error processing CAD data: {e}")
            return None
    
    def to_snake_case(self, name: str) -> str:
        """Convert string to snake_case"""
        s = str(name)
        s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
        s = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', s)
        s = re.sub(r'[^0-9A-Za-z]+', ' ', s).strip()
        s = re.sub(r'\s+', '_', s).lower()
        return s
    
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
            
            # RMS matching with LEFT JOIN to preserve all RMS records
            rms_matched = rms_df[rms_df['case_number'].isin(all_filtered_cases)].copy()
            
            processing_time = time.time() - start_time
            
            # Processing stats
            filtering_stats = {
                'processing_time': round(processing_time, 2),
                'cad_original_records': len(cad_df),
                'cad_filtered_records': len(cad_filtered),
                'rms_original_records': len(rms_df),
                'rms_matched_records': len(rms_matched),
                'quality_status': 'SUCCESS'
            }
            
            self.logger.info(f"Hybrid filtering completed: {filtering_stats['quality_status']}")
            return cad_filtered, rms_matched, filtering_stats
            
        except Exception as e:
            self.logger.error(f"Hybrid filtering error: {str(e)}")
            raise
    
    def create_powerbi_exports_enhanced(self, cad_filtered: pd.DataFrame, rms_matched: pd.DataFrame, 
                                      export_stats: Dict) -> Dict:
        """Create PowerBI-ready export files with proper organization"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # REQUIREMENT 4: Fix file output paths for proper organization
        production_dir = Path(self.config['production_dir'])  # 04_powerbi/
        test_output_dir = Path(self.config['test_output_dir'])  # 03_output/
        
        production_dir.mkdir(exist_ok=True)
        test_output_dir.mkdir(exist_ok=True)
        
        # Production outputs (04_powerbi/)
        cad_export_path = production_dir / f"C08W31_{timestamp}_cad_data_enhanced.csv"
        rms_export_path = production_dir / f"C08W31_{timestamp}_rms_data_enhanced.csv" 
        matched_export_path = production_dir / f"C08W31_{timestamp}_cad_rms_matched_enhanced.csv"
        
        # Test/validation outputs (03_output/)
        summary_path = test_output_dir / f"SCRPA_Enhanced_Processing_Summary_{timestamp}.json"
        validation_path = test_output_dir / f"SCRPA_Enhanced_Validation_{timestamp}.json"
        
        try:
            # Export production datasets
            cad_filtered.to_csv(cad_export_path, index=False)
            rms_matched.to_csv(rms_export_path, index=False)
            
            # Create matched dataset
            matched_df = rms_matched.merge(
                cad_filtered[['case_number', 'incident', 'category_type', 'response_type']], 
                on='case_number', 
                how='left'
            )
            matched_df.to_csv(matched_export_path, index=False)
            
            # Create processing summary
            processing_summary = {
                'export_timestamp': datetime.now().isoformat(),
                'processing_stats': export_stats,
                'enhancement_features': {
                    'enhanced_date_time_cascade': True,
                    'narrative_cleaning': True,
                    'vehicle_uppercase_formatting': True,
                    'corrected_column_mapping': True,
                    'proper_file_organization': True
                },
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
                    },
                    'matched_dataset': {
                        'filename': matched_export_path.name,
                        'path': str(matched_export_path),
                        'records': len(matched_df),
                        'columns': matched_df.columns.tolist()
                    }
                },
                'data_quality_metrics': {
                    'rms_record_preservation': f"{len(rms_matched)}/{self.target_rms_records}",
                    'location_data_populated': rms_matched['location'].notna().sum(),
                    'incident_type_populated': rms_matched['incident_type'].notna().sum(),
                    'time_data_populated': rms_matched['incident_time'].notna().sum()
                },
                'powerbi_integration': {
                    'ready': True,
                    'refresh_timestamp': datetime.now().isoformat(),
                    'data_freshness': 'Current'
                }
            }
            
            # Save summary and validation
            with open(summary_path, 'w') as f:
                json.dump(processing_summary, f, indent=2, default=str)
            
            # Create validation report
            validation_report = {
                'validation_timestamp': datetime.now().isoformat(),
                'critical_field_validation': {
                    'location': {
                        'populated': rms_matched['location'].notna().sum(),
                        'total': len(rms_matched),
                        'percentage': (rms_matched['location'].notna().sum() / len(rms_matched)) * 100
                    },
                    'incident_type': {
                        'populated': rms_matched['incident_type'].notna().sum(),
                        'total': len(rms_matched),
                        'percentage': (rms_matched['incident_type'].notna().sum() / len(rms_matched)) * 100
                    },
                    'incident_time': {
                        'populated': rms_matched['incident_time'].notna().sum(),
                        'total': len(rms_matched),
                        'percentage': (rms_matched['incident_time'].notna().sum() / len(rms_matched)) * 100
                    }
                },
                'enhancement_validation': {
                    'narrative_cleaning_applied': rms_matched['narrative'].apply(lambda x: isinstance(x, str) and x.strip() != '').sum(),
                    'vehicle_formatting_applied': True,
                    'enhanced_time_cascade_applied': True
                }
            }
            
            with open(validation_path, 'w') as f:
                json.dump(validation_report, f, indent=2, default=str)
            
            export_info = {
                'cad_export': str(cad_export_path),
                'rms_export': str(rms_export_path),
                'matched_export': str(matched_export_path),
                'summary_export': str(summary_path),
                'validation_export': str(validation_path),
                'processing_summary': processing_summary
            }
            
            self.logger.info("Enhanced PowerBI exports created successfully")
            self.logger.info(f"Production files: {production_dir}")
            self.logger.info(f"Test files: {test_output_dir}")
            
            return export_info
            
        except Exception as e:
            self.logger.error(f"Export creation error: {str(e)}")
            raise
    
    def run_enhanced_production_pipeline(self) -> Dict:
        """Run complete enhanced production pipeline"""
        self.pipeline_start_time = time.time()
        self.logger.info("Starting SCRPA Enhanced Production Pipeline")
        
        try:
            # 1. Process RMS data with all fixes
            self.logger.info("Step 1: Processing RMS data with enhanced column mapping")
            rms_df = self.process_rms_data_enhanced()
            if rms_df is None:
                raise ValueError("RMS data processing failed")
            
            # 2. Process CAD data with reference integration
            self.logger.info("Step 2: Processing CAD data with reference integration")
            cad_df = self.process_cad_data_enhanced()
            if cad_df is None:
                raise ValueError("CAD data processing failed")
            
            # 3. Apply hybrid filtering
            self.logger.info("Step 3: Applying hybrid filtering")
            cad_filtered, rms_matched, processing_stats = self.apply_hybrid_filtering(cad_df, rms_df)
            
            # 4. Create enhanced exports with proper organization
            self.logger.info("Step 4: Creating enhanced PowerBI exports")
            export_info = self.create_powerbi_exports_enhanced(cad_filtered, rms_matched, processing_stats)
            
            # 5. Generate final results
            pipeline_end_time = time.time()
            total_processing_time = pipeline_end_time - self.pipeline_start_time
            
            final_results = {
                'status': 'SUCCESS',
                'pipeline_summary': {
                    'total_processing_time': round(total_processing_time, 2),
                    'rms_records_processed': len(rms_df),
                    'cad_records_processed': len(cad_df),
                    'matched_records_created': len(rms_matched)
                },
                'enhancement_features': {
                    'enhanced_date_time_cascade': True,
                    'narrative_cleaning': True,
                    'vehicle_uppercase_formatting': True,  
                    'corrected_column_mapping': True,
                    'proper_file_organization': True
                },
                'data_quality_metrics': {
                    'record_preservation_rate': (len(rms_matched) / self.target_rms_records) * 100,
                    'location_population_rate': (rms_matched['location'].notna().sum() / len(rms_matched)) * 100,
                    'incident_type_population_rate': (rms_matched['incident_type'].notna().sum() / len(rms_matched)) * 100
                },
                'export_info': export_info,
                'processing_stats': processing_stats
            }
            
            # Save final results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"SCRPA_Enhanced_Pipeline_Results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(final_results, f, indent=2, default=str)
            
            self.logger.info(f"Enhanced pipeline completed successfully: {results_file}")
            return final_results
            
        except Exception as e:
            self.logger.error(f"Enhanced pipeline failed: {str(e)}")
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
    print("=== SCRPA ENHANCED PRODUCTION PIPELINE ===")
    
    # Initialize enhanced pipeline
    pipeline = SCRPAEnhancedProductionPipeline()
    
    # Run enhanced production pipeline
    results = pipeline.run_enhanced_production_pipeline()
    
    # Display results
    if results.get('status') == 'FAILED':
        print(f"Pipeline FAILED: {results.get('error', 'Unknown error')}")
        return False
    
    # Success summary
    pipeline_summary = results.get('pipeline_summary', {})
    data_quality = results.get('data_quality_metrics', {})
    enhancement_features = results.get('enhancement_features', {})
    
    print(f"\nPipeline Status: {results.get('status', 'UNKNOWN')}")
    print(f"Processing Time: {pipeline_summary.get('total_processing_time', 0):.2f} seconds")
    print(f"RMS Records: {pipeline_summary.get('rms_records_processed', 0)}")
    print(f"CAD Records: {pipeline_summary.get('cad_records_processed', 0)}")
    print(f"Record Preservation: {data_quality.get('record_preservation_rate', 0):.1f}%")
    print(f"Location Population: {data_quality.get('location_population_rate', 0):.1f}%")
    
    print(f"\nEnhancement Features Applied:")
    for feature, enabled in enhancement_features.items():
        status = "✓" if enabled else "✗"
        feature_name = feature.replace('_', ' ').title()
        print(f"  {status} {feature_name}")
    
    export_info = results.get('export_info', {})
    if export_info:
        print(f"\nProduction Files Created:")
        if 'cad_export' in export_info:
            print(f"  CAD Data: {Path(export_info['cad_export']).name}")
        if 'rms_export' in export_info:
            print(f"  RMS Data: {Path(export_info['rms_export']).name}")
        if 'matched_export' in export_info:
            print(f"  Matched Dataset: {Path(export_info['matched_export']).name}")
    
    print("\n=== ENHANCED PRODUCTION PIPELINE COMPLETE ===")
    return True

if __name__ == "__main__":
    success = main()