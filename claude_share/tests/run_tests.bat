@echo off
echo ============================================================
echo 🚀 RUNNING UPDATED CAD NOTES TESTS
echo ============================================================

cd /d "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\claude_share\tests"

echo.
echo 🔍 First, validating imports...
python validate_imports.py

echo.
echo 🧪 Now running the full test suite...
python run_tests.py

echo.
echo ✅ Test execution complete!
pause