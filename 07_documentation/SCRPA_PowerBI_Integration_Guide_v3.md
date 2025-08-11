# SCRPA Time v3 - PowerBI Integration Guide

## Table of Contents
1. [Overview](#overview)
2. [Data Source Setup](#data-source-setup)
3. [Data Model Configuration](#data-model-configuration)
4. [Report Development](#report-development)
5. [Automated Refresh](#automated-refresh)
6. [Performance Optimization](#performance-optimization)
7. [Troubleshooting](#troubleshooting)

## Overview

### Integration Architecture
```
SCRPA Pipeline → CSV Exports → PowerBI Desktop → PowerBI Service → Reports
```

### Key Features
- **Real-time data refresh** from automated pipeline exports
- **Snake_case compliant** column names for consistency
- **Metadata integration** with processing summary JSON
- **Quality monitoring** with validation rate tracking
- **Crime type analysis** with geographic mapping

### Data Sources Summary
| File Type | Purpose | Update Frequency | Records |
|-----------|---------|------------------|---------|
| SCRPA_CAD_Filtered_*.csv | Primary incident data | Weekly | ~114 |
| SCRPA_RMS_Matched_*.csv | Case details & NIBRS | Weekly | ~86 |
| SCRPA_Processing_Summary_*.json | Quality metrics | Weekly | Metadata |

## Data Source Setup

### Step 1: Initial Connection

#### Connect to CAD Data
1. Open PowerBI Desktop
2. **Home** → **Get Data** → **Text/CSV**
3. Navigate to: `C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\05_Exports\`
4. Select most recent: `SCRPA_CAD_Filtered_YYYYMMDD_HHMMSS.csv`
5. **Preview data**:
   ```
   case_number,incident,response_type,category_type,location,time_of_call,...
   25-000813,Motor Vehicle Theft - 2C:20-3,Routine,Criminal Incidents,...
   ```
6. Click **Load**

#### Connect to RMS Data
1. **Home** → **Get Data** → **Text/CSV**
2. Select most recent: `SCRPA_RMS_Matched_YYYYMMDD_HHMMSS.csv`
3. **Preview data**:
   ```
   case_number,incident_date,nibrs_classification,total_value_stolen,...
   25-000813,2025-01-03,240 = Theft of Motor Vehicle,,...
   ```
4. Click **Load**

### Step 2: Data Type Configuration

#### CAD Data Types
```
case_number: Text
incident: Text
response_type: Text
category_type: Text
location: Text
time_of_call: Date/Time
time_dispatched: Date/Time
time_spent_minutes: Decimal Number
grid: Text
post: Decimal Number
officer: Text
```

#### RMS Data Types
```
case_number: Text
incident_date: Date
nibrs_classification: Text
total_value_stolen: Decimal Number
squad: Text
officer_of_record: Text
vehicle_1: Text
vehicle_2: Text
```

### Step 3: Data Cleaning

#### CAD Data Transformations
```powerbi
// Remove null case numbers
= Table.SelectRows(#"Changed Type", each [case_number] <> null and [case_number] <> "")

// Standardize time formats
= Table.TransformColumns(#"Filtered Rows", {{"time_of_call", DateTime.From}})

// Clean location data
= Table.TransformColumns(#"Previous Step", {{"location", Text.Clean}})
```

#### RMS Data Transformations
```powerbi
// Parse NIBRS codes
= Table.AddColumn(#"Changed Type", "nibrs_code", each Text.BeforeDelimiter([nibrs_classification], " = "))

// Extract offense description
= Table.AddColumn(#"Added NIBRS Code", "offense_description", each Text.AfterDelimiter([nibrs_classification], " = "))

// Convert value stolen to number
= Table.TransformColumns(#"Previous Step", {{"total_value_stolen", Number.From}})
```

## Data Model Configuration

### Step 1: Create Relationships

#### Primary Relationship
```
CAD[case_number] ←→ RMS[case_number]
- Cardinality: One to One
- Cross filter direction: Both
- Make this relationship active: Yes
```

#### Verification Query
```dax
EVALUATE
SUMMARIZE(
    CAD,
    CAD[case_number],
    "RMS_Match", RELATED(RMS[case_number])
)
```

### Step 2: Create Date Table

#### Date Dimension
```dax
Date = 
ADDCOLUMNS(
    CALENDAR(DATE(2025,1,1), DATE(2025,12,31)),
    "Year", YEAR([Date]),
    "Month", MONTH([Date]),
    "MonthName", FORMAT([Date], "MMMM"),
    "Quarter", "Q" & QUARTER([Date]),
    "WeekDay", WEEKDAY([Date]),
    "WeekDayName", FORMAT([Date], "DDDD"),
    "IsWeekend", WEEKDAY([Date]) IN {1,7}
)
```

#### Connect to CAD Data
```
Date[Date] ←→ CAD[incident_date]
- Cardinality: One to Many
- Cross filter direction: Single
```

### Step 3: Create Calculated Columns

#### Crime Categories
```dax
Crime_Category = 
SWITCH(
    TRUE(),
    CONTAINSSTRING(CAD[incident], "Motor Vehicle Theft"), "Motor Vehicle Theft",
    CONTAINSSTRING(CAD[incident], "Robbery"), "Robbery", 
    CONTAINSSTRING(CAD[incident], "Burglary - Auto"), "Burglary - Auto",
    CONTAINSSTRING(CAD[incident], "Sexual"), "Sexual Offenses",
    CONTAINSSTRING(CAD[incident], "Burglary - Commercial"), "Burglary - Commercial",
    CONTAINSSTRING(CAD[incident], "Burglary - Residence"), "Burglary - Residence",
    "Other"
)
```

#### Response Time Categories
```dax
Response_Time_Category = 
SWITCH(
    TRUE(),
    CAD[time_response_minutes] <= 5, "Excellent (≤5 min)",
    CAD[time_response_minutes] <= 10, "Good (5-10 min)",
    CAD[time_response_minutes] <= 15, "Average (10-15 min)",
    CAD[time_response_minutes] <= 30, "Slow (15-30 min)",
    "Very Slow (>30 min)"
)
```

#### Case Status
```dax
Case_Status = 
IF(
    NOT(ISBLANK(RELATED(RMS[case_number]))),
    "Complete (CAD + RMS)",
    "CAD Only"
)
```

### Step 4: Create Measures

#### Key Performance Indicators
```dax
// Total Incidents
Total_Incidents = COUNTROWS(CAD)

// Cases with RMS Data
RMS_Matched_Cases = 
CALCULATE(
    COUNTROWS(CAD),
    NOT(ISBLANK(RELATED(RMS[case_number])))
)

// Validation Rate
Validation_Rate = 
DIVIDE([RMS_Matched_Cases], [Total_Incidents], 0) * 100

// Average Response Time
Avg_Response_Time = AVERAGE(CAD[time_response_minutes])

// Total Value Stolen
Total_Value_Stolen = SUM(RMS[total_value_stolen])
```

#### Time-based Measures
```dax
// This Week Incidents
This_Week_Incidents = 
CALCULATE(
    [Total_Incidents],
    DATESINPERIOD(Date[Date], TODAY(), -7, DAY)
)

// Last Week Incidents
Last_Week_Incidents = 
CALCULATE(
    [Total_Incidents],
    DATESINPERIOD(Date[Date], TODAY()-7, -7, DAY)
)

// Week over Week Change
WoW_Change = [This_Week_Incidents] - [Last_Week_Incidents]
```

## Report Development

### Page 1: Executive Dashboard

#### Key Visuals
1. **Card Visuals**: Total Incidents, Validation Rate, Avg Response Time
2. **Line Chart**: Incidents by Date
3. **Donut Chart**: Crime Type Distribution
4. **Map Visual**: Incidents by Location
5. **Table**: Top 10 Recent Incidents

#### Sample Layout
```
┌─────────────────────────────────────────────────────┐
│ [114]         [77.4%]        [8.5 min]              │
│ Total         Validation     Avg Response            │
│ Incidents     Rate          Time                     │
├─────────────────────────────────────────────────────┤
│ [Line Chart: Incidents by Date    ] [Donut: Crime ] │
│                                      Types        ] │
├─────────────────────────────────────────────────────┤
│ [Map: Geographic Distribution                     ] │
├─────────────────────────────────────────────────────┤
│ [Table: Recent Incidents                          ] │
└─────────────────────────────────────────────────────┘
```

### Page 2: Crime Analysis

#### Detailed Analysis Visuals
1. **Matrix**: Crime Type by Time Period
2. **Bar Chart**: Incidents by Grid/Post
3. **Scatter Plot**: Response Time vs Value Stolen
4. **Funnel Chart**: CAD to RMS Conversion

### Page 3: Quality Monitoring

#### Quality Metrics
1. **Gauge**: Validation Rate (Target: 70%)
2. **Column Chart**: Validation by Crime Type  
3. **Line Chart**: Quality Trends Over Time
4. **Table**: Data Quality Summary

#### Quality Measure Examples
```dax
// Validation Rate by Crime
Validation_by_Crime = 
CALCULATE(
    DIVIDE(
        COUNTROWS(FILTER(CAD, NOT(ISBLANK(RELATED(RMS[case_number]))))),
        COUNTROWS(CAD),
        0
    ) * 100,
    ALLEXCEPT(CAD, CAD[Crime_Category])
)

// Quality Status
Quality_Status = 
SWITCH(
    TRUE(),
    [Validation_Rate] >= 70, "Good",
    [Validation_Rate] >= 50, "Warning", 
    "Poor"
)
```

## Automated Refresh

### PowerBI Desktop Refresh

#### Manual Refresh Process
1. **Before opening PowerBI**:
   ```cmd
   # Run SCRPA pipeline to generate fresh data
   python SCRPA_Time_v3_Production_Pipeline.py
   ```

2. **In PowerBI Desktop**:
   - Home → Refresh
   - Wait for completion
   - Verify new data timestamps

#### Automated Refresh Script
```powershell
# PowerShell script for automated refresh
param(
    [string]$PBIXPath = "C:\Path\To\SCRPA_Report.pbix"
)

# Run SCRPA pipeline
Set-Location "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
python SCRPA_Time_v3_Production_Pipeline.py

# Open and refresh PowerBI file
Start-Process "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe" -ArgumentList $PBIXPath
# Manual refresh required in PowerBI Desktop
```

### PowerBI Service Refresh

#### Publishing to Service
1. **PowerBI Desktop**: File → Publish → PowerBI Service
2. **Select workspace**: Choose appropriate workspace
3. **Configure gateway**: Set up On-premises data gateway

#### Scheduled Refresh Setup
1. **PowerBI Service**: Go to dataset settings
2. **Data source credentials**: Configure file path credentials
3. **Schedule refresh**: Set to weekly/daily as needed
4. **Refresh history**: Monitor for failures

#### Gateway Configuration
```json
{
    "dataSourceType": "File",
    "connectionDetails": {
        "path": "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\05_Exports"
    },
    "credentialType": "Windows",
    "refreshSchedule": {
        "frequency": "Weekly",
        "days": ["Monday"],
        "time": "08:00"
    }
}
```

## Performance Optimization

### Data Model Optimization

#### 1. Column Optimization
```dax
// Remove unnecessary columns in PowerQuery
= Table.RemoveColumns(Source, {"cad_notes_cleaned", "cad_notes_username", "cad_notes_timestamp"})

// Create calculated columns only when needed
= Table.AddColumn(#"Previous Step", "Key_Fields_Only", each [case_number] & [incident])
```

#### 2. Relationship Optimization
- Use single direction filtering where possible
- Avoid bidirectional relationships unless necessary
- Create star schema with dimension tables

#### 3. DAX Optimization
```dax
// Use CALCULATE instead of FILTER when possible
Optimized_Measure = 
CALCULATE(
    COUNTROWS(CAD),
    CAD[Crime_Category] = "Motor Vehicle Theft"
)

// Instead of:
Slow_Measure = 
COUNTROWS(
    FILTER(CAD, CAD[Crime_Category] = "Motor Vehicle Theft")
)
```

### Report Performance

#### 1. Visual Optimization
- Limit visuals per page (max 10-12)
- Use appropriate visual types for data size
- Implement drill-through instead of large tables
- Use bookmarks for navigation

#### 2. Data Reduction
```dax
// Create summary tables for large datasets
Crime_Summary = 
SUMMARIZE(
    CAD,
    CAD[Crime_Category],
    Date[Month],
    "Total_Count", COUNTROWS(CAD),
    "Avg_Response", AVERAGE(CAD[time_response_minutes])
)
```

## Troubleshooting

### Common Connection Issues

#### Issue: "File not found"
**Solution**:
1. Verify file paths in Data Source Settings
2. Check OneDrive sync status
3. Ensure latest files exist in 05_Exports folder

#### Issue: "Data source error"  
**Solution**:
1. Update data source credentials
2. Check file permissions
3. Refresh data source connection

#### Issue: "Schema changes detected"
**Solution**:
1. Check export file column structure
2. Update PowerQuery transformations
3. Verify data types match expectations

### Performance Issues

#### Issue: Slow refresh times
**Solutions**:
1. Reduce data volume with filters
2. Optimize DAX calculations
3. Use incremental refresh for large datasets
4. Consider data model restructuring

#### Issue: Visual loading slowly
**Solutions**:
1. Limit visual complexity
2. Use drill-through for detailed views
3. Implement proper relationships
4. Cache frequently used calculations

### Data Validation

#### Verification Checks
```dax
// Check for data freshness
Data_Age_Days = 
DATEDIFF(
    MAX(CAD[time_of_call]),
    TODAY(),
    DAY
)

// Validate record counts
Record_Count_Check = 
"CAD: " & COUNTROWS(CAD) & " | RMS: " & COUNTROWS(RMS)

// Check validation rates
Quality_Check = 
IF(
    [Validation_Rate] < 50,
    "⚠️ Low quality data",
    "✅ Data quality acceptable"
)
```

---

**Document Version**: 3.0  
**Last Updated**: August 2025  
**PowerBI Version**: Compatible with Desktop & Service  
**Review Schedule**: Monthly