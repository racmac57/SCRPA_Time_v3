REM // 🕒 2025-01-27-23-59-00
REM // SCRPA_Fix/powerpoint_template_fix.bat
REM // Author: R. A. Carucci
REM // Purpose: Fix PowerPoint template path issue

@echo off
echo ==========================================
echo SCRPA PowerPoint Template Fix
echo ==========================================

REM Create the missing directory
set "TEMPLATE_DIR=C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\7_Day_Templet_SCRPA_Time"
set "SOURCE_TEMPLATE=C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\TimeSCRPATemplet\SCRPA_REPORT.pptx"

echo [INFO] Checking template directories...

REM Check if source template exists
if not exist "%SOURCE_TEMPLATE%" (
    echo [ERROR] Source template not found: %SOURCE_TEMPLATE%
    echo [INFO] Please check if the template exists in TimeSCRPATemplet folder
    pause
    exit /b 1
)

echo [OK] Source template found: %SOURCE_TEMPLATE%

REM Create target directory if it doesn't exist
if not exist "%TEMPLATE_DIR%" (
    echo [INFO] Creating target directory: %TEMPLATE_DIR%
    mkdir "%TEMPLATE_DIR%"
)

REM Copy template to expected location
echo [INFO] Copying template to expected location...
copy "%SOURCE_TEMPLATE%" "%TEMPLATE_DIR%\SCRPA_REPORT.pptx"

if exist "%TEMPLATE_DIR%\SCRPA_REPORT.pptx" (
    echo [SUCCESS] Template copied successfully!
    echo [INFO] Template now available at: %TEMPLATE_DIR%\SCRPA_REPORT.pptx
) else (
    echo [ERROR] Template copy failed
    pause
    exit /b 1
)

echo.
echo ==========================================
echo SCRPA Template Fix Complete
echo ==========================================
echo.
echo You can now run your SCRPA script again:
echo cd C:\Users\carucci_r\SCRPA_LAPTOP\scripts
echo python main.py true false false 30 false 2025_06_03
echo.
pause