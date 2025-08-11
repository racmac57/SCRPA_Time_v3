# 2025-08-01-00-00-00
# SCRPA_Time_v2/SCRPA_Automated_Geocoding_Complete
# Author: R. A. Carucci
# Purpose: Fully automated ArcPy geocoding script for SCRPA spatial enhancement

import arcpy
import pandas as pd
import numpy as np
import os
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime
import logging
import json
import traceback

class SCRPAAutomatedGeocoding:
    """
    Fully automated SCRPA geocoding system using ArcPy and NJ_Geocode service.
    
    Features:
    - Complete end-to-end automation (no manual steps)
    - Template project integration
    - Batch processing with error handling
    - Automatic dataset enhancement
    - Comprehensive reporting and validation
    - Single-script execution
    """
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)
        
        # System paths
        self.template_path = self.project_path / "10_Refrence_Files" / "7_Day_Templet_SCRPA_Time.aprx"
        self.output_dir = self.project_path / '04_powerbi'
        self.geocoding_dir = self.project_path / 'geocoding_input'
        self.temp_workspace = self.project_path / 'temp_geocoding_auto'
        
        # Processing parameters
        self.batch_size = 50
        self.target_srid = 3424  # State Plane NJ
        self.geocode_service = str(self.project_path / "10_Refrence_Files" / "NJ_Geocode.loc")
        
        # Create temporary workspace
        self.temp_workspace.mkdir(exist_ok=True)
        
        # Results tracking
        self.automation_results = {
            'execution_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'start_time': datetime.now(),
            'total_addresses': 0,
            'successful_geocodes': 0,
            'failed_geocodes': 0,
            'high_accuracy_geocodes': 0,  # Score >= 90
            'medium_accuracy_geocodes': 0,  # Score 80-89
            'processing_time': 0,
            'datasets_enhanced': [],
            'validation_results': {},
            'error_log': [],
            'status': 'RUNNING'
        }
        
        self.setup_logging()
        self.setup_arcgis_environment()

    def setup_logging(self):
        """Setup comprehensive logging for automated execution."""
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"automated_geocoding_{self.automation_results['execution_id']}.log"
        
        # Setup logging with both file and console handlers
        self.logger = logging.getLogger('SCRPAAutomatedGeocoding')
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # File handler
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        self.logger.info("="*80)
        self.logger.info(f"SCRPA AUTOMATED GEOCODING - {self.automation_results['execution_id']}")
        self.logger.info("="*80)

    def setup_arcgis_environment(self):
        """Setup ArcGIS environment and validate prerequisites."""
        self.logger.info("Setting up ArcGIS environment...")
        
        try:
            # Set workspace to temporary directory
            arcpy.env.workspace = str(self.temp_workspace)
            arcpy.env.overwriteOutput = True
            
            # Set spatial reference
            self.spatial_reference = arcpy.SpatialReference(self.target_srid)
            arcpy.env.outputCoordinateSystem = self.spatial_reference
            
            self.logger.info(f"Workspace set: {arcpy.env.workspace}")
            self.logger.info(f"Coordinate system: {self.spatial_reference.name} (EPSG:{self.target_srid})")
            
            # Validate template exists
            if not self.template_path.exists():
                raise FileNotFoundError(f"ArcGIS Pro template not found: {self.template_path}")
            
            self.logger.info(f"Template validated: {self.template_path}")
            
            # Test NJ_Geocode service accessibility
            try:
                # This will raise an exception if service is not available
                geocode_desc = arcpy.geocoding.DescribeGeocodeService(self.geocode_service)
                self.logger.info(f"NJ_Geocode service validated: {geocode_desc}")
            except Exception as e:
                self.logger.warning(f"NJ_Geocode service validation failed: {e}")
                self.logger.info("Continuing with assumption that service will be available during execution")
            
            return True
            
        except Exception as e:
            self.logger.error(f"ArcGIS environment setup failed: {e}")
            self.automation_results['error_log'].append(f"Environment setup failed: {e}")
            return False

    def create_processing_geodatabase(self):
        """Create temporary geodatabase for processing."""
        self.logger.info("Creating processing geodatabase...")
        
        try:
            # Create geodatabase
            gdb_name = f"SCRPA_Geocoding_{self.automation_results['execution_id']}.gdb"
            self.processing_gdb = str(self.temp_workspace / gdb_name)
            
            # Remove existing if present
            if arcpy.Exists(self.processing_gdb):
                arcpy.Delete_management(self.processing_gdb)
            
            # Create new geodatabase
            arcpy.CreateFileGDB_management(str(self.temp_workspace), gdb_name)
            
            # Set as workspace
            arcpy.env.workspace = self.processing_gdb
            
            self.logger.info(f"Processing geodatabase created: {self.processing_gdb}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create processing geodatabase: {e}")
            self.automation_results['error_log'].append(f"Geodatabase creation failed: {e}")
            return False

    def import_address_data(self):
        """Import master address list to geodatabase table."""
        self.logger.info("Importing address data...")
        
        try:
            # Check if master address file exists
            master_file = self.geocoding_dir / 'master_address_list.csv'
            if not master_file.exists():
                raise FileNotFoundError(f"Master address file not found: {master_file}")
            
            # Import CSV to geodatabase table
            address_table = "SCRPA_Addresses_Master"
            
            arcpy.conversion.TableToTable(
                in_rows=str(master_file),
                out_path=self.processing_gdb,
                out_name=address_table
            )
            
            # Verify import
            result = arcpy.GetCount_management(address_table)
            record_count = int(result.getOutput(0))
            
            self.automation_results['total_addresses'] = record_count
            self.logger.info(f"Address data imported successfully: {record_count} records")
            
            # Validate required fields
            field_names = [f.name for f in arcpy.ListFields(address_table)]
            required_fields = ['Address', 'AddressID']
            
            for field in required_fields:
                if field not in field_names:
                    raise ValueError(f"Required field '{field}' not found in address table")
            
            self.logger.info(f"Required fields validated: {required_fields}")
            
            self.address_table = address_table
            return True
            
        except Exception as e:
            self.logger.error(f"Address data import failed: {e}")
            self.automation_results['error_log'].append(f"Address import failed: {e}")
            return False

    def execute_batch_geocoding(self):
        """Execute automated batch geocoding using NJ_Geocode service."""
        self.logger.info("Executing automated batch geocoding...")
        
        try:
            # Output feature class for geocoding results
            geocoded_fc = "SCRPA_Geocoded_Results"
            
            self.logger.info(f"Starting geocoding of {self.automation_results['total_addresses']} addresses...")
            self.logger.info(f"Using service: {self.geocode_service}")
            
            # Execute geocoding
            start_time = time.time()
            
            arcpy.geocoding.GeocodeAddresses(
                in_table=self.address_table,
                address_locator=self.geocode_service,
                in_address_fields="Address Address VISIBLE NONE",
                out_feature_class=geocoded_fc,
                out_relationship_type="STATIC"
            )
            
            geocoding_time = time.time() - start_time
            
            # Verify results
            result = arcpy.GetCount_management(geocoded_fc)
            geocoded_count = int(result.getOutput(0))
            
            self.logger.info(f"Geocoding completed in {geocoding_time:.2f} seconds")
            self.logger.info(f"Geocoded records: {geocoded_count}")
            
            # Analyze geocoding quality
            self.analyze_geocoding_quality(geocoded_fc)
            
            self.geocoded_fc = geocoded_fc
            self.automation_results['processing_time'] = geocoding_time
            
            return True
            
        except Exception as e:
            self.logger.error(f"Batch geocoding failed: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.automation_results['error_log'].append(f"Geocoding failed: {e}")
            return False

    def analyze_geocoding_quality(self, geocoded_fc):
        """Analyze geocoding results and generate quality metrics."""
        self.logger.info("Analyzing geocoding quality...")
        
        try:
            # Extract scores and analyze quality
            scores = []
            statuses = []
            
            with arcpy.da.SearchCursor(geocoded_fc, ["Score", "Status"]) as cursor:
                for row in cursor:
                    if row[0] is not None:
                        scores.append(row[0])
                        statuses.append(row[1] if row[1] else 'UNKNOWN')
            
            # Calculate statistics
            total_geocoded = len(scores)
            
            if total_geocoded > 0:
                high_accuracy = sum(1 for s in scores if s >= 90)
                medium_accuracy = sum(1 for s in scores if 80 <= s < 90)
                low_accuracy = sum(1 for s in scores if s < 80)
                
                successful_geocodes = high_accuracy + medium_accuracy
                failed_geocodes = total_geocoded - successful_geocodes
                
                # Update results
                self.automation_results['successful_geocodes'] = successful_geocodes
                self.automation_results['failed_geocodes'] = failed_geocodes
                self.automation_results['high_accuracy_geocodes'] = high_accuracy
                self.automation_results['medium_accuracy_geocodes'] = medium_accuracy
                
                # Calculate rates
                success_rate = (successful_geocodes / total_geocoded) * 100
                high_accuracy_rate = (high_accuracy / total_geocoded) * 100
                
                self.logger.info("Geocoding Quality Analysis:")
                self.logger.info(f"  Total processed: {total_geocoded}")
                self.logger.info(f"  Successful (>=80): {successful_geocodes} ({success_rate:.1f}%)")
                self.logger.info(f"  High accuracy (>=90): {high_accuracy} ({high_accuracy_rate:.1f}%)")
                self.logger.info(f"  Medium accuracy (80-89): {medium_accuracy}")
                self.logger.info(f"  Low accuracy (<80): {low_accuracy}")
                
                # Validation against targets
                if success_rate >= 85:
                    self.logger.info("SUCCESS CRITERIA MET: Geocoding success rate >= 85%")
                else:
                    self.logger.warning(f"SUCCESS CRITERIA NOT MET: Success rate {success_rate:.1f}% < 85%")
                
                if high_accuracy_rate >= 70:
                    self.logger.info("QUALITY CRITERIA MET: High accuracy rate >= 70%")
                else:
                    self.logger.warning(f"QUALITY CRITERIA NOT MET: High accuracy rate {high_accuracy_rate:.1f}% < 70%")
            
            else:
                self.logger.error("No geocoding results found for analysis")
                self.automation_results['error_log'].append("No geocoding results for quality analysis")
            
        except Exception as e:
            self.logger.error(f"Quality analysis failed: {e}")
            self.automation_results['error_log'].append(f"Quality analysis failed: {e}")

    def export_geocoding_results(self):
        """Export geocoding results to CSV for integration."""
        self.logger.info("Exporting geocoding results...")
        
        try:
            # Output CSV file
            results_csv = self.geocoding_dir / "geocoding_results.csv"
            
            # Export feature class to CSV
            arcpy.conversion.TableToTable(
                in_table=self.geocoded_fc,
                out_path=str(self.geocoding_dir),
                out_name="geocoding_results.csv"
            )
            
            # Verify export
            if results_csv.exists():
                # Read and validate CSV
                results_df = pd.read_csv(results_csv)
                export_count = len(results_df)
                
                self.logger.info(f"Geocoding results exported: {results_csv}")
                self.logger.info(f"Exported records: {export_count}")
                
                # Show sample results
                if export_count > 0:
                    self.logger.info("Sample geocoding results:")
                    sample_results = results_df[['Address', 'SHAPE_X', 'SHAPE_Y', 'Score', 'Status']].head(3)
                    for _, row in sample_results.iterrows():
                        self.logger.info(f"  {row['Address'][:40]}... -> ({row['SHAPE_X']:.2f}, {row['SHAPE_Y']:.2f}) Score: {row['Score']}")
                
                return True
            else:
                raise FileNotFoundError("Geocoding results CSV was not created")
                
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            self.automation_results['error_log'].append(f"Export failed: {e}")
            return False

    def enhance_scrpa_datasets(self):
        """Automatically enhance SCRPA datasets with geocoding results."""
        self.logger.info("Enhancing SCRPA datasets with spatial coordinates...")
        
        try:
            # Load geocoding results
            results_csv = self.geocoding_dir / "geocoding_results.csv"
            if not results_csv.exists():
                raise FileNotFoundError(f"Geocoding results not found: {results_csv}")
            
            geocoding_df = pd.read_csv(results_csv)
            self.logger.info(f"Loaded {len(geocoding_df)} geocoding results")
            
            # Create address lookup dictionary
            lookup = {}
            for _, row in geocoding_df.iterrows():
                address = row.get('Address', '')
                lookup[address] = {
                    'x_coord': row.get('SHAPE_X', None),
                    'y_coord': row.get('SHAPE_Y', None),
                    'geocode_score': row.get('Score', 0),
                    'geocode_status': row.get('Status', 'UNKNOWN'),
                    'match_address': row.get('Match_addr', '')
                }
            
            # Target datasets to enhance
            target_datasets = [
                'cad_data_standardized.csv',
                'rms_data_standardized.csv',
                'cad_rms_matched_standardized.csv'
            ]
            
            enhancement_results = []
            
            for dataset_file in target_datasets:
                result = self.enhance_single_dataset(dataset_file, lookup)
                if result:
                    enhancement_results.append(result)
            
            self.automation_results['datasets_enhanced'] = enhancement_results
            
            if enhancement_results:
                self.logger.info(f"Successfully enhanced {len(enhancement_results)} datasets")
                return True
            else:
                self.logger.error("No datasets were successfully enhanced")
                return False
                
        except Exception as e:
            self.logger.error(f"Dataset enhancement failed: {e}")
            self.automation_results['error_log'].append(f"Dataset enhancement failed: {e}")
            return False

    def enhance_single_dataset(self, dataset_file, geocoding_lookup):
        """Enhance a single dataset with geocoding results."""
        try:
            file_path = self.output_dir / dataset_file
            
            if not file_path.exists():
                self.logger.warning(f"Dataset not found: {dataset_file}")
                return None
            
            self.logger.info(f"Enhancing {dataset_file}...")
            
            # Read dataset
            df = pd.read_csv(file_path)
            original_count = len(df)
            
            # Add spatial columns if they don't exist
            spatial_columns = ['x_coord', 'y_coord', 'geocode_score', 'geocode_status', 'match_address']
            for col in spatial_columns:
                if col not in df.columns:
                    df[col] = None
            
            # Match addresses and populate coordinates
            matched_count = 0
            
            if 'location' in df.columns:
                for idx, address in df['location'].items():
                    if pd.notna(address) and str(address) in geocoding_lookup:
                        result = geocoding_lookup[str(address)]
                        
                        # Convert data types appropriately
                        df.at[idx, 'x_coord'] = float(result['x_coord']) if result['x_coord'] is not None else None
                        df.at[idx, 'y_coord'] = float(result['y_coord']) if result['y_coord'] is not None else None
                        df.at[idx, 'geocode_score'] = float(result['geocode_score']) if result['geocode_score'] else 0.0
                        df.at[idx, 'geocode_status'] = str(result['geocode_status']) if result['geocode_status'] else ''
                        df.at[idx, 'match_address'] = str(result['match_address']) if result['match_address'] else ''
                        
                        matched_count += 1
            
            # Calculate enhancement statistics
            geocoded_count = df['x_coord'].notna().sum()
            enhancement_rate = (geocoded_count / original_count) * 100 if original_count > 0 else 0
            
            # Overwrite original file with enhanced version (as requested)
            df.to_csv(file_path, index=False)
            
            self.logger.info(f"  {dataset_file} enhanced:")
            self.logger.info(f"    - Original records: {original_count}")
            self.logger.info(f"    - Geocoded records: {int(geocoded_count)}")
            self.logger.info(f"    - Enhancement rate: {enhancement_rate:.1f}%")
            self.logger.info(f"    - Original file overwritten with enhanced data")
            
            return {
                'dataset': dataset_file,
                'original_records': original_count,
                'geocoded_records': int(geocoded_count),
                'enhancement_rate': enhancement_rate,
                'addresses_matched': matched_count
            }
            
        except Exception as e:
            self.logger.error(f"Failed to enhance {dataset_file}: {e}")
            self.automation_results['error_log'].append(f"Enhancement failed for {dataset_file}: {e}")
            return None

    def validate_enhanced_datasets(self):
        """Validate enhanced datasets for coordinate data quality."""
        self.logger.info("Validating enhanced datasets...")
        
        validation_results = {
            'validation_timestamp': datetime.now().isoformat(),
            'datasets_validated': [],
            'overall_status': 'PASS',
            'issues_found': []
        }
        
        try:
            target_datasets = [
                'cad_data_standardized.csv',
                'rms_data_standardized.csv',
                'cad_rms_matched_standardized.csv'
            ]
            
            for dataset_file in target_datasets:
                dataset_validation = self.validate_single_dataset(dataset_file)
                if dataset_validation:
                    validation_results['datasets_validated'].append(dataset_validation)
                    
                    # Check for issues
                    if dataset_validation['enhancement_rate'] < 70:  # Less than 70% geocoded
                        validation_results['issues_found'].append(f"{dataset_file}: Low enhancement rate ({dataset_validation['enhancement_rate']:.1f}%)")
                        validation_results['overall_status'] = 'WARNING'
            
            # Coordinate bounds validation (Bergen County, NJ approximate bounds)
            nj_bounds = {
                'x_min': 630000,
                'x_max': 650000,
                'y_min': 750000,
                'y_max': 780000
            }
            
            self.validate_coordinate_bounds(nj_bounds, validation_results)
            
            self.automation_results['validation_results'] = validation_results
            
            self.logger.info(f"Validation completed: {validation_results['overall_status']}")
            if validation_results['issues_found']:
                for issue in validation_results['issues_found']:
                    self.logger.warning(f"  Issue: {issue}")
            
            return validation_results['overall_status'] in ['PASS', 'WARNING']
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            self.automation_results['error_log'].append(f"Validation failed: {e}")
            return False

    def validate_single_dataset(self, dataset_file):
        """Validate a single enhanced dataset."""
        try:
            file_path = self.output_dir / dataset_file
            
            if not file_path.exists():
                return None
            
            df = pd.read_csv(file_path)
            
            # Check for spatial columns
            spatial_columns = ['x_coord', 'y_coord', 'geocode_score', 'geocode_status', 'match_address']
            missing_columns = [col for col in spatial_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.warning(f"{dataset_file}: Missing spatial columns: {missing_columns}")
            
            # Calculate statistics
            total_records = len(df)
            geocoded_records = df['x_coord'].notna().sum()
            enhancement_rate = (geocoded_records / total_records) * 100 if total_records > 0 else 0
            
            # Score statistics
            scores = df['geocode_score'].dropna()
            avg_score = scores.mean() if len(scores) > 0 else 0
            high_accuracy_count = sum(1 for s in scores if s >= 90)
            
            validation_result = {
                'dataset': dataset_file,
                'total_records': total_records,
                'geocoded_records': int(geocoded_records),
                'enhancement_rate': enhancement_rate,
                'average_score': avg_score,
                'high_accuracy_count': high_accuracy_count,
                'spatial_columns_present': len(missing_columns) == 0
            }
            
            self.logger.info(f"  {dataset_file}: {geocoded_records}/{total_records} geocoded ({enhancement_rate:.1f}%)")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Failed to validate {dataset_file}: {e}")
            return None

    def validate_coordinate_bounds(self, bounds, validation_results):
        """Validate that coordinates are within expected bounds."""
        try:
            out_of_bounds_count = 0
            
            target_datasets = [
                'cad_data_standardized.csv',
                'rms_data_standardized.csv',
                'cad_rms_matched_standardized.csv'
            ]
            
            for dataset_file in target_datasets:
                file_path = self.output_dir / dataset_file
                
                if file_path.exists():
                    df = pd.read_csv(file_path)
                    
                    if 'x_coord' in df.columns and 'y_coord' in df.columns:
                        # Check coordinates within bounds
                        valid_coords = df[df['x_coord'].notna() & df['y_coord'].notna()]
                        
                        if len(valid_coords) > 0:
                            out_of_bounds = valid_coords[
                                (valid_coords['x_coord'] < bounds['x_min']) |
                                (valid_coords['x_coord'] > bounds['x_max']) |
                                (valid_coords['y_coord'] < bounds['y_min']) |
                                (valid_coords['y_coord'] > bounds['y_max'])
                            ]
                            
                            out_of_bounds_count += len(out_of_bounds)
                            
                            if len(out_of_bounds) > 0:
                                validation_results['issues_found'].append(
                                    f"{dataset_file}: {len(out_of_bounds)} coordinates outside expected bounds"
                                )
            
            if out_of_bounds_count > 0:
                self.logger.warning(f"Found {out_of_bounds_count} coordinates outside expected bounds")
            else:
                self.logger.info("All coordinates within expected Bergen County bounds")
                
        except Exception as e:
            self.logger.warning(f"Coordinate bounds validation failed: {e}")

    def cleanup_processing_files(self):
        """Clean up temporary processing files."""
        self.logger.info("Cleaning up temporary processing files...")
        
        try:
            # Remove processing geodatabase
            if hasattr(self, 'processing_gdb') and arcpy.Exists(self.processing_gdb):
                arcpy.Delete_management(self.processing_gdb)
                self.logger.info("Processing geodatabase removed")
            
            # Keep geocoding results CSV for reference
            results_csv = self.geocoding_dir / "geocoding_results.csv"
            if results_csv.exists():
                self.logger.info(f"Geocoding results preserved: {results_csv}")
            
            # Remove other temporary files if needed
            temp_files = list(self.temp_workspace.glob("*.lock"))
            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                except:
                    pass  # Ignore lock file removal errors
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Cleanup warning: {e}")
            return False

    def generate_automation_report(self):
        """Generate comprehensive automation report."""
        self.logger.info("Generating automation report...")
        
        try:
            # Calculate final statistics
            end_time = datetime.now()
            total_time = (end_time - self.automation_results['start_time']).total_seconds()
            
            self.automation_results['end_time'] = end_time
            self.automation_results['total_processing_time'] = total_time
            
            # Set final status
            if self.automation_results['error_log']:
                self.automation_results['status'] = 'COMPLETED_WITH_WARNINGS'
            else:
                self.automation_results['status'] = 'SUCCESS'
            
            # Create comprehensive report
            report_data = {
                'execution_summary': {
                    'execution_id': self.automation_results['execution_id'],
                    'start_time': self.automation_results['start_time'].isoformat(),
                    'end_time': self.automation_results['end_time'].isoformat(),
                    'total_processing_time_seconds': total_time,
                    'status': self.automation_results['status']
                },
                'geocoding_results': {
                    'total_addresses': self.automation_results['total_addresses'],
                    'successful_geocodes': self.automation_results['successful_geocodes'],
                    'failed_geocodes': self.automation_results['failed_geocodes'],
                    'high_accuracy_geocodes': self.automation_results['high_accuracy_geocodes'],
                    'medium_accuracy_geocodes': self.automation_results['medium_accuracy_geocodes'],
                    'success_rate_percentage': (self.automation_results['successful_geocodes'] / self.automation_results['total_addresses']) * 100 if self.automation_results['total_addresses'] > 0 else 0,
                    'processing_time_seconds': self.automation_results.get('processing_time', 0)
                },
                'dataset_enhancement': {
                    'datasets_enhanced': self.automation_results['datasets_enhanced'],
                    'total_datasets_processed': len(self.automation_results['datasets_enhanced'])
                },
                'validation_results': self.automation_results.get('validation_results', {}),
                'system_configuration': {
                    'template_path': str(self.template_path),
                    'geocoding_service': self.geocode_service,
                    'coordinate_system': f"State Plane NJ (EPSG:{self.target_srid})",
                    'batch_size': self.batch_size
                },
                'errors_and_warnings': self.automation_results['error_log']
            }
            
            # Save JSON report
            timestamp = self.automation_results['execution_id']
            json_report_path = self.project_path / '03_output' / f'automated_geocoding_report_{timestamp}.json'
            with open(json_report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            # Create markdown summary
            success_rate = report_data['geocoding_results']['success_rate_percentage']
            
            md_content = f"""# SCRPA Automated Geocoding Report

**Execution ID:** {self.automation_results['execution_id']}
**Date:** {self.automation_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
**Status:** {self.automation_results['status']}
**Total Processing Time:** {total_time:.2f} seconds

## Executive Summary

### Geocoding Results
- **Total Addresses Processed:** {self.automation_results['total_addresses']}
- **Successful Geocodes:** {self.automation_results['successful_geocodes']} ({success_rate:.1f}%)
- **High Accuracy (≥90):** {self.automation_results['high_accuracy_geocodes']}
- **Medium Accuracy (80-89):** {self.automation_results['medium_accuracy_geocodes']}
- **Processing Time:** {self.automation_results.get('processing_time', 0):.2f} seconds

### Dataset Enhancement
- **Datasets Enhanced:** {len(self.automation_results['datasets_enhanced'])}
- **Original Files Overwritten:** Yes (as requested)

"""
            
            for dataset in self.automation_results['datasets_enhanced']:
                md_content += f"""#### {dataset['dataset']}
- **Records:** {dataset['original_records']}
- **Geocoded:** {dataset['geocoded_records']} ({dataset['enhancement_rate']:.1f}%)
- **Addresses Matched:** {dataset['addresses_matched']}

"""
            
            # Add validation results
            validation = self.automation_results.get('validation_results', {})
            if validation:
                md_content += f"""## Validation Results

**Overall Status:** {validation.get('overall_status', 'UNKNOWN')}

"""
                
                issues = validation.get('issues_found', [])
                if issues:
                    md_content += "**Issues Found:**\n"
                    for issue in issues:
                        md_content += f"- {issue}\n"
                else:
                    md_content += "**No Issues Found** - All validation checks passed\n"
            
            # Add system information
            md_content += f"""
## System Configuration

- **Template:** {self.template_path}
- **Geocoding Service:** {self.geocode_service}
- **Coordinate System:** State Plane NJ (EPSG:{self.target_srid})
- **Batch Size:** {self.batch_size}

## Files Generated

- **Geocoding Results:** `geocoding_input/geocoding_results.csv`
- **Enhanced Datasets:** Original CSV files overwritten with spatial data
- **Processing Report:** `{json_report_path.name}`

## Next Steps

### For ArcGIS Pro:
1. Import enhanced CSV files as XY data using x_coord, y_coord columns
2. Create point feature classes for spatial analysis
3. Apply symbology and configure mapping layers

### For Power BI:
1. Refresh datasets - spatial columns now available
2. Configure map visualizations using coordinate data
3. Test geographic filtering and spatial analysis capabilities

## Success Criteria Assessment

"""
            
            # Success criteria assessment
            if success_rate >= 85:
                md_content += "- ✅ **SUCCESS RATE TARGET MET:** {:.1f}% >= 85%\n".format(success_rate)
            else:
                md_content += "- ❌ **SUCCESS RATE TARGET NOT MET:** {:.1f}% < 85%\n".format(success_rate)
            
            high_accuracy_rate = (self.automation_results['high_accuracy_geocodes'] / self.automation_results['total_addresses']) * 100 if self.automation_results['total_addresses'] > 0 else 0
            
            if high_accuracy_rate >= 70:
                md_content += "- ✅ **HIGH ACCURACY TARGET MET:** {:.1f}% >= 70%\n".format(high_accuracy_rate)
            else:
                md_content += "- ❌ **HIGH ACCURACY TARGET NOT MET:** {:.1f}% < 70%\n".format(high_accuracy_rate)
            
            if total_time <= 1800:  # 30 minutes
                md_content += "- ✅ **PROCESSING TIME TARGET MET:** {:.1f} seconds <= 30 minutes\n".format(total_time)
            else:
                md_content += "- ⚠️ **PROCESSING TIME EXCEEDED:** {:.1f} seconds > 30 minutes\n".format(total_time)
            
            # Add errors if any
            if self.automation_results['error_log']:
                md_content += "\n## Errors and Warnings\n\n"
                for error in self.automation_results['error_log']:
                    md_content += f"- {error}\n"
            
            # Save markdown report
            md_report_path = self.project_path / '03_output' / f'automated_geocoding_summary_{timestamp}.md'
            with open(md_report_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            self.logger.info(f"Automation reports generated:")
            self.logger.info(f"  JSON Report: {json_report_path}")
            self.logger.info(f"  Summary Report: {md_report_path}")
            
            return str(md_report_path)
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return None

    def execute_complete_automation(self):
        """Execute the complete automated geocoding workflow."""
        self.logger.info("Starting complete automated SCRPA geocoding workflow...")
        
        try:
            # Step 1: Create processing geodatabase
            if not self.create_processing_geodatabase():
                raise Exception("Failed to create processing geodatabase")
            
            # Step 2: Import address data
            if not self.import_address_data():
                raise Exception("Failed to import address data")
            
            # Step 3: Execute batch geocoding
            if not self.execute_batch_geocoding():
                raise Exception("Failed to execute geocoding")
            
            # Step 4: Export geocoding results
            if not self.export_geocoding_results():
                raise Exception("Failed to export geocoding results")
            
            # Step 5: Enhance SCRPA datasets
            if not self.enhance_scrpa_datasets():
                raise Exception("Failed to enhance SCRPA datasets")
            
            # Step 6: Validate enhanced datasets
            if not self.validate_enhanced_datasets():
                self.logger.warning("Dataset validation completed with warnings")
            
            # Step 7: Generate comprehensive report
            report_path = self.generate_automation_report()
            
            # Step 8: Cleanup temporary files
            self.cleanup_processing_files()
            
            # Final summary
            end_time = datetime.now()
            total_time = (end_time - self.automation_results['start_time']).total_seconds()
            
            success_rate = (self.automation_results['successful_geocodes'] / self.automation_results['total_addresses']) * 100 if self.automation_results['total_addresses'] > 0 else 0
            
            self.logger.info("="*80)
            self.logger.info("SCRPA AUTOMATED GEOCODING COMPLETE")
            self.logger.info("="*80)
            self.logger.info(f"Status: {self.automation_results['status']}")
            self.logger.info(f"Total Processing Time: {total_time:.2f} seconds")
            self.logger.info(f"Addresses Processed: {self.automation_results['total_addresses']}")
            self.logger.info(f"Success Rate: {success_rate:.1f}%")
            self.logger.info(f"Datasets Enhanced: {len(self.automation_results['datasets_enhanced'])}")
            self.logger.info(f"Report Generated: {Path(report_path).name if report_path else 'FAILED'}")
            self.logger.info("="*80)
            
            if self.automation_results['error_log']:
                self.logger.info("WARNINGS/ERRORS ENCOUNTERED:")
                for error in self.automation_results['error_log']:
                    self.logger.warning(f"  - {error}")
                self.logger.info("="*80)
            
            return {
                'status': self.automation_results['status'],
                'total_addresses': self.automation_results['total_addresses'],
                'successful_geocodes': self.automation_results['successful_geocodes'],
                'success_rate': success_rate,
                'datasets_enhanced': len(self.automation_results['datasets_enhanced']),
                'processing_time': total_time,
                'report_path': report_path,
                'execution_id': self.automation_results['execution_id'],
                'errors': self.automation_results['error_log']
            }
            
        except Exception as e:
            # Handle fatal errors
            self.logger.error(f"FATAL ERROR - Automated geocoding failed: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            self.automation_results['status'] = 'FAILED'
            self.automation_results['error_log'].append(f"Fatal error: {e}")
            
            # Try to generate error report
            try:
                report_path = self.generate_automation_report()
            except:
                report_path = None
            
            # Cleanup on error
            self.cleanup_processing_files()
            
            return {
                'status': 'FAILED',
                'error': str(e),
                'execution_id': self.automation_results['execution_id'],
                'report_path': report_path,
                'errors': self.automation_results['error_log']
            }

def main():
    """Main execution function for standalone running."""
    try:
        # Check ArcPy availability
        try:
            import arcpy
            print("ArcPy module imported successfully")
        except ImportError:
            print("ERROR: ArcPy module not available. This script requires ArcGIS Pro or ArcGIS Desktop.")
            print("Please run this script from an ArcGIS Python environment.")
            sys.exit(1)
        
        # Initialize and execute automation
        geocoder = SCRPAAutomatedGeocoding()
        results = geocoder.execute_complete_automation()
        
        # Print final results
        print("\n" + "="*60)
        print("SCRPA AUTOMATED GEOCODING RESULTS")
        print("="*60)
        print(f"Status: {results['status']}")
        
        if results['status'] in ['SUCCESS', 'COMPLETED_WITH_WARNINGS']:
            print(f"Addresses Processed: {results['total_addresses']}")
            print(f"Success Rate: {results['success_rate']:.1f}%")
            print(f"Processing Time: {results['processing_time']:.2f} seconds")
            print(f"Datasets Enhanced: {results['datasets_enhanced']}")
            if results['report_path']:
                print(f"Report: {Path(results['report_path']).name}")
            
            if results.get('errors'):
                print(f"Warnings: {len(results['errors'])}")
            
            print("\nENHANCED DATASETS READY FOR ARCGIS PRO MAPPING!")
            sys.exit(0)
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
            if results.get('errors'):
                print("Error Log:")
                for error in results['errors']:
                    print(f"  - {error}")
            
            print("\nAUTOMATED GEOCODING FAILED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()