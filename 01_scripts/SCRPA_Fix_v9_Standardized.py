# 🕒 2025-07-29-17-00-00
# SCRPA_Time_v2/Comprehensive_SCRPA_Fix_v8.5_Standardized
# Author: R. A. Carucci
# Purpose: Fixed version with proper PascalCase_With_Underscores column standardization to match Power BI requirements
# ✅ NEW in v8.5: Cycle calendar integration for temporal analysis and export naming

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from pathlib import Path
import logging
import time
import psutil
import os
from contextlib import contextmanager
import gc
import difflib

# Helper functions for header normalization and column coalescing
def to_snake(name: str) -> str:
    """Convert any string to lowercase snake_case format."""
    s = str(name)
    # Handle camelCase/PascalCase by inserting space before capital letters
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    # Handle numbers following letters
    s = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', s)
    # Replace any non-alphanumeric characters with spaces
    s = re.sub(r'[^0-9A-Za-z]+', ' ', s).strip()
    # Replace multiple spaces with single underscore
    s = re.sub(r'\s+', '_', s).lower()
    return s

def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame headers to lowercase snake_case format."""
    df = df.copy()
    df.columns = [to_snake(c) for c in df.columns]
    return df

def coalesce_cols(df: pd.DataFrame, *cols: str):
    """Coalesce multiple columns, filling nulls with values from subsequent columns."""
    out = pd.Series(pd.NA, index=df.index)
    for c in cols:
        if c in df.columns:
            out = out.fillna(df[c])
    return out

def extract_incident_types(all_incidents: str) -> str | None:
    """
    Extracts standardized crime categories from a combined incident string.
    FIXED: Uses standard hyphens to prevent character encoding issues.
    """
    if pd.isna(all_incidents) or not all_incidents:
        return None

    text = str(all_incidents).upper()
    found_types = []

    # Note: Order matters for specific burglary types before a general one.
    if "BURGLARY" in text:
        if "AUTO" in text or "VEHICLE" in text:
            found_types.append("Burglary - Auto")
        if "RESIDENCE" in text or "RESIDENTIAL" in text:
            found_types.append("Burglary - Residence")
        if "COMMERCIAL" in text:
            found_types.append("Burglary - Commercial")

    if any(keyword in text for keyword in ["MOTOR VEHICLE THEFT", "AUTO THEFT", "VEHICLE THEFT", "MV THEFT"]):
        found_types.append("Motor Vehicle Theft")
    if "ROBBERY" in text:
        found_types.append("Robbery")
    if "SEXUAL" in text:
        found_types.append("Sexual Offense")

    return ", ".join(found_types) if found_types else None


class ComprehensiveSCRPAFixV8_5:
    """
    ✅ **NEW in v8.5**: Cycle calendar integration for temporal analysis and export naming
    ✅ **NEW in v8.0**: Complete alignment with Power BI column standardization requirements
    ✅ All columns follow PascalCase_With_Underscores standard
    ✅ Matches the M Code transformation functions exactly
    ✅ Proper case-insensitive crime filtering 
    ✅ Enhanced time calculations with standardized column names
    ✅ Vehicle formatting consistent with M Code requirements
    ✅ Block calculation matching Power Query logic
    """
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)
            
        self.export_dirs = {
            'cad_exports': self.project_path / '05_Exports',
            'rms_exports': self.project_path / '05_Exports'
        }
        
        self.ref_dirs = {
            'call_types': self.project_path / '10_Refrence_Files' / 'CallType_Categories.xlsx',
            'zone_grid': self.project_path / '10_Refrence_Files' / 'zone_grid_master.xlsx',
            'cycle_calendar': self.project_path / '10_Refrence_Files' / '7Day_28Day_Cycle_20250414.xlsx'
        }
        
        self.call_type_ref = None
        self.zone_grid_ref = None
        self.cycle_calendar = None
        self.current_cycle = None
        self.current_date = None
        self.setup_logging()
        self.load_reference_data()
        
        # Load cycle calendar and get current cycle info
        self.cycle_calendar = self.load_cycle_calendar()
        self.current_cycle, self.current_date = self.get_current_cycle_info(self.cycle_calendar)

    def setup_logging(self):
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"comprehensive_scrpa_fix_v8_5_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.logger = logging.getLogger('ComprehensiveSCRPAFixV8_5')
        self.logger.setLevel(logging.INFO)
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        fh = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        # Also log to console
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        self.logger.info("=== Comprehensive SCRPA Fix V8.5 - Cycle Calendar Integration Version ===")

    @contextmanager
    def monitor_performance(self, operation_name):
        """Context manager for performance monitoring with memory tracking."""
        start_time = time.time()
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        self.logger.info(f"🚀 Starting {operation_name}... (Memory: {start_memory:.1f}MB)")
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            # Performance classification
            if duration < 1.0:
                speed_icon = "⚡"
                speed_desc = "Fast"
            elif duration < 5.0:
                speed_icon = "✅"
                speed_desc = "Good"
            elif duration < 15.0:
                speed_icon = "⚠️"
                speed_desc = "Slow"
            else:
                speed_icon = "🐌"
                speed_desc = "Very Slow"
            
            self.logger.info(f"{speed_icon} Completed {operation_name} ({speed_desc}):")
            self.logger.info(f"  ⏱️ Duration: {duration:.2f}s")
            self.logger.info(f"  💾 Memory: {end_memory:.1f}MB (Δ{memory_delta:+.1f}MB)")
            
            # Memory usage warnings
            if memory_delta > 100:
                self.logger.warning(f"  ⚠️ High memory usage increase: {memory_delta:.1f}MB")
            if end_memory > 500:
                self.logger.warning(f"  ⚠️ High total memory usage: {end_memory:.1f}MB")

    def optimize_dataframe_memory(self, df, operation_name="DataFrame"):
        """Optimize DataFrame memory usage by downcasting numeric types."""
        initial_memory = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
        
        # Downcast integer columns
        for col in df.select_dtypes(include=['int64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')
        
        # Downcast float columns
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Convert object columns to category if they have few unique values
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() < len(df) * 0.5:  # Less than 50% unique values
                df[col] = df[col].astype('category')
        
        final_memory = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
        memory_saved = initial_memory - final_memory
        
        if memory_saved > 0.1:  # Only log if significant savings
            self.logger.info(f"💾 {operation_name} memory optimized: {initial_memory:.1f}MB → {final_memory:.1f}MB (saved {memory_saved:.1f}MB)")
        
        return df

    def get_system_performance_summary(self):
        """Get current system performance metrics."""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'memory_rss_mb': memory_info.rss / 1024 / 1024,
            'memory_vms_mb': memory_info.vms / 1024 / 1024,
            'cpu_percent': process.cpu_percent(),
            'num_threads': process.num_threads(),
            'system_memory_percent': psutil.virtual_memory().percent,
            'system_cpu_percent': psutil.cpu_percent()
        }

    def performance_test_demo(self):
        """Demonstrate performance monitoring capabilities."""
        self.logger.info("🧪 Running Performance Monitoring Demo")
        
        with self.monitor_performance("Performance Test Demo"):
            # Test 1: DataFrame creation and manipulation
            with self.monitor_performance("Large DataFrame Creation"):
                test_df = pd.DataFrame({
                    'id': range(10000),
                    'value': np.random.randn(10000),
                    'category': np.random.choice(['A', 'B', 'C'], 10000),
                    'timestamp': pd.date_range('2024-01-01', periods=10000, freq='1min')
                })
                
            # Test 2: Memory optimization
            test_df = self.optimize_dataframe_memory(test_df, "Test DataFrame")
            
            # Test 3: Basic operations
            with self.monitor_performance("DataFrame Operations"):
                result = test_df.groupby('category')['value'].agg(['mean', 'std', 'count'])
                
            # Test 4: System performance summary
            perf_summary = self.get_system_performance_summary()
            self.logger.info(f"📊 System Performance Summary: {perf_summary}")
            
            # Force garbage collection
            gc.collect()
            
        self.logger.info("✅ Performance monitoring demo completed successfully")

    def process_large_dataset_chunked(self, file_path, chunk_size=1000):
        """Process large datasets in chunks to manage memory efficiently."""
        
        # Count total rows first
        with open(file_path, 'r', encoding='utf-8') as f:
            total_rows = sum(1 for line in f) - 1  # Subtract header
        
        if total_rows <= chunk_size:
            self.logger.info(f"📄 Dataset size ({total_rows} rows) within single chunk limit")
            return pd.read_csv(file_path)
        
        self.logger.info(f"📚 Processing large dataset: {total_rows} rows in chunks of {chunk_size}")
        
        chunk_results = []
        processed_rows = 0
        
        with self.monitor_performance(f"Chunked processing ({total_rows} rows)"):
            for i, chunk_df in enumerate(pd.read_csv(file_path, chunksize=chunk_size)):
                with self.monitor_performance(f"Chunk {i+1}"):
                    # Apply standard processing to chunk
                    processed_chunk = self.apply_standard_processing_to_chunk(chunk_df)
                    chunk_results.append(processed_chunk)
                    
                    processed_rows += len(chunk_df)
                    progress = (processed_rows / total_rows) * 100
                    self.logger.info(f"📊 Progress: {processed_rows:,}/{total_rows:,} rows ({progress:.1f}%)")
            
            # Combine all chunks
            self.logger.info("🔗 Combining processed chunks...")
            final_df = pd.concat(chunk_results, ignore_index=True)
            
            # Optimize final combined dataset
            final_df = self.optimize_dataframe_memory(final_df, "Combined Chunked Dataset")
            
            # Force garbage collection
            gc.collect()
            
        self.logger.info(f"✅ Large dataset processing complete: {len(final_df):,} total records")
        return final_df

    def apply_standard_processing_to_chunk(self, chunk_df):
        """Apply standard SCRPA processing to a data chunk."""
        # Apply the same processing steps as normal, but to chunk
        # This includes header normalization, data cleaning, etc.
        
        # Normalize headers
        chunk_df = normalize_headers(chunk_df)
        
        # Apply text cleaning to text columns
        text_columns = chunk_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            if hasattr(self, 'clean_text_comprehensive'):
                chunk_df[col] = chunk_df[col].apply(self.clean_text_comprehensive)
            else:
                # Fallback basic text cleaning
                chunk_df[col] = chunk_df[col].astype(str).str.strip()
        
        # Apply memory optimization to chunk
        chunk_df = self.optimize_dataframe_memory(chunk_df, "Processing Chunk")
        
        return chunk_df

    def process_large_excel_chunked(self, file_path, chunk_size=1000, sheet_name=0):
        """Process large Excel files in chunks (converts to CSV first for chunking)."""
        
        self.logger.info(f"📊 Loading Excel file for chunked processing: {file_path}")
        
        with self.monitor_performance("Excel to DataFrame conversion"):
            # Load full Excel file first (this is unavoidable for Excel)
            full_df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
            total_rows = len(full_df)
        
        if total_rows <= chunk_size:
            self.logger.info(f"📄 Excel dataset size ({total_rows} rows) within single chunk limit")
            return self.apply_standard_processing_to_chunk(full_df)
        
        self.logger.info(f"📚 Processing large Excel dataset: {total_rows} rows in chunks of {chunk_size}")
        
        chunk_results = []
        processed_rows = 0
        
        with self.monitor_performance(f"Chunked Excel processing ({total_rows} rows)"):
            # Process DataFrame in chunks
            for i in range(0, total_rows, chunk_size):
                with self.monitor_performance(f"Excel Chunk {i//chunk_size + 1}"):
                    end_idx = min(i + chunk_size, total_rows)
                    chunk_df = full_df.iloc[i:end_idx].copy()
                    
                    # Apply standard processing to chunk
                    processed_chunk = self.apply_standard_processing_to_chunk(chunk_df)
                    chunk_results.append(processed_chunk)
                    
                    processed_rows += len(chunk_df)
                    progress = (processed_rows / total_rows) * 100
                    self.logger.info(f"📊 Progress: {processed_rows:,}/{total_rows:,} rows ({progress:.1f}%)")
            
            # Clear original dataframe from memory
            del full_df
            gc.collect()
            
            # Combine all chunks
            self.logger.info("🔗 Combining processed Excel chunks...")
            final_df = pd.concat(chunk_results, ignore_index=True)
            
            # Optimize final combined dataset
            final_df = self.optimize_dataframe_memory(final_df, "Combined Excel Dataset")
            
            # Force garbage collection
            gc.collect()
            
        self.logger.info(f"✅ Large Excel dataset processing complete: {len(final_df):,} total records")
        return final_df

    def test_chunked_processing(self, test_size=5000, chunk_size=1000):
        """Test chunked processing functionality with synthetic data."""
        self.logger.info("🧪 Testing chunked processing functionality")
        
        # Create test CSV file
        temp_dir = self.project_path / '03_output' / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)
        test_file = temp_dir / f'test_large_dataset_{test_size}_rows.csv'
        
        with self.monitor_performance("Creating test dataset"):
            # Generate synthetic test data
            test_data = {
                'id': range(1, test_size + 1),
                'incident_number': [f'INC{i:06d}' for i in range(1, test_size + 1)],
                'date_occurred': pd.date_range('2024-01-01', periods=test_size, freq='1h'),
                'location': [f'{100 + i % 900} Main St' for i in range(test_size)],
                'description': [f'Test incident description {i}' for i in range(test_size)],
                'category': np.random.choice(['Crime', 'Traffic', 'Medical', 'Fire'], test_size),
                'priority': np.random.choice(['High', 'Medium', 'Low'], test_size),
                'status': np.random.choice(['Open', 'Closed', 'Pending'], test_size)
            }
            
            test_df = pd.DataFrame(test_data)
            test_df.to_csv(test_file, index=False)
            self.logger.info(f"📁 Created test file: {test_file} ({test_size:,} rows)")
        
        try:
            # Test chunked processing
            with self.monitor_performance("Chunked processing test"):
                result_df = self.process_large_dataset_chunked(test_file, chunk_size=chunk_size)
                
            # Validate results
            self.logger.info("✅ Chunked processing test validation:")
            self.logger.info(f"  📊 Original rows: {test_size:,}")
            self.logger.info(f"  📊 Processed rows: {len(result_df):,}")
            self.logger.info(f"  📊 Columns: {len(result_df.columns)}")
            self.logger.info(f"  📊 Memory usage: {result_df.memory_usage(deep=True).sum() / 1024 / 1024:.1f}MB")
            
            # Check data integrity
            if len(result_df) == test_size:
                self.logger.info("✅ Data integrity check PASSED")
            else:
                self.logger.error("❌ Data integrity check FAILED")
                
        finally:
            # Cleanup test file
            if test_file.exists():
                test_file.unlink()
                self.logger.info(f"🗑️ Cleaned up test file: {test_file.name}")
        
        self.logger.info("✅ Chunked processing test completed")

    def write_large_csv_efficiently(self, df, file_path, chunk_size=5000):
        """Write large DataFrame to CSV in chunks to manage memory."""
        
        total_rows = len(df)
        
        if total_rows <= chunk_size:
            self.logger.info(f"💾 Writing standard CSV: {total_rows:,} rows")
            df.to_csv(file_path, index=False)
            return
        
        self.logger.info(f"💾 Writing large CSV: {total_rows:,} rows in chunks of {chunk_size:,}")
        
        with self.monitor_performance(f"Large CSV write ({total_rows:,} rows)"):
            # Write header first
            df.head(0).to_csv(file_path, index=False)
            
            # Write data in chunks
            for i in range(0, total_rows, chunk_size):
                chunk = df.iloc[i:i+chunk_size]
                chunk.to_csv(file_path, mode='a', header=False, index=False)
                
                progress = min(i + chunk_size, total_rows)
                progress_pct = (progress / total_rows) * 100
                self.logger.info(f"📝 Write progress: {progress:,}/{total_rows:,} rows ({progress_pct:.1f}%)")
        
        self.logger.info(f"✅ Large CSV write complete: {file_path}")

    def write_large_excel_efficiently(self, df, file_path, chunk_size=5000, sheet_name='Data'):
        """Write large DataFrame to Excel in chunks to manage memory."""
        
        total_rows = len(df)
        
        if total_rows <= chunk_size:
            self.logger.info(f"📊 Writing standard Excel: {total_rows:,} rows")
            df.to_excel(file_path, index=False, sheet_name=sheet_name, engine='openpyxl')
            return
        
        self.logger.info(f"📊 Writing large Excel: {total_rows:,} rows in chunks of {chunk_size:,}")
        
        with self.monitor_performance(f"Large Excel write ({total_rows:,} rows)"):
            from openpyxl import Workbook
            from openpyxl.utils.dataframe import dataframe_to_rows
            
            # Create workbook and worksheet
            wb = Workbook()
            ws = wb.active
            ws.title = sheet_name
            
            # Write header
            header_written = False
            
            # Write data in chunks
            for i in range(0, total_rows, chunk_size):
                chunk = df.iloc[i:i+chunk_size]
                
                # Convert chunk to rows
                for r_idx, row in enumerate(dataframe_to_rows(chunk, index=False, header=not header_written)):
                    ws.append(row)
                
                header_written = True
                
                progress = min(i + chunk_size, total_rows)
                progress_pct = (progress / total_rows) * 100
                self.logger.info(f"📝 Excel write progress: {progress:,}/{total_rows:,} rows ({progress_pct:.1f}%)")
            
            # Save workbook
            wb.save(file_path)
        
        self.logger.info(f"✅ Large Excel write complete: {file_path}")

    def test_large_file_writing(self, test_size=10000, chunk_size=2500):
        """Test large file writing functionality with synthetic data."""
        self.logger.info("🧪 Testing large file writing functionality")
        
        # Create test directory
        temp_dir = self.project_path / '03_output' / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        with self.monitor_performance("Creating large test dataset"):
            # Generate synthetic test data
            test_data = {
                'record_id': range(1, test_size + 1),
                'incident_number': [f'INC{i:08d}' for i in range(1, test_size + 1)],
                'date_time': pd.date_range('2024-01-01', periods=test_size, freq='30min'),
                'location_address': [f'{100 + i % 9000} {["Main", "Oak", "Pine", "Cedar", "Elm"][i % 5]} St' for i in range(test_size)],
                'incident_description': [f'Test incident description {i} - Lorem ipsum dolor sit amet' for i in range(test_size)],
                'category': np.random.choice(['Crime', 'Traffic', 'Medical', 'Fire', 'Service'], test_size),
                'priority_level': np.random.choice(['High', 'Medium', 'Low', 'Routine'], test_size),
                'status': np.random.choice(['Open', 'Closed', 'Pending', 'In Progress'], test_size),
                'officer_badge': [f'BADGE{1000 + i % 500}' for i in range(test_size)],
                'response_time_minutes': np.random.randint(1, 60, test_size)
            }
            
            large_test_df = pd.DataFrame(test_data)
            self.logger.info(f"📊 Created large test dataset: {test_size:,} rows, {len(large_test_df.columns)} columns")
            self.logger.info(f"📊 Memory usage: {large_test_df.memory_usage(deep=True).sum() / 1024 / 1024:.1f}MB")
        
        try:
            # Test large CSV writing
            csv_file = temp_dir / f'test_large_export_{test_size}_rows.csv'
            self.write_large_csv_efficiently(large_test_df, csv_file, chunk_size=chunk_size)
            
            # Verify CSV file
            if csv_file.exists():
                file_size_mb = csv_file.stat().st_size / 1024 / 1024
                self.logger.info(f"✅ CSV file created: {file_size_mb:.1f}MB")
                
                # Quick verification - read first few rows
                verify_df = pd.read_csv(csv_file, nrows=5)
                self.logger.info(f"✅ CSV verification: {len(verify_df)} sample rows read successfully")
            
            # Test large Excel writing (smaller test due to Excel overhead)
            if test_size <= 5000:  # Excel is more memory intensive
                excel_file = temp_dir / f'test_large_export_{test_size}_rows.xlsx'
                self.write_large_excel_efficiently(large_test_df, excel_file, chunk_size=chunk_size)
                
                if excel_file.exists():
                    file_size_mb = excel_file.stat().st_size / 1024 / 1024
                    self.logger.info(f"✅ Excel file created: {file_size_mb:.1f}MB")
            else:
                self.logger.info("⏭️ Skipping Excel test for large dataset (memory optimization)")
                
        finally:
            # Cleanup test files
            for test_file in temp_dir.glob(f'test_large_export_{test_size}_rows.*'):
                if test_file.exists():
                    test_file.unlink()
                    self.logger.info(f"🗑️ Cleaned up test file: {test_file.name}")
        
        self.logger.info("✅ Large file writing test completed")

    def load_reference_data(self):
        """Load reference data for call type categorization and zone/grid mapping."""
        # Load call type reference with incident column forced to string type and preserve Excel's Response_Type and Category_Type columns
        try:
            if self.ref_dirs['call_types'].exists():
                # Load with incident column forced to string type and preserve Excel's original column names
                self.call_type_ref = pd.read_excel(
                    self.ref_dirs['call_types'], 
                    dtype={"Incident": str, "Response Type": str, "Category Type": str}
                )
                self.logger.info(f"Loaded call type reference: {len(self.call_type_ref)} records")
                self.logger.info(f"Reference file columns: {list(self.call_type_ref.columns)}")
                
                # Ensure incident column is properly formatted as string
                if 'Incident' in self.call_type_ref.columns:
                    self.call_type_ref['Incident'] = self.call_type_ref['Incident'].astype(str)
                    self.logger.info(f"Incident column forced to string type with {len(self.call_type_ref)} records")
            else:
                self.logger.warning("Call type reference file not found - using fallback categorization")
                self.call_type_ref = None
        except Exception as e:
            self.logger.error(f"Could not load call type reference: {e}")
            self.call_type_ref = None
            
        # Load zone/grid reference
        try:
            if self.ref_dirs['zone_grid'].exists():
                self.zone_grid_ref = pd.read_excel(self.ref_dirs['zone_grid'])
                self.logger.info(f"Loaded zone/grid reference: {len(self.zone_grid_ref)} records")
                # Standardize column names in reference data
                if not self.zone_grid_ref.empty:
                    self.zone_grid_ref.columns = [to_snake(col) for col in self.zone_grid_ref.columns]
            else:
                self.logger.warning("Zone/grid reference file not found - no backfill available")
                self.zone_grid_ref = None
        except Exception as e:
            self.logger.error(f"Could not load zone/grid reference: {e}")
            self.zone_grid_ref = None

    def load_cycle_calendar(self):
        """Load Excel file from 10_Refrence_Files/7Day_28Day_Cycle_20250414.xlsx"""
        try:
            if self.ref_dirs['cycle_calendar'].exists():
                cycle_df = pd.read_excel(self.ref_dirs['cycle_calendar'])
                self.logger.info(f"Loaded cycle calendar: {len(cycle_df)} records")
                self.logger.info(f"Cycle calendar columns: {list(cycle_df.columns)}")
                return cycle_df
            else:
                self.logger.warning("Cycle calendar file not found - cycle features will be disabled")
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Could not load cycle calendar: {e}")
            return pd.DataFrame()

    def get_cycle_for_date(self, incident_date, cycle_df):
        """Return cycle name (like "C08W31") for any date"""
        if cycle_df.empty or pd.isna(incident_date):
            return None
            
        try:
            # Convert incident_date to datetime if it's not already
            if isinstance(incident_date, str):
                incident_date = pd.to_datetime(incident_date, errors='coerce')
            
            if pd.isna(incident_date):
                return None
            
            # Convert to date for comparison
            incident_date = incident_date.date() if hasattr(incident_date, 'date') else incident_date
            
            # Check if date falls within any 7-day cycle
            for _, row in cycle_df.iterrows():
                start_date = pd.to_datetime(row['7_Day_Start']).date()
                end_date = pd.to_datetime(row['7_Day_End']).date()
                
                if start_date <= incident_date <= end_date:
                    return row['Report_Name']
            
            return None
        except Exception as e:
            self.logger.warning(f"Error getting cycle for date {incident_date}: {e}")
            return None

    def get_current_cycle_info(self, cycle_df):
        """Get current cycle for export naming"""
        if cycle_df.empty:
            return None, None
            
        try:
            today = datetime.now().date()
            
            # Find current cycle
            for _, row in cycle_df.iterrows():
                start_date = pd.to_datetime(row['7_Day_Start']).date()
                end_date = pd.to_datetime(row['7_Day_End']).date()
                
                if start_date <= today <= end_date:
                    current_cycle = row['Report_Name']
                    current_date = today.strftime('%Y%m%d')
                    self.logger.info(f"Current cycle: {current_cycle}, Date: {current_date}")
                    return current_cycle, current_date
            
            # If not in current cycle, find the most recent past cycle
            past_cycles = []
            for _, row in cycle_df.iterrows():
                end_date = pd.to_datetime(row['7_Day_End']).date()
                if end_date <= today:
                    past_cycles.append((end_date, row['Report_Name']))
            
            if past_cycles:
                # Get the most recent past cycle
                most_recent = max(past_cycles, key=lambda x: x[0])
                current_cycle = most_recent[1]
                current_date = today.strftime('%Y%m%d')
                self.logger.info(f"Using most recent past cycle: {current_cycle}, Date: {current_date}")
                return current_cycle, current_date
            
            return None, None
        except Exception as e:
            self.logger.error(f"Error getting current cycle info: {e}")
            return None, None

    def convert_to_lowercase_with_underscores(self, column_name: str) -> str:
        """
        Convert any column name to lowercase_with_underscores standard.
        This matches the critical path correction requirements.
        FIXED: Now properly handles numbers in column names.
        """
        # Clean the input
        name = str(column_name).strip()
        
        # Remove common prefixes
        name = re.sub(r'^(CAD_|RMS_|cad_|rms_)', '', name, flags=re.IGNORECASE)
        
        # Handle specific cases first
        special_cases = {
            'PDZone': 'pd_zone',
            'CADNotes': 'cad_notes',
            'ReportNumberNew': 'report_number_new',
            'vehicle_1': 'vehicle_1',
            'vehicle_2': 'vehicle_2',
            'vehicle_1_and_vehicle_2': 'vehicle_1_and_vehicle_2'
        }
        
        if name in special_cases:
            return special_cases[name]
        
        # Handle camelCase and PascalCase by inserting spaces before capitals
        # But not at the beginning of the string
        name = re.sub(r'(?<!^)([a-z])([A-Z])', r'\1 \2', name)
        
        # Handle sequences of capitals followed by lowercase (like 'CADNotes' -> 'CAD Notes')
        name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', name)
        
        # Replace various separators with spaces
        name = re.sub(r'[_\-\s]+', ' ', name)
        
        # Split by spaces and convert to lowercase
        words = [word.lower() for word in name.split() if word]
        
        # Join with underscores
        return '_'.join(words)

    def map_call_type(self, incident_value):
        """
        Enhanced CAD CallType mapping with response classification.
        
        Implements the updated mapping logic:
        1. Exact case-insensitive lookup in CallType_Categories.xlsx
        2. Partial match fallback (incident value contained in reference or vice versa)
        3. Keyword fallback with Response_Type and Category_Type set to same value
        
        Args:
            incident_value: Raw incident value from CAD data
            
        Returns:
            tuple: (response_type, category_type)
        """
        if pd.isna(incident_value) or not incident_value:
            return None, None
            
        # Clean input for consistent matching
        incident_clean = str(incident_value).strip().upper()
        
        # Step 1: Try exact case-insensitive lookup in reference data
        if self.call_type_ref is not None and not self.call_type_ref.empty:
            try:
                # Ensure 'Incident' column exists and force to string type
                if 'Incident' in self.call_type_ref.columns:
                    # Force incident column to string type for consistent matching
                    ref_incidents = self.call_type_ref['Incident'].astype(str).str.strip().str.upper()
                    
                    # Exact case-insensitive match lookup
                    exact_match = ref_incidents == incident_clean
                    if exact_match.any():
                        match_idx = exact_match.idxmax()
                        response_type = self.call_type_ref.loc[match_idx, 'Response Type']
                        category_type = self.call_type_ref.loc[match_idx, 'Category Type']
                        return response_type, category_type
                    
                    # Step 2: Partial match fallback - check if incident_clean is contained in any reference incident
                    partial_matches = ref_incidents.str.contains(incident_clean, case=False, na=False)
                    if partial_matches.any():
                        match_idx = partial_matches.idxmax()
                        response_type = self.call_type_ref.loc[match_idx, 'Response Type']
                        category_type = self.call_type_ref.loc[match_idx, 'Category Type']
                        return response_type, category_type
                    
                    # Step 3: Reverse partial fallback - check if any reference incident is contained in incident_clean
                    for _, row in self.call_type_ref.iterrows():
                        ref_incident = str(row['Incident']).strip().upper()
                        if ref_incident and ref_incident in incident_clean:
                            response_type = row['Response Type']
                            category_type = row['Category Type']
                            return response_type, category_type
                            
            except Exception as e:
                self.logger.warning(f"Error in reference data lookup: {e}")
        
        # Step 4: Keyword fallback categorization
        # Both Response_Type and Category_Type are set to the same value for each category
        
        # Define keyword patterns for category classification (ordered by priority)
        # Crime should be checked before Alarm to avoid "BURGLARY AUTO" being classified as Alarm
        keyword_patterns = {
            'Crime': ['THEFT', 'BURGLARY', 'ROBBERY', 'LARCENY', 'ASSAULT', 'BATTERY', 'FRAUD'],
            'Traffic': ['TRAFFIC', 'MOTOR', 'VEHICLE', 'ACCIDENT', 'COLLISION', 'DUI', 'DWI', 'SPEEDING'],
            'Medical': ['MEDICAL', 'EMS', 'AMBULANCE', 'HEART', 'STROKE', 'SEIZURE', 'OVERDOSE'],
            'Fire': ['FIRE', 'SMOKE', 'BURNING', 'EXPLOSION', 'HAZMAT'],
            'Disturbance': ['DOMESTIC', 'DISTURBANCE', 'FIGHT', 'NOISE', 'DISPUTE', 'ARGUMENT'],
            'Alarm': ['ALARM', 'SECURITY', 'BURGLAR', 'FIRE ALARM', 'PANIC']
        }
        
        # Check each category's keywords
        for category, keywords in keyword_patterns.items():
            if any(keyword in incident_clean for keyword in keywords):
                # Both Response_Type and Category_Type are set to the same value
                return category, category
        else:
            # Default category if no keywords match
            # Response_Type = original incident value, Category_Type = 'Other'
            return incident_value, 'Other'

    def format_time_spent_minutes(self, minutes):
        """Format time spent minutes to '0 Hrs. 00 Mins' format."""
        if pd.isna(minutes) or minutes is None:
            return None
        try:
            total_minutes = int(float(minutes))
            if total_minutes < 0:
                return None
            hours = total_minutes // 60
            mins = total_minutes % 60
            return f"{hours} Hrs. {mins:02d} Mins"
        except:
            return None

    def format_time_response_minutes(self, minutes):
        """Format time response minutes to '00 Mins. 00 Secs' format."""
        if pd.isna(minutes) or minutes is None:
            return None
        try:
            total_minutes = float(minutes)
            if total_minutes < 0:
                return None
            mins = int(total_minutes)
            secs = int((total_minutes - mins) * 60)
            return f"{mins:02d} Mins. {secs:02d} Secs"
        except:
            return None

    def clean_how_reported_911(self, how_reported):
        """Fix '9-1-1' date issue in how_reported field."""
        if pd.isna(how_reported):
            return None
        
        text = str(how_reported).strip()
        
        # Handle various date formats that might be incorrectly applied to "9-1-1"
        # Common patterns when Excel converts "9-1-1" to dates:
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD format
            r'^\d{1,2}/\d{1,2}/\d{4}',  # M/D/YYYY or MM/DD/YYYY format
            r'^\d{1,2}-\d{1,2}-\d{4}',  # M-D-YYYY or MM-DD-YYYY format
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO datetime format
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # YYYY-MM-DD HH:MM:SS format
        ]
        
        # Check if the value matches any date pattern
        for pattern in date_patterns:
            if re.match(pattern, text):
                return "9-1-1"
        
        # Also check for specific date values that commonly result from "9-1-1" conversion
        # September 1, 2001 (9/1/2001) is a common misinterpretation
        date_values = [
            '2001-09-01', '2001-09-01 00:00:00', '09/01/2001', '9/1/2001', '2001-09-01T00:00:00',
            '2001-09-01 00:00:00.000000', '2001-09-01T00:00:00.000000', '2001-09-01 00:00:00.000000000',
            '2025-09-01', '2025-09-01 00:00:00', '09/01/2025', '9/1/2025', '2025-09-01T00:00:00',
            '2025-09-01 00:00:00.000000', '2025-09-01T00:00:00.000000', '2025-09-01 00:00:00.000000000',
            # Additional patterns that might be missed
            '9/1/2001', '09/01/2001', '2001-09-01', '2001-9-1', '9-1-2001',
            '9/1/2025', '09/01/2025', '2025-09-01', '2025-9-1', '9-1-2025'
        ]
        if text in date_values:
            return "9-1-1"
        
        # Check for partial matches with date patterns
        if any(pattern in text for pattern in ['2001-09-01', '09/01/2001', '9/1/2001', '2025-09-01', '09/01/2025', '9/1/2025']):
            return "9-1-1"
        
        # Enhanced check for any date-like pattern that could be "9-1-1"
        # This catches cases where Excel might format it differently
        if re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{4}', text):
            # Check if it's September 1st of any year (common misinterpretation of 9-1-1)
            try:
                parts = re.split(r'[/-]', text)
                if len(parts) == 3:
                    month, day, year = parts
                    if (month == '9' or month == '09') and (day == '1' or day == '01'):
                        return "9-1-1"
            except:
                pass
        
        # If the original value is already "9-1-1" or similar, return as is
        if text.lower() in ['9-1-1', '911', '9-1-1', '9/1/1', 'nine-one-one']:
            return "9-1-1"
        
        return text

    def extract_username_timestamp(self, cad_notes):
        """Extract username and timestamp from CAD notes and return cleaned notes."""
        if pd.isna(cad_notes):
            return None, None, None
            
        text = str(cad_notes)
        username = None
        timestamp = None
        
        # Look for username pattern (usually at start)
        username_match = re.search(r'^([A-Z]+\d*|[a-zA-Z]+\.[a-zA-Z]+)', text)
        if username_match:
            username = username_match.group(1)
        
        # Look for timestamp patterns
        timestamp_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [AP]M',
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}'
        ]
        
        for pattern in timestamp_patterns:
            timestamp_match = re.search(pattern, text)
            if timestamp_match:
                timestamp = timestamp_match.group(0)
                break
        
        # Clean the notes by removing username/timestamp patterns
        cleaned = text
        if username:
            cleaned = re.sub(f'^{re.escape(username)}[\\s:]*', '', cleaned)
        if timestamp:
            cleaned = re.sub(re.escape(timestamp), '', cleaned)
        
        # Additional cleaning
        cleaned = re.sub(r'[\r\n\t]+', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned) 
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else None, username, timestamp

    def parse_cad_notes(self, raw: str) -> pd.Series:
        """
        Parse CAD notes to extract username, timestamp, and cleaned text.
        Enhanced version with better pattern matching and cleaning.
        
        Args:
            raw: Raw CAD notes string
            
        Returns:
            pd.Series with columns: [CAD_Username, CAD_Timestamp, CAD_Notes_Cleaned]
        """
        if pd.isna(raw) or not raw:
            return pd.Series([None, None, None], index=['CAD_Username', 'CAD_Timestamp', 'CAD_Notes_Cleaned'])
        
        text = str(raw).strip()
        username = None
        timestamp = None
        cleaned = None
        
        # Enhanced username patterns to match examples like 'kiselow_g - 1/4/2025 11:00:23 AM'
        username_patterns = [
            r'^([a-zA-Z0-9_]+(?:_[a-zA-Z0-9]+)?(?:\s*-\s*)?)',  # kiselow_g, Gervasi_J, intake_fa
            r'^([A-Z]+\d*)',  # All caps with optional digits
            r'^([a-zA-Z]+\.[a-zA-Z]+)',  # First.Last format
        ]
        
        for pattern in username_patterns:
            username_match = re.search(pattern, text)
            if username_match:
                username = username_match.group(1)
                break
        
        # Enhanced timestamp patterns to match examples like '1/4/2025 11:00:23 AM'
        timestamp_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} (?:AM|PM|am|pm)',  # 1/14/2025 3:47:59 PM
            r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2} (?:AM|PM|am|pm)',  # Date with time (no seconds)
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # ISO format
            r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}',  # Date with time (no seconds, no AM/PM)
        ]
        
        for pattern in timestamp_patterns:
            timestamp_match = re.search(pattern, text)
            if timestamp_match:
                timestamp = timestamp_match.group(0)
                # Standardize timestamp format to MM/DD/YYYY HH:MM:SS
                try:
                    # Parse the timestamp and reformat it
                    if 'AM' in timestamp or 'PM' in timestamp:
                        # Handle 12-hour format - try different formats
                        try:
                            parsed_time = pd.to_datetime(timestamp, format='%m/%d/%Y %I:%M:%S %p')
                        except:
                            # Try without seconds
                            parsed_time = pd.to_datetime(timestamp, format='%m/%d/%Y %I:%M %p')
                    else:
                        # Handle 24-hour format
                        parsed_time = pd.to_datetime(timestamp)
                    
                    timestamp = parsed_time.strftime('%m/%d/%Y %H:%M:%S')
                except:
                    # If parsing fails, keep original format
                    pass
                break
        
        # Clean the notes by removing username, timestamp, and other metadata
        cleaned = text
        
        # Remove username
        if username:
            # Remove username with various separators
            username_patterns_to_remove = [
                f'^{re.escape(username)}\\s*',  # Start of line
                f'^{re.escape(username)}[\\s-]+',  # With dash separator
                f'^{re.escape(username)}[\\s:]+',  # With colon separator
            ]
            for pattern in username_patterns_to_remove:
                cleaned = re.sub(pattern, '', cleaned)
        
        # Remove timestamp
        if timestamp:
            # Try both original and standardized formats
            timestamp_variants = [timestamp]
            try:
                # Add original format if different
                original_match = re.search(r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [AP]M', text)
                if original_match and original_match.group(0) != timestamp:
                    timestamp_variants.append(original_match.group(0))
            except:
                pass
            
            for ts in timestamp_variants:
                cleaned = re.sub(re.escape(ts), '', cleaned)
            
            # Also remove any remaining AM/PM patterns that might be left
            cleaned = re.sub(r'\s+[AP]M\s+', ' ', cleaned)
            cleaned = re.sub(r'^[AP]M\s+', '', cleaned)
        
        # Remove header patterns, stray date fragments, and clean up
        cleaned = re.sub(r'^[\\s-]+', '', cleaned)  # Remove leading dashes/spaces
        cleaned = re.sub(r'[\r\n\t]+', ' ', cleaned)  # Replace line breaks with spaces
        cleaned = re.sub(r'\\s+', ' ', cleaned)  # Normalize whitespace
        cleaned = cleaned.strip()
        
        # Only keep cleaned text if it's not empty and not just whitespace
        if not cleaned or cleaned.isspace():
            cleaned = None
        
        return pd.Series([username, timestamp, cleaned], index=['CAD_Username', 'CAD_Timestamp', 'CAD_Notes_Cleaned'])

    def validate_hackensack_address(self, address):
        """Validate and fix addresses to ensure they're in Hackensack, NJ."""
        if pd.isna(address):
            return None
            
        addr_str = str(address).strip()
        
        # Remove any Jersey City addresses - these are errors
        if 'JERSEY CITY' in addr_str.upper() or 'JC,' in addr_str.upper():
            self.logger.warning(f"Removing Jersey City address: {addr_str}")
            return None
            
        # Ensure Hackensack addresses are properly formatted
        if 'HACKENSACK' not in addr_str.upper():
            # Add Hackensack, NJ if missing
            if not addr_str.endswith(', NJ') and not addr_str.endswith(', NJ, 07601'):
                addr_str = f"{addr_str}, Hackensack, NJ, 07601"
            else:
                addr_str = addr_str.replace(', NJ', ', Hackensack, NJ')
                
        return addr_str

    def backfill_grid_post(self, address, current_grid, current_post):
        """Backfill missing grid and post values using zone_grid_master reference."""
        # If both grid and post exist, return as is
        if pd.notna(current_grid) and pd.notna(current_post):
            return current_grid, current_post
            
        # If no reference data available, return current values
        if self.zone_grid_ref is None or self.zone_grid_ref.empty:
            return current_grid, current_post
            
        if pd.isna(address):
            return current_grid, current_post
            
        try:
            # Clean address for matching
            clean_addr = str(address).replace(', Hackensack, NJ, 07601', '').strip()
            
            # Try to find a match in the reference data
            # Assuming the reference has columns like 'address', 'grid', 'post' or similar
            ref_cols = self.zone_grid_ref.columns.tolist()
            
            # Look for address-like column
            address_col = None
            for col in ref_cols:
                if any(term in col.lower() for term in ['address', 'location', 'street']):
                    address_col = col
                    break
                    
            if address_col:
                # Try exact match first
                match = self.zone_grid_ref[self.zone_grid_ref[address_col].str.contains(clean_addr, case=False, na=False)]
                
                if not match.empty:
                    row = match.iloc[0]
                    
                    # Get grid if missing
                    if pd.isna(current_grid):
                        for col in ref_cols:
                            if 'grid' in col.lower():
                                current_grid = row.get(col)
                                break
                                
                    # Get post if missing  
                    if pd.isna(current_post):
                        for col in ref_cols:
                            if any(term in col.lower() for term in ['post', 'zone', 'district']):
                                current_post = row.get(col)
                                break
                                
        except Exception as e:
            self.logger.warning(f"Error in grid/post backfill: {e}")
            
        return current_grid, current_post

    def format_incident_time(self, time_val):
        """Format incident time to HH:MM format."""
        if pd.isna(time_val):
            return None
            
        try:
            if isinstance(time_val, pd.Timedelta):
                total_seconds = time_val.total_seconds()
                hours = int(total_seconds // 3600) % 24
                minutes = int((total_seconds % 3600) // 60)
                return f"{hours:02d}:{minutes:02d}"
            elif hasattr(time_val, 'hour') and hasattr(time_val, 'minute'):
                return f"{time_val.hour:02d}:{time_val.minute:02d}"
            else:
                # Try to parse as time
                parsed_time = pd.to_datetime(time_val, errors='coerce').time()
                if parsed_time:
                    return f"{parsed_time.hour:02d}:{parsed_time.minute:02d}"
        except:
            pass
            
        return None

    def standardize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize data types for consistent CSV export output"""
        
        # Force object dtype for string cols, convert empties to None
        string_cols = ['case_number','incident_date','incident_time','all_incidents',
                       'vehicle_1','vehicle_2','vehicle_1_and_vehicle_2','narrative',
                       'location','block','response_type','category_type','period',
                       'season','day_of_week','day_type','cycle_name', 'incident_type']
        for col in string_cols:
            if col in df.columns:
                # Force object dtype and handle NaN values properly
                df[col] = df[col].astype('object')
                # Convert non-null values to string, keep None for null values
                df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) and str(x).lower() != 'nan' else None)

        # Coerce numeric cols
        numeric_cols = ['post','time_of_day_sort_order','total_value_stolen','total_value_recovered']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def get_rms_column_mapping(self) -> dict:
        """
        Get the standardized RMS column mapping to match M Code.
        FIXED: Changed 'FullAddress' key to 'full_address' to match post-normalization name.
        """
        return {
            "case_number": "case_number",
            "incident_date": "incident_date",
            "incident_time": "incident_time",
            "incident_date_between": "incident_date_between",
            "incident_time_between": "incident_time_between",
            "report_date": "report_date",
            "report_time": "report_time",
            "incident_type_1": "incident_type_1_raw",
            "incident_type_2": "incident_type_2_raw",
            "incident_type_3": "incident_type_3_raw",
            "full_address": "full_address_raw",
            "grid": "grid_raw",
            "zone": "zone_raw",
            "narrative": "narrative_raw",
            "total_value_stolen": "total_value_stolen",
            "total_value_recover": "total_value_recovered",
            "registration_1": "registration_1",
            "make_1": "make_1",
            "model_1": "model_1",
            "reg_state_1": "reg_state_1",
            "registration_2": "registration_2",
            "reg_state_2": "reg_state_2",
            "make_2": "make_2",
            "model_2": "model_2",
            "reviewed_by": "reviewed_by",
            "complete_calc": "complete_calc",
            "officer_of_record": "officer_of_record",
            "squad": "squad",
            "det_assigned": "det_assigned",
            "case_status": "case_status",
            "nibrs_classification": "nibrs_classification"
        }

    def get_cad_column_mapping(self) -> dict:
        """Get the standardized CAD column mapping with lowercase_with_underscores."""
        return {
            "ReportNumberNew": "case_number",
            "Incident": "incident",
            "How Reported": "how_reported",
            "FullAddress2": "full_address_raw",
            "PDZone": "post",
            "Grid": "grid_raw",
            "Time of Call": "time_of_call",
            "cYear": "call_year",
            "cMonth": "call_month",
            "HourMinuetsCalc": "hour_minutes_calc",
            "DayofWeek": "day_of_week_raw",
            "Time Dispatched": "time_dispatched",
            "Time Out": "time_out",
            "Time In": "time_in",
            "Time Spent": "time_spent_raw",
            "Time Response": "time_response_raw",
            "Officer": "officer",
            "Disposition": "disposition",
            "Response Type": "response_type_fallback",
            "CADNotes": "cad_notes_raw"
        }

    def clean_text_comprehensive(self, text):
        """Enhanced text cleaning function."""
        if pd.isna(text) or text is None:
            return None
        
        text = str(text)
        
        # Remove problematic patterns
        text = re.sub(r'(\s*[\?\-]\s*){2,}', ' ', text)
        text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # Remove non-printable characters
        text = ''.join(c for c in text if c.isprintable() or c.isspace())
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text if text else None

    def get_time_of_day(self, time_val):
        """Time of day calculation matching M Code exactly."""
        if pd.isna(time_val) or time_val is None:
            return "Unknown"
        
        # Handle both time objects and integer hours
        if hasattr(time_val, 'hour'):
            hour = time_val.hour
        else:
            hour = int(time_val)
            
        if 0 <= hour < 4:
            return "00:00-03:59 Early Morning"
        elif 4 <= hour < 8:
            return "04:00-07:59 Morning"
        elif 8 <= hour < 12:
            return "08:00-11:59 Morning Peak"
        elif 12 <= hour < 16:
            return "12:00-15:59 Afternoon"
        elif 16 <= hour < 20:
            return "16:00-19:59 Evening Peak"
        else:
            return "20:00-23:59 Night"

    def get_time_of_day_sort_order(self, time_of_day):
        """Get sort order for time of day categories for Power BI sorting."""
        sort_order_map = {
            "00:00-03:59 Early Morning": 1,
            "04:00-07:59 Morning": 2,
            "08:00-11:59 Morning Peak": 3,
            "12:00-15:59 Afternoon": 4,
            "16:00-19:59 Evening Peak": 5,
            "20:00-23:59 Night": 6,
            "Unknown": 99
        }
        return sort_order_map.get(time_of_day, 99)

    def get_period(self, date_val):
        """
        Period calculation based on the current date.
        """
        if pd.isna(date_val) or not date_val:
            return "Historical"

        try:
            today = datetime.now().date()
            incident_date = pd.to_datetime(date_val).date()
            days_diff = (today - incident_date).days

            if days_diff < 0: # Future dates
                return "Unknown"
            elif days_diff <= 7:
                return "7-Day"
            elif days_diff <= 28:
                return "28-Day"
            elif incident_date.year == today.year:
                return "YTD"
            else:
                return "Historical"
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse date for period calculation: {date_val}")
            return "Historical"

    def get_season(self, date_val):
        """Season calculation matching M Code exactly."""
        if pd.isna(date_val):
            return None
        
        month = date_val.month
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        else:
            return "Fall"

    def calculate_block(self, address):
        """Block calculation matching M Code exactly."""
        if pd.isna(address):
            return "Check Location Data"
        
        # Clean address
        addr = str(address).replace(", Hackensack, NJ, 07601", "")
        
        # Handle intersections
        if " & " in addr:
            parts = addr.split(" & ")
            if len(parts) == 2 and all(p.strip() for p in parts):
                # For intersections, extract just the street names (remove house numbers)
                street1 = parts[0].strip()
                street2 = parts[1].strip()
                
                # Remove house numbers from street names (only if they start with digits)
                def clean_street_name(street):
                    words = street.split()
                    if words and words[0].isdigit():
                        return ' '.join(words[1:])
                    return street
                
                street1_clean = clean_street_name(street1)
                street2_clean = clean_street_name(street2)
                
                return f"{street1_clean} & {street2_clean}"
            else:
                return "Incomplete Address - Check Location Data"
        else:
            # Handle regular addresses
            try:
                parts = addr.split(" ", 1)
                if len(parts) >= 2 and parts[0].isdigit():
                    street_num = int(parts[0])
                    street_name = parts[1].split(",")[0].strip()
                    block_num = (street_num // 100) * 100
                    return f"{street_name}, {block_num} Block"
                else:
                    return "Check Location Data"
            except:
                return "Check Location Data"

    def clean_incident_type(self, incident_str):
        """Clean incident type by removing statute codes."""
        if pd.isna(incident_str) or incident_str == "":
            return None
        # Remove statute codes
        if " - 2C" in incident_str:
            return incident_str.split(" - 2C")[0]
        return incident_str

    def create_all_incidents(self, row):
        """Combine incident types with statute code removal"""
        types = []
        
        # Use normalized column names post-mapping
        for col in ['incident_type_1_raw', 'incident_type_2_raw', 'incident_type_3_raw']:
            if pd.notna(row.get(col)) and str(row[col]).strip():
                incident_type = str(row[col]).strip()
                # Remove " - 2C" and everything after (statute codes)
                if " - 2C" in incident_type:
                    incident_type = incident_type.split(" - 2C")[0]
                types.append(incident_type)
        
        return ", ".join(types) if types else ""

    def multi_column_crime_search(self, row, crime_patterns):
        """
        Search across all incident-type columns for crime patterns.
        
        Args:
            row (pd.Series): DataFrame row containing incident data
            crime_patterns (dict): Dictionary mapping crime categories to regex patterns
            
        Returns:
            str: Matching crime category or 'Other' if no match found
        """
        # Define columns to search across (in order of priority)
        search_columns = [
            'incident_cad',            # CAD incident column (highest priority for matched data)
            'incident_type',           # Primary RMS column
            'all_incidents',           # Combined incidents
            'incident',                # CAD incident without suffix
            'vehicle_1',               # Additional incident data
            'vehicle_2',               # Additional incident data
            'incident_type_1_raw',     # Raw incident types if available
            'incident_type_2_raw',     # Raw incident types if available
            'incident_type_3_raw'      # Raw incident types if available
        ]
        
        # Search each column for crime patterns
        for column in search_columns:
            if column in row.index and pd.notna(row[column]):
                column_value = str(row[column]).upper()
                
                # Test each crime pattern against the column value
                for category, patterns in crime_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, column_value, re.IGNORECASE):
                            self.logger.debug(f"Found {category} in column {column}: '{row[column]}' matches pattern '{pattern}'")
                            return category
        
        return 'Other'

    def validate_multi_column_filtering(self, df):
        """
        Validate filtering logic across all incident-type columns simultaneously.
        Compare unpivot-then-filter vs. multi-column filtering approaches.
        """
        # Define target crime types (case-insensitive)
        target_crimes = [
            "Motor Vehicle Theft", "Robbery", "Burglary - Auto", 
            "Sexual", "Burglary - Commercial", "Burglary - Residence"
        ]
        
        # Search columns in priority order (matching multi_column_crime_search exactly)
        search_columns = [
            'incident_cad',            # CAD incident column (highest priority for matched data)
            'incident_type',           # Primary RMS column
            'all_incidents',           # Combined incidents
            'incident',                # CAD incident without suffix
            'vehicle_1',               # Additional incident data
            'vehicle_2',               # Additional incident data
            'incident_type_1_raw',     # Raw incident types if available
            'incident_type_2_raw',     # Raw incident types if available
            'incident_type_3_raw'      # Raw incident types if available
        ]
        
        validation_results = {
            'total_records': len(df),
            'search_columns_available': [],
            'crime_matches_by_column': {},
            'total_unique_matches': 0,
            'filtering_accuracy': 0.0,
            'recommendations': []
        }
        
        # Track available columns and their match counts
        for col in search_columns:
            if col in df.columns:
                validation_results['search_columns_available'].append(col)
                
                # Count matches for each target crime in this column
                col_matches = {}
                total_col_matches = 0
                
                for crime in target_crimes:
                    matches = df[col].astype(str).str.contains(
                        crime, case=False, na=False, regex=False
                    ).sum()
                    col_matches[crime] = matches
                    total_col_matches += matches
                
                validation_results['crime_matches_by_column'][col] = {
                    'crime_breakdown': col_matches,
                    'total_matches': total_col_matches
                }
        
        # Calculate overall filtering statistics
        all_matching_records = set()
        for col in validation_results['search_columns_available']:
            for crime in target_crimes:
                matching_indices = df[df[col].astype(str).str.contains(
                    crime, case=False, na=False, regex=False
                )].index
                all_matching_records.update(matching_indices)
        
        validation_results['total_unique_matches'] = len(all_matching_records)
        validation_results['filtering_accuracy'] = (
            len(all_matching_records) / len(df) * 100 if len(df) > 0 else 0
        )
        
        # Generate recommendations
        if len(validation_results['search_columns_available']) < 3:
            validation_results['recommendations'].append(
                "Limited search columns available - consider adding more incident type fields"
            )
        
        if validation_results['filtering_accuracy'] < 10:
            validation_results['recommendations'].append(
                f"Low filtering accuracy ({validation_results['filtering_accuracy']:.1f}%) - review crime pattern matching"
            )
        
        # Log comprehensive results
        self.logger.info("Multi-Column Filtering Validation Results:")
        self.logger.info(f"  - Available search columns: {len(validation_results['search_columns_available'])}")
        self.logger.info(f"  - Total unique crime matches: {validation_results['total_unique_matches']}")
        self.logger.info(f"  - Filtering accuracy: {validation_results['filtering_accuracy']:.1f}%")
        
        for col, data in validation_results['crime_matches_by_column'].items():
            self.logger.info(f"  - {col}: {data['total_matches']} total matches")
            for crime, count in data['crime_breakdown'].items():
                if count > 0:
                    self.logger.info(f"    * {crime}: {count}")
        
        return validation_results

    def validate_7day_crime_categories(self, filtered_df, crime_patterns):
        """
        Validate that filtered 7-day records match expected crime categories.
        Provides detailed analysis of each record's crime categorization.
        """
        validation_report = {
            'total_filtered_records': len(filtered_df),
            'crime_category_breakdown': {},
            'validation_details': [],
            'potential_issues': [],
            'column_match_analysis': {},
            'pattern_match_analysis': {}
        }
        
        if filtered_df.empty:
            self.logger.warning("No 7-Day records to validate")
            return validation_report
        
        # Initialize column match tracking
        search_columns = ['incident_type', 'all_incidents', 'vehicle_1', 'vehicle_2', 
                         'incident_cad', 'incident', 'incident_type_1_raw', 
                         'incident_type_2_raw', 'incident_type_3_raw']
        
        for col in search_columns:
            validation_report['column_match_analysis'][col] = {
                'available': col in filtered_df.columns,
                'populated_records': 0,
                'crime_matches': 0,
                'sample_values': []
            }
        
        # Initialize pattern match tracking
        for category in crime_patterns.keys():
            validation_report['pattern_match_analysis'][category] = {
                'total_matches': 0,
                'matching_records': [],
                'pattern_details': {}
            }
        
        # Analyze each filtered record in detail
        for idx, row in filtered_df.iterrows():
            # Get crime category using multi-column search
            crime_category = self.multi_column_crime_search(row, crime_patterns)
            
            # Track which column(s) triggered the match
            matching_columns = []
            matching_values = []
            pattern_matches = {}
            
            # Check each search column for matches
            for col in search_columns:
                if col in row.index and pd.notna(row[col]):
                    col_value = str(row[col]).upper()
                    validation_report['column_match_analysis'][col]['populated_records'] += 1
                    
                    # Add sample values (limit to 3 unique values per column)
                    if len(validation_report['column_match_analysis'][col]['sample_values']) < 3:
                        if row[col] not in validation_report['column_match_analysis'][col]['sample_values']:
                            validation_report['column_match_analysis'][col]['sample_values'].append(row[col])
                    
                    # Check if this column contains any crime patterns
                    for category, patterns in crime_patterns.items():
                        for pattern_idx, pattern in enumerate(patterns):
                            if re.search(pattern, col_value, re.IGNORECASE):
                                matching_columns.append(col)
                                matching_values.append(row[col])
                                validation_report['column_match_analysis'][col]['crime_matches'] += 1
                                
                                # Track pattern matches
                                if category not in pattern_matches:
                                    pattern_matches[category] = []
                                pattern_matches[category].append({
                                    'pattern': pattern,
                                    'column': col,
                                    'value': row[col],
                                    'pattern_index': pattern_idx
                                })
                                
                                # Update pattern analysis
                                if pattern not in validation_report['pattern_match_analysis'][category]['pattern_details']:
                                    validation_report['pattern_match_analysis'][category]['pattern_details'][pattern] = {
                                        'match_count': 0,
                                        'matching_columns': set(),
                                        'sample_matches': []
                                    }
                                
                                pattern_detail = validation_report['pattern_match_analysis'][category]['pattern_details'][pattern]
                                pattern_detail['match_count'] += 1
                                pattern_detail['matching_columns'].add(col)
                                
                                if len(pattern_detail['sample_matches']) < 3:
                                    pattern_detail['sample_matches'].append({
                                        'case_number': row.get('case_number', 'Unknown'),
                                        'column': col,
                                        'value': row[col]
                                    })
                                
                                break  # Only count first pattern match per column
            
            # Record detailed validation for this record
            validation_details = {
                'case_number': row.get('case_number', 'Unknown'),
                'incident_date': row.get('incident_date', 'Unknown'),
                'incident_time': row.get('incident_time', 'Unknown'),
                'period': row.get('period', 'Unknown'),
                'crime_category': crime_category,
                'matching_columns': list(set(matching_columns)),  # Remove duplicates
                'matching_values': list(set(matching_values)),     # Remove duplicates
                'pattern_matches': pattern_matches,
                'incident_type': row.get('incident_type', 'None'),
                'all_incidents': row.get('all_incidents', 'None'),
                'incident_cad': row.get('incident_cad', 'None'),
                'location': row.get('location', 'Unknown'),
                'narrative': row.get('narrative', 'None')
            }
            
            validation_report['validation_details'].append(validation_details)
            
            # Count by crime category
            if crime_category not in validation_report['crime_category_breakdown']:
                validation_report['crime_category_breakdown'][crime_category] = 0
            validation_report['crime_category_breakdown'][crime_category] += 1
            
            # Update pattern match analysis
            if crime_category in validation_report['pattern_match_analysis']:
                validation_report['pattern_match_analysis'][crime_category]['total_matches'] += 1
                validation_report['pattern_match_analysis'][crime_category]['matching_records'].append(
                    row.get('case_number', 'Unknown')
                )
            
            # Check for potential issues
            if not matching_columns:
                validation_report['potential_issues'].append(
                    f"Case {row.get('case_number', 'Unknown')}: No matching columns found but record was filtered"
                )
            
            if crime_category == 'Other':
                validation_report['potential_issues'].append(
                    f"Case {row.get('case_number', 'Unknown')}: Categorized as 'Other' - may need pattern review"
                )
            
            if len(matching_columns) > 3:
                validation_report['potential_issues'].append(
                    f"Case {row.get('case_number', 'Unknown')}: Multiple matching columns ({len(matching_columns)}) - verify priority logic"
                )
        
        # Convert sets to lists for JSON serialization
        for category_data in validation_report['pattern_match_analysis'].values():
            for pattern_data in category_data['pattern_details'].values():
                pattern_data['matching_columns'] = list(pattern_data['matching_columns'])
        
        # Log comprehensive validation results
        self.logger.info("=" * 60)
        self.logger.info("7-DAY CRIME CATEGORY VALIDATION REPORT")
        self.logger.info("=" * 60)
        self.logger.info(f"Total 7-Day records validated: {validation_report['total_filtered_records']}")
        
        # Crime category breakdown
        self.logger.info("Crime Category Breakdown:")
        for category, count in validation_report['crime_category_breakdown'].items():
            self.logger.info(f"  - {category}: {count} incidents")
        
        # Column analysis
        self.logger.info("Column Match Analysis:")
        for col, analysis in validation_report['column_match_analysis'].items():
            if analysis['available'] and analysis['populated_records'] > 0:
                self.logger.info(f"  - {col}: {analysis['populated_records']} populated, {analysis['crime_matches']} matches")
                if analysis['sample_values']:
                    sample_str = ", ".join(str(v)[:30] + "..." if len(str(v)) > 30 else str(v) 
                                         for v in analysis['sample_values'])
                    self.logger.info(f"    Sample values: {sample_str}")
        
        # Pattern match analysis
        self.logger.info("Pattern Match Analysis:")
        for category, analysis in validation_report['pattern_match_analysis'].items():
            if analysis['total_matches'] > 0:
                self.logger.info(f"  - {category}: {analysis['total_matches']} matches")
                for pattern, details in analysis['pattern_details'].items():
                    self.logger.info(f"    * Pattern '{pattern}': {details['match_count']} matches in columns {list(details['matching_columns'])}")
        
        # Detailed record validation
        self.logger.info("Detailed Record Validation:")
        for i, detail in enumerate(validation_report['validation_details'], 1):
            self.logger.info(f"  Record {i} - Case {detail['case_number']}:")
            self.logger.info(f"    - Date/Time: {detail['incident_date']} {detail['incident_time']}")
            self.logger.info(f"    - Period: {detail['period']}")
            self.logger.info(f"    - Crime Category: {detail['crime_category']}")
            self.logger.info(f"    - Matching Columns: {detail['matching_columns']}")
            self.logger.info(f"    - Location: {detail['location']}")
            
            # Show incident data that triggered the match
            if detail['incident_type'] and detail['incident_type'] != 'None':
                self.logger.info(f"    - Incident Type: {detail['incident_type']}")
            if detail['all_incidents'] and detail['all_incidents'] != 'None':
                self.logger.info(f"    - All Incidents: {detail['all_incidents']}")
            if detail['incident_cad'] and detail['incident_cad'] != 'None':
                self.logger.info(f"    - Incident (CAD): {detail['incident_cad']}")
            if detail['narrative'] and detail['narrative'] != 'None':
                narrative_preview = detail['narrative'][:100] + "..." if len(detail['narrative']) > 100 else detail['narrative']
                self.logger.info(f"    - Narrative: {narrative_preview}")
        
        # Potential issues
        if validation_report['potential_issues']:
            self.logger.warning("Potential Issues Found:")
            for issue in validation_report['potential_issues']:
                self.logger.warning(f"  - {issue}")
        else:
            self.logger.info("No validation issues found - all records properly categorized")
        
        self.logger.info("=" * 60)
        
        return validation_report

    def validate_export_consistency(self, export_files):
        """
        Validate consistency across all exported CSV files.
        Check data types, header compliance, and cross-file compatibility.
        Ensures Power BI import readiness.
        """
        validation_results = {
            'validation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S EST'),
            'files_validated': [],
            'header_compliance': {},
            'data_type_consistency': {},
            'cross_file_compatibility': {},
            'powerbi_readiness': {},
            'overall_status': 'PASS',
            'issues_found': [],
            'recommendations': []
        }
        
        file_schemas = {}
        file_data_samples = {}
        
        self.logger.info("=" * 70)
        self.logger.info("COMPREHENSIVE EXPORT CONSISTENCY VALIDATION")
        self.logger.info("=" * 70)
        
        # Validate each export file
        for file_path in export_files:
            if not Path(file_path).exists():
                validation_results['issues_found'].append(f"File not found: {file_path}")
                self.logger.error(f"File not found: {file_path}")
                continue
            
            try:
                # Read file and analyze schema
                df = pd.read_csv(file_path)
                file_name = Path(file_path).name
                
                validation_results['files_validated'].append(file_name)
                self.logger.info(f"Analyzing: {file_name} ({len(df)} rows, {len(df.columns)} columns)")
                
                # Header compliance check
                header_val = self.validate_lowercase_snake_case_headers(df, file_name)
                validation_results['header_compliance'][file_name] = header_val
                
                if header_val['overall_status'] == 'PASS':
                    self.logger.info(f"  Headers: All {header_val['total_columns']} columns follow lowercase_snake_case")
                else:
                    self.logger.warning(f"  Headers: {len(header_val['non_compliant_columns'])} non-compliant columns")
                    validation_results['issues_found'].append(
                        f"{file_name}: Non-compliant headers: {header_val['non_compliant_columns']}"
                    )
                
                # Data type analysis with detailed breakdown
                data_type_info = {
                    'total_columns': len(df.columns),
                    'total_rows': len(df),
                    'string_columns': [],
                    'numeric_columns': [],
                    'datetime_columns': [],
                    'mixed_type_columns': [],
                    'null_percentage_by_column': {},
                    'data_quality_issues': []
                }
                
                for col in df.columns:
                    col_dtype = df[col].dtype
                    non_null_count = df[col].notna().sum()
                    null_percentage = ((len(df) - non_null_count) / len(df)) * 100 if len(df) > 0 else 0
                    data_type_info['null_percentage_by_column'][col] = round(null_percentage, 1)
                    
                    # Sample non-null values for analysis
                    sample_values = df[col].dropna().head(5).tolist() if non_null_count > 0 else []
                    
                    if col_dtype == 'object':
                        # Analyze object columns for consistency
                        unique_types = set()
                        for val in df[col].dropna().head(20):  # Sample first 20 non-null values
                            if pd.isna(val):
                                continue
                            try:
                                # Test if it's numeric
                                float(val)
                                unique_types.add('numeric_string')
                            except:
                                unique_types.add('string')
                        
                        data_type_info['string_columns'].append({
                            'column': col,
                            'dtype': str(col_dtype),
                            'non_null_count': non_null_count,
                            'null_percentage': null_percentage,
                            'sample_values': sample_values,
                            'detected_types': list(unique_types)
                        })
                        
                        # Check for mixed numeric/string data that could cause Power BI issues
                        if 'numeric_string' in unique_types and 'string' in unique_types:
                            data_type_info['data_quality_issues'].append(
                                f"Column '{col}' contains mixed numeric/string data"
                            )
                    
                    elif pd.api.types.is_numeric_dtype(col_dtype):
                        data_type_info['numeric_columns'].append({
                            'column': col,
                            'dtype': str(col_dtype),
                            'non_null_count': non_null_count,
                            'null_percentage': null_percentage,
                            'min_value': df[col].min() if non_null_count > 0 else None,
                            'max_value': df[col].max() if non_null_count > 0 else None
                        })
                    
                    elif pd.api.types.is_datetime64_any_dtype(col_dtype):
                        data_type_info['datetime_columns'].append({
                            'column': col,
                            'dtype': str(col_dtype),
                            'non_null_count': non_null_count,
                            'null_percentage': null_percentage,
                            'sample_values': sample_values
                        })
                    
                    else:
                        data_type_info['mixed_type_columns'].append({
                            'column': col,
                            'dtype': str(col_dtype),
                            'non_null_count': non_null_count,
                            'null_percentage': null_percentage,
                            'sample_values': sample_values
                        })
                    
                    # Flag columns with high null percentages
                    if null_percentage > 50:
                        data_type_info['data_quality_issues'].append(
                            f"Column '{col}' has high null percentage: {null_percentage:.1f}%"
                        )
                
                validation_results['data_type_consistency'][file_name] = data_type_info
                file_schemas[file_name] = df.dtypes.to_dict()
                file_data_samples[file_name] = df.head(3).to_dict('records')  # Store sample data
                
                # Log data type summary
                self.logger.info(f"  Data Types: {len(data_type_info['string_columns'])} string, " +
                               f"{len(data_type_info['numeric_columns'])} numeric, " +
                               f"{len(data_type_info['datetime_columns'])} datetime, " +
                               f"{len(data_type_info['mixed_type_columns'])} mixed")
                
                if data_type_info['data_quality_issues']:
                    self.logger.warning(f"  Data Quality Issues: {len(data_type_info['data_quality_issues'])}")
                    for issue in data_type_info['data_quality_issues'][:3]:  # Show first 3
                        self.logger.warning(f"    - {issue}")
                
                # Power BI readiness check
                powerbi_issues = self.validate_powerbi_readiness(file_path)
                validation_results['powerbi_readiness'][file_name] = {
                    'ready': len(powerbi_issues) == 0,
                    'issues': powerbi_issues
                }
                
                if powerbi_issues:
                    self.logger.warning(f"  Power BI Issues: {len(powerbi_issues)}")
                    for issue in powerbi_issues[:3]:  # Show first 3
                        self.logger.warning(f"    - {issue}")
                    validation_results['issues_found'].extend([f"{file_name}: {issue}" for issue in powerbi_issues])
                else:
                    self.logger.info(f"  Power BI Ready: No import issues detected")
                
            except Exception as e:
                error_msg = f"Error validating {file_path}: {e}"
                validation_results['issues_found'].append(error_msg)
                self.logger.error(f"{error_msg}")
        
        # Cross-file compatibility analysis
        if len(file_schemas) > 1:
            self.logger.info("Cross-File Compatibility Analysis:")
            
            # Find common columns across files
            all_columns = set()
            for schema in file_schemas.values():
                all_columns.update(schema.keys())
            
            common_columns = all_columns
            for schema in file_schemas.values():
                common_columns = common_columns.intersection(set(schema.keys()))
            
            validation_results['cross_file_compatibility'] = {
                'total_unique_columns': len(all_columns),
                'common_columns': list(common_columns),
                'common_column_count': len(common_columns),
                'schema_consistency': {},
                'file_specific_columns': {}
            }
            
            self.logger.info(f"  Total unique columns across all files: {len(all_columns)}")
            self.logger.info(f"  Common columns across all files: {len(common_columns)}")
            
            # Analyze file-specific columns
            for file_name, schema in file_schemas.items():
                file_specific = set(schema.keys()) - common_columns
                validation_results['cross_file_compatibility']['file_specific_columns'][file_name] = list(file_specific)
                if file_specific:
                    self.logger.info(f"  {file_name} specific columns: {len(file_specific)}")
                    if len(file_specific) <= 5:  # Show all if 5 or fewer
                        self.logger.info(f"    - {', '.join(file_specific)}")
                    else:  # Show first 5 if more
                        self.logger.info(f"    - {', '.join(list(file_specific)[:5])} (and {len(file_specific)-5} more)")
            
            # Check data type consistency for common columns
            inconsistent_columns = []
            for col in common_columns:
                col_types = {}
                for file_name, schema in file_schemas.items():
                    col_types[file_name] = str(schema[col])
                
                # Check if all files have same data type for this column
                unique_types = set(col_types.values())
                is_consistent = len(unique_types) == 1
                
                validation_results['cross_file_compatibility']['schema_consistency'][col] = {
                    'consistent': is_consistent,
                    'types_by_file': col_types,
                    'unique_types': list(unique_types)
                }
                
                if not is_consistent:
                    inconsistent_columns.append(col)
                    validation_results['issues_found'].append(
                        f"Inconsistent data types for column '{col}': {col_types}"
                    )
            
            if inconsistent_columns:
                self.logger.warning(f"  Inconsistent data types in {len(inconsistent_columns)} common columns:")
                for col in inconsistent_columns[:5]:  # Show first 5
                    types = validation_results['cross_file_compatibility']['schema_consistency'][col]['types_by_file']
                    self.logger.warning(f"    - {col}: {types}")
            else:
                self.logger.info(f"  All common columns have consistent data types")
        
        # Generate recommendations
        if validation_results['issues_found']:
            validation_results['recommendations'].extend([
                "Review header naming conventions to ensure lowercase_snake_case compliance",
                "Standardize data types for common columns across all files",
                "Address Power BI compatibility issues before import"
            ])
        
        # High null percentage recommendations
        for file_name, data_info in validation_results['data_type_consistency'].items():
            high_null_cols = [col for col, pct in data_info['null_percentage_by_column'].items() if pct > 75]
            if high_null_cols:
                validation_results['recommendations'].append(
                    f"{file_name}: Consider reviewing columns with >75% null values: {', '.join(high_null_cols[:3])}"
                )
        
        # Determine overall status
        if validation_results['issues_found']:
            validation_results['overall_status'] = 'FAIL' if any('Error' in issue for issue in validation_results['issues_found']) else 'WARNING'
        else:
            validation_results['overall_status'] = 'PASS'
        
        # Final summary
        self.logger.info("=" * 70)
        self.logger.info("EXPORT CONSISTENCY VALIDATION SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Overall Status: {validation_results['overall_status']}")
        self.logger.info(f"Files Validated: {len(validation_results['files_validated'])}")
        self.logger.info(f"Issues Found: {len(validation_results['issues_found'])}")
        self.logger.info(f"Power BI Ready Files: {sum(1 for v in validation_results['powerbi_readiness'].values() if v['ready'])}/{len(validation_results['powerbi_readiness'])}")
        
        if validation_results['recommendations']:
            self.logger.info("Recommendations:")
            for rec in validation_results['recommendations'][:5]:  # Show first 5
                self.logger.info(f"  - {rec}")
        
        self.logger.info("=" * 70)
        
        return validation_results

    def validate_powerbi_readiness(self, file_path):
        """
        Check if CSV file is ready for Power BI import.
        Identifies common issues that prevent successful Power BI data import.
        """
        issues = []
        
        try:
            df = pd.read_csv(file_path)
            
            # Check for problematic characters in headers
            for col in df.columns:
                if any(char in col for char in [' ', '-', '.', '(', ')', '[', ']', '!', '@', '#', '%', '^', '&', '*']):
                    issues.append(f"Header contains special characters: '{col}' (use lowercase_snake_case)")
            
            # Check for extremely long column names (Power BI limit ~128 chars)
            for col in df.columns:
                if len(col) > 100:
                    issues.append(f"Column name too long: '{col}' ({len(col)} chars, recommend <100)")
            
            # Check for reserved words or problematic column names
            reserved_words = ['date', 'time', 'year', 'month', 'day', 'table', 'column', 'row', 'value', 'index']
            for col in df.columns:
                if col.lower() in reserved_words:
                    issues.append(f"Column name may conflict with Power BI reserved word: '{col}'")
            
            # Check for mixed data types that cause Power BI issues
            for col in df.columns:
                if df[col].dtype == 'object' and len(df) > 0:
                    # Sample values to check for mixed types
                    non_null_values = df[col].dropna().head(50)
                    if len(non_null_values) > 0:
                        numeric_count = 0
                        string_count = 0
                        
                        for val in non_null_values:
                            try:
                                float(str(val))
                                numeric_count += 1
                            except:
                                string_count += 1
                        
                        # If we have both numeric and string values, flag as potential issue
                        if numeric_count > 0 and string_count > 0:
                            ratio = min(numeric_count, string_count) / max(numeric_count, string_count)
                            if ratio > 0.1:  # More than 10% minority type
                                issues.append(f"Column '{col}' has mixed numeric/string values (may cause import issues)")
            
            # Check for extremely wide tables (Power BI performs better with <100 columns)
            if len(df.columns) > 100:
                issues.append(f"Table very wide ({len(df.columns)} columns, consider splitting or reducing)")
            
            # Check for extremely large files (>100MB can be slow in Power BI)
            file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            if file_size_mb > 100:
                issues.append(f"Large file size ({file_size_mb:.1f}MB, may impact Power BI performance)")
            
            # Check for completely empty columns
            empty_columns = [col for col in df.columns if df[col].isna().all()]
            if empty_columns:
                issues.append(f"Completely empty columns found: {', '.join(empty_columns[:5])}")
            
        except Exception as e:
            issues.append(f"Error reading file for Power BI validation: {e}")
        
        return issues

    def get_crime_category(self, all_incidents, incident_type):
        """
        Enhanced case-insensitive crime category filtering with multi-column search.
        Now searches across all relevant incident columns for comprehensive coverage.
        """
        # Define comprehensive crime patterns with regex for flexible matching
        crime_patterns = {
            'Motor Vehicle Theft': [
                r'MOTOR\s+VEHICLE\s+THEFT',
                r'AUTO\s+THEFT',
                r'MV\s+THEFT',
                r'VEHICLE\s+THEFT'
            ],
            'Burglary - Auto': [
                r'BURGLARY.*AUTO',
                r'BURGLARY.*VEHICLE',
                r'BURGLARY\s*-\s*AUTO',
                r'BURGLARY\s*-\s*VEHICLE'
            ],
            'Burglary - Commercial': [
                r'BURGLARY.*COMMERCIAL',
                r'BURGLARY\s*-\s*COMMERCIAL',
                r'BURGLARY.*BUSINESS'
            ],
            'Burglary - Residence': [
                r'BURGLARY.*RESIDENCE',
                r'BURGLARY\s*-\s*RESIDENCE',
                r'BURGLARY.*RESIDENTIAL',
                r'BURGLARY\s*-\s*RESIDENTIAL'
            ],
            'Robbery': [
                r'ROBBERY'
            ],
            'Sexual Offenses': [
                r'SEXUAL',
                r'SEX\s+CRIME',
                r'SEXUAL\s+ASSAULT',
                r'SEXUAL\s+OFFENSE'
            ]
        }
        
        # Create a mock row for the multi-column search
        # This allows us to use the existing multi_column_crime_search function
        mock_row = pd.Series({
            'incident_type': incident_type,
            'all_incidents': all_incidents,
            'vehicle_1': None,  # These would be populated in actual row processing
            'vehicle_2': None,
            'incident_type_1_raw': None,
            'incident_type_2_raw': None,
            'incident_type_3_raw': None
        })
        
        # Use the multi-column search function
        return self.multi_column_crime_search(mock_row, crime_patterns)

    def format_vehicle(self, reg_state, registration, make, model):
        """Format vehicle information consistently with M Code."""
        parts = []
        
        # State and registration
        if pd.notna(reg_state) and pd.notna(registration):
            parts.append(f"{reg_state} - {registration}")
        elif pd.notna(registration):
            parts.append(str(registration))
        elif pd.notna(reg_state):
            parts.append(str(reg_state))
        
        # Make and model
        make_model_parts = []
        if pd.notna(make):
            make_model_parts.append(str(make))
        if pd.notna(model):
            make_model_parts.append(str(model))
        
        if make_model_parts:
            parts.append("/".join(make_model_parts))
        
        result = ", ".join(parts) if parts else None
        
        # Convert to uppercase if result exists
        if result:
            return result.upper()
        return None

    def calculate_time_response(self, row):
        """Calculate response time in minutes with error handling."""
        try:
            time_call = pd.to_datetime(row.get('Time_Of_Call'))
            time_dispatched = pd.to_datetime(row.get('Time_Dispatched'))
            
            if pd.notna(time_call) and pd.notna(time_dispatched):
                # Calculate (Time Dispatched - Time Call)
                duration = time_dispatched - time_call
                minutes = duration.total_seconds() / 60
                
                # Handle negative durations by swapping order: (Time Call - Time Dispatched)
                if minutes < 0:
                    duration = time_call - time_dispatched
                    minutes = duration.total_seconds() / 60
                
                # Cap extreme outliers
                if minutes > 480:  # Cap at 8 hours
                    minutes = 480
                
                return round(minutes, 2)
            return None
        except:
            return None

    def calculate_time_spent(self, row):
        """Calculate time spent on scene in minutes with error handling."""
        try:
            time_out = pd.to_datetime(row.get('Time_Out'))
            time_in = pd.to_datetime(row.get('Time_In'))
            
            if pd.notna(time_out) and pd.notna(time_in):
                # Calculate (Time In - Time Out)
                duration = time_in - time_out
                minutes = duration.total_seconds() / 60
                
                # Handle negative durations by swapping order: (Time Out - Time In)
                if minutes < 0:
                    duration = time_out - time_in
                    minutes = duration.total_seconds() / 60
                
                # Cap extreme outliers
                if minutes > 720:  # Cap at 12 hours
                    minutes = 720
                
                return round(minutes, 2)
            return None
        except:
            return None

    def process_rms_data(self, rms_file):
        """Process RMS data with all fixes for time, location, and text fields."""
        with self.monitor_performance(f"RMS Data Processing - {rms_file.name}"):
            self.logger.info(f"Processing RMS data: {rms_file.name}")
            
            try:
                with self.monitor_performance("RMS File Loading"):
                    rms_df = pd.read_excel(rms_file, engine='openpyxl')
                    self.logger.info(f"Loaded RMS file with {len(rms_df)} rows and {len(rms_df.columns)} columns")
            except Exception as e:
                self.logger.error(f"Error loading RMS file: {e}")
                return pd.DataFrame()

            # NORMALIZE HEADERS: Apply lowercase snake_case normalization immediately
            rms_df = normalize_headers(rms_df)
            self.logger.info(f"Normalized RMS headers: {list(rms_df.columns)}")

            # MAP COLUMNS: Use the corrected mapping keys for normalized column names
            column_mapping = {
                "case_number": "case_number",
                "incident_date": "incident_date", 
                "incident_time": "incident_time",
                "incident_date_between": "incident_date_between",
                "incident_time_between": "incident_time_between", 
                "report_date": "report_date",
                "report_time": "report_time",
                "incident_type_1": "incident_type_1_raw",
                "incident_type_2": "incident_type_2_raw", 
                "incident_type_3": "incident_type_3_raw",
                "full_address": "full_address_raw",
                "grid": "grid_raw",
                "zone": "zone_raw", 
                "narrative": "narrative_raw",
                "total_value_stolen": "total_value_stolen",
                "total_value_recover": "total_value_recovered",
                "registration_1": "registration_1",
                "make1": "make_1",
                "model1": "model_1", 
                "reg_state_1": "reg_state_1",
                "registration_2": "registration_2",
                "reg_state_2": "reg_state_2",
                "make2": "make_2", 
                "model2": "model_2",
                "reviewed_by": "reviewed_by",
                "completecalc": "complete_calc",
                "officer_of_record": "officer_of_record",
                "squad": "squad",
                "det_assigned": "det_assigned", 
                "case_status": "case_status",
                "nibrs_classification": "nibrs_classification"
            }
            
            # Filter mapping to only include columns that exist in the dataframe
            existing_mapping = {k: v for k, v in column_mapping.items() if k in rms_df.columns}
            rms_df = rms_df.rename(columns=existing_mapping)
            self.logger.info(f"Applied column mapping to {len(existing_mapping)} columns.")

            # Clean all text columns
            text_columns = rms_df.select_dtypes(include=['object']).columns
            for col in text_columns:
                rms_df[col] = rms_df[col].apply(self.clean_text_comprehensive)
            
            # 1) Cascading date logic - use the actual column names after normalization
            date_cols = ['incident_date', 'incident_date_between', 'report_date']
            existing_date_cols = [col for col in date_cols if col in rms_df.columns]
            rms_df['incident_date'] = coalesce_cols(rms_df, *existing_date_cols)
            rms_df['incident_date'] = pd.to_datetime(rms_df['incident_date'], errors='coerce')
            self.logger.info(f"Cascaded incident dates populated: {rms_df['incident_date'].notna().sum()}/{len(rms_df)}")
            
            # 2) FIX: Cascading time - handle timedelta objects properly
            time_cols = ['incident_time', 'incident_time_between', 'report_time']
            existing_time_cols = [col for col in time_cols if col in rms_df.columns]
            rms_df['temp_time'] = coalesce_cols(rms_df, *existing_time_cols)
            
            # Convert timedelta to time string (HH:MM format)
            def timedelta_to_time_str(td):
                if pd.isna(td):
                    return None
                if isinstance(td, pd.Timedelta):
                    # Handle Excel time values stored as timedeltas
                    # Excel stores times as fractions of a day (e.g., 0.5 = 12:00, 0.75 = 18:00)
                    total_seconds = int(td.total_seconds())
                    
                    # If the timedelta represents more than 24 hours, it's likely a date/time combination
                    # We need to extract just the time portion
                    if total_seconds >= 24 * 3600:
                        # Extract just the time portion (modulo 24 hours)
                        time_seconds = total_seconds % (24 * 3600)
                        hours = time_seconds // 3600
                        minutes = (time_seconds % 3600) // 60
                    else:
                        # Standard time conversion
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                    
                    return f"{hours:02d}:{minutes:02d}"
                return None
            
            rms_df['incident_time'] = rms_df['temp_time'].apply(timedelta_to_time_str)
            rms_df = rms_df.drop(columns=['temp_time'])
            self.logger.info(f"Cascaded incident times populated: {rms_df['incident_time'].notna().sum()}/{len(rms_df)}")
            
            # 3) FIX: Recalculate Time-of-Day logic
            def time_str_to_time_of_day(time_str):
                if pd.isna(time_str) or time_str is None:
                    return 'Unknown'
                try:
                    # Parse HH:MM string to get hour
                    hour = int(time_str.split(':')[0])
                    return self.get_time_of_day(hour)
                except:
                    return 'Unknown'
            
            rms_df['time_of_day'] = rms_df['incident_time'].apply(time_str_to_time_of_day)
            rms_df["time_of_day_sort_order"] = rms_df["time_of_day"].apply(self.get_time_of_day_sort_order)
            self.logger.info(f"Time of Day populated: {len(rms_df[rms_df['time_of_day'] != 'Unknown'])}/{len(rms_df)}")

            # 4) Period, Day_of_Week & Cycle_Name Fixes - do these BEFORE formatting the date
            rms_df['period'] = rms_df['incident_date'].apply(self.get_period)
            rms_df['season'] = rms_df['incident_date'].apply(self.get_season)
            rms_df['day_of_week'] = rms_df['incident_date'].dt.day_name()
            rms_df['day_type'] = rms_df['day_of_week'].isin(['Saturday', 'Sunday']).map({True: 'Weekend', False: 'Weekday'})
            rms_df['cycle_name'] = rms_df['incident_date'].apply(
                lambda x: self.get_cycle_for_date(x, self.cycle_calendar) if pd.notna(x) else None
            )
            
            # Format incident_date to mm/dd/yy string AFTER all datetime operations
            rms_df['incident_date'] = rms_df['incident_date'].dt.strftime('%m/%d/%y')
            self.logger.info("Formatted incident_date to mm/dd/yy")

            # 5) FIX: Address validation and standardization
            if 'full_address_raw' in rms_df.columns:
                rms_df['location'] = rms_df['full_address_raw'].apply(self.validate_hackensack_address)
                self.logger.info(f"Address validation: {rms_df['location'].notna().sum()}/{len(rms_df)} addresses validated")
            else:
                rms_df['location'] = None
                self.logger.warning("full_address_raw column not found - location will be None")
            
            rms_df['block'] = rms_df['location'].apply(self.calculate_block)

            # Grid and post backfill
            def backfill_grid_post_row(row):
                grid, post = self.backfill_grid_post(row.get('location'), row.get('grid_raw'), row.get('zone_raw'))
                return pd.Series({'grid': grid, 'post': post})
            
            backfilled = rms_df.apply(backfill_grid_post_row, axis=1)
            rms_df['grid'] = backfilled['grid']
            rms_df['post'] = backfilled['post']

            # Clean and combine incident types
            rms_df['all_incidents'] = rms_df.apply(self.create_all_incidents, axis=1)
            rms_df["incident_type"] = rms_df["all_incidents"].apply(extract_incident_types)
            
            # Vehicle processing
            rms_df['vehicle_1'] = rms_df.apply(
                lambda row: self.format_vehicle(row.get('reg_state_1'), row.get('registration_1'), row.get('make_1'), row.get('model_1')), axis=1
            )
            rms_df['vehicle_2'] = rms_df.apply(
                lambda row: self.format_vehicle(row.get('reg_state_2'), row.get('registration_2'), row.get('make_2'), row.get('model_2')), axis=1
            )

            def combine_vehicles(row):
                v1, v2 = row.get('vehicle_1'), row.get('vehicle_2')
                return f"{v1} | {v2}" if pd.notna(v1) and pd.notna(v2) else None
            rms_df['vehicle_1_and_vehicle_2'] = rms_df.apply(combine_vehicles, axis=1)
            
            # 6) FIX: Narrative Cleaning
            if 'narrative_raw' in rms_df.columns:
                rms_df['narrative'] = rms_df['narrative_raw'].apply(self.clean_text_comprehensive)
                # Additional normalization for whitespace
                rms_df['narrative'] = rms_df['narrative'].str.replace(r'\s+', ' ', regex=True).str.strip()
            else:
                rms_df['narrative'] = None
            
            # Final column selection
            desired_columns = [
                'case_number', 'incident_date', 'incident_time', 'time_of_day', 'time_of_day_sort_order',
                'period', 'season', 'day_of_week', 'day_type', 'location', 'block', 
                'grid', 'post', 'incident_type', 'all_incidents', 'vehicle_1', 'vehicle_2', 
                'vehicle_1_and_vehicle_2', 'narrative', 'total_value_stolen', 'squad', 
                'officer_of_record', 'nibrs_classification', 'cycle_name', 'case_status'
            ]
            existing_columns = [col for col in desired_columns if col in rms_df.columns]
            rms_final = rms_df[existing_columns].copy()

            # Filtering
            initial_count = len(rms_final)
            rms_final = rms_final[rms_final['case_number'] != '25-057654']
            
            rms_final = rms_final[rms_final['period'] != 'Historical']
            self.logger.info(f"RMS processing complete: {len(rms_final)} records after filtering from {initial_count}")
            
            rms_final = self.optimize_dataframe_memory(rms_final, "RMS Final Dataset")
            gc.collect()
        
        return rms_final

    def process_cad_data(self, cad_file):
        """Process CAD data with enhanced incident mapping and lowercase snake_case headers."""
        with self.monitor_performance(f"CAD Data Processing - {cad_file.name}"):
            self.logger.info(f"Processing CAD data: {cad_file.name}")
        
        try:
            cad_df = pd.read_excel(cad_file, engine='openpyxl', dtype={"How Reported": str, "Grid": str})
            self.logger.info(f"Loaded CAD file with {len(cad_df)} rows and {len(cad_df.columns)} columns")
            self.logger.info("Applied dtype={'How Reported': str} to prevent Excel auto-parsing '9-1-1' as date")
            
            if "How Reported" in cad_df.columns:
                cad_df["How Reported"] = cad_df["How Reported"].apply(self.clean_how_reported_911)
                self.logger.info("Applied enhanced fixes to prevent '9-1-1' date conversion")
                
        except Exception as e:
            self.logger.error(f"Error loading CAD file: {e}")
            return pd.DataFrame()

        cad_df = normalize_headers(cad_df)
        column_mapping = self.get_cad_column_mapping()
        existing_mapping = {k:v for k,v in column_mapping.items() if to_snake(k) in cad_df.columns}
        cad_df = cad_df.rename(columns={to_snake(k): v for k, v in existing_mapping.items()})

        # Clean text columns
        text_columns = cad_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            cad_df[col] = cad_df[col].apply(self.clean_text_comprehensive)

        # Map incident to response_type and category_type
        if 'incident' in cad_df.columns:
            mapping_results = cad_df['incident'].apply(self.map_call_type)
            cad_df[['response_type', 'category_type']] = pd.DataFrame(mapping_results.tolist(), index=cad_df.index)
            # Create _cad suffixed columns for clarity in final merge
            cad_df['response_type_cad'] = cad_df['response_type']
            cad_df['category_type_cad'] = cad_df['category_type']

        # Time calculations
        cad_df['time_response_minutes'] = cad_df.apply(self.calculate_time_response, axis=1)
        cad_df['time_spent_minutes'] = cad_df.apply(self.calculate_time_spent, axis=1)
        cad_df['time_spent_formatted'] = cad_df['time_spent_minutes'].apply(self.format_time_spent_minutes)
        cad_df['time_response_formatted'] = cad_df['time_response_minutes'].apply(self.format_time_response_minutes)

        # Location processing
        if 'full_address_raw' in cad_df.columns:
            cad_df['location'] = cad_df['full_address_raw'].apply(self.validate_hackensack_address)
        else:
            cad_df['location'] = None
        cad_df['block'] = cad_df['location'].apply(self.calculate_block)

        # Grid and post processing
        if 'grid_raw' in cad_df.columns:
            cad_df['grid'] = cad_df['grid_raw'].replace(['', 'nan', 'NaN', 'None'], pd.NA)
        else:
            cad_df['grid'] = pd.NA
        if 'post' in cad_df.columns:
            cad_df['post'] = cad_df['post'].replace(['', 'nan', 'NaN', 'None'], pd.NA)

        # CAD notes parsing
        if 'cad_notes_raw' in cad_df.columns:
            notes_parsed = cad_df['cad_notes_raw'].apply(self.parse_cad_notes)
            cad_df[['cad_username', 'cad_timestamp', 'cad_notes_cleaned']] = notes_parsed
        
        # Add cycle_name column
        def get_cad_incident_date(row):
            if pd.notna(row.get('time_of_call')):
                try:
                    return pd.to_datetime(row['time_of_call']).date()
                except: return None
            return None
        
        cad_df['incident_date'] = cad_df.apply(get_cad_incident_date, axis=1)
        cad_df['cycle_name'] = cad_df['incident_date'].apply(
            lambda x: self.get_cycle_for_date(x, self.cycle_calendar) if pd.notna(x) else None
        )
        
        # Final column selection
        desired_columns = [
            'case_number', 'incident', 'response_type', 'category_type', 'response_type_cad', 'category_type_cad', 'how_reported', 
            'location', 'block', 'grid', 'post', 'time_of_call', 'time_dispatched', 
            'time_out', 'time_in', 'time_spent_minutes', 'time_response_minutes',
            'time_spent_formatted', 'time_response_formatted', 'officer', 'disposition', 
            'cad_notes_cleaned', 'cad_username', 'cad_timestamp', 'cycle_name'
        ]
        existing_columns = [col for col in desired_columns if col in cad_df.columns]
        cad_final = cad_df[existing_columns].copy()

        self.logger.info(f"CAD processing complete: {len(cad_final)} records")
        
        cad_final = self.optimize_dataframe_memory(cad_final, "CAD Final Dataset")
        gc.collect()
        
        return cad_final

    def find_latest_files(self):
        """Find the latest files in each export directory."""
        latest_files = {}
        
        cad_path = self.export_dirs['cad_exports']
        rms_path = self.export_dirs['rms_exports']
        
        if cad_path.exists():
            cad_files = list(cad_path.glob("*SCRPA_CAD.xlsx"))
            if cad_files:
                latest_files['cad'] = max(cad_files, key=lambda f: f.stat().st_mtime)
                self.logger.info(f"Latest CAD file: {latest_files['cad'].name}")
        
        if rms_path.exists():
            rms_files = list(rms_path.glob("*SCRPA_RMS.xlsx"))
            if rms_files:
                latest_files['rms'] = max(rms_files, key=lambda f: f.stat().st_mtime)
                self.logger.info(f"Latest RMS file: {latest_files['rms'].name}")

        if not latest_files:
            self.logger.error(f"No CAD or RMS excel files found in {cad_path}")

        return latest_files

    def process_final_pipeline(self):
        """Run the complete processing pipeline with standardized output."""
        with self.monitor_performance("Complete SCRPA Pipeline V8.5"):
            self.logger.info("Starting Comprehensive SCRPA Fix V8.5 pipeline...")
        
        latest_files = self.find_latest_files()
        
        if not latest_files:
            raise ValueError("No data files found to process")

        rms_data = self.process_rms_data(latest_files['rms']) if 'rms' in latest_files else pd.DataFrame()
        cad_data = self.process_cad_data(latest_files['cad']) if 'cad' in latest_files else pd.DataFrame()

        output_dir = self.project_path / '04_powerbi'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_suffix = f"{self.current_cycle}_{self.current_date}" if self.current_cycle else datetime.now().strftime('%Y%m%d')

        if not rms_data.empty:
            rms_output = output_dir / f'{file_suffix}_7Day_rms_data_standardized_v3.csv'
            self.write_large_csv_efficiently(self.standardize_data_types(rms_data), rms_output)
            self.logger.info(f"RMS data saved: {rms_output}")

        if not cad_data.empty:
            cad_output = output_dir / f'{file_suffix}_7Day_cad_data_standardized_v2.csv'
            self.write_large_csv_efficiently(self.standardize_data_types(cad_data), cad_output)
            self.logger.info(f"CAD data saved: {cad_output}")

        joined_result = pd.DataFrame()
        if not rms_data.empty and not cad_data.empty:
            joined_result = self.create_cad_rms_matched_dataset(rms_data, cad_data, output_dir)
            if not joined_result.empty:
                self.create_7day_scrpa_export(joined_result, output_dir)

        self.validate_final_outputs(rms_data, cad_data, joined_result)
        
        return {
            'rms_data': rms_data,
            'cad_data': cad_data,
            'joined_data': joined_result,
            'output_dir': str(output_dir)
        }

    def create_cad_rms_matched_dataset(self, rms_data, cad_data, output_dir):
        """Create properly matched CAD-RMS dataset with RMS as master (LEFT JOIN)."""
        self.logger.info(f"Starting CAD-RMS matching: RMS={len(rms_data)} records, CAD={len(cad_data)} records")
        
        rms_copy = rms_data.copy()
        cad_copy = cad_data.copy()
        
        cad_renamed = cad_copy.add_suffix('_cad')
        
        joined_data = pd.merge(
            rms_copy,
            cad_renamed,
            left_on='case_number',
            right_on='case_number_cad',
            how='left'
        )
        
        # FIX: Preserve critical _cad columns
        cols_to_keep = ['case_number_cad', 'response_type_cad', 'category_type_cad', 'grid_cad', 'post_cad']
        all_cad_cols = [c for c in joined_data.columns if c.endswith('_cad')]
        cols_to_drop = [c for c in all_cad_cols if c not in cols_to_keep]
        joined_data = joined_data.drop(columns=cols_to_drop)

        # CAD-first, RMS-fallback logic (only if RMS columns exist)
        if 'response_type' in joined_data.columns:
            joined_data['response_type'] = joined_data['response_type_cad'].fillna(joined_data['response_type'])
        else:
            joined_data['response_type'] = joined_data['response_type_cad']
            
        if 'category_type' in joined_data.columns:
            joined_data['category_type'] = joined_data['category_type_cad'].fillna(joined_data['category_type'])
        else:
            joined_data['category_type'] = joined_data['category_type_cad']

        match_rate = (joined_data['case_number_cad'].notna().sum() / len(joined_data)) * 100
        self.logger.info(f"CAD-RMS matching complete: {len(joined_data)} records with a {match_rate:.1f}% match rate.")

        file_suffix = f"{self.current_cycle}_{self.current_date}" if self.current_cycle else datetime.now().strftime('%Y%m%d')
        joined_output = output_dir / f'{file_suffix}_7Day_cad_rms_matched_standardized.csv'
        self.write_large_csv_efficiently(self.standardize_data_types(joined_data), joined_output)
        self.logger.info(f"Joined data saved: {joined_output}")
        
        return joined_data

    def create_7day_scrpa_export(self, matched_data, output_dir):
        """Create 7-Day SCRPA incident export with specific crime category filtering."""
        self.logger.info("Starting 7-Day SCRPA incident export...")
        
        if matched_data.empty:
            self.logger.warning("No matched data for 7-day export")
            return pd.DataFrame()

        crime_patterns = {
            'Motor Vehicle Theft': [r'MOTOR\s+VEHICLE\s+THEFT', r'AUTO\s+THEFT', r'MV\s+THEFT', r'VEHICLE\s+THEFT'],
            'Burglary - Auto': [r'BURGLARY.*AUTO', r'BURGLARY.*VEHICLE'],
            'Burglary - Commercial': [r'BURGLARY.*COMMERCIAL', r'BURGLARY.*BUSINESS'],
            'Burglary - Residence': [r'BURGLARY.*RESIDENCE', r'BURGLARY.*RESIDENTIAL'],
            'Robbery': [r'ROBBERY'],
            'Sexual Offenses': [r'SEXUAL', r'SEX\s+CRIME', r'SEXUAL\s+ASSAULT']
        }

        period_filtered = matched_data[matched_data['period'] == '7-Day'].copy()
        self.logger.info(f"7-Day period records found: {len(period_filtered)}")

        if period_filtered.empty:
            self.logger.warning("No 7-Day incidents found to filter for SCRPA export.")
            return pd.DataFrame()

        # Apply the multi-column crime filter
        crime_matches_indices = []
        for idx, row in period_filtered.iterrows():
            crime_category = self.multi_column_crime_search(row, crime_patterns)
            if crime_category != 'Other':
                crime_matches_indices.append(idx)
        
        filtered_df = period_filtered.loc[crime_matches_indices]
        self.logger.info(f"After multi-column crime filtering: {len(filtered_df)} records")

        if filtered_df.empty:
            self.logger.warning("No 7-Day incidents matched the required crime categories.")
            return pd.DataFrame()

        filtered_df['crime_category'] = filtered_df.apply(lambda row: self.multi_column_crime_search(row, crime_patterns), axis=1)

        export_df = pd.DataFrame({
            'case_number': filtered_df['case_number'],
            'incident_date_time': filtered_df['incident_date'].astype(str) + ' ' + filtered_df['incident_time'].astype(str),
            'incident_types': filtered_df['all_incidents'],
            'crime_category': filtered_df['crime_category'],
            'full_address': filtered_df['location'],
            'narrative': filtered_df['narrative'],
            'vehicle_registration': filtered_df['vehicle_1'],
            'grid_zone': filtered_df['grid'].astype(str) + '-' + filtered_df['post'].astype(str),
            'status': "Active"
        })

        file_suffix = f"{self.current_cycle}_{self.current_date}" if self.current_cycle else datetime.now().strftime('%Y%m%d')
        output_path = output_dir / f"{file_suffix}_7Day_SCRPA_Incidents.csv"
        
        self.write_large_csv_efficiently(self.standardize_data_types(export_df), output_path)
        self.logger.info(f"7-Day SCRPA export complete: {len(export_df)} incidents saved to {output_path}")
        
        return export_df

    def validate_final_outputs(self, rms_data, cad_data, joined_data):
        """Runs a series of validation checks on the final dataframes."""
        self.logger.info("=" * 60)
        self.logger.info("FINAL VALIDATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"✅ RMS records processed: {len(rms_data)}")
        self.logger.info(f"✅ CAD records processed: {len(cad_data)}")
        self.logger.info(f"✅ Matched records created: {len(joined_data)}")

        if not joined_data.empty:
            # Check for expected record count (adjust if needed)
            if len(joined_data) == 135:
                self.logger.info("✅ RECORD COUNT VALIDATION: PASSED (135 records)")
            else:
                self.logger.warning(f"⚠️ RECORD COUNT VALIDATION: Expected 135, got {len(joined_data)}")

            # Validate column naming convention
            non_compliant = [col for col in joined_data.columns if not re.match(r'^[a-z0-9]+(_[a-z0-9]+)*$', col)]
            if not non_compliant:
                self.logger.info("✅ COLUMN NAMING VALIDATION: PASSED (all lowercase_snake_case)")
            else:
                self.logger.error(f"❌ COLUMN NAMING VALIDATION: Non-compliant columns: {non_compliant}")
            
            # Validate critical columns
            critical_cols = ['case_number', 'incident_type', 'response_type_cad', 'grid_cad', 'post_cad']
            missing = [col for col in critical_cols if col not in joined_data.columns]
            if not missing:
                self.logger.info("✅ CRITICAL COLUMNS VALIDATION: PASSED")
            else:
                self.logger.error(f"❌ CRITICAL COLUMNS VALIDATION: Missing columns: {missing}")

if __name__ == "__main__":
    try:
        processor = ComprehensiveSCRPAFixV8_5()
        results = processor.process_final_pipeline()
        print("\n" + "="*60)
        print("🎯 SCRPA V8.5 PROCESSING COMPLETE")
        print("="*60)
        print(f"✅ RMS Records: {len(results['rms_data'])}")
        print(f"✅ CAD Records: {len(results['cad_data'])}")
        print(f"✅ Matched Records: {len(results['joined_data'])}")
        print(f"✅ Output Directory: {results['output_dir']}")
        print("="*60)
        
    except Exception as e:
        logging.getLogger('ComprehensiveSCRPAFixV8_5').error(f"Fatal error in main execution: {e}", exc_info=True)
        print(f"❌ An error occurred during processing: {e}")
        raise