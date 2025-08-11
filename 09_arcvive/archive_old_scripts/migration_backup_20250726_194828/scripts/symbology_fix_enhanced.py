# 🕒 2025-06-22-17-15-00
# Police_Data_Analysis/map_export_symbology_fix.py
# Author: R. A. Carucci
# Purpose: Enhanced symbology application with crime-specific colors and debugging

import arcpy
import os
import logging

def apply_symbology_enhanced(layer, layer_name):
    """
    Apply crime-specific symbology with proper colors and debugging
    
    Args:
        layer: ArcPy layer object
        layer_name (str): Name of the layer for crime type detection
    """
    try:
        logging.info(f"🎨 Applying enhanced symbology to: {layer_name}")
        
        # Get current symbology
        sym = layer.symbology
        
        if not hasattr(sym, 'renderer'):
            logging.warning(f"⚠️ Layer {layer_name} has no renderer - creating simple renderer")
            # Create simple renderer if none exists
            sym = sym.clone()
            
        # Crime-specific color mapping
        crime_colors = {
            "Robbery": {'RGB': [0, 0, 0, 100]},           # Black
            "MV Theft": {'RGB': [255, 255, 0, 100]},      # Yellow  
            "Burglary": {'RGB': [255, 0, 0, 100]},        # Red
            "Sexual Offenses": {'RGB': [128, 0, 128, 100]} # Purple
        }
        
        # Determine crime type from layer name
        crime_type = None
        for crime in crime_colors.keys():
            if crime in layer_name:
                crime_type = crime
                break
        
        if not crime_type:
            crime_type = "Default"
            logging.warning(f"⚠️ Unknown crime type in {layer_name}, using default")
        
        # Apply symbology based on renderer type
        if hasattr(sym, 'renderer') and hasattr(sym.renderer, 'symbol'):
            symbol = sym.renderer.symbol
            
            # Set color
            if crime_type in crime_colors:
                symbol.color = crime_colors[crime_type]
                logging.info(f"✅ Applied {crime_type} color: {crime_colors[crime_type]}")
            else:
                symbol.color = {'RGB': [255, 0, 0, 100]}  # Default red
                logging.info(f"⚠️ Applied default red color for {layer_name}")
            
            # Set size and style
            symbol.size = 8
            if hasattr(symbol, 'style'):
                symbol.style = 'STYLE_CIRCLE'
            
            # Apply the modified symbology back to layer
            layer.symbology = sym
            
            logging.info(f"✅ Symbology applied to {layer_name}: Color={symbol.color}, Size={symbol.size}")
            
        else:
            logging.warning(f"⚠️ Cannot modify symbology for {layer_name} - no symbol property")
            
    except Exception as e:
        logging.error(f"❌ Failed to apply symbology to {layer_name}: {e}")
        
        # Fallback: Try basic color assignment
        try:
            logging.info(f"🔄 Attempting fallback symbology for {layer_name}")
            
            # Simple color assignment fallback
            if hasattr(layer, 'symbology'):
                layer.symbology.renderer.symbol.color = {'RGB': [0, 0, 0, 100]} if "Robbery" in layer_name else {'RGB': [255, 255, 0, 100]}
                layer.symbology.renderer.symbol.size = 8
                logging.info(f"✅ Fallback symbology applied to {layer_name}")
                
        except Exception as fallback_error:
            logging.error(f"❌ Fallback symbology also failed for {layer_name}: {fallback_error}")

def log_layer_symbology_debug(layer, layer_name):
    """
    Debug function to log current symbology properties
    
    Args:
        layer: ArcPy layer object
        layer_name (str): Name of layer for logging
    """
    try:
        logging.info(f"🔍 Symbology debug for {layer_name}:")
        
        if hasattr(layer, 'symbology'):
            sym = layer.symbology
            logging.info(f"  - Has symbology: True")
            
            if hasattr(sym, 'renderer'):
                logging.info(f"  - Has renderer: True")
                renderer = sym.renderer
                
                if hasattr(renderer, 'symbol'):
                    symbol = renderer.symbol
                    logging.info(f"  - Has symbol: True")
                    
                    if hasattr(symbol, 'color'):
                        logging.info(f"  - Current color: {symbol.color}")
                    if hasattr(symbol, 'size'):
                        logging.info(f"  - Current size: {symbol.size}")
                    if hasattr(symbol, 'style'):
                        logging.info(f"  - Current style: {symbol.style}")
                else:
                    logging.info(f"  - Has symbol: False")
            else:
                logging.info(f"  - Has renderer: False")
        else:
            logging.info(f"  - Has symbology: False")
            
    except Exception as e:
        logging.error(f"❌ Error debugging symbology for {layer_name}: {e}")

def verify_map_extent_and_features(layout, crime_type):
    """
    Verify map extent includes all features for the crime type
    
    Args:
        layout: ArcPy layout object
        crime_type (str): Type of crime to check
    """
    try:
        logging.info(f"🗺️ Checking map extent for {crime_type}")
        
        # Get map frame
        map_frames = layout.listElements("MAPFRAME_ELEMENT")
        if not map_frames:
            logging.warning("⚠️ No map frame found in layout")
            return
            
        map_frame = map_frames[0]
        map_obj = map_frame.map
        
        # Get current extent
        current_extent = map_frame.camera.getExtent()
        logging.info(f"📐 Current map extent: {current_extent}")
        
        # Find crime layer
        crime_layer = None
        for lyr in map_obj.listLayers():
            if crime_type in lyr.name and "7-Day" in lyr.name:
                crime_layer = lyr
                break
        
        if not crime_layer:
            logging.warning(f"⚠️ No 7-Day layer found for {crime_type}")
            return
            
        # Check if layer has features
        feature_count = int(arcpy.GetCount_management(crime_layer).getOutput(0))
        logging.info(f"📊 {crime_type} 7-Day features: {feature_count}")
        
        if feature_count > 0:
            # Get layer extent
            layer_extent = arcpy.Describe(crime_layer).extent
            logging.info(f"📐 {crime_type} layer extent: {layer_extent}")
            
            # Check if extents overlap
            if (current_extent.XMin <= layer_extent.XMax and 
                current_extent.XMax >= layer_extent.XMin and
                current_extent.YMin <= layer_extent.YMax and 
                current_extent.YMax >= layer_extent.YMin):
                logging.info(f"✅ Map extent includes {crime_type} features")
            else:
                logging.warning(f"⚠️ Map extent may not fully include {crime_type} features")
                logging.info(f"💡 Consider zooming map to layer extent")
                
            # Sample coordinates check
            with arcpy.da.SearchCursor(crime_layer, ["SHAPE@XY"]) as cursor:
                for i, row in enumerate(cursor):
                    coords = row[0]
                    in_extent = (current_extent.XMin <= coords[0] <= current_extent.XMax and 
                               current_extent.YMin <= coords[1] <= current_extent.YMax)
                    logging.info(f"  Feature {i+1}: {coords}, In extent: {in_extent}")
                    if i >= 2:  # Show max 3 features
                        break
        else:
            logging.info(f"📋 No features to check extent for {crime_type}")
            
    except Exception as e:
        logging.error(f"❌ Error checking map extent for {crime_type}: {e}")

def force_symbology_for_crime_type(map_obj, crime_type):
    """
    Force correct symbology for specific crime type
    
    Args:
        map_obj: ArcPy map object
        crime_type (str): Type of crime
    """
    try:
        logging.info(f"🔧 Forcing symbology for {crime_type}")
        
        # Find the 7-Day layer
        target_layer = None
        for lyr in map_obj.listLayers():
            if crime_type in lyr.name and "7-Day" in lyr.name:
                target_layer = lyr
                break
        
        if not target_layer:
            logging.warning(f"⚠️ No 7-Day layer found for {crime_type}")
            return False
            
        # Log current state
        log_layer_symbology_debug(target_layer, target_layer.name)
        
        # Apply enhanced symbology
        apply_symbology_enhanced(target_layer, target_layer.name)
        
        # Verify the change
        log_layer_symbology_debug(target_layer, target_layer.name)
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error forcing symbology for {crime_type}: {e}")
        return False

# Test function for debugging
def test_symbology_fix():
    """Test function to verify symbology fixes"""
    try:
        logging.info("🧪 Testing symbology fixes")
        
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map_obj = aprx.listMaps()[0]
        
        # Test with common crime types
        test_crimes = ["Robbery", "MV Theft"]
        
        for crime_type in test_crimes:
            logging.info(f"\n🔧 Testing {crime_type}")
            success = force_symbology_for_crime_type(map_obj, crime_type)
            if success:
                logging.info(f"✅ {crime_type} symbology test passed")
            else:
                logging.error(f"❌ {crime_type} symbology test failed")
                
    except Exception as e:
        logging.error(f"❌ Symbology test failed: {e}")

if __name__ == "__main__":
    # Run test if executed directly
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    test_symbology_fix()
