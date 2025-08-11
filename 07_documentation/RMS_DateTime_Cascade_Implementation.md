# RMS Date/Time Cascade Logic - Implementation Guide

## Problem Statement

Missing `incident_date` and `incident_time` if both primary and fallback are null; time parsing glitch formats `19:00:00` as `1900:00:00`.

## Solution Overview

The solution implements enhanced cascading logic that:

1. **Parses each field separately** with `errors='coerce'`
2. **Chain-fills dates**: `Date` → `Date_Between` → `Report Date`
3. **Chain-fills times**: `Time` → `Time_Between` → `Report Time`
4. **Formats time via `strftime`** to avoid Excel fallback artifacts

## Implementation Details

### 1. Enhanced Date Cascade Function

**File**: `Comprehensive_SCRPA_Fix_v8.5_Standardized.py`  
**Method**: `cascade_date()`  
**Lines**: 796-820

```python
def cascade_date(self, row):
    """
    Enhanced cascading date logic according to specification.
    
    Chain-fill: date = Date → Date_Between → Report Date
    Parse each field separately with errors='coerce'
    """
    # Define the date cascade chain in priority order
    date_columns = [
        'Incident Date',           # Primary date field
        'Incident Date_Between',   # Fallback date field
        'Report Date'              # Final fallback
    ]
    
    # Try each column in the cascade chain
    for col in date_columns:
        if col in row.index and pd.notna(row.get(col)):
            try:
                # Parse each field separately with errors='coerce'
                result = pd.to_datetime(row[col], errors='coerce')
                if pd.notna(result):
                    return result.date()
            except Exception as e:
                self.logger.debug(f"Error parsing date from {col}: {e}")
                continue
    
    return None
```

**What this does**:
- **Priority Chain**: Tries `Incident Date` first, then `Incident Date_Between`, then `Report Date`
- **Error Handling**: Uses `errors='coerce'` to handle invalid dates gracefully
- **Robust Parsing**: Handles various date formats and edge cases

### 2. Enhanced Time Cascade Function

**File**: `Comprehensive_SCRPA_Fix_v8.5_Standardized.py`  
**Method**: `cascade_time()`  
**Lines**: 834-880

```python
def cascade_time(self, row):
    """
    Enhanced cascading time logic according to specification.
    
    Chain-fill: time = Time → Time_Between → Report Time
    Parse each field separately with errors='coerce'
    Format time via strftime to avoid Excel fallback artifact
    """
    # Define the time cascade chain in priority order
    time_columns = [
        'Incident Time',           # Primary time field
        'Incident Time_Between',   # Fallback time field
        'Report Time'              # Final fallback
    ]
    
    # Try each column in the cascade chain
    for col in time_columns:
        if col in row.index and pd.notna(row.get(col)):
            try:
                time_value = row[col]
                
                # Handle Excel Timedelta objects (common Excel time format)
                if isinstance(time_value, pd.Timedelta):
                    total_seconds = time_value.total_seconds()
                    hours = int(total_seconds // 3600) % 24  # Handle 24+ hour overflow
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = int(total_seconds % 60)
                    
                    from datetime import time
                    time_obj = time(hours, minutes, seconds)
                    # Format via strftime to avoid Excel fallback artifact
                    return time_obj.strftime("%H:%M:%S")
                
                # Handle other time formats
                else:
                    # Parse each field separately with errors='coerce'
                    parsed_time = pd.to_datetime(time_value, errors='coerce')
                    if pd.notna(parsed_time):
                        # Format via strftime to avoid Excel fallback artifact
                        return parsed_time.strftime("%H:%M:%S")
                        
            except Exception as e:
                self.logger.debug(f"Error parsing time from {col}: {e}")
                continue
    
    return None
```

**What this does**:
- **Priority Chain**: Tries `Incident Time` first, then `Incident Time_Between`, then `Report Time`
- **Excel Timedelta Handling**: Properly converts Excel's timedelta format to time
- **String Formatting**: Uses `strftime("%H:%M:%S")` to avoid Excel fallback artifacts
- **Error Handling**: Gracefully handles parsing errors

### 3. Application in RMS Data Processing

**File**: `Comprehensive_SCRPA_Fix_v8.5_Standardized.py`  
**Method**: `process_rms_data()`  
**Lines**: 1227-1240

```python
# Enhanced cascading date and time logic according to specification
# Date cascade: Date → Date_Between → Report Date
rms_df['incident_date'] = rms_df.apply(self.cascade_date, axis=1)

# DEBUG: Check incident_date population after cascading
date_populated = rms_df['incident_date'].notna().sum()
self.logger.info(f"Incident dates after cascading: {date_populated}/{len(rms_df)}")
if date_populated > 0:
    sample_cascaded_dates = rms_df['incident_date'].dropna().head(5).tolist()
    self.logger.info(f"Sample cascaded dates: {sample_cascaded_dates}")
else:
    self.logger.error("NO INCIDENT DATES POPULATED AFTER CASCADING - This will cause all records to be marked as 'Historical'")

# Time cascade: Time → Time_Between → Report Time
# Format time via strftime to avoid Excel fallback artifact
rms_df['incident_time'] = rms_df.apply(self.cascade_time, axis=1)
```

**What this does**:
- **Direct Application**: Applies cascade functions directly to create final columns
- **Comprehensive Logging**: Provides detailed logging for debugging and monitoring
- **Error Detection**: Identifies when no dates are populated (critical for period classification)

### 4. Enhanced Time of Day Calculation

**File**: `Comprehensive_SCRPA_Fix_v8.5_Standardized.py`  
**Method**: `process_rms_data()` (local function)  
**Lines**: 1241-1265

```python
def safe_get_time_of_day(time_val):
    if pd.isna(time_val) or not time_val:
        return "Unknown"
    try:
        # Parse time string (HH:MM:SS format)
        if isinstance(time_val, str):
            # Extract hour from HH:MM:SS format
            hour = int(time_val.split(':')[0])
        else:
            # Fallback for time objects
            hour = time_val.hour if hasattr(time_val, 'hour') else 0
        
        if 0 <= hour < 4:
            return "00:00-03:59 Early Morning"
        elif 4 <= hour < 8:
            return "04:00-07:59 Morning"
        elif 8 <= hour < 12:
            return "08:00-11:59 Morning Peak"
        elif 12 <= hour < 16:
            return "12:00-15:59 Afternoon"
        elif 16 <= hour < 20:
            return "16:00-19:59 Evening Peak"
        else:
            return "20:00-23:59 Night"
    except:
        return "Unknown"

rms_df['time_of_day'] = rms_df['incident_time'].apply(safe_get_time_of_day)
```

**What this does**:
- **String Time Handling**: Properly parses time strings in HH:MM:SS format
- **Hour Extraction**: Extracts hour component for time-of-day classification
- **Fallback Support**: Maintains compatibility with time objects
- **Error Handling**: Returns "Unknown" for invalid times

## Test Results

The implementation has been tested with the following scenarios:

### Date Cascade Test Results

| Incident Date | Incident Date_Between | Report Date | incident_date | Status |
| ------------- | ---------------------- | ----------- | -------------- | ------ |
| 2025-05-11    | NaT                    | 2025-05-11  | 2025-05-11     | ✅ PASS |
| NaT           | 2025-04-13             | 2025-04-13  | 2025-04-13     | ✅ PASS |
| NaT           | NaT                    | 2025-03-18  | 2025-03-18     | ✅ PASS |
| NaT           | NaT                    | NaT         | None           | ✅ PASS |

### Time Cascade Test Results

| Incident Time | Incident Time_Between | Report Time | incident_time | Status |
| ------------- | ---------------------- | ----------- | -------------- | ------ |
| 19:00:00      | NaT                    | 19:00:00    | 19:00:00       | ✅ PASS |
| NaT           | 05:30:00               | 06:34:38    | 05:30:00       | ✅ PASS |
| NaT           | NaT                    | 09:39:40    | 09:39:40       | ✅ PASS |
| NaT           | NaT                    | NaT         | None           | ✅ PASS |

### Time of Day Classification Results

| incident_time | time_of_day              | Status |
| ------------- | ------------------------ | ------ |
| 19:00:00      | 16:00-19:59 Evening Peak | ✅ PASS |
| 05:30:00      | 04:00-07:59 Morning      | ✅ PASS |
| 09:39:40      | 08:00-11:59 Morning Peak | ✅ PASS |
| None          | Unknown                  | ✅ PASS |

## Key Features

### 1. Robust Cascade Logic

- **Priority-Based**: Tries primary fields first, falls back to secondary fields
- **Error-Resistant**: Uses `errors='coerce'` to handle invalid data gracefully
- **Comprehensive**: Covers all three fallback levels for both dates and times

### 2. Excel Compatibility

- **Timedelta Handling**: Properly converts Excel's timedelta format to time
- **String Formatting**: Uses `strftime` to avoid Excel fallback artifacts
- **Format Consistency**: Ensures consistent HH:MM:SS output format

### 3. Enhanced Error Handling

- **Graceful Degradation**: Continues processing even when individual fields fail
- **Comprehensive Logging**: Provides detailed logging for debugging
- **Null Safety**: Properly handles null/empty values throughout the chain

### 4. Time of Day Classification

- **String Parsing**: Correctly extracts hours from formatted time strings
- **Multiple Formats**: Supports both string and time object formats
- **Accurate Classification**: Provides precise time-of-day categorization

## Usage Instructions

### For New Data Processing

1. The cascade logic is automatically applied when processing RMS data
2. Final columns are created: `incident_date` and `incident_time`
3. Time of day classification is automatically calculated

### For Testing

Run the test script to verify functionality:

```bash
python test_rms_datetime_cascade.py
```

### For Manual Application

If you need to apply the cascade functions manually:

```python
from Comprehensive_SCRPA_Fix_v8_5_Standardized import ComprehensiveSCRPAFixV8_5

processor = ComprehensiveSCRPAFixV8_5()

# Create a mock row
row = pd.Series({
    'Incident Date': '2025-05-11',
    'Incident Date_Between': None,
    'Report Date': '2025-05-11'
})

# Apply cascade functions
date_result = processor.cascade_date(row)
time_result = processor.cascade_time(row)
```

## Technical Notes

### Date Cascade Priority

The date cascade follows this priority order:
1. **Incident Date** (primary field)
2. **Incident Date_Between** (fallback field)
3. **Report Date** (final fallback)

### Time Cascade Priority

The time cascade follows this priority order:
1. **Incident Time** (primary field)
2. **Incident Time_Between** (fallback field)
3. **Report Time** (final fallback)

### Excel Timedelta Handling

Excel often stores times as timedelta objects (fraction of a day). The implementation:
- Converts timedelta to total seconds
- Calculates hours, minutes, seconds
- Handles 24+ hour overflow correctly
- Formats as HH:MM:SS string

### String Formatting Benefits

Using `strftime("%H:%M:%S")` provides:
- **Consistency**: Always produces HH:MM:SS format
- **Excel Compatibility**: Avoids Excel's automatic time formatting
- **Readability**: Clear, standardized time representation
- **Database Compatibility**: Works well with database storage

## Integration with Existing Code

This implementation integrates seamlessly with the existing SCRPA processing pipeline:

1. **Column Mapping**: Works with existing RMS column mapping system
2. **Header Normalization**: Compatible with lowercase snake_case header normalization
3. **Data Processing**: Fits into existing RMS data processing workflow
4. **Logging**: Uses existing logging infrastructure
5. **Period Classification**: Provides accurate dates for period calculations

## Future Enhancements

Potential improvements for future versions:

1. **Additional Date Formats**: Support more date format variations
2. **Time Zone Handling**: Add time zone awareness and conversion
3. **Validation**: Add validation to ensure cascade worked as expected
4. **Configuration**: Make cascade priorities configurable
5. **Performance**: Optimize for large datasets

## Conclusion

The RMS Date/Time Cascade Logic implementation successfully addresses the missing date/time issue while providing robust, Excel-compatible processing. The solution maintains data integrity, provides consistent output, and integrates seamlessly with the existing SCRPA processing pipeline. 