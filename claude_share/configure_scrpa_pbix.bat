@echo off
echo ============================================================
echo SCRPA PBIX CONFIGURATOR
echo ============================================================
echo.

cd /d "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\claude_share"

echo Choose configuration option:
echo 1. Development Environment (local paths)
echo 2. Production Environment (full OneDrive paths)  
echo 3. Test Environment (isolated test paths)
echo 4. Custom Path
echo 5. Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo Configuring for DEVELOPMENT environment...
    python configure_scrpa_pbix.py --environment dev
) else if "%choice%"=="2" (
    echo.
    echo Configuring for PRODUCTION environment...
    python configure_scrpa_pbix.py --environment prod
) else if "%choice%"=="3" (
    echo.
    echo Configuring for TEST environment...
    python configure_scrpa_pbix.py --environment test
) else if "%choice%"=="4" (
    echo.
    set /p custom_path="Enter custom path: "
    echo Configuring with custom path: %custom_path%
    python configure_scrpa_pbix.py --custom-path "%custom_path%"
) else if "%choice%"=="5" (
    echo Exiting...
    goto end
) else (
    echo Invalid choice. Please run the script again.
)

echo.
echo ============================================================
echo Configuration complete!
echo ============================================================

:end
echo.
pause