#!/usr/bin/env python3
"""
CRITICAL DEBUGGING SCRIPT - v8.5 Functions
Test each function with real data and detailed logging
"""

import sys
import os
import pandas as pd
import re
from datetime import datetime, time
import logging

# Setup debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - DEBUG - %(message)s')
logger = logging.getLogger('v85_debug')

# Add scripts path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '01_scripts'))

def debug_clean_how_reported_911():
    """DEBUG FUNCTION 1: clean_how_reported_911()"""
    print("="*60)
    print("DEBUGGING clean_how_reported_911()")
    print("="*60)
    
    def debug_clean_how_reported_911_logic(how_reported):
        """Debug version with extensive logging"""
        logger.debug(f"INPUT: {repr(how_reported)} (type: {type(how_reported)})")
        
        if pd.isna(how_reported):
            logger.debug("RESULT: None (input was NaN)")
            return None
        
        text = str(how_reported).strip()
        logger.debug(f"AFTER STR/STRIP: {repr(text)}")
        
        # Handle various date formats that might be incorrectly applied to "9-1-1"
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD format
            r'^\d{1,2}/\d{1,2}/\d{4}',  # M/D/YYYY or MM/DD/YYYY format
            r'^\d{1,2}-\d{1,2}-\d{4}',  # M-D-YYYY or MM-DD-YYYY format
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO datetime format
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # YYYY-MM-DD HH:MM:SS format
        ]
        
        # Check if the value matches any date pattern
        for i, pattern in enumerate(date_patterns):
            if re.match(pattern, text):
                logger.debug(f"MATCHED PATTERN {i}: {pattern} -> CONVERTING TO 9-1-1")
                return "9-1-1"
        
        # Check for specific date values that commonly result from "9-1-1" conversion
        problem_dates = ['2001-09-01', '2001-09-01 00:00:00', '09/01/2001', '9/1/2001', '2001-09-01T00:00:00']
        if text in problem_dates:
            logger.debug(f"MATCHED PROBLEM DATE: {text} -> CONVERTING TO 9-1-1")
            return "9-1-1"
        
        # Check for numeric only patterns that could be dates
        if re.match(r'^\d{8}$', text):  # YYYYMMDD
            logger.debug(f"MATCHED NUMERIC DATE: {text} -> CONVERTING TO 9-1-1")
            return "9-1-1"
        
        logger.debug(f"NO PATTERN MATCH: Returning original value: {text}")
        return text
    
    # Test cases
    test_cases = [
        "2001-09-01",
        "2001-09-01 00:00:00", 
        "9/1/2001",
        "09/01/2001",
        "2019-09-01",
        "911",
        "9-1-1",
        "Walk-in",
        "Phone"
    ]
    
    print("Testing clean_how_reported_911() logic:")
    for test_case in test_cases:
        print(f"\n--- Testing: {repr(test_case)} ---")
        result = debug_clean_how_reported_911_logic(test_case)
        expected = "9-1-1" if test_case in ["2001-09-01", "2001-09-01 00:00:00", "9/1/2001", "09/01/2001", "2019-09-01"] else test_case
        status = "PASS" if result == expected else "FAIL"
        print(f"RESULT: {repr(result)} | EXPECTED: {repr(expected)} | {status}")

def debug_extract_username_timestamp():
    """DEBUG FUNCTION 2: extract_username_timestamp()"""
    print("\n" + "="*60)
    print("DEBUGGING extract_username_timestamp()")
    print("="*60)
    
    def debug_extract_username_timestamp_logic(cad_notes):
        """Debug version with extensive logging"""
        logger.debug(f"INPUT: {repr(cad_notes)} (type: {type(cad_notes)})")
        
        if pd.isna(cad_notes):
            logger.debug("RESULT: (None, None, None) - input was NaN")
            return None, None, None
            
        text = str(cad_notes)
        logger.debug(f"AFTER STR: {repr(text)}")
        username = None
        timestamp = None
        
        # Look for username pattern (usually at start) - IMPROVED PATTERN
        username_match = re.search(r'^([A-Z]{2,}\d*|[a-zA-Z]+\.[a-zA-Z]+)', text)
        if username_match:
            username = username_match.group(1)
            logger.debug(f"FOUND USERNAME: {repr(username)}")
        else:
            logger.debug("NO USERNAME FOUND")
        
        # Look for timestamp patterns
        timestamp_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [AP]M',
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}'
        ]
        
        for i, pattern in enumerate(timestamp_patterns):
            timestamp_match = re.search(pattern, text)
            if timestamp_match:
                timestamp = timestamp_match.group(0)
                logger.debug(f"FOUND TIMESTAMP (pattern {i}): {repr(timestamp)}")
                break
        
        if not timestamp:
            logger.debug("NO TIMESTAMP FOUND")
        
        # Clean the notes by removing username/timestamp patterns
        cleaned = text
        logger.debug(f"CLEANING STARTED: {repr(cleaned)}")
        
        if username:
            cleaned = re.sub(f'^{re.escape(username)}[\\s:]*', '', cleaned)
            logger.debug(f"AFTER USERNAME REMOVAL: {repr(cleaned)}")
        if timestamp:
            cleaned = re.sub(re.escape(timestamp), '', cleaned)
            logger.debug(f"AFTER TIMESTAMP REMOVAL: {repr(cleaned)}")
        
        # Additional cleaning
        cleaned = re.sub(r'[\r\n\t]+', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned) 
        cleaned = cleaned.strip()
        logger.debug(f"AFTER FINAL CLEANING: {repr(cleaned)}")
        
        final_cleaned = cleaned if cleaned else None
        logger.debug(f"FINAL RESULT: cleaned={repr(final_cleaned)}, username={repr(username)}, timestamp={repr(timestamp)}")
        
        return final_cleaned, username, timestamp
    
    # Test cases
    test_cases = [
        "SMITH123 7/29/2024 2:15:30 PM: Officer responded to scene",
        "JOHN.DOE 2024-07-29 14:15:30 Multiple units dispatched", 
        "DISPATCH 8/1/2024 10:30 Incident reported",
        "Simple note without username or timestamp",
        "OFFICER1: 7/30/2024 9:45:15 AM - Unit en route",
        ""
    ]
    
    print("Testing extract_username_timestamp() logic:")
    for test_case in test_cases:
        print(f"\n--- Testing: {repr(test_case)} ---")
        cleaned, username, timestamp = debug_extract_username_timestamp_logic(test_case)
        print(f"CLEANED: {repr(cleaned)}")
        print(f"USERNAME: {repr(username)}")
        print(f"TIMESTAMP: {repr(timestamp)}")

def debug_cascade_functions():
    """DEBUG FUNCTION 3: cascade_date() and cascade_time()"""
    print("\n" + "="*60)
    print("DEBUGGING cascade_date() and cascade_time()")
    print("="*60)
    
    def debug_cascade_date_logic(row):
        """Debug version of cascade_date with extensive logging"""
        logger.debug(f"CASCADE_DATE INPUT ROW COLUMNS: {list(row.index)}")
        logger.debug(f"CASCADE_DATE INPUT ROW VALUES: {dict(row)}")
        
        # Try normalized lowercase column names first
        date_columns = [
            'incident_date', 'incident_date_between', 'report_date',
            'incident_date_raw', 'incident_date_between_raw', 'report_date_raw'
        ]
        
        for col in date_columns:
            if col in row.index:
                value = row.get(col)
                logger.debug(f"CHECKING COLUMN {col}: {repr(value)} (type: {type(value)})")
                if pd.notna(value):
                    try:
                        result = pd.to_datetime(value, errors='coerce').date()
                        logger.debug(f"SUCCESSFUL CONVERSION: {col} -> {result}")
                        return result
                    except Exception as e:
                        logger.debug(f"CONVERSION FAILED: {col} -> {e}")
                        continue
                else:
                    logger.debug(f"COLUMN {col} IS NaN")
            else:
                logger.debug(f"COLUMN {col} NOT FOUND IN ROW")
        
        logger.debug("CASCADE_DATE RETURNING None - no valid date found")
        return None
    
    def debug_cascade_time_logic(row):
        """Debug version of cascade_time with extensive logging"""
        logger.debug(f"CASCADE_TIME INPUT ROW COLUMNS: {list(row.index)}")
        
        # Priority order: try lowercase names first, then mapped names, fall back to raw names
        time_column_pairs = [
            ('incident_time_raw', 'Incident_Time_Raw', 'Incident Time'),
            ('incident_time_between_raw', 'Incident_Time_Between_Raw', 'Incident Time_Between'),
            ('report_time_raw', 'Report_Time_Raw', 'Report Time')
        ]
        
        for lowercase_col, mapped_col, raw_col in time_column_pairs:
            time_value = None
            found_col = None
            
            # Try lowercase column name first
            if lowercase_col in row.index and pd.notna(row.get(lowercase_col)):
                time_value = row[lowercase_col]
                found_col = lowercase_col
            # Try mapped column name
            elif mapped_col in row.index and pd.notna(row.get(mapped_col)):
                time_value = row[mapped_col]
                found_col = mapped_col
            # Fallback to raw column name
            elif raw_col in row.index and pd.notna(row.get(raw_col)):
                time_value = row[raw_col]
                found_col = raw_col
            
            if time_value is not None:
                logger.debug(f"FOUND TIME VALUE in {found_col}: {repr(time_value)} (type: {type(time_value)})")
                
                try:
                    # CRITICAL: Handle Excel Timedelta objects
                    if isinstance(time_value, pd.Timedelta):
                        total_seconds = time_value.total_seconds()
                        hours = int(total_seconds // 3600) % 24
                        minutes = int((total_seconds % 3600) // 60)
                        seconds = int(total_seconds % 60)
                        
                        from datetime import time
                        result = time(hours, minutes, seconds)
                        logger.debug(f"TIMEDELTA CONVERSION: {time_value} -> {result}")
                        return result
                    else:
                        result = pd.to_datetime(time_value, errors='coerce').time()
                        logger.debug(f"DATETIME CONVERSION: {time_value} -> {result}")
                        return result
                except Exception as e:
                    logger.debug(f"CONVERSION FAILED for {found_col}: {e}")
                    continue
            else:
                logger.debug(f"NO TIME VALUE FOUND for columns: {lowercase_col}, {mapped_col}, {raw_col}")
        
        logger.debug("CASCADE_TIME RETURNING None - no valid time found")
        return None
    
    # Create test RMS data
    test_data = {
        'case_number': ['2024-001', '2024-002', '2024-003'],
        'incident_date_raw': ['2024-07-29', None, '2024-08-01'],
        'incident_time_raw': [pd.Timedelta('08:30:00'), None, '14:45:00'],
        'report_date_raw': ['2024-07-29', '2024-07-30', None],
        'report_time_raw': ['09:00:00', pd.Timedelta('10:15:00'), None]
    }
    
    test_df = pd.DataFrame(test_data)
    print("Testing cascade functions with sample RMS data:")
    print(f"Test DataFrame:\n{test_df}")
    
    for i, row in test_df.iterrows():
        print(f"\n--- Testing Row {i} ---")
        print(f"Row data: {dict(row)}")
        
        date_result = debug_cascade_date_logic(row)
        time_result = debug_cascade_time_logic(row)
        
        print(f"CASCADE_DATE RESULT: {date_result}")
        print(f"CASCADE_TIME RESULT: {time_result}")

def main():
    """Run all debugging functions"""
    print("CRITICAL v8.5 FUNCTION DEBUGGING SESSION")
    print("=" * 80)
    
    try:
        # DEBUG 1: clean_how_reported_911
        debug_clean_how_reported_911()
        
        # DEBUG 2: extract_username_timestamp
        debug_extract_username_timestamp()
        
        # DEBUG 3: cascade functions
        debug_cascade_functions()
        
        print("\n" + "="*80)
        print("DEBUGGING SESSION COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"DEBUGGING FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()