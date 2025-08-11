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
    Extract standardized incident types from the all_incidents string.
    
    Args:
        all_incidents: String containing incident type information
        
    Returns:
        Comma-separated string of standardized incident types or None if no matches
    """
    if pd.isna(all_incidents) or not all_incidents:
        return None
    
    # Convert to uppercase for case-insensitive matching
    incidents_upper = all_incidents.upper()
    found_types = []
    
    # Check for specific patterns and add standardized strings
    if "BURGLARY" in incidents_upper and ("AUTO" in incidents_upper or "VEHICLE" in incidents_upper):
        found_types.append("Burglary - Auto")
    
    if "BURGLARY" in incidents_upper and ("RESIDENCE" in incidents_upper or "RESIDENTIAL" in incidents_upper):
        found_types.append("Burglary - Residence")
    
    if "BURGLARY" in incidents_upper and "COMMERCIAL" in incidents_upper:
        found_types.append("Burglary - Commercial")
    
    if any(pattern in incidents_upper for pattern in ["MOTOR VEHICLE THEFT", "AUTO THEFT", "VEHICLE THEFT", "MV THEFT"]):
        found_types.append("Motor Vehicle Theft")
    
    if "ROBBERY" in incidents_upper:
        found_types.append("Robbery")
    
    if "SEXUAL" in incidents_upper:
        found_types.append("Sexual Offense")
    
    # Return comma-separated string if types found, otherwise None
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
            'cad_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\05_EXPORTS"),
            'rms_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\05_EXPORTS")
        }
        
        self.ref_dirs = {
            'call_types': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Classifications\CallTypes\CallType_Categories.xlsx"),
            'zone_grid': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\zone_grid_master.xlsx"),
            'cycle_calendar': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Temporal\SCRPA_Cycle\7Day_28Day_Cycle_20250414.xlsx")
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
                'date_occurred': pd.date_range('2024-01-01', periods=test_size, freq='1H'),
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
                # Try fallback path
                fallback_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\CallType_Categories.xlsx")
                if fallback_path.exists():
                    # Load with incident column forced to string type and preserve Excel's original column names
                    self.call_type_ref = pd.read_excel(
                        fallback_path, 
                        dtype={"Incident": str, "Response Type": str, "Category Type": str}
                    )
                    self.logger.info(f"Loaded call type reference from fallback path: {len(self.call_type_ref)} records")
                    self.logger.info(f"Reference file columns: {list(self.call_type_ref.columns)}")
                    
                    # Ensure incident column is properly formatted as string
                    if 'Incident' in self.call_type_ref.columns:
                        self.call_type_ref['Incident'] = self.call_type_ref['Incident'].astype(str)
                        self.logger.info(f"Incident column forced to string type with {len(self.call_type_ref)} records")
                else:
                    self.logger.warning("Call type reference file not found at primary or fallback paths - using fallback categorization")
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
                    self.zone_grid_ref.columns = [self.convert_to_lowercase_with_underscores(col) for col in self.zone_grid_ref.columns]
            else:
                self.logger.warning("Zone/grid reference file not found - no backfill available")
                self.zone_grid_ref = None
        except Exception as e:
            self.logger.error(f"Could not load zone/grid reference: {e}")
            self.zone_grid_ref = None

    def load_cycle_calendar(self):
        """Load Excel file from 09_Reference/Temporal/SCRPA_Cycle/7Day_28Day_Cycle_20250414.xlsx"""
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
            
            # If no match found, handle historical dates
            # For dates outside the cycle calendar range, generate a cycle name based on the date
            if incident_date < datetime.now().date():
                # Calculate week number and year for historical dates
                year = incident_date.year
                week_num = incident_date.isocalendar()[1]
                return f"C{year%100:02d}W{week_num:02d}"
            
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
                       'season','day_of_week','day_type','cycle_name']
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
        """Get the standardized RMS column mapping to match M Code."""
        return {
            "Case Number": "case_number",
            "Incident Date": "incident_date",
            "Incident Time": "incident_time",
            "Incident Date_Between": "incident_date_between",
            "Incident Time_Between": "incident_time_between",
            "Report Date": "report_date",
            "Report Time": "report_time",
            "Incident Type_1": "incident_type_1_raw",
            "Incident Type_2": "incident_type_2_raw",
            "Incident Type_3": "incident_type_3_raw",
            "full_address": "full_address_raw",
            "Grid": "grid_raw",
            "Zone": "zone_raw",
            "Narrative": "narrative_raw",
            "Total Value Stolen": "total_value_stolen",
            "Total Value Recover": "total_value_recovered",
            "Registration 1": "registration_1",
            "Make1": "make_1",
            "Model1": "model_1",
            "Reg State 1": "reg_state_1",
            "Registration 2": "registration_2",
            "Reg State 2": "reg_state_2",
            "Make2": "make_2",
            "Model2": "model_2",
            "Reviewed By": "reviewed_by",
            "CompleteCalc": "complete_calc",
            "Officer of Record": "officer_of_record",
            "Squad": "squad",
            "Det_Assigned": "det_assigned",
            "Case_Status": "case_status",
            "NIBRS Classification": "nibrs_classification"
        }

    def get_cad_column_mapping(self) -> dict:
        """Get the standardized CAD column mapping with lowercase_with_underscores."""
        return {
            "ReportNumberNew": "case_number",
            "Incident": "incident",  # FIXED: Map directly to 'incident' instead of 'incident_raw'
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

    def cascade_date(self, row):
        """
        Enhanced cascading date logic according to specification.
        
        Chain-fill: date = Date → Date_Between → Report Date
        Parse each field separately with errors='coerce'
        """
        # Define the date cascade chain in priority order
        date_columns = [
            'Incident Date',           # Primary date field
            'Incident Date_Between',   # Fallback date field
            'Report Date'              # Final fallback
        ]
        
        # Try each column in the cascade chain
        for col in date_columns:
            if col in row.index and pd.notna(row.get(col)):
                try:
                    # Parse each field separately with errors='coerce'
                    result = pd.to_datetime(row[col], errors='coerce')
                    if pd.notna(result):
                        return result.date()
                except Exception as e:
                    self.logger.debug(f"Error parsing date from {col}: {e}")
                    continue
        
        return None

    def cascade_time(self, row):
        """
        Enhanced cascading time logic according to specification.
        
        Chain-fill: time = Time → Time_Between → Report Time
        Parse each field separately with errors='coerce'
        Format time via strftime to avoid Excel fallback artifact
        """
        # Define the time cascade chain in priority order
        time_columns = [
            'Incident Time',           # Primary time field
            'Incident Time_Between',   # Fallback time field
            'Report Time'              # Final fallback
        ]
        
        # Try each column in the cascade chain
        for col in time_columns:
            if col in row.index and pd.notna(row.get(col)):
                try:
                    time_value = row[col]
                    
                    # Handle Excel Timedelta objects (common Excel time format)
                    if isinstance(time_value, pd.Timedelta):
                        total_seconds = time_value.total_seconds()
                        hours = int(total_seconds // 3600) % 24  # Handle 24+ hour overflow
                        minutes = int((total_seconds % 3600) // 60)
                        seconds = int(total_seconds % 60)
                        
                        from datetime import time
                        time_obj = time(hours, minutes, seconds)
                        # Format via strftime to avoid Excel fallback artifact
                        return time_obj.strftime("%H:%M:%S")
                    
                    # Handle other time formats
                    else:
                        # Parse each field separately with errors='coerce'
                        parsed_time = pd.to_datetime(time_value, errors='coerce')
                        if pd.notna(parsed_time):
                            # Format via strftime to avoid Excel fallback artifact
                            return parsed_time.strftime("%H:%M:%S")
                            
                except Exception as e:
                    self.logger.debug(f"Error parsing time from {col}: {e}")
                    continue
        
        return None

    def get_time_of_day(self, time_val):
        """Time of day calculation matching M Code exactly."""
        if pd.isna(time_val):
            return "Unknown"
        
        hour = time_val.hour
        if 0 <= hour < 4:
            return "00:00–03:59 Early Morning"
        elif 4 <= hour < 8:
            return "04:00–07:59 Morning"
        elif 8 <= hour < 12:
            return "08:00–11:59 Morning Peak"
        elif 12 <= hour < 16:
            return "12:00–15:59 Afternoon"
        elif 16 <= hour < 20:
            return "16:00–19:59 Evening Peak"
        else:
            return "20:00–23:59 Night"

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

    def get_period(self, incident_date):
        """Enhanced period calculation with logging"""
        if pd.isna(incident_date):
            return "Historical"
        
        try:
            # Handle different input types
            if isinstance(incident_date, str):
                inc_date = pd.to_datetime(incident_date, format="%m/%d/%y").date()
            elif hasattr(incident_date, 'date'):
                # Handle datetime objects
                inc_date = incident_date.date()
            else:
                # Assume it's already a date object
                inc_date = incident_date
            
            today = datetime.now().date()
            days_diff = (today - inc_date).days
            
            # Log calculation for debugging
            if hasattr(self, 'period_debug_count'):
                self.period_debug_count += 1
                if self.period_debug_count <= 5:
                    self.logger.info(f"Period calc - Date: {inc_date}, Days diff: {days_diff}")
            
            if days_diff <= 7:
                return "7-Day"
            elif days_diff <= 28:
                return "28-Day"
            else:
                return "YTD"
                
        except Exception as e:
            self.logger.warning(f"Period calculation error for date {incident_date}: {e}")
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
                if len(parts) >= 2:
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
            "Motor Vehicle Theft", "Robbery", "Burglary – Auto", 
            "Sexual", "Burglary – Commercial", "Burglary – Residence"
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
        """Process RMS data with lowercase_with_underscores standardization, focused on crime data without CAD-specific columns."""
        # Initialize period debug counter
        self.period_debug_count = 0
        
        with self.monitor_performance(f"RMS Data Processing - {rms_file.name}"):
            self.logger.info(f"Processing RMS data: {rms_file.name}")
            
            try:
                with self.monitor_performance("RMS File Loading"):
                    rms_df = pd.read_excel(rms_file, engine='openpyxl')
                    self.logger.info(f"Loaded RMS file with {len(rms_df)} rows and {len(rms_df.columns)} columns")
                    self.logger.info(f"RMS columns found: {list(rms_df.columns)}")
            except Exception as e:
                self.logger.error(f"Error loading RMS file: {e}")
                return pd.DataFrame()

            # DEBUG: Check raw time columns before mapping
            time_related_cols = [col for col in rms_df.columns if 'time' in col.lower()]
            self.logger.info(f"Raw time columns found: {time_related_cols}")

            for col in time_related_cols:
                if col in rms_df.columns:
                    populated = rms_df[col].notna().sum()
                    self.logger.info(f"  {col}: {populated}/{len(rms_df)} populated")
                    if populated > 0:
                        sample_vals = rms_df[col].dropna().head(3).tolist()
                        sample_types = [type(val).__name__ for val in sample_vals]
                        self.logger.info(f"  Sample values: {sample_vals}")
                        self.logger.info(f"  Sample types: {sample_types}")

            # NORMALIZE HEADERS: Apply lowercase snake_case normalization immediately after loading
            with self.monitor_performance("RMS Header Normalization & Column Mapping"):
                rms_df = normalize_headers(rms_df)
                self.logger.info(f"Normalized RMS headers to lowercase snake_case: {list(rms_df.columns)}")

                # Apply column mapping only for columns that exist
                column_mapping = self.get_rms_column_mapping()
                existing_mapping = {k: v for k, v in column_mapping.items() if k in rms_df.columns}
                rms_df = rms_df.rename(columns=existing_mapping)
        self.logger.info(f"Applied column mapping: {existing_mapping}")
        
        # DEBUG: Check mapped time columns
        mapped_time_cols = ['incident_time', 'incident_time_between', 'report_time']
        for col in mapped_time_cols:
            if col in rms_df.columns:
                populated = rms_df[col].notna().sum()
                self.logger.info(f"Mapped {col}: {populated}/{len(rms_df)} populated")
                if populated > 0:
                    sample_vals = rms_df[col].dropna().head(3).tolist()
                    sample_types = [type(val).__name__ for val in sample_vals]
                    self.logger.info(f"  Sample values: {sample_vals}")
                    self.logger.info(f"  Sample types: {sample_types}")
        
        # Convert ALL remaining columns to lowercase_with_underscores (redundant but safe)
        rms_df.columns = [self.convert_to_lowercase_with_underscores(col) for col in rms_df.columns]
        
        # Clean text columns
        text_columns = rms_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            rms_df[col] = rms_df[col].apply(self.clean_text_comprehensive)

        # DEBUG: Check available date columns before cascading
        date_columns = [col for col in rms_df.columns if 'date' in col.lower()]
        self.logger.info(f"Available date columns: {date_columns}")
        
        # Check for date columns that cascade_date function expects
        expected_date_cols = ['incident_date', 'incident_date_between', 'report_date']
        missing_date_cols = [col for col in expected_date_cols if col not in rms_df.columns]
        if missing_date_cols:
            self.logger.warning(f"Missing expected date columns: {missing_date_cols}")
        
        # Sample raw date values before cascading
        for col in expected_date_cols:
            if col in rms_df.columns:
                populated = rms_df[col].notna().sum()
                self.logger.info(f"{col} populated: {populated}/{len(rms_df)}")
                if populated > 0:
                    sample = rms_df[col].dropna().head(3).tolist()
                    self.logger.info(f"Sample {col} values: {sample}")

        # Enhanced RMS date/time cascade logic according to specification
        # 1) Cascading date - using proper column names
        rms_df["incident_date"] = (
            pd.to_datetime(rms_df["incident_date"], errors="coerce")
              .fillna(pd.to_datetime(rms_df["incident_date_between"], errors="coerce"))
              .fillna(pd.to_datetime(rms_df["report_date"], errors="coerce"))
              .dt.date
        )
        
        # Convert incident_date to mm/dd/yy string format
        rms_df["incident_date"] = rms_df["incident_date"].apply(
            lambda d: d.strftime("%m/%d/%y") if pd.notna(d) else None
        )
        
        # DEBUG: Check incident_date population after cascading and formatting
        date_populated = rms_df['incident_date'].notna().sum()
        self.logger.info(f"Incident dates after cascading and formatting: {date_populated}/{len(rms_df)}")
        if date_populated > 0:
            sample_cascaded_dates = rms_df['incident_date'].dropna().head(5).tolist()
            self.logger.info(f"Sample formatted dates: {sample_cascaded_dates}")
        else:
            self.logger.error("NO INCIDENT DATES POPULATED AFTER CASCADING - This will cause all records to be marked as 'Historical'")
        
        # 2) Enhanced RMS time cascade logic with robust fallback
        def extract_time_from_timedelta(time_val):
            """Extract time string from various time formats including Timedelta"""
            if pd.isna(time_val):
                return None
            
            try:
                # Handle pandas Timedelta objects
                if isinstance(time_val, pd.Timedelta):
                    total_seconds = int(time_val.total_seconds())
                    hours = (total_seconds // 3600) % 24
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                # Handle time objects
                elif hasattr(time_val, 'hour'):
                    return time_val.strftime("%H:%M:%S")
                
                # Handle string values
                elif isinstance(time_val, str):
                    if ':' in time_val:
                        return time_val.strip()
                
                return None
            except:
                return None

        # DEBUG: Track cascade effectiveness
        t1_valid = rms_df["incident_time"].notna().sum()
        t2_valid = rms_df["incident_time_between"].notna().sum()  
        t3_valid = rms_df["report_time"].notna().sum()

        self.logger.info(f"Time cascade inputs - Primary: {t1_valid}, Secondary: {t2_valid}, Tertiary: {t3_valid}")

        # Apply 3-tier time cascade AFTER column mapping
        t1 = rms_df["incident_time"].apply(extract_time_from_timedelta)
        t2 = rms_df["incident_time_between"].apply(extract_time_from_timedelta) 
        t3 = rms_df["report_time"].apply(extract_time_from_timedelta)

        # VALIDATION: Log count of valid times after each cascade step
        t1_valid = t1.notna().sum()
        t2_valid = t2.notna().sum()
        t3_valid = t3.notna().sum()
        self.logger.info(f"Time cascade validation - t1 (incident_time): {t1_valid}/{len(rms_df)} valid")
        self.logger.info(f"Time cascade validation - t2 (incident_time_between): {t2_valid}/{len(rms_df)} valid")
        self.logger.info(f"Time cascade validation - t3 (report_time): {t3_valid}/{len(rms_df)} valid")
        
        # Show sample extracted time values
        if t1_valid > 0:
            sample_t1 = t1.dropna().head(3).tolist()
            self.logger.info(f"Sample t1 times: {sample_t1}")
        if t2_valid > 0:
            sample_t2 = t2.dropna().head(3).tolist()
            self.logger.info(f"Sample t2 times: {sample_t2}")
        if t3_valid > 0:
            sample_t3 = t3.dropna().head(3).tolist()
            self.logger.info(f"Sample t3 times: {sample_t3}")

        rms_df['incident_time'] = t1.fillna(t2).fillna(t3)
        
        # After cascade
        final_valid = rms_df['incident_time'].notna().sum()
        self.logger.info(f"Time cascade result: {final_valid}/{len(rms_df)} valid times")
        
        # VALIDATION: Ensure incident_time column populates successfully
        time_populated = rms_df['incident_time'].notna().sum()
        self.logger.info(f"Final incident_time populated: {time_populated}/{len(rms_df)}")
        if time_populated > 0:
            sample_times = rms_df['incident_time'].dropna().head(5).tolist()
            self.logger.info(f"Sample final formatted times: {sample_times}")
        else:
            self.logger.error("CRITICAL: incident_time column is completely empty after cascade!")
        
        # 3) Time-of-Day Buckets & Sort Order implementation
        # Apply map_tod function to cleaned incident_time
        rms_df['time_of_day'] = rms_df['incident_time'].apply(self.map_tod)
        
        # VALIDATION: Verify time_of_day calculation works with fixed times
        time_of_day_distribution = rms_df['time_of_day'].value_counts()
        self.logger.info(f"Time of day distribution: {time_of_day_distribution.to_dict()}")
        
        # Check for "Unknown" values when incident_time is valid
        unknown_count = (rms_df['time_of_day'] == 'Unknown').sum()
        valid_time_count = rms_df['incident_time'].notna().sum()
        self.logger.info(f"Time of day validation - Unknown: {unknown_count}, Valid times: {valid_time_count}")
        
        if unknown_count > 0 and valid_time_count > 0:
            self.logger.warning(f"⚠️ {unknown_count} records have 'Unknown' time_of_day despite having valid incident_time")
        
        # Generate sort order for time of day
        rms_df["time_of_day_sort_order"] = rms_df["time_of_day"].apply(self.get_time_of_day_sort_order)
        
        # VALIDATION: Verify sort_order values are correct integers
        sort_order_distribution = rms_df['time_of_day_sort_order'].value_counts().sort_index()
        self.logger.info(f"Time of day sort order distribution: {sort_order_distribution.to_dict()}")
        
        # 4) Date sort key (convert back to datetime for sorting)
        rms_df["date_sort_key"] = rms_df["incident_date"].apply(
            lambda d: int(pd.to_datetime(d, format="%m/%d/%y").strftime("%Y%m%d")) if pd.notna(d) else np.nan
        )
        
        # DEBUG: Check incident_date values before period calculation
        incident_dates_sample = rms_df['incident_date'].dropna().head(5).tolist()
        self.logger.info(f"Sample incident_date values: {incident_dates_sample}")
        self.logger.info(f"Null incident_date count: {rms_df['incident_date'].isna().sum()}")
        self.logger.info(f"Date types: {rms_df['incident_date'].dtype}")
        
        # Convert string dates back to datetime for period calculation
        rms_df['period'] = rms_df['incident_date'].apply(
            lambda d: self.get_period(pd.to_datetime(d, format="%m/%d/%y")) if pd.notna(d) else "Historical"
        )
        
        # DEBUG: Check period distribution immediately after calculation
        period_distribution = rms_df['period'].value_counts()
        self.logger.info(f"Period calculation results: {period_distribution.to_dict()}")
        
        # Additional validation: Check if we have recent dates
        if 'incident_date' in rms_df.columns:
            recent_7_day = rms_df[rms_df['period'] == '7-Day']['incident_date'].count()
            recent_28_day = rms_df[rms_df['period'] == '28-Day']['incident_date'].count()
            ytd_count = rms_df[rms_df['period'] == 'YTD']['incident_date'].count()
            historical_count = rms_df[rms_df['period'] == 'Historical']['incident_date'].count()
            
            self.logger.info(f"Date/Period Analysis Summary:")
            self.logger.info(f"  - 7-Day period records: {recent_7_day}")
            self.logger.info(f"  - 28-Day period records: {recent_28_day}")
            self.logger.info(f"  - YTD period records: {ytd_count}")
            self.logger.info(f"  - Historical period records: {historical_count}")
            
            if recent_7_day == 0 and recent_28_day == 0 and ytd_count == 0:
                self.logger.warning("⚠️ ALL RECORDS DEFAULTING TO HISTORICAL - Date processing issue detected!")
            else:
                self.logger.info("✅ Date processing working correctly - mix of periods found")
        
        # Period, Day_of_Week & Cycle_Name Fixes - Enhanced implementation
        # Convert string dates back to datetime for calculations
        incident_date_dt = rms_df['incident_date'].apply(
            lambda d: pd.to_datetime(d, format="%m/%d/%y", errors='coerce') if pd.notna(d) else None
        )
        
        # Season
        rms_df['season'] = incident_date_dt.apply(self.get_season)
        
        # Day of Week & Type
        rms_df['day_of_week'] = incident_date_dt.apply(
            lambda x: x.strftime('%A') if pd.notna(x) else None
        )
        rms_df['day_type'] = rms_df['day_of_week'].isin(['Saturday', 'Sunday']).map({True: 'Weekend', False: 'Weekday'})
        
        # Cycle Name (uses fixed incident_date)
        rms_df['cycle_name'] = incident_date_dt.apply(
            lambda x: self.get_cycle_for_date(x, self.cycle_calendar) if pd.notna(x) else None
        )

        # Address validation and standardization
        if 'full_address_raw' in rms_df.columns:
            rms_df['location'] = rms_df['full_address_raw'].apply(self.validate_hackensack_address)
            self.logger.info(f"Address validation: {rms_df['location'].notna().sum()}/{len(rms_df)} addresses validated")
        else:
            rms_df['location'] = None
            self.logger.warning("full_address_raw column not found - location will be None")
        
        rms_df['block'] = rms_df['location'].apply(self.calculate_block)
        self.logger.info(f"Block calculation: {rms_df['block'].notna().sum()}/{len(rms_df)} blocks calculated")

        # Grid and post backfill using reference data
        def backfill_grid_post_row(row):
            grid, post = self.backfill_grid_post(
                row.get('location'),
                row.get('grid'),
                row.get('zone')
            )
            return pd.Series({'grid': grid, 'post': post})

        backfilled = rms_df.apply(backfill_grid_post_row, axis=1)
        rms_df['grid'] = backfilled['grid']
        rms_df['post'] = backfilled['post']
        self.logger.info(f"Grid/Post backfill: {rms_df['grid'].notna().sum()}/{len(rms_df)} grids, {rms_df['post'].notna().sum()}/{len(rms_df)} posts")

        # Clean and combine incident types - safe column access
        for i in [1, 2, 3]:
            col_name = f'incident_type_{i}'
            if col_name in rms_df.columns:
                rms_df[f'incident_type_{i}_cleaned'] = rms_df[col_name].apply(self.clean_incident_type)

        # Use incident_type_1 as primary incident type (no unpivoting)
        # This prevents the 135→300 record expansion issue
        if 'incident_type_1' in rms_df.columns:
            rms_df['incident_type'] = rms_df['incident_type_1'].apply(self.clean_incident_type)
        else:
            rms_df['incident_type'] = None
        
        # Combine all incidents for reference only
        def combine_incidents(row):
            incidents = []
            for i in [1, 2, 3]:
                cleaned_col = f'incident_type_{i}_cleaned'
                if cleaned_col in row and pd.notna(row[cleaned_col]):
                    incidents.append(row[cleaned_col])
            return ", ".join(incidents) if incidents else None

        rms_df['all_incidents'] = rms_df.apply(combine_incidents, axis=1)
        
        # Apply the new incident type extraction function
        rms_df["incident_type"] = rms_df["all_incidents"].apply(extract_incident_types)
        
        # Vehicle processing - safe column access with proper casing
        rms_df['vehicle_1'] = rms_df.apply(
            lambda row: self.format_vehicle(
                row.get('reg_state_1'), row.get('registration_1'),
                row.get('make_1'), row.get('model_1')
            ), axis=1
        )
        
        rms_df['vehicle_2'] = rms_df.apply(
            lambda row: self.format_vehicle(
                row.get('reg_state_2'), row.get('registration_2'),
                row.get('make_2'), row.get('model_2')
            ), axis=1
        )

        # Combined vehicles (only when both exist)
        def combine_vehicles(row):
            v1, v2 = row.get('vehicle_1'), row.get('vehicle_2')
            if pd.notna(v1) and pd.notna(v2):
                return f"{v1} | {v2}"
            return None

        rms_df['vehicle_1_and_vehicle_2'] = rms_df.apply(combine_vehicles, axis=1)

        # Vehicle Fields Uppercasing - Enhanced implementation
        for col in ['vehicle_1', 'vehicle_2', 'vehicle_1_and_vehicle_2']:
            if col in rms_df.columns:
                rms_df[col] = rms_df[col].str.upper().where(rms_df[col].notna(), None)

        # Convert squad column to uppercase
        if 'squad' in rms_df.columns:
            rms_df['squad'] = rms_df['squad'].apply(lambda x: x.upper() if pd.notna(x) else None)

        # Narrative Cleaning - Enhanced implementation with comprehensive text cleaning
        def clean_narrative(text: str) -> str:
            if pd.isna(text):
                return None
            
            # Use the comprehensive text cleaning function
            cleaned = self.clean_text_comprehensive(text)
            if not cleaned:
                return None
            
            # Additional narrative-specific cleaning
            # Remove common problematic patterns in police narratives
            cleaned = re.sub(r'#\(cr\)#\(lf\)|#\(lf\)|#\(cr\)', ' ', cleaned)
            cleaned = re.sub(r'(\s*[\?\-]\s*){2,}', ' ', cleaned)  # Remove repeated question marks/dashes
            
            # Normalize whitespace and trim
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            # Apply title case for consistency
            return cleaned.title() if cleaned else None

        if 'narrative' in rms_df.columns:
            rms_df['narrative'] = rms_df['narrative'].apply(clean_narrative)
            # Additional whitespace normalization to ensure consistent formatting
            rms_df['narrative'] = rms_df['narrative'].str.replace(r'\s+', ' ', regex=True).str.strip()
            self.logger.info(f"Narrative cleaning: {rms_df['narrative'].notna().sum()}/{len(rms_df)} narratives cleaned")
        else:
            rms_df['narrative'] = None
            self.logger.warning("narrative column not found - narrative will be None")

        # HEADER VALIDATION: Enforce lowercase snake_case headers
        header_validation = self.validate_lowercase_snake_case_headers(rms_df, "RMS")
        if header_validation['overall_status'] == 'FAIL':
            invalid_headers = header_validation['non_compliant_columns']
            self.logger.error(f"RMS headers validation failed. Invalid headers: {invalid_headers}")
            raise ValueError(f"RMS headers must be lowercase snake_case. Invalid headers: {invalid_headers}")
        else:
            self.logger.info("RMS headers validation passed - all headers are lowercase snake_case")

        # Final column selection - Include incident_type as primary field
        desired_columns = [
            'case_number', 'incident_date', 'incident_time', 'time_of_day', 'time_of_day_sort_order',
            'period', 'season', 'day_of_week', 'day_type', 'location', 'block', 
            'grid', 'post', 'incident_type', 'all_incidents', 'vehicle_1', 'vehicle_2', 
            'vehicle_1_and_vehicle_2', 'narrative', 'total_value_stolen', 
            'total_value_recovered', 'squad', 'officer_of_record', 'nibrs_classification', 'cycle_name',
            'case_status'
        ]

        # Select only columns that exist in the dataframe
        existing_columns = [col for col in desired_columns if col in rms_df.columns]
        rms_final = rms_df[existing_columns].copy()

        # DEBUG: RMS filtering analysis
        self.logger.info(f"RMS records before filtering: {len(rms_final)}")
        
        # Check period column values
        if 'period' in rms_final.columns:
            period_counts = rms_final['period'].value_counts()
            self.logger.info(f"Period distribution: {period_counts.to_dict()}")
            non_historical = rms_final[rms_final['period'] != 'Historical']
            self.logger.info(f"Non-historical records: {len(non_historical)}")
        else:
            self.logger.warning("Period column not found in RMS data")
        
        # Check case number values
        if 'case_number' in rms_final.columns:
            self.logger.info(f"Sample case numbers: {rms_final['case_number'].head(5).tolist()}")
            excluded_case = rms_final[rms_final['case_number'] == '25-057654']
            self.logger.info(f"Records with excluded case number '25-057654': {len(excluded_case)}")
        else:
            self.logger.warning("Case number column not found in RMS data")
        
        # Check incident_date population
        if 'incident_date' in rms_final.columns:
            date_populated = rms_final['incident_date'].notna().sum()
            self.logger.info(f"Incident dates populated: {date_populated}/{len(rms_final)}")
            if date_populated > 0:
                sample_dates = rms_final['incident_date'].dropna().head(5).tolist()
                self.logger.info(f"Sample incident dates: {sample_dates}")
                date_range_min = rms_final['incident_date'].min()
                date_range_max = rms_final['incident_date'].max()
                self.logger.info(f"Date range: {date_range_min} to {date_range_max}")
            else:
                self.logger.warning("No incident dates populated - this may cause period calculation issues")
        else:
            self.logger.warning("Incident date column not found in RMS data")

        # Apply filtering with individual steps for debugging
        initial_count = len(rms_final)
        
        if 'case_number' in rms_final.columns and 'period' in rms_final.columns:
            # Case number filter
            case_filter = rms_final['case_number'] != '25-057654'
            rms_final = rms_final[case_filter]
            self.logger.info(f"After case number filter: {len(rms_final)}/{initial_count} records")
            
            # Period filter  
            period_filter = rms_final['period'] != 'Historical'
            rms_final = rms_final[period_filter]
            self.logger.info(f"After period filter: {len(rms_final)}/{initial_count} records")
            
            # Case status filter - exclude specific statuses
            if 'case_status' in rms_final.columns:
                statuses_to_exclude = ["TOT Outside Jurisdiction", "Unfounded / Closed", "No Investigation"]
                status_filter = ~rms_final['case_status'].isin(statuses_to_exclude)
                rms_final = rms_final[status_filter]
                self.logger.info(f"After case status filter: {len(rms_final)}/{initial_count} records")
            else:
                self.logger.warning("case_status column not found - skipping case status filtering")
        else:
            missing_cols = []
            if 'case_number' not in rms_final.columns:
                missing_cols.append('case_number')
            if 'period' not in rms_final.columns:
                missing_cols.append('period')
            self.logger.warning(f"Skipping filtering due to missing columns: {missing_cols}")

        self.logger.info(f"RMS processing complete: {len(rms_final)} records after filtering")
        self.logger.info(f"Final RMS columns: {list(rms_final.columns)}")
        self.logger.info("REMOVED CAD-specific columns: incident_type, crime_category, response_type")
        
        # Optimize memory usage before returning
        rms_final = self.optimize_dataframe_memory(rms_final, "RMS Final Dataset")
        
        # Force garbage collection
        gc.collect()
        
        return rms_final

    def process_cad_data(self, cad_file, ref_lookup=None):
        """Process CAD data with enhanced incident mapping and lowercase snake_case headers."""
        with self.monitor_performance(f"CAD Data Processing - {cad_file.name}"):
            self.logger.info(f"Processing CAD data: {cad_file.name}")
        
        try:
            # Load CAD file with "How Reported" and "Grid" columns forced to string type to prevent Excel auto-parsing
            cad_df = pd.read_excel(cad_file, engine='openpyxl', dtype={"How Reported": str, "Grid": str})
            self.logger.info(f"Loaded CAD file with {len(cad_df)} rows and {len(cad_df.columns)} columns")
            self.logger.info(f"CAD columns found: {list(cad_df.columns)}")
            self.logger.info("Applied dtype={'How Reported': str} to prevent Excel auto-parsing '9-1-1' as date")
            
            # Additional fix for "How Reported" column - convert any date-like values back to "9-1-1"
            if "How Reported" in cad_df.columns:
                # Check for common date patterns that result from "9-1-1" conversion
                date_patterns = [
                    '2001-09-01', '2001-09-01 00:00:00', '09/01/2001', '9/1/2001', 
                    '2001-09-01T00:00:00', '2001-09-01 00:00:00.000000',
                    '2025-09-01', '2025-09-01 00:00:00', '09/01/2025', '9/1/2025',
                    '2025-09-01T00:00:00', '2025-09-01 00:00:00.000000'
                ]
                
                # Convert any date-like values back to "9-1-1"
                for pattern in date_patterns:
                    cad_df["How Reported"] = cad_df["How Reported"].replace(pattern, "9-1-1")
                
                # Also check for any datetime objects and convert them
                cad_df["How Reported"] = cad_df["How Reported"].astype(str).apply(
                    lambda x: "9-1-1" if any(pattern in str(x) for pattern in date_patterns) else x
                )
                
                # Enhanced check for any September 1st date (common misinterpretation of 9-1-1)
                def fix_september_first(value):
                    if pd.isna(value):
                        return value
                    text = str(value).strip()
                    # Check if it matches September 1st pattern (9/1/YYYY or 09/01/YYYY)
                    if re.match(r'^(9|09)[/-](1|01)[/-]\d{4}$', text):
                        return "9-1-1"
                    return value
                
                cad_df["How Reported"] = cad_df["How Reported"].apply(fix_september_first)
                
                self.logger.info("Applied enhanced fixes to prevent '9-1-1' date conversion")
                
        except Exception as e:
            self.logger.error(f"Error loading CAD file: {e}")
            return pd.DataFrame()

        # Apply column mapping FIRST (before normalization) only for columns that exist
        column_mapping = self.get_cad_column_mapping()
        existing_mapping = {k: v for k, v in column_mapping.items() if k in cad_df.columns}
        cad_df = cad_df.rename(columns=existing_mapping)
        self.logger.info(f"Applied column mapping: {existing_mapping}")

        # NORMALIZE HEADERS: Apply lowercase snake_case normalization after column mapping
        cad_df = normalize_headers(cad_df)
        self.logger.info(f"Normalized CAD headers to lowercase snake_case: {list(cad_df.columns)}")

        # Clean text columns
        text_columns = cad_df.select_dtypes(include=['object']).columns
        for col in text_columns:
            cad_df[col] = cad_df[col].apply(self.clean_text_comprehensive)

        # Fix how_reported 9-1-1 date issue
        if 'how_reported' in cad_df.columns:
            cad_df['how_reported'] = cad_df['how_reported'].apply(self.clean_how_reported_911)

        # ENHANCED: Load call type reference if not provided and perform incident mapping
        if ref_lookup is None:
            ref_lookup, _ = self.load_call_type_reference_enhanced()
        
        # Map incident to response_type and category_type using proper CallType_Categories.xlsx mapping
        if 'incident' in cad_df.columns:
            # Ensure the incident values are properly processed
            cad_df['incident'] = cad_df['incident'].replace('', None)
            
            self.logger.info(f"Starting proper CallType_Categories.xlsx mapping for {len(cad_df)} CAD records")
            self.logger.info(f"Sample incident values: {cad_df['incident'].dropna().head(5).tolist()}")
            
            # Load the CallType_Categories.xlsx file for proper mapping
            call_type_file = self.project_path / '10_Refrence_Files' / 'CallType_Categories.xlsx'
            if call_type_file.exists():
                try:
                    call_type_df = pd.read_excel(call_type_file, engine='openpyxl')
                    self.logger.info(f"Loaded CallType_Categories.xlsx with {len(call_type_df)} records")
                    self.logger.info(f"CallType columns: {list(call_type_df.columns)}")
                    
                    # Create a mapping dictionary for fast lookup
                    call_type_mapping = {}
                    for _, row in call_type_df.iterrows():
                        incident = str(row.get('Incident', '')).strip()
                        if incident:
                            call_type_mapping[incident.upper()] = {
                                'response_type': row.get('Response Type', 'Unknown'),
                                'category_type': row.get('Category Type', 'Other')
                            }
                    
                    self.logger.info(f"Created mapping dictionary with {len(call_type_mapping)} entries")
                    
                    # Apply mapping to each incident with partial matching
                    response_types = []
                    category_types = []
                    
                    for incident in cad_df['incident']:
                        if pd.isna(incident) or not incident:
                            response_types.append('Unknown')
                            category_types.append('Other')
                        else:
                            incident_clean = str(incident).strip()
                            incident_upper = incident_clean.upper()
                            
                            # First try exact match
                            if incident_upper in call_type_mapping:
                                response_types.append(call_type_mapping[incident_upper]['response_type'])
                                category_types.append(call_type_mapping[incident_upper]['category_type'])
                            else:
                                # Try partial matching - check if any reference incident contains this incident
                                matched = False
                                for ref_incident, mapping in call_type_mapping.items():
                                    if incident_upper in ref_incident or ref_incident in incident_upper:
                                        response_types.append(mapping['response_type'])
                                        category_types.append(mapping['category_type'])
                                        matched = True
                                        break
                                
                                if not matched:
                                    # Fallback to keyword-based mapping
                                    fallback_result = self.map_call_type(incident)
                                    response_types.append(fallback_result[0] if fallback_result else 'Unknown')
                                    category_types.append(fallback_result[1] if fallback_result else 'Other')
                    
                    # Add the mapped columns with _cad suffix as requested
                    cad_df['response_type_cad'] = response_types
                    cad_df['category_type_cad'] = category_types
                    
                    # Also add the main response_type and category_type columns for compatibility
                    cad_df['response_type'] = response_types
                    cad_df['category_type'] = category_types
                    
                except Exception as e:
                    self.logger.error(f"Error loading CallType_Categories.xlsx: {e}")
                    # Fallback to original mapping method
                    mapping_results = cad_df['incident'].apply(self.map_call_type)
                    response_types = [result[0] if result else None for result in mapping_results]
                    category_types = [result[1] if result else None for result in mapping_results]
                    cad_df['response_type_cad'] = response_types
                    cad_df['category_type_cad'] = category_types
            else:
                self.logger.warning(f"CallType_Categories.xlsx not found at {call_type_file}")
                # Fallback to original mapping method
                mapping_results = cad_df['incident'].apply(self.map_call_type)
                response_types = [result[0] if result else None for result in mapping_results]
                category_types = [result[1] if result else None for result in mapping_results]
                cad_df['response_type_cad'] = response_types
                cad_df['category_type_cad'] = category_types
            
            # Calculate mapping statistics
            total_incidents = len(cad_df)
            mapped_count = sum(1 for rt in cad_df['response_type_cad'] if rt and rt != 'Unknown')
            unmapped_count = total_incidents - mapped_count
            mapping_rate = (mapped_count / total_incidents) * 100 if total_incidents > 0 else 0
            
            # Log mapping results
            self.logger.info(f"CallType_Categories.xlsx mapping results:")
            self.logger.info(f"  - Total incidents: {total_incidents}")
            self.logger.info(f"  - Mapped incidents: {mapped_count}")
            self.logger.info(f"  - Unmapped incidents: {unmapped_count}")
            self.logger.info(f"  - Mapping rate: {mapping_rate:.1f}%")
            
            # Log category distribution
            category_counts = pd.Series(cad_df['category_type_cad']).value_counts()
            self.logger.info(f"Category type distribution: {category_counts.to_dict()}")
            response_counts = pd.Series(cad_df['response_type_cad']).value_counts().head(10)
            self.logger.info(f"Top 10 response types: {response_counts.to_dict()}")
            
            # Keep both _cad suffix columns AND main columns for compatibility
            # sourced from Excel's Response_Type/Category_Type as specified
            
            # First, ensure we have the _cad suffix columns populated
            cad_df['response_type_cad'] = cad_df['response_type_cad'].fillna('Unknown')
            cad_df['category_type_cad'] = cad_df['category_type_cad'].fillna('Other')
            
            # Ensure main columns exist and are populated (for compatibility)
            cad_df['response_type'] = cad_df['response_type_cad']
            cad_df['category_type'] = cad_df['category_type_cad']
            
            # Log coverage on final columns
            response_coverage = (cad_df['response_type'].notna().sum() / len(cad_df)) * 100
            category_coverage = (cad_df['category_type'].notna().sum() / len(cad_df)) * 100
            
            self.logger.info(f"Final column coverage:")
            self.logger.info(f"  - response_type coverage: {response_coverage:.1f}%")
            self.logger.info(f"  - category_type coverage: {category_coverage:.1f}%")
            
        else:
            self.logger.warning("incident column not found in CAD data - cannot perform call type mapping")
            # Add empty columns to maintain schema
            cad_df['response_type'] = None
            cad_df['category_type'] = None

        # Time calculations with negative value handling
        def safe_calculate_time_response(row):
            try:
                time_call = pd.to_datetime(row.get('time_of_call'))
                time_dispatched = pd.to_datetime(row.get('time_dispatched'))
                
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

        def safe_calculate_time_spent(row):
            try:
                time_out = pd.to_datetime(row.get('time_out'))
                time_in = pd.to_datetime(row.get('time_in'))
                
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

        cad_df['time_response_minutes'] = cad_df.apply(safe_calculate_time_response, axis=1)
        cad_df['time_spent_minutes'] = cad_df.apply(safe_calculate_time_spent, axis=1)

        # Add formatted time columns
        cad_df['time_spent_formatted'] = cad_df['time_spent_minutes'].apply(self.format_time_spent_minutes)
        cad_df['time_response_formatted'] = cad_df['time_response_minutes'].apply(self.format_time_response_minutes)

        # Location processing - safe column access with proper population
        if 'full_address_raw' in cad_df.columns:
            cad_df['location'] = cad_df['full_address_raw'].apply(self.validate_hackensack_address)
        else:
            cad_df['location'] = None
        
        # Enhanced grid and post processing - use existing data more effectively
        if 'grid_raw' in cad_df.columns:
            # Use grid_raw directly, but clean it up properly
            cad_df['grid'] = cad_df['grid_raw'].copy()
            # Replace empty strings and NaN values with None
            cad_df['grid'] = cad_df['grid'].replace(['', 'nan', 'NaN', 'None', 'nan'], None)
            # Keep valid grid values as they are
            self.logger.info(f"Grid processing: {cad_df['grid'].notna().sum()}/{len(cad_df)} records have grid values")
        else:
            cad_df['grid'] = None
            
        # Ensure post is properly set
        if 'post' not in cad_df.columns:
            cad_df['post'] = None
        else:
            cad_df['post'] = cad_df['post'].replace(['', 'nan', 'NaN', 'None'], None)
            
        cad_df['block'] = cad_df['location'].apply(self.calculate_block)

        # Enhanced CAD notes parsing with metadata extraction using new parse_cad_notes function
        if 'cad_notes_raw' in cad_df.columns:
            # Apply the new parse_cad_notes function and extract results
            usernames = []
            timestamps = []
            cleaned_texts = []
            
            for raw_notes in cad_df['cad_notes_raw']:
                result = self.parse_cad_notes(raw_notes)
                usernames.append(result['CAD_Username'])
                timestamps.append(result['CAD_Timestamp'])
                cleaned_texts.append(result['CAD_Notes_Cleaned'])
            
            # Add the extracted columns
            cad_df['cad_username'] = usernames
            cad_df['cad_timestamp'] = timestamps
            cad_df['cad_notes_cleaned'] = cleaned_texts
            
            self.logger.info(f"CAD notes parsing complete: {len(cad_df)} records processed")
        
        # Add cycle_name column using cycle calendar lookup
        # For CAD data, we need to derive incident_date from time_of_call if available
        def get_cad_incident_date(row):
            if pd.notna(row.get('time_of_call')):
                try:
                    call_time = pd.to_datetime(row['time_of_call'])
                    return call_time.date()
                except:
                    return None
            return None
        
        cad_df['incident_date'] = cad_df.apply(get_cad_incident_date, axis=1)
        # Add cycle information with enhanced error handling
        try:
            cad_df['cycle_name'] = cad_df['incident_date'].apply(
                lambda x: self.get_cycle_for_date(x, self.cycle_calendar) if pd.notna(x) else None
            )
        except Exception as e:
            self.logger.warning(f"Error processing cycle names: {e}")
            cad_df['cycle_name'] = None

        # Validate that key columns have proper values before final selection
        # Check response_type population
        response_type_populated = cad_df['response_type'].notna().sum()
        self.logger.info(f"CAD response_type populated in {response_type_populated}/{len(cad_df)} records")
        
        # Check grid population  
        grid_populated = cad_df['grid'].notna().sum()
        self.logger.info(f"CAD grid populated in {grid_populated}/{len(cad_df)} records")
        
        # Check post population
        post_populated = cad_df['post'].notna().sum() if 'post' in cad_df.columns else 0
        self.logger.info(f"CAD post populated in {post_populated}/{len(cad_df)} records")
        
        # HEADER VALIDATION: Enforce lowercase snake_case headers
        header_validation = self.validate_lowercase_snake_case_headers(cad_df, "CAD")
        if header_validation['overall_status'] == 'FAIL':
            invalid_headers = header_validation['non_compliant_columns']
            self.logger.error(f"CAD headers validation failed. Invalid headers: {invalid_headers}")
            raise ValueError(f"CAD headers must be lowercase snake_case. Invalid headers: {invalid_headers}")
        else:
            self.logger.info("CAD headers validation passed - all headers are lowercase snake_case")
        
        # Final column selection with lowercase_with_underscores naming
        desired_columns = [
            'case_number', 'incident', 'response_type', 'category_type', 'response_type_cad', 'category_type_cad', 'how_reported', 
            'location', 'block', 'grid', 'post', 'time_of_call', 'time_dispatched', 
            'time_out', 'time_in', 'time_spent_minutes', 'time_response_minutes',
            'time_spent_formatted', 'time_response_formatted', 'officer', 'disposition', 
            'cad_notes_cleaned', 'cad_username', 'cad_timestamp', 'cycle_name'
        ]

        # Select only columns that exist in the dataframe
        existing_columns = [col for col in desired_columns if col in cad_df.columns]
        cad_final = cad_df[existing_columns].copy()

        self.logger.info(f"CAD processing complete: {len(cad_final)} records")
        self.logger.info(f"Final CAD columns: {list(cad_final.columns)}")
        
        # Optimize memory usage before returning
        cad_final = self.optimize_dataframe_memory(cad_final, "CAD Final Dataset")
        
        # Force garbage collection
        gc.collect()
        
        return cad_final

    def find_latest_files(self):
        """Find the latest files in each export directory."""
        latest_files = {}
        
        # Since both files are in the same directory, we need to identify them by filename
        cad_path = self.export_dirs['cad_exports']
        rms_path = self.export_dirs['rms_exports']
        
        if cad_path.exists():
            cad_files = [f for f in cad_path.glob("*.xlsx") if "CAD" in f.name.upper()]
            if cad_files:
                latest_cad = max(cad_files, key=lambda f: f.stat().st_mtime)
                latest_files['cad'] = latest_cad
                self.logger.info(f"Latest CAD file: {latest_cad.name}")
            else:
                self.logger.warning(f"No CAD Excel files found in {cad_path}")
        else:
            self.logger.warning(f"CAD directory not found: {cad_path}")
            
        if rms_path.exists():
            rms_files = [f for f in rms_path.glob("*.xlsx") if "RMS" in f.name.upper()]
            if rms_files:
                latest_rms = max(rms_files, key=lambda f: f.stat().st_mtime)
                latest_files['rms'] = latest_rms
                self.logger.info(f"Latest RMS file: {latest_rms.name}")
            else:
                self.logger.warning(f"No RMS Excel files found in {rms_path}")
        else:
            self.logger.warning(f"RMS directory not found: {rms_path}")
        
        return latest_files

    def process_final_pipeline(self):
        """Run the complete processing pipeline with standardized output."""
        with self.monitor_performance("Complete SCRPA Pipeline V8.5"):
            self.logger.info("Starting Comprehensive SCRPA Fix V8.5 pipeline...")
        
        latest_files = self.find_latest_files()
        
        if not latest_files:
            self.logger.error("No data files found to process")
            raise ValueError("No data files found")

        # Process RMS data
        rms_data = pd.DataFrame()
        if 'rms' in latest_files:
            try:
                rms_data = self.process_rms_data(latest_files['rms'])
                # Check if RMS processing failed and returned None
                if rms_data is None:
                    self.logger.error("RMS data processing failed - received None")
                    rms_data = pd.DataFrame()
            except Exception as e:
                self.logger.error(f"RMS data processing failed with exception: {e}")
                rms_data = pd.DataFrame()

        # Process CAD data with enhanced incident mapping
        cad_data = pd.DataFrame()
        mapping_diagnostics = None
        ref_diagnostics = None
        
        if 'cad' in latest_files:
            # Load reference data first for enhanced mapping
            ref_lookup, ref_diagnostics = self.load_call_type_reference_enhanced()
            
            # Process CAD data with reference lookup
            try:
                cad_data = self.process_cad_data(latest_files['cad'], ref_lookup)
                # Check if CAD processing failed and returned None
                if cad_data is None:
                    self.logger.error("CAD data processing failed - received None")
                    cad_data = pd.DataFrame()
            except Exception as e:
                self.logger.error(f"CAD data processing failed with exception: {e}")
                cad_data = pd.DataFrame()
            
            # Extract mapping diagnostics from CAD processing
            if cad_data is not None and not cad_data.empty and 'incident' in cad_data.columns:
                # Re-run mapping to get diagnostics for QC report
                _, _, mapping_diagnostics = self.map_incident_to_call_types_enhanced(
                    cad_data['incident'], ref_lookup
                )

        # Create output directory
        output_dir = self.project_path / '04_powerbi'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save individual datasets with cycle naming
        if rms_data is not None and not rms_data.empty:
            cycle_suffix = f"_{self.current_cycle}_{self.current_date}" if self.current_cycle and self.current_date else ""
            rms_output = output_dir / f'{self.current_cycle}_{self.current_date}_7Day_rms_data_standardized_v3.csv' if self.current_cycle and self.current_date else output_dir / 'rms_data_standardized_v3.csv'
            # Standardize data types before export
            rms_data = self.standardize_data_types(rms_data)
            # Validate headers before export
            header_val = self.validate_lowercase_snake_case_headers(rms_data, 'RMS')
            if header_val['overall_status']=='FAIL':
                raise ValueError(f"Invalid headers in RMS data: {header_val['non_compliant_columns']}")
            self.write_large_csv_efficiently(rms_data, rms_output)
            self.logger.info(f"RMS data saved: {rms_output}")

        if cad_data is not None and not cad_data.empty:
            cycle_suffix = f"_{self.current_cycle}_{self.current_date}" if self.current_cycle and self.current_date else ""
            cad_output = output_dir / f'{self.current_cycle}_{self.current_date}_7Day_cad_data_standardized_v2.csv' if self.current_cycle and self.current_date else output_dir / 'cad_data_standardized_v2.csv'
            # Standardize data types before export
            cad_data = self.standardize_data_types(cad_data)
            # Validate headers before export
            header_val = self.validate_lowercase_snake_case_headers(cad_data, 'CAD')
            if header_val['overall_status']=='FAIL':
                raise ValueError(f"Invalid headers in CAD data: {header_val['non_compliant_columns']}")
            self.write_large_csv_efficiently(cad_data, cad_output)
            self.logger.info(f"CAD data saved: {cad_output}")

        # Generate comprehensive QC report for CAD processing
        if cad_data is not None and not cad_data.empty and mapping_diagnostics and ref_diagnostics:
            qc_results = self.generate_enhanced_qc_report(
                cad_data, mapping_diagnostics, ref_diagnostics, output_dir
            )
            self.logger.info(f"Enhanced QC Report Status: {qc_results['overall_status']}")
            if qc_results['critical_issues']:
                self.logger.warning(f"Critical Issues Found: {qc_results['critical_issues']}")
            else:
                self.logger.info("All QC validations passed successfully")

        # Create properly matched dataset with RMS as master (LEFT JOIN)
        joined_result = None
        if rms_data is not None and not rms_data.empty and cad_data is not None and not cad_data.empty:
            self.logger.info(f"Starting CAD-RMS matching: RMS={len(rms_data)} records, CAD={len(cad_data)} records")
            
            # LEFT JOIN: RMS as master, CAD data added where case numbers match
            # Use case-insensitive matching on case_number
            rms_copy = rms_data.copy()
            cad_copy = cad_data.copy()
            
            # Create case-insensitive lookup keys
            rms_copy['_lookup_key'] = rms_copy['case_number'].astype(str).str.upper().str.strip()
            cad_copy['_lookup_key'] = cad_copy['case_number'].astype(str).str.upper().str.strip()
            
            # Add _cad suffix to CAD columns (except lookup key)
            cad_renamed = cad_copy.drop(columns=['_lookup_key']).add_suffix('_cad')
            cad_renamed['_lookup_key'] = cad_copy['_lookup_key']
            
            # Perform LEFT JOIN on lookup key
            joined_data = rms_copy.merge(
                cad_renamed,
                on='_lookup_key',
                how='left'
            )
            
            # Remove temporary lookup key
            joined_data = joined_data.drop(columns=['_lookup_key'])
            
            # ENHANCED: Implement CAD-first, RMS-fallback logic for response_type and category_type
            self.logger.info("Implementing CAD-first, RMS-fallback logic for response_type and category_type...")
            
            # Create response_type and category_type columns with CAD-first logic
            def cad_first_fallback(row, cad_col, rms_col=None):
                """CAD-first fallback logic: use CAD if available, otherwise use RMS if available"""
                if pd.notna(row.get(cad_col)):
                    return row[cad_col]
                elif rms_col and pd.notna(row.get(rms_col)):
                    return row[rms_col]
                else:
                    return None
            
            # Apply CAD-first logic for response_type
            joined_data['response_type'] = joined_data.apply(
                lambda row: cad_first_fallback(row, 'response_type_cad'), axis=1
            )
            
            # Apply CAD-first logic for category_type
            joined_data['category_type'] = joined_data.apply(
                lambda row: cad_first_fallback(row, 'category_type_cad'), axis=1
            )
            
            # Merge Logic: Deduplicate and Reapply Cleaning - Enhanced implementation
            # After merge with suffixes (_cad, _rms):
            if 'incident_date_cad' in joined_data.columns and 'incident_date_rms' in joined_data.columns:
                joined_data['incident_date'] = joined_data['incident_date_cad'].fillna(joined_data['incident_date_rms'])
            elif 'incident_date_cad' in joined_data.columns:
                joined_data['incident_date'] = joined_data['incident_date_cad']
            elif 'incident_date_rms' in joined_data.columns:
                joined_data['incident_date'] = joined_data['incident_date_rms']
            
            if 'incident_time_cad' in joined_data.columns and 'incident_time_rms' in joined_data.columns:
                joined_data['incident_time'] = joined_data['incident_time_cad'].fillna(joined_data['incident_time_rms'])
            elif 'incident_time_cad' in joined_data.columns:
                joined_data['incident_time'] = joined_data['incident_time_cad']
            elif 'incident_time_rms' in joined_data.columns:
                joined_data['incident_time'] = joined_data['incident_time_rms']
            
            # Reapply key fixes:
            if 'incident_time' in joined_data.columns:
                joined_data['time_of_day'] = joined_data['incident_time'].apply(self.map_tod)
            
            # Ensure response_type and category_type are properly set
            if 'response_type_cad' in joined_data.columns and 'response_type_rms' in joined_data.columns:
                joined_data['response_type'] = joined_data['response_type_cad'].fillna(joined_data['response_type_rms'])
            elif 'response_type_cad' in joined_data.columns:
                joined_data['response_type'] = joined_data['response_type_cad']
            elif 'response_type_rms' in joined_data.columns:
                joined_data['response_type'] = joined_data['response_type_rms']
            
            if 'category_type_cad' in joined_data.columns and 'category_type_rms' in joined_data.columns:
                joined_data['category_type'] = joined_data['category_type_cad'].fillna(joined_data['category_type_rms'])
            elif 'category_type_cad' in joined_data.columns:
                joined_data['category_type'] = joined_data['category_type_cad']
            elif 'category_type_rms' in joined_data.columns:
                joined_data['category_type'] = joined_data['category_type_rms']
            
            # Log the results of CAD-first logic BEFORE dropping columns
            cad_response_count = joined_data['response_type_cad'].notna().sum() if 'response_type_cad' in joined_data.columns else 0
            cad_category_count = joined_data['category_type_cad'].notna().sum() if 'category_type_cad' in joined_data.columns else 0
            final_response_count = joined_data['response_type'].notna().sum() if 'response_type' in joined_data.columns else 0
            final_category_count = joined_data['category_type'].notna().sum() if 'category_type' in joined_data.columns else 0
            
            self.logger.info(f"CAD-first logic results:")
            self.logger.info(f"  - response_type_cad populated: {cad_response_count}")
            self.logger.info(f"  - category_type_cad populated: {cad_category_count}")
            self.logger.info(f"  - Final response_type populated: {final_response_count}")
            self.logger.info(f"  - Final category_type populated: {final_category_count}")
            
            # Calculate match statistics BEFORE dropping columns
            cad_matches = joined_data['response_type_cad'].notna().sum() if 'response_type_cad' in joined_data.columns else 0
            match_rate = (cad_matches / len(joined_data)) * 100
            
            # Drop suffix columns AFTER logging - Enhanced to retain essential CAD columns
            # Define which _cad columns to KEEP
            cols_to_keep = ['case_number_cad', 'response_type_cad', 'category_type_cad', 'grid_cad', 'post_cad']
            
            # Identify all _cad columns
            all_cad_cols = [c for c in joined_data.columns if c.endswith('_cad')]
            
            # Determine which _cad columns to drop
            cols_to_drop = [c for c in all_cad_cols if c not in cols_to_keep]
            
            # Also find and drop any _rms columns
            rms_cols_to_drop = [c for c in joined_data.columns if c.endswith('_rms')]
            cols_to_drop.extend(rms_cols_to_drop)

            joined_data = joined_data.drop(columns=cols_to_drop)
            
            self.logger.info(f"CAD-RMS matching complete:")
            self.logger.info(f"  - Final record count: {len(joined_data)} (matches RMS input)")
            self.logger.info(f"  - CAD matches found: {cad_matches}")
            self.logger.info(f"  - Match rate: {match_rate:.1f}%")
            
            joined_output = output_dir / f'{self.current_cycle}_{self.current_date}_7Day_cad_rms_matched_standardized.csv' if self.current_cycle and self.current_date else output_dir / 'cad_rms_matched_standardized.csv'
            # Standardize data types before export
            joined_data = self.standardize_data_types(joined_data)
            # Validate headers before export
            header_val = self.validate_lowercase_snake_case_headers(joined_data, 'Joined CAD-RMS')
            if header_val['overall_status']=='FAIL':
                raise ValueError(f"Invalid headers in joined data: {header_val['non_compliant_columns']}")
            self.write_large_csv_efficiently(joined_data, joined_output)
            self.logger.info(f"Joined data saved: {joined_output}")
            
            # Generate comprehensive QC report
            if mapping_diagnostics and ref_diagnostics:
                qc_results = self.generate_enhanced_qc_report(
                    cad_data, mapping_diagnostics, ref_diagnostics, output_dir
                )
                self.logger.info(f"Enhanced QC Report Status: {qc_results['overall_status']}")
                if qc_results['critical_issues']:
                    self.logger.warning(f"Critical Issues Found: {qc_results['critical_issues']}")
                else:
                    self.logger.info("All QC validations passed successfully")
            
            # Create 7-Day SCRPA export using the matched dataset
            self.create_7day_scrpa_export(joined_data, output_dir)
            
            joined_result = joined_data

        # Create joined dataset result if not already created above
        if joined_result is None and not rms_data.empty and not cad_data.empty:
            joined_result = self.create_cad_rms_matched_dataset(rms_data, cad_data, output_dir)
            # Create 7-Day SCRPA export using the matched dataset
            if joined_result is not None and not joined_result.empty:
                self.create_7day_scrpa_export(joined_result, output_dir)
        
        # Final validation logging
        self.logger.info("=" * 60)
        self.logger.info("COMPREHENSIVE SCRPA FIX V8.5 COMPLETE - VALIDATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"✅ RMS records processed: {len(rms_data)}")
        self.logger.info(f"✅ CAD records processed: {len(cad_data)}")
        
        if joined_result is not None:
            self.logger.info(f"✅ Matched records: {len(joined_result)} (RMS as master)")
            
            # Validate target record count (should be 135)
            if len(joined_result) == 135:
                self.logger.info("✅ RECORD COUNT VALIDATION: PASSED (135 records)")
            else:
                self.logger.warning(f"⚠️ RECORD COUNT VALIDATION: Expected 135, got {len(joined_result)}")
            
            # Validate column naming convention
            lowercase_pattern = re.compile(r'^[a-z]+(_[a-z0-9]+)*$')
            non_compliant_cols = [col for col in joined_result.columns if not lowercase_pattern.match(col)]
            
            if not non_compliant_cols:
                self.logger.info("✅ COLUMN NAMING VALIDATION: PASSED (all lowercase_with_underscores)")
            else:
                self.logger.warning(f"⚠️ COLUMN NAMING VALIDATION: Non-compliant columns: {non_compliant_cols}")
            
            # Check CAD column suffixes
            cad_cols = [col for col in joined_result.columns if col.endswith('_cad')]
            self.logger.info(f"✅ CAD columns with _cad suffix: {len(cad_cols)}")
            
            # Validate critical columns exist
            critical_cols = ['case_number', 'incident_type', 'response_type_cad', 'grid_cad', 'post_cad']
            missing_cols = [col for col in critical_cols if col not in joined_result.columns]
            
            if not missing_cols:
                self.logger.info("✅ CRITICAL COLUMNS VALIDATION: PASSED")
            else:
                self.logger.warning(f"⚠️ CRITICAL COLUMNS VALIDATION: Missing columns: {missing_cols}")
            
            # Run comprehensive filtering validation
            self.logger.info("🔍 Running comprehensive filtering validation...")
            filtering_validation = self.validate_comprehensive_filtering(joined_result)
            
            # Log filtering validation results
            filtering_status = filtering_validation['filtering_validation']['overall_status']
            if filtering_status == 'PASS':
                self.logger.info("✅ COMPREHENSIVE FILTERING VALIDATION: PASSED")
            elif filtering_status == 'WARNING':
                self.logger.warning("⚠️ COMPREHENSIVE FILTERING VALIDATION: WARNING")
            else:
                self.logger.error("❌ COMPREHENSIVE FILTERING VALIDATION: FAILED")
            
            # Log key filtering metrics
            if 'filtering_accuracy_tests' in filtering_validation['filtering_validation']:
                filtering_analysis = filtering_validation['filtering_validation']['filtering_accuracy_tests']
                self.logger.info(f"✅ 7-Day records: {filtering_analysis.get('total_7day_records', 0)}")
                self.logger.info(f"✅ Filtered crime incidents: {filtering_analysis.get('filtered_records', 0)}")
                self.logger.info(f"✅ Filtering rate: {filtering_analysis.get('filtering_rate', '0%')}")
                
                # Log crime distribution
                crime_dist = filtering_analysis.get('crime_distribution', {})
                if crime_dist:
                    self.logger.info("✅ Crime distribution:")
                    for crime_type, count in crime_dist.items():
                        self.logger.info(f"   - {crime_type}: {count}")
            
            # Log recommendations if any
            recommendations = filtering_validation['filtering_validation'].get('recommendations', [])
            if recommendations:
                self.logger.warning("⚠️ Filtering validation recommendations:")
                for rec in recommendations:
                    self.logger.warning(f"   - {rec}")
        
        self.logger.info(f"✅ Output directory: {output_dir}")
        self.logger.info("=" * 60)
        
        # Run comprehensive export consistency validation
        self.logger.info("Running comprehensive export consistency validation...")
        export_files = []
        
        # Collect all CSV export files for validation
        output_path = Path(output_dir)
        
        # Standard exports
        rms_export = output_path / f"{self.current_cycle}_{self.current_date}_7Day_rms_data_standardized.csv"
        if rms_export.exists():
            export_files.append(str(rms_export))
        
        cad_export = output_path / f"{self.current_cycle}_{self.current_date}_7Day_cad_data_standardized.csv"
        if cad_export.exists():
            export_files.append(str(cad_export))
        
        matched_export = output_path / f"{self.current_cycle}_{self.current_date}_7Day_cad_rms_matched_standardized.csv"
        if matched_export.exists():
            export_files.append(str(matched_export))
        
        # 7-Day SCRPA export
        scrpa_export = output_path / f"{self.current_cycle}_{self.current_date}_7Day_SCRPA_Incidents.csv"
        if scrpa_export.exists():
            export_files.append(str(scrpa_export))
        
        # Also check for any other CSV files in the output directory
        for csv_file in output_path.glob("*.csv"):
            csv_path = str(csv_file)
            if csv_path not in export_files:
                export_files.append(csv_path)
        
        if export_files:
            self.logger.info(f"Found {len(export_files)} CSV files for validation")
            export_validation_results = self.validate_export_consistency(export_files)
            
            # Log overall validation status
            if export_validation_results['overall_status'] == 'PASS':
                self.logger.info("✅ All exports validated successfully - Power BI ready!")
            elif export_validation_results['overall_status'] == 'WARNING':
                self.logger.warning("⚠️ Export validation completed with warnings - review before Power BI import")
            else:
                self.logger.error("❌ Export validation failed - address issues before Power BI import")
        else:
            self.logger.warning("No CSV export files found for validation")
        
        return {
            'rms_data': rms_data,
            'cad_data': cad_data,
            'output_dir': str(output_dir),
            'export_validation': export_validation_results if export_files else None
        }

    def generate_column_validation_report(self, df, data_type="Unknown"):
        """Generate a validation report for column naming compliance."""
        
        report_lines = [
            f"# Column Validation Report - {data_type}",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}",
            "",
            "| Column Name | Compliant | Issue |",
            "|---|---|---|"
        ]
        
        # Pattern for lowercase_with_underscores - FIXED to allow numbers
        lowercase_pattern = re.compile(r'^[a-z]+(_[a-z0-9]+)*$')
        
        compliant_count = 0
        total_count = len(df.columns)
        
        for col in df.columns:
            # Add debug logging to show which columns are being tested
            self.logger.debug(f"Testing column: '{col}' against pattern: ^[a-z]+(_[a-z0-9]+)*$")
            
            if lowercase_pattern.match(col):
                report_lines.append(f"| {col} | ✅ Yes | None |")
                compliant_count += 1
                self.logger.debug(f"Column '{col}' PASSED validation")
            else:
                suggested = self.convert_to_lowercase_with_underscores(col)
                report_lines.append(f"| {col} | ❌ No | Should be: {suggested} |")
                self.logger.debug(f"Column '{col}' FAILED validation - suggested: {suggested}")
        
        report_lines.extend([
            "",
            f"**Summary:**",
            f"- Total columns: {total_count}",
            f"- Compliant columns: {compliant_count}",
            f"- Non-compliant columns: {total_count - compliant_count}",
            f"- Compliance rate: {(compliant_count/total_count)*100:.1f}%"
        ])
        
        return "\n".join(report_lines)

    def validate_data_quality(self, rms_data, cad_data):
        """Validate data quality and generate report."""
        
        validation_results = {
            'rms_validation': {},
            'cad_validation': {},
            'overall_status': 'PASS'
        }
        
        # RMS Data Validation
        if not rms_data.empty:
            rms_null_case_numbers = rms_data['case_number'].isnull().sum()
            rms_empty_case_numbers = (rms_data['case_number'] == '').sum()
            rms_total_null_empty = rms_null_case_numbers + rms_empty_case_numbers
            
            validation_results['rms_validation'] = {
                'total_records': len(rms_data),
                'null_case_numbers': rms_null_case_numbers,
                'empty_case_numbers': rms_empty_case_numbers,
                'total_invalid_case_numbers': rms_total_null_empty,
                'case_number_quality': f"{((len(rms_data) - rms_total_null_empty) / len(rms_data)) * 100:.1f}%",
                'incident_types_populated': rms_data.get('incident_type', pd.Series()).notna().sum(),
                'incident_dates_populated': rms_data['incident_date'].notna().sum(),
                'periods_calculated': rms_data['period'].notna().sum()
            }
            
            # Check for critical issues
            if rms_total_null_empty > len(rms_data) * 0.1:  # More than 10% invalid case numbers
                validation_results['overall_status'] = 'WARNING'
                
        # CAD Data Validation
        if cad_data is not None and not cad_data.empty:
            cad_null_case_numbers = cad_data['case_number'].isnull().sum()
            cad_empty_case_numbers = (cad_data['case_number'] == '').sum()
            cad_total_null_empty = cad_null_case_numbers + cad_empty_case_numbers
            
            validation_results['cad_validation'] = {
                'total_records': len(cad_data),
                'null_case_numbers': cad_null_case_numbers,
                'empty_case_numbers': cad_empty_case_numbers,
                'total_invalid_case_numbers': cad_total_null_empty,
                'case_number_quality': f"{((len(cad_data) - cad_total_null_empty) / len(cad_data)) * 100:.1f}%",
                'time_calculations_populated': cad_data.get('time_response_minutes', pd.Series()).notna().sum(),
                'officer_populated': cad_data.get('officer', pd.Series()).notna().sum()
            }
            
            # Check for critical issues
            if cad_total_null_empty > len(cad_data) * 0.1:  # More than 10% invalid case numbers
                validation_results['overall_status'] = 'WARNING'
        
        return validation_results

    def validate_comprehensive_filtering(self, matched_data):
        """
        Comprehensive validation of multi-column crime filtering functionality.
        
        Args:
            matched_data (pd.DataFrame): The cad_rms_matched_standardized dataset
            
        Returns:
            dict: Comprehensive validation results
        """
        self.logger.info("Starting comprehensive filtering validation...")
        
        validation_results = {
            'filtering_validation': {
                'overall_status': 'PASS',
                'test_results': {},
                'crime_pattern_tests': {},
                'column_coverage_tests': {},
                'filtering_accuracy_tests': {},
                'recommendations': []
            }
        }
        
        if matched_data.empty:
            validation_results['filtering_validation']['overall_status'] = 'FAIL'
            validation_results['filtering_validation']['recommendations'].append("No data available for filtering validation")
            return validation_results
        
        # Define crime patterns for testing (same as in create_7day_scrpa_export)
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
        
        # Test 1: Column Coverage Validation
        self.logger.info("Testing column coverage for filtering...")
        search_columns = [
            'incident_type', 'all_incidents', 'vehicle_1', 'vehicle_2',
            'incident_type_1_raw', 'incident_type_2_raw', 'incident_type_3_raw'
        ]
        
        available_columns = []
        missing_columns = []
        
        for col in search_columns:
            if col in matched_data.columns:
                available_columns.append(col)
                # Check data quality in this column
                non_null_count = matched_data[col].notna().sum()
                total_count = len(matched_data)
                coverage_pct = (non_null_count / total_count) * 100
                
                validation_results['filtering_validation']['column_coverage_tests'][col] = {
                    'available': True,
                    'non_null_count': non_null_count,
                    'total_count': total_count,
                    'coverage_percentage': f"{coverage_pct:.1f}%",
                    'status': 'PASS' if coverage_pct > 50 else 'WARNING'
                }
                
                if coverage_pct < 50:
                    validation_results['filtering_validation']['recommendations'].append(
                        f"Low data coverage in {col}: {coverage_pct:.1f}%"
                    )
            else:
                missing_columns.append(col)
                validation_results['filtering_validation']['column_coverage_tests'][col] = {
                    'available': False,
                    'status': 'WARNING'
                }
        
        validation_results['filtering_validation']['test_results']['column_coverage'] = {
            'available_columns': available_columns,
            'missing_columns': missing_columns,
            'coverage_score': f"{len(available_columns)}/{len(search_columns)} columns available"
        }
        
        # Test 2: Crime Pattern Validation
        self.logger.info("Testing crime pattern matching...")
        pattern_test_results = {}
        
        for category, patterns in crime_patterns.items():
            category_matches = 0
            pattern_details = {}
            
            for pattern in patterns:
                # Test pattern against all available columns
                pattern_matches = 0
                matching_records = []
                
                for col in available_columns:
                    if col in matched_data.columns:
                        # Count matches for this pattern in this column
                        matches = matched_data[col].astype(str).str.contains(
                            pattern, case=False, na=False, regex=True
                        ).sum()
                        pattern_matches += matches
                        
                        if matches > 0:
                            # Get sample matching records
                            sample_records = matched_data[
                                matched_data[col].astype(str).str.contains(
                                    pattern, case=False, na=False, regex=True
                                )
                            ][col].head(3).tolist()
                            matching_records.extend(sample_records)
                
                pattern_details[pattern] = {
                    'matches': pattern_matches,
                    'sample_matches': matching_records[:3]  # Limit to 3 samples
                }
                category_matches += pattern_matches
            
            pattern_test_results[category] = {
                'total_matches': category_matches,
                'patterns': pattern_details,
                'status': 'PASS' if category_matches > 0 else 'WARNING'
            }
            
            if category_matches == 0:
                validation_results['filtering_validation']['recommendations'].append(
                    f"No matches found for {category} - check pattern definitions"
                )
        
        validation_results['filtering_validation']['crime_pattern_tests'] = pattern_test_results
        
        # Test 3: Multi-Column Search Function Validation
        self.logger.info("Testing multi-column search function...")
        search_function_tests = {
            'test_cases': [],
            'overall_accuracy': 0,
            'status': 'PASS'
        }
        
        # Create test cases with known crime types
        test_cases = [
            {
                'description': 'Motor Vehicle Theft in incident_type',
                'row_data': {
                    'incident_type': 'MOTOR VEHICLE THEFT',
                    'all_incidents': 'Some other incident',
                    'vehicle_1': None,
                    'vehicle_2': None
                },
                'expected': 'Motor Vehicle Theft'
            },
            {
                'description': 'Burglary Auto in vehicle_1',
                'row_data': {
                    'incident_type': 'Some other incident',
                    'all_incidents': 'Some other incident',
                    'vehicle_1': 'BURGLARY AUTO',
                    'vehicle_2': None
                },
                'expected': 'Burglary - Auto'
            },
            {
                'description': 'Robbery in all_incidents',
                'row_data': {
                    'incident_type': 'Some other incident',
                    'all_incidents': 'ROBBERY',
                    'vehicle_1': None,
                    'vehicle_2': None
                },
                'expected': 'Robbery'
            },
            {
                'description': 'No crime match',
                'row_data': {
                    'incident_type': 'TRAFFIC VIOLATION',
                    'all_incidents': 'TRAFFIC VIOLATION',
                    'vehicle_1': None,
                    'vehicle_2': None
                },
                'expected': 'Other'
            }
        ]
        
        correct_matches = 0
        for i, test_case in enumerate(test_cases):
            try:
                # Create a mock row
                mock_row = pd.Series(test_case['row_data'])
                
                # Test the multi-column search function
                result = self.multi_column_crime_search(mock_row, crime_patterns)
                
                # Check if result matches expected
                is_correct = result == test_case['expected']
                if is_correct:
                    correct_matches += 1
                
                search_function_tests['test_cases'].append({
                    'test_number': i + 1,
                    'description': test_case['description'],
                    'expected': test_case['expected'],
                    'actual': result,
                    'passed': is_correct
                })
                
                self.logger.debug(f"Test {i+1}: Expected '{test_case['expected']}', Got '{result}', Passed: {is_correct}")
                
            except Exception as e:
                search_function_tests['test_cases'].append({
                    'test_number': i + 1,
                    'description': test_case['description'],
                    'error': str(e),
                    'passed': False
                })
                self.logger.error(f"Test {i+1} failed with error: {e}")
        
        # Calculate accuracy
        total_tests = len(test_cases)
        search_function_tests['overall_accuracy'] = (correct_matches / total_tests) * 100 if total_tests > 0 else 0
        search_function_tests['status'] = 'PASS' if search_function_tests['overall_accuracy'] >= 90 else 'FAIL'
        
        if search_function_tests['overall_accuracy'] < 90:
            validation_results['filtering_validation']['recommendations'].append(
                f"Multi-column search function accuracy below 90%: {search_function_tests['overall_accuracy']:.1f}%"
            )
        
        validation_results['filtering_validation']['test_results']['search_function'] = search_function_tests
        
        # Test 4: Real Data Filtering Validation
        self.logger.info("Testing filtering on real data...")
        
        # Apply the multi-column filter to real data
        def apply_multi_column_crime_filter(df):
            """Apply multi-column crime filtering using the enhanced search function."""
            crime_matches = []
            for idx, row in df.iterrows():
                crime_category = self.multi_column_crime_search(row, crime_patterns)
                if crime_category != 'Other':
                    crime_matches.append(idx)
            return df.loc[crime_matches] if crime_matches else pd.DataFrame()
        
        # Test filtering on 7-Day period data
        period_filtered = matched_data[matched_data['period'] == '7-Day'].copy()
        filtered_df = apply_multi_column_crime_filter(period_filtered)
        
        # Analyze filtering results
        filtering_analysis = {
            'total_7day_records': len(period_filtered),
            'filtered_records': len(filtered_df),
            'filtering_rate': f"{(len(filtered_df) / len(period_filtered)) * 100:.1f}%" if len(period_filtered) > 0 else "0%",
            'crime_distribution': {}
        }
        
        # Count crimes by category in filtered results
        for idx, row in filtered_df.iterrows():
            crime_category = self.multi_column_crime_search(row, crime_patterns)
            if crime_category not in filtering_analysis['crime_distribution']:
                filtering_analysis['crime_distribution'][crime_category] = 0
            filtering_analysis['crime_distribution'][crime_category] += 1
        
        # Validate filtering results
        if len(filtered_df) == 0:
            validation_results['filtering_validation']['recommendations'].append(
                "No crime incidents found in 7-Day period - check data and filtering logic"
            )
        elif len(filtered_df) < 3:
            validation_results['filtering_validation']['recommendations'].append(
                f"Very few crime incidents found ({len(filtered_df)}) - may indicate filtering issues"
            )
        
        validation_results['filtering_validation']['filtering_accuracy_tests'] = filtering_analysis
        
        # Test 5: Backward Compatibility Validation
        self.logger.info("Testing backward compatibility...")
        
        # Test the old get_crime_category method still works
        compatibility_tests = {
            'get_crime_category_tests': [],
            'status': 'PASS'
        }
        
        # Test cases for backward compatibility
        compatibility_test_cases = [
            ('MOTOR VEHICLE THEFT', 'Some other incident', 'Motor Vehicle Theft'),
            ('Some other incident', 'ROBBERY', 'Robbery'),
            ('BURGLARY AUTO', 'Some other incident', 'Burglary - Auto'),
            ('TRAFFIC VIOLATION', 'TRAFFIC VIOLATION', 'Other')
        ]
        
        compatibility_correct = 0
        for i, (incident_type, all_incidents, expected) in enumerate(compatibility_test_cases):
            try:
                result = self.get_crime_category(all_incidents, incident_type)
                is_correct = result == expected
                if is_correct:
                    compatibility_correct += 1
                
                compatibility_tests['get_crime_category_tests'].append({
                    'test_number': i + 1,
                    'incident_type': incident_type,
                    'all_incidents': all_incidents,
                    'expected': expected,
                    'actual': result,
                    'passed': is_correct
                })
                
            except Exception as e:
                compatibility_tests['get_crime_category_tests'].append({
                    'test_number': i + 1,
                    'error': str(e),
                    'passed': False
                })
        
        compatibility_tests['accuracy'] = (compatibility_correct / len(compatibility_test_cases)) * 100
        compatibility_tests['status'] = 'PASS' if compatibility_tests['accuracy'] >= 90 else 'FAIL'
        
        if compatibility_tests['accuracy'] < 90:
            validation_results['filtering_validation']['recommendations'].append(
                f"Backward compatibility accuracy below 90%: {compatibility_tests['accuracy']:.1f}%"
            )
        
        validation_results['filtering_validation']['test_results']['backward_compatibility'] = compatibility_tests
        
        # Overall validation status
        failed_tests = 0
        warning_tests = 0
        
        # Check all test results
        for test_category, test_result in validation_results['filtering_validation']['test_results'].items():
            if 'status' in test_result:
                if test_result['status'] == 'FAIL':
                    failed_tests += 1
                elif test_result['status'] == 'WARNING':
                    warning_tests += 1
        
        # Check column coverage
        for col_test in validation_results['filtering_validation']['column_coverage_tests'].values():
            if col_test.get('status') == 'FAIL':
                failed_tests += 1
            elif col_test.get('status') == 'WARNING':
                warning_tests += 1
        
        # Check crime pattern tests
        for pattern_test in validation_results['filtering_validation']['crime_pattern_tests'].values():
            if pattern_test['status'] == 'FAIL':
                failed_tests += 1
            elif pattern_test['status'] == 'WARNING':
                warning_tests += 1
        
        # Set overall status
        if failed_tests > 0:
            validation_results['filtering_validation']['overall_status'] = 'FAIL'
        elif warning_tests > 0:
            validation_results['filtering_validation']['overall_status'] = 'WARNING'
        else:
            validation_results['filtering_validation']['overall_status'] = 'PASS'
        
        # Log validation summary
        self.logger.info(f"Comprehensive filtering validation complete:")
        self.logger.info(f"  - Overall status: {validation_results['filtering_validation']['overall_status']}")
        self.logger.info(f"  - Failed tests: {failed_tests}")
        self.logger.info(f"  - Warning tests: {warning_tests}")
        self.logger.info(f"  - Recommendations: {len(validation_results['filtering_validation']['recommendations'])}")
        
        return validation_results

    def create_7day_scrpa_export(self, matched_data, output_dir):
        """
        Create 7-Day SCRPA incident export with specific crime category filtering.
        
        Args:
            matched_data (pd.DataFrame): The cad_rms_matched_standardized dataset
            output_dir (Path): Output directory for the CSV file
            
        Returns:
            pd.DataFrame: Filtered dataframe with 7-day incidents
        """
        self.logger.info("Starting 7-Day SCRPA incident export...")
        
        if matched_data.empty:
            self.logger.warning("No matched data available for 7-day export")
            return pd.DataFrame()
        
        # Validate required columns exist
        required_columns = ['period', 'incident_type', 'case_number', 'incident_date', 'incident_time', 
                          'all_incidents', 'location', 'narrative', 'vehicle_1', 'grid', 'post']
        missing_columns = [col for col in required_columns if col not in matched_data.columns]
        if missing_columns:
            self.logger.error(f"Missing required columns for 7-day export: {missing_columns}")
            return pd.DataFrame()
        
        # Define crime patterns for multi-column filtering
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
        
        # ENHANCED MULTI-COLUMN FILTERING LOGIC: Try multiple approaches
        filtered_df = None
        filtering_method = "Unknown"
        crime_validation_report = None
        
        def apply_multi_column_crime_filter(df):
            """Apply multi-column crime filtering using the enhanced search function."""
            crime_matches = []
            for idx, row in df.iterrows():
                crime_category = self.multi_column_crime_search(row, crime_patterns)
                if crime_category != 'Other':
                    crime_matches.append(idx)
            return df.loc[crime_matches] if crime_matches else pd.DataFrame()
        
        # Method 1: Original exact period matching - NO crime category filtering
        period_filtered = matched_data[matched_data['period'] == '7-Day'].copy()
        self.logger.info(f"7-Day period records found: {len(period_filtered)}")
        
        if len(period_filtered) > 0:
            # Use all 7-Day records without crime category filtering
            filtered_df = period_filtered.copy()
            filtering_method = "Exact period match - ALL records"
            self.logger.info(f"Using all 7-Day records: {len(filtered_df)} records")
        
        # Method 2: Case-insensitive period matching if Method 1 found 0
        if filtered_df is None or len(filtered_df) == 0:
            period_filtered = matched_data[
                matched_data['period'].str.contains('7-day|7day|7_day', case=False, na=False)
            ].copy()
            self.logger.info(f"Case-insensitive 7-day period records found: {len(period_filtered)}")
            
            if len(period_filtered) > 0:
                # Use all case-insensitive 7-day records without crime category filtering
                filtered_df = period_filtered.copy()
                filtering_method = "Case-insensitive period match - ALL records"
                self.logger.info(f"Using all case-insensitive 7-day records: {len(filtered_df)} records")
        
        # Method 3: Date-based filtering as fallback
        if filtered_df is None or len(filtered_df) == 0:
            self.logger.info("Trying date-based filtering as fallback...")
            
            # Filter for last 7 days from today
            today = pd.Timestamp.now().date()
            seven_days_ago = today - pd.Timedelta(days=7)
            
            # Convert incident_date to datetime if it's not already
            try:
                if matched_data['incident_date'].dtype == 'object':
                    date_filtered = matched_data[
                        pd.to_datetime(matched_data['incident_date'], errors='coerce').dt.date >= seven_days_ago
                    ].copy()
                else:
                    date_filtered = matched_data[
                        matched_data['incident_date'].dt.date >= seven_days_ago
                    ].copy()
                
                self.logger.info(f"Date-based filtering (last 7 days): {len(date_filtered)} records found")
                
                if len(date_filtered) > 0:
                    filtered_df = date_filtered.copy()
                    filtering_method = "Date-based filtering (last 7 days) - ALL records"
                    self.logger.info(f"Using all date-based filtered records: {len(filtered_df)} records")
                    
            except Exception as e:
                self.logger.error(f"Error in date-based filtering: {e}")
        
        # Final check - if we still have no results
        if filtered_df is None or len(filtered_df) == 0:
            self.logger.warning("No 7-Day incidents found matching crime categories")
            self.logger.info(f"Filtering method attempted: {filtering_method}")
            return pd.DataFrame()
        
        self.logger.info(f"7-Day filtering complete: {len(filtered_df)} incidents found using {filtering_method}")
        
        # Log total count of 7-Day records
        self.logger.info(f"7-Day incident total: {len(filtered_df)} records")
        
        # Export the filtered data with ALL columns from the CAD-RMS matched dataset
        export_df = filtered_df.copy()
        
        # Generate filename with cycle name and current date
        if self.current_cycle and self.current_date:
            filename = f"{self.current_cycle}_{self.current_date}_7Day_SCRPA_Incidents.csv"
        else:
            current_date = datetime.now().strftime('%Y_%m_%d')
            filename = f"{current_date}_7Day_SCRPA_Incidents.csv"
        output_path = output_dir / filename
        
        # Standardize data types before export
        export_df = self.standardize_data_types(export_df)
        
        # Normalize headers to snake_case before validation
        export_df = normalize_headers(export_df)
        
        # Validate headers before export
        header_val = self.validate_lowercase_snake_case_headers(export_df, '7-Day SCRPA Export')
        if header_val['overall_status']=='FAIL':
            raise ValueError(f"Invalid headers in 7-day export: {header_val['non_compliant_columns']}")
        
        # Export to CSV using efficient writing
        self.write_large_csv_efficiently(export_df, output_path)
        
        # Enhanced export summary logging
        self.logger.info("=" * 60)
        self.logger.info("7-DAY SCRPA EXPORT COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"Export Summary:")
        self.logger.info(f"  - Output file: {output_path}")
        self.logger.info(f"  - Total incidents exported: {len(export_df)}")
        self.logger.info(f"  - Date range: 7-Day period records")
        self.logger.info(f"  - Filtering method: {filtering_method}")
        self.logger.info(f"  - All columns from CAD-RMS matched data preserved")
                
        self.logger.info("=" * 60)
        
        return export_df

    def create_cad_rms_matched_dataset(self, rms_data, cad_data, output_dir):
        """Create properly matched CAD-RMS dataset with RMS as master (LEFT JOIN)."""
        self.logger.info(f"Starting CAD-RMS matching: RMS={len(rms_data)} records, CAD={len(cad_data)} records")
        
        # LEFT JOIN: RMS as master, CAD data added where case numbers match
        # Use case-insensitive matching on case_number
        rms_copy = rms_data.copy()
        cad_copy = cad_data.copy()
        
        # Create case-insensitive lookup keys
        rms_copy['_lookup_key'] = rms_copy['case_number'].astype(str).str.upper().str.strip()
        cad_copy['_lookup_key'] = cad_copy['case_number'].astype(str).str.upper().str.strip()
        
        # Add _cad suffix to CAD columns (except lookup key)
        cad_renamed = cad_copy.drop(columns=['_lookup_key']).add_suffix('_cad')
        cad_renamed['_lookup_key'] = cad_copy['_lookup_key']
        
        # Perform LEFT JOIN on lookup key
        joined_data = rms_copy.merge(
            cad_renamed,
            on='_lookup_key',
            how='left'
        )
        
        # Remove temporary lookup key
        joined_data = joined_data.drop(columns=['_lookup_key'])
        
        # Note: All CAD data is now accessible via column_name_cad format
        # No duplicate columns without _cad suffix are created
        
        # Fix CAD notes cleaning - remove username/timestamps more thoroughly
        def enhanced_clean_cad_notes(notes):
            if pd.isna(notes):
                return None
            
            text = str(notes)
            
            # Remove username patterns (letters followed by numbers or periods)
            text = re.sub(r'^[A-Z]+\d*\s*[:\-]?\s*', '', text)
            text = re.sub(r'^[a-zA-Z]+\.[a-zA-Z]+\s*[:\-]?\s*', '', text)
            
            # Remove timestamp patterns
            text = re.sub(r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M', '', text)
            text = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', '', text)
            text = re.sub(r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}', '', text)
            
            # Clean up extra whitespace and separators
            text = re.sub(r'[\r\n\t]+', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text if text else None
        
        joined_data['cad_notes_cleaned_cad'] = joined_data['cad_notes_cleaned_cad'].apply(enhanced_clean_cad_notes)
        
        # Calculate match statistics
        cad_matches = joined_data['response_type_cad'].notna().sum()
        match_rate = (cad_matches / len(joined_data)) * 100
        
        self.logger.info(f"CAD-RMS matching complete:")
        self.logger.info(f"  - Final record count: {len(joined_data)} (matches RMS input)")
        self.logger.info(f"  - CAD matches found: {cad_matches}")
        self.logger.info(f"  - Match rate: {match_rate:.1f}%")
        
        # Validate output has exactly same count as RMS input
        if len(joined_data) != len(rms_data):
            self.logger.warning(f"Record count mismatch! Expected {len(rms_data)}, got {len(joined_data)}")
        
        joined_output = output_dir / f'{self.current_cycle}_{self.current_date}_7Day_cad_rms_matched_standardized.csv' if self.current_cycle and self.current_date else output_dir / 'cad_rms_matched_standardized.csv'
        # Standardize data types before export
        joined_data = self.standardize_data_types(joined_data)
        # Validate headers before export
        header_val = self.validate_lowercase_snake_case_headers(joined_data, 'CAD-RMS Matched Dataset')
        if header_val['overall_status']=='FAIL':
            raise ValueError(f"Invalid headers in CAD-RMS matched dataset: {header_val['non_compliant_columns']}")
        self.write_large_csv_efficiently(joined_data, joined_output)
        self.logger.info(f"Joined data saved: {joined_output}")
        
        return joined_data

    def resolve_reference_duplicates(self, ref_df):
        """
        Resolve duplicate incidents using deterministic priority rules.
        
        Args:
            ref_df: DataFrame with potential duplicate incidents
            
        Returns:
            DataFrame with duplicates resolved using priority-based selection
        """
        # Define priority rankings for consistent duplicate resolution
        response_priority = {
            'EMERGENCY': 1,
            'URGENT': 2, 
            'HIGH': 3,
            'MEDIUM': 4,
            'ROUTINE': 5,
            'LOW': 6
        }
        
        category_priority = {
            'CRIMINAL INCIDENTS': 1,
            'CRIMINAL INVESTIGATION': 2,
            'PUBLIC SAFETY AND WELFARE': 3,
            'TRAFFIC AND TRANSPORTATION': 4,
            'PATROL AND PREVENTION': 5,
            'ADMINISTRATIVE AND SUPPORT': 6,
            'OTHER': 7
        }
        
        # Create priority scores for sorting
        ref_df['response_priority'] = ref_df['response_type'].str.upper().map(response_priority).fillna(99)
        ref_df['category_priority'] = ref_df['category_type'].str.upper().map(category_priority).fillna(99)
        
        # Sort by priority (lowest number = highest priority)
        ref_df_sorted = ref_df.sort_values([
            'incident_clean',
            'response_priority', 
            'category_priority',
            'response_type',  # Tie-breaker: alphabetical
            'category_type'   # Final tie-breaker
        ])
        
        # Keep first occurrence after priority sorting
        ref_df_clean = ref_df_sorted.drop_duplicates(subset=['incident_clean'], keep='first')
        
        # Remove temporary priority columns
        ref_df_clean = ref_df_clean.drop(columns=['response_priority', 'category_priority'])
        
        return ref_df_clean

    def load_call_type_reference_enhanced(self):
        """
        Enhanced call type reference loading with proper header normalization and duplicate detection.
        Returns the reference dataframe and diagnostics information.
        """
        reference_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\CallType_Categories.xlsx")
        
        diagnostics = {
            'loaded': False,
            'total_records': 0,
            'duplicate_incidents': [],
            'duplicate_count': 0,
            'resolved_duplicates': 0,
            'original_columns': [],
            'normalized_columns': [],
            'error': None
        }
        
        try:
            if not reference_path.exists():
                diagnostics['error'] = f"Reference file not found: {reference_path}"
                self.logger.error(diagnostics['error'])
                return None, diagnostics
            
            # Load the reference file
            ref_df = pd.read_excel(reference_path)
            diagnostics['total_records'] = len(ref_df)
            diagnostics['original_columns'] = list(ref_df.columns)
            
            # Normalize headers to lowercase snake_case
            ref_df.columns = [self.convert_to_lowercase_with_underscores(col) for col in ref_df.columns]
            diagnostics['normalized_columns'] = list(ref_df.columns)
            
            # Validate required columns exist
            required_columns = ['incident', 'response_type', 'category_type']
            missing_columns = [col for col in required_columns if col not in ref_df.columns]
            
            if missing_columns:
                diagnostics['error'] = f"Missing required columns in reference file: {missing_columns}"
                self.logger.error(diagnostics['error'])
                return None, diagnostics
            
            # Clean and prepare incident values for matching
            ref_df['incident_clean'] = ref_df['incident'].astype(str).str.strip().str.upper()
            
            # Detect and handle duplicate incidents with priority-based resolution
            duplicate_incidents = ref_df[ref_df.duplicated(subset=['incident_clean'], keep=False)]
            if not duplicate_incidents.empty:
                diagnostics['duplicate_count'] = len(duplicate_incidents)
                diagnostics['duplicate_incidents'] = duplicate_incidents['incident_clean'].value_counts().to_dict()
                
                # Log duplicate resolution details BEFORE applying resolution
                duplicate_summary = duplicate_incidents.groupby('incident_clean').agg({
                    'response_type': lambda x: list(x),
                    'category_type': lambda x: list(x)
                })
                
                self.logger.info(f"Found {diagnostics['duplicate_count']} duplicate incidents in reference file.")
                self.logger.info("Applying priority-based duplicate resolution:")
                for incident, row in duplicate_summary.iterrows():
                    self.logger.info(f"  '{incident}': {len(row['response_type'])} variants -> keeping highest priority")
                    self.logger.debug(f"    Response options: {row['response_type']}")
                    self.logger.debug(f"    Category options: {row['category_type']}")
                
                # Apply priority-based duplicate resolution
                ref_df = self.resolve_reference_duplicates(ref_df)
                
                # Log resolution results
                resolved_count = diagnostics['duplicate_count'] - len(ref_df[ref_df.duplicated(subset=['incident_clean'], keep=False)])
                self.logger.info(f"Priority-based resolution completed: {resolved_count} duplicates resolved")
                diagnostics['resolved_duplicates'] = resolved_count
            
            # Create lookup dictionary for efficient matching
            ref_lookup = {}
            for _, row in ref_df.iterrows():
                incident_clean = row['incident_clean']
                if incident_clean and incident_clean != 'NAN':
                    ref_lookup[incident_clean] = {
                        'response_type': row['response_type'],
                        'category_type': row['category_type'],
                        'original_incident': row['incident']
                    }
            
            diagnostics['loaded'] = True
            diagnostics['unique_incidents'] = len(ref_lookup)
            
            self.logger.info(f"Enhanced call type reference loaded successfully:")
            self.logger.info(f"  - Total records: {diagnostics['total_records']}")
            self.logger.info(f"  - Unique incidents: {diagnostics['unique_incidents']}")
            self.logger.info(f"  - Duplicates found: {diagnostics['duplicate_count']}")
            self.logger.info(f"  - Duplicates resolved: {diagnostics.get('resolved_duplicates', 0)}")
            self.logger.info(f"  - Normalized columns: {diagnostics['normalized_columns']}")
            
            return ref_lookup, diagnostics
            
        except Exception as e:
            diagnostics['error'] = f"Error loading call type reference: {str(e)}"
            self.logger.error(diagnostics['error'])
            return None, diagnostics

    def map_incident_to_call_types_enhanced(self, incident_values, ref_lookup):
        """
        Enhanced incident mapping using reference lookup with comprehensive diagnostics and fuzzy matching.
        
        Args:
            incident_values: Series of incident values to map
            ref_lookup: Dictionary lookup from load_call_type_reference_enhanced
            
        Returns:
            tuple: (response_types, category_types, mapping_diagnostics)
        """
        if ref_lookup is None:
            # Fallback to original mapping method
            self.logger.warning("Reference lookup not available, using fallback mapping")
            results = incident_values.apply(lambda x: pd.Series(self.map_call_type(x)))
            return results[0], results[1], {'mapped_count': 0, 'unmapped_count': len(incident_values)}
        
        ref_keys = list(ref_lookup.keys())
        response_types = []
        category_types = []
        mapped_count = 0
        unmapped_count = 0
        unmapped_values = []
        fuzzy_matches = 0
        
        for incident_value in incident_values:
            if pd.isna(incident_value) or not incident_value:
                response_types.append(None)
                category_types.append(None)
                unmapped_count += 1
                continue
                
            incident_clean = str(incident_value).strip().upper()
            
            # Exact match
            if incident_clean in ref_lookup:
                ref_data = ref_lookup[incident_clean]
                response_types.append(ref_data['response_type'])
                category_types.append(ref_data['category_type'])
                mapped_count += 1
                continue
                
            # Fuzzy match: remove code part after '- 2C:' and match
            if ' - 2C:' in incident_clean:
                base_incident = incident_clean.split(' - 2C:')[0].strip()
            else:
                base_incident = incident_clean
            
            # Try exact on base
            if base_incident in ref_lookup:
                ref_data = ref_lookup[base_incident]
                response_types.append(ref_data['response_type'])
                category_types.append(ref_data['category_type'])
                mapped_count += 1
                fuzzy_matches += 1
                continue
                
            # Fuzzy with difflib
            best_match = None
            best_score = 0
            for ref in ref_keys:
                score = difflib.SequenceMatcher(None, base_incident.lower(), ref.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = ref
            if best_score >= 0.9:
                ref_data = ref_lookup[best_match]
                response_types.append(ref_data['response_type'])
                category_types.append(ref_data['category_type'])
                mapped_count += 1
                fuzzy_matches += 1
            else:
                response_types.append(None)
                category_types.append(None)
                unmapped_count += 1
                unmapped_values.append(incident_value)
        
        # Create diagnostics
        mapping_diagnostics = {
            'total_incidents': len(incident_values),
            'mapped_count': mapped_count,
            'unmapped_count': unmapped_count,
            'fuzzy_matches': fuzzy_matches,
            'mapping_rate': (mapped_count / len(incident_values)) * 100 if len(incident_values) > 0 else 0,
            'unmapped_values': list(set(unmapped_values)),  # Remove duplicates
            'unmapped_value_counts': pd.Series(unmapped_values).value_counts().to_dict() if unmapped_values else {}
        }
        
        return pd.Series(response_types), pd.Series(category_types), mapping_diagnostics

    def generate_enhanced_qc_report(self, cad_data, mapping_diagnostics, ref_diagnostics, output_dir):
        """
        Generate comprehensive QC report for CAD incident mapping validation.
        
        Args:
            cad_data: Processed CAD DataFrame
            mapping_diagnostics: Results from enhanced mapping
            ref_diagnostics: Results from reference file loading
            output_dir: Directory for output files
            
        Returns:
            dict: Comprehensive QC results with PASS/FAIL status
        """
        from datetime import datetime
        
        # A. Reference File Validation
        ref_validation = {
            'file_loaded': ref_diagnostics['loaded'],
            'total_records': ref_diagnostics['total_records'],
            'unique_incidents': ref_diagnostics['unique_incidents'],
            'duplicates_found': ref_diagnostics['duplicate_count'],
            'duplicates_resolved': ref_diagnostics.get('resolved_duplicates', 0),
            'resolution_method': 'priority_based_deterministic',
            'status': 'PASS' if ref_diagnostics['loaded'] and ref_diagnostics['duplicate_count'] >= 0 else 'FAIL'
        }
        
        # B. Mapping Performance Validation
        mapping_validation = {
            'total_incidents': mapping_diagnostics['total_incidents'],
            'mapped_count': mapping_diagnostics['mapped_count'],
            'unmapped_count': mapping_diagnostics['unmapped_count'],
            'mapping_rate': mapping_diagnostics['mapping_rate'],
            'target_rate': 98.0,
            'meets_target': mapping_diagnostics['mapping_rate'] >= 98.0,
            'status': 'PASS' if mapping_diagnostics['mapping_rate'] >= 98.0 else 'FAIL'
        }
        
        # C. Data Quality Validation
        required_columns = ['incident', 'response_type_cad', 'category_type_cad', 'response_type', 'category_type']
        data_quality = {
            'total_records': len(cad_data),
            'incident_populated': cad_data['incident'].notna().sum(),
            'response_type_cad_populated': cad_data['response_type_cad'].notna().sum() if 'response_type_cad' in cad_data.columns else 0,
            'category_type_cad_populated': cad_data['category_type_cad'].notna().sum() if 'category_type_cad' in cad_data.columns else 0,
            'response_type_populated': cad_data['response_type'].notna().sum() if 'response_type' in cad_data.columns else 0,
            'category_type_populated': cad_data['category_type'].notna().sum() if 'category_type' in cad_data.columns else 0,
            'required_columns_present': all(col in cad_data.columns for col in required_columns),
            'missing_columns': [col for col in required_columns if col not in cad_data.columns],
            'no_data_loss': len(cad_data) == mapping_diagnostics['total_incidents'],
            'status': 'PASS' if all(col in cad_data.columns for col in required_columns) else 'FAIL'
        }
        
        # D. Header Compliance Validation
        header_validation = self.validate_lowercase_snake_case_headers(cad_data, "CAD Data")
        
        # E. Create unmapped incidents analysis if needed
        unmapped_analysis_file = None
        if mapping_diagnostics.get('unmapped_values'):
            unmapped_analysis_file = self.create_unmapped_analysis(
                mapping_diagnostics['unmapped_values'], output_dir
            )
        
        # F. Comprehensive Logging with Status Indicators
        self.logger.info("=" * 80)
        self.logger.info("COMPREHENSIVE QC REPORT - CAD INCIDENT MAPPING")
        self.logger.info("=" * 80)
        
        # Reference File Validation Logging
        self.logger.info("1. REFERENCE FILE VALIDATION")
        if ref_validation['status'] == 'PASS':
            self.logger.info(f"OK Reference file loaded: {ref_validation['total_records']} records")
            self.logger.info(f"OK Unique incidents: {ref_validation['unique_incidents']}")
            self.logger.info(f"OK Duplicates found: {ref_validation['duplicates_found']}")
            self.logger.info(f"OK Duplicates resolved: {ref_validation['duplicates_resolved']} (deterministic)")
            self.logger.info(f"OK Resolution method: {ref_validation['resolution_method']}")
        else:
            self.logger.error(f"FAIL Reference file validation FAILED")
            self.logger.error(f"     Error: {ref_diagnostics.get('error', 'Unknown error')}")
        
        # Mapping Performance Validation Logging
        self.logger.info("")
        self.logger.info("2. MAPPING PERFORMANCE VALIDATION")
        if mapping_validation['meets_target']:
            self.logger.info(f"OK Mapping success rate: {mapping_validation['mapping_rate']:.1f}% (>= {mapping_validation['target_rate']}%)")
            self.logger.info(f"OK Mapped incidents: {mapping_validation['mapped_count']}/{mapping_validation['total_incidents']}")
            if mapping_validation['unmapped_count'] > 0:
                self.logger.info(f"OK Unmapped incidents: {mapping_validation['unmapped_count']} (within tolerance)")
        else:
            self.logger.error(f"FAIL Mapping success rate: {mapping_validation['mapping_rate']:.1f}% (< {mapping_validation['target_rate']}%)")
            self.logger.error(f"FAIL Unmapped incidents: {mapping_validation['unmapped_count']}")
            if mapping_diagnostics.get('unmapped_values'):
                sample_unmapped = mapping_diagnostics['unmapped_values'][:5]
                self.logger.error(f"     Sample unmapped: {sample_unmapped}")
        
        # Data Quality Validation Logging
        self.logger.info("")
        self.logger.info("3. DATA QUALITY VALIDATION")
        if data_quality['required_columns_present']:
            self.logger.info("OK All required columns present")
            self.logger.info(f"OK Total records: {data_quality['total_records']}")
            self.logger.info(f"OK Incident populated: {data_quality['incident_populated']}/{data_quality['total_records']}")
            self.logger.info(f"OK Response type (CAD) populated: {data_quality['response_type_cad_populated']}/{data_quality['total_records']}")
            self.logger.info(f"OK Category type (CAD) populated: {data_quality['category_type_cad_populated']}/{data_quality['total_records']}")
            if data_quality['no_data_loss']:
                self.logger.info("OK No data loss: record count maintained")
            else:
                self.logger.warning(f"WARNING Data count mismatch: {data_quality['total_records']} vs {mapping_diagnostics['total_incidents']}")
        else:
            self.logger.error("FAIL Missing required columns")
            for col in data_quality['missing_columns']:
                self.logger.error(f"     Missing: {col}")
        
        # Header Compliance Validation Logging
        self.logger.info("")
        self.logger.info("4. HEADER COMPLIANCE VALIDATION")
        if header_validation['overall_status'] == 'PASS':
            self.logger.info(f"OK All headers lowercase snake_case: {len(cad_data.columns)}/{len(cad_data.columns)}")
        else:
            self.logger.error("FAIL Header compliance failed")
            for header in header_validation['invalid_headers']:
                self.logger.error(f"     Invalid header: '{header}'")
        
        # Unmapped Analysis Logging
        if unmapped_analysis_file:
            self.logger.info("")
            self.logger.info("5. UNMAPPED INCIDENTS ANALYSIS")
            self.logger.warning(f"WARNING Unmapped incidents analysis created: {unmapped_analysis_file}")
            self.logger.warning(f"WARNING Review unmapped incidents for potential reference updates")
        
        # G. Overall QC Status Determination
        overall_status = "PASS"
        critical_issues = []
        
        if ref_validation['status'] == 'FAIL':
            overall_status = "FAIL"
            critical_issues.append("Reference file loading failed")
        
        if mapping_validation['status'] == 'FAIL':
            overall_status = "FAIL" 
            critical_issues.append(f"Mapping rate below target ({mapping_validation['mapping_rate']:.1f}% < 98%)")
        
        if header_validation['overall_status'] == 'FAIL':
            overall_status = "FAIL"
            critical_issues.append("Header compliance failed")
        
        if not data_quality['required_columns_present']:
            overall_status = "FAIL"
            critical_issues.append("Required columns missing")
        
        # Final Status Report
        self.logger.info("")
        self.logger.info("6. OVERALL QC STATUS")
        if overall_status == "PASS":
            self.logger.info("SUCCESS OVERALL STATUS: PASS - All validations successful")
            self.logger.info("OK CAD incident mapping pipeline is fully operational")
            self.logger.info("OK Ready for production use")
        else:
            self.logger.error(f"FAIL OVERALL STATUS: FAIL")
            for issue in critical_issues:
                self.logger.error(f"   - {issue}")
            self.logger.error("FAIL Pipeline requires attention before production use")
        
        self.logger.info("=" * 80)
        
        # H. Compile comprehensive QC results
        qc_results = {
            'overall_status': overall_status,
            'critical_issues': critical_issues,
            'reference_validation': ref_validation,
            'mapping_validation': mapping_validation,
            'data_quality': data_quality,
            'header_validation': header_validation,
            'unmapped_analysis_file': unmapped_analysis_file,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return qc_results

    def create_unmapped_analysis(self, unmapped_values, output_dir):
        """
        Create detailed analysis of unmapped incidents.
        
        Args:
            unmapped_values: List of unmapped incident values
            output_dir: Directory for output files
            
        Returns:
            str: Path to the created analysis file or None
        """
        from datetime import datetime
        
        if not unmapped_values:
            self.logger.info("OK No unmapped incidents to analyze")
            return None
        
        # Create analysis DataFrame
        unmapped_df = pd.DataFrame({
            'incident_value': unmapped_values,
            'frequency': pd.Series(unmapped_values).value_counts().reindex(unmapped_values).values,
            'analysis_needed': 'Yes',
            'suggested_action': 'Review for reference file addition'
        })
        
        # Remove duplicates and sort by frequency
        unmapped_df = unmapped_df.drop_duplicates(subset=['incident_value']).sort_values('frequency', ascending=False)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unmapped_file = output_dir / f'unmapped_incidents_analysis_{timestamp}.csv'
        
        # Standardize data types before export
        unmapped_df = self.standardize_data_types(unmapped_df)
        
        # Validate headers before export
        header_val = self.validate_lowercase_snake_case_headers(unmapped_df, 'Unmapped Analysis')
        if header_val['overall_status']=='FAIL':
            raise ValueError(f"Invalid headers in unmapped analysis: {header_val['non_compliant_columns']}")
        
        # Write to CSV using efficient writing
        self.write_large_csv_efficiently(unmapped_df, unmapped_file)
        
        self.logger.warning(f"WARNING Unmapped incidents analysis: {unmapped_file}")
        self.logger.warning(f"WARNING Total unique unmapped: {len(unmapped_df)}")
        self.logger.warning(f"WARNING Total unmapped occurrences: {unmapped_df['frequency'].sum()}")
        
        return str(unmapped_file)

    def create_unmapped_incidents_csv(self, unmapped_values, output_dir):
        """
        Create CSV file with unmapped incident values for diagnostics.
        
        Args:
            unmapped_values: List of unmapped incident values
            output_dir: Output directory path
            
        Returns:
            str: Path to the created CSV file
        """
        if not unmapped_values:
            self.logger.info("No unmapped incidents to write to CSV")
            return None
        
        # Create unmapped incidents dataframe
        unmapped_df = pd.DataFrame({
            'incident_value': unmapped_values,
            'count': pd.Series(unmapped_values).value_counts().reindex(unmapped_values).values
        })
        
        # Remove duplicates and sort by count
        unmapped_df = unmapped_df.drop_duplicates(subset=['incident_value']).sort_values('count', ascending=False)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unmapped_file = output_dir / f'unmapped_incident_values_{timestamp}.csv'
        
        # Standardize data types before export
        unmapped_df = self.standardize_data_types(unmapped_df)
        
        # Validate headers before export
        header_val = self.validate_lowercase_snake_case_headers(unmapped_df, 'Unmapped Incidents CSV')
        if header_val['overall_status']=='FAIL':
            raise ValueError(f"Invalid headers in unmapped incidents CSV: {header_val['non_compliant_columns']}")
        
        # Write to CSV using efficient writing
        self.write_large_csv_efficiently(unmapped_df, unmapped_file)
        
        self.logger.info(f"Unmapped incidents CSV created: {unmapped_file}")
        self.logger.info(f"  - Total unique unmapped values: {len(unmapped_df)}")
        self.logger.info(f"  - Total unmapped occurrences: {unmapped_df['count'].sum()}")
        
        return str(unmapped_file)

    def validate_lowercase_snake_case_headers(self, df, data_type="Unknown"):
        """
        Validate that all column headers follow lowercase snake_case convention.
        
        Args:
            df: DataFrame to validate
            data_type: String identifier for the data type (for logging)
            
        Returns:
            dict: Validation results
        """
        validation_results = {
            'data_type': data_type,
            'total_columns': len(df.columns),
            'compliant_columns': 0,
            'non_compliant_columns': [],
            'overall_status': 'PASS'
        }
        
        # Pattern for lowercase snake_case (allows numbers)
        lowercase_pattern = re.compile(r'^[a-z]+(_[a-z0-9]+)*$')
        
        for col in df.columns:
            if lowercase_pattern.match(col):
                validation_results['compliant_columns'] += 1
            else:
                validation_results['non_compliant_columns'].append(col)
        
        if validation_results['non_compliant_columns']:
            validation_results['overall_status'] = 'FAIL'
        
        # Log results
        if validation_results['overall_status'] == 'PASS':
            self.logger.info(f"✅ {data_type} header validation PASSED: All {validation_results['total_columns']} columns follow lowercase snake_case")
        else:
            self.logger.error(f"❌ {data_type} header validation FAILED: {len(validation_results['non_compliant_columns'])} non-compliant columns")
            self.logger.error(f"Non-compliant columns: {validation_results['non_compliant_columns']}")
        
        return validation_results

    def map_tod(self, time_val):
        """Map time value to time of day category"""
        if pd.isna(time_val) or time_val is None or time_val == '':
            return "Unknown"
        
        try:
            # Handle string time format "HH:MM:SS"
            if isinstance(time_val, str):
                if ':' in time_val:
                    hour = int(time_val.split(':')[0])
                else:
                    return "Unknown"
            # Handle time objects
            elif hasattr(time_val, 'hour'):
                hour = time_val.hour
            else:
                return "Unknown"
            
            # Time of day mapping
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
        except:
            return "Unknown"


if __name__ == "__main__":
    try:
        # Initialize processor
        processor = ComprehensiveSCRPAFixV8_5()
        
        # Run performance monitoring demo
        processor.performance_test_demo()
        
        # Test chunked processing functionality
        processor.test_chunked_processing(test_size=2500, chunk_size=500)
        
        # Test large file writing functionality
        processor.test_large_file_writing(test_size=5000, chunk_size=1000)
        
        # Run the pipeline
        results = processor.process_final_pipeline()
        
        # Generate validation reports
        if not results['rms_data'].empty:
            rms_report = processor.generate_column_validation_report(results['rms_data'], "RMS Data")
            report_file = Path(results['output_dir']) / 'rms_column_validation_report.md'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(rms_report)
                
        if not results['cad_data'].empty:
            cad_report = processor.generate_column_validation_report(results['cad_data'], "CAD Data")
            report_file = Path(results['output_dir']) / 'cad_column_validation_report.md'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(cad_report)
        
        # Validate data quality
        validation_results = processor.validate_data_quality(results['rms_data'], results['cad_data'])
        
        # Run comprehensive filtering validation if we have matched data
        filtering_validation_results = None
        if 'rms_data' in results and 'cad_data' in results:
            # Try to get the matched data from the output directory
            output_dir = Path(results['output_dir'])
            matched_file = output_dir / 'cad_rms_matched_standardized.csv'
            if matched_file.exists():
                try:
                    matched_data = pd.read_csv(matched_file)
                    filtering_validation_results = processor.validate_comprehensive_filtering(matched_data)
                    
                    # Save filtering validation report
                    import json
                    filtering_report_file = output_dir / 'comprehensive_filtering_validation_report.json'
                    with open(filtering_report_file, 'w', encoding='utf-8') as f:
                        json.dump(filtering_validation_results, f, indent=2, default=str)
                    print(f"✅ Comprehensive filtering validation report saved: {filtering_report_file}")
                    
                except Exception as e:
                    print(f"⚠️ Could not run comprehensive filtering validation: {e}")
        
        print("\n" + "="*60)
        print("🎯 SCRPA V8.0 PROCESSING COMPLETE")
        print("="*60)
        print(f"✅ RMS Records: {len(results['rms_data'])}")
        print(f"✅ CAD Records: {len(results['cad_data'])}")
        print(f"✅ Output Directory: {results['output_dir']}")
        print(f"✅ Data Quality Status: {validation_results['overall_status']}")
        
        # Print key metrics
        if validation_results['rms_validation']:
            rms_val = validation_results['rms_validation']
            print(f"✅ RMS Case Number Quality: {rms_val['case_number_quality']}")
            print(f"✅ RMS Incident Types: {rms_val['incident_types_populated']} records")
            
        if validation_results['cad_validation']:
            cad_val = validation_results['cad_validation']
            print(f"✅ CAD Case Number Quality: {cad_val['case_number_quality']}")
            print(f"✅ CAD Time Calculations: {cad_val['time_calculations_populated']} records")
        
        # Print filtering validation results
        if filtering_validation_results:
            filtering_status = filtering_validation_results['filtering_validation']['overall_status']
            print(f"✅ Comprehensive Filtering Status: {filtering_status}")
            
            # Print key filtering metrics
            if 'filtering_accuracy_tests' in filtering_validation_results['filtering_validation']:
                filtering_analysis = filtering_validation_results['filtering_validation']['filtering_accuracy_tests']
                print(f"✅ 7-Day Records: {filtering_analysis.get('total_7day_records', 0)}")
                print(f"✅ Filtered Crime Incidents: {filtering_analysis.get('filtered_records', 0)}")
                print(f"✅ Filtering Rate: {filtering_analysis.get('filtering_rate', '0%')}")
                
                # Print crime distribution
                crime_dist = filtering_analysis.get('crime_distribution', {})
                if crime_dist:
                    print("✅ Crime Distribution:")
                    for crime_type, count in crime_dist.items():
                        print(f"   - {crime_type}: {count}")
            
            # Print recommendations if any
            recommendations = filtering_validation_results['filtering_validation'].get('recommendations', [])
            if recommendations:
                print("⚠️ Filtering Validation Recommendations:")
                for rec in recommendations:
                    print(f"   - {rec}")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Import the CSV files into Power BI")
        print("2. Verify column names are PascalCase_With_Underscores")
        print("3. Create relationships between tables on Case_Number")
        print("4. Test DAX measures with standardized column references")
        print("5. Review comprehensive filtering validation report")
        print("="*60)
        
    except Exception as e:
        print(f"❌ An error occurred during processing: {e}")
        logging.getLogger('ComprehensiveSCRPAFixV8_0').error(f"Fatal error in main execution: {e}", exc_info=True)
        raise