// 🕒 2025-07-23-16-00-00
// Project: SCRPA_Time_v2/ALL_CRIMES
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
                [Case Number] <> null and [Period] <> "Historical"
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
    #"Expanded Transform_File" = Table.ExpandTableColumn(InvokedCustom, "Transform_File", {
        "Case Number", "Incident_Date", "Incident_Time", "TimeOfDay", "TimeOfDay_SortOrder", 
        "Date_SortKey", "Block", "ALL_INCIDENTS", "Vehicle_1", "Vehicle_2", 
        "Vehicle_1_and_Vehicle_2", "Period", "IncidentType", "Crime_Category", "Narrative",
        "FullAddress", "Squad", "Officer of Record"
    }),
    #"Removed Other Columns" = Table.SelectColumns(#"Expanded Transform_File", {
        "Case Number", "Incident_Date", "Incident_Time", "TimeOfDay", "TimeOfDay_SortOrder", 
        "Date_SortKey", "Block", "ALL_INCIDENTS", "Vehicle_1", "Vehicle_2", 
        "Vehicle_1_and_Vehicle_2", "Period", "IncidentType", "Crime_Category", "Narrative",
        "FullAddress", "Squad", "Officer of Record"
    })
in
    #"Removed Other Columns"