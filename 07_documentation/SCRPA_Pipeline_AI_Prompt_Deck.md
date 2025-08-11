# SCRPA Pipeline AI Prompt Deck

## Overview

This document provides comprehensive AI prompts for implementing and enhancing the SCRPA (Statistical Crime Reporting and Analysis) pipeline. Each section addresses a specific problem with a clear solution blueprint and examples.

---

## 1. CAD CallType Mapping & Response Classification

**Problem:** Inconsistent mapping logic between `response_type` and `response_type_cad` columns, and `category_type` duplication.

**Solution Steps:**
1. Load `CallType_Categories.xlsx` forcing `incident` as string.
2. Implement `map_call_type(incident)` with: Exact lookup, Partial fallback, Keyword fallback (Traffic, Alarm, Medical, Fire, Crime, Disturbance, Other).
3. Rename downstream so only `response_type_cad` and `category_type_cad` exist, then drop/rename to `response_type` and `category_type`.

**Prompt Blueprint:**
```python
def map_call_type(incident_value):
    # Exact case-insensitive lookup
    # Partial match fallback
    # Keyword fallback with same value for both Response Type and Category Type
    return response_type, category_type

# Apply mapping
df['response_type_cad'] = df['incident'].apply(lambda x: map_call_type(x)[0])
df['category_type_cad'] = df['incident'].apply(lambda x: map_call_type(x)[1])
```

**Examples:**
| Incident | Response Type | Category Type |
|----------|---------------|---------------|
| "BURGLARY AUTO" | "Crime" | "Crime" |
| "TRAFFIC STOP" | "Traffic" | "Traffic" |
| "MEDICAL EMERGENCY" | "Medical" | "Medical" |

---

## 2. Preserve "9-1-1" as Text in `how_reported`

**Problem:** Excel auto-parses "9-1-1" as date (09/01/1900).

**Solution Steps:**
1. Use `pd.read_excel(..., dtype={"How Reported": str})`.
2. Apply `clean_how_reported_911()` to normalize variants back to "9-1-1".

**Prompt Blueprint:**
```python
def clean_how_reported_911(how_reported):
    # Handle various date formats and "9-1-1" variants
    # Normalize to "9-1-1"
    return normalized_value

# Load with string dtype
df = pd.read_excel(file, dtype={"How Reported": str})
df['how_reported'] = df['how_reported'].apply(clean_how_reported_911)
```

**Examples:**
| Input | Output |
|-------|--------|
| "09/01/1900" | "9-1-1" |
| "9-1-1" | "9-1-1" |
| "911" | "9-1-1" |

---

## 3. CAD Notes Parsing & Metadata Extraction

**Problem:** `cad_notes_cleaned` still contains username/timestamp; duplicates exist.

**Solution Steps:**
1. Implement `parse_cad_notes(raw: str) -> (username, timestamp, cleaned_text)` using regex.
2. Extract patterns like `- user_name -` and timestamps `MM/DD/YYYY HH:MM:SS AM/PM`.
3. Clean out header, user, timestamp, stray date fragments, title-case the remainder.

**Prompt Blueprint:**
```python
def parse_cad_notes(raw: str) -> tuple:
    # Extract username patterns
    # Extract timestamp patterns
    # Clean and title-case remaining text
    return username, timestamp, cleaned_text

# Apply parsing
df[['cad_username', 'cad_timestamp', 'cad_notes_cleaned']] = df['cad_notes_raw'].apply(parse_cad_notes)
```

**Examples:**
| Input | Username | Timestamp | Cleaned Text |
|-------|----------|-----------|--------------|
| "kiselow_g 1/14/2025 3:47:59 PM Vehicle broken into" | "kiselow_g" | "1/14/2025 3:47:59 PM" | "Vehicle Broken Into" |
| "Gervasi_J - 02/20/2025 08:05:00 AM Property stolen" | "Gervasi_J" | "02/20/2025 08:05:00 AM" | "Property Stolen" |

---

## 4. RMS Date/Time Cascade Logic

**Problem:** Missing `incident_date` and `incident_time` if both primary and fallback are null; time parsing glitch formats `19:00:00` as `1900:00:00`.

**Solution Steps:**
1. Parse each field separately with `errors='coerce'`.
2. Chain-fill: date = Date → Date_Between → Report Date; time = Time → Time_Between → Report Time.
3. Format time via `strftime` to avoid Excel fallback artifact.

**Prompt Blueprint:**
```python
# Robust RMS date/time cascade logic
d1 = pd.to_datetime(df["incident_date_raw"], errors="coerce")
d2 = pd.to_datetime(df["incident_date_between_raw"], errors="coerce")
d3 = pd.to_datetime(df["report_date_raw"], errors="coerce")
df['incident_date'] = d1.fillna(d2).fillna(d3).dt.date

t1 = pd.to_datetime(df["incident_time_raw"], errors="coerce").dt.time
t2 = pd.to_datetime(df["incident_time_between_raw"], errors="coerce").dt.time
t3 = pd.to_datetime(df["report_time_raw"], errors="coerce").dt.time
df['incident_time'] = t1.fillna(t2).fillna(t3)
df['incident_time'] = df['incident_time'].apply(lambda t: t.strftime("%H:%M:%S") if pd.notna(t) else None)
```

**Examples:**
| Date | Date_Between | Report Date | Result |
|------|--------------|-------------|--------|
| 2025-05-11 | NaT | 2025-05-11 | 2025-05-11 |
| NaT | 2025-05-11 | 2025-05-12 | 2025-05-11 |
| NaT | NaT | 2025-05-11 | 2025-05-11 |

---

## 5. Time-of-Day Buckets & Sort Order

**Problem:** `time_of_day` duplicated or unsorted alphabetically.

**Solution Steps:**
1. Define `map_tod(t)` buckets.
2. Apply to cleaned `incident_time`.
3. Convert to ordered categorical and generate `time_of_day_sort_order`.

**Prompt Blueprint:**
```python
def map_tod(t):
    # Map time to predefined buckets
    # Return "Unknown" for invalid inputs
    return time_bucket

# Apply mapping and create ordered categorical
df['time_of_day'] = df['incident_time'].apply(map_tod)
df['time_of_day'] = pd.Categorical(df['time_of_day'], categories=ordered_buckets, ordered=True)
df['time_of_day_sort_order'] = df['time_of_day'].cat.codes + 1
```

**Examples:**
| Time | Time of Day | Sort Order |
|------|-------------|------------|
| "14:30:00" | "12:00-15:59 Afternoon" | 4 |
| "22:45:00" | "20:00-23:59 Evening" | 6 |
| "03:15:00" | "00:00-03:59 Early Morning" | 1 |

---

## 6. Block Calculation & Enhancement

**Problem:** Inconsistent block formatting; CAD ("FullAddress2") vs RMS ("location") columns.

**Solution Steps:**
1. Standardize input column to `location`.
2. Implement `calculate_block(addr)` handling intersections and numeric addresses.

**Prompt Blueprint:**
```python
def calculate_block(addr):
    # Handle numeric addresses (extract street name)
    # Handle intersections (extract street names)
    # Format as "Street Name, XXX Block"
    return block_string

# Apply to location column
df['block'] = df['location'].apply(calculate_block)
```

**Examples:**
| Address | Block |
|---------|-------|
| "123 Main St" | "Main St, 100 Block" |
| "Main St & Oak Ave" | "Main St & Oak Ave" |
| "456 Oak Ave" | "Oak Ave, 400 Block" |

---

## 7. Combine `all_incidents` from Incident_Type Columns

**Problem:** `all_incidents` empty because using wrong column names.

**Solution Steps:**
1. Use cleaned columns: `incident_type_1_cleaned`, etc.
2. Strip statute codes and join non-null entries.

**Prompt Blueprint:**
```python
def combine_incidents(row):
    # Combine incident_type_1_cleaned, incident_type_2_cleaned, incident_type_3_cleaned
    # Strip statute codes
    # Join non-null entries
    return combined_string

df['all_incidents'] = df.apply(combine_incidents, axis=1)
```

**Examples:**
| Incident Type 1 | Incident Type 2 | Incident Type 3 | All Incidents |
|-----------------|-----------------|-----------------|---------------|
| "Burglary - Auto" | None | None | "Burglary - Auto" |
| "Theft" | "Assault" | None | "Theft; Assault" |
| "Vandalism" | "Trespassing" | "Disorderly Conduct" | "Vandalism; Trespassing; Disorderly Conduct" |

---

## 8. Vehicle Fields Uppercasing

**Problem:** `vehicle_1`, `vehicle_2`, `vehicle_1_and_vehicle_2` not all uppercase.

**Solution Steps:**
1. Iterate through the columns and apply `str.upper().where(df[col].notna(), None)`.

**Prompt Blueprint:**
```python
# Vehicle Fields Uppercasing
for col in ['vehicle_1', 'vehicle_2', 'vehicle_1_and_vehicle_2']:
    if col in df.columns:
        df[col] = df[col].str.upper().where(df[col].notna(), None)
```

**Examples:**
| Before | After |
|--------|-------|
| "nj-abc123" | "NJ-ABC123" |
| "pa-xyz789" | "PA-XYZ789" |
| None | None |

---

## 9. Narrative Cleaning

**Problem:** Line breaks and extra tokens remain in `narrative`.

**Solution Steps:**
1. Implement `clean_narrative(text:str)` to remove `#(cr)#(lf)|#(lf)|#(cr)|[\r\n\t]+` and normalize spaces, then title-case.

**Prompt Blueprint:**
```python
def clean_narrative(text: str) -> str:
    if pd.isna(text):
        return None
    s = re.sub(r'#\(cr\)#\(lf\)|#\(lf\)|#\(cr\)|[\r\n\t]+', ' ', text)
    s = re.sub(r'\s+', ' ', s).strip()
    return s.title() if s else None

df['narrative'] = df['narrative_raw'].apply(clean_narrative)
```

**Examples:**
| Before | After |
|--------|-------|
| "Vehicle broken into#(cr)#(lf)Property stolen" | "Vehicle Broken Into Property Stolen" |
| "Physical altercation reported" | "Physical Altercation Reported" |

---

## 10. Period, Day_of_Week & Cycle_Name Fixes

**Problem:** `period` shows `season`; `day_of_week` wrong dtype; `cycle_name` off when date blank.

**Solution Steps:**
1. Ensure `incident_date` is datetime using `pd.to_datetime(errors='coerce')`.
2. Apply `get_period` and `get_season` to `incident_date`.
3. Calculate `day_of_week` using `dt.day_name()` and `day_type` based on weekend/weekday.
4. Calculate `cycle_name` using `incident_date` and `base_date`.

**Prompt Blueprint:**
```python
# Ensure incident_date is datetime
df['incident_date'] = pd.to_datetime(df['incident_date'], errors='coerce')

# Period and Season
df['period'] = df['incident_date'].apply(get_period)
df['season'] = df['incident_date'].apply(get_season)

# Day of Week & Type
df['day_of_week'] = df['incident_date'].dt.day_name()
df['day_type'] = df['day_of_week'].isin(['Saturday', 'Sunday']).map({True: 'Weekend', False: 'Weekday'})

# Cycle Name
df['cycle_name'] = df['incident_date'].apply(lambda x: get_cycle_for_date(x, cycle_calendar) if pd.notna(x) else None)
```

**Examples:**
| Incident Date | Period | Season | Day of Week | Day Type | Cycle Name |
|---------------|--------|--------|-------------|----------|------------|
| 2025-08-01 | "7-Day" | "Summer" | "Friday" | "Weekday" | "C08W31" |
| 2025-08-02 | "7-Day" | "Summer" | "Saturday" | "Weekend" | "C08W31" |

---

## 11. Merge Logic: Deduplicate and Reapply Cleaning

**Problem:** Merged output still carries duplicates and stale values.

**Solution Steps:**
1. After merge with suffixes (`_cad`, `_rms`), coalesce `incident_date` and `incident_time` using `fillna`.
2. Reapply `map_tod` to `incident_time`.
3. Coalesce `response_type` and `category_type` using `fillna`.
4. Drop all columns ending with `_cad` or `_rms`.

**Prompt Blueprint:**
```python
# Coalesce incident_date and incident_time
if 'incident_date_cad' in df.columns and 'incident_date_rms' in df.columns:
    df['incident_date'] = df['incident_date_cad'].fillna(df['incident_date_rms'])

if 'incident_time_cad' in df.columns and 'incident_time_rms' in df.columns:
    df['incident_time'] = df['incident_time_cad'].fillna(df['incident_time_rms'])

# Reapply key fixes
df['time_of_day'] = df['incident_time'].apply(map_tod)

# Coalesce response_type and category_type
if 'response_type_cad' in df.columns and 'response_type_rms' in df.columns:
    df['response_type'] = df['response_type_cad'].fillna(df['response_type_rms'])

# Drop suffix columns
drop_cols = [c for c in df.columns if c.endswith('_cad') or c.endswith('_rms')]
df = df.drop(columns=drop_cols)
```

**Examples:**
| CAD Date | RMS Date | Result |
|----------|----------|--------|
| 2025-08-01 | None | 2025-08-01 |
| None | 2025-08-01 | 2025-08-01 |
| 2025-08-01 | 2025-08-02 | 2025-08-01 (CAD priority) |

---

## 12. Data-Type Standardization for CSV Exports

**Problem:** Exported CSVs have inconsistent dtypes (all-NaN string columns → float64, mixed numerics, etc.).

**Solution Steps:**
1. Implement `standardize_data_types(df)` to:
   - Force object dtype on all designated string cols and map NaN→None.
   - Coerce numeric cols with `pd.to_numeric(errors="coerce")`.
2. Invoke immediately before **every** `.to_csv()` call.

**Prompt Blueprint:**
```python
def standardize_data_types(df: pd.DataFrame) -> pd.DataFrame:
    # Force object dtype for string cols, convert empties to None
    string_cols = ['case_number','incident_date','incident_time','all_incidents',
                   'vehicle_1','vehicle_2','vehicle_1_and_vehicle_2','narrative',
                   'location','block','response_type','category_type','period',
                   'season','day_of_week','day_type','cycle_name']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype('object').apply(lambda x: str(x) if pd.notna(x) else None)

    # Coerce numeric cols
    numeric_cols = ['post','grid','time_of_day_sort_order','total_value_stolen','total_value_recovered']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

# Apply before export:
df = standardize_data_types(df)
df.to_csv(path, index=False, encoding='utf-8')
```

**Examples:**
| Column | Before | After |
|--------|--------|-------|
| all_nan_str | float64 ([NaN,NaN]) | object ([None,None]) |
| mixed_numeric | object/int/float/null | float64 ([1.0,2.5,NaN, …]) |

---

## 13. Header Validation

**Problem:** Headers must follow lowercase_snake_case for Power BI.

**Solution Steps:**
1. Implement `validate_lowercase_snake_case_headers(df, context)` to:
   - Check each col against `^[a-z][a-z0-9_]*$`.
   - Return pass/fail and list of bad columns.
2. Invoke right before final export and error out if FAIL.

**Prompt Blueprint:**
```python
def validate_lowercase_snake_case_headers(df, name):
    # Loop cols, test regex, collect invalids
    lowercase_pattern = re.compile(r'^[a-z]+(_[a-z0-9]+)*$')
    non_compliant_cols = [col for col in df.columns if not lowercase_pattern.match(col)]
    
    return {
        'overall_status': 'PASS' if not non_compliant_cols else 'FAIL',
        'non_compliant_columns': non_compliant_cols
    }

# In pipeline:
hdr_val = validate_lowercase_snake_case_headers(rms_df, "RMS")
if hdr_val['overall_status']=='FAIL':
    raise ValueError(f"Non-compliant columns: {hdr_val['non_compliant_columns']}")
```

**Examples:**
| Column | Compliant | Issue |
|--------|-----------|-------|
| incident_date | ✅ | — |
| IncidentDate | ❌ | Should be: incident_date |
| case_number | ✅ | — |
| CaseNumber | ❌ | Should be: case_number |

---

## 14. Cycle-Calendar Integration

**Problem:** Need to tag records with the correct SCRPA cycle (e.g. "C08W31") for reporting.

**Solution Steps:**
1. Load cycle calendar Excel with start/end dates + report names.
2. Implement `get_cycle_for_date(date, cycle_df)` to find matching `Report_Name`.
3. Compute `cycle_name` in both RMS and CAD pipelines.
4. Use `current_cycle` + `current_date` in export filenames.

**Prompt Blueprint:**
```python
# Load cycle calendar
cycle_df = pd.read_excel(cycle_path)

def get_cycle_for_date(d, cycle_df):
    # Find cycle where date falls between start and end dates
    # Return Report_Name for matching cycle
    return cycle_name

# Apply to incident_date
df['cycle_name'] = df['incident_date'].apply(lambda d: get_cycle_for_date(d, cycle_df))

# Use in filenames
current_cycle, current_date = get_current_cycle_info(cycle_df)
outfile = f"{current_cycle}_{current_date}_rms_data.csv"
```

**Examples:**
| incident_date | cycle_name |
|---------------|------------|
| 2025-08-01 | C08W31 |
| 2025-06-15 | C07W26 |
| 2025-07-20 | C08W30 |

---

## 15. Enhanced SCRPA v4 Pipeline with Validation Checks and Structured Logging

**Problem:** Pipeline lacks validation checks and structured logging for quality assurance.

**Solution Steps:**
1. Add `validate_pipeline_results()` method to return pass/fail status for each major stage.
2. Add `log_processing_summary()` method for structured logging.
3. Invoke these at key points after each major stage.

**Prompt Blueprint:**
```python
def validate_pipeline_results(self):
    """Return pass/fail status for each major stage."""
    return {
        'rms_data_loaded': len(getattr(self, 'rms_data', [])) > 0,
        'rms_data_retained': len(getattr(self, 'rms_final', [])) > 0,
        'cad_data_processed': len(getattr(self, 'cad_data', [])) > 0,
        'matching_successful': hasattr(self, 'matched_data') and len(self.matched_data) > 0,
        'seven_day_export_generated': hasattr(self, '_seven_day_export_path') and Path(self._seven_day_export_path).exists(),
        'period_distribution_valid': set(getattr(self, 'matched_data', pd.DataFrame())['period']) >= {'7-Day','28-Day','YTD'}
    }

def log_processing_summary(self, rms_count, cad_count, matched_count, export_files):
    """Log a structured summary of pipeline results and generated files."""
    self.logger.info("="*50)
    self.logger.info("SCRPA v4 PIPELINE PROCESSING SUMMARY")
    self.logger.info("="*50)
    self.logger.info(f"RMS records loaded:     {rms_count}")
    self.logger.info(f"RMS records retained:   {rms_count}")
    self.logger.info(f"CAD records processed:  {cad_count}")
    self.logger.info(f"Matched records:        {matched_count}")
    self.logger.info("Exports generated:")
    for f in export_files:
        self.logger.info(f"  • {Path(f).name}")
    self.logger.info("="*50)
```

**Examples:**
```
Validation Results:
  rms_data_loaded: ✅ PASS
  rms_data_retained: ✅ PASS
  cad_data_processed: ✅ PASS
  matching_successful: ✅ PASS
  seven_day_export_generated: ❌ FAIL
  period_distribution_valid: ❌ FAIL

SCRPA v4 PIPELINE PROCESSING SUMMARY
==================================================
RMS records loaded:     5
RMS records retained:   5
CAD records processed:  5
Matched records:        5
Exports generated:
  • C08W31_20250804_015846_rms_data_final.csv
  • C08W31_20250804_015846_cad_data_final.csv
  • C08W31_20250804_015846_cad_rms_matched_final.csv
==================================================
```

---

## Implementation Notes

### File Structure
- **Main Pipeline**: `Comprehensive_SCRPA_Fix_v8.5_Standardized.py`
- **Production Pipeline**: `SCRPA_Time_v4_Production_Pipeline.py`
- **Test Files**: Various test scripts for each feature
- **Documentation**: Implementation guides for each feature

### Key Dependencies
- **pandas**: DataFrame manipulation and data processing
- **numpy**: Numerical operations
- **re**: Regular expressions for text processing
- **pathlib**: File path handling
- **logging**: Structured logging and validation reporting

### Best Practices
1. **Test-Driven Development**: Each feature includes comprehensive test scripts
2. **Error Handling**: Robust error handling with detailed logging
3. **Data Validation**: Multiple validation layers throughout the pipeline
4. **Documentation**: Complete documentation for each feature
5. **Modular Design**: Each feature is implemented as a separate, testable method

### Integration Points
- All features are integrated into the main pipeline classes
- Validation checks are performed at key stages
- Structured logging provides clear audit trails
- Data type standardization ensures consistent exports
- Header validation maintains Power BI compatibility

This comprehensive prompt deck covers all features currently implemented in the SCRPA pipeline, providing clear blueprints for implementation, testing, and validation. 