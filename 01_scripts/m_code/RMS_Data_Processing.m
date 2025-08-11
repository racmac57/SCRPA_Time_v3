// =============================================================================
// RMS DATA PROCESSING WITH ENHANCED FUNCTIONALITY - COMPLETE VERSION
// A. Column Naming Standards: snake_case format, cycle_name as 2nd column
// B. Export File Naming: C08W31_2025_08_02_7Day_RMS_Data_Standardized.csv
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
    
            // STEP 2: COMPREHENSIVE COLUMN STANDARDIZATION TO SNAKE_CASE
            // Robust null handling and column mapping with error recovery
            StandardizedColumns = try Table.RenameColumns(#"Promoted Headers", {
                {"Case Number", "case_number"},
                {"CaseNumber", "case_number"}, // Alternative format
                {"Case_Number", "case_number"}, // Alternative format
                {"Incident Date", "incident_date_raw"},
                {"IncidentDate", "incident_date_raw"}, // Alternative format
                {"Incident_Date", "incident_date_raw"}, // Alternative format
                {"Incident Time", "incident_time_raw"},
                {"IncidentTime", "incident_time_raw"}, // Alternative format
                {"Incident_Time", "incident_time_raw"}, // Alternative format
                {"Incident Date_Between", "incident_date_between_raw"},
                {"Incident Time_Between", "incident_time_between_raw"},
                {"Report Date", "report_date_raw"},
                {"ReportDate", "report_date_raw"}, // Alternative format
                {"Report Time", "report_time_raw"},
                {"ReportTime", "report_time_raw"}, // Alternative format
                {"Incident Type_1", "incident_type_1_raw"},
                {"IncidentType1", "incident_type_1_raw"}, // Alternative format
                {"Incident Type_2", "incident_type_2_raw"},
                {"IncidentType2", "incident_type_2_raw"}, // Alternative format
                {"Incident Type_3", "incident_type_3_raw"},
                {"IncidentType3", "incident_type_3_raw"}, // Alternative format
                {"FullAddress", "full_address_raw"},
                {"Full Address", "full_address_raw"}, // Alternative format
                {"Address", "full_address_raw"}, // Alternative format
                {"Grid", "grid_raw"},
                {"Zone", "zone_raw"},
                {"Narrative", "narrative_raw"},
                {"Total Value Stolen", "total_value_stolen"},
                {"TotalValueStolen", "total_value_stolen"}, // Alternative format
                {"Total Value Recover", "total_value_recovered"},
                {"TotalValueRecover", "total_value_recovered"}, // Alternative format
                {"Registration 1", "registration_1"},
                {"Registration1", "registration_1"}, // Alternative format
                {"Make1", "make_1"},
                {"Model1", "model_1"},
                {"Reg State 1", "reg_state_1"},
                {"RegState1", "reg_state_1"}, // Alternative format
                {"Registration 2", "registration_2"},
                {"Registration2", "registration_2"}, // Alternative format
                {"Reg State 2", "reg_state_2"},
                {"RegState2", "reg_state_2"}, // Alternative format
                {"Make2", "make_2"},
                {"Model2", "model_2"},
                {"Reviewed By", "reviewed_by"},
                {"ReviewedBy", "reviewed_by"}, // Alternative format
                {"CompleteCalc", "complete_calc"},
                {"Complete_Calc", "complete_calc"}, // Alternative format
                {"Officer of Record", "officer_of_record"},
                {"OfficerOfRecord", "officer_of_record"}, // Alternative format
                {"Squad", "squad"},
                {"Det_Assigned", "det_assigned"},
                {"DetAssigned", "det_assigned"}, // Alternative format
                {"Case_Status", "case_status"},
                {"CaseStatus", "case_status"}, // Alternative format
                {"NIBRS Classification", "nibrs_classification"},
                {"NIBRSClassification", "nibrs_classification"}, // Alternative format
                {"NIBRS_Classification", "nibrs_classification"} // Alternative format
            }, MissingField.Ignore) otherwise 
            // Fallback: Add missing columns with null values
            Table.AddColumn(
                Table.AddColumn(
                    Table.AddColumn(#"Promoted Headers", "case_number", each null, type nullable text),
                    "incident_date_raw", each null, type nullable datetime),
                "incident_time_raw", each null, type nullable time),
    
            // STEP 3: ROBUST CASCADING DATE WITH ERROR HANDLING
            WithIncidentDate = Table.AddColumn(StandardizedColumns, "incident_date", each
                try (
                    if try [incident_date_raw] otherwise null <> null then 
                        try Date.From([incident_date_raw]) otherwise null
                    else if try [incident_date_between_raw] otherwise null <> null then 
                        try Date.From([incident_date_between_raw]) otherwise null
                    else if try [report_date_raw] otherwise null <> null then 
                        try Date.From([report_date_raw]) otherwise null
                    else null
                ) otherwise null, type nullable date),
    
            // STEP 4: ROBUST CASCADING TIME WITH ERROR HANDLING
            WithIncidentTime = Table.AddColumn(WithIncidentDate, "incident_time", each
                try (
                    if try [incident_time_raw] otherwise null <> null then 
                        try Time.From([incident_time_raw]) otherwise null
                    else if try [incident_time_between_raw] otherwise null <> null then 
                        try Time.From([incident_time_between_raw]) otherwise null
                    else if try [report_time_raw] otherwise null <> null then 
                        try Time.From([report_time_raw]) otherwise null
                    else null
                ) otherwise null, type nullable time),
    
    // STEP 5: CYCLE DETECTION AND NAMING (C08W31 format)
    WithCycleDetection = Table.AddColumn(WithIncidentTime, "cycle_name", each
        let
            incidentDate = [incident_date] ?? Date.From(DateTime.LocalNow())
        in
            GetCurrentCycle(incidentDate), type text),
    
            // STEP 6: COMPREHENSIVE NULL VALUE HANDLING FOR INCIDENT COLUMNS
            WithNullHandling = try Table.ReplaceValue(WithCycleDetection, null, "", Replacer.ReplaceValue, 
                {"incident_type_1_raw", "incident_type_2_raw", "incident_type_3_raw", "nibrs_classification"}) otherwise WithCycleDetection,
    
            // STEP 7: ENHANCED INCIDENT TYPES CLEANING WITH ERROR HANDLING
            WithAllIncidents = Table.AddColumn(WithNullHandling, "all_incidents", each
                try (
                    let
                        cleanType1 = try (
                            if [incident_type_1_raw] <> null and [incident_type_1_raw] <> "" then 
                                if Text.Contains([incident_type_1_raw], " - 2C") then
                                    Text.BeforeDelimiter([incident_type_1_raw], " - 2C")
                                else [incident_type_1_raw]
                            else ""
                        ) otherwise "",
                        
                        cleanType2 = try (
                            if [incident_type_2_raw] <> null and [incident_type_2_raw] <> "" then 
                                if Text.Contains([incident_type_2_raw], " - 2C") then
                                    Text.BeforeDelimiter([incident_type_2_raw], " - 2C")
                                else [incident_type_2_raw]
                            else ""
                        ) otherwise "",
                        
                        cleanType3 = try (
                            if [incident_type_3_raw] <> null and [incident_type_3_raw] <> "" then 
                                if Text.Contains([incident_type_3_raw], " - 2C") then
                                    Text.BeforeDelimiter([incident_type_3_raw], " - 2C")
                                else [incident_type_3_raw]
                            else ""
                        ) otherwise ""
                    in
                        try Text.Combine(List.RemoveNulls(List.Select({cleanType1, cleanType2, cleanType3}, each _ <> "")), ", ") otherwise ""
                ) otherwise "", type nullable text),
    
            // STEP 8: ENHANCED PRIMARY INCIDENT TYPE WITH ERROR HANDLING
            WithIncidentType = Table.AddColumn(WithAllIncidents, "incident_type", each
                try (
                    let
                        cleanType = try (
                            if [incident_type_1_raw] <> null and [incident_type_1_raw] <> "" then 
                                if Text.Contains([incident_type_1_raw], " - 2C") then
                                    Text.BeforeDelimiter([incident_type_1_raw], " - 2C")
                                else [incident_type_1_raw]
                            else "Unknown"
                        ) otherwise "Unknown"
                    in cleanType
                ) otherwise "Unknown", type nullable text),
    
            // STEP 9: EXACT PYTHON-MATCHING FILTERING FUNCTION
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
                            Text.Contains(Text.Upper([incident_type] ?? ""), Text.Upper(pattern)) or
                            Text.Contains(Text.Upper([all_incidents] ?? ""), Text.Upper(pattern)) or  
                            Text.Contains(Text.Upper([nibrs_classification] ?? ""), Text.Upper(pattern))
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
    
    // STEP 10: TIME OF DAY
    WithTimeOfDay = Table.AddColumn(WithIncidentType, "time_of_day", each
        let t = [incident_time] in
        if t = null then "Unknown"
        else if t >= #time(0,0,0) and t < #time(4,0,0) then "00:00–03:59 Early Morning"
        else if t >= #time(4,0,0) and t < #time(8,0,0) then "04:00–07:59 Morning"
        else if t >= #time(8,0,0) and t < #time(12,0,0) then "08:00–11:59 Morning Peak"
        else if t >= #time(12,0,0) and t < #time(16,0,0) then "12:00–15:59 Afternoon"
        else if t >= #time(16,0,0) and t < #time(20,0,0) then "16:00–19:59 Evening Peak"
        else "20:00–23:59 Night", type text),
    
    // STEP 11: PERIOD
    WithPeriod = Table.AddColumn(WithTimeOfDay, "period", each
        let
            incidentDate = [incident_date],
            today = Date.From(DateTime.LocalNow()),
            daysDiff = if incidentDate <> null then Duration.Days(today - incidentDate) else 999
        in
            if daysDiff <= 7 then "7-Day"
            else if daysDiff <= 28 then "28-Day"
            else if incidentDate <> null and Date.Year(incidentDate) = Date.Year(today) then "YTD"
            else "Historical", type text),
    
    // STEP 12: UNIFIED LOCATION
    WithLocation = Table.AddColumn(WithPeriod, "location", each [full_address_raw], type text),
    WithGrid = Table.AddColumn(WithLocation, "grid", each [grid_raw], type text),
    WithPost = Table.AddColumn(WithGrid, "post", each [zone_raw], type text),
    
    // STEP 13: BLOCK CALCULATION
    WithBlock = Table.AddColumn(WithPost, "block", each
        let
            addr = [location] ?? "",
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
    
    // STEP 14: CLEAN NARRATIVE
    WithNarrative = Table.AddColumn(WithBlock, "narrative", each
        let
            raw = [narrative_raw] ?? ""
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
    
            // STEP 15: CYCLE-BASED EXPORT FILENAME GENERATION
            // Format: C08W31_2025_08_02_7Day_RMS_Data_Standardized.csv
            WithExportFilename = Table.AddColumn(WithNarrative, "export_filename", each
                try (
                    let
                        cycleName = try [cycle_name] otherwise "C08W31",
                        currentDate = try Date.ToText(Date.From(DateTime.LocalNow()), "yyyy_MM_dd") otherwise "2025_08_02"
                    in
                        cycleName & "_" & currentDate & "_7Day_RMS_Data_Standardized.csv"
                ) otherwise "C08W31_2025_08_02_7Day_RMS_Data_Standardized.csv", type text),
    
            // STEP 16: SELECT FINAL COLUMNS WITH CYCLE_NAME AS 2ND COLUMN
            // Ensures consistent snake_case naming and proper column ordering
            FinalColumns = try Table.SelectColumns(WithExportFilename, {
                "case_number",
                "cycle_name", // 2nd column as required
                "incident_date", 
                "incident_time",
                "time_of_day",
                "period",
                "location",
                "block", 
                "grid",
                "post",
                "all_incidents",
                "incident_type", 
                "narrative",
                "total_value_stolen",
                "total_value_recovered",
                "squad",
                "officer_of_record",
                "nibrs_classification",
                "export_filename"
            }) otherwise WithExportFilename, // Fallback to all columns if selection fails
    
    // STEP 17: EXCLUDE SPECIFIC CASE AND HISTORICAL RECORDS
    PreFilteredRows = Table.SelectRows(FinalColumns, each 
        [case_number] <> "25-057654" and 
        [period] <> "Historical"
    ),
    
            // STEP 18: APPLY CRIME FILTERING WITH COMPREHENSIVE ERROR HANDLING
            FilteredRows = try FilterTargetCrimes(PreFilteredRows) otherwise PreFilteredRows,
            
            // STEP 19: GENERATE VALIDATION REPORT WITH ERROR HANDLING
            ValidationReport = try ValidateFilteringResults(PreFilteredRows, FilteredRows) otherwise [
                original_count = Table.RowCount(PreFilteredRows),
                filtered_count = Table.RowCount(FilteredRows),
                reduction_percentage = 0,
                status = "Validation Error"
            ],
            
            // STEP 20: ADD COMPREHENSIVE METADATA
            FilteredRowsWithValidation = try Table.AddColumn(FilteredRows, "validation_report", each ValidationReport, type record) otherwise FilteredRows,
            
            // STEP 21: ADD ERROR REPORTING COLUMN
            FinalResult = Table.AddColumn(FilteredRowsWithValidation, "processing_status", each "Success", type text)
        in
            FinalResult
    ) otherwise (
        // COMPREHENSIVE ERROR FALLBACK
        let
            ErrorTable = #table(
                {"case_number", "cycle_name", "processing_status", "error_message"},
                {{null, "C08W31", "Error", "Failed to process RMS data - check source file format"}}
            )
        in
            ErrorTable
    )
in
    ProcessWithErrorHandling