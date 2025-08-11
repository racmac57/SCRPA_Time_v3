# 2025-07-29-08:28:00
# SCRPA_Time_v2/Comprehensive_SCRPA_Fix_v7.2
# Author: R. A. Carucci (with modifications by Gemini)
# Purpose: Final version with adjustments for minor remaining data issues.
# Version 7.2 Update: Improved junk character removal and fixed CAD_ResponseType column name.

import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path
import logging

class ComprehensiveSCRPAFixV7_2:
    """
    FINAL COMPREHENSIVE FIX FOR ALL SCRPA ISSUES:
    ✅ Fixed CaseNumber with 0% nulls.
    ✅ Advanced Crime_Category mapping from reference file.
    ✅ Correct creation and formatting of Vehicle columns.
    ✅ Solved Power BI Time parsing error.
    ✅ Cleaned 'How Reported' column.
    ✅ **NEW in v7.2**: Improved junk character '????' removal.
    ✅ **NEW in v7.2**: Fixed 'CAD_CAD_ResponseType' double prefix bug.
    """
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)
            
        self.export_dirs = {
            'cad_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA"),
            'rms_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA")
        }
        
        self.ref_dirs = {
            'call_types': self.project_path / '09_Reference' / 'CallType_Categories.xlsx'
        }
        
        self.call_type_ref = None
        self.setup_logging()
        self.load_reference_data()
        
    def setup_logging(self):
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"comprehensive_scrpa_fix_v7_2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = logging.getLogger('ComprehensiveSCRPAFixV7_2')
        self.logger.setLevel(logging.INFO)
        if self.logger.hasHandlers(): self.logger.handlers.clear()
        fh = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.info("Comprehensive SCRPA Fix V7.2 initialized.")

    def load_reference_data(self):
        try:
            if self.ref_dirs['call_types'].exists():
                self.call_type_ref = pd.read_excel(self.ref_dirs['call_types'])
                self.logger.info(f"Loaded call type reference: {len(self.call_type_ref)} records.")
            else:
                self.logger.warning("Call type reference file not found. Will use fallback categorization.")
        except Exception as e:
            self.logger.error(f"Could not load call type reference: {e}")

    def clean_text_comprehensive(self, text):
        if pd.isna(text) or text is None: return ''
        text = str(text)
        # More aggressive regex to catch any sequence of question marks and surrounding whitespace/dashes
        text = re.sub(r'(\s*[\?\-]\s*){2,}', ' ', text)
        text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        text = ''.join(c for c in text if c.isprintable() or c.isspace())
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def fix_datetime_parsing(self, dt_series):
        def parse_single_datetime(dt_value):
            if pd.isna(dt_value): return pd.NaT
            dt_str = str(dt_value).strip()
            if not dt_str or dt_str.lower() in ['nan', 'nat', 'none', '']: return pd.NaT
            formats_to_try = ['%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M', '%Y-%m-%d %H:%M', '%m/%d/%Y', '%Y-%m-%d']
            for fmt in formats_to_try:
                try: return pd.to_datetime(dt_str, format=fmt)
                except (ValueError, TypeError): continue
            return pd.to_datetime(dt_str, errors='coerce')
        return dt_series.apply(parse_single_datetime)

    def fix_time_only_parsing(self, time_series):
        return pd.to_timedelta(time_series.astype(str), errors='coerce')

    def apply_crime_category_lookup(self, df):
        incident_col = 'ALL_INCIDENTS'
        if incident_col not in df.columns:
            df['Crime_Category'] = 'Other'
            return df
        if self.call_type_ref is not None:
            self.logger.info("Applying Crime_Category using reference file.")
            lookup_dict = dict(zip(self.call_type_ref['CallType'].str.upper(), self.call_type_ref['Category']))
            def categorize_with_lookup(incident_type):
                incident_upper = str(incident_type).upper()
                for key, category in lookup_dict.items():
                    if key in incident_upper: return category
                return 'Other'
            df['Crime_Category'] = df[incident_col].apply(categorize_with_lookup)
        else:
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
        if pd.isna(address) or not address: return "Incomplete Address"
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
                    return f"{street_name}, {(street_num // 100) * 100} Block"
            street_name = address.split(',')[0].strip()
            return f"{street_name}, Unknown Block" if street_name else "Incomplete Address"
        except:
            return "Address Processing Error"

    def process_cad_data(self, cad_file):
        self.logger.info(f"Processing CAD data: {cad_file.name}")
        cad_df = pd.read_excel(cad_file, engine='openpyxl')
        
        for col in cad_df.select_dtypes(include=['object']).columns:
            cad_df[col] = cad_df[col].apply(self.clean_text_comprehensive)

        case_col = next((c for c in ['ReportNumberNew', 'Case_Number'] if c in cad_df.columns), None)
        cad_df['CaseNumber'] = cad_df[case_col].fillna('') if case_col else [f"CAD_{i}" for i in range(len(cad_df))]

        incident_col = next((c for c in cad_df.columns if 'incident' in c.lower()), None)
        cad_df['ALL_INCIDENTS'] = cad_df[incident_col].fillna('') if incident_col else ''
        
        for col in ['Time of Call', 'Time Dispatched', 'Time Out', 'Time In']:
            if col in cad_df.columns: cad_df[col] = self.fix_datetime_parsing(cad_df[col])
        for col in ['Time Spent', 'Response Time', 'HourMinuetsCalc']:
            if col in cad_df.columns: cad_df[col] = self.fix_time_only_parsing(cad_df[col])
        if 'PDZone' in cad_df.columns:
            cad_df['PDZone'] = pd.to_numeric(cad_df['PDZone'], errors='coerce').fillna(0).astype(int)
        
        if 'How Reported' in cad_df.columns:
            self.logger.info("Cleaning 'How Reported' column.")
            col = 'How Reported'
            cad_df[col] = cad_df[col].astype(str)
            cad_df.loc[cad_df[col].str.contains(r'\d{1,2}/\d{1,2}/(?:19|20)\d{2}', na=False, regex=True), col] = '9-1-1'
            cad_df.loc[cad_df[col].str.contains(r'\d{4}-\d{2}-\d{2}', na=False, regex=True), col] = '9-1-1'
            cad_df[col] = cad_df[col].replace({'37135': '9-1-1'})
            
        def assign_response_type(row):
            incident = str(row.get('ALL_INCIDENTS', '')).upper()
            if any(kw in incident for kw in ['SHOOTING', 'STABBING', 'ROBBERY', 'BURGLARY', 'ASSAULT', 'DOMESTIC', 'ALARM', 'MOTOR VEHICLE THEFT', 'SEXUAL', '9-1-1']): return 'Emergency'
            if any(kw in incident for kw in ['THEFT', 'CRIMINAL', 'SUSPICIOUS', 'DRUG', 'WARRANT']): return 'Priority'
            return 'Routine'
        cad_df['CAD_ResponseType'] = cad_df.apply(assign_response_type, axis=1)

        cad_df = self.apply_crime_category_lookup(cad_df)
        address_col = next((c for c in ['FullAddress2', 'Address'] if c in cad_df.columns), None)
        cad_df['Enhanced_Block'] = cad_df[address_col].apply(self.calculate_enhanced_block) if address_col else 'No Address Data'
        cad_df['DataSource'] = 'CAD'
        
        # Corrected list of shared columns to prevent double-prefixing
        shared_cols = {'CaseNumber', 'ALL_INCIDENTS', 'Crime_Category', 'Enhanced_Block', 'DataSource', 'CAD_ResponseType'}
        cad_df = cad_df.rename(columns={c: f'CAD_{c}' for c in cad_df.columns if c not in shared_cols})
        
        self.logger.info(f"CAD processing complete: {len(cad_df)} records.")
        return cad_df

    def process_rms_data(self, rms_file):
        self.logger.info(f"Processing RMS data: {rms_file.name}")
        rms_df = pd.read_excel(rms_file, engine='openpyxl')

        for col in rms_df.select_dtypes(include=['object']).columns:
            rms_df[col] = rms_df[col].apply(self.clean_text_comprehensive)
            
        vehicle_cols = [c for c in rms_df.columns if any(kw in c for kw in ['Registration', 'Make', 'Model', 'Reg State'])]
        for col in vehicle_cols:
            rms_df[col] = rms_df[col].str.upper()
        self.logger.info("Applied uppercase to vehicle data.")

        case_col = next((c for c in ['Case Number', 'CaseNumber'] if c in rms_df.columns), None)
        rms_df['CaseNumber'] = rms_df[case_col].fillna('') if case_col else [f"RMS_{i}" for i in range(len(rms_df))]
        
        incident_cols = sorted([c for c in rms_df.columns if 'Incident Type_' in c])
        rms_df['ALL_INCIDENTS'] = rms_df[incident_cols].apply(lambda row: ', '.join(row.dropna().astype(str)), axis=1)
        
        def combine_vehicle(row, num):
            parts = [row.get(f'Make{num}', ''), row.get(f'Model{num}', ''), row.get(f'Registration {num}', ''), row.get(f'Reg State {num}', '')]
            return ' '.join(p for p in parts if p).strip()

        rms_df['Vehicle_1'] = rms_df.apply(combine_vehicle, num=1, axis=1)
        rms_df['Vehicle_2'] = rms_df.apply(combine_vehicle, num=2, axis=1)
        rms_df['Vehicle_and_Vehicle_2'] = rms_df.apply(lambda row: ' | '.join(v for v in [row['Vehicle_1'], row['Vehicle_2']] if v), axis=1)
        self.logger.info("Created derived vehicle columns.")
        
        rms_df = self.apply_crime_category_lookup(rms_df)
        address_col = next((c for c in ['FullAddress', 'Address'] if c in rms_df.columns), None)
        rms_df['Enhanced_Block'] = rms_df[address_col].apply(self.calculate_enhanced_block) if address_col else 'No Address Data'
        rms_df['DataSource'] = 'RMS'
        
        shared_cols = {'CaseNumber', 'ALL_INCIDENTS', 'Crime_Category', 'Enhanced_Block', 'DataSource', 'Vehicle_1', 'Vehicle_2', 'Vehicle_and_Vehicle_2'}
        rms_df = rms_df.rename(columns={c: f'RMS_{c}' for c in rms_df.columns if c not in shared_cols})

        self.logger.info(f"RMS processing complete: {len(rms_df)} records.")
        return rms_df

    def find_latest_files(self):
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
        self.logger.info("Starting Comprehensive SCRPA Fix V7.2 pipeline...")
        latest_files = self.find_latest_files()
        
        processed_data = []
        if 'cad' in latest_files: processed_data.append(self.process_cad_data(latest_files['cad']))
        if 'rms' in latest_files: processed_data.append(self.process_rms_data(latest_files['rms']))
            
        if not processed_data:
            self.logger.error("No CAD or RMS files found to process. Exiting.")
            raise ValueError("No data files found.")
            
        final_df = pd.concat(processed_data, ignore_index=True, sort=False)
        
        null_mask = final_df['CaseNumber'].isnull() | (final_df['CaseNumber'] == '')
        if null_mask.any():
            final_df.loc[null_mask, 'CaseNumber'] = [f"GEN_{i:06d}" for i in range(null_mask.sum())]
        
        priority_cols = ['CaseNumber', 'ALL_INCIDENTS', 'Crime_Category', 'Enhanced_Block', 'DataSource', 'Vehicle_1', 'Vehicle_2', 'Vehicle_and_Vehicle_2']
        ordered_cols = [c for c in priority_cols if c in final_df.columns]
        other_cols = sorted([c for c in final_df.columns if c not in ordered_cols])
        final_df = final_df[ordered_cols + other_cols]
        
        output_file = self.project_path / '04_powerbi' / 'enhanced_scrpa_data_v7_2_final.csv'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(output_file, index=False, encoding='utf-8')
        
        self.logger.info("=" * 60)
        self.logger.info("COMPREHENSIVE SCRPA FIX V7.2 COMPLETE")
        self.logger.info(f"✅ Total records processed: {len(final_df)}")
        self.logger.info(f"✅ Null/Empty CaseNumbers: {(final_df['CaseNumber'].isnull() | (final_df['CaseNumber'] == '')).sum()}")
        self.logger.info(f"✅ Output file: {output_file}")
        self.logger.info("=" * 60)
        
        return final_df, str(output_file)

if __name__ == "__main__":
    try:
        processor = ComprehensiveSCRPAFixV7_2()
        final_df, output_path = processor.process_final_pipeline()
        print(f"✅ Processing complete. {len(final_df)} records saved to {output_path}")
        print(f"📊 Null or empty case numbers in final output: {(final_df['CaseNumber'].isnull() | (final_df['CaseNumber'] == '')).sum()}")
    except Exception as e:
        print(f"❌ An error occurred during processing: {e}")
        logging.getLogger('ComprehensiveSCRPAFixV7_2').error(f"Fatal error in main execution: {e}", exc_info=True)