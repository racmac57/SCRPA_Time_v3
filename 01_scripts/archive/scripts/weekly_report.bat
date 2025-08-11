@echo off
set /p report_date=Enter report due date (YYYY_MM_DD): 
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" "C:\Users\carucci_r\SCRPA_LAPTOP\scripts\main.py" true false false 30 false %report_date%
echo Report complete! Opening folder...
start "" "C:\Users\carucci_r\SCRPA_LAPTOP\temp_reports"
pause