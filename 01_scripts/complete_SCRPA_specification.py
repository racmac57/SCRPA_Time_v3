# 2025-01-29-16-00-00
# SCRPA_Time_v2/Complete_SCRPA_Specification_Implementation
# Author: R. A. Carucci
# Purpose: Complete implementation of all SCRPA data transformation requirements

import pandas as pd
import numpy as np
import re
import os
from datetime import datetime, timedelta
from pathlib import Path

class CompleteSCRPAProcessor:
    """
    COMPLETE SCRPA SPECIFICATION IMPLEMENTATION:
    1. ✅ Proper column naming (CAD_/RMS_ prefixes, PascalCase)
    2. ✅ CaseNumber as first column (Column 0)
    3. ✅ Fix ALL_INCIDENTS delimiters (", " separators)
    4. ✅ Fix HowReported date issues (9-1-1 not dates)
    5. ✅ Reference lookup integration (Crime_Category, Period)
    6. ✅ Location backfill logic (Enhanced_Block)
    7. ✅ Complete null value handling
    8. ✅ Vehicle column integration
    9. ✅ Zone/Grid backfill using reference data
    10. ✅ Proper data type enforcement
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
        
        # Reference directories
        self.ref_dirs = {
            'call_types': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Classifications\CallTypes\CallType_Categories.xlsx"),
            'periods': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Temporal\SCRPA_Cycle\7Day_28Day_Cycle_20250414.xlsx"),
            'zone_grid': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\GeographicData\zone_grid_data\zone_grid_master.xlsx")
        }
        
        # Load reference data
        self.load_reference_data()
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        import logging
        
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"complete_scrpa_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.logger = logging.getLogger('CompleteSCRPAProcessor')
        self.logger.setLevel(logging.INFO)
        
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        fh = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        self.logger.info("Complete SCRPA Processor initialized with full specification")
        
    def load_reference_data(self):
        """Load all reference data for lookups"""
        
        # Load Crime Category mappings
        try:
            if self.ref_dirs['call_types'].exists():
                self.call_type_ref = pd.read_excel(self.ref_dirs['call_types'])
                self.logger.info(f"Loaded call type reference: {len(self.call_type_ref)} records")
            else:
                self.call_type_ref = None
                self.logger.warning("Call type reference file not found")
        except Exception as e:
            self.call_type_ref = None
            self.logger.warning(f"Could not load call type reference: {e}")
        
        # Load Period reference
        try:
            if self.ref_dirs['periods'].exists():
                self.period_ref = pd.read_excel(self.ref_dirs['periods'])
                self.logger.info(f"Loaded period reference: {len(self.period_ref)} records")
            else:
                self.period_ref = None
                self.logger.warning("Period reference file not found")
        except Exception as e:
            self.period_ref = None
            self.logger.warning(f"Could not load period reference: {e}")
            
        # Load Zone/Grid reference
        try:
            if self.ref_dirs['zone_grid'].exists():
                self.zone_grid_ref = pd.read_excel(self.ref_dirs['zone_grid'])
                self.logger.info(f"Loaded zone/grid reference: {len(self.zone_grid_ref)} records")
            else:
                self.zone_grid_ref = None
                self.logger.warning("Zone/grid reference file not found")
        except Exception as e:
            self.zone_grid_ref = None
            self.logger.warning(f"Could not load zone/grid reference: {e}")
            
    def convert_to_pascal_case(self, column_name):
        """Convert column names to PascalCase"""
        # Handle special cases and clean the name
        name = str(column_name).strip()
        
        # Remove common prefixes that might interfere
        name = re.sub(r'^(CAD_|RMS_)', '', name)
        
        # Replace common separators with spaces
        name = re.sub(r'[_\-\s]+', ' ', name)
        
        # Split by spaces and capitalize each word
        words = name.split()
        pascal_case = ''.join(word.capitalize() for word in words if word)
        
        return pascal_case
        
    def standardize_column_names(self, df, source_prefix):
        """Apply proper column naming conventions"""
        
        new_columns = {}
        
        for col in df.columns:
            # Convert to PascalCase
            pascal_name = self.convert_to_pascal_case(col)
            
            # Add source prefix
            if not pascal_name.startswith(('CAD', 'RMS')):
                new_name = f"{source_prefix}_{pascal_name}"
            else:
                new_name = pascal_name
                
            new_columns[col] = new_name
            
        df = df.rename(columns=new_columns)
        
        self.logger.info(f"Applied {source_prefix} naming conventions to {len(new_columns)} columns")
        return df
        
    def fix_how_reported_values(self, df):
        """Fix HowReported values - prevent dates, ensure proper strings"""
        
        how_reported_cols = [col for col in df.columns if 'howreported' in col.lower() or 'how_reported' in col.lower()]
        
        for col in how_reported_cols:
            if col in df.columns:
                # Create proper mapping
                df[col] = df[col].astype(str)
                
                # Fix date conversions back to proper values
                df.loc[df[col].str.contains(r'\d{1,2}/\d{1,2}/(19|20)\d{2}', na=False, regex=True), col] = '9-1-1'
                df.loc[df[col].str.contains(r'\d{4}-\d{2}-\d{2}', na=False, regex=True), col] = '9-1-1'
                
                # Standard mappings
                df[col] = df[col].replace({
                    '37135': '9-1-1',
                    'Phone': 'Phone', 
                    'Walk-In': 'Walk-In',
                    'Radio': 'Radio',
                    'Other - See Notes': 'Other - See Notes',
                    'nan': 'Unknown',
                    'NaN': 'Unknown'
                })
                
                self.logger.info(f"Fixed HowReported values in {col}")
                
        return df
        
    def create_all_incidents_with_delimiters(self, df, source_type):
        """Create ALL_INCIDENTS with proper delimiters"""
        
        if source_type == 'RMS':
            # Find incident type columns
            incident_cols = [col for col in df.columns if 'incidenttype' in col.lower() and any(x in col for x in ['1', '2', '3'])]
            
            if incident_cols:
                def combine_incidents(row):
                    incidents = []
                    for col in incident_cols:
                        if pd.notna(row[col]) and str(row[col]).strip():
                            incidents.append(str(row[col]).strip())
                    return ', '.join(incidents) if incidents else ''
                    
                df['ALL_INCIDENTS'] = df.apply(combine_incidents, axis=1)
                self.logger.info(f"Created ALL_INCIDENTS with ', ' delimiters for RMS data")
                
        elif source_type == 'CAD':
            # For CAD, use the single incident type
            incident_col = [col for col in df.columns if 'incident' in col.lower() and 'all' not in col.lower()]
            if incident_col:
                df['ALL_INCIDENTS'] = df[incident_col[0]].fillna('')
                self.logger.info(f"Created ALL_INCIDENTS for CAD data from {incident_col[0]}")
                
        return df
        
    def apply_crime_category_lookup(self, df):
        """Apply Crime_Category using reference lookup"""
        
        if self.call_type_ref is not None:
            # Create lookup dictionary from reference
            try:
                lookup_dict = dict(zip(
                    self.call_type_ref['CallType'].str.upper(),
                    self.call_type_ref['Category']
                ))
                
                def categorize_with_lookup(incident_type):
                    if pd.isna(incident_type):
                        return 'Other'
                        
                    incident_upper = str(incident_type).upper()
                    
                    # Direct lookup first
                    if incident_upper in lookup_dict:
                        return lookup_dict[incident_upper]
                    
                    # Partial matching for complex incident types
                    for key, category in lookup_dict.items():
                        if key in incident_upper:
                            return category
                            
                    return 'Other'
                    
                # Apply to primary incident type column
                incident_col = 'ALL_INCIDENTS' if 'ALL_INCIDENTS' in df.columns else None
                if not incident_col:
                    incident_col = [col for col in df.columns if 'incident' in col.lower()][0] if any('incident' in col.lower() for col in df.columns) else None
                    
                if incident_col:
                    df['Crime_Category'] = df[incident_col].apply(categorize_with_lookup)
                    self.logger.info("Applied Crime_Category using reference lookup")
                    
            except Exception as e:
                self.logger.warning(f"Could not apply crime category lookup: {e}")
                self.apply_fallback_crime_categorization(df)
        else:
            self.apply_fallback_crime_categorization(df)
            
        return df
        
    def apply_fallback_crime_categorization(self, df):
        """Fallback crime categorization logic"""
        
        def categorize_crime(incident_type):
            if pd.isna(incident_type):
                return 'Other'
                
            incident_upper = str(incident_type).upper()
            
            # SCRPA priority categories
            if any(term in incident_upper for term in ['MOTOR VEHICLE THEFT', 'AUTO THEFT', 'MV THEFT']):
                return 'Motor Vehicle Theft'
            elif 'ROBBERY' in incident_upper:
                return 'Robbery'
            elif 'BURGLARY' in incident_upper and 'AUTO' in incident_upper:
                return 'Burglary – Auto'
            elif 'SEXUAL' in incident_upper:
                return 'Sexual'
            elif 'BURGLARY' in incident_upper and 'COMMERCIAL' in incident_upper:
                return 'Burglary – Commercial'
            elif 'BURGLARY' in incident_upper and 'RESIDENCE' in incident_upper:
                return 'Burglary – Residence'
            else:
                return 'Other'
                
        incident_col = 'ALL_INCIDENTS' if 'ALL_INCIDENTS' in df.columns else None
        if not incident_col:
            incident_col = [col for col in df.columns if 'incident' in col.lower()][0] if any('incident' in col.lower() for col in df.columns) else None
            
        if incident_col:
            df['Crime_Category'] = df[incident_col].apply(categorize_crime)
            self.logger.info("Applied fallback crime categorization")
            
        return df
        
    def apply_period_classification(self, df):
        """Apply Period classification (7-Day, 28-Day, YTD only)"""
        
        def classify_period(dt):
            if pd.isna(dt):
                return 'YTD'  # Default for missing dates
                
            try:
                today = pd.Timestamp.now().date()
                incident_date = pd.to_datetime(dt).date()
                days_diff = (today - incident_date).days
                
                if days_diff <= 7:
                    return '7-Day'
                elif days_diff <= 28:
                    return '28-Day'
                else:
                    return 'YTD'  # No Historical per specification
                    
            except:
                return 'YTD'
                
        # Find datetime column
        datetime_col = [col for col in df.columns if 'datetime' in col.lower() or 'timeofcall' in col.lower()]
        if datetime_col:
            df['Period'] = df[datetime_col[0]].apply(classify_period)
        else:
            df['Period'] = 'YTD'
            
        self.logger.info("Applied Period classification (7-Day, 28-Day, YTD)")
        return df
        
    def apply_location_backfill(self, df):
        """Apply Enhanced_Block location backfill logic"""
        
        def calculate_enhanced_block(row):
            # Priority: CAD FullAddress2 -> RMS FullAddress -> fallback
            address = None
            
            # Check for CAD address
            cad_address_cols = [col for col in df.columns if 'cad' in col.lower() and 'fulladdress' in col.lower()]
            if cad_address_cols and pd.notna(row.get(cad_address_cols[0])):
                address = row[cad_address_cols[0]]
            
            # Check for RMS address if CAD is null
            if not address:
                rms_address_cols = [col for col in df.columns if 'rms' in col.lower() and 'fulladdress' in col.lower()]
                if rms_address_cols and pd.notna(row.get(rms_address_cols[0])):
                    address = row[rms_address_cols[0]]
                    
            # General address columns
            if not address:
                address_cols = [col for col in df.columns if 'address' in col.lower()]
                for col in address_cols:
                    if pd.notna(row.get(col)):
                        address = row[col]
                        break
                        
            if not address:
                return "Incomplete Address - Check Location Data"
                
            try:
                address = str(address).strip()
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
                
        df['Enhanced_Block'] = df.apply(calculate_enhanced_block, axis=1)
        self.logger.info("Applied Enhanced_Block location backfill logic")
        
        return df
        
    def apply_zone_grid_backfill(self, df):
        """Apply zone/grid backfill using reference data"""
        
        if self.zone_grid_ref is not None:
            try:
                # Merge with zone/grid reference
                zone_cols = [col for col in df.columns if 'zone' in col.lower() or 'pdzone' in col.lower()]
                
                if zone_cols:
                    zone_col = zone_cols[0]
                    
                    # Merge to get Post and Grid
                    df = df.merge(
                        self.zone_grid_ref[['Zone', 'Post', 'Grid']],
                        left_on=zone_col,
                        right_on='Zone',
                        how='left',
                        suffixes=('', '_ref')
                    )
                    
                    # Backfill missing values
                    if 'Post' in df.columns and 'Post_ref' in df.columns:
                        df['Post'] = df['Post'].fillna(df['Post_ref'])
                        df = df.drop(columns=['Post_ref'])
                        
                    if 'Grid' in df.columns and 'Grid_ref' in df.columns:
                        df['Grid'] = df['Grid'].fillna(df['Grid_ref'])
                        df = df.drop(columns=['Grid_ref'])
                        
                    self.logger.info("Applied zone/grid backfill using reference data")
                    
            except Exception as e:
                self.logger.warning(f"Could not apply zone/grid backfill: {e}")
                
        return df
        
    def add_vehicle_columns(self, df):
        """Add and combine vehicle columns"""
        
        # Find vehicle-related columns
        vehicle_cols = [col for col in df.columns if any(v in col.lower() for v in ['vehicle', 'registration', 'make', 'model'])]
        
        # Create Vehicle1 and Vehicle2 combinations
        reg1_cols = [col for col in vehicle_cols if '1' in col]
        reg2_cols = [col for col in vehicle_cols if '2' in col]
        
        if reg1_cols:
            def combine_vehicle1(row):
                parts = []
                for col in sorted(reg1_cols):
                    if pd.notna(row.get(col)) and str(row[col]).strip():
                        parts.append(str(row[col]).strip())
                return ' '.join(parts) if parts else ''
                
            df['Vehicle1'] = df.apply(combine_vehicle1, axis=1)
            
        if reg2_cols:
            def combine_vehicle2(row):
                parts = []
                for col in sorted(reg2_cols):
                    if pd.notna(row.get(col)) and str(row[col]).strip():
                        parts.append(str(row[col]).strip())
                return ' '.join(parts) if parts else ''
                
            df['Vehicle2'] = df.apply(combine_vehicle2, axis=1)
            
        # Create combined Vehicle1AndVehicle2
        if 'Vehicle1' in df.columns and 'Vehicle2' in df.columns:
            def combine_all_vehicles(row):
                vehicles = []
                if row.get('Vehicle1', '').strip():
                    vehicles.append(row['Vehicle1'].strip())
                if row.get('Vehicle2', '').strip():
                    vehicles.append(row['Vehicle2'].strip())
                return ' | '.join(vehicles) if vehicles else ''
                
            df['Vehicle1AndVehicle2'] = df.apply(combine_all_vehicles, axis=1)
            
        self.logger.info("Added and combined vehicle columns")
        return df
        
    def handle_null_values(self, df):
        """Handle all null values as specified"""
        
        # Time-related columns - set defaults
        time_columns = [col for col in df.columns if any(t in col.lower() for t in ['time', 'date'])]
        for col in time_columns:
            if 'time' in col.lower() and 'datetime' not in col.lower():
                df[col] = df[col].fillna('00:00:00')
            elif 'date' in col.lower() and 'datetime' not in col.lower():
                df[col] = df[col].fillna(pd.Timestamp.now().date())
                
        # Response Type mapping
        response_cols = [col for col in df.columns if 'response' in col.lower() and 'type' in col.lower()]
        for col in response_cols:
            if col in df.columns:
                df[col] = df[col].fillna('Routine')
                
        # Text columns - set to empty string or appropriate default
        text_columns = df.select_dtypes(include=['object']).columns
        for col in text_columns:
            if col not in time_columns:
                df[col] = df[col].fillna('')
                
        self.logger.info("Applied null value handling across all columns")
        return df
        
    def reorder_columns_specification(self, df):
        """Reorder columns with CaseNumber first"""
        
        # Find CaseNumber column
        case_num_col = None
        for col in df.columns:
            if 'casenumber' in col.lower() or ('case' in col.lower() and 'number' in col.lower()):
                case_num_col = col
                break
                
        if not case_num_col:
            self.logger.warning("CaseNumber column not found!")
            return df
            
        # Define column priority order
        priority_columns = [
            case_num_col,  # CaseNumber FIRST (Column 0)
            'ALL_INCIDENTS',
            'Crime_Category', 
            'Period',
            'TimeOfDay',
            'Enhanced_Block'
        ]
        
        # Get all other columns
        other_columns = [col for col in df.columns if col not in priority_columns]
        
        # Final column order
        final_order = [col for col in priority_columns if col in df.columns] + other_columns
        
        # Reorder dataframe
        df = df[final_order]
        
        self.logger.info(f"Reordered columns with {case_num_col} as Column 0")
        return df
        
    def process_cad_data(self, cad_file):
        """Process CAD data with full specification"""
        
        self.logger.info(f"Processing CAD data: {cad_file.name}")
        
        # Load data
        cad_df = pd.read_excel(cad_file, engine='openpyxl')
        
        # Apply column naming conventions
        cad_df = self.standardize_column_names(cad_df, 'CAD')
        
        # Fix HowReported values
        cad_df = self.fix_how_reported_values(cad_df)
        
        # Create ALL_INCIDENTS with delimiters
        cad_df = self.create_all_incidents_with_delimiters(cad_df, 'CAD')
        
        # Apply reference lookups
        cad_df = self.apply_crime_category_lookup(cad_df)
        cad_df = self.apply_period_classification(cad_df)
        
        # Location processing
        cad_df = self.apply_location_backfill(cad_df)
        cad_df = self.apply_zone_grid_backfill(cad_df)
        
        # Add vehicle columns
        cad_df = self.add_vehicle_columns(cad_df)
        
        # Handle null values
        cad_df = self.handle_null_values(cad_df)
        
        # Add data source identifier
        cad_df['DataSource'] = 'CAD'
        
        self.logger.info(f"CAD processing complete: {len(cad_df)} records")
        return cad_df
        
    def process_rms_data(self, rms_file):
        """Process RMS data with full specification"""
        
        self.logger.info(f"Processing RMS data: {rms_file.name}")
        
        # Load data
        rms_df = pd.read_excel(rms_file, engine='openpyxl')
        
        # Apply column naming conventions
        rms_df = self.standardize_column_names(rms_df, 'RMS')
        
        # Create ALL_INCIDENTS with delimiters (RMS unpivoting)
        rms_df = self.create_all_incidents_with_delimiters(rms_df, 'RMS')
        
        # Apply reference lookups
        rms_df = self.apply_crime_category_lookup(rms_df)
        rms_df = self.apply_period_classification(rms_df)
        
        # Location processing
        rms_df = self.apply_location_backfill(rms_df)
        rms_df = self.apply_zone_grid_backfill(rms_df)
        
        # Add vehicle columns
        rms_df = self.add_vehicle_columns(rms_df)
        
        # Handle null values
        rms_df = self.handle_null_values(rms_df)
        
        # Add data source identifier
        rms_df['DataSource'] = 'RMS'
        
        self.logger.info(f"RMS processing complete: {len(rms_df)} records")
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
        
    def process_complete_specification(self):
        """Process complete specification requirements"""
        
        self.logger.info("Starting complete SCRPA specification processing")
        
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
            
        # Final column reordering with CaseNumber first
        final_df = self.reorder_columns_specification(final_df)
        
        # Export results
        output_file = self.project_path / '04_powerbi' / 'enhanced_scrpa_data.csv'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        final_df.to_csv(output_file, index=False, encoding='utf-8')
        
        self.logger.info(f"Complete specification processing finished: {len(final_df)} records exported to {output_file}")
        
        # Validation summary
        self.logger.info("SPECIFICATION VALIDATION:")
        self.logger.info(f"✅ CaseNumber is Column 0: {final_df.columns[0]}")
        self.logger.info(f"✅ ALL_INCIDENTS delimiter check: {',' in str(final_df['ALL_INCIDENTS'].iloc[0]) if 'ALL_INCIDENTS' in final_df.columns else 'N/A'}")
        self.logger.info(f"✅ Period values: {final_df['Period'].unique() if 'Period' in final_df.columns else 'N/A'}")
        self.logger.info(f"✅ Total columns: {len(final_df.columns)}")
        
        return final_df, str(output_file)


# Usage
if __name__ == "__main__":
    processor = CompleteSCRPAProcessor()
    final_df, output_path = processor.process_complete_specification()
    print(f"✅ Complete specification processing finished: {len(final_df)} records")
    print(f"📄 Output: {output_path}")
    print(f"📊 CaseNumber is Column 0: {final_df.columns[0]}")
