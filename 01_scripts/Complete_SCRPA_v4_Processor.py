#!/usr/bin/env python3
"""
Complete SCRPA v4 Processor
Comprehensive SCRPA v4 data processing with all integrated modules.

Author: Crime Analysis Team
Version: 4.0  
Date: 2025-08-03
Purpose: Complete SCRPA v4 processing pipeline integrating all proven components
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings

# Import specialized processors
from CAD_CallType_Mapping_Processor import CADCallTypeProcessor
from RMS_DateTime_Cascade_Processor import RMSDateTimeCascadeProcessor
from SCRPA_v4_TimeOfDay_Location_Processor import SCRPAv4TimeLocationProcessor

warnings.filterwarnings('ignore')

class CompleteSCRPAv4Processor:
    """Complete SCRPA v4 processor integrating all modules."""
    
    def __init__(self, base_dir: str = None):
        """Initialize the complete SCRPA v4 processor."""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize specialized processors
        self.cad_processor = CADCallTypeProcessor(str(self.base_dir))
        self.rms_cascade_processor = RMSDateTimeCascadeProcessor()
        self.time_location_processor = SCRPAv4TimeLocationProcessor()
        
        # Processing statistics
        self.stats = {
            'input_records': {'rms': 0, 'cad': 0},
            'output_records': {'rms': 0, 'cad': 0, 'matched': 0},
            'processing_modules_applied': [],
            'processing_time': 0,
            'module_results': {}
        }
        
    def process_rms_data(self, df: pd.DataFrame, apply_cascade: bool = True) -> pd.DataFrame:
        """
        Process RMS data with datetime cascade and time-of-day/location processing.
        
        Args:
            df: Input RMS DataFrame
            apply_cascade: Whether to apply datetime cascade logic
            
        Returns:
            Fully processed RMS DataFrame
        """
        self.logger.info(f"Processing RMS data: {len(df)} records")
        self.stats['input_records']['rms'] = len(df)
        
        processed_df = df.copy()
        modules_applied = []
        
        # Apply datetime cascade if available
        if apply_cascade:
            cascade_columns = ['Incident Date', 'Incident Date_Between', 'Report Date',
                             'Incident Time', 'Incident Time_Between']
            
            if all(col in processed_df.columns for col in cascade_columns):
                self.logger.info("Applying RMS datetime cascade")
                processed_df = self.rms_cascade_processor.cascade_datetime(processed_df)
                modules_applied.append('datetime_cascade')
                
                # Store cascade results
                self.stats['module_results']['rms_cascade'] = self.rms_cascade_processor.generate_cascade_report()
            else:
                self.logger.info("Using existing processed date/time columns")
                
        # Apply time-of-day and location processing
        if 'incident_time' in processed_df.columns:
            self.logger.info("Applying time-of-day and location processing")
            processed_df = self.time_location_processor.process_time_and_location(processed_df)
            modules_applied.append('time_location_processing')
            
            # Store time/location results
            self.stats['module_results']['time_location'] = self.time_location_processor.generate_processing_report()
            
        self.stats['output_records']['rms'] = len(processed_df)
        self.stats['processing_modules_applied'].extend(modules_applied)
        
        self.logger.info(f"RMS processing complete: {len(processed_df)} records, modules: {modules_applied}")
        
        return processed_df
        
    def process_cad_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process CAD data with CallType mapping and response classification.
        
        Args:
            df: Input CAD DataFrame
            
        Returns:
            Fully processed CAD DataFrame
        """
        self.logger.info(f"Processing CAD data: {len(df)} records")
        self.stats['input_records']['cad'] = len(df)
        
        processed_df = df.copy()
        modules_applied = []
        
        # Apply CallType mapping and response classification
        self.logger.info("Applying CAD CallType mapping")
        processed_df = self.cad_processor.process_cad_data(processed_df)
        modules_applied.append('calltype_mapping')
        
        # Store CAD processing results
        self.stats['module_results']['cad_processing'] = {
            'mapping_report': self.cad_processor.generate_mapping_report(),
            'validation_report': self.cad_processor.validate_processing(df, processed_df)
        }
        
        # Apply time-of-day and location processing if columns are available
        if 'incident_time' in processed_df.columns or any('time' in col.lower() for col in processed_df.columns):
            self.logger.info("Applying CAD time-of-day and location processing")
            processed_df = self.time_location_processor.process_time_and_location(processed_df)
            modules_applied.append('time_location_processing')
            
        self.stats['output_records']['cad'] = len(processed_df)
        self.stats['processing_modules_applied'].extend(modules_applied)
        
        self.logger.info(f"CAD processing complete: {len(processed_df)} records, modules: {modules_applied}")
        
        return processed_df
        
    def match_cad_rms_data(self, rms_df: pd.DataFrame, cad_df: pd.DataFrame) -> pd.DataFrame:
        """
        Match CAD and RMS data using enhanced matching logic.
        
        Args:
            rms_df: Processed RMS DataFrame
            cad_df: Processed CAD DataFrame
            
        Returns:
            Matched DataFrame with combined data
        """
        self.logger.info(f"Matching CAD ({len(cad_df)}) and RMS ({len(rms_df)}) data")
        
        # Use RMS as base for matched dataset
        matched_df = rms_df.copy()
        
        # Add CAD columns that don't exist in RMS
        cad_columns_to_add = [
            'response_type', 'category_type', 'how_reported_clean',
            'cad_notes_cleaned', 'cad_notes_username', 'cad_notes_timestamp'
        ]
        
        for col in cad_columns_to_add:
            if col in cad_df.columns and col not in matched_df.columns:
                matched_df[col] = ''
                
        # Perform matching logic
        matches_found = 0
        
        for idx, rms_row in matched_df.iterrows():
            # Try matching by case number
            if pd.notna(rms_row.get('case_number')):
                cad_match = cad_df[cad_df.get('case_number', '') == rms_row['case_number']]
                
                if not cad_match.empty:
                    cad_row = cad_match.iloc[0]
                    for col in cad_columns_to_add:
                        if col in cad_df.columns:
                            matched_df.at[idx, col] = cad_row[col]
                    matches_found += 1
                    
        self.stats['output_records']['matched'] = len(matched_df)
        self.stats['module_results']['matching'] = {
            'matches_found': matches_found,
            'match_rate': matches_found / len(matched_df) * 100 if len(matched_df) > 0 else 0
        }
        
        self.logger.info(f"Matching complete: {matches_found} matches found ({matches_found/len(matched_df)*100:.1f}%)")
        
        return matched_df
        
    def process_complete_dataset(self, rms_file: str, cad_file: str) -> Dict[str, pd.DataFrame]:
        """
        Process complete SCRPA v4 dataset with all modules.
        
        Args:
            rms_file: Path to RMS data file
            cad_file: Path to CAD data file
            
        Returns:
            Dictionary containing all processed datasets
        """
        start_time = datetime.now()
        self.logger.info("Starting complete SCRPA v4 processing")
        
        try:
            # Load data
            rms_df = pd.read_csv(rms_file)
            cad_df = pd.read_csv(cad_file)
            
            self.logger.info(f"Loaded RMS: {len(rms_df)} records, CAD: {len(cad_df)} records")
            
            # Process RMS data
            processed_rms = self.process_rms_data(rms_df)
            
            # Process CAD data
            processed_cad = self.process_cad_data(cad_df)
            
            # Match datasets
            matched_data = self.match_cad_rms_data(processed_rms, processed_cad)
            
            # Calculate processing time
            end_time = datetime.now()
            self.stats['processing_time'] = (end_time - start_time).total_seconds()
            
            results = {
                'rms_processed': processed_rms,
                'cad_processed': processed_cad,
                'matched_data': matched_data
            }
            
            self.logger.info(f"Complete processing finished in {self.stats['processing_time']:.2f} seconds")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            raise
            
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive processing report for all modules."""
        
        report = {
            'processing_summary': {
                'total_processing_time': self.stats['processing_time'],
                'modules_applied': list(set(self.stats['processing_modules_applied'])),
                'input_records': self.stats['input_records'],
                'output_records': self.stats['output_records']
            },
            'module_results': self.stats['module_results'],
            'quality_assessment': {
                'rms_processing_quality': 'Unknown',
                'cad_processing_quality': 'Unknown',
                'overall_system_quality': 'Unknown'
            }
        }
        
        # Assess quality based on module results
        quality_scores = []
        
        # RMS quality assessment
        if 'rms_cascade' in self.stats['module_results']:
            cascade_results = self.stats['module_results']['rms_cascade']
            if 'cascade_effectiveness' in cascade_results:
                date_rate = cascade_results['cascade_effectiveness'].get('date_cascade_rate', 0)
                time_rate = cascade_results['cascade_effectiveness'].get('time_cascade_rate', 0)
                
                if date_rate >= 95 and time_rate >= 85:
                    report['quality_assessment']['rms_processing_quality'] = 'Excellent'
                    quality_scores.append(95)
                elif date_rate >= 90 and time_rate >= 75:
                    report['quality_assessment']['rms_processing_quality'] = 'Good'
                    quality_scores.append(85)
                else:
                    report['quality_assessment']['rms_processing_quality'] = 'Fair'
                    quality_scores.append(70)
                    
        # CAD quality assessment
        if 'cad_processing' in self.stats['module_results']:
            cad_results = self.stats['module_results']['cad_processing']
            if 'mapping_report' in cad_results:
                unmapped_count = cad_results['mapping_report'].get('unmapped_count', 0)
                total_categories = cad_results['mapping_report'].get('total_categories', 1)
                
                mapping_rate = (1 - unmapped_count / max(total_categories, 1)) * 100
                
                if mapping_rate >= 95:
                    report['quality_assessment']['cad_processing_quality'] = 'Excellent'
                    quality_scores.append(95)
                elif mapping_rate >= 90:
                    report['quality_assessment']['cad_processing_quality'] = 'Good'
                    quality_scores.append(85)
                else:
                    report['quality_assessment']['cad_processing_quality'] = 'Fair'
                    quality_scores.append(70)
                    
        # Overall system quality
        if quality_scores:
            avg_score = sum(quality_scores) / len(quality_scores)
            if avg_score >= 90:
                report['quality_assessment']['overall_system_quality'] = 'Excellent'
            elif avg_score >= 80:
                report['quality_assessment']['overall_system_quality'] = 'Good'
            else:
                report['quality_assessment']['overall_system_quality'] = 'Fair'
                
        return report


def main():
    """Main execution function for testing complete SCRPA v4 processing."""
    print("Complete SCRPA v4 Processor")
    print("=" * 30)
    
    try:
        # Initialize processor
        processor = CompleteSCRPAv4Processor()
        
        # Define input files
        base_dir = Path(__file__).parent.parent
        rms_file = base_dir / "C08W31_20250803_051051_rms_data_fixed.csv"
        cad_file = base_dir / "C08W31_20250803_051051_cad_data_fixed.csv"
        
        if not rms_file.exists() or not cad_file.exists():
            print(f"ERROR: Input files not found")
            print(f"RMS file exists: {rms_file.exists()}")
            print(f"CAD file exists: {cad_file.exists()}")
            return 1
            
        print(f"Processing files:")
        print(f"  RMS: {rms_file.name}")
        print(f"  CAD: {cad_file.name}")
        
        # Process complete dataset
        results = processor.process_complete_dataset(str(rms_file), str(cad_file))
        
        # Display results summary
        print(f"\n[PROCESSING RESULTS]")
        for dataset_name, dataset in results.items():
            print(f"{dataset_name}: {len(dataset)} records")
            
        # Generate comprehensive report
        report = processor.generate_comprehensive_report()
        
        print(f"\n[COMPREHENSIVE REPORT]")
        summary = report['processing_summary']
        print(f"Processing time: {summary['total_processing_time']:.2f} seconds")
        print(f"Modules applied: {', '.join(summary['modules_applied'])}")
        print(f"Input records - RMS: {summary['input_records']['rms']}, CAD: {summary['input_records']['cad']}")
        print(f"Output records - RMS: {summary['output_records']['rms']}, CAD: {summary['output_records']['cad']}, Matched: {summary['output_records']['matched']}")
        
        quality = report['quality_assessment']
        print(f"\n[QUALITY ASSESSMENT]")
        print(f"RMS processing: {quality['rms_processing_quality']}")
        print(f"CAD processing: {quality['cad_processing_quality']}")
        print(f"Overall system: {quality['overall_system_quality']}")
        
        # Show sample of final matched data
        matched_data = results['matched_data']
        print(f"\n[SAMPLE FINAL DATA]")
        sample_cols = ['case_number', 'incident_date', 'incident_time', 'time_of_day', 
                      'location', 'block', 'incident_type', 'response_type']
        available_cols = [col for col in sample_cols if col in matched_data.columns]
        print(matched_data[available_cols].head(5).to_string())
        
        # Save all results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = base_dir / '03_output'
        output_dir.mkdir(exist_ok=True)
        
        for dataset_name, dataset in results.items():
            output_file = output_dir / f"SCRPA_v4_{dataset_name}_{timestamp}.csv"
            dataset.to_csv(output_file, index=False)
            print(f"\nSaved: {output_file.name}")
            
        print(f"\n[SUCCESS] Complete SCRPA v4 processing completed!")
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())