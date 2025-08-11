#!/usr/bin/env python3
"""
Complete RMS DateTime Processor
Comprehensive RMS data processing with datetime cascade logic integration.

Author: Crime Analysis Team  
Version: 1.0
Date: 2025-08-03
Purpose: Complete RMS processing pipeline with proven cascade logic
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, date, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import warnings

# Import the cascade processor
from RMS_DateTime_Cascade_Processor import RMSDateTimeCascadeProcessor

warnings.filterwarnings('ignore')

class CompleteRMSProcessor:
    """Complete RMS data processor with datetime cascade integration."""
    
    def __init__(self, base_dir: str = None):
        """Initialize the complete RMS processor."""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize cascade processor
        self.cascade_processor = RMSDateTimeCascadeProcessor()
        
        # Processing statistics
        self.stats = {
            'input_records': 0,
            'output_records': 0,
            'cascade_results': {},
            'processing_time': 0,
            'validation_results': {}
        }
        
    def process_rms_data(self, df: pd.DataFrame, apply_cascade: bool = True) -> pd.DataFrame:
        """
        Process RMS data with optional datetime cascade logic.
        
        Args:
            df: Input RMS DataFrame
            apply_cascade: Whether to apply datetime cascade logic
            
        Returns:
            Processed RMS DataFrame with datetime cascade applied
        """
        start_time = datetime.now()
        self.logger.info(f"Starting complete RMS processing: {len(df)} records")
        
        self.stats['input_records'] = len(df)
        
        # Create working copy
        processed_df = df.copy()
        
        # Apply datetime cascade if requested and columns are available
        if apply_cascade:
            cascade_columns = ['Incident Date', 'Incident Date_Between', 'Report Date',
                             'Incident Time', 'Incident Time_Between']
            
            if all(col in processed_df.columns for col in cascade_columns):
                self.logger.info("Applying datetime cascade logic")
                processed_df = self.cascade_processor.cascade_datetime(processed_df)
                
                # Store cascade results
                self.stats['cascade_results'] = self.cascade_processor.generate_cascade_report()
                
            else:
                self.logger.warning(f"Cascade columns not found. Available: {list(processed_df.columns)}")
                
                # If cascade columns don't exist but we have processed date/time, use them
                if 'incident_date' in processed_df.columns and 'incident_time' in processed_df.columns:
                    self.logger.info("Using existing processed date/time columns")
                else:
                    self.logger.error("No date/time columns available for processing")
                    
        # Additional RMS processing can be added here
        processed_df = self._apply_additional_processing(processed_df)
        
        # Final validation
        self.stats['output_records'] = len(processed_df)
        
        # Calculate processing time
        end_time = datetime.now()
        self.stats['processing_time'] = (end_time - start_time).total_seconds()
        
        self.logger.info(f"RMS processing completed: {len(processed_df)} records in {self.stats['processing_time']:.2f} seconds")
        
        return processed_df
        
    def _apply_additional_processing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply additional RMS data processing beyond cascade logic."""
        
        # Ensure we have date/time columns
        if 'incident_date' not in df.columns or 'incident_time' not in df.columns:
            self.logger.warning("incident_date or incident_time columns missing - skipping additional processing")
            return df
            
        # Add time of day categorization
        if 'incident_time' in df.columns:
            df = self._categorize_time_of_day(df)
            
        # Add day of week and period information
        if 'incident_date' in df.columns:
            df = self._add_temporal_features(df)
            
        # Validate date/time consistency
        df = self._validate_datetime_consistency(df)
        
        return df
        
    def _categorize_time_of_day(self, df: pd.DataFrame) -> pd.DataFrame:
        """Categorize incident time into time of day periods."""
        
        def get_time_category(time_val):
            if pd.isna(time_val):
                return "Unknown"
                
            try:
                if isinstance(time_val, str):
                    time_obj = datetime.strptime(time_val, '%H:%M:%S').time()
                elif isinstance(time_val, time):
                    time_obj = time_val
                else:
                    return "Unknown"
                    
                hour = time_obj.hour
                
                if 6 <= hour < 12:
                    return "Morning"
                elif 12 <= hour < 17:
                    return "Afternoon"
                elif 17 <= hour < 21:
                    return "Evening"
                else:
                    return "Night"
                    
            except Exception:
                return "Unknown"
                
        df['time_of_day'] = df['incident_time'].apply(get_time_category)
        
        # Add sort order for time periods
        time_order = {"Morning": 1, "Afternoon": 2, "Evening": 3, "Night": 4, "Unknown": 5}
        df['time_of_day_sort_order'] = df['time_of_day'].map(time_order)
        
        return df
        
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add temporal features based on incident date."""
        
        # Convert to datetime if needed
        if df['incident_date'].dtype == 'object':
            df['incident_date_dt'] = pd.to_datetime(df['incident_date'], errors='coerce')
        else:
            df['incident_date_dt'] = pd.to_datetime(df['incident_date'], errors='coerce')
            
        # Day of week
        df['day_of_week'] = df['incident_date_dt'].dt.day_name()
        
        # Day type (Weekday/Weekend)
        df['day_type'] = df['incident_date_dt'].dt.dayofweek.apply(
            lambda x: 'Weekend' if x >= 5 else 'Weekday'
        )
        
        # Season
        def get_season(date_val):
            if pd.isna(date_val):
                return "Unknown"
            month = date_val.month
            if month in [12, 1, 2]:
                return "Winter"
            elif month in [3, 4, 5]:
                return "Spring"
            elif month in [6, 7, 8]:
                return "Summer"
            else:
                return "Fall"
                
        df['season'] = df['incident_date_dt'].apply(get_season)
        
        # Period (for reporting cycles)
        df['period'] = df['incident_date_dt'].dt.strftime('%Y-W%U')
        
        # Clean up temporary column
        df = df.drop(columns=['incident_date_dt'])
        
        return df
        
    def _validate_datetime_consistency(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate date/time consistency and flag anomalies."""
        
        validation_issues = []
        
        # Check for future dates
        current_date = datetime.now().date()
        if 'incident_date' in df.columns:
            future_dates = df['incident_date'] > current_date
            if future_dates.any():
                count = future_dates.sum()
                validation_issues.append(f"Future dates found: {count} records")
                self.logger.warning(f"Found {count} records with future incident dates")
                
        # Check for very old dates (more than 2 years)
        if 'incident_date' in df.columns:
            cutoff_date = datetime.now().date().replace(year=datetime.now().year - 2)
            old_dates = df['incident_date'] < cutoff_date
            if old_dates.any():
                count = old_dates.sum()
                validation_issues.append(f"Very old dates found: {count} records")
                self.logger.warning(f"Found {count} records with dates older than 2 years")
                
        # Store validation issues
        self.stats['validation_issues'] = validation_issues
        
        return df
        
    def generate_processing_report(self) -> Dict[str, Any]:
        """Generate comprehensive processing report."""
        
        report = {
            'processing_summary': {
                'input_records': self.stats['input_records'],
                'output_records': self.stats['output_records'],
                'processing_time_seconds': self.stats['processing_time'],
                'record_preservation': self.stats['output_records'] == self.stats['input_records']
            },
            'cascade_results': self.stats.get('cascade_results', {}),
            'validation_issues': self.stats.get('validation_issues', []),
            'quality_metrics': {
                'date_coverage': 0,
                'time_coverage': 0,
                'overall_data_quality': 'Unknown'
            }
        }
        
        # Calculate quality metrics if cascade results are available
        if self.stats.get('cascade_results'):
            cascade_effectiveness = self.stats['cascade_results'].get('cascade_effectiveness', {})
            report['quality_metrics']['date_coverage'] = cascade_effectiveness.get('date_cascade_rate', 0)
            report['quality_metrics']['time_coverage'] = cascade_effectiveness.get('time_cascade_rate', 0)
            
            # Overall quality assessment
            date_rate = cascade_effectiveness.get('date_cascade_rate', 0)
            time_rate = cascade_effectiveness.get('time_cascade_rate', 0)
            
            if date_rate >= 95 and time_rate >= 85:
                report['quality_metrics']['overall_data_quality'] = 'Excellent'
            elif date_rate >= 90 and time_rate >= 75:
                report['quality_metrics']['overall_data_quality'] = 'Good'
            elif date_rate >= 80 and time_rate >= 60:
                report['quality_metrics']['overall_data_quality'] = 'Fair'
            else:
                report['quality_metrics']['overall_data_quality'] = 'Poor'
                
        return report


def main():
    """Main execution function for testing complete RMS processing."""
    print("Complete RMS DateTime Processor")
    print("=" * 35)
    
    try:
        # Initialize processor
        processor = CompleteRMSProcessor()
        
        # Test with sample data (using the cascade processor's sample function)
        from RMS_DateTime_Cascade_Processor import create_sample_rms_data
        
        print("Testing with sample RMS data...")
        sample_df = create_sample_rms_data()
        
        print(f"Sample data: {len(sample_df)} records")
        print("\nOriginal sample:")
        print(sample_df[['Case Number', 'Incident Date', 'Incident Time', 'Incident Type']].to_string())
        
        # Process the data
        processed_df = processor.process_rms_data(sample_df, apply_cascade=True)
        
        print(f"\nProcessed data: {len(processed_df)} records")
        print("\nProcessed sample:")
        display_cols = ['Case Number', 'incident_date', 'incident_time', 'time_of_day', 'day_of_week']
        print(processed_df[display_cols].to_string())
        
        # Generate comprehensive report
        report = processor.generate_processing_report()
        
        print(f"\n[PROCESSING REPORT]")
        print(f"Input records: {report['processing_summary']['input_records']}")
        print(f"Output records: {report['processing_summary']['output_records']}")
        print(f"Processing time: {report['processing_summary']['processing_time_seconds']:.2f} seconds")
        print(f"Record preservation: {report['processing_summary']['record_preservation']}")
        
        if report['cascade_results']:
            print(f"\n[CASCADE RESULTS]")
            cascade_summary = report['cascade_results']['processing_summary']
            print(f"Records processed: {cascade_summary['processed_records']}")
            
            effectiveness = report['cascade_results']['cascade_effectiveness']
            print(f"Date coverage: {effectiveness['date_cascade_rate']:.1f}%")
            print(f"Time coverage: {effectiveness['time_cascade_rate']:.1f}%")
            
        print(f"\n[QUALITY METRICS]")
        quality = report['quality_metrics']
        print(f"Date coverage: {quality['date_coverage']:.1f}%")
        print(f"Time coverage: {quality['time_coverage']:.1f}%")
        print(f"Overall data quality: {quality['overall_data_quality']}")
        
        if report['validation_issues']:
            print(f"\n[VALIDATION ISSUES]")
            for issue in report['validation_issues']:
                print(f"  - {issue}")
        else:
            print(f"\n[VALIDATION] No issues found")
            
        # Save processed data
        output_file = Path(__file__).parent.parent / f"Complete_RMS_Processed_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        processed_df.to_csv(output_file, index=False)
        print(f"\nProcessed data saved: {output_file.name}")
        
        print(f"\n[SUCCESS] Complete RMS processing test completed!")
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())