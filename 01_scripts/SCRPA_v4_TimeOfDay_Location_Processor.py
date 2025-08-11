#!/usr/bin/env python3
"""
SCRPA v4 Time-of-Day and Location Processor
Implements standardized time-of-day buckets and location processing.

Author: Crime Analysis Team
Version: 4.0
Date: 2025-08-03
Purpose: Standardized time-of-day categorization and block address calculation
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings
import re

warnings.filterwarnings('ignore')

class SCRPAv4TimeLocationProcessor:
    """SCRPA v4 processor for time-of-day and location standardization."""
    
    def __init__(self):
        """Initialize the processor with logging and configuration."""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Standardized time-of-day categories with exact order
        self.TOD_ORDER = [
            "00:00–03:59 Early Morning",
            "04:00–07:59 Morning", 
            "08:00–11:59 Morning Peak",
            "12:00–15:59 Afternoon",
            "16:00–19:59 Evening Peak", 
            "20:00–23:59 Night",
            "Unknown"
        ]
        
        # Processing statistics
        self.stats = {
            'records_processed': 0,
            'time_categorization': {
                'successful': 0,
                'unknown': 0,
                'invalid': 0
            },
            'location_processing': {
                'intersections': 0,
                'blocks_calculated': 0,
                'check_location_data': 0,
                'standardized_addresses': 0
            }
        }
        
    def map_tod(self, t: Union[pd.Timestamp, time, str, None]) -> str:
        """
        Map time to standardized time-of-day category.
        
        Args:
            t: Time value (Timestamp, time object, string, or None)
            
        Returns:
            Standardized time-of-day category string
        """
        if pd.isna(t):
            return "Unknown"
            
        try:
            # Handle different time input types
            if isinstance(t, pd.Timestamp):
                hour = t.hour
            elif isinstance(t, time):
                hour = t.hour
            elif isinstance(t, str):
                # Try to parse string time formats
                if ':' in t:
                    time_parts = t.split(':')
                    hour = int(time_parts[0])
                else:
                    return "Unknown"
            else:
                return "Unknown"
                
            # Apply standardized time-of-day buckets
            if hour < 4:
                return "00:00–03:59 Early Morning"
            elif hour < 8:
                return "04:00–07:59 Morning"
            elif hour < 12:
                return "08:00–11:59 Morning Peak"
            elif hour < 16:
                return "12:00–15:59 Afternoon"
            elif hour < 20:
                return "16:00–19:59 Evening Peak"
            else:
                return "20:00–23:59 Night"
                
        except (ValueError, AttributeError, IndexError) as e:
            self.logger.warning(f"Invalid time format: {t} - {e}")
            return "Unknown"
            
    def calculate_block(self, addr: Union[str, None]) -> str:
        """
        Calculate block address with intersection handling.
        
        Args:
            addr: Address string
            
        Returns:
            Formatted block address or error message
        """
        if pd.isna(addr) or not addr:
            return "Check Location Data"
            
        try:
            # Clean and standardize address
            address_clean = str(addr).replace(", Hackensack, NJ, 07601", "").strip()
            
            # Handle intersections with " & " syntax
            if " & " in address_clean:
                parts = [p.strip() for p in address_clean.split(" & ")]
                if len(parts) == 2:
                    # Clean each part to remove house numbers if present
                    clean_parts = []
                    for part in parts:
                        # If part starts with a number, remove it
                        words = part.split()
                        if words and words[0].isdigit():
                            clean_parts.append(' '.join(words[1:]))
                        else:
                            clean_parts.append(part)
                    
                    # Return intersection format: "STREET1 & STREET2"
                    return " & ".join(clean_parts)
                else:
                    return "Incomplete Address - Check Location Data"
                    
            # Handle regular numbered addresses
            try:
                # Split address into number and street
                address_parts = address_clean.split(" ", 1)
                if len(address_parts) < 2:
                    return "Check Location Data"
                    
                num_str, street_part = address_parts
                
                # Convert number to integer
                num = int(num_str)
                
                # Calculate block (round down to nearest hundred)
                block = (num // 100) * 100
                
                # Clean street name (remove comma and everything after)
                street_name = street_part.split(',', 1)[0].strip()
                
                # Format as "STREET NAME, XXX Block"
                return f"{street_name}, {block} Block"
                
            except (ValueError, IndexError):
                # If number parsing fails, return error message
                return "Check Location Data"
                
        except Exception as e:
            self.logger.warning(f"Block calculation error for '{addr}': {e}")
            return "Check Location Data"
            
    def standardize_location_field(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize location fields from CAD FullAddress2 or RMS FullAddress to location.
        
        Args:
            df: DataFrame with location columns
            
        Returns:
            DataFrame with standardized location column
        """
        result_df = df.copy()
        
        # Check for available location columns
        location_columns = ['FullAddress2', 'FullAddress', 'location', 'full_address']
        available_columns = [col for col in location_columns if col in result_df.columns]
        
        if not available_columns:
            self.logger.warning(f"No location columns found. Checked: {location_columns}")
            result_df['location'] = "Check Location Data"
            return result_df
            
        # Use the first available location column
        source_column = available_columns[0]
        self.logger.info(f"Using location column: {source_column}")
        
        # Standardize to 'location' column
        if source_column != 'location':
            result_df['location'] = result_df[source_column]
            
        # Clean and standardize location data
        result_df['location'] = result_df['location'].fillna("Check Location Data")
        
        self.stats['location_processing']['standardized_addresses'] = len(result_df)
        
        return result_df
        
    def process_time_and_location(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process DataFrame to add time-of-day and location columns.
        
        Args:
            df: Input DataFrame with incident_time and location columns
            
        Returns:
            Enhanced DataFrame with new columns
        """
        self.logger.info(f"Processing time-of-day and location for {len(df)} records")
        self.stats['records_processed'] = len(df)
        
        # Create working copy
        result_df = df.copy()
        
        # Standardize location field first
        result_df = self.standardize_location_field(result_df)
        
        # Process time-of-day categorization
        if 'incident_time' in result_df.columns:
            self.logger.info("Processing time-of-day categorization")
            
            # Apply time-of-day mapping
            result_df['time_of_day'] = result_df['incident_time'].apply(self.map_tod)
            
            # Create categorical with proper ordering
            result_df['time_of_day'] = pd.Categorical(
                result_df['time_of_day'], 
                categories=self.TOD_ORDER, 
                ordered=True
            )
            
            # Add sort order (1-based indexing)
            result_df['time_of_day_sort_order'] = result_df['time_of_day'].cat.codes + 1
            
            # Count statistics
            tod_counts = result_df['time_of_day'].value_counts()
            self.stats['time_categorization']['successful'] = len(result_df) - tod_counts.get('Unknown', 0)
            self.stats['time_categorization']['unknown'] = tod_counts.get('Unknown', 0)
            
            self.logger.info(f"Time categorization: {self.stats['time_categorization']['successful']} successful, "
                           f"{self.stats['time_categorization']['unknown']} unknown")
            
        else:
            self.logger.warning("'incident_time' column not found")
            result_df['time_of_day'] = "Unknown"
            result_df['time_of_day_sort_order'] = 7  # Unknown category
            
        # Process block calculation
        if 'location' in result_df.columns:
            self.logger.info("Processing block calculation")
            
            # Apply block calculation
            result_df['block'] = result_df['location'].apply(self.calculate_block)
            
            # Count statistics
            block_counts = result_df['block'].value_counts()
            
            # Count intersections (containing " & ")
            intersections = result_df['block'].str.contains(" & ", na=False).sum()
            self.stats['location_processing']['intersections'] = intersections
            
            # Count successful blocks (not error messages)
            error_messages = ["Check Location Data", "Incomplete Address - Check Location Data"]
            check_location_count = sum(block_counts.get(msg, 0) for msg in error_messages)
            self.stats['location_processing']['check_location_data'] = check_location_count
            self.stats['location_processing']['blocks_calculated'] = len(result_df) - check_location_count
            
            self.logger.info(f"Block processing: {self.stats['location_processing']['blocks_calculated']} calculated, "
                           f"{intersections} intersections, {check_location_count} need review")
            
        else:
            self.logger.warning("'location' column not found")
            result_df['block'] = "Check Location Data"
            
        return result_df
        
    def validate_processing(self, original_df: pd.DataFrame, processed_df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the processing results."""
        validation = {
            'record_count_preserved': len(original_df) == len(processed_df),
            'original_records': len(original_df),
            'processed_records': len(processed_df),
            'new_columns_added': [],
            'time_categorization_stats': {},
            'location_processing_stats': {},
            'categorical_ordering_test': {}
        }
        
        # Check for new columns
        original_cols = set(original_df.columns)
        processed_cols = set(processed_df.columns)
        validation['new_columns_added'] = sorted(list(processed_cols - original_cols))
        
        # Validate time categorization
        if 'time_of_day' in processed_df.columns:
            tod_distribution = processed_df['time_of_day'].value_counts()
            validation['time_categorization_stats'] = {
                'categories_used': len(tod_distribution),
                'unknown_count': int(tod_distribution.get('Unknown', 0)),
                'unknown_rate': float(tod_distribution.get('Unknown', 0) / len(processed_df) * 100),
                'most_common_category': str(tod_distribution.index[0]) if not tod_distribution.empty else None
            }
            
            # Test categorical ordering
            if processed_df['time_of_day'].dtype.name == 'category':
                validation['categorical_ordering_test'] = {
                    'is_categorical': True,
                    'is_ordered': processed_df['time_of_day'].dtype.ordered,
                    'categories_match': list(processed_df['time_of_day'].dtype.categories) == self.TOD_ORDER,
                    'sort_order_consistent': True  # Will validate this below
                }
                
                # Test sort order consistency
                if 'time_of_day_sort_order' in processed_df.columns:
                    sort_test = processed_df.groupby('time_of_day')['time_of_day_sort_order'].nunique()
                    validation['categorical_ordering_test']['sort_order_consistent'] = (sort_test == 1).all()
                    
        # Validate location processing  
        if 'block' in processed_df.columns:
            block_distribution = processed_df['block'].value_counts()
            intersections = processed_df['block'].str.contains(" & ", na=False).sum()
            blocks_with_numbers = processed_df['block'].str.contains(r"\d+ Block", na=False).sum()
            
            validation['location_processing_stats'] = {
                'total_addresses': len(processed_df),
                'intersections_found': int(intersections),
                'numeric_blocks_found': int(blocks_with_numbers),
                'check_location_data_count': int(block_distribution.get('Check Location Data', 0)),
                'processing_success_rate': float((len(processed_df) - block_distribution.get('Check Location Data', 0)) / len(processed_df) * 100)
            }
            
        return validation
        
    def generate_processing_report(self) -> Dict[str, Any]:
        """Generate comprehensive processing report."""
        report = {
            'processing_summary': {
                'records_processed': self.stats['records_processed'],
                'processing_modules': ['time_categorization', 'location_processing']
            },
            'time_categorization_results': self.stats['time_categorization'],
            'location_processing_results': self.stats['location_processing'],
            'quality_metrics': {
                'time_categorization_rate': 0,
                'location_processing_rate': 0,
                'overall_success_rate': 0
            }
        }
        
        # Calculate quality metrics
        total_records = self.stats['records_processed']
        if total_records > 0:
            time_success = self.stats['time_categorization']['successful']
            location_success = self.stats['location_processing']['blocks_calculated']
            
            report['quality_metrics']['time_categorization_rate'] = (time_success / total_records) * 100
            report['quality_metrics']['location_processing_rate'] = (location_success / total_records) * 100
            report['quality_metrics']['overall_success_rate'] = ((time_success + location_success) / (total_records * 2)) * 100
            
        return report


def create_sample_data() -> pd.DataFrame:
    """Create sample data for testing time-of-day and location processing."""
    sample_data = {
        'case_number': ['25-001001', '25-001002', '25-001003', '25-001004', '25-001005', '25-001006', '25-001007'],
        'incident_time': [
            time(14, 30, 0),      # Afternoon
            time(2, 15, 0),       # Early Morning
            time(9, 45, 0),       # Morning Peak
            time(18, 20, 0),      # Evening Peak
            time(22, 0, 0),       # Night
            time(6, 30, 0),       # Morning
            None                   # Unknown
        ],
        'location': [
            "456 OAK AVE, Hackensack, NJ, 07601",         # Block calculation
            "123 MAIN ST & ELM ST",                        # Intersection
            "789 PINE RD, Hackensack, NJ, 07601",         # Block calculation
            "CEDAR AVE & FIRST ST",                       # Intersection
            "234 WASHINGTON ST, Hackensack, NJ, 07601",   # Block calculation
            "INCOMPLETE ADDRESS",                          # Error case
            None                                           # Missing data
        ],
        'incident_type': ['Burglary', 'Theft', 'Assault', 'Vandalism', 'Robbery', 'Disturbance', 'Traffic']
    }
    
    return pd.DataFrame(sample_data)


def main():
    """Main execution function for testing."""
    print("SCRPA v4 Time-of-Day and Location Processor")
    print("=" * 45)
    
    try:
        # Initialize processor
        processor = SCRPAv4TimeLocationProcessor()
        
        # Create sample data
        print("Creating sample test data...")
        sample_df = create_sample_data()
        
        print(f"Sample data: {len(sample_df)} records")
        print("\nOriginal data:")
        print(sample_df[['case_number', 'incident_time', 'location']].to_string())
        
        # Process the data
        print(f"\nProcessing time-of-day and location...")
        processed_df = processor.process_time_and_location(sample_df)
        
        print(f"\nProcessed data: {len(processed_df)} records")
        print("\nTime-of-Day Results:")
        display_cols = ['case_number', 'incident_time', 'time_of_day', 'time_of_day_sort_order']
        print(processed_df[display_cols].to_string())
        
        print(f"\nLocation Processing Results:")
        location_cols = ['case_number', 'location', 'block']
        print(processed_df[location_cols].to_string())
        
        # Test categorical ordering
        print(f"\nCategorical Ordering Test:")
        print(f"Time-of-Day Categories: {list(processed_df['time_of_day'].dtype.categories)}")
        print(f"Is Ordered: {processed_df['time_of_day'].dtype.ordered}")
        print(f"Sort Order Test:")
        sorted_test = processed_df.sort_values('time_of_day_sort_order')[['time_of_day', 'time_of_day_sort_order']].drop_duplicates()
        print(sorted_test.to_string())
        
        # Generate reports
        processing_report = processor.generate_processing_report()
        validation_report = processor.validate_processing(sample_df, processed_df)
        
        # Display results
        print(f"\n[PROCESSING REPORT]")
        print(f"Records processed: {processing_report['processing_summary']['records_processed']}")
        
        time_results = processing_report['time_categorization_results']
        print(f"\nTime Categorization:")
        print(f"  Successful: {time_results['successful']}")
        print(f"  Unknown: {time_results['unknown']}")
        print(f"  Success rate: {processing_report['quality_metrics']['time_categorization_rate']:.1f}%")
        
        location_results = processing_report['location_processing_results']
        print(f"\nLocation Processing:")
        print(f"  Blocks calculated: {location_results['blocks_calculated']}")
        print(f"  Intersections: {location_results['intersections']}")
        print(f"  Need review: {location_results['check_location_data']}")
        print(f"  Success rate: {processing_report['quality_metrics']['location_processing_rate']:.1f}%")
        
        print(f"\n[VALIDATION REPORT]")
        print(f"Record preservation: {validation_report['record_count_preserved']}")
        print(f"New columns: {validation_report['new_columns_added']}")
        
        if 'time_categorization_stats' in validation_report:
            time_stats = validation_report['time_categorization_stats']
            print(f"Time categories used: {time_stats['categories_used']}")
            print(f"Unknown rate: {time_stats['unknown_rate']:.1f}%")
            print(f"Most common: {time_stats['most_common_category']}")
            
        if 'categorical_ordering_test' in validation_report:
            cat_test = validation_report['categorical_ordering_test']
            print(f"Categorical ordering: {'[PASS]' if cat_test['categories_match'] and cat_test['is_ordered'] else '[FAIL]'}")
            
        if 'location_processing_stats' in validation_report:
            loc_stats = validation_report['location_processing_stats']
            print(f"Intersections found: {loc_stats['intersections_found']}")
            print(f"Numeric blocks: {loc_stats['numeric_blocks_found']}")
            print(f"Processing success: {loc_stats['processing_success_rate']:.1f}%")
        
        # Save processed data
        output_file = Path(__file__).parent.parent / f"SCRPA_v4_TimeLocation_Processed_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        processed_df.to_csv(output_file, index=False)
        print(f"\nProcessed data saved: {output_file.name}")
        
        print(f"\n[SUCCESS] SCRPA v4 Time-of-Day and Location processing completed!")
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())