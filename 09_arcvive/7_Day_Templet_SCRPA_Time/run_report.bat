@echo off
set PROPY="C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat"
set SCRIPT="C:\Users\carucci_r\OneDrive - City of Hackensack\_Hackensack_Data_Repository\GIS_Tools\Scripts\ScriptsTimeSCRPATemplet\7_day_crime_report_tool_scripts\main.py"

%PROPY% %SCRIPT% true true false 30 false 2025_06_10
pause
