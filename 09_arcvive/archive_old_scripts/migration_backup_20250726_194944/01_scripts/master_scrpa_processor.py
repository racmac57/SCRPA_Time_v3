# 🕒 2025-07-23-17-30-00
# SCRPA_Time_v2/Master_SCRPA_Processor
# Author: R. A. Carucci  
# Purpose: Complete integration script that replaces complex M Code with clean Python processing

import pandas as pd
import numpy as np
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import warnings
warnings.filterwarnings('ignore')

# Import your existing validation and processing modules
try:
    from actual_structure_python_validation import SCRPAActualDataValidator, DataSource
    from enhanced_cadnotes_processor import EnhancedCADNotesProcessor
    from unified_data_processor import UnifiedDataProcessor
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Make sure all your existing scripts are in the same directory")

class MasterSCRPAProcessor:
    """
    Master processor that integrates all your existing scripts into a complete
    pipeline that replaces your complex Power BI M Code.
    """
    
    def __init__(self, project_path: str = None):
        """Initialize master processor with your actual export directory structure."""
        
        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)
        
        # Your actual export directories
        self.export_dirs = {
            'cad_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA"),
            'rms_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA")
        }
        
        # Setup directory structure
        self.setup_directories()
        
        # Initialize logging
        self.setup_logging()
        
        # Initialize component processors
        self.data_validator = SCRPAActualDataValidator(str(self.project_path))
        self.cadnotes_processor = EnhancedCADNotesProcessor()
        
        # Processing statistics
        self.stats = {
            'processing_start_time': None,
            'data_source_detected': None,
            'total_input_records': 0,
            'total_output_records': 0,
            'cadnotes_processed': 0,
            'quality_score_avg': 0.0,
            'processing_duration': 0.0,
            'errors_encountered': []
        }
        
        self.logger.info("🚀 Master SCRPA Processor initialized")
    
    def setup_directories(self):
        """Setup your actual project directory structure."""
        
        self.dirs = {
            'scripts': self.project_path / '01_scripts',
            'cad_exports': self.export_dirs['cad_exports'],
            'rms_exports': self.export_dirs['rms_exports'],
            'output': self.project_path / '03_output', 
            'powerbi': self.project_path / '04_powerbi',
            'logs': self.project_path / '03_output' / 'logs',
            'reports': self.project_path / '03_output' / 'reports'
        }
        
        # Create output directories if they don't exist (don't create export dirs - they're managed by your system)
        for dir_name, dir_path in self.dirs.items():
            if dir_name not in ['cad_exports', 'rms_exports']:
                dir_path.mkdir(parents=True, exist_ok=True)
        
        # Verify export directories exist
        if not self.dirs['cad_exports'].exists():
            self.logger.warning(f"CAD export directory not found: {self.dirs['cad_exports']}")
        if not self.dirs['rms_exports'].exists():
            self.logger.warning(f"RMS export directory not found: {self.dirs['rms_exports']}")
    
    def find_latest_export_file(self, export_type: str = "auto") -> Tuple[str, DataSource]:
        """Find the latest CAD or RMS export file from your actual export directories."""
        
        self.logger.info(f"🔍 Searching for latest {export_type} export files")
        
        latest_file = None
        detected_source = DataSource.UNKNOWN
        
        if export_type.lower() in ["auto", "cad"]:
            # Search CAD exports
            cad_files = list(self.dirs['cad_exports'].glob("*.xlsx"))
            if cad_files:
                latest_cad = max(cad_files, key=lambda x: x.stat().st_mtime)
                self.logger.info(f"   📁 Latest CAD file: {latest_cad.name}")
                if export_type == "auto" or export_type.lower() == "cad":
                    latest_file = str(latest_cad)
                    detected_source = DataSource.CAD
        
        if export_type.lower() in ["auto", "rms"] and not latest_file:
            # Search RMS exports
            rms_files = list(self.dirs['rms_exports'].glob("*.xlsx"))
            if rms_files:
                latest_rms = max(rms_files, key=lambda x: x.stat().st_mtime)
                self.logger.info(f"   📁 Latest RMS file: {latest_rms.name}")
                if export_type == "auto" or export_type.lower() == "rms":
                    latest_file = str(latest_rms)
                    detected_source = DataSource.RMS
        
        if export_type == "auto" and latest_file is None:
            # Compare both directories and pick the most recent
            all_files = []
            
            cad_files = list(self.dirs['cad_exports'].glob("*.xlsx"))
            rms_files = list(self.dirs['rms_exports'].glob("*.xlsx"))
            
            for f in cad_files:
                all_files.append((f, DataSource.CAD))
            for f in rms_files:
                all_files.append((f, DataSource.RMS))
            
            if all_files:
                latest_file_info = max(all_files, key=lambda x: x[0].stat().st_mtime)
                latest_file = str(latest_file_info[0])
                detected_source = latest_file_info[1]
                self.logger.info(f"   🎯 Most recent file: {latest_file_info[0].name} ({detected_source.value})")
        
        if latest_file is None:
            raise FileNotFoundError(f"No export files found in {self.dirs['cad_exports']} or {self.dirs['rms_exports']}")
        
        return latest_file, detected_source
    
    def setup_logging(self):
        """Setup comprehensive logging system."""
        
        log_file = self.dirs['logs'] / f"master_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('MasterProcessor')
        self.logger.info(f"Logging initialized: {log_file}")
    
    def process_complete_pipeline(self, input_file: str = None, 
                                output_file: str = None, export_type: str = "auto") -> Tuple[pd.DataFrame, Dict]:
        """
        Run the complete SCRPA processing pipeline.
        This replaces all your complex M Code with clean, fast Python processing.
        """
        
        self.logger.info("=" * 80)
        self.logger.info("🚀 STARTING COMPLETE SCRPA PROCESSING PIPELINE")
        self.logger.info("=" * 80)
        
        self.stats['processing_start_time'] = datetime.now()
        
        try:
            # Step 1: Auto-detect and load data from your export directories
            df, data_source, structure_info = self.auto_detect_and_load_data(input_file, export_type)
            
            # Step 2: Process based on detected structure
            processed_df = self.process_by_data_source(df, data_source)
            
            # Step 3: Enhanced CADNotes processing
            enhanced_df = self.process_cadnotes_enhanced(processed_df)
            
            # Step 4: Add all derived columns (replaces M Code logic)
            final_df = self.add_all_enhancements(enhanced_df)
            
            # Step 5: Data quality validation and cleanup
            validated_df = self.validate_and_cleanup(final_df)
            
            # Step 6: Export for Power BI
            output_path = self.export_for_powerbi(validated_df, output_file)
            
            # Step 7: Generate processing report
            report_path = self.generate_processing_report(validated_df, structure_info)
            
            # Calculate final statistics
            self.calculate_final_stats(validated_df)
            
            self.logger.info("=" * 80)
            self.logger.info("✅ COMPLETE SCRPA PROCESSING PIPELINE FINISHED")
            self.logger.info(f"📊 Processed: {self.stats['total_input_records']} → {self.stats['total_output_records']} records")
            self.logger.info(f"⏱️ Duration: {self.stats['processing_duration']:.1f} seconds")
            self.logger.info(f"📄 Output: {output_path}")
            self.logger.info(f"📋 Report: {report_path}")
            self.logger.info("=" * 80)
            
            return validated_df, self.stats
            
        except Exception as e:
            self.logger.error(f"❌ PIPELINE FAILED: {str(e)}")
            self.stats['errors_encountered'].append(str(e))
            raise


# Helper functions for data processing
def categorize_crime_type(incident_type: str) -> str:
    """Categorize crime types using your exact patterns."""
    if pd.isna(incident_type):
        return 'Other'
    
    incident_upper = str(incident_type).upper()
    
    if any(term in incident_upper for term in ['MOTOR VEHICLE THEFT', 'AUTO THEFT', 'MV THEFT']):
        return 'Motor Vehicle Theft'
    elif 'BURGLARY' in incident_upper and ('AUTO' in incident_upper or 'VEHICLE' in incident_upper):
        return 'Burglary - Auto'
    elif 'BURGLARY' in incident_upper and 'COMMERCIAL' in incident_upper:
        return 'Burglary - Commercial'
    elif 'BURGLARY' in incident_upper and 'RESIDENCE' in incident_upper:
        return 'Burglary - Residence'
    elif 'ROBBERY' in incident_upper:
        return 'Robbery'
    elif 'SEXUAL' in incident_upper:
        return 'Sexual Offenses'
    else:
        return 'Other'

def categorize_time_of_day(row) -> str:
    """Categorize time into day periods."""
    try:
        if 'Incident_Time' in row and pd.notna(row['Incident_Time']):
            time_val = row['Incident_Time']
            if isinstance(time_val, str):
                hour = int(time_val.split(':')[0])
            else:
                hour = time_val.hour
        else:
            return "Unknown"
        
        if 4 <= hour < 8:
            return "04:00–07:59 Morning"
        elif 8 <= hour < 12:
            return "08:00–11:59 Morning Peak" 
        elif 12 <= hour < 16:
            return "12:00–15:59 Afternoon"
        elif 16 <= hour < 20:
            return "16:00–19:59 Evening Peak"
        else:
            return "20:00–03:59 Night"
    except:
        return "Unknown"

def calculate_enhanced_block(address: str) -> str:
    """Calculate enhanced block from address."""
    if pd.isna(address) or not address:
        return "Incomplete Address - Check Location Data"
    
    try:
        address = str(address).strip()
        # Remove Hackensack suffix
        clean_addr = address.replace(", Hackensack, NJ, 07601", "").replace(", Hackensack, NJ", "")
        
        # Handle intersections
        if ' & ' in clean_addr:
            return clean_addr.strip()
        
        # Extract block number
        parts = clean_addr.split()
        if parts and parts[0].replace('-', '').isdigit():
            street_num = int(parts[0].replace('-', ''))
            street_name = ' '.join(parts[1:]).split(',')[0]
            block_num = (street_num // 100) * 100
            return f"{street_name}, {block_num} Block"
        else:
            street_name = clean_addr.split(',')[0]
            return f"{street_name}, Unknown Block"
    except:
        return "Incomplete Address - Check Location Data"

def format_response_time(minutes) -> str:
    """Format response time in minutes to readable format."""
    if pd.isna(minutes):
        return None
    
    try:
        total_seconds = int(float(minutes) * 60)
        mins = total_seconds // 60
        secs = total_seconds % 60
        
        if mins == 0:
            return f"{secs} Secs"
        elif secs == 0:
            return f"{mins} Mins"
        else:
            return f"{mins} Mins {secs:02d} Secs"
    except:
        return "Invalid Time"

def format_time_spent(minutes) -> str:
    """Format time spent in minutes to readable format."""
    if pd.isna(minutes):
        return None
    
    try:
        total_minutes = int(float(minutes))
        hours = total_minutes // 60
        remaining_mins = total_minutes % 60
        
        if hours == 0:
            return f"{remaining_mins} Mins"
        elif remaining_mins == 0:
            return f"{hours} Hrs"
        else:
            return f"{hours} Hrs {remaining_mins:02d} Mins"
    except:
        return "Invalid Time"


def main():
    """Main execution function with command line interface."""
    
    parser = argparse.ArgumentParser(description="Master SCRPA Processor - Complete M Code Replacement")
    
    parser.add_argument('--input-file', '-i', type=str, 
                       help='Specific input file to process (optional)')
    parser.add_argument('--output-file', '-o', type=str,
                       help='Output file path (optional)')
    parser.add_argument('--export-type', '-t', choices=['auto', 'cad', 'rms'], default='auto',
                       help='Type of export to process (auto, cad, or rms)')
    parser.add_argument('--mode', '-m', choices=['process', 'validate', 'test'], default='process',
                       help='Processing mode')
    parser.add_argument('--project-path', '-p', type=str,
                       help='Project path (uses default if not specified)')
    
    args = parser.parse_args()
    
    try:
        # Initialize processor
        processor = MasterSCRPAProcessor(args.project_path)
        
        if args.mode == 'test':
            # Test mode - validate processor components
            print("🧪 Running test mode...")
            
            # Test CADNotes processor
            cadnotes_test_passed = processor.cadnotes_processor.validate_against_examples()
            
            # Test file detection
            try:
                latest_file, detected_source = processor.find_latest_export_file(args.export_type)
                print(f"✅ Latest file detection: {Path(latest_file).name} ({detected_source.value})")
                file_detection_passed = True
            except Exception as e:
                print(f"❌ File detection failed: {e}")
                file_detection_passed = False
            
            if cadnotes_test_passed and file_detection_passed:
                print("🎉 All tests passed! Ready for processing.")
            else:
                print("⚠️ Some tests failed. Check configuration.")
                
        elif args.mode == 'validate':
            # Validation mode - run data validation only
            print("🔍 Running validation mode...")
            
            latest_file, detected_source = processor.find_latest_export_file(args.export_type)
            df = pd.read_excel(latest_file, engine='openpyxl')
            
            results_df, quality_report = processor.data_validator.run_validation()
            
            print("\n📊 Validation Results:")
            print(results_df.to_string(index=False))
            
        else:
            # Full processing mode
            print("🚀 Running full processing mode...")
            
            # Run complete pipeline
            final_df, stats = processor.process_complete_pipeline(
                input_file=args.input_file,
                output_file=args.output_file,
                export_type=args.export_type
            )
            
            print(f"\n✅ Processing complete!")
            print(f"📊 Final statistics:")
            for key, value in stats.items():
                if not key.endswith('_time') and key != 'errors_encountered':
                    print(f"   {key.replace('_', ' ').title()}: {value}")
    
    except Exception as e:
        print(f"\n❌ Processing failed: {str(e)}")
        print(f"Check the log files in: C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\03_output\\logs")
        sys.exit(1)


if __name__ == "__main__":
    main()
    
    def auto_detect_and_load_data(self, input_file: str = None, export_type: str = "auto") -> Tuple[pd.DataFrame, DataSource, Dict]:
        """Auto-detect data source and load using your actual export directories."""
        
        self.logger.info("🔍 Step 1: Auto-detecting data source and loading data")
        
        try:
            if input_file:
                # Load specific file
                self.logger.info(f"   📂 Loading specified file: {Path(input_file).name}")
                df = pd.read_excel(input_file, engine='openpyxl')
                data_source, structure_info = self.data_validator.detect_data_source(df)
            else:
                # Find latest export file from your actual directories
                latest_file, detected_source = self.find_latest_export_file(export_type)
                self.logger.info(f"   📂 Loading latest export: {Path(latest_file).name}")
                
                df = pd.read_excel(latest_file, engine='openpyxl')
                data_source, structure_info = self.data_validator.detect_data_source(df)
                
                # Verify detection matches file location
                if detected_source != data_source:
                    self.logger.warning(f"   ⚠️ File location suggests {detected_source.value} but structure detected as {data_source.value}")
            
            self.stats['data_source_detected'] = data_source.value
            self.stats['total_input_records'] = len(df)
            
            self.logger.info(f"✅ Detected {data_source.value} structure with {len(df)} records")
            return df, data_source, structure_info
            
        except Exception as e:
            self.logger.error(f"Failed to auto-detect and load data: {e}")
            raise
    
    def process_by_data_source(self, df: pd.DataFrame, data_source: DataSource) -> pd.DataFrame:
        """Process data based on detected source structure."""
        
        self.logger.info(f"🔧 Step 2: Processing {data_source.value} data structure")
        
        if data_source == DataSource.CAD:
            return self.process_cad_structure(df)
        elif data_source == DataSource.RMS:
            return self.process_rms_structure(df)
        else:
            raise ValueError(f"Unknown data source: {data_source}")
    
    def process_cad_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process CAD data structure (single Incident column)."""
        
        self.logger.info("   📋 Processing CAD structure (no unpivoting needed)")
        
        # Use your existing CAD preparation logic
        prepared_df = self.data_validator.prepare_cad_data(df)
        
        # Standardize column names for downstream processing
        if 'ReportNumberNew' in prepared_df.columns:
            prepared_df['Case_Number'] = prepared_df['ReportNumberNew']
        
        if 'Incident' in prepared_df.columns:
            prepared_df['IncidentType'] = prepared_df['Incident']
        
        # Add crime categorization
        prepared_df['Crime_Category'] = prepared_df['IncidentType'].apply(self.categorize_crime_type)
        
        self.logger.info(f"   ✅ CAD processing complete: {len(prepared_df)} records")
        return prepared_df
    
    def process_rms_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process RMS data structure (multiple Incident Type columns)."""
        
        self.logger.info("   📋 Processing RMS structure (unpivoting required)")
        
        # Use your existing RMS preparation logic
        prepared_df = self.data_validator.prepare_rms_data(df)
        
        # Standardize column names
        if 'Case Number' in prepared_df.columns:
            prepared_df['Case_Number'] = prepared_df['Case Number']
        
        if 'incident_text' in prepared_df.columns:
            prepared_df['IncidentType'] = prepared_df['incident_text']
        
        # Add crime categorization
        prepared_df['Crime_Category'] = prepared_df['IncidentType'].apply(self.categorize_crime_type)
        
        self.logger.info(f"   ✅ RMS processing complete: {len(prepared_df)} records")
        return prepared_df
    
    def process_cadnotes_enhanced(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process CADNotes using enhanced processor."""
        
        self.logger.info("🤖 Step 3: Enhanced CADNotes processing")
        
        if 'CADNotes' in df.columns:
            enhanced_df = self.cadnotes_processor.process_cadnotes_dataframe(df, 'CADNotes')
            self.stats['cadnotes_processed'] = enhanced_df['CAD_Username'].notna().sum()
        else:
            self.logger.warning("   ⚠️ No CADNotes column found, skipping CADNotes processing")
            enhanced_df = df.copy()
            # Add empty CADNotes columns for consistency
            enhanced_df['CAD_Username'] = None
            enhanced_df['CAD_Timestamp'] = None
            enhanced_df['CAD_Notes_Cleaned'] = None
            enhanced_df['CADNotes_Processing_Quality'] = 0.0
        
        self.logger.info(f"   ✅ CADNotes processing complete: {self.stats['cadnotes_processed']} notes processed")
        return enhanced_df
    
    def add_all_enhancements(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all derived columns that replace your M Code logic."""
        
        self.logger.info("📊 Step 4: Adding derived columns (replaces M Code logic)")
        
        enhanced_df = df.copy()
        
        # Date/Time enhancements
        enhanced_df = self.add_datetime_enhancements(enhanced_df)
        
        # Address/Block enhancements  
        enhanced_df = self.add_address_enhancements(enhanced_df)
        
        # Period classification
        enhanced_df = self.add_period_classification(enhanced_df)
        
        # Time formatting (response time, time spent)
        enhanced_df = self.add_time_formatting(enhanced_df)
        
        # Geographic enhancements
        enhanced_df = self.add_geographic_enhancements(enhanced_df)
        
        self.logger.info("   ✅ All enhancements complete")
        return enhanced_df
    
    def add_datetime_enhancements(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add date/time derived columns."""
        
        # Ensure we have proper date/time columns
        if 'incident_date' in df.columns:
            df['Incident_Date'] = pd.to_datetime(df['incident_date'], errors='coerce').dt.date
        elif 'Incident_Date' not in df.columns:
            # Try to extract from available datetime columns
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    try:
                        df['Incident_Date'] = pd.to_datetime(df[col], errors='coerce').dt.date
                        break
                    except:
                        continue
        
        if 'incident_time' in df.columns:
            df['Incident_Time'] = pd.to_datetime(df['incident_time'], errors='coerce').dt.time
        elif 'Incident_Time' not in df.columns:
            df['Incident_Time'] = None
        
        # Add time of day categorization
        df['TimeOfDay'] = df.apply(self.categorize_time_of_day, axis=1)
        
        # Add day/month/year components
        if 'Incident_Date' in df.columns:
            incident_dates = pd.to_datetime(df['Incident_Date'], errors='coerce')
            df['Day_Name'] = incident_dates.dt.day_name()
            df['Month_Name'] = incident_dates.dt.month_name()
            df['Year'] = incident_dates.dt.year
            df['Month'] = incident_dates.dt.month
            df['Day'] = incident_dates.dt.day
        
        return df
    
    def add_address_enhancements(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add address and block enhancements."""
        
        # Find address column
        address_col = None
        for col in ['address', 'Address', 'FullAddress', 'FullAddress2', 'Enhanced_FullAddress']:
            if col in df.columns:
                address_col = col
                break
        
        if address_col:
            df['Enhanced_Block'] = df[address_col].apply(self.calculate_enhanced_block)
        else:
            df['Enhanced_Block'] = 'Unknown Block'
        
        return df
    
    def add_period_classification(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add period classification (7-Day, 28-Day, YTD, Historical)."""
        
        def classify_period(incident_date):
            if pd.isna(incident_date):
                return 'Historical'
            
            try:
                incident_dt = pd.to_datetime(incident_date)
                today = pd.Timestamp.now()
                days_diff = (today - incident_dt).days
                
                if days_diff <= 7:
                    return '7-Day'
                elif days_diff <= 28:
                    return '28-Day'
                elif incident_dt.year == today.year:
                    return 'YTD'
                else:
                    return 'Historical'
            except:
                return 'Historical'
        
        df['Period'] = df['Incident_Date'].apply(classify_period)
        return df
    
    def add_time_formatting(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add formatted time columns for response time and time spent."""
        
        # Format response time
        if 'Time_Response_Minutes' in df.columns:
            df['Time_Response_Formatted'] = df['Time_Response_Minutes'].apply(self.format_response_time)
        
        # Format time spent
        if 'Time_Spent_Minutes' in df.columns:
            df['Time_Spent_Formatted'] = df['Time_Spent_Minutes'].apply(self.format_time_spent)
        
        return df
    
    def add_geographic_enhancements(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add geographic enhancements (Grid, Zone, etc.)."""
        
        # Standardize Grid/Zone columns
        grid_cols = [col for col in df.columns if 'grid' in col.lower()]
        if grid_cols:
            df['Grid'] = df[grid_cols[0]]
        
        zone_cols = [col for col in df.columns if 'zone' in col.lower()]
        if zone_cols:
            df['Zone'] = df[zone_cols[0]]
        
        # Standardize Officer column
        officer_cols = [col for col in df.columns if 'officer' in col.lower()]
        if officer_cols:
            df['Officer'] = df[officer_cols[0]]
        
        return df
    
    def validate_and_cleanup(self, df: pd.DataFrame) -> pd.DataFrame:
        """Final data validation and cleanup."""
        
        self.logger.info("🔍 Step 5: Data validation and cleanup")
        
        # Remove records with missing critical fields
        original_count = len(df)
        
        # Keep records with valid case numbers and incident types
        df = df[
            df['Case_Number'].notna() & 
            (df['Case_Number'] != '') &
            df['IncidentType'].notna() &
            (df['IncidentType'] != '')
        ]
        
        # Calculate overall data quality score
        if 'CADNotes_Processing_Quality' in df.columns:
            self.stats['quality_score_avg'] = df['CADNotes_Processing_Quality'].mean()
        
        removed_count = original_count - len(df)
        if removed_count > 0:
            self.logger.warning(f"   ⚠️ Removed {removed_count} records with missing critical fields")
        
        self.logger.info(f"   ✅ Validation complete: {len(df)} clean records")
        return df
    
    def export_for_powerbi(self, df: pd.DataFrame, output_file: str = None) -> str:
        """Export clean data for Power BI consumption."""
        
        self.logger.info("📊 Step 6: Exporting for Power BI")
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.dirs['powerbi'] / f"enhanced_scrpa_data