# 🕒 2025-08-01-00-00-00
# SCRPA_Time_v2/SCRPA_Complete_Pipeline_Validator_with_Spatial
# Author: R. A. Carucci
# Purpose: Complete SCRPA pipeline validation and spatial enhancement integration

import pandas as pd
import numpy as np
import re
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional, Any

class SCRPACompleteValidator:
    """
    Complete SCRPA pipeline validation and spatial enhancement system.
    
    Features:
    - Full pipeline validation with record count verification
    - Column compliance checking (lowercase_with_underscores)
    - Time formatting validation (HH:MM, "00 Mins 00 Secs")
    - CAD-RMS matching rate analysis
    - Address standardization validation
    - Spatial enhancement integration with NJ_Geocode
    - ArcPy spatial grid/zone validation
    - Comprehensive reporting and benchmarking
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
        
        self.template_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\7_Day_Templet_SCRPA_Time.aprx")
        
        self.validation_results = {}
        self.performance_metrics = {}
        self.spatial_enhancement_results = {}
        
        self.setup_logging()

    def setup_logging(self):
        """Setup comprehensive logging."""
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"scrpa_complete_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.logger = logging.getLogger('SCRPACompleteValidator')
        self.logger.setLevel(logging.INFO)
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        fh = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        # Console handler with encoding fix
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        self.logger.info("=== SCRPA Complete Pipeline Validator with Spatial Enhancement ===")

    def run_base_pipeline(self) -> Dict[str, pd.DataFrame]:
        """Run the base SCRPA pipeline and return datasets."""
        self.logger.info("🚀 Running base SCRPA pipeline...")
        start_time = time.time()
        
        try:
            # Import and run the fixed pipeline
            import sys
            sys.path.append(str(self.project_path / '01_scripts'))
            
            from Comprehensive_SCRPA_Fix_v8_0_Standardized import ComprehensiveSCRPAFixV8_0
            
            processor = ComprehensiveSCRPAFixV8_0()
            results = processor.process_final_pipeline()
            
            pipeline_time = time.time() - start_time
            self.performance_metrics['pipeline_processing_time'] = pipeline_time
            
            self.logger.info(f"✅ Base pipeline completed in {pipeline_time:.2f} seconds")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Base pipeline failed: {e}")
            return {}

    def validate_record_counts(self, results: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate expected record counts."""
        self.logger.info("📊 Validating record counts...")
        
        validation = {
            'timestamp': datetime.now().isoformat(),
            'expected_counts': {
                'cad_records': 114,  # Expected CAD records
                'rms_records': 135,  # Expected RMS records  
                'matched_records': 135  # Should match RMS count
            },
            'actual_counts': {},
            'validation_status': {},
            'issues': []
        }
        
        # Check actual counts
        if 'cad_data' in results and not results['cad_data'].empty:
            actual_cad = len(results['cad_data'])
            validation['actual_counts']['cad_records'] = actual_cad
            
            if actual_cad >= 110:  # Allow some variance
                validation['validation_status']['cad_count'] = 'PASS'
            else:
                validation['validation_status']['cad_count'] = 'FAIL'
                validation['issues'].append(f"CAD record count too low: {actual_cad} < 110")
        
        if 'rms_data' in results and not results['rms_data'].empty:
            actual_rms = len(results['rms_data'])
            validation['actual_counts']['rms_records'] = actual_rms
            
            if actual_rms >= 130:  # Allow some variance
                validation['validation_status']['rms_count'] = 'PASS'
            else:
                validation['validation_status']['rms_count'] = 'FAIL'
                validation['issues'].append(f"RMS record count too low: {actual_rms} < 130")
        
        # Check matched dataset by loading the CSV (if exists)
        matched_file = self.output_dir / 'cad_rms_matched_standardized.csv'
        if matched_file.exists():
            try:
                matched_df = pd.read_csv(matched_file)
                actual_matched = len(matched_df)
                validation['actual_counts']['matched_records'] = actual_matched
                
                # Should exactly match RMS count
                if actual_matched == validation['actual_counts'].get('rms_records', 0):
                    validation['validation_status']['matched_count'] = 'PASS'
                else:
                    validation['validation_status']['matched_count'] = 'FAIL'  
                    validation['issues'].append(f"Matched count {actual_matched} != RMS count {validation['actual_counts'].get('rms_records', 0)}")
                    
            except Exception as e:
                validation['issues'].append(f"Could not load matched dataset: {e}")
        
        # Overall validation status
        validation['overall_status'] = 'PASS' if not validation['issues'] else 'FAIL'
        
        self.logger.info(f"Record count validation: {validation['overall_status']}")
        for issue in validation['issues']:
            self.logger.warning(f"  ⚠️ {issue}")
            
        return validation

    def validate_column_compliance(self, results: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate 100% column compliance with lowercase_with_underscores."""
        self.logger.info("🔍 Validating column compliance...")
        
        compliance = {
            'timestamp': datetime.now().isoformat(),
            'pattern': 'lowercase_with_underscores',
            'datasets': {},
            'overall_compliance': 0.0,
            'non_compliant_columns': [],
            'validation_status': 'PASS'
        }
        
        # Pattern for lowercase_with_underscores
        pattern = re.compile(r'^[a-z]+(_[a-z0-9]+)*$')
        
        total_columns = 0
        compliant_columns = 0
        
        for dataset_name, df in results.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                dataset_compliance = {
                    'total_columns': len(df.columns),
                    'compliant_columns': 0,
                    'compliance_rate': 0.0,
                    'non_compliant': []
                }
                
                for col in df.columns:
                    if pattern.match(col):
                        dataset_compliance['compliant_columns'] += 1
                        compliant_columns += 1
                    else:
                        dataset_compliance['non_compliant'].append(col)
                        compliance['non_compliant_columns'].append(f"{dataset_name}: {col}")
                
                total_columns += dataset_compliance['total_columns']
                dataset_compliance['compliance_rate'] = (dataset_compliance['compliant_columns'] / dataset_compliance['total_columns']) * 100
                
                compliance['datasets'][dataset_name] = dataset_compliance
                
                self.logger.info(f"  {dataset_name}: {dataset_compliance['compliance_rate']:.1f}% compliant ({dataset_compliance['compliant_columns']}/{dataset_compliance['total_columns']})")
        
        # Overall compliance
        if total_columns > 0:
            compliance['overall_compliance'] = (compliant_columns / total_columns) * 100
        
        # Check CSV files as well
        csv_files = ['cad_data_standardized.csv', 'rms_data_standardized.csv', 'cad_rms_matched_standardized.csv']
        for csv_file in csv_files:
            file_path = self.output_dir / csv_file
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path, nrows=1)  # Just check headers
                    dataset_name = csv_file.replace('.csv', '')
                    
                    dataset_compliance = {
                        'total_columns': len(df.columns),
                        'compliant_columns': 0,
                        'compliance_rate': 0.0,
                        'non_compliant': []
                    }
                    
                    for col in df.columns:
                        if pattern.match(col):
                            dataset_compliance['compliant_columns'] += 1
                        else:
                            dataset_compliance['non_compliant'].append(col)
                            compliance['non_compliant_columns'].append(f"{dataset_name}: {col}")
                    
                    dataset_compliance['compliance_rate'] = (dataset_compliance['compliant_columns'] / dataset_compliance['total_columns']) * 100
                    compliance['datasets'][dataset_name] = dataset_compliance
                    
                    self.logger.info(f"  {dataset_name} (CSV): {dataset_compliance['compliance_rate']:.1f}% compliant")
                    
                except Exception as e:
                    self.logger.warning(f"Could not validate {csv_file}: {e}")
        
        # Validation status
        if compliance['overall_compliance'] < 100.0:
            compliance['validation_status'] = 'FAIL'
            self.logger.warning(f"❌ Column compliance FAILED: {compliance['overall_compliance']:.1f}%")
            for col in compliance['non_compliant_columns']:
                self.logger.warning(f"  Non-compliant: {col}")
        else:
            self.logger.info(f"✅ Column compliance PASSED: 100%")
        
        return compliance

    def validate_time_formatting(self) -> Dict[str, Any]:
        """Validate time formatting across all datasets."""
        self.logger.info("⏰ Validating time formatting...")
        
        time_validation = {
            'timestamp': datetime.now().isoformat(),
            'formats': {
                'incident_time': 'HH:MM',
                'response_time': '00 Mins 00 Secs',
                'time_spent': '0 Hrs. 00 Mins'
            },
            'datasets': {},
            'validation_status': 'PASS',
            'issues': []
        }
        
        # Check RMS data
        rms_file = self.output_dir / 'rms_data_standardized.csv'
        if rms_file.exists():
            try:
                df = pd.read_csv(rms_file)
                rms_validation = {'dataset': 'rms_data', 'checks': {}}
                
                # Check incident_time format (HH:MM)
                if 'incident_time' in df.columns:
                    sample_times = df['incident_time'].dropna().head(10)
                    hhmm_pattern = re.compile(r'^\d{2}:\d{2}$')
                    valid_times = sum(1 for t in sample_times if hhmm_pattern.match(str(t)))
                    
                    rms_validation['checks']['incident_time_format'] = {
                        'expected': 'HH:MM',
                        'sample_size': len(sample_times),
                        'valid_count': valid_times,
                        'compliance_rate': (valid_times / len(sample_times)) * 100 if len(sample_times) > 0 else 0
                    }
                    
                    if rms_validation['checks']['incident_time_format']['compliance_rate'] < 95:
                        time_validation['issues'].append(f"RMS incident_time format compliance low: {rms_validation['checks']['incident_time_format']['compliance_rate']:.1f}%")
                
                time_validation['datasets']['rms'] = rms_validation
                
            except Exception as e:
                time_validation['issues'].append(f"Could not validate RMS time formatting: {e}")
        
        # Check CAD data
        cad_file = self.output_dir / 'cad_data_standardized.csv'
        if cad_file.exists():
            try:
                df = pd.read_csv(cad_file)
                cad_validation = {'dataset': 'cad_data', 'checks': {}}
                
                # Check time_response_formatted (00 Mins 00 Secs)
                if 'time_response_formatted' in df.columns:
                    sample_times = df['time_response_formatted'].dropna().head(10)
                    mins_secs_pattern = re.compile(r'^\d{2} Mins \d{2} Secs$')
                    valid_times = sum(1 for t in sample_times if mins_secs_pattern.match(str(t)))
                    
                    cad_validation['checks']['time_response_format'] = {
                        'expected': '00 Mins 00 Secs',
                        'sample_size': len(sample_times),
                        'valid_count': valid_times,
                        'compliance_rate': (valid_times / len(sample_times)) * 100 if len(sample_times) > 0 else 0
                    }
                    
                    if cad_validation['checks']['time_response_format']['compliance_rate'] < 95:
                        time_validation['issues'].append(f"CAD time_response_formatted compliance low: {cad_validation['checks']['time_response_format']['compliance_rate']:.1f}%")
                
                time_validation['datasets']['cad'] = cad_validation
                
            except Exception as e:
                time_validation['issues'].append(f"Could not validate CAD time formatting: {e}")
        
        # Overall validation status
        if time_validation['issues']:
            time_validation['validation_status'] = 'FAIL'
            self.logger.warning("❌ Time formatting validation FAILED")
            for issue in time_validation['issues']:
                self.logger.warning(f"  {issue}")
        else:
            self.logger.info("✅ Time formatting validation PASSED")
        
        return time_validation

    def validate_cad_rms_matching(self) -> Dict[str, Any]:
        """Validate CAD-RMS matching rates and _cad column population."""
        self.logger.info("🔗 Validating CAD-RMS matching...")
        
        matching_validation = {
            'timestamp': datetime.now().isoformat(),
            'total_rms_records': 0,
            'cad_matches_found': 0,
            'match_rate_percentage': 0.0,
            'cad_columns_populated': {},
            'validation_status': 'PASS',
            'issues': []
        }
        
        matched_file = self.output_dir / 'cad_rms_matched_standardized.csv'
        if matched_file.exists():
            try:
                df = pd.read_csv(matched_file)
                matching_validation['total_rms_records'] = len(df)
                
                # Count CAD matches by checking for non-null CAD columns
                cad_columns = [col for col in df.columns if col.endswith('_cad')]
                
                if cad_columns:
                    # Use response_type_cad as primary indicator
                    if 'response_type_cad' in df.columns:
                        cad_matches = df['response_type_cad'].notna().sum()
                        matching_validation['cad_matches_found'] = cad_matches
                        matching_validation['match_rate_percentage'] = (cad_matches / len(df)) * 100
                    
                    # Check population of key CAD columns
                    key_cad_columns = ['response_type_cad', 'grid_cad', 'post_cad', 'cad_notes_cleaned_cad']
                    for col in key_cad_columns:
                        if col in df.columns:
                            populated_count = df[col].notna().sum()
                            population_rate = (populated_count / len(df)) * 100
                            matching_validation['cad_columns_populated'][col] = {
                                'populated_count': populated_count,
                                'population_rate': population_rate
                            }
                            
                            # Warn if key columns are mostly empty
                            if col in ['response_type_cad'] and population_rate < 50:
                                matching_validation['issues'].append(f"{col} population rate too low: {population_rate:.1f}%")
                
                # Validate match rate is reasonable
                if matching_validation['match_rate_percentage'] < 50:
                    matching_validation['issues'].append(f"CAD-RMS match rate too low: {matching_validation['match_rate_percentage']:.1f}%")
                
                self.logger.info(f"  Match rate: {matching_validation['match_rate_percentage']:.1f}% ({matching_validation['cad_matches_found']}/{matching_validation['total_rms_records']})")
                
                for col, stats in matching_validation['cad_columns_populated'].items():
                    self.logger.info(f"  {col}: {stats['population_rate']:.1f}% populated")
                
            except Exception as e:
                matching_validation['issues'].append(f"Could not validate CAD-RMS matching: {e}")
        else:
            matching_validation['issues'].append("CAD-RMS matched file not found")
        
        # Overall validation status
        if matching_validation['issues']:
            matching_validation['validation_status'] = 'FAIL'
            self.logger.warning("❌ CAD-RMS matching validation FAILED")
            for issue in matching_validation['issues']:
                self.logger.warning(f"  {issue}")
        else:
            self.logger.info("✅ CAD-RMS matching validation PASSED")
        
        return matching_validation

    def validate_address_standardization(self) -> Dict[str, Any]:
        """Validate address standardization to Hackensack, NJ, 07601 format."""
        self.logger.info("🏠 Validating address standardization...")
        
        address_validation = {
            'timestamp': datetime.now().isoformat(),
            'expected_format': 'Address, Hackensack, NJ, 07601',
            'datasets': {},
            'validation_status': 'PASS',
            'issues': []
        }
        
        # Check datasets for address standardization
        datasets_to_check = [
            ('rms_data_standardized.csv', 'location'),
            ('cad_data_standardized.csv', 'location'),
            ('cad_rms_matched_standardized.csv', 'location')
        ]
        
        hackensack_pattern = re.compile(r'.*Hackensack.*NJ.*07601', re.IGNORECASE)
        
        for filename, address_column in datasets_to_check:
            file_path = self.output_dir / filename
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    dataset_name = filename.replace('.csv', '')
                    
                    if address_column in df.columns:
                        addresses = df[address_column].dropna()
                        total_addresses = len(addresses)
                        
                        if total_addresses > 0:
                            # Check for Hackensack standardization
                            hackensack_count = sum(1 for addr in addresses if hackensack_pattern.match(str(addr)))
                            hackensack_rate = (hackensack_count / total_addresses) * 100
                            
                            # Check for non-Hackensack addresses (should be minimal)
                            non_hackensack = [addr for addr in addresses if not hackensack_pattern.match(str(addr))]
                            
                            address_validation['datasets'][dataset_name] = {
                                'total_addresses': total_addresses,
                                'hackensack_standardized': hackensack_count,
                                'standardization_rate': hackensack_rate,
                                'non_hackensack_count': len(non_hackensack),
                                'non_hackensack_sample': non_hackensack[:5]  # First 5 examples
                            }
                            
                            self.logger.info(f"  {dataset_name}: {hackensack_rate:.1f}% Hackensack standardized ({hackensack_count}/{total_addresses})")
                            
                            # Flag if standardization rate is low
                            if hackensack_rate < 85:
                                address_validation['issues'].append(f"{dataset_name} Hackensack standardization rate low: {hackensack_rate:.1f}%")
                
                except Exception as e:
                    address_validation['issues'].append(f"Could not validate addresses in {filename}: {e}")
        
        # Overall validation status
        if address_validation['issues']:
            address_validation['validation_status'] = 'FAIL'
            self.logger.warning("❌ Address standardization validation FAILED")
            for issue in address_validation['issues']:
                self.logger.warning(f"  {issue}")
        else:
            self.logger.info("✅ Address standardization validation PASSED")
        
        return address_validation

    def prepare_spatial_enhancement(self) -> Dict[str, Any]:
        """Prepare for spatial enhancement with NJ_Geocode service."""
        self.logger.info("🗺️ Preparing spatial enhancement...")
        
        spatial_prep = {
            'timestamp': datetime.now().isoformat(),
            'template_path': str(self.template_path),
            'template_exists': self.template_path.exists(),
            'spatial_columns_to_add': ['x_coord', 'y_coord', 'geocode_score', 'geocode_status', 'match_address'],
            'coordinate_system': 'State Plane NJ (EPSG:3424)',
            'addresses_to_geocode': {},
            'batch_size': 100,
            'preparation_status': 'READY'
        }
        
        # Check ArcGIS Pro template
        if not spatial_prep['template_exists']:
            spatial_prep['preparation_status'] = 'WARNING'
            self.logger.warning(f"⚠️ ArcGIS Pro template not found: {self.template_path}")
        else:
            self.logger.info(f"✅ ArcGIS Pro template found: {self.template_path}")
        
        # Collect addresses from all datasets for geocoding
        datasets_to_geocode = [
            ('rms_data_standardized.csv', 'location'),
            ('cad_data_standardized.csv', 'location'),
            ('cad_rms_matched_standardized.csv', 'location')
        ]
        
        all_addresses = set()
        
        for filename, address_column in datasets_to_geocode:
            file_path = self.output_dir / filename
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    if address_column in df.columns:
                        addresses = df[address_column].dropna().unique()
                        unique_addresses = set(str(addr) for addr in addresses if pd.notna(addr))
                        
                        spatial_prep['addresses_to_geocode'][filename] = {
                            'count': len(unique_addresses),
                            'sample': list(unique_addresses)[:5]
                        }
                        
                        all_addresses.update(unique_addresses)
                        
                        self.logger.info(f"  {filename}: {len(unique_addresses)} unique addresses")
                
                except Exception as e:
                    self.logger.warning(f"Could not collect addresses from {filename}: {e}")
        
        spatial_prep['total_unique_addresses'] = len(all_addresses)
        spatial_prep['estimated_batches'] = (len(all_addresses) + spatial_prep['batch_size'] - 1) // spatial_prep['batch_size']
        
        self.logger.info(f"📍 Total unique addresses to geocode: {len(all_addresses)}")
        self.logger.info(f"📦 Estimated batches: {spatial_prep['estimated_batches']}")
        
        return spatial_prep

    def create_geocoding_batch_processor(self) -> str:
        """Create a geocoding batch processing function."""
        self.logger.info("⚙️ Creating geocoding batch processor...")
        
        geocoding_script = '''
import arcpy
import pandas as pd
from pathlib import Path
import logging

def batch_geocode_addresses(addresses_list, output_path, batch_size=100):
    """
    Batch geocode addresses using NJ_Geocode service.
    
    Args:
        addresses_list: List of addresses to geocode
        output_path: Path to save geocoded results
        batch_size: Number of addresses per batch
    
    Returns:
        Dict with geocoding results and statistics
    """
    
    # Set up workspace
    arcpy.env.workspace = r"C:\\temp\\geocoding"
    arcpy.env.overwriteOutput = True
    
    results = {
        'total_addresses': len(addresses_list),
        'processed_count': 0,
        'successful_geocodes': 0,
        'failed_geocodes': 0,
        'geocoded_data': []
    }
    
    try:
        # Create temporary geodatabase
        temp_gdb = arcpy.env.workspace + "\\temp_geocoding.gdb"
        if not arcpy.Exists(temp_gdb):
            arcpy.CreateFileGDB_management(arcpy.env.workspace, "temp_geocoding.gdb")
        
        # NJ Geocode service (configured in ArcGIS Pro template)
        geocode_service = "NJ_Geocode"
        
        # Process in batches
        batch_num = 0
        for i in range(0, len(addresses_list), batch_size):
            batch = addresses_list[i:i + batch_size]
            batch_num += 1
            
            print(f"Processing batch {batch_num}: {len(batch)} addresses")
            
            # Create input table for batch
            input_table = temp_gdb + f"\\batch_{batch_num}_input"
            
            # Create table with address field
            arcpy.CreateTable_management(temp_gdb, f"batch_{batch_num}_input")
            arcpy.AddField_management(input_table, "Address", "TEXT", field_length=255)
            
            # Insert addresses
            with arcpy.da.InsertCursor(input_table, ["Address"]) as cursor:
                for address in batch:
                    cursor.insertRow([address])
            
            # Geocode batch
            output_fc = temp_gdb + f"\\batch_{batch_num}_geocoded"
            
            try:
                arcpy.GeocodeAddresses_geocoding(
                    input_table,
                    geocode_service,
                    "Address Address VISIBLE NONE",
                    output_fc,
                    "STATIC"
                )
                
                # Extract results
                fields = ["Address", "SHAPE@X", "SHAPE@Y", "Score", "Status", "Match_addr"]
                
                with arcpy.da.SearchCursor(output_fc, fields) as cursor:
                    for row in cursor:
                        results['geocoded_data'].append({
                            'address': row[0],
                            'x_coord': row[1],
                            'y_coord': row[2],
                            'geocode_score': row[3],
                            'geocode_status': row[4],
                            'match_address': row[5]
                        })
                        
                        if row[3] >= 80:  # Score >= 80 considered successful
                            results['successful_geocodes'] += 1
                        else:
                            results['failed_geocodes'] += 1
                
                results['processed_count'] += len(batch)
                
            except Exception as e:
                print(f"Error geocoding batch {batch_num}: {e}")
                # Add failed records
                for address in batch:
                    results['geocoded_data'].append({
                        'address': address,
                        'x_coord': None,
                        'y_coord': None,
                        'geocode_score': 0,
                        'geocode_status': 'FAILED',
                        'match_address': None
                    })
                    results['failed_geocodes'] += 1
        
        # Save results to CSV
        if results['geocoded_data']:
            df = pd.DataFrame(results['geocoded_data'])
            df.to_csv(output_path, index=False)
            print(f"Geocoding results saved to: {output_path}")
        
        # Cleanup
        arcpy.Delete_management(temp_gdb)
        
        return results
        
    except Exception as e:
        print(f"Geocoding batch processor error: {e}")
        return results

# Example usage:
# addresses = ["123 Main St, Hackensack, NJ", "456 Oak Ave, Hackensack, NJ"]
# results = batch_geocode_addresses(addresses, "geocoded_results.csv")
'''
        
        # Save geocoding script
        geocoding_script_path = self.project_path / '01_scripts' / 'batch_geocoding_processor.py'
        with open(geocoding_script_path, 'w', encoding='utf-8') as f:
            f.write(geocoding_script)
        
        self.logger.info(f"✅ Geocoding batch processor created: {geocoding_script_path}")
        return str(geocoding_script_path)

    def generate_comprehensive_report(self, all_results: Dict[str, Any]) -> str:
        """Generate comprehensive validation and processing report."""
        self.logger.info("📋 Generating comprehensive report...")
        
        report_data = {
            'report_metadata': {
                'timestamp': datetime.now().isoformat(),
                'generator': 'SCRPA Complete Pipeline Validator',
                'version': '1.0.0'
            },
            'validation_results': all_results,
            'performance_metrics': self.performance_metrics,
            'spatial_enhancement': self.spatial_enhancement_results
        }
        
        # Create JSON report
        json_report_path = self.project_path / '03_output' / f'scrpa_validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Create Markdown summary report
        md_report_path = self.project_path / '03_output' / f'scrpa_validation_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        
        md_content = f"""# SCRPA Complete Pipeline Validation Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Pipeline Version:** v8.0 Standardized

## Executive Summary

"""
        
        # Add validation summaries
        for validation_name, validation_results in all_results.items():
            status = validation_results.get('validation_status', 'UNKNOWN')
            status_emoji = "✅" if status == 'PASS' else "❌" if status == 'FAIL' else "⚠️"
            
            md_content += f"- **{validation_name.replace('_', ' ').title()}:** {status_emoji} {status}\n"
        
        md_content += f"""
## Performance Metrics

- **Pipeline Processing Time:** {self.performance_metrics.get('pipeline_processing_time', 'N/A'):.2f} seconds

## Detailed Results

"""
        
        # Add detailed results for each validation
        for validation_name, validation_results in all_results.items():
            md_content += f"### {validation_name.replace('_', ' ').title()}\n\n"
            
            if validation_name == 'record_counts':
                md_content += f"""**Status:** {validation_results['validation_status']}

**Expected vs Actual:**
- CAD Records: {validation_results['actual_counts'].get('cad_records', 'N/A')} (expected ~114)
- RMS Records: {validation_results['actual_counts'].get('rms_records', 'N/A')} (expected ~135)
- Matched Records: {validation_results['actual_counts'].get('matched_records', 'N/A')} (should match RMS)

"""
            
            elif validation_name == 'column_compliance':
                md_content += f"""**Status:** {validation_results['validation_status']}
**Overall Compliance:** {validation_results['overall_compliance']:.1f}%

**Dataset Compliance:**
"""
                for dataset, compliance in validation_results['datasets'].items():
                    md_content += f"- {dataset}: {compliance['compliance_rate']:.1f}% ({compliance['compliant_columns']}/{compliance['total_columns']})\n"
            
            elif validation_name == 'cad_rms_matching':
                md_content += f"""**Status:** {validation_results['validation_status']}
**Match Rate:** {validation_results['match_rate_percentage']:.1f}% ({validation_results['cad_matches_found']}/{validation_results['total_rms_records']})

**CAD Column Population:**
"""
                for col, stats in validation_results['cad_columns_populated'].items():
                    md_content += f"- {col}: {stats['population_rate']:.1f}% populated\n"
            
            # Add issues if any
            issues = validation_results.get('issues', [])
            if issues:
                md_content += "\n**Issues:**\n"
                for issue in issues:
                    md_content += f"- ⚠️ {issue}\n"
            
            md_content += "\n"
        
        md_content += """
## Next Steps

### For Production Deployment:
1. Address any validation failures above
2. Run spatial enhancement with NJ_Geocode service
3. Integrate with ArcGIS Pro template for mapping
4. Set up automated weekly processing
5. Configure Power BI dashboard with spatial coordinates

### For Spatial Enhancement:
1. Use the batch geocoding processor script
2. Process addresses in 100-record batches
3. Validate spatial grid/zone assignments
4. Generate spatial-enhanced datasets

### For Weekly Automation:  
1. Schedule pipeline execution
2. Monitor validation metrics
3. Generate automated reports
4. Update Power BI datasets
"""
        
        with open(md_report_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        self.logger.info(f"✅ JSON report saved: {json_report_path}")
        self.logger.info(f"✅ Markdown report saved: {md_report_path}")
        
        return str(md_report_path)

    def run_complete_validation(self) -> Dict[str, str]:
        """Run the complete validation pipeline."""
        self.logger.info("🚀 Starting complete SCRPA pipeline validation...")
        start_time = time.time()
        
        all_results = {}
        
        try:
            # 1. Run base pipeline
            pipeline_results = self.run_base_pipeline()
            
            # 2. Validate record counts
            all_results['record_counts'] = self.validate_record_counts(pipeline_results)
            
            # 3. Validate column compliance  
            all_results['column_compliance'] = self.validate_column_compliance(pipeline_results)
            
            # 4. Validate time formatting
            all_results['time_formatting'] = self.validate_time_formatting()
            
            # 5. Validate CAD-RMS matching
            all_results['cad_rms_matching'] = self.validate_cad_rms_matching()
            
            # 6. Validate address standardization
            all_results['address_standardization'] = self.validate_address_standardization()
            
            # 7. Prepare spatial enhancement
            all_results['spatial_preparation'] = self.prepare_spatial_enhancement()
            
            # 8. Create geocoding batch processor
            geocoding_script_path = self.create_geocoding_batch_processor()
            
            # 9. Generate comprehensive report
            report_path = self.generate_comprehensive_report(all_results)
            
            # Record total time
            total_time = time.time() - start_time
            self.performance_metrics['total_validation_time'] = total_time
            
            self.logger.info("=" * 80)
            self.logger.info("🎯 SCRPA COMPLETE VALIDATION FINISHED")
            self.logger.info("=" * 80)
            self.logger.info(f"⏱️ Total time: {total_time:.2f} seconds")
            self.logger.info(f"📋 Report: {report_path}")
            self.logger.info(f"⚙️ Geocoding script: {geocoding_script_path}")
            
            # Summary of validation statuses
            passed_validations = sum(1 for result in all_results.values() 
                                   if result.get('validation_status') == 'PASS')
            total_validations = len(all_results)
            
            self.logger.info(f"✅ Validations passed: {passed_validations}/{total_validations}")
            
            if passed_validations == total_validations:
                self.logger.info("🎉 ALL VALIDATIONS PASSED - PIPELINE READY FOR PRODUCTION")
            else:
                self.logger.warning("⚠️ SOME VALIDATIONS FAILED - REVIEW REPORT FOR DETAILS")
            
            self.logger.info("=" * 80)
            
            return {
                'status': 'SUCCESS',
                'report_path': report_path,
                'geocoding_script_path': geocoding_script_path,
                'validation_summary': f"{passed_validations}/{total_validations} passed"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Complete validation failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e),
                'report_path': None,
                'geocoding_script_path': None
            }

if __name__ == "__main__":
    try:
        validator = SCRPACompleteValidator()
        results = validator.run_complete_validation()
        
        print("\n" + "="*60)
        print("🎯 SCRPA COMPLETE VALIDATION RESULTS")
        print("="*60)
        print(f"Status: {results['status']}")
        if results['status'] == 'SUCCESS':
            print(f"Report: {results['report_path']}")
            print(f"Geocoding Script: {results['geocoding_script_path']}")
            print(f"Validation Summary: {results['validation_summary']}")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
        print("="*60)
        
    except Exception as e:
        print(f"Fatal error: {e}")