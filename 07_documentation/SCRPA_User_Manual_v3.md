# SCRPA Time v3 - User Manual

## Table of Contents
1. [Getting Started](#getting-started)
2. [Running the Pipeline](#running-the-pipeline)
3. [Understanding Output](#understanding-output)
4. [Quality Monitoring](#quality-monitoring)
5. [PowerBI Integration](#powerbi-integration)
6. [Maintenance Tasks](#maintenance-tasks)
7. [FAQ](#faq)

## Getting Started

### System Requirements
- Windows 10/11 with administrative access
- Python 3.7 or higher
- Access to network drives (OneDrive - City of Hackensack)
- PowerBI Desktop (for report generation)

### Initial Setup Verification
1. Navigate to the project directory:
   ```
   C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\
   ```

2. Verify required folders exist:
   - `04_powerbi\` (input data)
   - `05_Exports\` (output files)
   - `backups\` (automatic backups)
   - `logs\` (processing logs)

3. Confirm the main script exists:
   ```
   SCRPA_Time_v3_Production_Pipeline.py
   ```

## Running the Pipeline

### Step 1: Prepare Input Data
1. Ensure fresh CAD and RMS files are in `04_powerbi\` folder
2. Files should follow naming convention:
   - `C08W31_*_cad_data_standardized.csv`
   - `C08W31_*_rms_data_standardized.csv`

### Step 2: Execute Pipeline
1. Open Command Prompt or PowerShell
2. Navigate to project directory:
   ```cmd
   cd "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
   ```
3. Run the pipeline:
   ```cmd
   python SCRPA_Time_v3_Production_Pipeline.py
   ```

### Step 3: Monitor Execution
Watch for the following output sequence:

```
=== SCRPA Production Deployment Pipeline ===
[INFO] Production pipeline initialized
[INFO] Using CAD file: ...\C08W31_*_cad_data_standardized.csv
[INFO] Using RMS file: ...\C08W31_*_rms_data_standardized.csv
[INFO] Input file validation passed
[INFO] Backup created: ...\backups\backup_YYYYMMDD_HHMMSS
[INFO] Loading data files
[INFO] Data quality validation: PASS
[INFO] Applying hybrid filtering
[WARNING] Validation rate 35.5% below threshold 70.0%  # Expected for current data
[INFO] Hybrid filtering completed: WARNING
[INFO] Creating PowerBI exports
[INFO] PowerBI exports created successfully
[INFO] Pipeline completed: SUCCESS
```

### Step 4: Verify Success
Look for the final summary:
```
Pipeline Status: SUCCESS
Processing Time: X.XX seconds
Data Quality: PASS
Validation Rate: XX.X%
PowerBI Ready: True
```

## Understanding Output

### Export Files Location
All output files are created in `05_Exports\` with timestamp naming:

#### 1. CAD Filtered Data
- **File**: `SCRPA_CAD_Filtered_YYYYMMDD_HHMMSS.csv`
- **Content**: All CAD incidents matching target crime types
- **Records**: Typically 100-120 records
- **Usage**: Primary incident data for reporting

#### 2. RMS Matched Data  
- **File**: `SCRPA_RMS_Matched_YYYYMMDD_HHMMSS.csv`
- **Content**: RMS cases that match CAD incidents
- **Records**: Typically 80-90 records
- **Usage**: Supplementary case details and NIBRS codes

#### 3. Processing Summary
- **File**: `SCRPA_Processing_Summary_YYYYMMDD_HHMMSS.json`
- **Content**: Metadata, statistics, and quality metrics
- **Usage**: Quality monitoring and audit trail

### File Naming Convention
Format: `SCRPA_[TYPE]_[DATE]_[TIME].csv`
- **TYPE**: CAD_Filtered, RMS_Matched, Processing_Summary
- **DATE**: YYYYMMDD (20250802)
- **TIME**: HHMMSS (234441)

Example: `SCRPA_CAD_Filtered_20250802_234441.csv`

## Quality Monitoring

### Key Metrics to Monitor

#### 1. Validation Rates by Crime Type
| Crime Type | Target Rate | Current Performance |
|------------|-------------|-------------------|
| Motor Vehicle Theft | 70%+ | 77.4% ✅ |
| Burglary - Auto | 50%+ | 57.7% ✅ |
| Robbery | 50%+ | 54.5% ✅ |
| Sexual Offenses | 40%+ | 23.5% ⚠️ |
| Burglary - Commercial | 40%+ | 0.0% ❌ |
| Burglary - Residence | 40%+ | 0.0% ❌ |

#### 2. Processing Performance
- **Processing Time**: Target < 5 seconds (Current: ~0.1 seconds ✅)
- **Data Quality**: Target PASS (Current: PASS ✅)
- **Overall Validation**: Target 70%+ (Current: 35.5% ⚠️)

#### 3. Data Completeness
- **Header Compliance**: Target 100% (Current: 100% ✅)
- **Record Completeness**: Target 80%+ (Current: 96.2% ✅)
- **Required Columns**: All present ✅

### Daily Quality Checks

#### Morning Verification (5 minutes)
1. Check for new log entries in `logs\scrpa_production_YYYYMMDD.log`
2. Verify no ERROR or FAIL messages
3. Confirm export files were generated overnight
4. Validate file timestamps are recent

#### Weekly Quality Review (15 minutes)
1. Review validation rate trends
2. Check for any declining performance
3. Verify backup files are being created
4. Assess overall system health

### Alert Thresholds
- **🔴 CRITICAL**: Processing fails or ERROR status
- **🟡 WARNING**: Validation rate below 70%
- **🟢 NORMAL**: All metrics within thresholds

## PowerBI Integration

### Connecting to Data Sources

#### 1. CAD Data Connection
1. Open PowerBI Desktop
2. Get Data → Text/CSV
3. Navigate to: `05_Exports\`
4. Select most recent: `SCRPA_CAD_Filtered_*.csv`
5. Verify data preview shows crime incidents
6. Click "Load"

#### 2. RMS Data Connection
1. Get Data → Text/CSV
2. Select most recent: `SCRPA_RMS_Matched_*.csv`
3. Verify NIBRS classifications are present
4. Click "Load"

### Data Refresh Procedures

#### Manual Refresh
1. Run SCRPA pipeline to generate new exports
2. In PowerBI: Home → Refresh
3. Verify data updated with new timestamps
4. Save PowerBI file

#### Automated Refresh (Advanced)
1. Publish to PowerBI Service
2. Configure scheduled refresh
3. Set data source credentials
4. Monitor refresh history

### Data Model Setup
1. Create relationship between CAD and RMS on `case_number`
2. Configure date tables using `incident_date`
3. Set up crime type categorization
4. Create calculated measures for validation rates

## Maintenance Tasks

### Daily Tasks (2 minutes)
- [ ] Check processing logs for errors
- [ ] Verify export files generated
- [ ] Confirm PowerBI data is current

### Weekly Tasks (15 minutes)
- [ ] Run pipeline with new data
- [ ] Review quality metrics
- [ ] Archive old export files (>30 days)
- [ ] Update PowerBI reports

### Monthly Tasks (30 minutes)
- [ ] Analyze performance trends
- [ ] Review validation rate patterns
- [ ] Clean up old backup files (>90 days)
- [ ] Update crime type patterns if needed

### Quarterly Tasks (1 hour)
- [ ] System performance review
- [ ] Documentation updates
- [ ] Training refresher for new staff
- [ ] Backup testing and validation

## FAQ

### Q: What do I do if the pipeline fails?
**A**: Check the log file for specific error messages. Common solutions:
1. Verify input files exist and are accessible
2. Ensure no files are locked/in use
3. Check disk space availability
4. Restart and try again

### Q: Why is the validation rate low?
**A**: The current 35.5% rate is expected due to data quality. Key factors:
- RMS data entry timing differences
- NIBRS classification variations
- Crime type pattern matching accuracy

### Q: How often should I run the pipeline?
**A**: Weekly for production reports, or as needed when new data arrives.

### Q: What if PowerBI shows old data?
**A**: 
1. Verify new export files were generated
2. Refresh PowerBI data sources
3. Check file paths in PowerBI connections
4. Confirm timestamp on data files

### Q: Can I modify the crime type patterns?
**A**: Yes, but requires technical knowledge. Contact system administrator for pattern updates.

### Q: What happens if I accidentally delete export files?
**A**: Re-run the pipeline to regenerate files. Original input data is backed up automatically.

### Q: How do I interpret the JSON summary file?
**A**: The summary contains metadata and statistics. Key sections:
- `processing_stats`: Performance metrics
- `validation_rates`: Crime-specific accuracy
- `crime_distribution`: Count and percentages
- `powerbi_integration`: Connection status

---

**Document Version**: 3.0  
**Last Updated**: August 2025  
**Review Schedule**: Monthly  
**Contact**: SCRPA System Administrator