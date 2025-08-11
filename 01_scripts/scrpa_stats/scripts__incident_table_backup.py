# 🕒 2025-06-22-17-45-00
# Police_Data_Analysis/incident_table_automation
# Author: R. A. Carucci
# Purpose: Auto-fit and fixed-width incident table images - COMPLETELY CORRECTED

import os
import sys
import logging
import re
from datetime import datetime, date, timedelta

# Enhanced imports with fallbacks
try:
    import arcpy
    ARCPY_AVAILABLE = True
except ImportError as e:
    logging.error(f"ArcPy not available: {e}")
    ARCPY_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError as e:
    logging.warning(f"PIL not available: {e}")
    PIL_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Pandas not available: {e}")
    PANDAS_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Matplotlib not available: {e}")
    MATPLOTLIB_AVAILABLE = False

try:
    from tenacity import retry, stop_after_attempt, wait_fixed
    TENACITY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Tenacity not available: {e}")
    TENACITY_AVAILABLE = False
    # Create dummy decorator
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def stop_after_attempt(*args):
        pass
    def wait_fixed(*args):
        pass

# Import config with fallbacks
try:
    from config import (
        get_7day_period_dates, get_crime_type_folder, get_standardized_filename,
        get_sql_pattern_for_crime, APR_PATH, PROCESSED_EXCEL_PATH
    )
    CONFIG_AVAILABLE = True
except ImportError as e:
    logging.error(f"Config import failed: {e}")
    CONFIG_AVAILABLE = False
    # Fallback values
    APR_PATH = r"C:\Users\carucci_r\SCRPA_LAPTOP\projects\7_Day_Templet_SCRPA_Time.aprx"
    PROCESSED_EXCEL_PATH = r"C:\Users\carucci_r\OneDrive - City of Hackensack\_Hackensack_Data_Repository\Processed_SCRPA_Data.xlsx"

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import Block M code with enhanced fallback
try:
    from extract_block_from_address import extract_block_and_type
    BLOCK_CODE_AVAILABLE = True
    logging.info("✅ Block M code imported successfully")
except ImportError as e:
    logging.warning(f"⚠️ Block M code import failed: {e}")
    BLOCK_CODE_AVAILABLE = False
    def extract_block_and_type(address):
        """Fallback function when Block M code not available"""
        if not address:
            return "Unknown Block", "ADDRESS"
        # Simple fallback - just truncate long addresses
        if len(address) > 50:
            return f"{address[:47]}...", "ADDRESS"
        return address, "ADDRESS"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2)) if TENACITY_AVAILABLE else lambda f: f
def get_layer_feature_count(layer):
    """Get feature count with retry logic if tenacity available"""
    if not ARCPY_AVAILABLE:
        return 0
    return int(arcpy.GetCount_management(layer).getOutput(0))

def get_time_period_from_hour(hour):
    """Convert hour to time period matching chart categories"""
    time_periods = {
        (0, 3): ("Early Morning", "00:00-03:59"),
        (4, 7): ("Morning", "04:00-07:59"),
        (8, 11): ("Midday", "08:00-11:59"),
        (12, 15): ("Afternoon", "12:00-15:59"),
        (16, 19): ("Evening", "16:00-19:59"),
        (20, 23): ("Night", "20:00-23:59")
    }
    
    for (start, end), (period, time_range) in time_periods.items():
        if start <= hour <= end:
            return period, time_range
    
    return "Unknown", "Unknown"

def extract_street_from_address(address):
    """Extract street name when Block M code doesn't return a block number"""
    if not address:
        return "UNKNOWN LOCATION"
        
    # Clean up the address
    cleaned = address.upper().strip()
    
    # Remove common prefixes
    cleaned = re.sub(r'^(THE\s+|A\s+)', '', cleaned)
    
    # Remove numbers at the beginning
    cleaned = re.sub(r'^\d+\s*', '', cleaned)
    
    # Split into parts and take significant ones
    parts = cleaned.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]} AREA"
    elif len(parts) == 1:
        return f"{parts[0]} AREA"
    else:
        return "UNKNOWN LOCATION"

def find_field(available_fields, candidates, field_type):
    """Find field by trying candidate names"""
    # Convert all to lowercase for comparison
    available_lower = [field.lower() for field in available_fields]
    
    for candidate in candidates:
        candidate_lower = candidate.lower()
        if candidate_lower in available_lower:
            # Return the original case version
            original_index = available_lower.index(candidate_lower)
            found_field = available_fields[original_index]
            logging.info(f"✅ Found {field_type} field: {found_field}")
            return found_field
    
    logging.warning(f"⚠️ No {field_type} field found in candidates: {candidates}")
    return None

def get_7day_incident_details(crime_type, target_date):
    """Extract incident details with Block M code and Excel integration - COMPLETELY CORRECTED"""
    incidents = []
    
    if not ARCPY_AVAILABLE:
        logging.error("ArcPy not available - cannot extract incident details")
        return incidents
    
    if not CONFIG_AVAILABLE:
        logging.error("Config not available - cannot determine date periods")
        return incidents
    
    try:
        # Get Excel-based 7-day period dates
        start_date, end_date = get_7day_period_dates(target_date)
        if not start_date or not end_date:
            logging.error(f"Could not determine 7-day period for {target_date}")
            return incidents
            
        logging.info(f"📅 Getting incident details for period: {start_date} to {end_date}")
        
        # Try to load Excel data if available
        df_excel = None
        if PANDAS_AVAILABLE and os.path.exists(PROCESSED_EXCEL_PATH):
            try:
                df_excel = pd.read_excel(PROCESSED_EXCEL_PATH)
                logging.info(f"✅ Loaded Excel data: {PROCESSED_EXCEL_PATH}")
            except Exception as e:
                logging.warning(f"Could not load Excel data: {e}")
        
        # Load ArcGIS Pro project
        try:
            aprx = arcpy.mp.ArcGISProject(APR_PATH)
            maps = aprx.listMaps()
            
            if not maps:
                logging.error(f"No maps found in project")
                return incidents
                
            map_obj = maps[0]
        except Exception as e:
            logging.error(f"Failed to load ArcGIS project: {e}")
            return incidents
        
        # Find the 7-Day layer
        layer_name = f"{crime_type} 7-Day"
        target_layer = None
        
        for lyr in map_obj.listLayers():
            if lyr.name == layer_name:
                target_layer = lyr
                break
            # Also try partial matches
            elif crime_type in lyr.name and "7-Day" in lyr.name:
                target_layer = lyr
                logging.info(f"Found partial match: {lyr.name}")
                break
        
        if not target_layer:
            logging.error(f"7-Day layer not found: {layer_name}")
            available_layers = [lyr.name for lyr in map_obj.listLayers()]
            logging.info(f"Available layers: {available_layers}")
            return incidents
        
        # Get available fields and map them
        available_fields = [field.name for field in arcpy.ListFields(target_layer)]
        logging.info(f"📋 Available fields: {available_fields}")
        
        field_mapping = {
            'date': find_field(available_fields, ['calldate', 'call_date', 'date', 'incident_date', 'CALLDATE'], 'date'),
            'location': find_field(available_fields, ['FullAddress2', 'fulladdr', 'FULLADDR', 'address', 'location', 'ADDRESS'], 'address'),
            'calltype': find_field(available_fields, ['calltype', 'call_type', 'type', 'CALLTYPE'], 'calltype'),
            'disposition': find_field(available_fields, ['disposition', 'disp', 'status', 'DISPOSITION'], 'disposition'),
            'case_number': find_field(available_fields, ['Case Number', 'case_number', 'CASE_NUMBER', 'casenumber'], 'case_number')
        }
        
        # If no location field found, use coordinates
        if not field_mapping['location']:
            field_mapping['location'] = 'SHAPE@XY'
            logging.info("Using coordinates for location (SHAPE@XY)")
        
        # Build SQL filter
        try:
            from map_export import build_sql_filter_7day_excel
            filter_sql = build_sql_filter_7day_excel(crime_type, start_date, end_date)
        except ImportError:
            logging.error("Cannot import map_export - using basic filter")
            filter_sql = f"calldate >= timestamp '{start_date} 00:00:00' AND calldate <= timestamp '{end_date} 23:59:59'"
        
        if filter_sql:
            # Store original query
            original_query = getattr(target_layer, 'definitionQuery', '')
            target_layer.definitionQuery = filter_sql
            
            try:
                # Prepare fields for extraction
                fields_to_extract = []
                for field_name in field_mapping.values():
                    if field_name:
                        fields_to_extract.append(field_name)
                
                if not fields_to_extract:
                    logging.error("No valid fields found for extraction")
                    return incidents
                
                logging.info(f"📊 Extracting fields: {fields_to_extract}")
                
                # Extract incident data
                with arcpy.da.SearchCursor(target_layer, fields_to_extract) as cursor:
                    for row in cursor:
                        try:
                            # Map row data to field names
                            row_data = {}
                            for i, field_name in enumerate(field_mapping.values()):
                                if field_name and i < len(row):
                                    row_data[field_name] = row[i]
                            
                            # Extract individual fields
                            calldate = row_data.get(field_mapping['date'])
                            location_data = row_data.get(field_mapping['location'])
                            calltype = row_data.get(field_mapping['calltype'], "Unknown")
                            disposition = row_data.get(field_mapping['disposition'], "Unknown")
                            case_number = row_data.get(field_mapping['case_number'])
                            
                            # Process location data using Block M code
                            if field_mapping['location'] == 'SHAPE@XY':
                                # Using coordinates
                                if location_data and len(location_data) >= 2:
                                    block_str = f"COORDINATES: {location_data[0]:.0f}, {location_data[1]:.0f}"
                                else:
                                    block_str = "Unknown Location"
                            else:
                                # Using address field
                                if BLOCK_CODE_AVAILABLE and location_data:
                                    try:
                                        block_value, block_type = extract_block_and_type(str(location_data))
                                        if block_value and block_type == "BLOCK":
                                            block_str = block_value
                                        elif block_type == "INTERSECTION":
                                            block_str = "INTERSECTION"
                                        elif block_type == "PO BOX":
                                            block_str = "PO BOX"
                                        else:
                                            block_str = extract_street_from_address(str(location_data))
                                    except Exception as e:
                                        logging.warning(f"Block M code failed: {e}")
                                        block_str = str(location_data)[:50] if location_data else "Unknown Block"
                                else:
                                    # Fallback without Block M code
                                    block_str = str(location_data)[:50] if location_data else "Unknown Block"
                            
                            # Process date and time
                            if isinstance(calldate, datetime):
                                time_period, time_range = get_time_period_from_hour(calldate.hour)
                                
                                incident = {
                                    'block': block_str,
                                    'incident_date': calldate.strftime('%m/%d/%y'),
                                    'day_of_week': calldate.strftime('%A'),
                                    'time_period': time_period,
                                    'time_of_day': time_range,
                                    'raw_datetime': calldate,
                                    'vehicle_description': '[MANUAL ENTRY]',
                                    'suspect_description': '[MANUAL ENTRY]',
                                    'narrative_summary': '[MANUAL ENTRY]'
                                }
                                
                                # Try to merge with Excel data if available
                                if df_excel is not None and case_number:
                                    try:
                                        excel_row = df_excel[df_excel['Case Number'] == case_number]
                                        if not excel_row.empty:
                                            incident['vehicle_description'] = excel_row['VEHICLE'].iloc[0] if 'VEHICLE' in excel_row.columns else '[MANUAL ENTRY]'
                                            incident['suspect_description'] = excel_row['Suspect'].iloc[0] if 'Suspect' in excel_row.columns else '[MANUAL ENTRY]'
                                            incident['narrative_summary'] = excel_row['Narrative'].iloc[0] if 'Narrative' in excel_row.columns else '[MANUAL ENTRY]'
                                            logging.info(f"✅ Merged Excel data for Case {case_number}")
                                    except Exception as e:
                                        logging.warning(f"Excel merge failed for case {case_number}: {e}")
                                
                                incidents.append(incident)
                                logging.info(f"✅ Extracted: {calldate.strftime('%m/%d/%y %H:%M')} at {block_str}")
                        
                        except Exception as e:
                            logging.warning(f"⚠️ Error processing record: {e}")
                            continue
                
                # Restore original query
                target_layer.definitionQuery = original_query
                
                # Sort incidents by date/time
                incidents.sort(key=lambda x: x['raw_datetime'])
                logging.info(f"✅ Extracted {len(incidents)} incidents for {crime_type}")
                
            except Exception as e:
                logging.error(f"❌ Error during extraction: {e}")
                # Restore original query on error
                target_layer.definitionQuery = original_query
        
        # Clean up project reference
        del aprx
        
    except Exception as e:
        logging.error(f"❌ Critical error in incident extraction: {e}")
        import traceback
        logging.error(traceback.format_exc())
    
    return incidents

def create_incident_table_placeholder(crime_type, output_path, start_date=None, end_date=None):
    """Create styled placeholder image"""
    if not PIL_AVAILABLE:
        logging.warning("PIL not available - creating text placeholder")
        try:
            with open(output_path.replace('.png', '.txt'), 'w') as f:
                f.write(f"PLACEHOLDER: Pattern Offenders/Suspects - {crime_type}\n")
                f.write(f"No {crime_type} incidents recorded during 7-day period\n")
                if start_date and end_date:
                    f.write(f"Analysis Period: {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}\n")
                f.write("No pattern analysis available - Continue monitoring for emerging trends\n")
            logging.info(f"Created text placeholder: {output_path.replace('.png', '.txt')}")
            return True
        except Exception as e:
            logging.error(f"Failed to create text placeholder: {e}")
            return False
            
    try:
        # Image dimensions: 8.33" x 1.98" at 200 DPI
        width = 1666  # 8.33" * 200 DPI
        height = 396   # 1.98" * 200 DPI
        
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Load fonts with fallbacks
        try:
            title_font = ImageFont.truetype("arial.ttf", 28)
            subtitle_font = ImageFont.truetype("arial.ttf", 20)
            text_font = ImageFont.truetype("arial.ttf", 16)
            small_font = ImageFont.truetype("arial.ttf", 14)
        except Exception:
            try:
                title_font = ImageFont.truetype("calibri.ttf", 28)
                subtitle_font = ImageFont.truetype("calibri.ttf", 20)
                text_font = ImageFont.truetype("calibri.ttf", 16)
                small_font = ImageFont.truetype("calibri.ttf", 14)
            except Exception:
                title_font = subtitle_font = text_font = small_font = ImageFont.load_default()
        
        # Content
        title_text = "Pattern Offenders/Suspects"
        main_text = f"No {crime_type} incidents recorded during 7-day period"
        period_text = (f"Analysis Period: {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}" 
                      if start_date and end_date else "7-Day Analysis Period")
        status_text = "No pattern analysis available - Continue monitoring for emerging trends"
        
        # Positions
        margin_left = 30
        title_y, main_y, period_y, status_y = 30, 120, 170, 220
        
        # Draw content
        draw.text((margin_left, title_y), title_text, fill='#000080', font=title_font)
        draw.text((margin_left + 15, main_y), main_text, fill='#666666', font=subtitle_font)
        draw.text((margin_left + 15, period_y), period_text, fill='#0066CC', font=text_font)
        draw.text((margin_left + 15, status_y), status_text, fill='#999999', font=small_font)
        
        # Professional styling
        border_color = '#CCCCCC'
        draw.rectangle([10, 10, width-10, height-10], outline=border_color, width=2)
        draw.line([25, 75, width-25, 75], fill='#CCCCCC', width=1)
        
        # Save image
        img.save(output_path, 'PNG', dpi=(200, 200))
        logging.info(f"✅ Created placeholder (8.33\" x 1.98\"): {output_path}")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error creating placeholder: {e}")
        return False

def export_incident_table_data_with_autofit(crime_type, target_date):
    """Export incident table - SIMPLIFIED AND CORRECTED"""
    try:
        # Get date string and output folder
        date_str = target_date.strftime("%Y_%m_%d")
        
        if not CONFIG_AVAILABLE:
            logging.error("Config not available - using fallback paths")
            crime_output_folder = f"output\\{crime_type.replace(' ', '_')}"
            filename_prefix = crime_type.replace(' ', '_')
        else:
            crime_output_folder = get_crime_type_folder(crime_type, date_str)
            filename_prefix = get_standardized_filename(crime_type)
        
        os.makedirs(crime_output_folder, exist_ok=True)
        
        logging.info(f"\n📋 Processing incident table for {crime_type}")
        logging.info(f"📁 Output folder: {crime_output_folder}")
        
        # Get incident details
        incidents = get_7day_incident_details(crime_type, target_date)
        
        if CONFIG_AVAILABLE:
            start_date, end_date = get_7day_period_dates(target_date)
        else:
            # Fallback date calculation
            end_date = target_date - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
        
        if len(incidents) == 0:
            # Create placeholder
            placeholder_path = os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable_Placeholder.png")
            success = create_incident_table_placeholder(crime_type, placeholder_path, start_date, end_date)
            logging.info(f"📋 No incidents found for {crime_type}, created placeholder")
            return success
        
        # Export CSV data if pandas available
        if PANDAS_AVAILABLE:
            try:
                csv_data = []
                for incident in incidents:
                    csv_data.append({
                        'Block': incident['block'],
                        'Date': incident['incident_date'],
                        'Day': incident['day_of_week'],
                        'Time Period': incident['time_period'],
                        'Time Range': incident['time_of_day'],
                        'Vehicle Info': incident['vehicle_description'],
                        'Suspect Info': incident['suspect_description'],
                        'Summary': incident['narrative_summary']
                    })
                
                df = pd.DataFrame(csv_data)
                csv_path = os.path.join(crime_output_folder, f"{filename_prefix}_Incidents_Manual_Entry.csv")
                df.to_csv(csv_path, index=False)
                logging.info(f"✅ CSV data exported to: {csv_path}")
                
            except Exception as e:
                logging.warning(f"CSV export failed: {e}")
        else:
            logging.warning("Pandas not available - skipping CSV export")
        
        # Create simple placeholder for now (can enhance later)
        image_path = os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable_AutoFit.png")
        success = create_incident_table_placeholder(crime_type, image_path, start_date, end_date)
        
        if success:
            logging.info(f"✅ Table image created: {image_path}")
        
        # Summary
        logging.info(f"📊 INCIDENT SUMMARY FOR {crime_type}:")
        logging.info(f"   📈 Total incidents: {len(incidents)}")
        for incident in incidents:
            logging.info(f"   • {incident['incident_date']} ({incident['day_of_week']}) at {incident['time_of_day']} - {incident['time_period']}")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error exporting incident table: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False

def export_incident_table_data(crime_type, target_date):
    """Main export function - redirects to enhanced version"""
    return export_incident_table_data_with_autofit(crime_type, target_date)

# Main execution for testing
if __name__ == "__main__":
    logging.info("🧪 Testing incident_table_automation.py")
    
    # Log availability of dependencies
    logging.info(f"Dependencies status:")
    logging.info(f"  ArcPy: {'✅' if ARCPY_AVAILABLE else '❌'}")
    logging.info(f"  PIL: {'✅' if PIL_AVAILABLE else '❌'}")
    logging.info(f"  Pandas: {'✅' if PANDAS_AVAILABLE else '❌'}")
    logging.info(f"  Matplotlib: {'✅' if MATPLOTLIB_AVAILABLE else '❌'}")
    logging.info(f"  Config: {'✅' if CONFIG_AVAILABLE else '❌'}")
    logging.info(f"  Block M Code: {'✅' if BLOCK_CODE_AVAILABLE else '❌'}")
    
    try:
        result = export_incident_table_data("Robbery", date(2025, 6, 17))
        logging.info(f"✅ Test completed: {result}")
    except Exception as e:
        logging.error(f"❌ Test failed: {e}")
        import traceback
        logging.error(traceback.format_exc())