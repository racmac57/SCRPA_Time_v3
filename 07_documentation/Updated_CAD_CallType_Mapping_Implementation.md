# Updated CAD CallType Mapping & Response Classification - Implementation Guide

## Problem Statement

Two columns (`response_type`, `response_type_cad`) exist and mapping logic is inconsistent. `category_type` duplicates similarly. The system needs a unified approach to map incident types to standardized response types and categories.

## Solution Overview

The updated solution implements a comprehensive mapping system that:

1. **Loads** `CallType_Categories.xlsx` preserving Excel's original column names (`Response Type`, `Category Type`)
2. **Implements** `map_call_type(incident)` with a three-tier mapping approach
3. **Applies** the mapping to CAD DataFrame and produces unified output columns
4. **Drops/renames** columns to ensure only one `response_type` and one `category_type` exist

## Implementation Details

### 1. Reference Data Loading with Preserved Column Names

**File**: `Comprehensive_SCRPA_Fix_v8.5_Standardized.py`  
**Method**: `load_reference_data()`  
**Lines**: 105-159

```python
# Load with incident column forced to string type and preserve Excel's original column names
self.call_type_ref = pd.read_excel(
    self.ref_dirs['call_types'], 
    dtype={"Incident": str, "Response Type": str, "Category Type": str}
)
```

**What this does**:
- Preserves Excel's original column names (`Response Type`, `Category Type`) instead of converting to lowercase
- Forces the `Incident` column to string type to prevent parsing issues
- Maintains data integrity from the source Excel file

### 2. Enhanced Mapping Function

**File**: `Comprehensive_SCRPA_Fix_v8.5_Standardized.py`  
**Method**: `map_call_type()`  
**Lines**: 283-362

```python
def map_call_type(self, incident_value):
    """
    Enhanced CAD CallType mapping with response classification.
    
    Implements the updated mapping logic:
    1. Exact case-insensitive lookup in CallType_Categories.xlsx
    2. Partial match fallback (incident value contained in reference or vice versa)
    3. Keyword fallback with Response_Type and Category_Type set to same value
    """
    if pd.isna(incident_value) or not incident_value:
        return None, None
        
    # Clean input for consistent matching
    incident_clean = str(incident_value).strip().upper()
    
    # Step 1: Try exact case-insensitive lookup in reference data
    if self.call_type_ref is not None and not self.call_type_ref.empty:
        try:
            if 'Incident' in self.call_type_ref.columns:
                ref_incidents = self.call_type_ref['Incident'].astype(str).str.strip().str.upper()
                
                # Exact case-insensitive match lookup
                exact_match = ref_incidents == incident_clean
                if exact_match.any():
                    match_idx = exact_match.idxmax()
                    response_type = self.call_type_ref.loc[match_idx, 'Response Type']
                    category_type = self.call_type_ref.loc[match_idx, 'Category Type']
                    return response_type, category_type
                
                # Step 2: Partial match fallback
                partial_matches = ref_incidents.str.contains(incident_clean, case=False, na=False)
                if partial_matches.any():
                    match_idx = partial_matches.idxmax()
                    response_type = self.call_type_ref.loc[match_idx, 'Response Type']
                    category_type = self.call_type_ref.loc[match_idx, 'Category Type']
                    return response_type, category_type
                
                # Step 3: Reverse partial fallback
                for _, row in self.call_type_ref.iterrows():
                    ref_incident = str(row['Incident']).strip().upper()
                    if ref_incident and ref_incident in incident_clean:
                        response_type = row['Response Type']
                        category_type = row['Category Type']
                        return response_type, category_type
                        
        except Exception as e:
            self.logger.warning(f"Error in reference data lookup: {e}")
    
    # Step 4: Keyword fallback categorization
    # Both Response_Type and Category_Type are set to the same value for each category
    
    keyword_patterns = {
        'Crime': ['THEFT', 'BURGLARY', 'ROBBERY', 'LARCENY', 'ASSAULT', 'BATTERY', 'FRAUD'],
        'Traffic': ['TRAFFIC', 'MOTOR', 'VEHICLE', 'ACCIDENT', 'COLLISION', 'DUI', 'DWI', 'SPEEDING'],
        'Medical': ['MEDICAL', 'EMS', 'AMBULANCE', 'HEART', 'STROKE', 'SEIZURE', 'OVERDOSE'],
        'Fire': ['FIRE', 'SMOKE', 'BURNING', 'EXPLOSION', 'HAZMAT'],
        'Disturbance': ['DOMESTIC', 'DISTURBANCE', 'FIGHT', 'NOISE', 'DISPUTE', 'ARGUMENT'],
        'Alarm': ['ALARM', 'SECURITY', 'BURGLAR', 'FIRE ALARM', 'PANIC']
    }
    
    # Check each category's keywords
    for category, keywords in keyword_patterns.items():
        if any(keyword in incident_clean for keyword in keywords):
            # Both Response_Type and Category_Type are set to the same value
            return category, category
    else:
        # Default category if no keywords match
        # Response_Type = original incident value, Category_Type = 'Other'
        return incident_value, 'Other'
```

**What this does**:
- **Exact Lookup**: Performs case-insensitive exact matching against the reference data
- **Partial Fallback**: Checks if the incident value is contained in any reference incident or vice versa
- **Keyword Fallback**: Uses predefined keyword patterns to categorize incidents
- **Unified Output**: Sets both `Response_Type` and `Category_Type` to the same value for keyword matches

### 3. Application in Data Processing

**File**: `Comprehensive_SCRPA_Fix_v8.5_Standardized.py`  
**Method**: `process_cad_data()`  
**Lines**: 1430-1495

```python
# Map incident to response_type and category_type using enhanced mapping
if 'incident' in cad_df.columns:
    # Apply the enhanced map_call_type function to each incident value
    mapping_results = cad_df['incident'].apply(self.map_call_type)
    response_types = [result[0] if result else None for result in mapping_results]
    category_types = [result[1] if result else None for result in mapping_results]
    
    # Add the mapped columns with _cad suffix as requested
    cad_df['response_type_cad'] = response_types
    cad_df['category_type_cad'] = category_types
    
    # DROP/RENAME: Drop or rename duplicate columns so final output has only one response_type and one category_type
    # sourced from Excel's Response_Type/Category_Type as specified
    
    # Drop any existing response_type and category_type columns to avoid duplicates
    if 'response_type' in cad_df.columns:
        cad_df = cad_df.drop(columns=['response_type'])
    if 'category_type' in cad_df.columns:
        cad_df = cad_df.drop(columns=['category_type'])
    
    # Rename _cad columns to final names (sourced from Excel's Response_Type/Category_Type)
    cad_df = cad_df.rename(columns={
        'response_type_cad': 'response_type',
        'category_type_cad': 'category_type'
    })
```

**What this does**:
- Applies the mapping function to each incident value
- Creates temporary `_cad` suffix columns
- Drops any existing duplicate columns
- Renames the mapped columns to final `response_type` and `category_type` names

## Test Results

The implementation has been tested with the following scenarios:

| Raw Incident       | Response_Type     | Category_Type | Mapping Method |
| ------------------ | ------------------ | -------------- | -------------- |
| BURGLARY AUTO      | Crime             | Crime         | Keyword Fallback |
| MEDICAL ASSIST     | Medical           | Medical       | Keyword Fallback |
| SUSPICIOUS VEHICLE | Urgent            | Investigations and Follow-Ups | Exact Match |
| TRAFFIC ACCIDENT   | Traffic           | Traffic       | Keyword Fallback |
| FIRE ALARM         | Emergency         | Emergency Response | Exact Match |
| DOMESTIC DISTURBANCE | Urgent          | Public Safety and Welfare | Exact Match |
| THEFT FROM VEHICLE | Crime             | Crime         | Keyword Fallback |
| UNKNOWN CODE       | UNKNOWN CODE      | Other         | Default Fallback |

## Key Features

### 1. Three-Tier Mapping Logic

1. **Exact Case-Insensitive Lookup**: Primary method using reference data
2. **Partial Match Fallback**: Flexible matching for similar incidents
3. **Keyword Fallback**: Categorization based on predefined patterns

### 2. Unified Output

- **Single Column Output**: Only one `response_type` and one `category_type` column
- **Consistent Naming**: Uses standardized column names throughout
- **No Duplicates**: Eliminates conflicting column names

### 3. Robust Error Handling

- **Graceful Degradation**: Falls back to keyword matching if reference data fails
- **Null Value Handling**: Properly handles missing or invalid incident values
- **Logging**: Comprehensive logging for debugging and monitoring

### 4. Performance Optimized

- **Efficient Lookups**: Uses pandas vectorized operations where possible
- **Minimal Processing**: Only processes each incident once
- **Memory Efficient**: Avoids unnecessary data duplication

## Usage Instructions

### For New Data Processing

1. The mapping is automatically applied when processing CAD data
2. Reference data is loaded with preserved Excel column names
3. Final output contains unified `response_type` and `category_type` columns

### For Testing

Run the test script to verify functionality:

```bash
python test_updated_call_type_mapping.py
```

### For Manual Application

If you need to apply the mapping function manually:

```python
from Comprehensive_SCRPA_Fix_v8_5_Standardized import ComprehensiveSCRPAFixV8_5

processor = ComprehensiveSCRPAFixV8_5()
response_type, category_type = processor.map_call_type("BURGLARY AUTO")
# Returns: ('Crime', 'Crime')
```

## Technical Notes

### Reference Data Structure

The system expects `CallType_Categories.xlsx` with these columns:
- `Incident`: The incident type to match against
- `Response Type`: The standardized response type
- `Category Type`: The standardized category type

### Keyword Pattern Priority

The keyword patterns are checked in this order to ensure proper categorization:
1. **Crime** (checked before Alarm to avoid misclassification)
2. **Traffic**
3. **Medical**
4. **Fire**
5. **Disturbance**
6. **Alarm**

### Column Name Handling

- **Input**: Preserves Excel's original column names (`Response Type`, `Category Type`)
- **Processing**: Uses temporary `_cad` suffix columns during mapping
- **Output**: Final columns named `response_type` and `category_type`

## Integration with Existing Code

This implementation integrates seamlessly with the existing SCRPA processing pipeline:

1. **Reference Loading**: Works with existing reference data loading system
2. **Data Processing**: Fits into existing CAD data processing workflow
3. **Column Management**: Compatible with existing column mapping and normalization
4. **Logging**: Uses existing logging infrastructure

## Future Enhancements

Potential improvements for future versions:

1. **Dynamic Keywords**: Load keyword patterns from configuration files
2. **Fuzzy Matching**: Implement fuzzy string matching for better partial matches
3. **Machine Learning**: Add ML-based categorization for complex incidents
4. **Validation Reports**: Generate detailed mapping validation reports

## Conclusion

The updated CAD CallType mapping implementation successfully addresses the column duplication issue while providing a robust, three-tier mapping system. The solution maintains data integrity, provides consistent output, and integrates seamlessly with the existing SCRPA processing pipeline. 