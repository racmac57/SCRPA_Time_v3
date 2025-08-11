#!/usr/bin/env python3
"""
update_pbix_parameter.py

Artifact: update_pbix_parameter.py
Timestamp: 2025-07-26 18:00:00 EST
Project: SCRPA_Time_v2
Author: R. A. Carucci
Purpose: Programmatically update Power BI PBIX mashup parameter values.
"""

import zipfile
import os
import sys
import shutil
import tempfile
import re
import argparse


def find_datamashup_file(extract_dir):
    """
    Recursively searches extract_dir for any file whose name starts with 'DataMashup'
    (case-insensitive), returns the first full path found, or raises if none exists.
    """
    for root, dirs, files in os.walk(extract_dir):
        for fname in files:
            if fname.lower().startswith('datamashup'):
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, extract_dir)
                print(f"Using mashup file: {rel_path}")
                return full_path
    raise FileNotFoundError(f"Could not locate any DataMashup file under {extract_dir}")


def process_pbix(input_pbix, output_pbix, parameter_name, new_value):
    """
    Extracts the PBIX archive, updates the specified mashup parameter, and repacks to a new PBIX.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        # Unzip PBIX contents
        with zipfile.ZipFile(input_pbix, 'r') as z:
            z.extractall(temp_dir)

        # Locate and update the mashup file
        mashup_path = find_datamashup_file(temp_dir)
        raw = open(mashup_path, 'rb').read().decode('latin1')
        pattern = rf'(let\s+{re.escape(parameter_name)}\s*=\s*)"[^"]*"'
        replacement = rf"\1\"{new_value}\""
        updated = re.sub(pattern, replacement, raw, flags=re.IGNORECASE)
        with open(mashup_path, 'wb') as f:
            f.write(updated.encode('latin1'))

        # Rezip into output PBIX
        with zipfile.ZipFile(output_pbix, 'w', zipfile.ZIP_DEFLATED) as z_out:
            for folder, _, files in os.walk(temp_dir):
                for file in files:
                    full_path = os.path.join(folder, file)
                    rel_path = os.path.relpath(full_path, temp_dir)
                    z_out.write(full_path, rel_path)
        print(f"Updated PBIX saved to: {output_pbix}")

    finally:
        shutil.rmtree(temp_dir)


def main():
    parser = argparse.ArgumentParser(description="Update a Power BI PBIX mashup parameter")
    parser.add_argument('--input', '-i', required=True, help="Path to input .pbix file")
    parser.add_argument('--output', '-o', required=True, help="Path to output .pbix file")
    parser.add_argument('--param', '-p', required=True, help="Mashup parameter name to update")
    parser.add_argument('--value', '-v', required=True, help="New value for the parameter")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: Input file not found → {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        process_pbix(args.input, args.output, args.param, args.value)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
