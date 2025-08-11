@echo off
REM 🕒 2025-06-20-18-45-00
REM Police_Data_Analysis/find_arcgis_python
REM Author: R. A. Carucci
REM Purpose: Find the correct ArcGIS Pro Python installation

echo ============================================
echo 🔍 Finding ArcGIS Pro Python Installation
echo ============================================

echo 📍 Checking common ArcGIS Pro Python locations...

REM Check Location 1
set PATH1="C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
echo.
echo 🔎 Checking: %PATH1%
if exist %PATH1% (
    echo ✅ FOUND: %PATH1%
    echo 🧪 Testing arcpy import...
    %PATH1% -c "import arcpy; print('✅ arcpy import successful')"
) else (
    echo ❌ NOT FOUND: %PATH1%
)

REM Check Location 2
set PATH2="C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat"
echo.
echo 🔎 Checking: %PATH2%
if exist %PATH2% (
    echo ✅ FOUND: %PATH2%
    echo 🧪 Testing arcpy import...
    %PATH2% python -c "import arcpy; print('✅ arcpy import successful')"
) else (
    echo ❌ NOT FOUND: %PATH2%
)

REM Check Location 3 (Alternative)
set PATH3="C:\Program Files\ArcGIS\Pro\bin\Python\python.exe"
echo.
echo 🔎 Checking: %PATH3%
if exist %PATH3% (
    echo ✅ FOUND: %PATH3%
    echo 🧪 Testing arcpy import...
    %PATH3% -c "import arcpy; print('✅ arcpy import successful')"
) else (
    echo ❌ NOT FOUND: %PATH3%
)

REM Check what Python is currently being used
echo.
echo 📋 Current Python in PATH:
where python
python --version

REM List ArcGIS Pro directory structure
echo.
echo 📁 ArcGIS Pro directory structure:
if exist "C:\Program Files\ArcGIS\Pro" (
    dir "C:\Program Files\ArcGIS\Pro\bin" /w
    echo.
    echo 📁 Python subdirectory:
    if exist "C:\Program Files\ArcGIS\Pro\bin\Python" (
        dir "C:\Program Files\ArcGIS\Pro\bin\Python" /w
    ) else (
        echo ❌ Python directory not found
    )
) else (
    echo ❌ ArcGIS Pro not found at standard location
    echo 🔍 Checking alternative locations...
    if exist "C:\ArcGIS\Pro" (
        echo ✅ Found ArcGIS Pro at: C:\ArcGIS\Pro
        dir "C:\ArcGIS\Pro\bin" /w
    )
)

echo.
echo ============================================
echo 🏁 Diagnostic Complete
echo ============================================
pause