#!/usr/bin/env python3
"""
Column Header Investigation Script
Analyzes CAD and RMS CSV files for snake_case compliance
"""

import csv
import re
import json
from pathlib import Path

def is_snake_case(header):
    """Check if header follows snake_case convention"""
    # snake_case: lowercase letters, numbers, and underscores only
    # Must start with a letter, no consecutive underscores, no trailing underscore
    pattern = r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$'
    return bool(re.match(pattern, header))

def to_snake_case(header):
    """Convert header to snake_case"""
    # Replace spaces and hyphens with underscores
    header = re.sub(r'[-\s]+', '_', header)
    # Insert underscore before capital letters (except at start)
    header = re.sub(r'(?<!^)(?=[A-Z])', '_', header)
    # Convert to lowercase
    header = header.lower()
    # Remove multiple consecutive underscores
    header = re.sub(r'_+', '_', header)
    # Remove leading/trailing underscores
    header = header.strip('_')
    return header

def analyze_csv_headers(file_path):
    """Extract and analyze headers from CSV file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader)
            return headers
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def main():
    # File paths
    base_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi")
    cad_file = base_dir / "C08W31_20250802_7Day_cad_data_standardized.csv"
    rms_file = base_dir / "C08W31_20250802_7Day_rms_data_standardized.csv"
    
    # Extract headers
    print("=== COLUMN HEADER INVESTIGATION REPORT ===\n")
    
    # CAD File Analysis
    print("1. CAD FILE HEADERS")
    print(f"File: {cad_file.name}")
    cad_headers = analyze_csv_headers(cad_file)
    
    if cad_headers:
        print(f"Total columns: {len(cad_headers)}\n")
        
        compliant_cad = []
        non_compliant_cad = []
        
        for header in cad_headers:
            if is_snake_case(header):
                compliant_cad.append(header)
            else:
                non_compliant_cad.append(header)
        
        print("COMPLIANT HEADERS (snake_case):")
        for header in compliant_cad:
            print(f"  [OK] {header}")
        
        print(f"\nNON-COMPLIANT HEADERS ({len(non_compliant_cad)} violations):")
        for header in non_compliant_cad:
            suggested = to_snake_case(header)
            print(f"  [X] {header} -> {suggested}")
    
    print("\n" + "="*60 + "\n")
    
    # RMS File Analysis
    print("2. RMS FILE HEADERS")
    print(f"File: {rms_file.name}")
    rms_headers = analyze_csv_headers(rms_file)
    
    if rms_headers:
        print(f"Total columns: {len(rms_headers)}\n")
        
        compliant_rms = []
        non_compliant_rms = []
        
        for header in rms_headers:
            if is_snake_case(header):
                compliant_rms.append(header)
            else:
                non_compliant_rms.append(header)
        
        print("COMPLIANT HEADERS (snake_case):")
        for header in compliant_rms:
            print(f"  [OK] {header}")
        
        print(f"\nNON-COMPLIANT HEADERS ({len(non_compliant_rms)} violations):")
        for header in non_compliant_rms:
            suggested = to_snake_case(header)
            print(f"  [X] {header} -> {suggested}")
    
    print("\n" + "="*60 + "\n")
    
    # Summary Statistics
    print("3. COMPLIANCE SUMMARY")
    total_cad = len(cad_headers) if cad_headers else 0
    total_rms = len(rms_headers) if rms_headers else 0
    compliant_cad_count = len(compliant_cad) if cad_headers else 0
    compliant_rms_count = len(compliant_rms) if rms_headers else 0
    
    print(f"CAD File:")
    print(f"  - Total headers: {total_cad}")
    print(f"  - Compliant: {compliant_cad_count}")
    print(f"  - Non-compliant: {total_cad - compliant_cad_count}")
    print(f"  - Compliance rate: {(compliant_cad_count/total_cad*100):.1f}%" if total_cad > 0 else "  - No data")
    
    print(f"\nRMS File:")
    print(f"  - Total headers: {total_rms}")
    print(f"  - Compliant: {compliant_rms_count}")
    print(f"  - Non-compliant: {total_rms - compliant_rms_count}")
    print(f"  - Compliance rate: {(compliant_rms_count/total_rms*100):.1f}%" if total_rms > 0 else "  - No data")
    
    print(f"\nOverall:")
    total_headers = total_cad + total_rms
    total_compliant = compliant_cad_count + compliant_rms_count
    print(f"  - Total headers: {total_headers}")
    print(f"  - Total compliant: {total_compliant}")
    print(f"  - Total non-compliant: {total_headers - total_compliant}")
    print(f"  - Overall compliance rate: {(total_compliant/total_headers*100):.1f}%" if total_headers > 0 else "  - No data")
    
    # Generate conversion mapping
    print("\n" + "="*60 + "\n")
    print("4. CONVERSION MAPPING (JSON Format)")
    
    conversion_mapping = {}
    
    if cad_headers:
        conversion_mapping['cad_headers'] = {}
        for header in cad_headers:
            if not is_snake_case(header):
                conversion_mapping['cad_headers'][header] = to_snake_case(header)
    
    if rms_headers:
        conversion_mapping['rms_headers'] = {}
        for header in rms_headers:
            if not is_snake_case(header):
                conversion_mapping['rms_headers'][header] = to_snake_case(header)
    
    print(json.dumps(conversion_mapping, indent=2))
    
    # Save mapping to file
    mapping_file = Path(__file__).parent / "header_conversion_mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(conversion_mapping, f, indent=2)
    
    print(f"\nConversion mapping saved to: {mapping_file}")

if __name__ == "__main__":
    main()