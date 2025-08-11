# PowerShell script to run the CAD notes tests
Write-Host "============================================================" -ForegroundColor Green
Write-Host "🚀 RUNNING UPDATED CAD NOTES TESTS" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

# Change to the tests directory
Set-Location -Path "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\claude_share\tests"

# Run the Python test script
python run_tests.py

# Check the exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ All tests completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Some tests failed. Check the output above." -ForegroundColor Red
}

Write-Host "`nPress any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")