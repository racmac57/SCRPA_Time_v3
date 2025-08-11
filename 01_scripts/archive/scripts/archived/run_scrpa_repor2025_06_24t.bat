@echo off
setlocal EnableDelayedExpansion

rem === Auto-detect ArcGIS Pro Python path ===
if not defined PYTHON_PATH (
    for /f "delims=" %%i in ('powershell -nologo -command ^
      "Get-ChildItem 'C:\Program Files\ArcGIS\Pro\bin\Python\envs' -Directory -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq 'arcgispro-py3' } | Select-Object -First 1 | %% { $_.FullName }"') do (
        set "PYTHON_PATH=%%i\python.exe"
    )
)
if not exist "!PYTHON_PATH!" (
    echo ⚠️ ArcGIS Python not found. Falling back to system default.
    set "PYTHON_PATH=python"
) else (
    echo Detected ArcGIS Python: "!PYTHON_PATH!"
)

rem === Get custom date input ===
:enter_custom_date
set /p input_raw="Enter custom date (YYYY_MM_DD or 'today', 'yesterday', 'tomorrow'): "
set "custom_date="

if /i "!input_raw!"=="today" (
    for /f %%i in ('powershell -nologo -command "Get-Date -Format yyyy_MM_dd"') do set "custom_date=%%i"
) else if /i "!input_raw!"=="yesterday" (
    for /f %%i in ('powershell -nologo -command "(Get-Date).AddDays(-1).ToString('yyyy_MM_dd')"') do set "custom_date=%%i"
) else if /i "!input_raw!"=="tomorrow" (
    for /f %%i in ('powershell -nologo -command "(Get-Date).AddDays(1).ToString('yyyy_MM_dd')"') do set "custom_date=%%i"
) else (
    echo !input_raw! | find "-" >nul
    if !errorlevel! == 0 (
        set "custom_date=!input_raw:-=_!"
    ) else (
        set "custom_date=!input_raw!"
    )
)

echo [DEBUG] custom_date=!custom_date!
pause

rem === Validate date ===
set "is_valid=1"
for /f "tokens=1-3 delims=_" %%a in ("!custom_date!") do (
    set "year=%%a"
    set "month=%%b"
    set "day=%%c"
    if defined year if !year! LSS 2000 if !year! GTR 2100 set "is_valid=0"
    if defined month if !month! LSS 1 if !month! GTR 12 set "is_valid=0"
    if defined day if !day! LSS 1 if !day! GTR 31 set "is_valid=0"
)
if "!is_valid!"=="0" (
    echo ❌ Invalid date: !custom_date!
    pause
    goto end
)

rem === Locate main.py ===
for /f "delims=" %%i in ('powershell -nologo -command "Get-ChildItem -Recurse -Filter main.py | Select-Object -First 1 | %% { $_.DirectoryName }"') do (
    set "SCRIPT_DIR=%%i"
)
if not defined SCRIPT_DIR (
    echo ❌ main.py not found. Exiting.
    pause
    goto end
)
echo Found main.py in: !SCRIPT_DIR!

rem === Setup logging ===
set "LOG_DATE=!year!-!month!-!day!"
set "LOG_DIR=%~dp0logs\!LOG_DATE!"
if not exist "!LOG_DIR!" mkdir "!LOG_DIR!"
set "DEBUG_LOG=!LOG_DIR!\debug.log"
set "RUN_LOG=!LOG_DIR!\run.log"

rem === Python version log ===
for /f "delims=" %%i in ('"!PYTHON_PATH!" -c "import sys; print(sys.version)"') do set "PYTHON_VERSION=%%i"
echo Python: !PYTHON_VERSION!
echo [%TIME%] Python: !PYTHON_VERSION! >> "!RUN_LOG!"

rem === Start run ===
set "start_time=%TIME%"
echo [%TIME%] BEGIN: !custom_date! >> "!RUN_LOG!"

rem === Execute safely with redirection escape ===
call "!PYTHON_PATH!" "!SCRIPT_DIR!\main.py" true true false 30 false "!custom_date!" ^>"!DEBUG_LOG!" 2^>^&1
set "exec_errorlevel=%ERRORLEVEL%"
set "end_time=%TIME%"

rem === Compute runtime ===
setlocal EnableDelayedExpansion
for /f "tokens=1-3 delims=:.," %%a in ("!start_time!") do (
    set /a start_sec=1%%a %% 100 * 3600 + 1%%b %% 100 * 60 + 1%%c %% 100
)
for /f "tokens=1-3 delims=:.," %%a in ("!end_time!") do (
    set /a end_sec=1%%a %% 100 * 3600 + 1%%b %% 100 * 60 + 1%%c %% 100
)
set /a runtime_sec=end_sec - start_sec
if !runtime_sec! LSS 0 set /a runtime_sec+=86400
endlocal & set "runtime_sec=%runtime_sec%"

set /a hrs=runtime_sec / 3600
set /a min=(runtime_sec %% 3600) / 60
set /a sec=runtime_sec %% 60
set "runtime_fmt="
if %hrs% LSS 10 set "runtime_fmt=0%hrs%" & goto cont1
set "runtime_fmt=%hrs%"
:cont1
if %min% LSS 10 set "runtime_fmt=%runtime_fmt%:0%min%" & goto cont2
set "runtime_fmt=%runtime_fmt%:%min%"
:cont2
if %sec% LSS 10 set "runtime_fmt=%runtime_fmt%:0%sec%" & goto cont3
set "runtime_fmt=%runtime_fmt%:%sec%"
:cont3

echo ▶ Runtime: %runtime_fmt% (%runtime_sec%)
echo [%TIME%] Runtime: %runtime_fmt% (%runtime_sec%) >> "!RUN_LOG!"

rem === Append runtime to CSV ===
set "CSV_LOG=%~dp0runtime_log.csv"
if not exist "!CSV_LOG!" echo date,time,duration_sec,duration_hms >> "!CSV_LOG!"
echo !LOG_DATE!,!start_time!,%runtime_sec%,%runtime_fmt% >> "!CSV_LOG!"

for /f "skip=1" %%a in ('powershell -nologo -command ^
  "Get-Content '!CSV_LOG!' | Select-Object -Last 100"') do echo %%a>>"!CSV_LOG!.tmp"
move /Y "!CSV_LOG!.tmp" "!CSV_LOG!" >nul

if %exec_errorlevel% neq 0 (
    echo ❌ Run failed. Opening debug.log...
    echo [%TIME%] STATUS: FAIL >> "!RUN_LOG!"
    start notepad "!DEBUG_LOG!"
) else (
    echo ✅ Run complete.
    echo [%TIME%] STATUS: OK >> "!RUN_LOG!"
    type "!DEBUG_LOG!"
)

:end
echo Done. Press any key to close...
pause
exit /b 0
