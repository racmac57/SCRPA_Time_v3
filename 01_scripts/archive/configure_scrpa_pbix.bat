@echo off
REM ============================================================
REM SCRPA PBIX CONFIGURATOR - FINAL DROP-IN READY
REM ============================================================

setlocal enableextensions enabledelayedexpansion

REM Navigate to this script's folder
cd /d "%~dp0"

REM Determine project root (parent folder)
pushd "%~dp0.."
set "PROJECT_ROOT=%CD%"
popd

REM Define PBIX paths
set "MAIN_PBIX=%PROJECT_ROOT%SCRPA_Time_v2.pbix"
set "LEGACY_PBIX=%PROJECT_ROOT%SCRPA_Time.pbix"

REM Detect 7-Zip availability, set extraction and compression commands
where 7z >nul 2>&1
if errorlevel 1 (
set "EXTRACT_CMD=powershell -NoProfile -Command ""Expand-Archive -Force '%1' '%2'"""
set "COMPRESS_CMD=powershell -NoProfile -Command ""Compress-Archive -Force '%2\*' '%1'"""
) else (
set "EXTRACT_CMD=7z x ""%1"" -o""%2"" -y >nul"
set "COMPRESS_CMD=7z a -tzip ""%1"" ""%2\*"" -mx=9 >nul"
)

:menu
cls
echo ============================================================
echo SCRPA PBIX CONFIGURATOR
echo ============================================================

echo 1. Development Environment (local paths)
echo 2. Production Environment (full OneDrive paths)
echo 3. Test Environment (isolated test paths)
echo 4. Custom Path
echo 5. Exit

echo.
set /p choice="Enter your choice (1-5): "
if "%choice%"=="5" exit /b 0

REM Configure environment
if "%choice%"=="1" (
set "ENV=Development"
set "BASEPATH=%PROJECT_ROOT%"
) else if "%choice%"=="2" (
set "ENV=Production"
set "BASEPATH=%PROJECT_ROOT%"
) else if "%choice%"=="3" (
set "ENV=Test"
set "BASEPATH=%PROJECT_ROOT%test_data"
) else if "%choice%"=="4" (
set /p BASEPATH="Enter custom base path: "
set "ENV=Custom"
) else (
echo Invalid choice.
pause>nul
goto menu
)

echo Configuring for %ENV% environment...

echo.
echo Locating PBIX files in %PROJECT_ROOT%
if not exist "%MAIN_PBIX%" (
echo ERROR: Main PBIX not found: %MAIN_PBIX%
pause>nul
exit /b 1
)
if not exist "%LEGACY_PBIX%" (
echo ERROR: Legacy PBIX not found: %LEGACY_PBIX%
pause>nul
exit /b 1
)

echo   - main:   %MAIN_PBIX%
(echo   - legacy: %LEGACY_PBIX%)

echo.
echo BACKUP: Creating backups...
set "TIMESTAMP=%date:\~10,4%%date:\~4,2%%date:\~7,2%*%time:\~0,2%%time:\~3,2%%time:\~6,2%"
set "BACKUP_DIR=%PROJECT_ROOT%backups\pbix_backup_%TIMESTAMP%"
mkdir "%BACKUP_DIR%" 2>nul
copy "%MAIN_PBIX%" "%BACKUP_DIR%\main_%~nxMAIN_PBIX%" >nul
copy "%LEGACY_PBIX%" "%BACKUP_DIR%\legacy_%~nxLEGACY_PBIX%" >nul

echo Backup completed at: %BACKUP_DIR%

echo.
echo Processing PBIX files:
set FILES_PROCESSED=0

for %%F in ("%MAIN_PBIX%","%LEGACY_PBIX%") do (
set "PBIX=%%~F"
call :process_pbix "%%~F"
set /a FILES_PROCESSED+=1
)

echo.
echo SUMMARY:
echo   Environment: %ENV%
echo   Files processed: %FILES_PROCESSED%
echo   Press any key to exit.
pause>nul
exit /b 0

:process_pbix
setlocal
set "PBIXFILE=%~1"
echo -- Processing: %PBIXFILE%

REM Prepare temp directory
set "TEMP_DIR=%TEMP%\pbix_extract_%RANDOM%"
mkdir "%TEMP_DIR%"

REM Extract PBIX
call %EXTRACT_CMD% "%PBIXFILE%" "%TEMP_DIR%"

echo Searching for DataMashup...
set "DATAMASHUP="
for /r "%TEMP_DIR%" %%G in (DataMashup\*) do (
if exist "%%G" (
set "DATAMASHUP=%%G"
goto FoundDM
)
)
echo ERROR: DataMashup not found in %PBIXFILE%
endlocal
exit /b 0

:FoundDM
echo Found DataMashup at: %DATAMASHUP%

REM Patch BasePath
echo Patching BasePath...
powershell -NoProfile -Command "(Get-Content -Raw '%DATAMASHUP%') -replace '(?<=BasePath":")\[^"]+(?=")', '%BASEPATH%' | Set-Content -Encoding UTF8 '%DATAMASHUP%'"

echo Repacking PBIX...
call %COMPRESS_CMD% "%PBIXFILE%" "%TEMP_DIR%"

echo SUCCESS: Updated %PBIXFILE%

REM Cleanup temp
echo Cleaning up...
rmdir /s /q "%TEMP_DIR%"
endlocal
exit /b 0
