@echo off
:: ============================================================================
:: Batch File to run the complete SCRPA Weekly Production Workflow (v3)
:: ============================================================================
::
:: This version adds robust error checking to diagnose why the script might
:: be closing prematurely.
::
:: It now verifies:
:: 1. The script directory exists before trying to change to it.
:: 2. Each Python script file exists before trying to execute it.
:: 3. The path to the ArcGIS Pro Python executable exists.
::
:: This will help us pinpoint the exact point of failure.
::

TITLE SCRPA Weekly Production Workflow (v3 - Debugging)

:: --- Configuration ---
SET "SCRIPT_DIR=C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts"
SET "ARCGIS_PYTHON_EXE=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"

ECHO =================================================
ECHO.
ECHO   Starting the SCRPA Weekly Production Workflow...
ECHO.
ECHO =================================================

:: 1. Verify the script directory exists
IF NOT EXIST "%SCRIPT_DIR%" (
    ECHO [ERROR] The script directory was not found!
    ECHO Please verify this path is correct:
    ECHO %SCRIPT_DIR%
    GOTO:END
)

:: Navigate to the directory containing the Python scripts. The /D switch changes the drive if needed.
cd /D "%SCRIPT_DIR%"

ECHO.
ECHO [Step 1 of 2] Preparing to run the main data processing script...

:: 2. Verify the first python script exists
IF NOT EXIST "Comprehensive_SCRPA_Fix_v8.0_Standardized.py" (
    ECHO [ERROR] The first Python script was not found in the directory.
    ECHO Missing File: Comprehensive_SCRPA_Fix_v8.0_Standardized.py
    GOTO:END
)

ECHO Executing... (This may take 2-5 minutes)
python Comprehensive_SCRPA_Fix_v8.0_Standardized.py

:: 3. Check if the first script failed
IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO [ERROR] The data processing script failed to run.
    ECHO This could be because 'python' is not in your system's PATH or due to an error in the script itself.
    ECHO The geocoding script will NOT be run. Please review the error message above.
    GOTO:END
)

ECHO [Step 1] Complete.
ECHO.
ECHO =================================================
ECHO.
ECHO [Step 2 of 2] Preparing to run the automated geocoding script...

:: 4. Verify the ArcGIS Python executable exists
IF NOT EXIST "%ARCGIS_PYTHON_EXE%" (
    ECHO [ERROR] The ArcGIS Pro Python executable was not found!
    ECHO Please verify the path is correct or update it in the batch file.
    ECHO Path Checked: %ARCGIS_PYTHON_EXE%
    GOTO:END
)

:: 5. Verify the second python script exists
IF NOT EXIST "SCRPA_Automated_Geocoding_Complete.py" (
    ECHO [ERROR] The second Python script was not found in the directory.
    ECHO Missing File: SCRPA_Automated_Geocoding_Complete.py
    GOTO:END
)

ECHO Executing... (This requires ArcGIS Pro and may take 15-20 minutes)
"%ARCGIS_PYTHON_EXE%" SCRPA_Automated_Geocoding_Complete.py

:: 6. Check if the second script failed
IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO [ERROR] The geocoding script failed to run.
    ECHO This is often due to an ArcGIS Pro license issue or an error in the script.
    GOTO:END
)

ECHO [Step 2] Complete.
ECHO.
ECHO =================================================
ECHO.
ECHO   SCRPA Weekly Production Workflow has finished successfully.
ECHO.
ECHO =================================================
ECHO.

:END
ECHO Press any key to continue . . .
pause
