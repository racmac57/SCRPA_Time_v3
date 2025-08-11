#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_workflow.py

Complete PBIX processing workflow with integrated features:
- Multi-parameter updates in batch mode
- Environment-specific configurations
- Comprehensive logging and result tracking
- Automatic backup and rollback management
- JSON summary generation and consolidation
- Error recovery and retry mechanisms

Usage:
    # Single parameter update
    python main_workflow.py --pbix "SCRPA_Time_v2.pbix" --param "BasePath" --value "C:\\New\\Path"
    
    # Multiple parameters from JSON config
    python main_workflow.py --pbix "SCRPA_Time_v2.pbix" --config "workflow_config.json"
    
    # Environment-specific batch processing
    python main_workflow.py --environment "production" --batch-process
"""

import argparse
import json
import os
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from update_pbix_parameter import PBIXParameterUpdater, ConfigurationSummary
except ImportError as e:
    print(f"❌ ERROR: Could not import update_pbix_parameter.py: {e}")
    print("   Make sure update_pbix_parameter.py is in the same directory")
    sys.exit(1)

@dataclass
class WorkflowConfig:
    """Workflow configuration for batch processing."""
    pbix_files: List[str]
    parameters: Dict[str, str]
    environments: Dict[str, Dict[str, str]]
    output_directory: str = "workflow_output"
    backup_directory: str = "workflow_backups"
    log_directory: str = "workflow_logs"
    summary_directory: str = "workflow_summaries"
    retry_attempts: int = 3
    continue_on_error: bool = True
    create_individual_summaries: bool = True
    create_consolidated_summary: bool = True

@dataclass
class WorkflowResult:
    """Result of workflow processing."""
    workflow_id: str
    start_timestamp: str
    end_timestamp: str
    duration_seconds: float
    total_files: int
    successful_files: int
    failed_files: int
    total_parameters: int
    successful_parameters: int
    failed_parameters: int
    files_processed: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    backups_created: int
    rollbacks_performed: int
    config_summaries: List[str]
    consolidated_summary_path: str

class PBIXWorkflowManager:
    """Comprehensive PBIX workflow management system."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.workflow_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self.start_time = datetime.now()
        
        # Initialize directories
        self.output_dir = Path("workflow_output")
        self.backup_dir = Path("workflow_backups") 
        self.log_dir = Path("workflow_logs")
        self.summary_dir = Path("workflow_summaries")
        
        # Create directories
        for directory in [self.output_dir, self.backup_dir, self.log_dir, self.summary_dir]:
            directory.mkdir(exist_ok=True)
        
        # Setup workflow logging
        self._setup_workflow_logging()
        
        # Track workflow results
        self.files_processed: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.config_summaries: List[str] = []
        
    def _setup_workflow_logging(self):
        """Setup comprehensive workflow logging system."""
        log_filename = self.log_dir / f"workflow_{self.workflow_id}.log"
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [WORKFLOW:%(name)s] - %(message)s'
        )
        
        # Setup file handler
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO if self.verbose else logging.WARNING)
        console_handler.setFormatter(detailed_formatter)
        
        # Configure workflow logger
        self.logger = logging.getLogger('PBIXWorkflow')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.log_filename = log_filename
        self.logger.info(f"PBIX Workflow Manager initialized - ID: {self.workflow_id}")
    
    def load_workflow_config(self, config_path: str) -> WorkflowConfig:
        """Load workflow configuration from JSON file."""
        self.logger.info(f"Loading workflow configuration: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Convert to WorkflowConfig with defaults
            config = WorkflowConfig(
                pbix_files=config_data.get('pbix_files', []),
                parameters=config_data.get('parameters', {}),
                environments=config_data.get('environments', {}),
                output_directory=config_data.get('output_directory', 'workflow_output'),
                backup_directory=config_data.get('backup_directory', 'workflow_backups'),
                log_directory=config_data.get('log_directory', 'workflow_logs'),
                summary_directory=config_data.get('summary_directory', 'workflow_summaries'),
                retry_attempts=config_data.get('retry_attempts', 3),
                continue_on_error=config_data.get('continue_on_error', True),
                create_individual_summaries=config_data.get('create_individual_summaries', True),
                create_consolidated_summary=config_data.get('create_consolidated_summary', True)
            )
            
            self.logger.info(f"Configuration loaded: {len(config.pbix_files)} files, {len(config.parameters)} parameters")
            return config
            
        except Exception as e:
            error_msg = f"Failed to load workflow configuration: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            raise
    
    def create_sample_config(self, config_path: str):
        """Create a sample workflow configuration file."""
        sample_config = {
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
                },
                "test": {
                    "BasePath": "C:\\Test\\SCRPA_Time_v2",
                    "ServerName": "test-server",
                    "DatabaseName": "SCRPA_Test"
                }
            },
            "output_directory": "workflow_output",
            "backup_directory": "workflow_backups",
            "log_directory": "workflow_logs",
            "summary_directory": "workflow_summaries",
            "retry_attempts": 3,
            "continue_on_error": True,
            "create_individual_summaries": True,
            "create_consolidated_summary": True
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Sample configuration created: {config_path}")
            print(f"✅ Sample workflow configuration created: {config_path}")
            print("   Edit this file to customize your workflow parameters")
            
        except Exception as e:
            error_msg = f"Failed to create sample configuration: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def process_single_file(self, pbix_file: str, parameters: Dict[str, str], 
                          environment: str = None, retry_attempts: int = 3) -> Dict[str, Any]:
        """Process a single PBIX file with multiple parameters."""
        file_result = {
            'file': pbix_file,
            'environment': environment,
            'start_timestamp': datetime.now().isoformat(),
            'success': False,
            'parameters_processed': [],
            'parameters_successful': 0,
            'parameters_failed': 0,
            'backups_created': 0,
            'rollbacks_performed': 0,
            'config_summary_path': None,
            'errors': [],
            'warnings': [],
            'retry_attempts_used': 0
        }
        
        self.logger.info(f"Processing file: {os.path.basename(pbix_file)}")
        
        try:
            # Validate input file exists
            if not os.path.exists(pbix_file):
                raise FileNotFoundError(f"PBIX file not found: {pbix_file}")
            
            # Create output filename with environment suffix
            pbix_path = Path(pbix_file)
            env_suffix = f"_{environment}" if environment else "_updated"
            output_filename = f"{pbix_path.stem}{env_suffix}_{self.workflow_id}{pbix_path.suffix}"
            output_path = self.output_dir / output_filename
            
            # Process parameters sequentially (each update builds on the previous)
            current_input = pbix_file
            successful_params = 0
            
            for param_name, param_value in parameters.items():
                param_result = {
                    'parameter': param_name,
                    'value': param_value,
                    'success': False,
                    'attempts': 0,
                    'error': None
                }
                
                # Try updating this parameter with retry logic
                for attempt in range(1, retry_attempts + 1):
                    param_result['attempts'] = attempt
                    file_result['retry_attempts_used'] = max(file_result['retry_attempts_used'], attempt)
                    
                    try:
                        self.logger.info(f"Updating parameter '{param_name}' (attempt {attempt})")
                        
                        # Create temporary output for this parameter
                        temp_output = self.output_dir / f"temp_{param_name}_{self.workflow_id}.pbix"
                        
                        # Create PBIX updater
                        updater = PBIXParameterUpdater(verbose=self.verbose)
                        
                        # Process with validation
                        result = updater.process_pbix_with_validation(
                            current_input, str(temp_output), param_name, param_value
                        )
                        
                        if result['success']:
                            param_result['success'] = True
                            successful_params += 1
                            
                            # Move temp output to be input for next parameter
                            if current_input != pbix_file and os.path.exists(current_input):
                                os.remove(current_input)  # Clean up previous temp file
                            
                            current_input = str(temp_output)
                            
                            # Track backup and rollback info
                            if result.get('backup_info'):
                                file_result['backups_created'] += 1
                            if result.get('rollback_performed'):
                                file_result['rollbacks_performed'] += 1
                            
                            self.logger.info(f"Parameter '{param_name}' updated successfully")
                            break
                            
                        else:
                            param_result['error'] = '; '.join(result.get('errors', ['Unknown error']))
                            self.logger.warning(f"Parameter '{param_name}' update failed: {param_result['error']}")
                            
                            # Clean up temp file on failure
                            if os.path.exists(temp_output):
                                os.remove(temp_output)
                    
                    except Exception as e:
                        param_result['error'] = str(e)
                        self.logger.error(f"Parameter '{param_name}' update attempt {attempt} failed: {e}")
                        
                        # Clean up temp file on exception
                        temp_output = self.output_dir / f"temp_{param_name}_{self.workflow_id}.pbix"
                        if os.path.exists(temp_output):
                            os.remove(temp_output)
                
                file_result['parameters_processed'].append(param_result)
                
                if not param_result['success']:
                    file_result['parameters_failed'] += 1
                    file_result['errors'].append(f"Parameter '{param_name}': {param_result['error']}")
            
            # Move final result to output location
            if successful_params > 0 and current_input != pbix_file:
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rename(current_input, output_path)
                file_result['output_file'] = str(output_path)
                self.logger.info(f"Final output saved: {output_filename}")
            
            file_result['parameters_successful'] = successful_params
            file_result['success'] = successful_params > 0
            file_result['end_timestamp'] = datetime.now().isoformat()
            
            # Generate individual summary if requested
            if successful_params > 0:
                summary_filename = f"summary_{pbix_path.stem}_{self.workflow_id}.json"
                summary_path = self.summary_dir / summary_filename
                
                # Create a final updater instance to generate summary
                final_updater = PBIXParameterUpdater(verbose=False)
                
                # Create mock result for summary generation
                mock_result = {
                    'success': file_result['success'],
                    'session_id': self.workflow_id,
                    'parameters_processed': file_result['parameters_processed'],
                    'backups_created': file_result['backups_created'],
                    'rollbacks_performed': file_result['rollbacks_performed'],
                    'errors': file_result['errors'],
                    'warnings': file_result['warnings']
                }
                
                try:
                    summary = final_updater.generate_configuration_summary(
                        mock_result, pbix_file, str(output_path), str(summary_path)
                    )
                    file_result['config_summary_path'] = str(summary_path)
                    self.config_summaries.append(str(summary_path))
                    
                except Exception as e:
                    self.logger.warning(f"Could not generate individual summary: {e}")
            
        except Exception as e:
            file_result['success'] = False
            file_result['end_timestamp'] = datetime.now().isoformat()
            error_msg = f"File processing failed: {e}"
            file_result['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        return file_result
    
    def process_batch(self, config: WorkflowConfig, environment: str = None) -> WorkflowResult:
        """Process multiple PBIX files in batch mode."""
        self.logger.info(f"Starting batch processing: {len(config.pbix_files)} files")
        
        # Determine parameters to use
        if environment and environment in config.environments:
            parameters = config.environments[environment]
            self.logger.info(f"Using environment '{environment}' parameters")
        else:
            parameters = config.parameters
            self.logger.info("Using default parameters")
        
        # Process each file
        successful_files = 0
        failed_files = 0
        total_parameters = 0
        successful_parameters = 0
        failed_parameters = 0
        total_backups = 0
        total_rollbacks = 0
        
        for pbix_file in config.pbix_files:
            try:
                file_result = self.process_single_file(
                    pbix_file, parameters, environment, config.retry_attempts
                )
                
                self.files_processed.append(file_result)
                
                # Update counters
                total_parameters += len(parameters)
                successful_parameters += file_result['parameters_successful']
                failed_parameters += file_result['parameters_failed']
                total_backups += file_result['backups_created']
                total_rollbacks += file_result['rollbacks_performed']
                
                if file_result['success']:
                    successful_files += 1
                    self.logger.info(f"✅ File processed successfully: {os.path.basename(pbix_file)}")
                else:
                    failed_files += 1
                    self.logger.error(f"❌ File processing failed: {os.path.basename(pbix_file)}")
                    
                    # Add errors to workflow errors
                    self.errors.extend(file_result['errors'])
                    
                    # Stop on error if configured to do so
                    if not config.continue_on_error:
                        self.logger.error("Stopping batch processing due to error")
                        break
                
            except Exception as e:
                failed_files += 1
                error_msg = f"Critical error processing {pbix_file}: {e}"
                self.logger.error(error_msg)
                self.errors.append(error_msg)
                
                if not config.continue_on_error:
                    break
        
        # Create workflow result
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        workflow_result = WorkflowResult(
            workflow_id=self.workflow_id,
            start_timestamp=self.start_time.isoformat(),
            end_timestamp=end_time.isoformat(),
            duration_seconds=round(duration, 3),
            total_files=len(config.pbix_files),
            successful_files=successful_files,
            failed_files=failed_files,
            total_parameters=total_parameters,
            successful_parameters=successful_parameters,
            failed_parameters=failed_parameters,
            files_processed=self.files_processed,
            errors=self.errors,
            warnings=self.warnings,
            backups_created=total_backups,
            rollbacks_performed=total_rollbacks,
            config_summaries=self.config_summaries,
            consolidated_summary_path=""
        )
        
        # Generate consolidated summary
        if config.create_consolidated_summary:
            consolidated_path = self._generate_consolidated_summary(workflow_result)
            workflow_result.consolidated_summary_path = consolidated_path
        
        return workflow_result
    
    def _generate_consolidated_summary(self, workflow_result: WorkflowResult) -> str:
        """Generate consolidated summary of entire workflow."""
        summary_path = self.summary_dir / f"consolidated_summary_{self.workflow_id}.json"
        
        try:
            # Create comprehensive consolidated summary
            consolidated_summary = {
                "workflow_summary": asdict(workflow_result),
                "system_info": {
                    "workflow_id": self.workflow_id,
                    "log_file": str(self.log_filename),
                    "output_directory": str(self.output_dir),
                    "backup_directory": str(self.backup_dir),
                    "summary_directory": str(self.summary_dir)
                },
                "detailed_file_results": self.files_processed,
                "performance_metrics": {
                    "total_duration": workflow_result.duration_seconds,
                    "average_time_per_file": workflow_result.duration_seconds / max(workflow_result.total_files, 1),
                    "success_rate": (workflow_result.successful_files / max(workflow_result.total_files, 1)) * 100,
                    "parameter_success_rate": (workflow_result.successful_parameters / max(workflow_result.total_parameters, 1)) * 100
                },
                "file_summaries": []
            }
            
            # Add individual file summaries if they exist
            for summary_path_str in self.config_summaries:
                try:
                    with open(summary_path_str, 'r', encoding='utf-8') as f:
                        individual_summary = json.load(f)
                        consolidated_summary["file_summaries"].append({
                            "summary_file": summary_path_str,
                            "file_info": individual_summary.get("input_file", {}),
                            "success": individual_summary.get("success", False),
                            "parameters": individual_summary.get("parameters", []),
                            "errors": individual_summary.get("errors", [])
                        })
                except Exception as e:
                    self.logger.warning(f"Could not include individual summary {summary_path_str}: {e}")
            
            # Save consolidated summary
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(consolidated_summary, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Consolidated summary generated: {summary_path}")
            return str(summary_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate consolidated summary: {e}")
            return ""
    
    def print_workflow_summary(self, workflow_result: WorkflowResult):
        """Print comprehensive workflow summary to console."""
        print(f"\n{'='*80}")
        print("PBIX WORKFLOW PROCESSING SUMMARY")
        print(f"{'='*80}")
        print(f"Workflow ID: {workflow_result.workflow_id}")
        print(f"Duration: {workflow_result.duration_seconds:.3f} seconds")
        print(f"Files: {workflow_result.successful_files}/{workflow_result.total_files} successful")
        print(f"Parameters: {workflow_result.successful_parameters}/{workflow_result.total_parameters} successful")
        print(f"Backups Created: {workflow_result.backups_created}")
        print(f"Rollbacks Performed: {workflow_result.rollbacks_performed}")
        
        # File-by-file summary
        print(f"\nFILE PROCESSING RESULTS:")
        for file_result in workflow_result.files_processed:
            status = "✅" if file_result['success'] else "❌"
            filename = os.path.basename(file_result['file'])
            params_status = f"{file_result['parameters_successful']}/{len(file_result['parameters_processed'])}"
            print(f"  {status} {filename}: {params_status} parameters")
            
            if file_result['errors'] and self.verbose:
                for error in file_result['errors'][:2]:  # Show first 2 errors
                    print(f"     • {error}")
        
        # Overall status
        if workflow_result.successful_files == workflow_result.total_files:
            print(f"\n✅ ALL FILES PROCESSED SUCCESSFULLY!")
        else:
            print(f"\n⚠️  {workflow_result.failed_files} FILES FAILED")
        
        # File locations
        print(f"\nOUTPUT LOCATIONS:")
        print(f"  Logs: {self.log_filename}")
        print(f"  Output Files: {self.output_dir}")
        print(f"  Backups: {self.backup_dir}")
        print(f"  Summaries: {self.summary_dir}")
        
        if workflow_result.consolidated_summary_path:
            print(f"  Consolidated Summary: {workflow_result.consolidated_summary_path}")

def main():
    """Main workflow execution function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive PBIX Workflow Processing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file, single parameter
  python main_workflow.py --pbix "SCRPA_Time_v2.pbix" --param "BasePath" --value "C:\\New\\Path"
  
  # Single file, multiple parameters from config
  python main_workflow.py --pbix "SCRPA_Time_v2.pbix" --config "workflow_config.json"
  
  # Batch processing with environment
  python main_workflow.py --config "workflow_config.json" --environment "production"
  
  # Create sample configuration
  python main_workflow.py --create-sample-config "my_workflow.json"
        """
    )
    
    # Configuration options
    parser.add_argument('--config', '-c', help="Path to workflow configuration JSON file")
    parser.add_argument('--create-sample-config', help="Create a sample configuration file at specified path")
    
    # Single file processing
    parser.add_argument('--pbix', help="Single PBIX file to process")
    parser.add_argument('--param', help="Single parameter name to update")
    parser.add_argument('--value', help="Single parameter value")
    
    # Environment and batch processing
    parser.add_argument('--environment', '-e', help="Environment configuration to use")
    parser.add_argument('--batch-process', action='store_true', help="Enable batch processing mode")
    
    # Options
    parser.add_argument('--verbose', '-v', action='store_true', help="Enable verbose output")
    parser.add_argument('--continue-on-error', action='store_true', default=True, help="Continue processing other files on error")
    parser.add_argument('--retry-attempts', type=int, default=3, help="Number of retry attempts per parameter")
    
    args = parser.parse_args()
    
    try:
        # Create sample configuration if requested
        if args.create_sample_config:
            workflow_manager = PBIXWorkflowManager(verbose=True)
            workflow_manager.create_sample_config(args.create_sample_config)
            return 0
        
        print("COMPREHENSIVE PBIX WORKFLOW PROCESSING TOOL")
        print("=" * 80)
        
        # Create workflow manager
        workflow_manager = PBIXWorkflowManager(verbose=args.verbose)
        
        # Determine processing mode
        if args.config:
            # Configuration-based processing
            config = workflow_manager.load_workflow_config(args.config)
            
            # Override config with command line options
            if args.retry_attempts != 3:
                config.retry_attempts = args.retry_attempts
            if not args.continue_on_error:
                config.continue_on_error = False
            
            # Process batch
            workflow_result = workflow_manager.process_batch(config, args.environment)
            
        elif args.pbix and args.param and args.value:
            # Single file, single parameter processing
            print(f"Processing single file: {args.pbix}")
            print(f"Parameter: {args.param} = {args.value}")
            
            # Create minimal config
            config = WorkflowConfig(
                pbix_files=[args.pbix],
                parameters={args.param: args.value},
                environments={},
                retry_attempts=args.retry_attempts,
                continue_on_error=args.continue_on_error
            )
            
            workflow_result = workflow_manager.process_batch(config, args.environment)
            
        else:
            print("❌ ERROR: Must specify either --config or (--pbix, --param, --value)")
            print("Use --help for usage information")
            return 1
        
        # Print results
        workflow_manager.print_workflow_summary(workflow_result)
        
        # Return appropriate exit code
        if workflow_result.failed_files == 0:
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"\n❌ CRITICAL WORKFLOW ERROR: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())