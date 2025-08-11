# Power BI SCRPA Troubleshooting and Fix Guide

// 🕒 2025-07-23-16-00-00  
// Project: SCRPA_Time_v2/PowerBI_Troubleshooting_Guide  
// Author: R. A. Carucci  
// Purpose: Step-by-step guide to fix single row null, TimeOfDay buckets, and data type errors

---

## 🚨 **Issues Fixed**

### **Issue 1: Single Row of Null Data**
**Problem:** ALL_CRIMES query returns single row with null values  
**Root Cause:** Sheet selection error - "Key matched more than one row in table"  
**✅ Fixed:** More specific sheet selection logic in Transform_File function

### **Issue 2: Wrong TimeOfDay Buckets** 
**Problem:** Incorrect time ranges in TimeOfDay column  
**✅ Fixed:** Updated to correct project specifications:
- `"00:00–03:59 Early Morning"`
- `"04:00–07:59 Morning"`  
- `"08:00–11:59 Morning Peak"`
- `"12:00–15:59 Afternoon"`
- `"16:00–19:59 Evening Peak"`
- `"20:00–23:59 Night"`

### **Issue 3: CAD Time Data Type Errors**
**Problem:** "Cannot apply operator < to types Number and DateTime"  
**Root Cause:** Time columns being parsed as DateTime instead of duration  
**✅ Fixed:** Enhanced time handling logic for Time Spent/Time Response

---

## ⚡ **Step-by-Step Fix Implementation**

### **Step 1: Replace ALL_CRIMES Query**
1. **Open Power BI Desktop**
2. **Transform Data** → **Queries panel** → Right-click **ALL_CRIMES**
3. **Advanced Editor** → **Select All** → **Delete existing code**
4. **Paste corrected ALL_CRIMES M Code** from artifact
5. **Done** → **Close & Apply**

### **Step 2: Replace CAD_Data Query** 
1. **Right-click CAD_Data** → **Advanced Editor**
2. **Select All** → **Delete existing code**  
3. **Paste corrected CAD_Data M Code** from artifact
4. **Done**

### **Step 3: Update CAD_RMS_Matched Query**
1. **Right-click CAD_RMS_Matched** → **Advanced Editor**
2. **Replace with corrected CAD_RMS_Matched code**
3. **Done** → **Close & Apply**

### **Step 4: Verify Data Load**
1. **Check ALL_CRIMES** - should show multiple rows with actual data
2. **Check TimeOfDay column** - should show correct time buckets
3. **Check CAD_Data** - Time Spent/Response should be numbers, not errors
4. **Check CAD_RMS_Matched** - should show joined data with Has_CAD_Data flag

---

## 🔧 **Key Technical Fixes Applied**

### **Sheet Selection Fix:**
```powerquery
// ✅ OLD (Caused "key matched more than one row" error)
FirstSheet = Workbook{[Item="Sheet1",Kind="Sheet"]}[Data]

// ✅ NEW (Handles multiple sheets safely)
FilteredSheets = Table.SelectRows(Source, each [Kind] = "Sheet"),
FirstSheet = if Table.RowCount(FilteredSheets) > 0 
            then FilteredSheets{0}[Data]
            else error "No valid sheets found in workbook"
```

### **TimeOfDay Bucket Correction:**
```powerquery
// ❌ OLD (Wrong time ranges)
if [StartOfHour] >= #time(6,0,0) and [StartOfHour] < #time(14,0,0) then "Day (06:00-13:59)"

// ✅ NEW (Correct project specifications)
if t >= #time(0,0,0) and t < #time(4,0,0) then "00:00–03:59 Early Morning"
else if t >= #time(4,0,0) and t < #time(8,0,0) then "04:00–07:59 Morning"
```

### **Time Data Type Handling:**
```powerquery
// ✅ Enhanced time column processing
{"Time Spent", each 
    let value = _ in
    if value = null then null
    else if value is number then 
        if value < 0 then null else value
    else if value is time then 
        let minutes = Duration.TotalMinutes(value - #time(0,0,0))
        in if minutes < 0 then null else minutes
    else if value is datetime then
        let minutes = Duration.TotalMinutes(Time.From(value) - #time(0,0,0))
        in if minutes < 0 then null else minutes
    else try Number.From(value) otherwise null
, type number}
```

### **Column Name Handling:**
```powerquery
// ✅ Uses actual column names with spaces
"Incident Type_1", "Incident Type_2", "Incident Type_3"  // Not IncidentType1, etc.
"Incident Date"     // Not IncDate
"Incident Time"     // Not IncTime
```

---

## 📊 **Expected Results After Fix**

### **ALL_CRIMES Query:**
- ✅ **Multiple rows** instead of single null row
- ✅ **Proper TimeOfDay buckets** with correct time ranges
- ✅ **Valid Crime_Category** classifications
- ✅ **Populated ALL_INCIDENTS** column with concatenated incident types
- ✅ **Correct Period** assignments (7-Day, 28-Day, YTD)

### **CAD_Data Query:**
- ✅ **Time Spent/Response as numbers** (no DateTime conversion errors)
- ✅ **Negative time values** converted to null
- ✅ **Block addresses** properly calculated
- ✅ **No data type comparison errors**

### **CAD_RMS_Matched Query:**
- ✅ **All RMS records preserved** (LEFT JOIN)
- ✅ **CAD data joined** where Case Numbers match  
- ✅ **Has_CAD_Data flag** shows Yes/No properly
- ✅ **Response time metrics** available for analysis

---

## 🎯 **Validation Steps**

### **Test 1: Data Volume Check**
```powerquery
// Create temporary query to count records
let Source = ALL_CRIMES in Table.RowCount(Source)
```
**Expected:** > 1 row (should be hundreds/thousands depending on data)

### **Test 2: TimeOfDay Verification**
```powerquery
// Check TimeOfDay values
let Source = ALL_CRIMES in 
Table.Group(Source, {"TimeOfDay"}, {{"Count", each Table.RowCount(_), Int64.Type}})
```
**Expected:** 6 distinct time periods with correct labels

### **Test 3: Crime Category Distribution**
```powerquery
// Verify crime categorization working
let Source = ALL_CRIMES in
Table.Group(Source, {"Crime_Category"}, {{"Count", each Table.RowCount(_), Int64.Type}})
```
**Expected:** Categories like "Motor Vehicle Theft", "Burglary – Auto", etc.

### **Test 4: CAD Join Success Rate**
```powerquery
// Check CAD matching rate
let Source = CAD_RMS_Matched in
Table.Group(Source, {"Has_CAD_Data"}, {{"Count", each Table.RowCount(_), Int64.Type}})
```
**Expected:** Mix of "Yes" and "No" values

---

## 🚨 **If Issues Persist**

### **Problem: Still Getting Single Null Row**
**Debugging Steps:**
1. Check if SCRPA folder exists and contains .xlsx files
2. Verify file isn't password protected or corrupted
3. Try opening Excel file manually to confirm structure
4. Use this debug query to see available files:
```powerquery
let Source = Folder.Files("C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA") in Source
```

### **Problem: TimeOfDay Still Wrong**
**Check:** Verify [Incident_Time] column contains actual time values, not null

### **Problem: CAD Time Errors Continue**
**Solution:** Add this before time transformations:
```powerquery
// Check what data types exist in Time columns
let Headers = Table.PromoteHeaders(FirstSheet),
    TimeSpentType = Value.Type(Table.Column(Headers, "Time Spent"){0}),
    TimeResponseType = Value.Type(Table.Column(Headers, "Time Response"){0})
in {TimeSpentType, TimeResponseType}
```

---

## ✅ **Success Confirmation**

Once all fixes are applied successfully, you should see:

1. **✅ ALL_CRIMES loads** with multiple rows of actual crime data
2. **✅ TimeOfDay shows** "Early Morning", "Morning Peak", etc. labels
3. **✅ CAD_Data loads** without time comparison errors
4. **✅ Charts display properly** with correct time periods and crime categories
5. **✅ CAD/RMS matching** provides response time analytics

**Your Power BI backup charts are now ready while you fix the ArcGIS mapping issues!**