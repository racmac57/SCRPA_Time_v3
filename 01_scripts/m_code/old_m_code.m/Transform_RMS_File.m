// =============================================================================
// RMS TRANSFORMATION FUNCTION - COPY THIS EXACTLY
// =============================================================================

(Parameter2 as binary) =>
let
    Source = Excel.Workbook(Parameter2, null, true),
    Sheet1_Sheet = Source{[Item="Sheet1",Kind="Sheet"]}[Data],
    #"Promoted Headers" = Table.PromoteHeaders(Sheet1_Sheet, [PromoteAllScalars=true]),
    
    // STEP 1: STANDARDIZE COLUMN NAMES
    StandardizedColumns = Table.RenameColumns(#"Promoted Headers", {
        {"Case Number", "Case_Number"},
        {"Incident Date", "Incident_Date_Raw"},
        {"Incident Time", "Incident_Time_Raw"},
        {"Incident Date_Between", "Incident_Date_Between_Raw"},
        {"Incident Time_Between", "Incident_Time_Between_Raw"},
        {"Report Date", "Report_Date_Raw"},
        {"Report Time", "Report_Time_Raw"},
        {"Incident Type_1", "Incident_Type_1_Raw"},
        {"Incident Type_2", "Incident_Type_2_Raw"},
        {"Incident Type_3", "Incident_Type_3_Raw"},
        {"FullAddress", "Full_Address_Raw"},
        {"Grid", "Grid_Raw"},
        {"Zone", "Zone_Raw"},
        {"Narrative", "Narrative_Raw"},
        {"Total Value Stolen", "Total_Value_Stolen"},
        {"Total Value Recover", "Total_Value_Recovered"},
        {"Registration 1", "Registration_1"},
        {"Make1", "Make_1"},
        {"Model1", "Model_1"},
        {"Reg State 1", "Reg_State_1"},
        {"Registration 2", "Registration_2"},
        {"Reg State 2", "Reg_State_2"},
        {"Make2", "Make_2"},
        {"Model2", "Model_2"},
        {"Reviewed By", "Reviewed_By"},
        {"CompleteCalc", "Complete_Calc"},
        {"Officer of Record", "Officer_Of_Record"},
        {"Squad", "Squad"},
        {"Det_Assigned", "Det_Assigned"},
        {"Case_Status", "Case_Status"},
        {"NIBRS Classification", "NIBRS_Classification"}
    }, MissingField.Ignore),
    
    // STEP 2: CASCADING DATE
    WithIncidentDate = Table.AddColumn(StandardizedColumns, "Incident_Date", each
        if [Incident_Date_Raw] <> null then Date.From([Incident_Date_Raw])
        else if [Incident_Date_Between_Raw] <> null then Date.From([Incident_Date_Between_Raw])
        else if [Report_Date_Raw] <> null then Date.From([Report_Date_Raw])
        else null, type nullable date),
    
    // STEP 3: CASCADING TIME
    WithIncidentTime = Table.AddColumn(WithIncidentDate, "Incident_Time", each
        if [Incident_Time_Raw] <> null then Time.From([Incident_Time_Raw])
        else if [Incident_Time_Between_Raw] <> null then Time.From([Incident_Time_Between_Raw])
        else if [Report_Time_Raw] <> null then Time.From([Report_Time_Raw])
        else null, type nullable time),
    
    // STEP 4: TIME OF DAY
    WithTimeOfDay = Table.AddColumn(WithIncidentTime, "Time_Of_Day", each
        let t = [Incident_Time] in
        if t = null then "Unknown"
        else if t >= #time(0,0,0) and t < #time(4,0,0) then "00:00–03:59 Early Morning"
        else if t >= #time(4,0,0) and t < #time(8,0,0) then "04:00–07:59 Morning"
        else if t >= #time(8,0,0) and t < #time(12,0,0) then "08:00–11:59 Morning Peak"
        else if t >= #time(12,0,0) and t < #time(16,0,0) then "12:00–15:59 Afternoon"
        else if t >= #time(16,0,0) and t < #time(20,0,0) then "16:00–19:59 Evening Peak"
        else "20:00–23:59 Night", type text),
    
    // STEP 5: PERIOD
    WithPeriod = Table.AddColumn(WithTimeOfDay, "Period", each
        let
            incidentDate = [Incident_Date],
            today = Date.From(DateTime.LocalNow()),
            daysDiff = if incidentDate <> null then Duration.Days(today - incidentDate) else 999
        in
            if daysDiff <= 7 then "7-Day"
            else if daysDiff <= 28 then "28-Day"
            else if incidentDate <> null and Date.Year(incidentDate) = Date.Year(today) then "YTD"
            else "Historical", type text),
    
    // STEP 6: UNIFIED LOCATION
    WithLocation = Table.AddColumn(WithPeriod, "Location", each [Full_Address_Raw], type text),
    WithGrid = Table.AddColumn(WithLocation, "Grid", each [Grid_Raw], type text),
    WithPost = Table.AddColumn(WithGrid, "Post", each [Zone_Raw], type text),
    
    // STEP 7: BLOCK CALCULATION
    WithBlock = Table.AddColumn(WithPost, "Block", each
        let
            addr = [Location] ?? "",
            isIntersection = Text.Contains(addr, " & "),
            cleanAddr = Text.Replace(addr, ", Hackensack, NJ, 07601", "")
        in
            if isIntersection then
                let
                    beforeAmpersand = Text.Trim(Text.BeforeDelimiter(cleanAddr, " & ")),
                    afterAmpersand = Text.Trim(Text.AfterDelimiter(cleanAddr, " & "))
                in
                    if beforeAmpersand <> "" and afterAmpersand <> "" then
                        beforeAmpersand & " & " & afterAmpersand
                    else "Incomplete Address - Check Location Data"
            else
                let
                    streetNum = try Number.FromText(Text.BeforeDelimiter(cleanAddr, " ")) otherwise null,
                    streetName = Text.Trim(Text.BeforeDelimiter(Text.AfterDelimiter(cleanAddr, " "), ","))
                in
                    if streetNum <> null and streetName <> "" then 
                        streetName & ", " & Text.From(Number.IntegerDivide(streetNum, 100) * 100) & " Block"
                    else if streetName <> "" then 
                        streetName & ", Unknown Block"
                    else "Check Location Data", type text),
    
    // STEP 8: CLEAN INCIDENT TYPES
    WithAllIncidents = Table.AddColumn(WithBlock, "All_Incidents", each
        let
            cleanType1 = if [Incident_Type_1_Raw] <> null then 
                if Text.Contains([Incident_Type_1_Raw], " - 2C") then
                    Text.BeforeDelimiter([Incident_Type_1_Raw], " - 2C")
                else [Incident_Type_1_Raw]
            else null,
            
            cleanType2 = if [Incident_Type_2_Raw] <> null then 
                if Text.Contains([Incident_Type_2_Raw], " - 2C") then
                    Text.BeforeDelimiter([Incident_Type_2_Raw], " - 2C")
                else [Incident_Type_2_Raw]
            else null,
            
            cleanType3 = if [Incident_Type_3_Raw] <> null then 
                if Text.Contains([Incident_Type_3_Raw], " - 2C") then
                    Text.BeforeDelimiter([Incident_Type_3_Raw], " - 2C")
                else [Incident_Type_3_Raw]
            else null
        in
            Text.Combine(List.RemoveNulls({cleanType1, cleanType2, cleanType3}), ", "), type text),
    
    // STEP 9: PRIMARY INCIDENT TYPE
    WithIncidentType = Table.AddColumn(WithAllIncidents, "Incident_Type", each
        let
            cleanType = if [Incident_Type_1_Raw] <> null then 
                if Text.Contains([Incident_Type_1_Raw], " - 2C") then
                    Text.BeforeDelimiter([Incident_Type_1_Raw], " - 2C")
                else [Incident_Type_1_Raw]
            else "Unknown"
        in cleanType, type text),
    
    // STEP 10: CLEAN NARRATIVE
    WithNarrative = Table.AddColumn(WithIncidentType, "Narrative", each
        let
            raw = [Narrative_Raw] ?? ""
        in
            if raw = "" then null
            else
                let
                    step1 = Text.Replace(Text.Replace(raw, "#(cr)#(lf)", " "), "#(lf)", " "),
                    step2 = Text.Replace(step1, "#(cr)", " "),
                    step3 = Text.Replace(Text.Replace(Text.Replace(step2, "    ", " "), "   ", " "), "  ", " "),
                    cleaned = Text.Clean(Text.Trim(step3))
                in
                    if cleaned = "" then null else cleaned, type text),
    
    // STEP 11: SELECT FINAL COLUMNS
    FinalColumns = Table.SelectColumns(WithNarrative, {
        "Case_Number",
        "Incident_Date", 
        "Incident_Time",
        "Time_Of_Day",
        "Period",
        "Location",
        "Block", 
        "Grid",
        "Post",
        "All_Incidents",
        "Incident_Type", 
        "Narrative",
        "Total_Value_Stolen",
        "Total_Value_Recovered",
        "Squad",
        "Officer_Of_Record",
        "NIBRS_Classification"
    }),
    
    // STEP 12: FILTER
    FilteredRows = Table.SelectRows(FinalColumns, each 
        [Case_Number] <> "25-057654" and [Period] <> "Historical"
    )
in
    FilteredRows