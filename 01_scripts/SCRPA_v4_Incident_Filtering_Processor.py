#!/usr/bin/env python3
"""
SCRPA v4 Incident Type Tagging & Multi-Column Filtering
Implements advanced incident type tagging and comparative filtering analysis.

Author: Crime Analysis Team
Version: 4.0
Date: 2025-08-03
Purpose: Comprehensive incident type tagging with multi-method filtering validation
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings
import re

warnings.filterwarnings('ignore')

class SCRPAv4IncidentFilteringProcessor:
    """SCRPA v4 processor for incident type tagging and filtering analysis."""
    
    def __init__(self):
        """Initialize the processor with logging and tracked crime types."""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Tracked crime types from specification (case-insensitive matching)
        self.TRACKED_CRIMES = [
            "Burglary - Auto",
            "Burglary - Residence", 
            "Burglary - Commercial",
            "Motor Vehicle Theft",
            "Robbery",
            "Sexual"
        ]
        
        # Alternative spellings and variations for better matching
        self.CRIME_VARIATIONS = {
            "Burglary - Auto": ["Burglary – Auto", "Burglary-Auto", "Auto Burglary", "Burglary Auto"],
            "Burglary - Residence": ["Burglary – Residence", "Burglary-Residence", "Residential Burglary", "Burglary Residence"],
            "Burglary - Commercial": ["Burglary – Commercial", "Burglary-Commercial", "Commercial Burglary", "Burglary Commercial"],
            "Motor Vehicle Theft": ["MV Theft", "Auto Theft", "Vehicle Theft", "Car Theft"],
            "Robbery": ["Armed Robbery", "Strong Arm Robbery"],
            "Sexual": ["Sexual Assault", "Sexual Offense", "Sex Offense", "Sexual Contact", "Criminal Sexual Contact"]
        }
        
        # Processing statistics
        self.stats = {
            'records_processed': 0,
            'incident_tagging': {
                'tagged_records': 0,
                'untagged_records': 0,
                'multiple_tags': 0
            },
            'filtering_comparison': {
                'method_a_count': 0,
                'method_b_count': 0,
                'discrepancy': 0,
                'filtering_accuracy': 0
            }
        }
        
    def tag_incidents(self, all_inc: Union[str, None]) -> Union[str, None]:
        """
        Tag incidents with tracked crime types from all_incidents string.
        
        Args:
            all_inc: String containing all incident types (comma or pipe separated)
            
        Returns:
            Comma-separated string of matched tracked crime types, or None if no matches
        """
        if pd.isna(all_inc) or not str(all_inc).strip():
            return None
            
        try:
            incident_text = str(all_inc).lower()
            found_crimes = []
            
            # Check each tracked crime type
            for crime in self.TRACKED_CRIMES:
                # Check main crime name
                if crime.lower() in incident_text:
                    if crime not in found_crimes:
                        found_crimes.append(crime)
                    continue
                    
                # Check variations
                if crime in self.CRIME_VARIATIONS:
                    for variation in self.CRIME_VARIATIONS[crime]:
                        if variation.lower() in incident_text:
                            if crime not in found_crimes:
                                found_crimes.append(crime)
                            break
                            
            return ", ".join(found_crimes) if found_crimes else None
            
        except Exception as e:
            self.logger.warning(f"Error tagging incidents for '{all_inc}': {e}")
            return None
            
    def compare_filtering_methods(self, df: pd.DataFrame, target_crimes: List[str] = None) -> Dict[str, Any]:
        """
        Compare multi-column filtering methods for accuracy validation.
        
        Args:
            df: DataFrame with incident columns
            target_crimes: List of target crime types (defaults to tracked crimes)
            
        Returns:
            Dictionary with comparison results and filtering statistics
        """
        if target_crimes is None:
            target_crimes = self.TRACKED_CRIMES
            
        self.logger.info(f"Comparing filtering methods for {len(df)} records")
        
        # Add unique identifier for tracking
        df_work = df.copy()
        df_work['_temp_id'] = range(len(df_work))
        
        # Method A: Multi-column boolean mask (DEFAULT METHOD)
        method_a_mask = pd.Series(False, index=df_work.index)
        
        incident_columns = [col for col in df_work.columns if 'incident_type' in col.lower() or 
                          col in ['Incident_Type_1', 'Incident_Type_2', 'Incident_Type_3']]
        
        self.logger.info(f"Found incident columns for Method A: {incident_columns}")
        
        for col in incident_columns:
            if col in df_work.columns:
                for crime in target_crimes:
                    # Check main crime name
                    mask = df_work[col].str.contains(crime, case=False, na=False)
                    method_a_mask |= mask
                    
                    # Check variations
                    if crime in self.CRIME_VARIATIONS:
                        for variation in self.CRIME_VARIATIONS[crime]:
                            var_mask = df_work[col].str.contains(re.escape(variation), case=False, na=False)
                            method_a_mask |= var_mask
                            
        method_a_count = method_a_mask.sum()
        method_a_records = df_work[method_a_mask]
        
        # Method B: Unpivot approach (VALIDATION METHOD)
        try:
            # Create unpivoted dataset
            id_vars = [col for col in df_work.columns if 'incident_type' not in col.lower() and 
                      col not in ['Incident_Type_1', 'Incident_Type_2', 'Incident_Type_3']]
            value_vars = incident_columns
            
            if not value_vars:
                # Fallback: use all_incidents column if available
                if 'all_incidents' in df_work.columns:
                    method_b_matches = df_work[df_work['all_incidents'].str.contains(
                        '|'.join([re.escape(crime) for crime in target_crimes]), 
                        case=False, na=False
                    )]
                    method_b_count = len(method_b_matches)
                else:
                    method_b_count = 0
                    method_b_matches = pd.DataFrame()
            else:
                df_long = df_work.melt(
                    id_vars=id_vars,
                    value_vars=value_vars,
                    var_name='incident_column',
                    value_name='incident_value'
                )
                
                # Create pattern for all target crimes and variations
                all_patterns = []
                for crime in target_crimes:
                    all_patterns.append(re.escape(crime))
                    if crime in self.CRIME_VARIATIONS:
                        for variation in self.CRIME_VARIATIONS[crime]:
                            all_patterns.append(re.escape(variation))
                            
                pattern = '|'.join(all_patterns)
                
                method_b_matches = df_long[df_long['incident_value'].str.contains(
                    pattern, case=False, na=False
                )]
                
                # Count unique records (by temp_id)
                method_b_count = len(method_b_matches['_temp_id'].unique()) if not method_b_matches.empty else 0
                
        except Exception as e:
            self.logger.error(f"Method B (unpivot) failed: {e}")
            method_b_count = 0
            method_b_matches = pd.DataFrame()
            
        # Calculate comparison metrics
        discrepancy = abs(method_a_count - method_b_count)
        filtering_accuracy = method_a_count / len(df_work) * 100 if len(df_work) > 0 else 0
        
        # Store results
        self.stats['filtering_comparison'] = {
            'method_a_count': int(method_a_count),
            'method_b_count': int(method_b_count),
            'discrepancy': int(discrepancy),
            'filtering_accuracy': float(filtering_accuracy)
        }
        
        results = {
            'method_a_count': int(method_a_count),
            'method_b_count': int(method_b_count),
            'discrepancy': int(discrepancy),
            'method_a_records': method_a_records.drop(columns=['_temp_id']),
            'filtering_accuracy': float(filtering_accuracy),
            'discrepancy_rate': float(discrepancy / len(df_work) * 100) if len(df_work) > 0 else 0,
            'validation_status': 'PASS' if discrepancy / len(df_work) * 100 < 5 else 'FAIL',
            'accuracy_status': 'PASS' if filtering_accuracy >= 90 else 'REVIEW'
        }
        
        self.logger.info(f"Filtering comparison - Method A: {method_a_count}, Method B: {method_b_count}, "
                        f"Discrepancy: {discrepancy} ({discrepancy/len(df_work)*100:.1f}%)")
        
        return results
        
    def process_incident_tagging(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process DataFrame to add incident type tagging.
        
        Args:
            df: Input DataFrame with incident data
            
        Returns:
            Enhanced DataFrame with incident_type column
        """
        self.logger.info(f"Processing incident tagging for {len(df)} records")
        self.stats['records_processed'] = len(df)
        
        result_df = df.copy()
        
        # Apply incident tagging
        if 'all_incidents' in result_df.columns:
            self.logger.info("Using 'all_incidents' column for tagging")
            result_df['incident_type'] = result_df['all_incidents'].apply(self.tag_incidents)
        elif 'incident' in result_df.columns:
            self.logger.info("Using 'incident' column for tagging")
            result_df['incident_type'] = result_df['incident'].apply(self.tag_incidents)
        else:
            # Try to create all_incidents column from individual columns
            incident_columns = [col for col in result_df.columns if 'incident_type' in col.lower() or 
                              col in ['Incident_Type_1', 'Incident_Type_2', 'Incident_Type_3']]
            
            if incident_columns:
                self.logger.info(f"Creating all_incidents from columns: {incident_columns}")
                
                def combine_incidents(row):
                    incidents = []
                    for col in incident_columns:
                        if pd.notna(row[col]) and str(row[col]).strip():
                            incidents.append(str(row[col]).strip())
                    return ' | '.join(incidents) if incidents else None
                
                result_df['all_incidents'] = result_df.apply(combine_incidents, axis=1)
                result_df['incident_type'] = result_df['all_incidents'].apply(self.tag_incidents)
            else:
                self.logger.warning("No suitable incident columns found for tagging")
                result_df['incident_type'] = None
                
        # Calculate tagging statistics
        tagged_count = result_df['incident_type'].notna().sum()
        untagged_count = result_df['incident_type'].isna().sum()
        multiple_tags_count = result_df['incident_type'].str.contains(',', na=False).sum()
        
        self.stats['incident_tagging'] = {
            'tagged_records': int(tagged_count),
            'untagged_records': int(untagged_count), 
            'multiple_tags': int(multiple_tags_count)
        }
        
        self.logger.info(f"Incident tagging complete - Tagged: {tagged_count}, "
                        f"Untagged: {untagged_count}, Multiple tags: {multiple_tags_count}")
        
        return result_df
        
    def generate_filtering_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive filtering analysis report."""
        
        # Run comparison analysis
        comparison_results = self.compare_filtering_methods(df)
        
        # Analyze tagged incidents
        if 'incident_type' in df.columns:
            tagged_breakdown = {}
            for crime in self.TRACKED_CRIMES:
                count = df['incident_type'].str.contains(crime, na=False).sum()
                tagged_breakdown[crime] = int(count)
        else:
            tagged_breakdown = {}
            
        # Generate comprehensive report
        report = {
            'processing_summary': {
                'total_records': len(df),
                'tagged_records': self.stats['incident_tagging']['tagged_records'],
                'tagging_rate': self.stats['incident_tagging']['tagged_records'] / len(df) * 100 if len(df) > 0 else 0
            },
            'filtering_comparison': comparison_results,
            'crime_type_breakdown': tagged_breakdown,
            'quality_metrics': {
                'discrepancy_acceptable': comparison_results['discrepancy_rate'] < 5,
                'filtering_accuracy_good': comparison_results['filtering_accuracy'] >= 90,
                'overall_quality': 'EXCELLENT' if (comparison_results['discrepancy_rate'] < 5 and 
                                                 comparison_results['filtering_accuracy'] >= 90) else 'REVIEW'
            }
        }
        
        return report
        
    def validate_processing(self, original_df: pd.DataFrame, processed_df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the incident processing results."""
        validation = {
            'record_count_preserved': len(original_df) == len(processed_df),
            'original_records': len(original_df),
            'processed_records': len(processed_df),
            'new_columns_added': [],
            'incident_tagging_validation': {},
            'before_after_totals': {}
        }
        
        # Check for new columns
        original_cols = set(original_df.columns)
        processed_cols = set(processed_df.columns)
        validation['new_columns_added'] = sorted(list(processed_cols - original_cols))
        
        # Validate incident tagging
        if 'incident_type' in processed_df.columns:
            tagged_count = processed_df['incident_type'].notna().sum()
            total_count = len(processed_df)
            
            validation['incident_tagging_validation'] = {
                'tagged_records': int(tagged_count),
                'total_records': int(total_count),
                'tagging_rate': float(tagged_count / total_count * 100) if total_count > 0 else 0,
                'multiple_tag_records': int(processed_df['incident_type'].str.contains(',', na=False).sum())
            }
            
        # Before/after totals for each tracked crime
        validation['before_after_totals'] = {}
        for crime in self.TRACKED_CRIMES:
            before_count = 0
            after_count = 0
            
            # Count in original data (if possible)
            if 'all_incidents' in original_df.columns:
                before_count = original_df['all_incidents'].str.contains(crime, case=False, na=False).sum()
            
            # Count in processed data
            if 'incident_type' in processed_df.columns:
                after_count = processed_df['incident_type'].str.contains(crime, na=False).sum()
                
            validation['before_after_totals'][crime] = {
                'before': int(before_count),
                'after': int(after_count),
                'preserved': int(before_count) == int(after_count)
            }
            
        return validation


def create_sample_incident_data() -> pd.DataFrame:
    """Create sample data for testing incident tagging and filtering."""
    sample_data = {
        'case_number': ['25-001001', '25-001002', '25-001003', '25-001004', '25-001005', '25-001006', '25-001007'],
        'all_incidents': [
            "Burglary - Auto, Criminal Mischief",                    # Single tracked crime
            "Robbery, Theft, Medical Call",                          # Single tracked crime
            "Motor Vehicle Theft, Burglary - Residence",             # Multiple tracked crimes
            "Sexual Assault, Domestic Violence",                     # Tracked crime (variation)
            "Burglary – Commercial, Vandalism",                     # Tracked crime (alt spelling)
            "Disorderly Conduct, Public Intoxication",              # No tracked crimes
            "Burglary-Auto, Motor Vehicle Theft, Robbery"           # Multiple tracked crimes
        ],
        'Incident_Type_1': [
            "Burglary - Auto",
            "Robbery", 
            "Motor Vehicle Theft",
            "Sexual Assault",
            "Burglary – Commercial",
            "Disorderly Conduct",
            "Burglary-Auto"
        ],
        'Incident_Type_2': [
            "Criminal Mischief",
            "Theft",
            "Burglary - Residence", 
            "Domestic Violence",
            "Vandalism",
            "Public Intoxication",
            "Motor Vehicle Theft"
        ],
        'Incident_Type_3': [
            None,
            "Medical Call",
            None,
            None,
            None,
            None,
            "Robbery"
        ]
    }
    
    return pd.DataFrame(sample_data)


def main():
    """Main execution function for testing."""
    print("SCRPA v4 Incident Type Tagging & Multi-Column Filtering")
    print("=" * 55)
    
    try:
        # Initialize processor
        processor = SCRPAv4IncidentFilteringProcessor()
        
        # Create sample data
        print("Creating sample test data...")
        sample_df = create_sample_incident_data()
        
        print(f"Sample data: {len(sample_df)} records")
        print("\nOriginal data:")
        print(sample_df[['case_number', 'all_incidents']].to_string())
        
        # Process incident tagging
        print(f"\nProcessing incident tagging...")
        processed_df = processor.process_incident_tagging(sample_df)
        
        print(f"\nIncident Tagging Results:")
        display_cols = ['case_number', 'all_incidents', 'incident_type']
        print(processed_df[display_cols].to_string())
        
        # Test individual tag_incidents function
        print(f"\nTesting tag_incidents function:")
        test_cases = [
            "Burglary - Auto, Criminal Mischief",
            "Robbery, Theft, Medical Call", 
            "Motor Vehicle Theft, Burglary - Residence",
            "Sexual Assault, Domestic Violence",
            "Disorderly Conduct, Public Intoxication"
        ]
        
        for test_case in test_cases:
            result = processor.tag_incidents(test_case)
            print(f"  '{test_case}' -> '{result}'")
            
        # Run filtering comparison
        print(f"\nRunning filtering method comparison...")
        comparison_results = processor.compare_filtering_methods(processed_df)
        
        print(f"\nFiltering Comparison Results:")
        print(f"  Method A (Multi-column): {comparison_results['method_a_count']} records")
        print(f"  Method B (Unpivot): {comparison_results['method_b_count']} records")
        print(f"  Discrepancy: {comparison_results['discrepancy']} ({comparison_results['discrepancy_rate']:.1f}%)")
        print(f"  Filtering accuracy: {comparison_results['filtering_accuracy']:.1f}%")
        print(f"  Validation status: {comparison_results['validation_status']}")
        print(f"  Accuracy status: {comparison_results['accuracy_status']}")
        
        # Generate comprehensive analysis
        analysis_report = processor.generate_filtering_analysis(processed_df)
        validation_report = processor.validate_processing(sample_df, processed_df)
        
        # Display comprehensive results
        print(f"\n[COMPREHENSIVE ANALYSIS]")
        proc_summary = analysis_report['processing_summary']
        print(f"Total records: {proc_summary['total_records']}")
        print(f"Tagged records: {proc_summary['tagged_records']}")
        print(f"Tagging rate: {proc_summary['tagging_rate']:.1f}%")
        
        print(f"\nCrime Type Breakdown:")
        for crime, count in analysis_report['crime_type_breakdown'].items():
            print(f"  {crime}: {count}")
            
        quality = analysis_report['quality_metrics']
        print(f"\nQuality Metrics:")
        print(f"  Discrepancy acceptable (<5%): {'[PASS]' if quality['discrepancy_acceptable'] else '[FAIL]'}")
        print(f"  Filtering accuracy (>=90%): {'[PASS]' if quality['filtering_accuracy_good'] else '[FAIL]'}")
        print(f"  Overall quality: {quality['overall_quality']}")
        
        print(f"\n[VALIDATION REPORT]")
        print(f"Record preservation: {validation_report['record_count_preserved']}")
        print(f"New columns: {validation_report['new_columns_added']}")
        
        if 'incident_tagging_validation' in validation_report:
            tag_val = validation_report['incident_tagging_validation']
            print(f"Tagging validation: {tag_val['tagged_records']}/{tag_val['total_records']} ({tag_val['tagging_rate']:.1f}%)")
            print(f"Multiple tag records: {tag_val['multiple_tag_records']}")
            
        # Save processed data
        output_file = Path(__file__).parent.parent / f"SCRPA_v4_IncidentFiltering_Sample_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        processed_df.to_csv(output_file, index=False)
        print(f"\nProcessed data saved: {output_file.name}")
        
        print(f"\n[SUCCESS] SCRPA v4 Incident Type Tagging & Filtering completed!")
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())