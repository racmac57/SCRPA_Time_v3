@echo off
setlocal ENABLEDELAYEDEXPANSION

echo --------------------------------------------
echo ≡ƒòÆ SCRPA Report Automation
echo ≡ƒÆ╝ Author: R. A. Carucci
echo --------------------------------------------

set /p REPORT_DATE=Enter report date (format: YYYY_MM_DD): 

echo Running SCRPA report for !REPORT_DATE!...

"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" ^
 "C:\Users\carucci_r\OneDrive - City of Hackensack\_Hackensack_Data_Repository\GIS_Tools\Scripts\ScriptsTimeSCRPATemplet\7_day_crime_report_tool_scripts\main.py" ^
 true true false 30 false !REPORT_DATE!

echo --------------------------------------------
echo Γ£à SCRPA Report Run Complete!
pause
