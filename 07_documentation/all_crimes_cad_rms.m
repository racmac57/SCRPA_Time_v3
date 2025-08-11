// 🕒 2025-07-23-16-30-00
// Project: SCRPA_Time_v2/CAD_RMS_Matched_FIXED_Duration_Formatting
// Author: R. A. Carucci
// Purpose: Fixed duration formatting with proper error handling, plus CADNotes username/timestamp extraction and cleaning

let
    // 1) Load both datasets
    SourceRMS      = ALL_CRIMES,
    SourceCAD      = CAD_DATA,

    // 2) Rename conflicting columns BEFORE joining
    RMSRenamed     = Table.RenameColumns(
                       SourceRMS,
                       {
                         {"Grid", "RMS_Grid"},
                         {"Zone", "RMS_Zone"},
                         {"Officer of Record", "RMS_Officer"},
                         {"Block", "RMS_Block"}
                       },
                       MissingField.Ignore
                     ),
    CADRenamed     = Table.RenameColumns(
                       SourceCAD,
                       {
                         {"Grid", "CAD_Grid"},
                         {"PDZone", "CAD_Zone"},
                         {"Officer", "CAD_Officer"},
                         {"Block", "CAD_Block"},
                         {"Disposition", "CAD_Disposition"},
                         {"Response Type", "CAD_Response_Type"}
                       },
                       MissingField.Ignore
                     ),

    // 3) LEFT JOIN RMS with CAD on Case Number → ReportNumberNew
    JoinedData     = Table.Join(
                       RMSRenamed, {"Case Number"},
                       CADRenamed, {"ReportNumberNew"},
                       JoinKind.LeftOuter
                     ),

    // 4) Flag whether CAD data exists
    WithCADFlag    = Table.AddColumn(
                       JoinedData,
                       "Has_CAD_Data",
                       each if [ReportNumberNew] <> null then "Yes" else "No",
                       type text
                     ),

    // 5) Parse CADNotes into CAD_Username, CAD_Timestamp & CAD_Notes_Cleaned
    WithParsedCADNotes = Table.AddColumn(
      WithCADFlag,
      "CADNotes_Parsed",
      each let
        raw            = [CADNotes] ?? "",
        // split into lines and pick the first non‑empty header
        lines          = Text.Split(raw, "#(lf)"),
        nonEmptyLines  = List.Select(lines, each Text.Trim(_) <> ""),
        header         = if List.Count(nonEmptyLines)>0 then nonEmptyLines{0} else "",

        // 5a) Username = first underscore token or blank
        headerTokens   = Text.Split(Text.Trim(header), " "),
        userCandidates = List.Select(headerTokens, each Text.Contains(_, "_")),
        userRaw        = if List.Count(userCandidates)>0 then userCandidates{0} else "",
        CAD_Username   = if Text.Length(userRaw)>0
                         then Text.Combine(
                                List.Transform(Text.Split(userRaw, "_"), each Text.Proper(_)),
                                "_"
                              )
                         else null,

        // 5b) Timestamp = first date token + next token
        dateTokens     = List.Select(headerTokens, each Text.Contains(_, "/")),
        dateRaw        = if List.Count(dateTokens)>0 then dateTokens{0} else "",
        dateIndex      = if dateRaw<>"" then List.PositionOf(headerTokens, dateRaw) else -1,
        timeRaw        = if dateIndex>=0 and dateIndex < List.Count(headerTokens)-1
                         then headerTokens{dateIndex+1} else "",
        dtRaw          = if dateRaw<>"" and timeRaw<>"" then dateRaw & " " & timeRaw else "",
        dtParsed       = try DateTime.FromText(dtRaw) otherwise null,
        CAD_Timestamp  = if dtParsed<>null then DateTime.ToText(dtParsed,"MM/dd/yyyy HH:mm:ss") else null,

        // 5c) Remove header, dtRaw, userRaw from the full text
        combinedLines  = Text.Combine(lines, " "),
        withoutHdr     = Text.Replace(combinedLines, header, ""),
        withoutDt      = Text.Replace(withoutHdr, dtRaw, ""),
        withoutUser    = Text.Replace(withoutDt, userRaw, ""),

        // 5d) Tokenize & filter stray tokens
        toks           = Text.Split(Text.Trim(withoutUser), " "),
        keepTokens     = List.Select(toks, each let t=Text.Trim(_) in
                            t<>"" and
                            not (Text.Contains(t,"/") and Text.Contains(t,":")) and
                            not Text.StartsWith(t,"(") and
                            not Text.EndsWith(t,")") and
                            not Text.StartsWith(t,"#") and
                            Text.Lower(t)<>"cc" and
                            Text.Trim(Text.Remove(t,{"-","?"}))<>""
                          ),

        // 5e) Recombine & proper‑case narrative
        combined       = Text.Combine(keepTokens, " "),
        CAD_Notes_Cleaned = if Text.Length(combined)=0 then null else Text.Proper(combined)

      in
        [
          CAD_Username      = CAD_Username,
          CAD_Timestamp     = CAD_Timestamp,
          CAD_Notes_Cleaned = CAD_Notes_Cleaned
        ],
      type record
    ),

    // 6) Expand parsed record into three columns
    ExpandedCADNotes = Table.ExpandRecordColumn(
                         WithParsedCADNotes,
                         "CADNotes_Parsed",
                         {"CAD_Username","CAD_Timestamp","CAD_Notes_Cleaned"},
                         {"CAD_Username","CAD_Timestamp","CAD_Notes_Cleaned"}
                       ),

    // 7) FIXED Time_Spent Formatting
    WithTimeSpentFormatted = Table.AddColumn(
      ExpandedCADNotes,
      "Time_Spent_Formatted",
      each let m=[Time_Spent_Minutes] in
        if m=null then null else try
          let
            vm=Number.Round(Number.From(m),0),
            h=Number.IntegerDivide(vm,60),
            r=Number.Mod(vm,60)
          in
            if vm<=0 then "0 Mins"
            else if h=0 then Text.From(r)&" Mins"
            else if r=0 then Text.From(h)&" Hrs"
            else Text.From(h)&" Hrs "&Text.PadStart(Text.From(r),2,"0")&" Mins"
        otherwise "Invalid Time",
      type text
    ),
    WithTimeSpentFlag = Table.AddColumn(
      WithTimeSpentFormatted,
      "Time_Spent_Flag",
      each let m=[Time_Spent_Minutes] in
        if m=null then null else try
          let v=Number.From(m) in
            if v<5 then "Under 5 Minutes"
            else if v>300 then "Over 5 Hours"
            else "Normal"
        otherwise "Invalid",
      type text
    ),

    // 8) FIXED Time_Response Formatting
    WithTimeResponseFormatted = Table.AddColumn(
      WithTimeSpentFlag,
      "Time_Response_Formatted",
      each let m=[Time_Response_Minutes] in
        if m=null then null else try
          let
            totalSec=Number.Round(Number.From(m)*60,0),
            mins=Number.IntegerDivide(totalSec,60),
            secs=Number.Mod(totalSec,60)
          in
            if totalSec<=0 then "0 Secs"
            else if mins=0 then Text.From(secs)&" Secs"
            else if secs=0 then Text.From(mins)&" Mins"
            else Text.From(mins)&" Mins "&Text.PadStart(Text.From(secs),2,"0")&" Secs"
        otherwise "Invalid Time",
      type text
    ),
    WithTimeResponseFlag = Table.AddColumn(
      WithTimeResponseFormatted,
      "Time_Response_Flag",
      each let m=[Time_Response_Minutes] in
        if m=null then null else try
          let v=Number.From(m) in
            if v<=1 then "0-1 Minutes"
            else if v>10 then "Over 10 Minutes"
            else "Normal"
        otherwise "Invalid",
      type text
    ),

    // 9) Unified Grid / Zone & Enhanced Block
    WithUnifiedGrid = Table.AddColumn(
      WithTimeResponseFlag,
      "Grid",
      each if [CAD_Grid]<>null then [CAD_Grid] else [RMS_Grid],
      type text
    ),
    WithUnifiedZone = Table.AddColumn(
      WithUnifiedGrid,
      "Zone",
      each if [CAD_Zone]<>null then [CAD_Zone] else [RMS_Zone],
      type text
    ),
    WithEnhancedBlock = Table.AddColumn(
      WithUnifiedZone,
      "Enhanced_Block",
      each let
        rm=[RMS_Block],
        cb=[CAD_Block]
      in
        if (Text.Contains(rm??"","Check CAD Location Data") or Text.Contains(rm??"","Incomplete Address")) and cb<>null
        then cb else rm,
      type text
    ),

    // 10) Unified Officer
    WithUnifiedOfficer = Table.AddColumn(
      WithEnhancedBlock,
      "Officer",
      each if [CAD_Officer]<>null then [CAD_Officer] else [RMS_Officer],
      type text
    ),

    // 11) Select final columns
    FinalColumns = Table.SelectColumns(
      WithUnifiedOfficer,
      {
        "Case Number","ReportNumberNew","Incident_Date","Incident_Time",
        "IncidentType","ALL_INCIDENTS","Crime_Category","TimeOfDay","Period",
        "Officer","Grid","Zone","RMS_Block","CAD_Block","Enhanced_Block",
        "Has_CAD_Data",
        "Time_Response_Minutes","Time_Response_Formatted","Time_Response_Flag",
        "Time_Spent_Minutes","Time_Spent_Formatted","Time_Spent_Flag",
        "CADNotes","CAD_Notes_Cleaned","CAD_Username","CAD_Timestamp",
        "CAD_Disposition","CAD_Response_Type"
      }
    )
in
    FinalColumns
	
// 🕒 2025-07-23-16-00-00
// Project: SCRPA_Time_v2/Fixed_ALL_CRIMES_Complete
// Author: R. A. Carucci
// Purpose: Complete ALL_CRIMES with fixed unpivot logic that preserves all 130 records

let
    Source = Folder.Files("C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA"),
    FilteredExcel = Table.SelectRows(Source, each [Extension] = ".xlsx" and Record.FieldOrDefault([Attributes], "Hidden", false) <> true),
    Sorted = Table.Sort(FilteredExcel,{{"Date modified", Order.Descending}}),
    LatestFile = Table.FirstN(Sorted, 1),
    
    Transform_File = (Parameter2 as binary) =>
        let
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
            
            // ✅ NORMALIZED TEXT COLUMNS
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
            
            // ✅ FIXED VEHICLE COLUMNS with proper text concatenation
            WithVehicle1 = Table.AddColumn(WithAllIncidents, "Vehicle_1", each
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
                    
            WithVehicle2 = Table.AddColumn(WithVehicle1, "Vehicle_2", each
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
                    
            // ✅ FIXED Vehicle_1_and_Vehicle_2: Only when BOTH vehicles exist
            WithVehicle1and2 = Table.AddColumn(WithVehicle2, "Vehicle_1_and_Vehicle_2", each
                let
                    vehicle1 = [Vehicle_1],
                    vehicle2 = [Vehicle_2]
                in
                    // Only combine when BOTH vehicles have data
                    if vehicle1 <> null and vehicle2 <> null then 
                        vehicle1 & " | " & vehicle2
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
                in
                    cleanType, type text),
            
            // ✅ Crime categorization using primary incident type
            WithCrimeCategory = Table.AddColumn(WithIncidentType, "Crime_Category", each
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
            
            // ✅ METHOD 3: Comprehensive narrative cleaning
            ComprehensiveCleanedNarrative = Table.TransformColumns(WithCrimeCategory, {
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
	
// 🕒 2025-07-23-16-00-00
// Project: SCRPA_Time_v2/Final_CAD_DATA_Script
// Author: R. A. Carucci
// Purpose: Complete CAD_DATA query with time calculations, CADNotes cleaning, and fixed block logic

let
    Source = Folder.Files("C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA"),
    FilteredExcel = Table.SelectRows(Source, each [Extension] = ".xlsx" and Record.FieldOrDefault([Attributes], "Hidden", false) <> true),
    Sorted = Table.Sort(FilteredExcel,{{"Date modified", Order.Descending}}),
    LatestFile = Table.FirstN(Sorted, 1),

    Transform_File = (Parameter2 as binary) =>
        let
            Source = Excel.Workbook(Parameter2, null, true),
            FilteredSheets = Table.SelectRows(Source, each [Kind] = "Sheet"),
            Sheet1_Sheet = if Table.RowCount(FilteredSheets) > 0 then FilteredSheets{0}[Data] else error "No valid CAD sheets found",

            #"Promoted Headers" = Table.PromoteHeaders(Sheet1_Sheet, [PromoteAllScalars=true]),
            
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
in
    #"Filtered Rows"