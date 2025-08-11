# 🕒 2025-07-23-06-00-00
# SCRPA_Time_v2/updated_scrpa_validation.py
# Author: R. A. Carucci
# Purpose: Updated validation script handling both CAD (single Incident column) and RMS (multiple Incident Type_X columns) data structures

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

class DataSource(Enum):
    CAD = "CAD"
    RMS = "RMS" 
    UNKNOWN = "UNKNOWN"

class SCRPADataValidator:
    """
    Validates crime data filtering for both CAD and RMS export structures
    CAD: Single 'Incident' column
    RMS: Multiple 'Incident Type_1', 'Incident Type_2', 'Incident Type_3' columns
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
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scrpa_validation.log'),
                logging.StreamHandler()
            ]
        )
        
    def detect_data_source(self, df: pd.DataFrame) -> DataSource:
        """Detect whether data is from CAD or RMS export"""
        
        # Check for CAD structure (single Incident column)
        if 'Incident' in df.columns:
            logging.info("Detected CAD data structure (single 'Incident' column)")
            return DataSource.CAD
            
        # Check for RMS structure (multiple Incident Type columns)
        rms_columns = ['Incident Type_1', 'Incident Type_2', 'Incident Type_3']
        if any(col in df.columns for col in rms_columns):
            found_cols = [col for col in rms_columns if col in df.columns]
            logging.info(f"Detected RMS data structure (columns: {found_cols})")
            return DataSource.RMS
            
        # Check for alternative naming patterns
        incident_cols = [col for col in df.columns if 'incident' in col.lower()]
        if incident_cols:
            logging.warning(f"Found incident-related columns but unclear structure: {incident_cols}")
            return DataSource.UNKNOWN
            
        logging.error("No incident columns found in dataset")
        return DataSource.UNKNOWN
    
    def load_data_file(self, file_pattern: str = "*.xlsx") -> tuple[pd.DataFrame, DataSource]:
        """Load data file and detect its structure"""
        
        # Try to find the most recent matching file
        matching_files = list(self.data_path.glob(file_pattern))
        if not matching_files:
            raise FileNotFoundError(f"No files matching pattern '{file_pattern}' found in {self.data_path}")
            
        # Use the most recently modified file
        latest_file = max(matching_files, key=lambda x: x.stat().st_mtime)
        logging.info(f"Loading data from: {latest_file}")
        
        # Load the data
        df = pd.read_excel(latest_file, engine='openpyxl')
        logging.info(f"Loaded {len(df)} records from {latest_file}")
        
        # Detect data source type
        data_source = self.detect_data_source(df)
        
        return df, data_source
    
    def prepare_cad_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare CAD data (single Incident column, no unpivoting needed)"""
        
        # Validate required columns
        if 'Incident' not in df.columns:
            raise ValueError("CAD data must have 'Incident' column")
            
        # Remove excluded cases
        if 'Case Number' in df.columns:
            df = df[df['Case Number'] != '25-057654']
            
        # Clean incident data
        df['incident_clean'] = df['Incident'].fillna('').astype(str)
        
        # Apply disposition fil