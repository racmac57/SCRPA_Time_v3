# SCRPA Script Fix Instructions

## Problem Summary
The script has 3 critical issues causing data loss:
1. Period logic uses "days from today" instead of cycle calendar dates
2. Excel time format (1899 dates) not parsing correctly
3. All RMS records filtered out (136 → 0 records)

## Test Data
- RMS Export has 2 incidents on 07/31/25 that should be "7-Day" period
- Current cycle C08W31: 07/29/25 - 08/04/25 (Report due 08/05/25)
- Times stored as Excel 1899 format: "1899-12-30T20:35:00"

## Required Fixes

### Fix 1: Update get_period() Method
```python
def get_period(self, date_val):
    """Fixed period calculation using cycle calendar dates."""
    if pd.isna(date_val) or date_val is None:
        return "Historical"
    
    # Convert to date object
    try:
        if hasattr(date_val, 'date'):
            date_val = date_val.date()
        elif isinstance(date_val, str):
            for fmt in ['%m/%d/%y', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    date_val = pd.to_datetime(date_val, format=fmt).date()
                    break
                except:
                    continue
    except:
        return "Historical"
    
    # C08W31 cycle dates
    seven_day_start = pd.to_datetime('2025-07-29').date()
    seven_day_end = pd.to_datetime('2025-08-04').date()
    twenty_eight_day_start = pd.to_datetime('2025-07-08').date()
    twenty_eight_day_end = pd.to_datetime('2025-08-04').date()
    
    # Assign period based on cycle
    if seven_day_start <= date_val <= seven_day_end:
        return "7-Day"
    elif twenty_eight_day_start <= date_val <= twenty_eight_day_end:
        return "28-Day"
    elif date_val.year == 2025:
        return "YTD"
    else:
        return "Historical"
```

### Fix 2: Update Time Processing (in process_rms_data)
```python
# Fix for Excel 1899 time format
time_columns = ['incident_time', 'incident_time_between', 'report_time']
for col in time_columns:
    if col in rms_df.columns:
        # Parse and extract time only
        time_series = pd.to_datetime(rms_df[col], errors='coerce')
        if time_series.notna().any():
            rms_df[col] = time_series.dt.strftime('%H:%M:%S')
```

### Fix 3: Update Filtering Logic (in process_rms_data)
```python
# Change from filtering OUT Historical to keeping specific periods
if 'period' in rms_df.columns:
    # Log distribution before filtering
    period_counts = rms_df['period'].value_counts()
    self.logger.info(f"Period distribution: {period_counts.to_dict()}")
    
    # Keep these periods
    keep_periods = ['7-Day', '28-Day', 'YTD']
    rms_df = rms_df[rms_df['period'].isin(keep_periods)]
    
    self.logger.info(f"After filtering: {len(rms_df)} records kept")
```

## Expected Results After Fix
- 2 incidents on 07/31/25 marked as "7-Day"
- RMS records retained after filtering (not 0)
- Times properly formatted as HH:MM:SS
- 7-Day SCRPA export generated successfully

## Testing
Run script and verify:
1. Log shows "7-Day: 2 records" in period distribution
2. RMS output file has records (not empty)
3. 7-Day SCRPA export file created in 04_powerbi folder