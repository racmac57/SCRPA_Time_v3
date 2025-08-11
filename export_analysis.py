#!/usr/bin/env python3
"""
Export File Analysis Script
==========================

Analyzes export files in CAD and RMS directories and identifies
missing processing scripts or patterns.

Author: Claude Code Assistant
Date: 2025-01-27
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class ExportAnalyzer:
    def __init__(self):
        self.cad_exports = []
        self.rms_exports = []
        self.processing_scripts = []
        self.analysis_results = {}
    
    def scan_exports(self):
        """Scan export directories for files."""
        # CAD exports
        cad_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA")
        if cad_dir.exists():
            self.cad_exports = [f for f in cad_dir.iterdir() if f.is_file()]
        
        # RMS exports
        rms_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA")
        if rms_dir.exists():
            self.rms_exports = [f for f in rms_dir.iterdir() if f.is_file()]
    
    def analyze_file_patterns(self):
        """Analyze file naming patterns and dates."""
        patterns = {
            'cad_timestamped': [],
            'rms_timestamped': [],
            'rms_simple': [],
            'dates_found': set(),
            'file_types': set()
        }
        
        # Pattern: YYYY_MM_DD_HH_MM_SS_TYPE.ext
        timestamp_pattern = r'(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(.+)\.(.+)'
        # Pattern: TYPE_Export_YYYY_MM_DD.ext
        simple_pattern = r'(.+)_Export_(\d{4})_(\d{2})_(\d{2})\.(.+)'
        
        for file_path in self.cad_exports:
            filename = file_path.name
            patterns['file_types'].add(file_path.suffix)
            
            match = re.match(timestamp_pattern, filename)
            if match:
                year, month, day, hour, minute, second, file_type, ext = match.groups()
                date_str = f"{year}-{month}-{day}"
                patterns['dates_found'].add(date_str)
                patterns['cad_timestamped'].append({
                    'file': filename,
                    'date': date_str,
                    'time': f"{hour}:{minute}:{second}",
                    'type': file_type,
                    'ext': ext
                })
        
        for file_path in self.rms_exports:
            filename = file_path.name
            patterns['file_types'].add(file_path.suffix)
            
            # Check timestamped pattern
            match = re.match(timestamp_pattern, filename)
            if match:
                year, month, day, hour, minute, second, file_type, ext = match.groups()
                date_str = f"{year}-{month}-{day}"
                patterns['dates_found'].add(date_str)
                patterns['rms_timestamped'].append({
                    'file': filename,
                    'date': date_str,
                    'time': f"{hour}:{minute}:{second}",
                    'type': file_type,
                    'ext': ext
                })
            
            # Check simple pattern
            match = re.match(simple_pattern, filename)
            if match:
                file_type, year, month, day, ext = match.groups()
                date_str = f"{year}-{month}-{day}"
                patterns['dates_found'].add(date_str)
                patterns['rms_simple'].append({
                    'file': filename,
                    'date': date_str,
                    'type': file_type,
                    'ext': ext
                })
        
        return patterns
    
    def check_processing_scripts(self):
        """Check for scripts that might process these exports."""
        scripts_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts")
        
        # Look for scripts that reference CAD, RMS, or export processing
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
                    if any(keyword in content for keyword in keywords):
                        relevant_scripts.append({
                            'file': py_file.name,
                            'path': str(py_file),
                            'keywords_found': [kw for kw in keywords if kw in content]
                        })
                
                except Exception:
                    continue
        
        return relevant_scripts
    
    def generate_report(self):
        """Generate comprehensive analysis report."""
        patterns = self.analyze_file_patterns()
        scripts = self.check_processing_scripts()
        
        report = []
        report.append("EXPORT FILE ANALYSIS REPORT")
        report.append("=" * 50)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Export file inventory
        report.append("EXPORT FILE INVENTORY")
        report.append("-" * 30)
        report.append(f"CAD Exports: {len(self.cad_exports)} files")
        for export in self.cad_exports:
            report.append(f"  📄 {export.name}")
        
        report.append(f"\nRMS Exports: {len(self.rms_exports)} files")
        for export in self.rms_exports:
            report.append(f"  📄 {export.name}")
        
        report.append("")
        
        # File patterns analysis
        report.append("FILE PATTERN ANALYSIS")
        report.append("-" * 30)
        report.append(f"File Types: {', '.join(patterns['file_types'])}")
        report.append(f"Unique Dates: {len(patterns['dates_found'])}")
        
        sorted_dates = sorted(patterns['dates_found'])
        for date in sorted_dates:
            report.append(f"  📅 {date}")
        
        report.append("")
        
        # Timestamped files detail
        if patterns['cad_timestamped']:
            report.append("CAD TIMESTAMPED FILES")
            report.append("-" * 30)
            for file_info in patterns['cad_timestamped']:
                report.append(f"  📊 {file_info['file']}")
                report.append(f"     Date: {file_info['date']} Time: {file_info['time']}")
                report.append(f"     Type: {file_info['type']}")
        
        if patterns['rms_timestamped']:
            report.append("\nRMS TIMESTAMPED FILES")
            report.append("-" * 30)
            for file_info in patterns['rms_timestamped']:
                report.append(f"  📊 {file_info['file']}")
                report.append(f"     Date: {file_info['date']} Time: {file_info['time']}")
                report.append(f"     Type: {file_info['type']}")
        
        if patterns['rms_simple']:
            report.append("\nRMS SIMPLE FORMAT FILES")
            report.append("-" * 30)
            for file_info in patterns['rms_simple']:
                report.append(f"  📊 {file_info['file']}")
                report.append(f"     Date: {file_info['date']}")
                report.append(f"     Type: {file_info['type']}")
        
        report.append("")
        
        # Processing scripts analysis
        report.append("PROCESSING SCRIPTS ANALYSIS")
        report.append("-" * 30)
        report.append(f"Relevant Scripts Found: {len(scripts)}")
        
        for script in scripts:
            report.append(f"  🐍 {script['file']}")
            report.append(f"     Keywords: {', '.join(script['keywords_found'])}")
        
        report.append("")
        
        # Gap analysis
        report.append("GAP ANALYSIS")
        report.append("-" * 30)
        
        # Check for missing date processors
        recent_dates = sorted(patterns['dates_found'])[-3:] if patterns['dates_found'] else []
        
        missing_processors = []
        if not any('ALL_CADS' in script['keywords_found'] for script in scripts):
            missing_processors.append("CAD data processor")
        
        if not any('ALL_RMS' in script['keywords_found'] for script in scripts):
            missing_processors.append("RMS data processor")
        
        # Check for automated export processors
        automated_found = any('export' in script['keywords_found'] and 'excel' in script['keywords_found'] 
                            for script in scripts)
        
        if missing_processors:
            report.append("❌ MISSING PROCESSORS:")
            for processor in missing_processors:
                report.append(f"   - {processor}")
        else:
            report.append("✅ Basic processors appear to exist")
        
        if not automated_found:
            report.append("⚠️  No automated export processing scripts detected")
        
        # Recent file processing status
        if recent_dates:
            report.append(f"\n📅 RECENT EXPORT DATES: {', '.join(recent_dates)}")
            report.append("   Status: Files present, processor verification needed")
        
        return '\n'.join(report)

def main():
    """Main execution function."""
    print("🔍 EXPORT FILE ANALYSIS")
    print("=" * 30)
    
    analyzer = ExportAnalyzer()
    analyzer.scan_exports()
    
    report = analyzer.generate_report()
    print(report)
    
    # Save report
    report_file = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\export_analysis_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Report saved to: {report_file}")

if __name__ == "__main__":
    main()