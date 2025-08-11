@echo off
chcp 65001 > nul

REM ===================================================================
REM Weekly Crime Report Automation - Hackensack Police Department
REM Author: R. Carucci
REM Purpose: Launch crime report automation with Option B Chart Export
REM Last Updated: 2025-05-27
REM ===================================================================

echo [%date% %time%] Starting Weekly Crime Report Automation...

REM Set paths with proper error checking - NO QUOTES in directory variables
set PROPY=C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat
set SCRIPT=C:\Users\carucci_r\OneDrive - City of Hackensack\_Hackensack_Data_Repository\GIS_Tools\Scripts\ScriptsTimeSCRPATemplet\crime_report_tool\main.py
set LOG_DIR=C:\Users\carucci_r\Documents\SCRPA_logs

REM Build log filename with proper quoting
set LOG_FILE=%LOG_DIR%\crime_report_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%.log

REM Create log directory if it doesn't exist
if not exist "%LOG_DIR%" (
    echo Creating log directory: %LOG_DIR%
    mkdir "%LOG_DIR%"
)

REM Verify that propy.bat exists
if not exist "%PROPY%" (
    echo ERROR: propy.bat not found at %PROPY%
    echo Please verify ArcGIS Pro installation
    pause
    exit /b 1
)

REM Verify that the Python script exists
if not exist "%SCRIPT%" (
    echo ERROR: Python script not found at %SCRIPT%
    echo Please verify script path
    pause
    exit /b 1
)

echo Running Crime Report Script: "%SCRIPT%"
echo Arguments: report=true email=true archive=false archive_days=30 dry_run=false date=2025_05_27
echo Log file: "%LOG_FILE%"
echo.

REM Run the script with proper error handling and logging
call "%PROPY%" "%SCRIPT%" true true false 30 false 2025_05_27 > "%LOG_FILE%" 2>&1

REM Check the exit code
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] SUCCESS: Crime report automation completed successfully
    echo.
    echo === RECENT LOG OUTPUT ===
    REM Show last 20 lines using Windows-native commands
    for /f "tokens=3" %%f in ('find /c /v "" "%LOG_FILE%"') do set nbLines=%%f
    set /a nbSkippedLines=!nbLines!-20
    if !nbSkippedLines! LSS 0 set nbSkippedLines=0
    for /f "usebackq skip=!nbSkippedLines! delims=" %%d in ("%LOG_FILE%") do echo %%d
) else (
    echo [%date% %time%] ERROR: Crime report automation failed with exit code %ERRORLEVEL%
    echo.
    echo === ERROR LOG OUTPUT ===
    type "%LOG_FILE%" | findstr /C:"[ERROR]" /C:"Exception" /C:"Traceback"
)

echo.
echo === FULL LOG OUTPUT ===
type "%LOG_FILE%"

echo.
echo [%date% %time%] Crime report automation finished.
echo Log saved to: "%LOG_FILE%"
echo.
echo Press any key to close.
pause
