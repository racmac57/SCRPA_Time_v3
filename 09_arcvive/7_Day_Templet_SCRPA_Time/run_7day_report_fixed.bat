@echo off
REM ============================================
REM Working Weekly Report Batch Script (fixed)
REM ============================================

SET PYTHON_PATH="C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat"
SET SCRIPT_PATH="C:\Users\carucci_r\OneDrive - City of Hackensack\_Hackensack_Data_Repository\GIS_Tools\Scripts\ScriptsTimeSCRPATemplet\7_day_crime_report_tool_scripts\main.py"

REM Get today’s date in YYYY_MM_DD
FOR /F %%i IN ('powershell -command "Get-Date -Format yyyy_MM_dd"') DO SET TODAY=%%i

echo 🔄 Running %SCRIPT_PATH% with date %TODAY%
%PYTHON_PATH% %SCRIPT_PATH% --date %TODAY%

echo ✅ Done! Press any key to close.
pause >nul
