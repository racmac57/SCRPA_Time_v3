# 🕒 2025-06-22-22-50-00
# SCRPA_Place_and_Time/script_corrections
# Author: R. A. Carucci
# Purpose: Critical corrections needed before testing SCRPA system

## 📋 **ANALYSIS RESULTS**

### **✅ GOOD NEWS - Scripts Are 95% Ready!**
Your integration work is excellent. Most functions and logic are correctly implemented. Only a few critical fixes needed.

### **❌ CRITICAL ISSUES TO FIX:**

---

## 🔧 **1. main.py - PowerPoint File Detection Issue**

**Problem**: The PowerPoint filename logic will fail because it tries to extract date from folder path incorrectly.

**Fix**: Replace the `auto_assemble_powerpoint_final` function:

```python
def auto_assemble_powerpoint_final(output_folder, crime_types):
    """
    Final PowerPoint assembly - overlays new images on existing template
    CORRECTED: Proper PowerPoint file detection
    """
    try:
        # Look for any .pptx file in the output folder
        ppt_files = glob.glob(os.path.join(output_folder, "*.pptx"))
        if not ppt_files:
            logging.error(f"❌ No PowerPoint file found in: {output_folder}")
            return False
            
        ppt_file = ppt_files[0]  # Use the first .pptx file found
        logging.info(f"✅ Loading PowerPoint: {os.path.basename(ppt_file)}")
            
        prs = Presentation(ppt_file)
        
        for i, crime_type in enumerate(crime_types):
            if i >= len(prs.slides):
                logging.warning(f"⚠️ No slide available for {crime_type}, skipping")
                continue
                
            slide = prs.slides[i]
            
            # Use the correct folder structure from your config
            date_str = os.path.basename(output_folder).split('_')[-2] + '_' + os.path.basename(output_folder).split('_')[-1]  # Extract from folder name
            crime_output_folder = get_crime_type_folder(crime_type, date_str)
            filename_prefix = get_standardized_filename(crime_type)
            
            logging.info(f"📊 Processing slide {i+1}: {crime_type}")
            
            # EXACT POSITIONING from your specifications
            chart_left = Inches(0.5)
            chart_top = Inches(2.8) 
            chart_width = Inches(5.84)
            chart_height = Inches(4.00)
            
            map_left = Inches(6.8)
            map_top = Inches(2.8)
            map_width = Inches(5.60)
            map_height = Inches(4.03)
            
            table_left = Inches(6.8)
            table_top = Inches(0.8)
            table_width = Inches(8.33)
            table_height = Inches(1.98)
            
            # Add chart
            chart_path = os.path.join(crime_output_folder, f"{filename_prefix}_Chart.png")
            if os.path.exists(chart_path):
                slide.shapes.add_picture(chart_path, chart_left, chart_top, chart_width, chart_height)
                logging.info(f"✅ Added chart: {filename_prefix}_Chart.png")
            
            # Add map
            map_path = os.path.join(crime_output_folder, f"{filename_prefix}_Map.png")
            if os.path.exists(map_path):
                slide.shapes.add_picture(map_path, map_left, map_top, map_width, map_height)
                logging.info(f"✅ Added map: {filename_prefix}_Map.png")
            else:
                # Try placeholder
                placeholder_path = os.path.join(crime_output_folder, f"{filename_prefix}_Map_Placeholder.png")
                if os.path.exists(placeholder_path):
                    slide.shapes.add_picture(placeholder_path, map_left, map_top, map_width, map_height)
                    logging.info(f"✅ Added map placeholder")
            
            # Add incident table
            table_paths = [
                os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable_AutoFit.png"),
                os.path.join(crime_output_folder, f"{filename_prefix}_IncidentTable_Placeholder.png")
            ]
            
            for table_path in table_paths:
                if os.path.exists(table_path):
                    slide.shapes.add_picture(table_path, table_left, table_top, table_width, table_height)
                    logging.info(f"✅ Added incident table: {os.path.basename(table_path)}")
                    break
        
        prs.save(ppt_file)
        logging.info(f"✅ PowerPoint assembly completed: {os.path.basename(ppt_file)}")
        return True
        
    except Exception as e:
        logging.error(f"❌ PowerPoint assembly failed: {e}", exc_info=True)
        return False
```

---

## 🔧 **2. incident_table_automation.py - Missing Import Fix**

**Problem**: The script tries to import `extract_street_from_address` but it doesn't exist in your Block M code.

**Fix**: Add this function to `incident_table_automation.py` (after the imports):

```python
def extract_street_from_address(address):
    """
    Extract street name when Block M code doesn't return a block number
    """
    import re
    
    if not address:
        return "UNKNOWN LOCATION"
        
    # Clean up the address
    cleaned = address.upper().strip()
    
    # Remove common prefixes
    cleaned = re.sub(r'^(THE\s+|A\s+)', '', cleaned)
    
    # Split into parts and take significant ones
    parts = cleaned.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]} AREA"
    elif len(parts) == 1:
        return f"{parts[0]} AREA"
    else:
        return "UNKNOWN LOCATION"
```

---

## 🔧 **3. Need Missing chart_export.py Integration**

**Problem**: Your scripts reference `chart_export` but I don't see that module in your files.

**Question**: Do you have a working `chart_export.py` file? If not, we need to create a basic one for testing.

---

## 🔧 **4. Missing extract_block_from_address.py File**

**Critical**: You need to copy your `extract_block_from_address.py` file to the same directory as your other scripts.

---

## 📋 **TESTING READINESS CHECKLIST**

### **✅ Ready to Test:**
- All major integration logic is correct
- Block M code integration properly implemented
- Excel integration working
- PowerPoint assembly framework complete
- Map extent calculations implemented

### **❌ Need These Files/Fixes:**

1. **Copy `extract_block_from_address.py`** to your scripts folder
2. **Apply the PowerPoint fix** above to `main.py`
3. **Add the street extraction function** to `incident_table_automation.py`
4. **Verify you have `chart_export.py`** (or we'll create a minimal version)

---

## 🎯 **RECOMMENDED TEST DATE**

**Use: `2025_05_07`**

**Why this date:**
- It's in your Excel file (should work with Excel integration)
- Previous testing showed it has actual incident data
- Good for testing both incidents and placeholders across different crime types

---

## 🚀 **TEST COMMAND**

```bash
python main.py true true true 30 false 2025_05_07
```

**Expected Results:**
- ✅ Folder: `C05W19_2025_05_07_7Day` (or Excel equivalent)
- ✅ CSV with proper Block addresses (not coordinates)
- ✅ Maps with proper zoom showing city boundaries
- ✅ PowerPoint with overlaid images at exact dimensions
- ✅ Incident tables as images

---

## 📝 **ACTION PLAN**

### **Step 1: Apply Fixes (10 minutes)**
1. Replace `auto_assemble_powerpoint_final` in `main.py` with corrected version above
2. Add `extract_street_from_address` function to `incident_table_automation.py`
3. Copy `extract_block_from_address.py` to scripts folder

### **Step 2: Verify Dependencies (5 minutes)**
```bash
pip install pandas matplotlib pillow python-pptx openpyxl tenacity
```

### **Step 3: Test (15 minutes)**
```bash
python main.py true true true 30 false 2025_05_07
```

### **Step 4: Verify Results**
- Check for proper Block addresses in CSV files
- Verify PowerPoint assembly worked
- Confirm map zoom levels appropriate

---

**You're 95% ready! Just need these few critical fixes and you'll be good to test with `2025_05_07`.**