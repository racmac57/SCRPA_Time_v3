# SCRPA Data Processing Script Assessment & Fixes

-----

## Assessment

The script's data enrichment process fails because it cannot correctly handle the different date and time structures from the separate **CAD** and **RMS** export files. This creates a logical break in the pipeline where a standardized datetime column is not created, causing downstream calculations for `TimeOfDay` and `Period` to fail and result in `null` values.

  * **RMS Data Failure**: The script correctly identifies the separate `Incident Date` and `Incident Time` columns from the RMS export but fails to properly combine them into a single, valid datetime object.
  * **CAD Data Failure**: The script correctly identifies the `Time of Call` column from the CAD export but does not successfully pass this data to the functions responsible for creating the enrichment columns.
  * **Log File Confirmation**: The script's log file explicitly confirms this issue, showing warnings that it "Could not find a valid date column" for both the RMS and CAD processing stages, which directly leads to the calculation failures.

-----

## Corrected Python Script

The solution is to replace the `_process_rms_export` and `_process_cad_export` functions in your `master_scrpa_processor.py` file. The corrected code below centralizes the date/time creation logic and resolves the parsing errors.

```python
def _process_rms_export(self, df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
    """
    Processes the raw RMS export DataFrame to standardize columns and create a reliable datetime column.
    This version fixes the date and time combination logic.
    """
    self.logger.info("Processing RMS data structure...")
    cleaned_df = pd.DataFrame()

    # --- FIX START: Correctly combine separate Date and Time columns ---
    date_col_name = column_map.get('incident_date')
    time_col_name = column_map.get('incident_time')

    if date_col_name and time_col_name:
        self.logger.info(f"Combining RMS date ('{date_col_name}') and time ('{time_col_name}') columns.")
        # Convert date and time columns to string to ensure consistent concatenation
        date_series = df[date_col_name].astype(str)
        time_series = df[time_col_name].astype(str)
        
        # Combine the string representations and then convert to datetime
        combined_datetime_str = date_series + " " + time_series
        cleaned_df['Incident_DateTime'] = pd.to_datetime(combined_datetime_str, errors='coerce')
        
        # Log how many dates failed to parse
        failed_parses = cleaned_df['Incident_DateTime'].isnull().sum()
        if failed_parses > 0:
            self.logger.warning(f"{failed_parses} RMS records had invalid date/time formats and could not be parsed.")
    else:
        self.logger.warning("RMS data is missing 'incident_date' or 'incident_time' columns. DateTime will be null.")
        cleaned_df['Incident_DateTime'] = pd.NaT
    # --- FIX END ---

    # Map other relevant columns
    for key, col_name in column_map.items():
        if col_name in df.columns and key not in ['incident_date', 'incident_time']:
            cleaned_df[key.capitalize()] = df[col_name]

    return cleaned_df

def _process_cad_export(self, df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
    """
    Processes the raw CAD export DataFrame to standardize columns and create a reliable datetime column.
    This version ensures the 'Time of Call' is correctly used.
    """
    self.logger.info("Processing CAD data structure...")
    cleaned_df = pd.DataFrame()

    # --- FIX START: Correctly parse the single datetime column from CAD ---
    call_time_col_name = column_map.get('call_time')
    if call_time_col_name:
        self.logger.info(f"Using CAD '{call_time_col_name}' for Incident DateTime.")
        cleaned_df['Incident_DateTime'] = pd.to_datetime(df[call_time_col_name], errors='coerce')
        
        # Log how many dates failed to parse
        failed_parses = cleaned_df['Incident_DateTime'].isnull().sum()
        if failed_parses > 0:
            self.logger.warning(f"{failed_parses} CAD records had invalid datetime formats and could not be parsed.")
    else:
        self.logger.warning("CAD data is missing 'call_time' column. DateTime will be null.")
        cleaned_df['Incident_DateTime'] = pd.NaT
    # --- FIX END ---
    
    # Map other relevant columns
    for key, col_name in column_map.items():
        if col_name in df.columns and key != 'call_time':
            cleaned_df[key.capitalize()] = df[col_name]
            
    return cleaned_df
```

-----

## Explanation of Fixes

  * **Standardized `Incident_DateTime` Column**: Both corrected functions now create a single, reliable column named `Incident_DateTime`. This provides a consistent source of truth for all downstream calculations like `TimeOfDay` and `Period`.
  * **Fix for RMS Data**: The `_process_rms_export` function now correctly combines the separate `Incident Date` and `Incident Time` columns by treating them as text first before converting them to a proper datetime format.
  * **Fix for CAD Data**: The `_process_cad_export` function now properly uses the `Time of Call` column to create the standardized `Incident_DateTime` column.
  * **Robust Error Handling**: The `errors='coerce'` command ensures that any date or time value that cannot be properly formatted will be set to `null` (`NaT`) instead of crashing the script. A warning is also logged to alert you to potential data quality issues.

-----

## Next Steps

1.  Open your `master_scrpa_processor.py` file.
2.  Locate the `_process_rms_export` and `_process_cad_export` functions.
3.  Replace them entirely with the corrected code provided above.
4.  Save the file and re-run the script.
5.  Verify that the output `enhanced_scrpa_data.csv` now contains the correct, calculated values for all enrichment columns.