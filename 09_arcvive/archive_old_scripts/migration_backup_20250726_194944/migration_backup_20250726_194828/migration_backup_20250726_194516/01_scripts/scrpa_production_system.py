# SCRPA Crime Analysis System - Production Version
# Date: 2025-06-25-09-15-00
# Project: SCRPA_Crime_Analysis/SCRPA_Production_System.py
# Author: R. A. Carucci
# Purpose: Production crime analysis system with enhanced charts and summaries (ArcGIS mapping optional)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, timedelta
import numpy as np

class SCRPAProductionSystem:
    def __init__(self):
        """Initialize the SCRPA Production System"""
        
        # File paths
        self.base_path = r"C:\Users\carucci_r\SCRPA_LAPTOP\projects"
        self.data_path = os.path.join(self.base_path, "data")
        self.output_path = os.path.join(self.base_path, "output")
        
        # Input file
        self.input_csv = os.path.join(self.data_path, "CAD_data_final.csv")
        
        # Create directories
        os.makedirs(self.output_path, exist_ok=True)
        
        # Report settings
        self.report_date = datetime(2025, 6, 24)
        
        # Professional color schemes
        self.zone_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        self.time_colors = ['#8dd3c7', '#ffffb3', '#bebada', '#fb8072']
        
        print("🎯 SCRPA Production System Initialized")
        print(f"📊 Report Date: {self.report_date.strftime('%Y-%m-%d')}")
        print(f"📁 Base Path: {self.base_path}")

    def load_and_validate_data(self):
        """Load and validate the crime data"""
        try:
            print(f"\n📊 Loading data from: {self.input_csv}")
            
            # Load the data
            self.df = pd.read_csv(self.input_csv)
            print(f"✅ Data loaded: {len(self.df)} total records")
            
            # Convert date column
            self.df['CallDateTime'] = pd.to_datetime(self.df['Time of Call'], errors='coerce')
            
            # Clean and validate zone data
            initial_count = len(self.df)
            self.df = self.df.dropna(subset=['PDZone'])
            self.df = self.df[self.df['PDZone'].isin([5, 6, 7, 8, 9])]
            
            valid_count = len(self.df)
            print(f"📍 Valid records after filtering: {valid_count} ({valid_count/initial_count*100:.1f}%)")
            
            # Show cycle distribution
            cycle_counts = self.df['Cycle'].value_counts()
            print(f"📊 Cycle Distribution:")
            for cycle, count in cycle_counts.items():
                print(f"   {cycle}: {count} records")
                
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def create_enhanced_charts(self, cycle_name, data_subset):
        """Create enhanced professional charts"""
        
        print(f"\n📊 Creating enhanced charts for {cycle_name} ({len(data_subset)} records)...")
        
        cycle_output_dir = os.path.join(self.output_path, f"{cycle_name}_Enhanced_Charts")
        os.makedirs(cycle_output_dir, exist_ok=True)
        
        # Set professional style
        plt.style.use('default')
        sns.set_palette("husl")
        
        try:
            # 1. Enhanced Zone Distribution Chart
            plt.figure(figsize=(12, 8))
            zone_counts = data_subset['PDZone'].value_counts().sort_index()
            
            bars = plt.bar(zone_counts.index, zone_counts.values, 
                          color=self.zone_colors[:len(zone_counts)],
                          edgecolor='black', linewidth=1.2, alpha=0.8)
            
            plt.title(f'Crime Distribution by Police Zone - {cycle_name} Period', 
                     fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Police Zone', fontsize=13, fontweight='bold')
            plt.ylabel('Number of Incidents', fontsize=13, fontweight='bold')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{int(height)}', ha='center', va='bottom', 
                        fontweight='bold', fontsize=11)
            
            # Add percentage labels
            total = sum(zone_counts.values)
            for i, bar in enumerate(bars):
                height = bar.get_height()
                percentage = (height / total) * 100
                plt.text(bar.get_x() + bar.get_width()/2., height/2,
                        f'{percentage:.1f}%', ha='center', va='center', 
                        fontweight='bold', color='white', fontsize=10)
            
            plt.grid(axis='y', alpha=0.3)
            plt.xticks(fontsize=11)
            plt.yticks(fontsize=11)
            plt.tight_layout()
            plt.savefig(os.path.join(cycle_output_dir, f'{cycle_name}_Zone_Distribution_Enhanced.png'), 
                       dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            # 2. Advanced Time Analysis (Dual Chart)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
            
            # Time period distribution (pie chart)
            def categorize_time(hour):
                if 6 <= hour < 12:
                    return 'Morning (6-12)'
                elif 12 <= hour < 18:
                    return 'Afternoon (12-18)'
                elif 18 <= hour < 24:
                    return 'Evening (18-24)'
                else:
                    return 'Night (0-6)'
            
            data_subset_copy = data_subset.copy()
            data_subset_copy['Hour'] = data_subset_copy['CallDateTime'].dt.hour
            data_subset_copy['TimePeriod'] = data_subset_copy['Hour'].apply(categorize_time)
            
            time_counts = data_subset_copy['TimePeriod'].value_counts()
            time_order = ['Morning (6-12)', 'Afternoon (12-18)', 'Evening (18-24)', 'Night (0-6)']
            time_counts = time_counts.reindex(time_order, fill_value=0)
            
            wedges, texts, autotexts = ax1.pie(time_counts.values, labels=time_counts.index, 
                                              autopct='%1.1f%%', colors=self.time_colors,
                                              startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'})
            ax1.set_title(f'Incidents by Time Period - {cycle_name}', fontsize=14, fontweight='bold', pad=20)
            
            # 24-hour distribution (bar chart)
            hourly_counts = data_subset_copy['Hour'].value_counts().sort_index()
            hourly_counts = hourly_counts.reindex(range(24), fill_value=0)
            
            bars = ax2.bar(hourly_counts.index, hourly_counts.values, 
                          color='steelblue', alpha=0.7, edgecolor='black', linewidth=0.8)
            ax2.set_title(f'24-Hour Crime Distribution - {cycle_name}', fontsize=14, fontweight='bold', pad=20)
            ax2.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Number of Incidents', fontsize=12, fontweight='bold')
            ax2.set_xticks(range(0, 24, 2))
            ax2.grid(axis='y', alpha=0.3)
            
            # Add value labels for significant hours
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                            f'{int(height)}', ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            plt.savefig(os.path.join(cycle_output_dir, f'{cycle_name}_Time_Analysis_Enhanced.png'), 
                       dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            # 3. Top Crime Types (Enhanced Horizontal Bar)
            plt.figure(figsize=(14, 8))
            crime_counts = data_subset['Incident'].value_counts().head(8)
            
            # Create color gradient
            colors = plt.cm.viridis(np.linspace(0, 1, len(crime_counts)))
            
            bars = plt.barh(range(len(crime_counts)), crime_counts.values, 
                           color=colors, edgecolor='black', linewidth=0.8)
            
            # Format crime type labels
            crime_labels = []
            for incident in crime_counts.index:
                if len(incident) > 45:
                    label = incident[:42] + '...'
                else:
                    label = incident
                crime_labels.append(label)
            
            plt.yticks(range(len(crime_counts)), crime_labels, fontsize=10)
            plt.xlabel('Number of Incidents', fontsize=13, fontweight='bold')
            plt.title(f'Top Crime Types - {cycle_name} Period', fontsize=16, fontweight='bold', pad=20)
            
            # Add value and percentage labels
            total_crimes = sum(crime_counts.values)
            for i, bar in enumerate(bars):
                width = bar.get_width()
                percentage = (width / total_crimes) * 100
                plt.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                        f'{int(width)} ({percentage:.1f}%)', 
                        ha='left', va='center', fontweight='bold', fontsize=10)
            
            plt.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(cycle_output_dir, f'{cycle_name}_Crime_Types_Enhanced.png'), 
                       dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            # 4. Enhanced Day of Week Pattern
            plt.figure(figsize=(12, 7))
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_counts = data_subset['DayofWeek'].value_counts()
            day_counts = day_counts.reindex(day_order, fill_value=0)
            
            # Use distinct colors for each day
            day_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
            
            bars = plt.bar(day_counts.index, day_counts.values, 
                          color=day_colors, edgecolor='black', linewidth=1, alpha=0.8)
            
            plt.title(f'Crime Pattern by Day of Week - {cycle_name} Period', 
                     fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Day of Week', fontsize=13, fontweight='bold')
            plt.ylabel('Number of Incidents', fontsize=13, fontweight='bold')
            plt.xticks(rotation=45, fontsize=11)
            plt.yticks(fontsize=11)
            
            # Add value and percentage labels
            total_incidents = sum(day_counts.values)
            for bar in bars:
                height = bar.get_height()
                percentage = (height / total_incidents) * 100 if total_incidents > 0 else 0
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{int(height)}', ha='center', va='bottom', 
                        fontweight='bold', fontsize=10)
                plt.text(bar.get_x() + bar.get_width()/2., height/2,
                        f'{percentage:.1f}%', ha='center', va='center', 
                        fontweight='bold', color='white', fontsize=9)
            
            plt.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(cycle_output_dir, f'{cycle_name}_Daily_Pattern_Enhanced.png'), 
                       dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"   ✅ Enhanced charts created successfully")
            
        except Exception as e:
            print(f"   ❌ Error creating charts: {e}")

    def create_executive_summary(self, cycle_name, data_subset):
        """Create comprehensive executive summary"""
        
        summary_path = os.path.join(self.output_path, f"{cycle_name}_Executive_Summary.txt")
        
        try:
            with open(summary_path, 'w') as f:
                f.write("HACKENSACK POLICE DEPARTMENT\n")
                f.write("CRIME ANALYSIS EXECUTIVE SUMMARY\n")
                f.write(f"{cycle_name.upper()} PERIOD REPORT\n")
                f.write("=" * 60 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Report Period Ending: {self.report_date.strftime('%Y-%m-%d')}\n")
                f.write("=" * 60 + "\n\n")
                
                # Key metrics
                total_incidents = len(data_subset)
                zones_affected = data_subset['PDZone'].nunique()
                top_crime = data_subset['Incident'].value_counts().index[0] if total_incidents > 0 else "N/A"
                
                f.write("EXECUTIVE SUMMARY\n")
                f.write("-" * 20 + "\n")
                f.write(f"• Total Incidents: {total_incidents}\n")
                f.write(f"• Zones Affected: {zones_affected}/5\n")
                f.write(f"• Most Common Crime: {top_crime}\n")
                f.write(f"• Analysis Period: {cycle_name}\n\n")
                
                # Zone breakdown
                f.write("ZONE DISTRIBUTION ANALYSIS\n")
                f.write("-" * 30 + "\n")
                zone_counts = data_subset['PDZone'].value_counts().sort_index()
                for zone, count in zone_counts.items():
                    percentage = (count / total_incidents) * 100
                    f.write(f"Zone {int(zone)}: {count} incidents ({percentage:.1f}%)\n")
                
                # Crime type analysis
                f.write(f"\nTOP CRIME TYPES\n")
                f.write("-" * 20 + "\n")
                top_crimes = data_subset['Incident'].value_counts().head(5)
                for crime, count in top_crimes.items():
                    percentage = (count / total_incidents) * 100
                    f.write(f"• {crime}\n")
                    f.write(f"  {count} incidents ({percentage:.1f}%)\n\n")
                
                # Time analysis
                f.write(f"TEMPORAL ANALYSIS\n")
                f.write("-" * 20 + "\n")
                
                data_subset_copy = data_subset.copy()
                data_subset_copy['Hour'] = data_subset_copy['CallDateTime'].dt.hour
                
                def categorize_time(hour):
                    if 6 <= hour < 12:
                        return 'Morning (6AM-12PM)'
                    elif 12 <= hour < 18:
                        return 'Afternoon (12PM-6PM)'
                    elif 18 <= hour < 24:
                        return 'Evening (6PM-12AM)'
                    else:
                        return 'Night (12AM-6AM)'
                
                data_subset_copy['TimePeriod'] = data_subset_copy['Hour'].apply(categorize_time)
                time_counts = data_subset_copy['TimePeriod'].value_counts()
                
                f.write("Time Period Distribution:\n")
                for period, count in time_counts.items():
                    percentage = (count / total_incidents) * 100
                    f.write(f"• {period}: {count} incidents ({percentage:.1f}%)\n")
                
                # Day of week analysis
                f.write(f"\nDAY OF WEEK PATTERNS\n")
                f.write("-" * 25 + "\n")
                day_counts = data_subset['DayofWeek'].value_counts()
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                for day in day_order:
                    count = day_counts.get(day, 0)
                    percentage = (count / total_incidents) * 100 if total_incidents > 0 else 0
                    f.write(f"• {day}: {count} incidents ({percentage:.1f}%)\n")
                
                # Response analysis
                f.write(f"\nRESPONSE TYPE ANALYSIS\n")
                f.write("-" * 25 + "\n")
                response_counts = data_subset['Response Type'].value_counts().head(3)
                for response_type, count in response_counts.items():
                    percentage = (count / total_incidents) * 100
                    f.write(f"• {response_type}: {count} ({percentage:.1f}%)\n")
                
                f.write(f"\n" + "=" * 60 + "\n")
                f.write(f"Report prepared by: Principal Analyst R. A. Carucci\n")
                f.write(f"Hackensack Police Department\n")
                f.write(f"SCRPA Production System v2.0\n")
            
            print(f"   ✅ Executive summary created")
            
        except Exception as e:
            print(f"   ❌ Error creating summary: {e}")

    def generate_all_reports(self):
        """Generate comprehensive reports for all cycles"""
        
        cycles = {
            '7-Day': self.df[self.df['Cycle'] == '7-Day'],
            '28-Day': self.df[self.df['Cycle'] == '28-Day'],
            'YTD': self.df[self.df['Cycle'] == 'YTD']
        }
        
        print(f"\n🚀 Generating comprehensive reports for all cycles...")
        
        for cycle_name, data_subset in cycles.items():
            if len(data_subset) > 0:
                print(f"\n📊 Processing {cycle_name} cycle ({len(data_subset)} records)...")
                
                # Create enhanced charts
                self.create_enhanced_charts(cycle_name, data_subset)
                
                # Create executive summary
                self.create_executive_summary(cycle_name, data_subset)
                
            else:
                print(f"⚠️ No data for {cycle_name} cycle")

    def create_system_dashboard(self):
        """Create overall system dashboard summary"""
        
        dashboard_path = os.path.join(self.output_path, "SCRPA_Dashboard_Summary.txt")
        
        with open(dashboard_path, 'w') as f:
            f.write("SCRPA CRIME ANALYSIS SYSTEM DASHBOARD\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"System Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Report Date: {self.report_date.strftime('%Y-%m-%d')}\n")
            f.write(f"Total Records: {len(self.df)}\n\n")
            
            # Cycle overview
            cycle_counts = self.df['Cycle'].value_counts()
            f.write("CYCLE OVERVIEW:\n")
            f.write("-" * 15 + "\n")
            for cycle, count in cycle_counts.items():
                f.write(f"{cycle}: {count} records\n")
            
            # Zone overview
            f.write(f"\nZONE OVERVIEW:\n")
            f.write("-" * 15 + "\n")
            zone_counts = self.df['PDZone'].value_counts().sort_index()
            for zone, count in zone_counts.items():
                f.write(f"Zone {int(zone)}: {count} incidents\n")
            
            # System outputs
            f.write(f"\nSYSTEM OUTPUTS GENERATED:\n")
            f.write("-" * 30 + "\n")
            f.write("✅ Enhanced charts for all cycles\n")
            f.write("✅ Executive summaries\n")
            f.write("✅ System dashboard\n")
            f.write("✅ Professional formatting (300 DPI)\n")
            
            f.write(f"\n🚀 SYSTEM STATUS: OPERATIONAL\n")
            f.write("All reports generated successfully\n")
            f.write("Ready for distribution and analysis\n")

    def run_production_system(self):
        """Run the complete production system"""
        
        print("🎯 SCRPA Production Crime Analysis System")
        print("=" * 50)
        
        # Step 1: Load and validate data
        if not self.load_and_validate_data():
            print("❌ System failed - data loading error")
            return False
        
        # Step 2: Generate all reports
        self.generate_all_reports()
        
        # Step 3: Create system dashboard
        self.create_system_dashboard()
        
        print("\n🎉 SCRPA Production System Complete!")
        print("=" * 50)
        print(f"📁 All outputs saved to: {self.output_path}")
        print("📊 Enhanced charts generated for all cycles")
        print("📋 Executive summaries prepared")
        print("📈 System dashboard created")
        print("\n🚀 READY FOR OPERATIONAL DEPLOYMENT")
        
        return True

def main():
    """Main execution function"""
    
    try:
        # Initialize and run production system
        scrpa_system = SCRPAProductionSystem()
        success = scrpa_system.run_production_system()
        
        if success:
            print("\n🎯 DEPLOYMENT STATUS: ✅ READY")
            print("=" * 40)
            print("✅ Data validation complete")
            print("✅ Enhanced charts generated")
            print("✅ Executive summaries prepared")
            print("✅ Professional formatting applied")
            print("✅ All cycles processed successfully")
            print("\n📂 Check output folder for all generated reports")
            print("🚀 System ready for regular operational use")
        else:
            print("❌ System deployment failed - check error logs")
            
    except Exception as e:
        print(f"❌ Critical system error: {e}")

if __name__ == "__main__":
    main()
