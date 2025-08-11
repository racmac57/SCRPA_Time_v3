@echo off
REM ============================================================================
REM PBIX Parameter Update Test Suite Runner
REM ============================================================================

echo.
echo ========================================================================
echo PBIX PARAMETER UPDATE - COMPREHENSIVE TEST SUITE
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

REM Set default PBIX file (user can override)
set "DEFAULT_PBIX=SCRPA_Time_v2.pbix"
set "TEST_PBIX=%1"

if "%TEST_PBIX%"=="" (
    if exist "%DEFAULT_PBIX%" (
        set "TEST_PBIX=%DEFAULT_PBIX%"
        echo Using default PBIX file: %DEFAULT_PBIX%
    ) else (
        echo ERROR: No PBIX file specified and default file not found
        echo Usage: %0 ^<PBIX_FILE^>
        echo   or place SCRPA_Time_v2.pbix in the current directory
        pause
        exit /b 1
    )
) else (
    echo Using specified PBIX file: %TEST_PBIX%
)

echo.

REM Check if PBIX file exists
if not exist "%TEST_PBIX%" (
    echo ERROR: PBIX file not found: %TEST_PBIX%
    pause
    exit /b 1
)

echo Found PBIX file: %TEST_PBIX%
echo.

REM Create results directory
set "RESULTS_DIR=test_results_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "RESULTS_DIR=%RESULTS_DIR: =0%"
mkdir "%RESULTS_DIR%" 2>nul

echo Results will be saved to: %RESULTS_DIR%
echo.

REM Menu for test selection
:MENU
echo ========================================================================
echo TEST SELECTION MENU
echo ========================================================================
echo 1. Run Full PBIX Parameter Update Test
echo 2. Run Rollback Functionality Test  
echo 3. Run Rollback Scenarios Demo
echo 4. Run Enhanced PBIX Test Suite
echo 5. Run All Tests (Comprehensive)
echo 6. Exit
echo.
set /p "choice=Select test to run (1-6): "

if "%choice%"=="1" goto FULL_TEST
if "%choice%"=="2" goto ROLLBACK_TEST
if "%choice%"=="3" goto ROLLBACK_DEMO
if "%choice%"=="4" goto ENHANCED_TESTS
if "%choice%"=="5" goto ALL_TESTS
if "%choice%"=="6" goto EXIT
echo Invalid choice. Please select 1-6.
goto MENU

:FULL_TEST
echo.
echo ========================================================================
echo RUNNING: Full PBIX Parameter Update Test
echo ========================================================================
echo.
python test_pbix_update.py --pbix "%TEST_PBIX%" --param "BasePath" --value "C:\Test\Path\%time:~0,2%%time:~3,2%%time:~6,2%" --report "%RESULTS_DIR%\full_test_report.txt" --verbose
if errorlevel 1 (
    echo.
    echo TEST FAILED - Check report for details
) else (
    echo.
    echo TEST COMPLETED SUCCESSFULLY
)
echo.
pause
goto MENU

:ROLLBACK_TEST
echo.
echo ========================================================================
echo RUNNING: Rollback Functionality Test
echo ========================================================================
echo.
python test_pbix_update.py --pbix "%TEST_PBIX%" --rollback-test --report "%RESULTS_DIR%\rollback_test_report.txt" --verbose
if errorlevel 1 (
    echo.
    echo ROLLBACK TEST FAILED - Check report for details
) else (
    echo.
    echo ROLLBACK TEST COMPLETED SUCCESSFULLY
)
echo.
pause
goto MENU

:ROLLBACK_DEMO
echo.
echo ========================================================================
echo RUNNING: Rollback Scenarios Demonstration
echo ========================================================================
echo.
python demo_rollback_scenarios.py
if errorlevel 1 (
    echo.
    echo ROLLBACK DEMO FAILED
) else (
    echo.
    echo ROLLBACK DEMO COMPLETED SUCCESSFULLY
)
echo.
pause
goto MENU

:ENHANCED_TESTS
echo.
echo ========================================================================
echo RUNNING: Enhanced PBIX Test Suite
echo ========================================================================
echo.
python test_enhanced_pbix.py
if errorlevel 1 (
    echo.
    echo ENHANCED TESTS FAILED
) else (
    echo.
    echo ENHANCED TESTS COMPLETED SUCCESSFULLY
)
echo.
pause
goto MENU

:ALL_TESTS
echo.
echo ========================================================================
echo RUNNING: ALL TESTS (COMPREHENSIVE SUITE)
echo ========================================================================
echo.

echo [1/4] Running Enhanced PBIX Tests...
python test_enhanced_pbix.py > "%RESULTS_DIR%\enhanced_tests.log" 2>&1
set "enhanced_result=%errorlevel%"

echo [2/4] Running Full PBIX Update Test...
python test_pbix_update.py --pbix "%TEST_PBIX%" --param "BasePath" --value "C:\Comprehensive\Test\Path" --report "%RESULTS_DIR%\comprehensive_test_report.txt" > "%RESULTS_DIR%\full_test.log" 2>&1
set "full_result=%errorlevel%"

echo [3/4] Running Rollback Test...
python test_pbix_update.py --pbix "%TEST_PBIX%" --rollback-test --report "%RESULTS_DIR%\comprehensive_rollback_report.txt" > "%RESULTS_DIR%\rollback_test.log" 2>&1
set "rollback_result=%errorlevel%"

echo [4/4] Running Rollback Scenarios Demo...
python demo_rollback_scenarios.py > "%RESULTS_DIR%\rollback_demo.log" 2>&1
set "demo_result=%errorlevel%"

echo.
echo ========================================================================
echo COMPREHENSIVE TEST RESULTS SUMMARY
echo ========================================================================
echo Enhanced Tests:       %enhanced_result% (0=Success, 1=Failed)
echo Full Update Test:     %full_result% (0=Success, 1=Failed)  
echo Rollback Test:        %rollback_result% (0=Success, 1=Failed)
echo Rollback Demo:        %demo_result% (0=Success, 1=Failed)
echo.
echo All logs and reports saved to: %RESULTS_DIR%
echo.

REM Calculate overall result
set /a "total_failures=%enhanced_result%+%full_result%+%rollback_result%+%demo_result%"
if %total_failures%==0 (
    echo OVERALL RESULT: ALL TESTS PASSED
) else (
    echo OVERALL RESULT: %total_failures% TEST(S) FAILED
)
echo.
pause
goto MENU

:EXIT
echo.
echo ========================================================================
echo TEST SESSION COMPLETE
echo ========================================================================
echo.
if exist "%RESULTS_DIR%" (
    echo Test results and logs saved to: %RESULTS_DIR%
    echo.
    dir /b "%RESULTS_DIR%"
    echo.
)
echo Thank you for using the PBIX Parameter Update Test Suite!
echo.
pause
exit /b 0