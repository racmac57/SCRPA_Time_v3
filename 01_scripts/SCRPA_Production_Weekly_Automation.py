# 2025-08-01-00-00-00
# SCRPA_Time_v2/SCRPA_Production_Weekly_Automation
# Author: R. A. Carucci
# Purpose: Production-ready weekly SCRPA automation with validation and spatial enhancement

import pandas as pd
import numpy as np
import re
import json
import time
import os
import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging
import traceback

class SCRPAProductionAutomation:
    """
    Production-ready weekly SCRPA automation system.
    
    Features:
    - Complete pipeline execution with error recovery
    - Comprehensive validation and quality checks
    - Spatial enhancement integration
    - Automated reporting and alerting
    - Performance monitoring and benchmarking
    - Weekly scheduling compatibility
    """
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)
            
        self.export_dirs = {
            'cad_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA"),
            'rms_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA")
        }
        
        self.output_dir = self.project_path / '04_powerbi'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.backup_dir = self.project_path / 'backups' / f"backup_{datetime.now().strftime('%Y%m%d')}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {
            'execution_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'start_time': datetime.now(),
            'status': 'RUNNING',
            'steps_completed': [],
            'steps_failed': [],
            'performance_metrics': {},
            'validation_results': {},
            'final_datasets': {},
            'errors': []
        }
        
        self.setup_logging()

    def setup_logging(self):
        """Setup comprehensive logging for production."""
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create both execution log and daily log
        execution_log = log_dir / f"scrpa_execution_{self.results['execution_id']}.log"
        daily_log = log_dir / f"scrpa_daily_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Setup logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(execution_log, encoding='utf-8'),
                logging.FileHandler(daily_log, encoding='utf-8', mode='a'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("="*80)
        self.logger.info(f"SCRPA PRODUCTION AUTOMATION STARTING - {self.results['execution_id']}")
        self.logger.info("="*80)

    def backup_existing_outputs(self):
        """Backup existing output files before processing."""
        self.logger.info("Step 1: Backing up existing outputs...")
        
        try:
            files_to_backup = [
                'cad_data_standardized.csv',
                'rms_data_standardized.csv',
                'cad_rms_matched_standardized.csv'
            ]
            
            backed_up_files = []
            
            for filename in files_to_backup:
                source_file = self.output_dir / filename
                if source_file.exists():
                    backup_file = self.backup_dir / filename
                    shutil.copy2(source_file, backup_file)
                    backed_up_files.append(filename)
                    self.logger.info(f"  Backed up: {filename}")
            
            self.results['steps_completed'].append('backup_existing_outputs')
            self.logger.info(f"Backup completed: {len(backed_up_files)} files backed up")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            self.results['steps_failed'].append('backup_existing_outputs')
            self.results['errors'].append(f"Backup error: {e}")
            return False

    def run_corrected_pipeline(self):
        """Run the corrected SCRPA pipeline."""
        self.logger.info("Step 2: Running corrected SCRPA pipeline...")
        
        try:
            start_time = time.time()
            
            # Import and run the corrected pipeline
            import importlib.util
            
            module_path = self.project_path / '01_scripts' / 'Comprehensive_SCRPA_Fix_v8.0_Standardized.py'
            spec = importlib.util.spec_from_file_location("Comprehensive_SCRPA_Fix_v8_0_Standardized", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Run pipeline
            processor = module.ComprehensiveSCRPAFixV8_0()
            pipeline_results = processor.process_final_pipeline()
            
            processing_time = time.time() - start_time
            self.results['performance_metrics']['pipeline_processing_time'] = processing_time
            
            self.logger.info(f"Pipeline completed in {processing_time:.2f} seconds")
            self.results['steps_completed'].append('run_corrected_pipeline')
            
            return pipeline_results
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.results['steps_failed'].append('run_corrected_pipeline')
            self.results['errors'].append(f"Pipeline error: {e}")
            return None

    def validate_pipeline_outputs(self):
        """Validate pipeline outputs with comprehensive checks."""
        self.logger.info("Step 3: Validating pipeline outputs...")
        
        try:
            # Use the simple validator
            import importlib.util
            
            validator_path = self.project_path / '01_scripts' / 'SCRPA_Pipeline_Validator_Simple.py'
            spec = importlib.util.spec_from_file_location("SCRPASimpleValidator", validator_path)
            validator_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(validator_module)
            
            # Run validation
            validator = validator_module.SCRPASimpleValidator(str(self.project_path))
            validation_results = validator.run_complete_validation()
            
            self.results['validation_results'] = validation_results
            
            # Check if validation passed
            if validation_results.get('ready_for_production', False):
                self.logger.info("All validations PASSED - Pipeline ready for production")
                self.results['steps_completed'].append('validate_pipeline_outputs')
                return True
            else:
                self.logger.warning(f"Validation issues found: {validation_results.get('validations_passed', 'Unknown')}")
                self.results['steps_completed'].append('validate_pipeline_outputs')  # Still completed, but with warnings
                return True  # Continue processing even with warnings
                
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            self.results['steps_failed'].append('validate_pipeline_outputs')
            self.results['errors'].append(f"Validation error: {e}")
            return False

    def prepare_spatial_datasets(self):
        """Prepare datasets for spatial enhancement."""
        self.logger.info("Step 4: Preparing spatial datasets...")
        
        try:
            # Create spatial-ready datasets with coordinate placeholders
            datasets_to_enhance = [
                'cad_data_standardized.csv',
                'rms_data_standardized.csv',
                'cad_rms_matched_standardized.csv'
            ]
            
            spatial_columns = ['x_coord', 'y_coord', 'geocode_score', 'geocode_status', 'match_address']
            
            for dataset_file in datasets_to_enhance:
                file_path = self.output_dir / dataset_file
                if file_path.exists():
                    # Read dataset
                    df = pd.read_csv(file_path)
                    
                    # Add spatial columns with null values (ready for geocoding)
                    for col in spatial_columns:
                        if col not in df.columns:
                            df[col] = None
                    
                    # Save spatial-ready version
                    spatial_file = self.output_dir / dataset_file.replace('.csv', '_spatial_ready.csv')
                    df.to_csv(spatial_file, index=False)
                    
                    self.logger.info(f"  Prepared spatial dataset: {spatial_file.name}")
                    
                    # Store in results
                    self.results['final_datasets'][dataset_file.replace('.csv', '_spatial_ready')] = {
                        'path': str(spatial_file),
                        'record_count': len(df),
                        'column_count': len(df.columns),
                        'spatial_ready': True
                    }
            
            self.results['steps_completed'].append('prepare_spatial_datasets')
            self.logger.info("Spatial datasets prepared successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Spatial preparation failed: {e}")
            self.results['steps_failed'].append('prepare_spatial_datasets')
            self.results['errors'].append(f"Spatial preparation error: {e}")
            return False

    def generate_production_report(self):
        """Generate comprehensive production report."""
        self.logger.info("Step 5: Generating production report...")
        
        try:
            # Calculate final execution time
            end_time = datetime.now()
            total_time = (end_time - self.results['start_time']).total_seconds()
            
            self.results['end_time'] = end_time
            self.results['total_execution_time'] = total_time
            
            # Set final status
            if self.results['steps_failed']:
                self.results['status'] = 'COMPLETED_WITH_ERRORS'
            else:
                self.results['status'] = 'SUCCESS'
            
            # Create comprehensive JSON report
            report_data = {
                'execution_summary': {
                    'execution_id': self.results['execution_id'],
                    'start_time': self.results['start_time'].isoformat(),
                    'end_time': self.results['end_time'].isoformat(),
                    'total_execution_time_seconds': total_time,
                    'status': self.results['status']
                },
                'steps_summary': {
                    'completed_steps': self.results['steps_completed'],
                    'failed_steps': self.results['steps_failed'],
                    'success_rate': len(self.results['steps_completed']) / (len(self.results['steps_completed']) + len(self.results['steps_failed'])) * 100 if (self.results['steps_completed'] or self.results['steps_failed']) else 0
                },
                'performance_metrics': self.results['performance_metrics'],
                'validation_results': self.results['validation_results'],
                'final_datasets': self.results['final_datasets'],
                'errors': self.results['errors']
            }
            
            # Save JSON report
            json_report_path = self.project_path / '03_output' / f'production_report_{self.results["execution_id"]}.json'
            with open(json_report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            # Create executive summary report
            summary_content = f"""# SCRPA Production Execution Report

**Execution ID:** {self.results['execution_id']}
**Date:** {self.results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
**Status:** {self.results['status']}
**Total Time:** {total_time:.2f} seconds

## Execution Summary

**Steps Completed:** {len(self.results['steps_completed'])}/{len(self.results['steps_completed']) + len(self.results['steps_failed'])}

### Successful Steps:
"""
            
            for step in self.results['steps_completed']:
                summary_content += f"- ✅ {step.replace('_', ' ').title()}\n"
            
            if self.results['steps_failed']:
                summary_content += "\n### Failed Steps:\n"
                for step in self.results['steps_failed']:
                    summary_content += f"- ❌ {step.replace('_', ' ').title()}\n"
            
            # Add validation summary if available
            if self.results['validation_results']:
                val_results = self.results['validation_results']
                summary_content += f"""
## Validation Results

**Production Ready:** {val_results.get('ready_for_production', 'Unknown')}
**Validations Passed:** {val_results.get('validations_passed', 'Unknown')}
"""
            
            # Add dataset summary
            if self.results['final_datasets']:
                summary_content += "\n## Final Datasets\n\n"
                for dataset_name, dataset_info in self.results['final_datasets'].items():
                    summary_content += f"- **{dataset_name}:** {dataset_info['record_count']} records, {dataset_info['column_count']} columns\n"
            
            # Add errors if any
            if self.results['errors']:
                summary_content += "\n## Errors Encountered\n\n"
                for error in self.results['errors']:
                    summary_content += f"- ⚠️ {error}\n"
            
            # Add next steps
            summary_content += """
## Next Steps

### For Successful Execution:
1. Review validation results and address any warnings
2. Run spatial enhancement geocoding if needed
3. Update Power BI datasets with new data
4. Verify dashboard functionality

### For Failed Execution:
1. Review error details in the full JSON report
2. Check source data availability and quality
3. Verify system resources and permissions
4. Contact system administrator if needed

### Weekly Schedule Recommendations:
- Schedule execution for early morning (e.g., 6:00 AM)
- Allow 30-60 minutes processing window
- Set up email alerts for execution status
- Maintain 30-day backup retention policy
"""
            
            # Save summary report
            summary_path = self.project_path / '03_output' / f'production_summary_{self.results["execution_id"]}.md'
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            self.logger.info(f"Production reports generated:")
            self.logger.info(f"  JSON Report: {json_report_path}")
            self.logger.info(f"  Summary Report: {summary_path}")
            
            self.results['steps_completed'].append('generate_production_report')
            return str(summary_path)
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            self.results['steps_failed'].append('generate_production_report')
            self.results['errors'].append(f"Report generation error: {e}")
            return None

    def cleanup_temporary_files(self):
        """Clean up temporary files and optimize storage."""
        self.logger.info("Step 6: Cleaning up temporary files...")
        
        try:
            # Clean up old log files (keep last 30 days)
            log_dir = self.project_path / '03_output' / 'logs'
            if log_dir.exists():
                cutoff_date = datetime.now() - timedelta(days=30)
                
                old_files_removed = 0
                for log_file in log_dir.glob('*.log'):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        log_file.unlink()
                        old_files_removed += 1
                
                if old_files_removed > 0:
                    self.logger.info(f"  Removed {old_files_removed} old log files")
            
            # Clean up old backup directories (keep last 7 days)
            backup_base = self.project_path / 'backups'
            if backup_base.exists():
                cutoff_date = datetime.now() - timedelta(days=7)
                
                old_backups_removed = 0
                for backup_dir in backup_base.iterdir():
                    if backup_dir.is_dir() and backup_dir.stat().st_mtime < cutoff_date.timestamp():
                        shutil.rmtree(backup_dir)
                        old_backups_removed += 1
                
                if old_backups_removed > 0:
                    self.logger.info(f"  Removed {old_backups_removed} old backup directories")
            
            self.results['steps_completed'].append('cleanup_temporary_files')
            self.logger.info("Cleanup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            self.results['steps_failed'].append('cleanup_temporary_files')
            self.results['errors'].append(f"Cleanup error: {e}")
            return False

    def run_production_automation(self):
        """Run the complete production automation workflow."""
        self.logger.info("Starting SCRPA production automation workflow...")
        
        try:
            # Step 1: Backup existing outputs
            if not self.backup_existing_outputs():
                self.logger.error("Failed to backup existing outputs - continuing with caution")
            
            # Step 2: Run corrected pipeline
            pipeline_results = self.run_corrected_pipeline()
            if pipeline_results is None:
                self.logger.error("Pipeline execution failed - aborting automation")
                return self.finalize_execution()
            
            # Step 3: Validate outputs
            if not self.validate_pipeline_outputs():
                self.logger.error("Output validation failed - continuing with warnings")
            
            # Step 4: Prepare spatial datasets
            if not self.prepare_spatial_datasets():
                self.logger.error("Spatial preparation failed - continuing without spatial enhancement")
            
            # Step 5: Generate production report
            report_path = self.generate_production_report()
            if report_path is None:
                self.logger.error("Report generation failed")
            
            # Step 6: Cleanup
            if not self.cleanup_temporary_files():
                self.logger.error("Cleanup failed - manual cleanup may be required")
            
            return self.finalize_execution()
            
        except Exception as e:
            self.logger.error(f"Production automation failed: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.results['status'] = 'FAILED'
            self.results['errors'].append(f"Critical error: {e}")
            return self.finalize_execution()

    def finalize_execution(self):
        """Finalize execution and return results."""
        # Calculate final metrics
        end_time = datetime.now()
        total_time = (end_time - self.results['start_time']).total_seconds()
        
        self.results['end_time'] = end_time
        self.results['total_execution_time'] = total_time
        
        # Log final summary
        self.logger.info("="*80)
        self.logger.info("SCRPA PRODUCTION AUTOMATION COMPLETE")
        self.logger.info("="*80)
        self.logger.info(f"Execution ID: {self.results['execution_id']}")
        self.logger.info(f"Status: {self.results['status']}")
        self.logger.info(f"Total Time: {total_time:.2f} seconds")
        self.logger.info(f"Steps Completed: {len(self.results['steps_completed'])}")
        self.logger.info(f"Steps Failed: {len(self.results['steps_failed'])}")
        
        if self.results['errors']:
            self.logger.warning(f"Errors Encountered: {len(self.results['errors'])}")
            for error in self.results['errors']:
                self.logger.warning(f"  - {error}")
        
        self.logger.info("="*80)
        
        return self.results

def main():
    """Main execution function for standalone running."""
    try:
        automation = SCRPAProductionAutomation()
        results = automation.run_production_automation()
        
        # Print summary for console output
        print("\n" + "="*60)
        print("SCRPA PRODUCTION AUTOMATION RESULTS")
        print("="*60)
        print(f"Execution ID: {results['execution_id']}")
        print(f"Status: {results['status']}")
        print(f"Total Time: {results.get('total_execution_time', 0):.2f} seconds")
        print(f"Steps Completed: {len(results['steps_completed'])}")
        print(f"Steps Failed: {len(results['steps_failed'])}")
        
        if results['errors']:
            print(f"Errors: {len(results['errors'])}")
        
        # Exit with appropriate code
        if results['status'] == 'SUCCESS':
            print("✅ AUTOMATION COMPLETED SUCCESSFULLY")
            sys.exit(0)
        elif results['status'] == 'COMPLETED_WITH_ERRORS':
            print("⚠️ AUTOMATION COMPLETED WITH WARNINGS")
            sys.exit(1)
        else:
            print("❌ AUTOMATION FAILED")
            sys.exit(2)
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()