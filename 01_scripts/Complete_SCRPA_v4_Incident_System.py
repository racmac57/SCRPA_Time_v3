#!/usr/bin/env python3
"""
Complete SCRPA v4 Incident System
Comprehensive SCRPA v4 incident processing integrating all modules with incident filtering.

Author: Crime Analysis Team
Version: 4.0
Date: 2025-08-03
Purpose: Complete SCRPA v4 system with incident type tagging and filtering
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings

# Import all specialized processors
from CAD_CallType_Mapping_Processor import CADCallTypeProcessor
from RMS_DateTime_Cascade_Processor import RMSDateTimeCascadeProcessor
from SCRPA_v4_TimeOfDay_Location_Processor import SCRPAv4TimeLocationProcessor
from SCRPA_v4_Incident_Filtering_Processor import SCRPAv4IncidentFilteringProcessor

warnings.filterwarnings('ignore')

class CompleteSCRPAv4IncidentSystem:
    """Complete SCRPA v4 system with all modules including incident filtering."""
    
    def __init__(self, base_dir: str = None):
        """Initialize the complete SCRPA v4 incident system."""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize all specialized processors
        self.cad_processor = CADCallTypeProcessor(str(self.base_dir))
        self.rms_cascade_processor = RMSDateTimeCascadeProcessor()
        self.time_location_processor = SCRPAv4TimeLocationProcessor()
        self.incident_filtering_processor = SCRPAv4IncidentFilteringProcessor()
        
        # System-wide statistics
        self.system_stats = {
            'processing_start_time': None,
            'processing_end_time': None,
            'total_processing_time': 0,
            'modules_applied': [],
            'data_flow': {
                'rms_input': 0,
                'cad_input': 0,
                'rms_processed': 0,
                'cad_processed': 0,
                'matched_output': 0,
                'filtered_output': 0
            },
            'module_results': {}
        }
        
    def process_rms_complete(self, df: pd.DataFrame, apply_cascade: bool = True) -> pd.DataFrame:
        """
        Complete RMS processing with all modules.
        
        Args:
            df: Input RMS DataFrame
            apply_cascade: Whether to apply datetime cascade logic
            
        Returns:
            Fully processed RMS DataFrame with all enhancements
        """
        self.logger.info(f"Complete RMS processing: {len(df)} records")
        self.system_stats['data_flow']['rms_input'] = len(df)
        
        processed_df = df.copy()
        modules_applied = []
        
        # 1. DateTime cascade processing
        if apply_cascade:
            cascade_columns = ['Incident Date', 'Incident Date_Between', 'Report Date',
                             'Incident Time', 'Incident Time_Between']
            
            if all(col in processed_df.columns for col in cascade_columns):
                self.logger.info("Applying RMS datetime cascade")
                processed_df = self.rms_cascade_processor.cascade_datetime(processed_df)
                modules_applied.append('datetime_cascade')
                self.system_stats['module_results']['rms_cascade'] = self.rms_cascade_processor.generate_cascade_report()
            else:
                self.logger.info("Using existing processed date/time columns")
                
        # 2. Time-of-day and location processing
        if 'incident_time' in processed_df.columns:
            self.logger.info("Applying RMS time-of-day and location processing")
            processed_df = self.time_location_processor.process_time_and_location(processed_df)
            modules_applied.append('time_location_processing')
            
        # 3. Incident type tagging and filtering
        self.logger.info("Applying RMS incident type tagging")
        processed_df = self.incident_filtering_processor.process_incident_tagging(processed_df)
        modules_applied.append('incident_filtering')
        
        # Store module results
        self.system_stats['module_results']['rms_incident_filtering'] = {
            'filtering_analysis': self.incident_filtering_processor.generate_filtering_analysis(processed_df),
            'comparison_results': self.incident_filtering_processor.compare_filtering_methods(processed_df)
        }
        
        self.system_stats['data_flow']['rms_processed'] = len(processed_df)
        self.system_stats['modules_applied'].extend([f"rms_{module}" for module in modules_applied])
        
        self.logger.info(f"Complete RMS processing finished: {len(processed_df)} records, modules: {modules_applied}")
        
        return processed_df
        
    def process_cad_complete(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Complete CAD processing with all modules.
        
        Args:
            df: Input CAD DataFrame
            
        Returns:
            Fully processed CAD DataFrame with all enhancements
        """
        self.logger.info(f"Complete CAD processing: {len(df)} records")
        self.system_stats['data_flow']['cad_input'] = len(df)
        
        processed_df = df.copy()
        modules_applied = []
        
        # 1. CallType mapping and response classification
        self.logger.info("Applying CAD CallType mapping")
        processed_df = self.cad_processor.process_cad_data(processed_df)
        modules_applied.append('calltype_mapping')
        
        # 2. Time-of-day and location processing
        self.logger.info("Applying CAD time-of-day and location processing")
        processed_df = self.time_location_processor.process_time_and_location(processed_df)
        modules_applied.append('time_location_processing')
        
        # 3. Incident type tagging and filtering  
        self.logger.info("Applying CAD incident type tagging")
        processed_df = self.incident_filtering_processor.process_incident_tagging(processed_df)
        modules_applied.append('incident_filtering')
        
        # Store module results
        self.system_stats['module_results']['cad_processing'] = {
            'calltype_mapping': self.cad_processor.generate_mapping_report(),
            'incident_filtering': self.incident_filtering_processor.generate_filtering_analysis(processed_df)
        }
        
        self.system_stats['data_flow']['cad_processed'] = len(processed_df)
        self.system_stats['modules_applied'].extend([f"cad_{module}" for module in modules_applied])
        
        self.logger.info(f"Complete CAD processing finished: {len(processed_df)} records, modules: {modules_applied}")
        
        return processed_df
        
    def match_and_filter_data(self, rms_df: pd.DataFrame, cad_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Match CAD/RMS data and apply incident filtering.
        
        Args:
            rms_df: Processed RMS DataFrame
            cad_df: Processed CAD DataFrame
            
        Returns:
            Dictionary with matched and filtered datasets
        """
        self.logger.info(f"Matching and filtering data - RMS: {len(rms_df)}, CAD: {len(cad_df)}")
        
        # Create matched dataset (RMS as base)
        matched_df = rms_df.copy()
        
        # Add CAD columns that don't exist in RMS
        cad_columns_to_add = [
            'response_type', 'category_type', 'how_reported_clean',
            'cad_notes_cleaned', 'cad_notes_username', 'cad_notes_timestamp'
        ]
        
        for col in cad_columns_to_add:
            if col in cad_df.columns and col not in matched_df.columns:
                matched_df[col] = None
                
        # Perform case number matching
        matches_found = 0
        
        for idx, rms_row in matched_df.iterrows():
            if pd.notna(rms_row.get('case_number')):
                cad_match = cad_df[cad_df.get('case_number', '') == rms_row['case_number']]
                
                if not cad_match.empty:
                    cad_row = cad_match.iloc[0]
                    for col in cad_columns_to_add:
                        if col in cad_df.columns:
                            matched_df.at[idx, col] = cad_row[col]
                    matches_found += 1
                    
        # Filter for tracked crimes only
        tracked_crimes_filter = matched_df['incident_type'].notna()
        filtered_df = matched_df[tracked_crimes_filter].copy()
        
        self.system_stats['data_flow']['matched_output'] = len(matched_df)
        self.system_stats['data_flow']['filtered_output'] = len(filtered_df)
        
        # Store matching results
        self.system_stats['module_results']['matching_filtering'] = {
            'matches_found': matches_found,
            'match_rate': matches_found / len(matched_df) * 100 if len(matched_df) > 0 else 0,
            'tracked_crimes_found': len(filtered_df),
            'filtering_rate': len(filtered_df) / len(matched_df) * 100 if len(matched_df) > 0 else 0
        }
        
        self.logger.info(f"Matching complete: {matches_found} matches ({matches_found/len(matched_df)*100:.1f}%)")
        self.logger.info(f"Tracked crimes filtered: {len(filtered_df)} records ({len(filtered_df)/len(matched_df)*100:.1f}%)")
        
        return {
            'matched_complete': matched_df,
            'tracked_crimes_only': filtered_df
        }
        
    def process_complete_system(self, rms_file: str, cad_file: str) -> Dict[str, Any]:
        """
        Process complete SCRPA v4 system with all modules.
        
        Args:
            rms_file: Path to RMS data file
            cad_file: Path to CAD data file
            
        Returns:
            Complete system results with all datasets and analysis
        """
        self.system_stats['processing_start_time'] = datetime.now()
        self.logger.info("Starting complete SCRPA v4 incident system processing")
        
        try:
            # Load raw data
            rms_df = pd.read_csv(rms_file)
            cad_df = pd.read_csv(cad_file)
            
            self.logger.info(f"Loaded data - RMS: {len(rms_df)} records, CAD: {len(cad_df)} records")
            
            # Process both datasets completely
            processed_rms = self.process_rms_complete(rms_df)
            processed_cad = self.process_cad_complete(cad_df)
            
            # Match and filter data
            matched_results = self.match_and_filter_data(processed_rms, processed_cad)
            
            # Calculate processing time
            self.system_stats['processing_end_time'] = datetime.now()
            self.system_stats['total_processing_time'] = (
                self.system_stats['processing_end_time'] - 
                self.system_stats['processing_start_time']
            ).total_seconds()
            
            # Complete system results
            system_results = {
                'datasets': {
                    'rms_processed': processed_rms,
                    'cad_processed': processed_cad,
                    'matched_complete': matched_results['matched_complete'],
                    'tracked_crimes_only': matched_results['tracked_crimes_only']
                },
                'system_statistics': self.system_stats,
                'quality_assessment': self.generate_system_quality_assessment()
            }
            
            self.logger.info(f"Complete system processing finished in {self.system_stats['total_processing_time']:.2f} seconds")
            
            return system_results
            
        except Exception as e:
            self.logger.error(f"System processing failed: {e}")
            raise
            
    def generate_system_quality_assessment(self) -> Dict[str, Any]:
        """Generate comprehensive system quality assessment."""
        
        assessment = {
            'overall_system_status': 'Unknown',
            'module_performance': {},
            'data_flow_metrics': {},
            'quality_scores': {}
        }
        
        # Data flow metrics
        data_flow = self.system_stats['data_flow']
        assessment['data_flow_metrics'] = {
            'record_preservation_rms': data_flow['rms_processed'] == data_flow['rms_input'],
            'record_preservation_cad': data_flow['cad_processed'] == data_flow['cad_input'],
            'matching_rate': data_flow['matched_output'] / max(data_flow['rms_processed'], 1) * 100,
            'filtering_effectiveness': data_flow['filtered_output'] / max(data_flow['matched_output'], 1) * 100
        }
        
        # Module performance assessment
        module_results = self.system_stats['module_results']
        quality_scores = []
        
        # RMS cascade quality
        if 'rms_cascade' in module_results:
            cascade_effectiveness = module_results['rms_cascade'].get('cascade_effectiveness', {})
            date_rate = cascade_effectiveness.get('date_cascade_rate', 0)
            time_rate = cascade_effectiveness.get('time_cascade_rate', 0)
            
            if date_rate >= 95 and time_rate >= 85:
                assessment['module_performance']['rms_cascade'] = 'Excellent'
                quality_scores.append(95)
            elif date_rate >= 90 and time_rate >= 75:
                assessment['module_performance']['rms_cascade'] = 'Good'
                quality_scores.append(85)
            else:
                assessment['module_performance']['rms_cascade'] = 'Fair'
                quality_scores.append(70)
                
        # CAD processing quality
        if 'cad_processing' in module_results:
            calltype_report = module_results['cad_processing'].get('calltype_mapping', {})
            unmapped_count = calltype_report.get('unmapped_count', 0)
            
            if unmapped_count == 0:
                assessment['module_performance']['cad_processing'] = 'Excellent'
                quality_scores.append(95)
            elif unmapped_count <= 5:
                assessment['module_performance']['cad_processing'] = 'Good'
                quality_scores.append(85)
            else:
                assessment['module_performance']['cad_processing'] = 'Fair'
                quality_scores.append(70)
                
        # Incident filtering quality
        if 'rms_incident_filtering' in module_results:
            filtering_analysis = module_results['rms_incident_filtering'].get('filtering_analysis', {})
            quality_metrics = filtering_analysis.get('quality_metrics', {})
            
            if quality_metrics.get('overall_quality') == 'EXCELLENT':
                assessment['module_performance']['incident_filtering'] = 'Excellent'
                quality_scores.append(95)
            elif quality_metrics.get('discrepancy_acceptable', False):
                assessment['module_performance']['incident_filtering'] = 'Good'
                quality_scores.append(85)
            else:
                assessment['module_performance']['incident_filtering'] = 'Fair'
                quality_scores.append(70)
                
        # Overall system assessment
        if quality_scores:
            avg_score = sum(quality_scores) / len(quality_scores)
            assessment['quality_scores']['average_score'] = avg_score
            
            if avg_score >= 90:
                assessment['overall_system_status'] = 'Excellent'
            elif avg_score >= 80:
                assessment['overall_system_status'] = 'Good'
            else:
                assessment['overall_system_status'] = 'Needs Review'
                
        return assessment


def main():
    """Main execution function for complete system testing."""
    print("Complete SCRPA v4 Incident System")
    print("=" * 35)
    
    try:
        # Initialize system
        system = CompleteSCRPAv4IncidentSystem()
        
        # Define input files
        base_dir = Path(__file__).parent.parent
        rms_file = base_dir / "C08W31_20250803_051051_rms_data_fixed.csv"
        cad_file = base_dir / "C08W31_20250803_051051_cad_data_fixed.csv"
        
        if not rms_file.exists() or not cad_file.exists():
            print(f"ERROR: Input files not found")
            return 1
            
        print(f"Processing files:")
        print(f"  RMS: {rms_file.name}")
        print(f"  CAD: {cad_file.name}")
        
        # Process complete system
        results = system.process_complete_system(str(rms_file), str(cad_file))
        
        # Display system results
        print(f"\n[SYSTEM RESULTS]")
        datasets = results['datasets']
        for dataset_name, dataset in datasets.items():
            print(f"{dataset_name}: {len(dataset)} records")
            
        # Display system statistics
        stats = results['system_statistics']
        print(f"\n[SYSTEM STATISTICS]")
        print(f"Processing time: {stats['total_processing_time']:.2f} seconds")
        print(f"Modules applied: {', '.join(set(stats['modules_applied']))}")
        
        data_flow = stats['data_flow']
        print(f"\nData flow:")
        print(f"  RMS input: {data_flow['rms_input']} -> processed: {data_flow['rms_processed']}")
        print(f"  CAD input: {data_flow['cad_input']} -> processed: {data_flow['cad_processed']}")
        print(f"  Matched output: {data_flow['matched_output']}")
        print(f"  Filtered (tracked crimes): {data_flow['filtered_output']}")
        
        # Display quality assessment
        quality = results['quality_assessment']
        print(f"\n[QUALITY ASSESSMENT]")
        print(f"Overall system status: {quality['overall_system_status']}")
        
        if 'module_performance' in quality:
            print(f"Module performance:")
            for module, performance in quality['module_performance'].items():
                print(f"  {module}: {performance}")
                
        data_flow_metrics = quality['data_flow_metrics']
        print(f"Data flow metrics:")
        print(f"  RMS preservation: {data_flow_metrics['record_preservation_rms']}")
        print(f"  CAD preservation: {data_flow_metrics['record_preservation_cad']}")
        print(f"  Matching rate: {data_flow_metrics['matching_rate']:.1f}%")
        print(f"  Filtering effectiveness: {data_flow_metrics['filtering_effectiveness']:.1f}%")
        
        # Show sample of tracked crimes
        tracked_crimes = datasets['tracked_crimes_only']
        print(f"\n[SAMPLE TRACKED CRIMES]")
        sample_cols = ['case_number', 'incident_date', 'incident_time', 'time_of_day', 
                      'location', 'block', 'incident_type']
        available_cols = [col for col in sample_cols if col in tracked_crimes.columns]
        print(tracked_crimes[available_cols].head(5).to_string())
        
        # Save all datasets
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = base_dir / '03_output'
        output_dir.mkdir(exist_ok=True)
        
        for dataset_name, dataset in datasets.items():
            output_file = output_dir / f"SCRPA_v4_Complete_{dataset_name}_{timestamp}.csv"
            dataset.to_csv(output_file, index=False)
            print(f"\nSaved: {output_file.name}")
            
        print(f"\n[SUCCESS] Complete SCRPA v4 Incident System processing completed!")
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())