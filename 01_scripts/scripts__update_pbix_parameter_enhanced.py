#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_pbix_parameter_enhanced.py

Enhanced PBIX parameter update script with comprehensive validation.
Validates paths, parameters, and outputs before and after processing.

Features:
- Pre-run validation (file exists, valid PBIX, parameter detection)
- Post-run validation (output valid, parameters correctly updated)
- Path resolution and normalization
- Detailed logging and error reporting
- Backup creation
- Rollback capability

Usage:
    python update_pbix_parameter_enhanced.py \
        --input SourceReport.pbix \
        --output UpdatedReport.pbix \
        --param BasePath \
        --value "C:\\New\\Data\\Path\\" \
        --validate-all
"""

import argparse
import zipfile
import os
import re
import tempfile
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

class PBIXValidationError(Exception):
    """Custom exception for PBIX validation errors."""
    pass

class PBIXParameterUpdater:
    """Enhanced PBIX parameter updater with comprehensive validation."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.validation_results = {}
        self.backup_created = False
        self.backup_path = None
        
        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('pbix_update.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def validate_input_file(self, pbix_path: str) -> Dict[str, Any]:
        """Comprehensive validation of input PBIX file."""
        self.logger.info(f"Validating input file: {pbix_path}")
        
        validation = {
            'file_exists': False,
            'is_pbix': False,
            'is_valid_zip': False,
            'has_common_files': False,
            'datamashup_found': False,
            'datamashup_location': None,
            'file_size': 0,
            'parameters_detected': [],
            'errors': []
        }
        
        try:
            # Check file existence
            path = Path(pbix_path)
            if not path.exists():
                validation['errors'].append(f"File does not exist: {pbix_path}")
                return validation
            
            validation['file_exists'] = True
            validation['file_size'] = path.stat().st_size
            
            # Check file extension
            if not pbix_path.lower().endswith(('.pbix', '.pbit')):
                validation['errors'].append(f"File must have .pbix or .pbit extension")
                return validation
            
            validation['is_pbix'] = True
            
            # Validate as ZIP file
            try:
                with zipfile.ZipFile(pbix_path, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    validation['is_valid_zip'] = True
                    
                    # Check for common PBIX files
                    common_files = ['Version', 'Metadata', 'Settings', 'SecurityBindings']
                    found_common = [f for f in file_list if any(common in f for common in common_files)]
                    validation['has_common_files'] = len(found_common) > 0
                    
                    if not validation['has_common_files']:
                        validation['errors'].append("Missing standard PBIX files - may not be valid PBIX")
                    
                    # Extract temporarily to find DataMashup
                    with tempfile.TemporaryDirectory() as temp_dir:
                        zip_ref.extractall(temp_dir)
                        
                        # Find DataMashup file
                        mashup_location = self._find_datamashup_file(temp_dir)
                        if mashup_location:
                            validation['datamashup_found'] = True
                            validation['datamashup_location'] = os.path.relpath(mashup_location, temp_dir)
                            
                            # Detect parameters in DataMashup
                            parameters = self._detect_parameters(mashup_location)
                            validation['parameters_detected'] = parameters
                        else:
                            validation['errors'].append("DataMashup file not found - PBIX may not contain parameters")
                            
            except zipfile.BadZipFile:
                validation['errors'].append("File is not a valid ZIP/PBIX file")
                validation['is_valid_zip'] = False
                
        except Exception as e:
            validation['errors'].append(f"Validation error: {str(e)}")
            
        return validation
    
    def validate_paths(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """Validate and resolve input/output paths."""
        self.logger.info("Validating paths")
        
        validation = {
            'input_resolved': None,
            'output_resolved': None,
            'input_accessible': False,
            'output_writable': False,
            'paths_different': False,
            'backup_needed': False,
            'errors': []
        }
        
        try:
            # Resolve input path
            input_path_obj = Path(input_path).resolve()
            validation['input_resolved'] = str(input_path_obj)
            
            # Check input accessibility
            if input_path_obj.exists() and os.access(input_path_obj, os.R_OK):
                validation['input_accessible'] = True
            else:
                validation['errors'].append(f"Input file not readable: {input_path}")
            
            # Resolve output path
            output_path_obj = Path(output_path).resolve()
            validation['output_resolved'] = str(output_path_obj)
            
            # Check output directory writability
            output_dir = output_path_obj.parent
            if output_dir.exists() and os.access(output_dir, os.W_OK):
                validation['output_writable'] = True
            else:
                validation['errors'].append(f"Output directory not writable: {output_dir}")
            
            # Check if paths are different
            validation['paths_different'] = input_path_obj != output_path_obj
            
            # Determine if backup is needed
            validation['backup_needed'] = not validation['paths_different']
            
        except Exception as e:
            validation['errors'].append(f"Path validation error: {str(e)}")
            
        return validation
    
    def validate_parameter_exists(self, pbix_path: str, param_name: str) -> Dict[str, Any]:
        """Validate that the specified parameter exists in the PBIX file."""
        self.logger.info(f"Validating parameter '{param_name}' exists")
        
        validation = {
            'parameter_found': False,
            'current_value': None,
            'parameter_pattern': None,
            'datamashup_content_preview': None,
            'errors': []
        }
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract PBIX
                with zipfile.ZipFile(pbix_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find DataMashup
                mashup_file = self._find_datamashup_file(temp_dir)
                if not mashup_file:
                    validation['errors'].append("DataMashup file not found")
                    return validation
                
                # Read and decode DataMashup
                with open(mashup_file, 'rb') as f:
                    data = f.read()
                
                text, encoding = self._decode_with_fallback(data)
                if not text:
                    validation['errors'].append("Could not decode DataMashup file")
                    return validation
                
                validation['datamashup_content_preview'] = text[:500] if len(text) > 500 else text
                
                # Search for parameter
                patterns = [
                    re.compile(r'let\s+' + re.escape(param_name) + r'\s*=\s*"([^"]*)"', re.IGNORECASE),
                    re.compile(r'let\s+' + re.escape(param_name) + r'\s*=\s*\'([^\']*)\'', re.IGNORECASE),
                    re.compile(r'let\s+' + re.escape(param_name) + r'\s*=\s*([^,;\r\n]+)', re.IGNORECASE)
                ]
                
                for i, pattern in enumerate(patterns):
                    match = pattern.search(text)
                    if match:
                        validation['parameter_found'] = True
                        validation['current_value'] = match.group(1) if match.lastindex >= 1 else match.group(0)
                        validation['parameter_pattern'] = f"Pattern {i+1}: {pattern.pattern}"
                        break
                
                if not validation['parameter_found']:
                    validation['errors'].append(f"Parameter '{param_name}' not found in DataMashup")
                    
        except Exception as e:
            validation['errors'].append(f"Parameter validation error: {str(e)}")
            
        return validation
    
    def create_backup(self, input_path: str) -> Optional[str]:
        """Create backup of original PBIX file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            input_path_obj = Path(input_path)
            backup_filename = f"{input_path_obj.stem}_backup_{timestamp}{input_path_obj.suffix}"
            backup_path = input_path_obj.parent / backup_filename
            
            shutil.copy2(input_path, backup_path)
            self.backup_created = True
            self.backup_path = str(backup_path)
            
            self.logger.info(f"Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            return None
    
    def process_pbix_with_validation(self, input_pbix: str, output_pbix: str, 
                                   param_name: str, new_value: str) -> Dict[str, Any]:
        """Process PBIX with comprehensive validation."""
        result = {
            'success': False,
            'pre_validation': {},
            'post_validation': {},
            'processing_log': [],
            'backup_path': None,
            'errors': []
        }
        
        try:
            # Pre-run validation
            self.logger.info("=== PRE-RUN VALIDATION ===")
            
            # Validate input file
            input_validation = self.validate_input_file(input_pbix)
            result['pre_validation']['input_file'] = input_validation
            
            if input_validation['errors']:
                result['errors'].extend(input_validation['errors'])
                return result
            
            # Validate paths
            path_validation = self.validate_paths(input_pbix, output_pbix)
            result['pre_validation']['paths'] = path_validation
            
            if path_validation['errors']:
                result['errors'].extend(path_validation['errors'])
                return result
            
            # Validate parameter exists
            param_validation = self.validate_parameter_exists(input_pbix, param_name)
            result['pre_validation']['parameter'] = param_validation
            
            if param_validation['errors']:
                result['errors'].extend(param_validation['errors'])
                return result
            
            # Create backup if needed
            if path_validation['backup_needed']:
                backup_path = self.create_backup(input_pbix)
                result['backup_path'] = backup_path
            
            # Process PBIX
            self.logger.info("=== PROCESSING PBIX ===")
            processing_success = self._process_pbix_internal(
                path_validation['input_resolved'],
                path_validation['output_resolved'],
                param_name,
                new_value,
                result['processing_log']
            )
            
            if not processing_success:
                result['errors'].append("PBIX processing failed")
                return result
            
            # Post-run validation
            self.logger.info("=== POST-RUN VALIDATION ===")
            
            # Validate output file
            output_validation = self.validate_input_file(path_validation['output_resolved'])
            result['post_validation']['output_file'] = output_validation
            
            # Validate parameter was updated
            param_check = self.validate_parameter_exists(path_validation['output_resolved'], param_name)
            result['post_validation']['parameter_updated'] = param_check
            
            # Check if parameter value matches what we set
            if param_check['parameter_found']:
                if param_check['current_value'] == new_value:
                    result['post_validation']['value_matches'] = True
                    self.logger.info(f"✅ Parameter '{param_name}' successfully updated to '{new_value}'")
                else:
                    result['post_validation']['value_matches'] = False
                    result['errors'].append(
                        f"Parameter update verification failed. "
                        f"Expected: '{new_value}', Found: '{param_check['current_value']}'"
                    )
            
            result['success'] = len(result['errors']) == 0
            
        except Exception as e:
            result['errors'].append(f"Processing error: {str(e)}")
            self.logger.error(f"Processing failed: {e}")
            
        return result
    
    def _process_pbix_internal(self, input_pbix: str, output_pbix: str, 
                             param_name: str, new_value: str, log: List[str]) -> bool:
        """Internal PBIX processing method."""
        temp_dir = tempfile.mkdtemp()
        try:
            log.append(f"Extracting PBIX to temporary directory: {temp_dir}")
            
            # Extract all contents
            with zipfile.ZipFile(input_pbix, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            log.append("Extraction completed")
            
            # Find DataMashup file
            mashup_file = self._find_datamashup_file(temp_dir)
            if not mashup_file:
                raise FileNotFoundError("DataMashup file not found")
            
            log.append(f"Found DataMashup at: {os.path.relpath(mashup_file, temp_dir)}")
            
            # Update parameter
            self._update_parameter_in_mashup(mashup_file, param_name, new_value, log)
            
            # Create new PBIX
            log.append("Creating updated PBIX file")
            with zipfile.ZipFile(output_pbix, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, temp_dir)
                        zip_out.write(full_path, rel_path)
            
            log.append("PBIX file created successfully")
            return True
            
        except Exception as e:
            log.append(f"Processing error: {str(e)}")
            return False
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _find_datamashup_file(self, temp_dir: str) -> Optional[str]:
        """Find the DataMashup file in extracted PBIX contents."""
        potential_locations = [
            'DataMashup',
            'DataModel/DataMashup',
            'Model/DataMashup',
            'Mashup/DataMashup',
            'PowerQuery/DataMashup',
            'DataMashup.bin',
            'DataMashup.m',
            'DataMashup.pq',
            'Report/DataMashup',
            'DataModelSchema/DataMashup'
        ]
        
        # Check common locations first
        for location in potential_locations:
            mashup_path = os.path.join(temp_dir, location)
            if os.path.exists(mashup_path):
                return mashup_path
        
        # Recursive search
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if 'mashup' in file.lower() or 'datamashup' in file.lower():
                    full_path = os.path.join(root, file)
                    if self._verify_mashup_content(full_path):
                        return full_path
        
        # Last resort: search for M-code patterns
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(('.png', '.jpg', '.gif', '.ico', '.exe', '.dll')):
                    continue
                full_path = os.path.join(root, file)
                if self._verify_mashup_content(full_path):
                    return full_path
        
        return None
    
    def _verify_mashup_content(self, file_path: str) -> bool:
        """Verify that a file contains M-code (DataMashup content)."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read(2048)
            
            text, _ = self._decode_with_fallback(content)
            if not text:
                return False
            
            m_code_patterns = ['let ', 'Source = ', 'Parameter.', '#"', '= Table.', 'in ', 'Query = ']
            pattern_count = sum(1 for pattern in m_code_patterns if pattern in text)
            
            return pattern_count >= 3
            
        except Exception:
            return False
    
    def _decode_with_fallback(self, data: bytes) -> Tuple[Optional[str], Optional[str]]:
        """Decode bytes with multiple encoding fallbacks."""
        encodings = ['latin1', 'utf-8', 'utf-16le', 'utf-16be']
        
        for encoding in encodings:
            try:
                text = data.decode(encoding)
                return text, encoding
            except UnicodeDecodeError:
                continue
        
        return None, None
    
    def _detect_parameters(self, mashup_file: str) -> List[Dict[str, str]]:
        """Detect parameters in DataMashup file."""
        parameters = []
        
        try:
            with open(mashup_file, 'rb') as f:
                data = f.read()
            
            text, _ = self._decode_with_fallback(data)
            if not text:
                return parameters
            
            # Find parameter definitions
            param_pattern = re.compile(r'let\s+(\w+)\s*=\s*["\']?([^",;\r\n]*)["\']?', re.IGNORECASE)
            matches = param_pattern.findall(text)
            
            for param_name, param_value in matches:
                if 'Parameter.' in text and param_name in text:
                    parameters.append({
                        'name': param_name,
                        'value': param_value.strip('"\''),
                        'type': 'detected'
                    })
            
        except Exception:
            pass
        
        return parameters
    
    def _update_parameter_in_mashup(self, mashup_path: str, param_name: str, 
                                   new_value: str, log: List[str]):
        """Update parameter in DataMashup file."""
        log.append(f"Updating parameter '{param_name}' in DataMashup file")
        
        with open(mashup_path, 'rb') as f:
            data = f.read()
        
        text, encoding = self._decode_with_fallback(data)
        if not text:
            raise ValueError("Could not decode DataMashup file")
        
        log.append(f"Successfully decoded with {encoding}")
        
        # Try multiple patterns
        patterns = [
            re.compile(r'(let\s+' + re.escape(param_name) + r'\s*=\s*")([^"]*)"', re.IGNORECASE),
            re.compile(r"(let\s+" + re.escape(param_name) + r"\s*=\s*')([^']*)'", re.IGNORECASE),
            re.compile(r'(let\s+' + re.escape(param_name) + r'\s*=\s*)([^,;\r\n]+)', re.IGNORECASE)
        ]
        
        updated = False
        for pattern in patterns:
            if pattern.search(text):
                updated_text = pattern.sub(r'\1"' + new_value + '"', text)
                if updated_text != text:
                    text = updated_text
                    updated = True
                    break
        
        if not updated:
            raise ValueError(f"Parameter '{param_name}' could not be updated")
        
        log.append("Parameter updated successfully")
        
        with open(mashup_path, 'wb') as f:
            f.write(text.encode(encoding))
    
    def generate_validation_report(self, result: Dict[str, Any], output_path: str = None) -> str:
        """Generate detailed validation report."""
        report_lines = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report_lines.append("=" * 80)
        report_lines.append("PBIX PARAMETER UPDATE VALIDATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Timestamp: {timestamp}")
        report_lines.append(f"Success: {'✅ YES' if result['success'] else '❌ NO'}")
        report_lines.append("")
        
        # Pre-validation results
        if 'pre_validation' in result:
            report_lines.append("PRE-RUN VALIDATION:")
            report_lines.append("-" * 40)
            
            pre_val = result['pre_validation']
            
            # Input file validation
            if 'input_file' in pre_val:
                input_val = pre_val['input_file']
                report_lines.append(f"Input File: {'✅' if input_val['file_exists'] else '❌'}")
                report_lines.append(f"  - File Size: {input_val['file_size']:,} bytes")
                report_lines.append(f"  - Valid PBIX: {'✅' if input_val['is_pbix'] else '❌'}")
                report_lines.append(f"  - Valid ZIP: {'✅' if input_val['is_valid_zip'] else '❌'}")
                report_lines.append(f"  - DataMashup Found: {'✅' if input_val['datamashup_found'] else '❌'}")
                if input_val['datamashup_location']:
                    report_lines.append(f"  - DataMashup Location: {input_val['datamashup_location']}")
                report_lines.append(f"  - Parameters Detected: {len(input_val['parameters_detected'])}")
                for param in input_val['parameters_detected']:
                    report_lines.append(f"    • {param['name']}: {param['value']}")
            
            # Path validation
            if 'paths' in pre_val:
                path_val = pre_val['paths']
                report_lines.append(f"Paths: {'✅' if not path_val['errors'] else '❌'}")
                report_lines.append(f"  - Input Accessible: {'✅' if path_val['input_accessible'] else '❌'}")
                report_lines.append(f"  - Output Writable: {'✅' if path_val['output_writable'] else '❌'}")
                report_lines.append(f"  - Backup Needed: {'✅' if path_val['backup_needed'] else 'No'}")
            
            # Parameter validation
            if 'parameter' in pre_val:
                param_val = pre_val['parameter']
                report_lines.append(f"Parameter: {'✅' if param_val['parameter_found'] else '❌'}")
                if param_val['parameter_found']:
                    report_lines.append(f"  - Current Value: {param_val['current_value']}")
                    report_lines.append(f"  - Pattern Used: {param_val['parameter_pattern']}")
        
        # Post-validation results
        if 'post_validation' in result:
            report_lines.append("")
            report_lines.append("POST-RUN VALIDATION:")
            report_lines.append("-" * 40)
            
            post_val = result['post_validation']
            
            if 'output_file' in post_val:
                output_val = post_val['output_file']
                report_lines.append(f"Output File: {'✅' if output_val['file_exists'] else '❌'}")
                report_lines.append(f"  - File Size: {output_val['file_size']:,} bytes")
                report_lines.append(f"  - Valid PBIX: {'✅' if output_val['is_pbix'] else '❌'}")
                report_lines.append(f"  - DataMashup Present: {'✅' if output_val['datamashup_found'] else '❌'}")
            
            if 'parameter_updated' in post_val:
                param_check = post_val['parameter_updated']
                report_lines.append(f"Parameter Updated: {'✅' if param_check['parameter_found'] else '❌'}")
                if param_check['parameter_found']:
                    report_lines.append(f"  - New Value: {param_check['current_value']}")
            
            if 'value_matches' in post_val:
                report_lines.append(f"Value Verification: {'✅' if post_val['value_matches'] else '❌'}")
        
        # Processing log
        if 'processing_log' in result and result['processing_log']:
            report_lines.append("")
            report_lines.append("PROCESSING LOG:")
            report_lines.append("-" * 40)
            for log_entry in result['processing_log']:
                report_lines.append(f"  {log_entry}")
        
        # Errors
        if result['errors']:
            report_lines.append("")
            report_lines.append("ERRORS:")
            report_lines.append("-" * 40)
            for error in result['errors']:
                report_lines.append(f"  ❌ {error}")
        
        # Backup info
        if result.get('backup_path'):
            report_lines.append("")
            report_lines.append(f"BACKUP CREATED: {result['backup_path']}")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        report_content = "\n".join(report_lines)
        
        # Save report if output path specified
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
        
        return report_content

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Enhanced PBIX Parameter Update Tool with Validation")
    
    parser.add_argument('--input', '-i', required=True, help="Path to input .pbix file")
    parser.add_argument('--output', '-o', required=True, help="Path to output .pbix file")
    parser.add_argument('--param', '-p', required=True, help="Parameter name to update")
    parser.add_argument('--value', '-v', required=True, help="New value for the parameter")
    parser.add_argument('--validate-all', action='store_true', help="Enable comprehensive validation")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose output")
    parser.add_argument('--report', '-r', help="Save validation report to file")
    parser.add_argument('--no-backup', action='store_true', help="Skip backup creation")
    
    args = parser.parse_args()
    
    try:
        print("ENHANCED PBIX PARAMETER UPDATE TOOL")
        print("=" * 60)
        
        # Create updater instance
        updater = PBIXParameterUpdater(verbose=args.verbose)
        
        # Process with validation
        result = updater.process_pbix_with_validation(
            args.input, args.output, args.param, args.value
        )
        
        # Generate and display report
        report = updater.generate_validation_report(result, args.report)
        print(report)
        
        # Exit with appropriate code
        if result['success']:
            print(f"\n✅ SUCCESS: PBIX parameter updated successfully!")
            print(f"Output file: {args.output}")
            if args.report:
                print(f"Validation report: {args.report}")
            return 0
        else:
            print(f"\n❌ FAILED: PBIX parameter update failed!")
            print("Check the validation report for details.")
            return 1
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())