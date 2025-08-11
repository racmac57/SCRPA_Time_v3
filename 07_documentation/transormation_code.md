Normalize column column headers for CAD and RMS Exports
```
rsm column headers
    rms_case_number
    rms_incident_date
    rms_incident_time
    rms_incident_date_between
    rms_incident_time_between
    rms_report_date
    rms_report_time
    rms_incident_type_1
    rms_incident_type_2
    rms_incident_type_3
    rms_fulladdress
    rms_grid
    rms_zone
    rms_narrative
    rms_total_value_stolen
    rms_total_value_recover
    rms_registration_1
    rms_make1
    rms_model1
    rms_reg_state_1
    rms_registration_2
    rms_reg_state_2
    rms_make2
    rms_model2
    rms_reviewed_by
    rms_completecalc
    rms_officer_of_record
    rms_squad
    rms_det_assigned
    rms_case_status
    rms_nibrs_classification

cad column headers
    cad_reportnumbernew
    cad_incident
    cad_how_reported
    cad_fulladdress2
    cad_pdzone
    cad_grid
    cad_time_of_call
    cad_cyear
    cad_cmonth
    cad_hourminuetscalc
    cad_dayofweek
    cad_time_dispatched
    cad_time_out
    cad_time_in
    cad_time_spent
    cad_time_response
    cad_officer
    cad_disposition
    cad_response_type
    cad_cadnotes
```

1. cad_reportnumbernew map to rms_case_number, once mapped take value and make a new column named "case_number"
2. cad_incident is the reference column for new column "response_type". use "c:\users\carucci_r\onedrive - city of hackensack\09_reference\classifications\calltypes\calltype_categories.xlsx" for the mapping, use the file to backfill null values in "response_type"
3. cad_how_reported make sure value "9-1-1" is not mistakenly recognized as a date calltype_categories
4. cad_fulladdress2 and rms_fulladdress when the records are mapped these values should be the same so they can be used for backfilling. when backfilling is complete the remaining value will be added to a new column "location"; the other columns can be removed.
5. cad_pdzone and rms_zone are the same and can be used for backfilling. the remaining value after backfilling will be added to a new column "post"; remove original columns.
6. cad_grid and rms_grid will be handled in the same way as cad_pdzone and rms_zone.
7. cad_time_of_call is a mm/dd/yyyy hh:mm:ss
8. cad_time_dispatched, cad_time_out, cad_time_in is a mm/dd/yyyy hh:mm:ss
9. cad_time_spent is caluculated by subtacting cad_time_in from cad_time_out. the value is duration data type new column name  H:mm:ss in a bew column named time_spent and a new column "time_spent_formatted" 0Hrs. 00Mins round to nearest minute (duration data type)
10. cad_time_response is caluculated by subtacting cad_time_out from cad_time_dispatched, new column name H:mm:ss in a bew column named time_response and a new column "time_response_formatted" 0Hrs. 00Mins round to nearest minute (duration data type)
WithTimeSpentFormatted = Table.AddColumn(prev,"Time_Spent_Formatted", each let m=[Time_Spent_Minutes] in
  if m=null then null else
    let vm=Number.Round(Number.From(m),0), h=Number.IntegerDivide(vm,60), r=Number.Mod(vm,60) in
    if vm<=0 then "0 Mins"
    else if h=0 then Text.From(r)&" Mins"
    else if r=0 then Text.From(h)&" Hrs"
    else Text.From(h)&" Hrs "&Text.PadStart(Text.From(r),2,"0")&" Mins",
  type text
),
WithTimeSpentFlag      = Table.AddColumn(prev,"Time_Spent_Flag", each …
),
WithTimeResponseFormatted = Table.AddColumn(prev,"Time_Response_Formatted", each …),
WithTimeResponseFlag      = Table.AddColumn(prev,"Time_Response_Flag", each …)
```

```python
# Python (pandas)
def fmt_duration(mins):
    if pd.isna(mins): return None
    vm = round(mins)
    h, r = divmod(vm, 60)
    if vm <= 0:       return "0 Mins"
    if h == 0:        return f"{r} Mins"
    if r == 0:        return f"{h} Hrs"
    return f"{h} Hrs {r:02d} Mins"

def flag_spent(mins):
    if pd.isna(mins): return None
    if mins < 5:      return "Under 5 Minutes"
    if mins > 300:    return "Over 5 Hours"
    return "Normal"

def fmt_response(mins):
    if pd.isna(mins): return None
    total_sec = round(mins * 60)
    m, s = divmod(total_sec, 60)
    if total_sec <= 0: return "0 Secs"
    if m == 0:         return f"{s} Secs"
    if s == 0:         return f"{m} Mins"
    return f"{m} Mins {s:02d} Secs"

def flag_response(mins):
    if pd.isna(mins): return None
    if mins <= 1:     return "0-1 Minutes"
    if mins > 10:     return "Over 10 Minutes"
    return "Normal"

df["Time_Spent_Formatted"]  = df["Time_Spent_Minutes"].apply(fmt_duration)
df["Time_Spent_Flag"]       = df["Time_Spent_Minutes"].apply(flag_spent)
df["Time_Response_Formatted"] = df["Time_Response_Minutes"].apply(fmt_response)
df["Time_Response_Flag"]      = df["Time_Response_Minutes"].apply(flag_response)
11. cad_cadnotes // Parse CADNotes
WithParsedCADNotes = Table.AddColumn(prev,"CADNotes_Parsed", each let
  raw=[CADNotes]??"", lines=Text.Split(raw,"#(lf)"), header=… in
  [ CAD_Username=…, CAD_Timestamp=…, CAD_Notes_Cleaned=… ],
  type record
),
ExpandedCADNotes = Table.ExpandRecordColumn(…),
// Combine incident types
WithAllIncidents = Table.AddColumn(prev,"ALL_INCIDENTS", each
  Text.Combine( List.RemoveNulls({
    cleanType1, cleanType2, cleanType3 }), ", "), type text

# 2) Parse CADNotes
import re
def parse_cad_notes(raw):
    if pd.isna(raw): return pd.Series([None,None,None])
    lines = [l for l in raw.splitlines() if l.strip()]
    header = lines[0] if lines else ""
    toks = header.split()
    user = next((t for t in toks if "_" in t), None)
    dt_raw = ""
    for i,t in enumerate(toks):
        if "/" in t and i+1<len(toks):
            dt_raw = t + " " + toks[i+1]; break
    try:
        dt = pd.to_datetime(dt_raw)
        ts = dt.strftime("%m/%d/%Y %H:%M:%S")
    except:
        ts = None
    cleaned = raw.replace(header,"").replace(dt_raw,"").replace(user or "","")
    cleaned = " ".join([w for w in cleaned.split() if not re.match(r"\d{1,2}/\d{1,2}/",w)])
    cleaned = cleaned.strip().title() or None
    return pd.Series([user, ts, cleaned])

df[["CAD_Username","CAD_Timestamp","CAD_Notes_Cleaned"]] = (
    df["CADNotes"].apply(parse_cad_notes)
)

# 3) Combine Incident Types
df["ALL_INCIDENTS"] = df[["Incident Type_1","Incident Type_2","Incident Type_3"]]  .apply(lambda row: ", ".join(
      t.split(" - 2C")[0] for t in row if pd.notna(t)
  ), axis=1)


- to calculate new column "block" use "location" to calculate:
```m
WithUnifiedGrid  = Table.AddColumn(prev,"Grid", each if [CAD_Grid]<>null then [CAD_Grid] else [RMS_Grid], type text),
WithUnifiedZone  = Table.AddColumn(…   ,"Zone", each if [CAD_Zone]<>null then [CAD_Zone] else [RMS_Zone], type text),
WithEnhancedBlock= Table.AddColumn(…   ,"Enhanced_Block", each let
    rm=[RMS_Block], cb=[CAD_Block] in
    if Text.Contains(rm,"Check CAD Location Data") and cb<>null then cb else rm,
  type text
),
WithBlock = Table.AddColumn(…,"Block", each
  let addr=[location]??"", isInt=Text.Contains(addr," & ") in
    if isInt then addr
    else  /* parse number and street into “X Block” */
)
```

```python
# Python (pandas)
# 1) Unified grid/zone
df["Grid"] = df["CAD_Grid"].fillna(df["RMS_Grid"])
df["Zone"] = df["CAD_Zone"].fillna(df["RMS_Zone"])

# 2) Enhanced block
def enhance_block(rms, cad):
    if pd.notna(rms) and "Check CAD Location Data" in rms and pd.notna(cad):
        return cad
    return rms

df["Enhanced_Block"] = df.apply(
    lambda row: enhance_block(row["RMS_Block"], row["CAD_Block"]), axis=1
)

# 3) Block parsing (basic)
def parse_block(addr):
    if pd.isna(addr):
        return None
    if "&" in addr:
        return addr  # preserve intersections
    parts = addr.replace(", Hackensack, NJ, 07601","").split(" ",1)
    try:
        num = int(parts[0])
        street = parts[1].split(",",1)[0].strip()
        return f"{street}, {num//100*100} Block"
    except:
        return "Check CAD Location Data"

df["Block"] = df["location"].apply(parse_block)
```

RMS COLUMNS:
- to calculate incident_date: 
```m
// Cascading date/time
WithIncidentDate = Table.AddColumn(prev,"incident_date", each
  if [Incident Date]<>null then [Incident Date]
  else if [Incident Date_Between]<>null then [Incident Date_Between]
  else if [Report Date]<>null then [Report Date]
  else null, type date
  
- to calculate incident_time:
  WithIncidentTime = Table.AddColumn(WithIncidentDate,"incident_time", each
  if [Incident Time]<>null then [Incident Time]
  else if [Incident Time_Between]<>null then [Incident Time_Between]
  else if [Report Time]<>null then Time.From([Report Time])
  else null, type time
 
- After calulation remove:
RMS_Incident_Date
RMS_Incident_Time
RMS_Incident_Date_Between
RMS_Incident_Time_Between
RMS_Report_Date
RMS_Report_Time

- all_incidents
RMS_Incident_Type_1
RMS_Incident_Type_2
RMS_Incident_Type_3

// ✅ ALL_INCIDENTS with comma separator AND statute code removal
            WithAllIncidents = Table.AddColumn(WithBlock, "ALL_INCIDENTS", each
                let
                    // Clean each incident type by removing " - 2C" and everything after
                    cleanType1 = if [Incident Type_1] <> null then 
                        if Text.Contains([Incident Type_1], " - 2C") then
                            Text.BeforeDelimiter([Incident Type_1], " - 2C")
                        else [Incident Type_1]
                    else null,
                    
                    cleanType2 = if [Incident Type_2] <> null then 
                        if Text.Contains([Incident Type_2], " - 2C") then
                            Text.BeforeDelimiter([Incident Type_2], " - 2C")
                        else [Incident Type_2]
                    else null,
                    
                    cleanType3 = if [Incident Type_3] <> null then 
                        if Text.Contains([Incident Type_3], " - 2C") then
                            Text.BeforeDelimiter([Incident Type_3], " - 2C")
                        else [Incident Type_3]
                    else null
                in
                    Text.Combine(
                        List.RemoveNulls({
                            cleanType1,
                            cleanType2,
                            cleanType3
                        }), ", "
                    ), type text),

# 3) Combine Incident Types
df["all_incidents"] = df[["Incident Type_1","Incident Type_2","Incident Type_3"]]  .apply(lambda row: ", ".join(
      t.split(" - 2C")[0] for t in row if pd.notna(t)
  ), axis=1)
  


- RMS_Narrative normalize to narrative
# 5) Narrative cleanup
df["Narrative"] = (
    df["Narrative"]
      .str.replace(r"#\(lf\)|#\(cr\)", " ", regex=True)
      .str.replace(r"\s{2,}", " ", regex=True)
      .str.strip()
)

new column vehicle_1
 Withvehicle_1 = Table.AddColumn(WithAllIncidents, "vehicle_1", each
                let
                    regState = [Reg State 1] ?? "",
                    registration = [Registration 1] ?? "",
                    make = [Make1] ?? "",
                    model = [Model1] ?? "",
                    
                    // Only create vehicle string if we have meaningful data
                    hasVehicleData = regState <> "" or registration <> "" or make <> "" or model <> ""
                in
                    if hasVehicleData then
                        let
                            // Build parts safely
                            statePart = if regState <> "" then regState else "",
                            regPart = if registration <> "" then registration else "",
                            makePart = if make <> "" then make else "",
                            modelPart = if model <> "" then model else "",
                            
                            // Combine state and registration with " - "
                            stateReg = if statePart <> "" and regPart <> "" then 
                                statePart & " - " & regPart
                            else if regPart <> "" then regPart
                            else if statePart <> "" then statePart
                            else "",
                            
                            // Combine make and model with "/"
                            makeModel = if makePart <> "" and modelPart <> "" then 
                                makePart & "/" & modelPart
                            else if makePart <> "" then makePart
                            else if modelPart <> "" then modelPart
                            else "",
                            
                            // Final combination with ", "
                            result = if stateReg <> "" and makeModel <> "" then 
                                stateReg & ", " & makeModel
                            else if stateReg <> "" then stateReg
                            else if makeModel <> "" then makeModel
                            else ""
                        in
                            if result = "" then null else result
                    else null, type text),
                    
            Withvehicle2 = Table.AddColumn(WithVehicle1, "vehicle_2", each
                let
                    regState = [Reg State 2] ?? "",
                    registration = [Registration 2] ?? "",
                    make = [Make2] ?? "",
                    model = [Model2] ?? "",
                    
                    // Only create vehicle string if we have meaningful data
                    hasVehicleData = regState <> "" or registration <> "" or make <> "" or model <> ""
                in
                    if hasVehicleData then
                        let
                            // Build parts safely
                            statePart = if regState <> "" then regState else "",
                            regPart = if registration <> "" then registration else "",
                            makePart = if make <> "" then make else "",
                            modelPart = if model <> "" then model else "",
                            
                            // Combine state and registration with " - "
                            stateReg = if statePart <> "" and regPart <> "" then 
                                statePart & " - " & regPart
                            else if regPart <> "" then regPart
                            else if statePart <> "" then statePart
                            else "",
                            
                            // Combine make and model with "/"
                            makeModel = if makePart <> "" and modelPart <> "" then 
                                makePart & "/" & modelPart
                            else if makePart <> "" then makePart
                            else if modelPart <> "" then modelPart
                            else "",
                            
                            // Final combination with ", "
                            result = if stateReg <> "" and makeModel <> "" then 
                                stateReg & ", " & makeModel
                            else if stateReg <> "" then stateReg
                            else if makeModel <> "" then makeModel
                            else ""
                        in
                            if result = "" then null else result
                    else null, type text),
                    
            // ✅ FIXED vehicle_1_and_vehicle_2: Only when BOTH vehicles exist
            Withvehicle1and2 = Table.AddColumn(Withvehicle2, "vehicle_1_and_vehicle_2", each
                let
                    vehicle1 = [vehicle_1],
                    vehicle2 = [vehicle_2]
                in
                    // Only combine when BOTH vehicles have data
                    if vehicle1 <> null and vehicle2 <> null then 
                        vehicle1 & " | " & vehicle2
                    else null, type text),
            
            // ✅ period calculation
            WithPeriod = Table.AddColumn(WithVehicle1and2, "period", each
                let
                    incidentDate = [incident_date],
                    today = Date.From(DateTime.LocalNow()),
                    daysDiff = if incidentDate <> null then Duration.Days(today - incidentDate) else 999
                in
                    if daysDiff <= 7 then "7-Day"
                    else if daysDiff <= 28 then "28-Day"
                    else if incidentDate <> null and Date.Year(incidentDate) = Date.Year(today) then "YTD"
                    else "Historical", type text),

- rename Squad to "squad" capatlize 

- remaining RMS export transformations:
// ✅ Filter BEFORE unpivot to preserve record count
            FilteredRows = Table.SelectRows(WithPeriod, each 
                [Case Number] <> "25-057654" and [Period] <> "Historical"
            ),
            
            // ✅ MODIFIED UNPIVOT - Keep one row per case for most analyses
            // Only unpivot if you specifically need incident-level analysis
            // For now, create IncidentType from primary incident type
            WithIncidentType = Table.AddColumn(FilteredRows, "IncidentType", each
                let
                    cleanType = if [Incident Type_1] <> null then 
                        if Text.Contains([Incident Type_1], " - 2C") then
                            Text.BeforeDelimiter([Incident Type_1], " - 2C")
                        else [Incident Type_1]
                    else "Unknown"
					
// ✅ TimeOfDay buckets with sort order
            WithTimeOfDay = Table.AddColumn(WithIncidentTime, "time_of_day", each
                let t = [Incident_Time] in
                if t = null then "Unknown"
                else if t >= #time(0,0,0) and t < #time(4,0,0) then "00:00–03:59 Early Morning"
                else if t >= #time(4,0,0) and t < #time(8,0,0) then "04:00–07:59 Morning"
                else if t >= #time(8,0,0) and t < #time(12,0,0) then "08:00–11:59 Morning Peak"
                else if t >= #time(12,0,0) and t < #time(16,0,0) then "12:00–15:59 Afternoon"
                else if t >= #time(16,0,0) and t < #time(20,0,0) then "16:00–19:59 Evening Peak"
                else "20:00–23:59 Night", type text),
                
            WithTimeOfDaySortOrder = Table.AddColumn(WithTimeOfDay, "time_of_day_SortOrder", each
                let t = [Incident_Time] in
                if t = null then 7
                else if t >= #time(0,0,0) and t < #time(4,0,0) then 1
                else if t >= #time(4,0,0) and t < #time(8,0,0) then 2
                else if t >= #time(8,0,0) and t < #time(12,0,0) then 3
                else if t >= #time(12,0,0) and t < #time(16,0,0) then 4
                else if t >= #time(16,0,0) and t < #time(20,0,0) then 5
                else 6, Int64.Type),
            
            // ✅ Date sort key
            WithDateSortKey = Table.AddColumn(Withtime_of_daySortOrder, "Date_SortKey", each
                if [incident_date] <> null then 
                    Date.Year([incident_date]) * 10000 + Date.Month([incident_date]) * 100 + Date.Day([incident_date])
                else null, Int64.Type),
				
// ✅ ENHANCED Block calculation with intersection detection
            WithBlock = Table.AddColumn(WithDateSortKey, "Block", each
                let
                    addr = [location] ?? "",
                    isIntersection = Text.Contains(addr, " & "),
                    cleanAddr = Text.Replace(addr, ", Hackensack, NJ, 07601", ""),
                    intersectionResult = if isIntersection then
                        let
                            beforeAmpersand = Text.Trim(Text.BeforeDelimiter(cleanAddr, " & ")),
                            afterAmpersand = Text.Trim(Text.AfterDelimiter(cleanAddr, " & "))
                        in
                            if beforeAmpersand <> "" and afterAmpersand <> "" then
                                beforeAmpersand & " & " & afterAmpersand
                            else if beforeAmpersand <> "" and afterAmpersand = "" then
                                "Incomplete Address - Check Location Data"
                            else
                                "Incomplete Address - Check Location Data"
                    else
                        let
                            streetNum = try Number.FromText(Text.BeforeDelimiter(cleanAddr, " ")) otherwise null,
                            streetName = Text.Trim(Text.BeforeDelimiter(Text.AfterDelimiter(cleanAddr, " "), ","))
                        in
                            if streetNum <> null and streetName <> "" then 
                                streetName & ", " & Text.From(Number.IntegerDivide(streetNum, 100) * 100) & " Block"
                            else if streetName <> "" then 
                                streetName & ", Unknown Block"
                            else
                                "Check CAD Location Data"
                in
                    intersectionResult, type text),
            
            // ✅ ALL_INCIDENTS with comma separator AND statute code removal
            WithAllIncidents = Table.AddColumn(WithBlock, "all_incidents", each
                let
                    // Clean each incident type by removing " - 2C" and everything after
                    cleanType1 = if [Incident Type_1] <> null then 
                        if Text.Contains([Incident Type_1], " - 2C") then
                            Text.BeforeDelimiter([Incident Type_1], " - 2C")
                        else [Incident Type_1]
                    else null,
                    
                    cleanType2 = if [Incident Type_2] <> null then 
                        if Text.Contains([Incident Type_2], " - 2C") then
                            Text.BeforeDelimiter([Incident Type_2], " - 2C")
                        else [Incident Type_2]
                    else null,
                    
                    cleanType3 = if [Incident Type_3] <> null then 
                        if Text.Contains([Incident Type_3], " - 2C") then
                            Text.BeforeDelimiter([Incident Type_3], " - 2C")
                        else [Incident Type_3]
                    else null
                in
                    Text.Combine(
                        List.RemoveNulls({
                            cleanType1,
                            cleanType2,
                            cleanType3
                        }), ", "
                    ), type text),
					
"season"
```python
# Python (pandas)
def get_season(date):
    if pd.isna(date): return None
    month = date.month
    if month in (12, 1, 2):
        return "Winter"
    elif month in (3, 4, 5):
        return "Spring"
    elif month in (6, 7, 8):
        return "Summer"
    else:
        return "Fall"

df["Season"] = pd.to_datetime(df["Incident_Date"]).dt.date.apply(get_season)

# Group 2: Date & Time Transformations

```m
// Cascading date/time
WithIncidentDate = Table.AddColumn(prev,"incident_date", each
  if [Incident Date]<>null then [Incident Date]
  else if [Incident Date_Between]<>null then [Incident Date_Between]
  else if [Report Date]<>null then [Report Date]
  else null, type date
),
WithIncidentTime = Table.AddColumn(WithIncidentDate,"incident_time", each
  if [Incident Time]<>null then [Incident Time]
  else if [Incident Time_Between]<>null then [Incident Time_Between]
  else if [Report Time]<>null then Time.From([Report Time])
  else null, type time
),
WithTimeOfDay = Table.AddColumn(…, "TimeOfDay", each
  let t=[Incident_Time] in
    if t<#time(4,0,0) then "00:00–03:59 Early Morning"
    … else "20:00–23:59 Night", type text
),
WithTimeOfDaySortOrder = Table.AddColumn(…, "TimeOfDay_SortOrder", each
  let t=[Incident_Time] in
    if t<#time(4,0,0) then 1
    … else 6, Int64.Type
),
WithDateSortKey = Table.AddColumn(…, "Date_SortKey", each
  if [Incident_Date]<>null then
    Date.Year([Incident_Date])*10000
    +Date.Month([Incident_Date])*100
    +Date.Day([Incident_Date])
  else null, Int64.Type
)
```

```python
# Python (pandas)
import numpy as np

# 1) Cascading date
df["Incident_Date"] = (
    pd.to_datetime(df["Incident Date"])
      .fillna(pd.to_datetime(df["Incident Date_Between"]))
      .fillna(pd.to_datetime(df["Report Date"]))
      .dt.date
)

# 2) Cascading time
df["Incident_Time"] = pd.to_datetime(df["Incident Time"]).dt.time
mask = df["Incident_Time"].isna()
df.loc[mask, "Incident_Time"] = pd.to_datetime(
    df.loc[mask, "Incident Time_Between"]
).dt.time

# 3) TimeOfDay bins & sort order
def map_tod(t):
    if pd.isna(t): return "Unknown"
    h = t.hour
    if h < 4:    return "00:00–03:59 Early Morning"
    if h < 8:    return "04:00–07:59 Morning"
    if h < 12:   return "08:00–11:59 Morning Peak"
    if h < 16:   return "12:00–15:59 Afternoon"
    if h < 20:   return "16:00–19:59 Evening Peak"
    return "20:00–23:59 Night"

df["TimeOfDay"] = df["Incident_Time"].apply(map_tod)
order = {
    "00:00–03:59 Early Morning":1, "04:00–07:59 Morning":2,
    "08:00–11:59 Morning Peak":3, "12:00–15:59 Afternoon":4,
    "16:00–19:59 Evening Peak":5, "20:00–23:59 Night":6,
    "Unknown":7
}
df["TimeOfDay_SortOrder"] = df["TimeOfDay"].map(order)

# 4) Date sort key
df["Date_SortKey"] = df["Incident_Date"].apply(
    lambda d: int(d.strftime("%Y%m%d")) if pd.notna(d) else np.nan
)
```

## 5. Season of the Year

```m
WithSeason = Table.AddColumn(PreviousStep, "Season", each
  let m = Date.Month([Incident_Date]) in
    if m in {12, 1, 2} then "Winter"
    else if m in {3, 4, 5} then "Spring"
    else if m in {6, 7, 8} then "Summer"
    else "Fall", type text)
```

```python
# Python (pandas)
def get_season(date):
    if pd.isna(date): return None
    month = date.month
    if month in (12, 1, 2):
        return "Winter"
    elif month in (3, 4, 5):
        return "Spring"
    elif month in (6, 7, 8):
        return "Summer"
    else:
        return "Fall"

df["Season"] = pd.to_datetime(df["Incident_Date"]).dt.date.apply(get_season)
```

## 6. Additional Enrichment Columns

```m
WithDayOfWeek = Table.AddColumn(PreviousStep, "day_of_week", each Date.day_of_weekName([incident_date]), type text),
WithWeekOfYear = Table.AddColumn(PreviousStep, "week_of_year", each Date.week_of_year([incident_date]), Int64.Type),
WithMonthName = Table.AddColumn(PreviousStep, "month_name", each Date.ToText([incident_date], "MMMM"), type text),
WithQuarter = Table.AddColumn(PreviousStep, "quarter", each "Q" & Number.ToText(Date.QuarterOfYear([incident_date])), type text),
WithIsWeekend = Table.AddColumn(PreviousStep, "is_Weekend", each List.Contains({Day.Saturday, Day.Sunday}, Date.DayOfWeek([incident_date])), type logical)
```

```python
# Day of Week
df["day_of_week"] = pd.to_datetime(df["incident_date"]).dt.day_name()
# Week of Year
df["week_of_year"] = pd.to_datetime(df["incident_date"]).dt.isocalendar().week
# Month Name
df["month_name"] = pd.to_datetime(df["incident_date"]).dt.month_name()
# Quarter
df["quarter"] = "Q" + pd.to_datetime(df["incident_date"]).dt.quarter.astype(str)
# Is Weekend
df["is_weekend"] = pd.to_datetime(df["incident_date"]).dt.dayofweek >= 5
```


## 7. Weekday vs Weekend Classification

```m
WithDayType = Table.AddColumn(PreviousStep, "day_type", each 
    if [is_weekend] then "Weekend" 
    else "Weekday", type text)
```

```python
# Python (pandas)
df["day_type"] = df["IsWeekend"].apply(lambda x: "Weekend" if x else "Weekday")
```

Additional CAD Transormation:

// ✅ COMPREHENSIVE TIME CALCULATIONS
            TimeCalculations = Table.AddColumn(#"Promoted Headers", "Time_Response_Minutes", each
                let
                    timeOfCall = [Time of Call],
                    timeDispatched = [Time Dispatched]
                in
                    if timeOfCall <> null and timeDispatched <> null then
                        try
                            let
                                duration = timeDispatched - timeOfCall,
                                minutes = Duration.TotalMinutes(duration)
                            in
                                // Handle negative durations and cap extreme outliers
                                if minutes < 0 then Number.Abs(minutes)
                                else if minutes > 480 then 480  // Cap at 8 hours
                                else Number.Round(minutes, 2)
                        otherwise null
                    else null, type number),
            
            WithTimeSpent = Table.AddColumn(TimeCalculations, "Time_Spent_Minutes", each
                let
                    timeOut = [Time Out],
                    timeIn = [Time In]
                in
                    if timeOut <> null and timeIn <> null then
                        try
                            let
                                duration = timeIn - timeOut,
                                minutes = Duration.TotalMinutes(duration)
                            in
                                // Handle negative durations and cap extreme outliers
                                if minutes < 0 then Number.Abs(minutes)
                                else if minutes > 720 then 720  // Cap at 12 hours
                                else Number.Round(minutes, 2)
                        otherwise null
                    else null, type number),

            // ✅ COMPREHENSIVE CADNotes CLEANING
            WithCleanedCADNotes = Table.TransformColumns(WithTimeSpent, {
                {"CADNotes", each 
                    let
                        notes = _ ?? ""
                    in
                        if notes = "" then ""
                        else
                            let
                                // Remove line breaks
                                step1 = Text.Replace(Text.Replace(Text.Replace(notes, "#(cr)#(lf)", " "), "#(lf)", " "), "#(cr)", " "),
                                // Remove "? - ? - ?" patterns
                                step2 = Text.Replace(step1, "? - ? - ?", ""),
                                // Remove timestamp patterns and usernames
                                step3 = Text.Replace(step2, Text.BeforeDelimiter(step2 & " - ", " - "), ""),
                                // Remove excessive whitespace
                                step4 = Text.Replace(Text.Replace(Text.Replace(step3, "    ", " "), "   ", " "), "  ", " "),
                                // Clean and trim
                                step5 = Text.Clean(Text.Trim(step4)),
                                // Handle empty results
                                final = if step5 = "" or step5 = "-" then null else step5
                            in
                                final, type text
                }
            }),

            // ✅ ENHANCED Block calculation (FIXED intersection logic)
            WithBlock = Table.AddColumn(WithCleanedCADNotes, "Block", each
                let
                    addr = [FullAddress2] ?? "",
                    isIntersection = Text.Contains(addr, " & "),
                    
                    // Clean address by removing ", Hackensack, NJ, 07601"
                    cleanAddr = Text.Replace(addr, ", Hackensack, NJ, 07601", ""),
                    
                    // Handle intersections - PRESERVE FULL STREET NAMES
                    intersectionResult = if isIntersection then
                        let
                            // Split on " & " and preserve both full street names
                            beforeAmpersand = Text.Trim(Text.BeforeDelimiter(cleanAddr, " & ")),
                            afterAmpersand = Text.Trim(Text.AfterDelimiter(cleanAddr, " & "))
                        in
                            if beforeAmpersand <> "" and afterAmpersand <> "" then
                                beforeAmpersand & " & " & afterAmpersand
                            else if beforeAmpersand <> "" and afterAmpersand = "" then
                                "Incomplete Address - Check Location Data"
                            else
                                "Incomplete Address - Check Location Data"
                    else
                        // Handle non-intersections (regular addresses)
                        let
                            streetNum = try Number.FromText(Text.BeforeDelimiter(cleanAddr, " ")) otherwise null,
                            streetName = Text.Trim(Text.BeforeDelimiter(Text.AfterDelimiter(cleanAddr, " "), ","))
                        in
                            if streetNum <> null and streetName <> "" then 
                                streetName & ", " & Text.From(Number.IntegerDivide(streetNum, 100) * 100) & " Block"
                            else if streetName <> "" then 
                                streetName & ", Unknown Block"
                            else
                                "Incomplete Address - Check Location Data"
                in
                    intersectionResult, type text)
        in
            WithBlock,

    InvokedCustom = Table.AddColumn(LatestFile, "Transform_File", each Transform_File([Content])),
    #"Expanded Transform_File" = Table.ExpandTableColumn(InvokedCustom, "Transform_File", Table.ColumnNames(Transform_File(LatestFile{0}[Content]))),
    #"Removed Other Columns" = Table.SelectColumns(#"Expanded Transform_File", Table.ColumnNames(Transform_File(LatestFile{0}[Content]))),
    #"Filtered Rows" = Table.SelectRows(#"Removed Other Columns", each ([CADNotes] <> "- kiselow_g - 1/4/2025 11:00:23 AM night - kiselow_g - 1/4/2025 11:00:23 AM"))