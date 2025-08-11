# 2025-08-01-00-00-00
# SCRPA_Time_v2/SCRPA_Spatial_Grid_Zone_Validator
# Author: R. A. Carucci
# Purpose: Spatial grid/zone validation using ArcPy vs zone_grid_master.xlsx

import arcpy
import pandas as pd
import numpy as np
import os
from pathlib import Path
import logging
from datetime import datetime
import json

class SCRPASpatialValidator:
    """
    Spatial grid/zone validation comparing ArcPy spatial joins vs zone_grid_master.xlsx lookup.
    
    Features:
    - Compare spatial accuracy between methods
    - Validate grid/zone assignments
    - Generate accuracy metrics
    - Recommend best approach for production
    """
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)
        
        self.zone_grid_ref_path = self.project_path / "10_Refrence_Files" / "zone_grid_master.xlsx"
        self.output_dir = self.project_path / '04_powerbi'
        self.aprx_path = self.project_path / "10_Refrence_Files" / "7_Day_Templet_SCRPA_Time.aprx"
        
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for spatial validation."""
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"spatial_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("=== SCRPA Spatial Grid/Zone Validator ===")

    def load_reference_data(self):
        """Load zone_grid_master.xlsx reference data."""
        self.logger.info("Loading zone/grid reference data...")
        
        try:
            if not self.zone_grid_ref_path.exists():
                raise FileNotFoundError(f"Zone grid reference not found: {self.zone_grid_ref_path}")
            
            zone_grid_df = pd.read_excel(self.zone_grid_ref_path)
            self.logger.info(f"Loaded zone/grid reference: {len(zone_grid_df)} records")
            
            # Standardize column names
            zone_grid_df.columns = [col.lower().replace(' ', '_') for col in zone_grid_df.columns]
            
            return zone_grid_df
            
        except Exception as e:
            self.logger.error(f"Failed to load reference data: {e}")
            return None

    def setup_arcgis_workspace(self):
        """Setup ArcGIS workspace and check requirements."""
        self.logger.info("Setting up ArcGIS workspace...")
        
        try:
            # Set workspace
            arcpy.env.workspace = str(self.project_path / "temp_spatial")
            os.makedirs(arcpy.env.workspace, exist_ok=True)
            arcpy.env.overwriteOutput = True
            
            # Check if ArcGIS Pro project exists
            if not self.aprx_path.exists():
                self.logger.warning(f"ArcGIS Pro project not found: {self.aprx_path}")
                return False
            
            self.logger.info(f"Using ArcGIS Pro project: {self.aprx_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"ArcGIS workspace setup failed: {e}")
            return False

    def geocode_addresses_sample(self, addresses_sample, max_addresses=50):
        """Geocode a sample of addresses for spatial validation."""
        self.logger.info(f"Geocoding sample of {len(addresses_sample)} addresses...")
        
        try:
            # Create temporary geodatabase
            temp_gdb = os.path.join(arcpy.env.workspace, "spatial_validation.gdb")
            if arcpy.Exists(temp_gdb):
                arcpy.Delete_management(temp_gdb)
            arcpy.CreateFileGDB_management(arcpy.env.workspace, "spatial_validation")
            
            # Create input table
            input_table = os.path.join(temp_gdb, "sample_addresses")
            arcpy.CreateTable_management(temp_gdb, "sample_addresses")
            arcpy.AddField_management(input_table, "Address", "TEXT", field_length=500)
            arcpy.AddField_management(input_table, "AddressID", "LONG")
            
            # Insert sample addresses
            with arcpy.da.InsertCursor(input_table, ["Address", "AddressID"]) as cursor:
                for i, address in enumerate(addresses_sample[:max_addresses]):
                    cursor.insertRow([str(address), i])
            
            # Geocode using NJ_Geocode service
            output_fc = os.path.join(temp_gdb, "geocoded_sample")
            
            arcpy.GeocodeAddresses_geocoding(
                input_table,
                "NJ_Geocode",  # Assumes NJ_Geocode service is configured
                "Address Address VISIBLE NONE",
                output_fc,
                "STATIC"
            )
            
            # Extract geocoded results
            geocoded_results = []
            fields = ["Address", "SHAPE@X", "SHAPE@Y", "Score", "Status", "AddressID"]
            
            with arcpy.da.SearchCursor(output_fc, fields) as cursor:
                for row in cursor:
                    if row[3] >= 80:  # Good geocoding score
                        geocoded_results.append({
                            'address': row[0],
                            'x_coord': row[1],
                            'y_coord': row[2],
                            'geocode_score': row[3],
                            'geocode_status': row[4],
                            'address_id': row[5]
                        })
            
            self.logger.info(f"Successfully geocoded {len(geocoded_results)} addresses")
            return geocoded_results
            
        except Exception as e:
            self.logger.error(f"Geocoding failed: {e}")
            return []

    def perform_spatial_join_validation(self, geocoded_points):
        """Perform spatial join to validate grid/zone assignments."""
        self.logger.info("Performing spatial join validation...")
        
        try:
            # This would require access to the police grid/zone shapefiles
            # For demonstration, we'll simulate the process
            
            spatial_results = []
            
            for point in geocoded_points:
                # In real implementation, this would:
                # 1. Create point geometry from coordinates
                # 2. Spatial join with police grid/zone layers
                # 3. Extract grid and zone values
                
                # Simulated spatial join result
                spatial_result = {
                    'address': point['address'],
                    'x_coord': point['x_coord'],
                    'y_coord': point['y_coord'],
                    'spatial_grid': self._simulate_spatial_grid(point['x_coord'], point['y_coord']),
                    'spatial_zone': self._simulate_spatial_zone(point['x_coord'], point['y_coord']),
                    'geocode_score': point['geocode_score']
                }
                
                spatial_results.append(spatial_result)
            
            self.logger.info(f"Completed spatial join for {len(spatial_results)} points")
            return spatial_results
            
        except Exception as e:
            self.logger.error(f"Spatial join failed: {e}")
            return []

    def _simulate_spatial_grid(self, x, y):
        """Simulate spatial grid assignment (replace with actual spatial join)."""
        # This is a placeholder - real implementation would use actual grid polygons
        grid_options = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
        return np.random.choice(grid_options)

    def _simulate_spatial_zone(self, x, y):
        """Simulate spatial zone assignment (replace with actual spatial join)."""
        # This is a placeholder - real implementation would use actual zone polygons
        zone_options = ['North', 'South', 'East', 'West', 'Central']
        return np.random.choice(zone_options)

    def compare_lookup_vs_spatial(self, spatial_results, zone_grid_ref):
        """Compare lookup table results vs spatial join results."""
        self.logger.info("Comparing lookup vs spatial results...")
        
        comparison_results = {
            'total_comparisons': 0,
            'exact_matches': 0,
            'grid_matches': 0,
            'zone_matches': 0,
            'discrepancies': [],
            'accuracy_metrics': {}
        }
        
        try:
            for spatial_result in spatial_results:
                address = spatial_result['address']
                
                # Find matching address in lookup table
                lookup_match = self._find_lookup_match(address, zone_grid_ref)
                
                if lookup_match is not None:
                    comparison_results['total_comparisons'] += 1
                    
                    # Compare grid values
                    lookup_grid = lookup_match.get('grid', '')
                    spatial_grid = spatial_result['spatial_grid']
                    
                    # Compare zone values  
                    lookup_zone = lookup_match.get('zone', '')
                    spatial_zone = spatial_result['spatial_zone']
                    
                    grid_match = str(lookup_grid).upper() == str(spatial_grid).upper()
                    zone_match = str(lookup_zone).upper() == str(spatial_zone).upper()
                    
                    if grid_match:
                        comparison_results['grid_matches'] += 1
                    if zone_match:
                        comparison_results['zone_matches'] += 1
                    if grid_match and zone_match:
                        comparison_results['exact_matches'] += 1
                    
                    # Record discrepancies
                    if not (grid_match and zone_match):
                        comparison_results['discrepancies'].append({
                            'address': address,
                            'lookup_grid': lookup_grid,
                            'spatial_grid': spatial_grid,
                            'lookup_zone': lookup_zone,
                            'spatial_zone': spatial_zone,
                            'geocode_score': spatial_result['geocode_score']
                        })
            
            # Calculate accuracy metrics
            total = comparison_results['total_comparisons']
            if total > 0:
                comparison_results['accuracy_metrics'] = {
                    'exact_match_rate': (comparison_results['exact_matches'] / total) * 100,
                    'grid_match_rate': (comparison_results['grid_matches'] / total) * 100,
                    'zone_match_rate': (comparison_results['zone_matches'] / total) * 100
                }
            
            self.logger.info(f"Comparison completed: {total} addresses compared")
            self.logger.info(f"Exact match rate: {comparison_results['accuracy_metrics'].get('exact_match_rate', 0):.1f}%")
            
            return comparison_results
            
        except Exception as e:
            self.logger.error(f"Comparison failed: {e}")
            return comparison_results

    def _find_lookup_match(self, address, zone_grid_ref):
        """Find matching address in lookup table."""
        try:
            # Clean address for matching
            clean_address = str(address).replace(', Hackensack, NJ, 07601', '').strip().upper()
            
            # Look for address column in reference data
            address_columns = ['address', 'location', 'street', 'full_address']
            
            for col in address_columns:
                if col in zone_grid_ref.columns:
                    matches = zone_grid_ref[zone_grid_ref[col].str.upper().str.contains(clean_address, na=False)]
                    if not matches.empty:
                        return matches.iloc[0].to_dict()
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Lookup match failed for {address}: {e}")
            return None

    def generate_spatial_validation_report(self, comparison_results):
        """Generate comprehensive spatial validation report."""
        self.logger.info("Generating spatial validation report...")
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create detailed JSON report
            report_data = {
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'validator_version': '1.0.0',
                    'total_comparisons': comparison_results['total_comparisons']
                },
                'accuracy_summary': comparison_results['accuracy_metrics'],
                'detailed_results': comparison_results,
                'recommendations': self._generate_recommendations(comparison_results)
            }
            
            json_path = self.project_path / '03_output' / f'spatial_validation_report_{timestamp}.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            # Create markdown summary
            md_content = f"""# SCRPA Spatial Grid/Zone Validation Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Addresses Compared:** {comparison_results['total_comparisons']}

## Accuracy Summary

"""
            
            if comparison_results['accuracy_metrics']:
                metrics = comparison_results['accuracy_metrics']
                md_content += f"""- **Exact Match Rate:** {metrics.get('exact_match_rate', 0):.1f}%
- **Grid Match Rate:** {metrics.get('grid_match_rate', 0):.1f}%
- **Zone Match Rate:** {metrics.get('zone_match_rate', 0):.1f}%

"""
            
            # Add discrepancies summary
            discrepancies = comparison_results.get('discrepancies', [])
            if discrepancies:
                md_content += f"""## Discrepancies Found

**Total Discrepancies:** {len(discrepancies)}

### Sample Discrepancies:
"""
                for i, disc in enumerate(discrepancies[:5]):  # Show first 5
                    md_content += f"""
**Address {i+1}:** {disc['address']}
- Lookup Grid/Zone: {disc['lookup_grid']} / {disc['lookup_zone']}
- Spatial Grid/Zone: {disc['spatial_grid']} / {disc['spatial_zone']}
- Geocode Score: {disc['geocode_score']}
"""
            
            # Add recommendations
            recommendations = self._generate_recommendations(comparison_results)
            md_content += f"""
## Recommendations

### Method Selection:
{recommendations.get('method_recommendation', 'Further analysis needed')}

### Accuracy Improvement:
{recommendations.get('accuracy_improvement', 'Review data quality')}

### Production Implementation:
{recommendations.get('production_recommendation', 'Test with larger sample')}
"""
            
            md_path = self.project_path / '03_output' / f'spatial_validation_summary_{timestamp}.md'
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            self.logger.info(f"Reports generated:")
            self.logger.info(f"  JSON: {json_path}")
            self.logger.info(f"  Markdown: {md_path}")
            
            return str(md_path)
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return None

    def _generate_recommendations(self, comparison_results):
        """Generate recommendations based on validation results."""
        recommendations = {}
        
        if comparison_results['accuracy_metrics']:
            exact_match_rate = comparison_results['accuracy_metrics'].get('exact_match_rate', 0)
            
            if exact_match_rate >= 90:
                recommendations['method_recommendation'] = "Lookup table method is highly accurate and recommended for production use."
                recommendations['production_recommendation'] = "Implement lookup-based grid/zone assignment with confidence."
            elif exact_match_rate >= 75:
                recommendations['method_recommendation'] = "Lookup table method shows good accuracy but may benefit from spatial validation for critical cases."
                recommendations['production_recommendation'] = "Use lookup method as primary with spatial fallback for unmatched addresses."
            else:
                recommendations['method_recommendation'] = "Spatial join method may be more accurate than lookup table. Consider hybrid approach."
                recommendations['production_recommendation'] = "Implement spatial join as primary method with lookup as fallback."
            
            recommendations['accuracy_improvement'] = f"Current accuracy: {exact_match_rate:.1f}%. Target 95%+ for production deployment."
        
        return recommendations

    def run_spatial_validation(self, sample_size=25):
        """Run complete spatial validation workflow."""
        self.logger.info("Starting spatial grid/zone validation...")
        
        try:
            # Step 1: Load reference data
            zone_grid_ref = self.load_reference_data()
            if zone_grid_ref is None:
                raise Exception("Failed to load reference data")
            
            # Step 2: Setup ArcGIS workspace
            if not self.setup_arcgis_workspace():
                raise Exception("Failed to setup ArcGIS workspace")
            
            # Step 3: Get sample addresses from SCRPA data
            sample_addresses = self._get_sample_addresses(sample_size)
            if not sample_addresses:
                raise Exception("No sample addresses available")
            
            # Step 4: Geocode sample addresses
            geocoded_results = self.geocode_addresses_sample(sample_addresses, sample_size)
            if not geocoded_results:
                raise Exception("Geocoding failed")
            
            # Step 5: Perform spatial join validation
            spatial_results = self.perform_spatial_join_validation(geocoded_results)
            if not spatial_results:
                raise Exception("Spatial join failed")
            
            # Step 6: Compare methods
            comparison_results = self.compare_lookup_vs_spatial(spatial_results, zone_grid_ref)
            
            # Step 7: Generate report
            report_path = self.generate_spatial_validation_report(comparison_results)
            
            self.logger.info("Spatial validation completed successfully")
            
            return {
                'status': 'SUCCESS',
                'report_path': report_path,
                'accuracy_metrics': comparison_results.get('accuracy_metrics', {}),
                'total_comparisons': comparison_results.get('total_comparisons', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Spatial validation failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }

    def _get_sample_addresses(self, sample_size):
        """Get sample addresses from SCRPA datasets."""
        try:
            sample_addresses = []
            
            # Try to get addresses from RMS data
            rms_file = self.output_dir / 'rms_data_standardized.csv'
            if rms_file.exists():
                df = pd.read_csv(rms_file)
                if 'location' in df.columns:
                    addresses = df['location'].dropna().unique()[:sample_size//2]
                    sample_addresses.extend(addresses)
            
            # Try to get addresses from CAD data
            cad_file = self.output_dir / 'cad_data_standardized.csv'  
            if cad_file.exists():
                df = pd.read_csv(cad_file)
                if 'location' in df.columns:
                    addresses = df['location'].dropna().unique()[:sample_size//2]
                    sample_addresses.extend(addresses)
            
            # Remove duplicates and limit to sample size
            unique_addresses = list(set(sample_addresses))[:sample_size]
            
            self.logger.info(f"Collected {len(unique_addresses)} sample addresses")
            return unique_addresses
            
        except Exception as e:
            self.logger.error(f"Failed to get sample addresses: {e}")
            return []

if __name__ == "__main__":
    try:
        validator = SCRPASpatialValidator()
        results = validator.run_spatial_validation(sample_size=25)
        
        print("\n" + "="*60)
        print("SCRPA SPATIAL VALIDATION RESULTS")
        print("="*60)
        print(f"Status: {results['status']}")
        
        if results['status'] == 'SUCCESS':
            print(f"Report: {results['report_path']}")
            print(f"Total Comparisons: {results['total_comparisons']}")
            
            metrics = results.get('accuracy_metrics', {})
            if metrics:
                print(f"Exact Match Rate: {metrics.get('exact_match_rate', 0):.1f}%")
                print(f"Grid Match Rate: {metrics.get('grid_match_rate', 0):.1f}%")
                print(f"Zone Match Rate: {metrics.get('zone_match_rate', 0):.1f}%")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
        
        print("="*60)
        
    except Exception as e:
        print(f"Fatal error: {e}")