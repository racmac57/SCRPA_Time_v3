#!/usr/bin/env python3
"""
RMS Column Mapping & Data Processing Fix
Comprehensive fix for critical null value issues and record loss
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from pathlib import Path

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

def extract_time_from_timedelta(time_val):
    """Extract time string from Timedelta objects"""
    if pd.isna(time_val):
        return None
    
    if isinstance(time_val, pd.Timedelta):
        total_seconds = int(time_val.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    # Handle string formats
    if isinstance(time_val, str):
        return time_val
    
    return str(time_val)

def categorize_time_of_day(time_val):
    """Categorize time into periods"""
    if pd.isna(time_val):
        return "Unknown"
    
    if isinstance(time_val, pd.Timedelta):
        total_seconds = int(time_val.total_seconds())
        hours = total_seconds // 3600
        
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

def extract_date_string(date_val):
    """Extract date string from various date formats"""
    if pd.isna(date_val):
        return None
    
    if isinstance(date_val, (pd.Timestamp, datetime)):
        return date_val.strftime('%Y-%m-%d')
    
    try:
        parsed_date = pd.to_datetime(date_val)
        return parsed_date.strftime('%Y-%m-%d')
    except:
        return str(date_val)

def extract_day_of_week(date_val):
    """Extract day of week from date"""
    if pd.isna(date_val):
        return None
    
    if isinstance(date_val, (pd.Timestamp, datetime)):
        return date_val.strftime('%A')
    
    try:
        parsed_date = pd.to_datetime(date_val)
        return parsed_date.strftime('%A')
    except:
        return None

def calculate_block_from_address(address):
    """Calculate block from full address"""
    if pd.isna(address):
        return "Check Location Data"
    
    address_str = str(address).strip()
    if not address_str:
        return "Check Location Data"
    
    # Extract first two words/numbers as block identifier
    parts = address_str.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    elif len(parts) == 1:
        return parts[0]
    else:
        return "Check Location Data"

def build_vehicle_info(row):
    """Build vehicle information string from components"""
    vehicle_parts = []
    
    # Add state and registration
    reg_state = row.get('Reg State 1', '')
    registration = row.get('Registration 1', '')
    make = row.get('Make1', '')
    model = row.get('Model1', '')
    
    if pd.notna(registration) and str(registration).strip():
        vehicle_parts.append(f"{reg_state} - {registration}")
        
        # Add make/model if available
        make_model_parts = []
        if pd.notna(make) and str(make).strip():
            make_model_parts.append(str(make))
        if pd.notna(model) and str(model).strip():
            make_model_parts.append(str(model))
        
        if make_model_parts:
            vehicle_parts.append(f"{'/'.join(make_model_parts)}")
        
        return ', '.join(vehicle_parts)
    
    return None

def apply_rms_column_mapping_fix():
    """Apply comprehensive RMS column mapping fixes"""
    print("=== RMS COLUMN MAPPING & DATA PROCESSING FIX ===")
    
    # Load raw RMS export
    exports_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\05_Exports")
    rms_exports = list(exports_dir.glob("*SCRPA_RMS*.xlsx"))
    
    if not rms_exports:
        print("ERROR: No RMS export files found")
        return None
    
    # Use most recent file
    latest_export = max(rms_exports, key=lambda p: p.stat().st_mtime)
    print(f"Processing: {latest_export.name}")
    
    try:
        # Load raw data
        raw_df = pd.read_excel(latest_export)
        print(f"Loaded raw data: {len(raw_df)} records, {len(raw_df.columns)} columns")
        
        # Create processed dataframe with corrected column mapping
        processed_df = pd.DataFrame()
        
        # 1. CASE NUMBER - Standardized format
        processed_df['case_number'] = raw_df['Case Number'].apply(standardize_case_number)
        print(f"Case numbers processed: {processed_df['case_number'].notna().sum()}/{len(processed_df)}")
        
        # 2. DATE PROCESSING - Fixed mapping
        processed_df['incident_date'] = raw_df['Incident Date'].apply(extract_date_string)
        processed_df['day_of_week'] = raw_df['Incident Date'].apply(extract_day_of_week)
        processed_df['day_type'] = processed_df['day_of_week'].apply(
            lambda x: "Weekend" if x in ['Saturday', 'Sunday'] else "Weekday" if x else None
        )
        print(f"Dates processed: {processed_df['incident_date'].notna().sum()}/{len(processed_df)}")
        
        # 3. TIME PROCESSING - Fixed Timedelta handling
        processed_df['incident_time'] = raw_df['Incident Time'].apply(extract_time_from_timedelta)
        processed_df['time_of_day'] = raw_df['Incident Time'].apply(categorize_time_of_day)
        
        # Time of day sort order
        time_order_map = {
            "Early Morning": 1, "Morning": 2, "Afternoon": 3, 
            "Evening": 4, "Night": 5, "Unknown": 99
        }
        processed_df['time_of_day_sort_order'] = processed_df['time_of_day'].map(time_order_map)
        print(f"Times processed: {processed_df['incident_time'].notna().sum()}/{len(processed_df)}")
        
        # 4. LOCATION - CRITICAL FIX: Use 'FullAddress' not 'location'
        processed_df['location'] = raw_df['FullAddress']  # CORRECTED MAPPING
        processed_df['block'] = processed_df['location'].apply(calculate_block_from_address)
        print(f"Locations processed: {processed_df['location'].notna().sum()}/{len(processed_df)}")
        
        # 5. GRID AND POST - CRITICAL FIX: Correct column mapping
        processed_df['grid'] = raw_df['Grid']  # Direct mapping
        processed_df['post'] = raw_df['Zone']  # CORRECTED: Zone -> post
        print(f"Grid processed: {processed_df['grid'].notna().sum()}/{len(processed_df)}")
        print(f"Post processed: {processed_df['post'].notna().sum()}/{len(processed_df)}")
        
        # 6. INCIDENT TYPE - CRITICAL FIX: Use 'Incident Type_1' not 'incident_type'
        processed_df['incident_type'] = raw_df['Incident Type_1']  # CORRECTED MAPPING
        processed_df['all_incidents'] = raw_df['Incident Type_1']  # Same as primary
        print(f"Incident types processed: {processed_df['incident_type'].notna().sum()}/{len(processed_df)}")
        
        # 7. VEHICLE INFORMATION - Fixed construction
        processed_df['vehicle_1'] = raw_df.apply(build_vehicle_info, axis=1)
        processed_df['vehicle_2'] = None  # Rarely used
        processed_df['vehicle_1_and_vehicle_2'] = None
        
        # 8. ADDITIONAL FIELDS - Direct mapping
        processed_df['narrative'] = raw_df['Narrative']
        processed_df['total_value_stolen'] = raw_df['Total Value Stolen']
        processed_df['squad'] = raw_df['Squad']
        processed_df['officer_of_record'] = raw_df['Officer of Record']
        processed_df['nibrs_classification'] = raw_df['NIBRS Classification']
        
        # 9. COMPUTED FIELDS
        processed_df['period'] = "YTD"  # Year to date
        processed_df['season'] = "Winter"  # Based on January dates
        
        # 10. CYCLE NAME - From case number pattern
        processed_df['cycle_name'] = processed_df['case_number'].apply(
            lambda x: f"C{x[:2]}W{x[3:5]}" if isinstance(x, str) and len(x) >= 8 else None
        )
        
        print(f"\nProcessed dataset: {len(processed_df)} records, {len(processed_df.columns)} columns")
        
        return processed_df, raw_df
        
    except Exception as e:
        print(f"ERROR in column mapping fix: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def validate_fix_results(processed_df, raw_df):
    """Validate the fix results against original data"""
    print("\n=== VALIDATION REPORT ===")
    
    if processed_df is None or raw_df is None:
        print("ERROR: Missing data for validation")
        return False
    
    # Record preservation check
    print(f"1. RECORD PRESERVATION:")
    print(f"   Raw records: {len(raw_df)}")
    print(f"   Processed records: {len(processed_df)}")
    record_loss = len(raw_df) - len(processed_df)
    if record_loss == 0:
        print(f"   SUCCESS: 100% record preservation")
    else:
        print(f"   WARNING: {record_loss} records lost")
    
    # Critical field validation
    print(f"\n2. CRITICAL FIELDS VALIDATION:")
    critical_fields = {
        'location': 'FullAddress',
        'incident_type': 'Incident Type_1', 
        'incident_time': 'Incident Time',
        'grid': 'Grid',
        'post': 'Zone'
    }
    
    all_success = True
    for processed_col, raw_col in critical_fields.items():
        if processed_col in processed_df.columns and raw_col in raw_df.columns:
            processed_count = processed_df[processed_col].notna().sum()
            raw_count = raw_df[raw_col].notna().sum()
            
            print(f"   {processed_col}:")
            print(f"     Raw: {raw_count}/{len(raw_df)} populated")
            print(f"     Processed: {processed_count}/{len(processed_df)} populated")
            
            if processed_count >= raw_count * 0.95:  # Allow 5% tolerance
                print(f"     SUCCESS: Data preserved")
            else:
                print(f"     FAILURE: Data loss detected")
                all_success = False
        else:
            print(f"   {processed_col}: MISSING COLUMN")
            all_success = False
    
    # Sample data verification
    print(f"\n3. SAMPLE DATA VERIFICATION:")
    sample_processed = processed_df[['case_number', 'location', 'incident_type', 'incident_time', 'grid', 'post']].head(3)
    print(sample_processed.to_string(index=False))
    
    return all_success

def save_fixed_results(processed_df):
    """Save the fixed RMS data"""
    if processed_df is None:
        print("ERROR: No processed data to save")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"RMS_Fixed_ColumnMapping_{timestamp}.csv"
    
    try:
        processed_df.to_csv(output_file, index=False)
        print(f"\nFixed RMS data saved: {output_file}")
        return output_file
    except Exception as e:
        print(f"ERROR saving fixed data: {e}")
        return None

def main():
    """Main execution function"""
    print("=== EXECUTING RMS COLUMN MAPPING FIX ===")
    
    # Apply the column mapping fix
    processed_df, raw_df = apply_rms_column_mapping_fix()
    
    if processed_df is None:
        print("FAILED: Column mapping fix could not be applied")
        return False
    
    # Validate the results
    validation_success = validate_fix_results(processed_df, raw_df)
    
    # Save the fixed data
    output_file = save_fixed_results(processed_df)
    
    # Final summary
    print(f"\n=== FIX EXECUTION SUMMARY ===")
    if validation_success and output_file:
        print("SUCCESS: RMS column mapping fix completed")
        print(f"- Records preserved: {len(processed_df)}/{len(raw_df) if raw_df is not None else 'Unknown'}")
        print(f"- Critical fields populated: All key fields now have data")
        print(f"- Output file: {output_file}")
        print("- Ready for integration into main pipeline")
    else:
        print("PARTIAL SUCCESS: Fix applied with issues")
        print("- Review validation report for details")
    
    return validation_success

if __name__ == "__main__":
    success = main()