#!/usr/bin/env python3
"""
pbix_automation_examples.py

Examples and automation scripts for SCRPA PBIX parameter management.
Demonstrates various automation scenarios for crime analysis reports.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import schedule
import time

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from configure_scrpa_pbix import SCRPAPBIXConfigurator

class SCRPAAutomation:
    """Automation workflows for SCRPA PBIX management."""
    
    def __init__(self):
        self.configurator = SCRPAPBIXConfigurator()
        self.log_file = Path(__file__).parent / "automation.log"
    
    def log_message(self, message):
        """Log automation messages."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
        
        print(log_entry)
    
    def daily_report_update(self):
        """Daily automation: Update reports with current data paths."""
        self.log_message("🔄 Starting daily report update")
        
        try:
            # Update for production environment
            results = self.configurator.update_pbix_environment('prod')
            
            successful = sum(1 for r in results.values() if r.get('success'))
            total = len(results)
            
            self.log_message(f"✅ Daily update complete: {successful}/{total} files updated")
            
            # Optional: Send notification or email
            if successful == total:
                self.log_message("📧 All reports updated successfully - sending notification")
                # Add email/notification logic here
            else:
                self.log_message("⚠️ Some reports failed to update - check logs")
            
        except Exception as e:
            self.log_message(f"❌ Daily update failed: {e}")
    
    def weekly_backup_and_update(self):
        """Weekly automation: Create backups and update all environments."""
        self.log_message("📅 Starting weekly backup and update")
        
        try:
            # Create comprehensive backup
            backup_dir = self.configurator.backup_files()
            self.log_message(f"📂 Weekly backup created: {backup_dir}")
            
            # Update all environments
            for env in ['dev', 'prod', 'test']:
                self.log_message(f"🔧 Updating {env} environment")
                results = self.configurator.update_pbix_environment(env)
                
                successful = sum(1 for r in results.values() if r.get('success'))
                self.log_message(f"   {env}: {successful} files updated")
            
            self.log_message("✅ Weekly maintenance complete")
            
        except Exception as e:
            self.log_message(f"❌ Weekly maintenance failed: {e}")
    
    def update_for_data_refresh(self, new_data_path):
        """Update PBIX files when new data is available."""
        self.log_message(f"📊 Updating reports for new data: {new_data_path}")
        
        try:
            # Update DataPath parameter specifically
            results = self.configurator.update_custom_path(
                custom_path=new_data_path,
                parameter_name='DataPath'
            )
            
            successful = sum(1 for r in results.values() if r.get('success'))
            self.log_message(f"✅ Data path update complete: {successful} files updated")
            
            return results
            
        except Exception as e:
            self.log_message(f"❌ Data path update failed: {e}")
            return {}
    
    def emergency_path_update(self, old_path, new_path):
        """Emergency update when paths change (e.g., OneDrive migration)."""
        self.log_message(f"🚨 Emergency path update: {old_path} → {new_path}")
        
        try:
            # Update all path-related parameters
            path_params = ['BasePath', 'DataPath', 'ExportPath', 'LogPath']
            
            for param in path_params:
                if old_path in str(self.configurator.environments['prod'].get(param, '')):
                    updated_path = str(self.configurator.environments['prod'][param]).replace(old_path, new_path)
                    
                    self.log_message(f"   Updating {param}: {updated_path}")
                    
                    results = self.configurator.update_custom_path(
                        custom_path=updated_path,
                        parameter_name=param
                    )
                    
                    successful = sum(1 for r in results.values() if r.get('success'))
                    self.log_message(f"   {param} update: {successful} files updated")
            
            self.log_message("✅ Emergency path update complete")
            
        except Exception as e:
            self.log_message(f"❌ Emergency path update failed: {e}")

def setup_automated_schedule():
    """Set up automated scheduling for PBIX updates."""
    automation = SCRPAAutomation()
    
    # Schedule daily updates at 6 AM
    schedule.every().day.at("06:00").do(automation.daily_report_update)
    
    # Schedule weekly maintenance on Sundays at 2 AM
    schedule.every().sunday.at("02:00").do(automation.weekly_backup_and_update)
    
    print("📅 Automation schedule configured:")
    print("   - Daily updates: 6:00 AM")
    print("   - Weekly maintenance: Sunday 2:00 AM")
    
    return automation

def example_use_cases():
    """Demonstrate various use cases for PBIX automation."""
    configurator = SCRPAPBIXConfigurator()
    
    print("=" * 60)
    print("📚 SCRPA PBIX AUTOMATION EXAMPLES")
    print("=" * 60)
    
    # Example 1: Switch to development environment
    print("\n🔧 Example 1: Development Environment Setup")
    print("Command: python configure_scrpa_pbix.py --environment dev")
    print("Use case: Local development and testing")
    
    # Example 2: Production deployment
    print("\n🚀 Example 2: Production Deployment")
    print("Command: python configure_scrpa_pbix.py --environment prod")
    print("Use case: Deploy reports with production data paths")
    
    # Example 3: Custom data source
    print("\n📊 Example 3: Custom Data Source")
    print("Command: python configure_scrpa_pbix.py --custom-path 'C:\\NewDataLocation'")
    print("Use case: Point reports to new data location")
    
    # Example 4: Specific parameter update
    print("\n🎯 Example 4: Specific Parameter Update")
    print("Command: python configure_scrpa_pbix.py --custom-path 'C:\\Logs' --parameter LogPath")
    print("Use case: Update only the log file location")
    
    # Example 5: Selective file update
    print("\n📁 Example 5: Update Specific Files")
    print("Command: python configure_scrpa_pbix.py --environment prod --files main")
    print("Use case: Update only the main PBIX file")
    
    # Example 6: Batch processing
    print("\n⚡ Example 6: Batch Processing Script")
    print("""
    @echo off
    echo Updating all SCRPA reports for production...
    python configure_scrpa_pbix.py --environment prod
    echo.
    echo Updating test environment...
    python configure_scrpa_pbix.py --environment test
    echo.
    echo Batch update complete!
    """)
    
    return configurator

def monitoring_and_alerts():
    """Set up monitoring and alerting for PBIX automation."""
    
    def check_pbix_health():
        """Check if PBIX files are healthy and accessible."""
        configurator = SCRPAPBIXConfigurator()
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'files_checked': 0,
            'files_healthy': 0,
            'issues': []
        }
        
        for name, path in configurator.pbix_files.items():
            health_status['files_checked'] += 1
            
            if not path.exists():
                health_status['issues'].append(f"{name}: File not found")
                continue
            
            # Check file size (should be > 1MB for typical PBIX)
            file_size = path.stat().st_size
            if file_size < 1024 * 1024:  # Less than 1MB
                health_status['issues'].append(f"{name}: File size too small ({file_size} bytes)")
                continue
            
            # Check last modified (should be recent for active reports)
            last_modified = datetime.fromtimestamp(path.stat().st_mtime)
            days_old = (datetime.now() - last_modified).days
            if days_old > 7:  # Older than 1 week
                health_status['issues'].append(f"{name}: File not updated in {days_old} days")
            
            health_status['files_healthy'] += 1
        
        # Save health report
        health_file = configurator.project_dir / "pbix_health_report.json"
        with open(health_file, 'w') as f:
            json.dump(health_status, f, indent=2)
        
        return health_status
    
    # Example health check
    health = check_pbix_health()
    
    print("🏥 PBIX Health Check:")
    print(f"   Files checked: {health['files_checked']}")
    print(f"   Files healthy: {health['files_healthy']}")
    
    if health['issues']:
        print("   Issues found:")
        for issue in health['issues']:
            print(f"     - {issue}")
    else:
        print("   ✅ All files healthy")
    
    return health

if __name__ == "__main__":
    print("🔧 SCRPA PBIX Automation Examples")
    print("=" * 40)
    
    # Show examples
    example_use_cases()
    
    print("\n🏥 Health Check")
    print("=" * 20)
    monitoring_and_alerts()
    
    print("\n📅 To set up automated scheduling:")
    print("   automation = setup_automated_schedule()")
    print("   # Then run the scheduler")
    
    print("\n✅ Examples complete!")