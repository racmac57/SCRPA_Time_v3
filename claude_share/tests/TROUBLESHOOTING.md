# Troubleshooting Guide for CAD Notes Tests

## If You Can't Run the Tests

### Issue 1: Command Not Found
```bash
cd claude_share/tests
python run_tests.py
# bash: python: command not found
```

**Solutions:**
```bash
# Try python3 instead
python3 run_tests.py

# Or use full path
C:\Python39\python.exe run_tests.py

# Or use py launcher (Windows)
py run_tests.py
```

### Issue 2: Directory Not Found
```bash
cd claude_share/tests
# No such file or directory
```

**Solutions:**
```bash
# Use full path
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\claude_share\tests"

# Or navigate step by step
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
cd claude_share
cd tests
```

### Issue 3: PowerShell Execution Policy
```powershell
./run_tests.ps1
# Execution of scripts is disabled on this system
```

**Solutions:**
```powershell
# Change execution policy temporarily
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or run directly
powershell -ExecutionPolicy Bypass -File run_tests.ps1
```

## If Tests Fail to Import

### Error: Module Not Found
```python
❌ enhanced_cadnotes_python import failed: No module named 'enhanced_cadnotes_python'
```

**Diagnosis Steps:**
1. Check if file exists:
```bash
dir "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts\enhanced_cadnotes_python.py"
```

2. Check Python path:
```python
python validate_imports.py
```

**Solutions:**
- Ensure `enhanced_cadnotes_python.py` exists in `01_scripts/`
- Verify file is not corrupted
- Check file permissions

### Error: Missing Dependencies
```python
❌ pandas import failed: No module named 'pandas'
```

**Solution:**
```bash
pip install pandas openpyxl
# Or from requirements file
pip install -r requirements.txt
```

## If Individual Tests Fail

### Test 1: Username Extraction Fails
```python
❌ assert result.loc[0, "CAD_Username"] == "Doe_J"
AssertionError
```

**Diagnosis:**
```python
# Check what was actually extracted
print(f"Expected: 'Doe_J', Got: '{result.loc[0, 'CAD_Username']}'")
```

**Possible Causes:**
- Regex pattern changed in processor
- Input format doesn't match expected pattern
- Case sensitivity issue

### Test 2: Timestamp Parsing Fails
```python
❌ assert pd.to_datetime(result.loc[0, "CAD_Timestamp"]).year == 2025
```

**Diagnosis:**
```python
# Check timestamp format
print(f"Timestamp: '{result.loc[0, 'CAD_Timestamp']}'")
print(f"Type: {type(result.loc[0, 'CAD_Timestamp'])}")
```

**Possible Causes:**
- Date format changed in processor
- Timezone handling issues
- String vs datetime type mismatch

### Test 3: Enhanced Processor Validation Fails
```python
❌ EnhancedCADNotesProcessor validation failed
```

**Diagnosis:**
- Check processor's built-in validation examples
- Look for changes in expected vs actual output
- Review validation criteria

**Solution:**
- Update test expectations to match current processor behavior
- Or fix processor if behavior is incorrect

## Performance Issues

### Slow Test Execution
If tests run slowly:

1. **Check logging output**:
   - Processor may be writing extensive logs
   - Disable verbose logging for tests

2. **Large data processing**:
   - Tests may be processing more data than expected
   - Reduce test data size

3. **Network calls**:
   - Check if processor makes external API calls
   - Mock external dependencies for testing

## General Debugging

### Enable Verbose Output
```python
# In test_cadnotes.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Processor State
```python
# After creating processor:
processor = EnhancedCADNotesProcessor()
print(f"Processor patterns: {processor.patterns}")
print(f"Logger level: {processor.logger.level}")
```

### Verify Test Data
```python
# Check test input:
df = pd.DataFrame({"CADNotes": ["- Doe_J - 1/1/2025 1:02:03 PM Test"]})
print(f"Input data:\n{df}")
print(f"Column types: {df.dtypes}")
```

## Alternative Test Methods

If `run_tests.py` doesn't work, try:

### Method 1: Direct Test Execution
```python
python test_cadnotes.py
```

### Method 2: Individual Test Functions
```python
python -c "
from test_cadnotes import test_username_and_timestamp_extraction
test_username_and_timestamp_extraction()
print('Test passed!')
"
```

### Method 3: Interactive Testing
```python
python
>>> from test_cadnotes import *
>>> test_username_and_timestamp_extraction()
>>> # Should complete without error
```

### Method 4: Pytest (if installed)
```bash
pip install pytest
python -m pytest test_cadnotes.py -v
```

## Success Indicators

When tests run successfully, you should see:
- ✅ No ImportError messages
- ✅ All 5 tests pass
- ✅ 100% success rate
- ✅ Final success message

## Getting Help

If you continue to have issues:

1. **Run import validation first**:
   ```bash
   python validate_imports.py
   ```

2. **Check the detailed logs**:
   - Look for `enhanced_cadnotes_processing.log`
   - Review any error messages

3. **Verify file structure**:
   ```
   SCRPA_Time_v2/
   ├── 01_scripts/
   │   └── enhanced_cadnotes_python.py
   └── claude_share/
       └── tests/
           ├── test_cadnotes.py
           ├── run_tests.py
           └── validate_imports.py
   ```

4. **Test minimal functionality**:
   ```python
   # Simple test
   import pandas as pd
   import sys
   from pathlib import Path
   
   scripts_path = Path("../../01_scripts")
   sys.path.insert(0, str(scripts_path))
   
   from enhanced_cadnotes_python import EnhancedCADNotesProcessor
   processor = EnhancedCADNotesProcessor()
   print("✅ Basic import successful!")
   ```

The integration should work correctly based on the code analysis, but this guide covers common issues that might arise in different environments.