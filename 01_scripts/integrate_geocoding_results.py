# SCRPA Geocoding Results Integration Script
# Run this after ArcGIS Pro geocoding is complete

import pandas as pd
from pathlib import Path

def integrate_geocoding_results():
    """Integrate geocoding results with SCRPA datasets."""
    
    # Paths
    project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
    output_dir = project_path / "04_powerbi"
    geocoding_dir = project_path / "geocoding_input"
    
    # Load geocoding results
    geocoding_results_file = geocoding_dir / "geocoding_results.csv"
    
    if not geocoding_results_file.exists():
        print("❌ Geocoding results file not found!")
        print(f"Expected: {geocoding_results_file}")
        return False
    
    # Read geocoding results
    geocoding_df = pd.read_csv(geocoding_results_file)
    print(f"📍 Loaded {len(geocoding_df)} geocoding results")
    
    # Create address lookup
    lookup = {}
    for _, row in geocoding_df.iterrows():
        address = row.get('Address', '')
        lookup[address] = {
            'x_coord': row.get('X', None),
            'y_coord': row.get('Y', None),
            'geocode_score': row.get('Score', 0),
            'geocode_status': row.get('Status', 'UNKNOWN'),
            'match_address': row.get('Match_addr', '')
        }
    
    # Integrate with each dataset
    datasets = [
        'cad_data_standardized_spatial_ready.csv',
        'rms_data_standardized_spatial_ready.csv',
        'cad_rms_matched_standardized_spatial_ready.csv'
    ]
    
    enhanced_datasets = []
    
    for dataset_file in datasets:
        file_path = output_dir / dataset_file
        
        if file_path.exists():
            print(f"🔄 Processing {dataset_file}...")
            
            df = pd.read_csv(file_path)
            original_count = len(df)
            
            # Match addresses and populate coordinates
            matched_count = 0
            
            if 'location' in df.columns:
                for idx, address in df['location'].items():
                    if pd.notna(address) and str(address) in lookup:
                        result = lookup[str(address)]
                        
                        df.at[idx, 'x_coord'] = result['x_coord']
                        df.at[idx, 'y_coord'] = result['y_coord']
                        df.at[idx, 'geocode_score'] = result['geocode_score']
                        df.at[idx, 'geocode_status'] = result['geocode_status']
                        df.at[idx, 'match_address'] = result['match_address']
                        
                        matched_count += 1
            
            # Save enhanced dataset
            enhanced_file = output_dir / dataset_file.replace('_spatial_ready.csv', '_with_coordinates.csv')
            df.to_csv(enhanced_file, index=False)
            
            geocoded_count = df['x_coord'].notna().sum()
            enhancement_rate = (geocoded_count / original_count) * 100 if original_count > 0 else 0
            
            print(f"  ✅ {dataset_file}: {geocoded_count}/{original_count} geocoded ({enhancement_rate:.1f}%)")
            print(f"  📄 Output: {enhanced_file.name}")
            
            enhanced_datasets.append({
                'original': dataset_file,
                'enhanced': enhanced_file.name,
                'records': original_count,
                'geocoded': int(geocoded_count),
                'rate': enhancement_rate
            })
        
        else:
            print(f"⚠️ Dataset not found: {dataset_file}")
    
    # Summary
    print("\n" + "="*60)
    print("GEOCODING INTEGRATION COMPLETE")
    print("="*60)
    
    for dataset in enhanced_datasets:
        print(f"✅ {dataset['enhanced']}: {dataset['geocoded']}/{dataset['records']} ({dataset['rate']:.1f}%)")
    
    total_records = sum(d['records'] for d in enhanced_datasets)
    total_geocoded = sum(d['geocoded'] for d in enhanced_datasets)
    overall_rate = (total_geocoded / total_records) * 100 if total_records > 0 else 0
    
    print(f"\n📊 Overall: {total_geocoded}/{total_records} geocoded ({overall_rate:.1f}%)")
    print("="*60)
    
    return True

if __name__ == "__main__":
    integrate_geocoding_results()
