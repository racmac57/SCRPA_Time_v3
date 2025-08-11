Here's a full `.md` documentation version of the new CLI functionality you've added:

---

# 📘 `main.py` — Quick Export Enhancements

This document describes new command-line flags added to `main.py` for flexible automation and batch export workflows in the SCRPA system.

---

## 🚀 Quick Export Flags

### `--map-only <crime_type> [YYYY_MM_DD]`

Export just the map for a given crime type and optional target date.

```bash
python main.py --map-only "MV Theft" 2025_06_24
```

---

### `--chart-only <crime_type> [YYYY_MM_DD]`

Generate only the chart image for a specific crime type.

```bash
python main.py --chart-only "Burglary - Auto" 2025_06_24
```

---

### `--table-only <crime_type> [YYYY_MM_DD]`

Export only the incident table for a specified crime type.

```bash
python main.py --table-only "Robbery" 2025_06_24
```

---

## 🔁 Bulk Export Modes

### `--rebuild-all-charts [YYYY_MM_DD]`

Rebuild charts for **all crime types**. Logs success/failure in:

```
chart_export_log_<YYYY_MM_DD>.csv
```

```bash
python main.py --rebuild-all-charts 2025_06_24
```

---

### `--rebuild-all-tables [YYYY_MM_DD]`

Re-export tables with autofit for **all crimes**. Logs to:

```
table_export_log_<YYYY_MM_DD>.csv
```

```bash
python main.py --rebuild-all-tables 2025_06_24
```

---

## 🖼️ Full PowerPoint Generation

### `--embed-all-to-ppt [YYYY_MM_DD]`

Embed exported map, chart, and table PNGs into one PowerPoint file using layout from config.

* Output: `SCRPA_Report_<YYYY_MM_DD>.pptx`

```bash
python main.py --embed-all-to-ppt 2025_06_24
```

---

## 📄 Output Summary

| Flag                   | Purpose                 | Output Files                           |
| ---------------------- | ----------------------- | -------------------------------------- |
| `--map-only`           | Map image only          | `*_Map.png`                            |
| `--chart-only`         | Time-of-day chart only  | `*_Chart.png`                          |
| `--table-only`         | Incident table only     | `*_Table.png`                          |
| `--rebuild-all-charts` | All charts (all crimes) | CSV log: `chart_export_log_<DATE>.csv` |
| `--rebuild-all-tables` | All incident tables     | CSV log: `table_export_log_<DATE>.csv` |
| `--embed-all-to-ppt`   | Final PowerPoint report | `SCRPA_Report_<DATE>.pptx`             |

---

Would you like this saved as a file `SCRPA_CommandLineGuide.md` in your repo?
