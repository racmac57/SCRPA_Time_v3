# // 2025-08-05-17-45-00
# SCRPA_Time_v2/period_time_fixes.py
# Author: R. A. Carucci
# Purpose: Critical fixes for period calculation and incident_time processing in Comprehensive_SCRPA_Fix_v8.5_Standardized.py

# ============================================================================
# FIX 1: Update get_period() to Use Cycle Calendar Logic
# ============================================================================

def get_period(self, date_val):
    """
    Fixed period calculation using actual cycle calendar dates.
    Uses 7-day cycle: 07/29/25 - 08/04/25 for current period.
    """
    if pd.isna(date_val) or date_val is None:
        return "Historical"
    
    # Convert date_val to date object if needed
    try:
        if hasattr(date_val, 'date'):
            date_val = date_val.date()
        elif isinstance(date_val, str):
            # Handle both mm/dd/yy and ISO formats
            for fmt in ['%m/%d/%y', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    date_val = pd.to_datetime(date_val, format=fmt).date()
                    break
                except:
                    continue
        elif not hasattr(date_val, 'year'):
            return "Historical"
    except:
        self.logger.warning(f"Could not parse date: {date_val}")
        return "Historical"
    
    # Define current cycle periods (from cycle calendar)
    # C08W31: Report Due 08/05/25
    seven_day_start = pd.to_datetime('2025-07-29').date()
    seven_day_end = pd.to_datetime('2025-08-04').date()
    twenty_eight_day_start = pd.to_datetime('2025-07-08').date()
    twenty_eight_day_end = pd.to_datetime('2025-08-04').date()
    
    # YTD is current year
    current_year = 2025
    
    # Period assignment based on cycle calendar
    if seven_day_start <= date_val <= seven_day_end:
        return "7-Day"
    elif twenty_eight_day_start <= date_val <= twenty_eight_day_end:
        return "28-Day"
    elif date_val.year == current_year:
        return "YTD"
    else:
        return "Historical"

# ============================================================================
# FIX 2: Enhanced Time Processing for Excel 1899 Format
# ============================================================================

def process_rms_time_columns(self, rms_df):
    """
    Fixed time processing to handle Excel's 1899 date format.
    """
    self.logger.info("Processing RMS time columns with Excel format handling...")
    
    # Time column mapping
    time_columns = {
        'incident_time': 'Incident Time',
        'incident_time_between': 'Incident Time_Between', 
        'report_time': 'Report Time'
    }
    
    # Process each time column
    for new_col, old_col in time_columns.items():
        if old_col in rms_df.columns:
            # Parse times, handling Excel 1899 format
            time_series = pd.to_datetime(rms_df[old_col], errors='coerce')
            
            # Extract just the time component
            if time_series.notna().any():
                # If it's a datetime with 1899 date, extract time only
                rms_df[new_col] = time_series.dt.strftime('%H:%M:%S')
            else:
                rms_df[new_col] = None
                
            self.logger.info(f"{new_col}: {rms_df[new_col].notna().sum()}/{len(rms_df)} populated")
    
    # Apply cascade logic for incident_time
    t1 = rms_df['incident_time']
    t2 = rms_df['incident_time_between'] 
    t3 = rms_df['report_time']
    
    # Cascade: Use first non-null value
    rms_df['incident_time'] = t1.fillna(t2).fillna(t3)
    
    self.logger.info(f"Final incident_time: {rms_df['incident_time'].notna().sum()}/{len(rms_df)} populated")
    
    return rms_df

# ============================================================================
# FIX 3: Update RMS Filtering Logic with Better Diagnostics
# ============================================================================

def apply_rms_filtering(self, rms_df):
    """
    Enhanced filtering with detailed diagnostics.
    """
    initial_count = len(rms_df)
    self.logger.info(f"RMS filtering - Starting with {initial_count} records")
    
    # Log period distribution BEFORE filtering
    if 'period' in rms_df.columns:
        period_counts = rms_df['period'].value_counts()
        self.logger.info(f"Period distribution before filtering:")
        for period, count in period_counts.items():
            self.logger.info(f"  - {period}: {count} records")
    
    # Apply filters separately to diagnose issues
    filters_applied = []
    
    # Filter 1: Remove specific case number
    if 'case_number' in rms_df.columns:
        before = len(rms_df)
        rms_df = rms_df[rms_df['case_number'] != '25-057654']
        after = len(rms_df)
        self.logger.info(f"Case filter removed {before - after} records")
        filters_applied.append(f"case≠25-057654")
    
    # Filter 2: Keep non-Historical records (modified logic)
    if 'period' in rms_df.columns:
        before = len(rms_df)
        # Keep 7-Day, 28-Day, and YTD records
        keep_periods = ['7-Day', '28-Day', 'YTD']
        rms_df = rms_df[rms_df['period'].isin(keep_periods)]
        after = len(rms_df)
        self.logger.info(f"Period filter removed {before - after} Historical records")
        filters_applied.append(f"period in {keep_periods}")
    
    # Final summary
    self.logger.info(f"RMS filtering complete: {initial_count} → {len(rms_df)} records")
    self.logger.info(f"Filters applied: {', '.join(filters_applied)}")
    
    # Log final period distribution
    if 'period' in rms_df.columns and len(rms_df) > 0:
        final_periods = rms_df['period'].value_counts()
        self.logger.info("Final period distribution:")
        for period, count in final_periods.items():
            self.logger.info(f"  - {period}: {count} records")
    
    return rms_df

# ============================================================================
# FIX 4: Date Cascade Enhancement
# ============================================================================

def cascade_date(self, rms_df):
    """
    Enhanced date cascading with better format handling.
    """
    self.logger.info("Cascading RMS date columns...")
    
    # Date columns to cascade
    date_cols = ['Incident Date', 'Incident Date_Between', 'Report Date']
    
    # Parse each date column with multiple format attempts
    parsed_dates = []
    for col in date_cols:
        if col in rms_df.columns:
            # Try multiple date formats
            formats = ['%m/%d/%y', '%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']
            date_series = None
            
            for fmt in formats:
                try:
                    date_series = pd.to_datetime(rms_df[col], format=fmt, errors='coerce')
                    valid_count = date_series.notna().sum()
                    if valid_count > 0:
                        self.logger.info(f"{col}: Parsed {valid_count} dates with format {fmt}")
                        break
                except:
                    continue
            
            if date_series is None:
                # Fallback to pandas auto-detection
                date_series = pd.to_datetime(rms_df[col], errors='coerce')
            
            parsed_dates.append(date_series)
        else:
            parsed_dates.append(pd.Series([pd.NaT] * len(rms_df)))
    
    # Cascade: Use first non-null date
    rms_df['incident_date'] = parsed_dates[0].fillna(parsed_dates[1]).fillna(parsed_dates[2])
    
    # Format as MM/DD/YY string for consistency
    rms_df['incident_date'] = rms_df['incident_date'].dt.strftime('%m/%d/%y')
    
    populated = rms_df['incident_date'].notna().sum()
    self.logger.info(f"incident_date populated: {populated}/{len(rms_df)}")
    
    if populated > 0:
        # Sample date check
        sample_dates = rms_df['incident_date'].dropna().head(5).tolist()
        self.logger.info(f"Sample dates: {sample_dates}")
        
        # Check for 7-day period dates
        seven_day_dates = rms_df[
            rms_df['incident_date'].str.contains('07/29/25|07/30/25|07/31/25|08/01/25|08/02/25|08/03/25|08/04/25', na=False)
        ]
        self.logger.info(f"Dates in 7-day period (07/29-08/04): {len(seven_day_dates)} records")
    
    return rms_df

# ============================================================================
# INTEGRATION INSTRUCTIONS
# ============================================================================

"""
To integrate these fixes into Comprehensive_SCRPA_Fix_v8.5_Standardized.py:

1. Replace the get_period() method with FIX 1
2. Add process_rms_time_columns() method (FIX 2) and call it in process_rms_data()
3. Replace filtering logic in process_rms_data() with FIX 3
4. Replace cascade_date() method with FIX 4

Key Changes:
- Period calculation now uses actual cycle calendar dates
- Time processing handles Excel 1899 format properly
- Filtering keeps 7-Day, 28-Day, and YTD records
- Enhanced diagnostics throughout

Expected Results:
- 2 incidents on 07/31/25 will be marked as "7-Day"
- Times will parse correctly from Excel format
- RMS records will not be filtered out
- 7-Day SCRPA export will generate successfully
"""