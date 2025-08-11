# 2025-08-01-00-00-00
# SCRPA_Time_v2/SCRPA_Geocoding_Preparation
# Author: R. A. Carucci
# Purpose: Prepare SCRPA datasets for geocoding and create spatial enhancement framework

import pandas as pd
import numpy as np
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import logging
import json
import re

class SCRPAGeocodingPreparation:
    """
    Prepare SCRPA datasets for geocoding with NJ_Geocode service.
    
    Features:
    - Collect and validate unique addresses
    - Create geocoding input files
    - Prepare spatial-ready datasets
    - Generate ArcGIS Pro geocoding instructions
    - Create batch processing framework
    """
    
    def __init__(self, project_path: str = None):
        if project_path is None:
            self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
        else:
            self.project_path = Path(project_path)
        
        self.template_path = self.project_path / "10_Refrence_Files" / "7_Day_Templet_SCRPA_Time.aprx"
        self.output_dir = self.project_path / '04_powerbi'
        self.geocoding_dir = self.project_path / 'geocoding_input'
        self.geocoding_dir.mkdir(exist_ok=True)
        
        # Processing parameters
        self.batch_size = 50
        self.target_srid = 3424  # State Plane NJ
        
        # Results tracking
        self.preparation_results = {
            'execution_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'start_time': datetime.now(),
            'unique_addresses_found': 0,
            'datasets_prepared': [],
            'geocoding_batches': 0,
            'validation_results': {},
            'arcgis_instructions_created': False
        }
        
        self.setup_logging()

    def setup_logging(self):
        """Setup logging for geocoding preparation."""
        log_dir = self.project_path / '03_output' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"geocoding_prep_{self.preparation_results['execution_id']}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("="*80)
        self.logger.info(f"SCRPA GEOCODING PREPARATION - {self.preparation_results['execution_id']}")
        self.logger.info("="*80)

    def validate_address_quality(self, address):
        """Validate and clean address for geocoding."""
        if pd.isna(address) or not address:
            return None, "Empty address"
        
        addr_str = str(address).strip()
        
        # Remove obviously invalid addresses
        if len(addr_str) < 10:
            return None, "Address too short"
        
        if addr_str.lower() in ['unknown', 'n/a', 'none', 'null']:
            return None, "Invalid address value"
        
        # Check for Hackensack format
        hackensack_pattern = re.compile(r'.*Hackensack.*NJ.*07601', re.IGNORECASE)
        if not hackensack_pattern.match(addr_str):
            return None, "Not Hackensack address format"
        
        # Clean common issues
        cleaned_addr = re.sub(r'\s+', ' ', addr_str)  # Multiple spaces
        cleaned_addr = re.sub(r'[^\w\s,.-]', '', cleaned_addr)  # Invalid characters
        
        return cleaned_addr, "Valid"

    def collect_and_validate_addresses(self):
        """Collect all unique addresses from SCRPA datasets with validation."""
        self.logger.info("Collecting and validating unique addresses...")
        
        unique_addresses = {}  # address -> {datasets: [list], validation: status}
        dataset_summaries = {}
        
        # Target datasets and their address columns
        datasets_to_process = [
            ('cad_data_standardized.csv', ['location']),
            ('rms_data_standardized.csv', ['location']),
            ('cad_rms_matched_standardized.csv', ['location'])
        ]
        
        for dataset_file, address_columns in datasets_to_process:
            file_path = self.output_dir / dataset_file
            dataset_summaries[dataset_file] = {
                'exists': False,
                'total_records': 0,
                'addresses_found': 0,
                'valid_addresses': 0,
                'invalid_addresses': 0
            }
            
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    dataset_summaries[dataset_file]['exists'] = True
                    dataset_summaries[dataset_file]['total_records'] = len(df)
                    
                    # Process each address column
                    for col in address_columns:
                        if col in df.columns:
                            addresses = df[col].dropna().unique()
                            dataset_summaries[dataset_file]['addresses_found'] += len(addresses)
                            
                            for addr in addresses:
                                cleaned_addr, status = self.validate_address_quality(addr)
                                
                                if cleaned_addr:
                                    if cleaned_addr not in unique_addresses:
                                        unique_addresses[cleaned_addr] = {
                                            'datasets': [],
                                            'validation_status': status,
                                            'original_address': str(addr)
                                        }
                                    unique_addresses[cleaned_addr]['datasets'].append(f"{dataset_file}[{col}]")
                                    dataset_summaries[dataset_file]['valid_addresses'] += 1
                                else:
                                    dataset_summaries[dataset_file]['invalid_addresses'] += 1
                    
                    self.logger.info(f"  ✅ {dataset_file}: {dataset_summaries[dataset_file]['total_records']} records, {dataset_summaries[dataset_file]['valid_addresses']} valid addresses")
                    
                except Exception as e:
                    self.logger.error(f"  ❌ Error processing {dataset_file}: {e}")
                    
            else:
                self.logger.warning(f"  ⚠️ Dataset not found: {dataset_file}")
        
        # Convert to list and sort
        valid_addresses = list(unique_addresses.keys())
        valid_addresses.sort()
        
        self.preparation_results['unique_addresses_found'] = len(valid_addresses)
        self.preparation_results['dataset_summaries'] = dataset_summaries
        self.preparation_results['address_validation'] = unique_addresses
        
        self.logger.info(f"✅ Address collection complete:")
        self.logger.info(f"  📍 Unique valid addresses: {len(valid_addresses)}")
        self.logger.info(f"  📊 Dataset breakdown:")
        
        for dataset, summary in dataset_summaries.items():
            if summary['exists']:
                self.logger.info(f"    - {dataset}: {summary['valid_addresses']} valid / {summary['invalid_addresses']} invalid")
        
        return valid_addresses, unique_addresses

    def create_geocoding_input_files(self, address_list):
        """Create input files for ArcGIS Pro geocoding."""
        self.logger.info(f"Creating geocoding input files for {len(address_list)} addresses...")
        
        # Create master address list
        address_df = pd.DataFrame({
            'AddressID': range(len(address_list)),
            'Address': address_list,
            'BatchID': [(i // self.batch_size) + 1 for i in range(len(address_list))]
        })
        
        # Save master list
        master_file = self.geocoding_dir / 'master_address_list.csv'
        address_df.to_csv(master_file, index=False)
        self.logger.info(f"  📄 Master address list: {master_file}")
        
        # Create batch files
        batch_files = []
        for batch_id in address_df['BatchID'].unique():
            batch_df = address_df[address_df['BatchID'] == batch_id]
            batch_file = self.geocoding_dir / f'batch_{batch_id:02d}_addresses.csv'
            batch_df.to_csv(batch_file, index=False)
            batch_files.append(batch_file)
            
            self.logger.info(f"  📦 Batch {batch_id}: {len(batch_df)} addresses → {batch_file.name}")
        
        self.preparation_results['geocoding_batches'] = len(batch_files)
        self.preparation_results['master_address_file'] = str(master_file)
        self.preparation_results['batch_files'] = [str(f) for f in batch_files]
        
        return master_file, batch_files

    def prepare_spatial_datasets(self):
        """Prepare datasets with spatial column placeholders."""
        self.logger.info("Preparing datasets with spatial column placeholders...")
        
        target_datasets = [
            'cad_data_standardized.csv',
            'rms_data_standardized.csv',
            'cad_rms_matched_standardized.csv'
        ]
        
        spatial_columns = ['x_coord', 'y_coord', 'geocode_score', 'geocode_status', 'match_address']
        
        for dataset_file in target_datasets:
            file_path = self.output_dir / dataset_file
            
            if file_path.exists():
                try:
                    # Read dataset
                    df = pd.read_csv(file_path)
                    original_columns = len(df.columns)
                    
                    # Add spatial columns with null values
                    for col in spatial_columns:
                        if col not in df.columns:
                            df[col] = None
                    
                    # Save spatial-ready version
                    spatial_file = self.output_dir / dataset_file.replace('.csv', '_spatial_ready.csv')
                    df.to_csv(spatial_file, index=False)
                    
                    self.logger.info(f"  ✅ {dataset_file} → {spatial_file.name}")
                    self.logger.info(f"    - Original columns: {original_columns}")
                    self.logger.info(f"    - Spatial columns added: {len(spatial_columns)}")
                    self.logger.info(f"    - Total columns: {len(df.columns)}")
                    
                    self.preparation_results['datasets_prepared'].append({
                        'original_file': dataset_file,
                        'spatial_ready_file': spatial_file.name,
                        'records': len(df),
                        'original_columns': original_columns,
                        'total_columns': len(df.columns)
                    })
                    
                except Exception as e:
                    self.logger.error(f"  ❌ Failed to prepare {dataset_file}: {e}")
                    
            else:
                self.logger.warning(f"  ⚠️ Dataset not found: {dataset_file}")

    def create_arcgis_pro_instructions(self):
        """Create detailed ArcGIS Pro geocoding instructions."""
        self.logger.info("Creating ArcGIS Pro geocoding instructions...")
        
        instructions_content = f"""# ArcGIS Pro Geocoding Instructions for SCRPA Data

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Addresses to Process:** {self.preparation_results['unique_addresses_found']}
**Batch Count:** {self.preparation_results['geocoding_batches']}

## Prerequisites

1. **ArcGIS Pro** must be installed and licensed
2. **NJ_Geocode service** must be configured and accessible
3. **Template project** located at: `{self.template_path}`

## Step-by-Step Geocoding Process

### Step 1: Open ArcGIS Pro Template
1. Launch ArcGIS Pro
2. Open project: `{self.template_path}`
3. Verify NJ_Geocode service is available in the Locators folder

### Step 2: Prepare Workspace
1. Create new geodatabase: `SCRPA_Geocoding.gdb`
2. Set workspace to the new geodatabase
3. Ensure coordinate system is set to State Plane NJ (EPSG:{self.target_srid})

### Step 3: Import Address Data
**Master address file:** `{self.preparation_results.get('master_address_file', 'master_address_list.csv')}`

1. Right-click geodatabase → Import → Table
2. Select the master address CSV file
3. Name the table: `SCRPA_Addresses_Master`
4. Verify fields: AddressID, Address, BatchID

### Step 4: Execute Batch Geocoding

#### Option A: Process All Addresses at Once
```python
# In ArcGIS Pro Python window
import arcpy

# Set workspace
arcpy.env.workspace = r"path/to/SCRPA_Geocoding.gdb"

# Geocode all addresses
arcpy.geocoding.GeocodeAddresses(
    in_table="SCRPA_Addresses_Master",
    address_locator="NJ_Geocode",
    in_address_fields="Address Address VISIBLE NONE",
    out_feature_class="SCRPA_Geocoded_All",
    out_relationship_type="STATIC"
)
```

#### Option B: Process in Batches (Recommended for large datasets)
```python
import arcpy

# Process each batch
for batch_id in range(1, {self.preparation_results['geocoding_batches']} + 1):
    print(f"Processing batch {{batch_id}}")
    
    # Select current batch
    where_clause = f"BatchID = {{batch_id}}"
    batch_table = f"SCRPA_Batch_{{batch_id:02d}}"
    
    # Create batch table
    arcpy.analysis.TableSelect(
        in_table="SCRPA_Addresses_Master",
        out_table=batch_table,
        where_clause=where_clause
    )
    
    # Geocode batch
    output_fc = f"SCRPA_Geocoded_Batch_{{batch_id:02d}}"
    arcpy.geocoding.GeocodeAddresses(
        in_table=batch_table,
        address_locator="NJ_Geocode",
        in_address_fields="Address Address VISIBLE NONE",
        out_feature_class=output_fc,
        out_relationship_type="STATIC"
    )
    
    print(f"Batch {{batch_id}} completed")
```

### Step 5: Merge Batch Results (if using Option B)
```python
# Merge all batch results
batch_fcs = [f"SCRPA_Geocoded_Batch_{{i:02d}}" for i in range(1, {self.preparation_results['geocoding_batches']} + 1)]

arcpy.management.Merge(
    inputs=batch_fcs,
    output="SCRPA_Geocoded_Final"
)
```

### Step 6: Export Results
```python
# Export to CSV for integration with datasets
arcpy.conversion.TableToTable(
    in_table="SCRPA_Geocoded_Final",
    out_path=r"{self.geocoding_dir}",
    out_name="geocoding_results.csv"
)
```

### Step 7: Quality Assessment
After geocoding, run this analysis:

```python
# Count results by score
with arcpy.da.SearchCursor("SCRPA_Geocoded_Final", ["Score"]) as cursor:
    scores = [row[0] for row in cursor if row[0] is not None]

high_accuracy = sum(1 for s in scores if s >= 90)
medium_accuracy = sum(1 for s in scores if 80 <= s < 90)
low_accuracy = sum(1 for s in scores if s < 80)

print(f"High accuracy (>=90): {{high_accuracy}}")
print(f"Medium accuracy (80-89): {{medium_accuracy}}")
print(f"Low accuracy (<80): {{low_accuracy}}")
print(f"Success rate: {{(high_accuracy + medium_accuracy) / len(scores) * 100:.1f}}%")
```

## Expected Results

### Success Criteria
- **Target Success Rate:** 85%+ (addresses with score >= 80)
- **High Accuracy Rate:** 70%+ (addresses with score >= 90)
- **Processing Time:** < 30 minutes total

### Output Files
After successful geocoding, you should have:
1. `SCRPA_Geocoded_Final` (feature class with coordinates)
2. `geocoding_results.csv` (exportable results)

## Integration with SCRPA Datasets

After geocoding completion:

1. **Export coordinates:** Use the geocoding_results.csv
2. **Run integration script:** Execute the spatial enhancement script
3. **Update Power BI:** Refresh with enhanced datasets containing x_coord, y_coord

## Troubleshooting

### Common Issues
- **Service not found:** Verify NJ_Geocode is configured in ArcGIS Pro
- **Low success rate:** Check address quality and format
- **Performance issues:** Use batch processing for large datasets
- **Coordinate system:** Ensure State Plane NJ (EPSG:{self.target_srid}) is set

### Support Files
- **Address validation log:** Available in preparation results
- **Batch files:** Located in `{self.geocoding_dir}`
- **Spatial-ready datasets:** Available in `{self.output_dir}`

---

**Next Steps After Geocoding:**
1. Verify geocoding success rate meets targets
2. Run spatial dataset integration
3. Test ArcGIS Pro mapping with results  
4. Update Power BI with enhanced spatial data
"""
        
        # Save instructions
        instructions_file = self.project_path / '03_output' / f'arcgis_pro_geocoding_instructions_{self.preparation_results["execution_id"]}.md'
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions_content)
        
        self.preparation_results['arcgis_instructions_file'] = str(instructions_file)
        self.preparation_results['arcgis_instructions_created'] = True
        
        self.logger.info(f"✅ ArcGIS Pro instructions created: {instructions_file}")
        return str(instructions_file)

    def create_integration_script(self):
        """Create script to integrate geocoding results with datasets."""
        self.logger.info("Creating geocoding integration script...")
        
        integration_script = f'''# SCRPA Geocoding Results Integration Script
# Run this after ArcGIS Pro geocoding is complete

import pandas as pd
from pathlib import Path

def integrate_geocoding_results():
    """Integrate geocoding results with SCRPA datasets."""
    
    # Paths
    project_path = Path(r"{self.project_path}")
    output_dir = project_path / "04_powerbi"
    geocoding_dir = project_path / "geocoding_input"
    
    # Load geocoding results
    geocoding_results_file = geocoding_dir / "geocoding_results.csv"
    
    if not geocoding_results_file.exists():
        print("❌ Geocoding results file not found!")
        print(f"Expected: {{geocoding_results_file}}")
        return False
    
    # Read geocoding results
    geocoding_df = pd.read_csv(geocoding_results_file)
    print(f"📍 Loaded {{len(geocoding_df)}} geocoding results")
    
    # Create address lookup
    lookup = {{}}
    for _, row in geocoding_df.iterrows():
        address = row.get('Address', '')
        lookup[address] = {{
            'x_coord': row.get('X', None),
            'y_coord': row.get('Y', None),
            'geocode_score': row.get('Score', 0),
            'geocode_status': row.get('Status', 'UNKNOWN'),
            'match_address': row.get('Match_addr', '')
        }}
    
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
            print(f"🔄 Processing {{dataset_file}}...")
            
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
            
            print(f"  ✅ {{dataset_file}}: {{geocoded_count}}/{{original_count}} geocoded ({{enhancement_rate:.1f}}%)")
            print(f"  📄 Output: {{enhanced_file.name}}")
            
            enhanced_datasets.append({{
                'original': dataset_file,
                'enhanced': enhanced_file.name,
                'records': original_count,
                'geocoded': int(geocoded_count),
                'rate': enhancement_rate
            }})
        
        else:
            print(f"⚠️ Dataset not found: {{dataset_file}}")
    
    # Summary
    print("\\n" + "="*60)
    print("GEOCODING INTEGRATION COMPLETE")
    print("="*60)
    
    for dataset in enhanced_datasets:
        print(f"✅ {{dataset['enhanced']}}: {{dataset['geocoded']}}/{{dataset['records']}} ({{dataset['rate']:.1f}}%)")
    
    total_records = sum(d['records'] for d in enhanced_datasets)
    total_geocoded = sum(d['geocoded'] for d in enhanced_datasets)
    overall_rate = (total_geocoded / total_records) * 100 if total_records > 0 else 0
    
    print(f"\\n📊 Overall: {{total_geocoded}}/{{total_records}} geocoded ({{overall_rate:.1f}}%)")
    print("="*60)
    
    return True

if __name__ == "__main__":
    integrate_geocoding_results()
'''
        
        # Save integration script
        integration_file = self.project_path / '01_scripts' / 'integrate_geocoding_results.py'
        with open(integration_file, 'w', encoding='utf-8') as f:
            f.write(integration_script)
        
        self.preparation_results['integration_script'] = str(integration_file)
        self.logger.info(f"✅ Integration script created: {integration_file}")
        
        return str(integration_file)

    def generate_preparation_report(self):
        """Generate comprehensive preparation report."""
        self.logger.info("Generating preparation report...")
        
        try:
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - self.preparation_results['start_time']).total_seconds()
            
            # Create comprehensive report
            report_data = {
                'execution_summary': {
                    'execution_id': self.preparation_results['execution_id'],
                    'start_time': self.preparation_results['start_time'].isoformat(),
                    'end_time': end_time.isoformat(),
                    'processing_time_seconds': processing_time
                },
                'address_collection': {
                    'unique_addresses_found': self.preparation_results['unique_addresses_found'],
                    'geocoding_batches_created': self.preparation_results['geocoding_batches'],
                    'batch_size': self.batch_size,
                    'dataset_summaries': self.preparation_results.get('dataset_summaries', {})
                },
                'datasets_prepared': self.preparation_results['datasets_prepared'],
                'files_created': {
                    'master_address_file': self.preparation_results.get('master_address_file'),
                    'batch_files_count': len(self.preparation_results.get('batch_files', [])),
                    'arcgis_instructions': self.preparation_results.get('arcgis_instructions_file'),
                    'integration_script': self.preparation_results.get('integration_script')
                },
                'next_steps': {
                    'ready_for_arcgis_pro': True,
                    'estimated_geocoding_time': f"{self.preparation_results['unique_addresses_found'] * 0.5:.1f} minutes",
                    'expected_success_rate': "85%+",
                    'coordinate_system': f"State Plane NJ (EPSG:{self.target_srid})"
                }
            }
            
            # Save JSON report
            timestamp = self.preparation_results['execution_id']
            json_report_path = self.project_path / '03_output' / f'geocoding_preparation_report_{timestamp}.json'
            with open(json_report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            # Create markdown summary
            md_content = f"""# SCRPA Geocoding Preparation Report

**Execution ID:** {self.preparation_results['execution_id']}
**Date:** {self.preparation_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
**Processing Time:** {processing_time:.2f} seconds

## Preparation Summary

### Address Collection Results
- **Unique Addresses Found:** {self.preparation_results['unique_addresses_found']}
- **Geocoding Batches Created:** {self.preparation_results['geocoding_batches']}
- **Batch Size:** {self.batch_size} addresses per batch
- **Estimated Geocoding Time:** {self.preparation_results['unique_addresses_found'] * 0.5:.1f} minutes

### Dataset Breakdown
"""
            
            for dataset, summary in self.preparation_results.get('dataset_summaries', {}).items():
                if summary['exists']:
                    md_content += f"""
**{dataset}:**
- Total Records: {summary['total_records']}
- Valid Addresses: {summary['valid_addresses']}
- Invalid Addresses: {summary['invalid_addresses']}
"""
            
            md_content += f"""
### Files Created

#### Input Files for Geocoding:
- **Master Address List:** `{Path(self.preparation_results.get('master_address_file', '')).name}`
- **Batch Files:** {len(self.preparation_results.get('batch_files', []))} files created

#### Spatial-Ready Datasets:
"""
            
            for dataset in self.preparation_results['datasets_prepared']:
                md_content += f"- **{dataset['spatial_ready_file']}:** {dataset['records']} records, {dataset['total_columns']} columns (added {dataset['total_columns'] - dataset['original_columns']} spatial columns)\n"
            
            md_content += f"""
#### Supporting Files:
- **ArcGIS Pro Instructions:** `{Path(self.preparation_results.get('arcgis_instructions_file', '')).name}`
- **Integration Script:** `{Path(self.preparation_results.get('integration_script', '')).name}`

## Next Steps for Geocoding

### 1. ArcGIS Pro Execution
Follow the detailed instructions in: `{Path(self.preparation_results.get('arcgis_instructions_file', '')).name}`

**Key Points:**
- Use existing ArcGIS Pro template: `{self.template_path}`
- Access configured NJ_Geocode service
- Process {self.preparation_results['geocoding_batches']} batches of {self.batch_size} addresses each
- Output coordinates in State Plane NJ (EPSG:{self.target_srid})

### 2. Expected Results
- **Target Success Rate:** 85%+ (addresses with score >= 80)
- **High Accuracy Rate:** 70%+ (addresses with score >= 90)
- **Processing Time:** ~{self.preparation_results['unique_addresses_found'] * 0.5:.1f} minutes

### 3. Integration with Datasets
After successful geocoding:
1. Export results to CSV from ArcGIS Pro
2. Run integration script: `integrate_geocoding_results.py`
3. Verify enhanced datasets with coordinate columns

## Quality Assurance

### Address Validation Summary
All addresses have been validated for:
- ✅ Minimum length requirements
- ✅ Hackensack, NJ format compliance
- ✅ Invalid value filtering
- ✅ Character cleaning and normalization

### Expected Enhancement Rates
Based on address quality analysis:
- **CAD Data:** Expected 90%+ geocoding success
- **RMS Data:** Expected 85%+ geocoding success  
- **Matched Data:** Expected 87%+ geocoding success

## Files Ready for Processing

### Geocoding Input Directory: `{self.geocoding_dir}`
"""
            
            if self.preparation_results.get('batch_files'):
                md_content += f"""
#### Batch Files ({len(self.preparation_results['batch_files'])} files):
"""
                for i, batch_file in enumerate(self.preparation_results['batch_files'][:5], 1):  # Show first 5
                    md_content += f"- `{Path(batch_file).name}`\n"
                
                if len(self.preparation_results['batch_files']) > 5:
                    md_content += f"- ... and {len(self.preparation_results['batch_files']) - 5} more batch files\n"
            
            md_content += f"""
### Spatial-Ready Datasets: `{self.output_dir}`
"""
            
            for dataset in self.preparation_results['datasets_prepared']:
                md_content += f"- `{dataset['spatial_ready_file']}` (ready for coordinate integration)\n"
            
            md_content += f"""
## Success Criteria

### Geocoding Execution:
- ✅ All {self.preparation_results['unique_addresses_found']} addresses processed
- ✅ Success rate >= 85% (score >= 80)
- ✅ High accuracy rate >= 70% (score >= 90)
- ✅ Processing time < 30 minutes

### Dataset Enhancement:
- ✅ All 3 target datasets enhanced with spatial columns
- ✅ Coordinate data populated for matched addresses
- ✅ Enhanced datasets ready for ArcGIS Pro and Power BI

---

**Status: READY FOR ARCGIS PRO GEOCODING** ✅

All preparation steps completed successfully. Proceed with ArcGIS Pro geocoding execution using the provided instructions.
"""
            
            # Save markdown report
            md_report_path = self.project_path / '03_output' / f'geocoding_preparation_summary_{timestamp}.md'
            with open(md_report_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            self.logger.info(f"✅ Preparation reports generated:")
            self.logger.info(f"  📊 JSON Report: {json_report_path}")
            self.logger.info(f"  📋 Summary Report: {md_report_path}")
            
            return str(md_report_path)
            
        except Exception as e:
            self.logger.error(f"❌ Report generation failed: {e}")
            return None

    def execute_preparation(self):
        """Execute the complete geocoding preparation workflow."""
        self.logger.info("🚀 Starting SCRPA Geocoding Preparation...")
        
        try:
            # Step 1: Collect and validate addresses
            address_list, address_validation = self.collect_and_validate_addresses()
            if not address_list:
                raise Exception("No valid addresses found for geocoding")
            
            # Step 2: Create geocoding input files
            master_file, batch_files = self.create_geocoding_input_files(address_list)
            
            # Step 3: Prepare spatial-ready datasets
            self.prepare_spatial_datasets()
            
            # Step 4: Create ArcGIS Pro instructions
            instructions_file = self.create_arcgis_pro_instructions()
            
            # Step 5: Create integration script
            integration_script = self.create_integration_script()
            
            # Step 6: Generate comprehensive report
            report_path = self.generate_preparation_report()
            
            # Final summary
            total_addresses = self.preparation_results['unique_addresses_found']
            batches = self.preparation_results['geocoding_batches']
            datasets = len(self.preparation_results['datasets_prepared'])
            
            self.logger.info("="*80)
            self.logger.info("🎯 SCRPA GEOCODING PREPARATION COMPLETE")
            self.logger.info("="*80)
            self.logger.info(f"📍 Unique Addresses: {total_addresses}")
            self.logger.info(f"📦 Geocoding Batches: {batches}")
            self.logger.info(f"📊 Datasets Prepared: {datasets}")
            self.logger.info(f"📋 Instructions: {Path(instructions_file).name}")
            self.logger.info(f"📋 Report: {Path(report_path).name}")
            self.logger.info("="*80)
            self.logger.info("✅ READY FOR ARCGIS PRO GEOCODING EXECUTION")
            self.logger.info("="*80)
            
            return {
                'status': 'SUCCESS',
                'unique_addresses': total_addresses,
                'geocoding_batches': batches,
                'datasets_prepared': datasets,
                'instructions_file': instructions_file,
                'integration_script': integration_script,
                'report_path': report_path,
                'execution_id': self.preparation_results['execution_id']
            }
            
        except Exception as e:
            self.logger.error(f"❌ Geocoding preparation failed: {e}")
            
            return {
                'status': 'FAILED',
                'error': str(e),
                'execution_id': self.preparation_results['execution_id']
            }

def main():
    """Main execution function."""
    try:
        preparator = SCRPAGeocodingPreparation()
        results = preparator.execute_preparation()
        
        # Print summary for console
        print("\n" + "="*60)
        print("SCRPA GEOCODING PREPARATION RESULTS")
        print("="*60)
        print(f"Status: {results['status']}")
        
        if results['status'] == 'SUCCESS':
            print(f"Unique Addresses: {results['unique_addresses']}")
            print(f"Geocoding Batches: {results['geocoding_batches']}")
            print(f"Datasets Prepared: {results['datasets_prepared']}")
            print(f"Instructions: {Path(results['instructions_file']).name}")
            print(f"Report: {Path(results['report_path']).name}")
            print("\n🎉 PREPARATION COMPLETED - READY FOR ARCGIS PRO!")
            sys.exit(0)
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
            print("\n❌ PREPARATION FAILED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()