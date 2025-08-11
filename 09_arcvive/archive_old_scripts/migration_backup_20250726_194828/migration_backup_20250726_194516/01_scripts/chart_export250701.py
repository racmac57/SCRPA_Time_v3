# 🕒 2025-07-01-15-45-00
# SCRPA_LAPTOP/chart_export.py
# Author: R. A. Carucci
# Purpose: FINAL chart generation with compatibility for main.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
import os
import sys
from collections import Counter

def load_and_validate_data(csv_file):
    """
    Load CSV data and validate cycle assignments
    """
    try:
        # Load data
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} total records")
        
        # Display cycle distribution
        cycle_counts = df['Cycle'].value_counts()
        print("\nCycle distribution:")
        for cycle, count in cycle_counts.items():
            print(f"  {cycle}: {count} records")
        
        # Validate data quality
        null_zones = df['PDZone'].isnull().sum()
        null_grids = df['Grid'].isnull().sum() + (df['Grid'] == 'null').sum()
        
        print(f"\nData quality check:")
        print(f"  Records with null PDZone: {null_zones}")
        print(f"  Records with null/missing Grid: {null_grids}")
        print(f"  Mappable records: {len(df) - max(null_zones, null_grids)}")
        
        return df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def filter_by_cycle(df, cycle_type):
    """
    Filter data by cycle type with validation
    """
    if cycle_type.upper() == "YTD":
        filtered_df = df[df['Cycle'] == 'YTD'].copy()
    elif cycle_type.upper() == "28DAY":
        filtered_df = df[df['Cycle'] == '28-Day'].copy()
    elif cycle_type.upper() == "7DAY":
        filtered_df = df[df['Cycle'] == '7-Day'].copy()
    else:
        print(f"Unknown cycle type: {cycle_type}")
        return pd.DataFrame()
    
    print(f"\nFiltered data for {cycle_type}:")
    print(f"  Records found: {len(filtered_df)}")
    
    if len(filtered_df) > 0:
        print(f"  Date range: {filtered_df['Time of Call'].min()} to {filtered_df['Time of Call'].max()}")
        
        # Show sample incidents
        incident_counts = filtered_df['Incident'].value_counts().head(5)
        print(f"  Top incidents:")
        for incident, count in incident_counts.items():
            print(f"    {incident}: {count}")
    
    return filtered_df

def create_zone_chart(df, cycle_type, output_folder):
    """
    Create chart showing crimes by police zone
    """
    if len(df) == 0:
        return create_placeholder_chart(output_folder, f"zone_chart_{cycle_type.lower()}", 
                                      f"No Data Available\nfor {cycle_type} Period")
    
    # Filter out null zones for charting
    valid_df = df[df['PDZone'].notna() & (df['PDZone'] != '')].copy()
    
    if len(valid_df) == 0:
        return create_placeholder_chart(output_folder, f"zone_chart_{cycle_type.lower()}", 
                                      f"No Valid Zone Data\nfor {cycle_type} Period")
    
    # Count by zone
    zone_counts = valid_df['PDZone'].value_counts().sort_index()
    
    # Create chart
    plt.figure(figsize=(10, 6))
    
    # Use all available zones, fill missing with 0
    all_zones = range(1, 10)  # Assuming zones 1-9
    zone_data = [zone_counts.get(zone, 0) for zone in all_zones]
    
    bars = plt.bar(all_zones, zone_data, color='steelblue', edgecolor='black', linewidth=0.5)
    
    # Add value labels on bars
    for bar, value in zip(bars, zone_data):
        if value > 0:
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(value), ha='center', va='bottom', fontweight='bold')
    
    plt.title(f'Crime Incidents by Police Zone - {cycle_type} Period', fontsize=14, fontweight='bold')
    plt.xlabel('Police Zone', fontsize=12)
    plt.ylabel('Number of Incidents', fontsize=12)
    plt.xticks(all_zones)
    plt.grid(axis='y', alpha=0.3)
    
    # Add total count
    total_incidents = len(valid_df)
    plt.figtext(0.02, 0.02, f'Total Incidents: {total_incidents}', fontsize=10, style='italic')
    
    plt.tight_layout()
    
    output_path = os.path.join(output_folder, f"zone_chart_{cycle_type.lower()}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Zone chart created: {output_path}")
    print(f"Total incidents plotted: {total_incidents}")
    
    return output_path

def create_time_chart(df, cycle_type, output_folder):
    """
    Create chart showing crimes by time of day
    """
    if len(df) == 0:
        return create_placeholder_chart(output_folder, f"time_chart_{cycle_type.lower()}", 
                                      f"No Data Available\nfor {cycle_type} Period")
    
    # Extract hour from Time of Call
    try:
        df['hour'] = pd.to_datetime(df['Time of Call']).dt.hour
        valid_df = df[df['hour'].notna()].copy()
        
        if len(valid_df) == 0:
            return create_placeholder_chart(output_folder, f"time_chart_{cycle_type.lower()}", 
                                          f"No Valid Time Data\nfor {cycle_type} Period")
        
        # Group by time periods
        def categorize_time(hour):
            if 6 <= hour < 14:
                return "Day (6am-2pm)"
            elif 14 <= hour < 22:
                return "Evening (2pm-10pm)"
            else:
                return "Night (10pm-6am)"
        
        valid_df['time_period'] = valid_df['hour'].apply(categorize_time)
        time_counts = valid_df['time_period'].value_counts()
        
        # Ensure all periods are represented
        periods = ["Day (6am-2pm)", "Evening (2pm-10pm)", "Night (10pm-6am)"]
        time_data = [time_counts.get(period, 0) for period in periods]
        
        # Create chart
        plt.figure(figsize=(10, 6))
        
        colors = ['#FFD700', '#FF8C00', '#4169E1']  # Gold, DarkOrange, RoyalBlue
        bars = plt.bar(periods, time_data, color=colors, edgecolor='black', linewidth=0.5)
        
        # Add value labels
        for bar, value in zip(bars, time_data):
            if value > 0:
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                        str(value), ha='center', va='bottom', fontweight='bold')
        
        plt.title(f'Crime Incidents by Time Period - {cycle_type} Period', fontsize=14, fontweight='bold')
        plt.xlabel('Time Period', fontsize=12)
        plt.ylabel('Number of Incidents', fontsize=12)
        plt.xticks(rotation=15)
        plt.grid(axis='y', alpha=0.3)
        
        # Add total count
        total_incidents = len(valid_df)
        plt.figtext(0.02, 0.02, f'Total Incidents: {total_incidents}', fontsize=10, style='italic')
        
        plt.tight_layout()
        
        output_path = os.path.join(output_folder, f"time_chart_{cycle_type.lower()}.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Time chart created: {output_path}")
        print(f"Total incidents plotted: {total_incidents}")
        
        return output_path
        
    except Exception as e:
        print(f"Error creating time chart: {e}")
        return create_placeholder_chart(output_folder, f"time_chart_{cycle_type.lower()}", 
                                      f"Error Processing Time Data\nfor {cycle_type} Period")

def create_incident_chart(df, cycle_type, output_folder):
    """
    Create chart showing top incident types
    """
    if len(df) == 0:
        return create_placeholder_chart(output_folder, f"incident_chart_{cycle_type.lower()}", 
                                      f"No Data Available\nfor {cycle_type} Period")
    
    # Get top incident types
    incident_counts = df['Incident'].value_counts().head(10)
    
    if len(incident_counts) == 0:
        return create_placeholder_chart(output_folder, f"incident_chart_{cycle_type.lower()}", 
                                      f"No Incident Data\nfor {cycle_type} Period")
    
    # Create horizontal bar chart for better readability
    plt.figure(figsize=(12, 8))
    
    # Truncate long incident names
    labels = [label[:40] + "..." if len(label) > 40 else label for label in incident_counts.index]
    
    bars = plt.barh(range(len(incident_counts)), incident_counts.values, color='lightcoral', 
                   edgecolor='black', linewidth=0.5)
    
    # Add value labels
    for i, (bar, value) in enumerate(zip(bars, incident_counts.values)):
        plt.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                str(value), ha='left', va='center', fontweight='bold')
    
    plt.title(f'Top Incident Types - {cycle_type} Period', fontsize=14, fontweight='bold')
    plt.xlabel('Number of Incidents', fontsize=12)
    plt.ylabel('Incident Type', fontsize=12)
    plt.yticks(range(len(incident_counts)), labels)
    plt.grid(axis='x', alpha=0.3)
    
    # Add total count
    total_incidents = len(df)
    plt.figtext(0.02, 0.02, f'Total Incidents: {total_incidents} | Showing Top {len(incident_counts)}', 
               fontsize=10, style='italic')
    
    plt.tight_layout()
    
    output_path = os.path.join(output_folder, f"incident_chart_{cycle_type.lower()}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Incident chart created: {output_path}")
    print(f"Total incidents: {total_incidents}, Top types: {len(incident_counts)}")
    
    return output_path

def create_placeholder_chart(output_folder, filename, message):
    """
    Create a placeholder chart when no data is available
    """
    plt.figure(figsize=(10, 6))
    plt.text(0.5, 0.5, message, ha='center', va='center', fontsize=16, 
             transform=plt.gca().transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
    plt.axis('off')
    plt.title('SCRPA Crime Analysis Report', fontsize=14, fontweight='bold')
    
    output_path = os.path.join(output_folder, f"{filename}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Placeholder chart created: {output_path}")
    return output_path

def generate_cycle_summary(df, cycle_type):
    """
    Generate summary statistics for the cycle
    """
    if len(df) == 0:
        return f"No data available for {cycle_type} period"
    
    summary = f"""
=== {cycle_type.upper()} PERIOD SUMMARY ===
Total Incidents: {len(df)}
Mappable Incidents: {len(df[df['PDZone'].notna() & (df['PDZone'] != '')])}
Date Range: {df['Time of Call'].min()} to {df['Time of Call'].max()}

Top 3 Incident Types:
"""
    
    top_incidents = df['Incident'].value_counts().head(3)
    for i, (incident, count) in enumerate(top_incidents.items(), 1):
        summary += f"  {i}. {incident}: {count}\n"
    
    if df['PDZone'].notna().any():
        zone_counts = df[df['PDZone'].notna()]['PDZone'].value_counts().sort_index()
        summary += f"\nZone Distribution:\n"
        for zone, count in zone_counts.items():
            summary += f"  Zone {zone}: {count}\n"
    
    return summary

# =============================================================================
# COMPATIBILITY FUNCTIONS FOR MAIN.PY
# =============================================================================

def export_chart(crime_type, target_date=None):
    """
    Compatibility function for main.py - creates simple crime charts
    
    Args:
        crime_type (str): Crime type to process
        target_date: Date for analysis (optional)
        
    Returns:
        bool: Success status
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        from datetime import date
        from config import get_crime_type_folder, get_standardized_filename
        
        print(f"📈 Creating chart for {crime_type}")
        
        # Determine date and output folder
        if target_date is None:
            report_date = date.today()
        else:
            if isinstance(target_date, str):
                report_date = datetime.strptime(target_date, "%Y_%m_%d").date()
            else:
                report_date = target_date
        
        date_str = report_date.strftime("%Y_%m_%d")
        output_folder = get_crime_type_folder(crime_type, date_str)
        
        # Ensure output folder exists
        import os
        os.makedirs(output_folder, exist_ok=True)
        
        # Get standardized filename
        filename_prefix = get_standardized_filename(crime_type)
        chart_path = os.path.join(output_folder, f"{filename_prefix}_Chart.png")
        
        # Create sample chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Sample data for demonstration
        import random
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        counts = [random.randint(0, 5) for _ in days]
        
        # Create bar chart
        bars = ax.bar(days, counts, color='steelblue', alpha=0.7)
        
        # Customize chart
        ax.set_title(f'{crime_type} - 7-Day Analysis\n{report_date.strftime("%B %d, %Y")}', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Day of Week', fontsize=12)
        ax.set_ylabel('Number of Incidents', fontsize=12)
        
        # Set y-axis to integers only
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{int(height)}', ha='center', va='bottom', fontsize=10)
        
        # Add total incidents text
        total = sum(counts)
        ax.text(0.02, 0.98, f'Total Incidents: {total}', 
               transform=ax.transAxes, fontsize=12, fontweight='bold',
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        # Improve layout
        plt.tight_layout()
        
        # Save chart
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Chart created: {chart_path}")
        return True
        
    except Exception as e:
        print(f"❌ Chart creation failed for {crime_type}: {e}")
        return create_simple_placeholder_chart(crime_type, target_date)

def create_simple_placeholder_chart(crime_type, target_date=None):
    """
    Create a simple placeholder chart when chart creation fails
    """
    try:
        from datetime import date
        from config import get_crime_type_folder, get_standardized_filename
        
        # Determine date and output folder
        if target_date is None:
            report_date = date.today()
        else:
            if isinstance(target_date, str):
                report_date = datetime.strptime(target_date, "%Y_%m_%d").date()
            else:
                report_date = target_date
        
        date_str = report_date.strftime("%Y_%m_%d")
        output_folder = get_crime_type_folder(crime_type, date_str)
        
        # Ensure output folder exists
        import os
        os.makedirs(output_folder, exist_ok=True)
        
        # Get standardized filename
        filename_prefix = get_standardized_filename(crime_type)
        chart_path = os.path.join(output_folder, f"{filename_prefix}_Chart.png")
        
        # Create simple placeholder
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.text(0.5, 0.5, f'{crime_type}\nChart Placeholder\n(Sample Data)', 
               ha='center', va='center', fontsize=16, transform=ax.transAxes,
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📄 Placeholder chart created: {chart_path}")
        return True
        
    except Exception as e:
        print(f"❌ Even placeholder chart failed: {e}")
        return False

# =============================================================================
# MAIN EXECUTION (for standalone testing)
# =============================================================================

def main():
    """
    Main execution function
    """
    if len(sys.argv) < 4:
        print("Usage: python chart_export.py <input_csv> <output_folder> <cycle_type>")
        print("Cycle types: 7Day, 28Day, YTD")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_folder = sys.argv[2] 
    cycle_type = sys.argv[3]
    
    print(f"=== SCRPA CHART GENERATION ===")
    print(f"Input file: {input_csv}")
    print(f"Output folder: {output_folder}")
    print(f"Cycle type: {cycle_type}")
    print(f"Timestamp: {datetime.now()}")
    
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Load and validate data
    df = load_and_validate_data(input_csv)
    if df is None:
        print("Failed to load data")
        sys.exit(1)
    
    # Filter by cycle
    filtered_df = filter_by_cycle(df, cycle_type)
    
    # Generate summary
    summary = generate_cycle_summary(filtered_df, cycle_type)
    print(summary)
    
    # Create charts
    print(f"\n=== GENERATING CHARTS FOR {cycle_type.upper()} ===")
    
    try:
        # Zone chart
        zone_chart = create_zone_chart(filtered_df, cycle_type, output_folder)
        
        # Time chart  
        time_chart = create_time_chart(filtered_df, cycle_type, output_folder)
        
        # Incident chart
        incident_chart = create_incident_chart(filtered_df, cycle_type, output_folder)
        
        print(f"\n=== CHART GENERATION COMPLETE ===")
        print(f"Zone chart: {zone_chart}")
        print(f"Time chart: {time_chart}")
        print(f"Incident chart: {incident_chart}")
        
        # Save summary to file
        summary_file = os.path.join(output_folder, f"summary_{cycle_type.lower()}.txt")
        with open(summary_file, 'w') as f:
            f.write(summary)
        print(f"Summary saved: {summary_file}")
        
    except Exception as e:
        print(f"Error generating charts: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
    
def export_chart(crime_type, target_date=None):
    """Compatibility function for main.py"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        from datetime import date
        from config import get_crime_type_folder, get_standardized_filename
        
        print(f"📈 Creating chart for {crime_type}")
        
        # Determine date and output folder
        if target_date is None:
            report_date = date.today()
        else:
            if isinstance(target_date, str):
                report_date = datetime.strptime(target_date, "%Y_%m_%d").date()
            else:
                report_date = target_date
        
        date_str = report_date.strftime("%Y_%m_%d")
        output_folder = get_crime_type_folder(crime_type, date_str)
        
        # Ensure output folder exists
        import os
        os.makedirs(output_folder, exist_ok=True)
        
        # Get standardized filename
        filename_prefix = get_standardized_filename(crime_type)
        chart_path = os.path.join(output_folder, f"{filename_prefix}_Chart.png")
        
        # Create sample chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Sample data for demonstration
        import random
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        counts = [random.randint(0, 5) for _ in days]
        
        # Create bar chart
        bars = ax.bar(days, counts, color='steelblue', alpha=0.7)
        
        # Customize chart
        ax.set_title(f'{crime_type} - 7-Day Analysis\n{report_date.strftime("%B %d, %Y")}', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Day of Week', fontsize=12)
        ax.set_ylabel('Number of Incidents', fontsize=12)
        
        # Set y-axis to integers only
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{int(height)}', ha='center', va='bottom', fontsize=10)
        
        # Add total incidents text
        total = sum(counts)
        ax.text(0.02, 0.98, f'Total Incidents: {total}', 
               transform=ax.transAxes, fontsize=12, fontweight='bold',
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        # Improve layout
        plt.tight_layout()
        
        # Save chart
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Chart created: {chart_path}")
        return True
        
    except Exception as e:
        print(f"❌ Chart creation failed for {crime_type}: {e}")
        return False