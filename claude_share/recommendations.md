# SCRPA_Time_v2 Implementation Guide

This consolidated document combines recommendations, code snippets, and automation scripts for the SCRPA_Time_v2 project, ready to share with an AI like Claude.

## 1. Centralize Configuration

**config.py** (Python)
```python
from pathlib import Path
import os

# Base directory (allows override via ENV var)
BASE_DIR = Path(os.getenv(
    "SCRPA_BASE_DIR",
    Path.home() / "OneDrive - City of Hackensack" / "01_DataSources" / "SCRPA_Time_v2"
))

# Exposed paths
CAD_EXPORT_DIR      = BASE_DIR / "05_EXPORTS" / "_CAD" / "SCRPA"
RMS_EXPORT_DIR      = BASE_DIR / "05_EXPORTS" / "_RMS" / "SCRPA"
SCRIPTS_DIR         = BASE_DIR / "01_scripts"
LOG_DIR             = BASE_DIR / "03_output" / "logs"
REPORT_DIR          = BASE_DIR / "03_output" / "reports"
POWERBI_CSV_PATH    = BASE_DIR / "04_powerbi" / "enhanced_scrpa_data.csv"

# Ensure critical directories exist
for d in (CAD_EXPORT_DIR, RMS_EXPORT_DIR, LOG_DIR, REPORT_DIR):
    d.mkdir(parents=True, exist_ok=True)
```

**config.json** (JSON)
```json
{
  "BASE_DIR": "C:/Users/carucci_r/OneDrive - City of Hackensack/01_DataSources/SCRPA_Time_v2",
  "CAD_EXPORT_DIR": "05_EXPORTS/_CAD/SCRPA",
  "RMS_EXPORT_DIR": "05_EXPORTS/_RMS/SCRPA",
  "SCRIPTS_DIR": "01_scripts",
  "LOG_DIR": "03_output/logs",
  "REPORT_DIR": "03_output/reports",
  "POWERBI_CSV_PATH": "04_powerbi/enhanced_scrpa_data.csv"
}
```

---

## 2. Unified CAD-Notes Processor

**cadnotes_processor.py**
```python
import re
import logging
import pandas as pd

logger = logging.getLogger(__name__)

TIMESTAMP_RE = re.compile(r"\\b\\d{1,2}/\\d{1,2}/\\d{4}\\s+\\d{1,2}:\\d{2}:\\d{2}\\s*(?:AM|PM)\\b", re.IGNORECASE)
USER_RE      = re.compile(r"-\\s*([A-Za-z]+_[A-Za-z]+)\\s*-\\s*", re.IGNORECASE)

def clean_cad_notes(df: pd.DataFrame, notes_col="CADNotes"):
    text = df[notes_col].fillna("").astype(str)
    users = text.str.extract(USER_RE, expand=False)
    times = text.str.extract(TIMESTAMP_RE, expand=False)
    timestamps = pd.to_datetime(times, format="%m/%d/%Y %I:%M:%S %p", errors="coerce")
    cleaned = (text
               .str.replace(USER_RE, "", regex=True)
               .str.replace(TIMESTAMP_RE, "", regex=True)
               .str.strip(" -"))
    df = df.assign(
        CAD_Username=users,
        CAD_Timestamp=timestamps,
        CAD_Notes_Cleaned=cleaned
    )
    missing_ts = df["CAD_Timestamp"].isna().sum()
    if missing_ts:
        logger.warning(f"{missing_ts} timestamps failed to parse")
    return df
```

---

## 3. Robust Logging Setup

**logging_setup.py**
```python
import logging
from logging.handlers import RotatingFileHandler
import config

def setup_logging():
    log_path = config.LOG_DIR / "scrpa.log"
    handler = RotatingFileHandler(
        log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    root.addHandler(logging.StreamHandler())
    logging.getLogger("requests").setLevel(logging.WARNING)
```

---

## 4. Linting, Testing & CI

**.pre-commit-config.yaml**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
  - repo: https://github.com/pre-commit/mirrors-isort
    rev: v5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
```

**tests/test_cadnotes.py**
```python
import pandas as pd
from scripts.cadnotes_processor import clean_cad_notes

def test_username_and_timestamp_extraction():
    df = pd.DataFrame({"CADNotes": ["- Doe_J - 1/1/2025 1:02:03 PM Test"]})
    result = clean_cad_notes(df)
    assert result.loc[0, "CAD_Username"] == "Doe_J"
    assert result.loc[0, "CAD_Timestamp"].year == 2025
    assert "Test" in result.loc[0, "CAD_Notes_Cleaned"]
```

**.github/workflows/ci.yml**
```yaml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pre-commit run --all-files
      - run: pytest --maxfail=1 --disable-warnings -q --cov=scripts
      - run: codecov
```

---

## 5. Power BI M Code Parameterization

```m
let
    BasePath = Parameter.BasePath,
    CsvFile = BasePath & "enhanced_scrpa_data.csv",
    Source = Csv.Document(File.Contents(CsvFile), [Delimiter=",", Encoding=1252]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(Promoted,
        {
          {"Case_Number", type text},
          {"Incident_Date", type date},
          {"CAD_Timestamp", type datetime}
        })
in
    ChangedTypes
```

---

## 6. PBIX Parameter Injection Scripts

**update_pbix_parameter.py**  
```python
# (Full Python script content in update_pbix_parameter.py)
```

**update_pbix_parameter.ps1**  
```powershell
# (Full PowerShell script content in update_pbix_parameter.ps1)
```
