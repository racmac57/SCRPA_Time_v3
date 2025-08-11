
import arcpy
import pandas as pd
from pathlib import Path
import logging

def batch_geocode_addresses(addresses_list, output_path, batch_size=100):
    """
    Batch geocode addresses using NJ_Geocode service.
    
    Args:
        addresses_list: List of addresses to geocode
        output_path: Path to save geocoded results
        batch_size: Number of addresses per batch
    
    Returns:
        Dict with geocoding results and statistics
    """
    
    # Set up workspace
    arcpy.env.workspace = r"C:\temp\geocoding"
    arcpy.env.overwriteOutput = True
    
    results = {
        'total_addresses': len(addresses_list),
        'processed_count': 0,
        'successful_geocodes': 0,
        'failed_geocodes': 0,
        'geocoded_data': []
    }
    
    try:
        # Create temporary geodatabase
        temp_gdb = arcpy.env.workspace + "\temp_geocoding.gdb"
        if not arcpy.Exists(temp_gdb):
            arcpy.CreateFileGDB_management(arcpy.env.workspace, "temp_geocoding.gdb")
        
        # NJ Geocode service (configured in ArcGIS Pro template)
        geocode_service = "NJ_Geocode"
        
        # Process in batches
        batch_num = 0
        for i in range(0, len(addresses_list), batch_size):
            batch = addresses_list[i:i + batch_size]
            batch_num += 1
            
            print(f"Processing batch {batch_num}: {len(batch)} addresses")
            
            # Create input table for batch
            input_table = temp_gdb + f"\batch_{batch_num}_input"
            
            # Create table with address field
            arcpy.CreateTable_management(temp_gdb, f"batch_{batch_num}_input")
            arcpy.AddField_management(input_table, "Address", "TEXT", field_length=255)
            
            # Insert addresses
            with arcpy.da.InsertCursor(input_table, ["Address"]) as cursor:
                for address in batch:
                    cursor.insertRow([address])
            
            # Geocode batch
            output_fc = temp_gdb + f"\batch_{batch_num}_geocoded"
            
            try:
                arcpy.GeocodeAddresses_geocoding(
                    input_table,
                    geocode_service,
                    "Address Address VISIBLE NONE",
                    output_fc,
                    "STATIC"
                )
                
                # Extract results
                fields = ["Address", "SHAPE@X", "SHAPE@Y", "Score", "Status", "Match_addr"]
                
                with arcpy.da.SearchCursor(output_fc, fields) as cursor:
                    for row in cursor:
                        results['geocoded_data'].append({
                            'address': row[0],
                            'x_coord': row[1],
                            'y_coord': row[2],
                            'geocode_score': row[3],
                            'geocode_status': row[4],
                            'match_address': row[5]
                        })
                        
                        if row[3] >= 80:  # Score >= 80 considered successful
                            results['successful_geocodes'] += 1
                        else:
                            results['failed_geocodes'] += 1
                
                results['processed_count'] += len(batch)
                
            except Exception as e:
                print(f"Error geocoding batch {batch_num}: {e}")
                # Add failed records
                for address in batch:
                    results['geocoded_data'].append({
                        'address': address,
                        'x_coord': None,
                        'y_coord': None,
                        'geocode_score': 0,
                        'geocode_status': 'FAILED',
                        'match_address': None
                    })
                    results['failed_geocodes'] += 1
        
        # Save results to CSV
        if results['geocoded_data']:
            df = pd.DataFrame(results['geocoded_data'])
            df.to_csv(output_path, index=False)
            print(f"Geocoding results saved to: {output_path}")
        
        # Cleanup
        arcpy.Delete_management(temp_gdb)
        
        return results
        
    except Exception as e:
        print(f"Geocoding batch processor error: {e}")
        return results

# Example usage:
# addresses = ["123 Main St, Hackensack, NJ", "456 Oak Ave, Hackensack, NJ"]
# results = batch_geocode_addresses(addresses, "geocoded_results.csv")
