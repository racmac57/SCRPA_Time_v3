import pandas as pd
import re
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────────
CAD_EXPORT       = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA\2025_08_01_19_38_12_SCRPA_CAD.xlsx")
STANDARDIZED_CAD = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\C08W31_20250802_7Day_cad_data_standardized.csv")
REFERENCE_FILE   = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\CallType_Categories.xlsx")
DIAG_CSV         = STANDARDIZED_CAD.parent / "mapping_diagnostics.csv"
FIXED_CAD_CSV    = STANDARDIZED_CAD.parent / "C08W31_20250802_7Day_cad_data_standardized_fixed.csv"
# ─────────────────────────────────────────────────────────────────────────────

def normalize_key(value: str) -> str:
    """Trim, collapse spaces, strip punctuation, uppercase."""
    if pd.isna(value):
        return ""
    s = str(value).strip()
    s = re.sub(r"\s+", " ", s)
    s = s.strip("-–—:;,.\u2013\u2014")
    return s.upper()

def main():
    # 1) Load your current standardized CAD output
    cad_std = pd.read_csv(STANDARDIZED_CAD, dtype=str, low_memory=False)

    # 2) Load raw CAD export
    raw = pd.read_excel(CAD_EXPORT, dtype=str)
    raw['incident_raw']  = raw['Incident']
    raw['incident_norm'] = raw['incident_raw'].map(normalize_key)
    raw['case_number']   = raw['ReportNumberNew']

    # 3) Load reference mapping
    ref = pd.read_excel(REFERENCE_FILE, dtype=str)
    ref['incident_norm'] = ref['Incident'].map(normalize_key)
    ref = ref.rename(columns={
        'Response Type':    'response_type_cad_ref',
        'Category Type':    'category_type_cad_ref'
    })

    # 4) Duplicate reference keys
    dup = ref['incident_norm'][ref['incident_norm'].duplicated(keep=False)].value_counts().to_dict()

    # 5) Merge raw CAD → reference
    merged = raw.merge(
        ref[['incident_norm','response_type_cad_ref','category_type_cad_ref']],
        on='incident_norm', how='left', indicator=True
    )

    # 6) Diagnostics
    zero = merged[merged['_merge']=='left_only'][['incident_raw','incident_norm']].copy()
    zero['issue'] = 'no_match'
    multi = pd.DataFrame([{'incident_norm':k,'ref_count':v} for k,v in dup.items()])
    multi['issue'] = 'multi_ref'
    zero = zero.rename(columns={'incident_raw':'raw_value'}).assign(cad_count=len(merged))
    multi = multi.assign(cad_count=merged.groupby('incident_norm').size().reindex(multi['incident_norm']).fillna(0).astype(int))
    diag = pd.concat([zero, multi], sort=False)
    diag.to_csv(DIAG_CSV, index=False)

    # 7) Create corrected CAD columns
    merged['response_type_cad_new']  = merged['response_type_cad_ref'].fillna("Other")
    merged['category_type_cad_new']  = merged['category_type_cad_ref'].fillna("Other")

    # 8) Merge back, using suffixes to avoid collision
    fixed = cad_std.merge(
        merged[['case_number','response_type_cad_new','category_type_cad_new']],
        on='case_number', how='left'
    )

    # 9) Overwrite old CAD fields, drop temp
    if 'response_type_cad' in fixed.columns:
        fixed['response_type_cad'] = fixed['response_type_cad_new']
    else:
        fixed.rename(columns={'response_type_cad_new':'response_type_cad'}, inplace=True)

    if 'category_type_cad' in fixed.columns:
        fixed['category_type_cad'] = fixed['category_type_cad_new']
    else:
        fixed.rename(columns={'category_type_cad_new':'category_type_cad'}, inplace=True)

    fixed.drop(columns=['response_type_cad_new','category_type_cad_new'], inplace=True)

    # 10) Save fixed CSV
    fixed.to_csv(FIXED_CAD_CSV, index=False)

    # 11) Summary
    print(f"Diagnostics CSV: {DIAG_CSV}")
    print(f"Fixed CAD CSV:   {FIXED_CAD_CSV}")
    print(f"- Total CAD rows:           {len(raw)}")
    print(f"- Unmatched incidents:      {len(zero)}")
    print(f"- Duplicate reference keys: {len(multi)}")
    mapped = fixed['category_type_cad'].notna().sum()
    print(f"- Mapped category_type_cad: {mapped}/{len(fixed)}")

if __name__ == "__main__":
    main()
