# 🚀 GeoJSON Performance Optimization Guide
# 🕒 2025-08-02-15-35-00
# SCRPA_Time_v2/Performance Optimization
# Author: R. A. Carucci

## 🎯 **Problem Statement**

Your GeoJSON files are very large (400MB+ each) and take a long time to load in Power BI, causing:
- Slow query refresh times
- Memory issues
- Poor user experience
- Timeout errors

## 🔧 **Solution Overview**

This guide provides multiple optimization strategies to dramatically reduce file sizes and improve loading performance.

---

## 📊 **Strategy 1: File Compression (Immediate 70-80% Reduction)**

### **What It Does:**
- Compresses GeoJSON files using GZip compression
- Reduces file sizes by 70-80%
- Maintains data integrity
- Works with Power BI's built-in compression support

### **How to Implement:**

1. **Run the Optimization Script:**
   ```bash
   cd "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts"
   python geojson_optimizer.py --input-dir "08_json\arcgis_pro_layers" --output-dir "08_json\arcgis_pro_layers\optimized" --compress
   ```

2. **Update M Code to Use Compressed Files:**
   ```m
   Source = Json.Document(
       Binary.Decompress(
           File.Contents("path/to/file.geojson.gz"),
           Compression.GZip
       )
   )
   ```

### **Expected Results:**
- **File Size:** 400MB → 80-120MB (70-80% reduction)
- **Loading Speed:** 3-5x faster
- **Memory Usage:** Significantly reduced

---

## 🎯 **Strategy 2: Property Filtering (Additional 20-30% Reduction)**

### **What It Does:**
- Removes unnecessary properties from GeoJSON features
- Keeps only essential fields needed for analysis
- Reduces JSON parsing overhead

### **Essential Properties Only:**
```json
{
  "OBJECTID": "unique_id",
  "callid": "call_identifier", 
  "calltype": "incident_type",
  "callsource": "source_system",
  "fulladdr": "address",
  "beat": "police_beat",
  "district": "police_district",
  "calldate": "incident_date",
  "dispatchdate": "dispatch_date",
  "enroutedate": "enroute_date",
  "cleardate": "clear_date",
  "responsetime": "response_time_ms"
}
```

### **Removed Properties:**
- Redundant fields
- Unused metadata
- Duplicate information
- Debug fields

---

## 📐 **Strategy 3: Coordinate Precision Reduction (Additional 10-15% Reduction)**

### **What It Does:**
- Reduces coordinate precision from 15+ decimal places to 6
- Maintains sufficient accuracy for mapping
- Significantly reduces file size

### **Before vs After:**
```json
// Before: 15+ decimal places
"coordinates": [-74.043117523456789, 40.885912345678901]

// After: 6 decimal places (sufficient for mapping)
"coordinates": [-74.043118, 40.885912]
```

### **Accuracy Impact:**
- **6 decimal places** = ~1 meter accuracy
- **More than sufficient** for police incident mapping
- **No loss** of meaningful precision

---

## ⚡ **Strategy 4: M Code Optimizations**

### **Early Filtering:**
```m
// Filter BEFORE expensive transformations
FilteredIncidents = Table.SelectRows(
    RenamedDates,
    each [Call_Date] >= #datetime(2024, 12, 31, 0, 0, 0)
)
```

### **Reduced Property Expansion:**
```m
// Only expand essential properties
ExpandedProps = Table.ExpandRecordColumn(
    AddWebMercatorY,
    "Properties",
    {"OBJECTID","callid","calltype","callsource","fulladdr","beat","district",
     "calldate","dispatchdate","enroutedate","cleardate","responsetime"},
    {"objectid","callid","calltype","callsource","fulladdr","beat","district",
     "calldate","dispatchdate","enroutedate","cleardate","responsetime"}
)
```

---

## 📈 **Strategy 5: Power BI Performance Settings**

### **Enable Fast Data Load:**
1. **File** → **Options and settings** → **Options**
2. **Data Load** → **Fast Data Load**
3. **Enable:** "Allow data preview to download in the background"

### **Optimize Memory Settings:**
1. **File** → **Options and settings** → **Options**
2. **Data Load** → **Memory**
3. **Increase:** "Maximum memory for data load" to 4-8GB

### **Use Incremental Refresh (Premium):**
```m
// Add to your M code
IncrementalRefresh = Table.SelectRows(
    YourTable,
    each [Call_Date] >= Date.AddDays(DateTime.LocalNow(), -7)
)
```

---

## 🛠️ **Implementation Steps**

### **Step 1: Run Optimization Script**
```bash
# Navigate to scripts directory
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts"

# Run optimization
python geojson_optimizer.py --input-dir "..\08_json\arcgis_pro_layers" --output-dir "..\08_json\arcgis_pro_layers\optimized" --compress --create-template
```

### **Step 2: Update M Code Files**
1. Copy the optimized M code template
2. Update file paths to use `.geojson.gz` files
3. Test with one query first

### **Step 3: Update All M Code Files**
- `Burglary_Auto_7d.m`
- `Burglary_Com_Res_7d.m`
- `MV_Theft_7d.m`
- `Robbery_7d.m`
- `Sexual_Offenses_7d.m`

### **Step 4: Test Performance**
1. Load optimized files in Power BI
2. Measure refresh times
3. Compare memory usage
4. Verify data accuracy

---

## 📊 **Expected Performance Improvements**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **File Size** | 400MB | 80-120MB | 70-80% reduction |
| **Load Time** | 30-60s | 5-15s | 3-5x faster |
| **Memory Usage** | 2-4GB | 500MB-1GB | 50-75% reduction |
| **Refresh Time** | 2-5min | 30-60s | 3-5x faster |

---

## 🔍 **Troubleshooting**

### **Common Issues:**

1. **Compression Not Working:**
   - Ensure Python gzip module is available
   - Check file permissions
   - Verify output directory exists

2. **M Code Errors:**
   - Update file paths correctly
   - Use `Binary.Decompress` for `.gz` files
   - Test with small files first

3. **Performance Still Slow:**
   - Check Power BI memory settings
   - Enable Fast Data Load
   - Consider incremental refresh

### **Verification Steps:**
1. **File Size Check:** Compare original vs optimized sizes
2. **Data Integrity:** Verify record counts match
3. **Coordinate Accuracy:** Check sample coordinates
4. **Performance Test:** Measure load times

---

## 🎯 **Next Steps**

1. **Immediate:** Run the optimization script
2. **Short-term:** Update M code files
3. **Medium-term:** Implement incremental refresh
4. **Long-term:** Consider database solutions for very large datasets

---

## 📞 **Support**

If you encounter issues:
1. Check the optimization script logs
2. Verify file paths and permissions
3. Test with a single small file first
4. Review Power BI error messages

**Expected Outcome:** 70-80% file size reduction and 3-5x faster loading times! 