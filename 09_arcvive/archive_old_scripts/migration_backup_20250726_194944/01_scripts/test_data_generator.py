# 🧪 Test Data Generator for SCRPA Security Validation
# Author: Claude Code (Anthropic)
# Purpose: Generate realistic test data with known sensitive patterns for security testing
# Features: Police incident data with embedded PII, addresses, phone numbers, SSNs, etc.

import pandas as pd
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SensitiveDataPatterns:
    """Repository of sensitive data patterns for testing."""
    
    # Names (mix of common and realistic police names)
    FIRST_NAMES = [
        "John", "Jane", "Michael", "Sarah", "David", "Lisa", "Robert", "Maria",
        "James", "Jennifer", "William", "Patricia", "Richard", "Linda", "Joseph", "Barbara",
        "Thomas", "Elizabeth", "Christopher", "Susan", "Charles", "Jessica", "Daniel", "Karen",
        "Matthew", "Nancy", "Anthony", "Betty", "Mark", "Helen", "Donald", "Sandra"
    ]
    
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
        "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
        "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young"
    ]
    
    # Phone number patterns
    AREA_CODES = ["201", "551", "973", "732", "908", "609", "856", "862", "848"]
    
    # Street names for addresses
    STREET_NAMES = [
        "Main Street", "Oak Avenue", "Pine Road", "Elm Drive", "Cedar Lane",
        "First Avenue", "Second Street", "Park Place", "Washington Ave", "Lincoln Road",
        "Maple Street", "Church Street", "School Street", "Water Street", "High Street",
        "Mill Road", "Spring Street", "Prospect Street", "Union Street", "Franklin Avenue"
    ]
    
    CITIES = [
        "Hackensack", "Teaneck", "Englewood", "Fair Lawn", "Paramus",
        "Ridgewood", "Bergenfield", "New Milford", "Dumont", "Cresskill"
    ]
    
    # License plate patterns (NJ format examples)
    LICENSE_PATTERNS = [
        "ABC123", "XYZ789", "DEF456", "GHI012", "JKL345", "MNO678", "PQR901", "STU234"
    ]
    
    # Email domains
    EMAIL_DOMAINS = [
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
        "icloud.com", "comcast.net", "verizon.net", "att.net"
    ]
    
    # Incident types
    INCIDENT_TYPES = [
        "Burglary - Residential", "Burglary - Auto", "Theft", "Robbery", "Assault",
        "Domestic Violence", "Drug Possession", "DUI", "Vandalism", "Fraud",
        "Sexual Offense", "Motor Vehicle Theft", "Harassment", "Trespassing"
    ]
    
    # Officer names/badges
    OFFICER_NAMES = [
        "P.O. John Smith 374", "Det. Sarah Wilson 298", "Sgt. Michael Johnson 156",
        "P.O. Lisa Brown 429", "Det. David Garcia 301", "P.O. Maria Rodriguez 445",
        "Sgt. Robert Miller 089", "P.O. Jennifer Davis 267", "Det. James Martinez 334",
        "P.O. Patricia Anderson 178"
    ]

def generate_name() -> str:
    """Generate a realistic full name."""
    first = random.choice(SensitiveDataPatterns.FIRST_NAMES)
    last = random.choice(SensitiveDataPatterns.LAST_NAMES)
    return f"{first} {last}"

def generate_phone_number() -> str:
    """Generate a realistic phone number."""
    area_code = random.choice(SensitiveDataPatterns.AREA_CODES)
    exchange = random.randint(200, 999)
    number = random.randint(1000, 9999)
    
    # Mix different formats
    formats = [
        f"{area_code}-{exchange}-{number}",
        f"({area_code}) {exchange}-{number}",
        f"{area_code}.{exchange}.{number}",
        f"{area_code}{exchange}{number}"
    ]
    
    return random.choice(formats)

def generate_ssn() -> str:
    """Generate a realistic SSN pattern (not real SSN)."""
    # Use invalid SSN ranges for testing
    area = random.randint(900, 999)  # Invalid area numbers
    group = random.randint(10, 99)
    serial = random.randint(1000, 9999)
    
    formats = [
        f"{area}-{group}-{serial}",
        f"{area} {group} {serial}",
        f"{area}{group}{serial}"
    ]
    
    return random.choice(formats)

def generate_email() -> str:
    """Generate a realistic email address."""
    first = random.choice(SensitiveDataPatterns.FIRST_NAMES).lower()
    last = random.choice(SensitiveDataPatterns.LAST_NAMES).lower()
    domain = random.choice(SensitiveDataPatterns.EMAIL_DOMAINS)
    
    patterns = [
        f"{first}.{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{first}_{last}@{domain}"
    ]
    
    return random.choice(patterns)

def generate_address() -> str:
    """Generate a realistic address."""
    number = random.randint(10, 9999)
    street = random.choice(SensitiveDataPatterns.STREET_NAMES)
    city = random.choice(SensitiveDataPatterns.CITIES)
    
    return f"{number} {street}, {city}, NJ"

def generate_license_plate() -> str:
    """Generate a realistic license plate."""
    return random.choice(SensitiveDataPatterns.LICENSE_PATTERNS)

def generate_credit_card() -> str:
    """Generate a test credit card number pattern."""
    # Use invalid Luhn check digits for testing
    patterns = [
        "4111-1111-1111-1111",  # Test Visa pattern
        "5555-5555-5555-4444",  # Test MasterCard pattern
        "3782-822463-10005",    # Test Amex pattern
        "6011111111111117"      # Test Discover pattern
    ]
    
    return random.choice(patterns)

def generate_narrative_with_pii() -> str:
    """Generate a realistic police narrative with embedded PII."""
    
    victim_name = generate_name()
    suspect_name = generate_name()
    witness_name = generate_name()
    victim_phone = generate_phone_number()
    victim_email = generate_email()
    victim_ssn = generate_ssn()
    license_plate = generate_license_plate()
    credit_card = generate_credit_card()
    
    narratives = [
        f"Officer responded to call from victim {victim_name} ({victim_phone}) reporting break-in. "
        f"Suspect {suspect_name} fled scene in vehicle with plate {license_plate}. "
        f"Victim contact email: {victim_email}. SSN {victim_ssn} verified.",
        
        f"Domestic disturbance reported by {victim_name}. Suspect {suspect_name} arrested on scene. "
        f"Victim provided phone {victim_phone} for follow-up. Witness {witness_name} interviewed.",
        
        f"Credit card fraud reported by {victim_name}. Card number {credit_card} compromised. "
        f"Contact information: {victim_phone}, {victim_email}. Driver license checked with SSN {victim_ssn}.",
        
        f"Motor vehicle theft reported. Owner {victim_name} states vehicle plate {license_plate} stolen. "
        f"Contact at {victim_phone}. Witness {witness_name} saw suspect {suspect_name} flee scene.",
        
        f"Burglary in progress. Homeowner {victim_name} called police at {victim_phone}. "
        f"Suspect {suspect_name} apprehended. Victim email {victim_email} for report delivery. "
        f"ID verified with SSN {victim_ssn}.",
    ]
    
    return random.choice(narratives)

def generate_officer_notes_with_pii() -> str:
    """Generate officer notes with embedded sensitive information."""
    
    subject_name = generate_name()
    contact_phone = generate_phone_number()
    dl_number = f"N{random.randint(10000000, 99999999)}"  # NJ DL format
    
    notes = [
        f"Interviewed subject {subject_name}. Phone number {contact_phone} verified. "
        f"Driver license {dl_number} checked with no warrants.",
        
        f"Witness {subject_name} provided statement. Contact info: {contact_phone}. "
        f"Reliable witness, has assisted in previous investigations.",
        
        f"Suspect {subject_name} processed and released. Emergency contact {contact_phone}. "
        f"Driver license {dl_number} suspended pending court hearing.",
        
        f"Victim {subject_name} transported for medical evaluation. "
        f"Family notified at {contact_phone}. Follow-up required.",
    ]
    
    return random.choice(notes)

def generate_test_data(num_records: int = 20) -> pd.DataFrame:
    """
    Generate comprehensive test dataset with embedded sensitive information.
    
    Args:
        num_records: Number of test records to generate
        
    Returns:
        DataFrame with realistic police incident data containing PII
    """
    
    logger.info(f"Generating {num_records} test records with embedded PII")
    
    records = []
    
    for i in range(num_records):
        # Generate case number
        case_num = f"25-{60000 + i:06d}"
        
        # Generate incident date (recent)
        base_date = datetime.now() - timedelta(days=random.randint(0, 30))
        incident_date = base_date.strftime("%Y-%m-%d")
        incident_time = f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"
        
        # Create record with embedded PII
        record = {
            'case_number': case_num,
            'incident_date': incident_date,
            'incident_time': incident_time,
            'incident_type': random.choice(SensitiveDataPatterns.INCIDENT_TYPES),
            'address': generate_address(),
            'narrative': generate_narrative_with_pii(),
            'officer': random.choice(SensitiveDataPatterns.OFFICER_NAMES),
            'officer_notes': generate_officer_notes_with_pii(),
            'witness_statement': f"Witness {generate_name()} contacted at {generate_phone_number()}.",
            'suspect_description': f"Suspect identified as {generate_name()}, DOB verified with SSN {generate_ssn()}.",
            'victim_info': f"Victim {generate_name()} ({generate_phone_number()}) - email: {generate_email()}",
            'evidence_log': f"License plate {generate_license_plate()} photographed. "
                           f"Credit card {generate_credit_card()} recovered.",
            'case_status': random.choice(['Active Investigation', 'Cleared/Closed', 'Suspended']),
            'grid': random.choice(['A1', 'B2', 'C3', 'D4', 'E1', 'F2']),
            'zone': str(random.randint(1, 6)),
            'total_value_stolen': f"${random.randint(0, 10000)}.00"
        }
        
        records.append(record)
    
    df = pd.DataFrame(records)
    
    logger.info(f"Generated test dataset with {len(df)} records containing:")
    logger.info(f"  - Names: ~{num_records * 4} embedded")
    logger.info(f"  - Phone numbers: ~{num_records * 3} embedded")  
    logger.info(f"  - SSNs: ~{num_records * 2} embedded")
    logger.info(f"  - Email addresses: ~{num_records * 2} embedded")
    logger.info(f"  - License plates: ~{num_records * 2} embedded")
    logger.info(f"  - Credit cards: ~{num_records} embedded")
    
    return df

def generate_edge_case_data() -> pd.DataFrame:
    """Generate edge cases for testing sanitization robustness."""
    
    edge_cases = [
        {
            'case_number': 'EDGE-001',
            'narrative': 'Multiple formats: John Smith (555) 123-4567, jane.doe@email.com, SSN: 123 45 6789',
            'test_description': 'Multiple PII formats in single field'
        },
        {
            'case_number': 'EDGE-002', 
            'narrative': 'Embedded: Contact555-123-4567immediately, emailtest@test.comurgent',
            'test_description': 'PII without spaces/punctuation'
        },
        {
            'case_number': 'EDGE-003',
            'narrative': 'Case sensitive: JOHN SMITH, john smith, John SMITH at 555.123.4567',
            'test_description': 'Case sensitivity variations'
        },
        {
            'case_number': 'EDGE-004',
            'narrative': 'Special chars: John O\'Connor, Mary-Jane Smith, José García (555) 123-4567',
            'test_description': 'Names with special characters'
        },
        {
            'case_number': 'EDGE-005',
            'narrative': 'Partial SSN 123-45-#### and phone 555-###-4567 redacted',
            'test_description': 'Partially masked data'
        }
    ]
    
    return pd.DataFrame(edge_cases)

def create_validation_dataset() -> Dict[str, pd.DataFrame]:
    """Create comprehensive validation dataset for security testing."""
    
    return {
        'standard_test_data': generate_test_data(20),
        'edge_case_data': generate_edge_case_data(),
        'high_pii_density': generate_test_data(5),  # For intensive PII testing
        'minimal_data': pd.DataFrame([{
            'case_number': 'MIN-001',
            'narrative': 'Simple test case with no PII',
            'incident_type': 'Test'
        }])
    }

if __name__ == "__main__":
    # Generate and display sample test data
    print("🧪 SCRPA Test Data Generator")
    print("=" * 50)
    
    # Generate standard test data
    test_data = generate_test_data(5)
    
    print(f"\n📊 Generated {len(test_data)} test records")
    print("\nSample record (with embedded PII for testing):")
    print(f"Case: {test_data.iloc[0]['case_number']}")
    print(f"Narrative: {test_data.iloc[0]['narrative'][:100]}...")
    print(f"Officer Notes: {test_data.iloc[0]['officer_notes'][:100]}...")
    
    # Generate edge cases
    edge_data = generate_edge_case_data()
    print(f"\n🔧 Generated {len(edge_data)} edge case records")
    
    # Save for testing
    test_data.to_csv('test_data_with_pii.csv', index=False)
    edge_data.to_csv('edge_case_test_data.csv', index=False)
    
    print(f"\n💾 Test data saved:")
    print(f"  - test_data_with_pii.csv ({len(test_data)} records)")
    print(f"  - edge_case_test_data.csv ({len(edge_data)} records)")
    print(f"\n⚠️  WARNING: Test data contains synthetic PII for validation purposes only!")
    print(f"   Delete these files after testing is complete.")