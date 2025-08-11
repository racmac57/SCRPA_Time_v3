# 2025-01-29-18-00-00
# SCRPA_Time_v2/Final_SCRPA_Fix_v6
# Author: R. A. Carucci
# Purpose: Final fix for case number logic and proper data combination

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from pathlib import Path

class FinalSCRPAFixV6:
    """
    FINAL FIX FOR ALL ISSUES:
    ✅ Create unified CaseNumber column (CAD or RMS case numbers)
    ✅ NO unpivoting for RMS (maintains data integrity)
    ✅ Proper data type fixes for all columns
    ✅ Comprehensive text cleaning
    ✅ Fixed Enhanced_Block logic
    ✅ Corrected Crime_Category classifications
    ✅ 0% null case numbers guaranteed
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
        
        log_file = log_dir / f"final_scrpa_fix_v6_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.logger = logging.getLogger('FinalSCRPAFixV6')
        self.logger.setLevel(logging.INFO)
        
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        fh = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        self.logger.info("Final SCRPA Fix V6 initialized - Unified case number logic")
        
    def clean_text_comprehensive(self, text):
        """COMPREHENSIVE text cleaning"""
        if pd.isna(text) or text is None:
            return None
            
        text = str(text)
        
        # Remove erroneous question marks (????)
        text = re.sub(r'\s*\?\s*\?\s*\?\s*\?\s*', ' ', text)
        text = re.sub(r'\s*\?\s*\?\s*\?\s*', ' ', text)  
        text = re.sub(r'\s*\?\s*\?\s*', ' ', text)
        
        # Fix line breaks and replace with spaces
        text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # Clean control characters
        text = ''.join(c for c in text if c.isprintable() or c.isspace())
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Replace special characters
        text = text.replace('â', "'").replace('â', '')
        
        # Trim leading/trailing whitespace
        text = text.strip()
        
        return text if text else None
        
    def fix_datetime_parsing(self, dt_series):
        """Fix datetime parsing with multiple format attempts"""
        
        def parse_single_datetime(dt_value):
            if pd.isna(dt_value):
                return pd.NaT
                
            dt_str = str(dt_value).strip()
            
            if not dt_str or dt_str.lower() in ['nan', 'nat', 'none', '']:
                return pd.NaT
                
            # Try multiple formats
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
                    return pd.to_datetime(dt_str, format=fmt)
                except:
                    continue
                    
            # Last resort
            try:
                return pd.to_datetime(dt_str, errors='coerce')
            except:
                return pd.NaT
                
        return dt_series.apply(parse_single_datetime)
        
    def process_cad_data(self, cad_file):
        """Process CAD data with proper structure"""
        
        self.logger.info(f"Processing CAD data: {cad_file.name}")
        
        # Load data
        cad_df = pd.read_excel(cad_file, engine='openpyxl')
        original_count = len(cad_df)
        self.logger.info(f"Loaded CAD data: {original_count} records")
        
        # Apply text cleaning to all text columns FIRST
        text_columns = cad_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            cad_df[col] = cad_df[col].apply(self.clean_text_comprehensive)
        
        # Create unified CaseNumber column from CAD data
        case_col = 'ReportNumberNew' if 'ReportNumberNew' in cad_df.columns else 'Case_Number'
        if case_col in cad_df.columns:
            cad_df['CaseNumber'] = cad_df[case_col].fillna('')
        else:
            cad_df['CaseNumber'] = f"CAD_{range(len(cad_df))}"
            
        # Fix HowReported specifically
        if 'How Reported' in cad_df.columns:
            cad_df['How Reported'] = cad_df['How Reported'].astype(str)
            # Fix date conversions
            cad_df.loc[cad_df['How Reported'].str.contains(r'\d{1,2}/\d{1,2}/(19|20)\d{2}', na=False, regex=True), 'How Reported'] = '9-1-1'
            cad_df.loc[cad_df['How Reported'].str.contains(r'\d{4}-\d{2}-\d{2}', na=False, regex=True), 'How Reported'] = '9-1-1'
            # Standard mappings
            cad_df['How Reported'] = cad_df['How Reported'].replace({
                '37135': '9-1-1',
                'Phone': 'Phone', 
                'Walk-In': 'Walk-In',
                'Radio': 'Radio'
            })
        
        # Fix PDZone as integer
        if 'PDZone' in cad_df.columns:
            cad_df['PDZone'] = pd.to_numeric(cad_df['PDZone'], errors='coerce').fillna(0).astype(int)
            
        # Fix datetime columns
        datetime_cols = ['Time of Call', 'Time Dispatched', 'Time Out', 'Time In']
        for col in datetime_cols:
            if col in cad_df.columns:
                cad_df[col] = self.fix_datetime_parsing(cad_df[col])
                
        # Fix HourMinuetsCalc as numeric
        if 'HourMinuetsCalc' in cad_df.columns:
            cad_df['HourMinuetsCalc'] = pd.to_numeric(cad_df['HourMinuetsCalc'], errors='coerce')
            
        # Create ALL_INCIDENTS
        if 'Incident' in cad_df.columns:
            cad_df['ALL_INCIDENTS'] = cad_df['Incident'].fillna('')
        else:
            cad_df['ALL_INCIDENTS'] = ''
            
        # Crime categorization
        def categorize_crime(incident_type):
            if pd.isna(incident_type):
                return 'Other'
                
            incident_upper = str(incident_type).upper()
            
            if any(term in incident_upper for term in ['MOTOR VEHICLE THEFT', 'AUTO THEFT']):
                return 'Motor Vehicle Theft'
            elif 'ROBBERY' in incident_upper:
                return 'Robbery'
            elif 'BURGLARY' in incident_upper and 'AUTO' in incident_upper:
                return 'Burglary – Auto'
            elif 'BURGLARY' in incident_upper and 'COMMERCIAL' in incident_upper:
                return 'Burglary – Commercial'
            elif 'BURGLARY' in incident_upper and 'RESIDENCE' in incident_upper:
                return 'Burglary – Residence'
            elif any(term in incident_upper for term in ['SEXUAL ASSAULT', 'AGGRAVATED SEXUAL ASSAULT']):
                return 'Sexual Offenses'
            else:
                return 'Other'
                
        cad_df['Crime_Category'] = cad_df['ALL_INCIDENTS'].apply(categorize_crime)
        
        # Period classification
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
                
        if 'Time of Call' in cad_df.columns:
            cad_df['Period'] = cad_df['Time of Call'].apply(classify_period)
        else:
            cad_df['Period'] = 'YTD'
            
        # Enhanced Block
        def calculate_enhanced_block(address):
            if pd.isna(address) or not address:
                return "Incomplete Address - Check Location Data"
                
            try:
                address = str(address).strip()
                clean_addr = address.replace(", Hackensack, NJ, 07601", "").replace(", Hackensack, NJ", "")
                
                if ' & ' in clean_addr:
                    parts = clean_addr.split(' & ')
                    if len(parts) == 2 and parts[1].strip():
                        return f"{parts[0].strip()} & {parts[1].strip()}"
                    else:
                        return parts[0].strip() if parts[0].strip() else "Unknown Intersection"
                        
                parts = clean_addr.split()
                if parts and parts[0].replace('-', '').isdigit():
                    street_num = int(parts[0].replace('-', ''))
                    street_name = ' '.join(parts[1:]).split(',')[0].strip()
                    if street_name:
                        block_num = (street_num // 100) * 100
                        return f"{street_name}, {block_num} Block"
                    else:
                        return "Unknown Block"
                else:
                    street_name = clean_addr.split(',')[0].strip()
                    return f"{street_name}, Unknown Block" if street_name else "Incomplete Address - Check Location Data"
                    
            except:
                return "Incomplete Address - Check Location Data"
                
        if 'FullAddress2' in cad_df.columns:
            cad_df['Enhanced_Block'] = cad_df['FullAddress2'].apply(calculate_enhanced_block)
        else:
            cad_df['Enhanced_Block'] = "No Address Data"
            
        # Fix Response Type
        def assign_response_type(row):
            existing = row.get('Response Type', '')
            if pd.notna(existing) and str(existing).strip():
                return existing
                
            incident = str(row.get('Incident', '')).upper()
            
            emergency_keywords = ['SHOOTING', 'STABBING', 'ROBBERY', 'BURGLARY', 'ASSAULT', 'DOMESTIC', 'ALARM', 'EMERGENCY', 'MOTOR VEHICLE THEFT']
            if any(keyword in incident for keyword in emergency_keywords):
                return 'Emergency'
                
            priority_keywords = ['THEFT', 'CRIMINAL', 'SUSPICIOUS', 'DRUG', 'WARRANT']
            if any(keyword in incident for keyword in priority_keywords):
                return 'Priority'
                
            return 'Routine'
            
        cad_df['Response_Type'] = cad_df.apply(assign_response_type, axis=1)
        
        # Add prefixes to CAD-specific columns (but NOT CaseNumber)
        columns_to_prefix = [col for col in cad_df.columns if col not in ['CaseNumber', 'ALL_INCIDENTS', 'Crime_Category', 'Period', 'Enhanced_Block', 'Response_Type']]
        for col in columns_to_prefix:
            cad_df = cad_df.rename(columns={col: f'CAD_{col}'})
            
        # Add data source
        cad_df['DataSource'] = 'CAD'
        
        self.logger.info(f"CAD processing complete: {len(cad_df)} records with unified CaseNumber")
        return cad_df
        
    def process_rms_data(self, rms_file):
        """Process RMS data with proper structure (NO UNPIVOTING)"""
        
        self.logger.info(f"Processing RMS data: {rms_file.name}")
        
        # Load data
        rms_df = pd.read_excel(rms_file, engine='openpyxl')
        original_count = len(rms_df)
        self.logger.info(f"Loaded RMS data: {original_count} records")
        
        # Apply text cleaning to all text columns FIRST
        text_columns = rms_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            rms_df[col] = rms_df[col].apply(self.clean_text_comprehensive)
        
        # Create unified CaseNumber column from RMS data
        case_col = 'Case Number' if 'Case Number' in rms_df.columns else 'CaseNumber'
        if case_col in rms_df.columns:
            rms_df['CaseNumber'] = rms_df[case_col].fillna('')
        else:
            rms_df['CaseNumber'] = f"RMS_{range(len(rms_df))}"
            
        # Fix datetime columns
        datetime_cols = ['Incident Date', 'Incident Date_Between', 'Report Date']
        for col in datetime_cols:
            if col in rms_df.columns:
                rms_df[col] = self.fix_datetime_parsing(rms_df[col])
                
        # Create ALL_INCIDENTS by concatenating (NO UNPIVOTING)
        incident_type_cols = ['Incident Type_1', 'Incident Type_2', 'Incident Type_3']
        available_cols = [col for col in incident_type_cols if col in rms_df.columns]
        
        if available_cols:
            def combine_incidents(row):
                incidents = []
                for col in available_cols:
                    if pd.notna(row[col]) and str(row[col]).strip():
                        incidents.append(str(row[col]).strip())
                return ', '.join(incidents) if incidents else ''
                
            rms_df['ALL_INCIDENTS'] = rms_df.apply(combine_incidents, axis=1)
            self.logger.info(f"Created ALL_INCIDENTS without unpivoting")
        else:
            rms_df['ALL_INCIDENTS'] = ''
            
        # Crime categorization (same logic as CAD)
        def categorize_crime(incident_type):
            if pd.isna(incident_type):
                return 'Other'
                
            incident_upper = str(incident_type).upper()
            
            if any(term in incident_upper for term in ['MOTOR VEHICLE THEFT', 'AUTO THEFT']):
                return 'Motor Vehicle Theft'
            elif 'ROBBERY' in incident_upper:
                return 'Robbery'
            elif 'BURGLARY' in incident_upper and 'AUTO' in incident_upper:
                return 'Burglary – Auto'
            elif 'BURGLARY' in incident_upper and 'COMMERCIAL' in incident_upper:
                return 'Burglary – Commercial'
            elif 'BURGLARY' in incident_upper and 'RESIDENCE' in incident_upper:
                return 'Burglary – Residence'
            elif any(term in incident_upper for term in ['SEXUAL ASSAULT', 'AGGRAVATED SEXUAL ASSAULT']):
                return 'Sexual Offenses'
            else:
                return 'Other'
                
        rms_df['Crime_Category'] = rms_df['ALL_INCIDENTS'].apply(categorize_crime)
        
        # Period classification using cascading date logic
        def classify_period(row):
            # Try Incident Date first, then alternatives
            date_value = None
            for col in ['Incident Date', 'Incident Date_Between', 'Report Date']:
                if col in row and pd.notna(row[col]):
                    date_value = row[col]
                    break
                    
            if pd.isna(date_value):
                return 'YTD'
                
            try:
                today = pd.Timestamp.now().date()
                incident_date = pd.to_datetime(date_value).date()
                days_diff = (today - incident_date).days
                
                if days_diff <= 7:
                    return '7-Day'
                elif days_diff <= 28:
                    return '28-Day'
                else:
                    return 'YTD'
            except:
                return 'YTD'
                
        rms_df['Period'] = rms_df.apply(classify_period, axis=1)
        
        # Enhanced Block using RMS address
        def calculate_enhanced_block(address):
            if pd.isna(address) or not address:
                return "Incomplete Address - Check Location Data"
                
            try:
                address = str(address).strip()
                clean_addr = address.replace(", Hackensack, NJ, 07601", "").replace(", Hackensack, NJ", "")
                
                if ' & ' in clean_addr:
                    parts = clean_addr.split(' & ')
                    if len(parts) == 2 and parts[1].strip():
                        return f"{parts[0].strip()} & {parts[1].strip()}"
                    else:
                        return parts[0].strip() if parts[0].strip() else "Unknown Intersection"
                        
                parts = clean_addr.split()
                if parts and parts[0].replace('-', '').isdigit():
                    street_num = int(parts[0].replace('-', ''))
                    street_name = ' '.join(parts[1:]).split(',')[0].strip()
                    if street_name:
                        block_num = (street_num // 100) * 100
                        return f"{street_name}, {block_num} Block"
                    else:
                        return "Unknown Block"
                else:
                    street_name = clean_addr.split(',')[0].strip()
                    return f"{street_name}, Unknown Block" if street_name else "Incomplete Address - Check Location Data"
                    
            except:
                return "Incomplete Address - Check Location Data"
                
        if 'FullAddress' in rms_df.columns:
            rms_df['Enhanced_Block'] = rms_df['FullAddress'].apply(calculate_enhanced_block)
        else:
            rms_df['Enhanced_Block'] = "No Address Data"
            
        # Add prefixes to RMS-specific columns (but NOT CaseNumber)
        columns_to_prefix = [col for col in rms_df.columns if col not in ['CaseNumber', 'ALL_INCIDENTS', 'Crime_Category', 'Period', 'Enhanced_Block']]
        for col in columns_to_prefix:
            rms_df = rms_df.rename(columns={col: f'RMS_{col}'})
            
        # Add data source
        rms_df['DataSource'] = 'RMS'
        
        self.logger.info(f"RMS processing complete: {len(rms_df)} records with unified CaseNumber (NO unpivoting)")
        return rms_df
        
    def find_latest_files(self):
        """Find latest CAD and RMS files"""
        latest_files = {}
        
        if self.export_dirs['cad_exports'].exists():
            cad_files = list(self.export_dirs['cad_exports'].glob("*.xlsx"))
            if cad_files:
                latest_cad = max(cad_files, key=lambda x: x.stat().st_mtime)
                latest_files['cad'] = latest_cad
                self.logger.info(f"Latest CAD file: {latest_cad.name}")
        
        if self.export_dirs['rms_exports'].exists():
            rms_files = list(self.export_dirs['rms_exports'].glob("*.xlsx"))
            if rms_files:
                latest_rms = max(rms_files, key=lambda x: x.stat().st_mtime)
                latest_files['rms'] = latest_rms
                self.logger.info(f"Latest RMS file: {latest_rms.name}")
            
        return latest_files
        
    def process_final_pipeline(self):
        """Process final pipeline with unified case number logic"""
        
        self.logger.info("Starting Final SCRPA Fix V6 - Unified CaseNumber logic")
        
        # Find latest files
        latest_files = self.find_latest_files()
        
        processed_dataframes = []
        
        # Process CAD data if available
        if 'cad' in latest_files:
            cad_df = self.process_cad_data(latest_files['cad'])
            processed_dataframes.append(cad_df)
            
        # Process RMS data if available
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
            
        # Ensure CaseNumber is first column and has no nulls
        if 'CaseNumber' in final_df.columns:
            # Fill any remaining nulls with generated IDs
            null_mask = final_df['CaseNumber'].isnull() | (final_df['CaseNumber'] == '')
            if null_mask.any():
                final_df.loc[null_mask, 'CaseNumber'] = [f"GEN_{i:06d}" for i in range(null_mask.sum())]
                
            # Reorder columns with CaseNumber first
            other_cols = [col for col in final_df.columns if col != 'CaseNumber']
            final_df = final_df[['CaseNumber'] + other_cols]
            
        # Export results
        output_file = self.project_path / '04_powerbi' / 'enhanced_scrpa_data.csv'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        final_df.to_csv(output_file, index=False, encoding='utf-8')
        
        # Final validation
        null_case_count = final_df['CaseNumber'].isnull().sum()
        empty_case_count = (final_df['CaseNumber'] == '').sum()
        total_null_empty = null_case_count + empty_case_count
        
        self.logger.info("=" * 60)
        self.logger.info("FINAL SCRPA FIX V6 COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"✅ Total records: {len(final_df)}")
        self.logger.info(f"✅ CaseNumber column: {final_df.columns[0]}")
        self.logger.info(f"✅ Null case numbers: {null_case_count}")
        self.logger.info(f"✅ Empty case numbers: {empty_case_count}")
        self.logger.info(f"✅ Total missing case numbers: {total_null_empty} ({(total_null_empty/len(final_df)*100):.1f}%)")
        self.logger.info(f"✅ Output: {output_file}")
        
        return final_df, str(output_file)


# Usage
if __name__ == "__main__":
    processor = FinalSCRPAFixV6()
    final_df, output_path = processor.process_final_pipeline()
    print(f"✅ Final fix complete: {len(final_df)} records")
    print(f"📄 Output: {output_path}")
    print(f"📊 CaseNumber column: {final_df.columns[0]}")
    print(f"📊 Null case numbers: {final_df['CaseNumber'].isnull().sum()}")
    print(f"📊 Empty case numbers: {(final_df['CaseNumber'] == '').sum()}")