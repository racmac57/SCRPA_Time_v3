#!/usr/bin/env python3
"""
Production Pipeline Validator for SCRPA Data Processing
Comprehensive testing, benchmarking, and validation suite.
"""

import pandas as pd
import numpy as np
import time
import json
import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Tuple, Any
import concurrent.futures
import psutil
import memory_profiler

# Import our processing modules
from fixed_data_quality import SCRPADataProcessor
from reference_integration_functions import ReferenceDataIntegrator, NJGeocodingService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_for_json(obj):
    """Recursively clean data structure for JSON serialization"""
    if isinstance(obj, dict):
        return {key: clean_for_json(value) for key, value in obj.items() if not callable(value)}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj if not callable(item)]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, 'item'):
        return obj.item()
    elif callable(obj):
        return f"<function: {getattr(obj, '__name__', 'unknown')}>"
    else:
        return obj

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle cleaned data structures"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if hasattr(obj, 'item'):
            return obj.item()
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

class ProductionValidator:
    """Comprehensive production validation and benchmarking suite"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.results = {}
        self.benchmarks = {}
        self.test_cases = []
        
        # Initialize processors
        self.processor = SCRPADataProcessor(base_path)
        self.integrator = ReferenceDataIntegrator(os.path.join(base_path, "10_Refrence_Files"))
        
        # Performance tracking
        self.start_memory = psutil.virtual_memory().used
        self.start_time = time.time()
    
    def log_performance(self, operation: str, start_time: float, records_processed: int = 0):
        """Log performance metrics for an operation"""
        duration = time.time() - start_time
        current_memory = psutil.virtual_memory().used
        memory_delta = current_memory - self.start_memory
        
        perf_data = {
            'operation': operation,
            'duration_seconds': round(duration, 3),
            'records_processed': records_processed,
            'records_per_second': round(records_processed / duration if duration > 0 else 0, 2),
            'memory_used_mb': round(memory_delta / 1024 / 1024, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        self.benchmarks[operation] = perf_data
        logger.info(f"{operation}: {duration:.3f}s, {records_processed} records, {perf_data['records_per_second']} rec/s")
        return perf_data
    
    def create_test_datasets(self, base_size: int = 1000) -> Dict[str, pd.DataFrame]:
        """Create synthetic test datasets of various sizes"""
        logger.info(f"Creating test datasets with base size {base_size}")
        
        # Load real data as template
        real_rms = pd.read_csv(os.path.join(self.base_path, "03_output", "enhanced_rms_data_20250731_025811.csv"))
        real_cad = pd.read_csv(os.path.join(self.base_path, "03_output", "enhanced_cad_data_20250731_025811.csv"))
        
        test_datasets = {}
        
        # Create datasets of different sizes
        sizes = [100, 500, 1000, 2000, 5000]
        
        for size in sizes:
            if size <= len(real_rms):
                # Use real data subset
                test_rms = real_rms.head(size).copy()
                test_cad = real_cad.head(min(size, len(real_cad))).copy()
            else:
                # Replicate and modify real data
                multiplier = size // len(real_rms) + 1
                test_rms = pd.concat([real_rms] * multiplier, ignore_index=True).head(size)
                test_cad = pd.concat([real_cad] * multiplier, ignore_index=True).head(size)
                
                # Modify case numbers to be unique
                test_rms['case_number'] = test_rms['case_number'].astype(str) + '_' + test_rms.index.astype(str)
                test_cad['report_number_new'] = test_cad['report_number_new'].astype(str) + '_' + test_cad.index.astype(str)
            
            test_datasets[f'rms_{size}'] = test_rms
            test_datasets[f'cad_{size}'] = test_cad
        
        logger.info(f"Created {len(test_datasets)} test datasets")
        return test_datasets
    
    def benchmark_data_processing(self, test_datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Benchmark core data processing operations"""
        logger.info("Starting data processing benchmarks")
        
        processing_benchmarks = {}
        
        # Test RMS processing with different sizes
        for dataset_name, dataset in test_datasets.items():
            if 'rms' not in dataset_name:
                continue
                
            size = dataset_name.split('_')[1]
            logger.info(f"Benchmarking RMS processing - {size} records")
            
            start_time = time.time()
            
            try:
                # Simulate processing steps
                processed_df = dataset.copy()
                
                # Convert headers to snake_case
                processed_df.columns = self.processor._convert_to_snake_case(processed_df.columns)
                
                # Fix incident time
                if 'incident_time' in processed_df.columns:
                    processed_df['incident_time'] = self.processor._fix_incident_time_format(processed_df['incident_time'])
                
                # Clean addresses
                if 'full_address' in processed_df.columns:
                    processed_df['full_address'] = self.processor._clean_address_data(processed_df['full_address'])
                
                # Convert Squad to uppercase
                if 'squad' in processed_df.columns:
                    processed_df['squad'] = processed_df['squad'].str.upper()
                
                perf_data = self.log_performance(f'RMS_processing_{size}', start_time, len(dataset))
                processing_benchmarks[f'RMS_{size}'] = perf_data
                
            except Exception as e:
                logger.error(f"RMS processing failed for size {size}: {e}")
                processing_benchmarks[f'RMS_{size}'] = {'error': str(e)}
        
        # Test CAD processing
        for dataset_name, dataset in test_datasets.items():
            if 'cad' not in dataset_name:
                continue
                
            size = dataset_name.split('_')[1]
            logger.info(f"Benchmarking CAD processing - {size} records")
            
            start_time = time.time()
            
            try:
                processed_df = dataset.copy()
                processed_df.columns = self.processor._convert_to_snake_case(processed_df.columns)
                
                # Add response type lookup
                if 'incident' in processed_df.columns and not self.processor.calltype_categories.empty:
                    processed_df = self.processor._add_response_type_lookup(processed_df, 'incident')
                
                perf_data = self.log_performance(f'CAD_processing_{size}', start_time, len(dataset))
                processing_benchmarks[f'CAD_{size}'] = perf_data
                
            except Exception as e:
                logger.error(f"CAD processing failed for size {size}: {e}")
                processing_benchmarks[f'CAD_{size}'] = {'error': str(e)}
        
        return processing_benchmarks
    
    def test_geocoding_integration(self) -> Dict[str, Any]:
        """Test NJ Geocoding integration with various scenarios"""
        logger.info("Testing NJ Geocoding integration")
        
        geocoding_service = NJGeocodingService()
        
        # Test addresses - mix of valid and problematic ones
        test_addresses = [
            "309 Lookout Avenue, Hackensack, NJ, 07601",
            "135 First Street, Hackensack, NJ, 07601",
            "Invalid Address Format",
            "123 Main St, Hackensack, NJ",
            "456 Oak Avenue, Hackensack, NJ, 07601",
            "",  # Empty address
            None,  # Null address
            "789 Pine Street, Newark, NJ, 07102",  # Different NJ city
        ]
        
        geocoding_results = {
            'total_addresses': len(test_addresses),
            'successful_geocodes': 0,
            'failed_geocodes': 0,
            'validation_issues': 0,
            'performance': {}
        }
        
        start_time = time.time()
        
        for i, address in enumerate(test_addresses):
            try:
                result = geocoding_service.geocode_address(address)
                
                if result['status'] == 'SUCCESS':
                    geocoding_results['successful_geocodes'] += 1
                else:
                    geocoding_results['failed_geocodes'] += 1
                    
                if result.get('error_message'):
                    geocoding_results['validation_issues'] += 1
                    
            except Exception as e:
                logger.error(f"Geocoding error for address {i}: {e}")
                geocoding_results['failed_geocodes'] += 1
        
        geocoding_results['performance'] = self.log_performance(
            'geocoding_batch', start_time, len(test_addresses)
        )
        
        # Test batch processing
        start_time = time.time()
        batch_results = geocoding_service.batch_geocode(test_addresses[:5])
        geocoding_results['batch_performance'] = self.log_performance(
            'geocoding_batch_api', start_time, 5
        )
        
        return geocoding_results
    
    def test_arcgis_functionality(self) -> Dict[str, Any]:
        """Test ArcGIS/ArcPy functionality"""
        logger.info("Testing ArcGIS functionality")
        
        arcgis_results = {
            'arcpy_available': False,
            'spatial_operations': {},
            'errors': []
        }
        
        try:
            from reference_integration_functions import ArcGISIntegration
            arcgis = ArcGISIntegration()
            
            arcgis_results['arcpy_available'] = arcgis.arcpy_available
            
            if arcgis.arcpy_available:
                # Test with sample coordinate data
                sample_coords = pd.DataFrame({
                    'x_coordinate': [-74.0431, -74.0432, -74.0433],
                    'y_coordinate': [40.8859, 40.8860, 40.8861],
                    'address': ['309 Lookout Ave', '135 First St', '90 Prospect Ave'],
                    'case_number': ['25-000813', '25-002564', '25-002635'],
                    'incident_type': ['Theft', 'Assault', 'Vandalism']
                })
                
                # Test point feature creation (mock)
                start_time = time.time()
                test_output = os.path.join(self.base_path, "temp_test_features.shp")
                
                # This would fail without proper ArcGIS setup, but we'll track the attempt
                try:
                    success = arcgis.create_point_features(sample_coords, test_output)
                    arcgis_results['spatial_operations']['point_creation'] = {
                        'success': success,
                        'performance': self.log_performance('arcgis_point_creation', start_time, len(sample_coords))
                    }
                except Exception as e:
                    arcgis_results['spatial_operations']['point_creation'] = {
                        'success': False,
                        'error': str(e)
                    }
            else:
                arcgis_results['errors'].append("ArcPy not available - install ArcGIS Pro or ArcMap")
                
        except Exception as e:
            arcgis_results['errors'].append(f"ArcGIS integration error: {e}")
        
        return arcgis_results
    
    def quality_assurance_testing(self) -> Dict[str, Any]:
        """Comprehensive quality assurance on processed data"""
        logger.info("Running quality assurance testing")
        
        qa_results = {
            'data_integrity': {},
            'format_validation': {},
            'reference_lookups': {},
            'completeness': {}
        }
        
        # Load processed datasets
        rms_file = os.path.join(self.base_path, "03_output", "enhanced_rms_data_20250731_025811.csv")
        cad_file = os.path.join(self.base_path, "03_output", "enhanced_cad_data_20250731_025811.csv")
        final_file = os.path.join(self.base_path, "03_output", "enhanced_final_datasets.csv")
        
        try:
            rms_df = pd.read_csv(rms_file)
            cad_df = pd.read_csv(cad_file)
            final_df = pd.read_csv(final_file)
            
            # Data integrity checks
            qa_results['data_integrity'] = {
                'rms_records': len(rms_df),
                'cad_records': len(cad_df),
                'final_records': len(final_df),
                'rms_duplicates': rms_df.duplicated().sum(),
                'cad_duplicates': cad_df.duplicated().sum(),
                'final_duplicates': final_df.duplicated().sum()
            }
            
            # Format validation
            format_checks = {
                'snake_case_headers': True,
                'incident_time_format': True,
                'squad_uppercase': True,
                'response_type_populated': True
            }
            
            # Check snake_case headers
            for col in rms_df.columns:
                if not col.islower() or ' ' in col:
                    format_checks['snake_case_headers'] = False
                    break
            
            # Check incident time format (HH:MM)
            if 'incident_time' in rms_df.columns:
                time_pattern = rms_df['incident_time'].str.match(r'^\d{2}:\d{2}$', na=False)
                format_checks['incident_time_format'] = time_pattern.all()
            
            # Check Squad uppercase
            if 'squad' in rms_df.columns:
                squad_upper = rms_df['squad'].str.isupper()
                format_checks['squad_uppercase'] = squad_upper.all()
            
            # Check response type population
            if 'response_type' in cad_df.columns:
                response_populated = cad_df['response_type'].notna().sum() / len(cad_df)
                format_checks['response_type_populated'] = response_populated > 0.8
            
            qa_results['format_validation'] = format_checks
            
            # Reference lookup validation
            calltype_matches = 0
            if 'response_type' in cad_df.columns:
                calltype_matches = cad_df['response_type'].notna().sum()
            
            qa_results['reference_lookups'] = {
                'calltype_categories_loaded': len(self.processor.calltype_categories),
                'calltype_matches_found': calltype_matches,
                'calltype_match_rate': calltype_matches / len(cad_df) if len(cad_df) > 0 else 0
            }
            
            # Completeness checks
            qa_results['completeness'] = {
                'rms_required_fields': {
                    'case_number': (rms_df['case_number'].notna().sum() / len(rms_df)),
                    'incident_time': (rms_df['incident_time'].notna().sum() / len(rms_df)) if 'incident_time' in rms_df.columns else 0,
                    'full_address': (rms_df['full_address'].notna().sum() / len(rms_df)) if 'full_address' in rms_df.columns else 0
                },
                'cad_required_fields': {
                    'report_number_new': (cad_df['report_number_new'].notna().sum() / len(cad_df)),
                    'incident': (cad_df['incident'].notna().sum() / len(cad_df)) if 'incident' in cad_df.columns else 0,
                    'response_type': (cad_df['response_type'].notna().sum() / len(cad_df)) if 'response_type' in cad_df.columns else 0
                }
            }
            
        except Exception as e:
            qa_results['error'] = str(e)
            logger.error(f"QA testing failed: {e}")
        
        return qa_results
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and edge cases"""
        logger.info("Testing error handling and edge cases")
        
        error_test_results = {
            'edge_cases_tested': 0,
            'errors_handled': 0,
            'unhandled_errors': 0,
            'test_cases': []
        }
        
        # Test cases for edge conditions
        edge_cases = [
            {
                'name': 'empty_dataframe',
                'test': lambda: self.processor.process_rms_data.__call__,
                'data': pd.DataFrame()
            },
            {
                'name': 'missing_columns',
                'data': pd.DataFrame({'wrong_column': [1, 2, 3]})
            },
            {
                'name': 'null_values',
                'data': pd.DataFrame({
                    'case_number': [None, '', 'valid'],
                    'incident_time': [None, '', '21:30'],
                    'full_address': [None, '', 'valid address']
                })
            },
            {
                'name': 'malformed_data',
                'data': pd.DataFrame({
                    'incident_time': ['invalid', '25:99', 'not-time'],
                    'squad': [123, None, 'valid']
                })
            }
        ]
        
        for case in edge_cases:
            error_test_results['edge_cases_tested'] += 1
            
            try:
                # Test various processing functions with edge case data
                if 'data' in case:
                    # Test snake_case conversion
                    result = self.processor._convert_to_snake_case(case['data'].columns)
                    
                    # Test time formatting
                    if 'incident_time' in case['data'].columns:
                        result = self.processor._fix_incident_time_format(case['data']['incident_time'])
                    
                    # Test address cleaning
                    if 'full_address' in case['data'].columns:
                        result = self.processor._clean_address_data(case['data']['full_address'])
                
                error_test_results['errors_handled'] += 1
                case['result'] = 'handled'
                
            except Exception as e:
                error_test_results['unhandled_errors'] += 1
                case['result'] = f'unhandled_error: {str(e)}'
                logger.warning(f"Unhandled error in {case['name']}: {e}")
            
            error_test_results['test_cases'].append(case)
        
        return error_test_results
    
    def concurrent_processing_test(self) -> Dict[str, Any]:
        """Test concurrent processing capabilities"""
        logger.info("Testing concurrent processing")
        
        concurrent_results = {
            'single_thread': {},
            'multi_thread': {},
            'performance_improvement': 0
        }
        
        # Create test dataset
        test_addresses = [
            f"Address {i}, Hackensack, NJ, 07601" for i in range(100)
        ]
        
        # Single-threaded processing
        start_time = time.time()
        geocoding_service = NJGeocodingService()
        single_results = []
        for address in test_addresses:
            single_results.append(geocoding_service.geocode_address(address))
        
        concurrent_results['single_thread'] = self.log_performance(
            'single_thread_geocoding', start_time, len(test_addresses)
        )
        
        # Multi-threaded processing
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            multi_results = list(executor.map(geocoding_service.geocode_address, test_addresses))
        
        concurrent_results['multi_thread'] = self.log_performance(
            'multi_thread_geocoding', start_time, len(test_addresses)
        )
        
        # Calculate improvement
        single_time = concurrent_results['single_thread']['duration_seconds']
        multi_time = concurrent_results['multi_thread']['duration_seconds']
        improvement = ((single_time - multi_time) / single_time) * 100 if single_time > 0 else 0
        concurrent_results['performance_improvement'] = round(improvement, 2)
        
        return concurrent_results
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        logger.info("Starting full production validation suite")
        
        validation_start = time.time()
        
        # Run all validation tests
        validation_results = {
            'validation_metadata': {
                'start_time': datetime.now().isoformat(),
                'python_version': f"{sys.version}",
                'system_info': {
                    'cpu_count': psutil.cpu_count(),
                    'memory_gb': round(psutil.virtual_memory().total / 1024**3, 2),
                    'platform': os.name
                }
            }
        }
        
        try:
            # 1. Performance benchmarks
            self.log_performance('validation_start', validation_start, 0)
            test_datasets = self.create_test_datasets(1000)
            validation_results['performance_benchmarks'] = self.benchmark_data_processing(test_datasets)
            
            # 2. Geocoding integration
            validation_results['geocoding_integration'] = self.test_geocoding_integration()
            
            # 3. ArcGIS functionality
            validation_results['arcgis_functionality'] = self.test_arcgis_functionality()
            
            # 4. Quality assurance
            validation_results['quality_assurance'] = self.quality_assurance_testing()
            
            # 5. Error handling
            validation_results['error_handling'] = self.test_error_handling()
            
            # 6. Concurrent processing
            validation_results['concurrent_processing'] = self.concurrent_processing_test()
            
            # Overall performance summary
            total_duration = time.time() - validation_start
            validation_results['validation_summary'] = {
                'total_duration_seconds': round(total_duration, 3),
                'total_memory_used_mb': round((psutil.virtual_memory().used - self.start_memory) / 1024 / 1024, 2),
                'validation_complete': True,
                'end_time': datetime.now().isoformat()
            }
            
            logger.info(f"Full validation completed in {total_duration:.3f} seconds")
            
        except Exception as e:
            validation_results['validation_error'] = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            logger.error(f"Validation failed: {e}")
        
        return validation_results

def main():
    """Main validation execution"""
    base_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
    
    validator = ProductionValidator(base_path)
    results = validator.run_full_validation()
    
    # Export results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Clean data for JSON serialization
    clean_benchmarks = clean_for_json(validator.benchmarks)
    clean_results = clean_for_json(results)
    
    # Performance benchmarks JSON
    benchmarks_file = os.path.join(base_path, f"performance_benchmarks_{timestamp}.json")
    with open(benchmarks_file, 'w') as f:
        json.dump(clean_benchmarks, f, indent=2, cls=NumpyEncoder)
    
    # Full validation results JSON
    results_file = os.path.join(base_path, f"production_validation_results_{timestamp}.json")
    with open(results_file, 'w') as f:
        json.dump(clean_results, f, indent=2, cls=NumpyEncoder)
    
    logger.info(f"Validation results exported to: {results_file}")
    logger.info(f"Performance benchmarks exported to: {benchmarks_file}")
    
    return results, validator.benchmarks

if __name__ == "__main__":
    main()