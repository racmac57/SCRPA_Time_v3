# 2025-01-29-17-00-00
# SCRPA_Time_v2/Fixed_SCRPA_Processor_v5
# Author: R. A. Carucci
# Purpose: Fix all identified data processing issues - NO unpivoting, proper data types, clean text

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from pathlib import Path

class FixedSCRPAProcessorV5:
    """
    FIXES ALL IDENTIFIED ISSUES:
    ❌ NO RMS unpivoting (causes 46% null case numbers)
    ✅ Keep RMS data as single records with concatenated ALL_INCIDENTS
    ✅ Fix all data type issues (CAD_Pdzone as int, proper datetime parsing)
    ✅ Comprehensive text cleaning (remove ???, trim, fix line breaks)
    ✅ Proper Enhanced_Block logic (no double entries)
    ✅ Fix Crime_Category values (no incorrect "Sexual" entries)
    ✅ Proper CAD_ResponseType logic (add urgent types)
    ✅ Handle all datetime parsing errors
    """
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)
            
        # Export directories
        self.export_dirs = {
            'cad_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA"),
            'rms_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA")
        }
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        import logging
        
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"fixed_scrpa_processor_v5_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.logger = logging.getLogger('FixedSCRPAProcessorV5')
        self.logger.setLevel(logging.INFO)
        
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        fh = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        self.logger.info("Fixed SCRPA Processor V5 initialized - NO unpivoting, proper data types")
        
    def clean_text_comprehensive(self, text):
        """COMPREHENSIVE text cleaning - Trim, Clean, fix line breaks, remove ????"""
        if pd.isna(text) or text is None:
            return None
            
        text = str(text)
        
        # Remove erroneous question marks (????)
        text = re.sub(r'\s*\?\s*\?\s*\?\s*\?\s*', ' ', text)
        text = re.sub(r'\s*\?\s*\?\s*\?\s*', ' ', text)  
        text = re.sub(r'\s*\?\s*\?\s*', ' ', text)
        
        # Fix line breaks and replace with spaces
        text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # Clean control characters (Text.Clean equivalent)
        text = ''.join(c for c in text if c.isprintable() or c.isspace())
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Replace special characters
        text = text.replace('â', "'").replace('â', '')
        
        # Trim leading/trailing whitespace
        text = text.strip()
        
        return text if text else None
        
    def fix_datetime_parsing(self, dt_series, expected_format='datetime'):
        """Fix datetime parsing errors with multiple format attempts"""
        
        def parse_single_datetime(dt_value):
            if pd.isna(dt_value):
                return pd.NaT
                
            dt_str = str(dt_value).strip()
            
            # Skip empty or null strings
            if not dt_str or dt_str.lower() in ['nan', 'nat', 'none', '']:
                return pd.NaT
                
            # Common datetime formats to try
            formats_to_try = [
                '%Y-%m-%d %H:%M:%S',
                '%m/%d/%Y %H:%M:%S', 
                '%m/%d/%Y %H:%M',
                '%Y-%m-%d %H:%M',
                '%m/%d/%Y',
                '%Y-%m-%d',
                '%H:%M:%S',
                '%H:%M'
            ]
            
            for fmt in formats_to_try:
                try:
                    parsed = pd.to_datetime(dt_str, format=fmt)
                    return parsed
                except:
                    continue
                    
            # Last resort - let pandas try to parse
            try:
                return pd.to_datetime(dt_str, errors='coerce')
            except:
                return pd.NaT
                
        # Apply parsing to entire series
        parsed_series = dt_series.apply(parse_single_datetime)
        
        # Log results
        null_count = parsed_series.isnull().sum()
        total_count = len(parsed_series)
        success_rate = ((total_count - null_count) / total_count * 100) if total_count > 0 else 0
        
        self.logger.info(f"DateTime parsing: {success_rate:.1f}% success rate ({total_count - null_count}/{total_count})")
        
        return parsed_series
        
    def fix_data_types(self, df):
        """Fix all data type issues"""
        
        # Fix CAD_Pdzone as whole number
        pdzone_cols = [col for col in df.columns if 'pdzone' in col.lower()]
        for col in pdzone_cols:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                self.logger.info(f"Fixed {col} as integer")
            except Exception as e:
                self.logger.warning(f"Could not fix {col} data type: {e}")
                
        # Fix CAD_Cyear as integer (remove .0)
        year_cols = [col for col in df.columns if 'year' in col.lower()]
        for col in year_cols:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(2025).astype(int)
                self.logger.info(f"Fixed {col} as integer")
            except Exception as e:
                self.logger.warning(f"Could not fix {col} data type: {e}")
                
        # Fix CAD_Hourminuetscalc as numeric
        hour_cols = [col for col in df.columns if 'hour' in col.lower() and 'calc' in col.lower()]
        for col in hour_cols:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                self.logger.info(f"Fixed {col} as numeric")
            except Exception as e:
                self.logger.warning(f"Could not fix {col} data type: {e}")
                
        # Fix all datetime columns
        datetime_cols = [col for col in df.columns if any(t in col.lower() for t in ['timeofcall', 'timedispatched', 'timeout', 'timein', 'incidentdate', 'reportdate'])]
        for col in datetime_cols:
            if col in df.columns:
                try:
                    df[col] = self.fix_datetime_parsing(df[col])
                    self.logger.info(f"Fixed {col} datetime parsing")
                except Exception as e:
                    self.logger.warning(f"Could not fix {col} datetime: {e}")
                    
        # Fix time-only columns 
        time_cols = [col for col in df.columns if any(t in col.lower() for t in ['timespent', 'timeresponse', 'incidenttime', 'reporttime']) and 'datetime' not in col.lower()]
        for col in time_cols:
            if col in df.columns:
                try:
                    # For time columns, try to parse as time or duration
                    df[col] = pd.to_timedelta(df[col], errors='coerce')
                    self.logger.info(f"Fixed {col} as timedelta")
                except Exception as e:
                    self.logger.warning(f"Could not fix {col} time: {e}")
                    
        return df
        
    def fix_enhanced_block(self, df):
        """Fix Enhanced_Block to eliminate double entries and invalid values"""
        
        def calculate_proper_enhanced_block(address):
            if pd.isna(address) or not address:
                return "Incomplete Address - Check Location Data"
                
            try:
                address = str(address).strip()
                
                # Clean the address
                clean_addr = address.replace(", Hackensack, NJ, 07601", "").replace(", Hackensack, NJ", "")
                
                # Handle intersections properly (no double &)
                if ' & ' in clean_addr:
                    # Clean up intersection format
                    parts = clean_addr.split(' & ')
                    if len(parts) == 2 and parts[1].strip():
                        return f"{parts[0].strip()} & {parts[1].strip()}"
                    else:
                        return parts[0].strip() if parts[0].strip() else "Unknown Intersection"
                        
                # Extract block number for regular addresses
                parts = clean_addr.split()
                if parts and parts[0].replace('-', '').isdigit():
                    try:
                        street_num = int(parts[0].replace('-', ''))
                        street_name = ' '.join(parts[1:]).split(',')[0].strip()
                        
                        # Only create block if we have a valid street name
                        if street_name:
                            block_num = (street_num // 100) * 100
                            return f"{street_name}, {block_num} Block"
                        else:
                            return "Unknown Block"
                    except:
                        return "Invalid Address Format"
                else:
                    # No number, just use street name
                    street_name = clean_addr.split(',')[0].strip()
                    if street_name:
                        return f"{street_name}, Unknown Block"
                    else:
                        return "Incomplete Address - Check Location Data"
                        
            except Exception as e:
                self.logger.warning(f"Error processing address '{address}': {e}")
                return "Incomplete Address - Check Location Data"
                
        # Apply to all address columns
        address_cols = [col for col in df.columns if 'address' in col.lower()]
        
        if address_cols:
            # Use the first available address column
            primary_address_col = address_cols[0]
            df['Enhanced_Block'] = df[primary_address_col].apply(calculate_proper_enhanced_block)
            self.logger.info(f"Fixed Enhanced_Block using {primary_address_col}")
        else:
            df['Enhanced_Block'] = "No Address Data"
            self.logger.warning("No address columns found for Enhanced_Block")
            
        return df
        
    def fix_crime_category(self, df):
        """Fix Crime_Category to eliminate incorrect values like 'Sexual'"""
        
        def categorize_crime_properly(incident_type, all_incidents=''):
            if pd.isna(incident_type):
                return 'Other'
                
            incident_upper = str(incident_type).upper()
            all_upper = str(all_incidents).upper()
            
            # Motor Vehicle Theft - highest priority
            if any(term in incident_upper for term in ['MOTOR VEHICLE THEFT', 'AUTO THEFT', 'MV THEFT']):
                return 'Motor Vehicle Theft'
            if all_incidents and 'MOTOR VEHICLE THEFT' in all_upper:
                return 'Motor Vehicle Theft'
                
            # Robbery
            if 'ROBBERY' in incident_upper or (all_incidents and 'ROBBERY' in all_upper):
                return 'Robbery'
                
            # Burglary subcategories (more specific matching)
            if 'BURGLARY' in incident_upper or (all_incidents and 'BURGLARY' in all_upper):
                if 'AUTO' in incident_upper or 'VEHICLE' in incident_upper or (all_incidents and ('AUTO' in all_upper or 'VEHICLE' in all_upper)):
                    return 'Burglary – Auto'
                elif 'COMMERCIAL' in incident_upper or (all_incidents and 'COMMERCIAL' in all_upper):
                    return 'Burglary – Commercial'  
                elif 'RESIDENCE' in incident_upper or 'RESIDENTIAL' in incident_upper or (all_incidents and ('RESIDENCE' in all_upper or 'RESIDENTIAL' in all_upper)):
                    return 'Burglary – Residence'
                else:
                    return 'Other'  # Generic burglary goes to Other
                    
            # Sexual Offenses (more specific - only for actual sexual crimes)
            if any(term in incident_upper for term in ['SEXUAL ASSAULT', 'AGGRAVATED SEXUAL ASSAULT', 'CRIMINAL SEXUAL CONTACT']):
                return 'Sexual Offenses'
            if all_incidents and any(term in all_upper for term in ['SEXUAL ASSAULT', 'AGGRAVATED SEXUAL ASSAULT', 'CRIMINAL SEXUAL CONTACT']):
                return 'Sexual Offenses'
                
            # Everything else goes to Other
            return 'Other'
            
        # Find incident type columns
        incident_col = 'ALL_INCIDENTS' if 'ALL_INCIDENTS' in df.columns else None
        if not incident_col:
            incident_cols = [col for col in df.columns if 'incident' in col.lower() and 'all' not in col.lower()]
            incident_col = incident_cols[0] if incident_cols else None
            
        if incident_col:
            df['Crime_Category'] = df.apply(
                lambda row: categorize_crime_properly(
                    row.get(incident_col, ''), 
                    row.get('ALL_INCIDENTS', '')
                ), axis=1
            )
            self.logger.info("Fixed Crime_Category with proper SCRPA classifications")
        else:
            df['Crime_Category'] = 'Other'
            self.logger.warning("No incident column found for Crime_Category")
            
        return df
        
    def fix_response_type(self, df):
        """Fix CAD_ResponseType to include urgent types"""
        
        def assign_proper_response_type(row):
            # Check existing value first
            existing_response = row.get('CAD_ResponseType', '')
            if pd.notna(existing_response) and str(existing_response).strip() and str(existing_response).strip().lower() != 'nan':
                return existing_response
                
            # Assign based on incident type
            incident = str(row.get('CAD_Incident', '')).upper()
            
            # Emergency/Urgent response types
            emergency_keywords = [
                'SHOOTING', 'STABBING', 'ROBBERY', 'BURGLARY', 'ASSAULT', 'DOMESTIC', 
                'ALARM', 'EMERGENCY', 'MOTOR VEHICLE THEFT', 'SEXUAL', '9-1-1'
            ]
            
            if any(keyword in incident for keyword in emergency_keywords):
                return 'Emergency'
                
            # Priority response types  
            priority_keywords = [
                'THEFT', 'CRIMINAL', 'SUSPICIOUS', 'DRUG', 'WARRANT', 'TRAFFIC'
            ]
            
            if any(keyword in incident for keyword in priority_keywords):
                return 'Priority'
                
            # Default to routine
            return 'Routine'
            
        # Apply response type logic
        response_cols = [col for col in df.columns if 'response' in col.lower() and 'type' in col.lower()]
        for col in response_cols:
            df[col] = df.apply(assign_proper_response_type, axis=1)
            self.logger.info(f"Fixed {col} with Emergency/Priority/Routine classifications")
            
        return df
        
    def process_cad_data(self, cad_file):
        """Process CAD data with all fixes applied"""
        
        self.logger.info(f"Processing CAD data: {cad_file.name}")
        
        # Load data
        cad_df = pd.read_excel(cad_file, engine='openpyxl')
        self.logger.info(f"Loaded CAD data: {len(cad_df)} records")
        
        # Add CAD_ prefix to all columns
        cad_df.columns = ['CAD_' + col if not col.startswith('CAD_') else col for col in cad_df.columns]
        
        # Apply comprehensive text cleaning to all text columns
        text_columns = cad_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            cad_df[col] = cad_df[col].apply(self.clean_text_comprehensive)
            
        # Fix data types
        cad_df = self.fix_data_types(cad_df)
        
        # Create ALL_INCIDENTS (no unpivoting for CAD)
        incident_col = [col for col in cad_df.columns if 'incident' in col.lower() and 'all' not in col.lower()]
        if incident_col:
            cad_df['ALL_INCIDENTS'] = cad_df[incident_col[0]].fillna('')
        else:
            cad_df['ALL_INCIDENTS'] = ''
            
        # Apply fixes
        cad_df = self.fix_enhanced_block(cad_df)
        cad_df = self.fix_crime_category(cad_df)
        cad_df = self.fix_response_type(cad_df)
        
        # Add period classification
        def classify_period(dt):
            if pd.isna(dt):
                return 'YTD'
            try:
                today = pd.Timestamp.now().date()
                incident_date = pd.to_datetime(dt).date()
                days_diff = (today - incident_date).days
                
                if days_diff <= 7:
                    return '7-Day'
                elif days_diff <= 28:
                    return '28-Day'
                else:
                    return 'YTD'
            except:
                return 'YTD'
                
        datetime_col = [col for col in cad_df.columns if 'timeofcall' in col.lower() or 'datetime' in col.lower()]
        if datetime_col:
            cad_df['Period'] = cad_df[datetime_col[0]].apply(classify_period)
        else:
            cad_df['Period'] = 'YTD'
            
        # Add data source
        cad_df['DataSource'] = 'CAD'
        
        self.logger.info(f"CAD processing complete: {len(cad_df)} records with all fixes applied")
        return cad_df
        
    def process_rms_data(self, rms_file):
        """Process RMS data WITHOUT unpivoting (keep as single records)"""
        
        self.logger.info(f"Processing RMS data: {rms_file.name}")
        
        # Load data
        rms_df = pd.read_excel(rms_file, engine='openpyxl')
        self.logger.info(f"Loaded RMS data: {len(rms_df)} records")
        
        # Add RMS_ prefix to all columns
        rms_df.columns = ['RMS_' + col if not col.startswith('RMS_') else col for col in rms_df.columns]
        
        # Apply comprehensive text cleaning
        text_columns = rms_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            rms_df[col] = rms_df[col].apply(self.clean_text_comprehensive)
            
        # Fix data types
        rms_df = self.fix_data_types(rms_df)
        
        # Create ALL_INCIDENTS by concatenating (NO UNPIVOTING)
        incident_type_cols = [col for col in rms_df.columns if 'incidenttype' in col.lower() and any(x in col for x in ['1', '2', '3'])]
        
        if incident_type_cols:
            def combine_incidents_no_unpivot(row):
                incidents = []
                for col in sorted(incident_type_cols):
                    if pd.notna(row[col]) and str(row[col]).strip():
                        incidents.append(str(row[col]).strip())
                return ', '.join(incidents) if incidents else ''
                
            rms_df['ALL_INCIDENTS'] = rms_df.apply(combine_incidents_no_unpivot, axis=1)
            self.logger.info(f"Created ALL_INCIDENTS without unpivoting: {len(rms_df)} records maintained")
        else:
            rms_df['ALL_INCIDENTS'] = ''
            
        # Apply fixes
        rms_df = self.fix_enhanced_block(rms_df)
        rms_df = self.fix_crime_category(rms_df)
        
        # Add period classification
        def classify_period(dt):
            if pd.isna(dt):
                return 'YTD'
            try:
                today = pd.Timestamp.now().date()
                incident_date = pd.to_datetime(dt).date()
                days_diff = (today - incident_date).days
                
                if days_diff <= 7:
                    return '7-Day'
                elif days_diff <= 28:
                    return '28-Day'
                else:
                    return 'YTD'
            except:
                return 'YTD'
                
        # Use cascading date logic for period
        date_col = None
        for col_variation in ['RMS_IncidentDate', 'RMS_IncidentDateBetween', 'RMS_ReportDate']:
            if col_variation in rms_df.columns:
                date_col = col_variation
                break
                
        if date_col:
            rms_df['Period'] = rms_df[date_col].apply(classify_period)
        else:
            rms_df['Period'] = 'YTD'
            
        # Add data source
        rms_df['DataSource'] = 'RMS'
        
        self.logger.info(f"RMS processing complete: {len(rms_df)} records (NO unpivoting)")
        return rms_df
        
    def find_latest_files(self):
        """Find latest CAD and RMS files"""
        latest_files = {}
        
        # Find latest CAD file
        if self.export_dirs['cad_exports'].exists():
            cad_files = list(self.export_dirs['cad_exports'].glob("*.xlsx"))
            if cad_files:
                latest_cad = max(cad_files, key=lambda x: x.stat().st_mtime)
                latest_files['cad'] = latest_cad
                self.logger.info(f"Latest CAD file: {latest_cad.name}")
        
        # Find latest RMS file  
        if self.export_dirs['rms_exports'].exists():
            rms_files = list(self.export_dirs['rms_exports'].glob("*.xlsx"))
            if rms_files:
                latest_rms = max(rms_files, key=lambda x: x.stat().st_mtime)
                latest_files['rms'] = latest_rms
                self.logger.info(f"Latest RMS file: {latest_rms.name}")
            
        return latest_files
        
    def reorder_columns_properly(self, df):
        """Reorder columns with Case_Number first and logical grouping"""
        
        # Find case number column
        case_num_col = None
        for col in df.columns:
            if 'casenumber' in col.lower() and col in df.columns:
                case_num_col = col
                break
                
        if not case_num_col:
            self.logger.warning("No case number column found for reordering")
            return df
            
        # Priority columns in logical order
        priority_columns = [
            case_num_col,  # Case number FIRST
            'ALL_INCIDENTS',
            'Crime_Category', 
            'Period',
            'Enhanced_Block',
            'DataSource'
        ]
        
        # Get all other columns
        other_columns = [col for col in df.columns if col not in priority_columns]
        
        # Final column order
        final_order = [col for col in priority_columns if col in df.columns] + other_columns
        
        # Reorder dataframe
        df = df[final_order]
        
        self.logger.info(f"Reordered columns with {case_num_col} as Column 0")
        return df
        
    def process_complete_fixed_pipeline(self):
        """Process complete pipeline with all fixes applied"""
        
        self.logger.info("Starting Fixed SCRPA Processing V5 - NO unpivoting, all data type fixes")
        
        # Find latest files
        latest_files = self.find_latest_files()
        
        processed_dataframes = []
        
        # Process CAD data if available
        if 'cad' in latest_files:
            cad_df = self.process_cad_data(latest_files['cad'])
            processed_dataframes.append(cad_df)
            
        # Process RMS data if available (NO UNPIVOTING)
        if 'rms' in latest_files:
            rms_df = self.process_rms_data(latest_files['rms'])
            processed_dataframes.append(rms_df)
            
        if not processed_dataframes:
            raise ValueError("No CAD or RMS files found to process")
            
        # Combine all dataframes
        if len(processed_dataframes) == 1:
            final_df = processed_dataframes[0]
        else:
            final_df = pd.concat(processed_dataframes, ignore_index=True, sort=False)
            
        # Final column reordering
        final_df = self.reorder_columns_properly(final_df)
        
        # Export results
        output_file = self.project_path / '04_powerbi' / 'enhanced_scrpa_data.csv'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        final_df.to_csv(output_file, index=False, encoding='utf-8')
        
        # Final validation
        case_col = final_df.columns[0]
        null_case_count = final_df[case_col].isnull().sum()
        null_case_pct = (null_case_count / len(final_df)) * 100
        
        self.logger.info("=" * 60)
        self.logger.info("FIXED PROCESSING V5 COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"✅ Total records: {len(final_df)}")
        self.logger.info(f"✅ Case number column: {case_col}")
        self.logger.info(f"✅ Null case numbers: {null_case_count} ({null_case_pct:.1f}%)")
        self.logger.info(f"✅ Output: {output_file}")
        
        return final_df, str(output_file)


# Usage
if __name__ == "__main__":
    processor = FixedSCRPAProcessorV5()
    final_df, output_path = processor.process_complete_fixed_pipeline()
    print(f"✅ Fixed processing complete: {len(final_df)} records")
    print(f"📄 Output: {output_path}")
    print(f"📊 Case number column: {final_df.columns[0]}")
    print(f"📊 Null case numbers: {final_df[final_df.columns[0]].isnull().sum()}")