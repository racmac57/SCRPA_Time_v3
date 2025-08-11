@echo off
REM 🕒 2025-06-25-18-30-00
REM SCRPA Crime Analysis/run_complete_scrpa.bat
REM Author: R. A. Carucci
REM Purpose: Complete SCRPA report generation with enhanced charts and maps

echo ====================================
echo    SCRPA COMPLETE REPORT GENERATOR
echo    Hackensack Police Department
echo ====================================
echo.

REM Set paths - UPDATE THESE TO MATCH YOUR SYSTEM
set INPUT_CSV="C:\Users\carucci_r\SCRPA_LAPTOP\projects\data\CAD_data_final.csv"
set OUTPUT_DIR="C:\Users\carucci_r\SCRPA_LAPTOP\projects\output"
set SCRIPT_DIR="C:\Users\carucci_r\SCRPA_LAPTOP\projects"

REM Create timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%_%MM%_%DD%_%HH%_%Min%_%Sec%"

echo Report Generation Started: %timestamp%
echo.

REM Create output directories
if not exist %OUTPUT_DIR% mkdir %OUTPUT_DIR%
if not exist "%OUTPUT_DIR%\7day" mkdir "%OUTPUT_DIR%\7day"
if not exist "%OUTPUT_DIR%\28day" mkdir "%OUTPUT_DIR%\28day"
if not exist "%OUTPUT_DIR%\ytd" mkdir "%OUTPUT_DIR%\ytd"

echo ====================================
echo    GENERATING 7-DAY REPORTS
echo ====================================

echo [1/6] Creating 7-Day enhanced charts...
python "%SCRIPT_DIR%\enhanced_chart_export.py" %INPUT_CSV% "%OUTPUT_DIR%\7day" "7Day"
if %errorlevel% neq 0 (
    echo ERROR: 7-Day charts failed
    pause
    exit /b 1
)

echo [2/6] Creating 7-Day professional map...
python "%SCRIPT_DIR%\enhanced_map_export.py" %INPUT_CSV% "%OUTPUT_DIR%\7day" "7Day"
if %errorlevel% neq 0 (
    echo ERROR: 7-Day map failed
    pause
    exit /b 1
)

echo ====================================
echo    GENERATING 28-DAY REPORTS  
echo ====================================

echo [3/6] Creating 28-Day enhanced charts...
python "%SCRIPT_DIR%\enhanced_chart_export.py" %INPUT_CSV% "%OUTPUT_DIR%\28day" "28Day"
if %errorlevel% neq 0 (
    echo ERROR: 28-Day charts failed
    pause
    exit /b 1
)

echo [4/6] Creating 28-Day professional map...
python "%SCRIPT_DIR%\enhanced_map_export.py" %INPUT_CSV% "%OUTPUT_DIR%\28day" "28Day"
if %errorlevel% neq 0 (
    echo ERROR: 28-Day map failed
    pause
    exit /b 1
)

echo ====================================
echo    GENERATING YTD REPORTS
echo ====================================

echo [5/6] Creating YTD enhanced charts...
python "%SCRIPT_DIR%\enhanced_chart_export.py" %INPUT_CSV% "%OUTPUT_DIR%\ytd" "YTD"
if %errorlevel% neq 0 (
    echo ERROR: YTD charts failed
    pause
    exit /b 1
)

echo [6/6] Creating YTD professional map...
python "%SCRIPT_DIR%\enhanced_map_export.py" %INPUT_CSV% "%OUTPUT_DIR%\ytd" "YTD"
if %errorlevel% neq 0 (
    echo ERROR: YTD map failed
    pause
    exit /b 1
)

echo ====================================
echo    GENERATING SUMMARY REPORT
echo ====================================

echo Creating executive summary...
python -c "
import pandas as pd
from datetime import datetime

# Load data
df = pd.read_csv(r'%INPUT_CSV%')

# Generate summary
summary = f'''
HACKENSACK POLICE DEPARTMENT
SCRPA Crime Analysis Executive Summary
Generated: {datetime.now().strftime('%%B %%d, %%Y at %%I:%%M %%p')}

TOTAL INCIDENTS: {len(df)}

CYCLE BREAKDOWN:
- 7-Day Period: {len(df[df['Cycle'] == '7-Day'])} incidents
- 28-Day Period: {len(df[df['Cycle'] == '28-Day'])} incidents  
- Year-to-Date: {len(df[df['Cycle'] == 'YTD'])} incidents

ZONE DISTRIBUTION:
'''

zone_dist = df[df['PDZone'].notna()]['PDZone'].value_counts().sort_index()
for zone, count in zone_dist.items():
    summary += f'- Zone {int(zone)}: {count} incidents\n'

summary += f'''

TOP CRIME TYPES:
'''
crime_dist = df['Incident'].value_counts().head(5)
for crime, count in crime_dist.items():
    summary += f'- {crime[:40]}: {count}\n'

summary += f'''

FILES GENERATED:
- Enhanced charts with time-of-day analysis
- Professional maps with basemaps and legends  
- High-resolution PNG and PDF exports
- Zone, time, incident, and daily pattern analysis

Analyst: R. A. Carucci
Principal Analyst, Hackensack Police Department
'''

with open(r'%OUTPUT_DIR%\Executive_Summary.txt', 'w') as f:
    f.write(summary)
    
print('Executive summary created')
"

echo ====================================
echo    REPORT GENERATION COMPLETE!
echo ====================================
echo.
echo Files generated in: %OUTPUT_DIR%
echo.
echo 7-Day Reports: %OUTPUT_DIR%\7day\
echo 28-Day Reports: %OUTPUT_DIR%\28day\
echo YTD Reports: %OUTPUT_DIR%\ytd\
echo Summary: %OUTPUT_DIR%\Executive_Summary.txt
echo.
echo Report includes:
echo - Time-of-day analysis charts
echo - Professional maps with basemaps
echo - Zone distribution analysis  
echo - Daily pattern analysis
echo - Crime type breakdowns
echo - High-resolution exports
echo.
echo Generation completed at: %time%
echo.
pause