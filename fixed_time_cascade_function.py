# URGENT FIX: Time Cascade Function Bug
# Date: 2025-07-30
# Issue: incident_time extraction fails due to column mapping bug
# Root Cause: cascade_time function expects mapped column names but they may not exist

import pandas as pd
import numpy as np
from datetime import datetime

class FixedTimeCascadeProcessor:
    """
    CRITICAL FIX for time cascade function in Comprehensive_SCRPA_Fix_v8.0_Standardized.py
    
    PROBLEM IDENTIFIED:
    - Raw data has: 'Incident Time', 'Incident Time_Between', 'Report Time'
    - Column mapping creates: 'Incident_Time_Raw', 'Incident_Time_Between_Raw', 'Report_Time_Raw'
    - cascade_time function looks for mapped names correctly
    - BUT: Function may be called before mapping is applied OR mapping is not working
    
    SOLUTION: Make cascade function robust to handle both raw and mapped column names
    """
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        import logging
        self.logger = logging.getLogger('FixedTimeCascade')
        
    def get_rms_column_mapping(self) -> dict:
        """Get the standardized RMS column mapping to match M Code."""
        return {
            "Case Number": "Case_Number",
            "Incident Date": "Incident_Date_Raw",
            "Incident Time": "Incident_Time_Raw",
            "Incident Date_Between": "Incident_Date_Between_Raw", 
            "Incident Time_Between": "Incident_Time_Between_Raw",
            "Report Date": "Report_Date_Raw",
            "Report Time": "Report_Time_Raw",
            "Incident Type_1": "Incident_Type_1_Raw",
            "Incident Type_2": "Incident_Type_2_Raw",
            "Incident Type_3": "Incident_Type_3_Raw",
            # ... other mappings
        }
    
    def cascade_time_fixed(self, row):
        """
        FIXED: Cascading time logic that handles both raw and mapped column names.
        
        The bug was that cascade function may be called on dataframes that have
        either raw column names OR mapped column names, depending on processing order.
        
        This fixed version checks for BOTH possibilities.
        """
        # Priority order for time extraction
        time_column_pairs = [
            ('Incident Time', 'Incident_Time_Raw'),           # Raw name, Mapped name
            ('Incident Time_Between', 'Incident_Time_Between_Raw'),
            ('Report Time', 'Report_Time_Raw')
        ]
        
        for raw_col, mapped_col in time_column_pairs:
            # Check both raw and mapped column names
            time_value = None
            
            # Try mapped column name first (preferred)
            if mapped_col in row.index and pd.notna(row.get(mapped_col)):
                time_value = row[mapped_col]
                self.logger.debug(f"Found time in mapped column: {mapped_col}")
            # Fallback to raw column name
            elif raw_col in row.index and pd.notna(row.get(raw_col)):
                time_value = row[raw_col]
                self.logger.debug(f"Found time in raw column: {raw_col}")
            
            # Process the time value if found
            if time_value is not None:
                try:
                    # CRITICAL FIX: Handle Timedelta objects from Excel
                    if isinstance(time_value, pd.Timedelta):
                        # Convert Timedelta to time object
                        total_seconds = time_value.total_seconds()
                        hours = int(total_seconds // 3600)
                        minutes = int((total_seconds % 3600) // 60)
                        seconds = int(total_seconds % 60)
                        
                        # Handle day overflow (24+ hours)
                        hours = hours % 24
                        
                        from datetime import time
                        return time(hours, minutes, seconds)
                        
                    elif isinstance(time_value, str):
                        # Try parsing string time
                        parsed_time = pd.to_datetime(time_value, errors='coerce')
                        if pd.notna(parsed_time):
                            return parsed_time.time()
                    elif hasattr(time_value, 'time'):
                        # Already a datetime object
                        return time_value.time()
                    elif hasattr(time_value, 'hour'):
                        # Already a time object
                        return time_value
                    else:
                        # Try converting to datetime
                        parsed_time = pd.to_datetime(time_value, errors='coerce')
                        if pd.notna(parsed_time):
                            return parsed_time.time()
                except Exception as e:
                    self.logger.warning(f"Failed to parse time value {time_value} (type: {type(time_value)}): {e}")
                    continue
        
        # No valid time found
        return None
    
    def cascade_date_fixed(self, row):
        """
        FIXED: Cascading date logic that handles both raw and mapped column names.
        """
        # Priority order for date extraction
        date_column_pairs = [
            ('Incident Date', 'Incident_Date_Raw'),
            ('Incident Date_Between', 'Incident_Date_Between_Raw'),
            ('Report Date', 'Report_Date_Raw')
        ]
        
        for raw_col, mapped_col in date_column_pairs:
            date_value = None
            
            # Try mapped column name first (preferred)
            if mapped_col in row.index and pd.notna(row.get(mapped_col)):
                date_value = row[mapped_col]
            # Fallback to raw column name
            elif raw_col in row.index and pd.notna(row.get(raw_col)):
                date_value = row[raw_col]
            
            # Process the date value if found
            if date_value is not None:
                try:
                    parsed_date = pd.to_datetime(date_value, errors='coerce')
                    if pd.notna(parsed_date):
                        return parsed_date.date()
                except Exception as e:
                    self.logger.warning(f"Failed to parse date value {date_value}: {e}")
                    continue
        
        return None
    
    def get_time_of_day(self, time_val):
        """Time of day calculation matching M Code exactly."""
        if pd.isna(time_val) or time_val is None:
            return "Unknown"
        
        try:
            # Handle different time formats
            if isinstance(time_val, str):
                time_obj = pd.to_datetime(time_val, errors='coerce').time()
            elif hasattr(time_val, 'hour'):
                time_obj = time_val
            else:
                return "Unknown"
            
            if time_obj is None:
                return "Unknown"
                
            hour = time_obj.hour
            if 0 <= hour < 4:
                return "00:00–03:59 Early Morning"
            elif 4 <= hour < 8:
                return "04:00–07:59 Morning"
            elif 8 <= hour < 12:
                return "08:00–11:59 Late Morning"
            elif 12 <= hour < 16:
                return "12:00–15:59 Afternoon"
            elif 16 <= hour < 20:
                return "16:00–19:59 Evening"
            else:
                return "20:00–23:59 Night"
        except:
            return "Unknown"
    
    def process_rms_data_fixed(self, rms_file):
        """
        FIXED: Process RMS data with robust time extraction.
        
        Key fixes:
        1. Apply column mapping first
        2. Use fixed cascade functions that handle both raw and mapped names
        3. Add validation logging for time extraction
        """
        self.logger.info(f"Processing RMS data: {rms_file}")
        
        try:
            # Load the data
            if isinstance(rms_file, str):
                rms_df = pd.read_excel(rms_file, engine='openpyxl')
            else:
                rms_df = pd.read_excel(rms_file, engine='openpyxl')
            
            self.logger.info(f"Loaded RMS file with {len(rms_df)} rows and {len(rms_df.columns)} columns")
            self.logger.info(f"Original columns: {list(rms_df.columns)}")
            
            # CRITICAL: Apply column mapping FIRST
            column_mapping = self.get_rms_column_mapping()
            existing_mapping = {k: v for k, v in column_mapping.items() if k in rms_df.columns}
            rms_df = rms_df.rename(columns=existing_mapping)
            self.logger.info(f"Applied column mapping: {existing_mapping}")
            self.logger.info(f"Mapped columns: {list(rms_df.columns)}")
            
            # Validate time columns exist
            time_columns = ['Incident_Time_Raw', 'Incident_Time_Between_Raw', 'Report_Time_Raw']
            found_time_cols = [col for col in time_columns if col in rms_df.columns]
            self.logger.info(f"Time columns found after mapping: {found_time_cols}")
            
            # Check for data in time columns
            for col in found_time_cols:
                non_null_count = rms_df[col].notna().sum()
                self.logger.info(f"Column {col}: {non_null_count} non-null values out of {len(rms_df)}")
                if non_null_count > 0:
                    sample_values = rms_df[col].dropna().head(3).tolist()
                    self.logger.info(f"Sample values in {col}: {sample_values}")
            
            # Apply FIXED cascade functions
            self.logger.info("Applying fixed cascade date function...")
            rms_df['Incident_Date'] = rms_df.apply(self.cascade_date_fixed, axis=1)
            
            self.logger.info("Applying fixed cascade time function...")
            rms_df['Incident_Time'] = rms_df.apply(self.cascade_time_fixed, axis=1)
            
            # Validate time extraction results
            time_extracted_count = rms_df['Incident_Time'].notna().sum()
            self.logger.info(f"RESULT: {time_extracted_count} out of {len(rms_df)} rows had time extracted")
            
            if time_extracted_count > 0:
                sample_times = rms_df['Incident_Time'].dropna().head(5).tolist()
                self.logger.info(f"Sample extracted times: {sample_times}")
            else:
                self.logger.error("CRITICAL: NO TIMES EXTRACTED - debugging required")
                
                # Debug: Check what's in the time columns
                for col in found_time_cols:
                    if col in rms_df.columns:
                        sample_data = rms_df[col].head(10).tolist()
                        self.logger.error(f"Debug - Raw data in {col}: {sample_data}")
            
            # Apply time of day calculation
            self.logger.info("Calculating time of day...")
            rms_df['Time_Of_Day'] = rms_df['Incident_Time'].apply(self.get_time_of_day)
            
            # Count time of day results
            time_of_day_known = rms_df[rms_df['Time_Of_Day'] != 'Unknown'].shape[0]
            self.logger.info(f"Time of day calculated for {time_of_day_known} out of {len(rms_df)} rows")
            
            return rms_df
            
        except Exception as e:
            self.logger.error(f"Error processing RMS data: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return pd.DataFrame()


# REPLACEMENT CODE for Comprehensive_SCRPA_Fix_v8.0_Standardized.py
# Replace lines 191-199 with this:

def cascade_time_FIXED(self, row):
    """
    FIXED: Cascading time logic that handles both raw and mapped column names.
    
    CRITICAL BUG FIXES:
    1. Original function assumed columns were already mapped
    2. Did not handle Excel Timedelta objects correctly
    
    This version handles both raw/mapped names AND Timedelta objects.
    """
    # Priority order: try mapped names first, fall back to raw names
    time_column_pairs = [
        ('Incident_Time_Raw', 'Incident Time'),           # Mapped name, Raw name
        ('Incident_Time_Between_Raw', 'Incident Time_Between'),
        ('Report_Time_Raw', 'Report Time')
    ]
    
    for mapped_col, raw_col in time_column_pairs:
        time_value = None
        
        # Try mapped column name first
        if mapped_col in row.index and pd.notna(row.get(mapped_col)):
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


if __name__ == "__main__":
    print("Fixed Time Cascade Function loaded.")
    print("Use cascade_time_FIXED() to replace the buggy function.")
    print("This fixes the column mapping issue causing 100% NULL incident_time values.")