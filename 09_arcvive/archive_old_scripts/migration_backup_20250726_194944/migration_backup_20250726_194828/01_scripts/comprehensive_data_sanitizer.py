# 🔒 Comprehensive Police Data Sanitizer
# Author: Claude Code (Anthropic)
# Purpose: Advanced data sanitization for police incident reports with consistent replacements
# Features: Name tracking, regex patterns, audit functions, comprehensive logging

import pandas as pd
import logging
import re
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SanitizationOperation:
    """Record of a single sanitization operation."""
    field_name: str
    original_hash: str  # SHA256 hash of original (never store actual sensitive data)
    replacement_value: str
    data_type: str
    timestamp: datetime
    record_id: Optional[str] = None

@dataclass
class SanitizationStats:
    """Statistics for sanitization operations."""
    total_operations: int = 0
    operations_by_type: Dict[str, int] = field(default_factory=dict)
    operations_by_field: Dict[str, int] = field(default_factory=dict)
    unique_names_found: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ComprehensiveDataSanitizer:
    """
    Advanced data sanitizer for police incident data with consistent name replacement
    and comprehensive audit capabilities.
    """
    
    def __init__(self, case_sensitive_names: bool = False):
        """
        Initialize the data sanitizer.
        
        Args:
            case_sensitive_names: Whether name matching should be case-sensitive
        """
        self.case_sensitive_names = case_sensitive_names
        
        # Name tracking for consistent replacements
        self.name_mapping: Dict[str, str] = {}  # original_name -> SUBJECT_X
        self.name_counter = 1
        
        # Operation tracking
        self.operations: List[SanitizationOperation] = []
        self.stats = SanitizationStats()
        
        # Initialize regex patterns
        self._initialize_patterns()
        
        logger.info("🔒 Comprehensive Data Sanitizer initialized")
    
    def _initialize_patterns(self):
        """Initialize comprehensive regex patterns for sensitive data detection."""
        
        # Phone number patterns (various formats)
        self.phone_patterns = [
            re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'),  # 555-123-4567, 555.123.4567, 555 123 4567
            re.compile(r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}'),      # (555) 123-4567
            re.compile(r'\b1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'),  # 1-555-123-4567
            re.compile(r'\b\d{10}\b'),                          # 5551234567
        ]
        
        # SSN patterns
        self.ssn_patterns = [
            re.compile(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'),    # 123-45-6789, 123 45 6789
            re.compile(r'\b\d{9}\b'),                           # 123456789 (if clearly SSN context)
        ]
        
        # Email patterns
        self.email_patterns = [
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE),
        ]
        
        # License plate patterns (US format variations)
        self.license_plate_patterns = [
            re.compile(r'\b[A-Z0-9]{2,8}\b(?=\s*(?:plate|license|reg|registration|LP|tag))', re.IGNORECASE),
            re.compile(r'(?:plate|license|LP|tag)[\s:#]*([A-Z0-9]{2,8})', re.IGNORECASE),
            re.compile(r'\b[A-Z]{1,3}[-\s]?\d{1,4}[A-Z]?\b(?=\s*(?:plate|license))', re.IGNORECASE),
        ]
        
        # Name patterns (more sophisticated)
        self.name_patterns = [
            # First Last format
            re.compile(r'\b[A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,15}\b'),
            # First Middle Last format
            re.compile(r'\b[A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,15}\b'),
            # Last, First format
            re.compile(r'\b[A-Z][a-z]{1,15},\s*[A-Z][a-z]{1,15}\b'),
            # Title + Name (Mr. John Smith, Dr. Jane Doe, etc.)
            re.compile(r'\b(?:Mr|Mrs|Ms|Dr|Officer|Detective|Sgt|Lt|Capt)\.?\s+[A-Z][a-z]{1,15}(?:\s+[A-Z][a-z]{1,15})+\b', re.IGNORECASE),
        ]
        
        # Address patterns for extracting street addresses
        self.address_patterns = [
            # Standard address: 123 Main Street
            re.compile(r'\b(\d{1,6})\s+([A-Za-z0-9\s]{2,50}(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl|Court|Ct|Circle|Cir))\b', re.IGNORECASE),
            # PO Box addresses
            re.compile(r'\bP\.?O\.?\s*Box\s+\d+\b', re.IGNORECASE),
        ]
        
        # Credit card patterns
        self.credit_card_patterns = [
            re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),  # 1234-5678-9012-3456
        ]
        
        # Driver's license patterns (varies by state, general format)
        self.drivers_license_patterns = [
            re.compile(r'\b[A-Z]\d{7,14}\b'),                   # A1234567 (common format)
            re.compile(r'\b\d{8,12}\b(?=\s*(?:DL|license))', re.IGNORECASE),
        ]
    
    def sanitize_dataframe(self, df: pd.DataFrame, 
                          text_columns: Optional[List[str]] = None,
                          id_column: Optional[str] = None) -> pd.DataFrame:
        """
        Sanitize entire DataFrame with comprehensive PII removal.
        
        Args:
            df: Input DataFrame
            text_columns: List of columns to sanitize (if None, auto-detect text columns)
            id_column: Column name to use as record identifier for logging
            
        Returns:
            Sanitized DataFrame
        """
        logger.info(f"🔒 Starting sanitization of {len(df)} records")
        self.stats.start_time = datetime.now()
        
        # Reset counters for new dataset
        self.name_mapping.clear()
        self.name_counter = 1
        self.operations.clear()
        
        # Auto-detect text columns if not specified
        if text_columns is None:
            text_columns = df.select_dtypes(include=['object', 'string']).columns.tolist()
        
        logger.info(f"📋 Sanitizing columns: {text_columns}")
        
        # Create copy for sanitization
        sanitized_df = df.copy()
        
        # Process each record
        for idx, row in df.iterrows():
            record_id = str(row[id_column]) if id_column and id_column in row else str(idx)
            
            # Sanitize each text column in the record
            for column in text_columns:
                if column in row and pd.notna(row[column]):
                    original_value = str(row[column])
                    sanitized_value = self._sanitize_text_comprehensive(
                        original_value, column, record_id
                    )
                    sanitized_df.at[idx, column] = sanitized_value
        
        self.stats.end_time = datetime.now()
        self.stats.total_operations = len(self.operations)
        self.stats.unique_names_found = len(self.name_mapping)
        
        logger.info(f"✅ Sanitization complete: {self.stats.total_operations} operations, "
                   f"{self.stats.unique_names_found} unique names processed")
        
        return sanitized_df
    
    def _sanitize_text_comprehensive(self, text: str, field_name: str, record_id: str) -> str:
        """
        Comprehensive text sanitization with all PII patterns.
        
        Args:
            text: Text to sanitize
            field_name: Name of the field being sanitized
            record_id: Identifier for the record
            
        Returns:
            Sanitized text
        """
        if not text or pd.isna(text):
            return text
        
        sanitized_text = str(text)
        
        # 1. Sanitize names (must be first to maintain consistency)
        sanitized_text = self._sanitize_names(sanitized_text, field_name, record_id)
        
        # 2. Sanitize phone numbers
        sanitized_text = self._sanitize_phones(sanitized_text, field_name, record_id)
        
        # 3. Sanitize SSNs
        sanitized_text = self._sanitize_ssns(sanitized_text, field_name, record_id)
        
        # 4. Sanitize emails
        sanitized_text = self._sanitize_emails(sanitized_text, field_name, record_id)
        
        # 5. Sanitize license plates
        sanitized_text = self._sanitize_license_plates(sanitized_text, field_name, record_id)
        
        # 6. Sanitize addresses
        sanitized_text = self._sanitize_addresses(sanitized_text, field_name, record_id)
        
        # 7. Sanitize credit cards
        sanitized_text = self._sanitize_credit_cards(sanitized_text, field_name, record_id)
        
        # 8. Sanitize driver's licenses
        sanitized_text = self._sanitize_drivers_licenses(sanitized_text, field_name, record_id)
        
        return sanitized_text
    
    def _sanitize_names(self, text: str, field_name: str, record_id: str) -> str:
        """Sanitize names with consistent SUBJECT_X replacement."""
        sanitized_text = text
        
        for pattern in self.name_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Normalize the name for consistent mapping
                normalized_name = match.strip()
                if not self.case_sensitive_names:
                    normalized_name = normalized_name.lower()
                
                # Get or create consistent replacement
                if normalized_name not in self.name_mapping:
                    self.name_mapping[normalized_name] = f"SUBJECT_{self.name_counter}"
                    self.name_counter += 1
                
                replacement = self.name_mapping[normalized_name]
                sanitized_text = sanitized_text.replace(match, replacement)
                
                self._log_operation(field_name, match, replacement, "name", record_id)
        
        return sanitized_text
    
    def _sanitize_phones(self, text: str, field_name: str, record_id: str) -> str:
        """Sanitize phone numbers."""
        sanitized_text = text
        
        for pattern in self.phone_patterns:
            matches = pattern.findall(text)
            for match in matches:
                replacement = "XXX-XXX-XXXX"
                sanitized_text = sanitized_text.replace(match, replacement)
                self._log_operation(field_name, match, replacement, "phone", record_id)
        
        return sanitized_text
    
    def _sanitize_ssns(self, text: str, field_name: str, record_id: str) -> str:
        """Sanitize Social Security Numbers."""
        sanitized_text = text
        
        for pattern in self.ssn_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Only replace if it looks like a real SSN (not just any 9 digits)
                if len(match.replace('-', '').replace(' ', '')) == 9:
                    replacement = "XXX-XX-XXXX"
                    sanitized_text = sanitized_text.replace(match, replacement)
                    self._log_operation(field_name, match, replacement, "ssn", record_id)
        
        return sanitized_text
    
    def _sanitize_emails(self, text: str, field_name: str, record_id: str) -> str:
        """Sanitize email addresses."""
        sanitized_text = text
        
        for pattern in self.email_patterns:
            matches = pattern.findall(text)
            for match in matches:
                replacement = "EMAIL_REDACTED"
                sanitized_text = sanitized_text.replace(match, replacement)
                self._log_operation(field_name, match, replacement, "email", record_id)
        
        return sanitized_text
    
    def _sanitize_license_plates(self, text: str, field_name: str, record_id: str) -> str:
        """Sanitize license plates."""
        sanitized_text = text
        
        for pattern in self.license_plate_patterns:
            matches = pattern.findall(text)
            for match in matches:
                replacement = "PLATE_XXX"
                sanitized_text = sanitized_text.replace(match, replacement)
                self._log_operation(field_name, match, replacement, "license_plate", record_id)
        
        return sanitized_text
    
    def _sanitize_addresses(self, text: str, field_name: str, record_id: str) -> str:
        """Sanitize addresses to block level."""
        sanitized_text = text
        
        for pattern in self.address_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                full_match = match.group(0)
                street_number = match.group(1) if match.groups() else None
                street_name = match.group(2) if len(match.groups()) > 1 else None
                
                if street_number and street_name:
                    # Convert to block level
                    block_number = (int(street_number) // 100) * 100
                    replacement = f"{block_number} XX BLOCK {street_name}"
                    sanitized_text = sanitized_text.replace(full_match, replacement)
                    self._log_operation(field_name, full_match, replacement, "address", record_id)
        
        return sanitized_text
    
    def _sanitize_credit_cards(self, text: str, field_name: str, record_id: str) -> str:
        """Sanitize credit card numbers."""
        sanitized_text = text
        
        for pattern in self.credit_card_patterns:
            matches = pattern.findall(text)
            for match in matches:
                replacement = "XXXX-XXXX-XXXX-XXXX"
                sanitized_text = sanitized_text.replace(match, replacement)
                self._log_operation(field_name, match, replacement, "credit_card", record_id)
        
        return sanitized_text
    
    def _sanitize_drivers_licenses(self, text: str, field_name: str, record_id: str) -> str:
        """Sanitize driver's license numbers."""
        sanitized_text = text
        
        for pattern in self.drivers_license_patterns:
            matches = pattern.findall(text)
            for match in matches:
                replacement = "DL_REDACTED"
                sanitized_text = sanitized_text.replace(match, replacement)
                self._log_operation(field_name, match, replacement, "drivers_license", record_id)
        
        return sanitized_text
    
    def _log_operation(self, field_name: str, original: str, replacement: str, 
                      data_type: str, record_id: str):
        """Log a sanitization operation."""
        # Create hash of original data (never store the actual sensitive data)
        original_hash = hashlib.sha256(original.encode()).hexdigest()[:16]
        
        operation = SanitizationOperation(
            field_name=field_name,
            original_hash=original_hash,
            replacement_value=replacement,
            data_type=data_type,
            timestamp=datetime.now(),
            record_id=record_id
        )
        
        self.operations.append(operation)
        
        # Update statistics
        self.stats.operations_by_type[data_type] = self.stats.operations_by_type.get(data_type, 0) + 1
        self.stats.operations_by_field[field_name] = self.stats.operations_by_field.get(field_name, 0) + 1
        
        logger.debug(f"🔒 Sanitized {data_type} in {field_name}: {original_hash} -> {replacement}")
    
    def audit_unsanitized_data(self, df: pd.DataFrame, 
                              text_columns: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """
        Audit DataFrame for potentially unsanitized sensitive data.
        
        Args:
            df: DataFrame to audit
            text_columns: Columns to check (if None, check all text columns)
            
        Returns:
            Dictionary of potential violations by data type
        """
        logger.info(f"🔍 Auditing {len(df)} records for unsanitized data")
        
        if text_columns is None:
            text_columns = df.select_dtypes(include=['object', 'string']).columns.tolist()
        
        violations = {
            'names': [],
            'phones': [],
            'ssns': [],
            'emails': [],
            'license_plates': [],
            'credit_cards': [],
            'drivers_licenses': []
        }
        
        for idx, row in df.iterrows():
            for column in text_columns:
                if column in row and pd.notna(row[column]):
                    text = str(row[column])
                    
                    # Check for each type of sensitive data
                    self._audit_names(text, idx, column, violations['names'])
                    self._audit_phones(text, idx, column, violations['phones'])
                    self._audit_ssns(text, idx, column, violations['ssns'])
                    self._audit_emails(text, idx, column, violations['emails'])
                    self._audit_license_plates(text, idx, column, violations['license_plates'])
                    self._audit_credit_cards(text, idx, column, violations['credit_cards'])
                    self._audit_drivers_licenses(text, idx, column, violations['drivers_licenses'])
        
        # Log audit results
        total_violations = sum(len(v) for v in violations.values())
        if total_violations > 0:
            logger.warning(f"⚠️ Audit found {total_violations} potential violations")
            for data_type, items in violations.items():
                if items:
                    logger.warning(f"   {data_type}: {len(items)} violations")
        else:
            logger.info("✅ Audit passed - no unsanitized data detected")
        
        return violations
    
    def _audit_names(self, text: str, row_idx: int, column: str, violations: List):
        """Audit for unsanitized names."""
        for pattern in self.name_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                # Skip if it's already a sanitized replacement
                if not match.group().startswith('SUBJECT_'):
                    violations.append({
                        'row': row_idx,
                        'column': column,
                        'match': match.group(),
                        'position': match.span()
                    })
    
    def _audit_phones(self, text: str, row_idx: int, column: str, violations: List):
        """Audit for unsanitized phone numbers."""
        for pattern in self.phone_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                if match.group() != "XXX-XXX-XXXX":
                    violations.append({
                        'row': row_idx,
                        'column': column,
                        'match': match.group(),
                        'position': match.span()
                    })
    
    def _audit_ssns(self, text: str, row_idx: int, column: str, violations: List):
        """Audit for unsanitized SSNs."""
        for pattern in self.ssn_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                if match.group() != "XXX-XX-XXXX":
                    violations.append({
                        'row': row_idx,
                        'column': column,
                        'match': match.group(),
                        'position': match.span()
                    })
    
    def _audit_emails(self, text: str, row_idx: int, column: str, violations: List):
        """Audit for unsanitized emails."""
        for pattern in self.email_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                if match.group() != "EMAIL_REDACTED":
                    violations.append({
                        'row': row_idx,
                        'column': column,
                        'match': match.group(),
                        'position': match.span()
                    })
    
    def _audit_license_plates(self, text: str, row_idx: int, column: str, violations: List):
        """Audit for unsanitized license plates."""
        for pattern in self.license_plate_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                matched_text = match.group(1) if match.groups() else match.group()
                if matched_text != "PLATE_XXX":
                    violations.append({
                        'row': row_idx,
                        'column': column,
                        'match': matched_text,
                        'position': match.span()
                    })
    
    def _audit_credit_cards(self, text: str, row_idx: int, column: str, violations: List):
        """Audit for unsanitized credit cards."""
        for pattern in self.credit_card_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                if match.group() != "XXXX-XXXX-XXXX-XXXX":
                    violations.append({
                        'row': row_idx,
                        'column': column,
                        'match': match.group(),
                        'position': match.span()
                    })
    
    def _audit_drivers_licenses(self, text: str, row_idx: int, column: str, violations: List):
        """Audit for unsanitized driver's licenses."""
        for pattern in self.drivers_license_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                matched_text = match.group(1) if match.groups() else match.group()
                if matched_text != "DL_REDACTED":
                    violations.append({
                        'row': row_idx,
                        'column': column,
                        'match': matched_text,
                        'position': match.span()
                    })
    
    def get_sanitization_report(self) -> Dict:
        """Generate comprehensive sanitization report."""
        processing_time = None
        if self.stats.start_time and self.stats.end_time:
            processing_time = (self.stats.end_time - self.stats.start_time).total_seconds()
        
        return {
            'summary': {
                'total_operations': self.stats.total_operations,
                'unique_names_processed': self.stats.unique_names_found,
                'processing_time_seconds': processing_time
            },
            'operations_by_type': dict(self.stats.operations_by_type),
            'operations_by_field': dict(self.stats.operations_by_field),
            'name_mappings_count': len(self.name_mapping),
            'timestamp': datetime.now().isoformat()
        }
    
    def save_audit_log(self, filepath: str):
        """Save detailed audit log to file."""
        audit_data = {
            'sanitization_report': self.get_sanitization_report(),
            'operations': [
                {
                    'field_name': op.field_name,
                    'original_hash': op.original_hash,
                    'replacement_value': op.replacement_value,
                    'data_type': op.data_type,
                    'timestamp': op.timestamp.isoformat(),
                    'record_id': op.record_id
                }
                for op in self.operations
            ],
            'name_mapping_count': len(self.name_mapping)  # Don't save actual mappings for security
        }
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, indent=2)
        
        logger.info(f"📋 Audit log saved: {filepath}")

# Test cases and validation
def create_test_data() -> pd.DataFrame:
    """Create test DataFrame with various types of sensitive data."""
    test_data = pd.DataFrame([
        {
            'case_id': 'CASE-001',
            'narrative': 'Officer Smith responded to call. Victim John Doe (555-123-4567) reported theft. Suspect Mary Johnson fled in vehicle with plate ABC123. Contact at john.doe@email.com. SSN 123-45-6789 provided.',
            'officer_notes': 'Detective Wilson interviewed witness Sarah Brown at 123 Main Street. Credit card 1234-5678-9012-3456 was stolen.',
            'address': '456 Oak Avenue, Anytown, NY',
            'witness_info': 'Called Mike Davis (555-987-6543) for statement. License plate XYZ789 seen.'
        },
        {
            'case_id': 'CASE-002',
            'narrative': 'P.O. Johnson arrived at scene. Victim contacted family member Lisa White. Address 789 Pine Street confirmed.',
            'officer_notes': 'Driver license A1234567 checked. Phone 555-111-2222 verified.',
            'address': '1010 First Avenue, Somewhere, CA',
            'witness_info': 'Mrs. Jane Smith provided statement. Email jane.smith@test.com.'
        }
    ])
    return test_data

def run_comprehensive_tests():
    """Run comprehensive tests of the DataSanitizer."""
    logger.info("🧪 Starting comprehensive tests")
    
    # Initialize sanitizer
    sanitizer = ComprehensiveDataSanitizer()
    
    # Create test data
    test_df = create_test_data()
    
    logger.info("📋 Original test data:")
    print(test_df.to_string())
    
    # Sanitize data
    sanitized_df = sanitizer.sanitize_dataframe(
        test_df, 
        text_columns=['narrative', 'officer_notes', 'address', 'witness_info'],
        id_column='case_id'
    )
    
    logger.info("\n📋 Sanitized data:")
    print(sanitized_df.to_string())
    
    # Generate report
    report = sanitizer.get_sanitization_report()
    logger.info(f"\n📊 Sanitization Report:")
    print(json.dumps(report, indent=2))
    
    # Audit the sanitized data
    violations = sanitizer.audit_unsanitized_data(sanitized_df)
    
    # Test with some unsanitized data to verify audit function
    logger.info("\n🔍 Testing audit function with unsanitized data:")
    unsanitized_test = pd.DataFrame([{
        'test_field': 'This contains John Smith phone 555-123-4567 and email test@test.com'
    }])
    
    violations = sanitizer.audit_unsanitized_data(unsanitized_test)
    logger.info(f"Violations found: {sum(len(v) for v in violations.values())}")
    
    # Save audit log
    sanitizer.save_audit_log('test_sanitization_audit.json')
    
    logger.info("✅ All tests completed")

if __name__ == "__main__":
    run_comprehensive_tests()