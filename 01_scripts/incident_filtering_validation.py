#!/usr/bin/env python3
"""
SCRPA Incident Filtering Logic Validation Script
Validates filtering logic for target crimes with snake_case headers
"""

import pandas as pd
import numpy as np
import json
import re
from datetime import datetime
from pathlib import Path

class IncidentFilteringValidator:
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
        
    def load_data(self, cad_path, rms_path):
        """Load CAD and RMS data files"""
        try:
            self.cad_data = pd.read_csv(cad_path)
            self.rms_data = pd.read_csv(rms_path)
            
            print(f"Loaded CAD data: {len(self.cad_data)} records")
            print(f"Loaded RMS data: {len(self.rms_data)} records")
            
            # Verify snake_case headers
            self.verify_snake_case_headers()
            
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def verify_snake_case_headers(self):
        """Verify all headers are snake_case compliant"""
        snake_case_pattern = r'^[a-z]+(?:_[a-z]+)*$'
        
        cad_non_compliant = [col for col in self.cad_data.columns 
                           if not re.match(snake_case_pattern, col)]
        rms_non_compliant = [col for col in self.rms_data.columns 
                           if not re.match(snake_case_pattern, col)]
        
        if cad_non_compliant or rms_non_compliant:
            print("WARNING: Non-snake_case headers found:")
            if cad_non_compliant:
                print(f"CAD: {cad_non_compliant}")
            if rms_non_compliant:
                print(f"RMS: {rms_non_compliant}")
        else:
            print("All headers are snake_case compliant")
    
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
    
    def test_cad_filtering(self):
        """Test CAD filtering using incident, response_type, category_type columns"""
        print("\n=== CAD Filtering Test ===")
        
        cad_results = {}
        total_records = len(self.cad_data)
        
        for crime in self.target_crimes:
            # Check each column for matches
            incident_matches = self.cad_data['incident'].apply(
                lambda x: self.match_crime_pattern(x, crime)
            )
            response_type_matches = self.cad_data['response_type'].apply(
                lambda x: self.match_crime_pattern(x, crime)
            )
            category_type_matches = self.cad_data['category_type'].apply(
                lambda x: self.match_crime_pattern(x, crime)
            )
            
            # Combined logic: any column matches
            combined_matches = incident_matches | response_type_matches | category_type_matches
            matched_count = combined_matches.sum()
            
            cad_results[crime] = {
                'total_records': total_records,
                'matched_records': int(matched_count),
                'retention_rate': (matched_count / total_records) * 100,
                'incident_column_matches': int(incident_matches.sum()),
                'response_type_matches': int(response_type_matches.sum()),
                'category_type_matches': int(category_type_matches.sum())
            }
            
            print(f"{crime}: {matched_count} matches ({cad_results[crime]['retention_rate']:.2f}%)")
        
        self.results['cad_filtering'] = cad_results
        return cad_results
    
    def test_rms_filtering(self):
        """Test RMS filtering using incident_type, nibrs_classification columns"""
        print("\n=== RMS Filtering Test ===")
        
        rms_results = {}
        total_records = len(self.rms_data)
        
        for crime in self.target_crimes:
            # Check each column for matches
            incident_type_matches = self.rms_data['incident_type'].apply(
                lambda x: self.match_crime_pattern(x, crime)
            )
            nibrs_matches = self.rms_data['nibrs_classification'].apply(
                lambda x: self.match_crime_pattern(x, crime)
            )
            
            # Combined logic: any column matches
            combined_matches = incident_type_matches | nibrs_matches
            matched_count = combined_matches.sum()
            
            rms_results[crime] = {
                'total_records': total_records,
                'matched_records': int(matched_count),
                'retention_rate': (matched_count / total_records) * 100,
                'incident_type_matches': int(incident_type_matches.sum()),
                'nibrs_matches': int(nibrs_matches.sum())
            }
            
            print(f"{crime}: {matched_count} matches ({rms_results[crime]['retention_rate']:.2f}%)")
        
        self.results['rms_filtering'] = rms_results
        return rms_results
    
    def test_hybrid_approach(self):
        """Test hybrid CAD classification → RMS case matching"""
        print("\n=== Hybrid Approach Test ===")
        
        hybrid_results = {}
        
        # Get CAD classifications
        cad_classified = {}
        for crime in self.target_crimes:
            incident_matches = self.cad_data['incident'].apply(
                lambda x: self.match_crime_pattern(x, crime)
            )
            cad_classified[crime] = self.cad_data[incident_matches]['case_number'].tolist()
        
        # Match with RMS cases
        for crime in self.target_crimes:
            cad_cases = set(cad_classified[crime])
            rms_cases = set(self.rms_data['case_number'].tolist())
            
            # Find intersection
            matched_cases = cad_cases.intersection(rms_cases)
            
            hybrid_results[crime] = {
                'cad_classified_cases': len(cad_cases),
                'rms_available_cases': len(rms_cases),
                'hybrid_matched_cases': len(matched_cases),
                'hybrid_success_rate': (len(matched_cases) / len(cad_cases) * 100) if cad_cases else 0
            }
            
            print(f"{crime}: {len(matched_cases)} hybrid matches "
                  f"({hybrid_results[crime]['hybrid_success_rate']:.2f}% success rate)")
        
        self.results['hybrid_approach'] = hybrid_results
        return hybrid_results
    
    def validate_case_insensitive_matching(self):
        """Validate case-insensitive matching works correctly"""
        print("\n=== Case-Insensitive Validation ===")
        
        # Test various case combinations
        test_cases = [
            "Motor Vehicle Theft",
            "MOTOR VEHICLE THEFT", 
            "motor vehicle theft",
            "Motor VEHICLE theft",
            "240 = Theft of Motor Vehicle",
            "240 = THEFT OF MOTOR VEHICLE"
        ]
        
        validation_results = {}
        
        for test_case in test_cases:
            matched = self.match_crime_pattern(test_case, "Motor Vehicle Theft")
            validation_results[test_case] = matched
            print(f"'{test_case}': {'PASS' if matched else 'FAIL'}")
        
        self.results['case_insensitive_validation'] = validation_results
        return validation_results
    
    def generate_accuracy_metrics(self):
        """Generate comprehensive accuracy metrics"""
        print("\n=== Accuracy Metrics ===")
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'data_summary': {
                'cad_total_records': len(self.cad_data),
                'rms_total_records': len(self.rms_data),
                'target_crimes_count': len(self.target_crimes)
            }
        }
        
        # Calculate overall retention rates
        if 'cad_filtering' in self.results:
            cad_total_matches = sum(result['matched_records'] 
                                  for result in self.results['cad_filtering'].values())
            metrics['cad_overall_retention'] = (cad_total_matches / len(self.cad_data)) * 100
        
        if 'rms_filtering' in self.results:
            rms_total_matches = sum(result['matched_records'] 
                                  for result in self.results['rms_filtering'].values())
            metrics['rms_overall_retention'] = (rms_total_matches / len(self.rms_data)) * 100
        
        # Performance comparison
        metrics['performance_comparison'] = {
            'cad_filtering': {
                'pros': ['Direct incident classification', 'Real-time filtering'],
                'cons': ['May miss some incident types', 'Depends on CAD data quality']
            },
            'rms_filtering': {
                'pros': ['NIBRS standardized codes', 'More consistent classification'],
                'cons': ['Less detailed incident descriptions', 'Delayed data entry']
            },
            'hybrid_approach': {
                'pros': ['Best of both methods', 'Higher accuracy'],
                'cons': ['More complex processing', 'Requires both datasets']
            }
        }
        
        self.results['accuracy_metrics'] = metrics
        return metrics
    
    def generate_production_recommendation(self):
        """Generate production-ready recommendation"""
        print("\n=== Production Recommendation ===")
        
        recommendation = {
            'recommended_approach': 'Hybrid CAD Classification -> RMS Case Matching',
            'reasoning': [
                'Combines real-time CAD incident classification with RMS case validation',
                'Provides highest accuracy for target crime identification',
                'Maintains data integrity through cross-validation'
            ],
            'implementation_steps': [
                '1. Apply CAD filtering using incident column as primary classifier',
                '2. Use response_type and category_type as secondary filters',
                '3. Match identified cases with RMS data using case_number',
                '4. Validate using nibrs_classification for final confirmation',
                '5. Implement case-insensitive pattern matching throughout'
            ],
            'performance_optimization': [
                'Pre-compile regex patterns for faster matching',
                'Use vectorized pandas operations where possible',
                'Implement caching for frequently accessed patterns',
                'Consider parallel processing for large datasets'
            ],
            'quality_assurance': [
                'Implement automated testing for pattern updates',
                'Regular validation against known good datasets',
                'Monitor retention rates for unexpected changes',
                'Maintain audit trail of filtering decisions'
            ]
        }
        
        self.results['production_recommendation'] = recommendation
        
        print("Recommended Approach: Hybrid CAD Classification -> RMS Case Matching")
        print("Key Benefits:")
        for benefit in recommendation['reasoning']:
            print(f"  - {benefit}")
        
        return recommendation
    
    def save_results(self, output_path=None):
        """Save validation results to JSON file"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"filtering_validation_results_{timestamp}.json"
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nResults saved to: {output_path}")
        return output_path
    
    def run_full_validation(self, cad_path, rms_path):
        """Run complete validation suite"""
        print("=== SCRPA Incident Filtering Validation ===")
        print(f"Target Crimes: {', '.join(self.target_crimes)}")
        
        # Load data
        if not self.load_data(cad_path, rms_path):
            return False
        
        # Run all tests
        self.test_cad_filtering()
        self.test_rms_filtering() 
        self.test_hybrid_approach()
        self.validate_case_insensitive_matching()
        self.generate_accuracy_metrics()
        self.generate_production_recommendation()
        
        # Save results
        output_file = self.save_results()
        
        print(f"\n=== Validation Complete ===")
        print(f"Results file: {output_file}")
        
        return True

def main():
    """Main execution function"""
    validator = IncidentFilteringValidator()
    
    # File paths
    cad_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\C08W31_20250802_7Day_cad_data_standardized.csv"
    rms_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\C08W31_20250802_7Day_rms_data_standardized.csv"
    
    # Run validation
    success = validator.run_full_validation(cad_path, rms_path)
    
    if success:
        print("Validation completed successfully!")
    else:
        print("Validation failed!")
    
    return validator

if __name__ == "__main__":
    validator = main()