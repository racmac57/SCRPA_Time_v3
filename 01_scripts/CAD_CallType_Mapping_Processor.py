#!/usr/bin/env python3
"""
CAD CallType Mapping & Response Classification
Implements comprehensive CallType mapping and response classification for CAD data.

Author: Crime Analysis Team
Version: 1.0
Date: 2025-08-03
Purpose: Map CAD incident types to standardized response/category types
"""

import pandas as pd
import numpy as np
import re
import logging
from pathlib import Path
from typing import Tuple, Dict, Optional
import warnings

warnings.filterwarnings('ignore')

class CADCallTypeProcessor:
    """Processes CAD data with CallType mapping and response classification."""
    
    def __init__(self, base_dir: str = None):
        """Initialize the processor."""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.calltype_mapping = {}
        self.unmapped_incidents = set()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load CallType categories
        self.load_calltype_categories()
        
    def load_calltype_categories(self) -> None:
        """Load CallType_Categories.xlsx and create mapping dictionary."""
        try:
            calltype_file = self.base_dir / '10_Refrence_Files' / 'CallType_Categories.xlsx'
            
            if not calltype_file.exists():
                self.logger.error(f"CallType_Categories.xlsx not found at: {calltype_file}")
                return
                
            df = pd.read_excel(calltype_file)
            self.logger.info(f"Loaded CallType categories: {len(df)} records")
            
            # Create mapping dictionary with normalized keys
            for _, row in df.iterrows():
                incident = str(row['Incident']).upper().strip()
                response_type = str(row['Response Type']).strip()
                category_type = str(row['Category Type']).strip()
                
                self.calltype_mapping[incident] = {
                    'response_type': response_type,
                    'category_type': category_type
                }
                
            self.logger.info(f"Created mapping for {len(self.calltype_mapping)} incident types")
            
        except Exception as e:
            self.logger.error(f"Error loading CallType categories: {e}")
            self.calltype_mapping = {}
            
    def map_call_type(self, incident: str) -> Tuple[str, str]:
        """
        Map incident to (response_type, category_type) using lookup hierarchy.
        
        Args:
            incident: The incident type string
            
        Returns:
            Tuple of (response_type, category_type)
        """
        if pd.isna(incident) or not str(incident).strip():
            return "Unknown", "Other"
            
        incident_normalized = str(incident).upper().strip()
        
        # 1. Exact case-insensitive lookup
        if incident_normalized in self.calltype_mapping:
            mapping = self.calltype_mapping[incident_normalized]
            return mapping['response_type'], mapping['category_type']
            
        # 2. Partial match fallback
        for key, mapping in self.calltype_mapping.items():
            if incident_normalized in key or key in incident_normalized:
                return mapping['response_type'], mapping['category_type']
                
        # 3. Keyword fallback
        keyword_mappings = {
            'TRAFFIC': ('Traffic Violation', 'Traffic'),
            'ALARM': ('Alarm Response', 'Alarm'),
            'MEDICAL': ('Medical Emergency', 'Medical'),
            'FIRE': ('Fire Response', 'Fire'),
        }
        
        # Check crime keywords
        crime_keywords = ['THEFT', 'BURGLARY', 'ROBBERY', 'LARCENY']
        for keyword in crime_keywords:
            if keyword in incident_normalized:
                return "Crime Investigation", "Crime"
                
        # Check disturbance keywords  
        disturbance_keywords = ['DOMESTIC', 'DISTURBANCE', 'FIGHT']
        for keyword in disturbance_keywords:
            if keyword in incident_normalized:
                return "Disturbance Call", "Disturbance"
                
        # Check other keywords
        for keyword, (response, category) in keyword_mappings.items():
            if keyword in incident_normalized:
                return response, category
                
        # 4. Default fallback
        self.unmapped_incidents.add(incident_normalized)
        return "Other Response", "Other"
        
    def clean_how_reported_911(self, how_reported: str) -> str:
        """
        Clean and normalize how_reported field.
        
        Args:
            how_reported: Raw how_reported value
            
        Returns:
            Normalized how_reported value
        """
        if pd.isna(how_reported) or not str(how_reported).strip():
            return ""
            
        text = str(how_reported).strip()
        
        # Check for 9-1-1 patterns
        if text in ["9-1-1", "911"]:
            return "9-1-1"
            
        # Check for date pattern (indicates 9-1-1 call)
        date_pattern = r'^\d{1,2}/\d{1,2}/\d{4}$'
        if re.match(date_pattern, text):
            return "9-1-1"
            
        return text
        
    def extract_username_timestamp(self, text: str) -> Tuple[str, str, str]:
        """
        Extract username and timestamp from CAD notes text.
        
        Args:
            text: Raw CAD notes text
            
        Returns:
            Tuple of (cleaned_text, username, timestamps)
        """
        if pd.isna(text) or not str(text).strip():
            return "", "", ""
            
        text_str = str(text).strip()
        cleaned_text = text_str
        username = ""
        timestamps = ""
        
        try:
            # Extract username pattern: word_word format
            username_pattern = r'(\w+_\w+)'
            username_matches = re.findall(username_pattern, text_str)
            if username_matches:
                username = username_matches[0]
                
            # Extract timestamp pattern: MM/dd/yyyy HH:mm:ss AM/PM
            timestamp_pattern = r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [AP]M'
            timestamp_matches = re.findall(timestamp_pattern, text_str)
            if timestamp_matches:
                timestamps = ' | '.join(timestamp_matches)
                
            # Clean text by removing extracted patterns
            for match in username_matches:
                cleaned_text = cleaned_text.replace(match, '').strip()
                
            for match in timestamp_matches:
                cleaned_text = cleaned_text.replace(match, '').strip()
                
            # Clean up extra whitespace and punctuation
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            cleaned_text = re.sub(r'^[-\s,]+|[-\s,]+$', '', cleaned_text).strip()
            
        except Exception as e:
            self.logger.warning(f"Error extracting metadata from text: {e}")
            
        return cleaned_text, username, timestamps
        
    def process_cad_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process CAD DataFrame with CallType mapping and response classification.
        
        Args:
            df: CAD DataFrame with required columns
            
        Returns:
            Enhanced DataFrame with new columns
        """
        self.logger.info(f"Processing {len(df)} CAD records")
        
        # Create copy to avoid modifying original
        processed_df = df.copy()
        
        # Apply CallType mapping
        if 'incident' in processed_df.columns:
            mapping_results = processed_df['incident'].apply(self.map_call_type)
            processed_df['response_type'] = [result[0] for result in mapping_results]
            processed_df['category_type'] = [result[1] for result in mapping_results]
            
            # Log mapping statistics
            mapped_count = len(processed_df) - len(self.unmapped_incidents)
            mapping_rate = mapped_count / len(processed_df) * 100 if len(processed_df) > 0 else 0
            self.logger.info(f"CallType mapping: {mapped_count}/{len(processed_df)} ({mapping_rate:.1f}%)")
            
            if self.unmapped_incidents:
                self.logger.warning(f"Unmapped incidents: {sorted(list(self.unmapped_incidents))}")
        else:
            self.logger.warning("'incident' column not found in DataFrame")
            
        # Clean how_reported field
        if 'how_reported' in processed_df.columns:
            processed_df['how_reported_clean'] = processed_df['how_reported'].apply(
                self.clean_how_reported_911
            )
            
            # Log how_reported statistics
            clean_911_count = (processed_df['how_reported_clean'] == '9-1-1').sum()
            self.logger.info(f"how_reported cleaning: {clean_911_count} records normalized to '9-1-1'")
        else:
            self.logger.warning("'how_reported' column not found in DataFrame")
            
        # Process CAD notes if available
        cad_notes_column = None
        possible_columns = ['cad_notes_raw', 'cad_notes', 'notes']
        
        for col in possible_columns:
            if col in processed_df.columns:
                cad_notes_column = col
                break
                
        if cad_notes_column:
            self.logger.info(f"Processing CAD notes from column: {cad_notes_column}")
            
            # Extract metadata
            extraction_results = processed_df[cad_notes_column].apply(
                self.extract_username_timestamp
            )
            
            processed_df['cad_notes_cleaned'] = [result[0] for result in extraction_results]
            processed_df['cad_notes_username'] = [result[1] for result in extraction_results]
            processed_df['cad_notes_timestamp'] = [result[2] for result in extraction_results]
            
            # Log extraction statistics
            username_count = processed_df['cad_notes_username'].astype(bool).sum()
            timestamp_count = processed_df['cad_notes_timestamp'].astype(bool).sum()
            
            self.logger.info(f"CAD notes processing: {username_count} usernames, {timestamp_count} timestamps extracted")
        else:
            self.logger.warning("No CAD notes column found. Checked: " + ", ".join(possible_columns))
            
        return processed_df
        
    def generate_mapping_report(self) -> Dict:
        """Generate comprehensive mapping report."""
        report = {
            'total_categories': len(self.calltype_mapping),
            'unmapped_incidents': sorted(list(self.unmapped_incidents)),
            'unmapped_count': len(self.unmapped_incidents),
            'category_breakdown': {},
            'response_breakdown': {}
        }
        
        # Analyze category and response type distribution
        for mapping_data in self.calltype_mapping.values():
            category = mapping_data['category_type']
            response = mapping_data['response_type']
            
            report['category_breakdown'][category] = report['category_breakdown'].get(category, 0) + 1
            report['response_breakdown'][response] = report['response_breakdown'].get(response, 0) + 1
            
        return report
        
    def validate_processing(self, original_df: pd.DataFrame, processed_df: pd.DataFrame) -> Dict:
        """Validate the processing results."""
        validation = {
            'record_count_preserved': len(original_df) == len(processed_df),
            'original_records': len(original_df),
            'processed_records': len(processed_df),
            'new_columns_added': [],
            'mapping_coverage': {}
        }
        
        # Check for new columns
        original_cols = set(original_df.columns)
        processed_cols = set(processed_df.columns)
        validation['new_columns_added'] = sorted(list(processed_cols - original_cols))
        
        # Check mapping coverage
        if 'response_type' in processed_df.columns:
            mapped_count = (processed_df['response_type'] != 'Other Response').sum()
            total_count = len(processed_df)
            coverage_rate = mapped_count / total_count * 100 if total_count > 0 else 0
            
            validation['mapping_coverage'] = {
                'mapped_records': int(mapped_count),
                'total_records': int(total_count),
                'coverage_rate': float(coverage_rate),
                'target_met': coverage_rate >= 90.0  # 90% target
            }
            
        return validation


def main():
    """Main execution function for testing."""
    print("CAD CallType Mapping & Response Classification")
    print("=" * 50)
    
    try:
        # Initialize processor
        processor = CADCallTypeProcessor()
        
        # Load CAD data for testing
        base_dir = Path(__file__).parent.parent
        cad_files = list(base_dir.glob("*cad_data*.csv"))
        
        if not cad_files:
            print("ERROR: No CAD data file found")
            return 1
            
        # Use most recent CAD file
        cad_file = max(cad_files, key=lambda p: p.stat().st_mtime)
        print(f"Processing CAD file: {cad_file.name}")
        
        # Load and process data
        df = pd.read_csv(cad_file)
        print(f"Loaded {len(df)} CAD records")
        
        # Process the data
        processed_df = processor.process_cad_data(df)
        print(f"Processing complete: {len(processed_df)} records")
        
        # Generate reports
        mapping_report = processor.generate_mapping_report()
        validation_report = processor.validate_processing(df, processed_df)
        
        # Display results
        print("\nMapping Report:")
        print(f"  Total categories available: {mapping_report['total_categories']}")
        print(f"  Unmapped incidents: {mapping_report['unmapped_count']}")
        
        if mapping_report['unmapped_incidents']:
            print("  Unmapped incident types:")
            for incident in mapping_report['unmapped_incidents'][:5]:  # Show first 5
                print(f"    - {incident}")
            if len(mapping_report['unmapped_incidents']) > 5:
                print(f"    ... and {len(mapping_report['unmapped_incidents']) - 5} more")
                
        print(f"\nValidation Report:")
        print(f"  Record preservation: {validation_report['record_count_preserved']}")
        print(f"  New columns added: {len(validation_report['new_columns_added'])}")
        for col in validation_report['new_columns_added']:
            print(f"    - {col}")
            
        if 'mapping_coverage' in validation_report:
            coverage = validation_report['mapping_coverage']
            print(f"  Mapping coverage: {coverage['coverage_rate']:.1f}% ({coverage['mapped_records']}/{coverage['total_records']})")
            print(f"  Target met (90%): {'[PASS]' if coverage['target_met'] else '[FAIL]'}")
            
        # Save processed data
        output_file = base_dir / f"CAD_Processed_CallType_Mapping_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        processed_df.to_csv(output_file, index=False)
        print(f"\nOutput saved: {output_file.name}")
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())