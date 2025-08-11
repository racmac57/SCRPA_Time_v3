#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pbix_test_extract.py

Quick test to extract and examine PBIX file contents to find DataMashup location.
"""

import zipfile
import tempfile
import os
from pathlib import Path

def quick_pbix_test():
    """Quick test of PBIX extraction."""
    
    # Path to your main PBIX file
    pbix_path = Path(__file__).parent.parent / "SCRPA_Time_v2.pbix"
    
    if not pbix_path.exists():
        print(f"PBIX file not found: {pbix_path}")
        return
    
    print(f"Testing PBIX extraction: {pbix_path.name}")
    print("=" * 50)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Extracting to: {temp_dir}")
        
        try:
            # Extract PBIX file
            with zipfile.ZipFile(pbix_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            print("\\nExtraction successful!")
            
            # List all extracted files
            print("\\nExtracted files:")
            for root, dirs, files in os.walk(temp_dir):
                level = root.replace(temp_dir, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    print(f"{subindent}{file} ({file_size:,} bytes)")
            
            # Check for DataMashup file specifically
            print("\\n" + "=" * 50)
            print("CHECKING FOR DATAMASHUP FILE:")
            
            # Try original location
            original_mashup = os.path.join(temp_dir, 'DataMashup')
            if os.path.exists(original_mashup):
                print(f"SUCCESS: Found DataMashup at root level")
                size = os.path.getsize(original_mashup)
                print(f"  Size: {size:,} bytes")
            else:
                print("DataMashup NOT found at root level")
                
                # Search for alternatives
                print("\\nSearching for alternatives...")
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if 'mashup' in file.lower() or 'datamashup' in file.lower():
                            rel_path = os.path.relpath(os.path.join(root, file), temp_dir)
                            size = os.path.getsize(os.path.join(root, file))
                            print(f"  FOUND: {rel_path} ({size:,} bytes)")
            
            # Look for files that might contain M-code
            print("\\nLooking for M-code in files...")
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, temp_dir)
                    
                    try:
                        # Only check files that might be text
                        if file.endswith(('.json', '.xml', '.txt', '.m', '.pq')) or '.' not in file:
                            with open(file_path, 'rb') as f:
                                content = f.read(1000)  # First 1KB
                            
                            # Try to decode and check for M-code patterns
                            try:
                                text = content.decode('utf-8', errors='ignore')
                                
                                m_patterns = ['let ', 'Source = ', 'Parameter.', '#"', '= Table.']
                                pattern_count = sum(1 for p in m_patterns if p in text)
                                
                                if pattern_count >= 2:
                                    print(f"  M-CODE: {rel_path} (patterns: {pattern_count})")
                                    print(f"    Preview: {text[:100]}...")
                                    
                            except:
                                pass
                    except:
                        pass
            
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    quick_pbix_test()