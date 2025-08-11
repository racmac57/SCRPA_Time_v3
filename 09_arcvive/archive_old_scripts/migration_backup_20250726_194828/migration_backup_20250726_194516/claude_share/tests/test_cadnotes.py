import pandas as pd
import sys
from pathlib import Path

# Add the 01_scripts directory to the path so we can import the processors
scripts_path = Path(__file__).parent.parent.parent / "01_scripts"
sys.path.insert(0, str(scripts_path))

from enhanced_cadnotes_python import EnhancedCADNotesProcessor

def test_username_and_timestamp_extraction():
    """Test CAD notes processing using the existing EnhancedCADNotesProcessor class."""
    # Initialize the processor
    processor = EnhancedCADNotesProcessor()
    
    # Create test DataFrame
    df = pd.DataFrame({"CADNotes": ["- Doe_J - 1/1/2025 1:02:03 PM Test"]})
    
    # Process using the existing class method
    result = processor.process_cadnotes_dataframe(df, 'CADNotes')
    
    # Verify the results using the actual column names from EnhancedCADNotesProcessor
    assert result.loc[0, "CAD_Username"] == "Doe_J"
    assert pd.to_datetime(result.loc[0, "CAD_Timestamp"]).year == 2025
    assert "Test" in result.loc[0, "CAD_Notes_Cleaned"]

def test_enhanced_processor_validation():
    """Test the processor's built-in validation against examples."""
    processor = EnhancedCADNotesProcessor()
    
    # Run the processor's own validation tests
    validation_passed = processor.validate_against_examples()
    assert validation_passed, "EnhancedCADNotesProcessor validation failed"

def test_empty_cadnotes_handling():
    """Test handling of empty CAD notes."""
    processor = EnhancedCADNotesProcessor()
    
    # Test with empty string
    df = pd.DataFrame({"CADNotes": [""]})
    result = processor.process_cadnotes_dataframe(df, 'CADNotes')
    
    assert pd.isna(result.loc[0, "CAD_Username"]) or result.loc[0, "CAD_Username"] is None
    assert pd.isna(result.loc[0, "CAD_Timestamp"]) or result.loc[0, "CAD_Timestamp"] is None
    assert pd.isna(result.loc[0, "CAD_Notes_Cleaned"]) or result.loc[0, "CAD_Notes_Cleaned"] is None

def test_complex_cadnotes_parsing():
    """Test parsing of complex CAD notes with multiple entries."""
    processor = EnhancedCADNotesProcessor()
    
    complex_note = "- klosk_J - 3/25/2025 12:06:34 PM in front of store - klosk_J - 3/25/2025 12:06:34 PM Drone deployed. Provided overwatch. - weber_r - 3/25/2025 12:12:47 PM"
    df = pd.DataFrame({"CADNotes": [complex_note]})
    
    result = processor.process_cadnotes_dataframe(df, 'CADNotes')
    
    # Should extract first username and timestamp
    assert result.loc[0, "CAD_Username"] == "Klosk_J"
    assert "03/25/2025" in result.loc[0, "CAD_Timestamp"]
    # Should contain cleaned content from multiple entries
    cleaned_text = result.loc[0, "CAD_Notes_Cleaned"].lower()
    assert "front of store" in cleaned_text or "drone deployed" in cleaned_text

def test_data_quality_scoring():
    """Test that data quality scoring is working."""
    processor = EnhancedCADNotesProcessor()
    
    df = pd.DataFrame({"CADNotes": ["- Doe_J - 1/1/2025 1:02:03 PM Test incident"]})
    result = processor.process_cadnotes_dataframe(df, 'CADNotes')
    
    # Should have a quality score
    assert 'CADNotes_Processing_Quality' in result.columns
    assert result.loc[0, 'CADNotes_Processing_Quality'] > 0
    assert result.loc[0, 'CADNotes_Processing_Quality'] <= 100
