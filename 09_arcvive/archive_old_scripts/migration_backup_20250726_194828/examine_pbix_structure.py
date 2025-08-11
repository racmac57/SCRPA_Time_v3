# examine_pbix_structure.py
import zipfile
import sys
import os

def usage():
    script = os.path.basename(sys.argv[0])
    print(f"Usage: python {script} <path to .pbix file>")
    sys.exit(1)

if len(sys.argv) < 2:
    usage()

pbix_path = sys.argv[1]
if not os.path.isfile(pbix_path):
    print(f"Error: file not found → {pbix_path}")
    usage()

with zipfile.ZipFile(pbix_path, 'r') as z:
    found = False
    for name in z.namelist():
        if 'mashup' in name.lower():
            print(name)
            found = True
    if not found:
        print("No DataMashup file found in this PBIX.")
