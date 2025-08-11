@echo off
REM SCRPA Security Migration Launcher
REM Run as Administrator for best results

echo.
echo ===============================================
echo   SCRPA SECURITY MIGRATION TOOL
echo ===============================================
echo.
echo This script will safely migrate your SCRPA system
echo to the secure version with full backup capability.
echo.
echo IMPORTANT NOTES:
echo - All original files will be backed up
echo - Rollback capability will be provided
echo - Run as Administrator for full functionality
echo - Migration may take 5-15 minutes
echo.
echo WHAT THIS MIGRATION DOES:
echo ✓ Creates timestamped backup of all files
echo ✓ Scans for external API keys and dependencies
echo ✓ Replaces external LLM calls with local Ollama
echo ✓ Adds mandatory data sanitization
echo ✓ Implements localhost-only validation
echo ✓ Creates rollback script for emergency restore
echo.

pause

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Run the migration script
echo Starting SCRPA security migration...
echo.
python "%~dp0migrate_to_secure_scrpa.py"

set MIGRATION_RESULT=%errorlevel%

echo.
if %MIGRATION_RESULT% equ 0 (
    echo ========================================
    echo   MIGRATION COMPLETED SUCCESSFULLY!
    echo ========================================
    echo.
    echo ✓ All files backed up safely
    echo ✓ Security issues resolved
    echo ✓ Local Ollama processing configured
    echo ✓ Data sanitization enabled
    echo ✓ Rollback script created
    echo.
    echo NEXT STEPS:
    echo 1. Run setup_ollama_secure.py to configure Ollama
    echo 2. Test the secure SCRPA generator
    echo 3. Verify all functionality works as expected
    echo.
    echo If issues occur, use rollback_scrpa_migration.py
) else (
    echo ========================================
    echo   MIGRATION COMPLETED WITH ISSUES
    echo ========================================
    echo.
    echo ⚠ Check the output above for details
    echo ⚠ All original files are safely backed up
    echo ⚠ You can rollback if needed
    echo.
    echo TROUBLESHOOTING:
    echo 1. Check migration log file for details
    echo 2. Ensure you have write permissions
    echo 3. Run as Administrator if needed
    echo 4. Use rollback script if necessary
)

echo.
echo Press any key to exit...
pause >nul