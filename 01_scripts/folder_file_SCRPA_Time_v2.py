#!/usr/bin/env python3
"""
List all folders and files under the SCRPA_Time_v2 directory.
"""

import os

def list_dir_tree(root_path: str):
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Compute depth for indentation
        depth = dirpath.replace(root_path, '').count(os.sep)
        indent = '    ' * depth
        print(f"{indent}{os.path.basename(dirpath)}/")
        for filename in filenames:
            print(f"{indent}    {filename}")

if __name__ == '__main__':
    root = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
    if not os.path.isdir(root):
        raise FileNotFoundError(f"Directory not found: {root}")
    list_dir_tree(root)
