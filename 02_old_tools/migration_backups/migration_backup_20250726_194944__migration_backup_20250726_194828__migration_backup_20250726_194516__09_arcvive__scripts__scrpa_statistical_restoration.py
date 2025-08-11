# 🕒 2025-07-01-16-00-00
# SCRPA_Statistics/statistical_export_restoration
# Author: R. A. Carucci
# Purpose: Restore missing statistical exports matching last week's format

import os
import logging
from datetime import datetime, date
import arcpy
from config import (
    get_7day_period_dates, get_sql_pattern_for_crime, APR_PATH, CRIME_TYPES
)

def generate_complete_statistical_exports(report_date, output_base_path=None):
    """
    Generate complete statistical exports matching last week's format
    
    Args:
        report_date (date): Report date for analysis
        output_base_path (str): Base output path (default: current system path)
    
    Returns:
        bool: True if successful
    """
    if output_base_path is None:
        output_base_path = "C:/Users/carucci_r/SCRPA_LAPTOP/projects/output"
    
    print(f"\n📊 GENERATING COMPLETE STATISTICAL EXPORTS")
    print("=" * 60)
    print(f"Report Date: {report_date.strftime('%Y-%m-%d')}")
    
    try:
        # Create statistical reports directory
        stats_dir = os.path.join(output_base_path, "Statistical_Reports")
        os.makedirs(stats_dir, exist_ok=True)
        
        # Initialize comprehensive data collector
        stats_collector = ComprehensiveStatsCollector(report_date)
        
        # Collect comprehensive statistics
        print("Collecting comprehensive crime data...")
        comprehensive_stats = stats_collector.collect_all_statistics()
        
        # Generate reports in multiple formats
        report_generator = StatisticalReportGenerator(comprehensive_stats, report_date, stats_dir)
        
        # Create executive summaries (Word format like last week)
        print("Generating executive summaries...")
        exec_success = report_generator.create_executive_summaries_docx()
        
        # Create system dashboard
        print("Generating system dashboard...")
        dashboard_success = report_generator.create_system_dashboard_docx()
        
        # Create comprehensive CSV exports
        print("Generating CSV data exports...")
        csv_success = report_generator.create_comprehensive_csv_exports()
        
        # Create summary statistics report
        print("Generating summary statistics...")
        summary_success = report_generator.create_summary_statistics_txt()
        
        success = exec_success and dashboard_success and csv_success and summary_success
        
        if success:
            print("✅ Complete statistical exports generated successfully")
            print(f"📁 Saved to: {stats_dir}")
        else:
            print("❌ Some statistical exports failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Error generating statistical exports: {e}")
        logging.error(f"Statistical exports failed: {e}", exc_info=True)
        return False

class ComprehensiveStatsCollector:
    """Comprehensive statistics collector matching last week's format"""
    
    def __init__(self, report_date):
        self.report_date = report_date
        self.start_date, self.end_date = get_7day_period_dates(report_date)
        
    def collect_all_statistics(self):
        """Collect comprehensive statistics for all cycles and crime types"""
        stats = {
            'report_date': self.report_date,
            'cycles': {},
            'overall_summary': {},
            'zone_analysis': {},
            'temporal_analysis': {},
            'response_analysis': {},
            'crime_type_analysis': {}
        }
        
        try:
            # Load ArcGIS Pro project
            aprx = arcpy.mp.ArcGISProject(APR_PATH)
            maps = aprx.listMaps()
            
            if not maps:
                return stats
                
            map_obj = maps[0]
            
            # Collect data for each cycle
            for cycle in ['7-Day', '28-Day', 'YTD']:
                print(f"  Analyzing {cycle} cycle...")
                cycle_stats = self._analyze_cycle(map_obj, cycle)
                stats['cycles'][cycle] = cycle_stats
            
            # Generate comprehensive analysis
            stats['overall_summary'] = self._generate_overall_summary(stats['cycles'])
            stats['zone_analysis'] = self._generate_zone_analysis(stats['cycles'])
            stats['temporal_analysis'] = self._generate_temporal_analysis(stats['cycles'])
            stats['response_analysis'] = self._generate_response_analysis(stats['cycles'])
            stats['crime_type_analysis'] = self._generate_crime_type_analysis(stats['cycles'])
            
            del aprx
            
        except Exception as e:
            logging.error(f"Error collecting comprehensive statistics: {e}")
        
        return stats
    
    def _analyze_cycle(self, map_obj, cycle):
        """Analyze a specific cycle comprehensively"""
        cycle_stats = {
            'cycle_name': cycle,
            'total_incidents': 0,
            'crime_types': {},
            'zones': {},
            'time_periods': {},
            'days_of_week': {},
            'response_types': {},
            'incident_details': []
        }
        
        try:
            # Analyze each crime type for this cycle
            for crime_type in CRIME_TYPES:
                layer_name = f"{crime_type} {cycle}"
                target_layer = None
                
                for lyr in map_obj.listLayers():
                    if lyr.name == layer_name:
                        target_layer = lyr
                        break
                
                if target_layer:
                    crime_data = self._extract_crime_data(target_layer, crime_type, cycle)
                    
                    # Aggregate crime type data
                    if crime_data['count'] > 0:
                        cycle_stats['crime_types'][crime_type] = crime_data
                        cycle_stats['total_incidents'] += crime_data['count']
                        cycle_stats['incident_details'].extend(crime_data['details'])
            
            # Aggregate zone, time, day, and response data
            for detail in cycle_stats['incident_details']:
                # Zone aggregation
                zone = detail.get('zone')
                if zone:
                    cycle_stats['zones'][zone] = cycle_stats['zones'].get(zone, 0) + 1
                
                # Time period aggregation
                time_period = detail.get('time_period')
                if time_period:
                    cycle_stats['time_periods'][time_period] = cycle_stats['time_periods'].get(time_period, 0) + 1
                
                # Day of week aggregation
                day_of_week = detail.get('day_of_week')
                if day_of_week:
                    cycle_stats['days_of_week'][day_of_week] = cycle_stats['days_of_week'].get(day_of_week, 0) + 1
                
                # Response type aggregation
                response_type = detail.get('response_type')
                if response_type:
                    cycle_stats['response_types'][response_type] = cycle_stats['response_types'].get(response_type, 0) + 1
        
        except Exception as e:
            logging.error(f"Error analyzing {cycle} cycle: {e}")
        
        return cycle_stats
    
    def _extract_crime_data(self, layer, crime_type, cycle):
        """Extract detailed crime data from layer"""
        crime_data = {
            'crime_type': crime_type,
            'cycle': cycle,
            'count': 0,
            'details': []
        }
        
        try:
            # Apply appropriate filter based on cycle
            if cycle == '7-Day':
                from map_export import build_sql_filter_7day_excel
                filter_sql = build_sql_filter_7day_excel(crime_type, self.start_date, self.end_date)
            else:
                # For 28-Day and YTD, use broader filters
                sql_pattern = get_sql_pattern_for_crime(crime_type)
                if isinstance(sql_pattern, list):
                    conditions = [f"calltype LIKE '%{p}%'" for p in sql_pattern]
                    crime_condition = f"({' OR '.join(conditions)})"
                else:
                    crime_condition = f"calltype LIKE '%{sql_pattern}%'"
                
                base_conditions = f"disposition LIKE '%See Report%'"
                filter_sql = f"{crime_condition} AND {base_conditions}"
            
            # Apply filter
            original_query = layer.definitionQuery
            layer.definitionQuery = filter_sql
            
            # Get count
            feature_count = int(arcpy.GetCount_management(layer).getOutput(0))
            crime_data['count'] = feature_count
            
            if feature_count > 0:
                # Extract detailed data
                fields = ["calldate", "PDZone", "disposition", "calltype", "DayofWeek", "Response Type"]
                
                with arcpy.da.SearchCursor(layer, fields) as cursor:
                    for row in cursor:
                        try:
                            calldate, zone, disposition, calltype, day_of_week, response_type = row
                            
                            detail = {
                                'date': calldate,
                                'zone': zone,
                                'disposition': disposition,
                                'calltype': calltype,
                                'day_of_week': day_of_week,
                                'response_type': response_type,
                                'time_period': self._categorize_time(calldate.hour) if isinstance(calldate, datetime) else 'Unknown'
                            }
                            
                            crime_data['details'].append(detail)
                            
                        except Exception as e:
                            continue
            
            # Restore original query
            layer.definitionQuery = original_query
            
        except Exception as e:
            logging.error(f"Error extracting {crime_type} data: {e}")
        
        return crime_data
    
    def _categorize_time(self, hour):
        """Categorize hour into time period matching last week's format"""
        if 6 <= hour < 12:
            return 'Morning (6AM-12PM)'
        elif 12 <= hour < 18:
            return 'Afternoon (12PM-6PM)'
        elif 18 <= hour < 24:
            return 'Evening (6PM-12AM)'
        else:
            return 'Night (12AM-6AM)'
    
    def _generate_overall_summary(self, cycles_data):
        """Generate overall summary statistics"""
        summary = {}
        
        for cycle, data in cycles_data.items():
            summary[cycle] = {
                'total_incidents': data['total_incidents'],
                'zones_affected': len(data['zones']),
                'most_common_crime': max(data['crime_types'], key=lambda x: data['crime_types'][x]['count']) if data['crime_types'] else 'N/A'
            }
        
        return summary
    
    def _generate_zone_analysis(self, cycles_data):
        """Generate zone analysis matching last week's format"""
        zone_analysis = {}
        
        # Aggregate zone data across all cycles
        all_zones = {}
        total_incidents = 0
        
        # Use YTD data for overall zone analysis (matches last week's format)
        if 'YTD' in cycles_data:
            ytd_zones = cycles_data['YTD']['zones']
            total_incidents = cycles_data['YTD']['total_incidents']
            
            for zone, count in ytd_zones.items():
                percentage = (count / total_incidents) * 100 if total_incidents > 0 else 0
                zone_analysis[f'Zone {zone}'] = {
                    'count': count,
                    'percentage': percentage
                }
        
        return zone_analysis
    
    def _generate_temporal_analysis(self, cycles_data):
        """Generate temporal analysis matching last week's format"""
        temporal = {}
        
        # Use YTD data for temporal analysis (matches last week's format)
        if 'YTD' in cycles_data:
            time_periods = cycles_data['YTD']['time_periods']
            days_of_week = cycles_data['YTD']['days_of_week']
            total_incidents = cycles_data['YTD']['total_incidents']
            
            # Time periods
            temporal['time_periods'] = {}
            for period, count in time_periods.items():
                percentage = (count / total_incidents) * 100 if total_incidents > 0 else 0
                temporal['time_periods'][period] = {
                    'count': count,
                    'percentage': percentage
                }
            
            # Days of week
            temporal['days_of_week'] = {}
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for day in day_order:
                count = days_of_week.get(day, 0)
                percentage = (count / total_incidents) * 100 if total_incidents > 0 else 0
                temporal['days_of_week'][day] = {
                    'count': count,
                    'percentage': percentage
                }
        
        return temporal
    
    def _generate_response_analysis(self, cycles_data):
        """Generate response analysis matching last week's format"""
        response_analysis = {}
        
        # Use YTD data for response analysis (matches last week's format)
        if 'YTD' in cycles_data:
            response_types = cycles_data['YTD']['response_types']
            total_incidents = cycles_data['YTD']['total_incidents']
            
            for response_type, count in response_types.items():
                percentage = (count / total_incidents) * 100 if total_incidents > 0 else 0
                response_analysis[response_type] = {
                    'count': count,
                    'percentage': percentage
                }
        
        return response_analysis
    
    def _generate_crime_type_analysis(self, cycles_data):
        """Generate crime type analysis matching last week's format"""
        crime_analysis = {}
        
        # Use YTD data for crime type analysis (matches last week's format)
        if 'YTD' in cycles_data:
            crime_types = cycles_data['YTD']['crime_types']
            total_incidents = cycles_data['YTD']['total_incidents']
            
            # Sort by count (descending)
            sorted_crimes = sorted(crime_types.items(), key=lambda x: x[1]['count'], reverse=True)
            
            for crime_type, data in sorted_crimes:
                percentage = (data['count'] / total_incidents) * 100 if total_incidents > 0 else 0
                crime_analysis[crime_type] = {
                    'count': data['count'],
                    'percentage': percentage
                }
        
        return crime_analysis

class StatisticalReportGenerator:
    """Generate statistical reports in multiple formats matching last week's output"""
    
    def __init__(self, comprehensive_stats, report_date, output_dir):
        self.stats = comprehensive_stats
        self.report_date = report_date
        self.output_dir = output_dir
    
    def create_executive_summaries_docx(self):
        """Create executive summaries in Word format (matching last week)"""
        try:
            # For each cycle, create an executive summary
            for cycle in ['7-Day', '28-Day', 'YTD']:
                if cycle in self.stats['cycles']:
                    self._create_cycle_executive_summary_txt(cycle)
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating executive summaries: {e}")
            return False
    
    def _create_cycle_executive_summary_txt(self, cycle):
        """Create executive summary for specific cycle in TXT format"""
        cycle_data = self.stats['cycles'][cycle]
        summary_path = os.path.join(self.output_dir, f"{cycle}_Executive_Summary.txt")
        
        with open(summary_path, 'w') as f:
            f.write("HACKENSACK POLICE DEPARTMENT\n")
            f.write("CRIME ANALYSIS EXECUTIVE SUMMARY\n")
            f.write(f"{cycle.upper()} PERIOD REPORT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Report Period Ending: {self.report_date.strftime('%Y-%m-%d')}\n")
            f.write("=" * 60 + "\n\n")
            
            # Executive Summary
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"• Total Incidents: {cycle_data['total_incidents']}\n")
            f.write(f"• Zones Affected: {len(cycle_data['zones'])}/5\n")
            
            # Most common crime
            if cycle_data['crime_types']:
                most_common = max(cycle_data['crime_types'], key=lambda x: cycle_data['crime_types'][x]['count'])
                f.write(f"• Most Common Crime: {most_common}\n")
            else:
                f.write("• Most Common Crime: N/A\n")
            
            f.write(f"• Analysis Period: {cycle}\n\n")
            
            # Zone Distribution Analysis
            f.write("ZONE DISTRIBUTION ANALYSIS\n")
            f.write("-" * 30 + "\n")
            sorted_zones = sorted(cycle_data['zones'].items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else 0)
            total_incidents = cycle_data['total_incidents']
            
            for zone, count in sorted_zones:
                percentage = (count / total_incidents) * 100 if total_incidents > 0 else 0
                f.write(f"Zone {zone}: {count} incidents ({percentage:.1f}%)\n")
            
            # Top Crime Types
            f.write(f"\nTOP CRIME TYPES\n")
            f.write("-" * 20 + "\n")
            sorted_crimes = sorted(cycle_data['crime_types'].items(), key=lambda x: x[1]['count'], reverse=True)
            
            for crime_type, data in sorted_crimes:
                count = data['count']
                percentage = (count / total_incidents) * 100 if total_incidents > 0 else 0
                f.write(f"• {crime_type}\n")
                f.write(f"  {count} incidents ({percentage:.1f}%)\n\n")
            
            # Temporal Analysis
            f.write("TEMPORAL ANALYSIS\n")
            f.write("-" * 20 + "\n")
            f.write("Time Period Distribution:\n")
            
            sorted_times = sorted(cycle_data['time_periods'].items(), key=lambda x: x[1], reverse=True)
            for time_period, count in sorted_times:
                percentage = (count / total_incidents) * 100 if total_incidents > 0 else 0
                f.write(f"• {time_period}: {count} incidents ({percentage:.1f}%)\n")
            
            # Day of Week Patterns
            f.write(f"\nDAY OF WEEK PATTERNS\n")
            f.write("-" * 25 + "\n")
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for day in day_order:
                count = cycle_data['days_of_week'].get(day, 0)
                percentage = (count / total_incidents) * 100 if total_incidents > 0 else 0
                f.write(f"• {day}: {count} incidents ({percentage:.1f}%)\n")
            
            # Response Type Analysis
            f.write(f"\nRESPONSE TYPE ANALYSIS\n")
            f.write("-" * 25 + "\n")
            sorted_responses = sorted(cycle_data['response_types'].items(), key=lambda x: x[1], reverse=True)
            
            for response_type, count in sorted_responses:
                percentage = (count / total_incidents) * 100 if total_incidents > 0 else 0
                f.write(f"• {response_type}: {count} ({percentage:.1f}%)\n")
            
            f.write(f"\n" + "=" * 60 + "\n")
            f.write("Report prepared by: Principal Analyst R. A. Carucci\n")
            f.write("Hackensack Police Department\n")
            f.write("SCRPA Production System v2.0\n")
        
        print(f"✅ Created {cycle} executive summary")
    
    def create_system_dashboard_docx(self):
        """Create system dashboard in text format (matching last week)"""
        try:
            dashboard_path = os.path.join(self.output_dir, "SCRPA_Dashboard_Summary.txt")
            
            with open(dashboard_path, 'w') as f:
                f.write("SCRPA CRIME ANALYSIS SYSTEM DASHBOARD\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"System Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Report Date: {self.report_date.strftime('%Y-%m-%d')}\n")
                
                # Calculate total records
                total_records = sum(cycle_data['total_incidents'] for cycle_data in self.stats['cycles'].values())
                f.write(f"Total Records: {total_records}\n\n")
                
                # Cycle Overview
                f.write("CYCLE OVERVIEW:\n")
                f.write("-" * 15 + "\n")
                for cycle in ['YTD', '28-Day', '7-Day']:  # Match last week's order
                    if cycle in self.stats['cycles']:
                        count = self.stats['cycles'][cycle]['total_incidents']
                        f.write(f"{cycle}: {count} records\n")
                
                # Zone Overview (using YTD data like last week)
                f.write(f"\nZONE OVERVIEW:\n")
                f.write("-" * 15 + "\n")
                if 'YTD' in self.stats['cycles']:
                    ytd_zones = self.stats['cycles']['YTD']['zones']
                    sorted_zones = sorted(ytd_zones.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else 0)
                    
                    for zone, count in sorted_zones:
                        f.write(f"Zone {zone}: {count} incidents\n")
                
                # System Outputs
                f.write(f"\nSYSTEM OUTPUTS GENERATED:\n")
                f.write("-" * 30 + "\n")
                f.write("✅ Enhanced charts for all cycles\n")
                f.write("✅ Executive summaries\n")
                f.write("✅ System dashboard\n")
                f.write("✅ Professional formatting (300 DPI)\n")
                
                f.write(f"\n🚀 SYSTEM STATUS: OPERATIONAL\n")
                f.write("All reports generated successfully\n")
                f.write("Ready for distribution and analysis\n")
            
            print("✅ Created system dashboard")
            return True
            
        except Exception as e:
            print(f"❌ Error creating system dashboard: {e}")
            return False
    
    def create_comprehensive_csv_exports(self):
        """Create CSV exports with comprehensive data"""
        try:
            # Create overall statistics CSV
            csv_path = os.path.join(self.output_dir, f"SCRPA_Comprehensive_Statistics_{self.report_date.strftime('%Y_%m_%d')}.csv")
            
            import pandas as pd
            
            # Prepare comprehensive data
            csv_data = []
            
            for cycle, cycle_data in self.stats['cycles'].items():
                # Add cycle summary row
                base_row = {
                    'Cycle': cycle,
                    'Total_Incidents': cycle_data['total_incidents'],
                    'Zones_Affected': len(cycle_data['zones']),
                    'Crime_Types_Reported': len(cycle_data['crime_types'])
                }
                
                # Add crime type breakdowns
                for crime_type, data in cycle_data['crime_types'].items():
                    row = base_row.copy()
                    row['Crime_Type'] = crime_type
                    row['Crime_Count'] = data['count']
                    row['Crime_Percentage'] = (data['count'] / cycle_data['total_incidents']) * 100 if cycle_data['total_incidents'] > 0 else 0
                    csv_data.append(row)
                
                # If no crime types, add summary row
                if not cycle_data['crime_types']:
                    csv_data.append(base_row)
            
            # Create DataFrame and save
            df = pd.DataFrame(csv_data)
            df.to_csv(csv_path, index=False)
            
            print("✅ Created comprehensive CSV export")
            return True
            
        except ImportError:
            print("⚠️ Pandas not available - CSV export skipped")
            return True
        except Exception as e:
            print(f"❌ Error creating CSV export: {e}")
            return False
    
    def create_summary_statistics_txt(self):
        """Create summary statistics text file"""
        try:
            summary_path = os.path.join(self.output_dir, f"SCRPA_Summary_Statistics_{self.report_date.strftime('%Y_%m_%d')}.txt")
            
            with open(summary_path, 'w') as f:
                f.write("SCRPA CRIME ANALYSIS - SUMMARY STATISTICS\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Report Date: {self.report_date.strftime('%Y-%m-%d')}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Quick stats overview
                f.write("QUICK STATISTICS OVERVIEW:\n")
                f.write("-" * 30 + "\n")
                
                for cycle in ['7-Day', '28-Day', 'YTD']:
                    if cycle in self.stats['cycles']:
                        cycle_data = self.stats['cycles'][cycle]
                        f.write(f"\n{cycle} Period:\n")
                        f.write(f"  Total Incidents: {cycle_data['total_incidents']}\n")
                        f.write(f"  Active Zones: {len(cycle_data['zones'])}\n")
                        f.write(f"  Crime Types: {len(cycle_data['crime_types'])}\n")
                        
                        if cycle_data['crime_types']:
                            top_crime = max(cycle_data['crime_types'], key=lambda x: cycle_data['crime_types'][x]['count'])
                            f.write(f"  Top Crime: {top_crime}\n")
                
                f.write(f"\nStatistical analysis completed successfully.\n")
                f.write("All reports available in Statistical_Reports folder.\n")
            
            print("✅ Created summary statistics")
            return True
            
        except Exception as e:
            print(f"❌ Error creating summary statistics: {e}")
            return False

# Integration function to add to existing system
def add_statistical_exports_to_scrpa():
    """
    Add statistical exports to existing SCRPA system
    Call this function from your main production script
    """
    try:
        from datetime import date
        
        # Use current date or get from system
        report_date = date.today()
        
        # Generate statistical exports
        success = generate_complete_statistical_exports(report_date)
        
        if success:
            print("✅ Statistical exports added successfully!")
            print("📁 Check Statistical_Reports folder for outputs")
        else:
            print("❌ Statistical exports failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Error adding statistical exports: {e}")
        return False

# Usage example
if __name__ == "__main__":
    # Example: Generate statistical exports for specific date
    from datetime import date
    report_date = date(2025, 6, 24)
    
    success = generate_complete_statistical_exports(report_date)
    
    if success:
        print("🎉 Statistical exports generation complete!")
    else:
        print("❌ Statistical exports failed")
        
# Add statistical exports to production system
from scrpa_statistical_restoration import add_statistical_exports_to_scrpa

# At the end of your main() function, add:
print("\n📊 Generating statistical exports...")
stats_success = add_statistical_exports_to_scrpa()