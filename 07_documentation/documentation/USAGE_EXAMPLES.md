# PBIX Parameter Update Tools - Usage Examples

## Overview

This comprehensive suite provides enterprise-level PBIX parameter update capabilities with validation, rollback, and JSON logging. The suite includes:

- **`update_pbix_parameter.py`** - Core parameter updater with comprehensive validation
- **`main_workflow.py`** - Batch processing workflow manager
- **`test_pbix_update.py`** - Comprehensive testing suite
- **Supporting scripts** - Enhanced testing and demonstration tools

## Quick Start

### 1. Single Parameter Update

```bash
# Basic usage
python update_pbix_parameter.py \
    --input "SCRPA_Time_v2.pbix" \
    --output "SCRPA_Time_v2_updated.pbix" \
    --param "BasePath" \
    --value "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
```

### 2. With Comprehensive Validation and JSON Summary

```bash
# Recommended usage with full features
python update_pbix_parameter.py \
    --input "SCRPA_Time_v2.pbix" \
    --output "SCRPA_Time_v2_updated.pbix" \
    --param "BasePath" \
    --value "C:\New\Path\Data" \
    --validate-all \
    --verbose \
    --summary-json "config_summary.json"
```

### 3. Batch Processing Multiple Files

```bash
# Create sample configuration
python main_workflow.py --create-sample-config "my_workflow.json"

# Edit the configuration file, then run batch processing
python main_workflow.py --config "my_workflow.json" --environment "production" --verbose
```

## Detailed Usage Examples

### A. Environment-Specific Updates

#### Step 1: Create Workflow Configuration

```bash
python main_workflow.py --create-sample-config "scrpa_workflow.json"
```

This creates a configuration file like:

```json
{
  "pbix_files": [
    "SCRPA_Time_v2.pbix",
    "SCRPA_Analysis.pbix"
  ],
  "parameters": {
    "BasePath": "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2",
    "ServerName": "localhost",
    "DatabaseName": "SCRPA_CrimeDB"
  },
  "environments": {
    "development": {
      "BasePath": "C:\\Dev\\SCRPA_Time_v2",
      "ServerName": "dev-server",
      "DatabaseName": "SCRPA_Dev"
    },
    "production": {
      "BasePath": "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2",
      "ServerName": "prod-server", 
      "DatabaseName": "SCRPA_Production"
    }
  }
}
```

#### Step 2: Run Environment-Specific Processing

```bash
# Development environment
python main_workflow.py --config "scrpa_workflow.json" --environment "development"

# Production environment  
python main_workflow.py --config "scrpa_workflow.json" --environment "production"

# Test environment
python main_workflow.py --config "scrpa_workflow.json" --environment "test"
```

### B. Advanced Single File Processing

#### With Error Recovery and Detailed Logging

```bash
python update_pbix_parameter.py \
    --input "SCRPA_Time_v2.pbix" \
    --output "SCRPA_Time_v2_prod.pbix" \
    --param "BasePath" \
    --value "\\\\server\\share\\SCRPA_Data" \
    --validate-all \
    --verbose \
    --summary-json "production_update_$(date +%Y%m%d_%H%M%S).json"
```

#### Processing Multiple Parameters (Sequential)

```bash
# Update BasePath
python update_pbix_parameter.py \
    -i "SCRPA_Time_v2.pbix" \
    -o "SCRPA_Time_v2_step1.pbix" \
    -p "BasePath" \
    -v "C:\New\Base\Path" \
    --validate-all

# Update ServerName (using output from previous step)
python update_pbix_parameter.py \
    -i "SCRPA_Time_v2_step1.pbix" \
    -o "SCRPA_Time_v2_step2.pbix" \
    -p "ServerName" \
    -v "new-server-name" \
    --validate-all

# Update DatabaseName (final step)
python update_pbix_parameter.py \
    -i "SCRPA_Time_v2_step2.pbix" \
    -o "SCRPA_Time_v2_final.pbix" \
    -p "DatabaseName" \
    -v "NewDatabase" \
    --validate-all --summary-json "final_summary.json"
```

### C. Testing and Validation

#### Comprehensive Testing Suite

```bash
# Run full test suite
python test_pbix_update.py --pbix "SCRPA_Time_v2.pbix" --test-all --verbose

# Test specific parameter update
python test_pbix_update.py \
    --pbix "SCRPA_Time_v2.pbix" \
    --param "BasePath" \
    --value "C:\Test\Path" \
    --report "test_report.txt"

# Test rollback functionality
python test_pbix_update.py --pbix "SCRPA_Time_v2.pbix" --rollback-test

# Use convenient test runner
run_pbix_tests.bat SCRPA_Time_v2.pbix
```

#### Enhanced Test Suite

```bash
# Run enhanced validation tests
python test_enhanced_pbix.py

# Rollback scenario demonstrations
python demo_rollback_scenarios.py
```

### D. Production Deployment Examples

#### Daily Report Processing

```bash
#!/bin/bash
# daily_report_update.sh

DATE=$(date +%Y%m%d)
LOG_DIR="logs/$DATE"
SUMMARY_DIR="summaries/$DATE"

mkdir -p "$LOG_DIR" "$SUMMARY_DIR"

# Update production reports
python main_workflow.py \
    --config "production_workflow.json" \
    --environment "production" \
    --verbose \
    > "$LOG_DIR/daily_update.log" 2>&1

# Check results
if [ $? -eq 0 ]; then
    echo "✅ Daily report update completed successfully"
    # Copy updated reports to deployment location
    cp workflow_output/*.pbix /path/to/powerbi/reports/
else
    echo "❌ Daily report update failed - check logs"
    exit 1
fi
```

#### Automated Deployment with Validation

```bash
#!/bin/bash
# deploy_reports.sh

# Step 1: Test current reports
echo "Testing current PBIX files..."
python test_pbix_update.py --pbix "SCRPA_Time_v2.pbix" --test-all

if [ $? -ne 0 ]; then
    echo "❌ Pre-deployment tests failed"
    exit 1
fi

# Step 2: Update parameters for production
echo "Updating parameters for production environment..."
python main_workflow.py \
    --config "deployment_config.json" \
    --environment "production" \
    --verbose

if [ $? -ne 0 ]; then
    echo "❌ Parameter update failed"
    exit 1
fi

# Step 3: Validate updated files
echo "Validating updated files..."
for file in workflow_output/*.pbix; do
    python update_pbix_parameter.py \
        --input "$file" \
        --output "/tmp/test_output.pbix" \
        --param "BasePath" \
        --value "test_value" \
        --validate-all
    
    if [ $? -ne 0 ]; then
        echo "❌ Validation failed for $file"
        exit 1
    fi
    
    rm -f "/tmp/test_output.pbix"
done

echo "✅ All validations passed - deploying reports"
# Deploy to production
```

### E. Error Recovery and Troubleshooting

#### Rollback from Failed Updates

```bash
# If an update fails, check the JSON summary for backup locations
python -c "
import json
with open('config_summary.json', 'r') as f:
    summary = json.load(f)
    
if summary['backups']:
    backup_path = summary['backups'][0]['backup_file']
    original_path = summary['backups'][0]['original_file']
    print(f'Restore command: cp \"{backup_path}\" \"{original_path}\"')
"
```

#### Batch Recovery

```bash
# Restore all backups from a workflow
python -c "
import json
import shutil
import os

with open('consolidated_summary_20250726_143025.json', 'r') as f:
    summary = json.load(f)

for file_result in summary['workflow_summary']['files_processed']:
    if 'backup_file' in file_result:
        backup = file_result['backup_file']
        original = file_result['original_file']
        if os.path.exists(backup):
            shutil.copy2(backup, original)
            print(f'Restored: {os.path.basename(original)}')
"
```

#### Debugging Failed Updates

```bash
# Enable maximum verbosity and detailed error tracking
python update_pbix_parameter.py \
    --input "problematic_file.pbix" \
    --output "test_output.pbix" \
    --param "ProblematicParam" \
    --value "new_value" \
    --validate-all \
    --verbose \
    --summary-json "debug_summary.json"

# Examine the detailed logs
cat pbix_update_*.log | grep -E "(ERROR|WARNING|DataMashup)"

# Check JSON summary for detailed error information
python -c "
import json
with open('debug_summary.json', 'r') as f:
    summary = json.load(f)
    
print('Errors found:')
for error in summary['errors']:
    print(f'  {error[\"error_type\"]}: {error[\"error_message\"]}')
    print(f'  Step: {error[\"operation_step\"]}')
    print(f'  File: {error[\"file_context\"]}')
    print()
"
```

## Configuration Examples

### Complete Workflow Configuration

```json
{
  "pbix_files": [
    "SCRPA_Time_v2.pbix",
    "SCRPA_Analysis.pbix",
    "SCRPA_Dashboard.pbix"
  ],
  "parameters": {
    "BasePath": "C:\\Data\\SCRPA",
    "ServerName": "sql-server",
    "DatabaseName": "SCRPA_DB",
    "ReportDate": "2025-07-26",
    "UserProfile": "production"
  },
  "environments": {
    "development": {
      "BasePath": "C:\\Dev\\Data",
      "ServerName": "dev-sql",
      "DatabaseName": "SCRPA_Dev",
      "ReportDate": "2025-07-26",
      "UserProfile": "development"
    },
    "staging": {
      "BasePath": "\\\\staging-server\\data",
      "ServerName": "staging-sql",
      "DatabaseName": "SCRPA_Staging",
      "ReportDate": "2025-07-26",
      "UserProfile": "staging"
    },
    "production": {
      "BasePath": "\\\\prod-server\\data",
      "ServerName": "prod-sql",
      "DatabaseName": "SCRPA_Production",
      "ReportDate": "2025-07-26",
      "UserProfile": "production"
    }
  },
  "output_directory": "reports_output",
  "backup_directory": "reports_backups",
  "log_directory": "reports_logs",
  "summary_directory": "reports_summaries",
  "retry_attempts": 3,
  "continue_on_error": true,
  "create_individual_summaries": true,
  "create_consolidated_summary": true
}
```

## Output Structure

After running the tools, you'll find organized output:

```
project/
├── workflow_output/           # Updated PBIX files
│   ├── SCRPA_Time_v2_production_20250726_143025.pbix
│   └── SCRPA_Analysis_production_20250726_143025.pbix
│
├── workflow_backups/          # Original file backups
│   ├── backups_20250726_143025/
│   │   ├── SCRPA_Time_v2_backup_20250726_143026.pbix
│   │   └── SCRPA_Analysis_backup_20250726_143027.pbix
│
├── workflow_logs/             # Detailed operation logs
│   └── workflow_20250726_143025.log
│
├── workflow_summaries/        # JSON summaries
│   ├── summary_SCRPA_Time_v2_20250726_143025.json
│   ├── summary_SCRPA_Analysis_20250726_143025.json
│   └── consolidated_summary_20250726_143025.json
│
└── pbix_update_*.log         # Individual operation logs
```

## Best Practices

### 1. Always Use Validation

```bash
# Always include --validate-all for production use
python update_pbix_parameter.py \
    --input "report.pbix" \
    --output "updated_report.pbix" \
    --param "BasePath" \
    --value "new_path" \
    --validate-all  # ← Always include this
```

### 2. Enable JSON Summaries

```bash
# Always generate JSON summaries for auditability
python update_pbix_parameter.py \
    ... \
    --summary-json "operation_$(date +%Y%m%d_%H%M%S).json"
```

### 3. Test Before Production

```bash
# Always test with your actual PBIX files first
python test_pbix_update.py --pbix "your_report.pbix" --test-all

# Then run the actual update
python update_pbix_parameter.py ...
```

### 4. Use Batch Processing for Multiple Files

```bash
# Don't update files one by one - use workflow for consistency
python main_workflow.py --config "your_config.json" --environment "production"
```

### 5. Monitor and Log Everything

```bash
# Use verbose mode and save all logs
python main_workflow.py \
    --config "config.json" \
    --verbose \
    --environment "production" \
    > deployment_$(date +%Y%m%d_%H%M%S).log 2>&1
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Update PBIX Reports
on:
  push:
    branches: [main]
    paths: ['config/**']

jobs:
  update-reports:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: pip install psutil
        
      - name: Run PBIX updates
        run: |
          python main_workflow.py \
            --config "ci_config.json" \
            --environment "production" \
            --verbose
            
      - name: Upload summaries
        uses: actions/upload-artifact@v3
        with:
          name: pbix-summaries
          path: workflow_summaries/
          
      - name: Upload updated reports
        uses: actions/upload-artifact@v3
        with:
          name: updated-reports
          path: workflow_output/
```

This comprehensive suite provides enterprise-level PBIX parameter management with full auditability, error recovery, and batch processing capabilities.