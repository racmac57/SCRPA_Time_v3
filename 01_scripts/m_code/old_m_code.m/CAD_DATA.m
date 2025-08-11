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