# Header Validation and Cycle Calendar Integration Implementation

## Overview

This document describes the implementation of header validation and cycle calendar integration features in the SCRPA pipeline. These features ensure Power BI compatibility through proper column naming conventions and provide accurate cycle-based reporting through calendar integration.

## 1. Header Validation Implementation

### Problem Statement

Final CSV headers must conform to lowercase_snake_case (`^[a-z][a-z0-9_]*$`) for Power BI compliance. Non-compliant headers can cause import failures and data processing issues.

### Solution Implementation

#### 1.1 Header Validation Method

Implemented `validate_lowercase_snake_case_headers()` method in both pipeline classes:

```python
def validate_lowercase_snake_case_headers(self, df, data_type="Unknown"):
    """
    Validate that all column headers follow lowercase snake_case convention.
    
    Args:
        df: DataFrame to validate
        data_type: String identifier for the data type (for logging)
        
    Returns:
        dict: Validation results
    """
    validation_results = {
        'data_type': data_type,
        'total_columns': len(df.columns),
        'compliant_columns': 0,
        'non_compliant_columns': [],
        'overall_status': 'PASS'
    }
    
    # Pattern for lowercase snake_case (allows numbers)
    lowercase_pattern = re.compile(r'^[a-z]+(_[a-z0-9]+)*$')
    
    for col in df.columns:
        if lowercase_pattern.match(col):
            validation_results['compliant_columns'] += 1
        else:
            validation_results['non_compliant_columns'].append(col)
    
    if validation_results['non_compliant_columns']:
        validation_results['overall_status'] = 'FAIL'
    
    # Log results
    if validation_results['overall_status'] == 'PASS':
        self.logger.info(f"✅ {data_type} header validation PASSED: All {validation_results['total_columns']} columns follow lowercase snake_case")
    else:
        self.logger.error(f"❌ {data_type} header validation FAILED: {len(validation_results['non_compliant_columns'])} non-compliant columns")
        self.logger.error(f"Non-compliant columns: {validation_results['non_compliant_columns']}")
    
    return validation_results
```

#### 1.2 Integration Points

Header validation is called immediately before every CSV export:

**ComprehensiveSCRPAFixV8_5 Pipeline:**
```python
# RMS data export
header_val = self.validate_lowercase_snake_case_headers(rms_data, 'RMS')
if header_val['overall_status']=='FAIL':
    raise ValueError(f"Invalid headers in RMS data: {header_val['non_compliant_columns']}")
rms_data.to_csv(rms_output, index=False, encoding='utf-8')

# CAD data export
header_val = self.validate_lowercase_snake_case_headers(cad_data, 'CAD')
if header_val['overall_status']=='FAIL':
    raise ValueError(f"Invalid headers in CAD data: {header_val['non_compliant_columns']}")
cad_data.to_csv(cad_output, index=False, encoding='utf-8')

# Joined data export
header_val = self.validate_lowercase_snake_case_headers(joined_data, 'Joined CAD-RMS')
if header_val['overall_status']=='FAIL':
    raise ValueError(f"Invalid headers in joined data: {header_val['non_compliant_columns']}")
joined_data.to_csv(joined_output, index=False, encoding='utf-8')

# 7-day export
header_val = self.validate_lowercase_snake_case_headers(export_df, '7-Day SCRPA Export')
if header_val['overall_status']=='FAIL':
    raise ValueError(f"Invalid headers in 7-day export: {header_val['non_compliant_columns']}")
export_df.to_csv(output_path, index=False, encoding='utf-8')

# Unmapped analysis exports
header_val = self.validate_lowercase_snake_case_headers(unmapped_df, 'Unmapped Analysis')
if header_val['overall_status']=='FAIL':
    raise ValueError(f"Invalid headers in unmapped analysis: {header_val['non_compliant_columns']}")
unmapped_df.to_csv(unmapped_file, index=False, encoding='utf-8')
```

**SCRPAProductionProcessor Pipeline:**
```python
# Production outputs export
for file_key, filename in production_files.items():
    file_path = self.dirs['powerbi'] / filename
    # Standardize data types before export
    datasets[file_key] = self.standardize_data_types(datasets[file_key])
    # Validate headers before export
    header_val = self.validate_lowercase_snake_case_headers(datasets[file_key], f'Production {file_key}')
    if header_val['overall_status']=='FAIL':
        raise ValueError(f"Invalid headers in {file_key}: {header_val['non_compliant_columns']}")
    datasets[file_key].to_csv(file_path, index=False, encoding='utf-8-sig')
```

### Validation Examples

| Column | Compliant | Issue |
|--------|-----------|-------|
| incident_date | ✅ | — |
| IncidentDate | ❌ | Should be: incident_date |
| case_number | ✅ | — |
| CaseNumber | ❌ | Should be: case_number |
| response_type | ✅ | — |
| ResponseType | ❌ | Should be: response_type |

### Benefits

1. **Power BI Compatibility**: Ensures all exported CSVs have headers that work seamlessly with Power BI
2. **Error Prevention**: Catches header issues before they cause downstream problems
3. **Consistency**: Maintains uniform naming conventions across all exports
4. **Quality Assurance**: Provides clear error messages for non-compliant headers

## 2. Cycle Calendar Integration Implementation

### Problem Statement

Each record needs a `cycle_name` (e.g., "C08W31") based on the 7/28-day reporting calendar, and export filenames should use that cycle plus current date.

### Solution Implementation

#### 2.1 Cycle Calendar Loading

```python
def load_cycle_calendar(self):
    """Load Excel file from 09_Reference/Temporal/SCRPA_Cycle/7Day_28Day_Cycle_20250414.xlsx"""
    try:
        if self.ref_dirs['cycle_calendar'].exists():
            cycle_df = pd.read_excel(self.ref_dirs['cycle_calendar'])
            self.logger.info(f"Loaded cycle calendar: {len(cycle_df)} records")
            self.logger.info(f"Cycle calendar columns: {list(cycle_df.columns)}")
            return cycle_df
        else:
            self.logger.warning("Cycle calendar file not found - cycle features will be disabled")
            return pd.DataFrame()
    except Exception as e:
        self.logger.error(f"Could not load cycle calendar: {e}")
        return pd.DataFrame()
```

#### 2.2 Cycle Assignment Method

```python
def get_cycle_for_date(self, incident_date, cycle_df):
    """Return cycle name (like "C08W31") for any date"""
    if cycle_df.empty or pd.isna(incident_date):
        return None
        
    try:
        # Convert incident_date to datetime if it's not already
        if isinstance(incident_date, str):
            incident_date = pd.to_datetime(incident_date, errors='coerce')
        
        if pd.isna(incident_date):
            return None
        
        # Convert to date for comparison
        incident_date = incident_date.date() if hasattr(incident_date, 'date') else incident_date
        
        # Check if date falls within any 7-day cycle
        for _, row in cycle_df.iterrows():
            start_date = pd.to_datetime(row['7_Day_Start']).date()
            end_date = pd.to_datetime(row['7_Day_End']).date()
            
            if start_date <= incident_date <= end_date:
                return row['Report_Name']
        
        return None
    except Exception as e:
        self.logger.warning(f"Error getting cycle for date {incident_date}: {e}")
        return None
```

#### 2.3 Current Cycle Information

```python
def get_current_cycle_info(self, cycle_df):
    """Get current cycle for export naming"""
    if cycle_df.empty:
        return None, None
        
    try:
        today = datetime.now().date()
        
        # Find current cycle
        for _, row in cycle_df.iterrows():
            start_date = pd.to_datetime(row['7_Day_Start']).date()
            end_date = pd.to_datetime(row['7_Day_End']).date()
            
            if start_date <= today <= end_date:
                current_cycle = row['Report_Name']
                current_date = today.strftime('%Y%m%d')
                self.logger.info(f"Current cycle: {current_cycle}, Date: {current_date}")
                return current_cycle, current_date
        
        # If not in current cycle, find the most recent past cycle
        past_cycles = []
        for _, row in cycle_df.iterrows():
            end_date = pd.to_datetime(row['7_Day_End']).date()
            if end_date <= today:
                past_cycles.append((end_date, row['Report_Name']))
        
        if past_cycles:
            # Get the most recent past cycle
            most_recent = max(past_cycles, key=lambda x: x[0])
            current_cycle = most_recent[1]
            current_date = today.strftime('%Y%m%d')
            self.logger.info(f"Using most recent past cycle: {current_cycle}, Date: {current_date}")
            return current_cycle, current_date
        
        return None, None
    except Exception as e:
        self.logger.error(f"Error getting current cycle info: {e}")
        return None, None
```

#### 2.4 Integration in Data Processing

**RMS Data Processing:**
```python
# Apply cycle assignment to incident_date
rms_df['cycle_name'] = rms_df['incident_date'].apply(
    lambda x: self.get_cycle_for_date(x, self.cycle_calendar) if pd.notna(x) else None
)
```

**CAD Data Processing:**
```python
# Apply cycle assignment to incident_date
cad_df['cycle_name'] = cad_df['incident_date'].apply(
    lambda x: self.get_cycle_for_date(x, self.cycle_calendar) if pd.notna(x) else None
)
```

**Export Filename Generation:**
```python
# Generate filename with cycle name and current date
if self.current_cycle and self.current_date:
    filename = f"{self.current_cycle}_{self.current_date}_7Day_SCRPA_Incidents.csv"
else:
    current_date = datetime.now().strftime('%Y_%m_%d')
    filename = f"{current_date}_7Day_SCRPA_Incidents.csv"
```

### Cycle Calendar Examples

| incident_date | cycle_name |
|---------------|------------|
| 2025-08-01 | C08W31 |
| 2025-08-05 | C08W31 |
| 2025-08-10 | C08W32 |
| 2025-08-15 | C08W33 |
| 2025-08-20 | C08W33 |
| 2025-08-25 | C08W34 |
| 2025-09-01 | None (outside cycles) |

### Benefits

1. **Accurate Reporting**: Ensures records are tagged with the correct reporting cycle
2. **Consistent Naming**: Export files use standardized cycle-based naming
3. **Temporal Organization**: Enables proper time-based analysis and reporting
4. **Automated Assignment**: Eliminates manual cycle assignment errors

## 3. Test Results

### Header Validation Tests

```
✅ Header validation correctly identifies non-compliant column names
✅ Both pipeline classes have consistent validation functionality
✅ Validation catches non-compliant headers appropriately
✅ Compliant data passes validation without errors
✅ Error handling works correctly for non-compliant headers
```

### Cycle Calendar Tests

```
✅ Cycle calendar loading works correctly
✅ Date-to-cycle assignment functions properly
✅ Current cycle detection works for various scenarios
✅ Export filename generation uses correct cycle information
✅ Error handling for invalid dates works correctly
```

## 4. Files Modified

### Main Implementation Files
- **`Comprehensive_SCRPA_Fix_v8.5_Standardized.py`**: Added header validation and enhanced cycle calendar integration
- **`SCRPA_Time_v4_Production_Pipeline.py`**: Added header validation method and integration

### Test Files
- **`test_header_validation_and_cycle_calendar.py`**: Comprehensive test suite for both features

### Documentation
- **`Header_Validation_and_Cycle_Calendar_Implementation.md`**: This documentation file

## 5. Usage Examples

### Header Validation Usage

```python
# Initialize processor
processor = ComprehensiveSCRPAFixV8_5()

# Validate headers before export
validation_result = processor.validate_lowercase_snake_case_headers(df, 'Test Data')
if validation_result['overall_status'] == 'FAIL':
    print(f"Non-compliant columns: {validation_result['non_compliant_columns']}")
else:
    print("All headers are compliant")
```

### Cycle Calendar Usage

```python
# Load cycle calendar
cycle_df = processor.load_cycle_calendar()

# Get cycle for specific date
cycle_name = processor.get_cycle_for_date('2025-08-01', cycle_df)
print(f"Cycle for 2025-08-01: {cycle_name}")

# Get current cycle info
current_cycle, current_date = processor.get_current_cycle_info(cycle_df)
print(f"Current cycle: {current_cycle}, Date: {current_date}")
```

## 6. Future Enhancements

### Header Validation Enhancements
1. **Configurable Patterns**: Allow custom regex patterns for different naming conventions
2. **Auto-correction**: Automatically fix common header naming issues
3. **Batch Validation**: Validate multiple DataFrames simultaneously

### Cycle Calendar Enhancements
1. **Dynamic Calendar Loading**: Support for multiple calendar files
2. **Custom Cycle Definitions**: Allow custom cycle period definitions
3. **Historical Cycle Support**: Better handling of historical data cycles

## Conclusion

The header validation and cycle calendar integration features provide robust quality assurance and temporal organization for the SCRPA pipeline. These features ensure Power BI compatibility and accurate cycle-based reporting, improving the overall reliability and usability of the data processing system.

The implementation is comprehensive, well-tested, and integrated seamlessly into the existing pipeline workflow. Both features include proper error handling, logging, and validation to ensure reliable operation in production environments. 