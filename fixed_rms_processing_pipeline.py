#!/usr/bin/env python3
"""
FIXED RMS Processing Pipeline with Correct Column Mapping
Addresses critical issues identified in v8.5 integration
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from pathlib import Path

def load_cad_reference():
    """Load CAD reference file for proper categorization"""
    ref_file = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\CallType_Categories.xlsx")
    
    if not ref_file.exists():
        print(f"WARNING: CAD reference file not found: {ref_file}")
        return pd.DataFrame()
    
    try:
        ref_df = pd.read_excel(ref_file)
        print(f"Loaded CAD reference: {len(ref_df)} incident types")
        return ref_df
    except Exception as e:
        print(f"ERROR loading CAD reference: {e}")
        return pd.DataFrame()

def cascade_time(time_val):
    """Extract time from various time formats"""
    if pd.isna(time_val):
        return "Unknown"
    
    # Handle Timedelta objects (from Excel)
    if isinstance(time_val, pd.Timedelta):
        total_seconds = int(time_val.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        # Classify time periods
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
    
    # Handle string time formats
    if isinstance(time_val, str):
        # Extract hours from string patterns
        hour_match = re.search(r'(\d{1,2}):(\d{2})', time_val)
        if hour_match:
            hours = int(hour_match.group(1))
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
    
    return "Unknown"

def cascade_date(date_val):
    """Extract date components"""
    if pd.isna(date_val):
        return None
    
    if isinstance(date_val, (pd.Timestamp, datetime)):
        return date_val.strftime('%Y-%m-%d')
    
    try:
        parsed_date = pd.to_datetime(date_val)
        return parsed_date.strftime('%Y-%m-%d')
    except:
        return None

def standardize_case_number(case_num):
    """Standardize case number format"""
    if pd.isna(case_num):
        return None
    
    case_str = str(case_num).strip()
    
    # Handle different formats: 25-000813, 25000813, etc.
    if re.match(r'^\d{2}-\d{6}$', case_str):
        return case_str
    elif re.match(r'^\d{8}$', case_str):
        return f"{case_str[:2]}-{case_str[2:]}"
    
    return case_str

def process_raw_rms_data():
    """Process raw RMS Excel data with correct column mapping"""
    print("=== PROCESSING RAW RMS DATA ===")
    
    # Load raw RMS Excel
    rms_excel = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\05_Exports\2025_08_01_19_38_12_SCRPA_RMS.xlsx")
    
    if not rms_excel.exists():
        print(f"ERROR: Raw RMS Excel not found: {rms_excel}")
        return None
    
    try:
        # Load raw data
        raw_df = pd.read_excel(rms_excel)
        print(f"Loaded raw RMS data: {len(raw_df)} records")
        
        # CRITICAL FIX: Correct column mapping from raw RMS
        processed_df = pd.DataFrame()
        
        # 1. Case number standardization
        processed_df['case_number'] = raw_df['Case Number'].apply(standardize_case_number)
        
        # 2. Date processing (using cascade_date function)
        processed_df['incident_date'] = raw_df['Incident Date'].apply(cascade_date)
        
        # 3. Time processing (using cascade_time function)
        def format_timedelta_to_time(time_val):
            if pd.isna(time_val):
                return None
            if isinstance(time_val, pd.Timedelta):
                total_seconds = int(time_val.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            return str(time_val)
        
        processed_df['incident_time'] = raw_df['Incident Time'].apply(format_timedelta_to_time)
        processed_df['time_of_day'] = raw_df['Incident Time'].apply(cascade_time)
        
        # Time of day sort order
        time_order_map = {
            "Early Morning": 1, "Morning": 2, "Afternoon": 3, 
            "Evening": 4, "Night": 5, "Unknown": 99
        }
        processed_df['time_of_day_sort_order'] = processed_df['time_of_day'].map(time_order_map)
        
        # 4. Location - CRITICAL FIX: Use 'FullAddress' not 'location'
        processed_df['location'] = raw_df['FullAddress']
        
        # 5. Location components
        processed_df['block'] = processed_df['location'].apply(
            lambda x: ' '.join(str(x).split()[:2]) if pd.notna(x) else "Check Location Data"
        )
        processed_df['grid'] = raw_df['Grid']
        processed_df['post'] = raw_df['Zone']  # Zone maps to post
        
        # 6. Incident type - CRITICAL FIX: Use 'Incident Type_1' not 'incident_type'
        processed_df['incident_type'] = raw_df['Incident Type_1']
        processed_df['all_incidents'] = raw_df['Incident Type_1']  # Primary incident type
        
        # 7. Vehicle information
        # Combine vehicle info properly
        vehicle_1_parts = []
        if 'Reg State 1' in raw_df.columns:
            vehicle_1_parts.append(raw_df['Reg State 1'].fillna(''))
        if 'Registration 1' in raw_df.columns:
            vehicle_1_parts.append(raw_df['Registration 1'].fillna(''))
        if 'Make1' in raw_df.columns:
            vehicle_1_parts.append(raw_df['Make1'].fillna(''))
        if 'Model1' in raw_df.columns:
            vehicle_1_parts.append(raw_df['Model1'].fillna(''))
        
        if vehicle_1_parts:
            processed_df['vehicle_1'] = raw_df.apply(
                lambda row: f"{row.get('Reg State 1', '')} - {row.get('Registration 1', '')}, {row.get('Make1', '')}/{row.get('Model1', '')}"
                if pd.notna(row.get('Registration 1')) else None, axis=1
            )
        else:
            processed_df['vehicle_1'] = None
            
        processed_df['vehicle_2'] = None  # Second vehicle rarely used
        processed_df['vehicle_1_and_vehicle_2'] = None
        
        # 8. Additional fields
        processed_df['narrative'] = raw_df['Narrative']
        processed_df['total_value_stolen'] = raw_df['Total Value Stolen']
        processed_df['squad'] = raw_df['Squad']
        processed_df['officer_of_record'] = raw_df['Officer of Record']
        processed_df['nibrs_classification'] = raw_df['NIBRS Classification']
        
        # 9. Time components
        processed_df['period'] = "YTD"  # Year to date
        processed_df['season'] = "Winter"  # Based on January dates
        
        # Day of week calculation
        processed_df['day_of_week'] = raw_df['Incident Date'].apply(
            lambda x: x.strftime('%A') if isinstance(x, pd.Timestamp) else None
        )
        processed_df['day_type'] = processed_df['day_of_week'].apply(
            lambda x: "Weekend" if x in ['Saturday', 'Sunday'] else "Weekday" if x else None
        )
        
        # 10. Cycle name (from case number pattern)
        processed_df['cycle_name'] = processed_df['case_number'].apply(
            lambda x: f"C{x[:2]}W{x[3:5]}" if isinstance(x, str) and len(x) >= 8 else None
        )
        
        print(f"Processed RMS data: {len(processed_df)} records")
        print(f"Records with location: {processed_df['location'].notna().sum()}")
        print(f"Records with incident_type: {processed_df['incident_type'].notna().sum()}")
        print(f"Records with time_of_day: {(processed_df['time_of_day'] != 'Unknown').sum()}")
        
        return processed_df
        
    except Exception as e:
        print(f"ERROR processing raw RMS data: {e}")
        return None

def process_cad_with_reference():
    """Process CAD data with reference file integration"""
    print("=== PROCESSING CAD DATA WITH REFERENCE ===")
    
    # Load CAD reference
    ref_df = load_cad_reference()
    
    # Find latest CAD file
    powerbi_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi")
    cad_files = list(powerbi_dir.glob("*cad_data_standardized.csv"))
    
    if not cad_files:
        print("ERROR: No CAD files found")
        return None
    
    cad_file = max(cad_files, key=lambda p: p.stat().st_mtime)
    
    try:
        # Load CAD data
        cad_df = pd.read_csv(cad_file)
        print(f"Loaded CAD data: {len(cad_df)} records")
        
        if not ref_df.empty:
            # Merge with reference data for proper categorization
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
            
            print(f"Applied reference mapping to {len(ref_lookup)} incident types")
        
        return cad_df
        
    except Exception as e:
        print(f"ERROR processing CAD data: {e}")
        return None

def create_matched_dataset(cad_df, rms_df):
    """Create matched dataset with LEFT JOIN preserving all RMS records"""
    print("=== CREATING MATCHED DATASET ===")
    
    if cad_df is None or rms_df is None:
        print("ERROR: Missing input data")
        return None
    
    # Use LEFT JOIN with RMS as master to preserve all 134 records
    matched_df = rms_df.merge(
        cad_df[['case_number', 'incident', 'category_type', 'response_type']], 
        on='case_number', 
        how='left'
    )
    
    print(f"Matched dataset created: {len(matched_df)} records")
    print(f"RMS records preserved: {len(matched_df)} (should be 134)")
    print(f"CAD matches found: {matched_df['incident'].notna().sum()}")
    
    return matched_df

def main():
    """Main execution function"""
    print("=== FIXED RMS PROCESSING PIPELINE ===")
    
    # 1. Process raw RMS data with correct column mapping
    rms_df = process_raw_rms_data()
    if rms_df is None:
        print("FAILED: Could not process RMS data")
        return False
    
    # 2. Process CAD data with reference integration
    cad_df = process_cad_with_reference()
    if cad_df is None:
        print("FAILED: Could not process CAD data")
        return False
    
    # 3. Create matched dataset preserving all RMS records
    matched_df = create_matched_dataset(cad_df, rms_df)
    if matched_df is None:
        print("FAILED: Could not create matched dataset")
        return False
    
    # 4. Save corrected outputs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save individual datasets
    rms_output = f"C08W31_{timestamp}_rms_data_fixed.csv"
    rms_df.to_csv(rms_output, index=False)
    print(f"Saved fixed RMS data: {rms_output}")
    
    cad_output = f"C08W31_{timestamp}_cad_data_fixed.csv"
    cad_df.to_csv(cad_output, index=False)
    print(f"Saved fixed CAD data: {cad_output}")
    
    # Save matched dataset
    matched_output = f"C08W31_{timestamp}_cad_rms_matched_fixed.csv"
    matched_df.to_csv(matched_output, index=False)
    print(f"Saved fixed matched data: {matched_output}")
    
    # Validation summary
    print("\n=== VALIDATION SUMMARY ===")
    print(f"RMS records: {len(rms_df)}")
    print(f"RMS with location: {rms_df['location'].notna().sum()}")
    print(f"RMS with incident_type: {rms_df['incident_type'].notna().sum()}")
    print(f"RMS with proper time: {(rms_df['time_of_day'] != 'Unknown').sum()}")
    print(f"Matched records: {len(matched_df)}")
    print(f"CAD integration rate: {(matched_df['incident'].notna().sum() / len(matched_df)) * 100:.1f}%")
    
    print("\n=== FIXED PIPELINE COMPLETE ===")
    return True

if __name__ == "__main__":
    success = main()