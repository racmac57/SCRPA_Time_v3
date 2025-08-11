// 🕒 2025-07-22-13-45-00
// Project: SCRPA_Analysis/RMS_Data
// Author: R. A. Carucci
// Purpose: Complete RMS_Data M-Code with fixed null handling and data type conversions

let
    // RMS Data Source
    Source = Folder.Files("C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA"),
    FilteredFiles = Table.SelectRows(Source, each [Extension] = ".xlsx" and Record.FieldOrDefault([Attributes],"Hidden",false) <> true),
    SortedFiles = Table.Sort(FilteredFiles, {{"Date modified", Order.Descending}}),
    LatestFile = Table.FirstN(SortedFiles, 1),
    
    TransformRMS = (FileBinary as binary) =>
        let
            Workbook = Excel.Workbook(FileBinary, null, true),
            FirstSheet = try Workbook{[Item="Sheet1",Kind="Sheet"]}[Data]
                        otherwise try Workbook{0}[Data]  
                        otherwise Workbook{[Kind="Sheet"]}[Data],
            Headers = Table.PromoteHeaders(FirstSheet, [PromoteAllScalars=true]),
            
            // Get available columns to avoid errors
            AvailableColumns = Table.ColumnNames(Headers),
            
            // Safe data type conversion with null handling - only for columns that exist
            SafeTyped = Table.TransformColumnTypes(Headers, 
                List.Select({
                    {"Case Number", type text},
                    {"CaseNumber", type text},
                    {"IncidentType1", type text},
                    {"IncidentType2", type text}, 
                    {"IncidentType3", type text},
                    {"IncidentType", type text},
                    {"FullAddress", type text},
                    {"Zone", Int64.Type},
                    {"Officer", type text},
                    {"OfficerOfRecord", type text},
                    {"Disposition", type text}
                }, each List.Contains(AvailableColumns, _{0}))),
            
            // Crime category logic with safe text handling
            WithCrimeCategory = Table.AddColumn(SafeTyped, "Crime_Category", each 
                let 
                    incidentText = try 
                        if List.Contains(AvailableColumns, "IncidentType1") and [IncidentType1] <> null then Text.Upper([IncidentType1])
                        else if List.Contains(AvailableColumns, "IncidentType") and [IncidentType] <> null then Text.Upper([IncidentType])
                        else ""
                    otherwise ""
                in
                    if Text.Contains(incidentText,"MOTOR VEHICLE THEFT") then "Motor Vehicle Theft"
                    else if List.AnyTrue({
                        Text.Contains(incidentText,"BURGLARY - AUTO"),
                        Text.Contains(incidentText,"THEFT FROM MOTOR VEHICLE")
                    }) then "Burglary Auto"
                    else if List.AnyTrue({
                        Text.Contains(incidentText,"BURGLARY - COMMERCIAL"),
                        Text.Contains(incidentText,"BURGLARY - RESIDENCE")
                    }) then "Burglary - Comm & Res"
                    else if Text.Contains(incidentText,"ROBBERY") then "Robbery"
                    else if List.AnyTrue({
                        Text.Contains(incidentText,"SEXUAL"),
                        Text.Contains(incidentText,"RAPE")
                    }) then "Sexual Offenses"
                    else "Other", type text),
            
            // Safe incident date conversion - check multiple possible date columns
            WithIncidentDate = Table.AddColumn(WithCrimeCategory, "Incident_Date", each
                try 
                    if List.Contains(AvailableColumns, "IncidentDate") and [IncidentDate] <> null then 
                        Date.From([IncidentDate])
                    else if List.Contains(AvailableColumns, "IncidentDateBetween") and [IncidentDateBetween] <> null then 
                        Date.From([IncidentDateBetween])
                    else if List.Contains(AvailableColumns, "ReportDate") and [ReportDate] <> null then 
                        Date.From([ReportDate])
                    else if List.Contains(AvailableColumns, "Incident Date") and [Incident Date] <> null then
                        Date.From([Incident Date])
                    else null
                otherwise null, type date),
            
            // Safe period calculation
            WithPeriod = Table.AddColumn(WithIncidentDate, "Period", each 
                try
                    let 
                        incDate = [Incident_Date],
                        today = Date.From(DateTime.LocalNow()),
                        daysDiff = if incDate <> null then Duration.Days(today - incDate) else 999
                    in
                        if daysDiff <= 7 then "7-Day"
                        else if daysDiff <= 28 then "28-Day"
                        else if incDate <> null and Date.Year(incDate) = Date.Year(today) then "YTD"
                        else "Historical"
                otherwise "Historical", type text),
            
            // Add ALL_INCIDENTS field safely
            WithAllIncidents = Table.AddColumn(WithPeriod, "ALL_INCIDENTS", each
                try 
                    if List.Contains(AvailableColumns, "IncidentType1") and [IncidentType1] <> null then [IncidentType1]
                    else if List.Contains(AvailableColumns, "IncidentType") and [IncidentType] <> null then [IncidentType]
                    else "Unknown"
                otherwise "Unknown", type text),
            
            // Add Block calculation if address exists
            WithBlock = if List.Contains(AvailableColumns, "FullAddress") then
                Table.AddColumn(WithAllIncidents, "Block", each 
                    try
                        let
                            addr = if [FullAddress] <> null then [FullAddress] else "",
                            streetNum = try Number.FromText(Text.BeforeDelimiter(addr, " ")) otherwise null,
                            streetName = Text.Trim(Text.BeforeDelimiter(Text.AfterDelimiter(addr, " "), ","))
                        in
                            if streetNum <> null and streetName <> "" then 
                                streetName & ", " & Text.From(Number.IntegerDivide(streetNum, 100) * 100) & " Block"
                            else if streetName <> "" then 
                                streetName & ", Unknown Block"
                            else "Unknown Block"
                    otherwise "Unknown Block", type text)
            else
                Table.AddColumn(WithAllIncidents, "Block", each "Unknown Block", type text),
            
            // Standardize column names - handle both naming conventions
            StandardizedColumns = Table.RenameColumns(WithBlock, 
                List.Select({
                    {"CaseNumber", "Case Number"},
                    {"OfficerOfRecord", "Officer"},
                    {"Incident Date", "Incident_Date_Original"}
                }, each List.Contains(Table.ColumnNames(WithBlock), _{0})), MissingField.Ignore)
        in
            StandardizedColumns,
    
    InvokedRMS = Table.AddColumn(LatestFile, "RMS_Data", each TransformRMS([Content]), type table),
    ExpandedRMS = Table.ExpandTableColumn(InvokedRMS, "RMS_Data", 
        Table.ColumnNames(TransformRMS(LatestFile{0}[Content]))),
    FinalRMS = Table.SelectColumns(ExpandedRMS, 
        Table.ColumnNames(TransformRMS(LatestFile{0}[Content]))),
    #"Trimmed Text" = Table.TransformColumns(FinalRMS,{{"Narrative", Text.Trim, type text}}),
    #"Cleaned Text" = Table.TransformColumns(#"Trimmed Text",{{"Narrative", Text.Clean, type text}})
in
    #"Cleaned Text"