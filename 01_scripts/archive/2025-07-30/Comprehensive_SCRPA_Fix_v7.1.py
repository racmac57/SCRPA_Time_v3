# 2025-07-29-08:22:00
# SCRPA_Time_v2/Comprehensive_SCRPA_Fix_v7.1
# Author: R. A. Carucci (with modifications by Gemini)
# Purpose: A comprehensive and final script to resolve all known data quality issues.
# Version 7.1 Update: Re-integrated the specific fix for the 'How Reported' column.

import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path
import logging

class ComprehensiveSCRPAFixV7_1:
    """
    COMPREHENSIVE FIX FOR ALL SCRPA ISSUES:
    ✅ Unified CaseNumber column with 0% nulls (from v6).
    ✅ NO RMS unpivoting (from v6).
    ✅ Advanced Crime_Category mapping using a reference file (from Complete Spec).
    ✅ Correct creation of Vehicle_1, Vehicle_2, and uppercase formatting.
    ✅ Solves Power BI Time parsing error by handling time-only columns.
    ✅ Fixes nulls in CAD_ResponseType with improved logic (from v5).
    ✅ **NEW in v7.1**: Added specific cleaning for the 'How Reported' column.
    """
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)
            
        # Export directories from v6
        self.export_dirs = {
            'cad_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA"),
            'rms_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA")
        }
        
        # Reference directories from Complete Specification
        self.ref_dirs = {
            'call_types': self.project_path / '09_Reference' / 'CallType_Categories.xlsx'
        }
        
        self.call_type_ref = None
        self.setup_logging()
        self.load_reference_data()
        
    def setup_logging(self):
        """Setup comprehensive logging."""
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"comprehensive_scrpa_fix_v7_1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.logger = logging.getLogger('ComprehensiveSCRPAFixV7_1')
        self.logger.setLevel(logging.INFO)
        
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        fh = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        self.logger.info("Comprehensive SCRPA Fix V7.1 initialized.")

    def load_reference_data(self):
        """Load reference data for crime category lookups."""
        try:
            if self.ref_dirs['call_types'].exists():
                self.call_type_ref = pd.read_excel(self.ref_dirs['call_types'])
                self.logger.info(f"Loaded call type reference: {len(self.call_type_ref)} records.")
            else:
                self.logger.warning("Call type reference file not found. Will use fallback categorization.")
        except Exception as e:
            self.logger.error(f"Could not load call type reference: {e}")

    def clean_text_comprehensive(self, text):
        """Comprehensive text cleaning to remove junk characters."""
        if pd.isna(text) or text is None:
            return '' # Return empty string instead of None to avoid downstream errors
            
        text = str(text)
        # Removes various patterns of question marks that appear as junk
        text = re.sub(r'(\s*\?\s*){2,}', ' ', text)
        text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        text = ''.join(c for c in text if c.isprintable() or c.isspace())
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def fix_datetime_parsing(self, dt_series):
        """Fix datetime parsing with multiple format attempts."""
        def parse_single_datetime(dt_value):
            if pd.isna(dt_value): return pd.NaT
            dt_str = str(dt_value).strip()
            if not dt_str or dt_str.lower() in ['nan', 'nat', 'none', '']: return pd.NaT
            
            formats_to_try = ['%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M', '%Y-%m-%d %H:%M', '%m/%d/%Y', '%Y-%m-%d']
            for fmt in formats_to_try:
                try: return pd.to_datetime(dt_str, format=fmt)
                except (ValueError, TypeError): continue
            return pd.to_datetime(dt_str, errors='coerce') # Fallback to pandas parser
            
        return dt_series.apply(parse_single_datetime)

    def fix_time_only_parsing(self, time_series):
        """Fix time-only columns to prevent Power BI errors."""
        # This converts time-like strings to a timedelta format, which Power BI can handle as a 'Time' type.
        return pd.to_timedelta(time_series, errors='coerce')

    def apply_crime_category_lookup(self, df):
        """Apply Crime_Category using reference lookup; fallback if needed."""
        incident_col = 'ALL_INCIDENTS'
        if incident_col not in df.columns:
            self.logger.error("ALL_INCIDENTS column not found for categorization.")
            df['Crime_Category'] = 'Other'
            return df

        # Use advanced lookup if reference file was loaded
        if self.call_type_ref is not None:
            self.logger.info("Applying Crime_Category using reference file.")
            lookup_dict = dict(zip(self.call_type_ref['CallType'].str.upper(), self.call_type_ref['Category']))
            
            def categorize_with_lookup(incident_type):
                incident_upper = str(incident_type).upper()
                # Try partial matching for complex incident strings
                for key, category in lookup_dict.items():
                    if key in incident_upper:
                        return category
                return 'Other'
            df['Crime_Category'] = df[incident_col].apply(categorize_with_lookup)
        else:
            # Fallback to the hardcoded logic from v6 if reference is missing
            self.logger.warning("Applying fallback crime categorization.")
            def fallback_categorize(incident_type):
                incident_upper = str(incident_type).upper()
                if any(term in incident_upper for term in ['MOTOR VEHICLE THEFT', 'AUTO THEFT']): return 'Motor Vehicle Theft'
                if 'ROBBERY' in incident_upper: return 'Robbery'
                if 'BURGLARY' in incident_upper and 'AUTO' in incident_upper: return 'Burglary – Auto'
                if 'BURGLARY' in incident_upper and 'COMMERCIAL' in incident_upper: return 'Burglary – Commercial'
                if 'BURGLARY' in incident_upper and 'RESIDENCE' in incident_upper: return 'Burglary – Residence'
                if any(term in incident_upper for term in ['SEXUAL ASSAULT', 'AGGRAVATED SEXUAL ASSAULT']): return 'Sexual Offenses'
                return 'Other'
            df['Crime_Category'] = df[incident_col].apply(fallback_categorize)
        return df
        
    def calculate_enhanced_block(self, address):
        """Calculate a clean, standardized block-level address."""
        if pd.isna(address) or not address:
            return "Incomplete Address"
        try:
            address = str(address).strip().replace(", Hackensack, NJ, 07601", "").replace(", Hackensack, NJ", "")
            if ' & ' in address:
                parts = address.split(' & ')
                return f"{parts[0].strip()} & {parts[1].strip()}" if len(parts) == 2 and parts[1].strip() else address
            
            parts = address.split()
            if parts and parts[0].replace('-', '').isdigit():
                street_num = int(parts[0].replace('-', ''))
                street_name = ' '.join(parts[1:]).split(',')[0].strip()
                if street_name:
                    block_num = (street_num // 100) * 100
                    return f"{street_name}, {block_num} Block"
            
            street_name = address.split(',')[0].strip()
            return f"{street_name}, Unknown Block" if street_name else "Incomplete Address"
        except:
            return "Address Processing Error"

    def process_cad_data(self, cad_file):
        """Process CAD data with all fixes applied."""
        self.logger.info(f"Processing CAD data: {cad_file.name}")
        cad_df = pd.read_excel(cad_file, engine='openpyxl')
        
        # 1. Clean all text columns first
        for col in cad_df.select_dtypes(include=['object']).columns:
            cad_df[col] = cad_df[col].apply(self.clean_text_comprehensive)

        # 2. Create unified CaseNumber (from v6 logic)
        case_col = next((c for c in ['ReportNumberNew', 'Case_Number'] if c in cad_df.columns), None)
        cad_df['CaseNumber'] = cad_df[case_col].fillna('') if case_col else [f"CAD_{i}" for i in range(len(cad_df))]

        # 3. Create ALL_INCIDENTS
        incident_col = next((c for c in cad_df.columns if 'incident' in c.lower()), None)
        cad_df['ALL_INCIDENTS'] = cad_df[incident_col].fillna('') if incident_col else ''
        
        # 4. Fix data types and parse dates/times
        datetime_cols = ['Time of Call', 'Time Dispatched', 'Time Out', 'Time In']
        for col in datetime_cols:
            if col in cad_df.columns: cad_df[col] = self.fix_datetime_parsing(cad_df[col])
        
        time_only_cols = ['Time Spent', 'Response Time'] # Add other time-only columns if they exist
        for col in time_only_cols:
            if col in cad_df.columns: cad_df[col] = self.fix_time_only_parsing(cad_df[col])
        
        if 'PDZone' in cad_df.columns:
            cad_df['PDZone'] = pd.to_numeric(cad_df['PDZone'], errors='coerce').fillna(0).astype(int)
        
        # 5. *** NEW in v7.1 *** Fix 'How Reported' column to prevent misinterpreting '9-1-1' as a date.
        if 'How Reported' in cad_df.columns:
            self.logger.info("Cleaning 'How Reported' column.")
            col = 'How Reported'
            cad_df[col] = cad_df[col].astype(str)
            # Using a non-capturing group (?:...) to avoid the UserWarning from the logs.
            cad_df.loc[cad_df[col].str.contains(r'\d{1,2}/\d{1,2}/(?:19|20)\d{2}', na=False, regex=True), col] = '9-1-1'
            cad_df.loc[cad_df[col].str.contains(r'\d{4}-\d{2}-\d{2}', na=False, regex=True), col] = '9-1-1'
            cad_df[col] = cad_df[col].replace({'37135': '9-1-1'})
            
        # 6. Fix Response Type (Improved logic from v5)
        def assign_response_type(row):
            incident = str(row.get('ALL_INCIDENTS', '')).upper()
            emergency = ['SHOOTING', 'STABBING', 'ROBBERY', 'BURGLARY', 'ASSAULT', 'DOMESTIC', 'ALARM', 'MOTOR VEHICLE THEFT', 'SEXUAL', '9-1-1']
            priority = ['THEFT', 'CRIMINAL', 'SUSPICIOUS', 'DRUG', 'WARRANT']
            if any(kw in incident for kw in emergency): return 'Emergency'
            if any(kw in incident for kw in priority): return 'Priority'
            return 'Routine'
        cad_df['CAD_ResponseType'] = cad_df.apply(assign_response_type, axis=1)

        # 7. Apply standard transformations
        cad_df = self.apply_crime_category_lookup(cad_df)
        address_col = next((c for c in ['FullAddress2', 'Address'] if c in cad_df.columns), None)
        cad_df['Enhanced_Block'] = cad_df[address_col].apply(self.calculate_enhanced_block) if address_col else 'No Address Data'
        cad_df['DataSource'] = 'CAD'
        
        # 8. Add prefixes to remaining columns
        shared_cols = {'CaseNumber', 'ALL_INCIDENTS', 'Crime_Category', 'Enhanced_Block', 'DataSource'}
        cad_df = cad_df.rename(columns={c: f'CAD_{c}' for c in cad_df.columns if c not in shared_cols})
        
        self.logger.info(f"CAD processing complete: {len(cad_df)} records.")
        return cad_df

    def process_rms_data(self, rms_file):
        """Process RMS data with all fixes, including vehicle data."""
        self.logger.info(f"Processing RMS data: {rms_file.name}")
        rms_df = pd.read_excel(rms_file, engine='openpyxl')

        # 1. Clean all text columns first
        for col in rms_df.select_dtypes(include=['object']).columns:
            rms_df[col] = rms_df[col].apply(self.clean_text_comprehensive)
            
        # 2. Uppercase vehicle columns before combination
        vehicle_cols = [c for c in rms_df.columns if any(kw in c for kw in ['Registration', 'Make', 'Model', 'Reg State'])]
        for col in vehicle_cols:
            rms_df[col] = rms_df[col].str.upper()
        self.logger.info("Applied uppercase to vehicle data.")

        # 3. Create unified CaseNumber
        case_col = next((c for c in ['Case Number', 'CaseNumber'] if c in rms_df.columns), None)
        rms_df['CaseNumber'] = rms_df[case_col].fillna('') if case_col else [f"RMS_{i}" for i in range(len(rms_df))]
        
        # 4. Create ALL_INCIDENTS (No unpivoting)
        incident_cols = sorted([c for c in rms_df.columns if 'Incident Type_' in c])
        rms_df['ALL_INCIDENTS'] = rms_df[incident_cols].apply(lambda row: ', '.join(row.dropna().astype(str)), axis=1)
        
        # 5. Combine vehicle data into derived columns
        def combine_vehicle(row, num):
            parts = [row.get(f'RMS_Registration {num}', ''), row.get(f'RMS_Reg State {num}', ''), row.get(f'RMS_Make{num}', ''), row.get(f'RMS_Model{num}', '')]
            return ' '.join(p for p in parts if p).strip()

        rms_df['Vehicle_1'] = rms_df.apply(combine_vehicle, num=1, axis=1)
        rms_df['Vehicle_2'] = rms_df.apply(combine_vehicle, num=2, axis=1)
        rms_df['Vehicle_and_Vehicle_2'] = rms_df.apply(lambda row: ' | '.join(v for v in [row['Vehicle_1'], row['Vehicle_2']] if v), axis=1)
        self.logger.info("Created derived vehicle columns.")
        
        # 6. Apply standard transformations
        rms_df = self.apply_crime_category_lookup(rms_df)
        address_col = next((c for c in ['FullAddress', 'Address'] if c in rms_df.columns), None)
        rms_df['Enhanced_Block'] = rms_df[address_col].apply(self.calculate_enhanced_block) if address_col else 'No Address Data'
        rms_df['DataSource'] = 'RMS'
        
        # 7. Add prefixes to remaining columns
        shared_cols = {'CaseNumber', 'ALL_INCIDENTS', 'Crime_Category', 'Enhanced_Block', 'DataSource', 'Vehicle_1', 'Vehicle_2', 'Vehicle_and_Vehicle_2'}
        rms_df = rms_df.rename(columns={c: f'RMS_{c}' for c in rms_df.columns if c not in shared_cols})

        self.logger.info(f"RMS processing complete: {len(rms_df)} records.")
        return rms_df

    def find_latest_files(self):
        """Find the most recent CAD and RMS Excel files in the export directories."""
        latest_files = {}
        for key, path in self.export_dirs.items():
            if path.exists():
                files = list(path.glob("*.xlsx"))
                if files:
                    latest_file = max(files, key=lambda f: f.stat().st_mtime)
                    latest_files[key.replace('_exports', '')] = latest_file
                    self.logger.info(f"Latest {key.replace('_exports', '')} file: {latest_file.name}")
        return latest_files

    def process_final_pipeline(self):
        """Execute the complete, fixed data processing pipeline."""
        self.logger.info("Starting Comprehensive SCRPA Fix V7.1 pipeline...")
        latest_files = self.find_latest_files()
        
        processed_data = []
        if 'cad' in latest_files:
            processed_data.append(self.process_cad_data(latest_files['cad']))
        if 'rms' in latest_files:
            processed_data.append(self.process_rms_data(latest_files['rms']))
            
        if not processed_data:
            self.logger.error("No CAD or RMS files found to process. Exiting.")
            raise ValueError("No data files found.")
            
        final_df = pd.concat(processed_data, ignore_index=True, sort=False)
        
        # Final guarantee of no null CaseNumbers
        null_mask = final_df['CaseNumber'].isnull() | (final_df['CaseNumber'] == '')
        if null_mask.any():
            final_df.loc[null_mask, 'CaseNumber'] = [f"GEN_{i:06d}" for i in range(null_mask.sum())]
        
        # Reorder columns for clarity
        priority_cols = ['CaseNumber', 'ALL_INCIDENTS', 'Crime_Category', 'Enhanced_Block', 'DataSource', 'Vehicle_1', 'Vehicle_2', 'Vehicle_and_Vehicle_2']
        ordered_cols = [c for c in priority_cols if c in final_df.columns]
        other_cols = sorted([c for c in final_df.columns if c not in ordered_cols])
        final_df = final_df[ordered_cols + other_cols]
        
        # Export
        output_file = self.project_path / '04_powerbi' / 'enhanced_scrpa_data_v7_1_fixed.csv'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(output_file, index=False, encoding='utf-8')
        
        self.logger.info("=" * 60)
        self.logger.info("COMPREHENSIVE SCRPA FIX V7.1 COMPLETE")
        self.logger.info(f"✅ Total records processed: {len(final_df)}")
        self.logger.info(f"✅ Null/Empty CaseNumbers: {(final_df['CaseNumber'].isnull() | (final_df['CaseNumber'] == '')).sum()}")
        self.logger.info(f"✅ Output file: {output_file}")
        self.logger.info("=" * 60)
        
        return final_df, str(output_file)

# To run the script:
if __name__ == "__main__":
    try:
        processor = ComprehensiveSCRPAFixV7_1()
        final_df, output_path = processor.process_final_pipeline()
        print(f"✅ Processing complete. {len(final_df)} records saved to {output_path}")
        print(f"📊 Null or empty case numbers in final output: {(final_df['CaseNumber'].isnull() | (final_df['CaseNumber'] == '')).sum()}")
    except Exception as e:
        print(f"❌ An error occurred during processing: {e}")
        logging.getLogger('ComprehensiveSCRPAFixV7_1').error(f"Fatal error in main execution: {e}", exc_info=True)