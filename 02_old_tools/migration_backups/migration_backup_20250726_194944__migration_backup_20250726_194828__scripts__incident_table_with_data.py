# 🕒 2025-06-22-00-55-00
# Police_Data_Analysis/incident_table_with_data
# Author: R. A. Carucci
# Purpose: Generate incident table images for PowerPoint insertion (8" x 2.3")

from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import os

def create_incident_table_image_with_data(crime_type, incidents_data, output_path, start_date=None, end_date=None):
    """
    Create incident table image with actual data for PowerPoint insertion
    Dimensions: 8" x 2.3" at 200 DPI = 1600 x 460 pixels
    
    Args:
        crime_type (str): Name of crime type
        incidents_data (list): List of incident dictionaries
        output_path (str): Path to save the image
        start_date (date): Start date of 7-day period
        end_date (date): End date of 7-day period
        
    Returns:
        bool: True if successful
    """
    try:
        # Image dimensions matching PowerPoint shape: 8" x 2.3" at 200 DPI
        width = 1600  # 8 inches * 200 DPI
        height = 460  # 2.3 inches * 200 DPI
        
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
        for i, col in enumerate(columns[:-1]):  # Don't draw line after last column
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
                incident.get('block', '')[:25] + ('...' if len(incident.get('block', '')) > 25 else ''),  # Truncate long blocks
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
        print(f"✅ Created incident table image (8\" x 2.3\") with {len(incidents_data)} incidents: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating incident table image: {e}")
        return False

def create_incident_summary_image(crime_type, incidents_data, output_path, start_date=None, end_date=None):
    """
    Create a summary image when there are too many incidents for detailed table
    
    Args:
        crime_type (str): Name of crime type
        incidents_data (list): List of incident dictionaries
        output_path (str): Path to save the image
        start_date (date): Start date of 7-day period
        end_date (date): End date of 7-day period
        
    Returns:
        bool: True if successful
    """
    try:
        # Image dimensions matching PowerPoint shape: 8" x 2.3" at 200 DPI
        width = 1600  # 8 inches * 200 DPI
        height = 460  # 2.3 inches * 200 DPI
        
        # Create white background
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Font setup
        try:
            title_font = ImageFont.truetype("arial.ttf", 28)
            subtitle_font = ImageFont.truetype("arial.ttf", 22)
            text_font = ImageFont.truetype("arial.ttf", 18)
            small_font = ImageFont.truetype("arial.ttf", 14)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Title
        title_text = f"Pattern Offenders/Suspects - {crime_type}"
        if start_date and end_date:
            period_text = f"Period: {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"
        else:
            period_text = "7-Day Analysis Period"
        
        # Summary statistics
        total_incidents = len(incidents_data)
        
        # Time period breakdown
        time_breakdown = {}
        for incident in incidents_data:
            time_period = incident.get('time_period', 'Unknown')
            time_breakdown[time_period] = time_breakdown.get(time_period, 0) + 1
        
        # Most common time period
        if time_breakdown:
            most_common_time = max(time_breakdown, key=time_breakdown.get)
            most_common_count = time_breakdown[most_common_time]
        else:
            most_common_time = "Unknown"
            most_common_count = 0
        
        # Draw content
        margin_left = 40
        
        # Title and header info
        draw.text((margin_left, 20), title_text, fill='#000080', font=title_font)
        draw.text((margin_left, 60), period_text, fill='#666666', font=text_font)
        
        # Summary statistics
        summary_y = 120
        summary_text = f"Total Incidents: {total_incidents}"
        draw.text((margin_left, summary_y), summary_text, fill='#000000', font=subtitle_font)
        
        if most_common_time != "Unknown":
            pattern_text = f"Most Common Time: {most_common_time} ({most_common_count} incidents)"
            draw.text((margin_left, summary_y + 40), pattern_text, fill='#000000', font=text_font)
        
        # Time breakdown
        breakdown_x = margin_left + 500
        breakdown_y = 120
        draw.text((breakdown_x, breakdown_y), "Time Distribution:", fill='#000080', font=text_font)
        
        for i, (time_period, count) in enumerate(sorted(time_breakdown.items())):
            if count > 0:
                breakdown_text = f"• {time_period}: {count}"
                draw.text((breakdown_x, breakdown_y + 30 + (i * 25)), breakdown_text, fill='#000000', font=small_font)
        
        # Note about detailed data
        note_text = f"See {crime_type}_Incidents_Manual_Entry.csv for detailed incident information"
        draw.text((margin_left, height - 60), note_text, fill='#666666', font=small_font)
        
        # Professional border
        border_color = '#000080'
        draw.rectangle([10, 10, width-10, height-10], outline=border_color, width=3)
        
        # Header separator
        draw.line([20, 100, width-20, 100], fill='#CCCCCC', width=2)
        
        # Save image
        img.save(output_path, 'PNG', dpi=(200, 200))
        print(f"✅ Created incident summary image (8\" x 2.3\") for {total_incidents} incidents: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating incident summary image: {e}")
        return False