# MV_Theft7d Quick Test Reference Card
# 🚀 Immediate Testing & Troubleshooting

## ✅ **3-Minute Test Checklist**

### **Step 1: Basic Verification (1 minute)**
- [ ] Open Power BI → MV_Theft7d query
- [ ] Right-click → Refresh
- [ ] Check for error messages
- [ ] Verify Cycle_Name column appears as 2nd column

### **Step 2: Date Range Test (1 minute)**
- [ ] Filter Call_Date: 2025-07-29 to 2025-08-04
- [ ] Verify Cycle_Name shows "C08W31" for all records
- [ ] Check other dates show appropriate cycle codes

### **Step 3: Data Integrity (1 minute)**
- [ ] Compare record count with original
- [ ] Verify all original columns still exist
- [ ] Check coordinate values (Longitude_DD, Latitude_DD)

## 🚨 **Quick Fixes for Common Issues**

### **Issue: "Cycle_Calendar wasn't recognized"**
**Fix:** Check query name in Power BI file
```m
// Your query might be named:
CycleTable = 7Day_28Day_250414,  // Instead of Cycle_Calendar
```

### **Issue: "Column '7_Day_Start' wasn't found"**
**Fix:** Check actual column names in your Cycle_Calendar query
```m
// Your columns might be named:
each [7_Day_Start] <= incidentDate and [7_Day_End] >= incidentDate
// Instead of:
each [#"7_Day_Start"] <= incidentDate and [#"7_Day_End"] >= incidentDate
```

### **Issue: "Cannot convert DateTime to Date"**
**Fix:** Try alternative date conversion
```m
// Replace this line:
each GetCycle(Date.From([Call_Date])), type text)

// With this:
each GetCycle(if [Call_Date] <> null then Date.From([Call_Date]) else null), type text)
```

### **Issue: All Cycle_Name values show "UNKNOWN"**
**Fix:** Test Cycle_Calendar query directly
```m
// Add this temporary step to debug:
TestCycle = Cycle_Calendar,
TestRow = Table.FirstN(TestCycle, 1),
DebugResult = TestRow{0}[Report_Name]
```

## 📊 **Expected Results Summary**

| Test | Expected Result |
|------|----------------|
| **Column Position** | Cycle_Name appears as 2nd column (after OBJECTID) |
| **July 29 - Aug 4** | Cycle_Name = "C08W31" |
| **Other Dates** | Cycle_Name = appropriate cycle code |
| **Record Count** | Same as original query |
| **All Columns** | All original columns preserved |
| **Coordinates** | Longitude_DD, Latitude_DD still work |
| **Query Refresh** | No errors, completes successfully |

## 🔧 **Emergency Debug Steps**

If the query fails completely, add these debug steps one by one:

```m
// Step 1: Test Cycle_Calendar access
TestCycle = Cycle_Calendar,

// Step 2: Test date conversion  
TestDate = Table.AddColumn(AddedCleanCallType, "Debug_Date", 
    each Date.From([Call_Date]), type date),

// Step 3: Test cycle matching
TestMatch = Table.AddColumn(TestDate, "Debug_Cycle", 
    each GetCycle([Debug_Date]), type text)
```

## 📞 **If Still Having Issues**

1. **Check Cycle_Calendar query exists** and loads without errors
2. **Verify column names** match exactly (including quotes and brackets)
3. **Test date conversion** separately from cycle matching
4. **Check Power BI version** - some functions may vary by version

## ✅ **Success Indicators**

- ✅ Query refreshes without errors
- ✅ Cycle_Name column appears and populates correctly
- ✅ Dates 2025-07-29 to 2025-08-04 show "C08W31"
- ✅ All original data preserved
- ✅ Coordinate transformation still works

## 🔄 **Next Steps After Success**

1. **Apply same modification** to remaining 4 queries
2. **Test each query individually** before moving to next
3. **Verify cycle assignment** works across all crime types
4. **Document any variations** needed for different queries 