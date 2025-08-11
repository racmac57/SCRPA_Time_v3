# SCRPA PBIX Configurator

## Table of Contents
- [Introduction](#introduction)
- [Environment Setup](#environment-setup)
- [Script Execution](#script-execution)
- [Testing Procedures](#testing-procedures)
- [Troubleshooting](#troubleshooting)
- [Alternative Approaches](#alternative-approaches)
- [Appendix](#appendix)

## Introduction

The SCRPA PBIX Configurator is a comprehensive Python-based solution designed to automate the configuration and parameter management of Power BI (.pbix) files for the City of Hackensack Police Department's SCRPA (Statistical Crime Reporting and Predictive Analytics) system. This tool suite addresses the critical need for reliable, auditable, and scalable management of Power BI report parameters across multiple environments (development, staging, production).

### Purpose and Scope

The configurator provides the following core capabilities:

- **Automated Parameter Updates**: Programmatic modification of M-code parameters within PBIX files without requiring Power BI Desktop
- **Environment-Specific Configuration Management**: Support for multiple deployment environments with distinct parameter sets
- **Comprehensive Validation Framework**: Pre and post-execution validation to ensure data integrity and configuration accuracy
- **Backup and Recovery Operations**: Automatic backup creation with rollback capabilities for failed operations
- **Audit Trail Generation**: Complete JSON-based logging for compliance and troubleshooting purposes
- **Batch Processing Capabilities**: Simultaneous processing of multiple PBIX files with consolidated reporting

### Architecture Overview

The solution consists of two primary components:

1. **`update_pbix_parameter.py`**: Core parameter update engine with validation and recovery mechanisms
2. **`main_workflow.py`**: Batch processing orchestrator with environment management and consolidated reporting

These components operate in conjunction with supporting modules for testing, validation, and demonstration purposes.

## Environment Setup

### System Requirements

#### Python Environment
- **Python Version**: 3.8 or higher (3.11+ recommended for optimal performance)
- **Architecture**: 64-bit Python installation required for large PBIX file processing
- **Memory**: Minimum 8GB RAM, 16GB recommended for processing multiple large PBIX files

#### Operating System Compatibility
- **Primary**: Windows 10/11 (recommended for Power BI ecosystem compatibility)
- **Secondary**: Windows Server 2019/2022 for automated deployment scenarios
- **Limited Support**: Linux/macOS (may require additional configuration for file path handling)

### Python Dependencies

#### Core Dependencies
Install the following packages using pip:

```bash
# Essential packages (required)
pip install psutil>=5.9.0

# Optional packages (recommended for enhanced functionality)
pip install openpyxl>=3.1.0
pip install pandas>=1.5.0
```

#### Dependency Details

**Required Dependencies:**
- **`psutil`**: System and process utilities for environment monitoring and resource tracking
  - Used for: Memory usage monitoring, disk space validation, system information collection
  - Installation: `pip install psutil`

**Optional Dependencies:**
- **`openpyxl`**: Excel file manipulation (if PBIX files reference Excel data sources)
  - Used for: Excel file validation and data source verification
  - Installation: `pip install openpyxl`
- **`pandas`**: Data manipulation and analysis (for advanced data validation scenarios)
  - Used for: Data validation, CSV processing, analytical operations
  - Installation: `pip install pandas`

### ArcGIS Pro Integration

#### ArcGIS Pro Python Environment
If the SCRPA system integrates with ArcGIS Pro for geospatial analysis:

```bash
# Activate ArcGIS Pro conda environment
conda activate arcgispro-py3

# Install additional packages in ArcGIS environment
conda install psutil
pip install --user openpyxl pandas
```

#### ArcGIS Considerations
- **Python Path**: Ensure ArcGIS Pro Python environment is properly configured
- **License Validation**: Verify ArcGIS Pro licensing for automated scenarios
- **Spatial Reference**: Confirm coordinate system compatibility for geospatial data sources

### Path Configuration

#### Directory Structure Setup
Establish the following directory structure for optimal operation:

```
SCRPA_Time_v2/
├── scripts/                          # Python scripts location
│   ├── update_pbix_parameter.py      # Core parameter updater
│   ├── main_workflow.py              # Batch workflow manager
│   ├── test_pbix_update.py           # Testing suite
│   └── supporting_scripts/           # Additional utilities
├── pbix_files/                       # PBIX files directory
│   ├── SCRPA_Time_v2.pbix           # Primary report file
│   └── additional_reports/           # Additional PBIX files
├── config/                           # Configuration files
│   ├── workflow_config.json         # Workflow configuration
│   └── environment_configs/         # Environment-specific configs
├── output/                           # Generated output files
│   ├── updated_pbix/                # Updated PBIX files
│   ├── backups/                     # Backup files
│   ├── logs/                        # Log files
│   └── summaries/                   # JSON summaries
└── temp/                            # Temporary processing files
```

#### Environment Variables
Configure the following environment variables for consistent operation:

```bash
# Windows Command Prompt / PowerShell
set SCRPA_BASE_PATH=C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2
set SCRPA_OUTPUT_PATH=%SCRPA_BASE_PATH%\output
set SCRPA_BACKUP_PATH=%SCRPA_BASE_PATH%\backups
set PYTHONPATH=%SCRPA_BASE_PATH%\scripts;%PYTHONPATH%
```

```bash
# Linux/macOS (if applicable)
export SCRPA_BASE_PATH="/path/to/SCRPA_Time_v2"
export SCRPA_OUTPUT_PATH="$SCRPA_BASE_PATH/output"
export SCRPA_BACKUP_PATH="$SCRPA_BASE_PATH/backups"
export PYTHONPATH="$SCRPA_BASE_PATH/scripts:$PYTHONPATH"
```

#### Path Validation
Verify path configuration using the following validation script:

```python
import os
import sys
from pathlib import Path

def validate_environment():
    """Validate SCRPA environment configuration."""
    required_paths = [
        os.environ.get('SCRPA_BASE_PATH'),
        os.environ.get('SCRPA_OUTPUT_PATH'),
        os.environ.get('SCRPA_BACKUP_PATH')
    ]
    
    for path in required_paths:
        if not path or not Path(path).exists():
            print(f"ERROR: Required path not found or not set: {path}")
            return False
    
    print("✅ Environment configuration validated successfully")
    return True

if __name__ == "__main__":
    validate_environment()
```

## Script Execution

### Prerequisites Verification

Before executing scripts, ensure the following prerequisites are met:

```bash
# Verify Python installation and version
python --version
# Expected output: Python 3.8.x or higher

# Verify required packages
python -c "import psutil; print(f'psutil version: {psutil.__version__}')"

# Verify PBIX file accessibility
python -c "import os; print('PBIX file exists:', os.path.exists('SCRPA_Time_v2.pbix'))"
```

### Core Parameter Update Script

#### Basic Execution Syntax

```bash
python update_pbix_parameter.py [OPTIONS]
```

#### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--input`, `-i` | Path to input PBIX file | `"SCRPA_Time_v2.pbix"` |
| `--output`, `-o` | Path to output PBIX file | `"SCRPA_Time_v2_updated.pbix"` |
| `--param`, `-p` | Parameter name to update | `"BasePath"` |
| `--value`, `-v` | New parameter value | `"C:\\New\\Data\\Path"` |

#### Optional Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--validate-all` | Enable comprehensive validation | `False` |
| `--verbose` | Enable detailed logging | `False` |
| `--summary-json`, `-s` | JSON summary output path | Auto-generated |
| `--no-backup` | Skip backup creation | `False` |

#### Execution Examples

**Basic Parameter Update:**
```bash
python update_pbix_parameter.py \
    --input "SCRPA_Time_v2.pbix" \
    --output "SCRPA_Time_v2_updated.pbix" \
    --param "BasePath" \
    --value "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
```

**Comprehensive Update with Validation:**
```bash
python update_pbix_parameter.py \
    --input "SCRPA_Time_v2.pbix" \
    --output "SCRPA_Time_v2_prod.pbix" \
    --param "BasePath" \
    --value "\\server\share\SCRPA_Production" \
    --validate-all \
    --verbose \
    --summary-json "production_update_summary.json"
```

**Multiple Parameter Updates (Sequential):**
```bash
# Step 1: Update BasePath
python update_pbix_parameter.py \
    -i "SCRPA_Time_v2.pbix" \
    -o "SCRPA_Time_v2_step1.pbix" \
    -p "BasePath" \
    -v "C:\Production\Data" \
    --validate-all

# Step 2: Update ServerName
python update_pbix_parameter.py \
    -i "SCRPA_Time_v2_step1.pbix" \
    -o "SCRPA_Time_v2_step2.pbix" \
    -p "ServerName" \
    -v "prod-sql-server" \
    --validate-all

# Step 3: Final parameter update
python update_pbix_parameter.py \
    -i "SCRPA_Time_v2_step2.pbix" \
    -o "SCRPA_Time_v2_final.pbix" \
    -p "DatabaseName" \
    -v "SCRPA_Production" \
    --validate-all \
    --summary-json "final_summary.json"
```

### Batch Workflow Manager

#### Configuration File Creation

Generate a sample workflow configuration:

```bash
python main_workflow.py --create-sample-config "scrpa_workflow_config.json"
```

This creates a configuration file with the following structure:

```json
{
  "pbix_files": [
    "SCRPA_Time_v2.pbix",
    "SCRPA_Analysis.pbix"
  ],
  "parameters": {
    "BasePath": "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2",
    "ServerName": "localhost",
    "DatabaseName": "SCRPA_CrimeDB"
  },
  "environments": {
    "development": {
      "BasePath": "C:\\Dev\\SCRPA",
      "ServerName": "dev-server",
      "DatabaseName": "SCRPA_Dev"
    },
    "production": {
      "BasePath": "\\\\prod-server\\data",
      "ServerName": "prod-server",
      "DatabaseName": "SCRPA_Production"
    }
  },
  "retry_attempts": 3,
  "continue_on_error": true
}
```

#### Workflow Execution Examples

**Single File Processing:**
```bash
python main_workflow.py \
    --pbix "SCRPA_Time_v2.pbix" \
    --param "BasePath" \
    --value "C:\Production\Data" \
    --verbose
```

**Environment-Specific Batch Processing:**
```bash
# Development environment
python main_workflow.py \
    --config "scrpa_workflow_config.json" \
    --environment "development" \
    --verbose

# Production environment
python main_workflow.py \
    --config "scrpa_workflow_config.json" \
    --environment "production" \
    --verbose
```

**Advanced Batch Processing with Custom Options:**
```bash
python main_workflow.py \
    --config "scrpa_workflow_config.json" \
    --environment "production" \
    --retry-attempts 5 \
    --continue-on-error \
    --verbose
```

### Directory Navigation and File Management

#### Recommended Directory Navigation Sequence

```bash
# Navigate to project directory
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\scripts"

# Verify current directory contains required scripts
dir *.py

# Expected output should include:
# update_pbix_parameter.py
# main_workflow.py
# test_pbix_update.py

# Verify PBIX files are accessible
dir ..\*.pbix

# Create output directories if they don't exist
mkdir output 2>nul
mkdir backups 2>nul
mkdir logs 2>nul
```

#### File Management Best Practices

**Pre-Execution File Verification:**
```bash
# Verify PBIX file integrity
python -c "
import zipfile
import sys
try:
    with zipfile.ZipFile('SCRPA_Time_v2.pbix', 'r') as z:
        files = z.namelist()
        print(f'✅ PBIX file valid: {len(files)} internal files')
except Exception as e:
    print(f'❌ PBIX file error: {e}')
    sys.exit(1)
"
```

**Post-Execution Cleanup:**
```bash
# Archive log files (optional)
mkdir "archive\%date:~-4,4%%date:~-10,2%%date:~-7,2%" 2>nul
move *.log "archive\%date:~-4,4%%date:~-10,2%%date:~-7,2%\" 2>nul

# Clean temporary files
del /q temp_*.pbix 2>nul
```

## Testing Procedures

### Validation Framework Overview

The SCRPA PBIX Configurator implements a comprehensive multi-layered validation framework to ensure operational reliability and data integrity throughout the parameter update process.

### Pre-Execution Validation

#### Path and File Validation

```bash
# Execute comprehensive input validation
python update_pbix_parameter.py \
    --input "SCRPA_Time_v2.pbix" \
    --output "test_output.pbix" \
    --param "BasePath" \
    --value "C:\Test\Path" \
    --validate-all \
    --verbose
```

**Validation Checkpoints:**
- **File Existence**: Confirms input PBIX file accessibility
- **File Format**: Validates PBIX file as valid ZIP archive
- **File Permissions**: Verifies read/write access permissions
- **Directory Structure**: Validates output directory writability
- **Path Resolution**: Converts relative paths to absolute paths

#### Parameter Validation

**Parameter Existence Verification:**
```python
# Manual parameter validation example
python -c "
from update_pbix_parameter import PBIXParameterUpdater
updater = PBIXParameterUpdater(verbose=True)
result = updater.validate_parameter_exists('SCRPA_Time_v2.pbix', 'BasePath')
print(f'Parameter found: {result[\"parameter_found\"]}')
print(f'Current value: {result[\"current_value\"]}')
"
```

**Parameter Detection Output Analysis:**
- **Detection Method**: Regex pattern matching with multiple fallback strategies
- **Current Value Extraction**: Retrieves existing parameter values for comparison
- **Pattern Recognition**: Identifies M-code parameter assignment patterns
- **Encoding Compatibility**: Validates parameter content across different character encodings

### Runtime Validation

#### Processing Validation

**Step-by-Step Process Monitoring:**
```bash
# Execute with comprehensive logging
python update_pbix_parameter.py \
    --input "SCRPA_Time_v2.pbix" \
    --output "validated_output.pbix" \
    --param "BasePath" \
    --value "C:\Validated\Path" \
    --validate-all \
    --verbose \
    --summary-json "runtime_validation.json"
```

**Runtime Checkpoints:**
- **Extraction Validation**: Confirms successful PBIX content extraction
- **DataMashup Location**: Validates M-code file detection using multiple strategies
- **Content Modification**: Verifies successful parameter value updates
- **Repackaging Integrity**: Ensures proper PBIX file reconstruction

#### Backup and Recovery Validation

**Backup Creation Verification:**
```python
# Validate backup creation process
python -c "
import json
with open('runtime_validation.json', 'r') as f:
    summary = json.load(f)
    
backup_info = summary.get('validation_results', {}).get('backup_info', {})
if backup_info and backup_info.get('backup_successful'):
    print(f'✅ Backup created: {backup_info[\"backup_file\"]}')
    print(f'✅ Checksum verified: {backup_info[\"checksum_original\"] == backup_info[\"checksum_backup\"]}')
else:
    print('❌ Backup creation failed')
"
```

### Post-Execution Validation

#### Output File Validation

**Output Integrity Verification:**
```bash
# Validate output file completeness and integrity
python update_pbix_parameter.py \
    --input "validated_output.pbix" \
    --output "temp_verification.pbix" \
    --param "TestParam" \
    --value "TestValue" \
    --validate-all
```

**Post-Execution Checkpoints:**
- **File Size Consistency**: Compares input and output file sizes for reasonableness
- **ZIP Archive Integrity**: Validates output PBIX as properly formatted ZIP file
- **Parameter Verification**: Confirms updated parameters contain expected values
- **M-code Syntax Validation**: Ensures M-code remains syntactically correct

#### Parameter Update Verification

**Value Confirmation Process:**
```python
# Verify parameter update accuracy
python -c "
from update_pbix_parameter import PBIXParameterUpdater
updater = PBIXParameterUpdater(verbose=False)

# Check updated parameter value
result = updater.validate_parameter_exists('validated_output.pbix', 'BasePath')
expected_value = 'C:\Validated\Path'
actual_value = result.get('current_value')

if actual_value == expected_value:
    print(f'✅ Parameter verification successful: {actual_value}')
else:
    print(f'❌ Parameter verification failed: Expected {expected_value}, Got {actual_value}')
"
```

### Rollback Testing Procedures

#### Automatic Rollback Validation

**Induced Failure Testing:**
```bash
# Test rollback mechanism with intentional failure
python update_pbix_parameter.py \
    --input "SCRPA_Time_v2.pbix" \
    --output "rollback_test.pbix" \
    --param "NonExistentParameter" \
    --value "TestValue" \
    --validate-all \
    --verbose \
    --summary-json "rollback_test.json"
```

**Rollback Verification Process:**
```python
# Analyze rollback execution
python -c "
import json
with open('rollback_test.json', 'r') as f:
    summary = json.load(f)

rollback_performed = summary.get('rollback_performed', False)
rollback_successful = summary.get('rollback_successful', False)

print(f'Rollback performed: {rollback_performed}')
print(f'Rollback successful: {rollback_successful}')

if rollback_performed and rollback_successful:
    print('✅ Rollback mechanism validated successfully')
else:
    print('❌ Rollback mechanism requires attention')
"
```

#### Manual Rollback Testing

**Manual Recovery Process:**
```bash
# Manual rollback execution example
python -c "
import json
import shutil
import os

# Load backup information from summary
with open('rollback_test.json', 'r') as f:
    summary = json.load(f)

backup_info = summary.get('validation_results', {}).get('backup_info', {})
if backup_info and backup_info.get('backup_successful'):
    backup_file = backup_info['backup_file']
    original_file = backup_info['original_file']
    
    # Perform manual restoration
    if os.path.exists(backup_file):
        shutil.copy2(backup_file, original_file)
        print(f'✅ Manual rollback completed: {os.path.basename(original_file)}')
    else:
        print(f'❌ Backup file not found: {backup_file}')
else:
    print('❌ No backup information available for rollback')
"
```

### JSON Summary Validation

#### Summary Content Verification

**Comprehensive Summary Analysis:**
```python
# Analyze JSON summary completeness
python -c "
import json
from datetime import datetime

def validate_json_summary(summary_path):
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    # Required fields validation
    required_fields = [
        'session_id', 'success', 'duration_seconds', 
        'system_environment', 'input_file', 'output_file',
        'parameters', 'backups', 'errors', 'warnings'
    ]
    
    missing_fields = [field for field in required_fields if field not in summary]
    
    if missing_fields:
        print(f'❌ Missing required fields: {missing_fields}')
        return False
    
    # Content validation
    print(f'✅ Session ID: {summary[\"session_id\"]}')
    print(f'✅ Operation Success: {summary[\"success\"]}')
    print(f'✅ Duration: {summary[\"duration_seconds\"]}s')
    print(f'✅ Parameters Processed: {len(summary[\"parameters\"])}')
    print(f'✅ Backups Created: {len(summary[\"backups\"])}')
    print(f'✅ Errors Recorded: {len(summary[\"errors\"])}')
    print(f'✅ Warnings Recorded: {len(summary[\"warnings\"])}')
    
    return True

# Validate most recent summary
validate_json_summary('runtime_validation.json')
"
```

### End-to-End Testing Scenarios

#### Comprehensive Integration Testing

**Full Workflow Integration Test:**
```bash
# Execute comprehensive end-to-end test
python test_pbix_update.py \
    --pbix "SCRPA_Time_v2.pbix" \
    --param "BasePath" \
    --value "C:\EndToEnd\Test\Path" \
    --test-all \
    --verbose \
    --report "e2e_test_report.txt"
```

**Batch Processing Integration Test:**
```bash
# Create test configuration
python main_workflow.py --create-sample-config "e2e_test_config.json"

# Execute batch processing test
python main_workflow.py \
    --config "e2e_test_config.json" \
    --environment "development" \
    --verbose
```

#### Performance and Stress Testing

**Large File Processing Test:**
```bash
# Test with multiple large PBIX files
python main_workflow.py \
    --config "stress_test_config.json" \
    --retry-attempts 5 \
    --continue-on-error \
    --verbose
```

**Memory and Resource Monitoring:**
```python
# Monitor resource usage during processing
python -c "
import psutil
import subprocess
import time

# Start monitoring
process = psutil.Process()
start_memory = process.memory_info().rss / 1024 / 1024  # MB

print(f'Starting memory usage: {start_memory:.2f} MB')

# Execute parameter update
result = subprocess.run([
    'python', 'update_pbix_parameter.py',
    '--input', 'SCRPA_Time_v2.pbix',
    '--output', 'stress_test_output.pbix',
    '--param', 'BasePath',
    '--value', 'C:\\\\Stress\\\\Test\\\\Path',
    '--validate-all'
], capture_output=True, text=True)

end_memory = process.memory_info().rss / 1024 / 1024  # MB
memory_delta = end_memory - start_memory

print(f'Ending memory usage: {end_memory:.2f} MB')
print(f'Memory increase: {memory_delta:.2f} MB')
print(f'Exit code: {result.returncode}')
"
```

### Diagnostic and Debugging Procedures

#### Verbose Logging Analysis

**Log File Examination:**
```bash
# Generate detailed diagnostic logs
python update_pbix_parameter.py \
    --input "SCRPA_Time_v2.pbix" \
    --output "diagnostic_output.pbix" \
    --param "BasePath" \
    --value "C:\Diagnostic\Path" \
    --validate-all \
    --verbose \
    --summary-json "diagnostic_summary.json"

# Analyze log file contents
findstr /i "error\|warning\|datamashup\|validation" pbix_update_*.log
```

**Error Pattern Analysis:**
```python
# Analyze error patterns in JSON summaries
python -c "
import json
import glob

# Collect all summary files
summary_files = glob.glob('*summary*.json')

error_patterns = {}
for file in summary_files:
    try:
        with open(file, 'r') as f:
            summary = json.load(f)
            
        for error in summary.get('errors', []):
            error_type = error.get('error_type', 'Unknown')
            error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
    except:
        continue

print('Error Pattern Analysis:')
for pattern, count in error_patterns.items():
    print(f'  {pattern}: {count} occurrences')
"
```

#### Component-Level Testing

**Individual Module Testing:**
```bash
# Test DataMashup detection module
python -c "
from update_pbix_parameter import PBIXParameterUpdater
import tempfile
import zipfile

updater = PBIXParameterUpdater(verbose=True)

# Extract PBIX for inspection
with tempfile.TemporaryDirectory() as temp_dir:
    with zipfile.ZipFile('SCRPA_Time_v2.pbix', 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    mashup_location = updater._find_datamashup_file(temp_dir)
    if mashup_location:
        print(f'✅ DataMashup detection successful: {mashup_location}')
        
        # Test parameter detection
        parameters = updater._detect_parameters(mashup_location)
        print(f'✅ Parameters detected: {len(parameters)}')
        for param in parameters:
            print(f'  - {param[\"name\"]}: {param[\"value\"]}')
    else:
        print('❌ DataMashup detection failed')
"
```

## Troubleshooting

### Common Issues and Resolutions

#### Import and Module Issues

**Issue: ModuleNotFoundError for update_pbix_parameter**

```
Error: ModuleNotFoundError: No module named 'update_pbix_parameter'
```

**Resolution:**
```bash
# Verify current directory contains the required script
ls -la update_pbix_parameter.py

# If script is in different directory, either:
# Option 1: Navigate to correct directory
cd /path/to/scripts/directory

# Option 2: Add directory to PYTHONPATH
export PYTHONPATH="/path/to/scripts:$PYTHONPATH"

# Option 3: Use absolute path for script execution
python /full/path/to/update_pbix_parameter.py [options]
```

**Issue: psutil Import Failure**

```
Error: ModuleNotFoundError: No module named 'psutil'
```

**Resolution:**
```bash
# Install psutil using pip
pip install psutil

# For ArcGIS Pro environment
conda activate arcgispro-py3
pip install --user psutil

# Verify installation
python -c "import psutil; print('psutil version:', psutil.__version__)"
```

**Issue: Encoding Errors in Module Imports**

```
Error: UnicodeDecodeError: 'charmap' codec can't decode byte
```

**Resolution:**
```bash
# Set environment variables for UTF-8 encoding
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

# Or specify encoding in script execution
python -X utf8 update_pbix_parameter.py [options]
```

#### Path and File Access Issues

**Issue: PBIX File Access Denied**

```
Error: PermissionError: [Errno 13] Permission denied: 'SCRPA_Time_v2.pbix'
```

**Resolution:**
```bash
# Check file permissions
icacls "SCRPA_Time_v2.pbix"

# Grant full control to current user
icacls "SCRPA_Time_v2.pbix" /grant %username%:F

# Ensure file is not opened in Power BI Desktop
# Close Power BI Desktop and retry operation

# For network locations, verify network connectivity
net use \\server\share /persistent:yes
```

**Issue: Output Directory Creation Failure**

```
Error: FileNotFoundError: [Errno 2] No such file or directory: 'output/updated_file.pbix'
```

**Resolution:**
```bash
# Create required directories manually
mkdir output
mkdir backups
mkdir logs
mkdir summaries

# Or use Python to create directories
python -c "
import os
directories = ['output', 'backups', 'logs', 'summaries']
for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f'Created directory: {directory}')
"
```

**Issue: Long Path Names (Windows)**

```
Error: OSError: [Errno 36] File name too long
```

**Resolution:**
```bash
# Enable long path support in Windows (requires admin rights)
# Registry edit: HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem
# Set LongPathsEnabled to 1

# Alternative: Use shorter path names
# Move files to directory with shorter path
# Use UNC path format for very long paths
```

#### PBIX Archive and ZIP Issues

**Issue: BadZipFile Error**

```
Error: zipfile.BadZipFile: File is not a zip file
```

**Resolution:**
```bash
# Verify PBIX file integrity
python -c "
import zipfile
try:
    with zipfile.ZipFile('SCRPA_Time_v2.pbix', 'r') as z:
        print('✅ PBIX file is valid ZIP archive')
        print(f'Contains {len(z.namelist())} files')
except zipfile.BadZipFile:
    print('❌ PBIX file is corrupted or not a valid ZIP archive')
    print('Try re-saving the file from Power BI Desktop')
except Exception as e:
    print(f'❌ Error reading PBIX file: {e}')
"

# If corrupted, restore from backup or re-create in Power BI Desktop
# Verify file extension is correct (.pbix not .pbit)
```

**Issue: DataMashup File Not Found**

```
Error: DataMashup file not found in PBIX archive
```

**Resolution:**
```bash
# Inspect PBIX contents to locate DataMashup
python -c "
import zipfile
with zipfile.ZipFile('SCRPA_Time_v2.pbix', 'r') as z:
    files = z.namelist()
    print('PBIX Contents:')
    for file in sorted(files):
        print(f'  {file}')
    
    # Look for DataMashup alternatives
    mashup_candidates = [f for f in files if 'mashup' in f.lower() or 'datamashup' in f.lower()]
    if mashup_candidates:
        print('\\nPotential DataMashup files:')
        for candidate in mashup_candidates:
            print(f'  {candidate}')
    else:
        print('\\n❌ No DataMashup-like files found')
        print('This PBIX may not contain parameters or uses a different structure')
"

# If no DataMashup found, the PBIX may not contain parameters
# Create parameters in Power BI Desktop and re-save the file
```

**Issue: DataMashup Content Encoding Problems**

```
Error: UnicodeDecodeError: Could not decode DataMashup file
```

**Resolution:**
```bash
# Test different encoding methods
python -c "
import zipfile
import tempfile

with tempfile.TemporaryDirectory() as temp_dir:
    with zipfile.ZipFile('SCRPA_Time_v2.pbix', 'r') as z:
        z.extractall(temp_dir)
    
    # Try to read DataMashup with different encodings
    import os
    mashup_path = os.path.join(temp_dir, 'DataMashup')
    
    if os.path.exists(mashup_path):
        encodings = ['utf-8', 'latin1', 'utf-16le', 'utf-16be', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(mashup_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f'✅ Successfully decoded with {encoding}')
                print(f'Content length: {len(content)} characters')
                break
            except UnicodeDecodeError:
                continue
        else:
            print('❌ Could not decode with any standard encoding')
            print('File may be binary or use non-standard encoding')
    else:
        print('❌ DataMashup file not found at expected location')
"
```

#### Environment and Configuration Issues

**Issue: Environment Variable Not Set**

```
Error: KeyError: 'SCRPA_BASE_PATH'
```

**Resolution:**
```bash
# Windows Command Prompt
set SCRPA_BASE_PATH=C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2

# Windows PowerShell
$env:SCRPA_BASE_PATH = "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"

# Linux/macOS
export SCRPA_BASE_PATH="/path/to/SCRPA_Time_v2"

# Verify environment variable is set
echo %SCRPA_BASE_PATH%  # Windows CMD
echo $env:SCRPA_BASE_PATH  # PowerShell
echo $SCRPA_BASE_PATH  # Linux/macOS
```

**Issue: JSON Configuration File Errors**

```
Error: json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes
```

**Resolution:**
```bash
# Validate JSON configuration file syntax
python -m json.tool workflow_config.json

# If validation fails, check for:
# - Missing commas between properties
# - Unescaped backslashes in paths (use \\\\ or forward slashes)
# - Trailing commas before closing braces
# - Missing double quotes around property names

# Example of correct JSON format:
cat > corrected_config.json << 'EOL'
{
  "pbix_files": [
    "SCRPA_Time_v2.pbix"
  ],
  "parameters": {
    "BasePath": "C:\\\\Data\\\\SCRPA"
  },
  "environments": {
    "production": {
      "BasePath": "\\\\\\\\server\\\\share\\\\data"
    }
  }
}
EOL
```

**Issue: Memory Insufficient for Large PBIX Files**

```
Error: MemoryError: Unable to allocate array
```

**Resolution:**
```bash
# Monitor memory usage
python -c "
import psutil
memory = psutil.virtual_memory()
print(f'Total memory: {memory.total / 1024**3:.2f} GB')
print(f'Available memory: {memory.available / 1024**3:.2f} GB')
print(f'Memory usage: {memory.percent}%')
"

# For large files, process individually rather than in batch
# Close other applications to free memory
# Consider using 64-bit Python if using 32-bit
# Use --no-backup option for very large files if necessary
```

#### Parameter Update Issues

**Issue: Parameter Not Found in DataMashup**

```
Error: Parameter 'BasePath' not found in DataMashup file
```

**Resolution:**
```bash
# Inspect DataMashup content to identify actual parameter names
python -c "
from update_pbix_parameter import PBIXParameterUpdater
updater = PBIXParameterUpdater(verbose=True)

# Get detailed parameter information
validation = updater.validate_input_file('SCRPA_Time_v2.pbix')
if validation['parameters_detected']:
    print('Parameters found in PBIX:')
    for param in validation['parameters_detected']:
        print(f'  Name: {param[\"name\"]}')
        print(f'  Value: {param[\"value\"]}')
        print(f'  Type: {param[\"type\"]}')
        print()
else:
    print('No parameters detected in PBIX file')
    print('Parameters may need to be created in Power BI Desktop')
"

# Use exact parameter name as it appears in the M-code
# Parameter names are case-sensitive
```

**Issue: Parameter Update Verification Failed**

```
Error: Parameter update verification failed. Expected: 'NewValue', Found: 'OldValue'
```

**Resolution:**
```bash
# Enable verbose logging to see update process details
python update_pbix_parameter.py \
    --input "SCRPA_Time_v2.pbix" \
    --output "debug_output.pbix" \
    --param "BasePath" \
    --value "C:\\Debug\\Path" \
    --validate-all \
    --verbose

# Check for special characters or encoding issues in the new value
# Ensure parameter value doesn't contain conflicting quote characters
# Try updating with a simple test value first
```

### Advanced Troubleshooting Techniques

#### Debugging Mode Execution

**Enable Maximum Diagnostic Output:**
```bash
# Set Python to output maximum debugging information
set PYTHONVERBOSE=1
set PYTHONDONTWRITEBYTECODE=1

# Execute with all debugging options
python -u -v update_pbix_parameter.py \
    --input "SCRPA_Time_v2.pbix" \
    --output "debug_output.pbix" \
    --param "BasePath" \
    --value "C:\\Debug\\Path" \
    --validate-all \
    --verbose \
    --summary-json "debug_summary.json" \
    > debug_output.log 2>&1
```

#### Network and Connectivity Issues

**OneDrive Synchronization Issues:**
```bash
# Check OneDrive sync status
powershell -Command "Get-ODStatus"

# Force OneDrive synchronization
powershell -Command "Start-Process -FilePath 'onedrive.exe' -ArgumentList '/sync'"

# Work with local copies if network issues persist
xcopy "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\*" "C:\LocalCopy\" /E /Y
```

#### Performance Optimization

**Optimize for Large File Processing:**
```python
# Create optimized processing script
with open('optimized_processing.py', 'w') as f:
    f.write('''
import gc
import os
from update_pbix_parameter import PBIXParameterUpdater

# Disable backup for large files to save space and time
os.environ['PBIX_DISABLE_BACKUP'] = '1'

# Process with memory management
updater = PBIXParameterUpdater(verbose=True)

# Force garbage collection
gc.collect()

# Your processing code here
result = updater.process_pbix_with_validation(
    "large_file.pbix", "output.pbix", "ParamName", "NewValue"
)

# Clean up
del updater
gc.collect()
''')
```

## Alternative Approaches

### PowerShell-Based Alternative

When Python-based solutions encounter insurmountable issues, a PowerShell-based alternative can provide similar functionality with different dependency requirements.

#### PowerShell Parameter Update Script

```powershell
# PowerShell alternative: Update-PBIXParameter.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$InputPath,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputPath,
    
    [Parameter(Mandatory=$true)]
    [string]$ParameterName,
    
    [Parameter(Mandatory=$true)]
    [string]$NewValue
)

function Update-PBIXParameter {
    param($InputPath, $OutputPath, $ParameterName, $NewValue)
    
    try {
        # Create temporary directory
        $TempDir = New-TemporaryFile | %{ rm $_; mkdir $_ }
        
        # Extract PBIX (ZIP) contents
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($InputPath, $TempDir)
        
        # Find DataMashup file
        $DataMashupPath = Join-Path $TempDir "DataMashup"
        
        if (Test-Path $DataMashupPath) {
            # Read DataMashup content
            $Content = Get-Content $DataMashupPath -Raw -Encoding UTF8
            
            # Update parameter using regex
            $Pattern = "let\s+$ParameterName\s*=\s*`"([^`"]*)`""
            $Replacement = "let $ParameterName = `"$NewValue`""
            
            $UpdatedContent = $Content -replace $Pattern, $Replacement
            
            # Write updated content back
            Set-Content -Path $DataMashupPath -Value $UpdatedContent -Encoding UTF8
            
            # Repackage PBIX
            [System.IO.Compression.ZipFile]::CreateFromDirectory($TempDir, $OutputPath)
            
            Write-Output "✅ Parameter update completed successfully"
            return $true
        } else {
            Write-Error "❌ DataMashup file not found in PBIX"
            return $false
        }
    }
    catch {
        Write-Error "❌ Error updating PBIX parameter: $($_.Exception.Message)"
        return $false
    }
    finally {
        # Cleanup temporary directory
        if (Test-Path $TempDir) {
            Remove-Item $TempDir -Recurse -Force
        }
    }
}

# Execute parameter update
$Success = Update-PBIXParameter -InputPath $InputPath -OutputPath $OutputPath -ParameterName $ParameterName -NewValue $NewValue

if ($Success) {
    exit 0
} else {
    exit 1
}
```

**PowerShell Execution Example:**
```powershell
.\Update-PBIXParameter.ps1 -InputPath "SCRPA_Time_v2.pbix" -OutputPath "SCRPA_Time_v2_updated.pbix" -ParameterName "BasePath" -NewValue "C:\New\Path"
```

### Manual Configuration Alternative

When automated solutions are not feasible, manual configuration through Power BI Desktop provides a reliable fallback approach.

#### Manual Configuration Process

**Step 1: Parameter Creation in Power BI Desktop**
1. Open PBIX file in Power BI Desktop
2. Navigate to **Home** → **Transform Data** → **Power Query Editor**
3. Select **Home** → **Manage Parameters** → **New Parameter**
4. Configure parameter properties:
   - **Name**: BasePath
   - **Type**: Text
   - **Current Value**: C:\Default\Path
   - **Suggested Values**: Any value

**Step 2: Parameter Integration**
1. In Power Query Editor, locate data source queries
2. Replace hard-coded paths with parameter references:
   ```
   // Before
   Source = Excel.Workbook(File.Contents("C:\Hard\Coded\Path\data.xlsx"))
   
   // After  
   Source = Excel.Workbook(File.Contents(BasePath & "\data.xlsx"))
   ```

**Step 3: Environment-Specific File Creation**
1. Save PBIX file with parameters configured for development
2. Use **File** → **Save As** to create environment-specific copies:
   - `SCRPA_Time_v2_Development.pbix`
   - `SCRPA_Time_v2_Production.pbix`
   - `SCRPA_Time_v2_Test.pbix`

**Step 4: Parameter Value Updates**
1. Open environment-specific PBIX file
2. Navigate to **Home** → **Transform Data** → **Power Query Editor**
3. Select **Home** → **Manage Parameters**
4. Update parameter values for specific environment
5. Select **Home** → **Close & Apply**
6. Save updated PBIX file

### Template-Based Approach

Create PBIX templates with placeholder parameters that can be easily modified through text-based configuration files.

#### Template Configuration System

**Template Structure:**
```
SCRPA_Templates/
├── base_template.pbix              # Base PBIX with placeholder parameters
├── environments/
│   ├── development.json           # Development parameter values
│   ├── production.json            # Production parameter values
│   └── test.json                  # Test parameter values
└── scripts/
    ├── apply_template.py          # Template application script
    └── validate_template.py       # Template validation script
```

**Environment Configuration File (development.json):**
```json
{
  "template_version": "1.0",
  "environment": "development",
  "parameters": {
    "BasePath": "C:\\Dev\\SCRPA_Data",
    "ServerName": "dev-sql-server",
    "DatabaseName": "SCRPA_Development",
    "ReportingDate": "2025-07-26",
    "UserContext": "development_user"
  },
  "output_settings": {
    "filename_suffix": "_dev",
    "output_directory": "environments/development/",
    "backup_enabled": true
  }
}
```

**Template Application Script (apply_template.py):**
```python
#!/usr/bin/env python3
import json
import shutil
from pathlib import Path
from update_pbix_parameter import PBIXParameterUpdater

def apply_template(template_path, config_path, output_path):
    """Apply environment configuration to PBIX template."""
    
    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Start with template file
    current_pbix = template_path
    
    # Apply each parameter sequentially
    updater = PBIXParameterUpdater(verbose=True)
    
    for i, (param_name, param_value) in enumerate(config['parameters'].items()):
        if i == 0:
            # First parameter: template → temp1
            temp_output = f"temp_{i}.pbix"
        else:
            # Subsequent parameters: temp(i-1) → temp(i)
            temp_output = f"temp_{i}.pbix"
        
        result = updater.process_pbix_with_validation(
            current_pbix, temp_output, param_name, param_value
        )
        
        if not result['success']:
            raise Exception(f"Failed to update parameter {param_name}")
        
        # Clean up previous temp file
        if i > 0:
            Path(current_pbix).unlink()
        
        current_pbix = temp_output
    
    # Move final result to output location
    shutil.move(current_pbix, output_path)
    
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python apply_template.py template.pbix config.json output.pbix")
        sys.exit(1)
    
    template_path, config_path, output_path = sys.argv[1:4]
    
    try:
        apply_template(template_path, config_path, output_path)
        print(f"✅ Template applied successfully: {output_path}")
    except Exception as e:
        print(f"❌ Template application failed: {e}")
        sys.exit(1)
```

### API-Based Integration Alternative

For enterprise environments with Power BI Premium, REST API-based parameter updates provide an alternative approach through the Power BI Service.

#### Power BI REST API Configuration

**API Authentication Setup:**
```python
# power_bi_api_config.py
import requests
import json
from datetime import datetime, timedelta

class PowerBIAPIManager:
    def __init__(self, tenant_id, client_id, client_secret):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires = None
    
    def get_access_token(self):
        """Obtain access token for Power BI REST API."""
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/token"
        
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'resource': 'https://analysis.windows.net/powerbi/api'
        }
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code == 200:
            token_info = response.json()
            self.access_token = token_info['access_token']
            self.token_expires = datetime.now() + timedelta(seconds=token_info['expires_in'])
            return True
        else:
            raise Exception(f"Failed to obtain access token: {response.text}")
    
    def update_dataset_parameters(self, workspace_id, dataset_id, parameters):
        """Update dataset parameters via REST API."""
        if not self.access_token or datetime.now() >= self.token_expires:
            self.get_access_token()
        
        api_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/Default.UpdateParameters"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        update_data = {
            'updateDetails': [
                {
                    'name': param_name,
                    'newValue': param_value
                }
                for param_name, param_value in parameters.items()
            ]
        }
        
        response = requests.post(api_url, headers=headers, json=update_data)
        
        if response.status_code == 200:
            return True
        else:
            raise Exception(f"Failed to update parameters: {response.text}")

# Usage example
if __name__ == "__main__":
    api_manager = PowerBIAPIManager(
        tenant_id="your-tenant-id",
        client_id="your-client-id", 
        client_secret="your-client-secret"
    )
    
    parameters = {
        "BasePath": "C:\\Production\\Data",
        "ServerName": "prod-server"
    }
    
    try:
        api_manager.update_dataset_parameters(
            workspace_id="your-workspace-id",
            dataset_id="your-dataset-id",
            parameters=parameters
        )
        print("✅ Parameters updated via Power BI REST API")
    except Exception as e:
        print(f"❌ API update failed: {e}")
```

### Configuration Management Alternative

Implement external configuration management using environment variables and configuration files that are read by Power BI reports at runtime.

#### External Configuration System

**Configuration File Structure:**
```
config/
├── global_config.json             # Global configuration settings
├── environments/
│   ├── dev_config.json            # Development environment
│   ├── prod_config.json           # Production environment
│   └── test_config.json           # Test environment
└── scripts/
    └── config_manager.py          # Configuration management utility
```

**Power BI M-Code Configuration Integration:**
```m
// In Power BI Power Query Editor
let
    // Read configuration from external file
    ConfigPath = "C:\Config\current_environment.json",
    ConfigFile = Json.Document(File.Contents(ConfigPath)),
    
    // Extract parameters from configuration
    BasePath = ConfigFile[BasePath],
    ServerName = ConfigFile[ServerName],
    DatabaseName = ConfigFile[DatabaseName],
    
    // Use configuration in data source connections
    Source = Sql.Database(ServerName, DatabaseName),
    DataTable = Source{[Schema="dbo",Item="CrimeData"]}[Data]
in
    DataTable
```

This alternative approach allows parameter updates through simple JSON file modifications without requiring PBIX file manipulation.

## Appendix

### Reference Commands Quick Guide

**Basic Parameter Update:**
```bash
python update_pbix_parameter.py -i input.pbix -o output.pbix -p ParamName -v "NewValue"
```

**Comprehensive Update:**
```bash
python update_pbix_parameter.py -i input.pbix -o output.pbix -p ParamName -v "NewValue" --validate-all --verbose --summary-json summary.json
```

**Batch Processing:**
```bash
python main_workflow.py --config config.json --environment production --verbose
```

**Testing:**
```bash
python test_pbix_update.py --pbix input.pbix --test-all --verbose
```

### File Structure Reference

```
SCRPA_Time_v2/
├── scripts/                    # Python scripts
├── pbix_files/                # PBIX files
├── config/                    # Configuration files
├── output/                    # Generated outputs
│   ├── updated_pbix/          # Updated PBIX files
│   ├── backups/               # Backup files
│   ├── logs/                  # Log files
│   └── summaries/             # JSON summaries
└── temp/                      # Temporary files
```

### Environment Variables Reference

```bash
SCRPA_BASE_PATH=C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2
SCRPA_OUTPUT_PATH=%SCRPA_BASE_PATH%\output
SCRPA_BACKUP_PATH=%SCRPA_BASE_PATH%\backups
PYTHONPATH=%SCRPA_BASE_PATH%\scripts;%PYTHONPATH%
```

### JSON Summary Schema Reference

```json
{
  "session_id": "string",
  "success": "boolean",
  "duration_seconds": "number",
  "system_environment": {
    "platform": "string",
    "python_version": "string",
    "working_directory": "string",
    "total_memory_gb": "number"
  },
  "input_file": {
    "path": "string",
    "exists": "boolean",
    "size_bytes": "number",
    "checksum_md5": "string"
  },
  "parameters": [
    {
      "name": "string",
      "original_value": "string", 
      "new_value": "string",
      "update_successful": "boolean"
    }
  ],
  "backups": [
    {
      "backup_id": "string",
      "original_file": "string",
      "backup_file": "string",
      "backup_successful": "boolean"
    }
  ],
  "errors": [
    {
      "error_id": "string",
      "timestamp": "string",
      "error_type": "string",
      "error_message": "string"
    }
  ]
}
```

This comprehensive README provides complete documentation for the SCRPA PBIX Configurator project, covering all aspects from initial setup through advanced troubleshooting and alternative implementation approaches.