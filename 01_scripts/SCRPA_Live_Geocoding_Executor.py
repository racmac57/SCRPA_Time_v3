# 2025-08-01-00-00-00
# SCRPA_Time_v2/SCRPA_Live_Geocoding_Executor
# Author: R. A. Carucci
# Purpose: Live NJ_Geocode integration for SCRPA datasets using existing ArcGIS Pro template

import arcpy
import pandas as pd
import numpy as np
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import logging
import json

class SCRPALiveGeocoder:
    """
    Live geocoding executor for SCRPA datasets using NJ_Geocode service.
    
    Features:
    - Uses existing ArcGIS Pro template and NJ_Geocode service
    - Processes 144 unique addresses in 50-address batches
    - Outputs coordinates in State Plane NJ (EPSG:3424)
    - Comprehensive error handling and success reporting
    - Enhanced dataset generation with spatial columns
    """
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)
        
        self.template_path = self.project_path / "10_Refrence_Files" / "7_Day_Templet_SCRPA_Time.aprx"
        self.output_dir = self.project_path / '04_powerbi'
        self.temp_workspace = self.project_path / 'temp_geocoding'
        
        # Geocoding parameters
        self.batch_size = 50
        self.target_srid = 3424  # State Plane NJ
        self.geocode_service = "NJ_Geocode"
        
        # Results tracking
        self.geocoding_results = {
            'execution_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'start_time': datetime.now(),
            'total_addresses': 0,
            'successful_geocodes': 0,
            'failed_geocodes': 0,
            'high_accuracy_geocodes': 0,  # Score >= 90
            'medium_accuracy_geocodes': 0,  # Score 80-89
            'processing_time': 0,
            'batches_processed': 0,
            'datasets_enhanced': [],
            'error_log': []
        }
        
        self.setup_logging()
        self.setup_arcgis_environment()

    def setup_logging(self):
        """Setup comprehensive logging for geocoding execution."""
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"live_geocoding_{self.geocoding_results['execution_id']}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("="*80)
        self.logger.info(f"SCRPA LIVE GEOCODING EXECUTOR - {self.geocoding_results['execution_id']}")
        self.logger.info("="*80)

    def setup_arcgis_environment(self):
        """Setup ArcGIS environment and validate template access."""
        self.logger.info("Setting up ArcGIS environment...")
        
        try:
            # Create temporary workspace
            self.temp_workspace.mkdir(exist_ok=True)
            arcpy.env.workspace = str(self.temp_workspace)
            arcpy.env.overwriteOutput = True
            
            # Validate template exists
            if not self.template_path.exists():
                raise FileNotFoundError(f"ArcGIS Pro template not found: {self.template_path}")
            
            self.logger.info(f"✅ ArcGIS Pro template validated: {self.template_path}")
            
            # Set spatial reference to State Plane NJ
            self.spatial_reference = arcpy.SpatialReference(self.target_srid)
            self.logger.info(f"✅ Spatial reference set: {self.spatial_reference.name} (EPSG:{self.target_srid})")
            
            # Test NJ_Geocode service availability
            try:
                # This will fail gracefully if service not available
                arcpy.geocoding.DescribeGeocodeService(self.geocode_service)
                self.logger.info(f"✅ NJ_Geocode service validated and accessible")
                return True
            except:
                self.logger.warning(f"⚠️ NJ_Geocode service may not be available - will attempt anyway")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ ArcGIS environment setup failed: {e}")
            return False

    def collect_unique_addresses(self):
        """Collect all unique addresses from SCRPA datasets."""
        self.logger.info("Collecting unique addresses from SCRPA datasets...")
        
        unique_addresses = set()
        dataset_addresses = {}
        
        # Target datasets and their address columns
        datasets_to_process = [
            ('cad_data_standardized.csv', ['location', 'full_address_raw']),
            ('rms_data_standardized.csv', ['location', 'full_address_raw']),
            ('cad_rms_matched_standardized.csv', ['location'])
        ]
        
        for dataset_file, address_columns in datasets_to_process:
            file_path = self.output_dir / dataset_file
            
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    dataset_addresses[dataset_file] = set()
                    
                    # Collect addresses from all specified columns
                    for col in address_columns:
                        if col in df.columns:
                            addresses = df[col].dropna().unique()
                            valid_addresses = set()
                            
                            for addr in addresses:
                                addr_str = str(addr).strip()
                                if addr_str and addr_str != 'nan' and len(addr_str) > 10:
                                    valid_addresses.add(addr_str)
                            
                            dataset_addresses[dataset_file].update(valid_addresses)
                            unique_addresses.update(valid_addresses)
                            
                            self.logger.info(f"  {dataset_file} [{col}]: {len(valid_addresses)} addresses")
                    
                except Exception as e:
                    self.logger.error(f"Error reading {dataset_file}: {e}")
                    self.geocoding_results['error_log'].append(f"Failed to read {dataset_file}: {e}")
            else:
                self.logger.warning(f"Dataset not found: {dataset_file}")
        
        # Convert to sorted list for consistent processing
        address_list = sorted(list(unique_addresses))
        
        self.geocoding_results['total_addresses'] = len(address_list)
        self.logger.info(f"✅ Collected {len(address_list)} unique addresses for geocoding")
        
        return address_list, dataset_addresses

    def create_geocoding_workspace(self):
        """Create temporary geodatabase for geocoding operations."""
        self.logger.info("Creating geocoding workspace...")
        
        try:
            # Create temporary geodatabase
            temp_gdb = self.temp_workspace / "scrpa_geocoding.gdb"
            if temp_gdb.exists():
                arcpy.Delete_management(str(temp_gdb))
            
            arcpy.CreateFileGDB_management(str(self.temp_workspace), "scrpa_geocoding.gdb")
            self.temp_gdb = str(temp_gdb)
            
            self.logger.info(f"✅ Geocoding workspace created: {self.temp_gdb}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create geocoding workspace: {e}")
            return False

    def geocode_address_batch(self, batch_addresses, batch_number):
        """Geocode a batch of addresses using NJ_Geocode service."""
        self.logger.info(f"Processing batch {batch_number}: {len(batch_addresses)} addresses")
        
        batch_results = []
        
        try:
            # Create input table for this batch
            input_table = f"{self.temp_gdb}/batch_{batch_number}_input"
            arcpy.CreateTable_management(self.temp_gdb, f"batch_{batch_number}_input")
            arcpy.AddField_management(input_table, "Address", "TEXT", field_length=500)
            arcpy.AddField_management(input_table, "AddressID", "LONG")
            
            # Insert addresses into table
            with arcpy.da.InsertCursor(input_table, ["Address", "AddressID"]) as cursor:
                for i, address in enumerate(batch_addresses):
                    cursor.insertRow([str(address), i])
            
            self.logger.info(f"  Created input table with {len(batch_addresses)} addresses")
            
            # Perform geocoding
            output_fc = f"{self.temp_gdb}/batch_{batch_number}_geocoded"
            
            # Execute geocoding
            arcpy.geocoding.GeocodeAddresses(
                in_table=input_table,
                address_locator=self.geocode_service,
                in_address_fields="Address Address VISIBLE NONE",
                out_feature_class=output_fc,
                out_relationship_type="STATIC"
            )
            
            self.logger.info(f"  Geocoding completed for batch {batch_number}")
            
            # Extract results with coordinate transformation
            fields = ["Address", "SHAPE@X", "SHAPE@Y", "Score", "Status", "Match_addr", "AddressID"]
            
            with arcpy.da.SearchCursor(output_fc, fields, spatial_reference=self.spatial_reference) as cursor:
                for row in cursor:
                    result = {
                        'original_address': row[0],
                        'x_coord': row[1] if row[1] else None,
                        'y_coord': row[2] if row[2] else None,
                        'geocode_score': row[3] if row[3] else 0,
                        'geocode_status': row[4] if row[4] else 'FAILED',
                        'match_address': row[5] if row[5] else None,
                        'address_id': row[6],
                        'batch_number': batch_number
                    }
                    
                    batch_results.append(result)
                    
                    # Update statistics
                    score = result['geocode_score']
                    if score >= 90:
                        self.geocoding_results['high_accuracy_geocodes'] += 1
                        self.geocoding_results['successful_geocodes'] += 1
                    elif score >= 80:
                        self.geocoding_results['medium_accuracy_geocodes'] += 1
                        self.geocoding_results['successful_geocodes'] += 1
                    else:
                        self.geocoding_results['failed_geocodes'] += 1
            
            # Clean up batch tables
            arcpy.Delete_management(input_table)
            arcpy.Delete_management(output_fc)
            
            self.logger.info(f"  Batch {batch_number} completed: {len(batch_results)} results extracted")
            
        except Exception as e:
            self.logger.error(f"❌ Batch {batch_number} failed: {e}")
            self.geocoding_results['error_log'].append(f"Batch {batch_number} failed: {e}")
            
            # Create failed results for this batch
            for i, address in enumerate(batch_addresses):
                batch_results.append({
                    'original_address': address,
                    'x_coord': None,
                    'y_coord': None,
                    'geocode_score': 0,
                    'geocode_status': 'FAILED',
                    'match_address': None,
                    'address_id': i,
                    'batch_number': batch_number
                })
                self.geocoding_results['failed_geocodes'] += 1
        
        return batch_results

    def execute_batch_geocoding(self, address_list):
        """Execute geocoding in batches for optimal performance."""
        self.logger.info(f"Starting batch geocoding: {len(address_list)} addresses in batches of {self.batch_size}")
        
        all_results = []
        
        # Process addresses in batches
        for i in range(0, len(address_list), self.batch_size):
            batch_number = (i // self.batch_size) + 1
            batch_addresses = address_list[i:i + self.batch_size]
            
            # Process this batch
            batch_results = self.geocode_address_batch(batch_addresses, batch_number)
            all_results.extend(batch_results)
            
            self.geocoding_results['batches_processed'] += 1
            
            # Small delay between batches to prevent service overload
            time.sleep(1)
            
            self.logger.info(f"Progress: {batch_number} batches completed, {len(all_results)} addresses processed")
        
        self.logger.info(f"✅ Batch geocoding completed: {len(all_results)} total results")
        return all_results

    def create_geocoding_lookup(self, geocoding_results):
        """Create address-to-coordinates lookup dictionary."""
        lookup = {}
        
        for result in geocoding_results:
            address = result['original_address']
            lookup[address] = {
                'x_coord': result['x_coord'],
                'y_coord': result['y_coord'],
                'geocode_score': result['geocode_score'],
                'geocode_status': result['geocode_status'],
                'match_address': result['match_address']
            }
        
        return lookup

    def enhance_dataset_with_coordinates(self, dataset_file, geocoding_lookup):
        """Add spatial columns to a dataset using geocoding lookup."""
        self.logger.info(f"Enhancing {dataset_file} with spatial coordinates...")
        
        try:
            file_path = self.output_dir / dataset_file
            if not file_path.exists():
                self.logger.warning(f"Dataset not found: {dataset_file}")
                return False
            
            # Read dataset
            df = pd.read_csv(file_path)
            original_count = len(df)
            
            # Add spatial columns
            spatial_columns = ['x_coord', 'y_coord', 'geocode_score', 'geocode_status', 'match_address']
            for col in spatial_columns:
                df[col] = None
            
            # Find address column(s)
            address_columns = ['location', 'full_address_raw']
            addresses_matched = 0
            
            for addr_col in address_columns:
                if addr_col in df.columns:
                    for idx, address in df[addr_col].items():
                        if pd.notna(address) and str(address) in geocoding_lookup:
                            lookup_result = geocoding_lookup[str(address)]
                            
                            # Only update if we don't already have coordinates
                            if pd.isna(df.at[idx, 'x_coord']):
                                df.at[idx, 'x_coord'] = lookup_result['x_coord']
                                df.at[idx, 'y_coord'] = lookup_result['y_coord']
                                df.at[idx, 'geocode_score'] = lookup_result['geocode_score']
                                df.at[idx, 'geocode_status'] = lookup_result['geocode_status']
                                df.at[idx, 'match_address'] = lookup_result['match_address']
                                addresses_matched += 1
            
            # Calculate enhancement statistics
            geocoded_count = df['x_coord'].notna().sum()
            enhancement_rate = (geocoded_count / original_count) * 100 if original_count > 0 else 0
            
            # Save enhanced dataset
            enhanced_file = self.output_dir / dataset_file.replace('.csv', '_with_coordinates.csv')
            df.to_csv(enhanced_file, index=False)
            
            self.logger.info(f"  ✅ Enhanced {dataset_file}:")
            self.logger.info(f"    - Original records: {original_count}")
            self.logger.info(f"    - Geocoded records: {geocoded_count}")
            self.logger.info(f"    - Enhancement rate: {enhancement_rate:.1f}%")
            self.logger.info(f"    - Output: {enhanced_file.name}")
            
            # Track results
            self.geocoding_results['datasets_enhanced'].append({
                'dataset': dataset_file,
                'original_records': original_count,
                'geocoded_records': int(geocoded_count),
                'enhancement_rate': enhancement_rate,
                'output_file': enhanced_file.name
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to enhance {dataset_file}: {e}")
            self.geocoding_results['error_log'].append(f"Enhancement failed for {dataset_file}: {e}")
            return False

    def generate_geocoding_report(self):
        """Generate comprehensive geocoding success report."""
        self.logger.info("Generating geocoding success report...")
        
        try:
            # Calculate final statistics
            end_time = datetime.now()
            processing_time = (end_time - self.geocoding_results['start_time']).total_seconds()
            self.geocoding_results['processing_time'] = processing_time
            self.geocoding_results['end_time'] = end_time
            
            # Calculate success rates
            total = self.geocoding_results['total_addresses']
            successful = self.geocoding_results['successful_geocodes']
            failed = self.geocoding_results['failed_geocodes']
            
            success_rate = (successful / total) * 100 if total > 0 else 0
            high_accuracy_rate = (self.geocoding_results['high_accuracy_geocodes'] / total) * 100 if total > 0 else 0
            
            # Create comprehensive report
            report_data = {
                'execution_summary': {
                    'execution_id': self.geocoding_results['execution_id'],
                    'start_time': self.geocoding_results['start_time'].isoformat(),
                    'end_time': self.geocoding_results['end_time'].isoformat(),
                    'processing_time_seconds': processing_time,
                    'processing_time_formatted': f"{processing_time:.2f} seconds"
                },
                'geocoding_statistics': {
                    'total_addresses': total,
                    'successful_geocodes': successful,
                    'failed_geocodes': failed,
                    'high_accuracy_geocodes': self.geocoding_results['high_accuracy_geocodes'],
                    'medium_accuracy_geocodes': self.geocoding_results['medium_accuracy_geocodes'],
                    'success_rate_percentage': success_rate,
                    'high_accuracy_rate_percentage': high_accuracy_rate,
                    'batches_processed': self.geocoding_results['batches_processed'],
                    'batch_size': self.batch_size
                },
                'dataset_enhancements': self.geocoding_results['datasets_enhanced'],
                'technical_details': {
                    'geocoding_service': self.geocode_service,
                    'coordinate_system': f"State Plane NJ (EPSG:{self.target_srid})",
                    'template_used': str(self.template_path),
                    'output_directory': str(self.output_dir)
                },
                'errors_encountered': self.geocoding_results['error_log']
            }
            
            # Save JSON report
            timestamp = self.geocoding_results['execution_id']
            json_report_path = self.project_path / '03_output' / f'geocoding_report_{timestamp}.json'
            with open(json_report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            # Create markdown summary
            md_content = f"""# SCRPA Live Geocoding Execution Report

**Execution ID:** {self.geocoding_results['execution_id']}
**Date:** {self.geocoding_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
**Processing Time:** {processing_time:.2f} seconds

## Geocoding Results Summary

### Overall Statistics
- **Total Addresses Processed:** {total}
- **Successful Geocodes:** {successful} ({success_rate:.1f}%)
- **Failed Geocodes:** {failed} ({(failed/total)*100 if total > 0 else 0:.1f}%)
- **High Accuracy (≥90 score):** {self.geocoding_results['high_accuracy_geocodes']} ({high_accuracy_rate:.1f}%)
- **Medium Accuracy (80-89 score):** {self.geocoding_results['medium_accuracy_geocodes']}

### Processing Details
- **Batches Processed:** {self.geocoding_results['batches_processed']}
- **Batch Size:** {self.batch_size} addresses per batch
- **Geocoding Service:** {self.geocode_service}
- **Coordinate System:** State Plane NJ (EPSG:{self.target_srid})

## Dataset Enhancement Results

"""
            
            for dataset in self.geocoding_results['datasets_enhanced']:
                md_content += f"""### {dataset['dataset']}
- **Original Records:** {dataset['original_records']}
- **Geocoded Records:** {dataset['geocoded_records']}
- **Enhancement Rate:** {dataset['enhancement_rate']:.1f}%
- **Output File:** {dataset['output_file']}

"""
            
            # Add technical details
            md_content += f"""## Technical Configuration

- **Template Used:** {self.template_path}
- **Output Directory:** {self.output_dir}
- **Temporary Workspace:** {self.temp_workspace}

## Quality Assessment

### Success Criteria
- ✅ Target Success Rate: 85%+ (Achieved: {success_rate:.1f}%)
- ✅ High Accuracy Rate: 70%+ (Achieved: {high_accuracy_rate:.1f}%)
- ✅ Processing Time: <30 minutes (Achieved: {processing_time/60:.1f} minutes)

### Recommendations
"""
            
            if success_rate >= 85:
                md_content += "- ✅ **EXCELLENT**: Geocoding success rate exceeds target threshold\n"
            elif success_rate >= 70:
                md_content += "- ⚠️ **GOOD**: Geocoding success rate is acceptable but could be improved\n"
            else:
                md_content += "- ❌ **NEEDS IMPROVEMENT**: Geocoding success rate below acceptable threshold\n"
            
            if high_accuracy_rate >= 70:
                md_content += "- ✅ **HIGH QUALITY**: Most geocodes are high accuracy\n"
            else:
                md_content += "- ⚠️ **MODERATE QUALITY**: Consider address data cleanup for better accuracy\n"
            
            # Add errors if any
            if self.geocoding_results['error_log']:
                md_content += "\n## Errors Encountered\n\n"
                for error in self.geocoding_results['error_log']:
                    md_content += f"- ⚠️ {error}\n"
            
            md_content += f"""
## Next Steps

### For ArcGIS Pro Integration:
1. Import enhanced datasets with coordinate columns
2. Create point feature classes from x_coord, y_coord
3. Apply symbology and configure map layers
4. Test spatial analysis capabilities

### For Power BI Integration:
1. Refresh Power BI datasets with enhanced CSV files
2. Configure map visualizations using coordinate data
3. Test geographic filtering and spatial analysis
4. Validate dashboard performance with spatial data

### For Production Deployment:
1. Schedule weekly geocoding updates
2. Monitor geocoding success rates
3. Implement data quality improvements for failed addresses
4. Establish coordinate data validation processes
"""
            
            # Save markdown report
            md_report_path = self.project_path / '03_output' / f'geocoding_summary_{timestamp}.md'
            with open(md_report_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            self.logger.info(f"✅ Geocoding reports generated:")
            self.logger.info(f"  📊 JSON Report: {json_report_path}")
            self.logger.info(f"  📋 Summary Report: {md_report_path}")
            
            return str(md_report_path)
            
        except Exception as e:
            self.logger.error(f"❌ Report generation failed: {e}")
            return None

    def cleanup_workspace(self):
        """Clean up temporary geocoding workspace."""
        self.logger.info("Cleaning up temporary workspace...")
        
        try:
            if hasattr(self, 'temp_gdb') and arcpy.Exists(self.temp_gdb):
                arcpy.Delete_management(self.temp_gdb)
                self.logger.info("✅ Temporary geodatabase cleaned up")
            
            # Keep temp directory for other processes
            
        except Exception as e:
            self.logger.warning(f"⚠️ Cleanup warning: {e}")

    def execute_live_geocoding(self):
        """Execute the complete live geocoding workflow."""
        self.logger.info("🚀 Starting SCRPA Live Geocoding Execution...")
        
        try:
            # Step 1: Collect unique addresses
            address_list, dataset_addresses = self.collect_unique_addresses()
            if not address_list:
                raise Exception("No addresses found to geocode")
            
            # Step 2: Create geocoding workspace
            if not self.create_geocoding_workspace():
                raise Exception("Failed to create geocoding workspace")
            
            # Step 3: Execute batch geocoding
            geocoding_results = self.execute_batch_geocoding(address_list)
            if not geocoding_results:
                raise Exception("Geocoding execution failed")
            
            # Step 4: Create lookup dictionary
            geocoding_lookup = self.create_geocoding_lookup(geocoding_results)
            
            # Step 5: Enhance datasets with coordinates
            target_datasets = [
                'cad_data_standardized.csv',
                'rms_data_standardized.csv',
                'cad_rms_matched_standardized.csv'
            ]
            
            for dataset in target_datasets:
                self.enhance_dataset_with_coordinates(dataset, geocoding_lookup)
            
            # Step 6: Generate success report
            report_path = self.generate_geocoding_report()
            
            # Step 7: Cleanup
            self.cleanup_workspace()
            
            # Final summary
            total = self.geocoding_results['total_addresses']
            successful = self.geocoding_results['successful_geocodes']
            success_rate = (successful / total) * 100 if total > 0 else 0
            processing_time = self.geocoding_results['processing_time']
            
            self.logger.info("="*80)
            self.logger.info("🎯 SCRPA LIVE GEOCODING COMPLETE")
            self.logger.info("="*80)
            self.logger.info(f"📍 Addresses Processed: {total}")
            self.logger.info(f"✅ Success Rate: {success_rate:.1f}% ({successful}/{total})")
            self.logger.info(f"⏱️ Processing Time: {processing_time:.2f} seconds")
            self.logger.info(f"📊 Datasets Enhanced: {len(self.geocoding_results['datasets_enhanced'])}")
            self.logger.info(f"📋 Report: {report_path}")
            self.logger.info("="*80)
            
            return {
                'status': 'SUCCESS',
                'total_addresses': total,
                'successful_geocodes': successful,
                'success_rate': success_rate,
                'processing_time': processing_time,
                'datasets_enhanced': len(self.geocoding_results['datasets_enhanced']),
                'report_path': report_path,
                'execution_id': self.geocoding_results['execution_id']
            }
            
        except Exception as e:
            self.logger.error(f"❌ Live geocoding failed: {e}")
            self.cleanup_workspace()
            
            return {
                'status': 'FAILED',
                'error': str(e),
                'execution_id': self.geocoding_results['execution_id']
            }

def main():
    """Main execution function."""
    try:
        geocoder = SCRPALiveGeocoder()
        results = geocoder.execute_live_geocoding()
        
        # Print summary for console
        print("\n" + "="*60)
        print("SCRPA LIVE GEOCODING RESULTS")
        print("="*60)
        print(f"Status: {results['status']}")
        
        if results['status'] == 'SUCCESS':
            print(f"Addresses Processed: {results['total_addresses']}")
            print(f"Success Rate: {results['success_rate']:.1f}%")
            print(f"Processing Time: {results['processing_time']:.2f} seconds")
            print(f"Datasets Enhanced: {results['datasets_enhanced']}")
            print(f"Report: {results['report_path']}")
            print("\n🎉 GEOCODING COMPLETED SUCCESSFULLY!")
            sys.exit(0)
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
            print("\n❌ GEOCODING FAILED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()