// =============================================================================
// CAD TRANSFORMATION FUNCTION - COPY THIS EXACTLY  
// =============================================================================

(Parameter2 as binary) =>
let
    Source = Excel.Workbook(Parameter2, null, true),
    Sheet1_Sheet = Source{[Item="Sheet1",Kind="Sheet"]}[Data],
    #"Promoted Headers" = Table.PromoteHeaders(Sheet1_Sheet, [PromoteAllScalars=true]),
    
    // STEP 1: STANDARDIZE CAD COLUMN NAMES
    StandardizedColumns = Table.RenameColumns(#"Promoted Headers", {
        {"ReportNumberNew", "Case_Number"},
        {"Incident", "Response_Type_Raw"},
        {"How Reported", "How_Reported"},
        {"FullAddress2", "Full_Address_Raw"},
        {"PDZone", "Post_Raw"},
        {"Grid", "Grid_Raw"},
        {"Time of Call", "Time_Of_Call"},
        {"Time Dispatched", "Time_Dispatched"},
        {"Time Out", "Time_Out"},
        {"Time In", "Time_In"},
        {"Officer", "Officer"},
        {"Disposition", "Disposition"},
        {"Response Type", "Response_Type"},
        {"CADNotes", "CAD_Notes_Raw"}
    }, MissingField.Ignore),
    
    // STEP 2: TIME CALCULATIONS
    WithTimeResponse = Table.AddColumn(StandardizedColumns, "Time_Response_Minutes", each
        let
            timeOfCall = [Time_Of_Call],
            timeDispatched = [Time_Dispatched]
        in
            if timeOfCall <> null and timeDispatched <> null then
                try
                    let
                        duration = timeDispatched - timeOfCall,
                        minutes = Duration.TotalMinutes(duration)
                    in
                        if minutes < 0 then Number.Abs(minutes)
                        else if minutes > 480 then 480
                        else Number.Round(minutes, 2)
                otherwise null
            else null, type number),
    
    WithTimeSpent = Table.AddColumn(WithTimeResponse, "Time_Spent_Minutes", each
        let
            timeOut = [Time_Out],
            timeIn = [Time_In]
        in
            if timeOut <> null and timeIn <> null then
                try
                    let
                        duration = timeIn - timeOut,
                        minutes = Duration.TotalMinutes(duration)
                    in
                        if minutes < 0 then Number.Abs(minutes)
                        else if minutes > 720 then 720
                        else Number.Round(minutes, 2)
                otherwise null
            else null, type number),
    
    // STEP 3: UNIFIED COLUMNS
    WithLocation = Table.AddColumn(WithTimeSpent, "Location", each [Full_Address_Raw], type text),
    WithGrid = Table.AddColumn(WithLocation, "Grid", each [Grid_Raw], type text),
    WithPost = Table.AddColumn(WithGrid, "Post", each [Post_Raw], type text),
    
    // STEP 4: BLOCK CALCULATION
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
    
    // STEP 5: CLEAN CAD NOTES
    WithCleanedCADNotes = Table.AddColumn(WithBlock, "CAD_Notes_Cleaned", each
        let
            notes = [CAD_Notes_Raw] ?? ""
        in
            if notes = "" then null
            else
                let
                    step1 = Text.Replace(Text.Replace(Text.Replace(notes, "#(cr)#(lf)", " "), "#(lf)", " "), "#(cr)", " "),
                    step2 = Text.Replace(step1, "? - ? - ?", ""),
                    step3 = Text.Replace(Text.Replace(Text.Replace(step2, "    ", " "), "   ", " "), "  ", " "),
                    step4 = Text.Clean(Text.Trim(step3)),
                    final = if step4 = "" or step4 = "-" then null else step4
                in
                    final, type text),
    
    // STEP 6: SELECT FINAL COLUMNS
    FinalCADColumns = Table.SelectColumns(WithCleanedCADNotes, {
        "Case_Number",
        "Response_Type",
        "How_Reported",
        "Location",
        "Block",
        "Grid", 
        "Post",
        "Time_Of_Call",
        "Time_Dispatched",
        "Time_Out",
        "Time_In",
        "Time_Spent_Minutes",
        "Time_Response_Minutes",
        "Officer",
        "Disposition",
        "CAD_Notes_Cleaned"
    })
in
    FinalCADColumns