#!/usr/bin/env python3
"""
SCRPA Production Deployment Pipeline
Complete automated processing with validation checks and monitoring
"""

import pandas as pd
import numpy as np
import json
import re
import logging
import time
import traceback
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

class SCRPAProductionPipeline:
    def __init__(self, config: Optional[Dict] = None):
        """Initialize production pipeline with configuration"""
        self.config = config or self._default_config()
        self.logger = self._setup_logging()
        self.pipeline_start_time = None
        self.processing_stats = {}
        
        # Quality thresholds
        self.min_validation_rate = 70.0  # Minimum 70% validation rate
        self.max_processing_time = 300   # Maximum 5 minutes processing time
        
        # Target crimes and patterns
        self.target_crimes = [
            "Motor Vehicle Theft",
            "Robbery", 
            "Burglary – Auto",
            "Sexual",
            "Burglary – Commercial", 
            "Burglary – Residence"
        ]
        
        self.crime_patterns = {
            "Motor Vehicle Theft": [
                r"motor\s*vehicle\s*theft",
                r"theft\s*of\s*motor\s*vehicle",
                r"auto\s*theft",
                r"car\s*theft",
                r"vehicle\s*theft",
                r"240\s*=\s*theft\s*of\s*motor\s*vehicle"
            ],
            "Robbery": [
                r"robbery",
                r"120\s*=\s*robbery"
            ],
            "Burglary – Auto": [
                r"burglary\s*[-–]\s*auto",
                r"auto\s*burglary",
                r"theft\s*from\s*motor\s*vehicle",
                r"23f\s*=\s*theft\s*from\s*motor\s*vehicle"
            ],
            "Sexual": [
                r"sexual",
                r"11d\s*=\s*fondling",
                r"criminal\s*sexual\s*contact"
            ],
            "Burglary – Commercial": [
                r"burglary\s*[-–]\s*commercial",
                r"commercial\s*burglary",
                r"220\s*=\s*burglary.*commercial"
            ],
            "Burglary – Residence": [
                r"burglary\s*[-–]\s*residence",
                r"residential\s*burglary",
                r"220\s*=\s*burglary.*residential"
            ]
        }
    
    def _default_config(self) -> Dict:
        """Default configuration settings"""
        return {
            'input_dir': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi",
            'output_dir': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\05_Exports",
            'backup_dir': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\backups",
            'log_dir': r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\logs",
            'enable_backup': True,
            'enable_rollback': True,
            'quality_checks': True,
            'performance_monitoring': True
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup production logging"""
        log_dir = Path(self.config['log_dir'])
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"scrpa_production_{timestamp}.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger('SCRPA_Production')
        logger.info("Production pipeline initialized")
        return logger
    
    def validate_input_files(self, cad_path: str, rms_path: str) -> bool:
        """Validate input files exist and are accessible"""
        try:
            if not Path(cad_path).exists():
                self.logger.error(f"CAD file not found: {cad_path}")
                return False
            
            if not Path(rms_path).exists():
                self.logger.error(f"RMS file not found: {rms_path}")
                return False
            
            # Test file accessibility
            pd.read_csv(cad_path, nrows=1)
            pd.read_csv(rms_path, nrows=1)
            
            self.logger.info("Input file validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Input file validation failed: {str(e)}")
            return False
    
    def validate_data_quality(self, cad_df: pd.DataFrame, rms_df: pd.DataFrame) -> Dict:
        """Comprehensive data quality validation"""
        quality_report = {
            'timestamp': datetime.now().isoformat(),
            'cad_validation': {},
            'rms_validation': {},
            'overall_status': 'PASS'
        }
        
        try:
            # CAD validation
            cad_validation = {
                'record_count': len(cad_df),
                'required_columns': self._validate_required_columns(cad_df, 'CAD'),
                'data_completeness': self._check_data_completeness(cad_df),
                'header_compliance': self._validate_header_compliance(cad_df)
            }
            
            # RMS validation
            rms_validation = {
                'record_count': len(rms_df),
                'required_columns': self._validate_required_columns(rms_df, 'RMS'),
                'data_completeness': self._check_data_completeness(rms_df),
                'header_compliance': self._validate_header_compliance(rms_df)
            }
            
            quality_report['cad_validation'] = cad_validation
            quality_report['rms_validation'] = rms_validation
            
            # Overall status check
            if not cad_validation['required_columns']['status'] or not rms_validation['required_columns']['status']:
                quality_report['overall_status'] = 'FAIL'
            
            if not cad_validation['header_compliance']['status'] or not rms_validation['header_compliance']['status']:
                quality_report['overall_status'] = 'FAIL'
            
            self.logger.info(f"Data quality validation: {quality_report['overall_status']}")
            return quality_report
            
        except Exception as e:
            self.logger.error(f"Data quality validation error: {str(e)}")
            quality_report['overall_status'] = 'ERROR'
            quality_report['error'] = str(e)
            return quality_report
    
    def _validate_required_columns(self, df: pd.DataFrame, dataset_type: str) -> Dict:
        """Validate required columns exist"""
        required_columns = {
            'CAD': ['case_number', 'incident', 'response_type', 'category_type'],
            'RMS': ['case_number', 'incident_type', 'nibrs_classification']
        }
        
        required = required_columns.get(dataset_type, [])
        missing = [col for col in required if col not in df.columns]
        
        return {
            'status': len(missing) == 0,
            'required_columns': required,
            'missing_columns': missing,
            'total_columns': len(df.columns)
        }
    
    def _check_data_completeness(self, df: pd.DataFrame) -> Dict:
        """Check data completeness metrics"""
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        completeness_rate = ((total_cells - missing_cells) / total_cells) * 100
        
        return {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'completeness_rate': round(completeness_rate, 2),
            'missing_values': int(missing_cells),
            'status': completeness_rate > 80.0  # 80% completeness threshold
        }
    
    def _validate_header_compliance(self, df: pd.DataFrame) -> Dict:
        """Validate snake_case header compliance"""
        snake_case_pattern = r'^[a-z]+(?:_[a-z0-9]+)*$'
        
        headers = df.columns.tolist()
        compliant_headers = [col for col in headers if re.match(snake_case_pattern, col)]
        non_compliant = [col for col in headers if not re.match(snake_case_pattern, col)]
        
        compliance_rate = (len(compliant_headers) / len(headers)) * 100
        
        return {
            'status': len(non_compliant) == 0,
            'compliance_rate': round(compliance_rate, 2),
            'total_headers': len(headers),
            'compliant_headers': len(compliant_headers),
            'non_compliant_headers': non_compliant
        }
    
    def match_crime_pattern(self, text: str, crime_type: str) -> bool:
        """Match text against crime patterns"""
        if pd.isna(text):
            return False
            
        text = str(text).lower().strip()
        patterns = self.crime_patterns.get(crime_type, [])
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def apply_hybrid_filtering(self, cad_df: pd.DataFrame, rms_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """Apply production hybrid filtering with validation"""
        start_time = time.time()
        
        try:
            # CAD filtering
            filtered_cases = {}
            all_filtered_cases = set()
            
            for crime in self.target_crimes:
                # Primary: incident column
                incident_matches = cad_df['incident'].apply(
                    lambda x: self.match_crime_pattern(x, crime)
                )
                
                # Secondary: response_type and category_type  
                response_type_matches = cad_df['response_type'].apply(
                    lambda x: self.match_crime_pattern(x, crime)
                )
                category_type_matches = cad_df['category_type'].apply(
                    lambda x: self.match_crime_pattern(x, crime)
                )
                
                # Combined logic
                combined_matches = incident_matches | response_type_matches | category_type_matches
                
                # Get case numbers
                crime_cases = cad_df[combined_matches]['case_number'].tolist()
                filtered_cases[crime] = crime_cases
                all_filtered_cases.update(crime_cases)
            
            # Create filtered CAD dataframe
            cad_filtered = cad_df[cad_df['case_number'].isin(all_filtered_cases)].copy()
            
            # RMS matching with validation
            rms_matched = rms_df[rms_df['case_number'].isin(all_filtered_cases)].copy()
            
            # Validation metrics
            validation_metrics = self._calculate_validation_metrics(filtered_cases, rms_df)
            
            processing_time = time.time() - start_time
            
            # Quality checks
            overall_validation_rate = np.mean(list(validation_metrics['validation_rates'].values()))
            
            if overall_validation_rate < self.min_validation_rate:
                self.logger.warning(f"Validation rate {overall_validation_rate:.1f}% below threshold {self.min_validation_rate}%")
            
            # Processing stats
            filtering_stats = {
                'processing_time': round(processing_time, 2),
                'cad_original_records': len(cad_df),
                'cad_filtered_records': len(cad_filtered),
                'cad_retention_rate': (len(cad_filtered) / len(cad_df)) * 100,
                'rms_original_records': len(rms_df),
                'rms_matched_records': len(rms_matched),
                'rms_retention_rate': (len(rms_matched) / len(rms_df)) * 100,
                'overall_validation_rate': round(overall_validation_rate, 2),
                'quality_status': 'PASS' if overall_validation_rate >= self.min_validation_rate else 'WARNING'
            }
            
            filtering_stats.update(validation_metrics)
            
            self.logger.info(f"Hybrid filtering completed: {filtering_stats['quality_status']}")
            return cad_filtered, rms_matched, filtering_stats
            
        except Exception as e:
            self.logger.error(f"Hybrid filtering error: {str(e)}")
            raise
    
    def _calculate_validation_metrics(self, cad_cases: Dict, rms_df: pd.DataFrame) -> Dict:
        """Calculate detailed validation metrics"""
        validation_rates = {}
        detailed_metrics = {}
        
        for crime in self.target_crimes:
            cad_crime_cases = set(cad_cases[crime])
            
            # Find RMS cases with matching NIBRS codes
            nibrs_matches = rms_df['nibrs_classification'].apply(
                lambda x: self.match_crime_pattern(x, crime)
            )
            rms_crime_cases = set(rms_df[nibrs_matches]['case_number'].tolist())
            
            # Calculate validation
            validated_cases = cad_crime_cases.intersection(rms_crime_cases)
            validation_rate = (len(validated_cases) / len(cad_crime_cases) * 100) if cad_crime_cases else 0
            
            validation_rates[crime] = round(validation_rate, 2)
            detailed_metrics[crime] = {
                'cad_cases': len(cad_crime_cases),
                'rms_cases': len(rms_crime_cases),
                'validated_cases': len(validated_cases),
                'validation_rate': round(validation_rate, 2)
            }
        
        return {
            'validation_rates': validation_rates,
            'detailed_metrics': detailed_metrics
        }
    
    def create_powerbi_exports(self, cad_filtered: pd.DataFrame, rms_matched: pd.DataFrame, 
                             export_stats: Dict) -> Dict:
        """Create PowerBI-ready export files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(exist_ok=True)
        
        # Export paths
        cad_export_path = output_dir / f"SCRPA_CAD_Filtered_{timestamp}.csv"
        rms_export_path = output_dir / f"SCRPA_RMS_Matched_{timestamp}.csv"
        summary_path = output_dir / f"SCRPA_Processing_Summary_{timestamp}.json"
        
        try:
            # Export datasets
            cad_filtered.to_csv(cad_export_path, index=False)
            rms_matched.to_csv(rms_export_path, index=False)
            
            # Create processing summary
            processing_summary = {
                'export_timestamp': datetime.now().isoformat(),
                'processing_stats': export_stats,
                'file_info': {
                    'cad_filtered': {
                        'filename': cad_export_path.name,
                        'path': str(cad_export_path),
                        'records': len(cad_filtered),
                        'columns': cad_filtered.columns.tolist()
                    },
                    'rms_matched': {
                        'filename': rms_export_path.name,
                        'path': str(rms_export_path),
                        'records': len(rms_matched),
                        'columns': rms_matched.columns.tolist()
                    }
                },
                'crime_distribution': self._calculate_crime_distribution(cad_filtered),
                'powerbi_integration': {
                    'ready': True,
                    'refresh_timestamp': datetime.now().isoformat(),
                    'data_freshness': 'Current'
                }
            }
            
            # Save summary
            with open(summary_path, 'w') as f:
                json.dump(processing_summary, f, indent=2, default=str)
            
            export_info = {
                'cad_export': str(cad_export_path),
                'rms_export': str(rms_export_path),
                'summary_export': str(summary_path),
                'processing_summary': processing_summary
            }
            
            self.logger.info("PowerBI exports created successfully")
            return export_info
            
        except Exception as e:
            self.logger.error(f"Export creation error: {str(e)}")
            raise
    
    def _calculate_crime_distribution(self, cad_df: pd.DataFrame) -> Dict:
        """Calculate crime type distribution for reporting"""
        distribution = {}
        total_records = len(cad_df)
        
        for crime in self.target_crimes:
            crime_count = sum(1 for incident in cad_df['incident'] 
                            if self.match_crime_pattern(incident, crime))
            
            distribution[crime] = {
                'count': crime_count,
                'percentage': round((crime_count / total_records) * 100, 2) if total_records > 0 else 0
            }
        
        return distribution
    
    def create_backup(self, source_files: List[str]) -> str:
        """Create backup of source files"""
        if not self.config['enable_backup']:
            return "Backup disabled"
        
        backup_dir = Path(self.config['backup_dir'])
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = backup_dir / f"backup_{timestamp}"
        backup_subdir.mkdir()
        
        try:
            for file_path in source_files:
                if Path(file_path).exists():
                    shutil.copy2(file_path, backup_subdir)
            
            self.logger.info(f"Backup created: {backup_subdir}")
            return str(backup_subdir)
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            return f"Backup failed: {str(e)}"
    
    def generate_pipeline_dashboard(self, processing_stats: Dict, quality_report: Dict, 
                                  export_info: Dict) -> Dict:
        """Generate pipeline status dashboard"""
        pipeline_end_time = time.time()
        total_processing_time = pipeline_end_time - self.pipeline_start_time
        
        dashboard = {
            'pipeline_summary': {
                'status': 'SUCCESS',
                'start_time': datetime.fromtimestamp(self.pipeline_start_time).isoformat(),
                'end_time': datetime.fromtimestamp(pipeline_end_time).isoformat(),
                'total_processing_time': round(total_processing_time, 2),
                'performance_status': 'GOOD' if total_processing_time < self.max_processing_time else 'SLOW'
            },
            'quality_metrics': {
                'data_quality_status': quality_report['overall_status'],
                'validation_rate': processing_stats.get('overall_validation_rate', 0),
                'quality_threshold_met': processing_stats.get('overall_validation_rate', 0) >= self.min_validation_rate
            },
            'processing_metrics': {
                'cad_retention_rate': processing_stats.get('cad_retention_rate', 0),
                'rms_retention_rate': processing_stats.get('rms_retention_rate', 0),
                'total_target_crimes': len(self.target_crimes),
                'crimes_processed': len(processing_stats.get('validation_rates', {}))
            },
            'export_status': {
                'powerbi_ready': export_info.get('processing_summary', {}).get('powerbi_integration', {}).get('ready', False),
                'files_created': len([k for k in export_info.keys() if k.endswith('_export')]),
                'export_location': self.config['output_dir']
            }
        }
        
        self.logger.info(f"Pipeline completed: {dashboard['pipeline_summary']['status']}")
        return dashboard
    
    def run_production_pipeline(self, cad_file_pattern: str = "C08W31_*_cad_data_standardized.csv",
                               rms_file_pattern: str = "C08W31_*_rms_data_standardized.csv") -> Dict:
        """Run complete production pipeline"""
        self.pipeline_start_time = time.time()
        self.logger.info("Starting SCRPA production pipeline")
        
        try:
            # 1. Find input files
            input_dir = Path(self.config['input_dir'])
            cad_files = list(input_dir.glob(cad_file_pattern))
            rms_files = list(input_dir.glob(rms_file_pattern))
            
            if not cad_files or not rms_files:
                raise FileNotFoundError(f"Input files not found: CAD={len(cad_files)}, RMS={len(rms_files)}")
            
            # Use most recent files
            cad_path = max(cad_files, key=lambda p: p.stat().st_mtime)
            rms_path = max(rms_files, key=lambda p: p.stat().st_mtime)
            
            self.logger.info(f"Using CAD file: {cad_path}")
            self.logger.info(f"Using RMS file: {rms_path}")
            
            # 2. Validate input files
            if not self.validate_input_files(str(cad_path), str(rms_path)):
                raise ValueError("Input file validation failed")
            
            # 3. Create backup
            backup_location = self.create_backup([str(cad_path), str(rms_path)])
            
            # 4. Load data
            self.logger.info("Loading data files")
            cad_df = pd.read_csv(cad_path)
            rms_df = pd.read_csv(rms_path)
            
            # 5. Data quality validation
            quality_report = self.validate_data_quality(cad_df, rms_df)
            if quality_report['overall_status'] == 'FAIL':
                raise ValueError(f"Data quality validation failed: {quality_report}")
            
            # 6. Apply hybrid filtering
            self.logger.info("Applying hybrid filtering")
            cad_filtered, rms_matched, processing_stats = self.apply_hybrid_filtering(cad_df, rms_df)
            
            # 7. Create PowerBI exports
            self.logger.info("Creating PowerBI exports")
            export_info = self.create_powerbi_exports(cad_filtered, rms_matched, processing_stats)
            
            # 8. Generate dashboard
            dashboard = self.generate_pipeline_dashboard(processing_stats, quality_report, export_info)
            
            # 9. Save pipeline results
            pipeline_results = {
                'dashboard': dashboard,
                'quality_report': quality_report,
                'processing_stats': processing_stats,
                'export_info': export_info,
                'backup_location': backup_location
            }
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"SCRPA_Pipeline_Results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(pipeline_results, f, indent=2, default=str)
            
            self.logger.info(f"Pipeline completed successfully: {results_file}")
            return pipeline_results
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            error_result = {
                'status': 'FAILED',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'pipeline_duration': time.time() - self.pipeline_start_time if self.pipeline_start_time else 0
            }
            
            return error_result

def main():
    """Main execution function"""
    print("=== SCRPA Production Deployment Pipeline ===")
    
    # Initialize pipeline
    pipeline = SCRPAProductionPipeline()
    
    # Run production pipeline
    results = pipeline.run_production_pipeline()
    
    # Display results
    if results.get('status') == 'FAILED':
        print(f"Pipeline FAILED: {results.get('error', 'Unknown error')}")
        return False
    
    # Success summary
    dashboard = results.get('dashboard', {})
    pipeline_summary = dashboard.get('pipeline_summary', {})
    quality_metrics = dashboard.get('quality_metrics', {})
    
    print(f"\nPipeline Status: {pipeline_summary.get('status', 'UNKNOWN')}")
    print(f"Processing Time: {pipeline_summary.get('total_processing_time', 0):.2f} seconds")
    print(f"Data Quality: {quality_metrics.get('data_quality_status', 'UNKNOWN')}")
    print(f"Validation Rate: {quality_metrics.get('validation_rate', 0):.1f}%")
    print(f"PowerBI Ready: {dashboard.get('export_status', {}).get('powerbi_ready', False)}")
    
    export_info = results.get('export_info', {})
    if 'cad_export' in export_info:
        print(f"\nExported Files:")
        print(f"  CAD Filtered: {export_info['cad_export']}")
        print(f"  RMS Matched: {export_info['rms_export']}")
        print(f"  Summary: {export_info['summary_export']}")
    
    print("\n=== Production Pipeline Complete ===")
    return True

if __name__ == "__main__":
    success = main()