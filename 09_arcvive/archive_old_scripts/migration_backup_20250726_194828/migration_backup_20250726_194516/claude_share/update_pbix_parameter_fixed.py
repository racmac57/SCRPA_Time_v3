#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_pbix_parameter_fixed.py

Fixed version that handles multiple potential DataMashup file locations.
A script to update a Power BI parameter value in a .pbix (or .pbit) file by
unzipping the file, modifying the DataMashup with regex, and re-zipping.

Usage:
    python update_pbix_parameter_fixed.py \
        --input SourceReport.pbix \
        --output UpdatedReport.pbix \
        --param BasePath \
        --value "C:\\New\\Data\\Path\\"
"""

import argparse
import zipfile
import os
import re
import tempfile
import shutil

def find_datamashup_file(temp_dir):
    """Find the DataMashup file in the extracted PBIX contents."""
    
    # Common locations where DataMashup might be found
    potential_locations = [
        'DataMashup',                    # Root level (most common)
        'DataModel/DataMashup',          # In DataModel folder
        'Model/DataMashup',              # In Model folder  
        'Mashup/DataMashup',             # In Mashup folder
        'PowerQuery/DataMashup',         # In PowerQuery folder
        'DataMashup.bin',                # With .bin extension
        'DataMashup.m',                  # With .m extension
        'DataMashup.pq',                 # With .pq extension
        'Report/DataMashup',             # In Report folder
        'DataModelSchema/DataMashup'     # In DataModelSchema folder
    ]
    
    print("Searching for DataMashup file...")
    
    # Check each potential location
    for location in potential_locations:
        mashup_path = os.path.join(temp_dir, location)
        if os.path.exists(mashup_path):
            print(f"  SUCCESS: Found DataMashup at: {location}")
            return mashup_path
    
    # If not found in common locations, search recursively
    print("  DataMashup not found in common locations, searching recursively...")
    
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            # Check for files with 'mashup' in the name
            if 'mashup' in file.lower() or 'datamashup' in file.lower():
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, temp_dir)
                print(f"  CANDIDATE: Found {rel_path}")
                
                # Verify it contains M-code by checking content
                if verify_mashup_content(full_path):
                    print(f"  SUCCESS: Verified M-code content in: {rel_path}")
                    return full_path
    
    # Last resort: search for files containing M-code patterns
    print("  Searching all files for M-code patterns...")
    
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            # Skip obviously binary files
            if file.endswith(('.png', '.jpg', '.gif', '.ico', '.exe', '.dll')):
                continue
                
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, temp_dir)
            
            try:
                # Check if file contains M-code patterns
                if verify_mashup_content(full_path):
                    print(f"  SUCCESS: Found M-code in: {rel_path}")
                    return full_path
            except:
                continue  # Skip files that can't be read
    
    return None

def verify_mashup_content(file_path):
    """Verify that a file contains M-code (DataMashup content)."""
    try:
        with open(file_path, 'rb') as f:
            # Read first 2KB to check for M-code patterns
            content = f.read(2048)
        
        # Try different encodings
        encodings = ['utf-8', 'latin1', 'utf-16le', 'utf-16be']
        
        for encoding in encodings:
            try:
                text = content.decode(encoding, errors='ignore')
                
                # M-code patterns that indicate this is a DataMashup file
                m_code_patterns = [
                    'let ',
                    'Source = ',
                    'Parameter.',
                    '#"',
                    '= Table.',
                    'in ',
                    'Query = '
                ]
                
                # Count how many patterns are found
                pattern_count = sum(1 for pattern in m_code_patterns if pattern in text)
                
                # If we find multiple M-code patterns, this is likely the DataMashup
                if pattern_count >= 3:
                    return True
                    
            except UnicodeDecodeError:
                continue
                
        return False
        
    except Exception:
        return False

def update_parameter_in_mashup(mashup_path, param_name, new_value):
    """Update parameter in the DataMashup file with improved error handling."""
    
    print(f"Updating parameter '{param_name}' in DataMashup file...")
    
    # Read binary, decode with multiple encoding attempts
    with open(mashup_path, 'rb') as f:
        data = f.read()
    
    # Try different encodings
    encodings = ['latin1', 'utf-8', 'utf-16le', 'utf-16be']
    text = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            text = data.decode(encoding)
            used_encoding = encoding
            print(f"  Successfully decoded with {encoding}")
            break
        except UnicodeDecodeError:
            continue
    
    if text is None:
        raise ValueError("Could not decode DataMashup file with any known encoding")
    
    # Create regex pattern to find parameter assignment
    # Handles variations like:
    # let ParamName = "value"
    # let ParamName="value"  
    # let   ParamName   =   "value"
    pattern = re.compile(
        r'(let\s+' + re.escape(param_name) + r'\s*=\s*")([^"]*)(")', 
        re.IGNORECASE | re.MULTILINE
    )
    
    # Check if parameter exists
    if not pattern.search(text):
        # Try alternative patterns
        alt_patterns = [
            # Without quotes
            re.compile(r'(let\s+' + re.escape(param_name) + r'\s*=\s*)([^,;\r\n]+)', re.IGNORECASE),
            # With single quotes
            re.compile(r"(let\s+" + re.escape(param_name) + r"\s*=\s*')([^']*)(')", re.IGNORECASE),
        ]
        
        found_pattern = None
        for alt_pattern in alt_patterns:
            if alt_pattern.search(text):
                found_pattern = alt_pattern
                print(f"  Found parameter with alternative pattern")
                break
        
        if not found_pattern:
            raise ValueError(f"Parameter '{param_name}' not found in DataMashup file")
        
        pattern = found_pattern
    
    # Update the parameter value
    updated_text = pattern.sub(r'\1' + new_value + r'\3', text)
    
    # Verify the update worked
    if updated_text == text:
        raise ValueError(f"Parameter '{param_name}' was not updated (text unchanged)")
    
    print(f"  Parameter updated successfully")
    
    # Write back with same encoding
    with open(mashup_path, 'wb') as f:
        f.write(updated_text.encode(used_encoding))

def process_pbix(input_pbix, output_pbix, param_name, new_value):
    """Process PBIX file with improved DataMashup detection."""
    
    print(f"Processing PBIX: {os.path.basename(input_pbix)}")
    
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"Extracting PBIX to temporary directory...")
        
        # Extract all contents
        with zipfile.ZipFile(input_pbix, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        print("  Extraction completed")
        
        # Find DataMashup file with improved logic
        mashup_file = find_datamashup_file(temp_dir)
        
        if mashup_file is None:
            raise FileNotFoundError(
                "Could not locate DataMashup file in PBIX archive. "
                "This PBIX file may not contain parameters or uses a different structure."
            )
        
        # Update parameter in DataMashup
        update_parameter_in_mashup(mashup_file, param_name, new_value)
        
        print("Creating updated PBIX file...")
        
        # Create new pbix with updated DataMashup
        with zipfile.ZipFile(output_pbix, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    # Calculate relative path from temp_dir
                    rel_path = os.path.relpath(full_path, temp_dir)
                    zip_out.write(full_path, rel_path)
        
        print("  PBIX file created successfully")
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)

def validate_pbix_file(pbix_path):
    """Validate that the file is a valid PBIX file."""
    if not os.path.exists(pbix_path):
        raise FileNotFoundError(f"PBIX file not found: {pbix_path}")
    
    if not pbix_path.lower().endswith(('.pbix', '.pbit')):
        raise ValueError(f"File must have .pbix or .pbit extension: {pbix_path}")
    
    # Try to open as ZIP file
    try:
        with zipfile.ZipFile(pbix_path, 'r') as zip_ref:
            # Basic validation - should have some standard PBIX files
            file_list = zip_ref.namelist()
            
            # Look for common PBIX files
            common_files = ['Version', 'Metadata', 'Settings']
            has_common = any(any(common in f for common in common_files) for f in file_list)
            
            if not has_common:
                print("WARNING: File may not be a valid PBIX file (missing common files)")
            
    except zipfile.BadZipFile:
        raise ValueError(f"File is not a valid ZIP/PBIX file: {pbix_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Power BI PBIX parameter (Fixed Version)")
    parser.add_argument('--input', '-i', required=True, help="Path to input .pbix file")
    parser.add_argument('--output', '-o', required=True, help="Path to output .pbix file")
    parser.add_argument('--param', '-p', required=True, help="Parameter name to update")
    parser.add_argument('--value', '-v', required=True, help="New value for the parameter")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose output")
    
    args = parser.parse_args()
    
    try:
        print("PBIX Parameter Update Tool (Fixed Version)")
        print("=" * 50)
        
        # Validate input file
        validate_pbix_file(args.input)
        
        # Process the PBIX file
        process_pbix(args.input, args.output, args.param, args.value)
        
        print("=" * 50)
        print(f"SUCCESS: Updated PBIX saved to: {args.output}")
        print(f"Parameter '{args.param}' updated to: '{args.value}'")
        
    except Exception as e:
        print(f"\\nERROR: {str(e)}")
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        exit(1)