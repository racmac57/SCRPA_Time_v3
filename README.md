# SCRPA Time v3

**Special Crime Reduction and Pattern Analysis — Time Reporting Pipeline**
Hackensack Police Department | Internal Use

---

## What This Project Does

Processes weekly CAD and RMS crime data exports into filtered, validated datasets
for Power BI reporting. Covers six primary crime categories with hybrid CAD/RMS
cross-validation and automated quality scoring.

**Primary entry point:**
```bash
python SCRPA_Time_v3_Production_Pipeline.py
```

**Expected output:** Filtered CAD and RMS CSVs in `05_Exports/`, ready for Power BI refresh.

---

## Directory Structure

| Folder | Purpose |
|--------|---------|
| `01_scripts/` | Production pipeline scripts and M Code |
| `02_old_tools/` | Archived/retired scripts |
| `03_output/` | Pipeline output (excluded from git) |
| `04_powerbi/` | Power BI input data files |
| `05_Exports/` | Pipeline export files (excluded from git) |
| `07_documentation/` | Technical docs, user manual, changelogs |
| `08_json/` | JSON data files (arcgis_pro_layers excluded from git) |
| `09_arcvive/` | Archived reports and templates |
| `10_Refrence_Files/` | Reference/lookup data (NJ_Geocode .loz excluded from git) |
| `_large_offrepo/` | Large GeoJSON/ZIP files — stored locally only, excluded from git |
| `config/` | Configuration files |

---

## Requirements

- Python 3.7+
- pandas, numpy
- Power BI Desktop (for report integration)

---

## Git Repository

**Remote:** https://github.com/racmac57/SCRPA_Time_v3
**Default branch:** `main`

### Files Excluded from Git

Large files and generated outputs are excluded via `.gitignore`:

| Path | Reason |
|------|--------|
| `_large_offrepo/` | GeoJSON and ZIP files over 100 MB |
| `08_json/arcgis_pro_layers/` | ArcGIS layer exports, too large for GitHub |
| `10_Refrence_Files/NJ_Geocode/*.loz` | NJ geocoder binary, 160 MB |
| `03_output/` | Generated pipeline output |
| `05_Exports/` | Generated export files |
| `logs/` | Runtime log files |
| `desktop.ini` | Windows/OneDrive system files |

These files live on the local machine and OneDrive only. Do not commit them.

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 3.0 | August 2025 | Production pipeline, Power BI integration, full documentation |
| 3.1 | April 2026 | Git history rewritten — large files stripped from history; clean `main` branch established on GitHub; `desktop.ini` files removed from tracking |

---

## Documentation

Full documentation is in `07_documentation/`:

- `README_SCRPA_Time_v3.md` — Pipeline overview and quick start
- `SCRPA_User_Manual_v3.md` — Operation procedures
- `SCRPA_Technical_Documentation_v3.md` — Code and maintenance reference
- `SCRPA_Troubleshooting_Guide_v3.md` — Problem resolution
- `SCRPA_PowerBI_Integration_Guide_v3.md` — Power BI connection procedures

---

*Last updated: April 2026*
