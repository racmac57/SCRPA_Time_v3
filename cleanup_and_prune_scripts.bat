@echo off
REM cleanup_and_prune_scripts.bat
REM Final version using Robocopy for robust file moving.
REM This is a single, self-contained script with simplified logic and accurate counting.

SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

REM === Configuration ===
SET "ROOT=%~dp0"
SET "SCRIPTS_DIR=%ROOT%01_scripts"
SET "ARCHIVE_DIR=%ROOT%02_old_tools"
SET "MIGRATION_BACKUP_DIR=%ARCHIVE_DIR%\migration_backups"
SET "DUPLICATE_REPORT=%ROOT%duplicate_report.txt"
REM ======================

echo.
echo ================================================================
echo SCRPA CLEANUP AND MIGRATION BACKUP PROCESSING (Robocopy Version)
echo ================================================================
echo.

REM 1) Create archive directories if they don't exist
echo Step 1: Creating directory structure...
if not exist "%ARCHIVE_DIR%" mkdir "%ARCHIVE_DIR%"
if not exist "%MIGRATION_BACKUP_DIR%" mkdir "%MIGRATION_BACKUP_DIR%"
echo   Directory structure ready.
echo.

REM 2) Move all migration backup files using Robocopy
echo Step 2: Moving migration backup files...
robocopy "%SCRIPTS_DIR%" "%MIGRATION_BACKUP_DIR%" "migration_backup_*.py" /S /MOV
echo   Migration backup move operation completed.
echo.

REM 3) Archive OLD Arcpy .py files
echo Step 3: Archiving old Arcpy Python files...
SET "ARCPY_MOVED_COUNT=0"
for /f "delims=" %%F in ('dir /b /s /a-d "%SCRIPTS_DIR%\*.py"') do (
    findstr /I /C:"import arcpy" "%%F" >nul && (
        echo   Archiving "%%~nxF"
        robocopy "%%~dpF" "%ARCHIVE_DIR%" "%%~nxF" /MOV /NJH /NJS /NFL >nul
        SET /A ARCPY_MOVED_COUNT+=1
    )
)
echo   Archived !ARCPY_MOVED_COUNT! old Arcpy scripts.
echo.

REM 4) Generate duplicate report
echo Step 4: Generating duplicate report...
if exist "%DUPLICATE_REPORT%" del "%DUPLICATE_REPORT%"
powershell -NoProfile -Command "$duplicates = Get-ChildItem -LiteralPath '%SCRIPTS_DIR%' -Recurse -Filter '*.py' | Group-Object -Property Name | Where-Object { $_.Count -gt 1 } | ForEach-Object { $_.Group | Sort-Object LastWriteTime -Descending | Select-Object -Skip 1 } | Select-Object -ExpandProperty FullName; if ($duplicates) { $duplicates | Out-File -FilePath '%DUPLICATE_REPORT%' -Encoding UTF8 }"
if exist "%DUPLICATE_REPORT%" (
    echo   Duplicate report created.
) else (
    echo   No duplicates found in cleaned directory.
)
echo.

REM 5) Final Summary with accurate counting
echo ================================================================
echo FINAL PROCESSING SUMMARY
echo ================================================================
SET "REMAINING_BACKUPS=0"
for /f "delims=" %%F in ('dir /b /s /a-d "%SCRIPTS_DIR%\migration_backup_*.py" 2^>nul') do ( SET /A REMAINING_BACKUPS+=1 )

SET "FINAL_MIGRATION_COUNT=0"
for /f "delims=" %%F in ('dir /b /s /a-d "%MIGRATION_BACKUP_DIR%\*.py" 2^>nul') do ( SET /A FINAL_MIGRATION_COUNT+=1 )

echo Migration Backup Processing:
echo   - Total migration backups in archive: !FINAL_MIGRATION_COUNT! files
echo.
echo Script Organization:
echo   - Old Arcpy scripts archived: !ARCPY_MOVED_COUNT! files
if exist "%DUPLICATE_REPORT%" (
    echo   - Duplicate report: CREATED
) else (
    echo   - Duplicate report: NOT NEEDED (no duplicates found)
)
echo.
if !REMAINING_BACKUPS! EQU 0 (
    echo STATUS: SUCCESS - All files processed correctly.
) else (
    echo STATUS: INCOMPLETE - !REMAINING_BACKUPS! migration backups may still remain. Please check Robocopy log above for errors.
)
echo.
echo Processing completed at %DATE% %TIME%
echo ================================================================

ENDLOCAL
pause
