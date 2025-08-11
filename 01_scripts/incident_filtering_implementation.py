# 2025-08-02-23-30-15
# SCRPA_Time_v2/incident_filtering_implementation.py
# Author: R. A. Carucci
# Purpose: Production-ready incident filtering implementation with comparative methodologies and validation

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IncidentFilterProcessor:
    """
    Advanced incident filtering processor for CAD-RMS data with multiple filtering strategies
    and comprehensive validation capabilities.
    """
    
    def __init__(self, project_dir: str = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"):
        self.project_dir = project_dir
        self.target_crimes = [
            "Motor Vehicle Theft",
            "Robbery", 
            "Burglary – Auto",
            "Sexual",
            "Burglary – Commercial", 
            "Burglary – Residence"
        ]
        
        # Performance tracking
        self.performance_metrics = {}
        
    def filter_multi_column_simultaneous(self, df: pd.DataFrame, source_type: str = "CAD") -> pd.DataFrame:
        """
        Method 1: Filter across all incident-type columns simultaneously
        
        Args:
            df: Input dataframe (CAD or RMS)
            source_type: "CAD" or "RMS" for column selection
            
        Returns:
            Filtered dataframe
        """
        start_time = datetime.now()
        logger.info(f"Starting multi-column filtering for {source_type} data ({len(df)} records)")
        
        # Define column priority by data source
        if source_type.upper() == "CAD":
            incident_columns = ['incident', 'response_type_cad', 'category_type_cad', 
                              'response_type', 'category_type']
        else:  # RMS
            incident_columns = ['incident_type', 'all_incidents', 'nibrs_classification']
        
        # Available columns only
        available_columns = [col for col in incident_columns if col in df.columns]
        logger.info(f"Checking columns: {available_columns}")
        
        filtered_records = []
        case_numbers_processed = set()
        
        for _, row in df.iterrows():
            case_number = row.get('case_number', 'N/A')
            
            # Avoid duplicate processing
            if case_number in case_numbers_processed:
                continue
                
            match_found = False
            match_details = {}
            
            # Check each available column for target crimes
            for col in available_columns:
                if pd.notna(row[col]):
                    cell_value = str(row[col]).lower()
                    
                    # Case-insensitive matching
                    for crime in self.target_crimes:
                        if crime.lower() in cell_value:
                            filtered_records.append(row.to_dict())
                            match_details = {
                                'matched_column': col,
                                'matched_crime': crime,
                                'matched_value': row[col]
                            }
                            match_found = True
                            break
                            
                    if match_found:
                        break
            
            if match_found:
                case_numbers_processed.add(case_number)
                logger.debug(f"Match found - Case: {case_number}, {match_details}")
        
        result_df = pd.DataFrame(filtered_records)
        
        # Performance tracking
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        self.performance_metrics[f'multi_column_{source_type}'] = {
            'processing_time': processing_time,
            'input_records': len(df),
            'output_records': len(result_df),
            'retention_rate': len(result_df) / len(df) * 100 if len(df) > 0 else 0
        }
        
        logger.info(f"Multi-column filtering complete: {len(df)} → {len(result_df)} records ({processing_time:.2f}s)")
        return result_df
    
    def filter_unpivot_then_filter(self, df: pd.DataFrame, source_type: str = "CAD") -> pd.DataFrame:
        """
        Method 2: Unpivot incident columns then filter
        
        Args:
            df: Input dataframe
            source_type: "CAD" or "RMS" for column selection
            
        Returns:
            Filtered dataframe
        """
        start_time = datetime.now()
        logger.info(f"Starting unpivot-then-filter for {source_type} data ({len(df)} records)")
        
        # Identify incident-related columns
        incident_keywords = ['incident', 'type', 'category', 'response', 'classification']
        incident_cols = [col for col in df.columns 
                        if any(keyword in col.lower() for keyword in incident_keywords)]
        
        logger.info(f"Incident columns identified: {incident_cols}")
        
        if not incident_cols:
            logger.warning("No incident columns found - returning empty dataframe")
            return pd.DataFrame()
        
        # Non-incident columns as ID columns
        id_cols = [col for col in df.columns if col not in incident_cols]
        
        try:
            # Melt the dataframe
            melted_df = df.melt(id_vars=id_cols, 
                               value_vars=incident_cols,
                               var_name='incident_source', 
                               value_name='incident_value')
            
            # Create regex pattern for target crimes (case-insensitive)
            crime_pattern = '|'.join([crime.lower().replace('–', '-') for crime in self.target_crimes])
            
            # Filter for target crimes
            filtered_df = melted_df[
                melted_df['incident_value'].astype(str).str.lower().str.contains(
                    crime_pattern, 
                    case=False, 
                    na=False,
                    regex=True
                )
            ]
            
            # Deduplicate by case_number and get first match per case
            if 'case_number' in filtered_df.columns:
                result_df = filtered_df.drop_duplicates(subset=['case_number']).copy()
                
                # Reconstruct original structure by merging back
                case_numbers = result_df['case_number'].unique()
                result_df = df[df['case_number'].isin(case_numbers)].copy()
            else:
                # If no case_number, use index-based deduplication
                result_df = filtered_df.drop_duplicates().copy()
            
        except Exception as e:
            logger.error(f"Error in unpivot filtering: {str(e)}")
            return pd.DataFrame()
        
        # Performance tracking
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        self.performance_metrics[f'unpivot_{source_type}'] = {
            'processing_time': processing_time,
            'input_records': len(df),
            'output_records': len(result_df),
            'retention_rate': len(result_df) / len(df) * 100 if len(df) > 0 else 0
        }
        
        logger.info(f"Unpivot filtering complete: {len(df)} → {len(result_df)} records ({processing_time:.2f}s)")
        return result_df
    
    def filter_hybrid_approach(self, cad_df: pd.DataFrame, rms_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Method 3: Hybrid filtering using CAD for classification, RMS for details
        
        Args:
            cad_df: CAD dataframe
            rms_df: RMS dataframe
            
        Returns:
            Tuple of (filtered_cad_df, filtered_rms_df)
        """
        start_time = datetime.now()
        logger.info(f"Starting hybrid filtering: CAD({len(cad_df)}) + RMS({len(rms_df)}) records")
        
        # Step 1: Filter CAD data (has complete incident typing)
        cad_filtered = self.filter_multi_column_simultaneous(cad_df, "CAD")
        
        # Step 2: Get case numbers from filtered CAD data
        if not cad_filtered.empty and 'case_number' in cad_filtered.columns:
            target_cases = set(cad_filtered['case_number'].tolist())
            logger.info(f"CAD filtering identified {len(target_cases)} target cases")
            
            # Step 3: Filter RMS data by matching case numbers
            if 'case_number' in rms_df.columns:
                rms_filtered = rms_df[rms_df['case_number'].isin(target_cases)].copy()
            else:
                logger.warning("No case_number column in RMS data - cannot perform hybrid join")
                rms_filtered = pd.DataFrame()
        else:
            logger.warning("No case numbers available from CAD filtering")
            target_cases = set()
            rms_filtered = pd.DataFrame()
        
        # Performance tracking
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        self.performance_metrics['hybrid'] = {
            'processing_time': processing_time,
            'cad_input': len(cad_df),
            'cad_output': len(cad_filtered),
            'rms_input': len(rms_df),
            'rms_output': len(rms_filtered),
            'case_match_rate': len(rms_filtered) / len(cad_filtered) * 100 if len(cad_filtered) > 0 else 0
        }
        
        logger.info(f"Hybrid filtering complete: CAD({len(cad_df)}→{len(cad_filtered)}) RMS({len(rms_df)}→{len(rms_filtered)}) ({processing_time:.2f}s)")
        return cad_filtered, rms_filtered
    
    def validate_filtering_results(self, original_df: pd.DataFrame, filtered_df: pd.DataFrame, method_name: str) -> Dict[str, Any]:
        """
        Comprehensive validation of filtering results
        
        Args:
            original_df: Original dataframe before filtering
            filtered_df: Filtered dataframe
            method_name: Name of filtering method for reporting
            
        Returns:
            Dictionary with validation metrics
        """
        logger.info(f"Validating {method_name} filtering results")
        
        validation_results = {
            'method': method_name,
            'timestamp': datetime.now().isoformat(),
            'total_original': len(original_df),
            'total_filtered': len(filtered_df),
            'retention_rate': len(filtered_df) / len(original_df) * 100 if len(original_df) > 0 else 0,
            'case_loss': 0,
            'unexpected_inclusions': 0,
            'data_quality_issues': []
        }
        
        # Check for case loss (records that should have been included)
        incident_column = 'incident' if 'incident' in original_df.columns else 'incident_type'
        
        if incident_column in original_df.columns:
            should_be_included = []
            for _, row in original_df.iterrows():
                incident_value = str(row.get(incident_column, ''))
                if any(crime.lower() in incident_value.lower() for crime in self.target_crimes):
                    should_be_included.append(row.get('case_number', f'row_{_}'))
            
            actually_included = set(filtered_df.get('case_number', filtered_df.index).tolist())
            missed_cases = set(should_be_included) - actually_included
            validation_results['case_loss'] = len(missed_cases)
            
            if missed_cases:
                validation_results['data_quality_issues'].append(f"Missed cases: {list(missed_cases)[:5]}...")
        
        # Check for unexpected inclusions
        unexpected_count = 0
        if incident_column in filtered_df.columns:
            for _, row in filtered_df.iterrows():
                incident_value = str(row.get(incident_column, ''))
                if not any(crime.lower() in incident_value.lower() for crime in self.target_crimes):
                    unexpected_count += 1
        
        validation_results['unexpected_inclusions'] = unexpected_count
        
        # Calculate accuracy metrics
        if validation_results['total_original'] > 0:
            validation_results['accuracy'] = (
                (validation_results['total_filtered'] - validation_results['unexpected_inclusions']) /
                validation_results['total_original'] * 100
            )
        else:
            validation_results['accuracy'] = 0
        
        # Data quality checks
        if validation_results['retention_rate'] == 0:
            validation_results['data_quality_issues'].append("Zero retention - possible data structure mismatch")
        
        if validation_results['retention_rate'] > 95:
            validation_results['data_quality_issues'].append("Suspiciously high retention - check filter specificity")
        
        logger.info(f"Validation complete: {validation_results['retention_rate']:.1f}% retention, {validation_results['accuracy']:.1f}% accuracy")
        return validation_results
    
    def generate_comparative_report(self, cad_df: pd.DataFrame, rms_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive comparative analysis report
        
        Args:
            cad_df: CAD dataframe
            rms_df: RMS dataframe
            
        Returns:
            Dictionary with comparative analysis results
        """
        logger.info("Generating comparative filtering analysis report")
        
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'data_sources': {
                'cad_records': len(cad_df),
                'rms_records': len(rms_df)
            },
            'methods_tested': {},
            'recommendations': [],
            'performance_summary': {}
        }
        
        # Test Method 1: Multi-column on CAD
        logger.info("Testing Method 1: Multi-column filtering on CAD")
        cad_multi = self.filter_multi_column_simultaneous(cad_df.copy(), "CAD")
        cad_multi_validation = self.validate_filtering_results(cad_df, cad_multi, "Multi-Column CAD")
        
        # Test Method 1: Multi-column on RMS
        logger.info("Testing Method 1: Multi-column filtering on RMS")
        rms_multi = self.filter_multi_column_simultaneous(rms_df.copy(), "RMS")
        rms_multi_validation = self.validate_filtering_results(rms_df, rms_multi, "Multi-Column RMS")
        
        # Test Method 2: Unpivot on CAD
        logger.info("Testing Method 2: Unpivot filtering on CAD")
        cad_unpivot = self.filter_unpivot_then_filter(cad_df.copy(), "CAD")
        cad_unpivot_validation = self.validate_filtering_results(cad_df, cad_unpivot, "Unpivot CAD")
        
        # Test Method 2: Unpivot on RMS
        logger.info("Testing Method 2: Unpivot filtering on RMS")
        rms_unpivot = self.filter_unpivot_then_filter(rms_df.copy(), "RMS")
        rms_unpivot_validation = self.validate_filtering_results(rms_df, rms_unpivot, "Unpivot RMS")
        
        # Test Method 3: Hybrid approach
        logger.info("Testing Method 3: Hybrid filtering")
        hybrid_cad, hybrid_rms = self.filter_hybrid_approach(cad_df.copy(), rms_df.copy())
        hybrid_cad_validation = self.validate_filtering_results(cad_df, hybrid_cad, "Hybrid CAD")
        hybrid_rms_validation = self.validate_filtering_results(rms_df, hybrid_rms, "Hybrid RMS")
        
        # Compile results
        report['methods_tested'] = {
            'multi_column_cad': cad_multi_validation,
            'multi_column_rms': rms_multi_validation,
            'unpivot_cad': cad_unpivot_validation,
            'unpivot_rms': rms_unpivot_validation,
            'hybrid_cad': hybrid_cad_validation,
            'hybrid_rms': hybrid_rms_validation
        }
        
        # Performance summary
        report['performance_summary'] = self.performance_metrics
        
        # Generate recommendations
        best_cad_method = max(
            ['multi_column', 'unpivot', 'hybrid'],
            key=lambda x: report['methods_tested'][f'{x}_cad']['retention_rate']
        )
        
        best_rms_method = max(
            ['multi_column', 'unpivot', 'hybrid'],
            key=lambda x: report['methods_tested'][f'{x}_rms']['retention_rate']
        )
        
        report['recommendations'] = [
            f"Best CAD filtering method: {best_cad_method} ({report['methods_tested'][f'{best_cad_method}_cad']['retention_rate']:.1f}% retention)",
            f"Best RMS filtering method: {best_rms_method} ({report['methods_tested'][f'{best_rms_method}_rms']['retention_rate']:.1f}% retention)",
            "Use hybrid approach for production SCRPA reports" if hybrid_cad_validation['retention_rate'] > 0 else "CAD-only filtering recommended",
            "Implement data quality monitoring for RMS incident_type population" if rms_multi_validation['retention_rate'] == 0 else "RMS data quality acceptable"
        ]
        
        return report
    
    def export_filtered_data(self, filtered_df: pd.DataFrame, method_name: str, data_type: str) -> str:
        """
        Export filtered data with standardized naming convention
        
        Args:
            filtered_df: Filtered dataframe to export
            method_name: Name of filtering method
            data_type: "CAD" or "RMS"
            
        Returns:
            Path to exported file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"filtered_{data_type.lower()}_{method_name}_{timestamp}.csv"
        filepath = os.path.join(self.project_dir, filename)
        
        # Ensure all columns are lowercase snake_case
        filtered_df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in filtered_df.columns]
        
        filtered_df.to_csv(filepath, index=False)
        logger.info(f"Exported {len(filtered_df)} filtered {data_type} records to {filename}")
        
        return filepath
    
    def run_full_analysis(self, cad_file: str, rms_file: str) -> str:
        """
        Run complete comparative filtering analysis
        
        Args:
            cad_file: Path to CAD data file
            rms_file: Path to RMS data file
            
        Returns:
            Path to analysis report
        """
        logger.info("Starting comprehensive filtering analysis")
        
        # Load data
        try:
            cad_df = pd.read_csv(cad_file)
            rms_df = pd.read_csv(rms_file)
            logger.info(f"Loaded CAD: {len(cad_df)} records, RMS: {len(rms_df)} records")
        except Exception as e:
            logger.error(f"Error loading data files: {str(e)}")
            raise
        
        # Generate comparative report
        report = self.generate_comparative_report(cad_df, rms_df)
        
        # Export analysis report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"filtering_analysis_report_{timestamp}.json"
        report_filepath = os.path.join(self.project_dir, report_filename)
        
        import json
        with open(report_filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Analysis complete. Report saved to {report_filename}")
        return report_filepath


# Power BI M Code Implementation
def generate_powerbi_m_code() -> str:
    """
    Generate Power BI M Code for incident filtering
    
    Returns:
        M Code string for Power BI implementation
    """
    m_code = '''
let
    // 2025-08-02-23-35-15
    // SCRPA_Time_v2/PowerBI_IncidentFiltering.m
    // Author: R. A. Carucci
    // Purpose: Power BI M Code for multi-column incident filtering with case-insensitive logic
    
    // Define target crime types
    TargetCrimes = {
        "motor vehicle theft",
        "robbery", 
        "burglary – auto",
        "sexual",
        "burglary – commercial", 
        "burglary – residence"
    },
    
    // Custom function for case-insensitive matching
    ContainsAnyCrime = (inputText as text) as logical =>
        let
            LowerText = Text.Lower(inputText ?? ""),
            MatchFound = List.AnyTrue(
                List.Transform(TargetCrimes, each Text.Contains(LowerText, _))
            )
        in
            MatchFound,
    
    // Load and filter CAD data
    FilteredCAD = 
        let
            Source = Csv.Document(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\C08W31_20250802_7Day_cad_data_standardized.csv"),[Delimiter=",", Columns=25, Encoding=65001, QuoteStyle=QuoteStyle.None]),
            #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
            #"Filter Incidents" = Table.SelectRows(#"Promoted Headers", 
                each ContainsAnyCrime([incident]) or 
                     ContainsAnyCrime([response_type]) or 
                     ContainsAnyCrime([category_type])
            )
        in
            #"Filter Incidents",
    
    // Load and filter RMS data (with null handling)
    FilteredRMS = 
        let
            Source = Csv.Document(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\C08W31_20250802_7Day_rms_data_standardized.csv"),[Delimiter=",", Columns=24, Encoding=65001, QuoteStyle=QuoteStyle.None]),
            #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
            #"Filter Incidents" = Table.SelectRows(#"Promoted Headers", 
                each ContainsAnyCrime([incident_type] ?? "") or 
                     ContainsAnyCrime([all_incidents] ?? "") or
                     ContainsAnyCrime([nibrs_classification] ?? "")
            )
        in
            #"Filter Incidents"
in
    FilteredCAD
'''
    return m_code


# DAX Implementation
def generate_powerbi_dax_measures() -> str:
    """
    Generate DAX measures for Power BI incident filtering
    
    Returns:
        DAX measures string
    """
    dax_measures = '''
// 2025-08-02-23-37-15
// SCRPA_Time_v2/PowerBI_IncidentMeasures.dax
// Author: R. A. Carucci
// Purpose: DAX measures for incident filtering and validation in Power BI

// Primary filtering measure
Filtered Incident Count = 
VAR TargetCrimes = {
    "MOTOR VEHICLE THEFT",
    "ROBBERY", 
    "BURGLARY",
    "SEXUAL",
    "AUTO",
    "COMMERCIAL", 
    "RESIDENCE"
}
RETURN
SUMX(
    CAD_Data,
    IF(
        OR(
            CONTAINSSTRING(UPPER(CAD_Data[incident]), "MOTOR VEHICLE THEFT"),
            OR(
                CONTAINSSTRING(UPPER(CAD_Data[incident]), "ROBBERY"),
                OR(
                    CONTAINSSTRING(UPPER(CAD_Data[incident]), "BURGLARY"),
                    CONTAINSSTRING(UPPER(CAD_Data[incident]), "SEXUAL")
                )
            )
        ),
        1,
        0
    )
)

// Validation measure - retention rate
Filter Retention Rate = 
DIVIDE(
    [Filtered Incident Count],
    COUNTROWS(CAD_Data),
    0
) * 100

// Crime type breakdown
Motor Vehicle Theft Count = 
COUNTROWS(
    FILTER(
        CAD_Data,
        CONTAINSSTRING(UPPER(CAD_Data[incident]), "MOTOR VEHICLE THEFT")
    )
)

Burglary Count = 
COUNTROWS(
    FILTER(
        CAD_Data,
        CONTAINSSTRING(UPPER(CAD_Data[incident]), "BURGLARY")
    )
)

Robbery Count = 
COUNTROWS(
    FILTER(
        CAD_Data,
        CONTAINSSTRING(UPPER(CAD_Data[incident]), "ROBBERY")
    )
)

Sexual Crimes Count = 
COUNTROWS(
    FILTER(
        CAD_Data,
        CONTAINSSTRING(UPPER(CAD_Data[incident]), "SEXUAL")
    )
)
'''
    return dax_measures


# Usage Example
if __name__ == "__main__":
    # Initialize processor
    processor = IncidentFilterProcessor()
    
    # Define file paths
    cad_file = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\C08W31_20250802_7Day_cad_data_standardized.csv"
    rms_file = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\C08W31_20250802_7Day_rms_data_standardized.csv"
    
    # Run comprehensive analysis
    try:
        report_path = processor.run_full_analysis(cad_file, rms_file)
        print(f"Analysis complete. Report saved to: {report_path}")
        
        # Generate Power BI code files
        m_code = generate_powerbi_m_code()
        dax_measures = generate_powerbi_dax_measures()
        
        # Save Power BI implementations
        with open(os.path.join(processor.project_dir, "PowerBI_MCode_Implementation.m"), 'w') as f:
            f.write(m_code)
        
        with open(os.path.join(processor.project_dir, "PowerBI_DAX_Measures.dax"), 'w') as f:
            f.write(dax_measures)
        
        print("Power BI implementation files generated successfully")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise