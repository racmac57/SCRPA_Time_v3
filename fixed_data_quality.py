#!/usr/bin/env python3
"""
SCRPA Data Quality Fix and Integration Script
Addresses all critical data quality issues and integrates reference data.
"""

import pandas as pd
import numpy as np
import re
import os
import glob
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SCRPADataProcessor:
    def __init__(self, base_path):
        self.base_path = base_path
        self.exports_path = os.path.join(base_path, "05_Exports")
        self.reference_path = os.path.join(base_path, "10_Refrence_Files")
        
        # Load reference data
        self.calltype_categories = self._load_calltype_categories()
        self.zone_grid_lookup = self._load_zone_grid_lookup()
        
    def _load_calltype_categories(self):
        """Load CallType Categories reference data"""
        try:
            df = pd.read_excel(os.path.join(self.reference_path, "CallType_Categories.xlsx"))
            logger.info(f"Loaded {len(df)} CallType categories")
            return df
        except Exception as e:
            logger.error(f"Failed to load CallType categories: {e}")
            return pd.DataFrame()
    
    def _load_zone_grid_lookup(self):
        """Load and create zone/grid lookup data"""
        try:
            zone_grid_path = os.path.join(self.reference_path, "zone_grid_data")
            lookup_files = glob.glob(os.path.join(zone_grid_path, "*.xlsx"))
            lookup_files = [f for f in lookup_files if "master" not in os.path.basename(f).lower()]
            
            if lookup_files:
                dfs = [pd.read_excel(f) for f in lookup_files]
                combined = pd.concat(dfs, ignore_index=True)
                combined = combined.drop_duplicates(subset=["CrossStreetName", "Grid", "PDZone"])
                logger.info(f"Loaded {len(combined)} zone/grid lookup records")
                return combined
            else:
                logger.warning("No zone/grid lookup files found")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Failed to load zone/grid lookup: {e}")
            return pd.DataFrame()
    
    def _convert_to_snake_case(self, columns):
        """Convert column names to snake_case"""
        snake_case_cols = []
        for col in columns:
            # Convert to snake_case
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', col)
            s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
            # Clean up specific patterns
            s2 = s2.replace(' ', '_').replace('-', '_').replace('__', '_').strip('_')
            snake_case_cols.append(s2)
        return snake_case_cols
    
    def _fix_incident_time_format(self, time_series):
        """Convert incident time to HH:MM format"""
        def format_time(time_val):
            if pd.isna(time_val):
                return None
            
            # Handle timedelta objects
            if isinstance(time_val, pd.Timedelta):
                total_seconds = int(time_val.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                return f"{hours:02d}:{minutes:02d}"
            
            # Handle datetime objects
            if isinstance(time_val, datetime):
                return time_val.strftime("%H:%M")
            
            # Handle string representations
            if isinstance(time_val, str):
                # Extract time from various formats
                time_match = re.search(r'(\d{1,2}):(\d{2})', time_val)
                if time_match:
                    return f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
            
            return str(time_val)
        
        return time_series.apply(format_time)
    
    def _fix_encoding_artifacts(self, text_series):
        """Fix encoding artifacts like â€" to proper dashes"""
        if text_series.dtype != 'object':
            return text_series
            
        return text_series.str.replace('â€"', '-', regex=False)\
                          .str.replace('â€™', "'", regex=False)\
                          .str.replace('â€œ', '"', regex=False)\
                          .str.replace('â€\x9d', '"', regex=False)
    
    def _clean_address_data(self, address_series):
        """Clean contaminated addresses - remove duplicate city/state"""
        def clean_address(addr):
            if pd.isna(addr):
                return addr
                
            addr = str(addr).strip()
            
            # Remove duplicate "Hackensack, NJ" patterns
            # Pattern: address, Hackensack, NJ, Hackensack, NJ, 07601
            addr = re.sub(r',\s*Hackensack,\s*NJ,\s*Hackensack,\s*NJ', ', Hackensack, NJ', addr, flags=re.IGNORECASE)
            
            # Ensure proper format: Street, City, State, ZIP
            parts = [part.strip() for part in addr.split(',')]
            
            # If we have more than 4 parts, likely duplicate city/state
            if len(parts) > 4:
                # Keep first part (street), last occurrence of city, state, zip
                street = parts[0]
                # Find last occurrence of Hackensack and NJ
                hackensack_indices = [i for i, part in enumerate(parts) if 'hackensack' in part.lower()]
                nj_indices = [i for i, part in enumerate(parts) if part.strip().upper() == 'NJ']
                
                if hackensack_indices and nj_indices:
                    city_idx = hackensack_indices[-1]
                    state_idx = nj_indices[-1]
                    
                    # Reconstruct clean address
                    if len(parts) > state_idx + 1:  # ZIP exists
                        addr = f"{street}, {parts[city_idx]}, {parts[state_idx]}, {parts[-1]}"
                    else:
                        addr = f"{street}, {parts[city_idx]}, {parts[state_idx]}"
            
            return addr
        
        return address_series.apply(clean_address)
    
    def _standardize_vehicle_format(self, vehicle_series):
        """Convert vehicle data to ALL CAPS format"""
        if vehicle_series.dtype != 'object':
            return vehicle_series
            
        return vehicle_series.str.upper()
    
    def _backfill_grid_post(self, df, address_col='full_address'):
        """Backfill Grid/Post using zone_grid_data"""
        if self.zone_grid_lookup.empty:
            logger.warning("No zone/grid lookup data available for backfill")
            return df
        
        # Create clean address for matching
        df['clean_address'] = df[address_col].str.replace(' & ', ' / ')\
                                             .str.replace(r'\b(Street|Avenue|Road|Place|Drive|Court|Boulevard)\b', 
                                                         lambda m: {'Street': 'St', 'Avenue': 'Ave', 'Road': 'Rd', 
                                                                   'Place': 'Pl', 'Drive': 'Dr', 'Court': 'Ct', 
                                                                   'Boulevard': 'Blvd'}[m.group()], regex=True)\
                                             .str.title().str.strip()
        
        # Merge with lookup data
        original_count = len(df)
        merged = df.merge(self.zone_grid_lookup[['CrossStreetName', 'Grid', 'PDZone']], 
                         left_on='clean_address', right_on='CrossStreetName', 
                         how='left', suffixes=('', '_lookup'))
        
        # Fill missing Grid/Zone data
        if 'grid' in df.columns:
            df['grid'] = df['grid'].fillna(merged['Grid'])
        if 'zone' in df.columns:
            df['zone'] = df['zone'].fillna(merged['PDZone'])
        if 'pd_zone' in df.columns:
            df['pd_zone'] = df['pd_zone'].fillna(merged['PDZone'])
            
        # Clean up
        df.drop('clean_address', axis=1, inplace=True, errors='ignore')
        
        logger.info(f"Grid/Zone backfill completed for {original_count} records")
        return df
    
    def _add_response_type_lookup(self, df, incident_col='incident'):
        """Add Response_Type using CallType_Categories lookup"""
        if self.calltype_categories.empty:
            logger.warning("No CallType categories available for lookup")
            return df
        
        # Merge with CallType categories
        merged = df.merge(self.calltype_categories[['Incident', 'Response Type']], 
                         left_on=incident_col, right_on='Incident', 
                         how='left', suffixes=('', '_lookup'))
        
        df['response_type'] = merged['Response Type']
        
        logger.info(f"Response Type lookup completed")
        return df
    
    def process_rms_data(self, filepath=None):
        """Process RMS data with all quality fixes"""
        if filepath is None:
            # Find most recent RMS file
            rms_files = glob.glob(os.path.join(self.exports_path, "*SCRPA_RMS.xlsx"))
            if not rms_files:
                raise FileNotFoundError("No RMS files found in exports directory")
            filepath = max(rms_files, key=os.path.getctime)
        
        logger.info(f"Processing RMS file: {filepath}")
        df = pd.read_excel(filepath)
        
        logger.info(f"Original RMS data: {df.shape}")
        
        # 1. Convert headers to snake_case
        df.columns = self._convert_to_snake_case(df.columns)
        
        # 2. Fix incident_time format
        if 'incident_time' in df.columns:
            df['incident_time'] = self._fix_incident_time_format(df['incident_time'])
        
        # 3. Fix time_of_day encoding artifacts
        if 'time_of_day' in df.columns:
            df['time_of_day'] = self._fix_encoding_artifacts(df['time_of_day'])
        
        # 4. Clean location data
        if 'fulladdress' in df.columns:
            df['fulladdress'] = self._clean_address_data(df['fulladdress'])
        elif 'full_address' in df.columns:
            df['full_address'] = self._clean_address_data(df['full_address'])
        
        # 5. Fix Crime_Category encoding
        crime_cols = [col for col in df.columns if 'crime' in col.lower() or 'category' in col.lower()]
        for col in crime_cols:
            df[col] = self._fix_encoding_artifacts(df[col])
        
        # 6. Convert vehicle columns to ALL CAPS
        vehicle_cols = [col for col in df.columns if 'vehicle' in col.lower() or 'registration' in col.lower()]
        for col in vehicle_cols:
            df[col] = self._standardize_vehicle_format(df[col])
        
        # 7. Convert Squad to ALL CAPS
        if 'squad' in df.columns:
            df['squad'] = df['squad'].str.upper()
        
        # 8. Grid/Post backfill
        address_col = 'fulladdress' if 'fulladdress' in df.columns else 'full_address'
        df = self._backfill_grid_post(df, address_col)
        
        logger.info(f"Processed RMS data: {df.shape}")
        return df
    
    def process_cad_data(self, filepath=None):
        """Process CAD data with all quality fixes"""
        if filepath is None:
            # Find most recent CAD file
            cad_files = glob.glob(os.path.join(self.exports_path, "*SCRPA_CAD.xlsx"))
            if not cad_files:
                raise FileNotFoundError("No CAD files found in exports directory")
            filepath = max(cad_files, key=os.path.getctime)
        
        logger.info(f"Processing CAD file: {filepath}")
        df = pd.read_excel(filepath)
        
        logger.info(f"Original CAD data: {df.shape}")
        
        # 1. Convert headers to snake_case
        df.columns = self._convert_to_snake_case(df.columns)
        
        # 2. Add Response_Type lookup
        incident_col = None
        for col in df.columns:
            if 'incident' in col.lower() or 'response' in col.lower() or 'call' in col.lower():
                incident_col = col
                break
        
        if incident_col:
            df = self._add_response_type_lookup(df, incident_col)
        
        # 3. Grid/Post backfill if address column exists
        address_cols = [col for col in df.columns if 'address' in col.lower()]
        if address_cols:
            df = self._backfill_grid_post(df, address_cols[0])
        
        logger.info(f"Processed CAD data: {df.shape}")
        return df
    
    def add_nj_geocoding(self, df, address_col):
        """Add NJ geocoding functionality"""
        # This is a placeholder for NJ geocoding integration
        # The actual geocoding would require access to NJ geocoding service
        logger.info("NJ Geocoding placeholder - would integrate with NJ geocoding service")
        
        # Add placeholder columns for X/Y coordinates
        df['geocoded_x'] = np.nan
        df['geocoded_y'] = np.nan
        df['geocode_status'] = 'PENDING'
        
        # In a real implementation, this would:
        # 1. Parse addresses
        # 2. Call NJ geocoding service
        # 3. Return X/Y coordinates
        # 4. Set geocode_status to SUCCESS/FAILED
        
        return df
    
    def export_enhanced_datasets(self, rms_df, cad_df, output_dir=None):
        """Export enhanced datasets"""
        if output_dir is None:
            output_dir = os.path.join(self.base_path, "03_output")
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export individual datasets
        rms_output = os.path.join(output_dir, f"enhanced_rms_data_{timestamp}.csv")
        cad_output = os.path.join(output_dir, f"enhanced_cad_data_{timestamp}.csv")
        combined_output = os.path.join(output_dir, f"enhanced_final_datasets_{timestamp}.csv")
        
        rms_df.to_csv(rms_output, index=False)
        cad_df.to_csv(cad_output, index=False)
        
        logger.info(f"Enhanced RMS data exported to: {rms_output}")
        logger.info(f"Enhanced CAD data exported to: {cad_output}")
        
        # Create combined dataset if both have common key
        if 'case_number' in rms_df.columns and 'reportnumbernew' in cad_df.columns:
            combined = rms_df.merge(cad_df, left_on='case_number', right_on='reportnumbernew', 
                                  how='outer', suffixes=('_rms', '_cad'))
            combined.to_csv(combined_output, index=False)
            logger.info(f"Combined dataset exported to: {combined_output}")
            return rms_output, cad_output, combined_output
        
        return rms_output, cad_output, None

def main():
    """Main processing function"""
    base_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
    
    try:
        # Initialize processor
        processor = SCRPADataProcessor(base_path)
        
        # Process RMS data
        logger.info("=== Processing RMS Data ===")
        rms_df = processor.process_rms_data()
        
        # Process CAD data
        logger.info("=== Processing CAD Data ===")
        cad_df = processor.process_cad_data()
        
        # Add geocoding (placeholder)
        logger.info("=== Adding Geocoding ===")
        address_col = 'fulladdress' if 'fulladdress' in rms_df.columns else 'full_address'
        if address_col in rms_df.columns:
            rms_df = processor.add_nj_geocoding(rms_df, address_col)
            
        if 'fulladdress2' in cad_df.columns:
            cad_df = processor.add_nj_geocoding(cad_df, 'fulladdress2')
        
        # Export enhanced datasets
        logger.info("=== Exporting Enhanced Datasets ===")
        outputs = processor.export_enhanced_datasets(rms_df, cad_df)
        
        logger.info("=== Processing Complete ===")
        logger.info(f"RMS records processed: {len(rms_df)}")
        logger.info(f"CAD records processed: {len(cad_df)}")
        logger.info(f"Output files: {outputs}")
        
        return outputs
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise

if __name__ == "__main__":
    main()