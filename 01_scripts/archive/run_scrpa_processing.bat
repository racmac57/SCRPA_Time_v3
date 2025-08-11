@echo off
REM 🕒 2025-07-27-19-XX-XX
REM SCRPA_Time_v2\run_scrpa_processing.bat
REM Author: R. A. Carucci
REM Purpose: Interactive execution of SCRPA pipeline with full logging

setlocal enabledelayedexpansion

:: ——————————————————————————————
:: Configuration
:: ——————————————————————————————
set "PROJECT_DIR=C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
set "SCRIPTS_DIR=%PROJECT_DIR%\01_scripts"
set "LOG_DIR=%PROJECT_DIR%\03_output\logs"
set "OUTPUT_FILE=%PROJECT_DIR%\04_powerbi\enhanced_scrpa_data.csv"

:: Ensure log directory exists
if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
)

:: ——————————————————————————————
:: Mode Selection Menu
:: ——————————————————————————————
echo.
echo ==========================================
echo    SCRPA Data Processing Pipeline
echo    Select processing mode:
echo      1) Test Mode      - Component validation only
echo      2) Validate Mode  - Data validation only
echo      3) Full Processing Mode - Complete pipeline
echo ==========================================
set /p "CHOICE=Enter your choice (1-3): "

if "%CHOICE%"=="1" (
    set "MODE=test"
) else if "%CHOICE%"=="2" (
    set "MODE=validate"
) else (
    set "MODE=process"
)

echo.
echo Selected mode: %MODE%
echo.

:: ——————————————————————————————
:: Build timestamped log filename
:: ——————————————————————————————
for /f "tokens=1-4 delims=:/ " %%a in ("%date% %time%") do (
    set "MM=%%a" & set "DD=%%b" & set "YYYY=%%c"
    set "HH=%%d" & set "Min=%%e" & set "Sec=%%f"
)
set "TIMESTAMP=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
set "LOG_FILE=%LOG_DIR%\master_processing_%TIMESTAMP%.log"

echo Logging to: %LOG_FILE%
echo.

:: ——————————————————————————————
:: Execute the Python Processor
:: ——————————————————————————————
cd /d "%SCRIPTS_DIR%"

where python >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found in PATH. Please install Python 3.x and add to PATH.
    pause
    exit /b 1
)

echo ▶ Running %MODE% mode...
python master_scrpa_processor.py -m %MODE% -p "%PROJECT_DIR%" > "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Processing failed with code %ERRORLEVEL%.
    echo 🔍 Check logs for details at: %LOG_DIR%\
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ✅ Processing completed successfully.
echo    Output CSV: %OUTPUT_FILE%
echo    Log file:   %LOG_FILE%
pause
