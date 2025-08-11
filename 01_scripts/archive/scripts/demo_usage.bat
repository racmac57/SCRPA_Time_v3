@echo off
REM ============================================================================
REM PBIX Parameter Update Tools - Usage Demonstration
REM ============================================================================

echo.
echo ========================================================================
echo PBIX PARAMETER UPDATE TOOLS - USAGE DEMONSTRATION
echo ========================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Set demo PBIX file
set "DEMO_PBIX=SCRPA_Time_v2.pbix"

echo This demonstration will show you how to use the PBIX parameter update tools.
echo.
echo Prerequisites:
echo   - Python 3.x installed
echo   - PBIX file available: %DEMO_PBIX%
echo   - psutil package (optional, for system monitoring)
echo.

if not exist "%DEMO_PBIX%" (
    echo WARNING: Demo PBIX file not found: %DEMO_PBIX%
    echo You can still run the demonstration with any .pbix file you have.
    echo.
    set /p "DEMO_PBIX=Enter path to your PBIX file (or press Enter to skip): "
    
    if "%DEMO_PBIX%"=="" (
        echo Skipping file-based demonstrations...
        goto SHOW_EXAMPLES
    )
)

echo.
echo ========================================================================
echo DEMONSTRATION MENU
echo ========================================================================
echo.
echo 1. Create Sample Workflow Configuration
echo 2. Single Parameter Update (Basic)
echo 3. Single Parameter Update (Full Validation)
echo 4. Batch Processing Demonstration
echo 5. Test Suite Demonstration
echo 6. View Usage Examples
echo 7. Exit
echo.

:MENU
set /p "choice=Select demonstration (1-7): "

if "%choice%"=="1" goto CREATE_CONFIG
if "%choice%"=="2" goto SINGLE_BASIC
if "%choice%"=="3" goto SINGLE_FULL
if "%choice%"=="4" goto BATCH_DEMO
if "%choice%"=="5" goto TEST_DEMO
if "%choice%"=="6" goto SHOW_EXAMPLES
if "%choice%"=="7" goto EXIT

echo Invalid choice. Please select 1-7.
goto MENU

:CREATE_CONFIG
echo.
echo ========================================================================
echo DEMONSTRATION 1: Creating Sample Workflow Configuration
echo ========================================================================
echo.
echo Creating a sample workflow configuration file...
echo.

python main_workflow.py --create-sample-config "demo_workflow_config.json"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to create sample configuration
    pause
    goto MENU
)

echo.
echo SUCCESS: Sample configuration created as 'demo_workflow_config.json'
echo You can edit this file to customize parameters and PBIX files.
echo.
echo Opening the configuration file...
if exist "demo_workflow_config.json" (
    type "demo_workflow_config.json"
    echo.
    echo The configuration file shows:
    echo   - PBIX files to process
    echo   - Parameters to update
    echo   - Environment-specific settings
    echo   - Processing options
)
echo.
pause
goto MENU

:SINGLE_BASIC
echo.
echo ========================================================================
echo DEMONSTRATION 2: Single Parameter Update (Basic)
echo ========================================================================
echo.
echo This demonstrates basic parameter updating with minimal options.
echo.
echo Command that will be executed:
echo python update_pbix_parameter.py \
echo     --input "%DEMO_PBIX%" \
echo     --output "demo_output_basic.pbix" \
echo     --param "BasePath" \
echo     --value "C:\Demo\Path\Basic"
echo.
set /p "confirm=Press Enter to continue or 'S' to skip: "
if /i "%confirm%"=="S" goto MENU

python update_pbix_parameter.py --input "%DEMO_PBIX%" --output "demo_output_basic.pbix" --param "BasePath" --value "C:\Demo\Path\Basic"

if errorlevel 1 (
    echo.
    echo The update encountered issues. This is normal for demonstration purposes.
    echo Check the log files for detailed information.
) else (
    echo.
    echo SUCCESS: Basic parameter update completed
    echo Output file: demo_output_basic.pbix
)
echo.
pause
goto MENU

:SINGLE_FULL
echo.
echo ========================================================================
echo DEMONSTRATION 3: Single Parameter Update (Full Validation)
echo ========================================================================
echo.
echo This demonstrates comprehensive parameter updating with all features:
echo   - Pre and post validation
echo   - Backup creation
echo   - JSON summary generation
echo   - Verbose logging
echo   - Error recovery
echo.
echo Command that will be executed:
echo python update_pbix_parameter.py \
echo     --input "%DEMO_PBIX%" \
echo     --output "demo_output_full.pbix" \
echo     --param "BasePath" \
echo     --value "C:\Demo\Path\Full" \
echo     --validate-all \
echo     --verbose \
echo     --summary-json "demo_summary_full.json"
echo.
set /p "confirm=Press Enter to continue or 'S' to skip: "
if /i "%confirm%"=="S" goto MENU

python update_pbix_parameter.py --input "%DEMO_PBIX%" --output "demo_output_full.pbix" --param "BasePath" --value "C:\Demo\Path\Full" --validate-all --verbose --summary-json "demo_summary_full.json"

echo.
echo Results:
if exist "demo_output_full.pbix" (
    echo   ✅ Output file created: demo_output_full.pbix
) else (
    echo   ❌ Output file not created
)

if exist "demo_summary_full.json" (
    echo   ✅ JSON summary created: demo_summary_full.json
    echo.
    echo Summary preview:
    python -c "import json; f=open('demo_summary_full.json','r'); data=json.load(f); print(f'  Session ID: {data[\"session_id\"]}'); print(f'  Success: {data[\"success\"]}'); print(f'  Duration: {data[\"duration_seconds\"]}s'); print(f'  Errors: {len(data[\"errors\"])}'); f.close()"
) else (
    echo   ❌ JSON summary not created
)

dir /b demo_*.log >nul 2>&1
if not errorlevel 1 (
    echo   ✅ Log files created
)
echo.
pause
goto MENU

:BATCH_DEMO
echo.
echo ========================================================================
echo DEMONSTRATION 4: Batch Processing
echo ========================================================================
echo.
echo This demonstrates batch processing of multiple parameters using workflow configuration.
echo.

if not exist "demo_workflow_config.json" (
    echo First creating a sample configuration...
    python main_workflow.py --create-sample-config "demo_workflow_config.json"
)

echo.
echo Configuration file contents:
type "demo_workflow_config.json" | findstr /C:"pbix_files" /C:"parameters" /C:"environments"
echo ... (see full file for complete configuration)
echo.
echo Command that will be executed:
echo python main_workflow.py \
echo     --config "demo_workflow_config.json" \
echo     --environment "development" \
echo     --verbose
echo.
set /p "confirm=Press Enter to continue or 'S' to skip: "
if /i "%confirm%"=="S" goto MENU

python main_workflow.py --config "demo_workflow_config.json" --environment "development" --verbose

echo.
echo Batch processing results:
if exist "workflow_output" (
    echo   ✅ Workflow output directory created
    dir /b workflow_output\*.pbix 2>nul
)
if exist "workflow_summaries" (
    echo   ✅ Workflow summaries directory created
    dir /b workflow_summaries\*.json 2>nul
)
echo.
pause
goto MENU

:TEST_DEMO
echo.
echo ========================================================================
echo DEMONSTRATION 5: Test Suite
echo ========================================================================
echo.
echo This demonstrates the comprehensive testing capabilities.
echo.
echo Available tests:
echo   1. Enhanced PBIX Test Suite (unit tests)
echo   2. Full Process Test (integration test)
echo   3. Rollback Scenarios (failure recovery)
echo   4. Batch Test Runner (convenient interface)
echo.
set /p "test_choice=Select test to run (1-4) or Enter to skip: "

if "%test_choice%"=="1" (
    echo.
    echo Running Enhanced PBIX Test Suite...
    python test_enhanced_pbix.py
) else if "%test_choice%"=="2" (
    echo.
    echo Running Full Process Test...
    python test_pbix_update.py --pbix "%DEMO_PBIX%" --param "BasePath" --value "C:\Test\Path" --verbose
) else if "%test_choice%"=="3" (
    echo.
    echo Running Rollback Scenarios...
    python demo_rollback_scenarios.py
) else if "%test_choice%"=="4" (
    echo.
    echo Running Batch Test Runner...
    call run_pbix_tests.bat "%DEMO_PBIX%"
) else (
    echo Skipping test demonstration...
)

echo.
pause
goto MENU

:SHOW_EXAMPLES
echo.
echo ========================================================================
echo DEMONSTRATION 6: Usage Examples and Documentation
echo ========================================================================
echo.
echo Opening usage examples and documentation...
echo.

if exist "USAGE_EXAMPLES.md" (
    echo The USAGE_EXAMPLES.md file contains comprehensive documentation including:
    echo.
    echo   • Quick start examples
    echo   • Environment-specific configurations  
    echo   • Advanced batch processing
    echo   • Error recovery procedures
    echo   • Production deployment examples
    echo   • CI/CD integration guides
    echo.
    echo Key usage patterns:
    echo.
    echo 1. Single Parameter Update:
    echo    python update_pbix_parameter.py -i input.pbix -o output.pbix -p ParamName -v "NewValue"
    echo.
    echo 2. Comprehensive Update:
    echo    python update_pbix_parameter.py -i input.pbix -o output.pbix -p ParamName -v "NewValue" --validate-all --verbose --summary-json summary.json
    echo.
    echo 3. Batch Processing:
    echo    python main_workflow.py --config workflow.json --environment production
    echo.
    echo 4. Testing:
    echo    python test_pbix_update.py --pbix input.pbix --test-all
    echo.
    set /p "view_file=View full documentation file? (Y/N): "
    if /i "%view_file%"=="Y" (
        start notepad "USAGE_EXAMPLES.md"
    )
) else (
    echo USAGE_EXAMPLES.md file not found in current directory.
)

echo.
pause
goto MENU

:EXIT
echo.
echo ========================================================================
echo DEMONSTRATION COMPLETE
echo ========================================================================
echo.
echo Thank you for exploring the PBIX Parameter Update Tools!
echo.
echo Files created during this demonstration:
dir /b demo_* 2>nul
dir /b workflow_* 2>nul
echo.
echo To clean up demonstration files, you can delete:
echo   - demo_*.*
echo   - workflow_*
echo   - Any temporary log files
echo.
echo For production use, refer to:
echo   - USAGE_EXAMPLES.md (comprehensive documentation)
echo   - Sample configuration files created
echo   - Log files for troubleshooting examples
echo.
pause
exit /b 0