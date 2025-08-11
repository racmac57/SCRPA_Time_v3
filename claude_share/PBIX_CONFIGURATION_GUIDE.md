# SCRPA Power BI Configuration Guide

## 🚀 Quick Start

Your SCRPA crime analysis Power BI reports can now be automatically configured for different environments using the PBIX parameter update scripts.

### ⚡ Fastest Method - Run the Batch File:
```batch
configure_scrpa_pbix.bat
```
This will give you a menu to choose your configuration.

### 🔧 Command Line Usage:
```bash
# Production environment (recommended)
python configure_scrpa_pbix.py --environment prod

# Development environment  
python configure_scrpa_pbix.py --environment dev

# Custom data path
python configure_scrpa_pbix.py --custom-path "C:\Your\Custom\Path"
```

## 📁 Your PBIX Files Detected

The configurator found these Power BI files in your project:
- **Main Report**: `SCRPA_Time_v2.pbix`
- **Legacy Report**: `SCRPA_Time.pbix`

## 🌍 Environment Configurations

### 🔧 Development Environment (`--environment dev`)
**Use case**: Local development and testing
```
BasePath:   <project_directory>
DataPath:   <project_directory>/04_powerbi  
ExportPath: <project_directory>/03_output
LogPath:    <project_directory>/03_output/logs
```

### 🚀 Production Environment (`--environment prod`) 
**Use case**: Live crime analysis reports with full OneDrive paths
```
BasePath:   C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2
DataPath:   C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi
ExportPath: C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\03_output  
LogPath:    C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\03_output\logs
```

### 🧪 Test Environment (`--environment test`)
**Use case**: Isolated testing with test data
```
BasePath:   <project_directory>/test_environment
DataPath:   <project_directory>/test_environment/data
ExportPath: <project_directory>/test_environment/output
LogPath:    <project_directory>/test_environment/logs
```

## 🎯 Common Usage Scenarios

### Scenario 1: Daily Production Update
```bash
# Update both PBIX files for production
python configure_scrpa_pbix.py --environment prod
```
**Output**: Creates `SCRPA_Time_v2_prod.pbix` and `SCRPA_Time_prod.pbix`

### Scenario 2: Point to New Data Location
```bash
# Update data path when CAD/RMS exports move
python configure_scrpa_pbix.py --custom-path "C:\NewDataLocation\SCRPA_Exports"
```

### Scenario 3: Update Specific Files Only
```bash
# Update only the main report
python configure_scrpa_pbix.py --environment prod --files main
```

### Scenario 4: Update Specific Parameter
```bash
# Update only the log path
python configure_scrpa_pbix.py --custom-path "C:\Logs\SCRPA" --parameter LogPath
```

### Scenario 5: Skip Backups (Faster)
```bash
# Don't create backup files
python configure_scrpa_pbix.py --environment prod --no-backup
```

## 📊 What Happens During Configuration

1. **🔍 Validation**: Checks that your PBIX files exist
2. **📂 Backup**: Creates backup copies (unless `--no-backup`)
3. **🔧 Parameter Update**: Updates Power BI parameters in the DataMashup
4. **💾 Output**: Creates new PBIX files with updated parameters
5. **📋 Summary**: Generates configuration summary JSON file

## 🔧 Technical Details

### How It Works
1. **Unzips** the PBIX file (PBIX files are ZIP archives)
2. **Extracts** the `DataMashup` file containing M Code parameters
3. **Updates** parameters using regex pattern matching:
   ```
   let BasePath = "old_path"  →  let BasePath = "new_path"
   ```
4. **Re-compresses** everything back into a new PBIX file

### Parameters Updated
- **BasePath**: Main project directory
- **DataPath**: Location of processed data files  
- **ExportPath**: Output directory for reports
- **LogPath**: Log file directory

### Output Files
Original files are preserved. New files are created with environment suffix:
- `SCRPA_Time_v2.pbix` → `SCRPA_Time_v2_prod.pbix`
- `SCRPA_Time.pbix` → `SCRPA_Time_prod.pbix`

## 🛠️ Advanced Usage

### Automation Script Example
Create `daily_update.bat`:
```batch
@echo off
echo Updating SCRPA reports for production...
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\claude_share"
python configure_scrpa_pbix.py --environment prod --no-backup
echo Update complete!
```

### Python Integration
```python
from configure_scrpa_pbix import SCRPAPBIXConfigurator

configurator = SCRPAPBIXConfigurator()
results = configurator.update_pbix_environment('prod')

for file, result in results.items():
    if result['success']:
        print(f"✅ {file}: {result['output_file']}")
    else:
        print(f"❌ {file}: {result['error']}")
```

### Scheduled Automation
```python
import schedule
from configure_scrpa_pbix import SCRPAPBIXConfigurator

def daily_update():
    configurator = SCRPAPBIXConfigurator()
    configurator.update_pbix_environment('prod')

# Run daily at 6 AM
schedule.every().day.at("06:00").do(daily_update)
```

## 🚨 Troubleshooting

### Error: "Parameter not found in DataMashup"
**Solution**: The PBIX file doesn't contain the expected parameter. Check your Power BI file has parameters defined.

### Error: "File not found"
**Solution**: Verify PBIX files exist in the project directory:
```bash
dir *.pbix
```

### Error: "Access denied"
**Solution**: Close Power BI Desktop if you have the files open.

### Output Files Not Working
1. **Check file size**: Output files should be similar size to originals
2. **Test in Power BI**: Open the new PBIX file and verify data sources
3. **Check backup**: Restore from backup if needed

## 📁 File Structure After Configuration

```
SCRPA_Time_v2/
├── SCRPA_Time_v2.pbix                 # Original main report
├── SCRPA_Time.pbix                    # Original legacy report  
├── SCRPA_Time_v2_prod.pbix           # Production main report
├── SCRPA_Time_prod.pbix              # Production legacy report
├── backups/                          # Backup copies
│   └── pbix_backup_20250125_143022/
├── pbix_configuration_summary.json   # Configuration summary
└── claude_share/
    ├── configure_scrpa_pbix.py       # Main configuration script
    ├── configure_scrpa_pbix.bat      # Windows batch interface
    ├── update_pbix_parameter.py      # Core parameter update logic
    └── update_pbix_parameter.ps1     # PowerShell version
```

## 📈 Benefits

✅ **Automated Configuration**: No manual parameter updates in Power BI  
✅ **Environment Management**: Easy switching between dev/test/prod  
✅ **Backup Protection**: Automatic backup before changes  
✅ **Batch Processing**: Update multiple files at once  
✅ **Version Control**: Keep different versions for different environments  
✅ **Reproducible**: Same configuration can be applied consistently  

## 🎯 Best Practices

1. **Always test first**: Use `--environment test` before production
2. **Keep backups**: Don't use `--no-backup` for important changes
3. **Verify updates**: Open updated PBIX files to confirm they work
4. **Document changes**: Keep notes on what configurations you use
5. **Schedule updates**: Automate daily/weekly updates for consistency

## 📞 Getting Help

If you need assistance:

1. **Check logs**: Look for error messages in the console output
2. **Verify files**: Ensure PBIX files exist and aren't corrupted
3. **Test minimal**: Try updating just one parameter first
4. **Use examples**: Run `python pbix_automation_examples.py` for demos

---

🎉 **Your SCRPA Power BI reports are now ready for automated configuration!** 

Use `configure_scrpa_pbix.bat` for the easiest setup, or use the command line for more control.