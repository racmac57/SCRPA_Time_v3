# 🕒 2025-07-23-06-00-00
# SCRPA_Time_v2/actual_structure_validation.py
# Author: R. A. Carucci
# Purpose: Validation script for actual CAD (Incident column) vs RMS (Incident Type_X columns) structures based on real sample data

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
from enum import Enum
import re
import warnings
warnings.filterwarnings('ignore')

class DataSource(Enum):
    CAD = "CAD"
    RMS = "RMS"
    UNKNOWN = "UNKNOWN"

class SCRPAActualDataValidator:
    """
    Validates crime data based on actual CAD and RMS export structures
    CAD: ReportNumberNew, Incident, FullAddress2, Time of Call, Disposition
    RMS: Case Number, Incident Type_1, Incident Type_2, Incident Type_3
    """
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        
        # Crime patterns based on actual CAD sample data format
        self.crime_patterns = {
            'motor_vehicle_theft': [
                'MOTOR VEHICLE THEFT',
                'AUTO THEFT', 
                'MV THEFT',
                'VEHICLE THEFT'
            ],
            'burglary_auto': [
                'BURGLARY.*AUTO',
                'BURGLARY.*VEHICLE',
                'AUTO.*BURGLARY'
            ],
            'burglary_commercial': [
                'BURGLARY.*COMMERCIAL',
                'COMMERCIAL.*BURGLARY'
            ],
            'burglary_residence': [
                'BURGLARY.*RESIDENCE',
                'BURGLARY.*RESIDENTIAL',
                'RESIDENTIAL.*BURGLARY'
            ],
            'robbery': ['ROBBERY'],
            'sexual': ['SEXUAL']
        }
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'scrpa_validation_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        
    def detect_data_source(self, df: pd.DataFrame) -> tuple[DataSource, dict]:
        """Detect data source and return structure info"""
        
        structure_info = {
            'columns_found': list(df.columns),
            'total_records': len(df),
            'key_columns': {}
        }
        
        # Check for CAD structure (based on actual sample)
        cad_indicators = {
            'ReportNumberNew': 'ReportNumberNew' in df.columns,
            'Incident': 'Incident' in df.columns,
            'FullAddress2': 'FullAddress2' in df.columns,
            'Time of Call': 'Time of Call' in df.columns,
            'Disposition': 'Disposition' in df.columns
        }
        
        # Check for RMS structure
        rms_indicators = {
            'Case Number': 'Case Number' in df.columns,
            'Incident Type_1': 'Incident Type_1' in df.columns,
            'Incident Type_2': 'Incident Type_2' in df.columns,
            'Incident Type_3': 'Incident Type_3' in df.columns
        }
        
        structure_info['cad_indicators'] = cad_indicators
        structure_info['rms_indicators'] = rms_indicators
        
        # Determine data source
        cad_score = sum(cad_indicators.values())
        rms_score = sum(rms_indicators.values())
        
        if cad_score >= 3:  # At least 3 key CAD columns present
            logging.info(f"Detected CAD structure (score: {cad_score}/5)")
            structure_info['detected_source'] = 'CAD'
            structure_info['confidence'] = 'High' if cad_score >= 4 else 'Medium'
            return DataSource.CAD, structure_info
            
        elif rms_score >= 2:  # At least 2 RMS incident columns present
            logging.info(f"Detected RMS structure (score: {rms_score}/4)")
            structure_info['detected_source'] = 'RMS'
            structure_info['confidence'] = 'High' if rms_score >= 3 else 'Medium'
            return DataSource.RMS, structure_info
            
        else:
            logging.warning("Unable to clearly identify data source structure")
            structure_info['detected_source'] = 'UNKNOWN'
            structure_info['confidence'] = 'Low'
            return DataSource.UNKNOWN, structure_info
    
    def prepare_cad_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare CAD data using actual column structure"""
        
        # Validate required CAD columns
        required_cols = ['Incident', 'ReportNumberNew']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required CAD columns: {missing_cols}")
        
        # Create working copy
        df_clean = df.copy()
        
        # Standardize column names for processing
        df_clean['case_number'] = df_clean['ReportNumberNew']
        df_clean['incident_text'] = df_clean['Incident'].fillna('').astype(str)
        
        # Remove excluded cases
        excluded_cases = ['25-057654']
        df_clean = df_clean[~df_clean['case_number'].isin(excluded_cases)]
        
        # Apply disposition filtering if available
        if 'Disposition' in df_clean.columns:
            original_count = len(df_clean)
            df_clean = df_clean[
                df_clean['Disposition'].str.contains('See Report', case=False, na=False)
            ]
            logging.info(f"CAD disposition filtering: {original_count} → {len(df_clean)} records")
        
        # Add address and time fields if available
        if 'FullAddress2' in df_clean.columns:
            df_clean['address'] = df_clean['FullAddress2']
        if 'Time of Call' in df_clean.columns:
            df_clean['incident_datetime'] = df_clean['Time of Call']
        
        logging.info(f"CAD data prepared: {len(df_clean)} records ready for processing")
        return df_clean
    
    def prepare_rms_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare RMS data with unpivoting"""
        
        # Find available incident type columns
        incident_type_cols = [col for col in df.columns if col.startswith('Incident Type_')]
        if not incident_type_cols:
            raise ValueError("RMS data must have 'Incident Type_X' columns")
        
        logging.info(f"Found RMS incident columns: {incident_type_cols}")
        
        # Remove excluded cases
        if 'Case Number' in df.columns:
            excluded_cases = ['25-057654']
            df = df[~df['Case Number'].isin(excluded_cases)]
        
        # Unpivot incident type columns
        id_cols = [col for col in df.columns if col not in incident_type_cols]
        df_unpivoted = pd.melt(
            df,
            id_vars=id_cols,
            value_vars=incident_type_cols,
            var_name='incident_source_column',
            value_name='incident_text'
        )
        
        # Remove null/empty incident types
        df_unpivoted = df_unpivoted[
            df_unpivoted['incident_text'].notna() & 
            (df_unpivoted['incident_text'] != '')
        ]
        
        # Standardize column names
        if 'Case Number' in df_unpivoted.columns:
            df_unpivoted['case_number'] = df_unpivoted['Case Number']
        
        logging.info(f"RMS unpivoting: {len(df)} → {len(df_unpivoted)} records")
        
        # Apply disposition filtering if available
        if 'Disposition' in df_unpivoted.columns:
            original_count = len(df_unpivoted)
            df_unpivoted = df_unpivoted[
                df_unpivoted['Disposition'].str.contains('See Report', case=False, na=False)
            ]
            logging.info(f"RMS disposition filtering: {original_count} → {len(df_unpivoted)} records")
        
        return df_unpivoted
    
    def apply_crime_filters(self, df: pd.DataFrame, data_source: DataSource) -> dict:
        """Apply crime type filtering with enhanced pattern matching"""
        
        results = {}
        
        for crime_type, patterns in self.crime_patterns.items():
            
            # Create vectorized mask for all patterns
            masks = []
            for pattern in patterns:
                if '.*' in pattern:
                    # Regex pattern
                    mask = df['incident_text'].str.upper().str.contains(
                        pattern.upper(), na=False, regex=True
                    )
                else:
                    # Simple text contains
                    mask = df['incident_text'].str.upper().str.contains(
                        pattern.upper(), na=False, regex=False
                    )
                masks.append(mask)
            
            # Combine all pattern masks with OR
            combined_mask = pd.Series([False] * len(df), index=df.index)
            for mask in masks:
                combined_mask = combined_mask | mask
            
            # Apply special logic for burglary subtypes
            if crime_type == 'burglary_auto':
                # Must contain BURGLARY and (AUTO or VEHICLE), but not COMMERCIAL or RESIDENCE
                burglary_mask = df['incident_text'].str.upper().str.contains('BURGLARY', na=False)
                auto_mask = (
                    df['incident_text'].str.upper().str.contains('AUTO', na=False) |
                    df['incident_text'].str.upper().str.contains('VEHICLE', na=False)
                )
                exclude_mask = (
                    df['incident_text'].str.upper().str.contains('COMMERCIAL', na=False) |
                    df['incident_text'].str.upper().str.contains('RESIDENCE', na=False)
                )
                combined_mask = burglary_mask & auto_mask & ~exclude_mask
                
            elif crime_type in ['burglary_commercial', 'burglary_residence']:
                # Exclude auto burglaries
                auto_exclude = (
                    df['incident_text'].str.upper().str.contains('AUTO', na=False) |
                    df['incident_text'].str.upper().str.contains('VEHICLE', na=False)
                )
                combined_mask = combined_mask & ~auto_exclude
            
            # Count results appropriately by data source
            if data_source == DataSource.RMS and 'case_number' in df.columns:
                # For RMS, count unique case numbers to avoid duplicates
                unique_count = df[combined_mask]['case_number'].nunique()
                results[crime_type] = unique_count
                logging.info(f"{data_source.value} {crime_type}: {unique_count} unique cases")
            else:
                # For CAD, count total records
                record_count = combined_mask.sum()
                results[crime_type] = record_count
                logging.info(f"{data_source.value} {crime_type}: {record_count} records")
        
        # Add total count
        if data_source == DataSource.RMS and 'case_number' in df.columns:
            results['total_records'] = df['case_number'].nunique()
        else:
            results['total_records'] = len(df)
        
        return results
    
    def validate_data_quality(self, df: pd.DataFrame, data_source: DataSource, structure_info: dict) -> dict:
        """Comprehensive data quality validation"""
        
        quality_report = {
            'data_source': data_source.value,
            'detection_confidence': structure_info.get('confidence', 'Unknown'),
            'total_records': len(df),
            'columns_detected': len(df.columns),
            'required_columns_present': True,
            'data_quality_issues': []
        }
        
        # Check case number availability
        case_col = 'case_number' if 'case_number' in df.columns else None
        if case_col:
            quality_report['null_case_numbers'] = df[case_col].isna().sum()
            quality_report['duplicate_case_numbers'] = df.duplicated(subset=[case_col]).sum()
        else:
            quality_report['data_quality_issues'].append('No case number column found')
        
        # Check incident data quality
        if 'incident_text' in df.columns:
            quality_report['null_incidents'] = df['incident_text'].isna().sum()
            quality_report['empty_incidents'] = (df['incident_text'] == '').sum()
            
            # Sample incident patterns for verification
            sample_incidents = df['incident_text'].dropna().head(10).tolist()
            quality_report['sample_incidents'] = sample_incidents
        else:
            quality_report['data_quality_issues'].append('No incident text column found')
        
        # Disposition data check
        if 'Disposition' in df.columns:
            see_report_count = df['Disposition'].str.contains('See Report', case=False, na=False).sum()
            quality_report['see_report_records'] = see_report_count
            quality_report['disposition_coverage'] = round(see_report_count / len(df) * 100, 2)
        else:
            quality_report['data_quality_issues'].append('No disposition column found')
        
        # Data source specific checks
        if data_source == DataSource.CAD:
            cad_specific = structure_info.get('cad_indicators', {})
            missing_cad_cols = [col for col, present in cad_specific.items() if not present]
            if missing_cad_cols:
                quality_report['missing_cad_columns'] = missing_cad_cols
        
        elif data_source == DataSource.RMS:
            rms_specific = structure_info.get('rms_indicators', {})
            missing_rms_cols = [col for col, present in rms_specific.items() if not present]
            if missing_rms_cols:
                quality_report['missing_rms_columns'] = missing_rms_cols
        
        return quality_report
    
    def run_validation(self, filename_pattern: str = "*.xlsx") -> tuple:
        """Run complete validation process"""
        
        logging.info("Starting SCRPA validation with actual data structures...")
        
        try:
            # Find and load data file
            matching_files = list(self.data_path.glob(filename_pattern))
            if not matching_files:
                raise FileNotFoundError(f"No files matching '{filename_pattern}' in {self.data_path}")
            
            latest_file = max(matching_files, key=lambda x: x.stat().st_mtime)
            logging.info(f"Processing: {latest_file}")
            
            df = pd.read_excel(latest_file, engine='openpyxl')
            logging.info(f"Loaded {len(df)} records, {len(df.columns)} columns")
            
            # Detect data source
            data_source, structure_info = self.detect_data_source(df)
            if data_source == DataSource.UNKNOWN:
                raise ValueError("Unable to identify data structure as CAD or RMS")
            
            # Prepare data based on source
            if data_source == DataSource.CAD:
                prepared_df = self.prepare_cad_data(df)
            else:  # RMS
                prepared_df = self.prepare_rms_data(df)
            
            # Run quality validation
            quality_report = self.validate_data_quality(prepared_df, data_source, structure_info)
            
            # Apply crime filtering
            crime_counts = self.apply_crime_filters(prepared_df, data_source)
            
            # Create summary results
            summary_data = []
            for crime_type, count in crime_counts.items():
                if crime_type != 'total_records':
                    summary_data.append({
                        'Crime_Type': crime_type.replace('_', ' ').title(),
                        'Count': count,
                        'Data_Source': data_source.value,
                        'Percentage': round(count / crime_counts['total_records'] * 100, 2) if crime_counts['total_records'] > 0 else 0
                    })
            
            # Add total row
            summary_data.append({
                'Crime_Type': 'TOTAL RECORDS',
                'Count': crime_counts['total_records'],
                'Data_Source': data_source.value,
                'Percentage': 100.0
            })
            
            results_df = pd.DataFrame(summary_data)
            
            return results_df, quality_report, data_source, structure_info
            
        except Exception as e:
            logging.error(f"Validation failed: {str(e)}")
            raise
    
    def export_comprehensive_report(self, results_df: pd.DataFrame, quality_report: dict, 
                                  data_source: DataSource, structure_info: dict):
        """Export comprehensive validation report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.data_path / f"SCRPA_Comprehensive_Report_{data_source.value}_{timestamp}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            # Crime type results
            results_df.to_excel(writer, sheet_name='Crime_Counts', index=False)
            
            # Data quality report
            quality_df = pd.DataFrame([quality_report]).T
            quality_df.columns = ['Value']
            quality_df.to_excel(writer, sheet_name='Data_Quality')
            
            # Structure analysis
            structure_df = pd.DataFrame([structure_info]).T
            structure_df.columns = ['Status']
            structure_df.to_excel(writer, sheet_name='Data_Structure')
            
            # Implementation recommendations
            if data_source == DataSource.CAD:
                recommendations = [
                    "CAD EXPORT PROCESSING RECOMMENDATIONS",
                    "=====================================",
                    "",
                    "✅ CONFIRMED DATA STRUCTURE:",
                    "- Single 'Incident' column (no unpivoting needed)",
                    "- Case numbers in 'ReportNumberNew' column",
                    "- Addresses in 'FullAddress2' column", 
                    "- Time data in 'Time of Call' column",
                    "- Disposition filtering available",
                    "",
                    "📋 M CODE IMPLEMENTATION:",
                    "1. Use ALL_CRIMES_CAD query (no unpivoting)",
                    "2. Reference [ReportNumberNew] for case numbers",
                    "3. Filter directly on [Incident] column",
                    "4. Apply Text.Upper() for case-insensitive matching",
                    "5. Include disposition filtering: 'See Report'",
                    "",
                    "⚡ PERFORMANCE ADVANTAGES:",
                    "- Faster processing (no unpivoting overhead)",
                    "- Simpler debugging and validation",
                    "- Direct alignment with ArcGIS Pro SQL",
                    "",
                    "⚠️ CRITICAL CORRECTIONS NEEDED:",
                    "- Change [Case Number] to [ReportNumberNew]",
                    "- Remove unpivoting logic from queries",
                    "- Add case-insensitive Text.Upper() filtering",
                    "- Verify disposition = 'See Report' filtering"
                ]
            else:  # RMS
                recommendations = [
                    "RMS EXPORT PROCESSING RECOMMENDATIONS",
                    "=====================================",
                    "",
                    "✅ CONFIRMED DATA STRUCTURE:",
                    "- Multiple 'Incident Type_1/2/3' columns (unpivoting required)",
                    "- Column names have SPACES not underscores",
                    "- Case numbers in 'Case Number' column",
                    "- Complex incident categorization supported",
                    "",
                    "📋 M CODE IMPLEMENTATION:",
                    "1. Use ALL_CRIMES_RMS query (with unpivoting)",
                    "2. Unpivot 'Incident Type_1', 'Incident Type_2', 'Incident Type_3'",
                    "3. Count unique [Case Number] values in child queries",
                    "4. Handle null/empty incident types after unpivot",
                    "",
                    "⚠️ PERFORMANCE CONSIDERATIONS:",
                    "- Slower processing due to unpivoting",
                    "- Larger memory usage after unpivot",
                    "- Must handle duplicate case counting",
                    "",
                    "🔧 KEY CORRECTIONS:",
                    "- Column names: 'Incident Type_1' (with space)",
                    "- Add validation before unpivoting",
                    "- Count unique case numbers, not total rows",
                    "- Verify disposition filtering post-unpivot"
                ]
            
            rec_df = pd.DataFrame({'Recommendations': recommendations})
            rec_df.to_excel(writer, sheet_name='Implementation', index=False)
        
        logging.info(f"Comprehensive report exported: {output_file}")
        return output_file

def main():
    """Main execution with enhanced reporting"""
    
    project_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
    
    try:
        validator = SCRPAActualDataValidator(project_path)
        
        print("🔍 SCRPA Data Structure Validation")
        print("=" * 50)
        
        # Run comprehensive validation
        results_df, quality_report, data_source, structure_info = validator.run_validation()
        
        # Display results
        print(f"\n📊 RESULTS - {data_source.value} DATA STRUCTURE DETECTED")
        print("=" * 50)
        print(results_df.to_string(index=False))
        
        print(f"\n🔍 DATA QUALITY SUMMARY")
        print("=" * 30)
        for key, value in quality_report.items():
            if not key.endswith('_issues') and not key.endswith('_incidents'):
                print(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Highlight issues
        if quality_report.get('data_quality_issues'):
            print(f"\n⚠️  DATA QUALITY ISSUES:")
            for issue in quality_report['data_quality_issues']:
                print(f"  - {issue}")
        
        # Export comprehensive report
        output_file = validator.export_comprehensive_report(
            results_df, quality_report, data_source, structure_info
        )
        
        print(f"\n📄 Detailed report saved: {output_file}")
        
        # Provide immediate next steps
        print(f"\n🎯 IMMEDIATE NEXT STEPS:")
        if data_source == DataSource.CAD:
            print("  1. Update Power BI to use ALL_CRIMES_CAD query")
            print("  2. Change [Case Number] to [ReportNumberNew] in filters")
            print("  3. Remove unpivoting logic from all child queries")
            print("  4. Test with sample data before full refresh")
        else:
            print("  1. Update Power BI to use ALL_CRIMES_RMS query")
            print("  2. Verify column names: 'Incident Type_1' (with space)")
            print("  3. Add unpivoting validation before processing")
            print("  4. Update child queries to count unique case numbers")
        
        print(f"\n✅ Validation completed successfully!")
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {str(e)}")
        print("\nCheck the log file for detailed error information:")
        print(f"  {project_path}/scrpa_validation_{datetime.now().strftime('%Y%m%d')}.log")

if __name__ == "__main__":
    main()