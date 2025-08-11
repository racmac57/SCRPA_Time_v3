@echo off
REM // 🕒 2025-01-27-22-55-00
REM // SCRPA_Analysis/run_report_enhanced.bat
REM // Author: R. A. Carucci
REM // Purpose: Enhanced SCRPA report runner with full debug capabilities

setlocal EnableDelayedExpansion

echo ==========================================
echo SCRPA Crime Analysis Report Generator
echo Enhanced Production Version
echo ==========================================
echo.

REM Set working directory
set "SCRIPT_DIR=C:\Users\carucci_r\SCRPA_LAPTOP\scripts"
set "PROJECT_DIR=C:\Users\carucci_r\SCRPA_LAPTOP"

REM Change to scripts directory
cd /d "%SCRIPT_DIR%"

REM Validate environment
echo [INFO] Validating environment...
if not exist "%SCRIPT_DIR%\main.py" (
    echo [ERROR] main.py not found in: %SCRIPT_DIR%
    echo [ERROR] Please ensure all scripts are in the correct location
    pause
    exit /b 1
)

REM Set ArcGIS Python path (hardcoded for reliability)
set "PYTHON_PATH=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
if not exist "%PYTHON_PATH%" (
    echo [ERROR] ArcGIS Pro Python not found at: %PYTHON_PATH%
    echo [ERROR] Please check ArcGIS Pro installation
    pause
    exit /b 1
)

echo [OK] Environment validated
echo.

REM Get current date for default
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=!dt:~0,4!" & set "MM=!dt:~4,2!" & set "DD=!dt:~6,2!"
set "TODAY_DATE=!YY!_!MM!_!DD!"

REM Interactive menu
echo Select operation:
echo.
echo [1] Full Production Run (Maps + Charts + Tables)
echo [2] Maps Only Export
echo [3] Charts Only Export  
echo [4] Tables Only Export
echo [5] Debug Mode (Full Validation)
echo [6] Quick Validation Only
echo [7] Test with Sample Date (2025_06_03)
echo.
set /p operation=Enter choice (1-7): 

echo.
echo Enter report date (YYYY_MM_DD format):
echo Examples: 2025_06_24, %TODAY_DATE%
echo.
set /p report_date=Date (or press Enter for today): 

REM Use today's date if none provided
if "%report_date%"=="" (
    set "report_date=%TODAY_DATE%"
    echo [INFO] Using today's date: !report_date!
)

REM Create log directory
set "LOG_DIR=%PROJECT_DIR%\logs\!report_date!"
if not exist "!LOG_DIR!" mkdir "!LOG_DIR!"

set "RUN_LOG=!LOG_DIR!\run.log"
set "DEBUG_LOG=!LOG_DIR!\debug.log"

echo.
echo ==========================================
echo EXECUTION STARTING
echo ==========================================
echo Date: %report_date%
echo Operation: %operation%
echo Log Directory: !LOG_DIR!
echo ==========================================

REM Record start time
set startTime=%time%
echo [%date% %time%] SCRPA Report Generation Started > "!RUN_LOG!"
echo Target Date: %report_date% >> "!RUN_LOG!"

REM Execute based on selection
if "%operation%"=="1" (
    echo [INFO] Running FULL PRODUCTION MODE...
    echo Command: "%PYTHON_PATH%" main.py true true true 30 false %report_date%
    call "%PYTHON_PATH%" main.py true true true 30 false %report_date% > "!DEBUG_LOG!" 2>&1
) else if "%operation%"=="2" (
    echo [INFO] Running MAPS ONLY...
    echo Command: "%PYTHON_PATH%" main.py true false false 30 false %report_date%
    call "%PYTHON_PATH%" main.py true false false 30 false %report_date% > "!DEBUG_LOG!" 2>&1
) else if "%operation%"=="3" (
    echo [INFO] Running CHARTS ONLY...
    echo Command: "%PYTHON_PATH%" main.py false true false 30 false %report_date%
    call "%PYTHON_PATH%" main.py false true false 30 false %report_date% > "!DEBUG_LOG!" 2>&1
) else if "%operation%"=="4" (
    echo [INFO] Running TABLES ONLY...
    echo Command: "%PYTHON_PATH%" main.py false false true 30 false %report_date%
    call "%PYTHON_PATH%" main.py false false true 30 false %report_date% > "!DEBUG_LOG!" 2>&1
) else if "%operation%"=="5" (
    echo [INFO] Running DEBUG MODE...
    echo Command: "%PYTHON_PATH%" main.py --debug %report_date%
    call "%PYTHON_PATH%" main.py --debug %report_date% > "!DEBUG_LOG!" 2>&1
) else if "%operation%"=="6" (
    echo [INFO] Running VALIDATION ONLY...
    echo Command: "%PYTHON_PATH%" main.py --validate
    call "%PYTHON_PATH%" main.py --validate > "!DEBUG_LOG!" 2>&1
) else if "%operation%"=="7" (
    echo [INFO] Running TEST MODE with sample date...
    echo Command: "%PYTHON_PATH%" main.py true true true 30 false 2025_06_03
    call "%PYTHON_PATH%" main.py true true true 30 false 2025_06_03 > "!DEBUG_LOG!" 2>&1
) else (
    echo [ERROR] Invalid selection: %operation%
    echo [INFO] Defaulting to full production run...
    call "%PYTHON_PATH%" main.py true true true 30 false %report_date% > "!DEBUG_LOG!" 2>&1
)

REM Calculate runtime
set endTime=%ti