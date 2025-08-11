# 🕒 2025-07-23-05-30-00
# SCRPA_Time_v2/unified_data_processor.py
# Author: R. A. Carucci
# Purpose: Unified CAD/RMS data processing pipeline with deduplication, weather data, and LLM integration

import pandas as pd
import numpy as np
import logging
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import sqlite3
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class IncidentRecord:
    """Standardized incident record structure."""
    case_number: str
    incident_date: datetime
    incident_time: str
    incident_type: str
    address: str
    grid: str
    zone: str
    officer: str
    response_time: Optional[float]
    time_spent: Optional[float]
    narrative: Optional[str]
    source: str  # 'CAD' or 'RMS'
    data_quality_score: float
    unique_hash: str
    
class UnifiedDataProcessor:
    """
    Unified CAD/RMS data processing pipeline.
    
    Features:
    - Prevents double-counting through intelligent deduplication
    - Fixes negative response times and excessive time spent
    - Adds weather conditions from open source APIs
    - Creates custom columns (time of day, block, etc.)
    - Exports clean data for Power BI
    - Includes watchdog automation
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize unified processor."""
        self.base_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        self.config = self._load_config(config_path)
        
        # Processing statistics
        self.stats = {
            'cad_records_processed': 0,
            'rms_records_processed': 0,
            'duplicates_removed': 0,
            'negative_times_fixed': 0,
            'weather_records_added': 0,
            'total_combined_records': 0,
            'data_quality_avg': 0.0
        }
        
        # Create database for deduplication tracking
        self.db_path = self.base_path / "incident_tracking.db"
        self._init_database()
        
        # Load reference data
        self.officer_mappings = self._load_officer_mappings()
        self.zone_mappings = self._load_zone_mappings()
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration with defaults."""
        default_config = {
            "input_folders": {
                "cad_exports": str(self.base_path / "CAD_Exports"),
                "rms_exports": str(self.base_path / "RMS_Exports")
            },
            "output_folder": str(self.base_path / "Processed_Data"),
            "weather_api": {
                "enabled": True,
                "source": "openweathermap",
                "api_key": None,  # Set in environment or config
                "location": "Hackensack,NJ,US"
            },
            "deduplication": {
                "match_threshold": 0.85,
                "time_window_minutes": 30,
                "key_fields": ["address", "incident_type", "incident_time"]
            },
            "time_corrections": {
                "max_response_time_hours": 8,
                "max_time_spent_hours": 12,
                "fix_negative_times": True
            },
            "custom_columns": {
                "time_of_day_buckets": {
                    "Morning": "06:00-11:59",
                    "Afternoon": "12:00-15:59", 
                    "Evening Peak": "16:00-19:59",
                    "Night": "20:00-05:59"
                },
                "block_generation": True,
                "enhanced_geocoding": True
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _init_database(self):
        """Initialize SQLite database for tracking processed incidents."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_incidents (
                unique_hash TEXT PRIMARY KEY,
                case_number TEXT,
                incident_date TEXT,
                incident_time TEXT,
                address TEXT,
                incident_type TEXT,
                source TEXT,
                processed_date TEXT,
                data_quality_score REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def process_cad_data(self, file_path: str) -> pd.DataFrame:
        """Process CAD data with enhanced cleaning."""
        logger.info(f"🔄 Processing CAD file: {Path(file_path).name}")
        
        # Load CAD data
        df = self._load_data_file(file_path)
        original_count = len(df)
        
        # Apply CAD-specific cleaning
        df = self._clean_cad_data(df)
        df = self._fix_time_issues(df, 'CAD')
        df = self._standardize_addresses(df)
        df = self._map_officers(df)
        df = self._add_custom_columns(df)
        
        # Add source identifier
        df['source'] = 'CAD'
        
        # Generate unique hash for deduplication
        df['unique_hash'] = df.apply(self._generate_incident_hash, axis=1)
        
        # Calculate data quality scores
        df['data_quality_score'] = df.apply(self._calculate_quality_score, axis=1)
        
        self.stats['cad_records_processed'] = len(df)
        logger.info(f"✅ CAD processing complete: {original_count} → {len(df)} records")
        
        return df
    
    def process_rms_data(self, file_path: str) -> pd.DataFrame:
        """Process RMS data with enhanced cleaning."""
        logger.info(f"🔄 Processing RMS file: {Path(file_path).name}")
        
        # Load RMS data
        df = self._load_data_file(file_path)
        original_count = len(df)
        
        # Apply RMS-specific cleaning
        df = self._clean_rms_data(df)
        df = self._fix_time_issues(df, 'RMS')
        df = self._standardize_addresses(df)
        df = self._map_officers(df)
        df = self._add_custom_columns(df)
        
        # Add source identifier
        df['source'] = 'RMS'
        
        # Generate unique hash for deduplication
        df['unique_hash'] = df.apply(self._generate_incident_hash, axis=1)
        
        # Calculate data quality scores
        df['data_quality_score'] = df.apply(self._calculate_quality_score, axis=1)
        
        self.stats['rms_records_processed'] = len(df)
        logger.info(f"✅ RMS processing complete: {original_count} → {len(df)} records")
        
        return df
    
    def _fix_time_issues(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Fix negative response times and excessive time spent."""
        logger.info(f"🔧 Fixing time issues for {source} data")
        
        fixed_count = 0
        
        # Fix response times
        if 'response_time' in df.columns:
            # Convert to minutes if needed
            df['response_time'] = pd.to_numeric(df['response_time'], errors='coerce')
            
            # Fix negative response times
            negative_mask = df['response_time'] < 0
            fixed_count += negative_mask.sum()
            df.loc[negative_mask, 'response_time'] = abs(df.loc[negative_mask, 'response_time'])
            
            # Cap excessive response times (8 hours = 480 minutes)
            max_response = self.config['time_corrections']['max_response_time_hours'] * 60
            excessive_mask = df['response_time'] > max_response
            df.loc[excessive_mask, 'response_time'] = max_response
            
        # Fix time spent on scene
        if 'time_spent' in df.columns:
            # Convert to minutes if needed
            df['time_spent'] = pd.to_numeric(df['time_spent'], errors='coerce')
            
            # Fix negative time spent
            negative_mask = df['time_spent'] < 0
            fixed_count += negative_mask.sum()
            df.loc[negative_mask, 'time_spent'] = abs(df.loc[negative_mask, 'time_spent'])
            
            # Cap excessive time spent (12 hours = 720 minutes)
            max_time_spent = self.config['time_corrections']['max_time_spent_hours'] * 60
            excessive_mask = df['time_spent'] > max_time_spent
            df.loc[excessive_mask, 'time_spent'] = max_time_spent
        
        self.stats['negative_times_fixed'] += fixed_count
        logger.info(f"   Fixed {fixed_count} time issues")
        
        return df
    
    def _add_custom_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add custom columns like time of day, block, enhanced geocoding."""
        logger.info("📊 Adding custom columns")
        
        # Time of day buckets
        df['time_of_day'] = df['incident_time'].apply(self._categorize_time_of_day)
        
        # Enhanced time of day with more detail
        df['enhanced_time_of_day'] = df['incident_time'].apply(self._enhanced_time_category)
        
        # Block generation from address
        df['block'] = df['address'].apply(self._generate_block)
        
        # Enhanced block with cleanup
        df['block_enhanced'] = df['block'].apply(self._enhance_block_name)
        
        # Day name and month name
        if 'incident_date' in df.columns:
            df['incident_date'] = pd.to_datetime(df['incident_date'], errors='coerce')
            df['day_name'] = df['incident_date'].dt.day_name()
            df['month_name'] = df['incident_date'].dt.month_name()
            df['year'] = df['incident_date'].dt.year
            df['week_of_year'] = df['incident_date'].dt.isocalendar().week
            df['day'] = df['incident_date'].dt.day
        
        # Period classification (7-day, 28-day, etc.)
        df['period'] = '7-Day'  # Default, can be customized based on analysis window
        
        return df
    
    def _categorize_time_of_day(self, time_str: str) -> str:
        """Categorize time into day periods."""
        if pd.isna(time_str):
            return "Unknown"
        
        try:
            # Parse time string
            if isinstance(time_str, str):
                hour = int(time_str.split(':')[0])
            else:
                hour = time_str.hour
            
            if 6 <= hour < 12:
                return "Morning (06:00-11:59)"
            elif 12 <= hour < 16:
                return "Afternoon (12:00-15:59)"
            elif 16 <= hour < 20:
                return "Evening Peak (16:00-19:59)"
            else:
                return "Night (20:00-05:59)"
        except:
            return "Unknown"
    
    def _enhanced_time_category(self, time_str: str) -> str:
        """Enhanced time categorization with more periods."""
        if pd.isna(time_str):
            return "Unknown"
        
        try:
            if isinstance(time_str, str):
                hour = int(time_str.split(':')[0])
            else:
                hour = time_str.hour
            
            if 6 <= hour < 10:
                return "Early Morning (06:00-09:59)"
            elif 10 <= hour < 12:
                return "Late Morning (10:00-11:59)"
            elif 12 <= hour < 16:
                return "Afternoon (12:00-15:59)"
            elif 16 <= hour < 20:
                return "Evening Peak (16:00-19:59)"
            elif 20 <= hour < 24:
                return "Night (20:00-23:59)"
            else:
                return "Overnight (00:00-05:59)"
        except:
            return "Unknown"
    
    def _generate_block(self, address: str) -> str:
        """Generate block from address."""
        if pd.isna(address) or not address:
            return "Unknown Block"
        
        try:
            address = str(address).strip().upper()
            
            # Extract street number and name
            parts = address.split()
            if parts and parts[0].isdigit():
                street_num = int(parts[0])
                street_name = ' '.join(parts[1:]).split(',')[0]
                
                # Generate block (round down to nearest 100)
                block_num = (street_num // 100) * 100
                return f"{street_name}, {block_num} Block"
            else:
                street_name = address.split(',')[0]
                return f"{street_name}, Unknown Block"
        except:
            return "Unknown Block"
    
    def _enhance_block_name(self, block: str) -> str:
        """Enhance block names with standard abbreviations."""
        if pd.isna(block):
            return "Unknown Block"
        
        # Standard street abbreviations
        abbreviations = {
            ' STREET,': ' ST,',
            ' AVENUE,': ' AVE,',
            ' BOULEVARD,': ' BLVD,',
            ' DRIVE,': ' DR,',
            ' COURT,': ' CT,',
            ' PLACE,': ' PL,'
        }
        
        for full, abbrev in abbreviations.items():
            block = block.replace(full, abbrev)
        
        return block
    
    def combine_data_sources(self, cad_df: pd.DataFrame, rms_df: pd.DataFrame) -> pd.DataFrame:
        """Combine CAD and RMS data with intelligent deduplication."""
        logger.info("🔗 Combining CAD and RMS data with deduplication")
        
        # Standardize column names across both sources
        cad_std = self._standardize_columns(cad_df, 'CAD')
        rms_std = self._standardize_columns(rms_df, 'RMS')
        
        # Combine dataframes
        combined_df = pd.concat([cad_std, rms_std], ignore_index=True, sort=False)
        
        # Remove duplicates using intelligent matching
        deduplicated_df = self._remove_duplicates(combined_df)
        
        # Add combined incident indicators
        deduplicated_df['has_cad_data'] = deduplicated_df['source'].str.contains('CAD')
        deduplicated_df['has_rms_data'] = deduplicated_df['source'].str.contains('RMS')
        
        self.stats['total_combined_records'] = len(deduplicated_df)
        self.stats['duplicates_removed'] = len(combined_df) - len(deduplicated_df)
        
        logger.info(f"✅ Combined data: {len(combined_df)} → {len(deduplicated_df)} records (removed {self.stats['duplicates_removed']} duplicates)")
        
        return deduplicated_df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicates using sophisticated matching logic."""
        logger.info("🎯 Removing duplicates with intelligent matching")
        
        # Sort by data quality score (keep higher quality records)
        df = df.sort_values(['data_quality_score', 'source'], ascending=[False, True])
        
        # Group by potential duplicate indicators
        duplicate_groups = df.groupby(['case_number', 'incident_date', 'address'])
        
        kept_records = []
        
        for name, group in duplicate_groups:
            if len(group) == 1:
                # No duplicates in this group
                kept_records.append(group.iloc[0])
            else:
                # Potential duplicates - apply intelligent logic
                best_record = self._select_best_record(group)
                kept_records.append(best_record)
        
        result_df = pd.DataFrame(kept_records)
        return result_df.reset_index(drop=True)
    
    def _select_best_record(self, group: pd.DataFrame) -> pd.Series:
        """Select the best record from a group of potential duplicates."""
        # Priority logic:
        # 1. Higher data quality score
        # 2. RMS over CAD (more complete narrative typically)
        # 3. More complete fields
        
        # First, check if we can match by case number exactly
        if len(group['case_number'].unique()) == 1:
            # Same case number - likely duplicate
            # Prefer RMS data if available
            rms_records = group[group['source'] == 'RMS']
            if not rms_records.empty:
                return rms_records.iloc[0]
            else:
                return group.iloc[0]  # Highest quality (already sorted)
        
        # Different case numbers but same incident details
        # This might be CAD call + RMS report
        # Create combined record if possible
        return self._merge_cad_rms_records(group)
    
    def _merge_cad_rms_records(self, group: pd.DataFrame) -> pd.Series:
        """Merge CAD and RMS records for the same incident."""
        # Take RMS data as base (more complete narrative)
        rms_records = group[group['source'] == 'RMS']
        cad_records = group[group['source'] == 'CAD']
        
        if not rms_records.empty:
            base_record = rms_records.iloc[0].copy()
            base_record['source'] = 'RMS+CAD'
            
            # Supplement with CAD data where RMS is missing
            if not cad_records.empty:
                cad_record = cad_records.iloc[0]
                
                # Fill missing response times from CAD
                if pd.isna(base_record.get('response_time')) and not pd.isna(cad_record.get('response_time')):
                    base_record['response_time'] = cad_record['response_time']
                
                # Fill missing time spent from CAD
                if pd.isna(base_record.get('time_spent')) and not pd.isna(cad_record.get('time_spent')):
                    base_record['time_spent'] = cad_record['time_spent']
            
            return base_record
        else:
            # No RMS data, use CAD
            return group.iloc[0]
    
    def add_weather_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add weather conditions using open source weather API."""
        if not self.config['weather_api']['enabled']:
            logger.info("⏭️  Weather API disabled, skipping weather data")
            return df
        
        logger.info("🌤️  Adding weather conditions")
        
        # Get unique dates for weather lookup
        unique_dates = df['incident_date'].dt.date.unique()
        weather_cache = {}
        
        for date in unique_dates:
            if pd.isna(date):
                continue
            
            try:
                weather_data = self._get_weather_for_date(date)
                weather_cache[date] = weather_data
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.warning(f"Failed to get weather for {date}: {e}")
                weather_cache[date] = {
                    'temperature': None,
                    'conditions': 'Unknown',
                    'precipitation': None,
                    'visibility': None
                }
        
        # Add weather columns
        df['weather_temperature'] = df['incident_date'].dt.date.map(
            lambda x: weather_cache.get(x, {}).get('temperature')
        )
        df['weather_conditions'] = df['incident_date'].dt.date.map(
            lambda x: weather_cache.get(x, {}).get('conditions', 'Unknown')
        )
        df['weather_precipitation'] = df['incident_date'].dt.date.map(
            lambda x: weather_cache.get(x, {}).get('precipitation')
        )
        
        self.stats['weather_records_added'] = len([w for w in weather_cache.values() if w.get('temperature')])
        logger.info(f"✅ Added weather data for {self.stats['weather_records_added']} dates")
        
        return df
    
    def _get_weather_for_date(self, date) -> Dict:
        """Get weather data for specific date using OpenWeatherMap API."""
        # This is a placeholder - you'll need to implement based on your chosen weather API
        # Options: OpenWeatherMap, WeatherAPI, Visual Crossing Weather
        
        # Example for OpenWeatherMap historical data:
        api_key = self.config['weather_api'].get('api_key')
        if not api_key:
            return {'temperature': None, 'conditions': 'Unknown', 'precipitation': None}
        
        # For historical weather, you might use Visual Crossing Weather (free tier available)
        # or implement a simple lookup table for common Hackensack weather patterns
        
        # Placeholder implementation
        return {
            'temperature': 72,  # Default temperature
            'conditions': 'Clear',
            'precipitation': 0.0,
            'visibility': 10
        }
    
    def export_for_powerbi(self, df: pd.DataFrame, output_path: Optional[str] = None) -> str:
        """Export processed data in Power BI-friendly format."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.base_path / "Processed_Data" / f"unified_incidents_{timestamp}.xlsx"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📊 Exporting data for Power BI: {output_path}")
        
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Main incidents table
            df.to_excel(writer, sheet_name='Incidents', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': [
                    'Total Records',
                    'CAD Records',
                    'RMS Records', 
                    'Combined Records',
                    'Duplicates Removed',
                    'Avg Data Quality Score',
                    'Weather Records Added',
                    'Processing Date'
                ],
                'Value': [
                    len(df),
                    self.stats['cad_records_processed'],
                    self.stats['rms_records_processed'],
                    self.stats['total_combined_records'],
                    self.stats['duplicates_removed'],
                    round(df['data_quality_score'].mean(), 2),
                    self.stats['weather_records_added'],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Processing_Summary', index=False)
            
            # Data quality breakdown
            quality_breakdown = df.groupby(['source', 'incident_type']).agg({
                'case_number': 'count',
                'data_quality_score': 'mean',
                'response_time': 'mean',
                'time_spent': 'mean'
            }).round(2)
            quality_breakdown.to_excel(writer, sheet_name='Quality_Analysis')
        
        logger.info(f"✅ Export complete: {output_path}")
        return str(output_path)
    
    def _generate_incident_hash(self, row: pd.Series) -> str:
        """Generate unique hash for incident deduplication."""
        # Create hash from key identifying fields
        key_fields = [
            str(row.get('case_number', '')),
            str(row.get('incident_date', '')),
            str(row.get('incident_time', '')),
            str(row.get('address', '')),
            str(row.get('incident_type', ''))
        ]
        
        combined_key = '|'.join(key_fields).upper()
        return hashlib.md5(combined_key.encode()).hexdigest()
    
    def _calculate_quality_score(self, row: pd.Series) -> float:
        """Calculate data quality score for a record."""
        score = 0
        max_score = 100
        
        # Required fields (40 points)
        required_fields = ['case_number', 'incident_date', 'incident_type', 'address']
        filled_required = sum(1 for field in required_fields if pd.notna(row.get(field)) and str(row.get(field)).strip())
        score += (filled_required / len(required_fields)) * 40
        
        # Important fields (30 points)
        important_fields = ['officer', 'grid', 'zone', 'incident_time']
        filled_important = sum(1 for field in important_fields if pd.notna(row.get(field)) and str(row.get(field)).strip())
        score += (filled_important / len(important_fields)) * 30
        
        # Optional fields (20 points)
        optional_fields = ['response_time', 'time_spent', 'narrative']
        filled_optional = sum(1 for field in optional_fields if pd.notna(row.get(field)))
        score += (filled_optional / len(optional_fields)) * 20
        
        # Data validity (10 points)
        validity_score = 10
        
        # Check for reasonable response times
        if pd.notna(row.get('response_time')):
            if row['response_time'] < 0 or row['response_time'] > 480:  # 8 hours max
                validity_score -= 3
        
        # Check for reasonable time spent
        if pd.notna(row.get('time_spent')):
            if row['time_spent'] < 0 or row['time_spent'] > 720:  # 12 hours max
                validity_score -= 3
        
        score += validity_score
        
        return round(min(score, max_score), 1)
    
    # Placeholder methods for data loading and cleaning
    def _load_data_file(self, file_path: str) -> pd.DataFrame:
        """Load data from file."""
        # Implementation based on your existing CAD/RMS loading logic
        pass
    
    def _clean_cad_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean CAD-specific data."""
        # Implementation based on your existing CAD cleaning logic
        pass
    
    def _clean_rms_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean RMS-specific data.""" 
        # Implementation based on your existing RMS cleaning logic
        pass
    
    def _standardize_addresses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize address formatting."""
        # Implementation based on your existing address cleaning logic
        pass
    
    def _map_officers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map officer names using assignment data."""
        # Implementation based on your existing officer mapping logic
        pass
    
    def _standardize_columns(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Standardize column names between CAD and RMS."""
        # Implementation to ensure consistent column naming
        pass
    
    def _load_officer_mappings(self) -> Dict:
        """Load officer mapping reference data."""
        # Load from your Assignment_Master_V2.xlsx or similar
        return {}
    
    def _load_zone_mappings(self) -> Dict:
        """Load zone/grid mapping reference data."""
        return {}

class WatchdogHandler(FileSystemEventHandler):
    """File system event handler for automated processing."""
    
    def __init__(self, processor: UnifiedDataProcessor):
        self.processor = processor
        
    def on_created(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            
            # Check if it's a data file we should process
            if file_path.suffix.lower() in ['.xlsx', '.xls', '.csv']:
                logger.info(f"📁 New file detected: {file_path.name}")
                
                # Wait for file to be completely written
                time.sleep(2)
                
                try:
                    # Determine file type and process
                    if 'CAD' in file_path.name.upper():
                        cad_df = self.processor.process_cad_data(str(file_path))
                        # Store processed CAD data for later combination
                        
                    elif 'RMS' in file_path.name.upper():
                        rms_df = self.processor.process_rms_data(str(file_path))
                        # Store processed RMS data for later combination
                        
                    logger.info(f"✅ Successfully processed: {file_path.name}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {file_path.name}: {e}")

def main():
    """Main execution function."""
    logger.info("🚀 Starting Unified Data Processing Pipeline")
    
    # Initialize processor
    processor = UnifiedDataProcessor()
    
    # Example usage
    # ca