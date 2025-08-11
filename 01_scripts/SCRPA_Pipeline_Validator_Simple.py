# 2025-08-01-00-00-00
# SCRPA_Time_v2/SCRPA_Pipeline_Validator_Simple
# Author: R. A. Carucci
# Purpose: Simplified SCRPA pipeline validation and spatial enhancement

import pandas as pd
import numpy as np
import re
import json
import time
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging

class SCRPASimpleValidator:
    """
    Simplified SCRPA pipeline validator with spatial enhancement preparation.
    """
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)
            
        self.output_dir = self.project_path / '04_powerbi'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.validation_results = {}
        self.performance_metrics = {}
        
        self.setup_logging()

    def setup_logging(self):
        """Setup logging without Unicode characters."""
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"scrpa_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("=== SCRPA Pipeline Validator Starting ===")

    def check_existing_outputs(self):
        """Check existing output files and their properties."""
        files_to_check = [
            'cad_data_standardized.csv',
            'rms_data_standardized.csv', 
            'cad_rms_matched_standardized.csv'
        ]
        
        results = {}
        
        for filename in files_to_check:
            file_path = self.output_dir / filename
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    results[filename] = {
                        'exists': True,
                        'record_count': len(df),
                        'column_count': len(df.columns),
                        'columns': list(df.columns),
                        'file_size_mb': file_path.stat().st_size / (1024 * 1024)
                    }
                    self.logger.info(f"Found {filename}: {len(df)} records, {len(df.columns)} columns")
                except Exception as e:
                    results[filename] = {
                        'exists': True,
                        'error': str(e)
                    }
                    self.logger.error(f"Error reading {filename}: {e}")
            else:
                results[filename] = {'exists': False}
                self.logger.warning(f"File not found: {filename}")
        
        return results

    def validate_record_counts(self, file_results):
        """Validate expected record counts."""
        self.logger.info("Validating record counts...")
        
        validation = {
            'timestamp': datetime.now().isoformat(),
            'expected_counts': {
                'cad_records': 114,
                'rms_records': 135,
                'matched_records': 135
            },
            'actual_counts': {},
            'validation_status': 'PASS',
            'issues': []
        }
        
        # Check CAD records
        if 'cad_data_standardized.csv' in file_results and file_results['cad_data_standardized.csv']['exists']:
            cad_count = file_results['cad_data_standardized.csv']['record_count']
            validation['actual_counts']['cad_records'] = cad_count
            
            if cad_count < 110:
                validation['issues'].append(f"CAD record count too low: {cad_count}")
                validation['validation_status'] = 'FAIL'
        
        # Check RMS records
        if 'rms_data_standardized.csv' in file_results and file_results['rms_data_standardized.csv']['exists']:
            rms_count = file_results['rms_data_standardized.csv']['record_count']
            validation['actual_counts']['rms_records'] = rms_count
            
            if rms_count < 130:
                validation['issues'].append(f"RMS record count too low: {rms_count}")
                validation['validation_status'] = 'FAIL'
        
        # Check matched records
        if 'cad_rms_matched_standardized.csv' in file_results and file_results['cad_rms_matched_standardized.csv']['exists']:
            matched_count = file_results['cad_rms_matched_standardized.csv']['record_count']
            validation['actual_counts']['matched_records'] = matched_count
            
            # Should match RMS count
            expected_rms = validation['actual_counts'].get('rms_records', 135)
            if matched_count != expected_rms:
                validation['issues'].append(f"Matched count {matched_count} != RMS count {expected_rms}")
                validation['validation_status'] = 'FAIL'
        
        self.logger.info(f"Record count validation: {validation['validation_status']}")
        for issue in validation['issues']:
            self.logger.warning(f"  Issue: {issue}")
            
        return validation

    def validate_column_compliance(self, file_results):
        """Validate column naming compliance."""
        self.logger.info("Validating column compliance...")
        
        compliance = {
            'timestamp': datetime.now().isoformat(),
            'pattern': 'lowercase_with_underscores',
            'datasets': {},
            'overall_compliance': 0.0,
            'validation_status': 'PASS'
        }
        
        pattern = re.compile(r'^[a-z]+(_[a-z0-9]+)*$')
        
        total_columns = 0
        compliant_columns = 0
        
        for filename, file_info in file_results.items():
            if file_info.get('exists') and 'columns' in file_info:
                columns = file_info['columns']
                dataset_name = filename.replace('.csv', '')
                
                dataset_compliance = {
                    'total_columns': len(columns),
                    'compliant_columns': 0,
                    'compliance_rate': 0.0,
                    'non_compliant': []
                }
                
                for col in columns:
                    if pattern.match(col):
                        dataset_compliance['compliant_columns'] += 1
                        compliant_columns += 1
                    else:
                        dataset_compliance['non_compliant'].append(col)
                
                total_columns += dataset_compliance['total_columns']
                if dataset_compliance['total_columns'] > 0:
                    dataset_compliance['compliance_rate'] = (dataset_compliance['compliant_columns'] / dataset_compliance['total_columns']) * 100
                
                compliance['datasets'][dataset_name] = dataset_compliance
                
                self.logger.info(f"  {dataset_name}: {dataset_compliance['compliance_rate']:.1f}% compliant")
                
                # Log non-compliant columns
                if dataset_compliance['non_compliant']:
                    self.logger.warning(f"    Non-compliant columns: {dataset_compliance['non_compliant'][:5]}")
        
        # Overall compliance
        if total_columns > 0:
            compliance['overall_compliance'] = (compliant_columns / total_columns) * 100
        
        if compliance['overall_compliance'] < 100.0:
            compliance['validation_status'] = 'FAIL'
            self.logger.warning(f"Column compliance FAILED: {compliance['overall_compliance']:.1f}%")
        else:
            self.logger.info("Column compliance PASSED: 100%")
        
        return compliance

    def validate_cad_rms_matching(self):
        """Validate CAD-RMS matching rates."""
        self.logger.info("Validating CAD-RMS matching...")
        
        matching_validation = {
            'timestamp': datetime.now().isoformat(),
            'total_rms_records': 0,
            'cad_matches_found': 0,
            'match_rate_percentage': 0.0,
            'validation_status': 'PASS',
            'issues': []
        }
        
        matched_file = self.output_dir / 'cad_rms_matched_standardized.csv'
        if matched_file.exists():
            try:
                df = pd.read_csv(matched_file)
                matching_validation['total_rms_records'] = len(df)
                
                # Look for CAD columns (with _cad suffix or _CAD suffix)
                cad_columns = [col for col in df.columns if '_cad' in col.lower()]
                
                if cad_columns:
                    # Try to find a key CAD column to count matches
                    key_columns = ['response_type_cad', 'Response_Type_CAD', 'officer_cad', 'Officer_CAD']
                    match_column = None
                    
                    for col in key_columns:
                        if col in df.columns:
                            match_column = col
                            break
                    
                    if match_column:
                        cad_matches = df[match_column].notna().sum()
                        matching_validation['cad_matches_found'] = cad_matches
                        matching_validation['match_rate_percentage'] = (cad_matches / len(df)) * 100 if len(df) > 0 else 0
                    
                    self.logger.info(f"  CAD columns found: {len(cad_columns)}")
                    self.logger.info(f"  Match rate: {matching_validation['match_rate_percentage']:.1f}%")
                
                # Validate reasonable match rate
                if matching_validation['match_rate_percentage'] < 30:
                    matching_validation['issues'].append(f"CAD-RMS match rate too low: {matching_validation['match_rate_percentage']:.1f}%")
                    matching_validation['validation_status'] = 'FAIL'
                
            except Exception as e:
                matching_validation['issues'].append(f"Could not validate CAD-RMS matching: {e}")
                matching_validation['validation_status'] = 'FAIL'
        else:
            matching_validation['issues'].append("CAD-RMS matched file not found")
            matching_validation['validation_status'] = 'FAIL'
        
        self.logger.info(f"CAD-RMS matching validation: {matching_validation['validation_status']}")
        for issue in matching_validation['issues']:
            self.logger.warning(f"  Issue: {issue}")
        
        return matching_validation

    def prepare_spatial_enhancement(self):
        """Prepare spatial enhancement with address collection."""
        self.logger.info("Preparing spatial enhancement...")
        
        spatial_prep = {
            'timestamp': datetime.now().isoformat(),
            'template_path': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\7_Day_Templet_SCRPA_Time.aprx",
            'template_exists': False,
            'spatial_columns_to_add': ['x_coord', 'y_coord', 'geocode_score', 'geocode_status', 'match_address'],
            'coordinate_system': 'State Plane NJ (EPSG:3424)',
            'addresses_collected': 0,
            'preparation_status': 'READY'
        }
        
        # Check template
        template_path = Path(spatial_prep['template_path'])
        spatial_prep['template_exists'] = template_path.exists()
        
        if spatial_prep['template_exists']:
            self.logger.info(f"ArcGIS Pro template found: {template_path}")
        else:
            self.logger.warning(f"ArcGIS Pro template not found: {template_path}")
            spatial_prep['preparation_status'] = 'WARNING'
        
        # Collect unique addresses
        all_addresses = set()
        address_columns = ['location', 'Location']
        
        files_to_check = ['rms_data_standardized.csv', 'cad_data_standardized.csv']
        
        for filename in files_to_check:
            file_path = self.output_dir / filename
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    
                    # Find address column
                    addr_col = None
                    for col in address_columns:
                        if col in df.columns:
                            addr_col = col
                            break
                    
                    if addr_col:
                        addresses = df[addr_col].dropna().unique()
                        unique_addresses = set(str(addr) for addr in addresses if pd.notna(addr) and str(addr).strip())
                        all_addresses.update(unique_addresses)
                        
                        self.logger.info(f"  {filename}: {len(unique_addresses)} unique addresses")
                
                except Exception as e:
                    self.logger.error(f"Error collecting addresses from {filename}: {e}")
        
        spatial_prep['addresses_collected'] = len(all_addresses)
        spatial_prep['estimated_batches'] = (len(all_addresses) + 99) // 100  # 100 per batch
        
        self.logger.info(f"Total unique addresses: {len(all_addresses)}")
        self.logger.info(f"Estimated geocoding batches: {spatial_prep['estimated_batches']}")
        
        return spatial_prep

    def create_enhanced_geocoding_script(self):
        """Create an enhanced geocoding script."""
        self.logger.info("Creating geocoding script...")
        
        script_content = '''import arcpy
import pandas as pd
import os
from pathlib import Path
import logging

def setup_logging():
    """Setup logging for geocoding process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('geocoding.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def geocode_scrpa_addresses(input_csv_path, output_csv_path, batch_size=100):
    """
    Geocode addresses from SCRPA data using NJ_Geocode service.
    
    Args:
        input_csv_path: Path to CSV with addresses
        output_csv_path: Path to save geocoded results
        batch_size: Addresses per batch
    
    Returns:
        Dictionary with geocoding statistics
    """
    
    logger = setup_logging()
    logger.info("Starting SCRPA address geocoding...")
    
    # Results tracking
    results = {
        'total_addresses': 0,
        'successful_geocodes': 0,
        'failed_geocodes': 0,
        'high_accuracy_geocodes': 0,  # Score >= 90
        'processing_time': 0
    }
    
    try:
        import time
        start_time = time.time()
        
        # Read input data
        df = pd.read_csv(input_csv_path)
        
        # Find address column
        address_column = None
        possible_columns = ['location', 'Location', 'address', 'Address', 'full_address_raw']
        
        for col in possible_columns:
            if col in df.columns:
                address_column = col
                break
        
        if not address_column:
            raise ValueError(f"No address column found. Available columns: {list(df.columns)}")
        
        logger.info(f"Using address column: {address_column}")
        
        # Get unique addresses
        addresses = df[address_column].dropna().unique()
        results['total_addresses'] = len(addresses)
        
        logger.info(f"Found {len(addresses)} unique addresses to geocode")
        
        # Setup ArcGIS workspace
        arcpy.env.workspace = r"C:\\temp"
        arcpy.env.overwriteOutput = True
        
        # Create temporary workspace
        temp_gdb = "geocoding_temp.gdb"
        if arcpy.Exists(temp_gdb):
            arcpy.Delete_management(temp_gdb)
        arcpy.CreateFileGDB_management(arcpy.env.workspace, "geocoding_temp")
        
        # Geocoding service (configured in ArcGIS Pro)
        geocode_service = "NJ_Geocode"
        
        # Process all addresses at once for better performance
        logger.info("Creating input table for geocoding...")
        
        input_table = os.path.join(temp_gdb, "addresses_to_geocode")
        arcpy.CreateTable_management(temp_gdb, "addresses_to_geocode")
        arcpy.AddField_management(input_table, "Address", "TEXT", field_length=500)
        arcpy.AddField_management(input_table, "ID", "LONG")
        
        # Insert addresses
        with arcpy.da.InsertCursor(input_table, ["Address", "ID"]) as cursor:
            for i, address in enumerate(addresses):
                cursor.insertRow([str(address), i])
        
        # Geocode all addresses
        logger.info("Geocoding addresses...")
        output_fc = os.path.join(temp_gdb, "geocoded_addresses")
        
        arcpy.GeocodeAddresses_geocoding(
            input_table,
            geocode_service,
            "Address Address VISIBLE NONE",
            output_fc,
            "STATIC"
        )
        
        # Extract results
        logger.info("Extracting geocoding results...")
        geocoded_data = []
        
        fields = ["Address", "SHAPE@X", "SHAPE@Y", "Score", "Status", "Match_addr", "ID"]
        
        with arcpy.da.SearchCursor(output_fc, fields) as cursor:
            for row in cursor:
                geocoded_data.append({
                    'original_address': row[0],
                    'x_coord': row[1] if row[1] else None,
                    'y_coord': row[2] if row[2] else None,
                    'geocode_score': row[3] if row[3] else 0,
                    'geocode_status': row[4] if row[4] else 'FAILED',
                    'match_address': row[5] if row[5] else None,
                    'address_id': row[6]
                })
                
                # Count results
                if row[3] and row[3] >= 80:
                    results['successful_geocodes'] += 1
                    if row[3] >= 90:
                        results['high_accuracy_geocodes'] += 1
                else:
                    results['failed_geocodes'] += 1
        
        # Save results
        if geocoded_data:
            results_df = pd.DataFrame(geocoded_data)
            results_df.to_csv(output_csv_path, index=False)
            logger.info(f"Geocoded results saved to: {output_csv_path}")
        
        # Cleanup
        arcpy.Delete_management(temp_gdb)
        
        # Calculate processing time
        results['processing_time'] = time.time() - start_time
        
        # Log final statistics
        logger.info("Geocoding completed!")
        logger.info(f"Total addresses: {results['total_addresses']}")
        logger.info(f"Successful geocodes: {results['successful_geocodes']}")
        logger.info(f"High accuracy (>=90): {results['high_accuracy_geocodes']}")
        logger.info(f"Failed geocodes: {results['failed_geocodes']}")
        logger.info(f"Success rate: {(results['successful_geocodes']/results['total_addresses']*100):.1f}%")
        logger.info(f"Processing time: {results['processing_time']:.2f} seconds")
        
        return results
        
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        results['error'] = str(e)
        return results

# Example usage:
if __name__ == "__main__":
    # Geocode RMS data
    rms_path = r"C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\04_powerbi\\rms_data_standardized.csv"
    rms_output = r"C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\04_powerbi\\rms_data_geocoded.csv"
    
    if os.path.exists(rms_path):
        print("Geocoding RMS data...")
        rms_results = geocode_scrpa_addresses(rms_path, rms_output)
        print(f"RMS geocoding results: {rms_results}")
    
    # Geocode CAD data
    cad_path = r"C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\04_powerbi\\cad_data_standardized.csv"
    cad_output = r"C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\04_powerbi\\cad_data_geocoded.csv"
    
    if os.path.exists(cad_path):
        print("Geocoding CAD data...")
        cad_results = geocode_scrpa_addresses(cad_path, cad_output)
        print(f"CAD geocoding results: {cad_results}")
'''
        
        # Save geocoding script
        script_path = self.project_path / '01_scripts' / 'scrpa_geocoding_enhanced.py'
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        self.logger.info(f"Enhanced geocoding script created: {script_path}")
        return str(script_path)

    def generate_validation_report(self, all_results):
        """Generate validation report."""
        self.logger.info("Generating validation report...")
        
        # Create timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON report
        json_report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'validator_version': '1.0.0',
                'project_path': str(self.project_path)
            },
            'validation_results': all_results,
            'performance_metrics': self.performance_metrics
        }
        
        json_path = self.project_path / '03_output' / f'scrpa_validation_report_{timestamp}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, default=str)
        
        # Markdown summary
        md_content = f"""# SCRPA Pipeline Validation Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Validator Version:** 1.0.0

## Executive Summary

"""
        
        # Count passed/failed validations
        passed_count = 0
        total_count = 0
        
        for validation_name, validation_data in all_results.items():
            if isinstance(validation_data, dict):
                status = validation_data.get('validation_status', 'UNKNOWN')
                status_icon = "✅" if status == 'PASS' else "❌" if status == 'FAIL' else "⚠️"
                md_content += f"- **{validation_name.replace('_', ' ').title()}:** {status_icon} {status}\n"
                
                if status == 'PASS':
                    passed_count += 1
                total_count += 1
        
        md_content += f"\n**Overall Result:** {passed_count}/{total_count} validations passed\n\n"
        
        # Detailed results
        md_content += "## Detailed Results\n\n"
        
        for validation_name, validation_data in all_results.items():
            if isinstance(validation_data, dict):
                md_content += f"### {validation_name.replace('_', ' ').title()}\n\n"
                
                status = validation_data.get('validation_status', 'UNKNOWN')
                md_content += f"**Status:** {status}\n\n"
                
                # Add specific details based on validation type
                if validation_name == 'record_counts':
                    actual = validation_data.get('actual_counts', {})
                    expected = validation_data.get('expected_counts', {})
                    md_content += f"**Record Counts:**\n"
                    md_content += f"- CAD: {actual.get('cad_records', 'N/A')} (expected ~{expected.get('cad_records', 114)})\n"
                    md_content += f"- RMS: {actual.get('rms_records', 'N/A')} (expected ~{expected.get('rms_records', 135)})\n"
                    md_content += f"- Matched: {actual.get('matched_records', 'N/A')} (should match RMS)\n\n"
                
                elif validation_name == 'column_compliance':
                    overall = validation_data.get('overall_compliance', 0)
                    md_content += f"**Overall Compliance:** {overall:.1f}%\n\n"
                    
                    datasets = validation_data.get('datasets', {})
                    if datasets:
                        md_content += "**Dataset Details:**\n"
                        for dataset_name, compliance in datasets.items():
                            rate = compliance.get('compliance_rate', 0)
                            compliant = compliance.get('compliant_columns', 0)
                            total = compliance.get('total_columns', 0)
                            md_content += f"- {dataset_name}: {rate:.1f}% ({compliant}/{total})\n"
                        md_content += "\n"
                
                elif validation_name == 'cad_rms_matching':
                    match_rate = validation_data.get('match_rate_percentage', 0)
                    matches = validation_data.get('cad_matches_found', 0)
                    total = validation_data.get('total_rms_records', 0)
                    md_content += f"**Match Rate:** {match_rate:.1f}% ({matches}/{total})\n\n"
                
                # Add issues if any
                issues = validation_data.get('issues', [])
                if issues:
                    md_content += "**Issues Found:**\n"
                    for issue in issues:
                        md_content += f"- {issue}\n"
                    md_content += "\n"
        
        # Next steps
        md_content += """## Next Steps

### Immediate Actions:
1. Address any validation failures listed above
2. Run spatial enhancement geocoding if validation passes
3. Test Power BI integration with geocoded data

### For Production:
1. Set up weekly automated processing
2. Configure monitoring and alerting
3. Create user training materials
4. Establish data quality thresholds

### For Spatial Enhancement:
1. Run the enhanced geocoding script on all datasets
2. Validate geocoding accuracy (target >85% success rate)
3. Create spatial-enabled Power BI dashboards
4. Set up ArcGIS Pro integration for mapping
"""
        
        md_path = self.project_path / '03_output' / f'scrpa_validation_summary_{timestamp}.md'
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        self.logger.info(f"JSON report: {json_path}")
        self.logger.info(f"Markdown summary: {md_path}")
        
        return str(md_path)

    def run_complete_validation(self):
        """Run complete validation process."""
        self.logger.info("Starting complete SCRPA validation...")
        start_time = time.time()
        
        try:
            # 1. Check existing output files
            self.logger.info("Step 1: Checking existing output files...")
            file_results = self.check_existing_outputs()
            
            # 2. Validate record counts
            self.logger.info("Step 2: Validating record counts...")
            record_validation = self.validate_record_counts(file_results)
            
            # 3. Validate column compliance
            self.logger.info("Step 3: Validating column compliance...")
            column_validation = self.validate_column_compliance(file_results)
            
            # 4. Validate CAD-RMS matching
            self.logger.info("Step 4: Validating CAD-RMS matching...")
            matching_validation = self.validate_cad_rms_matching()
            
            # 5. Prepare spatial enhancement
            self.logger.info("Step 5: Preparing spatial enhancement...")
            spatial_prep = self.prepare_spatial_enhancement()
            
            # 6. Create geocoding script
            self.logger.info("Step 6: Creating geocoding script...")
            geocoding_script = self.create_enhanced_geocoding_script()
            
            # Compile all results
            all_results = {
                'file_check': file_results,
                'record_counts': record_validation,
                'column_compliance': column_validation,
                'cad_rms_matching': matching_validation,
                'spatial_preparation': spatial_prep
            }
            
            # Record performance
            total_time = time.time() - start_time
            self.performance_metrics['total_validation_time'] = total_time
            
            # 7. Generate report
            self.logger.info("Step 7: Generating validation report...")
            report_path = self.generate_validation_report(all_results)
            
            # Summary
            self.logger.info("="*60)
            self.logger.info("SCRPA VALIDATION COMPLETE")
            self.logger.info("="*60)
            self.logger.info(f"Total time: {total_time:.2f} seconds")
            self.logger.info(f"Report: {report_path}")
            self.logger.info(f"Geocoding script: {geocoding_script}")
            
            # Check overall status
            passed_validations = sum(1 for result in [record_validation, column_validation, matching_validation] 
                                   if result.get('validation_status') == 'PASS')
            total_validations = 3
            
            self.logger.info(f"Validations passed: {passed_validations}/{total_validations}")
            
            if passed_validations == total_validations:
                self.logger.info("ALL VALIDATIONS PASSED - READY FOR PRODUCTION")
            else:
                self.logger.warning("SOME VALIDATIONS FAILED - REVIEW REPORT")
            
            self.logger.info("="*60)
            
            return {
                'status': 'SUCCESS',
                'report_path': report_path,
                'geocoding_script': geocoding_script,
                'validations_passed': f"{passed_validations}/{total_validations}",
                'ready_for_production': passed_validations == total_validations
            }
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }

if __name__ == "__main__":
    try:
        validator = SCRPASimpleValidator()
        results = validator.run_complete_validation()
        
        print("\n" + "="*60)
        print("SCRPA VALIDATION RESULTS")
        print("="*60)
        print(f"Status: {results['status']}")
        
        if results['status'] == 'SUCCESS':
            print(f"Report: {results['report_path']}")
            print(f"Geocoding Script: {results['geocoding_script']}")
            print(f"Validations: {results['validations_passed']}")
            print(f"Production Ready: {results['ready_for_production']}")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
        
        print("="*60)
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import sys
        sys.exit(1)