# 📋 DataSanitizer Usage Examples
# Shows how to integrate the ComprehensiveDataSanitizer with existing SCRPA workflows

import pandas as pd
from comprehensive_data_sanitizer import ComprehensiveDataSanitizer
import logging
import re

def example_basic_usage():
    """Basic usage example for police incident data."""
    
    # Sample police incident data (similar to your SCRPA format)
    incident_data = pd.DataFrame([
        {
            'case_number': '25-060392',
            'incident_date': '2025-07-18',
            'incident_time': '20:30',
            'incident_type': 'Burglary-Auto',
            'address': '123 Main Street, Hackensack, NJ',
            'narrative': 'Officer John Smith responded. Victim Mary Johnson (201-555-1234) reported vehicle broken into. Contact email: mjohnson@email.com. SSN 123-45-6789 on file.',
            'officer': 'P.O. John Smith 374',
            'witness_statement': 'Witness Sarah Brown saw suspect fleeing. License plate ABC123 noted. Called witness at 201-555-9876.',
            'suspect_description': 'Male subject, approximately 25 years old. Name given as Mike Davis.'
        },
        {
            'case_number': '25-060393',
            'incident_date': '2025-07-19',
            'incident_time': '14:15',
            'incident_type': 'Theft',
            'address': '456 Oak Avenue, Hackensack, NJ',
            'narrative': 'Detective Lisa Wilson investigating. Credit card theft reported by victim Robert Chen. Card number 4321-8765-1234-5678 compromised.',
            'officer': 'Det. Lisa Wilson 298',
            'witness_statement': 'Store clerk Amanda White provided surveillance footage.',
            'suspect_description': 'Unknown at this time'
        }
    ])
    
    print("=== BASIC USAGE EXAMPLE ===")
    print("\n[DATA] Original Data Sample:")
    print(incident_data[['case_number', 'narrative']].to_string())
    
    # Initialize sanitizer
    sanitizer = ComprehensiveDataSanitizer()
    
    # Specify which columns contain text that needs sanitization
    text_columns = ['narrative', 'officer', 'witness_statement', 'suspect_description', 'address']
    
    # Sanitize the data
    sanitized_data = sanitizer.sanitize_dataframe(
        incident_data, 
        text_columns=text_columns,
        id_column='case_number'
    )
    
    print("\n[SECURE] Sanitized Data Sample:")
    print(sanitized_data[['case_number', 'narrative']].to_string())
    
    # Get sanitization report
    report = sanitizer.get_sanitization_report()
    print(f"\n[REPORT] Sanitization Summary:")
    print(f"   - Total operations: {report['summary']['total_operations']}")
    print(f"   - Names processed: {report['summary']['unique_names_processed']}")
    print(f"   - Processing time: {report['summary']['processing_time_seconds']:.3f}s")
    
    return sanitized_data, sanitizer

def example_audit_workflow():
    """Example showing audit workflow for data validation."""
    
    print("\n=== AUDIT WORKFLOW EXAMPLE ===")
    
    # Create data with some unsanitized content (to demonstrate audit)
    test_data = pd.DataFrame([
        {
            'case_id': 'TEST-001',
            'notes': 'This has been sanitized: SUBJECT_1 called XXX-XXX-XXXX',
            'description': 'Block address: 100 XX BLOCK Main Street'
        },
        {
            'case_id': 'TEST-002', 
            'notes': 'This was NOT sanitized: John Doe called 555-123-4567',
            'description': 'Email contact: test@email.com'
        }
    ])
    
    sanitizer = ComprehensiveDataSanitizer()
    
    # Audit the data for violations
    violations = sanitizer.audit_unsanitized_data(test_data)
    
    print(f"[AUDIT] Audit Results:")
    total_violations = sum(len(v) for v in violations.values())
    print(f"   - Total violations found: {total_violations}")
    
    for data_type, violation_list in violations.items():
        if violation_list:
            print(f"   - {data_type}: {len(violation_list)} violations")
            for violation in violation_list[:2]:  # Show first 2 examples
                print(f"     > Row {violation['row']}, Column '{violation['column']}': '{violation['match']}'")

def example_integration_with_existing_processor():
    """Example of how to integrate with existing unified_data_processor.py"""
    
    print("\n=== INTEGRATION EXAMPLE ===")
    
    # This would be your existing data processing workflow
    def simulate_existing_processor():
        """Simulate your existing data processor output."""
        return pd.DataFrame([
            {
                'case_number': '25-060394',
                'incident_type': 'Burglary-Residential', 
                'address': '789 Pine Street, Hackensack, NJ',
                'narrative': 'Homeowner Jane Smith discovered break-in. Called police at 201-555-7890. Driver license H1234567 checked.',
                'total_value_stolen': '$2,500.00'
            }
        ])
    
    # Step 1: Get processed data from your existing system
    processed_data = simulate_existing_processor()
    
    # Step 2: Add sanitization step before any AI/LLM processing
    sanitizer = ComprehensiveDataSanitizer()
    
    # Step 3: Sanitize sensitive data
    secure_data = sanitizer.sanitize_dataframe(
        processed_data,
        text_columns=['narrative', 'address'],  # Specify columns with PII
        id_column='case_number'
    )
    
    print("[SUCCESS] Data processing pipeline with sanitization:")
    print("   1. Original data processing [OK]")
    print("   2. PII sanitization [OK]") 
    print("   3. Ready for secure AI processing [OK]")
    
    # Step 4: Save audit trail
    sanitizer.save_audit_log('integration_audit_log.json')
    print("   4. Audit trail saved [OK]")
    
    return secure_data

def example_custom_patterns():
    """Example of customizing sanitization patterns for specific needs."""
    
    print("\n=== CUSTOM PATTERNS EXAMPLE ===")
    
    # Create sanitizer
    sanitizer = ComprehensiveDataSanitizer()
    
    # You can extend patterns for department-specific needs
    # Example: Add pattern for badge numbers
    badge_pattern = re.compile(r'\b(?:badge|shield)\s*#?\s*(\d{3,4})\b', re.IGNORECASE)
    
    # Add to sanitizer patterns (this would require extending the class)
    # sanitizer.custom_patterns = {'badge': badge_pattern}
    
    test_text = "Officer responded with badge #374 to the scene"
    print(f"[EXAMPLE] Custom pattern example: '{test_text}'")
    print("   > Could be sanitized to: 'Officer responded with badge BADGE_XXX to the scene'")

if __name__ == "__main__":
    # Run all examples
    logging.basicConfig(level=logging.INFO)
    
    # Basic usage
    sanitized_data, sanitizer = example_basic_usage()
    
    # Audit workflow
    example_audit_workflow()
    
    # Integration example
    secure_data = example_integration_with_existing_processor()
    
    # Custom patterns
    example_custom_patterns()
    
    print("\n[SUMMARY] KEY TAKEAWAYS:")
    print("   - Always sanitize data BEFORE AI/LLM processing")
    print("   - Use audit functions to verify sanitization")
    print("   - Save audit logs for compliance")
    print("   - Consistent name replacement (SUBJECT_1, SUBJECT_2, etc.)")
    print("   - Block-level addresses only (100 XX BLOCK Main Street)")