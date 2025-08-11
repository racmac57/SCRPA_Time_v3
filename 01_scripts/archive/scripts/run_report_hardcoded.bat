@REM 🕒 2025-07-01-14-30-00
@REM SCRPA_LAPTOP/run_report_hardcoded.bat
@REM Author: R. A. Carucci
@REM Purpose: Executes main.py, logs runtime, updates folder timestamp, opens report folder

@echo off
setlocal EnableDelayedExpansion

:: === Hardcoded ArcGIS Python Path ===
set "PYTHON_PATH=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
echo Detected ArcGIS Python manually: "!PYTHON_PATH!"

:: === Prompt for Date Input ===
set /p custom_date=Enter custom date (YYYY_MM_DD or 'today', 'yesterday', 'tomorrow'): 

:: === Handle special date keywords ===
if /i "!custom_date!"=="today" (
    for /f "tokens=1-3 delims=/" %%a in ('date /t') do (
        set "today_date=%%c_%%a_%%b"
    )
    set "custom_date=!today_date!"
    echo [INFO] Using today's date: !custom_date!
)

if /i "!custom_date!"=="yesterday" (
    powershell -Command "(Get-Date).AddDays(-1).ToString('yyyy_MM_dd')" > temp_date.txt
    set /p custom_date=<temp_date.txt
    del temp_date.txt
    echo [INFO] Using yesterday's date: !custom_date!
)

if /i "!custom_date!"=="tomorrow" (
    powershell -Command "(Get-Date).AddDays(1).ToString('yyyy_MM_dd')" > temp_date.txt
    set /p custom_date=<temp_date.txt
    del temp_date.txt
    echo [INFO] Using tomorrow's date: !custom_date!
)

:: === Normalize hyphenated input ===
echo %custom_date% | find "-" >nul
if !errorlevel! == 0 (
    set "custom_date=%custom_date:-=_%"
    echo [INFO] Normalized dash-separated date to: !custom_date!
)

:: === Debug: Show values ===
echo [DEBUG] custom_date=!custom_date!
echo Press any key to continue . . .
pause

:: === Locate main.py ===
echo Searching for main.py...
for /f "delims=" %%f in ('powershell -nologo -command "Get-ChildItem -Recurse -Filter main.py | Select-Object -First 1 | %% { $_.DirectoryName }"') do (
    set "SCRIPT_DIR=%%f"
)

if not defined SCRIPT_DIR (
    echo [ERROR] Could not locate main.py
    pause
    exit /b 1
)

echo Found main.py in: !SCRIPT_DIR!

:: === Log File Setup ===
set "LOG_DIR=%~dp0logs\!custom_date!"
if not exist "!LOG_DIR!" mkdir "!LOG_DIR!"
set "DEBUG_LOG=!LOG_DIR!\debug.log"
set "RUN_LOG=!LOG_DIR!\run.log"

:: === Execute Python Script ===
set startTime=%time%
echo Running: "!PYTHON_PATH!" "!SCRIPT_DIR!\main.py" true true false 30 false "!custom_date!"
echo --- [%date% %time%] START --- >"!RUN_LOG!"

call "!PYTHON_PATH!" "!SCRIPT_DIR!\main.py" true true false 30 false "!custom_date!" ^>"!DEBUG_LOG!" 2^>^&1

:: === Runtime Report ===
set endTime=%time%

for /f "tokens=1-4 delims=:.," %%a in ("%startTime%") do (
    set /a "startTotal=(((%%a*60)+1%%b %% 100)*60+1%%c %% 100)"
)

for /f "tokens=1-4 delims=:.," %%a in ("%endTime%") do (
    set /a "endTotal=(((%%a*60)+1%%b %% 100)*60+1%%c %% 100)"
)

set /a "elapsed=endTotal-startTotal"
echo Runtime: 00:00:!elapsed! seconds >> "!RUN_LOG!"

:: === Determine Report Directory ===
set "BASE_REPORT_DIR=C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reports"

:: Try to find the actual report folder created
for /f "delims=" %%d in ('dir "!BASE_REPORT_DIR!" /b /ad ^| findstr "!custom_date!"') do (
    set "REPORT_FOLDER=%%d"
    goto :found_folder
)

:: Fallback - construct expected folder name
set "REPORT_FOLDER=C07W26_!custom_date!_7Day"

:found_folder
set "REPORT_DIR=!BASE_REPORT_DIR!\!REPORT_FOLDER!"

:: === Update Parent Folder Timestamp ===
if exist "!REPORT_DIR!" (
    echo dummy > "!REPORT_DIR!\temp.txt"
    del "!REPORT_DIR!\temp.txt"
    echo [INFO] Updated folder timestamp for: !REPORT_FOLDER!
)

:: === Post Execution Check ===
if !errorlevel! neq 0 (
    echo Run failed. Opening debug.log...
    echo Status: FAIL >> "!RUN_LOG!"
    start notepad "!DEBUG_LOG!"
    pause
    exit /b 1
) else (
    echo Run complete.
    echo Status: OK >> "!RUN_LOG!"
    
    :: === Open Report Folder ===
    if exist "!REPORT_DIR!" (
        echo Opening report folder: !REPORT_DIR!
        start "" "!REPORT_DIR!"
    ) else (
        echo [WARNING] Report folder not found: !REPORT_DIR!
    )
)

echo Done. Press any key to close...
pause
exit /b 0