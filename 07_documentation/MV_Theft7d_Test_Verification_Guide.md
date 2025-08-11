# MV_Theft7d Query Test Verification Guide
# 🕒 2025-07-29-17-00-00
# Author: R. A. Carucci
# Purpose: Comprehensive testing and troubleshooting guide for cycle integration

## ✅ **Test Results Checklist**

### 1. **Cycle_Name Column Verification**
**Expected Result:** Cycle_Name column shows "C08W31" for July 29 - August 4 dates

**Test Steps:**
1. Open Power BI and refresh the MV_Theft7d query
2. Check if Cycle_Name column appears as 2nd column (after OBJECTID)
3. Filter data to show only dates between 2025-07-29 and 2025-08-04
4. Verify all records in this date range show "C08W31" in Cycle_Name column

**If Cycle_Name shows "UNKNOWN" or errors:**
- Check Cycle_Calendar query exists and loads properly
- Verify column references match exactly: `[#"7_Day_Start"]` and `[#"7_Day_End"]`
- Confirm date conversion: `Date.From([Call_Date])` handles datetime properly

### 2. **Data Preservation Verification**
**Expected Result:** All existing columns and data are preserved

**Test Steps:**
1. Compare column count before and after modification
2. Verify all original columns still exist:
   - OBJECTID, Call_ID, Clean_Call_Type, Call_Source
   - Full_Address, Beat, District, Call_Date
   - Dispatch_Date, Enroute_Date, Clear_Date
   - Response_Time_Minutes, Longitude_DD, Latitude_DD
3. Check that data values are unchanged
4. Confirm coordinate transformation still works correctly

### 3. **Query Refresh Verification**
**Expected Result:** Query refreshes without errors

**Test Steps:**
1. Right-click on MV_Theft7d query and select "Refresh"
2. Check for any error messages in the Power Query Editor
3. Verify the query completes successfully
4. Check that Cycle_Name column populates correctly

## 🔧 **Troubleshooting Guide**

### **Issue 1: Cycle_Name Shows "UNKNOWN" for All Records**

**Root Cause:** Cycle_Calendar query reference issue

**Solutions:**
1. **Verify Cycle_Calendar Query Exists:**
   ```m
   // Check if this query exists in your Power BI file
   // Query name should be: "7Day_28Day_250414"
   ```

2. **Check Cycle_Calendar Column Names:**
   ```m
   // Expected columns in Cycle_Calendar:
   // - Report_Due_Date
   // - 7_Day_Start  
   // - 7_Day_End
   // - 28_Day_Start
   // - 28_Day_End
   // - Report_Name
   ```

3. **Verify Column References:**
   ```m
   // In the GetCycle function, ensure these exact column names:
   each [#"7_Day_Start"] <= incidentDate and [#"7_Day_End"] >= incidentDate
   ```

4. **Test Cycle_Calendar Query:**
   ```m
   // Add this test step to verify Cycle_Calendar loads correctly:
   let
       TestCycle = Cycle_Calendar,
       TestFilter = Table.SelectRows(TestCycle, 
           each [#"7_Day_Start"] <= #date(2025, 7, 29) and [#"7_Day_End"] >= #date(2025, 7, 29))
   in
       TestFilter
   ```

### **Issue 2: Date Conversion Errors**

**Root Cause:** `Date.From([Call_Date])` conversion issue

**Solutions:**
1. **Check Call_Date Data Type:**
   ```m
   // Verify Call_Date is datetime type
   // If it's already date type, use: [Call_Date] instead of Date.From([Call_Date])
   ```

2. **Alternative Date Conversion:**
   ```m
   // Try this alternative if Date.From() fails:
   each GetCycle(if [Call_Date] <> null then Date.From([Call_Date]) else null)
   ```

3. **Debug Date Values:**
   ```m
   // Add this temporary column to debug:
   Table.AddColumn(AddedCleanCallType, "Debug_Date", 
       each if [Call_Date] <> null then Date.From([Call_Date]) else null, type date)
   ```

### **Issue 3: Query Refresh Fails**

**Root Cause:** Syntax or reference errors

**Solutions:**
1. **Check Cycle_Calendar Reference:**
   ```m
   // Ensure Cycle_Calendar is the correct query name
   // If your query is named differently, update the reference:
   CycleTable = YourActualQueryName,
   ```

2. **Verify Function Syntax:**
   ```m
   // Ensure the GetCycle function syntax is correct:
   GetCycle = (incidentDate as date) as text =>
       let
           MatchingCycle = Table.SelectRows(CycleTable, 
               each [#"7_Day_Start"] <= incidentDate and [#"7_Day_End"] >= incidentDate)
       in
           if Table.RowCount(MatchingCycle) > 0 
           then MatchingCycle{0}[Report_Name] 
           else "UNKNOWN"
   ```

3. **Step-by-Step Debugging:**
   ```m
   // Add these debug steps one by one:
   
   // Step 1: Test Cycle_Calendar access
   TestCycle = Cycle_Calendar,
   
   // Step 2: Test date conversion
   TestDate = Table.AddColumn(AddedCleanCallType, "Test_Date", 
       each Date.From([Call_Date]), type date),
   
   // Step 3: Test cycle matching
   TestMatch = Table.AddColumn(TestDate, "Test_Cycle", 
       each GetCycle([Test_Date]), type text)
   ```

## 📊 **Expected Test Results**

### **For Dates 2025-07-29 to 2025-08-04:**
- **Cycle_Name:** "C08W31"
- **Total Records:** Should match original count
- **All Other Columns:** Unchanged from original

### **For Other Date Ranges:**
- **Cycle_Name:** Should show appropriate cycle codes (C08W30, C08W32, etc.)
- **Unknown Dates:** Should show "UNKNOWN"

## 🔍 **Cycle_Calendar Reference Data**

Based on the documentation, the Cycle_Calendar should contain:

```m
// Expected cycle for July 29 - August 4, 2025:
// Report_Due_Date: 08/05/25
// 7_Day_Start: 07/29/25  
// 7_Day_End: 08/04/25
// Report_Name: "C08W31"
```

## ✅ **Success Criteria**

The modification is successful if:

1. ✅ **Cycle_Name column appears** as 2nd column after OBJECTID
2. ✅ **Dates 2025-07-29 to 2025-08-04** return "C08W31"
3. ✅ **All existing columns preserved** with original data
4. ✅ **Query refreshes without errors**
5. ✅ **Coordinate transformation still works** (Longitude_DD, Latitude_DD)
6. ✅ **All filtering logic preserved** (incidents after 12/31/2024)

## 🚨 **Common Error Messages & Solutions**

| Error Message | Solution |
|---------------|----------|
| `Expression.Error: The name 'Cycle_Calendar' wasn't recognized` | Check query name exists in Power BI file |
| `Expression.Error: The column '7_Day_Start' of the table wasn't found` | Verify column names in Cycle_Calendar query |
| `Expression.Error: We cannot convert a value of type DateTime to type Date` | Use `Date.From([Call_Date])` or check data type |
| `Expression.Error: The column 'Report_Name' of the table wasn't found` | Verify Report_Name column exists in Cycle_Calendar |

## 📞 **Next Steps After Testing**

1. **If all tests pass:** Apply the same modification to remaining queries
2. **If issues found:** Use troubleshooting guide above
3. **If Cycle_Calendar missing:** Create the query using the reference data provided
4. **If column names differ:** Update the GetCycle function to match your actual column names

## 🔄 **Apply to Remaining Queries**

Once MV_Theft7d is working correctly, apply the same cycle integration block to:

1. **Burglary_Auto_7d**
2. **Burglary_Comm_Res_7d**  
3. **Robbery_7d**
4. **Sexual_Offenses_7d**

Use the same cycle integration block and test each one individually. 