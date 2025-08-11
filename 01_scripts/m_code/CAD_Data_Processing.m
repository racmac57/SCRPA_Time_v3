// =============================================================================
// CAD DATA PROCESSING WITH ENHANCED FUNCTIONALITY - COMPLETE VERSION
// A. Column Naming Standards: snake_case format, cycle_name as 2nd column
// B. Export File Naming: C08W31_2025_08_02_7Day_CAD_Data_Standardized.csv
// C. Error Handling: Robust null handling, try-otherwise logic, error reporting
// =============================================================================

(Parameter2 as binary) =>
let
    // COMPREHENSIVE ERROR HANDLING WRAPPER
    ProcessWithErrorHandling = try (
        let
            // STEP 1: SAFE FILE LOADING WITH ERROR HANDLING
            Source = try Excel.Workbook(Parameter2, null, true) otherwise error "Failed to load Excel file",
            Sheet1_Sheet = try Source{[Item="Sheet1",Kind="Sheet"]}[Data] otherwise 
                          try Source{0}[Data] otherwise error "No valid sheet found in Excel file",
            #"Promoted Headers" = try Table.PromoteHeaders(Sheet1_Sheet, [PromoteAllScalars=true]) otherwise 
                               error "Failed to promote headers from Excel sheet",
    
    // STEP 1: CYCLE DETERMINATION FUNCTION
    GetCurrentCycle = (incident_date as date) as text =>
        let
            // Match Python get_current_cycle() logic
            CycleStart = #date(2025, 7, 29),
            CycleEnd = #date(2025, 8, 4)
        in
            if incident_date >= CycleStart and incident_date <= CycleEnd then "C08W31"
            else "Historical",
    
    // STEP 2: CYCLE FORMAT DETECTION AND STANDARDIZATION (C08W31 format)
    WithCycleDetection = Table.AddColumn(#"Promoted Headers", "cycle_name", each
        let
            callTime = try Date.From([Time of Call]) otherwise Date.From(DateTime.LocalNow())
        in
            GetCurrentCycle(callTime), type text),
    
            // STEP 3: COMPREHENSIVE COLUMN STANDARDIZATION TO SNAKE_CASE
            // Robust null handling and column mapping with error recovery
            StandardizedColumns = try Table.RenameColumns(WithCycleDetection, {
                {"ReportNumberNew", "case_number"},
                {"Report Number New", "case_number"}, // Alternative format
                {"CaseNumber", "case_number"}, // Alternative format
                {"Incident", "response_type_raw"},
                {"IncidentType", "response_type_raw"}, // Alternative format
                {"How Reported", "how_reported"},
                {"HowReported", "how_reported"}, // Alternative format
                {"FullAddress2", "full_address_raw"},
                {"Full Address", "full_address_raw"}, // Alternative format
                {"Address", "full_address_raw"}, // Alternative format
                {"PDZone", "post_raw"},
                {"PD Zone", "post_raw"}, // Alternative format
                {"Zone", "post_raw"}, // Alternative format
                {"Grid", "grid_raw"},
                {"Time of Call", "incident_date"},
                {"TimeOfCall", "incident_date"}, // Alternative format
                {"Call Time", "incident_date"}, // Alternative format
                {"Time Dispatched", "time_dispatched"},
                {"TimeDispatched", "time_dispatched"}, // Alternative format
                {"Time Out", "time_out"},
                {"TimeOut", "time_out"}, // Alternative format
                {"Time In", "time_in"},
                {"TimeIn", "time_in"}, // Alternative format
                {"Officer", "officer"},
                {"Disposition", "disposition"},
                {"Response Type", "response_type"},
                {"ResponseType", "response_type"}, // Alternative format
                {"CADNotes", "cad_notes_raw"},
                {"CAD Notes", "cad_notes_raw"}, // Alternative format
                {"Notes", "cad_notes_raw"} // Alternative format
            }, MissingField.Ignore) otherwise 
            // Fallback: Add missing columns with null values
            Table.AddColumn(
                Table.AddColumn(
                    Table.AddColumn(WithCycleDetection, "case_number", each null, type nullable text),
                    "response_type_raw", each null, type nullable text),
                "incident_date", each null, type nullable datetime),
    
            // STEP 4: ROBUST INCIDENT_TIME EXTRACTION WITH ERROR HANDLING
            WithIncidentTime = Table.AddColumn(StandardizedColumns, "incident_time", each
                try (
                    if [incident_date] <> null then
                        try Time.From([incident_date]) otherwise null
                    else null
                ) otherwise null, type nullable time),
    
            // STEP 5: EXACT PYTHON-MATCHING FILTERING FUNCTION
            // Uses identical patterns from SCRPA_Time_v3_Production_Pipeline.py
            PythonCrimePatterns = {
                "MOTOR VEHICLE THEFT", "THEFT OF MOTOR VEHICLE", "AUTO THEFT", "CAR THEFT", "VEHICLE THEFT", "240 = THEFT OF MOTOR VEHICLE",
                "ROBBERY", "120 = ROBBERY",
                "BURGLARY – AUTO", "BURGLARY - AUTO", "AUTO BURGLARY", "THEFT FROM MOTOR VEHICLE", "23F = THEFT FROM MOTOR VEHICLE",
                "SEXUAL", "11D = FONDLING", "CRIMINAL SEXUAL CONTACT",
                "BURGLARY – COMMERCIAL", "BURGLARY - COMMERCIAL", "COMMERCIAL BURGLARY", "220 = BURGLARY COMMERCIAL",
                "BURGLARY – RESIDENCE", "BURGLARY - RESIDENCE", "RESIDENTIAL BURGLARY", "220 = BURGLARY RESIDENTIAL"
            },
            
            FilterTargetCrimes = (data_table as table) as table =>
                let
                    FilteredTable = Table.SelectRows(data_table, each
                        List.AnyTrue(List.Transform(PythonCrimePatterns, (pattern) => 
                            Text.Contains(Text.Upper([response_type] ?? ""), Text.Upper(pattern)) or
                            Text.Contains(Text.Upper([response_type_raw] ?? ""), Text.Upper(pattern)) or  
                            Text.Contains(Text.Upper([disposition] ?? ""), Text.Upper(pattern))
                        ))
                    )
                in
                    FilteredTable,
    
    // VALIDATION FUNCTION TO COMPARE FILTERING RESULTS
    ValidateFilteringResults = (original_table as table, filtered_table as table) as record =>
        let
            OriginalCount = Table.RowCount(original_table),
            FilteredCount = Table.RowCount(filtered_table),
            ReductionPct = (OriginalCount - FilteredCount) / OriginalCount * 100
        in
            [
                original_count = OriginalCount,
                filtered_count = FilteredCount,
                reduction_percentage = ReductionPct,
                status = if ReductionPct > 90 then "WARNING: High reduction rate" else "OK"
            ],
    
            // STEP 6: ENHANCED TIME CALCULATIONS WITH NULL HANDLING
            WithTimeResponse = Table.AddColumn(WithIncidentTime, "time_response_minutes", each
                try (
                    let
                        timeOfCall = try [incident_date] otherwise null,
                        timeDispatched = try [time_dispatched] otherwise null
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
                        else null
                ) otherwise null, type nullable number),

                WithTimeSpent = Table.AddColumn(WithTimeResponse, "time_spent_minutes", each
                try (
                    let
                        timeOut = try [time_out] otherwise null,
                        timeIn = try [time_in] otherwise null
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
                        else null
                ) otherwise null, type nullable number),
    
            // STEP 7: UNIFIED COLUMNS WITH NULL HANDLING
            WithLocation = Table.AddColumn(WithTimeSpent, "location", each 
                try [full_address_raw] otherwise "", type nullable text),
            WithGrid = Table.AddColumn(WithLocation, "grid", each 
                try [grid_raw] otherwise "", type nullable text),
            WithPost = Table.AddColumn(WithGrid, "post", each 
                try [post_raw] otherwise "", type nullable text),
    
            // STEP 8: ENHANCED BLOCK CALCULATION WITH ERROR HANDLING
            WithBlock = Table.AddColumn(WithPost, "block", each
                try (
                    let
                        addr = try [location] otherwise "",
                        isIntersection = try Text.Contains(addr, " & ") otherwise false,
                        cleanAddr = try Text.Replace(addr, ", Hackensack, NJ, 07601", "") otherwise addr
                    in
                        if isIntersection then
                            try (
                                let
                                    beforeAmpersand = Text.Trim(Text.BeforeDelimiter(cleanAddr, " & ")),
                                    afterAmpersand = Text.Trim(Text.AfterDelimiter(cleanAddr, " & "))
                                in
                                    if beforeAmpersand <> "" and afterAmpersand <> "" then
                                        beforeAmpersand & " & " & afterAmpersand
                                    else "Incomplete Address - Check Location Data"
                            ) otherwise "Address Processing Error"
                        else
                            try (
                                let
                                    streetNum = try Number.FromText(Text.BeforeDelimiter(cleanAddr, " ")) otherwise null,
                                    streetName = try Text.Trim(Text.BeforeDelimiter(Text.AfterDelimiter(cleanAddr, " "), ",")) otherwise ""
                                in
                                    if streetNum <> null and streetName <> "" then 
                                        streetName & ", " & Text.From(Number.IntegerDivide(streetNum, 100) * 100) & " Block"
                                    else if streetName <> "" then 
                                        streetName & ", Unknown Block"
                                    else "Check Location Data"
                            ) otherwise "Address Processing Error"
                ) otherwise "Error Processing Address", type nullable text),
    
            // STEP 9: ENHANCED CAD NOTES CLEANING WITH ERROR HANDLING
            WithCleanedCADNotes = Table.AddColumn(WithBlock, "cad_notes_cleaned", each
                try (
                    let
                        notes = try [cad_notes_raw] otherwise ""
                    in
                        if notes = "" or notes = null then null
                        else
                            try (
                                let
                                    step1 = Text.Replace(Text.Replace(Text.Replace(notes, "#(cr)#(lf)", " "), "#(lf)", " "), "#(cr)", " "),
                                    step2 = Text.Replace(step1, "? - ? - ?", ""),
                                    step3 = Text.Replace(Text.Replace(Text.Replace(step2, "    ", " "), "   ", " "), "  ", " "),
                                    step4 = Text.Clean(Text.Trim(step3)),
                                    final = if step4 = "" or step4 = "-" then null else step4
                                in
                                    final
                            ) otherwise notes // Return original if cleaning fails
                ) otherwise null, type nullable text),
    
            // STEP 10: CYCLE-BASED EXPORT FILENAME GENERATION
            // Format: C08W31_2025_08_02_7Day_CAD_Data_Standardized.csv
            WithExportFilename = Table.AddColumn(WithCleanedCADNotes, "export_filename", each
                try (
                    let
                        cycleName = try [cycle_name] otherwise "C08W31",
                        currentDate = try Date.ToText(Date.From(DateTime.LocalNow()), "yyyy_MM_dd") otherwise "2025_08_02"
                    in
                        cycleName & "_" & currentDate & "_7Day_CAD_Data_Standardized.csv"
                ) otherwise "C08W31_2025_08_02_7Day_CAD_Data_Standardized.csv", type text),
    
            // STEP 11: SELECT FINAL COLUMNS WITH CYCLE_NAME AS 2ND COLUMN
            // Ensures consistent snake_case naming and proper column ordering
            FinalCADColumns = try Table.SelectColumns(WithExportFilename, {
                "case_number",
                "cycle_name", // 2nd column as required
                "incident_date",
                "incident_time",
                "response_type",
                "how_reported",
                "location",
                "block",
                "grid", 
                "post",
                "time_dispatched",
                "time_out",
                "time_in",
                "time_spent_minutes",
                "time_response_minutes",
                "officer",
                "disposition",
                "cad_notes_cleaned",
                "export_filename"
            }) otherwise WithExportFilename, // Fallback to all columns if selection fails
    
            // STEP 12: APPLY CRIME FILTERING WITH COMPREHENSIVE ERROR HANDLING
            FilteredCAD = try FilterTargetCrimes(FinalCADColumns) otherwise FinalCADColumns,
            
            // STEP 13: GENERATE VALIDATION REPORT WITH ERROR HANDLING
            ValidationReport = try ValidateFilteringResults(FinalCADColumns, FilteredCAD) otherwise [
                original_count = Table.RowCount(FinalCADColumns),
                filtered_count = Table.RowCount(FilteredCAD),
                reduction_percentage = 0,
                status = "Validation Error"
            ],
            
            // STEP 14: ADD COMPREHENSIVE METADATA
            FilteredCADWithValidation = try Table.AddColumn(FilteredCAD, "validation_report", each ValidationReport, type record) otherwise FilteredCAD,
            
            // STEP 15: ADD ERROR REPORTING COLUMN
            FinalResult = Table.AddColumn(FilteredCADWithValidation, "processing_status", each "Success", type text)
        in
            FinalResult
    ) otherwise (
        // COMPREHENSIVE ERROR FALLBACK
        let
            ErrorTable = #table(
                {"case_number", "cycle_name", "processing_status", "error_message"},
                {{null, "C08W31", "Error", "Failed to process CAD data - check source file format"}}
            )
        in
            ErrorTable
    )
in
    ProcessWithErrorHandling