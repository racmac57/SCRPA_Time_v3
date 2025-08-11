#!/usr/bin/env python3
"""
Manual Export File Analysis Script - Simplified version
"""

import os
import re
from pathlib import Path
from datetime import datetime

def main():
    print("🔍 EXPORT FILE ANALYSIS")
    print("=" * 50)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Scan CAD exports
    cad_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA")
    cad_exports = []
    if cad_dir.exists():
        cad_exports = [f for f in cad_dir.iterdir() if f.is_file()]
    
    # Scan RMS exports
    rms_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA")
    rms_exports = []
    if rms_dir.exists():
        rms_exports = [f for f in rms_dir.iterdir() if f.is_file()]
    
    # Print inventory
    print("EXPORT FILE INVENTORY")
    print("-" * 30)
    print(f"CAD Exports: {len(cad_exports)} files")
    for export in cad_exports:
        print(f"  📄 {export.name}")
    
    print(f"\nRMS Exports: {len(rms_exports)} files")
    for export in rms_exports:
        print(f"  📄 {export.name}")
    
    # Analyze patterns
    all_files = cad_exports + rms_exports
    dates_found = set()
    file_types = set()
    
    # Pattern: YYYY_MM_DD_HH_MM_SS_TYPE.ext
    timestamp_pattern = r'(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(.+)\.(.+)'
    # Pattern: TYPE_Export_YYYY_MM_DD.ext
    simple_pattern = r'(.+)_Export_(\d{4})_(\d{2})_(\d{2})\.(.+)'
    
    for file_path in all_files:
        filename = file_path.name
        file_types.add(file_path.suffix)
        
        # Check timestamped pattern
        match = re.match(timestamp_pattern, filename)
        if match:
            year, month, day, hour, minute, second, file_type, ext = match.groups()
            date_str = f"{year}-{month}-{day}"
            dates_found.add(date_str)
        
        # Check simple pattern
        match = re.match(simple_pattern, filename)
        if match:
            file_type, year, month, day, ext = match.groups()
            date_str = f"{year}-{month}-{day}"
            dates_found.add(date_str)
    
    print("")
    print("FILE PATTERN ANALYSIS")
    print("-" * 30)
    print(f"File Types: {', '.join(file_types)}")
    print(f"Unique Dates: {len(dates_found)}")
    
    sorted_dates = sorted(dates_found)
    for date in sorted_dates:
        print(f"  📅 {date}")
    
    # Check for processing scripts
    scripts_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts")
    relevant_scripts = []
    
    if scripts_dir.exists():
        for py_file in scripts_dir.glob("*.py"):
            # Skip migration backup files
            if "migration_backup" in py_file.name:
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                
                # Check for relevant keywords
                keywords = ['cad', 'rms', 'excel', 'xlsx', 'export', 'all_cads', 'all_rms']
                found_keywords = [kw for kw in keywords if kw in content]
                if found_keywords:
                    relevant_scripts.append({
                        'file': py_file.name,
                        'keywords_found': found_keywords
                    })
            
            except Exception:
                continue
    
    print("")
    print("PROCESSING SCRIPTS ANALYSIS")
    print("-" * 30)
    print(f"Relevant Scripts Found: {len(relevant_scripts)}")
    
    for script in relevant_scripts:
        print(f"  🐍 {script['file']}")
        print(f"     Keywords: {', '.join(script['keywords_found'])}")
    
    print("")
    print("GAP ANALYSIS")
    print("-" * 30)
    
    # Check for missing processors
    missing_processors = []
    if not any('all_cads' in script['keywords_found'] for script in relevant_scripts):
        missing_processors.append("CAD data processor")
    
    if not any('all_rms' in script['keywords_found'] for script in relevant_scripts):
        missing_processors.append("RMS data processor")
    
    # Check for automated export processors
    automated_found = any('export' in script['keywords_found'] and 'excel' in script['keywords_found'] 
                        for script in relevant_scripts)
    
    if missing_processors:
        print("❌ MISSING PROCESSORS:")
        for processor in missing_processors:
            print(f"   - {processor}")
    else:
        print("✅ Basic processors appear to exist")
    
    if not automated_found:
        print("⚠️  No automated export processing scripts detected")
    
    # Recent file processing status
    recent_dates = sorted(dates_found)[-3:] if dates_found else []
    if recent_dates:
        print(f"\n📅 RECENT EXPORT DATES: {', '.join(recent_dates)}")
        print("   Status: Files present, processor verification needed")

if __name__ == "__main__":
    main()