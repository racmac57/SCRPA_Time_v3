import os
import datetime
import logging
from pathlib import Path
from typing import Optional

class SCRPALogger:
    """
    Logger class for SCRPA (Statistical Crime Reporting and Police Analytics) operations.
    Handles logging for crime data analysis and ArcGIS Pro automation workflows.
    """
    
    def __init__(self, log_dir: Optional[str] = None, log_filename: str = "report_log.txt"):
        """
        Initialize the SCRPA logger.
        
        Args:
            log_dir: Custom log directory path. If None, uses default ~/Documents/SCRPA_logs
            log_filename: Name of the log file
        """
        if log_dir is None:
            self.log_dir = Path.home() / "Documents" / "SCRPA_logs"
        else:
            self.log_dir = Path(log_dir)
        
        self.log_filename = log_filename
        self.log_path = self.log_dir / self.log_filename
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up the logging directory and file."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Verify write permissions
            if not os.access(self.log_dir, os.W_OK):
                raise PermissionError(f"No write permission for log directory: {self.log_dir}")
                
        except (OSError, PermissionError) as e:
            print(f"Error setting up log directory: {e}")
            # Fallback to temp directory
            import tempfile
            self.log_dir = Path(tempfile.gettempdir()) / "SCRPA_logs"
            self.log_dir.mkdir(exist_ok=True)
            self.log_path = self.log_dir / self.log_filename
            print(f"Using fallback log directory: {self.log_dir}")
    
    def log_action(self, message: str, context: str = "GENERAL", level: str = "INFO"):
        """
        Log an action with timestamp, context, and message.
        
        Args:
            message: The message to log
            context: Context/category for the log entry (e.g., 'CRIME_ANALYSIS', 'DATA_EXPORT')
            level: Log level (INFO, WARNING, ERROR, DEBUG)
        """
        if not message or not isinstance(message, str):
            raise ValueError("Message must be a non-empty string")
        
        if not context or not isinstance(context, str):
            raise ValueError("Context must be a non-empty string")
        
        level = level.upper()
        valid_levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
        if level not in valid_levels:
            level = 'INFO'
        
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level}] {context}: {message}\n"
            
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
                f.flush()  # Ensure immediate write for critical operations
                
        except (OSError, IOError) as e:
            print(f"Error writing to log file: {e}")
            # Fallback to console logging
            print(f"[{timestamp}] [{level}] {context}: {message}")
    
    def log_info(self, message: str, context: str = "INFO"):
        """Log an informational message."""
        self.log_action(message, context, "INFO")
    
    def log_warning(self, message: str, context: str = "WARNING"):
        """Log a warning message."""
        self.log_action(message, context, "WARNING")
    
    def log_error(self, message: str, context: str = "ERROR"):
        """Log an error message."""
        self.log_action(message, context, "ERROR")
    
    def log_debug(self, message: str, context: str = "DEBUG"):
        """Log a debug message."""
        self.log_action(message, context, "DEBUG")
    
    def get_log_size(self) -> int:
        """Get the current log file size in bytes."""
        try:
            return self.log_path.stat().st_size
        except FileNotFoundError:
            return 0
    
    def rotate_log(self, max_size_mb: int = 10):
        """
        Rotate log file if it exceeds the maximum size.
        
        Args:
            max_size_mb: Maximum log file size in megabytes before rotation
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if self.get_log_size() > max_size_bytes:
            try:
                # Create backup with timestamp
                backup_name = f"{self.log_filename}.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
                backup_path = self.log_dir / backup_name
                
                self.log_path.rename(backup_path)
                self.log_info("Log file rotated", "SYSTEM")
                
            except OSError as e:
                self.log_error(f"Failed to rotate log file: {e}", "SYSTEM")

# Global logger instance for backward compatibility
_default_logger = SCRPALogger()

def log_action(message: str, context: str = "GENERAL"):
    """
    Legacy function for backward compatibility with existing code.
    
    Args:
        message: The message to log
        context: Context for the log entry
    """
    if not message:
        raise ValueError("Message cannot be empty")
    
    if not context:
        context = "GENERAL"
    
    _default_logger.log_action(message, context)

# Enhanced logging functions for different use cases
def log_crime_analysis(message: str):
    """Log crime analysis operations."""
    _default_logger.log_info(message, "CRIME_ANALYSIS")

def log_data_export(message: str):
    """Log data export operations."""
    _default_logger.log_info(message, "DATA_EXPORT")

def log_arcgis_operation(message: str):
    """Log ArcGIS Pro operations."""
    _default_logger.log_info(message, "ARCGIS_PRO")

def log_dashboard_update(message: str):
    """Log dashboard update operations."""
    _default_logger.log_info(message, "DASHBOARD")

def log_error_with_details(message: str, error: Exception):
    """Log errors with exception details."""
    error_msg = f"{message} - Error: {str(error)}"
    _default_logger.log_error(error_msg, "ERROR")

if __name__ == "__main__":
    # Test the logger
    logger = SCRPALogger()
    logger.log_info("Logger test started", "TEST")
    logger.log_warning("This is a test warning", "TEST")
    logger.log_error("This is a test error", "TEST")
    
    # Test legacy function
    log_action("Legacy function test", "TEST")
    
    print(f"Log file location: {logger.log_path}")
    print(f"Log file size: {logger.get_log_size()} bytes")
