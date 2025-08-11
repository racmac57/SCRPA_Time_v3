# SCRPA Report Automation

## 🧠 Overview

Automates the generation of maps, bar charts, and summary tables for Hackensack PD's 7-day, 28-day, and YTD crime reporting. Designed for use with ArcGIS Pro and exported via Python automation scripts.

## 📁 Folder Structure

```
SCRPA_Report_Automation/
├── 7_day_crime_report_tool_scripts/        # All logic scripts live here
│   ├── main.py                             # ✅ Main entry point
│   ├── chart_export.py                     # ✅ Generates crime distribution bar charts
│   ├── map_export.py                       # 📊 Exports ArcGIS maps for crime types
│   ├── table_export.py                     # 📄 Creates CSV tables for each crime type
│   ├── config.py                           # 🔧 Folder paths, crime mappings, settings
│   ├── batch_chart_runner.py               # 🌀 Optional batch mode for charts only
│   └── (other supporting scripts)
│
├── run_scrpa_report.bat                    # 🚀 One-click launcher for full pipeline
└── README.md                               # 📘 This file
```

## ▶️ How to Run

### Option A: Manual CLI

From `cmd.exe`:

```bash
cd 7_day_crime_report_tool_scripts
python main.py true true true 7 false 2025_06_17 --dry-run --charts-only
```

**Arguments:**

1. `generate_map`        – `true` or `false`
2. `export_charts`       – `true` or `false`
3. `export_reports`      – `true` or `false` *(not yet implemented)*
4. `day_span`            – usually `7`
5. `debug`               – `true` or `false`
6. `YYYY_MM_DD`          – report date
7. `--dry-run`           – *(optional)* Simulates file creation and logs steps only
8. `--charts-only`       – *(optional)* Only runs chart logic, skipping maps/tables

### Option B: Double-click `.bat`

Use the included `run_scrpa_report.bat`, which:

- Prompts for a report date
- Injects that date into the `main.py` script
- Executes map, chart, and CSV exports in one click

Modify the `.bat` as needed for automation:

```bat
@echo off
set /p rdate=Enter report date (YYYY_MM_DD):
cd /d "%~dp0\7_day_crime_report_tool_scripts"
python main.py true true true 7 false %rdate% --dry-run --charts-only
pause
```

## ⚙️ Setup Requirements

- ArcGIS Pro installed with valid license (ArcView or higher)
- Python 3.x ArcGIS Pro environment (arcpy)
- Valid paths in `config.py` for:
  - `REPORT_BASE_DIR`
  - `POWERPOINT_TEMPLATES`
  - Crime folder mapping

## ✅ Output

- `.../Reports/C06W21_YYYY_MM_DD/`
  - Individual subfolders for each crime type
  - Bar charts, ArcGIS map PNGs, CSV tables *(unless suppressed by flags)*
  - Processing summary log

## 🧹 Clean-Up

You can safely delete:

- `*.pyHistory`
- `updated_map_export_7day_only.py` *(if redundant)*
- `args_parser.py` *(if unused)*
- `Hybrid_Dynamic_Folder_Script.py` *(if not referenced)*

## 👨‍💻 Contact

R. Carucci – GIS / Crime Analysis – Hackensack Police Department

