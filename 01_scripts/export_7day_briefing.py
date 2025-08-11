# File: export_7day_briefing.py
# Purpose: Export detailed 7-day incidents for Patrol Captain briefing

import pandas as pd
from datetime import datetime, timedelta
import os

def export_7day_briefing():
    """Export detailed 7-day incidents with all fields needed for briefing template."""
    
    # Load the standardized data
    data_path = "C:/Users/carucci_r/OneDrive - City of Hackensack/01_DataSources/SCRPA_Time_v2/04_powerbi/"
    df = pd.read_csv(data_path + "rms_data_standardized.csv")
    
    # Debug: Print actual column names
    print("Available columns in CSV:")
    print(df.columns.tolist())
    print(f"\nTotal records: {len(df)}")
    print(f"Period distribution: {df['Period'].value_counts().to_dict()}")
    
    # Filter for 7-day period only
    seven_day_incidents = df[df['Period'] == '7-Day'].copy()
    print(f"\n7-Day incidents found: {len(seven_day_incidents)}")
    
    # Use actual column names from your standardized CSV
    available_columns = [
        'Case_Number', 'Incident_Date', 'Incident_Time', 'Crime_Category',
        'All_Incidents', 'Location', 'Block', 'Grid', 'Narrative', 
        'Vehicle_1', 'Vehicle_2', 'Squad', 'Officer_Of_Record'
    ]
    
    # Only select columns that actually exist
    existing_columns = [col for col in available_columns if col in df.columns]
    print(f"\nUsing columns: {existing_columns}")
    
    # Create briefing export with available fields
    briefing_export = seven_day_incidents[existing_columns].copy()
    
    # Sort chronologically (oldest to newest)
    if 'Incident_Date' in briefing_export.columns:
        briefing_export['Incident_Date'] = pd.to_datetime(briefing_export['Incident_Date'])
        briefing_export = briefing_export.sort_values('Incident_Date')
        
        # Format datetime for display
        time_col = briefing_export['Incident_Time'].fillna('00:00') if 'Incident_Time' in briefing_export.columns else '00:00'
        briefing_export['DateTime_Display'] = briefing_export['Incident_Date'].dt.strftime('%m/%d/%y') + ' ' + time_col.astype(str)
    
    # Export to CSV
    output_file = data_path + "7_day_briefing_incidents.csv"
    briefing_export.to_csv(output_file, index=False)
    
    print(f"\n7-Day Briefing Export Complete:")
    print(f"- File: {output_file}")
    print(f"- Records: {len(briefing_export)}")
    if 'Crime_Category' in briefing_export.columns:
        print(f"- Crime Categories: {briefing_export['Crime_Category'].value_counts().to_dict()}")
    
    return output_file

if __name__ == "__main__":
    export_7day_briefing()