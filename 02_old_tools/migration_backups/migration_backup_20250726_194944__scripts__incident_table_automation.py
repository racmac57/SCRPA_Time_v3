# 🕒 2025-01-27-23-25-00
# SCRPA_Project/incident_table_automation_final
# Author: R. A. Carucci
# Purpose: Complete incident table automation with Pattern Offenders/Suspects placeholders

import os
import logging
from datetime import datetime, date
from PIL import Image, ImageDraw, ImageFont
import arcpy
from config import (
    get_7day_period_dates, get_crime_type_folder, get_standardized_filename, 
    get_sql_pattern_for_crime, APR_PATH
)

def get_time_period_from_hour(hour):
    """Convert hour to time period matching chart categories"""
    if 0 <= hour <= 3:
        return "Early Morning"
    elif 4 <= hour <= 7:
        return "Morning"
    elif 8 <= hour <= 11:
        return "Midday"
    elif 12 <= hour <= 15:
        return "Afternoon"
    elif 16 <= hour <= 19:
        return "Evening"
    elif 20 <= hour <= 23:
        return "Night"
    else:
        return "Unknown"

def create_incident_table_placeholder(crime_type, output_path, start_date=None, end_date=None):
    """
    Create placeholder image for Pattern Offenders/Suspects section
    Dimensions: 8" x 2.3" at 200 DPI = 1600 x 460 pixels
    """
    try:
        # Image dimensions matching PowerPoint shape
        width = 1600  # 8 inches * 200 DPI
        height = 460  # 2.3 inches * 200 DPI
        
        # Create white background
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Try to use system fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 28)
            subtitle_font = ImageFont.truetype("arial.ttf", 22)
            text_font = ImageFont.truetype("arial.ttf", 18)
            small_font = ImageFont.truetype("arial.ttf", 16)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Text content
        title_text = "Pattern Offenders/Suspects"
        main_text = f"No {crime_type} incidents recorded during 7-day period"
        
        # Add period information if available
        if start_date and end_date:
            period_text = f"Analysis Period: {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"
        else:
            period_text = "7-Day Analysis Period"
        
        status_text = "No pattern analysis available - Continue monitoring for emerging trends"
        
        # Calculate positions for horizontal layout
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        main_bbox = draw.textbbox((0, 0), main_text, font=subtitle_font)
        period_bbox = draw.textbbox((0, 0), period_text, font=text_font)
        status_bbox = draw.textbbox((0, 0), status_text, font=small_font)
        
        # Left-aligned positions
        margin_left = 40
        title_x = margin_left
        main_x = margin_left + 20
        period_x = margin_left + 20
        status_x = margin_left + 20
        
        # Vertical positions optimized for 2.3" height
        title_y = 30
        main_y = 90
        period_y = 140
        status_y = 180
        
        # Draw main content
        draw.text((title_x, title_y), title_text, fill='#000080', font=title_font)  # Navy blue
        draw.text((main_x, main_y), main_text, fill='#666666', font=subtitle_font)
        draw.text((period_x, period_y), period_text, fill='#0066CC', font=text_font)
        draw.text((status_x, status_y), status_text, fill='#999999', font=small_font)
        
        # Add professional border
        border_color = '#CCCCCC'
        draw.rectangle([10, 10, width-10, height-10], outline=border_color, width=3)
        
        # Add header separator line
        draw.line([20, 75, width-20, 75], fill='#CCCCCC', width=2)
        
        # Add icon area
        icon_area_x = width - 200
        icon_area_y = 30
        draw.rectangle([icon_area_x, icon_area_y, icon_area_x + 150, icon_area_y + 100], 
                      outline='#E0E0E0', width=1, fill='#F8F8F8')
        
        # Add "NO DATA" text in icon area
        no_data_font = ImageFont.truetype("arial.ttf", 24) if title_font != ImageFont.load_default() else ImageFont.load_default()
        draw.text((icon_area_x + 20, icon_area_y + 40), "NO DATA", fill='#CCCCCC', font=no_data_font)
        
        # Save image
        img.save(output_path, 'PNG', dpi=(200, 200))
        print(f"Created incident table placeholder (8\" x 2.3\"): {output_path}")
        
        return True
        
    except Exception as e:
        print(f"Error creating incident table placeholder: {e}")
        return False

def get_7day_incident_details(crime_type, target_date):
    """Extract detailed incident information for 7-day period"""
    incidents = []
    
    try:
        # Get Excel-based 7-day period dates
        start_date, end_date = get_7day_period_dates(target_date)
        
        if not start_date or not end_date:
            print(f"Could not determine Excel 7-day period for {target_date}")
            return incidents
            
        print(f"Getting incident details for period: {start_date} to {end_date}")
        
        # Load ArcGIS Pro project
        aprx = arcpy.mp.ArcGISProject(APR_PATH)
        maps = aprx.listMaps()
        
        if not maps:
            print(f"No maps found in project")
            return incidents
            
        map_obj = maps[0]
        
        # Find the 7-Day layer
        layer_name = f"{crime_type} 7-Day"
        target_layer = None
        
        for lyr in map_obj.listLayers():
            if lyr.name == layer_name:
                target_layer = lyr
                break
        
        if not target_layer:
            print(f"7-Day layer not found: {layer_name}")
            return incidents
        
        # Build SQL filter for 7-day period
        from map_export import build_sql_filter_7day_excel
        filter_sql = build_sql_filter_7day_excel(crime_type, start_date, end_date)
        
        if filter_sql:
            # Apply the filter temporarily
            original_query = target_layer.definitionQuery
            target_layer.definitionQuery = filter_sql
            
            try:
                # Define fields to extract
                fields = ["calldate", "fulladdr", "calltype", "disposition", "SHAPE@XY"]
                
                with arcpy.da.SearchCursor(target_layer, fields) as cursor:
                    for row in cursor:
                        try:
                            calldate = row[0]
                            fulladdr = row[1] if row[1] else ""
                            calltype = row[2] if row[2] else "Unknown"
                            disposition = row[3] if row[3] else "Unknown"
                            coordinates = row[4] if row[4] else (0, 0)
                            
                            # Format address or use coordinates
                            if fulladdr:
                                formatted_block = fulladdr[:50]  # Truncate long addresses
                            else:
                                formatted_block = f"COORDINATES: {coordinates[0]:.0f}, {coordinates[1]:.0f}"
                            
                            if isinstance(calldate, datetime):
                                incident = {
                                    'block': formatted_block,
                                    'incident_date': calldate.strftime('%m/%d/%y'),
                                    'day_of_week': calldate.strftime('%A'),
                                    'time_period': get_time_period_from_hour(calldate.hour),
                                    'time_of_day': calldate.strftime('%H:%M'),
                                    'raw_datetime': calldate,
                                    'vehicle_description': '[MANUAL ENTRY]',
                                    'suspect_description': '[MANUAL ENTRY]',
                                    'narrative_summary': '[MANUAL ENTRY]'
                                }
                                
                                incidents.append(incident)
                                
                        except Exception as e:
                            print(f"  Error processing incident record: {e}")
                            continue
                
                # Restore original query
                target_layer.definitionQuery = original_query
                
                # Sort incidents by date/time
                incidents.sort(key=lambda x: x['raw_datetime'])
                
                print(f"Extracted {len(incidents)} incident details for {crime_type}")
                
            except Exception as e:
                print(f"Error extracting incident details: {e}")
                
        # Clean up project reference
        del aprx
        
    except Exception as e:
        print(f"Error accessing incident data for {crime_type}: {e}")
    
    return incidents

def create_incident_table_with_data(crime_type, incidents_data, output_path, start_date=None, end_date=None):
    """
    Create incident table image with actual data for PowerPoint insertion
    Dimensions: 8" x 2.3" at 200 DPI = 1600 x 460 pixels
    """
    try:
        width = 1600
        height = 460
        
        # Create white background
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Font setup
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            header_font = ImageFont.truetype("arial.ttf", 14)
            cell_font = ImageFont.truetype("arial.ttf", 12)
            small_font = ImageFont.truetype("arial.ttf", 10)
        except:
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            cell_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Colors
        header_bg = '#E6E6FA'  # Light lavender
        border_color = '#000080'  # Navy blue
        text_color = '#000000'
        alt_row_color = '#F8F8FF'  # Ghost white
        
        # Title area
        title_text = f"Pattern Offenders/Suspects - {crime_type}"
        if start_date and end_date:
            period_text = f"Period: {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"
        else:
            period_text = "7-Day Analysis Period"
        
        # Draw title and period
        draw.text((20, 10), title_text, fill=border_color, font=title_font)
        draw.text((20, 40), period_text, fill='#666666', font=small_font)
        
        # Table setup
        table_start_y = 70
        table_height = height - table_start_y - 20
        
        # Column definitions (optimized for 8" width)
        columns = [
            {'name': 'Date', 'width': 120, 'align': 'center'},
            {'name': 'Day', 'width': 100, 'align': 'center'},
            {'name': 'Time', 'width': 80, 'align': 'center'},
            {'name': 'Block', 'width': 200, 'align': 'left'},
            {'name': 'Vehicle', 'width': 300, 'align': 'left'},
            {'name': 'Suspect', 'width': 300, 'align': 'left'},
            {'name': 'Summary', 'width': 480, 'align': 'left'}
        ]
        
        # Calculate starting positions
        current_x = 20
        for col in columns:
            col['start_x'] = current_x
            current_x += col['width']
        
        # Draw table header
        header_y = table_start_y
        header_height = 30
        
        # Header background
        draw.rectangle([20, header_y, width-20, header_y + header_height], 
                      fill=header_bg, outline=border_color, width=2)
        
        # Header text
        for col in columns:
            text_x = col['start_x'] + 5
            if col['align'] == 'center':
                text_bbox = draw.textbbox((0, 0), col['name'], font=header_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_x = col['start_x'] + (col['width'] - text_width) // 2
            
            draw.text((text_x, header_y + 8), col['name'], fill=text_color, font=header_font)
        
        # Draw column separators in header
        for i, col in enumerate(columns[:-1]):
            line_x = col['start_x'] + col['width']
            draw.line([line_x, header_y, line_x, header_y + header_height], 
                     fill=border_color, width=1)
        
        # Draw data rows
        row_height = 25
        max_rows = min(len(incidents_data), (table_height - header_height) // row_height)
        
        for i, incident in enumerate(incidents_data[:max_rows]):
            row_y = header_y + header_height + (i * row_height)
            
            # Alternate row background
            if i % 2 == 1:
                draw.rectangle([20, row_y, width-20, row_y + row_height], 
                              fill=alt_row_color, outline=None)
            
            # Draw row data
            row_data = [
                incident.get('incident_date', ''),
                incident.get('day_of_week', '')[:3],  # Abbreviate day
                incident.get('time_of_day', ''),
                incident.get('block', '')[:25] + ('...' if len(incident.get('block', '')) > 25 else ''),
                incident.get('vehicle_description', '')[:35] + ('...' if len(incident.get('vehicle_description', '')) > 35 else ''),
                incident.get('suspect_description', '')[:35] + ('...' if len(incident.get('suspect_description', '')) > 35 else ''),
                incident.get('narrative_summary', '')[:55] + ('...' if len(incident.get('narrative_summary', '')) > 55 else '')
            ]
            
            for j, (col, data) in enumerate(zip(columns, row_data)):
                text_x = col['start_x'] + 5
                if col['align'] == 'center':
                    text_bbox = draw.textbbox((0, 0), data, font=cell_font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_x = col['start_x'] + (col['width'] - text_width) // 2
                
                draw.text((text_x, row_y + 5), data, fill=text_color, font=cell_font)
            
            # Draw bottom border for row
            draw.line([20, row_y + row_height, width-20, row_y + row_height], 
                     fill='#DDDDDD', width=1)
        
        # Draw column separators for data rows
        for col in columns[:-1]:
            line_x = col['start_x'] + col['width']
            draw.line([line_x, header_y + header_height, line_x, header_y + header_height + (max_rows * row_height)], 
                     fill='#DDDDDD', width=1)
        
        # Draw table border
        table_bottom = header_y + header_height + (max_rows * row_height)
        draw.rectangle([20, header_y, width-20, table_bottom], 
                      fill=None, outline=border_color, width=2)
        
        # Add note if there are more incidents than can fit
        if len(incidents_data) > max_rows:
            note_text = f"Showing {max_rows} of {len(incidents_data)} incidents - See CSV for complete list"
            draw.text((20, table_bottom + 10), note_text, fill='#666666', font=small_font)
        
        # Save image
        img.save(output_path, 'PNG', dpi=(200, 200))
        print(f"Created incident table image (8\" x 2.3\") with {len(incidents_data)} incidents: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"Error creating incident table image: {e}")
        return False

def export_incident_table_data_with_autofit(crime_type, target_date):
    """Export incident table data for Pattern Offenders/Suspects section"""
    try:
        # Get date string for folder naming
        date_str = target_date.strftime("%Y_%m_%d")
        
        # Get crime-specific output folder
        crime_output_folder = get_crime_type_folder(crime_type, date_str)
        os.makedirs(crime_output_folder, exist_ok=True)
        
        # Get standardized filename prefix
        filename_prefix = get_standardized_filename(crime_type)
        
        print(f"\nProcessing incident table for {crime_type}")
        
        # Get incident details
        incidents = get_7day_incident_details(crime_type, target_date)
        
        # Get 7-day period dates for placeholders
        start_date, end_date = get_7day_period_dates(target_date)
        
        if len(incidents) == 0:
            # Create placeholder for no incidents
            placeholder_path = os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable_Placeholder.png")
            success = create_incident_table_placeholder(crime_type, placeholder_path, start_date, end_date)
            
            print(f"No incidents found for {crime_type}, created placeholder")
            return success
        
        else:
            # Create incident table with data
            table_path = os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable_AutoFit.png")
            success = create_incident_table_with_data(crime_type, incidents, table_path, start_date, end_date)
            
            # Also export incident data to CSV for manual completion
            try:
                import pandas as pd
                
                csv_data = []
                for incident in incidents:
                    csv_data.append({
                        'Block': incident['block'],
                        'Incident_Date': incident['incident_date'],
                        'Day_of_Week': incident['day_of_week'],
                        'Time_Period': incident['time_period'],
                        'Time_of_Day': incident['time_of_day'],
                        'Vehicle_Description': incident['vehicle_description'],
                        'Suspect_Description': incident['suspect_description'],
                        'Narrative_Summary': incident['narrative_summary']
                    })
                
                df = pd.DataFrame(csv_data)
                csv_path = os.path.join(crime_output_folder, f"{filename_prefix}_Incidents_Manual_Entry.csv")
                df.to_csv(csv_path, index=False)
                
                print(f"Incident data exported to: {csv_path}")
                print(f"{len(incidents)} incidents need manual narrative entry")
                
            except ImportError:
                print("Pandas not available - CSV export skipped")
            except Exception as e:
                print(f"CSV export failed: {e}")
            
            return success
        
    except Exception as e:
        print(f"Error exporting incident table data for {crime_type}: {e}")
        return False