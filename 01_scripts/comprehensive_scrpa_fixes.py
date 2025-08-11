# 2025-01-29-15-15-00
# SCRPA_Time_v2/Comprehensive_SCRPA_Fixes
# Author: R. A. Carucci
# Purpose: Complete fixes for all identified data processing issues

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from pathlib import Path

class ComprehensiveSCRPAProcessor:
    """
    COMPREHENSIVE_SCRPA_FIXES - All Issues Resolved:
    1. ✅ Combine CAD + RMS data properly 
    2. ✅ Fix How_Reported date conversion (9-1-1 → 9-1-1, not date)
    3. ✅ Add CAD_ prefix to CAD-only columns
    4. ✅ Fix Response_Type nulls
    5. ✅ Clean CAD_Notes_Cleaned text (remove ????)
    6. ✅ Apply Trim/Clean to all text fields
    7. ✅ Fix datetime formatting to mm/dd/yyyy hh:mm:ss
    8. ✅ Fix blank Period and Crime_Category values
    9. ✅ Implement RMS unpivoting for ALL_INCIDENTS
    10. ✅ Make Case_Number column 0 (first column)
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
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging"""
        import logging
        
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"comprehensive_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.logger = logging.getLogger('ComprehensiveProcessor')
        self.logger.setLevel(logging.INFO)
        
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        fh = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        self.logger.info("Comprehensive SCRPA Processor initialized")
        
    def find_latest_files(self):
        """Find latest CAD and RMS files"""
        latest_files = {}
        
        # Find latest CAD file
        cad_files = list(self.export_dirs['cad_exports'].glob("*.xlsx"))
        if cad_files:
            latest_cad = max(cad_files, key=lambda x: x.stat().st_mtime)
            latest_files['cad'] = latest_cad
            self.logger.info(f"Latest CAD file: {latest_cad.name}")
        
        # Find latest RMS file  
        rms_files = list(self.export_dirs['rms_exports'].glob("*.xlsx"))
        if rms_files:
            latest_rms = max(rms_files, key=lambda x: x.stat().st_mtime)
            latest_files['rms'] = latest_rms
            self.logger.info(f"Latest RMS file: {latest_rms.name}")
            
        return latest_files
        
    def clean_text_comprehensive(self, text):
        """Comprehensive text cleaning with Trim, Clean, and line break fixes"""
        if pd.isna(text) or text is None:
            return None
            
        text = str(text)
        
        # Remove line breaks and replace with spaces
        text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # Remove erroneous question marks (????)
        text = re.sub(r'\s*\?\s*\?\s*\?\s*\?\s*', ' ', text)
        text = re.sub(r'\s*\?\s*\?\s*\?\s*', ' ', text)  
        text = re.sub(r'\s*\?\s*\?\s*', ' ', text)
        
        # Clean control characters (Text.Clean equivalent)
        text = ''.join(c for c in text if c.isprintable() or c.isspace())
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Replace special characters
        text = text.replace('â', "'").replace('â', '')
        
        # Trim leading/trailing whitespace
        text = text.strip()
        
        return text if text else None
        
    def fix_how_reported_values(self, df):
        """Fix How_Reported values - prevent 9-1-1 from becoming dates"""
        if 'How_Reported' in df.columns:
            # Create mapping to fix common issues
            how_reported_fixes = {
                '37135': '9-1-1',  # Code mapping
                'Phone': 'Phone',
                'Walk-In': 'Walk-In', 
                'Radio': 'Radio',
                'Other - See Notes': 'Other - See Notes'
            }
            
            # Apply fixes and convert any dates back to 9-1-1
            df['How_Reported'] = df['How_Reported'].astype(str)
            
            # Fix cases where 9-1-1 got converted to date
            date_pattern = r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}'
            mask = df['How_Reported'].str.contains(date_pattern, na=False, regex=True)
            df.loc[mask, 'How_Reported'] = '9-1-1'
            
            # Apply standard mappings
            df['How_Reported'] = df['How_Reported'].replace(how_reported_fixes)
            
            self.logger.info(f"Fixed How_Reported values: {df['How_Reported'].value_counts().to_dict()}")
            
        return df
        
    def fix_response_type_nulls(self, df):
        """Fix Response_Type nulls based on incident priority"""
        if 'Response_Type' in df.columns:
            # Create response type mapping based on incident types
            def assign_response_type(row):
                if pd.notna(row.get('Response_Type')):
                    return row['Response_Type']
                    
                incident = str(row.get('CAD_Incident', row.get('Incident', ''))).upper()
                
                # Emergency response types
                emergency_keywords = ['SHOOTING', 'STABBING', 'ROBBERY', 'ASSAULT', 'DOMESTIC', 'ALARM', 'EMERGENCY']
                if any(keyword in incident for keyword in emergency_keywords):
                    return 'Emergency'
                    
                # Priority response types  
                priority_keywords = ['THEFT', 'BURGLARY', 'CRIMINAL', 'SUSPICIOUS', 'DRUG']
                if any(keyword in incident for keyword in priority_keywords):
                    return 'Priority'
                    
                # Default to routine
                return 'Routine'
                
            df['Response_Type'] = df.apply(assign_response_type, axis=1)
            
            null_count = df['Response_Type'].isnull().sum()
            self.logger.info(f"Fixed Response_Type nulls: {null_count} remaining null values")
            
        return df
        
    def format_datetime_columns(self, df):
        """Format all datetime columns to mm/dd/yyyy hh:mm:ss"""
        datetime_columns = [
            'Incident_DateTime', 'CAD_Timestamp', 'Time_of_Call',
            'Incident_Date', 'Incident_Time'
        ]
        
        for col in datetime_columns:
            if col in df.columns:
                try:
                    # Convert to datetime first
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    
                    # Format based on column type
                    if 'Date' in col and 'Time' not in col:
                        # Date only columns
                        df[col] = df[col].dt.strftime('%m/%d/%Y')
                    elif 'Time' in col and 'Date' not in col:
                        # Time only columns  
                        df[col] = df[col].dt.strftime('%H:%M:%S')
                    else:
                        # Full datetime columns
                        df[col] = df[col].dt.strftime('%m/%d/%Y %H:%M:%S')
                        
                    self.logger.info(f"Formatted {col} to standard format")
                    
                except Exception as e:
                    self.logger.warning(f"Could not format {col}: {e}")
                    
        return df
        
    def process_cad_data(self, cad_file):
        """Process CAD data with proper column prefixing"""
        self.logger.info(f"Processing CAD data: {cad_file.name}")
        
        # Load CAD data
        cad_df = pd.read_excel(cad_file, engine='openpyxl')
        
        # Clean text fields
        text_columns = ['CADNotes', 'Narrative', 'FullAddress2', 'Officer']
        for col in text_columns:
            if col in cad_df.columns:
                cad_df[col] = cad_df[col].apply(self.clean_text_comprehensive)
                
        # Fix How_Reported
        cad_df = self.fix_how_reported_values(cad_df)
        
        # Add CAD_ prefix to CAD-specific columns
        cad_columns_to_prefix = ['Incident', 'Officer', 'Disposition', 'Grid', 'CADNotes']
        for col in cad_columns_to_prefix:
            if col in cad_df.columns:
                new_col_name = f'CAD_{col}' if not col.startswith('CAD') else col
                cad_df = cad_df.rename(columns={col: new_col_name})
                
        # Create standardized datetime
        if 'Time of Call' in cad_df.columns:
            cad_df['Incident_DateTime'] = pd.to_datetime(cad_df['Time of Call'], errors='coerce')
            
        # Extract date/time components
        cad_df['Incident_Date'] = cad_df['Incident_DateTime'].dt.date
        cad_df['Incident_Time'] = cad_df['Incident_DateTime'].dt.time
        
        # Create ALL_INCIDENTS (for CAD, same as incident type)
        incident_col = 'CAD_Incident' if 'CAD_Incident' in cad_df.columns else 'Incident'
        if incident_col in cad_df.columns:
            cad_df['ALL_INCIDENTS'] = cad_df[incident_col]
            cad_df['IncidentType'] = cad_df[incident_col]
        else:
            cad_df['ALL_INCIDENTS'] = ''
            cad_df['IncidentType'] = ''
            
        # Add data source identifier
        cad_df['Data_Source'] = 'CAD'
        
        # Fix Response_Type nulls
        cad_df = self.fix_response_type_nulls(cad_df)
        
        self.logger.info(f"CAD processing complete: {len(cad_df)} records")
        return cad_df
        
    def process_rms_data(self, rms_file):
        """Process RMS data with proper unpivoting"""
        self.logger.info(f"Processing RMS data: {rms_file.name}")
        
        # Load RMS data
        rms_df = pd.read_excel(rms_file, engine='openpyxl')
        
        # Clean text fields
        text_columns = ['Narrative', 'FullAddress']
        for col in text_columns:
            if col in rms_df.columns:
                rms_df[col] = rms_df[col].apply(self.clean_text_comprehensive)
                
        # Create datetime using cascading logic
        date_series = None
        time_series = None
        
        # Cascading date logic
        if 'Incident Date' in rms_df.columns:
            date_series = rms_df['Incident Date']
        elif 'Incident Date_Between' in rms_df.columns:
            date_series = rms_df['Incident Date_Between']
        elif 'Report Date' in rms_df.columns:
            date_series = rms_df['Report Date']
            
        # Cascading time logic
        if 'Incident Time' in rms_df.columns:
            time_series = rms_df['Incident Time']
        elif 'Incident Time_Between' in rms_df.columns:
            time_series = rms_df['Incident Time_Between']
        elif 'Report Time' in rms_df.columns:
            time_series = rms_df['Report Time']
            
        # Combine date and time
        if date_series is not None and time_series is not None:
            date_series = pd.to_datetime(date_series, errors='coerce').dt.strftime('%Y-%m-%d')
            time_series = pd.to_datetime(time_series, errors='coerce').dt.strftime('%H:%M:%S')
            combined_datetime = date_series + " " + time_series
            rms_df['Incident_DateTime'] = pd.to_datetime(combined_datetime, errors='coerce')
        else:
            rms_df['Incident_DateTime'] = pd.NaT
            
        # Extract date/time components
        rms_df['Incident_Date'] = rms_df['Incident_DateTime'].dt.date
        rms_df['Incident_Time'] = rms_df['Incident_DateTime'].dt.time
        
        # CRITICAL FIX: Unpivot incident types for ALL_INCIDENTS
        incident_type_cols = ['Incident Type_1', 'Incident Type_2', 'Incident Type_3']
        available_incident_cols = [col for col in incident_type_cols if col in rms_df.columns]
        
        if available_incident_cols:
            # Create ALL_INCIDENTS by concatenating all incident types
            def create_all_incidents(row):
                incidents = []
                for col in available_incident_cols:
                    if pd.notna(row[col]) and str(row[col]).strip():
                        incidents.append(str(row[col]).strip())
                return ' - '.join(incidents) if incidents else ''
                
            rms_df['ALL_INCIDENTS'] = rms_df.apply(create_all_incidents, axis=1)
            rms_df['IncidentType'] = rms_df[available_incident_cols[0]]  # Primary incident type
            
            # OPTIONAL: Create unpivoted version for detailed analysis
            id_cols = [col for col in rms_df.columns if col not in available_incident_cols]
            unpivoted_rms = pd.melt(
                rms_df, 
                id_vars=id_cols, 
                value_vars=available_incident_cols,
                var_name='Incident_Source_Column',
                value_name='Individual_IncidentType'
            )
            # Remove empty incident types
            unpivoted_rms = unpivoted_rms[
                unpivoted_rms['Individual_IncidentType'].notna() & 
                (unpivoted_rms['Individual_IncidentType'].astype(str).str.strip() != '')
            ]
            
            self.logger.info(f"RMS unpivoting: {len(rms_df)} → {len(unpivoted_rms)} records after unpivot")
            
            # Use unpivoted version for final processing
            rms_df = unpivoted_rms
        else:
            rms_df['ALL_INCIDENTS'] = ''
            rms_df['IncidentType'] = ''
            
        # Add data source identifier
        rms_df['Data_Source'] = 'RMS'
        
        self.logger.info(f"RMS processing complete: {len(rms_df)} records")
        return rms_df
        
    def add_derived_columns(self, df):
        """Add all derived columns with proper validation"""
        
        # TimeOfDay categorization
        def categorize_time_of_day(dt):
            if pd.isna(dt):
                return "Unknown"
            try:
                hour = dt.hour if hasattr(dt, 'hour') else pd.to_datetime(dt).hour
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
            except:
                return "Unknown"
                
        df['TimeOfDay'] = df['Incident_DateTime'].apply(categorize_time_of_day)
        
        # Period classification
        def classify_period(dt):
            if pd.isna(dt):
                return 'Historical'
            try:
                today = pd.Timestamp.now().date()
                incident_date = pd.to_datetime(dt).date()
                days_diff = (today - incident_date).days
                
                if days_diff <= 7:
                    return '7-Day'
                elif days_diff <= 28:
                    return '28-Day'
                elif pd.to_datetime(dt).year == today.year:
                    return 'YTD'
                else:
                    return 'Historical'
            except:
                return 'Historical'
                
        df['Period'] = df['Incident_DateTime'].apply(classify_period)
        
        # Enhanced_Block
        def calculate_enhanced_block(address):
            if pd.isna(address) or not address:
                return "Incomplete Address - Check Location Data"
            try:
                address = str(address).strip()
                clean_addr = address.replace(", Hackensack, NJ, 07601", "").replace(", Hackensack, NJ", "")
                
                if ' & ' in clean_addr:
                    return clean_addr.strip()
                    
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
                
        address_col = 'FullAddress2' if 'FullAddress2' in df.columns else 'FullAddress'
        if address_col in df.columns:
            df['Enhanced_Block'] = df[address_col].apply(calculate_enhanced_block)
        else:
            df['Enhanced_Block'] = 'Unknown Block'
            
        # Crime_Category
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
            
        df['Crime_Category'] = df.apply(
            lambda row: categorize_crime(
                row.get('IncidentType', ''), 
                row.get('ALL_INCIDENTS', '')
            ), axis=1
        )
        
        # Validate no blank values
        blank_period = df['Period'].isnull().sum()
        blank_crime = df['Crime_Category'].isnull().sum()
        
        if blank_period > 0:
            df['Period'] = df['Period'].fillna('Historical')
            self.logger.warning(f"Fixed {blank_period} blank Period values")
            
        if blank_crime > 0:
            df['Crime_Category'] = df['Crime_Category'].fillna('Other')
            self.logger.warning(f"Fixed {blank_crime} blank Crime_Category values")
            
        return df
        
    def combine_cad_rms_data(self, cad_df, rms_df):
        """Combine CAD and RMS data properly"""
        
        # Standardize column names for combination
        standardized_columns = [
            'Case_Number', 'Incident_DateTime', 'Incident_Date', 'Incident_Time',
            'ALL_INCIDENTS', 'IncidentType', 'Crime_Category', 'TimeOfDay', 'Period',
            'Enhanced_Block', 'Data_Source'
        ]
        
        # Keep CAD-specific columns with CAD_ prefix
        cad_specific = [col for col in cad_df.columns if col not in standardized_columns]
        
        # Keep RMS-specific columns  
        rms_specific = [col for col in rms_df.columns if col not in standardized_columns]
        
        # Combine dataframes
        combined_df = pd.concat([cad_df, rms_df], ignore_index=True, sort=False)
        
        self.logger.info(f"Combined data: CAD ({len(cad_df)}) + RMS ({len(rms_df)}) = {len(combined_df)} total records")
        
        return combined_df
        
    def reorder_columns(self, df):
        """Reorder columns with Case_Number first"""
        
        # Define column order with Case_Number first
        priority_columns = [
            'Case_Number',  # Column 0
            'Incident_DateTime',
            'ALL_INCIDENTS', 
            'IncidentType',
            'Crime_Category',
            'TimeOfDay',
            'Period',
            'Enhanced_Block',
            'Data_Source'
        ]
        
        # Get all other columns
        other_columns = [col for col in df.columns if col not in priority_columns]
        
        # Final column order
        final_column_order = priority_columns + other_columns
        
        # Reorder dataframe
        available_columns = [col for col in final_column_order if col in df.columns]
        df = df[available_columns]
        
        self.logger.info(f"Reordered columns with Case_Number first: {available_columns[:5]}...")
        
        return df
        
    def process_complete_pipeline(self):
        """Run complete processing pipeline with all fixes"""
        
        self.logger.info("Starting comprehensive SCRPA processing with all fixes")
        
        # Find latest files
        latest_files = self.find_latest_files()
        
        processed_dataframes = []
        
        # Process CAD data if available
        if 'cad' in latest_files:
            cad_df = self.process_cad_data(latest_files['cad'])
            cad_df = self.add_derived_columns(cad_df)
            cad_df = self.format_datetime_columns(cad_df)
            processed_dataframes.append(cad_df)
            
        # Process RMS data if available  
        if 'rms' in latest_files:
            rms_df = self.process_rms_data(latest_files['rms'])
            rms_df = self.add_derived_columns(rms_df)
            rms_df = self.format_datetime_columns(rms_df)
            processed_dataframes.append(rms_df)
            
        if not processed_dataframes:
            raise ValueError("No CAD or RMS files found to process")
            
        # Combine all dataframes
        if len(processed_dataframes) == 1:
            final_df = processed_dataframes[0]
        else:
            final_df = pd.concat(processed_dataframes, ignore_index=True, sort=False)
            
        # Apply final cleaning and formatting
        text_columns = [col for col in final_df.columns if final_df[col].dtype == 'object']
        for col in text_columns:
            if col not in ['Incident_DateTime', 'Incident_Date', 'Incident_Time']:
                final_df[col] = final_df[col].apply(self.clean_text_comprehensive)
                
        # Reorder columns with Case_Number first
        final_df = self.reorder_columns(final_df)
        
        # Export results
        output_file = self.project_path / '04_powerbi' / 'enhanced_scrpa_data.csv'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        final_df.to_csv(output_file, index=False, encoding='utf-8')
        
        self.logger.info(f"Processing complete: {len(final_df)} records exported to {output_file}")
        
        return final_df, str(output_file)


# Usage example
if __name__ == "__main__":
    processor = ComprehensiveSCRPAProcessor()
    final_df, output_path = processor.process_complete_pipeline()
    print(f"✅ Processing complete: {len(final_df)} records")
    print(f"📄 Output: {output_path}")
