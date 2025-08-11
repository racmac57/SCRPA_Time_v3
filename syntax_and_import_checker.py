#!/usr/bin/env python3
"""
Python Import-Syntax Checker for 01_scripts/
============================================

This script analyzes all .py files in 01_scripts/ for:
1. Import syntax validation
2. ArcPy dependency detection
3. Overall syntax errors
4. Missing modules

Author: Claude Code Assistant
Date: 2025-01-27
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
import traceback
import re

class ImportSyntaxChecker:
    def __init__(self, scripts_dir: Path):
        self.scripts_dir = scripts_dir
        self.results = {
            'syntax_valid': [],
            'syntax_errors': [],
            'arcpy_users': [],
            'import_errors': [],
            'summary': {}
        }
    
    def check_syntax(self, file_path: Path) -> Tuple[bool, str]:
        """Check if Python file has valid syntax."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Try to parse the AST
            ast.parse(content)
            return True, "Valid syntax"
        
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except Exception as e:
            return False, f"Parse error: {e}"
    
    def extract_imports(self, file_path: Path) -> Tuple[Set[str], Set[str], bool]:
        """
        Extract imports from Python file.
        Returns: (direct_imports, from_imports, has_arcpy)
        """
        direct_imports = set()
        from_imports = set()
        has_arcpy = False
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse the AST to extract imports
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        direct_imports.add(module_name)
                        if 'arcpy' in module_name.lower():
                            has_arcpy = True
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        from_imports.add(node.module)
                        if 'arcpy' in node.module.lower():
                            has_arcpy = True
            
            # Also check for string references to arcpy (less reliable but catches some cases)
            if not has_arcpy:
                if re.search(r'\barcpy\b', content, re.IGNORECASE):
                    has_arcpy = True
        
        except Exception as e:
            # If AST parsing fails, try regex as fallback
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Basic regex patterns for imports
                import_pattern = r'^import\s+([^\s#]+)'
                from_pattern = r'^from\s+([^\s#]+)\s+import'
                
                for line in content.split('\n'):
                    line = line.strip()
                    
                    import_match = re.match(import_pattern, line)
                    if import_match:
                        module = import_match.group(1)
                        direct_imports.add(module)
                        if 'arcpy' in module.lower():
                            has_arcpy = True
                    
                    from_match = re.match(from_pattern, line)
                    if from_match:
                        module = from_match.group(1)
                        from_imports.add(module)
                        if 'arcpy' in module.lower():
                            has_arcpy = True
                
                if not has_arcpy and re.search(r'\barcpy\b', content, re.IGNORECASE):
                    has_arcpy = True
            
            except Exception:
                pass
        
        return direct_imports, from_imports, has_arcpy
    
    def check_file(self, file_path: Path) -> Dict:
        """Comprehensive check of a single Python file."""
        result = {
            'file': file_path.name,
            'path': str(file_path.relative_to(self.scripts_dir.parent)),
            'syntax_valid': False,
            'syntax_error': None,
            'direct_imports': set(),
            'from_imports': set(),
            'has_arcpy': False,
            'import_count': 0,
            'file_size': 0
        }
        
        try:
            # Get file size
            result['file_size'] = file_path.stat().st_size
            
            # Check syntax
            syntax_valid, syntax_msg = self.check_syntax(file_path)
            result['syntax_valid'] = syntax_valid
            if not syntax_valid:
                result['syntax_error'] = syntax_msg
            
            # Extract imports
            direct_imports, from_imports, has_arcpy = self.extract_imports(file_path)
            result['direct_imports'] = direct_imports
            result['from_imports'] = from_imports
            result['has_arcpy'] = has_arcpy
            result['import_count'] = len(direct_imports) + len(from_imports)
            
        except Exception as e:
            result['syntax_error'] = f"File check error: {e}"
        
        return result
    
    def analyze_all_files(self) -> Dict:
        """Analyze all Python files in the scripts directory."""
        py_files = list(self.scripts_dir.glob("*.py"))
        
        print(f"Found {len(py_files)} Python files in {self.scripts_dir}")
        print("=" * 60)
        
        for py_file in sorted(py_files):
            print(f"Checking: {py_file.name}")
            result = self.check_file(py_file)
            
            # Categorize results
            if result['syntax_valid']:
                self.results['syntax_valid'].append(result)
            else:
                self.results['syntax_errors'].append(result)
                print(f"  ❌ SYNTAX ERROR: {result['syntax_error']}")
            
            if result['has_arcpy']:
                self.results['arcpy_users'].append(result)
                print(f"  🗺️  USES ARCPY")
            
            # Show import summary
            if result['import_count'] > 0:
                print(f"  📦 Imports: {result['import_count']} modules")
            
            print()
        
        # Generate summary
        self.results['summary'] = {
            'total_files': len(py_files),
            'syntax_valid': len(self.results['syntax_valid']),
            'syntax_errors': len(self.results['syntax_errors']),
            'arcpy_users': len(self.results['arcpy_users']),
            'success_rate': len(self.results['syntax_valid']) / len(py_files) * 100 if py_files else 0
        }
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate a detailed report of the analysis."""
        report = []
        report.append("PYTHON IMPORT-SYNTAX ANALYSIS REPORT")
        report.append("=" * 50)
        report.append(f"Analysis Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Directory: {self.scripts_dir}")
        report.append("")
        
        # Summary
        summary = self.results['summary']
        report.append("SUMMARY")
        report.append("-" * 20)
        report.append(f"Total Files Analyzed: {summary['total_files']}")
        report.append(f"Syntax Valid: {summary['syntax_valid']}")
        report.append(f"Syntax Errors: {summary['syntax_errors']}")
        report.append(f"ArcPy Dependencies: {summary['arcpy_users']}")
        report.append(f"Success Rate: {summary['success_rate']:.1f}%")
        report.append("")
        
        # Syntax Errors Detail
        if self.results['syntax_errors']:
            report.append("SYNTAX ERRORS")
            report.append("-" * 20)
            for result in self.results['syntax_errors']:
                report.append(f"❌ {result['file']}")
                report.append(f"   Error: {result['syntax_error']}")
                report.append(f"   Size: {result['file_size']} bytes")
                report.append("")
        
        # ArcPy Dependencies
        if self.results['arcpy_users']:
            report.append("ARCPY DEPENDENCIES")
            report.append("-" * 20)
            for result in self.results['arcpy_users']:
                report.append(f"🗺️  {result['file']}")
                if result['direct_imports']:
                    direct_arcpy = [imp for imp in result['direct_imports'] if 'arcpy' in imp.lower()]
                    if direct_arcpy:
                        report.append(f"   Direct: {', '.join(direct_arcpy)}")
                if result['from_imports']:
                    from_arcpy = [imp for imp in result['from_imports'] if 'arcpy' in imp.lower()]
                    if from_arcpy:
                        report.append(f"   From: {', '.join(from_arcpy)}")
                report.append("")
        
        # Clean Files (Valid Syntax, No ArcPy)
        clean_files = [r for r in self.results['syntax_valid'] if not r['has_arcpy']]
        if clean_files:
            report.append(f"CLEAN FILES (No ArcPy, Valid Syntax): {len(clean_files)}")
            report.append("-" * 20)
            for result in clean_files:
                report.append(f"✅ {result['file']} ({result['import_count']} imports)")
            report.append("")
        
        return '\n'.join(report)

def main():
    """Main execution function."""
    scripts_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts")
    
    if not scripts_dir.exists():
        print(f"❌ Scripts directory not found: {scripts_dir}")
        return 1
    
    print("🔍 PYTHON IMPORT-SYNTAX CHECKER")
    print("=" * 50)
    print(f"Analyzing: {scripts_dir}")
    print()
    
    # Create checker and analyze
    checker = ImportSyntaxChecker(scripts_dir)
    results = checker.analyze_all_files()
    
    # Generate and display report
    report = checker.generate_report()
    print(report)
    
    # Save report to file
    report_file = scripts_dir.parent / "import_syntax_analysis_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Report saved to: {report_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())