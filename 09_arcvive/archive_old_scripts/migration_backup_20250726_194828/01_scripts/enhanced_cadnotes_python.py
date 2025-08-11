# 🕒 2025-07-23-17-00-00
# SCRPA_Time_v2/Enhanced_CADNotes_Processor
# Author: R. A. Carucci
# Purpose: Production-ready CADNotes processing building on your existing validation scripts

import pandas as pd
import numpy as np
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

class EnhancedCADNotesProcessor:
    """
    Enhanced CADNotes processor building on your existing validation framework.
    Integrates with your UnifiedDataProcessor and SCRPADataValidator classes.
    """
    
    def __init__(self):
        self.setup_logging()
        
        # Enhanced regex patterns for robust parsing
        self.patterns = {
            'username': re.compile(r'-\s*([a-zA-Z]+_[a-zA-Z]+)\s*-', re.IGNORECASE),
            'timestamp': re.compile(r'(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s*[AP]M)', re.IGNORECASE),
            'artifacts': [
                re.compile(r'-\s*[a-zA-Z_]+\s*-', re.IGNORECASE),  # Remove all username patterns
                re.compile(r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s*[AP]M', re.IGNORECASE),  # Remove timestamps
                re.compile(r'\([^)]*\)', re.IGNORECASE),  # Remove parenthetical content
                re.compile(r'#\w+', re.IGNORECASE),  # Remove hash codes
                re.compile(r'\bcc\b', re.IGNORECASE),  # Remove CC artifacts
                re.compile(r'-+', re.IGNORECASE),  # Remove multiple dashes
                re.compile(r'\s+', re.IGNORECASE)  # Normalize spacing
            ]
        }
    
    def setup_logging(self):
        """Setup logging compatible with your existing framework."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('enhanced_cadnotes_processing.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def process_cadnotes_dataframe(self, df: pd.DataFrame, 
                                 cadnotes_column: str = 'CADNotes') -> pd.DataFrame:
        """
        Process entire CADNotes column efficiently using vectorized operations.
        Integrates with your existing data validation framework.
        """
        self.logger.info(f"🔄 Processing CADNotes for {len(df)} records")
        
        if cadnotes_column not in df.columns:
            self.logger.warning(f"Column {cadnotes_column} not found, skipping CADNotes processing")
            # Add empty columns for consistency
            df['CAD_Username'] = None
            df['CAD_Timestamp'] = None
            df['CAD_Notes_Cleaned'] = None
            return df
        
        # Vectorized processing using apply (much faster than row iteration)
        start_time = datetime.now()
        
        # Process all CADNotes at once
        parsed_data = df[cadnotes_column].fillna('').apply(self.parse_single_cadnote)
        
        # Extract components into separate columns
        df['CAD_Username'] = parsed_data.apply(lambda x: x.get('username'))
        df['CAD_Timestamp'] = parsed_data.apply(lambda x: x.get('timestamp'))  
        df['CAD_Notes_Cleaned'] = parsed_data.apply(lambda x: x.get('cleaned_text'))
        
        # Add processing metadata
        df['CADNotes_Processing_Quality'] = parsed_data.apply(
            lambda x: self._calculate_parsing_quality(x)
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"✅ CADNotes processing complete in {processing_time:.2f} seconds")
        
        # Log processing statistics
        self._log_processing_stats(df, parsed_data)
        
        return df
    
    def parse_single_cadnote(self, raw_notes: str) -> Dict[str, Optional[str]]:
        """
        Parse a single CAD note with comprehensive error handling.
        Handles your example: "- klosk_J - 3/25/2025 12:06:34 PM in front of store..."
        """
        
        if not raw_notes or pd.isna(raw_notes) or raw_notes.strip() == '':
            return {'username': None, 'timestamp': None, 'cleaned_text': None}
        
        try:
            # Step 1: Extract FIRST username occurrence
            username = self._extract_first_username(raw_notes)
            
            # Step 2: Extract FIRST timestamp occurrence  
            timestamp = self._extract_first_timestamp(raw_notes)
            
            # Step 3: Clean text by removing ALL patterns
            cleaned_text = self._comprehensive_text_cleaning(raw_notes)
            
            return {
                'username': username,
                'timestamp': timestamp,
                'cleaned_text': cleaned_text,
                'original_length': len(raw_notes),
                'cleaned_length': len(cleaned_text) if cleaned_text else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing CADNotes: {str(e)}")
            return {
                'username': None, 
                'timestamp': None, 
                'cleaned_text': raw_notes,  # Return original if parsing fails
                'error': str(e)
            }
    
    def _extract_first_username(self, text: str) -> Optional[str]:
        """Extract and format the first username occurrence."""
        match = self.patterns['username'].search(text)
        if match:
            username = match.group(1)
            return self._format_username(username)
        return None
    
    def _extract_first_timestamp(self, text: str) -> Optional[str]:
        """Extract and standardize the first timestamp occurrence."""
        match = self.patterns['timestamp'].search(text)
        if match:
            timestamp_str = match.group(1)
            return self._standardize_timestamp(timestamp_str)
        return None
    
    def _comprehensive_text_cleaning(self, text: str) -> Optional[str]:
        """
        Comprehensive text cleaning removing all artifacts.
        Much more robust than your current M Code approach.
        """
        
        cleaned = text
        
        # Apply all artifact removal patterns sequentially
        for pattern in self.patterns['artifacts']:
            cleaned = pattern.sub(' ', cleaned)
        
        # Additional cleanup steps
        cleaned = self._remove_remaining_artifacts(cleaned)
        cleaned = self._normalize_text(cleaned)
        
        # Return None for empty or minimal content
        if not cleaned or len(cleaned.strip()) < 3:
            return None
            
        return cleaned.strip()
    
    def _remove_remaining_artifacts(self, text: str) -> str:
        """Remove any remaining artifacts not caught by regex patterns."""
        
        # Remove common CAD system artifacts
        artifacts_to_remove = [
            'Time of Call:', 'Time Dispatched:', 'Time Out:', 'Time In:',
            'Disposition:', 'Grid:', 'Zone:', 'Officer:',
            'How Reported:', 'Response Type:'
        ]
        
        for artifact in artifacts_to_remove:
            text = text.replace(artifact, ' ')
        
        # Remove standalone numbers that look like case numbers
        text = re.sub(r'\b25-\d{6}\b', ' ', text)
        
        # Remove isolated single characters
        text = re.sub(r'\b[a-zA-Z]\b', ' ', text)
        
        return text
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text formatting and capitalization."""
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        if not text:
            return text
        
        # Apply proper sentence case
        # First word capitalized, rest lowercase except proper nouns
        sentences = text.split('. ')
        normalized_sentences = []
        
        for sentence in sentences:
            if sentence:
                # Capitalize first letter, keep rest as-is for proper nouns
                sentence = sentence[0].upper() + sentence[1:].lower() if len(sentence) > 1 else sentence.upper()
                normalized_sentences.append(sentence)
        
        return '. '.join(normalized_sentences)
    
    def _format_username(self, username: str) -> str:
        """Format username with proper capitalization: klosk_j → Klosk_J"""
        if '_' in username:
            parts = username.split('_')
            return '_'.join(part.capitalize() for part in parts)
        return username.capitalize()
    
    def _standardize_timestamp(self, timestamp_str: str) -> str:
        """Convert timestamp to standardized MM/dd/yyyy HH:mm:ss format."""
        
        # List of possible timestamp formats
        formats_to_try = [
            '%m/%d/%Y %I:%M:%S %p',  # 3/25/2025 12:06:34 PM
            '%m/%d/%Y %H:%M:%S',     # 3/25/2025 12:06:34
            '%m/%d/%y %I:%M:%S %p',  # 3/25/25 12:06:34 PM
            '%m/%d/%y %H:%M:%S',     # 3/25/25 12:06:34
        ]
        
        for fmt in formats_to_try:
            try:
                dt = datetime.strptime(timestamp_str.strip(), fmt)
                # Return in standardized format: MM/dd/yyyy HH:mm:ss
                return dt.strftime('%m/%d/%Y %H:%M:%S')
            except ValueError:
                continue
        
        # If parsing fails, return original cleaned up
        self.logger.warning(f"Could not parse timestamp: {timestamp_str}")
        return timestamp_str.strip()
    
    def _calculate_parsing_quality(self, parsed_data: Dict) -> float:
        """Calculate quality score for CADNotes parsing (0-100)."""
        
        score = 0
        
        # Username extracted (30 points)
        if parsed_data.get('username'):
            score += 30
        
        # Timestamp extracted (30 points)
        if parsed_data.get('timestamp'):
            score += 30
        
        # Cleaned text available (25 points)
        if parsed_data.get('cleaned_text'):
            score += 25
        
        # Text reduction indicates good cleaning (15 points)
        original_len = parsed_data.get('original_length', 0)
        cleaned_len = parsed_data.get('cleaned_length', 0)
        
        if original_len > 0 and cleaned_len > 0:
            reduction_ratio = (original_len - cleaned_len) / original_len
            if 0.2 <= reduction_ratio <= 0.8:  # Good reduction range
                score += 15
        
        return min(score, 100.0)
    
    def _log_processing_stats(self, df: pd.DataFrame, parsed_data: pd.Series):
        """Log comprehensive processing statistics."""
        
        total_records = len(df)
        username_extracted = df['CAD_Username'].notna().sum()
        timestamp_extracted = df['CAD_Timestamp'].notna().sum()
        text_cleaned = df['CAD_Notes_Cleaned'].notna().sum()
        
        avg_quality = df['CADNotes_Processing_Quality'].mean()
        
        self.logger.info(f"📊 CADNotes Processing Statistics:")
        self.logger.info(f"   Total records: {total_records}")
        self.logger.info(f"   Usernames extracted: {username_extracted} ({username_extracted/total_records*100:.1f}%)")
        self.logger.info(f"   Timestamps extracted: {timestamp_extracted} ({timestamp_extracted/total_records*100:.1f}%)")
        self.logger.info(f"   Text cleaned: {text_cleaned} ({text_cleaned/total_records*100:.1f}%)")
        self.logger.info(f"   Average quality score: {avg_quality:.1f}/100")
    
    def validate_against_examples(self) -> bool:
        """Validate processor against your specific examples."""
        
        test_cases = [
            {
                'input': '- klosk_J - 3/25/2025 12:06:34 PM in front of store - klosk_J - 3/25/2025 12:06:34 PM Drone deployed. Provided overwatch. - weber_r - 3/25/2025 12:12:47 PM',
                'expected_username': 'Klosk_J',
                'expected_timestamp': '03/25/2025 12:06:34',
                'should_contain_cleaned': ['front of store', 'drone deployed', 'provided overwatch']
            },
            {
                'input': '- cavallo_f - 1/10/2025 7:57:11 PM Unit responded to burglar alarm',
                'expected_username': 'Cavallo_F', 
                'expected_timestamp': '01/10/2025 19:57:11',
                'should_contain_cleaned': ['unit responded', 'burglar alarm']
            },
            {
                'input': '',
                'expected_username': None,
                'expected_timestamp': None,
                'should_contain_cleaned': []
            }
        ]
        
        self.logger.info("🧪 Running validation tests...")
        
        all_passed = True
        for i, test in enumerate(test_cases, 1):
            result = self.parse_single_cadnote(test['input'])
            
            # Validate username
            if result['username'] != test['expected_username']:
                self.logger.error(f"Test {i} FAILED: Username mismatch")
                all_passed = False
            
            # Validate timestamp
            if result['timestamp'] != test['expected_timestamp']:
                self.logger.error(f"Test {i} FAILED: Timestamp mismatch")
                all_passed = False
            
            # Validate cleaned text contains expected phrases
            cleaned = result['cleaned_text'] or ''
            for phrase in test['should_contain_cleaned']:
                if phrase.lower() not in cleaned.lower():
                    self.logger.error(f"Test {i} FAILED: Missing phrase '{phrase}'")
                    all_passed = False
            
            if all_passed:
                self.logger.info(f"Test {i} PASSED ✅")
        
        if all_passed:
            self.logger.info("🎉 All validation tests passed!")
        else:
            self.logger.error("❌ Some validation tests failed")
        
        return all_passed

def integrate_with_existing_scripts(data_path: str = None):
    """
    Integration function that works with your existing script framework.
    """
    
    # Use your existing path structure
    if not data_path:
        data_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
    
    # Initialize processors
    cadnotes_processor = EnhancedCADNotesProcessor()
    
    # Validate processor first
    if not cadnotes_processor.validate_against_examples():
        raise Exception("CADNotes processor validation failed")
    
    print("🚀 Enhanced CADNotes Processor Ready")
    print("=" * 50)
    
    # Example integration with your existing validation script
    try:
        from pathlib import Path
        
        # Look for existing data files
        project_path = Path(data_path)
        
        # Find CAD or RMS files
        cad_files = list(project_path.glob("*CAD*.xlsx"))
        rms_files = list(project_path.glob("*RMS*.xlsx"))
        
        if cad_files:
            print(f"📁 Found CAD files: {[f.name for f in cad_files[:3]]}")
        
        if rms_files:
            print(f"📁 Found RMS files: {[f.name for f in rms_files[:3]]}")
        
        # Integration points with your scripts:
        print("\n🔗 Integration Points:")
        print("1. Use with SCRPAActualDataValidator for data source detection")
        print("2. Integrate with UnifiedDataProcessor for complete pipeline")
        print("3. Add to LLM report generation for enhanced narratives")
        
        return cadnotes_processor
        
    except Exception as e:
        print(f"⚠️  Integration check failed: {e}")
        return cadnotes_processor

# Example usage with your existing data
def demonstrate_enhanced_processing():
    """Demonstrate the enhanced processing capabilities."""
    
    # Sample data matching your structure
    sample_data = pd.DataFrame([
        {
            'Case Number': '25-059260',
            'CADNotes': '- klosk_J - 3/25/2025 12:06:34 PM in front of store - klosk_J - 3/25/2025 12:06:34 PM Drone deployed. Provided overwatch. - weber_r - 3/25/2025 12:12:47 PM additional units requested',
            'ReportNumberNew': '25-059260',
            'Incident': 'Burglary - Auto'
        },
        {
            'Case Number': '25-059261', 
            'CADNotes': '- cavallo_f - 1/10/2025 7:57:11 PM Unit responded to burglar alarm, checked perimeter',
            'ReportNumberNew': '25-059261',
            'Incident': 'Alarm - Burglar'
        },
        {
            'Case Number': '25-059262',
            'CADNotes': '',  # Empty notes
            'ReportNumberNew': '25-059262',
            'Incident': 'Traffic Stop'
        }
    ])
    
    # Process with enhanced processor
    processor = EnhancedCADNotesProcessor()
    processed_df = processor.process_cadnotes_dataframe(sample_data)
    
    # Display results
    print("\n📋 Enhanced Processing Results:")
    print("=" * 60)
    
    display_columns = ['Case Number', 'CAD_Username', 'CAD_Timestamp', 'CAD_Notes_Cleaned', 'CADNotes_Processing_Quality']
    print(processed_df[display_columns].to_string(index=False))
    
    return processed_df

if __name__ == "__main__":
    # Run demonstration
    demonstrate_enhanced_processing()
    
    # Run integration setup
    processor = integrate_with_existing_scripts()