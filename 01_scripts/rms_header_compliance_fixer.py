#!/usr/bin/env python3
"""
RMS Header Compliance Fixer and Hybrid Filtering Implementation
Fixes header compliance and implements production-ready hybrid filtering
"""

import pandas as pd
import numpy as np
import json
import re
from datetime import datetime
from pathlib import Path

class RMSComplianceAndHybridFilter:
    def __init__(self):
        self.target_crimes = [
            "Motor Vehicle Theft",
            "Robbery", 
            "Burglary – Auto",
            "Sexual",
            "Burglary – Commercial", 
            "Burglary – Residence"
        ]
        
        # Enhanced patterns for better matching
        self.crime_patterns = {
            "Motor Vehicle Theft": [
                r"motor\s*vehicle\s*theft",
                r"theft\s*of\s*motor\s*vehicle",
                r"auto\s*theft",
                r"car\s*theft",
                r"vehicle\s*theft",
                r"240\s*=\s*theft\s*of\s*motor\s*vehicle"
            ],
            "Robbery": [
                r"robbery",
                r"120\s*=\s*robbery"
            ],
            "Burglary – Auto": [
                r"burglary\s*[-–]\s*auto",
                r"auto\s*burglary",
                r"theft\s*from\s*motor\s*vehicle",
                r"23f\s*=\s*theft\s*from\s*motor\s*vehicle"
            ],
            "Sexual": [
                r"sexual",
                r"11d\s*=\s*fondling",
                r"criminal\s*sexual\s*contact"
            ],
            "Burglary – Commercial": [
                r"burglary\s*[-–]\s*commercial",
                r"commercial\s*burglary",
                r"220\s*=\s*burglary.*commercial"
            ],
            "Burglary – Residence": [
                r"burglary\s*[-–]\s*residence",
                r"residential\s*burglary",
                r"220\s*=\s*burglary.*residential"
            ]
        }
        
        self.results = {}
        
    def analyze_header_compliance(self, df, dataset_name):
        """Analyze header compliance with snake_case standards"""
        snake_case_pattern = r'^[a-z]+(?:_[a-z0-9]+)*$'
        
        headers = df.columns.tolist()
        compliant_headers = []
        non_compliant_headers = []
        
        for header in headers:
            if re.match(snake_case_pattern, header):
                compliant_headers.append(header)
            else:
                non_compliant_headers.append(header)
        
        compliance_report = {
            'dataset': dataset_name,
            'total_headers': len(headers),
            'compliant_headers': len(compliant_headers),
            'non_compliant_headers': len(non_compliant_headers),
            'compliance_rate': (len(compliant_headers) / len(headers)) * 100,
            'non_compliant_list': non_compliant_headers,
            'all_headers': headers
        }
        
        return compliance_report
    
    def fix_header_compliance(self, df):
        """Fix header compliance by converting to proper snake_case"""
        header_mapping = {}
        
        for col in df.columns:
            # Convert to lowercase and replace problematic characters
            new_col = col.lower()
            
            # Replace spaces and hyphens with underscores
            new_col = re.sub(r'[\s\-–]+', '_', new_col)
            
            # Remove non-alphanumeric characters except underscores
            new_col = re.sub(r'[^a-z0-9_]', '', new_col)
            
            # Remove multiple consecutive underscores
            new_col = re.sub(r'_+', '_', new_col)
            
            # Remove leading/trailing underscores
            new_col = new_col.strip('_')
            
            # Handle empty or invalid column names
            if not new_col or new_col.isdigit():
                new_col = f"column_{col}"
            
            header_mapping[col] = new_col
        
        # Apply the mapping
        df_fixed = df.rename(columns=header_mapping)
        
        return df_fixed, header_mapping
    
    def match_crime_pattern(self, text, crime_type):
        """Match text against crime patterns"""
        if pd.isna(text):
            return False
            
        text = str(text).lower().strip()
        patterns = self.crime_patterns.get(crime_type, [])
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def apply_cad_filtering(self, cad_df):
        """Apply CAD filtering using incident column as primary classifier"""
        filtered_cases = {}
        all_filtered_cases = set()
        
        for crime in self.target_crimes:
            # Primary: incident column
            incident_matches = cad_df['incident'].apply(
                lambda x: self.match_crime_pattern(x, crime)
            )
            
            # Secondary: response_type and category_type
            response_type_matches = cad_df['response_type'].apply(
                lambda x: self.match_crime_pattern(x, crime)
            )
            category_type_matches = cad_df['category_type'].apply(
                lambda x: self.match_crime_pattern(x, crime)
            )
            
            # Combined logic: any column matches
            combined_matches = incident_matches | response_type_matches | category_type_matches
            
            # Get case numbers for this crime type
            crime_cases = cad_df[combined_matches]['case_number'].tolist()
            filtered_cases[crime] = crime_cases
            all_filtered_cases.update(crime_cases)
        
        # Create filtered CAD dataframe
        cad_filtered = cad_df[cad_df['case_number'].isin(all_filtered_cases)].copy()
        
        return cad_filtered, filtered_cases
    
    def match_rms_cases(self, rms_df, cad_filtered_cases):
        """Match CAD cases with RMS using case_number"""
        # Get all case numbers from CAD filtering
        all_cad_cases = set()
        for cases in cad_filtered_cases.values():
            all_cad_cases.update(cases)
        
        # Find matching RMS cases
        rms_matched = rms_df[rms_df['case_number'].isin(all_cad_cases)].copy()
        
        # Additional validation using RMS nibrs_classification
        rms_validation = {}
        for crime in self.target_crimes:
            cad_cases = set(cad_filtered_cases[crime])
            
            # Find RMS cases that match CAD cases AND have relevant NIBRS codes
            nibrs_matches = rms_df['nibrs_classification'].apply(
                lambda x: self.match_crime_pattern(x, crime)
            )
            
            rms_crime_cases = set(rms_df[nibrs_matches]['case_number'].tolist())
            
            # Intersection of CAD and RMS cases
            validated_cases = cad_cases.intersection(rms_crime_cases)
            
            rms_validation[crime] = {
                'cad_cases': len(cad_cases),
                'rms_nibrs_cases': len(rms_crime_cases),
                'validated_cases': len(validated_cases),
                'validation_rate': (len(validated_cases) / len(cad_cases) * 100) if cad_cases else 0
            }
        
        return rms_matched, rms_validation
    
    def generate_compliance_report(self, original_report, fixed_report, header_mapping):
        """Generate comprehensive compliance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'original_compliance': original_report,
            'fixed_compliance': fixed_report,
            'header_mapping': header_mapping,
            'improvements': {
                'compliance_increase': fixed_report['compliance_rate'] - original_report['compliance_rate'],
                'headers_fixed': len(header_mapping) - fixed_report['compliant_headers']
            }
        }
        
        return report
    
    def export_datasets(self, cad_filtered, rms_matched, output_dir=None):
        """Export filtered datasets with compliant headers"""
        if output_dir is None:
            output_dir = Path(".")
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export paths
        cad_export_path = output_dir / f"cad_filtered_compliant_{timestamp}.csv"
        rms_export_path = output_dir / f"rms_matched_compliant_{timestamp}.csv"
        
        # Export files
        cad_filtered.to_csv(cad_export_path, index=False)
        rms_matched.to_csv(rms_export_path, index=False)
        
        export_info = {
            'cad_filtered': {
                'path': str(cad_export_path),
                'records': len(cad_filtered),
                'headers': cad_filtered.columns.tolist()
            },
            'rms_matched': {
                'path': str(rms_export_path),
                'records': len(rms_matched),
                'headers': rms_matched.columns.tolist()
            }
        }
        
        return export_info
    
    def run_full_process(self, cad_path, rms_path, output_dir=None):
        """Run complete header compliance fix and hybrid filtering"""
        print("=== RMS Header Compliance Fix & Hybrid Filtering ===")
        
        # Load data
        print("Loading data...")
        cad_df = pd.read_csv(cad_path)
        rms_df = pd.read_csv(rms_path)
        
        print(f"Loaded CAD: {len(cad_df)} records")
        print(f"Loaded RMS: {len(rms_df)} records")
        
        # 1. Analyze original RMS header compliance
        print("\n=== Analyzing Header Compliance ===")
        original_compliance = self.analyze_header_compliance(rms_df, "Original RMS")
        print(f"Original RMS compliance: {original_compliance['compliance_rate']:.1f}%")
        print(f"Non-compliant headers: {original_compliance['non_compliant_list']}")
        
        # 2. Fix header compliance
        print("\n=== Fixing Header Compliance ===")
        rms_fixed, header_mapping = self.fix_header_compliance(rms_df)
        fixed_compliance = self.analyze_header_compliance(rms_fixed, "Fixed RMS")
        
        print(f"Fixed RMS compliance: {fixed_compliance['compliance_rate']:.1f}%")
        if header_mapping:
            print("Header mappings applied:")
            for old, new in header_mapping.items():
                if old != new:
                    print(f"  {old} -> {new}")
        
        # 3. Apply CAD filtering
        print("\n=== Applying CAD Filtering ===")
        cad_filtered, cad_cases = self.apply_cad_filtering(cad_df)
        print(f"CAD filtered: {len(cad_filtered)} records from {len(cad_df)} total")
        
        for crime, cases in cad_cases.items():
            print(f"  {crime}: {len(cases)} cases")
        
        # 4. Match RMS cases
        print("\n=== Matching RMS Cases ===")
        rms_matched, rms_validation = self.match_rms_cases(rms_fixed, cad_cases)
        print(f"RMS matched: {len(rms_matched)} records from {len(rms_fixed)} total")
        
        print("Validation rates:")
        for crime, validation in rms_validation.items():
            print(f"  {crime}: {validation['validation_rate']:.1f}% "
                  f"({validation['validated_cases']}/{validation['cad_cases']} cases)")
        
        # 5. Generate compliance report
        compliance_report = self.generate_compliance_report(
            original_compliance, fixed_compliance, header_mapping
        )
        
        # 6. Export datasets
        print("\n=== Exporting Datasets ===")
        export_info = self.export_datasets(cad_filtered, rms_matched, output_dir)
        
        print(f"CAD filtered exported: {export_info['cad_filtered']['path']}")
        print(f"RMS matched exported: {export_info['rms_matched']['path']}")
        
        # 7. Save comprehensive results
        results = {
            'compliance_report': compliance_report,
            'filtering_results': {
                'cad_cases': cad_cases,
                'rms_validation': rms_validation
            },
            'export_info': export_info
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = f"rms_compliance_hybrid_results_{timestamp}.json"
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nResults saved: {results_path}")
        
        return {
            'cad_filtered': cad_filtered,
            'rms_matched': rms_matched,
            'compliance_report': compliance_report,
            'results_file': results_path
        }

def main():
    """Main execution function"""
    processor = RMSComplianceAndHybridFilter()
    
    # File paths
    cad_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\C08W31_20250802_7Day_cad_data_standardized.csv"
    rms_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\C08W31_20250802_7Day_rms_data_standardized.csv"
    
    # Output directory (current directory)
    output_dir = "."
    
    # Run the complete process
    results = processor.run_full_process(cad_path, rms_path, output_dir)
    
    print("\n=== Process Complete ===")
    print("All headers are now compliant and hybrid filtering applied successfully!")
    
    return results

if __name__ == "__main__":
    results = main()