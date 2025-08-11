@echo off
REM 🕒 2025-08-02-15-35-00
REM SCRPA_Time_v2/GeoJSON Optimization Batch Script
REM Author: R. A. Carucci
REM Purpose: Optimize large GeoJSON files for better Power BI performance

echo ========================================
echo GEOJSON OPTIMIZATION SCRIPT
echo ========================================
echo.

REM Set paths
set INPUT_DIR=C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers
set OUTPUT_DIR=C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\optimized
set SCRIPT_DIR=C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts

echo Input Directory: %INPUT_DIR%
echo Output Directory: %OUTPUT_DIR%
echo Script Directory: %SCRIPT_DIR%
echo.

REM Create output directory
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Run optimization script
echo Starting GeoJSON optimization...
python "%SCRIPT_DIR%\geojson_optimizer.py" --input-dir "%INPUT_DIR%" --output-dir "%OUTPUT_DIR%" --compress --create-template

echo.
echo ========================================
echo OPTIMIZATION COMPLETE
echo ========================================
echo.
echo Optimized files saved to: %OUTPUT_DIR%
echo.
echo Next steps:
echo 1. Update your M code to use the compressed .geojson.gz files
echo 2. Use the optimized_m_code_template.m as a reference
echo 3. Test the performance improvement in Power BI
echo.
pause 