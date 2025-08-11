# SCRPA Crime Analysis System - Charts Only Test Version
# Date: 2025-06-25-09-00-00
# Project: SCRPA_Crime_Analysis/SCRPA_Test_Charts_Only.py
# Author: R. A. Carucci
# Purpose: Test version focusing only on chart generation (no ArcGIS)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, timedelta
import numpy as np

class SCRPAChartsTest:
    def __init__(self):
        """Initialize the SCRPA Charts Test System"""
        
        # File paths
        self.base_path = r"C:\Users\carucci_r\SCRPA_LAPTOP\projects"
        self.data_path = os.path.join(self.base_path, "data")
        self.output_path = os.path.join(self.base_path, "output")
        
        # Input file
        self.input_csv = os.path.join(self.data_path, "CAD_data_final.csv")
        
        # Create output directory
        os.makedirs(self.output_path, exist_ok=True)
        
        # Color schemes
        self.zone_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        self.time_colors = ['#8dd3c7', '#ffffb3', '#bebada', '#fb8072']
        
        print("🎯 SCRPA Charts Test System Initialized")
        print(f"📁 Data Path: {self.data_path}")
        print(f"📁 Output Path: {self.output_path}")

    def load_and_validate_data(self):
        """Load and validate the crime data"""
        try:
            print(f"\n📊 Loading data from: {self.input_csv}")
            
            # Check if file exists
            if not os.path.exists(self.input_csv):
                print(f"❌ File not found: {self.input_csv}")
                return False
            
            # Load the data
            self.df = pd.read_csv(self.input_csv)
            print(f"✅ Data loaded: {len(self.df)} total records")
            
            # Show column names
            print(f"📋 Columns: {list(self.df.columns)}")
            
            # Convert date column
            self.df['CallDateTime'] = pd.to_datetime(self.df['Time of Call'], errors='coerce')
            print(f"📅 Date conversion complete")
            
            # Check for zone data
            print(f"🏁 Zone data preview:")
            print(self.df['PDZone'].value_counts().sort_index())
            
            # Check cycle distribution
            print(f"🔄 Cycle distribution:")
            cycle_counts = self.df['Cycle'].value_counts()
            for cycle, count in cycle_counts.items():
                print(f"   {cycle}: {count} records")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def create_test_charts(self, cycle_name, data_subset):
        """Create test charts for a specific cycle"""
        
        print(f"\n📊 Creating charts for {cycle_name} ({len(data_subset)} records)...")
        
        cycle_output_dir = os.path.join(self.output_path, f"{cycle_name}_Test_Charts")
        os.makedirs(cycle_output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('default')
        
        try:
            # 1. Zone Distribution Chart
            plt.figure(figsize=(10, 6))
            
            # Remove NaN zones and filter valid zones
            valid_data = data_subset.dropna(subset=['PDZone'])
            valid_data = valid_data[valid_data['PDZone'].isin([5, 6, 7, 8, 9])]
            
            if len(valid_data) > 0:
                zone_counts = valid_data['PDZone'].value_counts().sort_index()
                
                bars = plt.bar(zone_counts.index, zone_counts.values, 
                              color=self.zone_colors[:len(zone_counts)])
                
                plt.title(f'Crime Distribution by Zone - {cycle_name}', fontsize=14, fontweight='bold')
                plt.xlabel('Police Zone', fontweight='bold')
                plt.ylabel('Number of Incidents', fontweight='bold')
                
                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{int(height)}', ha='center', va='bottom')
                
                plt.grid(axis='y', alpha=0.3)
                plt.tight_layout()
                plt.savefig(os.path.join(cycle_output_dir, f'{cycle_name}_Zone_Distribution.png'), 
                           dpi=300, bbox_inches='tight')
                plt.close()
                print(f"   ✅ Zone distribution chart saved")
            else:
                print(f"   ⚠️ No valid zone data for {cycle_name}")
            
            # 2. Crime Types Chart
            plt.figure(figsize=(12, 6))
            
            if len(data_subset) > 0:
                crime_counts = data_subset['Incident'].value_counts().head(5)
                
                bars = plt.barh(range(len(crime_counts)), crime_counts.values, 
                               color=plt.cm.viridis(np.linspace(0, 1, len(crime_counts))))
                
                plt.yticks(range(len(crime_counts)), 
                          [incident[:40] + '...' if len(incident) > 40 else incident 
                           for incident in crime_counts.index])
                plt.xlabel('Number of Incidents', fontweight='bold')
                plt.title(f'Top Crime Types - {cycle_name}', fontsize=14, fontweight='bold')
                
                # Add value labels
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    plt.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                            f'{int(width)}', ha='left', va='center')
                
                plt.grid(axis='x', alpha=0.3)
                plt.tight_layout()
                plt.savefig(os.path.join(cycle_output_dir, f'{cycle_name}_Crime_Types.png'), 
                           dpi=300, bbox_inches='tight')
                plt.close()
                print(f"   ✅ Crime types chart saved")
            
            # 3. Day of Week Chart
            plt.figure(figsize=(10, 6))
            
            if len(data_subset) > 0:
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_counts = data_subset['DayofWeek'].value_counts()
                day_counts = day_counts.reindex(day_order, fill_value=0)
                
                bars = plt.bar(day_counts.index, day_counts.values, 
                              color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'])
                
                plt.title(f'Crime Pattern by Day of Week - {cycle_name}', fontsize=14, fontweight='bold')
                plt.xlabel('Day of Week', fontweight='bold')
                plt.ylabel('Number of Incidents', fontweight='bold')
                plt.xticks(rotation=45)
                
                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{int(height)}', ha='center', va='bottom')
                
                plt.grid(axis='y', alpha=0.3)
                plt.tight_layout()
                plt.savefig(os.path.join(cycle_output_dir, f'{cycle_name}_Daily_Pattern.png'), 
                           dpi=300, bbox_inches='tight')
                plt.close()
                print(f"   ✅ Daily pattern chart saved")
        
        except Exception as e:
            print(f"   ❌ Error creating charts for {cycle_name}: {e}")

    def run_test(self):
        """Run the test system"""
        
        print("🎯 SCRPA Charts Test System")
        print("=" * 40)
        
        # Step 1: Load data
        if not self.load_and_validate_data():
            print("❌ Test failed - data loading error")
            return False
        
        # Step 2: Generate charts for each cycle
        cycles = {
            '7-Day': self.df[self.df['Cycle'] == '7-Day'],
            '28-Day': self.df[self.df['Cycle'] == '28-Day'],
            'YTD': self.df[self.df['Cycle'] == 'YTD']
        }
        
        for cycle_name, data_subset in cycles.items():
            if len(data_subset) > 0:
                self.create_test_charts(cycle_name, data_subset)
            else:
                print(f"⚠️ No data for {cycle_name} cycle")
        
        print(f"\n🎉 Test Complete!")
        print(f"📁 Charts saved to: {self.output_path}")
        print("✅ System appears to be working correctly")
        
        return True

def main():
    """Main execution function"""
    
    try:
        # Initialize and run test
        test_system = SCRPAChartsTest()
        success = test_system.run_test()
        
        if success:
            print("\n🚀 NEXT STEPS:")
            print("=" * 30)
            print("1. Check output folder for generated charts")
            print("2. If charts look good, proceed with full system")
            print("3. Full system includes ArcGIS mapping components")
        else:
            print("❌ Test failed - check error messages above")
            
    except Exception as e:
        print(f"❌ Critical error: {e}")

if __name__ == "__main__":
    main()
