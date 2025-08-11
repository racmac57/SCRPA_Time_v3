# 🕒 2025-06-22-22-45-00
# SCRPA_Place_and_Time/script_analysis_updates
# Author: R. A. Carucci
# Purpose: Analysis of provided scripts and required updates for full integration

## 📋 **SCRIPT ANALYSIS**

### **✅ GOOD UPDATES MADE:**
- **Block M code integration** in `incident_table_automation.py`
- **City boundaries extent calculation** in `map_export.py`
- **PowerPoint assembly framework** in `main.py`
- **Enhanced error handling** and logging

### **❌ CRITICAL MISSING INTEGRATIONS:**

---

## 🔧 **REQUIRED UPDATES**

### **1. main.py - Missing Key Integrations**

#### **Missing Imports & Functions:**
```python
# ADD THESE IMPORTS
import sys
import glob
from pathlib import Path
from datetime import date
from config import (
    CRIME_FOLDER_MAPPING, 
    get_crime_type_folder, 
    get_standardized_filename,
    REPORT_BASE_DIR,
    CRIME_TYPES
)

# ADD THIS HELPER FUNCTION
def get_date_string():
    """Helper to get current date string"""
    return date.today().strftime("%Y_%m_%d")

# REPLACE YOUR auto_assemble_powerpoint_final FUNCTION WITH:
def auto_assemble_powerpoint_final(output_folder, crime_types):
    """
    Final PowerPoint assembly - overlays new images on existing template
    Works with your exact folder structure and file naming
    """
    try:
        from pptx import Presentation
        from pptx.util import Inches
        
        # Find PowerPoint file in the main output folder
        ppt_files = glob.glob(os.path.join(output_folder, "*.pptx"))
        if not ppt_files:
            logging.error("❌ No PowerPoint file found")
            return False
            
        prs = Presentation(ppt_files[0])
        logging.info(f"✅ Loaded PowerPoint: {os.path.basename(ppt_files[0])}")
        
        for i, crime_type in enumerate(crime_types):
            if i >= len(prs.slides):
                continue
                
            slide = prs.slides[i]
            
            # Use your exact folder structure
            date_str = get_date_string()
            crime_output_folder = get_crime_type_folder(crime_type, date_str)
            filename_prefix = get_standardized_filename(crime_type)
            
            logging.info(f"📊 Processing slide {i+1}: {crime_type}")
            
            # EXACT POSITIONING (adjust these based on your template layout)
            chart_left = Inches(0.5)    # Left side
            chart_top = Inches(2.8)     # Below title
            chart_width = Inches(5.84)  # Your specified width
            chart_height = Inches(4.00) # Your specified height
            
            map_left = Inches(6.8)      # Right side
            map_top = Inches(2.8)       # Same level as chart
            map_width = Inches(5.60)    # Your specified width
            map_height = Inches(4.03)   # Your specified height
            
            table_left = Inches(6.8)    # Right side, aligned with map
            table_top = Inches(0.8)     # Top area under Pattern Offenders/Suspects
            table_width = Inches(8.33)  # Your specified width
            table_height = Inches(1.98) # Your specified height
            
            # Add chart
            chart_path = os.path.join(crime_output_folder, f"{filename_prefix}_Chart.png")
            if os.path.exists(chart_path):
                slide.shapes.add_picture(
                    chart_path, chart_left, chart_top, chart_width, chart_height
                )
                logging.info(f"  ✅ Added chart: {filename_prefix}_Chart.png")
            
            # Add map
            map_path = os.path.join(crime_output_folder, f"{filename_prefix}_Map.png")
            if os.path.exists(map_path):
                slide.shapes.add_picture(
                    map_path, map_left, map_top, map_width, map_height
                )
                logging.info(f"  ✅ Added map: {filename_prefix}_Map.png")
            else:
                # Try placeholder
                placeholder_path = os.path.join(crime_output_folder, f"{filename_prefix}_Map_Placeholder.png")
                if os.path.exists(placeholder_path):
                    slide.shapes.add_picture(
                        placeholder_path, map_left, map_top, map_width, map_height
                    )
                    logging.info(f"  ✅ Added map placeholder")
            
            # Add incident table
            table_paths = [
                os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable_AutoFit.png"),
                os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable_Placeholder.png")
            ]
            
            for table_path in table_paths:
                if os.path.exists(table_path):
                    slide.shapes.add_picture(
                        table_path, table_left, table_top, table_width, table_height
                    )
                    logging.info(f"  ✅ Added incident table: {os.path.basename(table_path)}")
                    break
        
        # Save updated presentation
        prs.save(ppt_files[0])
        logging.info(f"✅ PowerPoint assembly completed: {os.path.basename(ppt_files[0])}")
        return True
        
    except Exception as e:
        logging.error(f"❌ PowerPoint assembly failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# UPDATE YOUR MAIN FUNCTION TO CALL POWERPOINT ASSEMBLY
def main_with_powerpoint_assembly(report_date_str):
    """
    Updated main function that includes PowerPoint assembly
    """
    try:
        report_date = datetime.strptime(report_date_str, "%Y_%m_%d").date()
        
        # Get output folder using your existing logic
        output_folder = get_output_folder(report_date_str)  # From your config
        
        # YOUR EXISTING PROCESSING CODE HERE
        # ... (map exports, chart exports, incident tables) ...
        
        # After all processing is complete
        all_processing_complete = True  # Set based on your actual results
        
        if all_processing_complete:
            logging.info("\n🎯 ASSEMBLING POWERPOINT PRESENTATION")
            logging.info("=" * 50)
            
            powerpoint_success = auto_assemble_powerpoint_final(output_folder, CRIME_TYPES)
            
            if powerpoint_success:
                logging.info("✅ PowerPoint assembly completed successfully!")
            else:
                logging.error("❌ PowerPoint assembly failed - manual assembly required")
        
    except Exception as e:
        logging.error(f"❌ Main function failed: {e}")
```

---

### **2. map_export.py - Missing Core Integration**

#### **Critical Missing Function:**
```python
# ADD THIS TO INTEGRATE WITH YOUR EXISTING export_maps FUNCTION
def export_maps_enhanced_integration(crime_type, output_folder, args):
    """
    Integration with your existing export_maps function
    ADD THIS CALL TO YOUR EXISTING export_maps FUNCTION
    """
    try:
        # YOUR EXISTING CODE UNTIL YOU HAVE:
        # - target_layer (the 7-Day layer)
        # - map_frame (the layout map frame) 
        # - map_obj (the map object)
        
        # THEN ADD THIS CALL:
        if target_layer and map_frame and map_obj:
            # Apply the enhanced extent calculation
            calculate_optimal_map_extent_with_city_bounds(target_layer, map_frame, map_obj)
            
            # Continue with your existing symbology and export logic
            # ... rest of your existing export_maps code ...
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Enhanced map export failed: {e}")
        return False

# UPDATE YOUR CONFIG TO INCLUDE
CITY_BOUNDARIES_LAYER_NAME = "City Boundaries"  # Add this to config.py
```

---

### **3. incident_table_automation.py - Missing Functions**

#### **Missing Key Functions:**
```python
# ADD THESE MISSING FUNCTIONS

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

def export_incident_table_data_with_autofit(crime_type, target_date):
    """
    Main export function that creates incident tables or placeholders
    CALL THIS FROM YOUR MAIN PROCESSING LOOP
    """
    try:
        # Get incidents using the enhanced function
        incidents = get_7day_incident_details_enhanced(crime_type, target_date)
        
        # Get output paths
        date_str = target_date.strftime("%Y_%m_%d")
        crime_output_folder = get_crime_type_folder(crime_type, date_str)
        filename_prefix = get_standardized_filename(crime_type)
        
        if len(incidents) == 0:
            # Create placeholder for no incidents
            placeholder_path = os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable_Placeholder.png")
            return create_incident_table_placeholder(crime_type, placeholder_path)
        else:
            # Create table with data
            table_path = os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable_AutoFit.png")
            return create_incident_table_image_with_data(crime_type, incidents, table_path)
            
    except Exception as e:
        logging.error(f"❌ Incident table export failed for {crime_type}: {e}")
        return False

def create_incident_table_placeholder(crime_type, output_path):
    """Create placeholder image for zero incidents"""
    # YOUR EXISTING PLACEHOLDER CREATION CODE HERE
    pass

def create_incident_table_image_with_data(crime_type, incidents_data, output_path):
    """Create table image with actual incident data"""
    # IMPLEMENT TABLE IMAGE CREATION HERE
    pass

# FIX THE EXTRACT_STREET_FROM_ADDRESS IMPORT
def extract_street_from_address(address):
    """Extract street name when no number is available"""
    import re
    
    if not address:
        return "UNKNOWN LOCATION"
        
    cleaned = re.sub(r'^(THE\s+|A\s+)', '', address.upper().strip())
    parts = cleaned.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]} AREA"
    elif len(parts) == 1:
        return f"{parts[0]} AREA"
    else:
        return "UNKNOWN LOCATION"
```

---

## 🔧 **CONFIG.PY UPDATES NEEDED**

```python
# ADD THESE TO YOUR config.py
CITY_BOUNDARIES_LAYER_NAME = "City Boundaries"

# PowerPoint positioning coordinates
POWERPOINT_COORDINATES = {
    'chart': {'left': 0.5, 'top': 2.8, 'width': 5.84, 'height': 4.00},
    'map': {'left': 6.8, 'top': 2.8, 'width': 5.60, 'height': 4.03},
    'table': {'left': 6.8, 'top': 0.8, 'width': 8.33, 'height': 1.98}
}
```

---

## 📋 **INTEGRATION CHECKLIST**

### **✅ COMPLETED:**
- Block M code integration
- Basic PowerPoint assembly framework
- Enhanced extent calculation logic

### **❌ STILL NEEDED:**
1. **Copy your `extract_block_from_address.py`** to the scripts folder
2. **Update main.py** with the corrected PowerPoint assembly function
3. **Add extent calculation call** to your existing `export_maps` function
4. **Add missing functions** to `incident_table_automation.py`
5. **Update config.py** with new constants
6. **Test integration** with your existing processing pipeline

---

## 🎯 **NEXT STEPS**

1. **Apply the updates above** to your scripts
2. **Test with your working date** (like `2025_05_07`)
3. **Verify PowerPoint positioning** - may need coordinate adjustments
4. **Check Block M code output** in CSV files

**The scripts have good foundations but need these integrations to work with your existing system!**