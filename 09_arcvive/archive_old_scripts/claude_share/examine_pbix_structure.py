#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
examine_pbix_structure.py

Script to examine the internal structure of PBIX files to understand
where the DataMashup file is actually located.
"""

import zipfile
import os
import sys
from pathlib import Path

def examine_pbix_structure(pbix_path):
    """Examine the internal structure of a PBIX file."""
    print(f"\\nExamining PBIX structure: {Path(pbix_path).name}")
    print("=" * 60)
    
    try:
        with zipfile.ZipFile(pbix_path, 'r') as zip_ref:
            # List all files in the archive
            file_list = zip_ref.namelist()
            
            print(f"Total files in archive: {len(file_list)}")
            print("\\nFull file structure:")
            
            # Sort files for better readability
            file_list.sort()
            
            # Group files by directory
            directories = {}
            for file in file_list:
                if '/' in file:
                    dir_name = '/'.join(file.split('/')[:-1])
                    if dir_name not in directories:
                        directories[dir_name] = []
                    directories[dir_name].append(file.split('/')[-1])
                else:
                    # Root level files
                    if 'ROOT' not in directories:
                        directories['ROOT'] = []
                    directories['ROOT'].append(file)
            
            # Display structure
            for dir_name, files in directories.items():
                if dir_name == 'ROOT':
                    print("\\n[ROOT DIRECTORY]")
                else:
                    print(f"\\n[{dir_name}/]")
                
                for file in sorted(files):
                    file_size = zip_ref.getinfo(file if dir_name == 'ROOT' else f"{dir_name}/{file}").file_size
                    print(f"  - {file} ({file_size:,} bytes)")
            
            # Look for DataMashup specifically
            print("\\n" + "=" * 60)
            print("SEARCHING FOR DATAMASHUP FILE:")
            
            datamashup_candidates = []
            for file in file_list:
                if 'mashup' in file.lower() or 'datamashup' in file.lower():
                    datamashup_candidates.append(file)
                    print(f"  FOUND: {file}")
            
            if not datamashup_candidates:
                print("  No files with 'mashup' or 'datamashup' in name found")
                
                # Look for other potential candidates
                print("\\n  Looking for other potential M-code files:")
                for file in file_list:
                    if any(ext in file.lower() for ext in ['.m', '.pq', '.query', '.powerquery']):
                        print(f"  POTENTIAL: {file}")
                    elif file.endswith('.bin') and 'data' in file.lower():
                        print(f"  BINARY DATA: {file}")
            
            # Try to extract and examine potential DataMashup files
            for candidate in datamashup_candidates:
                print(f"\\n  Examining content of: {candidate}")
                try:
                    with zip_ref.open(candidate) as f:
                        content = f.read(500)  # Read first 500 bytes
                        
                        # Try different encodings
                        encodings = ['utf-8', 'latin1', 'utf-16', 'ascii']
                        decoded_content = None
                        
                        for encoding in encodings:
                            try:
                                decoded_content = content.decode(encoding)
                                print(f"    Successfully decoded with {encoding}")
                                print(f"    First 200 chars: {decoded_content[:200]}")
                                break
                            except UnicodeDecodeError:
                                continue
                        
                        if not decoded_content:
                            print(f"    Binary content (first 50 bytes): {content[:50]}")
                            
                except Exception as e:
                    print(f"    Error reading file: {e}")
            
            return file_list, datamashup_candidates
            
    except Exception as e:
        print(f"ERROR: Failed to examine PBIX file: {e}")
        return [], []

def find_datamashup_file(pbix_path):
    """Find the actual DataMashup file location."""
    print(f"\\nSearching for DataMashup in: {Path(pbix_path).name}")
    
    try:
        with zipfile.ZipFile(pbix_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            # Common DataMashup locations to check
            common_locations = [
                'DataMashup',  # Root level (original assumption)
                'DataModel/DataMashup',
                'Model/DataMashup', 
                'Mashup/DataMashup',
                'PowerQuery/DataMashup',
                'DataMashup.bin',
                'DataMashup.m',
                'DataMashup.pq'
            ]
            
            found_files = []
            
            for location in common_locations:
                if location in file_list:
                    found_files.append(location)
                    print(f"  FOUND: {location}")
            
            # Search for files containing mashup-related content
            print("\\n  Searching all files for M-code patterns...")
            
            for file in file_list:
                try:
                    with zip_ref.open(file) as f:
                        # Read first 1KB to check for M-code patterns
                        content = f.read(1024)
                        
                        # Try to decode as text
                        try:
                            text_content = content.decode('utf-8', errors='ignore')
                            
                            # Look for M-code patterns
                            m_code_patterns = [
                                'let ',
                                'in ',
                                'Source = ',
                                '= Table.',
                                'Parameter.',
                                '#"'
                            ]
                            
                            pattern_count = sum(1 for pattern in m_code_patterns if pattern in text_content)
                            
                            if pattern_count >= 2:  # If multiple M-code patterns found
                                found_files.append(file)
                                print(f"  M-CODE DETECTED: {file} (patterns: {pattern_count})")
                                
                        except UnicodeDecodeError:
                            pass  # Skip binary files
                            
                except Exception:
                    pass  # Skip files that can't be read
            
            return found_files
            
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def main():
    """Main function to examine PBIX files."""
    print("PBIX STRUCTURE EXAMINER")
    print("=" * 60)
    
    # Find PBIX files in the project
    project_dir = Path(__file__).parent.parent
    pbix_files = list(project_dir.glob("*.pbix"))
    
    if not pbix_files:
        print("No PBIX files found in project directory")
        return 1
    
    print(f"Found {len(pbix_files)} PBIX files:")
    for pbix in pbix_files:
        print(f"  - {pbix.name}")
    
    # Examine each PBIX file
    all_datamashup_locations = set()
    
    for pbix_file in pbix_files:
        print("\\n" + "=" * 80)
        
        # Full structure examination
        file_list, datamashup_candidates = examine_pbix_structure(pbix_file)
        
        # Focused DataMashup search
        found_datamashup = find_datamashup_file(pbix_file)
        
        all_datamashup_locations.update(found_datamashup)
    
    # Summary
    print("\\n" + "=" * 80)
    print("SUMMARY OF DATAMASHUP LOCATIONS FOUND:")
    print("=" * 80)
    
    if all_datamashup_locations:
        for location in sorted(all_datamashup_locations):
            print(f"  {location}")
    else:
        print("  No DataMashup files found!")
    
    print("\\nRecommended update_pbix_parameter.py fixes:")
    if all_datamashup_locations:
        print("  Update the script to check these locations in order:")
        for i, location in enumerate(sorted(all_datamashup_locations), 1):
            print(f"    {i}. {location}")
    else:
        print("  Need to investigate alternative approaches for parameter updates")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())