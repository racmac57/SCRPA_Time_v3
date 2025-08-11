# SCRPA Time v3 - Troubleshooting Guide

## Table of Contents
1. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
2. [Common Error Scenarios](#common-error-scenarios)
3. [Performance Issues](#performance-issues)
4. [Data Quality Problems](#data-quality-problems)
5. [PowerBI Integration Issues](#powerbi-integration-issues)
6. [System Recovery Procedures](#system-recovery-procedures)
7. [Contact Information](#contact-information)

## Quick Diagnostic Checklist

### Before Troubleshooting
Run this 2-minute checklist to identify the problem category:

- [ ] **Files Exist**: Verify input files in `04_powerbi\` directory
- [ ] **Permissions**: Ensure write access to `05_Exports\` and `logs\` directories  
- [ ] **Disk Space**: Check available space (minimum 1GB recommended)
- [ ] **Python**: Confirm Python 3.7+ is installed and accessible
- [ ] **Network**: Verify OneDrive sync is working
- [ ] **Recent Changes**: Note any recent system or data changes

### Quick Health Check
```cmd
# Navigate to project directory
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"

# Check if main script exists
dir SCRPA_Time_v3_Production_Pipeline.py

# Check latest log for errors
type logs\scrpa_production_*.log | findstr "ERROR"
```

## Common Error Scenarios

### 1. File Not Found Errors

#### Error Message
```
FileNotFoundError: Input files not found: CAD=0, RMS=0
```

#### Cause
- Missing input files in `04_powerbi\` directory
- Incorrect file naming convention
- OneDrive sync issues

#### Solution
```cmd
# Check for input files
dir "04_powerbi\C08W31_*_cad_data_standardized.csv"
dir "04_powerbi\C08W31_*_rms_data_standardized.csv"

# If files missing:
1. Verify OneDrive sync status
2. Check source data location
3. Confirm file naming matches pattern: C08W31_*_data_standardized.csv
4. Ensure files are not corrupted or locked
```

#### Prevention
- Set up automated file monitoring
- Create file validation checklist
- Establish backup data sources

### 2. Permission Denied Errors

#### Error Message
```
PermissionError: [Errno 13] Permission denied: '05_Exports\SCRPA_CAD_Filtered_*.csv'
```

#### Cause
- Files locked by PowerBI or Excel
- Insufficient user permissions
- Antivirus software blocking access

#### Solution
```cmd
# Close all applications using the files
1. Close PowerBI Desktop
2. Close Excel/CSV viewers
3. Check Task Manager for background processes

# Verify permissions
1. Right-click on 05_Exports folder
2. Properties → Security
3. Ensure user has "Full Control"
4. Apply to all subfolders and files
```

#### Prevention
- Close PowerBI before running pipeline
- Run pipeline during off-hours
- Use file locking detection

### 3. Python/Library Errors

#### Error Message
```
ModuleNotFoundError: No module named 'pandas'
ImportError: cannot import name 'DataFrame' from 'pandas'
```

#### Cause
- Missing Python libraries
- Python version incompatibility
- Virtual environment issues

#### Solution
```cmd
# Install missing libraries
pip install pandas numpy

# Check Python version
python --version  # Should be 3.7+

# Verify libraries
python -c "import pandas; print(pandas.__version__)"
```

#### Alternative Solution
```cmd
# Use specific Python installation
"C:\Program Files\Python39\python.exe" SCRPA_Time_v3_Production_Pipeline.py
```

### 4. Data Validation Failures

#### Error Message
```
ValueError: Data quality validation failed: {'overall_status': 'FAIL'}
```

#### Cause
- Missing required columns
- Corrupted data files
- Header compliance issues

#### Solution
1. **Check file structure**:
   ```cmd
   # View first few lines of CAD file
   head -5 "04_powerbi\C08W31_*_cad_data_standardized.csv"
   ```

2. **Verify required columns**:
   - CAD: `case_number`, `incident`, `response_type`, `category_type`
   - RMS: `case_number`, `incident_type`, `nibrs_classification`

3. **Fix header issues**:
   - Ensure all headers are lowercase
   - Replace spaces with underscores
   - Remove special characters

### 5. Low Validation Rate Warnings

#### Warning Message
```
WARNING - Validation rate 35.5% below threshold 70.0%
```

#### Cause
- Normal for current data quality
- Timing differences between CAD and RMS
- Pattern matching limitations

#### Assessment
```python
# Review validation breakdown by crime type:
{
    "Motor Vehicle Theft": 77.4%,    # ✅ Good
    "Burglary - Auto": 57.7%,        # ⚠️ Acceptable  
    "Robbery": 54.5%,                # ⚠️ Acceptable
    "Sexual": 23.5%,                 # ❌ Low
    "Burglary - Commercial": 0.0%,   # ❌ No matches
    "Burglary - Residence": 0.0%     # ❌ No matches
}
```

#### Actions
- **Immediate**: Continue processing (warning is expected)
- **Short-term**: Monitor trends for declining rates
- **Long-term**: Work with data providers to improve quality

## Performance Issues

### 1. Slow Processing (>5 seconds)

#### Symptoms
- Processing time exceeds normal range
- System appears frozen
- High CPU/memory usage

#### Diagnostic Steps
```cmd
# Check system resources
tasklist /fi "imagename eq python.exe"

# Monitor file sizes
dir /s "04_powerbi\*.csv"

# Check disk space
dir C:\ | findstr "bytes free"
```

#### Solutions
1. **Large Files**: Process in smaller chunks
2. **Memory Issues**: Restart Python process
3. **Disk Space**: Clean temporary files
4. **Network**: Check OneDrive sync speed

### 2. Memory Errors

#### Error Message
```
MemoryError: Unable to allocate array
```

#### Solutions
```python
# For large datasets, modify the pipeline to process in chunks
chunk_size = 1000  # Reduce if memory issues persist
for chunk in pd.read_csv(file_path, chunksize=chunk_size):
    process_chunk(chunk)
```

## Data Quality Problems

### 1. Missing Case Numbers

#### Problem
CAD and RMS files have mismatched case numbers

#### Investigation
```python
# Check case number overlap
cad_cases = set(cad_df['case_number'])
rms_cases = set(rms_df['case_number'])
missing_in_rms = cad_cases - rms_cases
missing_in_cad = rms_cases - cad_cases

print(f"CAD cases missing in RMS: {len(missing_in_rms)}")
print(f"RMS cases missing in CAD: {len(missing_in_cad)}")
```

#### Actions
1. Contact data providers about timing differences
2. Adjust processing window to allow for delays
3. Document expected mismatch rates

### 2. Invalid Date Formats

#### Problem
Date fields contain inconsistent formats

#### Solution
```python
# Standardize date parsing
def parse_date_flexible(date_str):
    formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y']
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except:
            continue
    return pd.NaT
```

### 3. Crime Type Classification Issues

#### Problem
New crime types not recognized by patterns

#### Investigation
```python
# Find unmatched incidents
all_incidents = cad_df['incident'].value_counts()
unmatched = all_incidents[~all_incidents.index.str.contains('|'.join(all_patterns))]
print("Unmatched incident types:")
print(unmatched.head(10))
```

#### Solution
Add new patterns to crime_patterns dictionary

## PowerBI Integration Issues

### 1. Data Not Refreshing

#### Problem
PowerBI shows old data after pipeline run

#### Solution Steps
1. **Verify new files created**:
   ```cmd
   dir /OD "05_Exports\SCRPA_*_*.csv"
   ```

2. **Check PowerBI data source paths**:
   - File → Options → Data source settings
   - Verify paths point to correct directory
   - Update to use latest file timestamps

3. **Manual refresh**:
   - Home → Refresh
   - Wait for completion message

### 2. Connection Errors

#### Error Message
```
We couldn't refresh the data source because of connection issues
```

#### Solutions
1. **File permissions**: Ensure PowerBI can access files
2. **File locks**: Close files in other applications  
3. **Path issues**: Use UNC paths instead of mapped drives
4. **OneDrive sync**: Verify files are synced locally

### 3. Schema Changes

#### Problem
PowerBI reports column type errors

#### Solution
1. **Check export structure**:
   ```python
   df.dtypes  # Verify column types
   df.head()  # Check first few rows
   ```

2. **PowerBI fixes**:
   - Transform data → Detect data types
   - Manually set column types
   - Remove and re-add data source

## System Recovery Procedures

### 1. Complete System Failure

#### Emergency Steps
1. **Check backups**:
   ```cmd
   dir /OD "backups\backup_*"
   ```

2. **Restore from backup**:
   ```cmd
   copy "backups\backup_YYYYMMDD_HHMMSS\*" "04_powerbi\"
   ```

3. **Re-run pipeline**:
   ```cmd
   python SCRPA_Time_v3_Production_Pipeline.py
   ```

### 2. Corrupted Export Files

#### Recovery Steps
1. **Delete corrupted files**:
   ```cmd
   del "05_Exports\SCRPA_*_corrupted_timestamp.*"
   ```

2. **Re-run pipeline with backup data**:
   ```cmd
   python SCRPA_Time_v3_Production_Pipeline.py
   ```

3. **Verify output integrity**:
   ```cmd
   # Check file sizes and record counts
   wc -l "05_Exports\SCRPA_*.csv"
   ```

### 3. Log File Analysis

#### Error Investigation
```cmd
# Search for specific errors
findstr /i "error\|fail\|exception" "logs\scrpa_production_*.log"

# View recent log entries
tail -50 "logs\scrpa_production_*.log"

# Check processing times
findstr "processing time" "logs\scrpa_production_*.log"
```

## Escalation Procedures

### Level 1: Self-Service (15 minutes)
- Run quick diagnostic checklist
- Try common solutions
- Check recent log entries

### Level 2: Technical Support (30 minutes)
- Contact IT department with error logs
- Provide system information and recent changes
- Include specific error messages and timestamps

### Level 3: Developer Support (1 hour)
- Contact SCRPA development team
- Provide complete log files and data samples
- Schedule troubleshooting session

## Contact Information

### Internal Support
- **Primary Contact**: SCRPA System Administrator
- **Email**: scrpa-support@hackensack.org
- **Phone**: (201) 646-xxxx
- **Hours**: Monday-Friday, 8:00 AM - 5:00 PM

### Technical Support
- **IT Helpdesk**: (201) 646-xxxx
- **OneDrive Support**: IT Department
- **PowerBI Support**: Business Intelligence Team

### Emergency Contacts
- **After Hours**: IT Emergency Line
- **Weekend Support**: On-call administrator
- **Critical Issues**: Police Department Supervisor

---

**Document Version**: 3.0  
**Last Updated**: August 2025  
**Review Schedule**: Monthly  
**Emergency Update Process**: Contact system administrator immediately