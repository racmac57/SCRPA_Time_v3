# 🕒 2025-06-22-01-30-00
# Police_Data_Analysis/incident_table_fixed_styling
# Author: R. A. Carucci
# Purpose: Fix incident table placeholder styling to match map placeholder

def create_incident_table_placeholder(crime_type, output_path, start_date=None, end_date=None):
    """
    Create placeholder image for Pattern Offenders/Suspects section - MAP STYLE
    Dimensions: 8" x 2.3" at 200 DPI = 1600 x 460 pixels
    
    Args:
        crime_type (str): Name of crime type
        output_path (str): Path to save the placeholder image
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
        
        # Font setup - horizontal layout optimized
        try:
            title_font = ImageFont.truetype("arial.ttf", 32)
            subtitle_font = ImageFont.truetype("arial.ttf", 24)
            text_font = ImageFont.truetype("arial.ttf", 20)
            period_font = ImageFont.truetype("arial.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            period_font = ImageFont.load_default()
        
        # Text content
        title_text = "Pattern Offenders/Suspects"
        main_text = f"No {crime_type} incidents recorded during 7-day period"
        
        # Add period information if available
        if start_date and end_date:
            period_text = f"Analysis Period: {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"
        else:
            period_text = "7-Day Analysis Period"
        
        status_text = "No pattern analysis available - Continue monitoring for emerging trends"
        
        # Calculate positions for horizontal layout (LEFT-ALIGNED like map)
        margin_left = 40
        title_x = margin_left
        main_x = margin_left + 20  # Slight indent
        period_x = margin_left + 20
        status_x = margin_left + 20
        
        # Vertical positions optimized for 2.3" height
        title_y = 40
        main_y = 100
        period_y = 150
        status_y = 190
        
        # Draw main content (SAME STYLE AS MAP PLACEHOLDER)
        draw.text((title_x, title_y), title_text, fill='#000080', font=title_font)  # Navy blue header
        draw.text((main_x, main_y), main_text, fill='#666666', font=subtitle_font)
        draw.text((period_x, period_y), period_text, fill='#0066CC', font=text_font)
        draw.text((status_x, status_y), status_text, fill='#999999', font=period_font)
        
        # SIMPLE BORDER (like map placeholder) - NO VERTICAL LINES
        border_color = '#CCCCCC'
        draw.rectangle([10, 10, width-10, height-10], outline=border_color, width=2)
        
        # Header separator line (single line only)
        draw.line([30, 85, width-30, 85], fill='#CCCCCC', width=1)
        
        # Save image
        img.save(output_path, 'PNG', dpi=(200, 200))
        print(f"✅ Created incident table placeholder (map style, 8\" x 2.3\"): {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating incident table placeholder: {e}")
        return False