#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
configure_scrpa_pbix.py

Customized PBIX parameter configuration script for SCRPA Crime Analysis reports.
Automatically updates data source paths and other parameters in your Power BI files.

Usage:
    python configure_scrpa_pbix.py --environment [dev|prod|test]
    python configure_scrpa_pbix.py --custom-path "C:\\Your\\Custom\\Path"
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
import json
import shutil

# Add the current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from update_pbix_parameter import process_pbix

class SCRPAPBIXConfigurator:
    """Configure PBIX files for SCRPA Crime Analysis system."""
    
    def __init__(self):
        # Base project directory
        self.project_dir = Path(__file__).parent.parent
        
        # Power BI files in your project
        self.pbix_files = {
            'main': self.project_dir / "SCRPA_Time_v2.pbix",
            'legacy': self.project_dir / "SCRPA_Time.pbix"
        }
        
        # Environment configurations
        self.environments = {
            'dev': {
                'BasePath': str(self.project_dir),
                'DataPath': str(self.project_dir / "04_powerbi"),
                'ExportPath': str(self.project_dir / "03_output"),
                'LogPath': str(self.project_dir / "03_output" / "logs"),
                'description': 'Development environment with local paths'
            },
            'prod': {
                'BasePath': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2",
                'DataPath': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi",
                'ExportPath': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\03_output",
                'LogPath': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\03_output\logs",
                'description': 'Production environment with full OneDrive paths'
            },
            'test': {
                'BasePath': str(self.project_dir / "test_environment"),
                'DataPath': str(self.project_dir / "test_environment" / "data"),
                'ExportPath': str(self.project_dir / "test_environment" / "output"),
                'LogPath': str(self.project_dir / "test_environment" / "logs"),
                'description': 'Test environment with isolated paths'
            }
        }
    
    def validate_files(self):
        """Validate that PBIX files exist."""
        missing_files = []
        for name, path in self.pbix_files.items():
            if not path.exists():
                missing_files.append(f"{name}: {path}")
        
        if missing_files:
            print("WARNING: Missing PBIX files:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        print("SUCCESS: All PBIX files found:")
        for name, path in self.pbix_files.items():
            print(f"   - {name}: {path.name}")
        return True
    
    def backup_files(self):
        """Create backup copies of PBIX files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.project_dir / "backups" / f"pbix_backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"BACKUP: Creating backups in: {backup_dir}")
        
        for name, path in self.pbix_files.items():
            if path.exists():
                backup_path = backup_dir / f"{name}_{path.name}"
                shutil.copy2(path, backup_path)
                print(f"   SUCCESS: Backed up {name}: {backup_path.name}")
        
        return backup_dir
    
    def update_pbix_environment(self, environment, target_files=None):
        """Update PBIX files for specific environment."""
        if environment not in self.environments:
            raise ValueError(f"Unknown environment: {environment}")
        
        config = self.environments[environment]
        print(f"\\nCONFIG: Configuring for {environment.upper()} environment:")
        print(f"   {config['description']}")
        
        # Default to all files if none specified
        if target_files is None:
            target_files = list(self.pbix_files.keys())
        
        results = {}
        
        for file_key in target_files:
            if file_key not in self.pbix_files:
                print(f"WARNING: Unknown file key: {file_key}")
                continue
            
            input_file = self.pbix_files[file_key]
            if not input_file.exists():
                print(f"WARNING: File not found: {input_file}")
                continue
            
            # Create output filename
            output_file = input_file.parent / f"{input_file.stem}_{environment}{input_file.suffix}"
            
            print(f"\\nPROCESS: Updating {file_key} ({input_file.name}):")
            
            # Update each parameter
            temp_file = input_file
            for param_name, param_value in config.items():
                if param_name == 'description':
                    continue
                
                print(f"   UPDATE: Setting {param_name} = {param_value}")
                
                try:
                    # For first parameter, use original file
                    # For subsequent parameters, use the temp output
                    next_temp = input_file.parent / f"temp_{file_key}_{param_name}.pbix"
                    
                    process_pbix(
                        input_pbix=str(temp_file),
                        output_pbix=str(next_temp),
                        param_name=param_name,
                        new_value=param_value
                    )
                    
                    # Clean up previous temp file (except original)
                    if temp_file != input_file and temp_file.exists():
                        temp_file.unlink()
                    
                    temp_file = next_temp
                    
                except Exception as e:
                    print(f"   ERROR: Failed to update {param_name}: {e}")
                    if temp_file != input_file and temp_file.exists():
                        temp_file.unlink()
                    results[file_key] = {'success': False, 'error': str(e)}
                    break
            else:
                # All parameters updated successfully
                if temp_file.exists():
                    temp_file.rename(output_file)
                    print(f"   SUCCESS: Successfully created: {output_file.name}")
                    results[file_key] = {'success': True, 'output_file': str(output_file)}
        
        return results
    
    def update_custom_path(self, custom_path, parameter_name='BasePath', target_files=None):
        """Update PBIX files with custom path."""
        print(f"\\nCONFIG: Configuring with custom path:")
        print(f"   Parameter: {parameter_name}")
        print(f"   Value: {custom_path}")
        
        # Default to all files if none specified
        if target_files is None:
            target_files = list(self.pbix_files.keys())
        
        results = {}
        
        for file_key in target_files:
            if file_key not in self.pbix_files:
                continue
            
            input_file = self.pbix_files[file_key]
            if not input_file.exists():
                continue
            
            output_file = input_file.parent / f"{input_file.stem}_custom{input_file.suffix}"
            
            print(f"\\nPROCESS: Updating {file_key} ({input_file.name}):")
            
            try:
                process_pbix(
                    input_pbix=str(input_file),
                    output_pbix=str(output_file),
                    param_name=parameter_name,
                    new_value=custom_path
                )
                
                print(f"   SUCCESS: Successfully created: {output_file.name}")
                results[file_key] = {'success': True, 'output_file': str(output_file)}
                
            except Exception as e:
                print(f"   ERROR: Failed to update: {e}")
                results[file_key] = {'success': False, 'error': str(e)}
        
        return results
    
    def create_configuration_summary(self, results, environment=None):
        """Create a summary of the configuration changes."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        summary = {
            'timestamp': timestamp,
            'environment': environment,
            'results': results,
            'project_directory': str(self.project_dir),
            'pbix_files_processed': len([r for r in results.values() if r.get('success')])
        }
        
        # Save summary to file
        summary_file = self.project_dir / "pbix_configuration_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\\nSUMMARY: Configuration Summary:")
        print(f"   Timestamp: {timestamp}")
        print(f"   Environment: {environment or 'Custom'}")
        print(f"   Files processed: {summary['pbix_files_processed']}")
        print(f"   Summary saved to: {summary_file.name}")
        
        return summary_file

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Configure SCRPA PBIX files")
    
    # Environment-based configuration
    parser.add_argument('--environment', '-e', 
                       choices=['dev', 'prod', 'test'],
                       help='Configure for specific environment')
    
    # Custom path configuration
    parser.add_argument('--custom-path', '-c',
                       help='Set custom path for BasePath parameter')
    
    parser.add_argument('--parameter', '-p', 
                       default='BasePath',
                       help='Parameter name to update (default: BasePath)')
    
    parser.add_argument('--files', '-f',
                       nargs='+',
                       choices=['main', 'legacy'],
                       help='Specific files to update (default: all)')
    
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip creating backup files')
    
    args = parser.parse_args()
    
    if not args.environment and not args.custom_path:
        parser.error("Must specify either --environment or --custom-path")
    
    try:
        configurator = SCRPAPBIXConfigurator()
        
        print("=" * 60)
        print("SCRPA PBIX CONFIGURATOR")
        print("=" * 60)
        
        # Validate files exist
        if not configurator.validate_files():
            print("ERROR: Cannot proceed without required PBIX files")
            return 1
        
        # Create backups unless disabled
        if not args.no_backup:
            backup_dir = configurator.backup_files()
            print(f"BACKUP: Backups created in: {backup_dir}")
        
        # Configure based on arguments
        if args.environment:
            results = configurator.update_pbix_environment(
                environment=args.environment,
                target_files=args.files
            )
            summary_file = configurator.create_configuration_summary(results, args.environment)
        else:
            results = configurator.update_custom_path(
                custom_path=args.custom_path,
                parameter_name=args.parameter,
                target_files=args.files
            )
            summary_file = configurator.create_configuration_summary(results)
        
        # Print final results
        print("\\n" + "=" * 60)
        print("FINAL RESULTS")
        print("=" * 60)
        
        successful = 0
        failed = 0
        
        for file_key, result in results.items():
            if result.get('success'):
                print(f"SUCCESS: {file_key}: {Path(result['output_file']).name}")
                successful += 1
            else:
                print(f"ERROR: {file_key}: {result.get('error', 'Unknown error')}")
                failed += 1
        
        print(f"\\nSTATS: Summary: {successful} successful, {failed} failed")
        
        if successful > 0:
            print(f"\\nCOMPLETE: Configuration complete! Updated PBIX files are ready to use.")
            print(f"REPORT: Detailed summary: {summary_file}")
        
        return 0 if failed == 0 else 1
        
    except Exception as e:
        print(f"\\nERROR: Configuration failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())