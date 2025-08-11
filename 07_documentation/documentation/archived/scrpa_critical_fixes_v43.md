# 🕒 2025-06-21-23-30-00
# Police_Data_Analysis/scrpa_critical_fixes_v43
# Author: R. A. Carucci
# Purpose: Critical fixes for database field issues, PowerPoint template problems, and symbology visibility

## 🚨 **Critical Issues Identified**

### **1. Database Schema Issue**
**Problem**: Missing 'block' field causing incident table failures
```
❌ Error extracting incident details: The field block was not found
```

### **2. PowerPoint Template Problems**
**Issues**:
- Old chart style (legend not upper-left)
- Map shows all three periods (7-Day, 28-Day, YTD) instead of 7-Day only
- No placeholders being inserted

### **3. Symbology Visibility**
**Problem**: MV Theft and Robbery maps have no visible symbology despite data

---

## 🔧 **Priority Fix 1: Database Field Correction**

### **Update incident_table_automation.py**

Replace the field extraction section:

```python
def get_7day_incident_details(crime_type, target_date):
    """Extract detailed incident information for 7-day period - FIXED FIELDS"""
    incidents = []
    
    try:
        # Get Excel-based 7-day period dates
        start_date, end_date = get_7day_period_dates(target_date)
        
        if not start_date or not end_date:
            print(f"❌ Could not determine Excel 7-day period for {target_date}")
            return incidents
            
        print(f"📅 Getting incident details for period: {start_date} to {end_date}")
        
        # Load ArcGIS Pro project
        aprx = arcpy.mp.ArcGISProject(APR_PATH)
        maps = aprx.listMaps()
        
        if not maps:
            print(f"❌ No maps found in project")
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
            print(f"❌ 7-Day layer not found: {layer_name}")
            return incidents
        
        # FIRST: Inspect available fields
        print(f"🔍 Available fields in {layer_name}:")
        field_names = [field.name for field in target_layer.getDefinition().getFieldDefinitions()]
        for field_name in field_names:
            print(f"  - {field_name}")
        
        # Build SQL filter for 7-day period
        from map_export import build_sql_filter_7day_excel
        filter_sql = build_sql_filter_7day_excel(crime_type, start_date, end_date)
        
        if filter_sql:
            # Apply the filter temporarily
            original_query = target_layer.definitionQuery
            target_layer.definitionQuery = filter_sql
            
            # Extract incident details with CORRECTED field names
            try:
                # UPDATED: Use actual field names from your database
                available_fields = [field.name for field in arcpy.ListFields(target_layer)]
                print(f"🔍 Actual available fields: {available_fields}")
                
                # Define fields with fallbacks
                field_mapping = {
                    'calldate': 'calldate',
                    'location': None,  # Will be determined dynamically
                    'calltype': 'calltype', 
                    'disposition': 'disposition'
                }
                
                # Find location field (try common variations)
                location_candidates = ['block', 'location', 'address', 'incident_location', 'loc', 'addr']
                for candidate in location_candidates:
                    if candidate.lower() in [f.lower() for f in available_fields]:
                        field_mapping['location'] = candidate
                        print(f"✅ Using location field: {candidate}")
                        break
                
                if not field_mapping['location']:
                    print("⚠️ No location field found, using coordinates")
                    field_mapping['location'] = 'SHAPE@'  # Use geometry
                
                # Build fields list for cursor
                fields_to_extract = [
                    field_mapping['calldate'],
                    field_mapping['location'], 
                    field_mapping['calltype'],
                    field_mapping['disposition']
                ]
                
                print(f"🔍 Extracting fields: {fields_to_extract}")
                
                with arcpy.da.SearchCursor(target_layer, fields_to_extract) as cursor:
                    for row in cursor:
                        try:
                            calldate = row[0]
                            location_data = row[1]
                            calltype = row[2] if row[2] else "Unknown"
                            disposition = row[3] if row[3] else "Unknown"
                            
                            # Handle location data
                            if field_mapping['location'] == 'SHAPE@':
                                # Convert geometry to readable location
                                if location_data:
                                    location_str = f"Lat: {location_data.centroid.Y:.4f}, Lon: {location_data.centroid.X:.4f}"
                                else:
                                    location_str = "Location Unknown"
                            else:
                                location_str = location_data if location_data else "Location Unknown"
                            
                            if isinstance(calldate, datetime):
                                # Format the incident details
                                incident = {
                                    'block': location_str,  # Using whatever location field we found
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
                                print(f"✅ Processed incident: {calldate.strftime('%m/%d %H:%M')} at {location_str}")
                                
                        except Exception as e:
                            print(f"  ⚠️ Error processing incident record: {e}")
                            continue
                
                # Restore original query
                target_layer.definitionQuery = original_query
                
                # Sort incidents by date/time
                incidents.sort(key=lambda x: x['raw_datetime'])
                
                print(f"✅ Extracted {len(incidents)} incident details for {crime_type}")
                
            except Exception as e:
                print(f"❌ Error extracting incident details: {e}")
                # Restore query even if error occurs
                try:
                    target_layer.definitionQuery = original_query
                except:
                    pass
                
        # Clean up project reference
        del aprx
        
    except Exception as e:
        print(f"❌ Error accessing incident data for {crime_type}: {e}")
    
    return incidents
```

---

## 🔧 **Priority Fix 2: PowerPoint Template Issues**

### **A. Update PowerPoint Template**

1. **Open PowerPoint Template:**
   ```
   C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\7_Day_Templet_SCRPA_Time\SCRPA_REPORT.pptx
   ```

2. **Fix Map Placeholder:**
   - Click on map placeholder
   - In ArcGIS Pro: Right-click map → Properties → Definition Query
   - Set to show **ONLY 7-Day layers**
   - Remove 28-Day and YTD layer visibility

3. **Update Chart Placeholders:**
   - Charts should reference exported files (not live data)
   - Set placeholder to load from: `[Crime]_Chart.png`

### **B. Manual PowerPoint Assembly Script**

Create `powerpoint_assembly.py`:

```python
# 🕒 2025-06-21-23-30-00
# Police_Data_Analysis/powerpoint_assembly
# Author: R. A. Carucci
# Purpose: Automate PowerPoint slide assembly from generated files

from pptx import Presentation
from pptx.util import Inches
import os
from config import CRIME_FOLDER_MAPPING, get_correct_folder_name, REPORT_BASE_DIR

def assemble_powerpoint_slides(target_date):
    """
    Assemble PowerPoint slides with generated charts, maps, and incident tables
    """
    try:
        # Get folder structure
        folder_name = get_correct_folder_name(target_date)
        base_folder = os.path.join(REPORT_BASE_DIR, folder_name)
        ppt_path = os.path.join(base_folder, f"{folder_name}.pptx")
        
        print(f"📊 Assembling PowerPoint: {ppt_path}")
        
        # Load presentation
        prs = Presentation(ppt_path)
        
        # Process each crime type
        for i, (crime_type, folder_name_mapping) in enumerate(CRIME_FOLDER_MAPPING.items()):
            if i < len(prs.slides):
                slide = prs.slides[i]
                crime_folder = os.path.join(base_folder, folder_name_mapping)
                
                print(f"🔄 Processing slide {i+1}: {crime_type}")
                
                # Insert chart (if exists)
                chart_file = os.path.join(crime_folder, f"{folder_name_mapping}_Chart.png")
                if os.path.exists(chart_file):
                    # Remove old chart placeholder and insert new
                    insert_image_to_slide(slide, chart_file, "chart")
                    print(f"  ✅ Inserted chart: {os.path.basename(chart_file)}")
                
                # Insert map (if exists)
                map_file = os.path.join(crime_folder, f"{folder_name_mapping}_Map.png")
                if os.path.exists(map_file):
                    insert_image_to_slide(slide, map_file, "map")
                    print(f"  ✅ Inserted map: {os.path.basename(map_file)}")
                
                # Insert incident table/placeholder
                incident_files = [
                    os.path.join(crime_folder, f"{folder_name_mapping}_Incidents_Placeholder.png"),
                    os.path.join(crime_folder, f"{folder_name_mapping}_Incidents_Table.png")
                ]
                
                for incident_file in incident_files:
                    if os.path.exists(incident_file):
                        insert_image_to_slide(slide, incident_file, "incident")
                        print(f"  ✅ Inserted incident table: {os.path.basename(incident_file)}")
                        break
        
        # Save updated presentation
        prs.save(ppt_path)
        print(f"✅ PowerPoint assembly completed: {ppt_path}")
        return True
        
    except Exception as e:
        print(f"❌ PowerPoint assembly failed: {e}")
        return False

def insert_image_to_slide(slide, image_path, image_type):
    """Insert image to appropriate location on slide"""
    try:
        if image_type == "chart":
            # Chart position: left side
            left = Inches(0.5)
            top = Inches(2)
            width = Inches(6)
            height = Inches(4)
        elif image_type == "map":
            # Map position: right side  
            left = Inches(7)
            top = Inches(2)
            width = Inches(6)
            height = Inches(4)
        elif image_type == "incident":
            # Incident table: bottom (replacing Pattern Offenders section)
            left = Inches(0.5)
            top = Inches(6.5)
            width = Inches(12)
            height = Inches(2)
        
        # Add image to slide
        slide.shapes.add_picture(image_path, left, top, width, height)
        return True
        
    except Exception as e:
        print(f"❌ Error inserting {image_type} image: {e}")
        return False

if __name__ == "__main__":
    from datetime import date
    test_date = date(2025, 6, 10)
    assemble_powerpoint_slides(test_date)
```

---

## 🔧 **Priority Fix 3: Symbology Visibility**

### **Enhanced Symbology Function**

Update map_export.py with this improved version:

```python
def apply_symbology_enhanced(layer, layer_name):
    """
    Apply ENHANCED symbology with FORCED visibility for crime incident layers
    """
    try:
        if any(crime in layer_name for crime in ["Robbery", "MV Theft", "Burglary", "Sexual Offenses"]):
            arcpy.AddMessage(f"🎨 Applying VISIBLE symbology to {layer_name}")
            
            # Get current symbology
            sym = layer.symbology
            
            # Method 1: Force simple marker symbology
            try:
                if hasattr(sym, 'renderer'):
                    # Ensure renderer exists
                    if not hasattr(sym.renderer, 'symbol'):
                        # Create simple marker renderer
                        arcpy.AddMessage(f"🔧 Creating simple marker for {layer_name}")
                        
                        # Use simple symbology approach
                        layer.transparency = 0  # Full opacity
                        
                        # Apply basic point symbology
                        if hasattr(sym, 'updateRenderer'):
                            sym.updateRenderer('SimpleRenderer')
                        
                        # Set basic properties
                        if hasattr(sym.renderer, 'symbol'):
                            try:
                                sym.renderer.symbol.size = 12  # Large, visible size
                                sym.renderer.symbol.color = {'RGB': [255, 0, 0, 100]}  # Bright red
                                layer.symbology = sym
                                arcpy.AddMessage(f"✅ Applied FORCED red symbology to {layer_name}")
                                return
                            except Exception as e:
                                arcpy.AddMessage(f"⚠️ Symbol property error: {e}")
                
            except Exception as e:
                arcpy.AddMessage(f"⚠️ Renderer modification failed: {e}")
            
            # Method 2: Apply from gallery if available
            try:
                arcpy.AddMessage(f"🎨 Trying symbol gallery for {layer_name}")
                if hasattr(layer.symbology.renderer, 'symbol'):
                    # Try to apply a simple circle symbol
                    layer.symbology.renderer.symbol.applySymbolFromGallery('Circle 1')
                    layer.symbology.renderer.symbol.size = 12
                    arcpy.AddMessage(f"✅ Applied gallery symbol to {layer_name}")
                    return
            except Exception as e:
                arcpy.AddMessage(f"⚠️ Gallery symbol failed: {e}")
            
            # Method 3: Force layer refresh and visibility
            try:
                arcpy.AddMessage(f"🔄 Forcing layer refresh for {layer_name}")
                layer.visible = True
                layer.transparency = 0
                
                # Get extent and zoom if needed
                desc = arcpy.Describe(layer)
                if hasattr(desc, 'extent'):
                    arcpy.AddMessage(f"📍 Layer extent: {desc.extent}")
                
                arcpy.AddMessage(f"✅ Forced visibility for {layer_name}")
                
            except Exception as e:
                arcpy.AddMessage(f"⚠️ Layer refresh failed: {e}")
            
            arcpy.AddMessage(f"💡 Using default symbology for {layer_name}")
        else:
            arcpy.AddMessage(f"💡 Skipping symbology for non-crime layer: {layer_name}")
            
    except Exception as e:
        arcpy.AddWarning(f"❌ Symbology error on {layer_name}: {str(e)}")
        arcpy.AddMessage(f"💡 Continuing with default symbology for {layer_name}")
```

---

## 🧪 **Testing Protocol**

### **Phase 1: Database Field Fix**
```bash
# Test incident table extraction
python -c "
from incident_table_automation import get_7day_incident_details
from datetime import date
incidents = get_7day_incident_details('MV Theft', date(2025, 6, 10))
print(f'Found {len(incidents)} incidents')
"
```

### **Phase 2: Symbology Visibility**
```bash
# Test map export with forced symbology
python main.py true false false 30 true 2025_06_10
# Check: MV_Theft_Map.png and Robbery_Map.png should show visible symbols
```

### **Phase 3: PowerPoint Assembly**
```bash
# Run PowerPoint assembly
python powerpoint_assembly.py
# Check: Slides should have updated charts, maps, placeholders
```

---

## 📋 **Implementation Priority**

### **Immediate (Today):**
1. ✅ **Fix database fields** - Update incident_table_automation.py
2. ✅ **Force symbology visibility** - Update map_export.py  
3. ✅ **Test field detection** - Run database inspection

### **Short-term (Tomorrow):**
1. **PowerPoint template fixes** - Remove multi-period layers
2. **Create assembly script** - Automate slide population
3. **Full system test** - All components working

### **Expected Results:**
- **Incident Tables**: ✅ Extract using available fields (no more 'block' errors)
- **Maps**: ✅ Visible symbology for all crime types
- **PowerPoint**: ✅ Clean slides with 7-day data only
- **Assembly**: ✅ Automated insertion of generated files

The database field issue is the highest priority - once that's fixed, your incident table automation will work properly!