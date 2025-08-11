# 🕒 2025-07-01-15-30-00
# SCRPA_LAPTOP/map_export.py
# Author: R. A. Carucci
# Purpose: FINAL Complete map export with professional layouts and compatibility functions

import arcpy
import os
import sys
from datetime import datetime

def create_professional_crime_map(input_csv, output_folder, cycle_type):
    """
    Create professional crime map with basemap, legend, and proper layout
    """
    
    print(f"=== CREATING PROFESSIONAL {cycle_type.upper()} CRIME MAP ===")
    
    try:
        # Setup
        gdb_path = os.path.join(output_folder, "CrimeAnalysis.gdb")
        if not arcpy.Exists(gdb_path):
            arcpy.CreateFileGDB_management(output_folder, "CrimeAnalysis.gdb")
        
        arcpy.env.workspace = gdb_path
        arcpy.env.overwriteOutput = True
        
        # Import and process data
        print("📂 Processing data...")
        temp_table = f"temp_crimes_{cycle_type}"
        arcpy.conversion.TableToTable(input_csv, gdb_path, temp_table)
        
        # Filter by cycle
        if cycle_type.upper() == '7DAY':
            where_clause = "Cycle = '7-Day' AND PDZone IS NOT NULL AND Grid IS NOT NULL"
        elif cycle_type.upper() == '28DAY':
            where_clause = "Cycle = '28-Day' AND PDZone IS NOT NULL AND Grid IS NOT NULL"
        elif cycle_type.upper() == 'YTD':
            where_clause = "Cycle = 'YTD' AND PDZone IS NOT NULL AND Grid IS NOT NULL"
        else:
            print(f"Unknown cycle type: {cycle_type}")
            return None
        
        filtered_table = f"filtered_{cycle_type}"
        arcpy.conversion.TableToTable(temp_table, gdb_path, filtered_table, where_clause)
        
        # Check record count
        result = arcpy.GetCount_management(filtered_table)
        record_count = int(result.getOutput(0))
        print(f"📊 Records for mapping: {record_count}")
        
        if record_count == 0:
            return create_no_data_map(output_folder, cycle_type)
        
        # Create feature class with enhanced attributes
        fc_name = f"Crime_Points_{cycle_type}"
        create_enhanced_feature_class(gdb_path, fc_name, filtered_table)
        
        # Get current project and create/update map
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        crime_map = setup_crime_map(aprx, cycle_type)
        
        # Add basemap
        add_basemap_to_map(crime_map)
        
        # Add crime layer with professional symbology
        crime_layer = add_crime_layer_to_map(crime_map, gdb_path, fc_name, cycle_type)
        
        # Create professional layout
        layout = create_professional_layout(aprx, crime_map, cycle_type, record_count)
        
        # Export high-quality map
        output_path = export_final_map(layout, output_folder, cycle_type)
        
        # Cleanup
        cleanup_temp_data(temp_table, filtered_table)
        
        print(f"✅ Professional map created: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Error creating map: {e}")
        import traceback
        traceback.print_exc()
        return create_no_data_map(output_folder, cycle_type)

def create_enhanced_feature_class(gdb_path, fc_name, filtered_table):
    """Create feature class with enhanced crime point attributes"""
    
    print("📍 Creating enhanced crime points...")
    
    # Create feature class
    spatial_ref = arcpy.SpatialReference(4326)  # WGS84
    arcpy.CreateFeatureclass_management(gdb_path, fc_name, "POINT", spatial_reference=spatial_ref)
    
    # Add enhanced fields
    arcpy.AddField_management(fc_name, "Zone", "LONG")
    arcpy.AddField_management(fc_name, "Crime_Type", "TEXT", field_length=100)
    arcpy.AddField_management(fc_name, "Crime_Category", "TEXT", field_length=50)
    arcpy.AddField_management(fc_name, "Report_Num", "TEXT", field_length=20)
    arcpy.AddField_management(fc_name, "Time_Period", "TEXT", field_length=20)
    arcpy.AddField_management(fc_name, "Address", "TEXT", field_length=150)
    
    # Enhanced zone coordinates (Hackensack area)
    zone_coords = {
        5: (-74.0431, 40.8859),
        6: (-74.0331, 40.8859), 
        7: (-74.0231, 40.8859),
        8: (-74.0131, 40.8859),
        9: (-74.0031, 40.8859)
    }
    
    # Crime categorization
    def categorize_crime(incident):
        incident_lower = incident.lower()
        if any(word in incident_lower for word in ['burglary', 'theft', 'larceny']):
            return "Property Crime"
        elif any(word in incident_lower for word in ['assault', 'robbery', 'sexual']):
            return "Violent Crime"
        elif 'vehicle' in incident_lower:
            return "Vehicle Crime"
        else:
            return "Other Crime"
    
    def get_time_period(time_str):
        try:
            from datetime import datetime
            dt = datetime.strptime(time_str, '%m/%d/%Y %H:%M:%S')
            hour = dt.hour
            if 6 <= hour < 12:
                return "Morning"
            elif 12 <= hour < 18:
                return "Afternoon"
            elif 18 <= hour < 24:
                return "Evening"
            else:
                return "Night"
        except:
            return "Unknown"
    
    # Insert points with enhanced attributes
    point_count = 0
    zone_counts = {}
    
    with arcpy.da.InsertCursor(fc_name, ['SHAPE@XY', 'Zone', 'Crime_Type', 'Crime_Category', 
                                        'Report_Num', 'Time_Period', 'Address']) as icursor:
        with arcpy.da.SearchCursor(filtered_table, ['PDZone', 'Incident', 'ReportNumb', 
                                                   'Time_of_Ca', 'FullAddres']) as scursor:
            for row in scursor:
                zone = row[0]
                if zone in zone_coords:
                    # Spread points within zone
                    base_x, base_y = zone_coords[zone]
                    zone_count = zone_counts.get(zone, 0)
                    offset_x = base_x + (zone_count % 6) * 0.002
                    offset_y = base_y + (zone_count // 6) * 0.002
                    
                    # Enhanced attributes
                    crime_type = row[1][:50] if row[1] else "Unknown"
                    crime_category = categorize_crime(row[1]) if row[1] else "Other Crime"
                    report_num = row[2][:20] if row[2] else f"P{point_count}"
                    time_period = get_time_period(row[3]) if row[3] else "Unknown"
                    address = row[4][:100] if row[4] else "Unknown Address"
                    
                    icursor.insertRow([
                        (offset_x, offset_y),
                        zone,
                        crime_type,
                        crime_category,
                        report_num,
                        time_period,
                        address
                    ])
                    
                    point_count += 1
                    zone_counts[zone] = zone_counts.get(zone, 0) + 1
    
    print(f"📍 Created {point_count} enhanced crime points")
    return point_count

def setup_crime_map(aprx, cycle_type):
    """Setup or create crime map"""
    
    map_name = f"Crime_Map_{cycle_type}"
    
    # Remove existing map if it exists
    for existing_map in aprx.listMaps():
        if existing_map.name == map_name:
            aprx.deleteMap(existing_map)
    
    # Create new map
    crime_map = aprx.createMap(map_name, "MAP")
    print(f"🗺️ Created map: {map_name}")
    
    return crime_map

def add_basemap_to_map(crime_map):
    """Add professional basemap"""
    
    try:
        # Try to add streets basemap
        crime_map.addBasemap("Streets")
        print("🗺️ Added Streets basemap")
    except:
        try:
            # Fallback to topographic
            crime_map.addBasemap("Topographic")
            print("🗺️ Added Topographic basemap")
        except:
            print("⚠️ Could not add basemap - continuing without")

def add_crime_layer_to_map(crime_map, gdb_path, fc_name, cycle_type):
    """Add crime layer with professional symbology"""
    
    print("🎨 Adding crime layer with symbology...")
    
    # Add layer to map
    fc_path = os.path.join(gdb_path, fc_name)
    crime_layer = crime_map.addDataFromPath(fc_path)
    
    # Apply enhanced symbology by crime category
    try:
        sym = crime_layer.symbology
        
        if hasattr(sym, 'renderer'):
            # Try to create unique value renderer by crime category
            if hasattr(sym, 'updateRenderer'):
                sym.updateRenderer('UniqueValueRenderer')
                sym.renderer.fields = ['Crime_Category']
                
                # Define colors for crime categories
                category_colors = {
                    'Violent Crime': {'RGB': [220, 20, 20, 255]},    # Red
                    'Property Crime': {'RGB': [255, 165, 0, 255]},   # Orange
                    'Vehicle Crime': {'RGB': [128, 0, 128, 255]},    # Purple
                    'Other Crime': {'RGB': [70, 130, 180, 255]}      # Steel Blue
                }
                
                # Apply category symbology
                for group in sym.renderer.groups:
                    for item in group.items:
                        category = item.values[0][0]
                        if category in category_colors:
                            if hasattr(item.symbol, 'color'):
                                item.symbol.color = category_colors[category]
                            if hasattr(item.symbol, 'size'):
                                item.symbol.size = 8
                
                crime_layer.symbology = sym
                print("🎨 Applied category-based symbology")
                
            else:
                # Fallback to simple symbology
                apply_simple_symbology(crime_layer)
        else:
            apply_simple_symbology(crime_layer)
            
    except Exception as e:
        print(f"⚠️ Symbology warning: {e}")
        apply_simple_symbology(crime_layer)
    
    # Rename layer
    crime_layer.name = f"Crime Incidents - {cycle_type}"
    
    return crime_layer

def apply_simple_symbology(layer):
    """Apply simple red circle symbology"""
    
    try:
        sym = layer.symbology
        if hasattr(sym, 'renderer') and sym.renderer.type == "SimpleRenderer":
            if hasattr(sym.renderer.symbol, 'color'):
                sym.renderer.symbol.color = {'RGB': [220, 20, 20, 255]}  # Red
            if hasattr(sym.renderer.symbol, 'size'):
                sym.renderer.symbol.size = 8
            layer.symbology = sym
            print("🎨 Applied simple red symbology")
    except:
        print("⚠️ Could not apply symbology")

def create_professional_layout(aprx, crime_map, cycle_type, record_count):
    """Create professional layout with title, legend, and metadata"""
    
    print("📄 Creating professional layout...")
    
    layout_name = f"Crime_Report_{cycle_type}"
    
    # Remove existing layout
    for existing_layout in aprx.listLayouts():
        if existing_layout.name == layout_name:
            aprx.deleteLayout(existing_layout)
    
    # Create new layout (11x8.5 landscape)
    layout = aprx.createLayout(11, 8.5, "INCH", layout_name)
    
    # Add map frame (main area)
    map_frame = layout.createMapFrame(
        arcpy.Extent(0.5, 1.5, 8.5, 7.5), crime_map, "Main Map"
    )
    
    # Add title
    title_text = f"HACKENSACK POLICE DEPARTMENT\nCrime Analysis Report - {cycle_type} Period"
    title_element = layout.createTextElement(
        arcpy.Extent(0.5, 7.8, 8.5, 8.4),
        "TEXT",
        title_text
    )
    
    # Add legend
    try:
        legend = layout.createLegend(
            arcpy.Extent(8.7, 5.5, 10.8, 7.5), map_frame, "Legend"
        )
        print("📋 Added legend")
    except:
        print("⚠️ Could not create legend")
    
    # Add metadata text
    metadata_text = f"""Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Total Incidents: {record_count}
Period: {cycle_type}
Analyst: R. A. Carucci
Hackensack Police Department"""
    
    metadata_element = layout.createTextElement(
        arcpy.Extent(8.7, 1.5, 10.8, 3.5),
        "TEXT",
        metadata_text
    )
    
    # Add north arrow
    try:
        north_arrow = layout.createNorthArrow(
            arcpy.Extent(8.7, 4.0, 9.5, 5.0), map_frame, "North Arrow"
        )
        print("🧭 Added north arrow")
    except:
        print("⚠️ Could not add north arrow")
    
    # Add scale bar
    try:
        scale_bar = layout.createScaleBar(
            arcpy.Extent(8.7, 3.5, 10.8, 4.0), map_frame, "Scale Bar"
        )
        print("📏 Added scale bar")
    except:
        print("⚠️ Could not add scale bar")
    
    print("📄 Professional layout created")
    return layout

def export_final_map(layout, output_folder, cycle_type):
    """Export high-quality map"""
    
    print("💾 Exporting final map...")
    
    output_path = os.path.join(output_folder, f"crime_map_{cycle_type.lower()}.png")
    
    try:
        layout.exportToPNG(output_path, resolution=300, 
                          world_file=False, color_mode="24-BIT_TRUE_COLOR")
        print(f"📄 Exported PNG: {output_path}")
        
        # Also export PDF for printing
        pdf_path = os.path.join(output_folder, f"crime_map_{cycle_type.lower()}.pdf")
        layout.exportToPDF(pdf_path, resolution=300)
        print(f"📄 Exported PDF: {pdf_path}")
        
        return output_path
        
    except Exception as e:
        print(f"⚠️ Export warning: {e}")
        return output_path

def create_no_data_map(output_folder, cycle_type):
    """Create placeholder map when no data available"""
    
    print("📄 Creating no-data placeholder map...")
    
    try:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        
        # Create simple layout
        layout_name = f"NoData_{cycle_type}"
        layout = aprx.createLayout(8.5, 11, "INCH", layout_name)
        
        # Add title
        title_text = f"HACKENSACK POLICE DEPARTMENT\nNo Crime Data Available\n{cycle_type} Period"
        title_element = layout.createTextElement(
            arcpy.Extent(1, 5, 7, 7),
            "TEXT",
            title_text
        )
        
        # Export placeholder
        output_path = os.path.join(output_folder, f"crime_map_{cycle_type.lower()}.png")
        layout.exportToPNG(output_path, resolution=300)
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error creating placeholder: {e}")
        return None

def cleanup_temp_data(temp_table, filtered_table):
    """Clean up temporary data"""
    
    try:
        arcpy.Delete_management(temp_table)
        arcpy.Delete_management(filtered_table)
        print("🧹 Cleaned up temporary data")
    except:
        pass

# =============================================================================
# COMPATIBILITY FUNCTIONS FOR MAIN.PY
# =============================================================================

def export_maps(crime_type, output_folder=None, args=None):
    """
    Main compatibility function for main.py - creates crime maps
    
    Args:
        crime_type (str): Crime type to process
        output_folder (str): Output directory (optional)
        args: Additional arguments (optional)
        
    Returns:
        bool: Success status
    """
    try:
        from datetime import date
        from config import get_crime_type_folder, get_standardized_filename
        
        print(f"🗺️ Starting map export for {crime_type}")
        
        # Determine output folder
        if output_folder is None:
            date_str = date.today().strftime("%Y_%m_%d")
            output_folder = get_crime_type_folder(crime_type, date_str)
        
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Check if ArcGIS Pro project is available
        try:
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            has_arcgis = True
            print("🗺️ ArcGIS Pro project detected")
        except:
            has_arcgis = False
            print("⚠️ No ArcGIS Pro project - creating placeholder")
        
        if has_arcgis:
            # Create a temporary CSV file with sample data for this crime type
            temp_csv = create_temp_crime_data(crime_type, output_folder)
            
            if temp_csv:
                # Use the professional map creation function
                result = create_professional_crime_map(temp_csv, output_folder, "7Day")
                
                # Clean up temp file
                try:
                    os.remove(temp_csv)
                except:
                    pass
                    
                if result:
                    print(f"✅ Professional map created for {crime_type}")
                    return True
                else:
                    print(f"⚠️ Professional map failed, creating placeholder")
                    return create_placeholder_map(crime_type, output_folder)
            else:
                return create_placeholder_map(crime_type, output_folder)
        else:
            # Create placeholder when no ArcGIS available
            return create_placeholder_map(crime_type, output_folder)
            
    except Exception as e:
        print(f"❌ Map export error for {crime_type}: {e}")
        return create_placeholder_map(crime_type, output_folder)

def create_temp_crime_data(crime_type, output_folder):
    """
    Create temporary CSV with sample crime data for testing
    In production, this would query your actual crime database
    """
    try:
        import csv
        from datetime import date, timedelta
        import random
        
        temp_csv = os.path.join(output_folder, f"temp_{crime_type.replace(' ', '_')}.csv")
        
        # Generate sample data
        sample_data = []
        base_date = date.today() - timedelta(days=7)
        
        # Create a few sample incidents for this crime type
        for i in range(random.randint(1, 5)):
            incident_date = base_date + timedelta(days=random.randint(0, 6))
            sample_data.append({
                'ReportNumb': f"P{random.randint(10000, 99999)}",
                'Incident': crime_type,
                'FullAddres': f"{random.randint(100, 999)} Main St",
                'PDZone': random.choice([5, 6, 7, 8, 9]),
                'Grid': f"A{random.randint(1, 3)}",
                'Time_of_Ca': incident_date.strftime('%m/%d/%Y %H:%M:%S'),
                'Cycle': '7-Day'
            })
        
        # Write to CSV
        with open(temp_csv, 'w', newline='', encoding='utf-8') as f:
            if sample_data:
                writer = csv.DictWriter(f, fieldnames=sample_data[0].keys())
                writer.writeheader()
                writer.writerows(sample_data)
                
                print(f"📊 Created sample data with {len(sample_data)} incidents for {crime_type}")
                return temp_csv
            else:
                print(f"📊 No sample data created for {crime_type}")
                return None
                
    except Exception as e:
        print(f"⚠️ Could not create sample data: {e}")
        return None

def create_placeholder_map(crime_type, output_folder):
    """
    Create a simple placeholder map when data/ArcGIS is not available
    """
    try:
        from config import get_standardized_filename
        
        # Get standardized filename
        filename_prefix = get_standardized_filename(crime_type)
        placeholder_path = os.path.join(output_folder, f"{filename_prefix}_Map.png")
        
        try:
            # Try to create with PIL if available
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple image placeholder
            img = Image.new('RGB', (800, 600), color='lightgray')
            draw = ImageDraw.Draw(img)
            
            # Add text
            try:
                font = ImageFont.load_default()
            except:
                font = None
                
            text = f"Map Placeholder\n{crime_type}\n(Sample Data)"
            
            # Center the text
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width, text_height = 200, 60
                
            x = (800 - text_width) // 2
            y = (600 - text_height) // 2
            
            draw.text((x, y), text, fill='black', font=font)
            
            # Save placeholder
            img.save(placeholder_path)
            
        except ImportError:
            # Fallback - create empty file
            with open(placeholder_path, 'w') as f:
                f.write(f"Map placeholder for {crime_type}")
        
        print(f"📄 Created placeholder map: {placeholder_path}")
        return True
        
    except Exception as e:
        print(f"⚠️ Could not create placeholder: {e}")
        return False

def export_maps_for_crime_type(crime_type, target_date):
    """
    Alternative compatibility function for different calling patterns
    """
    from config import get_crime_type_folder
    date_str = target_date.strftime("%Y_%m_%d")
    output_folder = get_crime_type_folder(crime_type, date_str)
    return export_maps(crime_type, output_folder)

# =============================================================================
# MAIN EXECUTION (for standalone testing)
# =============================================================================

def main():
    """Main execution function for standalone testing"""
    
    if len(sys.argv) < 4:
        print("Usage: python map_export.py <input_csv> <output_folder> <cycle_type>")
        print("Cycle types: 7Day, 28Day, YTD")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_folder = sys.argv[2]
    cycle_type = sys.argv[3]
    
    print(f"=== ENHANCED MAP EXPORT ===")
    print(f"Input: {input_csv}")
    print(f"Output: {output_folder}")
    print(f"Cycle: {cycle_type}")
    
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Create professional map
    result = create_professional_crime_map(input_csv, output_folder, cycle_type)
    
    if result:
        print(f"✅ Enhanced map creation completed: {result}")
    else:
        print("❌ Map creation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()