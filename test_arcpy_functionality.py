#!/usr/bin/env python3
"""
Test ArcPy functionality with ArcGIS Pro Python environment
"""

import sys
import os

def test_arcpy_functionality():
    """Test ArcPy functionality"""
    print('=== ARCGIS PRO PYTHON ENVIRONMENT TEST ===')
    print(f'Python Version: {sys.version.split()[0]}')
    print(f'Python Path: {sys.executable}')
    print()

    try:
        import arcpy
        print('[SUCCESS] ArcPy imported successfully!')
        
        # Get installation info
        install_info = arcpy.GetInstallInfo()
        print(f'Product: {install_info.get("ProductName", "Unknown")}')
        print(f'Version: {install_info.get("Version", "Unknown")}') 
        print(f'Install Dir: {install_info.get("InstallDir", "Unknown")}')
        print(f'License Level: {install_info.get("LicenseLevel", "Unknown")}')
        print()
        
        # Test project access
        project_path = r'C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\7_Day_Templet_SCRPA_Time.aprx'
        print(f'Testing project access: {project_path}')
        
        if os.path.exists(project_path):
            try:
                project = arcpy.mp.ArcGISProject(project_path)
                print('[SUCCESS] Project opened successfully!')
                try:
                    print(f'Project Name: {getattr(project, "name", "Unknown")}')
                    print(f'Project Path: {getattr(project, "filePath", project_path)}')
                except:
                    print(f'Project Path: {project_path}')
                
                # List maps
                maps = project.listMaps()
                print(f'[SUCCESS] Found {len(maps)} maps in project:')
                for i, map_obj in enumerate(maps):
                    print(f'  Map {i+1}: {map_obj.name}')
                    
                    # List layers in first map
                    if i == 0:
                        layers = map_obj.listLayers()
                        print(f'    Layers in {map_obj.name}: {len(layers)}')
                        for j, layer in enumerate(layers[:3]):  # Show first 3 layers
                            print(f'      Layer {j+1}: {layer.name}')
                
                print('[SUCCESS] ArcPy functionality test PASSED!')
                return True
                
            except Exception as e:
                print(f'[ERROR] Project access failed: {e}')
                return False
        else:
            print(f'[ERROR] Project file does not exist: {project_path}')
            return False
            
    except ImportError as e:
        print(f'[ERROR] ArcPy import failed: {e}')
        return False
    except Exception as e:
        print(f'[ERROR] ArcPy test failed: {e}')
        return False

if __name__ == "__main__":
    success = test_arcpy_functionality()
    sys.exit(0 if success else 1)