# Time-of-Day Buckets & Sort Order, Block Calculation & Enhancement, and Combine all_incidents from Incident_Type Columns

## Overview

This document describes the implementation of three new features in the Comprehensive SCRPA Fix V8.5 system:

1. **Time-of-Day Buckets & Sort Order**: Implements ordered categorical time-of-day buckets with sort order
2. **Block Calculation & Enhancement**: Standardizes block calculation for addresses and intersections
3. **Combine `all_incidents` from Incident_Type Columns**: Combines multiple incident type columns with statute code removal

## 1. Time-of-Day Buckets & Sort Order

### Problem
`time_of_day` was duplicated or unsorted alphabetically, making it difficult to analyze temporal patterns.

### Solution
1. Define `map_tod(t)` buckets
2. Apply to cleaned `incident_time`
3. Convert to ordered categorical and generate `time_of_day_sort_order`

### Implementation

#### New Method: `map_tod(t)`
```python
def map_tod(self, t):
    """
    Map time to time-of-day buckets.
    
    Args:
        t: Time value (string HH:MM:SS or time object)
        
    Returns:
        str: Time-of-day bucket description
    """
    if pd.isna(t) or not t:
        return "Unknown"
    
    try:
        # Parse time string (HH:MM:SS format)
        if isinstance(t, str):
            # Extract hour from HH:MM:SS format
            hour = int(t.split(':')[0])
        else:
            # Fallback for time objects
            hour = t.hour if hasattr(t, 'hour') else 0
        
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
```

#### Updated `process_rms_data` Method
```python
# Time-of-Day Buckets & Sort Order implementation
# Define time-of-day buckets in order
tod_order = [
    "00:00-03:59 Early Morning",
    "04:00-07:59 Morning", 
    "08:00-11:59 Morning Peak",
    "12:00-15:59 Afternoon",
    "16:00-19:59 Evening Peak",
    "20:00-23:59 Night",
    "Unknown"
]

# Apply map_tod function to cleaned incident_time
rms_df['time_of_day'] = rms_df['incident_time'].apply(self.map_tod)

# Convert to ordered categorical and generate sort order
rms_df['time_of_day'] = pd.Categorical(
    rms_df['time_of_day'], 
    categories=tod_order, 
    ordered=True
)
rms_df['time_of_day_sort_order'] = rms_df['time_of_day'].cat.codes + 1
```

### Examples

| incident_time | time_of_day | sort_order |
| -------------- | --------------------------- | ----------- |
| 02:30:00 | "00:00–03:59 Early Morning" | 1 |
| 07:15:00 | "04:00–07:59 Morning" | 2 |
| 14:45:00 | "12:00–15:59 Afternoon" | 4 |

## 2. Block Calculation & Enhancement

### Problem
Inconsistent block formatting between CAD ("FullAddress2") and RMS ("location") columns.

### Solution
1. Standardize input column to `location`
2. Implement `calculate_block(addr)` handling intersections and numeric addresses

### Implementation

#### Enhanced `calculate_block` Method
```python
def calculate_block(self, address):
    """Block calculation matching M Code exactly."""
    if pd.isna(address):
        return "Check Location Data"
    
    # Clean address
    addr = str(address).replace(", Hackensack, NJ, 07601", "")
    
    # Handle intersections
    if " & " in addr:
        parts = addr.split(" & ")
        if len(parts) == 2 and all(p.strip() for p in parts):
            # For intersections, extract just the street names (remove house numbers)
            street1 = parts[0].strip()
            street2 = parts[1].strip()
            
            # Remove house numbers from street names (only if they start with digits)
            def clean_street_name(street):
                words = street.split()
                if words and words[0].isdigit():
                    return ' '.join(words[1:])
                return street
            
            street1_clean = clean_street_name(street1)
            street2_clean = clean_street_name(street2)
            
            return f"{street1_clean} & {street2_clean}"
        else:
            return "Incomplete Address - Check Location Data"
    else:
        # Handle regular addresses
        try:
            parts = addr.split(" ", 1)
            if len(parts) >= 2:
                street_num = int(parts[0])
                street_name = parts[1].split(",")[0].strip()
                block_num = (street_num // 100) * 100
                return f"{street_name}, {block_num} Block"
            else:
                return "Check Location Data"
        except:
            return "Check Location Data"
```

### Examples

| location | block |
| ---------------------------------- | --------------------- |
| "123 Main St, Hackensack, NJ, ..." | "Main St, 100 Block" |
| "Broad St & Elm St" | "Broad St & Elm St" |
| "789 Pine St & Maple Ave" | "Pine St & Maple Ave" |
| "Xyz Rd" | "Check Location Data" |

## 3. Combine `all_incidents` from Incident_Type Columns

### Problem
`all_incidents` was empty because using wrong column names.

### Solution
1. Use cleaned columns: `incident_type_1_cleaned`, etc.
2. Strip statute codes and join non-null entries

### Implementation

#### Enhanced `clean_incident_type` Method
```python
def clean_incident_type(self, incident_str):
    """Clean incident type by removing statute codes."""
    if pd.isna(incident_str) or incident_str == "":
        return None
    # Remove statute codes
    if " - 2C" in incident_str:
        return incident_str.split(" - 2C")[0]
    return incident_str
```

#### Updated `process_rms_data` Method
```python
# Clean and combine incident types - safe column access
for i in [1, 2, 3]:
    col_name = f'incident_type_{i}_raw'
    if col_name in rms_df.columns:
        rms_df[f'incident_type_{i}_cleaned'] = rms_df[col_name].apply(self.clean_incident_type)

# Use incident_type_1_raw as primary incident type (no unpivoting)
# This prevents the 135→300 record expansion issue
if 'incident_type_1_raw' in rms_df.columns:
    rms_df['incident_type'] = rms_df['incident_type_1_raw'].apply(self.clean_incident_type)
else:
    rms_df['incident_type'] = None

# Combine all incidents for reference only
def combine_incidents(row):
    incidents = []
    for i in [1, 2, 3]:
        cleaned_col = f'incident_type_{i}_cleaned'
        if cleaned_col in row and pd.notna(row[cleaned_col]):
            incidents.append(row[cleaned_col])
    return ", ".join(incidents) if incidents else None

rms_df['all_incidents'] = rms_df.apply(combine_incidents, axis=1)
```

### Examples

| incident_type_1_cleaned | incident_type_2_cleaned | incident_type_3_cleaned | all_incidents |
| -------------------------- | -------------------------- | -------------------------- | ----------------- |
| "Burglary - Auto" | NaN | NaN | "Burglary - Auto" |
| "Theft" | "Robbery" | NaN | "Theft, Robbery" |
| NaN | NaN | NaN | "" (empty) |

## Integration

All three features are integrated into the `process_rms_data` method and work together seamlessly:

1. **Time-of-Day**: Applied to `incident_time` after cascade logic
2. **Block Calculation**: Applied to `location` after address validation
3. **All Incidents**: Applied to cleaned incident type columns

## Testing

A comprehensive test script `test_time_of_day_and_block_features.py` validates all three features:

- **Time-of-Day Buckets**: Tests all time ranges and ordered categorical functionality
- **Block Calculation**: Tests numeric addresses, intersections, and edge cases
- **All Incidents**: Tests statute code removal and multi-column combination

### Test Results
All tests pass with the following validation:
- ✅ Time-of-day mapping works correctly for all time ranges
- ✅ Ordered categorical data generates proper sort order (1-7)
- ✅ Block calculation handles intersections and numeric addresses
- ✅ Incident type cleaning removes statute codes properly
- ✅ Multi-column combination joins non-null entries correctly

## Benefits

1. **Time-of-Day Analysis**: Enables proper temporal analysis with consistent ordering
2. **Geographic Analysis**: Provides standardized block-level geographic analysis
3. **Incident Analysis**: Combines multiple incident types for comprehensive crime analysis
4. **Data Quality**: Improves data consistency and reduces manual data cleaning

## Files Modified

- `Comprehensive_SCRPA_Fix_v8.5_Standardized.py`: Main implementation
- `test_time_of_day_and_block_features.py`: Comprehensive test suite

## Dependencies

- pandas (for DataFrame operations and Categorical data)
- datetime (for time parsing)
- re (for string manipulation)

## Future Enhancements

1. **Time-of-Day**: Add custom time bucket definitions
2. **Block Calculation**: Add support for more address formats
3. **All Incidents**: Add support for more incident type columns 