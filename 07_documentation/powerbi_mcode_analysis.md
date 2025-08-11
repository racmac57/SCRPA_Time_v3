# Power BI M Code Analysis & Corrected Implementation

// 🕒 2025-07-23-16-00-00  
// Project: SCRPA_Time_v2/PowerBI_MCode_Analysis  
// Author: R. A. Carucci  
// Purpose: Analysis of current M Code and corrected implementation

---

## 🚨 **CRITICAL ISSUES IDENTIFIED**

### **Issue 1: Incomplete ALL_CRIMES Query**
**Problem:** Your current ALL_CRIMES query (lines 117-126) is missing essential columns:
- ❌ No `Crime_Category` column for filtering
- ❌ No `TimeOfDay` buckets for chart analysis
- ❌ No vehicle normalization (UPPERCASE)
- ❌ No comprehensive narrative cleaning
- ❌ No intersection detection for Block addresses

### **Issue 2: External Dependency Failure**
**Problem:** Query tries to load reference table from:
```
"C:\Users\carucci_r\OneDrive - City of Hackensack\Documents\Projects\T4_New\_Reference_Tables\CallTypeUpdatedWithCategories.csv"
```
**Result:** This path likely doesn't exist, causing Crime_Category logic to fail

### **Issue 3: Filtered Queries Return Empty Data**
**Problem:** Because ALL_CRIMES lacks Crime_Category column, all filtered queries show empty:
- MOTOR_VEHICLE_THEFT ← Empty
- BURGLARY_AUTO ← Empty  
- ROBBERY ← Empty
- SEXUAL_OFFENSES ← Empty
- BURGLARY_COMM_AND_RES ← Empty

---

## ✅ **CORRECTED IMPLEMENTATION**

### **Replace Your ALL_CRIMES Query With This:**

```powerquery
// 🕒 2025-07-23-16-00-00
// Project: SCRPA_Time_v2/Corrected_ALL_CRIMES_Query
// Author: R. A. Carucci
// Purpose: Complete ALL_CRIMES query with all requested normalizations

let
    // ✅ Dynamic file detection from actual path
    Source = Folder.Files("C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA"),
    FilteredExcel = Table.SelectRows(Source, each [Extension] = ".xlsx" and Record.FieldOrDefault([Attributes], "Hidden", false) <> true),
    Sorted = Table.Sort(FilteredExcel,{{"Date modified", Order.Descending}}),
    LatestFile = Table.FirstN(Sorted, 1),
    
    Transform_File = (Parameter2 as binary) =>
        let
            // ✅ Safe sheet selection
            Source = Excel.Workbook(Parameter2, null, true),
            FilteredSheets = Table.SelectRows(Source, each [Kind] = "Sheet"),
            Sheet1_Sheet = if Table.RowCount(FilteredSheets) > 0 then FilteredSheets{0}[Data] else error "No valid sheets found",
            
            #"Promoted Headers" = Table.PromoteHeaders(Sheet1_Sheet, [PromoteAllScalars=true]),
            
            // ✅ Core data type conversions
            #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
                {"Case Number", type text},
                {"Incident Date", type date},
                {"Incident Time", type time},
                {"Incident Date_Between", type date},
                {"Incident Time_Between", type time},
                {"Report Date", type date},
                {"Report Time", type time},
                {"Incident Type_1", type text},
                {"Incident Type_2", type text},
                {"Incident Type_3", type text},
                {"FullAddress", type text},
                {"Officer of Record", type text}
            }),
            
            // ✅ NORMALIZED TEXT COLUMNS - All your requests
            WithNormalizedText = Table.TransformColumns(#"Changed Type", {
                {"Squad", each if _ <> null then Text.Upper(_) else null, type text},
                {"Reviewed By", each if _ <> null then Text.Proper(_) else null, type text},
                {"Registration 1", each if _ <> null then Text.Upper(_) else null, type text},
                {"Make1", each if _ <> null then Text.Upper(_) else null, type text},
                {"Model1", each if _ <> null then Text.Upper(_) else null, type text},
                {"Reg State 1", each if _ <> null then Text.Upper(_) else null, type text},
                {"Registration 2", each if _ <> null then Text.Upper(_) else null, type text},
                {"Make2", each if _ <> null then Text.Upper(_) else null, type text},
                {"Model2", each if _ <> null then Text.Upper(_) else null, type text},
                {"Reg State 2", each if _ <> null then Text.Upper(_) else null, type text}
            }),
            
            // ✅ Cascading date/time logic
            WithIncidentDate = Table.AddColumn(WithNormalizedText, "Incident_Date", each
                if [Incident Date] <> null then [Incident Date]
                else if [Incident Date_Between] <> null then [Incident Date_Between]
                else if [Report Date] <> null then [Report Date]
                else null, type date),
            
            WithIncidentTime = Table.AddColumn(WithIncidentDate, "Incident_Time", each
                if [Incident Time] <> null then [Incident Time]
                else if [Incident Time_Between] <> null then [Incident Time_Between]
                else if [Report Time] <> null then Time.From([Report Time])
                else null, type time),
            
            // ✅ TimeOfDay buckets with sort order
            WithTimeOfDay = Table.AddColumn(WithIncidentTime, "TimeOfDay", each
                let t = [Incident_Time] in
                if t = null then "Unknown"
                else if t >= #time(0,0,0) and t < #time(4,0,0) then "00:00–03:59 Early Morning"
                else if t >= #time(4,0,0) and t < #time(8,0,0) then "04:00–07:59 Morning"
                else if t >= #time(8,0,0) and t < #time(12,0,0) then "08:00–11:59 Morning Peak"
                else if t >= #time(12,0,0) and t < #time(16,0,0) then "12:00–15:59 Afternoon"
                else if t >= #time(16,0,0) and t < #time(20,0,0) then "16:00–19:59 Evening Peak"
                else "20:00–23:59 Night", type text),
                
            WithTimeOfDaySortOrder = Table.AddColumn(WithTimeOfDay, "TimeOfDay_SortOrder", each
                let t = [Incident_Time] in
                if t = null then 7
                else if t >= #time(0,0,0) and t < #time(4,0,0) then 1
                else if t >= #time(4,0,0) and t < #time(8,0,0) then 2
                else if t >= #time(8,0,0) and t < #time(12,0,0) then 3
                else if t >= #time(12,0,0) and t < #time(16,0,0) then 4
                else if t >= #time(16,0,0) and t < #time(20,0,0) then 5
                else 6, Int64.Type),
            
            // ✅ Date sort key
            WithDateSortKey = Table.AddColumn(WithTimeOfDaySortOrder, "Date_SortKey", each
                if [Incident_Date] <> null then 
                    Date.Year([Incident_Date]) * 10000 + Date.Month([Incident_Date]) * 100 + Date.Day([Incident_Date])
                else null, Int64.Type),
            
            // ✅ ENHANCED Block calculation with intersection detection
            WithBlock = Table.AddColumn(WithDateSortKey, "Block", each
                let
                    addr = [FullAddress] ?? "",
                    isIntersection = Text.Contains(addr, " & "),
                    streetNum = try Number.FromText(Text.BeforeDelimiter(addr, " ")) otherwise null,
                    streetName = Text.Trim(Text.BeforeDelimiter(Text.AfterDelimiter(addr, " "), ","))
                in
                    if isIntersection then
                        if streetName <> "" then streetName else "Check Location Data"
                    else if streetNum <> null and streetName <> "" then 
                        streetName & ", " & Text.From(Number.IntegerDivide(streetNum, 100) * 100) & " Block"
                    else if streetName <> "" then 
                        streetName & ", Unknown Block"
                    else "Check Location Data", type text),
            
            // ✅ ALL_INCIDENTS with comma separator
            WithAllIncidents = Table.AddColumn(WithBlock, "ALL_INCIDENTS", each
                Text.Combine(
                    List.RemoveNulls({
                        [Incident Type_1],
                        [Incident Type_2],
                        [Incident Type_3]
                    }), ", "  // ✅ Comma and space separator
                ), type text),
            
            // ✅ VEHICLE COLUMNS
            WithVehicle1 = Table.AddColumn(WithAllIncidents, "Vehicle_1", each
                let
                    parts = List.RemoveNulls({
                        [Reg State 1], [Registration 1], [Make1], [Model1]
                    })
                in
                    if List.IsEmpty(parts) then null else Text.Combine(parts, " "), type text),
                    
            WithVehicle2 = Table.AddColumn(WithVehicle1, "Vehicle_2", each
                let
                    parts = List.RemoveNulls({
                        [Reg State 2], [Registration 2], [Make2], [Model2]
                    })
                in
                    if List.IsEmpty(parts) then null else Text.Combine(parts, " "), type text),
                    
            WithVehicle1and2 = Table.AddColumn(WithVehicle2, "Vehicle_1_and_Vehicle_2", each
                let
                    vehicle1 = [Vehicle_1],
                    vehicle2 = [Vehicle_2]
                in
                    if vehicle1 <> null and vehicle2 <> null then vehicle1 & " | " & vehicle2
                    else if vehicle1 <> null then vehicle1
                    else if vehicle2 <> null then vehicle2
                    else null, type text),
            
            // ✅ Period calculation
            WithPeriod = Table.AddColumn(WithVehicle1and2, "Period", each
                let
                    incidentDate = [Incident_Date],
                    today = Date.From(DateTime.LocalNow()),
                    daysDiff = if incidentDate <> null then Duration.Days(today - incidentDate) else 999
                in
                    if daysDiff <= 7 then "7-Day"
                    else if daysDiff <= 28 then "28-Day"
                    else if incidentDate <> null and Date.Year(incidentDate) = Date.Year(today) then "YTD"
                    else "Historical", type text),
            
            // ✅ Filter before unpivot
            FilteredRows = Table.SelectRows(WithPeriod, each 
                [Case Number] <> "25-057654" and [Period] <> "Historical"
            ),
            
            // ✅ UNPIVOT incident types
            IncidentColumns = {"Incident Type_1", "Incident Type_2", "Incident Type_3"},
            KeepColumns = Table.ColumnNames(FilteredRows),
            IdColumns = List.Difference(KeepColumns, IncidentColumns),
            
            Unpivoted = Table.UnpivotOtherColumns(FilteredRows, IdColumns, "IncidentColumn", "IncidentType"),
            
            CleanedIncidents = Table.SelectRows(Unpivoted, each 
                [IncidentType] <> null and [IncidentType] <> ""
            ),
            
            // ✅ Clean IncidentType - Remove " - 2C" statute codes
            WithCleanedIncidentType = Table.TransformColumns(CleanedIncidents, {
                {"IncidentType", each 
                    if Text.Contains(_ ?? "", " - 2C") then
                        Text.BeforeDelimiter(_ ?? "", " - 2C")
                    else _ ?? "", type text
                }
            }),
            
            // ✅ CRIME CATEGORIZATION - Pattern matching (no external file dependency)
            WithCrimeCategory = Table.AddColumn(WithCleanedIncidentType, "Crime_Category", each
                let
                    incident = Text.Upper([IncidentType] ?? ""),
                    allIncidents = Text.Upper([ALL_INCIDENTS] ?? "")
                in
                    if Text.Contains(incident, "MOTOR VEHICLE THEFT") or Text.Contains(allIncidents, "MOTOR VEHICLE THEFT") then "Motor Vehicle Theft"
                    else if Text.Contains(incident, "ROBBERY") or Text.Contains(allIncidents, "ROBBERY") then "Robbery"
                    else if (Text.Contains(incident, "BURGLARY") and Text.Contains(incident, "AUTO")) or (Text.Contains(allIncidents, "BURGLARY") and Text.Contains(allIncidents, "AUTO")) then "Burglary – Auto"
                    else if Text.Contains(incident, "SEXUAL") or Text.Contains(allIncidents, "SEXUAL") then "Sexual Offenses"
                    else if (Text.Contains(incident, "BURGLARY") and (Text.Contains(incident, "COMMERCIAL") or Text.Contains(incident, "RESIDENCE"))) or (Text.Contains(allIncidents, "BURGLARY") and (Text.Contains(allIncidents, "COMMERCIAL") or Text.Contains(allIncidents, "RESIDENCE"))) then "Burglary – Commercial/Residence"
                    else "Other", type text),
            
            // ✅ Remove duplicates
            DistinctCases = Table.Distinct(WithCrimeCategory, {"Case Number"}),
            
            // ✅ METHOD 3: Comprehensive narrative cleaning
            ComprehensiveCleanedNarrative = Table.TransformColumns(DistinctCases, {
                {"Narrative", each 
                    let
                        text = _ ?? "",
                        step1 = Text.Replace(Text.Replace(Text.Replace(text, "#(cr)#(lf)", " "), "#(lf)", " "), "#(cr)", " "),
                        step2 = Text.Replace(Text.Replace(Text.Replace(step1, "    ", " "), "   ", " "), "  ", " "),
                        step3 = Text.Clean(step2),
                        step4 = Text.Trim(step3),
                        step5 = Text.Replace(Text.Replace(step4, "â", "'"), "â", ""),
                        final = if step5 = "" then null else step5
                    in
                        final, type text
                }
            })
        in
            ComprehensiveCleanedNarrative,
    
    InvokedCustom = Table.AddColumn(LatestFile, "Transform_File", each Transform_File([Content])),
    #"Expanded Transform_File" = Table.ExpandTableColumn(InvokedCustom, "Transform_File", Table.ColumnNames(Transform_File(LatestFile{0}[Content]))),
    #"Removed Other Columns" = Table.SelectColumns(#"Expanded Transform_File", Table.ColumnNames(Transform_File(LatestFile{0}[Content])))
in
    #"Removed Other Columns"
```

---

## 🎯 **IMPLEMENTATION STEPS**

### **Step 1: Replace ALL_CRIMES Query (5 minutes)**
1. Open your Power BI file: `SCRPA_Time_Project`
2. **Transform Data** → **Queries panel** → Right-click **ALL_CRIMES**
3. **Advanced Editor** → **Select All** → **Delete existing code**
4. **Paste corrected M Code** from above
5. **Done** → **Close & Apply**

### **Step 2: Configure TimeOfDay Sort Order (2 minutes)**
1. **Data View** → Click **TimeOfDay** column
2. **Column Tools** → **Sort by Column**
3. **Select:** "TimeOfDay_SortOrder"

### **Step 3: Verify Results (3 minutes)**
Check that filtered queries now populate:
- **MOTOR_VEHICLE_THEFT** → Should show MV theft incidents
- **BURGLARY_AUTO** → Should show auto burglary incidents
- **ROBBERY** → Should show robbery incidents
- **SEXUAL_OFFENSES** → Should show sexual offense incidents
- **BURGLARY_COMM_AND_RES** → Should show commercial/residential burglaries

---

## ✅ **EXPECTED IMPROVEMENTS**

### **Data Quality:**
- ✅ **Crime_Category column** for proper filtering
- ✅ **Normalized text fields** (Squad uppercase, Reviewed By proper case)
- ✅ **Vehicle columns** combined and uppercase
- ✅ **Enhanced address parsing** with intersection detection
- ✅ **Clean incident types** without statute codes

### **Chart Functionality:**
- ✅ **TimeOfDay chronological sorting** in charts
- ✅ **Populated filtered queries** for visualizations
- ✅ **Period classifications** (7-Day, 28-Day, YTD)
- ✅ **Comprehensive narrative cleaning** for reports

### **Analysis Capabilities:**
- ✅ **Vehicle fleet analysis** with Vehicle_1_and_Vehicle_2
- ✅ **Location intelligence** with proper Block handling
- ✅ **Time pattern analysis** with sorted periods
- ✅ **SCRPA compliance reporting** with all 5 crime categories

---

## 🚨 **KEY FIXES APPLIED**

1. **Removed external file dependency** - No more missing CSV errors
2. **Added comprehensive normalizations** - All text fields properly formatted
3. **Implemented intersection detection** - Address parsing handles " & " correctly
4. **Created vehicle combinations** - Fleet analysis ready
5. **Added chronological sorting** - Charts display in proper time order
6. **Cleaned statute codes** - Incident types are readable
7. **Enhanced narrative cleaning** - Method 3 comprehensive text processing

**Your Power BI project should now function as intended with populated filtered queries and proper chart capabilities!**