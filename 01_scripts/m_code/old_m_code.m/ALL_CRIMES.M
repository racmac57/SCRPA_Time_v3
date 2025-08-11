// 🕒 2025-07-23-16-00-00
// Project: SCRPA_Time_v2/Final_Working_PowerBI_Solution
// Author: R. A. Carucci
// Purpose: Complete working M Code based on actual data structure analysis

// =============================================================================
// ALL_CRIMES Query - Final Working Version
// =============================================================================

let
    Source = Folder.Files("C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA"),
    FilteredExcel = Table.SelectRows(Source, each [Extension] = ".xlsx" and Record.FieldOrDefault([Attributes], "Hidden", false) <> true),
    Sorted = Table.Sort(FilteredExcel,{{"Date modified", Order.Descending}}),
    LatestFile = Table.FirstN(Sorted, 1),
    
    Transform_File = (Parameter2 as binary) =>
        let
            // ✅ Handle multiple sheets safely
            Source = Excel.Workbook(Parameter2, null, true),
            FilteredSheets = Table.SelectRows(Source, each [Kind] = "Sheet"),
            Sheet1_Sheet = if Table.RowCount(FilteredSheets) > 0 then FilteredSheets{0}[Data] else error "No valid sheets found",
            
            #"Promoted Headers" = Table.PromoteHeaders(Sheet1_Sheet, [PromoteAllScalars=true]),
            
            // ✅ Type conversions with error handling for actual column structure
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
            
            // ✅ Add calculated date/time columns with cascading logic
            WithIncidentDate = Table.AddColumn(#"Changed Type", "Incident_Date", each
                if [Incident Date] <> null then [Incident Date]
                else if [Incident Date_Between] <> null then [Incident Date_Between]
                else if [Report Date] <> null then [Report Date]
                else null, type date),
            
            WithIncidentTime = Table.AddColumn(WithIncidentDate, "Incident_Time", each
                if [Incident Time] <> null then [Incident Time]
                else if [Incident Time_Between] <> null then [Incident Time_Between]
                else if [Report Time] <> null then Time.From([Report Time])
                else null, type time),
            
            // ✅ Add StartOfHour calculation
            WithStartOfHour = Table.AddColumn(WithIncidentTime, "StartOfHour", each 
                if [Incident_Time] <> null then Time.StartOfHour([Incident_Time]) else null, type time),
            
            // ✅ CORRECTED TimeOfDay buckets - exact project specifications
            WithTimeOfDay = Table.AddColumn(WithStartOfHour, "TimeOfDay", each
                let t = [Incident_Time] in
                if t = null then "Unknown"
                else if t >= #time(0,0,0) and t < #time(4,0,0) then "00:00–03:59 Early Morning"
                else if t >= #time(4,0,0) and t < #time(8,0,0) then "04:00–07:59 Morning"
                else if t >= #time(8,0,0) and t < #time(12,0,0) then "08:00–11:59 Morning Peak"
                else if t >= #time(12,0,0) and t < #time(16,0,0) then "12:00–15:59 Afternoon"
                else if t >= #time(16,0,0) and t < #time(20,0,0) then "16:00–19:59 Evening Peak"
                else "20:00–23:59 Night", type text),
            
            // ✅ Add Block calculation using FullAddress (not FullAddress2)
            WithBlock = Table.AddColumn(WithTimeOfDay, "Block", each
                let
                    addr = [FullAddress] ?? "",
                    streetNum = try Number.FromText(Text.BeforeDelimiter(addr, " ")) otherwise null,
                    streetName = Text.Trim(Text.BeforeDelimiter(Text.AfterDelimiter(addr, " "), ","))
                in
                    if streetNum <> null and streetName <> "" then 
                        streetName & ", " & Text.From(Number.IntegerDivide(streetNum, 100) * 100) & " Block"
                    else if streetName <> "" then 
                        streetName & ", Unknown Block"
                    else "Unknown Block", type text),
            
            // ✅ Create ALL_INCIDENTS before unpivoting (for filtering logic)
            WithAllIncidents = Table.AddColumn(WithBlock, "ALL_INCIDENTS", each
                Text.Combine(
                    List.RemoveNulls({
                        [Incident Type_1],
                        [Incident Type_2],
                        [Incident Type_3]
                    }), " - "
                ), type text),
            
            // ✅ Add Period calculation
            WithPeriod = Table.AddColumn(WithAllIncidents, "Period", each
                let
                    incidentDate = [Incident_Date],
                    today = Date.From(DateTime.LocalNow()),
                    daysDiff = if incidentDate <> null then Duration.Days(today - incidentDate) else 999
                in
                    if daysDiff <= 7 then "7-Day"
                    else if daysDiff <= 28 then "28-Day"
                    else if incidentDate <> null and Date.Year(incidentDate) = Date.Year(today) then "YTD"
                    else "Historical", type text),
            
            // ✅ Filter out excluded case and Historical records BEFORE unpivoting
            FilteredRows = Table.SelectRows(WithPeriod, each 
                [Case Number] <> "25-057654" and [Period] <> "Historical"
            ),
            
            // ✅ UNPIVOT the incident type columns
            IncidentColumns = {"Incident Type_1", "Incident Type_2", "Incident Type_3"},
            KeepColumns = Table.ColumnNames(FilteredRows),
            IdColumns = List.Difference(KeepColumns, IncidentColumns),
            
            Unpivoted = Table.UnpivotOtherColumns(FilteredRows, IdColumns, "IncidentColumn", "IncidentType"),
            
            // ✅ Remove null/empty incident types (handles 56% missing Type_2, 80% missing Type_3)
            CleanedIncidents = Table.SelectRows(Unpivoted, each 
                [IncidentType] <> null and [IncidentType] <> ""
            ),
            
            // ✅ Crime categorization using both individual and combined incident types
            WithCrimeCategory = Table.AddColumn(CleanedIncidents, "Crime_Category", each
                let
                    incident = Text.Upper([IncidentType] ?? ""),
                    allIncidents = Text.Upper([ALL_INCIDENTS] ?? "")
                in
                    if Text.Contains(incident, "MOTOR VEHICLE THEFT") or Text.Contains(allIncidents, "MOTOR VEHICLE THEFT") then "Motor Vehicle Theft"
                    else if Text.Contains(incident, "ROBBERY") or Text.Contains(allIncidents, "ROBBERY") then "Robbery"
                    else if (Text.Contains(incident, "BURGLARY") and Text.Contains(incident, "AUTO")) or (Text.Contains(allIncidents, "BURGLARY") and Text.Contains(allIncidents, "AUTO")) then "Burglary – Auto"
                    else if Text.Contains(incident, "SEXUAL") or Text.Contains(allIncidents, "SEXUAL") then "Sexual Offenses"
                    else if (Text.Contains(incident, "BURGLARY") and Text.Contains(incident, "COMMERCIAL")) or (Text.Contains(allIncidents, "BURGLARY") and Text.Contains(allIncidents, "COMMERCIAL")) then "Burglary – Commercial"
                    else if (Text.Contains(incident, "BURGLARY") and Text.Contains(incident, "RESIDENCE")) or (Text.Contains(allIncidents, "BURGLARY") and Text.Contains(allIncidents, "RESIDENCE")) then "Burglary – Residence"
                    else "Other", type text),
            
            // ✅ Remove duplicates by Case Number (keeps first occurrence after unpivot)
            DistinctCases = Table.Distinct(WithCrimeCategory, {"Case Number"}),
            
            // ✅ METHOD 3: Comprehensive Narrative Text Cleaning (Kitchen Sink)
            ComprehensiveCleanedNarrative = Table.TransformColumns(DistinctCases, {
                {"Narrative", each 
                    let
                        text = _ ?? "",
                        // Step 1: Replace line breaks with spaces
                        step1 = Text.Replace(Text.Replace(Text.Replace(text, "#(cr)#(lf)", " "), "#(lf)", " "), "#(cr)", " "),
                        // Step 2: Replace multiple spaces with single space
                        step2 = Text.Replace(Text.Replace(Text.Replace(step1, "    ", " "), "   ", " "), "  ", " "),
                        // Step 3: Clean control characters
                        step3 = Text.Clean(step2),
                        // Step 4: Trim whitespace
                        step4 = Text.Trim(step3),
                        // Step 5: Replace common problematic characters
                        step5 = Text.Replace(Text.Replace(step4, "â", "'"), "â", ""),
                        // Step 6: Handle empty results
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
