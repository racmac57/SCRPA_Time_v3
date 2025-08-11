@echo off
REM SCRPA Security Test Suite Launcher
REM Comprehensive security validation for police data processing

echo.
echo ===============================================
echo   SCRPA SECURITY VALIDATION SUITE
echo ===============================================
echo.
echo This comprehensive security test suite will validate:
echo.
echo  [NETWORK SECURITY]
echo  ✓ Localhost-only connections enforced
echo  ✓ No external API calls detected
echo  ✓ Network monitoring for violations
echo.
echo  [DATA PROTECTION]
echo  ✓ PII sanitization effectiveness
echo  ✓ Names, phones, SSNs properly masked
echo  ✓ Address block-level filtering
echo.
echo  [SYSTEM SECURITY]
echo  ✓ LLM processing local-only
echo  ✓ Configuration audit
echo  ✓ File system protection
echo  ✓ Error handling validation
echo.
echo  [COMPLIANCE]
echo  ✓ CJIS security requirements
echo  ✓ Police data handling standards
echo  ✓ Audit trail completeness
echo.
echo IMPORTANT NOTES:
echo - This test may take 5-10 minutes to complete
echo - Network connections will be monitored in real-time
echo - Sensitive test data will be generated and sanitized
echo - Comprehensive reports will be generated (JSON + HTML)
echo - Run as Administrator for best results
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

REM Check if required dependencies are available
echo Checking required dependencies...
python -c "import pandas, psutil, requests" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Some required Python packages may be missing
    echo Installing required packages...
    pip install pandas psutil requests >nul 2>&1
)

REM Run the security validation suite
echo.
echo Starting comprehensive security validation...
echo.
python "%~dp0run_security_tests.py"

set TEST_RESULT=%errorlevel%

echo.
if %TEST_RESULT% equ 0 (
    echo ========================================
    echo   🎉 ALL SECURITY TESTS PASSED!
    echo ========================================
    echo.
    echo ✅ System meets all security requirements
    echo ✅ Ready for production police data processing
    echo ✅ Compliance reports generated
    echo.
    echo Your SCRPA system is SECURE and COMPLIANT!
) else if %TEST_RESULT% equ 1 (
    echo ========================================
    echo   ⚠️ MINOR SECURITY ISSUES FOUND
    echo ========================================
    echo.
    echo ⚠️ Some security tests failed or had warnings
    echo ⚠️ Review the detailed reports for specifics
    echo ⚠️ Address issues before production use
    echo.
    echo Check the generated reports for detailed findings
) else if %TEST_RESULT% equ 2 (
    echo ========================================
    echo   ❌ CRITICAL SECURITY ISSUES FOUND
    echo ========================================
    echo.
    echo ❌ Critical security violations detected
    echo ❌ System NOT SAFE for police data processing
    echo ❌ Must fix all critical issues before use
    echo.
    echo IMMEDIATE ACTION REQUIRED - Check reports for details
) else (
    echo ========================================
    echo   ❌ SECURITY VALIDATION FAILED
    echo ========================================
    echo.
    echo ❌ Security test suite encountered errors
    echo ❌ Check console output for error details
    echo ❌ Ensure all required files are present
    echo.
    echo Troubleshooting:
    echo 1. Verify all security validation files exist
    echo 2. Check Python installation and packages
    echo 3. Run as Administrator if permission issues
    echo 4. Check security_validation.log for details
)

echo.
echo Reports generated (if tests completed):
echo - scrpa_security_report_[timestamp].json (detailed data)
echo - scrpa_security_report_[timestamp].html (visual report)
echo - security_validation.log (execution log)
echo.
echo Press any key to exit...
pause >nul