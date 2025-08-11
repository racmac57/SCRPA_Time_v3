import os
import glob
import pandas as pd

# 1) Always resolve to this script’s folder, no matter where you launch Python from
base_dir = os.path.dirname(os.path.abspath(__file__))

# 2) Grab only the source .xlsx files (ignore the master output if it exists)
pattern    = os.path.join(base_dir, "*.xlsx")
all_files  = glob.glob(pattern)
lookup_files = [
    f for f in all_files
    if os.path.basename(f).lower() not in ("zone_grid_master.xlsx",)
]

# 3) Debug: confirm what we found
print("🔍 Found lookup files:")
for f in lookup_files:
    print("   ", os.path.basename(f))
if not lookup_files:
    raise FileNotFoundError(f"No .xlsx lookup files found in {base_dir}")

# 4) Read & concatenate
dfs = [pd.read_excel(f) for f in lookup_files]
combined = pd.concat(dfs, ignore_index=True)

# 5) Dedupe on the mapping keys
combined = combined.drop_duplicates(subset=["CrossStreetName", "Grid", "PDZone"])

# 6) Write out your master lookup
master_path = os.path.join(base_dir, "zone_grid_master.xlsx")
combined.to_excel(master_path, index=False)

print(f"\n✅ zone_grid_master.xlsx written ({len(combined)} rows).")
