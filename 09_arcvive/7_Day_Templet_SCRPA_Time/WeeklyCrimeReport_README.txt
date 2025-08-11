# Weekly Crime Report Export Engine

This script automates the export, reporting, archiving, and email distribution of crime incident data for Hackensack PD.

## Features
- 📊 Chart and summary table generation (flat and pivot)
- 🗺️ Map and layout export support
- 📄 PDF report builder with configurable time bins
- 📦 ZIP packaging of report assets per crime type
- ✉️ Auto-email to recipients listed in `email_recipients.csv`
- 🧾 Logging for email + archive events
- 🧪 Dry-run support to simulate all steps safely

## How to Run

Use ArcGIS Pro Python (or Windows Command Line) to execute:

```
python WeeklyCrimeReport_ExportEngine.py --report --email
```

### Available Options

| Flag              | Description                                         |
|-------------------|-----------------------------------------------------|
| `--report`        | Generate all charts, PDFs, and ZIPs                 |
| `--email`         | Email all ZIPs to contacts in config                |
| `--date YYYY-MM-DD` | Override report date (for historical reports)    |
| `--archive`       | Move old folders (older than 30 days) to `_Archive` |
| `--archive-days N`| Set custom folder age limit for archiving          |
| `--dry-run`       | Simulate all actions (no file writes or sends)     |

## Required Config Files

| File                         | Description                               |
|------------------------------|-------------------------------------------|
| `chart_suffixes.csv`         | List of suffixes like `7Day`, `YTD`       |
| `email_recipients.csv`       | One `Email` column of contacts to receive |
| `email_log.csv` (auto)       | Log of all emails sent                    |
| `_Archive/archive_log.csv`   | Log of all zipped archives                |

These are auto-created with defaults if missing.

## Output Folders

- All exports are placed under:
```
C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reports
```

Each crime type gets its own folder with maps, tables, PDFs, and a ZIP.