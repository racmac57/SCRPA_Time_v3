# 🕒 2025-06-30-12-41-52
# SCRPA_Time_Project/hybrid_chart_manager.py
# Author: R. A. Carucci
# Purpose: Hybrid chart system - ArcGIS primary, Power BI backup

import os
import glob
import shutil
import logging
from datetime import date, datetime
from config import get_crime_type_folder, get_standardized_filename

print("✅ hybrid_chart_manager.py loaded - ArcGIS primary, Power BI backup")

def check_chart_availability(crime_type, target_date=None):
    """Check what chart sources are available"""
    
    if target_date is None:
        report_date = date.today()
    else:
        if isinstance(target_date, str):
            report_date = datetime.strptime(target_date, "%Y_%m_%d").date()
        else:
            report_date = target_date
    
    target_date_str = report_date.strftime("%Y_%m_%d")
    crime_output_folder = get_crime_type_folder(crime_type, target_date_str)
    filename_prefix = get_standardized_filename(crime_type)
    
    # Check for different chart sources
    chart_sources = {
        'arcgis_python': os.path.join(crime_output_folder, f"{filename_prefix}_Chart.png"),
        'powerbi_export': os.path.join(crime_output_folder, f"{filename_prefix}_Chart_PowerBI.png"),
        'powerbi_manual': os.path.join(crime_output_folder, f"{filename_prefix}_Chart_Manual.png")
    }
    
    availability = {}
    for source, path in chart_sources.items():
        availability[source] = {
            'exists': os.path.exists(path),
            'path': path,
            'age_hours': get_file_age_hours(path) if os.path.exists(path) else None
        }
    
    return availability

def get_file_age_hours(file_path):
    """Get file age in hours"""
    try:
        import time
        file_time = os.path.getmtime(file_path)
        current_time = time.time()
        age_seconds = current_time - file_time
        return age_seconds / 3600  # Convert to hours
    except:
        return None

def ensure_chart_exists(crime_type, target_date=None, force_python=False):
    """Ensure a chart exists, using fallback hierarchy"""
    
    print(f"\n📊 Ensuring chart exists for {crime_type}...")
    
    availability = check_chart_availability(crime_type, target_date)
    
    # Print availability status
    print("📋 Chart source availability:")
    for source, info in availability.items():
        status = "✅" if info['exists'] else "❌"
        age = f" ({info['age_hours']:.1f}h old)" if info['age_hours'] else ""
        print(f"  {status} {source.replace('_', ' ').title()}{age}")
    
    # Decision hierarchy for chart source
    if force_python:
        print("🔧 Force Python mode - attempting ArcGIS chart generation...")
        try:
            from chart_export import export_chart
            success = export_chart(crime_type, target_date)
            if success:
                print("✅ ArcGIS Python chart generated successfully")
                return True, 'arcgis_python'
            else:
                print("❌ ArcGIS Python chart failed - falling back to Power BI")
        except Exception as e:
            print(f"❌ ArcGIS Python failed: {e}")
    
    # Check if ArcGIS chart exists and is recent (< 24 hours)
    if availability['arcgis_python']['exists'] and (availability['arcgis_python']['age_hours'] or 0) < 24:
        print("✅ Using existing ArcGIS Python chart (recent)")
        return True, 'arcgis_python'
    
    # Check if Power BI export exists and is recent
    if availability['powerbi_export']['exists'] and (availability['powerbi_export']['age_hours'] or 0) < 24:
        print("✅ Using Power BI exported chart (recent)")
        return True, 'powerbi_export'
    
    # Check if manual Power BI chart exists
    if availability['powerbi_manual']['exists']:
        print("✅ Using manual Power BI chart")
        return True, 'powerbi_manual'
    
    # Try to generate ArcGIS chart
    print("🔄 No recent charts found - attempting ArcGIS generation...")
    try:
        from chart_export import export_chart
        success = export_chart(crime_type, target_date)
        if success:
            print("✅ ArcGIS chart generated successfully")
            return True, 'arcgis_python'
    except Exception as e:
        print(f"❌ ArcGIS generation failed: {e}")
    
    # Final fallback - prompt for Power BI export
    print("⚠️ No charts available - need Power BI backup")
    print(f"📋 Action needed:")
    print(f"  1. Open Power BI SCRPA project")
    print(f"  2. Export {crime_type} chart as image")
    print(f"  3. Save as: {availability['powerbi_export']['path']}")
    
    return False, 'none'

def ensure_all_charts_exist(target_date=None, force_python=False):
    """Ensure charts exist for all crime types"""
    
    crime_types = ["MV Theft", "Burglary - Auto", "Burglary - Comm & Res", "Robbery", "Sexual Offenses"]
    
    print(f"\n🎯 Ensuring charts exist for all {len(crime_types)} crime types...")
    
    results = {}
    missing_charts = []
    
    for i, crime_type in enumerate(crime_types, 1):
        print(f"\n[{i}/{len(crime_types)}] Checking {crime_type}...")
        
        success, source = ensure_chart_exists(crime_type, target_date, force_python)
        results[crime_type] = {'success': success, 'source': source}
        
        if not success:
            missing_charts.append(crime_type)
    
    # Summary
    successful = sum(1 for result in results.values() if result['success'])
    print(f"\n📊 Chart Status Summary: {successful}/{len(crime_types)} charts available")
    
    for crime_type, result in results.items():
        if result['success']:
            status = "✅"
            source = result['source'].replace('_', ' ').title()
            print(f"  {status} {crime_type} ({source})")
        else:
            print(f"  ❌ {crime_type} (MISSING)")
    
    if missing_charts:
        print(f"\n⚠️ Action Required - Missing charts for:")
        for crime_type in missing_charts:
            print(f"  • {crime_type}")
        print(f"\n📋 Power BI Backup Process:")
        print(f"  1. Open Power BI SCRPA project")
        print(f"  2. Refresh data (Ctrl+R)")
        print(f"  3. Export missing charts as images")
        print(f"  4. Save to appropriate crime folders")
        print(f"  5. Re-run this script")
    
    return results

def create_chart_status_report(target_date=None):
    """Create a detailed status report of all charts"""
    
    crime_types = ["MV Theft", "Burglary - Auto", "Burglary - Comm & Res", "Robbery", "Sexual Offenses"]
    
    if target_date is None:
        report_date = date.today()
    else:
        if isinstance(target_date, str):
            report_date = datetime.strptime(target_date, "%Y_%m_%d").date()
        else:
            report_date = target_date
    
    print(f"\n📋 CHART STATUS REPORT - {report_date.strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    for crime_type in crime_types:
        print(f"\n🔍 {crime_type}:")
        availability = check_chart_availability(crime_type, target_date)
        
        for source, info in availability.items():
            status = "✅ Available" if info['exists'] else "❌ Missing"
            age = f" ({info['age_hours']:.1f}h old)" if info['age_hours'] else ""
            source_name = source.replace('_', ' ').title()
            print(f"  {status:<12} {source_name}{age}")

# Example usage functions
def quick_chart_check():
    """Quick check of chart status for today"""
    print("🚀 Quick Chart Status Check")
    create_chart_status_report()

def force_regenerate_charts():
    """Force regeneration of all charts using Python/ArcGIS"""
    print("🔧 Force Regenerating All Charts...")
    ensure_all_charts_exist(force_python=True)

def backup_charts_check():
    """Check if Power BI backup charts are needed"""
    print("💾 Backup Charts Check...")
    results = ensure_all_charts_exist(force_python=False)
    
    missing = [crime for crime, result in results.items() if not result['success']]
    if missing:
        print(f"\n💡 Recommendation: Create Power BI backup charts for {len(missing)} crime types")
    else:
        print(f"\n✅ All charts available - no backup needed")