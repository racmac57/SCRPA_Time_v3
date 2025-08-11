# 🕒 2025-07-23-16-50-00
# Project: SCRPA_Time_v2/Python_CADNotes_Processor
# Author: R. A. Carucci
# Purpose: Clean, efficient CADNotes processing using Python regex and string methods

import pandas as pd
import re
from datetime import datetime
from typing import Dict, Optional, Tuple
import logging

class CADNotesProcessor:
    """
    Processes CAD Notes with much cleaner logic than M Code equivalent.
    Handles username extraction, timestamp parsing, and text cleaning.
    """
    
    def __init__(self):
        # Regex patterns for efficient parsing
        self.username_pattern = r'- ([a-zA-Z_]+) -'
        self.timestamp_pattern = r'(\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [AP]M)'
        self.datetime_formats = [
            '%m/%d/%Y %I:%M:%S %p',  # 3/25/2025 12:06:34 PM
            '%m/%d/%Y %H:%M:%S',     # 3/25/2025 12:06:34
            '%m/%d/%y %I:%M:%S %p',  # 3/25/25 12:06:34 PM
        ]
        
    def process_cadnotes_batch(self, df: pd.DataFrame, cadnotes_column: str = 'CADNotes') -> pd.DataFrame:
        """
        Process entire CADNotes column efficiently using vectorized operations.
        Much faster than M Code row-by-row processing.
        """
        if cadnotes_column not in df.columns:
            logging.warning(f"Column {cadnotes_column} not found")
            return df
            
        # Apply processing to entire column at once (vectorized)
        cadnotes_data = df[cadnotes_column].fillna('').apply(self.parse_single_cadnote)
        
        # Extract components into separate columns
        df['CAD_Username'] = cadnotes_data.apply(lambda x: x['username'])
        df['CAD_Timestamp'] = cadnotes_data.apply(lambda x: x['timestamp'])
        df['CAD_Notes_Cleaned'] = cadnotes_data.apply(lambda x: x['cleaned_text'])
        
        return df
    
    def parse_single_cadnote(self, raw_notes: str) -> Dict[str, Optional[str]]:
        """
        Parse a single CAD note entry. Much cleaner than the M Code equivalent.
        
        Example input: "- klosk_J - 3/25/2025 12:06:34 PM in front of store - klosk_J - 3/25/2025 12:06:34 PM Drone deployed. Provided overwatch. - weber_r - 3/25/2025 12:12:47 PM"
        
        Expected output:
        - username: "Klosk_J" (first occurrence, properly capitalized)
        - timestamp: "03/25/2025 12:06:34" (first occurrence, standardized format)
        - cleaned_text: "In Front Of Store Drone Deployed. Provided Overwatch." (all usernames/timestamps removed)
        """
        
        if not raw_notes or raw_notes.strip() == '':
            return {'username': None, 'timestamp': None, 'cleaned_text': None}
        
        try:
            # Step 1: Extract FIRST username
            username = self._extract_first_username(raw_notes)
            
            # Step 2: Extract FIRST timestamp
            timestamp = self._extract_first_timestamp(raw_notes)
            
            # Step 3: Clean text by removing ALL username/timestamp patterns
            cleaned_text = self._clean_notes_text(raw_notes)
            
            return {
                'username': username,
                'timestamp': timestamp,
                'cleaned_text': cleaned_text
            }
            
        except Exception as e:
            logging.error(f"Error parsing CAD notes: {str(e)}")
            return {'username': None, 'timestamp': None, 'cleaned_text': raw_notes}
    
    def _extract_first_username(self, text: str) -> Optional[str]:
        """Extract and format the first username from CAD notes."""
        # Find first username pattern: "- username_name -"
        match = re.search(self.username_pattern, text)
        if match:
            username = match.group(1)
            # Format: "klosk_j" -> "Klosk_J"
            return self._format_username(username)
        return None
    
    def _extract_first_timestamp(self, text: str) -> Optional[str]:
        """Extract and standardize the first timestamp from CAD notes."""
        # Find first timestamp pattern
        match = re.search(self.timestamp_pattern, text)
        if match:
            timestamp_str = match.group(1)
            return self._standardize_timestamp(timestamp_str)
        return None
    
    def _clean_notes_text(self, text: str) -> Optional[str]:
        """Remove all username/timestamp patterns and clean the remaining text."""
        
        # Step 1: Remove all "- username -" patterns
        text = re.sub(r'- [a-zA-Z_]+ -', ' ', text)
        
        # Step 2: Remove all timestamp patterns
        text = re.sub(self.timestamp_pattern, ' ', text)
        
        # Step 3: Remove common artifacts
        artifacts_to_remove = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # Remaining dates
            r'\b\d{1,2}:\d{2}:\d{2}\b',    # Remaining times
            r'\b[AP]M\b',                   # AM/PM
            r'\bcc\b',                      # Common CAD artifact
            r'\([^)]*\)',                   # Parenthetical content
            r'#\w+',                        # Hash codes
            r'-+',                          # Multiple dashes
        ]
        
        for pattern in artifacts_to_remove:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Step 4: Clean up spacing and formatting
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces -> single space
        text = text.strip()
        
        # Step 5: Apply proper case formatting
        if text and len(text) > 2:
            return text.title()  # "in front of store" -> "In Front Of Store"
        
        return None if not text else text
    
    def _format_username(self, username: str) -> str:
        """Format username with proper capitalization."""
        if '_' in username:
            parts = username.split('_')
            return '_'.join(part.capitalize() for part in parts)
        return username.capitalize()
    
    def _standardize_timestamp(self, timestamp_str: str) -> Optional[str]:
        """Convert timestamp to standardized MM/dd/yyyy HH:mm:ss format."""
        for fmt in self.datetime_formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                return dt.strftime('%m/%d/%Y %H:%M:%S')  # Standardized format
            except ValueError:
                continue
        
        # If parsing fails, return original
        logging.warning(f"Could not parse timestamp: {timestamp_str}")
        return timestamp_str

# Example usage and testing
def test_cadnotes_processor():
    """Test the CADNotes processor with sample data."""
    
    processor = CADNotesProcessor()
    
    # Test cases based on your examples
    test_cases = [
        {
            'input': '- klosk_J - 3/25/2025 12:06:34 PM in front of store - klosk_J - 3/25/2025 12:06:34 PM Drone deployed. Provided overwatch. - weber_r - 3/25/2025 12:12:47 PM',
            'expected_username': 'Klosk_J',
            'expected_timestamp': '03/25/2025 12:06:34',
            'expected_cleaned': 'In Front Of Store Drone Deployed. Provided Overwatch.'
        },
        {
            'input': '- cavallo_f - 1/10/2025 7:57:11 PM responded to alarm',
            'expected_username': 'Cavallo_F',
            'expected_timestamp': '01/10/2025 19:57:11',
            'expected_cleaned': 'Responded To Alarm'
        },
        {
            'input': '',
            'expected_username': None,
            'expected_timestamp': None,
            'expected_cleaned': None
        }
    ]
    
    print("🧪 Testing CADNotes Processor")
    print("=" * 50)
    
    for i, test in enumerate(test_cases, 1):
        result = processor.parse_single_cadnote(test['input'])
        
        print(f"\nTest {i}:")
        print(f"Input: {test['input'][:50]}{'...' if len(test['input']) > 50 else ''}")
        print(f"Username: {result['username']} (expected: {test['expected_username']})")
        print(f"Timestamp: {result['timestamp']} (expected: {test['expected_timestamp']})")
        print(f"Cleaned: {result['cleaned_text']} (expected: {test['expected_cleaned']})")
        
        # Validation
        success = (
            result['username'] == test['expected_username'] and
            result['timestamp'] == test['expected_timestamp'] and
            result['cleaned_text'] == test['expected_cleaned']
        )
        print(f"✅ PASS" if success else "❌ FAIL")

def process_cad_rms_file(input_file: str, output_file: str):
    """
    Complete example of processing a CAD/RMS file with CADNotes cleaning.
    This replaces your entire complex M Code with simple, fast Python.
    """
    
    print(f"🔄 Processing {input_file}")
    
    # Load data
    df = pd.read_excel(input_file)
    print(f"📊 Loaded {len(df)} records")
    
    # Process CADNotes
    processor = CADNotesProcessor()
    df_processed = processor.process_cadnotes_batch(df)
    
    # Add other enhancements (similar to your M Code logic)
    df_enhanced = enhance_cad_rms_data(df_processed)
    
    # Export clean data
    df_enhanced.to_csv(output_file, index=False)
    print(f"✅ Saved enhanced data to {output_file}")
    
    # Show sample results
    sample_cols = ['Case_Number', 'CAD_Username', 'CAD_Timestamp', 'CAD_Notes_Cleaned']
    if all(col in df_enhanced.columns for col in sample_cols):
        print(f"\n📋 Sample Results:")
        print(df_enhanced[sample_cols].head(3).to_string())

def enhance_cad_rms_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Additional enhancements that replace other parts of your M Code.
    This is much cleaner and faster than Power Query transformations.
    """
    
    # Add crime categorization (replaces M Code logic)
    df['Crime_Category'] = df.get('Incident_Type_1', '').apply(categorize_crime_type)
    
    # Add period classification (replaces M Code logic)
    if 'Incident_Date' in df.columns:
        df['Period'] = df['Incident_Date'].apply(classify_period)
    
    # Add enhanced block calculation (replaces M Code logic)
    if 'Enhanced_FullAddress' in df.columns:
        df['Enhanced_Block'] = df['Enhanced_FullAddress'].apply(calculate_block)
    
    # Add response time formatting (replaces M Code logic)
    if 'Time_Response_Minutes' in df.columns:
        df['Time_Response_Formatted'] = df['Time_Response_Minutes'].apply(format_response_time)
    
    return df

def categorize_crime_type(incident_type: str) -> str:
    """Categorize crime types - much cleaner than M Code version."""
    if pd.isna(incident_type):
        return 'Other'
    
    incident_upper = str(incident_type).upper()
    
    if any(term in incident_upper for term in ['MOTOR VEHICLE THEFT', 'AUTO THEFT', 'MV THEFT']):
        return 'Motor Vehicle Theft'
    elif 'BURGLARY' in incident_upper and ('AUTO' in incident_upper or 'VEHICLE' in incident_upper):
        return 'Burglary - Auto'
    elif 'BURGLARY' in incident_upper and 'COMMERCIAL' in incident_upper:
        return 'Burglary - Commercial'
    elif 'BURGLARY' in incident_upper and 'RESIDENCE' in incident_upper:
        return 'Burglary - Residence'
    elif 'ROBBERY' in incident_upper:
        return 'Robbery'
    elif 'SEXUAL' in incident_upper:
        return 'Sexual Offenses'
    else:
        return 'Other'

def classify_period(incident_date) -> str:
    """Classify time periods - much simpler than M Code version."""
    if pd.isna(incident_date):
        return 'Historical'
    
    try:
        incident_dt = pd.to_datetime(incident_date)
        today = pd.Timestamp.now()
        days_diff = (today - incident_dt).days
        
        if days_diff <= 7:
            return '7-Day'
        elif days_diff <= 28:
            return '28-Day'
        elif incident_dt.year == today.year:
            return 'YTD'
        else:
            return 'Historical'
    except:
        return 'Historical'

def calculate_block(address: str) -> str:
    """Calculate block from address - cleaner than M Code version."""
    if pd.isna(address) or not address:
        return 'Incomplete Address - Check Location Data'
    
    # Remove common suffixes
    clean_addr = str(address).replace(', Hackensack, NJ, 07601', '')
    
    # Handle intersections
    if ' & ' in clean_addr:
        return clean_addr.strip()
    
    # Extract block number
    try:
        parts = clean_addr.split()
        if parts and parts[0].isdigit():
            street_num = int(parts[0])
            street_name = ' '.join(parts[1:]).split(',')[0]
            block_num = (street_num // 100) * 100
            return f"{street_name}, {block_num} Block"
    except:
        pass
    
    return 'Incomplete Address - Check Location Data'

def format_response_time(minutes) -> str:
    """Format response time - much simpler than M Code version."""
    if pd.isna(minutes):
        return None
    
    try:
        total_seconds = int(float(minutes) * 60)
        mins = total_seconds // 60
        secs = total_seconds % 60
        
        if mins == 0:
            return f"{secs} Secs"
        elif secs == 0:
            return f"{mins} Mins"
        else:
            return f"{mins} Mins {secs:02d} Secs"
    except:
        return "Invalid Time"

if __name__ == "__main__":
    # Run tests
    test_cadnotes_processor()
    
    # Example processing
    # process_cad_rms_file("input_file.xlsx", "enhanced_output.csv")