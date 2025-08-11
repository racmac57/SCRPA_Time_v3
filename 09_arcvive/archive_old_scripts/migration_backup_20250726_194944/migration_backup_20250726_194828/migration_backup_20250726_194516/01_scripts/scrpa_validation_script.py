# 🕒 2025-07-23-06-00-00
# SCRPA_Time_v2/scrpa_data_validation.py
# Author: R. A. Carucci
# Purpose: Validate crime data filtering consistency between multi-column and unpivot approaches with case-insensitive matching

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scrpa_validation.log'),
        logging.StreamHandler()
    ]
)

class SCRPADataValidator:
    """
    Validates crime data filtering approaches for SCRPA analysis
    Compares multi-column filtering vs unpivot-then-filter methodologies
    """
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.crime_patterns = {
            'motor_vehicle_theft': ['MOTOR VEHICLE THEFT', 'AUTO THEFT', 'MV THEFT'],
            'burglary_auto': ['BURGLARY.*AUTO', 'BURGLARY.*VEHICLE'],
            'burglary_commercial': ['BURGLARY.*COMMERCIAL', 'BURGLARY - COMMERCIAL'],
            'burglary_residence': ['BURGLARY.*RESIDENCE', 'BURGLARY - RESIDENCE'],
            'robbery': ['ROBBERY'],
            'sexual': ['SEXUAL']
        }
        
    def load_cad_data(self) -> pd.DataFrame:
        """Load CAD export data from Excel file"""
        try:
            # Adjust file path based on your actual export location
            file_path = self.data_path / "latest_cad_export.xlsx"
            df = pd.read_excel(file_path, engine='openpyxl')
            
            logging.info(f"Loaded {len(df)} records from {file_path}")
            return df
            
        except FileNotFoundError:
            logging.error(f"CAD export file not found at {file_path}")
            raise
        except Exception as e:
            logging.error(f"Error loading CAD data: {str(e)}")
            raise
    
    def case_insensitive_match(self, text: str, patterns: list) -> bool:
        """
        Perform case-insensitive pattern matching
        Returns True if any pattern matches the text
        """
        if pd.isna(text) or text == "":
            return False
            
        text_upper = str(text).upper()
        return any(pattern.upper() in text_upper for pattern in patterns)
    
    def multi_column_filtering(self, df: pd.DataFrame) -> dict:
        """
        Approach A: Filter across Incident_Type_1, Incident_Type_2, Incident_Type_3
        Combines all incident columns then applies filtering
        """
        results = {}
        
        # Create combined incident text
        incident_cols = ['Incident_Type_1', 'Incident_Type_2', 'Incident_Type_3']
        existing_cols = [col for col in incident_cols if col in df.columns]
        
        if not existing_cols:
            logging.warning("No incident type columns found - checking for alternatives")
            # Check for alternative column names
            alt_cols = [col for col in df.columns if 'incident' in col.lower() or 'call' in col.lower()]
            if alt_cols:
                existing_cols = alt_cols[:3]  # Take first 3 matching columns
                logging.info(f"Using alternative columns: {existing_cols}")
        
        df['combined_incidents'] = df[existing_cols].fillna('').apply(
            lambda row: ' '.join(row.astype(str)), axis=1
        )
        
        # Apply filtering for each crime type
        for crime_type, patterns in self.crime_patterns.items():
            mask = df['combined_incidents'].apply(
                lambda x: self.case_insensitive_match(x, patterns)
            )
            
            # Additional logic for burglary subtypes
            if crime_type == 'burglary_auto':
                burglary_mask = df['combined_incidents'].apply(
                    lambda x: self.case_insensitive_match(x, ['BURGLARY'])
                )
                auto_mask = df['combined_incidents'].apply(
                    lambda x: self.case_insensitive_match(x, ['AUTO', 'VEHICLE'])
                )
                mask = burglary_mask & auto_mask
                
            elif crime_type in ['burglary_commercial', 'burglary_residence']:
                # Exclude auto burglaries from commercial/residential
                auto_mask = df['combined_incidents'].apply(
                    lambda x: self.case_insensitive_match(x, ['AUTO', 'VEHICLE'])
                )
                mask = mask & ~auto_mask
            
            results[crime_type] = mask.sum()
            logging.info(f"Multi-column {crime_type}: {mask.sum()} incidents")
        
        results['total_records'] = len(df)
        return results
    
    def unpivot_filtering(self, df: pd.DataFrame) -> dict:
        """
        Approach B: Unpivot incident types then filter
        Creates long format data then applies filtering
        """
        results = {}
        
        # Identify incident type columns
        incident_cols = [col for col in df.columns if 'incident' in col.lower() and 'type' in col.lower()]
        if not incident_cols:
            incident_cols = ['Incident_Type_1', 'Incident_Type_2', 'Incident_Type_3']
            incident_cols = [col for col in incident_cols if col in df.columns]
        
        if not incident_cols:
            logging.error("No incident type columns found for unpivoting")
            return results
        
        # Create ID columns (everything except incident types)
        id_cols = [col for col in df.columns if col not in incident_cols]
        
        # Unpivot the data
        df_unpivoted = pd.melt(
            df, 
            id_vars=id_cols,
            value_vars=incident_cols,
            var_name='incident_column',
            value_name='incident_type'
        )
        
        # Remove null/empty incident types
        df_unpivoted = df_unpivoted[
            df_unpivoted['incident_type'].notna() & 
            (df_unpivoted['incident_type'] != '')
        ]
        
        # Apply disposition filtering if column exists
        if 'Disposition' in df_unpivoted.columns:
            df_unpivoted = df_unpivoted[
                df_unpivoted['Disposition'].str.contains('See Report', case=False, na=False)
            ]
            logging.info(f"Applied disposition filtering: {len(df_unpivoted)} records remaining")
        
        # Apply filtering for each crime type
        for crime_type, patterns in self.crime_patterns.items():
            mask = df_unpivoted['incident_type'].apply(
                lambda x: self.case_insensitive_match(x, patterns)
            )
            
            # Additional logic for burglary subtypes
            if crime_type == 'burglary_auto':
                burglary_mask = df_unpivoted['incident_type'].apply(
                    lambda x: self.case_insensitive_match(x, ['BURGLARY'])
                )
                auto_mask = df_unpivoted['incident_type'].apply(
                    lambda x: self.case_insensitive_match(x, ['AUTO', 'VEHICLE'])
                )
                mask = burglary_mask & auto_mask
                
            elif crime_type in ['burglary_commercial', 'burglary_residence']:
                auto_mask = df_unpivoted['incident_type'].apply(
                    lambda x: self.case_insensitive_match(x, ['AUTO', 'VEHICLE'])
                )
                mask = mask & ~auto_mask
            
            # Count unique case numbers (avoid duplicates from unpivoting)
            unique_cases = df_unpivoted[mask]['Case Number'].nunique() if 'Case Number' in df_unpivoted.columns else mask.sum()
            results[crime_type] = unique_cases
            logging.info(f"Unpivot {crime_type}: {unique_cases} unique cases")
        
        results['total_records'] = df['Case Number'].nunique() if 'Case Number' in df.columns else len(df)
        return results
    
    def generate_comparison_report(self, multi_col_results: dict, unpivot_results: dict) -> pd.DataFrame:
        """Generate comparison report between filtering approaches"""
        
        comparison_data = []
        for crime_type in self.crime_patterns.keys():
            multi_count = multi_col_results.get(crime_type, 0)
            unpivot_count = unpivot_results.get(crime_type, 0)
            difference = unpivot_count - multi_count
            pct_diff = (difference / multi_count * 100) if multi_count > 0 else 0
            
            comparison_data.append({
                'Crime_Type': crime_type.replace('_', ' ').title(),
                'Multi_Column_Count': multi_count,
                'Unpivot_Count': unpivot_count,
                'Difference': difference,
                'Percent_Difference': round(pct_diff, 2),
                'Recommendation': 'Investigate' if abs(pct_diff) > 5 else 'Acceptable'
            })
        
        # Add totals row
        comparison_data.append({
            'Crime_Type': 'TOTAL RECORDS',
            'Multi_Column_Count': multi_col_results.get('total_records', 0),
            'Unpivot_Count': unpivot_results.get('total_records', 0),
            'Difference': 0,
            'Percent_Difference': 0,
            'Recommendation': 'Reference'
        })
        
        return pd.DataFrame(comparison_data)
    
    def validate_data_quality(self, df: pd.DataFrame) -> dict:
        """Perform data quality checks"""
        quality_report = {
            'total_records': len(df),
            'null_case_numbers': df['Case Number'].isna().sum() if 'Case Number' in df.columns else 0,
            'duplicate_cases': df.duplicated(subset=['Case Number']).sum() if 'Case Number' in df.columns else 0,
            'missing_incident_types': 0,
            'missing_dispositions': df['Disposition'].isna().sum() if 'Disposition' in df.columns else 0
        }
        
        # Check for missing incident types across all columns
        incident_cols = [col for col in df.columns if 'incident' in col.lower() and 'type' in col.lower()]
        if incident_cols:
            all_null_mask = df[incident_cols].isna().all(axis=1)
            quality_report['missing_incident_types'] = all_null_mask.sum()
        
        return quality_report
    
    def run_validation(self) -> tuple:
        """Run complete validation process"""
        logging.info("Starting SCRPA data validation process...")
        
        # Load data
        df = self.load_cad_data()
        
        # Run data quality checks
        quality_report = self.validate_data_quality(df)
        logging.info(f"Data Quality Summary: {quality_report}")
        
        # Run both filtering approaches
        logging.info("Running multi-column filtering approach...")
        multi_col_results = self.multi_column_filtering(df)
        
        logging.info("Running unpivot filtering approach...")
        unpivot_results = self.unpivot_filtering(df)
        
        # Generate comparison report
        comparison_df = self.generate_comparison_report(multi_col_results, unpivot_results)
        
        return comparison_df, quality_report
    
    def export_results(self, comparison_df: pd.DataFrame, quality_report: dict):
        """Export validation results to Excel"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.data_path / f"SCRPA_Validation_Report_{timestamp}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Comparison results
            comparison_df.to_excel(writer, sheet_name='Filtering_Comparison', index=False)
            
            # Data quality summary
            quality_df = pd.DataFrame([quality_report]).T
            quality_df.columns = ['Count']
            quality_df.to_excel(writer, sheet_name='Data_Quality')
            
            # Recommendations
            recommendations = [
                "IMMEDIATE ACTIONS:",
                "1. Implement case-insensitive filtering for all crime types",
                "2. Add disposition filtering: 'See Report' validation", 
                "3. Use unpivot approach for consistency with ArcGIS Pro",
                "",
                "VALIDATION CRITERIA:",
                "- Differences >5% require investigation",
                "- Monitor null/duplicate case numbers", 
                "- Verify incident type completeness",
                "",
                "NEXT STEPS:",
                "- Update Power BI M Code with recommended patterns",
                "- Implement automated monitoring for count discrepancies",
                "- Schedule weekly validation runs"
            ]
            
            rec_df = pd.DataFrame({'Recommendations': recommendations})
            rec_df.to_excel(writer, sheet_name='Action_Items', index=False)
        
        logging.info(f"Validation report exported to: {output_file}")
        return output_file

def main():
    """Main execution function"""
    # Set your project directory path
    project_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
    
    try:
        validator = SCRPADataValidator(project_path)
        comparison_df, quality_report = validator.run_validation()
        
        # Print summary to console
        print("\n" + "="*80)
        print("SCRPA DATA VALIDATION SUMMARY")
        print("="*80)
        print(comparison_df.to_string(index=False))
        
        print(f"\nData Quality Issues:")
        for key, value in quality_report.items():
            if value > 0:
                print(f"  - {key.replace('_', ' ').title()}: {value}")
        
        # Export detailed results
        output_file = validator.export_results(comparison_df, quality_report)
        print(f"\nDetailed report saved to: {output_file}")
        
        # Identify critical issues
        critical_issues = comparison_df[
            abs(comparison_df['Percent_Difference']) > 10
        ]
        
        if len(critical_issues) > 0:
            print(f"\n⚠️  CRITICAL: {len(critical_issues)} crime types have >10% count differences")
            print("Immediate review required for:", critical_issues['Crime_Type'].tolist())
        else:
            print("\n✅ All crime type counts within acceptable variance (<10%)")
            
    except Exception as e:
        logging.error(f"Validation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()