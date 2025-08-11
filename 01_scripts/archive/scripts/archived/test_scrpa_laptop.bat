@echo off
REM 🕒 2025-06-20-18-35-00
REM Police_Data_Analysis/test_scrpa_laptop  
REM Author: R. A. Carucci
REM Purpose: Test SCRPA scripts on laptop environment

echo ============================================
echo 🧪 SCRPA Laptop Testing Suite
echo ============================================

REM Change to scripts directory
cd /d "C:\Users\carucci_r\SCRPA_LAPTOP\scripts"

echo 📁 Current directory: %CD%

echo.
echo 🔧 Testing config.py...
python config.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ config.py failed
) else (
    echo ✅ config.py passed
)

echo.
echo 📊 Testing chart_export.py...
python chart_export.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ chart_export.py failed
) else (
    echo ✅ chart_export.py passed
)

echo.
echo 🗺️ Testing map_export.py...
python map_export.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ map_export.py failed
) else (
    echo ✅ map_export.py passed
)

echo.
echo 🚀 Testing main.py with sample date...
python main.py 2025_06_10
if %ERRORLEVEL% NEQ 0 (
    echo ❌ main.py failed
) else (
    echo ✅ main.py passed
)

echo.
echo ============================================
echo 🏁 Testing Complete
echo ============================================
pause