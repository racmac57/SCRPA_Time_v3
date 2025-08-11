@echo off
REM Ollama Setup Launcher for Windows
REM Run as Administrator for best results

echo.
echo ===============================================
echo   SECURE OLLAMA SETUP FOR SCRPA PROCESSING
echo ===============================================
echo.
echo This script will set up Ollama for secure local AI processing.
echo.
echo IMPORTANT: 
echo - Run as Administrator for full functionality
echo - Ensure you have internet connection for model download
echo - Process may take 10-30 minutes depending on connection
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

REM Run the setup script
echo Starting Ollama setup...
python "%~dp0setup_ollama_secure.py"

if errorlevel 1 (
    echo.
    echo Setup completed with errors. Check the log file for details.
) else (
    echo.
    echo Setup completed successfully!
)

echo.
echo Press any key to exit...
pause >nul