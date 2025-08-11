# 🕒 2025-05-27-18-28-52
# crime_report_tool/table_export.py
# Author: R. Carucci
# Purpose: Export summary crime tables to CSV format for each crime type
# Last updated: 2025-05-27

import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Union
import logging

# Set up logging for this module
logger = logging.getLogger(__name__)

def validate_inputs(crime_type: str, output_folder: str, table_dir: str, suffixes: List[str]) -> None:
    """
    Validate input parameters for the export_tables function.
    
    Args:
        crime_type: Type of crime to process
        output_folder: Directory to save output files
        table_dir: Directory containing source CSV files
        suffixes: List of time period suffixes to process
        
    Raises:
        ValueError: If any input parameter is invalid
        FileNotFoundError: If required directories don't exist
    """
    if not crime_type or not isinstance(crime_type, str):
        raise ValueError("Crime type must be a non-empty string")
    
    if not output_folder or not isinstance(output_folder, str):
        raise ValueError("Output folder must be a non-empty string")
    
    if not table_dir or not isinstance(table_dir, str):
        raise ValueError("Table directory must be a non-empty string")
    
    if not suffixes or not isinstance(suffixes, list):
        raise ValueError("Suffixes must be a non-empty list")
    
    # Check if directories exist
    if not os.path.exists(table_dir):
        raise FileNotFoundError(f"Table directory does not exist: {table_dir}")
    
    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)

def sanitize_filename(crime_type: str) -> str:
    """
    Sanitize crime type for use in filenames.
    
    Args:
        crime_type: Raw crime type string
        
    Returns:
        Sanitized filename-safe string
    """
    # Replace spaces and ampersands, remove other problematic characters
    sanitized = crime_type.replace(' ', '_').replace('&', 'And')
    # Remove any remaining problematic characters for file systems
    sanitized = ''.join(c for c in sanitized if c.isalnum() or c in ('_', '-'))
    return sanitized

def export_tables(crime_type: str, output_folder: str, table_dir: Optional[str] = None, 
                 suffixes: Optional[List[str]] = None) -> Dict[str, Union[str, int]]:
    """
    Export summary crime tables to CSV format for each crime type.
    
    Args:
        crime_type: Type of crime to process (e.g., 'Burglary', 'Auto Theft')
        output_folder: Directory to save the summary CSV file
        table_dir: Directory containing source CSV files (uses config.TABLE_DIR if None)
        suffixes: List of time period suffixes (uses config.SUFFIXES if None)
        
    Returns:
        Dictionary with export results including file path and record count
        
    Raises:
        ValueError: If input parameters are invalid
        FileNotFoundError: If required directories don't exist
    """
    # Import config values if not provided as parameters
    if table_dir is None or suffixes is None:
        try:
            from config import TABLE_DIR, SUFFIXES
            if table_dir is None:
                table_dir = TABLE_DIR
            if suffixes is None:
                suffixes = SUFFIXES
        except ImportError:
            raise ImportError("Could not import TABLE_DIR and SUFFIXES from config module")
    
    # Validate all inputs
    validate_inputs(crime_type, output_folder, table_dir, suffixes)
    
    summary = []
    processed_files = 0
    error_count = 0
    
    logger.info(f"Starting export for crime type: {crime_type}")
    
    # Sanitize crime type for filename
    sanitized_crime_type = sanitize_filename(crime_type)
    
    for suffix in suffixes:
        fname = f"{sanitized_crime_type}_{suffix}.csv"
        path = os.path.join(table_dir, fname)
        
        if not os.path.exists(path):
            logger.warning(f"File not found: {path}")
            continue
        
        try:
            # Read CSV with error handling for encoding issues
            try:
                df = pd.read_csv(path, encoding='utf-8')
            except UnicodeDecodeError:
                logger.warning(f"UTF-8 encoding failed for {path}, trying latin-1")
                df = pd.read_csv(path, encoding='latin-1')
            
            # Validate that we have actual data
            if df.empty:
                logger.warning(f"Empty dataframe for {path}")
                count = 0
            else:
                count = len(df)
            
            summary.append({
                "Period": suffix,
                "Incidents": count,
                "Status": "Success"
            })
            processed_files += 1
            logger.debug(f"Processed {path}: {count} incidents")
            
        except pd.errors.EmptyDataError:
            error_msg = "Empty file"
            summary.append({
                "Period": suffix,
                "Incidents": 0,
                "Status": f"Error: {error_msg}"
            })
            error_count += 1
            logger.error(f"Empty data error for {path}")
            
        except pd.errors.ParserError as e:
            error_msg = f"Parse error: {str(e)[:50]}..."
            summary.append({
                "Period": suffix,
                "Incidents": "N/A",
                "Status": f"Error: {error_msg}"
            })
            error_count += 1
            logger.error(f"Parser error for {path}: {e}")
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)[:50]}..."
            summary.append({
                "Period": suffix,
                "Incidents": "N/A",
                "Status": f"Error: {error_msg}"
            })
            error_count += 1
            logger.error(f"Unexpected error for {path}: {e}")
    
    # Generate output only if we have data
    if summary:
        df_summary = pd.DataFrame(summary)
        
        # Create output filename with sanitized crime type
        output_filename = f"{sanitized_crime_type}_Records.csv"
        out_path = os.path.join(output_folder, output_filename)
        
        try:
            # Save with UTF-8 encoding and proper index handling
            df_summary.to_csv(out_path, index=False, encoding='utf-8')
            
            total_incidents = sum(
                row["Incidents"] for row in summary 
                if isinstance(row["Incidents"], int)
            )
            
            logger.info(f"Export completed: {out_path}")
            logger.info(f"Processed {processed_files} files, {error_count} errors, {total_incidents} total incidents")
            
            return {
                "status": "success",
                "output_path": out_path,
                "processed_files": processed_files,
                "error_count": error_count,
                "total_incidents": total_incidents
            }
            
        except Exception as e:
            logger.error(f"Failed to save output file {out_path}: {e}")
            raise
    else:
        logger.warning(f"No data found for crime type: {crime_type}")
        return {
            "status": "no_data",
            "output_path": None,
            "processed_files": 0,
            "error_count": error_count,
            "total_incidents": 0
        }

def export_multiple_crime_types(crime_types: List[str], output_folder: str, 
                               table_dir: Optional[str] = None, 
                               suffixes: Optional[List[str]] = None) -> Dict[str, Dict]:
    """
    Export tables for multiple crime types in batch.
    
    Args:
        crime_types: List of crime types to process
        output_folder: Directory to save output files
        table_dir: Directory containing source CSV files
        suffixes: List of time period suffixes
        
    Returns:
        Dictionary with results for each crime type
    """
    results = {}
    
    for crime_type in crime_types:
        try:
            result = export_tables(crime_type, output_folder, table_dir, suffixes)
            results[crime_type] = result
        except Exception as e:
            logger.error(f"Failed to export {crime_type}: {e}")
            results[crime_type] = {
                "status": "error",
                "error": str(e)
            }
    
    return results

if __name__ == "__main__":
    # Test the function
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    try:
        result = export_tables(
            crime_type="Burglary & Breaking Entering",
            output_folder="./test_output",
            table_dir="./test_tables",
            suffixes=["2024_Q1", "2024_Q2", "2024_Q3", "2024_Q4"]
        )
        print(f"Export result: {result}")
    except Exception as e:
        print(f"Export failed: {e}")
