#!/usr/bin/env python3
"""
ArcPy Environment Analyzer for SCRPA Data Processing
Comprehensive analysis of ArcGIS Pro installation and Python environment setup.
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path
from datetime import datetime

class ArcPyEnvironmentAnalyzer:
    """Comprehensive ArcPy environment analysis and setup helper"""
    
    def __init__(self):
        self.analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'python_environment': {},
            'arcgis_installation': {},
            'arcpy_status': {},
            'project_template_access': {},
            'recommendations': []
        }
        
        # Standard ArcGIS Pro installation paths
        self.standard_arcgis_paths = [
            r"C:\Program Files\ArcGIS\Pro",
            r"C:\Program Files (x86)\ArcGIS\Pro", 
            r"C:\ArcGIS\Pro",
            r"D:\Program Files\ArcGIS\Pro",
            r"D:\ArcGIS\Pro"
        ]
        
        # Common conda environment names for ArcGIS Pro
        self.arcgis_env_names = [
            'arcgispro-py3',
            'arcgis',
            'arcgispro',
            'esri-py3'
        ]
    
    def analyze_system_info(self):
        """Analyze system information"""
        print("=== ANALYZING SYSTEM INFORMATION ===")
        
        system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.architecture(),
            'processor': platform.processor(),
            'python_version': sys.version,
            'python_executable': sys.executable,
            'python_path': sys.path[:3]  # First 3 entries for brevity
        }
        
        self.analysis_results['system_info'] = system_info
        
        print(f"Platform: {system_info['platform']} {system_info['platform_release']}")
        print(f"Architecture: {system_info['architecture'][0]}")
        print(f"Python Version: {sys.version.split()[0]}")
        print(f"Python Executable: {sys.executable}")
        
        return system_info
    
    def check_arcpy_availability(self):
        """Check if ArcPy is available in current environment"""
        print("\n=== CHECKING ARCPY AVAILABILITY ===")
        
        arcpy_status = {
            'available': False,
            'import_error': None,
            'version': None,
            'installation_info': None
        }
        
        try:
            import arcpy
            arcpy_status['available'] = True
            
            # Get ArcPy version and installation info
            try:
                arcpy_status['version'] = arcpy.GetInstallInfo()
                print("[SUCCESS] ArcPy is AVAILABLE!")
                print(f"Version: {arcpy_status['version'].get('Version', 'Unknown')}")
                print(f"Product: {arcpy_status['version'].get('ProductName', 'Unknown')}")
                print(f"Install Dir: {arcpy_status['version'].get('InstallDir', 'Unknown')}")
            except Exception as e:
                print("[SUCCESS] ArcPy imported but version info unavailable")
                arcpy_status['version_error'] = str(e)
                
        except ImportError as e:
            arcpy_status['import_error'] = str(e)
            print("[ERROR] ArcPy is NOT AVAILABLE")
            print(f"Import Error: {e}")
        except Exception as e:
            arcpy_status['import_error'] = str(e)
            print(f"[ERROR] ArcPy check failed: {e}")
        
        self.analysis_results['arcpy_status'] = arcpy_status
        return arcpy_status
    
    def scan_arcgis_installations(self):
        """Scan for ArcGIS Pro installations at standard locations"""
        print("\n=== SCANNING FOR ARCGIS PRO INSTALLATIONS ===")
        
        installation_info = {
            'found_installations': [],
            'standard_paths_checked': self.standard_arcgis_paths,
            'registry_check': None
        }
        
        # Check standard installation paths
        for path in self.standard_arcgis_paths:
            if os.path.exists(path):
                installation_info['found_installations'].append({
                    'path': path,
                    'type': 'standard_path',
                    'bin_exists': os.path.exists(os.path.join(path, 'bin')),
                    'python_exists': os.path.exists(os.path.join(path, 'bin', 'Python')),
                    'contents': os.listdir(path) if os.path.exists(path) else []
                })
                print(f"✅ Found ArcGIS installation: {path}")
            else:
                print(f"❌ Not found: {path}")
        
        # Check for ArcGIS Pro executable in PATH
        try:
            result = subprocess.run(['where', 'ArcGISPro.exe'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                exe_path = result.stdout.strip()
                installation_info['found_installations'].append({
                    'path': exe_path,
                    'type': 'path_executable',
                    'note': 'Found ArcGISPro.exe in PATH'
                })
                print(f"✅ Found ArcGIS Pro executable: {exe_path}")
        except Exception as e:
            print(f"Could not check PATH for ArcGISPro.exe: {e}")
        
        # Windows Registry check (if on Windows)
        if platform.system() == 'Windows':
            try:
                import winreg
                registry_paths = [
                    r"SOFTWARE\ESRI\ArcGISPro",
                    r"SOFTWARE\WOW6432Node\ESRI\ArcGISPro"
                ]
                
                for reg_path in registry_paths:
                    try:
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                        install_dir = winreg.QueryValueEx(key, "InstallDir")[0]
                        winreg.CloseKey(key)
                        
                        installation_info['registry_check'] = {
                            'path': install_dir,
                            'registry_key': reg_path
                        }
                        print(f"✅ Registry found ArcGIS Pro: {install_dir}")
                        break
                    except FileNotFoundError:
                        continue
                    except Exception as e:
                        print(f"Registry check error: {e}")
            except ImportError:
                print("Registry check not available (winreg not found)")
        
        self.analysis_results['arcgis_installation'] = installation_info
        return installation_info
    
    def check_conda_environments(self):
        """Check for conda environments with ArcGIS"""
        print("\n=== CHECKING CONDA ENVIRONMENTS ===")
        
        conda_info = {
            'conda_available': False,
            'environments': [],
            'current_env': None,
            'arcgis_environments': []
        }
        
        try:
            # Check if conda is available
            result = subprocess.run(['conda', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                conda_info['conda_available'] = True
                print(f"✅ Conda available: {result.stdout.strip()}")
                
                # List conda environments
                env_result = subprocess.run(['conda', 'env', 'list'], 
                                          capture_output=True, text=True)
                if env_result.returncode == 0:
                    env_lines = env_result.stdout.strip().split('\n')
                    for line in env_lines:
                        if line.startswith('#') or not line.strip():
                            continue
                        parts = line.split()
                        if len(parts) >= 2:
                            env_name = parts[0]
                            env_path = parts[-1]
                            is_current = '*' in line
                            
                            env_info = {
                                'name': env_name,
                                'path': env_path,
                                'is_current': is_current,
                                'is_arcgis': any(arcgis_name in env_name.lower() 
                                               for arcgis_name in self.arcgis_env_names)
                            }
                            
                            conda_info['environments'].append(env_info)
                            
                            if is_current:
                                conda_info['current_env'] = env_info
                                print(f"📍 Current environment: {env_name}")
                            
                            if env_info['is_arcgis']:
                                conda_info['arcgis_environments'].append(env_info)
                                print(f"🗺️ ArcGIS environment found: {env_name}")
                
        except FileNotFoundError:
            print("❌ Conda not found in PATH")
        except Exception as e:
            print(f"❌ Conda check failed: {e}")
        
        self.analysis_results['conda_info'] = conda_info
        return conda_info
    
    def validate_project_template_access(self, template_path):
        """Validate access to the ArcGIS project template"""
        print(f"\n=== VALIDATING PROJECT TEMPLATE ACCESS ===")
        print(f"Template path: {template_path}")
        
        template_info = {
            'path': template_path,
            'exists': False,
            'readable': False,
            'file_info': {},
            'parent_directory': {}
        }
        
        try:
            path_obj = Path(template_path)
            
            # Check if file exists
            template_info['exists'] = path_obj.exists()
            if template_info['exists']:
                print("✅ Project template file EXISTS")
                
                # Check if readable
                template_info['readable'] = os.access(template_path, os.R_OK)
                if template_info['readable']:
                    print("✅ Project template is READABLE")
                else:
                    print("❌ Project template is NOT READABLE")
                
                # Get file info
                stat_info = path_obj.stat()
                template_info['file_info'] = {
                    'size_bytes': stat_info.st_size,
                    'modified_time': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    'created_time': datetime.fromtimestamp(stat_info.st_ctime).isoformat()
                }
                
                print(f"File size: {stat_info.st_size:,} bytes")
                print(f"Last modified: {datetime.fromtimestamp(stat_info.st_mtime)}")
                
            else:
                print("❌ Project template file DOES NOT EXIST")
            
            # Check parent directory
            parent_dir = path_obj.parent
            template_info['parent_directory'] = {
                'exists': parent_dir.exists(),
                'path': str(parent_dir),
                'contents': []
            }
            
            if parent_dir.exists():
                print(f"✅ Parent directory exists: {parent_dir}")
                try:
                    contents = list(parent_dir.iterdir())
                    template_info['parent_directory']['contents'] = [
                        {'name': item.name, 'is_file': item.is_file()} 
                        for item in contents[:10]  # Limit to first 10 items
                    ]
                    print(f"Parent directory contains {len(contents)} items")
                    
                    # Look for .aprx files specifically
                    aprx_files = [item for item in contents if item.suffix.lower() == '.aprx']
                    if aprx_files:
                        print(f"Found {len(aprx_files)} .aprx files in directory:")
                        for aprx_file in aprx_files[:5]:  # Show first 5
                            print(f"  - {aprx_file.name}")
                    
                except Exception as e:
                    print(f"Could not list parent directory contents: {e}")
            else:
                print(f"❌ Parent directory does not exist: {parent_dir}")
        
        except Exception as e:
            print(f"❌ Template validation failed: {e}")
            template_info['error'] = str(e)
        
        self.analysis_results['project_template_access'] = template_info
        return template_info
    
    def test_arcpy_functionality(self, project_path=None):
        """Test basic ArcPy functionality"""
        print(f"\n=== TESTING ARCPY FUNCTIONALITY ===")
        
        test_results = {
            'basic_import': False,
            'get_install_info': False,
            'project_access': False,
            'map_access': False,
            'errors': []
        }
        
        try:
            # Test 1: Basic import
            import arcpy
            test_results['basic_import'] = True
            print("✅ ArcPy import successful")
            
            # Test 2: Get installation info
            try:
                install_info = arcpy.GetInstallInfo()
                test_results['get_install_info'] = True
                print("✅ GetInstallInfo() successful")
                print(f"Product: {install_info.get('ProductName', 'Unknown')}")
                print(f"Version: {install_info.get('Version', 'Unknown')}")
            except Exception as e:
                test_results['errors'].append(f"GetInstallInfo failed: {e}")
                print(f"❌ GetInstallInfo() failed: {e}")
            
            # Test 3: Project access (if project path provided)
            if project_path and os.path.exists(project_path):
                try:
                    project = arcpy.mp.ArcGISProject(project_path)
                    test_results['project_access'] = True
                    print("✅ Project access successful")
                    print(f"Project name: {project.name}")
                    
                    # Test 4: Map access
                    try:
                        maps = project.listMaps()
                        if maps:
                            test_results['map_access'] = True
                            print(f"✅ Map access successful - found {len(maps)} maps")
                            for i, map_obj in enumerate(maps[:3]):  # Show first 3 maps
                                print(f"  Map {i+1}: {map_obj.name}")
                        else:
                            print("⚠️ Project has no maps")
                    except Exception as e:
                        test_results['errors'].append(f"Map access failed: {e}")
                        print(f"❌ Map access failed: {e}")
                    
                except Exception as e:
                    test_results['errors'].append(f"Project access failed: {e}")
                    print(f"❌ Project access failed: {e}")
            else:
                print("⚠️ Project path not provided or doesn't exist - skipping project tests")
                
        except ImportError as e:
            test_results['errors'].append(f"ArcPy import failed: {e}")
            print(f"❌ ArcPy import failed: {e}")
        except Exception as e:
            test_results['errors'].append(f"ArcPy test failed: {e}")
            print(f"❌ ArcPy test failed: {e}")
        
        self.analysis_results['arcpy_functionality_test'] = test_results
        return test_results
    
    def generate_installation_commands(self):
        """Generate installation commands for ArcGIS Pro Python environment"""
        print(f"\n=== ARCGIS PRO INSTALLATION COMMANDS ===")
        
        commands = {
            'conda_arcgis': [],
            'pip_arcgis': [],
            'environment_setup': [],
            'notes': []
        }
        
        # Conda installation commands
        commands['conda_arcgis'] = [
            "# Install ArcGIS API for Python via conda",
            "conda install -c esri arcgis",
            "",
            "# Or create dedicated ArcGIS environment",
            "conda create -n arcgis -c esri arcgis",
            "conda activate arcgis",
            "",
            "# Install additional packages",
            "conda install -c esri arcpy",
            "conda install jupyter notebook pandas numpy"
        ]
        
        # Pip installation commands  
        commands['pip_arcgis'] = [
            "# Install ArcGIS API for Python via pip",
            "pip install arcgis",
            "",
            "# Install additional geospatial packages",
            "pip install geopandas shapely fiona",
            "pip install jupyter notebook pandas numpy"
        ]
        
        # Environment setup
        commands['environment_setup'] = [
            "# Set up ArcGIS Pro Python environment",
            "# 1. Open ArcGIS Pro",
            "# 2. Go to Settings > Python",
            "# 3. Note the Python environment path",
            "# 4. Clone the environment:",
            "",
            "conda create --name arcgis-clone --clone arcgispro-py3",
            "conda activate arcgis-clone",
            "",
            "# Or activate existing ArcGIS Pro environment:",
            "conda activate arcgispro-py3"
        ]
        
        # Important notes
        commands['notes'] = [
            "IMPORTANT NOTES:",
            "1. ArcPy requires ArcGIS Pro or ArcGIS Desktop license",
            "2. ArcPy cannot be installed independently via pip/conda",
            "3. Use ArcGIS Pro's built-in Python environment",
            "4. Clone ArcGIS Pro environment for custom package installation",
            "5. Ensure ArcGIS Pro license is valid and activated"
        ]
        
        # Print commands
        for category, cmd_list in commands.items():
            print(f"\n--- {category.upper().replace('_', ' ')} ---")
            for cmd in cmd_list:
                print(cmd)
        
        self.analysis_results['installation_commands'] = commands
        return commands
    
    def generate_recommendations(self):
        """Generate recommendations based on analysis"""
        print(f"\n=== RECOMMENDATIONS ===")
        
        recommendations = []
        
        # Check ArcPy status
        if not self.analysis_results['arcpy_status']['available']:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'ArcPy Installation',
                'recommendation': 'Install ArcGIS Pro to get ArcPy functionality',
                'action': 'Purchase and install ArcGIS Pro license, then use built-in Python environment'
            })
        
        # Check installations found
        if not self.analysis_results['arcgis_installation']['found_installations']:
            recommendations.append({
                'priority': 'HIGH', 
                'category': 'ArcGIS Installation',
                'recommendation': 'No ArcGIS Pro installation detected',
                'action': 'Install ArcGIS Pro from ESRI'
            })
        
        # Check project template access
        if not self.analysis_results['project_template_access'].get('exists', False):
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Project Template',
                'recommendation': 'Project template file not accessible',
                'action': 'Verify template path or create new ArcGIS Pro project'
            })
        
        # Check conda environments
        conda_info = self.analysis_results.get('conda_info', {})
        if conda_info.get('conda_available') and not conda_info.get('arcgis_environments'):
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Environment Setup',
                'recommendation': 'No ArcGIS conda environments found',
                'action': 'Clone ArcGIS Pro environment or create dedicated ArcGIS environment'
            })
        
        # If ArcPy is available, recommend testing
        if self.analysis_results['arcpy_status']['available']:
            recommendations.append({
                'priority': 'LOW',
                'category': 'Testing',
                'recommendation': 'ArcPy is available - proceed with spatial analysis',
                'action': 'Test ArcPy functionality with SCRPA project template'
            })
        
        # Print recommendations
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. [{rec['priority']}] {rec['category']}")
            print(f"   Recommendation: {rec['recommendation']}")
            print(f"   Action: {rec['action']}")
            print()
        
        self.analysis_results['recommendations'] = recommendations
        return recommendations
    
    def run_complete_analysis(self, project_template_path=None):
        """Run complete ArcPy environment analysis"""
        print("ARCPY ENVIRONMENT ANALYSIS STARTING")
        print("=" * 60)
        
        # Run all analysis steps
        self.analyze_system_info()
        self.check_arcpy_availability()
        self.scan_arcgis_installations()
        self.check_conda_environments()
        
        if project_template_path:
            self.validate_project_template_access(project_template_path)
            self.test_arcpy_functionality(project_template_path)
        else:
            self.test_arcpy_functionality()
        
        self.generate_installation_commands()
        self.generate_recommendations()
        
        print("=" * 60)
        print("ANALYSIS COMPLETE")
        
        return self.analysis_results
    
    def export_analysis_report(self, output_path=None):
        """Export analysis results to JSON file"""
        if output_path is None:
            output_path = f"arcpy_environment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)
            print(f"\nAnalysis report exported to: {output_path}")
            return output_path
        except Exception as e:
            print(f"[ERROR] Failed to export analysis report: {e}")
            return None

def main():
    """Main analysis execution"""
    project_template_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\7_Day_Templet_SCRPA_Time.aprx"
    
    # Initialize analyzer
    analyzer = ArcPyEnvironmentAnalyzer()
    
    # Run complete analysis
    results = analyzer.run_complete_analysis(project_template_path)
    
    # Export report
    report_path = analyzer.export_analysis_report()
    
    return results, report_path

if __name__ == "__main__":
    main()