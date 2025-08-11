#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_pbix_parameter.py

Comprehensive PBIX parameter update script with all integrated features:
- Complete validation system (pre/post run)
- Environment detection and system information
- Backup creation and rollback capabilities
- JSON configuration summary with detailed logging
- Error tracking and recovery mechanisms
- Checksum verification and file integrity

Usage:
    python update_pbix_parameter.py \
        --input SourceReport.pbix \
        --output UpdatedReport.pbix \
        --param BasePath \
        --value "C:\\New\\Data\\Path\\" \
        --validate-all --verbose --summary-json config.json
"""

import argparse
import zipfile
import os
import re
import tempfile
import shutil
import json
import logging
import platform
import hashlib
import traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict

# Try to import psutil for system information, fallback gracefully
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. System monitoring features will be limited.")

@dataclass
class SystemEnvironment:
    """System environment information."""
    platform: str
    platform_version: str
    python_version: str
    working_directory: str
    user_name: str
    computer_name: str
    total_memory_gb: float
    available_memory_gb: float
    disk_usage_gb: Dict[str, float]
    environment_variables: Dict[str, str]
    timestamp: str
    psutil_available: bool = PSUTIL_AVAILABLE

@dataclass
class FileInfo:
    """Detailed file information."""
    path: str
    exists: bool
    size_bytes: int = 0
    size_mb: float = 0.0
    created_time: str = ""
    modified_time: str = ""
    checksum_md5: str = ""
    permissions: str = ""
    is_readable: bool = False
    is_writable: bool = False

@dataclass
class BackupInfo:
    """Backup operation information."""
    backup_id: str
    original_file: str
    backup_file: str
    created_timestamp: str
    size_bytes: int
    checksum_original: str
    checksum_backup: str
    backup_successful: bool
    restoration_timestamp: str = ""
    restoration_successful: bool = False

@dataclass
class ParameterInfo:
    """Parameter operation information."""
    name: str
    original_value: str
    new_value: str
    pattern_used: str
    update_successful: bool
    verification_successful: bool
    detection_method: str
    timestamp: str

@dataclass
class ErrorInfo:
    """Error information with context."""
    error_id: str
    timestamp: str
    error_type: str
    error_message: str
    operation_step: str
    file_context: str
    stack_trace: Optional[str] = None
    severity: str = "error"  # error, warning, info

@dataclass
class ConfigurationSummary:
    """Complete configuration summary."""
    session_id: str
    operation_type: str
    start_timestamp: str
    end_timestamp: str
    duration_seconds: float
    success: bool
    system_environment: SystemEnvironment
    input_file: FileInfo
    output_file: FileInfo
    parameters: List[ParameterInfo]
    backups: List[BackupInfo]
    errors: List[ErrorInfo]
    warnings: List[ErrorInfo]
    validation_results: Dict[str, Any]
    rollback_performed: bool
    rollback_successful: bool
    summary_file_path: str

class PBIXValidationError(Exception):
    """Custom exception for PBIX validation errors."""
    pass

class PBIXParameterUpdater:
    """Comprehensive PBIX parameter updater with all integrated features."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self.start_time = datetime.now()
        self.validation_results = {}
        self.backups: List[BackupInfo] = []
        self.errors: List[ErrorInfo] = []
        self.warnings: List[ErrorInfo] = []
        self.parameters: List[ParameterInfo] = []
        self.rollback_performed = False
        self.rollback_successful = False
        
        # Setup comprehensive logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup comprehensive logging system."""
        log_level = logging.DEBUG if self.verbose else logging.INFO
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Setup file handler
        log_filename = f'pbix_update_{self.session_id}.log'
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(simple_formatter)
        
        # Configure logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Store log filename for reference
        self.log_filename = log_filename
        
        self.logger.info(f"PBIX Parameter Updater initialized - Session: {self.session_id}")
        
    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        return f"ERR_{datetime.now().strftime('%H%M%S_%f')[:-3]}"
    
    def _add_error(self, error_type: str, message: str, operation_step: str, 
                   file_context: str = "", severity: str = "error", stack_trace: str = None):
        """Add error to comprehensive tracking system."""
        error = ErrorInfo(
            error_id=self._generate_error_id(),
            timestamp=datetime.now().isoformat(),
            error_type=error_type,
            error_message=message,
            operation_step=operation_step,
            file_context=file_context,
            stack_trace=stack_trace,
            severity=severity
        )
        
        if severity == "error":
            self.errors.append(error)
            self.logger.error(f"[{error.error_id}] {operation_step}: {message}")
        elif severity == "warning":
            self.warnings.append(error)
            self.logger.warning(f"[{error.error_id}] {operation_step}: {message}")
        else:
            self.logger.info(f"[{error.error_id}] {operation_step}: {message}")
    
    def _get_system_environment(self) -> SystemEnvironment:
        """Collect comprehensive system environment information."""
        try:
            # Memory and disk information with fallback
            if PSUTIL_AVAILABLE:
                try:
                    memory = psutil.virtual_memory()
                    total_memory_gb = memory.total / (1024**3)
                    available_memory_gb = memory.available / (1024**3)
                    
                    # Disk usage for current directory
                    current_disk = psutil.disk_usage('.')
                    disk_usage = {
                        'total_gb': round(current_disk.total / (1024**3), 2),
                        'used_gb': round(current_disk.used / (1024**3), 2),
                        'free_gb': round(current_disk.free / (1024**3), 2)
                    }
                except Exception as e:
                    self.logger.warning(f"Could not retrieve system metrics: {e}")
                    total_memory_gb = 0.0
                    available_memory_gb = 0.0
                    disk_usage = {'error': 'Could not retrieve disk usage'}
            else:
                total_memory_gb = 0.0
                available_memory_gb = 0.0
                disk_usage = {'info': 'psutil not available'}
            
            # Environment variables (filtered for security)
            safe_env_vars = {}
            safe_keys = ['PATH', 'PYTHONPATH', 'TEMP', 'TMP', 'USERPROFILE', 'COMPUTERNAME', 'USERNAME', 'USERDOMAIN']
            for key in safe_keys:
                if key in os.environ:
                    # Truncate very long paths for JSON readability
                    value = os.environ[key]
                    if len(value) > 500:
                        value = value[:500] + "...[truncated]"
                    safe_env_vars[key] = value
            
            return SystemEnvironment(
                platform=platform.system(),
                platform_version=platform.version(),
                python_version=platform.python_version(),
                working_directory=os.getcwd(),
                user_name=os.environ.get('USERNAME', os.environ.get('USER', 'unknown')),
                computer_name=os.environ.get('COMPUTERNAME', os.environ.get('HOSTNAME', 'unknown')),
                total_memory_gb=round(total_memory_gb, 2),
                available_memory_gb=round(available_memory_gb, 2),
                disk_usage_gb=disk_usage,
                environment_variables=safe_env_vars,
                timestamp=datetime.now().isoformat(),
                psutil_available=PSUTIL_AVAILABLE
            )
            
        except Exception as e:
            self._add_error("SystemEnvironmentError", str(e), "environment_collection", severity="warning")
            # Return minimal environment info on error
            return SystemEnvironment(
                platform=platform.system(),
                platform_version="unknown",
                python_version=platform.python_version(),
                working_directory=os.getcwd(),
                user_name=os.environ.get('USERNAME', 'unknown'),
                computer_name=os.environ.get('COMPUTERNAME', 'unknown'),
                total_memory_gb=0.0,
                available_memory_gb=0.0,
                disk_usage_gb={'error': 'collection_failed'},
                environment_variables={},
                timestamp=datetime.now().isoformat(),
                psutil_available=PSUTIL_AVAILABLE
            )
    
    def _get_file_info(self, file_path: str) -> FileInfo:
        """Get comprehensive file information with error handling."""
        file_info = FileInfo(path=str(Path(file_path).resolve()), exists=False)
        
        try:
            if os.path.exists(file_path):
                file_info.exists = True
                stat_info = os.stat(file_path)
                
                file_info.size_bytes = stat_info.st_size
                file_info.size_mb = round(stat_info.st_size / (1024*1024), 2)
                file_info.created_time = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
                file_info.modified_time = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                file_info.is_readable = os.access(file_path, os.R_OK)
                file_info.is_writable = os.access(file_path, os.W_OK)
                
                # Get file permissions (cross-platform)
                try:
                    if platform.system() == "Windows":
                        file_info.permissions = "Windows_ACL"
                    else:
                        file_info.permissions = oct(stat_info.st_mode)[-3:]
                except Exception:
                    file_info.permissions = "unknown"
                
                # Calculate MD5 checksum for smaller files (performance consideration)
                if file_info.size_bytes < 50 * 1024 * 1024:  # Less than 50MB
                    try:
                        with open(file_path, 'rb') as f:
                            hash_md5 = hashlib.md5()
                            for chunk in iter(lambda: f.read(4096), b""):
                                hash_md5.update(chunk)
                            file_info.checksum_md5 = hash_md5.hexdigest()
                    except Exception as e:
                        self._add_error("ChecksumError", str(e), "file_info_collection", file_path, "warning")
                        file_info.checksum_md5 = "error_calculating"
                else:
                    file_info.checksum_md5 = "skipped_large_file"
            
        except Exception as e:
            self._add_error("FileInfoError", str(e), "file_info_collection", file_path, "warning")
        
        return file_info
    
    def create_backup(self, file_path: str, backup_dir: Optional[str] = None) -> BackupInfo:
        """Create backup with comprehensive tracking and validation."""
        backup_id = f"BKP_{datetime.now().strftime('%H%M%S_%f')[:-3]}"
        
        try:
            # Get original file info
            original_info = self._get_file_info(file_path)
            if not original_info.exists:
                raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")
            
            # Create backup directory if not specified
            if backup_dir is None:
                backup_dir = os.path.join(os.path.dirname(file_path), f"backups_{self.session_id}")
            
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename with timestamp
            original_path = Path(file_path)
            timestamp = datetime.now()
            backup_filename = f"{original_path.stem}_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}{original_path.suffix}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copy file with metadata preservation
            self.logger.info(f"Creating backup: {backup_id}")
            shutil.copy2(file_path, backup_path)
            
            # Get backup file info for verification
            backup_info_file = self._get_file_info(backup_path)
            
            # Verify backup integrity
            backup_successful = (
                backup_info_file.exists and 
                backup_info_file.size_bytes == original_info.size_bytes
            )
            
            if not backup_successful:
                raise Exception("Backup verification failed - size mismatch or file missing")
            
            # Create backup tracking info
            backup_info = BackupInfo(
                backup_id=backup_id,
                original_file=str(original_path.resolve()),
                backup_file=str(Path(backup_path).resolve()),
                created_timestamp=timestamp.isoformat(),
                size_bytes=backup_info_file.size_bytes,
                checksum_original=original_info.checksum_md5,
                checksum_backup=backup_info_file.checksum_md5,
                backup_successful=backup_successful
            )
            
            self.backups.append(backup_info)
            self.logger.info(f"Backup created successfully: {backup_id} -> {os.path.basename(backup_path)}")
            
            return backup_info
            
        except Exception as e:
            # Create failed backup info for tracking
            backup_info = BackupInfo(
                backup_id=backup_id,
                original_file=file_path,
                backup_file="",
                created_timestamp=datetime.now().isoformat(),
                size_bytes=0,
                checksum_original="",
                checksum_backup="",
                backup_successful=False
            )
            
            self.backups.append(backup_info)
            self._add_error("BackupCreationError", str(e), "backup_creation", file_path)
            raise
    
    def rollback_from_backup(self, backup_info: BackupInfo) -> bool:
        """Restore file from backup with comprehensive validation."""
        try:
            if not backup_info.backup_successful:
                raise ValueError("Cannot rollback from failed backup")
            
            if not os.path.exists(backup_info.backup_file):
                raise FileNotFoundError(f"Backup file not found: {backup_info.backup_file}")
            
            self.logger.info(f"Starting rollback from backup: {backup_info.backup_id}")
            
            # Remove current file if it exists
            if os.path.exists(backup_info.original_file):
                os.remove(backup_info.original_file)
            
            # Restore from backup
            shutil.copy2(backup_info.backup_file, backup_info.original_file)
            
            # Verify restoration
            restored_info = self._get_file_info(backup_info.original_file)
            restoration_successful = (
                restored_info.exists and 
                restored_info.size_bytes == backup_info.size_bytes
            )
            
            # Update backup info
            backup_info.restoration_timestamp = datetime.now().isoformat()
            backup_info.restoration_successful = restoration_successful
            
            if restoration_successful:
                self.logger.info(f"Rollback successful: {backup_info.backup_id}")
            else:
                self.logger.error(f"Rollback verification failed: {backup_info.backup_id}")
            
            return restoration_successful
            
        except Exception as e:
            backup_info.restoration_timestamp = datetime.now().isoformat()
            backup_info.restoration_successful = False
            self._add_error("RollbackError", str(e), "rollback_operation", backup_info.original_file)
            self.logger.error(f"Rollback failed for {backup_info.backup_id}: {e}")
            return False
    
    def validate_input_file(self, pbix_path: str) -> Dict[str, Any]:
        """Comprehensive validation of input PBIX file."""
        self.logger.info(f"Validating input file: {os.path.basename(pbix_path)}")
        
        validation = {
            'file_exists': False,
            'is_pbix': False,
            'is_valid_zip': False,
            'has_common_files': False,
            'datamashup_found': False,
            'datamashup_location': None,
            'file_size': 0,
            'parameters_detected': [],
            'validation_timestamp': datetime.now().isoformat(),
            'errors': []
        }
        
        try:
            # Check file existence
            path = Path(pbix_path)
            if not path.exists():
                error_msg = f"File does not exist: {pbix_path}"
                validation['errors'].append(error_msg)
                self._add_error("FileNotFoundError", error_msg, "input_validation", pbix_path)
                return validation
            
            validation['file_exists'] = True
            validation['file_size'] = path.stat().st_size
            
            # Check file extension
            if not pbix_path.lower().endswith(('.pbix', '.pbit')):
                error_msg = "File must have .pbix or .pbit extension"
                validation['errors'].append(error_msg)
                self._add_error("InvalidExtensionError", error_msg, "input_validation", pbix_path)
                return validation
            
            validation['is_pbix'] = True
            
            # Validate as ZIP file and extract contents
            try:
                with zipfile.ZipFile(pbix_path, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    validation['is_valid_zip'] = True
                    
                    # Check for common PBIX files
                    common_files = ['Version', 'Metadata', 'Settings', 'SecurityBindings']
                    found_common = [f for f in file_list if any(common in f for common in common_files)]
                    validation['has_common_files'] = len(found_common) > 0
                    
                    if not validation['has_common_files']:
                        warning_msg = "Missing standard PBIX files - may not be valid PBIX"
                        validation['errors'].append(warning_msg)
                        self._add_error("MissingStandardFiles", warning_msg, "input_validation", pbix_path, "warning")
                    
                    # Extract temporarily to find DataMashup
                    with tempfile.TemporaryDirectory() as temp_dir:
                        zip_ref.extractall(temp_dir)
                        
                        # Find DataMashup file using enhanced detection
                        mashup_location = self._find_datamashup_file(temp_dir)
                        if mashup_location:
                            validation['datamashup_found'] = True
                            validation['datamashup_location'] = os.path.relpath(mashup_location, temp_dir)
                            
                            # Detect parameters in DataMashup
                            parameters = self._detect_parameters(mashup_location)
                            validation['parameters_detected'] = parameters
                            
                            self.logger.debug(f"DataMashup found at: {validation['datamashup_location']}")
                            self.logger.debug(f"Parameters detected: {len(parameters)}")
                        else:
                            error_msg = "DataMashup file not found - PBIX may not contain parameters"
                            validation['errors'].append(error_msg)
                            self._add_error("DataMashupNotFound", error_msg, "input_validation", pbix_path, "warning")
                            
            except zipfile.BadZipFile as e:
                error_msg = "File is not a valid ZIP/PBIX file"
                validation['errors'].append(error_msg)
                validation['is_valid_zip'] = False
                self._add_error("BadZipFile", error_msg, "input_validation", pbix_path)
                
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            validation['errors'].append(error_msg)
            self._add_error("ValidationError", error_msg, "input_validation", pbix_path)
            
        return validation
    
    def validate_parameter_exists(self, pbix_path: str, param_name: str) -> Dict[str, Any]:
        """Validate that the specified parameter exists in the PBIX file."""
        self.logger.info(f"Validating parameter '{param_name}' exists")
        
        validation = {
            'parameter_found': False,
            'current_value': None,
            'parameter_pattern': None,
            'datamashup_content_preview': None,
            'validation_timestamp': datetime.now().isoformat(),
            'errors': []
        }
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract PBIX
                with zipfile.ZipFile(pbix_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find DataMashup using enhanced detection
                mashup_file = self._find_datamashup_file(temp_dir)
                if not mashup_file:
                    error_msg = "DataMashup file not found"
                    validation['errors'].append(error_msg)
                    self._add_error("DataMashupNotFound", error_msg, "parameter_validation", pbix_path)
                    return validation
                
                # Read and decode DataMashup with fallback encodings
                with open(mashup_file, 'rb') as f:
                    data = f.read()
                
                text, encoding = self._decode_with_fallback(data)
                if not text:
                    error_msg = "Could not decode DataMashup file"
                    validation['errors'].append(error_msg)
                    self._add_error("DecodingError", error_msg, "parameter_validation", pbix_path)
                    return validation
                
                validation['datamashup_content_preview'] = text[:500] if len(text) > 500 else text
                
                # Search for parameter using multiple patterns
                patterns = [
                    re.compile(r'let\s+' + re.escape(param_name) + r'\s*=\s*"([^"]*)"', re.IGNORECASE),
                    re.compile(r'let\s+' + re.escape(param_name) + r'\s*=\s*\'([^\']*)\'', re.IGNORECASE),
                    re.compile(r'let\s+' + re.escape(param_name) + r'\s*=\s*([^,;\r\n]+)', re.IGNORECASE)
                ]
                
                for i, pattern in enumerate(patterns):
                    match = pattern.search(text)
                    if match:
                        validation['parameter_found'] = True
                        validation['current_value'] = match.group(1) if match.lastindex >= 1 else match.group(0).strip()
                        validation['parameter_pattern'] = f"Pattern {i+1}: {pattern.pattern}"
                        self.logger.debug(f"Parameter '{param_name}' found using pattern {i+1}")
                        break
                
                if not validation['parameter_found']:
                    error_msg = f"Parameter '{param_name}' not found in DataMashup"
                    validation['errors'].append(error_msg)
                    self._add_error("ParameterNotFound", error_msg, "parameter_validation", pbix_path)
                    
        except Exception as e:
            error_msg = f"Parameter validation error: {str(e)}"
            validation['errors'].append(error_msg)
            self._add_error("ParameterValidationError", error_msg, "parameter_validation", pbix_path)
            
        return validation
    
    def process_pbix_with_validation(self, input_pbix: str, output_pbix: str, 
                                   param_name: str, new_value: str) -> Dict[str, Any]:
        """Process PBIX with comprehensive validation and error handling."""
        operation_start = datetime.now()
        
        result = {
            'success': False,
            'session_id': self.session_id,
            'operation_start': operation_start.isoformat(),
            'pre_validation': {},
            'post_validation': {},
            'processing_log': [],
            'backup_info': None,
            'parameter_info': None,
            'rollback_performed': False,
            'errors': []
        }
        
        try:
            self.logger.info("=== STARTING PBIX PARAMETER UPDATE PROCESS ===")
            
            # Pre-run validation
            self.logger.info("=== PRE-RUN VALIDATION ===")
            
            # Validate input file
            input_validation = self.validate_input_file(input_pbix)
            result['pre_validation']['input_file'] = input_validation
            
            if input_validation['errors']:
                result['errors'].extend(input_validation['errors'])
                self.logger.error("Pre-validation failed for input file")
                return result
            
            # Validate parameter exists
            param_validation = self.validate_parameter_exists(input_pbix, param_name)
            result['pre_validation']['parameter'] = param_validation
            
            if param_validation['errors']:
                result['errors'].extend(param_validation['errors'])
                self.logger.error(f"Parameter '{param_name}' validation failed")
                return result
            
            # Create backup before processing
            self.logger.info("=== CREATING BACKUP ===")
            backup_info = self.create_backup(input_pbix)
            result['backup_info'] = asdict(backup_info)
            
            # Process PBIX file
            self.logger.info("=== PROCESSING PBIX ===")
            processing_success = self._process_pbix_internal(
                input_pbix, output_pbix, param_name, new_value, result['processing_log']
            )
            
            if not processing_success:
                error_msg = "PBIX processing failed during internal operations"
                result['errors'].append(error_msg)
                self._add_error("ProcessingFailure", error_msg, "pbix_processing", input_pbix)
                
                # Attempt automatic rollback
                self.logger.info("=== PERFORMING AUTOMATIC ROLLBACK ===")
                self.rollback_performed = True
                self.rollback_successful = self.rollback_from_backup(backup_info)
                result['rollback_performed'] = self.rollback_performed
                
                return result
            
            # Create parameter tracking info
            param_info = ParameterInfo(
                name=param_name,
                original_value=param_validation['current_value'],
                new_value=new_value,
                pattern_used=param_validation['parameter_pattern'],
                update_successful=True,
                verification_successful=False,  # Will be updated after post-validation
                detection_method="regex_pattern_matching",
                timestamp=datetime.now().isoformat()
            )
            
            # Post-run validation
            self.logger.info("=== POST-RUN VALIDATION ===")
            
            # Validate output file was created correctly
            output_validation = self.validate_input_file(output_pbix)
            result['post_validation']['output_file'] = output_validation
            
            if output_validation['errors']:
                self.logger.warning("Post-validation warnings for output file")
            
            # Validate parameter was updated correctly
            param_check = self.validate_parameter_exists(output_pbix, param_name)
            result['post_validation']['parameter_updated'] = param_check
            
            # Verify parameter value matches what we intended to set
            if param_check['parameter_found']:
                if param_check['current_value'] == new_value:
                    result['post_validation']['value_matches'] = True
                    param_info.verification_successful = True
                    self.logger.info(f"✅ Parameter '{param_name}' successfully updated: '{param_validation['current_value']}' -> '{new_value}'")
                else:
                    result['post_validation']['value_matches'] = False
                    param_info.verification_successful = False
                    error_msg = (f"Parameter update verification failed. "
                               f"Expected: '{new_value}', Found: '{param_check['current_value']}'")
                    result['errors'].append(error_msg)
                    self._add_error("VerificationFailure", error_msg, "post_validation", output_pbix)
            else:
                error_msg = f"Parameter '{param_name}' not found in updated file"
                result['errors'].append(error_msg)
                self._add_error("PostValidationParameterMissing", error_msg, "post_validation", output_pbix)
            
            # Store parameter info
            self.parameters.append(param_info)
            result['parameter_info'] = asdict(param_info)
            
            # Determine overall success
            result['success'] = len(result['errors']) == 0
            result['operation_end'] = datetime.now().isoformat()
            
            if result['success']:
                self.logger.info("=== PBIX PARAMETER UPDATE COMPLETED SUCCESSFULLY ===")
            else:
                self.logger.error("=== PBIX PARAMETER UPDATE COMPLETED WITH ERRORS ===")
            
        except Exception as e:
            error_msg = f"Critical processing error: {str(e)}"
            result['errors'].append(error_msg)
            stack_trace = traceback.format_exc()
            self._add_error("CriticalProcessingError", error_msg, "main_processing", input_pbix, 
                          stack_trace=stack_trace)
            self.logger.error(f"Critical error during processing: {e}")
            
            # Attempt rollback if backup exists
            if self.backups:
                self.logger.info("=== PERFORMING EMERGENCY ROLLBACK ===")
                self.rollback_performed = True
                self.rollback_successful = self.rollback_from_backup(self.backups[-1])
                result['rollback_performed'] = self.rollback_performed
            
        return result
    
    def _process_pbix_internal(self, input_pbix: str, output_pbix: str, 
                             param_name: str, new_value: str, log: List[str]) -> bool:
        """Internal PBIX processing with detailed logging."""
        temp_dir = tempfile.mkdtemp()
        try:
            log.append(f"Created temporary directory: {temp_dir}")
            self.logger.debug(f"Temporary extraction directory: {temp_dir}")
            
            # Extract all contents
            log.append("Extracting PBIX contents...")
            with zipfile.ZipFile(input_pbix, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            log.append("PBIX extraction completed successfully")
            
            # Find DataMashup file using enhanced detection
            log.append("Locating DataMashup file...")
            mashup_file = self._find_datamashup_file(temp_dir)
            if not mashup_file:
                raise FileNotFoundError("DataMashup file not found in PBIX contents")
            
            rel_path = os.path.relpath(mashup_file, temp_dir)
            log.append(f"DataMashup file found at: {rel_path}")
            
            # Update parameter in DataMashup
            log.append(f"Updating parameter '{param_name}'...")
            self._update_parameter_in_mashup(mashup_file, param_name, new_value, log)
            
            # Create new PBIX file
            log.append("Creating updated PBIX file...")
            with zipfile.ZipFile(output_pbix, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                file_count = 0
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, temp_dir)
                        zip_out.write(full_path, rel_path)
                        file_count += 1
                
                log.append(f"Added {file_count} files to updated PBIX")
            
            log.append("Updated PBIX file created successfully")
            return True
            
        except Exception as e:
            error_msg = f"Internal processing error: {str(e)}"
            log.append(error_msg)
            self._add_error("InternalProcessingError", error_msg, "internal_processing", input_pbix)
            return False
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                log.append("Temporary directory cleaned up")
            except Exception as e:
                log.append(f"Warning: Could not clean up temporary directory: {e}")
    
    def _find_datamashup_file(self, temp_dir: str) -> Optional[str]:
        """Enhanced DataMashup file detection with multiple fallback strategies."""
        self.logger.debug("Starting DataMashup file search...")
        
        # Primary locations to check (most common first)
        potential_locations = [
            'DataMashup',                    # Root level (most common)
            'DataModel/DataMashup',          # In DataModel folder
            'Model/DataMashup',              # In Model folder  
            'Mashup/DataMashup',             # In Mashup folder
            'PowerQuery/DataMashup',         # In PowerQuery folder
            'DataMashup.bin',                # With .bin extension
            'DataMashup.m',                  # With .m extension
            'DataMashup.pq',                 # With .pq extension
            'Report/DataMashup',             # In Report folder
            'DataModelSchema/DataMashup',    # In DataModelSchema folder
            'Queries/DataMashup',            # In Queries folder
            'DataSources/DataMashup'         # In DataSources folder
        ]
        
        # Check common locations first
        for location in potential_locations:
            mashup_path = os.path.join(temp_dir, location)
            if os.path.exists(mashup_path):
                self.logger.debug(f"DataMashup found at standard location: {location}")
                return mashup_path
        
        # Recursive search for files with 'mashup' in name
        self.logger.debug("Performing recursive search for mashup files...")
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if 'mashup' in file.lower() or 'datamashup' in file.lower():
                    full_path = os.path.join(root, file)
                    if self._verify_mashup_content(full_path):
                        rel_path = os.path.relpath(full_path, temp_dir)
                        self.logger.debug(f"DataMashup found via name search: {rel_path}")
                        return full_path
        
        # Last resort: search all files for M-code patterns
        self.logger.debug("Performing content-based search for M-code...")
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                # Skip obviously binary files
                if file.endswith(('.png', '.jpg', '.gif', '.ico', '.exe', '.dll', '.pdb')):
                    continue
                    
                full_path = os.path.join(root, file)
                if self._verify_mashup_content(full_path):
                    rel_path = os.path.relpath(full_path, temp_dir)
                    self.logger.debug(f"DataMashup found via content search: {rel_path}")
                    return full_path
        
        self.logger.warning("DataMashup file not found using any detection method")
        return None
    
    def _verify_mashup_content(self, file_path: str) -> bool:
        """Verify that a file contains M-code (DataMashup content)."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read(2048)  # Read first 2KB
            
            text, _ = self._decode_with_fallback(content)
            if not text:
                return False
            
            # M-code patterns that indicate this is a DataMashup file
            m_code_patterns = [
                'let ', 'Source = ', 'Parameter.', '#"', '= Table.', 
                'in ', 'Query = ', 'shared ', 'Table.', 'List.'
            ]
            
            # Count how many patterns are found
            pattern_count = sum(1 for pattern in m_code_patterns if pattern in text)
            
            # If we find multiple M-code patterns, this is likely the DataMashup
            return pattern_count >= 3
            
        except Exception:
            return False
    
    def _decode_with_fallback(self, data: bytes) -> Tuple[Optional[str], Optional[str]]:
        """Decode bytes with multiple encoding fallbacks."""
        encodings = ['latin1', 'utf-8', 'utf-16le', 'utf-16be', 'cp1252']
        
        for encoding in encodings:
            try:
                text = data.decode(encoding)
                return text, encoding
            except UnicodeDecodeError:
                continue
        
        # Final fallback: decode with errors='ignore'
        try:
            text = data.decode('utf-8', errors='ignore')
            return text, 'utf-8_with_errors_ignored'
        except Exception:
            return None, None
    
    def _detect_parameters(self, mashup_file: str) -> List[Dict[str, str]]:
        """Detect and extract parameters from DataMashup file."""
        parameters = []
        
        try:
            with open(mashup_file, 'rb') as f:
                data = f.read()
            
            text, encoding = self._decode_with_fallback(data)
            if not text:
                return parameters
            
            # Enhanced parameter detection patterns
            param_patterns = [
                # Standard parameter pattern: let ParamName = "value"
                re.compile(r'let\s+(\w+)\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE),
                # Parameter without quotes: let ParamName = value
                re.compile(r'let\s+(\w+)\s*=\s*([^,;\r\n\s][^,;\r\n]*)', re.IGNORECASE)
            ]
            
            for pattern in param_patterns:
                matches = pattern.findall(text)
                for param_name, param_value in matches:
                    # Filter out obvious non-parameters
                    if (len(param_name) > 1 and 
                        not param_name.lower().startswith(('table', 'source', 'query')) and
                        param_name not in [p['name'] for p in parameters]):
                        
                        parameters.append({
                            'name': param_name,
                            'value': param_value.strip(),
                            'type': 'detected',
                            'encoding_used': encoding
                        })
            
        except Exception as e:
            self._add_error("ParameterDetectionError", str(e), "parameter_detection", mashup_file, "warning")
        
        return parameters
    
    def _update_parameter_in_mashup(self, mashup_path: str, param_name: str, 
                                   new_value: str, log: List[str]):
        """Update parameter in DataMashup file with comprehensive error handling."""
        log.append(f"Reading DataMashup file: {os.path.basename(mashup_path)}")
        
        with open(mashup_path, 'rb') as f:
            data = f.read()
        
        text, encoding = self._decode_with_fallback(data)
        if not text:
            raise ValueError("Could not decode DataMashup file with any known encoding")
        
        log.append(f"DataMashup decoded successfully using {encoding}")
        
        # Multiple update patterns to handle different M-code formats
        patterns = [
            # Standard quoted parameter: let ParamName = "value"
            re.compile(r'(let\s+' + re.escape(param_name) + r'\s*=\s*")([^"]*)"', re.IGNORECASE),
            # Single quoted parameter: let ParamName = 'value'
            re.compile(r"(let\s+" + re.escape(param_name) + r"\s*=\s*')([^']*)'", re.IGNORECASE),
            # Unquoted parameter: let ParamName = value
            re.compile(r'(let\s+' + re.escape(param_name) + r'\s*=\s*)([^,;\r\n]+)', re.IGNORECASE)
        ]
        
        updated = False
        pattern_used = None
        
        for i, pattern in enumerate(patterns):
            if pattern.search(text):
                # Always quote the new value for consistency
                updated_text = pattern.sub(r'\1"' + new_value + '"', text)
                if updated_text != text:
                    text = updated_text
                    updated = True
                    pattern_used = f"Pattern {i+1}"
                    log.append(f"Parameter updated using {pattern_used}")
                    break
        
        if not updated:
            raise ValueError(f"Parameter '{param_name}' could not be updated - no matching pattern found")
        
        # Write updated content back to file
        with open(mashup_path, 'wb') as f:
            f.write(text.encode(encoding))
        
        log.append("DataMashup file updated successfully")
    
    def generate_configuration_summary(self, result: Dict[str, Any], 
                                     input_file: str, output_file: str, 
                                     summary_file_path: str) -> ConfigurationSummary:
        """Generate comprehensive configuration summary with all tracking data."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.logger.info(f"Generating configuration summary: {summary_file_path}")
        
        # Get comprehensive file information
        input_file_info = self._get_file_info(input_file)
        output_file_info = self._get_file_info(output_file)
        
        # Create complete configuration summary
        summary = ConfigurationSummary(
            session_id=self.session_id,
            operation_type="pbix_parameter_update",
            start_timestamp=self.start_time.isoformat(),
            end_timestamp=end_time.isoformat(),
            duration_seconds=round(duration, 3),
            success=result.get('success', False),
            system_environment=self._get_system_environment(),
            input_file=input_file_info,
            output_file=output_file_info,
            parameters=self.parameters,
            backups=self.backups,
            errors=self.errors,
            warnings=self.warnings,
            validation_results=result,
            rollback_performed=self.rollback_performed,
            rollback_successful=self.rollback_successful,
            summary_file_path=str(Path(summary_file_path).resolve())
        )
        
        # Save summary to JSON file with error handling
        try:
            with open(summary_file_path, 'w', encoding='utf-8') as f:
                # Convert dataclasses to dict for JSON serialization
                summary_dict = asdict(summary)
                json.dump(summary_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration summary saved successfully: {summary_file_path}")
            
        except Exception as e:
            self._add_error("SummarySaveError", str(e), "summary_generation", summary_file_path)
            self.logger.error(f"Failed to save configuration summary: {e}")
        
        return summary

def process_pbix(input_pbix: str, output_pbix: str, param_name: str, new_value: str, 
                verbose: bool = False, summary_json: Optional[str] = None) -> bool:
    """
    Convenience function to process PBIX file with comprehensive features.
    
    Args:
        input_pbix: Path to input PBIX file
        output_pbix: Path to output PBIX file  
        param_name: Name of parameter to update
        new_value: New value for the parameter
        verbose: Enable verbose logging
        summary_json: Path to save JSON summary (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create updater instance
        updater = PBIXParameterUpdater(verbose=verbose)
        
        # Process with comprehensive validation
        result = updater.process_pbix_with_validation(
            input_pbix, output_pbix, param_name, new_value
        )
        
        # Generate summary if requested
        if summary_json:
            updater.generate_configuration_summary(
                result, input_pbix, output_pbix, summary_json
            )
        
        return result['success']
        
    except Exception as e:
        if verbose:
            print(f"Error: {e}")
        return False

def main():
    """Main execution function with comprehensive argument handling."""
    parser = argparse.ArgumentParser(
        description="Comprehensive PBIX Parameter Update Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python update_pbix_parameter.py -i report.pbix -o updated.pbix -p BasePath -v "C:\\New\\Path"
  
  # With comprehensive validation and JSON summary
  python update_pbix_parameter.py -i report.pbix -o updated.pbix -p BasePath -v "C:\\New\\Path" --validate-all --summary-json config.json --verbose
  
  # Multiple parameters (run script multiple times or use main_workflow.py)
        """
    )
    
    parser.add_argument('--input', '-i', required=True, 
                       help="Path to input .pbix file")
    parser.add_argument('--output', '-o', required=True, 
                       help="Path to output .pbix file")
    parser.add_argument('--param', '-p', required=True, 
                       help="Parameter name to update")
    parser.add_argument('--value', '-v', required=True, 
                       help="New value for the parameter")
    parser.add_argument('--validate-all', action='store_true', 
                       help="Enable comprehensive validation (recommended)")
    parser.add_argument('--verbose', action='store_true', 
                       help="Enable verbose output and detailed logging")
    parser.add_argument('--summary-json', '-s', 
                       help="Path to save JSON configuration summary")
    parser.add_argument('--no-backup', action='store_true', 
                       help="Skip backup creation (not recommended)")
    
    args = parser.parse_args()
    
    # Generate summary file path if not provided
    if not args.summary_json:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.summary_json = f"pbix_config_summary_{timestamp}.json"
    
    try:
        print("COMPREHENSIVE PBIX PARAMETER UPDATE TOOL")
        print("=" * 80)
        print(f"Input File: {args.input}")
        print(f"Output File: {args.output}")
        print(f"Parameter: {args.param}")
        print(f"New Value: {args.value}")
        print(f"JSON Summary: {args.summary_json}")
        print("=" * 80)
        
        # Create updater instance
        updater = PBIXParameterUpdater(verbose=args.verbose)
        
        # Process with comprehensive validation
        result = updater.process_pbix_with_validation(
            args.input, args.output, args.param, args.value
        )
        
        # Generate configuration summary
        summary = updater.generate_configuration_summary(
            result, args.input, args.output, args.summary_json
        )
        
        # Print results summary
        print(f"\n{'='*80}")
        print("OPERATION SUMMARY")
        print(f"{'='*80}")
        print(f"Session ID: {summary.session_id}")
        print(f"Success: {'✅ YES' if summary.success else '❌ NO'}")
        print(f"Duration: {summary.duration_seconds:.3f} seconds")
        print(f"Parameters Updated: {len(summary.parameters)}")
        print(f"Backups Created: {len(summary.backups)}")
        print(f"Errors: {len(summary.errors)}")
        print(f"Warnings: {len(summary.warnings)}")
        print(f"Rollback Performed: {'Yes' if summary.rollback_performed else 'No'}")
        
        # Print error details if any
        if summary.errors:
            print(f"\nErrors:")
            for error in summary.errors[:5]:  # Show first 5 errors
                print(f"  • [{error.error_id}] {error.error_message}")
            if len(summary.errors) > 5:
                print(f"  ... and {len(summary.errors) - 5} more errors")
        
        print(f"\nLog File: {updater.log_filename}")
        print(f"JSON Summary: {args.summary_json}")
        
        if summary.success:
            print(f"\n✅ SUCCESS: PBIX parameter updated successfully!")
            return 0
        else:
            print(f"\n❌ FAILED: PBIX parameter update failed!")
            print("Check the log file and JSON summary for detailed error information.")
            return 1
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())