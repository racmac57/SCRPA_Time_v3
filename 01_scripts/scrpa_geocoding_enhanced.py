import arcpy
import pandas as pd
import os
from pathlib import Path
import logging

def setup_logging():
    """Setup logging for geocoding process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('geocoding.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def geocode_scrpa_addresses(input_csv_path, output_csv_path, batch_size=100):
    """
    Geocode addresses from SCRPA data using NJ_Geocode service.
    
    Args:
        input_csv_path: Path to CSV with addresses
        output_csv_path: Path to save geocoded results
        batch_size: Addresses per batch
    
    Returns:
        Dictionary with geocoding statistics
    """
    
    logger = setup_logging()
    logger.info("Starting SCRPA address geocoding...")
    
    # Results tracking
    results = {
        'total_addresses': 0,
        'successful_geocodes': 0,
        'failed_geocodes': 0,
        'high_accuracy_geocodes': 0,  # Score >= 90
        'processing_time': 0
    }
    
    try:
        import time
        start_time = time.time()
        
        # Read input data
        df = pd.read_csv(input_csv_path)
        
        # Find address column
        address_column = None
        possible_columns = ['location', 'Location', 'address', 'Address', 'full_address_raw']
        
        for col in possible_columns:
            if col in df.columns:
                address_column = col
                break
        
        if not address_column:
            raise ValueError(f"No address column found. Available columns: {list(df.columns)}")
        
        logger.info(f"Using address column: {address_column}")
        
        # Get unique addresses
        addresses = df[address_column].dropna().unique()
        results['total_addresses'] = len(addresses)
        
        logger.info(f"Found {len(addresses)} unique addresses to geocode")
        
        # Setup ArcGIS workspace
        arcpy.env.workspace = r"C:\temp"
        arcpy.env.overwriteOutput = True
        
        # Create temporary workspace
        temp_gdb = "geocoding_temp.gdb"
        if arcpy.Exists(temp_gdb):
            arcpy.Delete_management(temp_gdb)
        arcpy.CreateFileGDB_management(arcpy.env.workspace, "geocoding_temp")
        
        # Geocoding service (configured in ArcGIS Pro)
        geocode_service = "NJ_Geocode"
        
        # Process all addresses at once for better performance
        logger.info("Creating input table for geocoding...")
        
        input_table = os.path.join(temp_gdb, "addresses_to_geocode")
        arcpy.CreateTable_management(temp_gdb, "addresses_to_geocode")
        arcpy.AddField_management(input_table, "Address", "TEXT", field_length=500)
        arcpy.AddField_management(input_table, "ID", "LONG")
        
        # Insert addresses
        with arcpy.da.InsertCursor(input_table, ["Address", "ID"]) as cursor:
            for i, address in enumerate(addresses):
                cursor.insertRow([str(address), i])
        
        # Geocode all addresses
        logger.info("Geocoding addresses...")
        output_fc = os.path.join(temp_gdb, "geocoded_addresses")
        
        arcpy.GeocodeAddresses_geocoding(
            input_table,
            geocode_service,
            "Address Address VISIBLE NONE",
            output_fc,
            "STATIC"
        )
        
        # Extract results
        logger.info("Extracting geocoding results...")
        geocoded_data = []
        
        fields = ["Address", "SHAPE@X", "SHAPE@Y", "Score", "Status", "Match_addr", "ID"]
        
        with arcpy.da.SearchCursor(output_fc, fields) as cursor:
            for row in cursor:
                geocoded_data.append({
                    'original_address': row[0],
                    'x_coord': row[1] if row[1] else None,
                    'y_coord': row[2] if row[2] else None,
                    'geocode_score': row[3] if row[3] else 0,
                    'geocode_status': row[4] if row[4] else 'FAILED',
                    'match_address': row[5] if row[5] else None,
                    'address_id': row[6]
                })
                
                # Count results
                if row[3] and row[3] >= 80:
                    results['successful_geocodes'] += 1
                    if row[3] >= 90:
                        results['high_accuracy_geocodes'] += 1
                else:
                    results['failed_geocodes'] += 1
        
        # Save results
        if geocoded_data:
            results_df = pd.DataFrame(geocoded_data)
            results_df.to_csv(output_csv_path, index=False)
            logger.info(f"Geocoded results saved to: {output_csv_path}")
        
        # Cleanup
        arcpy.Delete_management(temp_gdb)
        
        # Calculate processing time
        results['processing_time'] = time.time() - start_time
        
        # Log final statistics
        logger.info("Geocoding completed!")
        logger.info(f"Total addresses: {results['total_addresses']}")
        logger.info(f"Successful geocodes: {results['successful_geocodes']}")
        logger.info(f"High accuracy (>=90): {results['high_accuracy_geocodes']}")
        logger.info(f"Failed geocodes: {results['failed_geocodes']}")
        logger.info(f"Success rate: {(results['successful_geocodes']/results['total_addresses']*100):.1f}%")
        logger.info(f"Processing time: {results['processing_time']:.2f} seconds")
        
        return results
        
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        results['error'] = str(e)
        return results

# Example usage:
if __name__ == "__main__":
    # Geocode RMS data
    rms_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\rms_data_standardized.csv"
    rms_output = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\rms_data_geocoded.csv"
    
    if os.path.exists(rms_path):
        print("Geocoding RMS data...")
        rms_results = geocode_scrpa_addresses(rms_path, rms_output)
        print(f"RMS geocoding results: {rms_results}")
    
    # Geocode CAD data
    cad_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\cad_data_standardized.csv"
    cad_output = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\cad_data_geocoded.csv"
    
    if os.path.exists(cad_path):
        print("Geocoding CAD data...")
        cad_results = geocode_scrpa_addresses(cad_path, cad_output)
        print(f"CAD geocoding results: {cad_results}")
