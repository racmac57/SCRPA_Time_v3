#!/usr/bin/env python3
"""
RMS Date/Time Cascade Logic
Implements comprehensive date/time cascade logic for RMS data processing.

Author: Crime Analysis Team
Version: 1.0
Date: 2025-08-03
Purpose: Apply 3-tier date cascade and 2-tier time cascade with robust error handling
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, date, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import warnings

warnings.filterwarnings('ignore')

class RMSDateTimeCascadeProcessor:
    """Processes RMS data with comprehensive date/time cascade logic."""
    
    def __init__(self):
        """Initialize the processor with logging."""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Statistics tracking
        self.stats = {
            'original_count': 0,
            'processed_count': 0,
            'date_cascade_stats': {
                'primary_used': 0,
                'between_used': 0,
                'report_used': 0,
                'nulls_remaining': 0
            },
            'time_cascade_stats': {
                'primary_used': 0,
                'between_used': 0,
                'nulls_remaining': 0
            },
            'validation_errors': []
        }
        
    def cascade_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply 3-tier date cascade and 2-tier time cascade with error handling.
        
        Date Cascade: Incident Date → Incident Date_Between → Report Date
        Time Cascade: Incident Time → Incident Time_Between
        
        Args:
            df: DataFrame with required cascade source columns
            
        Returns:
            DataFrame with new incident_date and incident_time columns
        """
        self.logger.info(f"Starting date/time cascade for {len(df)} records")
        original_count = len(df)
        self.stats['original_count'] = original_count
        
        # Validate input DataFrame
        required_columns = ['Incident Date', 'Incident Date_Between', 'Report Date', 
                          'Incident Time', 'Incident Time_Between']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            self.logger.error(f"Missing required columns: {missing_columns}")
            raise ValueError(f"Missing required columns for cascade: {missing_columns}")
            
        # Create working copy
        result_df = df.copy()
        
        # Apply date cascade
        result_df = self._apply_date_cascade(result_df)
        
        # Apply time cascade
        result_df = self._apply_time_cascade(result_df)
        
        # Final validation
        self._validate_cascade_results(original_count, len(result_df))
        
        self.stats['processed_count'] = len(result_df)
        self.logger.info(f"Date/time cascade completed: {len(result_df)} records processed")
        
        return result_df
        
    def _apply_date_cascade(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply 3-tier date cascade with comprehensive error handling."""
        self.logger.info("Applying 3-tier date cascade")
        
        # Track original null counts
        original_nulls = {
            'incident_date': df['Incident Date'].isna().sum(),
            'incident_date_between': df['Incident Date_Between'].isna().sum(),
            'report_date': df['Report Date'].isna().sum()
        }
        
        self.logger.info(f"Original null counts - Incident Date: {original_nulls['incident_date']}, "
                        f"Between: {original_nulls['incident_date_between']}, "
                        f"Report: {original_nulls['report_date']}")
        
        # Step 1: Convert Incident Date with error handling
        incident_date_converted = pd.to_datetime(df['Incident Date'], errors='coerce')
        primary_used = incident_date_converted.notna().sum()
        self.stats['date_cascade_stats']['primary_used'] = primary_used
        
        # Log invalid date strings
        invalid_primary = df.loc[df['Incident Date'].notna() & incident_date_converted.isna(), 'Incident Date']
        if not invalid_primary.empty:
            self.logger.warning(f"Invalid Incident Date strings found: {invalid_primary.unique()}")
            
        # Step 2: Fill with Incident Date_Between
        incident_date_between_converted = pd.to_datetime(df['Incident Date_Between'], errors='coerce')
        
        # Apply fillna for missing primary dates
        cascade_result = incident_date_converted.fillna(incident_date_between_converted)
        between_used = (incident_date_converted.isna() & incident_date_between_converted.notna()).sum()
        self.stats['date_cascade_stats']['between_used'] = between_used
        
        # Log invalid between date strings
        invalid_between = df.loc[df['Incident Date_Between'].notna() & incident_date_between_converted.isna(), 'Incident Date_Between']
        if not invalid_between.empty:
            self.logger.warning(f"Invalid Incident Date_Between strings found: {invalid_between.unique()}")
            
        # Step 3: Fill with Report Date
        report_date_converted = pd.to_datetime(df['Report Date'], errors='coerce')
        
        # Final cascade step
        final_cascade = cascade_result.fillna(report_date_converted)
        report_used = (cascade_result.isna() & report_date_converted.notna()).sum()
        self.stats['date_cascade_stats']['report_used'] = report_used
        
        # Log invalid report date strings
        invalid_report = df.loc[df['Report Date'].notna() & report_date_converted.isna(), 'Report Date']
        if not invalid_report.empty:
            self.logger.warning(f"Invalid Report Date strings found: {invalid_report.unique()}")
            
        # Convert to date objects (remove time component)
        df['incident_date'] = final_cascade.dt.date
        
        # Track final null count
        final_nulls = df['incident_date'].isna().sum()
        self.stats['date_cascade_stats']['nulls_remaining'] = final_nulls
        
        # Log cascade statistics
        self.logger.info(f"Date cascade results:")
        self.logger.info(f"  Primary (Incident Date) used: {primary_used}")
        self.logger.info(f"  Between used: {between_used}")
        self.logger.info(f"  Report Date used: {report_used}")
        self.logger.info(f"  Final nulls remaining: {final_nulls}")
        
        null_reduction = sum(original_nulls.values()) - final_nulls * 3  # Approximate reduction
        self.logger.info(f"  Total null reduction: ~{null_reduction}")
        
        return df
        
    def _apply_time_cascade(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply 2-tier time cascade with error handling."""
        self.logger.info("Applying 2-tier time cascade")
        
        # Track original null counts
        original_nulls = {
            'incident_time': df['Incident Time'].isna().sum(),
            'incident_time_between': df['Incident Time_Between'].isna().sum()
        }
        
        self.logger.info(f"Original time null counts - Incident Time: {original_nulls['incident_time']}, "
                        f"Between: {original_nulls['incident_time_between']}")
        
        # Step 1: Convert Incident Time with error handling
        incident_time_converted = pd.to_datetime(df['Incident Time'], errors='coerce')
        primary_used = incident_time_converted.notna().sum()
        self.stats['time_cascade_stats']['primary_used'] = primary_used
        
        # Extract time component
        df['incident_time'] = incident_time_converted.dt.time
        
        # Log invalid time strings
        invalid_primary_time = df.loc[df['Incident Time'].notna() & incident_time_converted.isna(), 'Incident Time']
        if not invalid_primary_time.empty:
            self.logger.warning(f"Invalid Incident Time strings found: {invalid_primary_time.unique()}")
            
        # Step 2: Fill missing times with Incident Time_Between
        mask = df['incident_time'].isna()
        if mask.any():
            incident_time_between_converted = pd.to_datetime(
                df.loc[mask, 'Incident Time_Between'], errors='coerce'
            )
            
            df.loc[mask, 'incident_time'] = incident_time_between_converted.dt.time
            between_used = incident_time_between_converted.notna().sum()
            self.stats['time_cascade_stats']['between_used'] = between_used
            
            # Log invalid between time strings
            between_mask = df['Incident Time_Between'].notna() & mask
            invalid_between_time = df.loc[between_mask & df.loc[mask, 'incident_time'].isna(), 'Incident Time_Between']
            if not invalid_between_time.empty:
                self.logger.warning(f"Invalid Incident Time_Between strings found: {invalid_between_time.unique()}")
        else:
            between_used = 0
            self.stats['time_cascade_stats']['between_used'] = between_used
            
        # Track final null count
        final_nulls = df['incident_time'].isna().sum()
        self.stats['time_cascade_stats']['nulls_remaining'] = final_nulls
        
        # Log time cascade statistics
        self.logger.info(f"Time cascade results:")
        self.logger.info(f"  Primary (Incident Time) used: {primary_used}")
        self.logger.info(f"  Between used: {between_used}")
        self.logger.info(f"  Final nulls remaining: {final_nulls}")
        
        null_reduction = sum(original_nulls.values()) - final_nulls * 2  # Approximate reduction
        self.logger.info(f"  Total null reduction: ~{null_reduction}")
        
        return df
        
    def _validate_cascade_results(self, original_count: int, processed_count: int) -> None:
        """Validate cascade processing results."""
        if processed_count != original_count:
            error_msg = f"Row count changed during cascade: {original_count} -> {processed_count}"
            self.stats['validation_errors'].append(error_msg)
            self.logger.error(error_msg)
            raise AssertionError(error_msg)
            
        self.logger.info("✅ Validation passed: Row count unchanged")
        
    def generate_cascade_report(self) -> Dict[str, Any]:
        """Generate comprehensive cascade processing report."""
        report = {
            'processing_summary': {
                'original_records': self.stats['original_count'],
                'processed_records': self.stats['processed_count'],
                'record_preservation': self.stats['processed_count'] == self.stats['original_count']
            },
            'date_cascade_summary': self.stats['date_cascade_stats'],
            'time_cascade_summary': self.stats['time_cascade_stats'],
            'validation_errors': self.stats['validation_errors'],
            'cascade_effectiveness': {
                'date_cascade_rate': 0,
                'time_cascade_rate': 0
            }
        }
        
        # Calculate effectiveness rates
        total_records = self.stats['original_count']
        if total_records > 0:
            date_stats = self.stats['date_cascade_stats']
            time_stats = self.stats['time_cascade_stats']
            
            date_filled = date_stats['primary_used'] + date_stats['between_used'] + date_stats['report_used']
            time_filled = time_stats['primary_used'] + time_stats['between_used']
            
            report['cascade_effectiveness']['date_cascade_rate'] = (date_filled / total_records) * 100
            report['cascade_effectiveness']['time_cascade_rate'] = (time_filled / total_records) * 100
            
        return report
        
    def validate_processing(self, original_df: pd.DataFrame, processed_df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the overall processing results."""
        validation = {
            'record_count_preserved': len(original_df) == len(processed_df),
            'original_records': len(original_df),
            'processed_records': len(processed_df),
            'new_columns_added': [],
            'cascade_coverage': {}
        }
        
        # Check for new columns
        original_cols = set(original_df.columns)
        processed_cols = set(processed_df.columns)
        validation['new_columns_added'] = sorted(list(processed_cols - original_cols))
        
        # Check cascade coverage
        if 'incident_date' in processed_df.columns:
            date_filled = processed_df['incident_date'].notna().sum()
            date_coverage = date_filled / len(processed_df) * 100 if len(processed_df) > 0 else 0
            
            validation['cascade_coverage']['date'] = {
                'filled_records': int(date_filled),
                'total_records': len(processed_df),
                'coverage_rate': float(date_coverage),
                'target_met': date_coverage >= 95.0  # 95% target
            }
            
        if 'incident_time' in processed_df.columns:
            time_filled = processed_df['incident_time'].notna().sum()
            time_coverage = time_filled / len(processed_df) * 100 if len(processed_df) > 0 else 0
            
            validation['cascade_coverage']['time'] = {
                'filled_records': int(time_filled),
                'total_records': len(processed_df),
                'coverage_rate': float(time_coverage),
                'target_met': time_coverage >= 85.0  # 85% target (time is often optional)
            }
            
        return validation


def create_sample_rms_data() -> pd.DataFrame:
    """Create sample RMS data with cascade scenarios for testing."""
    sample_data = {
        'Case Number': ['25-001234', '25-001235', '25-001236', '25-001237', '25-001238'],
        'Incident Date': ['2024-12-15', np.nan, '2024-12-17', 'invalid-date', np.nan],
        'Incident Date_Between': [np.nan, '2024-12-16', np.nan, '2024-12-18', np.nan],
        'Report Date': ['2024-12-16', '2024-12-17', '2024-12-18', '2024-12-19', '2024-12-20'],
        'Incident Time': ['14:30:00', np.nan, '09:15:30', 'invalid-time', '16:45:00'],
        'Incident Time_Between': [np.nan, '10:20:00', np.nan, '11:30:00', np.nan],
        'Incident Type': ['Burglary', 'Theft', 'Assault', 'Vandalism', 'Robbery'],
        'Location': ['Main St', 'Oak Ave', 'Pine Rd', 'Elm St', 'Cedar Ave']
    }
    
    return pd.DataFrame(sample_data)


def main():
    """Main execution function for testing."""
    print("RMS Date/Time Cascade Logic Processor")
    print("=" * 40)
    
    try:
        # Initialize processor
        processor = RMSDateTimeCascadeProcessor()
        
        # Create sample data for demonstration
        print("Creating sample RMS data with cascade scenarios...")
        sample_df = create_sample_rms_data()
        
        print(f"Sample data created: {len(sample_df)} records")
        print("\nOriginal data:")
        print(sample_df[['Case Number', 'Incident Date', 'Incident Date_Between', 
                        'Report Date', 'Incident Time', 'Incident Time_Between']].to_string())
        
        # Process the data
        print(f"\nProcessing cascade logic...")
        processed_df = processor.cascade_datetime(sample_df)
        
        print(f"\nProcessed data:")
        print(processed_df[['Case Number', 'incident_date', 'incident_time']].to_string())
        
        # Generate reports
        cascade_report = processor.generate_cascade_report()
        validation_report = processor.validate_processing(sample_df, processed_df)
        
        # Display results
        print(f"\nCascade Report:")
        print(f"  Records processed: {cascade_report['processing_summary']['processed_records']}")
        print(f"  Record preservation: {cascade_report['processing_summary']['record_preservation']}")
        
        date_stats = cascade_report['date_cascade_summary']
        print(f"  Date cascade - Primary: {date_stats['primary_used']}, Between: {date_stats['between_used']}, Report: {date_stats['report_used']}")
        print(f"  Date coverage: {cascade_report['cascade_effectiveness']['date_cascade_rate']:.1f}%")
        
        time_stats = cascade_report['time_cascade_summary'] 
        print(f"  Time cascade - Primary: {time_stats['primary_used']}, Between: {time_stats['between_used']}")
        print(f"  Time coverage: {cascade_report['cascade_effectiveness']['time_cascade_rate']:.1f}%")
        
        print(f"\nValidation Report:")
        print(f"  Record preservation: {validation_report['record_count_preserved']}")
        print(f"  New columns added: {validation_report['new_columns_added']}")
        
        if 'date' in validation_report['cascade_coverage']:
            date_cov = validation_report['cascade_coverage']['date']
            print(f"  Date coverage: {date_cov['coverage_rate']:.1f}% ({date_cov['filled_records']}/{date_cov['total_records']})")
            print(f"  Date target met (95%): {'[PASS]' if date_cov['target_met'] else '[FAIL]'}")
            
        if 'time' in validation_report['cascade_coverage']:
            time_cov = validation_report['cascade_coverage']['time']
            print(f"  Time coverage: {time_cov['coverage_rate']:.1f}% ({time_cov['filled_records']}/{time_cov['total_records']})")
            print(f"  Time target met (85%): {'[PASS]' if time_cov['target_met'] else '[FAIL]'}")
        
        # Save processed sample
        output_file = Path(__file__).parent.parent / f"RMS_DateTime_Cascade_Sample_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        processed_df.to_csv(output_file, index=False)
        print(f"\nSample output saved: {output_file.name}")
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())