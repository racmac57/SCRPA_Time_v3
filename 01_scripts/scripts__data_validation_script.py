# 🕒 2025-06-25-15-40-15
# SCRPA Crime Analysis/data_validation.py
# Author: R. A. Carucci  
# Purpose: Validates CAD data cycle assignments and identifies mapping issues

import pandas as pd
import sys
from datetime import datetime, timedelta

def validate_cad_data(csv_file):
    """
    Comprehensive validation of CAD data
    """
    
    print("=== SCRPA CAD DATA VALIDATION ===")
    print(f"File: {csv_file}")
    print(f"Validation time: {datetime.now()}")
    
    try:
        # Load data
        df = pd.read_csv(csv_file)
        print(f"\nLoaded {len(df)} total records")
        
        # Convert Time of Call to datetime
        df['call_datetime'] = pd.to_datetime(df['Time of Call'])
        df['call_date'] = df['call_datetime'].dt.date
        
        print(f"Date range: {df['call_date'].min()} to {df['call_date'].max()}")
        
        # Validate cycle assignments
        print("\n=== CYCLE VALIDATION ===")
        
        today = datetime.now().date()
        seven_days_ago = today - timedelta(days=7)
        twenty_eight_days_ago = today - timedelta(days=28)
        ytd_start = datetime(today.year, 1, 1).date()
        
        print(f"Today: {today}")
        print(f"7-Day period: {seven_days_ago} to {today}")
        print(f"28-Day period: {twenty_eight_days_ago} to {today}")
        print(f"YTD period: {ytd_start} to {today}")
        
        # Analyze actual cycle assignments
        cycle_counts = df['Cycle'].value_counts()
        print(f"\nActual cycle assignments:")
        for cycle, count in cycle_counts.items():
            print(f"  {cycle}: {count} records")
        
        # Validate 7-Day assignments
        seven_day_records = df[df['Cycle'] == '7-Day']
        if len(seven_day_records) > 0:
            seven_day_dates = seven_day_records['call_date'].unique()
            print(f"\n7-Day cycle dates: {sorted(seven_day_dates)}")
            
            # Check if any are outside the 7-day window
            invalid_7day = seven_day_records[seven_day_records['call_date'] < seven_days_ago]
            if len(invalid_7day) > 0:
                print(f"  WARNING: {len(invalid_7day)} records marked as 7-Day but older than 7 days")
        
        # Validate 28-Day assignments  
        twenty_eight_day_records = df[df['Cycle'] == '28-Day']
        if len(twenty_eight_day_records) > 0:
            twenty_eight_day_dates = twenty_eight_day_records['call_date'].unique()
            print(f"\n28-Day cycle dates: {sorted(twenty_eight_day_dates)}")
            
            # Check if any are outside the 28-day window
            invalid_28day = twenty_eight_day_records[twenty_eight_day_records['call_date'] < twenty_eight_days_ago]
            if len(invalid_28day) > 0:
                print(f"  WARNING: {len(invalid_28day)} records marked as 28-Day but older than 28 days")
        
        # Validate YTD assignments
        ytd_records = df[df['Cycle'] == 'YTD']
        if len(ytd_records) > 0:
            ytd_dates = ytd_records['call_date'].unique()
            print(f"\nYTD cycle date range: {min(ytd_dates)} to {max(ytd_dates)}")
            
            # Check if any are from previous year
            invalid_ytd = ytd_records[ytd_records['call_date'] < ytd_start]
            if len(invalid_ytd) > 0:
                print(f"  WARNING: {len(invalid_ytd)} records marked as YTD but from previous year")
        
        # Mapping validation
        print("\n=== MAPPING VALIDATION ===")
        
        total_records = len(df)
        null_zones = df['PDZone'].isnull().sum()
        null_grids = (df['Grid'].isnull() | (df['Grid'] == 'null')).sum()
        
        print(f"Total records: {total_records}")
        print(f"Records with null PDZone: {null_zones}")
        print(f"Records with null/missing Grid: {null_grids}")
        print(f"Mappable records: {total_records - max(null_zones, null_grids)}")
        print(f"Mapping success rate: {((total_records - max(null_zones, null_grids)) / total_records * 100):.1f}%")
        
        # Show problematic records
        problematic = df[df['PDZone'].isnull() | (df['Grid'] == 'null')]
        if len(problematic) > 0:
            print(f"\nProblematic records for mapping:")
            for idx, row in problematic.iterrows():
                print(f"  {row['ReportNumberNew']}: {row['FullAddress2']} (Zone: {row['PDZone']}, Grid: {row['Grid']})")
        
        # Zone distribution
        valid_zones = df[df['PDZone'].notna()]
        if len(valid_zones) > 0:
            print(f"\nZone distribution:")
            zone_counts = valid_zones['PDZone'].value_counts().sort_index()
            for zone, count in zone_counts.items():
                print(f"  Zone {zone}: {count} records")
        
        # Incident analysis
        print("\n=== INCIDENT ANALYSIS ===")
        
        incident_counts = df['Incident'].value_counts()
        print(f"Total unique incident types: {len(incident_counts)}")
        print(f"Top 10 incident types:")
        for i, (incident, count) in enumerate(incident_counts.head(10).items(), 1):
            print(f"  {i}. {incident}: {count}")
        
        # Time analysis
        print("\n=== TIME ANALYSIS ===")
        
        df['hour'] = df['call_datetime'].dt.hour
        
        def categorize_time(hour):
            if pd.isna(hour):
                return "Unknown"
            elif 6 <= hour < 14:
                return "Day (6am-2pm)"
            elif 14 <= hour < 22:
                return "Evening (2pm-10pm)"
            else:
                return "Night (10pm-6am)"
        
        df['time_period'] = df['hour'].apply(categorize_time)
        time_counts = df['time_period'].value_counts()
        
        print(f"Time period distribution:")
        for period, count in time_counts.items():
            print(f"  {period}: {count} records")
        
        # Monthly distribution
        print("\n=== MONTHLY DISTRIBUTION ===")
        monthly_counts = df['cMonth'].value_counts()
        print(f"Records by month:")
        for month, count in monthly_counts.items():
            print(f"  {month}: {count} records")
        
        # Recommendations
        print("\n=== RECOMMENDATIONS ===")
        
        if null_zones > 0 or null_grids > 0:
            print("• Address geocoding issues:")
            print("  - Review address format and quality")
            print("  - Check geocoding service configuration")
            print("  - Consider manual geocoding for problematic addresses")
        
        if len(invalid_7day) > 0 if 'invalid_7day' in locals() else False:
            print("• Review 7-day cycle assignment logic")
        
        if len(invalid_28day) > 0 if 'invalid_28day' in locals() else False:
            print("• Review 28-day cycle assignment logic")
            
        print("• For map export issues:")
        print("  - Use updated map_export.py with null zone filtering")
        print("  - Verify ArcGIS Pro symbology handling")
        print("  - Check coordinate system configuration")
        
        print("• For chart accuracy:")
        print("  - Use updated chart_export.py with proper cycle filtering")
        print("  - Verify date/time parsing")
        print("  - Validate cycle assignment rules")
        
        return True
        
    except Exception as e:
        print(f"Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python data_validation.py <cad_csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    success = validate_cad_data(csv_file)
    
    if not success:
        sys.exit(1)
    
    print("\n=== VALIDATION COMPLETE ===")

if __name__ == "__main__":
    main()
