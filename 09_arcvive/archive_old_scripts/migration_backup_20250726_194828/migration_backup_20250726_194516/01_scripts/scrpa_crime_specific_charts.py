# SCRPA Crime Analysis System - Crime-Specific Time Charts
# Date: 2025-06-25-09-30-00
# Project: SCRPA_Crime_Analysis/SCRPA_Crime_Specific_Charts.py
# Author: R. A. Carucci
# Purpose: Generate time-of-day charts for each individual crime type across all cycles

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, timedelta
import numpy as np

class SCRPACrimeSpecificCharts:
    def __init__(self):
        """Initialize the SCRPA Crime-Specific Charts System"""
        
        # File paths
        self.base_path = r"C:\Users\carucci_r\SCRPA_LAPTOP\projects"
        self.data_path = os.path.join(self.base_path, "data")
        self.output_path = os.path.join(self.base_path, "output")
        
        # Input file
        self.input_csv = os.path.join(self.data_path, "CAD_data_final.csv")
        
        # Create directories
        os.makedirs(self.output_path, exist_ok=True)
        
        # Time period definitions
        self.time_periods = [
            ('00:00-03:59', 'Early Morning'),
            ('04:00-07:59', 'Morning'),
            ('08:00-11:59', 'Midday'),
            ('12:00-15:59', 'Afternoon'),
            ('16:00-19:59', 'Evening'),
            ('20:00-23:59', 'Night')
        ]
        
        # Color scheme for cycles
        self.cycle_colors = {
            '7-Day': '#90EE90',    # Light green
            '28-Day': '#FF6B6B',   # Light red/coral
            'YTD': '#87CEEB'       # Light blue
        }
        
        print("🎯 SCRPA Crime-Specific Charts System Initialized")
        print(f"📁 Base Path: {self.base_path}")

    def load_and_validate_data(self):
        """Load and validate the crime data"""
        try:
            print(f"\n📊 Loading data from: {self.input_csv}")
            
            # Load the data
            self.df = pd.read_csv(self.input_csv)
            print(f"✅ Data loaded: {len(self.df)} total records")
            
            # Convert date column and extract hour
            self.df['CallDateTime'] = pd.to_datetime(self.df['Time of Call'], errors='coerce')
            self.df['Hour'] = self.df['CallDateTime'].dt.hour
            
            # Clean data
            self.df = self.df.dropna(subset=['PDZone', 'Hour'])
            self.df = self.df[self.df['PDZone'].isin([5, 6, 7, 8, 9])]
            
            print(f"📍 Valid records: {len(self.df)}")
            
            # Show crime type distribution
            print(f"\n📋 Crime Types Found:")
            crime_counts = self.df['Incident'].value_counts()
            for crime, count in crime_counts.head(10).items():
                print(f"   {crime}: {count} incidents")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def categorize_time_period(self, hour):
        """Categorize hour into time periods"""
        if 0 <= hour < 4:
            return 'Early Morning'
        elif 4 <= hour < 8:
            return 'Morning'
        elif 8 <= hour < 12:
            return 'Midday'
        elif 12 <= hour < 16:
            return 'Afternoon'
        elif 16 <= hour < 20:
            return 'Evening'
        else:
            return 'Night'

    def create_crime_specific_time_chart(self, crime_type, output_dir):
        """Create time-of-day chart for a specific crime type across all cycles"""
        
        try:
            # Filter data for this crime type
            crime_data = self.df[self.df['Incident'] == crime_type].copy()
            
            if len(crime_data) == 0:
                print(f"   ⚠️ No data for {crime_type}")
                return
            
            # Add time period categorization
            crime_data['TimePeriod'] = crime_data['Hour'].apply(self.categorize_time_period)
            
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Define time period order
            time_order = ['Early Morning', 'Morning', 'Midday', 'Afternoon', 'Evening', 'Night']
            
            # Prepare data for each cycle
            cycles = ['7-Day', '28-Day', 'YTD']
            x_positions = np.arange(len(time_order))
            bar_width = 0.25
            
            # Create bars for each cycle
            for i, cycle in enumerate(cycles):
                cycle_data = crime_data[crime_data['Cycle'] == cycle]
                
                if len(cycle_data) > 0:
                    # Count incidents by time period
                    time_counts = cycle_data['TimePeriod'].value_counts()
                    time_counts = time_counts.reindex(time_order, fill_value=0)
                    
                    # Create bars
                    bars = plt.bar(x_positions + i * bar_width, time_counts.values, 
                                  bar_width, label=cycle, 
                                  color=self.cycle_colors[cycle], 
                                  edgecolor='black', linewidth=0.8, alpha=0.8)
                    
                    # Add value labels on bars
                    for bar in bars:
                        height = bar.get_height()
                        if height > 0:
                            plt.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                                    f'{int(height)}', ha='center', va='bottom', 
                                    fontweight='bold', fontsize=9)
            
            # Customize chart
            plt.title(f'{crime_type} - Calls by Time of Day', 
                     fontsize=14, fontweight='bold', pad=20)
            plt.xlabel('Time of Day', fontsize=12, fontweight='bold')
            plt.ylabel('Count', fontsize=12, fontweight='bold')
            
            # Set x-axis
            plt.xticks(x_positions + bar_width, time_order, rotation=45, ha='right')
            
            # Add legend
            plt.legend(title='Period', title_fontsize=10, fontsize=9)
            
            # Add grid
            plt.grid(axis='y', alpha=0.3)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save chart
            safe_filename = crime_type.replace('/', '_').replace('\\', '_').replace(':', '-')
            safe_filename = safe_filename.replace('|', '_').replace('<', '_').replace('>', '_')
            
            output_file = os.path.join(output_dir, f'{safe_filename}_Time_Chart.png')
            plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"   ✅ Chart created for: {crime_type}")
            
        except Exception as e:
            print(f"   ❌ Error creating chart for {crime_type}: {e}")

    def generate_all_crime_time_charts(self):
        """Generate time-of-day charts for all crime types"""
        
        print(f"\n🚀 Generating crime-specific time charts...")
        
        # Create output directory
        charts_dir = os.path.join(self.output_path, "Crime_Specific_Time_Charts")
        os.makedirs(charts_dir, exist_ok=True)
        
        # Get all unique crime types
        crime_types = self.df['Incident'].unique()
        print(f"📊 Found {len(crime_types)} unique crime types")
        
        # Generate chart for each crime type
        for i, crime_type in enumerate(crime_types, 1):
            print(f"\n📈 Processing {i}/{len(crime_types)}: {crime_type}")
            self.create_crime_specific_time_chart(crime_type, charts_dir)
        
        print(f"\n🎉 All crime-specific time charts generated!")
        print(f"📁 Charts saved to: {charts_dir}")

    def create_summary_overview(self):
        """Create summary overview of all charts generated"""
        
        summary_path = os.path.join(self.output_path, "Crime_Time_Charts_Summary.txt")
        
        with open(summary_path, 'w') as f:
            f.write("SCRPA CRIME-SPECIFIC TIME ANALYSIS SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Records Analyzed: {len(self.df)}\n\n")
            
            # Crime type breakdown
            f.write("CRIME TYPES ANALYZED:\n")
            f.write("-" * 25 + "\n")
            crime_counts = self.df['Incident'].value_counts()
            for crime, count in crime_counts.items():
                f.write(f"• {crime}: {count} incidents\n")
            
            f.write(f"\nTIME PERIODS USED:\n")
            f.write("-" * 20 + "\n")
            for time_range, period_name in self.time_periods:
                f.write(f"• {time_range} = {period_name}\n")
            
            f.write(f"\nCYCLE COLOR CODING:\n")
            f.write("-" * 20 + "\n")
            f.write("• 7-Day: Light Green\n")
            f.write("• 28-Day: Light Red/Coral\n")
            f.write("• YTD: Light Blue\n")
            
            f.write(f"\nCHARTS GENERATED:\n")
            f.write("-" * 20 + "\n")
            f.write(f"• Total charts: {len(crime_counts)}\n")
            f.write("• Format: PNG (300 DPI)\n")
            f.write("• Style: Multi-cycle comparison bars\n")
            
            f.write(f"\n" + "=" * 50 + "\n")
            f.write("Hackensack Police Department\n")
            f.write("Principal Analyst: R. A. Carucci\n")
            f.write("SCRPA Crime-Specific Analysis System\n")

    def run_system(self):
        """Run the complete crime-specific charts system"""
        
        print("🎯 SCRPA Crime-Specific Time Charts System")
        print("=" * 50)
        
        # Step 1: Load data
        if not self.load_and_validate_data():
            print("❌ System failed - data loading error")
            return False
        
        # Step 2: Generate all crime-specific time charts
        self.generate_all_crime_time_charts()
        
        # Step 3: Create summary
        self.create_summary_overview()
        
        print("\n🎉 SCRPA Crime-Specific Charts Complete!")
        print("=" * 50)
        print("✅ Individual time charts generated for each crime type")
        print("✅ Multi-cycle comparison (7-Day, 28-Day, YTD)")
        print("✅ Professional formatting with value labels")
        print("✅ Summary documentation created")
        print(f"\n📁 All charts saved to: {self.output_path}/Crime_Specific_Time_Charts/")
        
        return True

def main():
    """Main execution function"""
    
    try:
        # Initialize and run system
        chart_system = SCRPACrimeSpecificCharts()
        success = chart_system.run_system()
        
        if success:
            print("\n🎯 SUCCESS: Crime-Specific Time Charts Generated")
            print("=" * 50)
            print("✅ Each crime type now has its own time-of-day chart")
            print("✅ Charts show 7-Day, 28-Day, and YTD comparisons")
            print("✅ Professional formatting ready for reports")
            print("\n📊 You now have charts like your Sexual Offenses example")
            print("📂 Check the Crime_Specific_Time_Charts folder")
        else:
            print("❌ System failed - check error messages above")
            
    except Exception as e:
        print(f"❌ Critical error: {e}")

if __name__ == "__main__":
    main()
