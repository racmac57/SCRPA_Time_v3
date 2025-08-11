#!/usr/bin/env python3
"""
GeoJSON Optimizer for SCRPA Pipeline
Reduces file sizes and improves loading performance by:
- Reducing coordinate precision
- Removing unnecessary properties
- Compressing data
- Filtering to essential fields only
"""

import json
import gzip
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeoJSONOptimizer:
    """Optimizes GeoJSON files for better performance"""
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.essential_properties = {
            "OBJECTID", "callid", "calltype", "callsource", "fulladdr", 
            "beat", "district", "calldate", "dispatchdate", "enroutedate", 
            "cleardate", "responsetime"
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
    def reduce_coordinate_precision(self, coordinates: List[float], precision: int = 6) -> List[float]:
        """Reduce coordinate precision to save space"""
        return [round(coord, precision) for coord in coordinates]
    
    def filter_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Keep only essential properties"""
        return {k: v for k, v in properties.items() if k in self.essential_properties}
    
    def optimize_feature(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize a single feature"""
        # Reduce coordinate precision
        if 'geometry' in feature and 'coordinates' in feature['geometry']:
            coords = feature['geometry']['coordinates']
            if isinstance(coords[0], list):  # Point coordinates
                feature['geometry']['coordinates'] = self.reduce_coordinate_precision(coords)
        
        # Filter properties
        if 'properties' in feature:
            feature['properties'] = self.filter_properties(feature['properties'])
        
        return feature
    
    def optimize_geojson(self, input_file: str, output_file: str, compress: bool = True) -> Dict[str, Any]:
        """Optimize a GeoJSON file"""
        logger.info(f"Optimizing {input_file}")
        
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Optimize features
        if 'features' in data:
            data['features'] = [self.optimize_feature(feature) for feature in data['features']]
        
        # Write optimized file
        if compress:
            output_file = output_file.replace('.geojson', '.geojson.gz')
            with gzip.open(output_file, 'wt', encoding='utf-8') as f:
                json.dump(data, f, separators=(',', ':'))
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, separators=(',', ':'))
        
        # Calculate size reduction
        original_size = os.path.getsize(input_file)
        optimized_size = os.path.getsize(output_file)
        reduction = ((original_size - optimized_size) / original_size) * 100
        
        stats = {
            'original_size_mb': round(original_size / (1024 * 1024), 2),
            'optimized_size_mb': round(optimized_size / (1024 * 1024), 2),
            'reduction_percent': round(reduction, 2),
            'feature_count': len(data.get('features', []))
        }
        
        logger.info(f"Optimization complete: {stats['original_size_mb']}MB → {stats['optimized_size_mb']}MB ({stats['reduction_percent']}% reduction)")
        
        return stats
    
    def batch_optimize(self, compress: bool = True) -> Dict[str, Any]:
        """Optimize all GeoJSON files in the input directory"""
        results = {}
        
        for filename in os.listdir(self.input_dir):
            if filename.endswith('.geojson'):
                input_path = os.path.join(self.input_dir, filename)
                output_path = os.path.join(self.output_dir, filename)
                
                try:
                    stats = self.optimize_geojson(input_path, output_path, compress)
                    results[filename] = stats
                except Exception as e:
                    logger.error(f"Error optimizing {filename}: {e}")
                    results[filename] = {'error': str(e)}
        
        return results

def create_optimized_m_code_template():
    """Create optimized M code template for compressed GeoJSON files"""
    template = '''
// 🕒 Optimized GeoJSON Query Template
// Use this template for compressed .geojson.gz files

let
    // ─── 1) Load compressed GeoJSON ───────────────────────────────────────────
    Source = Json.Document(
        Binary.Decompress(
            File.Contents("PATH_TO_COMPRESSED_FILE.geojson.gz"),
            Compression.GZip
        )
    ),

    // ─── 2) Expand features list ──────────────────────────────────────────────
    RootTable    = Table.FromRecords({ Source }),
    Features     = Table.ExpandListColumn(RootTable, "features"),
    ExpandedFeat = Table.ExpandRecordColumn(Features, "features", {"geometry","properties"}, {"Geometry","Properties"}),

    // ─── 3) Extract coordinates (already optimized) ───────────────────────────
    ExpandedGeom     = Table.ExpandRecordColumn(ExpandedFeat, "Geometry", {"coordinates"}, {"Coordinates"}),
    AddWebMercatorX  = Table.AddColumn(ExpandedGeom, "WebMercator_X", each try [Coordinates]{0} otherwise null, type number),
    AddWebMercatorY  = Table.AddColumn(AddWebMercatorX, "WebMercator_Y", each try [Coordinates]{1} otherwise null, type number),

    // ─── 4) Expand only essential properties (already filtered) ───────────────
    ExpandedProps = Table.ExpandRecordColumn(
        AddWebMercatorY,
        "Properties",
        {
            "OBJECTID","callid","calltype","callsource","fulladdr","beat","district",
            "calldate","dispatchdate","enroutedate","cleardate","responsetime"
        },
        {
            "objectid","callid","calltype","callsource","fulladdr","beat","district",
            "calldate","dispatchdate","enroutedate","cleardate","responsetime"
        }
    ),

    // ─── 5) Continue with your existing transformations ───────────────────────
    // ... rest of your M code ...
in
    Final
'''
    return template

def main():
    parser = argparse.ArgumentParser(description='Optimize GeoJSON files for better performance')
    parser.add_argument('--input-dir', required=True, help='Input directory containing GeoJSON files')
    parser.add_argument('--output-dir', required=True, help='Output directory for optimized files')
    parser.add_argument('--compress', action='store_true', help='Compress output files with gzip')
    parser.add_argument('--create-template', action='store_true', help='Create optimized M code template')
    
    args = parser.parse_args()
    
    # Create optimizer
    optimizer = GeoJSONOptimizer(args.input_dir, args.output_dir)
    
    # Optimize files
    results = optimizer.batch_optimize(args.compress)
    
    # Print summary
    print("\n" + "="*60)
    print("GEOJSON OPTIMIZATION SUMMARY")
    print("="*60)
    
    total_original = 0
    total_optimized = 0
    
    for filename, stats in results.items():
        if 'error' not in stats:
            print(f"{filename}:")
            print(f"  Original: {stats['original_size_mb']}MB")
            print(f"  Optimized: {stats['optimized_size_mb']}MB")
            print(f"  Reduction: {stats['reduction_percent']}%")
            print(f"  Features: {stats['feature_count']}")
            print()
            
            total_original += stats['original_size_mb']
            total_optimized += stats['optimized_size_mb']
        else:
            print(f"{filename}: ERROR - {stats['error']}")
    
    if total_original > 0:
        total_reduction = ((total_original - total_optimized) / total_original) * 100
        print(f"TOTAL: {total_original}MB → {total_optimized}MB ({total_reduction:.1f}% reduction)")
    
    # Create template if requested
    if args.create_template:
        template = create_optimized_m_code_template()
        template_file = os.path.join(args.output_dir, 'optimized_m_code_template.m')
        with open(template_file, 'w') as f:
            f.write(template)
        print(f"\nM code template created: {template_file}")

if __name__ == "__main__":
    main() 