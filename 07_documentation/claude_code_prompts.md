# Claude Code Prompts - SCRPA PBIX Configurator Fixes

// 2025-07-25-15-30-00
# SCRPA_Time_v2/configure_scrpa_pbix_fixes
# Author: R. A. Carucci  
# Purpose: Targeted Claude Code prompts to fix critical PBIX configurator errors

## **PRIORITY 1: Fix Batch Script Syntax Errors**

### Prompt 1A: Fix Variable Declaration Syntax
```bash
# Navigate to the project directory and fix the batch script variables
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"

# Review and fix the configure_scrpa_pbix.bat file - specifically these syntax errors:
# 1. Change %\~dp0 to %~dp0 (remove backslash)
# 2. Change PROJECT\_ROOT to PROJECT_ROOT (remove backslashes from variable names)
# 3. Fix all variable declarations with underscores and backslashes
# 4. Ensure proper path concatenation in MAIN_PBIX and LEGACY_PBIX variables

# Create a fixed version that resolves the PROJECT_ROOT correctly to parent directory
```

### Prompt 1B: Fix Archive Command Interpolation
```bash
# Fix the archive command variables in configure_scrpa_pbix.bat
# Current issue: %EXTRACT_CMD% and %COMPRESS_CMD% not interpolating with quoted paths
# 
# Need to fix:
# 1. PowerShell command quoting for Expand-Archive and Compress-Archive
# 2. 7z command parameter passing with proper placeholder substitution
# 3. Error handling when archive commands fail
```

## **PRIORITY 2: Python DateTime Import Fixes**

### Prompt 2A: Fix DateTime Module Imports Across All Scripts
```bash
# Search and fix datetime import issues in SCRPA Python scripts
cd "C:\Users\carucci_r\SCRPA_LAPTOP\scripts"

# Find all Python files with incorrect datetime imports and fix:
# Change: import datetime → from datetime import datetime, strptime
# Or: Use datetime.datetime.strptime instead of datetime.strptime
# 
# Files to check: main.py, config.py, chart_export.py, incident_table_automation.py
```

### Prompt 2B: Debug Config.py Import Failures
```bash
# Create a diagnostic script to identify why config.py fails to import
cd "C:\Users\carucci_r\SCRPA_LAPTOP\scripts"

# Test imports step by step:
# 1. Basic Python imports (os, sys, pathlib)
# 2. External dependencies (openpyxl, pandas, matplotlib)  
# 3. ArcPy import in ArcGIS Pro environment
# 4. Path resolution issues

# Generate a detailed error log showing exactly which import fails
```

## **PRIORITY 3: Path Resolution & Environment Detection**

### Prompt 3A: Create Robust PROJECT_ROOT Detection
```bash
# Fix the batch script PROJECT_ROOT detection logic
# Current issue: Script points to 01_scripts subfolder instead of parent

# Create a reliable method using:
# 1. %~dp0.. for parent directory resolution
# 2. pushd/popd for absolute path resolution  
# 3. Validation that PBIX files exist before proceeding
# 4. Fallback error handling with proper pause commands
```

### Prompt 3B: Environment-Specific Path Configuration
```bash
# Create an environment detection script that handles:
# 1. OneDrive vs local development paths
# 2. Different user profile locations
# 3. ArcGIS Pro Python environment detection
# 4. Automatic fallback to PowerShell archive commands when 7-Zip unavailable
```

## **PRIORITY 4: DataMashup Processing Fixes**

### Prompt 4A: Fix DataMashup Search Logic  
```bash
# Fix the recursive search for DataMashup files in extracted PBIX
# Current issue: Hard-coded locations fail, need wildcard pattern search

# Implement:
# 1. Recursive directory search with proper error handling
# 2. Validation that DataMashup contains BasePath parameter
# 3. Backup of original DataMashup before modification
# 4. Verification of successful parameter replacement
```

### Prompt 4B: Enhance PowerShell Regex for Parameter Replacement
```bash
# Improve the PowerShell regex for in-place BasePath replacement
# Current pattern may not handle all Edge cases

# Create robust pattern that:
# 1. Handles different quote types and escaping
# 2. Validates parameter exists before replacement
# 3. Preserves file encoding (UTF8 vs Latin1)
# 4. Logs successful vs failed replacements
```

## **PRIORITY 5: Comprehensive Testing & Validation**

### Prompt 5A: Create End-to-End Test Script
```bash
# Create a comprehensive test script that validates:
# 1. All paths resolve correctly
# 2. PBIX files are found and readable
# 3. Archive/extract operations work properly
# 4. Parameter replacement is successful
# 5. Generated files are valid Power BI files

# Include rollback mechanism if any step fails
```

### Prompt 5B: Generate Summary JSON Output
```bash
# Implement the missing pbix_configuration_summary.json output
# Current issue: Only echoed to console, not written to file

# Create JSON summary containing:
# 1. Environment configuration used
# 2. Files processed with success/failure status
# 3. Backup locations created  
# 4. Any errors encountered with timestamps
# 5. Parameter values applied to each file
```

## **EXECUTION ORDER**

1. **Start with Prompt 1A** - Fix basic batch syntax errors first
2. **Then Prompt 3A** - Get path resolution working
3. **Follow with Prompt 2A** - Fix Python datetime issues
4. **Continue with Prompts 1B & 4A** - Fix archive and DataMashup logic
5. **Finish with Prompt 5A** - Comprehensive testing

## **QUICK DIAGNOSTIC COMMANDS**

```bash
# Test basic functionality after each fix:
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
configure_scrpa_pbix.bat

# Test Python config separately:
cd "C:\Users\carucci_r\SCRPA_LAPTOP\scripts"
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" config.py

# Validate PBIX files exist:
dir *.pbix
```

## **ALTERNATIVE APPROACH: Python Replacement**

If batch script continues to fail, consider using the existing **update_pbix_parameter.py** script which already works correctly:

```bash
# Use Python script instead of batch for reliable operation:
python update_pbix_parameter.py --input "SCRPA_Time_v2.pbix" --output "SCRPA_Time_v2_updated.pbix" --param "BasePath" --value "C:\Your\New\Path"
```