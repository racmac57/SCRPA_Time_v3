#!/usr/bin/env python3
"""
Comprehensive Syntax and Import Checker
=======================================

Checks every .py file in 01_scripts/ for:
1. Syntax validity (parse errors)
2. ArcPy import usage
3. Generates summary table

Author: Claude Code Assistant
Date: 2025-01-27
"""

import ast
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple

class ComprehensiveSyntaxChecker:
    def __init__(self, scripts_dir: Path):
        self.scripts_dir = scripts_dir
        self.results = []
    
    def check_syntax(self, file_path: Path) -> Tuple[bool, str]:
        """Check if Python file has valid syntax."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Try to parse the AST
            ast.parse(content)
            return True, "OK"
        
        except SyntaxError as e:
            return False, f"SyntaxError: Line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"ParseError: {str(e)[:50]}..."
    
    def check_arcpy_usage(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Check if file imports or uses arcpy.
        Returns: (uses_arcpy, import_statements)
        """
        arcpy_imports = []
        uses_arcpy = False
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Method 1: AST parsing (most reliable)
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if 'arcpy' in alias.name.lower():
                                arcpy_imports.append(f"import {alias.name}")
                                uses_arcpy = True
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and 'arcpy' in node.module.lower():
                            imports = ', '.join([alias.name for alias in node.names])
                            arcpy_imports.append(f"from {node.module} import {imports}")
                            uses_arcpy = True
            
            except:
                # Fallback to regex if AST fails
                pass
            
            # Method 2: Regex patterns (fallback and additional detection)
            import_patterns = [
                r'^\s*import\s+arcpy\b',
                r'^\s*from\s+arcpy\b',
                r'^\s*import\s+\w*arcpy\w*',
            ]
            
            for line in content.split('\n'):
                for pattern in import_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        if line.strip() not in arcpy_imports:
                            arcpy_imports.append(line.strip())
                        uses_arcpy = True
            
            # Method 3: Check for arcpy usage in code (even without explicit import)
            if not uses_arcpy:
                # Look for arcpy usage patterns
                arcpy_usage_patterns = [
                    r'\barcpy\.',
                    r'\barcpy\[',
                    r'=\s*arcpy\b',
                ]
                
                for pattern in arcpy_usage_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        uses_arcpy = True
                        if not arcpy_imports:
                            arcpy_imports.append("(arcpy used without explicit import)")
                        break
        
        except Exception:
            pass
        
        return uses_arcpy, arcpy_imports
    
    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze a single Python file."""
        result = {
            'filename': file_path.name,
            'path': str(file_path.relative_to(self.scripts_dir.parent)),
            'syntax_ok': False,
            'syntax_error': None,
            'uses_arcpy': False,
            'arcpy_imports': [],
            'file_size': 0,
            'is_backup': 'migration_backup' in file_path.name
        }
        
        try:
            # Get file size
            result['file_size'] = file_path.stat().st_size
            
            # Check syntax
            syntax_ok, syntax_msg = self.check_syntax(file_path)
            result['syntax_ok'] = syntax_ok
            if not syntax_ok:
                result['syntax_error'] = syntax_msg
            
            # Check arcpy usage
            uses_arcpy, arcpy_imports = self.check_arcpy_usage(file_path)
            result['uses_arcpy'] = uses_arcpy
            result['arcpy_imports'] = arcpy_imports
            
        except Exception as e:
            result['syntax_error'] = f"File access error: {str(e)[:50]}..."
        
        return result
    
    def analyze_all_files(self) -> List[Dict]:
        """Analyze all Python files in the directory."""
        py_files = list(self.scripts_dir.glob("*.py"))
        print(f"Found {len(py_files)} Python files in {self.scripts_dir}")
        print("Analyzing files...\n")
        
        for i, py_file in enumerate(sorted(py_files), 1):
            if i % 50 == 0:  # Progress indicator
                print(f"Processed {i}/{len(py_files)} files...")
            
            result = self.analyze_file(py_file)
            self.results.append(result)
        
        return self.results
    
    def generate_summary_table(self) -> str:
        """Generate a summary table of all results."""
        # Sort results: clean files first, then backups
        clean_files = [r for r in self.results if not r['is_backup']]
        backup_files = [r for r in self.results if r['is_backup']]
        
        sorted_results = sorted(clean_files, key=lambda x: x['filename']) + \
                        sorted(backup_files, key=lambda x: x['filename'])
        
        # Calculate column widths
        max_filename_len = max(len(r['filename']) for r in sorted_results)
        filename_width = min(max_filename_len, 50)  # Cap at 50 characters
        
        # Create table
        table = []
        table.append("SYNTAX AND ARCPY ANALYSIS SUMMARY")
        table.append("=" * 80)
        table.append("")
        
        # Header
        header = f"{'FILENAME':<{filename_width}} {'SYNTAX':<10} {'ARCPY':<8} {'TYPE':<8}"
        table.append(header)
        table.append("-" * len(header))
        
        # Data rows
        syntax_ok_count = 0
        syntax_fail_count = 0
        arcpy_count = 0
        clean_count = 0
        backup_count = 0
        
        for result in sorted_results:
            # Truncate filename if too long
            filename = result['filename']
            if len(filename) > filename_width:
                filename = filename[:filename_width-3] + "..."
            
            syntax_status = "OK" if result['syntax_ok'] else "FAIL"
            arcpy_status = "Y" if result['uses_arcpy'] else "N"
            file_type = "BACKUP" if result['is_backup'] else "CLEAN"
            
            row = f"{filename:<{filename_width}} {syntax_status:<10} {arcpy_status:<8} {file_type:<8}"
            table.append(row)
            
            # Update counters
            if result['syntax_ok']:
                syntax_ok_count += 1
            else:
                syntax_fail_count += 1
            
            if result['uses_arcpy']:
                arcpy_count += 1
            
            if result['is_backup']:
                backup_count += 1
            else:
                clean_count += 1
        
        # Summary statistics
        total_files = len(sorted_results)
        table.append("")
        table.append("SUMMARY STATISTICS")
        table.append("-" * 30)
        table.append(f"Total Files:        {total_files}")
        table.append(f"Clean Files:        {clean_count}")
        table.append(f"Backup Files:       {backup_count}")
        table.append(f"Syntax OK:          {syntax_ok_count} ({syntax_ok_count/total_files*100:.1f}%)")
        table.append(f"Syntax Errors:      {syntax_fail_count} ({syntax_fail_count/total_files*100:.1f}%)")
        table.append(f"Uses ArcPy:         {arcpy_count} ({arcpy_count/total_files*100:.1f}%)")
        
        return '\n'.join(table)
    
    def generate_detailed_report(self) -> str:
        """Generate detailed error report."""
        # Filter for errors and arcpy details
        syntax_errors = [r for r in self.results if not r['syntax_ok']]
        arcpy_users = [r for r in self.results if r['uses_arcpy']]
        
        report = []
        report.append("\nDETAILED ANALYSIS REPORT")
        report.append("=" * 50)
        
        # Syntax errors detail
        if syntax_errors:
            report.append(f"\nSYNTAX ERRORS ({len(syntax_errors)} files)")
            report.append("-" * 30)
            for result in sorted(syntax_errors, key=lambda x: x['filename']):
                report.append(f"❌ {result['filename']}")
                report.append(f"   Error: {result['syntax_error']}")
                report.append(f"   Size: {result['file_size']} bytes")
                if result['is_backup']:
                    report.append("   Type: BACKUP FILE")
                report.append("")
        
        # ArcPy usage summary (clean files only)
        clean_arcpy_users = [r for r in arcpy_users if not r['is_backup']]
        if clean_arcpy_users:
            report.append(f"\nARCPY USAGE - CLEAN FILES ({len(clean_arcpy_users)} files)")
            report.append("-" * 40)
            for result in sorted(clean_arcpy_users, key=lambda x: x['filename']):
                report.append(f"🗺️  {result['filename']}")
                for imp in result['arcpy_imports']:
                    report.append(f"   {imp}")
                report.append("")
        
        return '\n'.join(report)

def main():
    """Main execution function."""
    scripts_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts")
    
    if not scripts_dir.exists():
        print(f"❌ Scripts directory not found: {scripts_dir}")
        return 1
    
    print("🔍 COMPREHENSIVE SYNTAX AND ARCPY CHECKER")
    print("=" * 50)
    
    # Create checker and analyze
    checker = ComprehensiveSyntaxChecker(scripts_dir)
    results = checker.analyze_all_files()
    
    # Generate and display summary table
    summary_table = checker.generate_summary_table()
    print(summary_table)
    
    # Generate detailed report
    detailed_report = checker.generate_detailed_report()
    print(detailed_report)
    
    # Save combined report
    full_report = summary_table + detailed_report
    report_file = scripts_dir.parent / "comprehensive_syntax_analysis.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(full_report)
    
    print(f"\n📄 Full report saved to: {report_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())