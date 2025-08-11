// 🕒 2025-08-02-15-45-00
// SCRPA_Time_v2/CAD_RMS_Matched_Standardized_Complete_Tag_Extractor
// Author: R. A. Carucci
// Purpose: Complete CAD_RMS_Matched_Standardized query with incident_type tag extraction and narrative fixes

let
    // === CONFIGURATION ===
    DataPath = "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\",
    
    // === DYNAMIC FILE DETECTION ===
    Source = Folder.Files(DataPath),
    FilteredFiles = Table.SelectRows(Source, each Text.Contains([Name], "cad_rms_matched_standardized")),
    SortedFiles = Table.Sort(FilteredFiles, {{"Date modified", Order.Descending}}),
    LatestFile = if Table.RowCount(SortedFiles) > 0 then SortedFiles{0}[Content] else null,
    
    // === DATA LOADING ===
    Headers = Table.PromoteHeaders(Csv.Document(LatestFile, [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]), [PromoteAllScalars=true]),
    
    // === SAFE DATA TYPE CONVERSIONS ===
    ColumnNames = Table.ColumnNames(Headers),
    
    // Build type conversion list only for existing columns
    TypeConversions = List.Accumulate(
        {
            // Core RMS columns (always present)
            {"case_number", type text},
            {"incident_date", type date},
            {"incident_time", type time},
            {"location", type text},
            {"period", type text},
            {"post", type number},
            {"grid", type text},
            {"block", type text},
            {"narrative", type text},
            {"officer_of_record", type text},
            {"all_incidents", type text},
            {"total_value_stolen", type number},
            
            // CAD columns (may be present with _cad suffix)
            {"case_number_cad", type text},
            {"response_type_cad", type text},
            {"time_response_minutes_cad", type number},
            {"time_spent_minutes_cad", type number},
            {"time_response_formatted_cad", type text},
            {"time_spent_formatted_cad", type text},
            {"officer_cad", type text},
            {"time_of_call_cad", type datetime}
        },
        {},
        (state, current) => 
            if List.Contains(ColumnNames, current{0}) 
            then state & {current} 
            else state
    ),
    
    // Apply only the conversions for columns that exist
    TypedData = if List.Count(TypeConversions) > 0 
                then Table.TransformColumnTypes(Headers, TypeConversions)
                else Headers,
    
    // === FIX NARRATIVE TRUNCATION ===
    FixNarrativeColumn = Table.TransformColumns(
        TypedData, 
        {{"narrative", each if _ <> null then Text.Replace(_, "...", "") else _, type text}}
    ),
    
    // Force full narrative text loading
    ForceFullNarrative = Table.TransformColumnTypes(
        FixNarrativeColumn,
        {{"narrative", type text}}
    ),
    
    // === ENHANCED INCIDENT_TYPE TAG EXTRACTION ===
    AddIncidentTypeTags = Table.AddColumn(ForceFullNarrative, "incident_type_tags", each
        let 
            allIncidents = Text.Upper([all_incidents] ?? ""),
            
            // === CHECK FOR EACH TRACKED INCIDENT TYPE ===
            
            // Burglary - Auto (check for both BURGLARY and AUTO/VEHICLE)
            burglaryAuto = if (Text.Contains(allIncidents, "BURGLARY") and 
                              (Text.Contains(allIncidents, "AUTO") or Text.Contains(allIncidents, "VEHICLE"))) 
                           then {"Burglary - Auto"} else {},
            
            // Burglary - Residence 
            burglaryRes = if (Text.Contains(allIncidents, "BURGLARY") and 
                             (Text.Contains(allIncidents, "RESIDENCE") or Text.Contains(allIncidents, "RESIDENTIAL"))) 
                          then {"Burglary - Residence"} else {},
            
            // Burglary - Commercial
            burglaryComm = if (Text.Contains(allIncidents, "BURGLARY") and Text.Contains(allIncidents, "COMMERCIAL")) 
                           then {"Burglary - Commercial"} else {},
            
            // Motor Vehicle Theft (multiple variations)
            mvTheft = if (Text.Contains(allIncidents, "MOTOR VEHICLE THEFT") or 
                         Text.Contains(allIncidents, "AUTO THEFT") or 
                         Text.Contains(allIncidents, "VEHICLE THEFT") or
                         Text.Contains(allIncidents, "MV THEFT") or
                         (Text.Contains(allIncidents, "THEFT") and Text.Contains(allIncidents, "VEHICLE")))
                      then {"Motor Vehicle Theft"} else {},
            
            // Robbery
            robbery = if Text.Contains(allIncidents, "ROBBERY") 
                      then {"Robbery"} else {},
            
            // Sexual Offenses (any with "SEXUAL")
            sexual = if Text.Contains(allIncidents, "SEXUAL") 
                     then {"Sexual Offense"} else {},
            
            // === COMBINE ALL FOUND INCIDENT TYPES ===
            allFound = burglaryAuto & burglaryRes & burglaryComm & mvTheft & robbery & sexual,
            
            // === CREATE COMMA-SEPARATED RESULT ===
            result = if List.Count(allFound) > 0 
                     then Text.Combine(allFound, ", ") 
                     else null
        in
            result, type text),
    
    // === OPTIONAL: REPLACE EXISTING INCIDENT_TYPE COLUMN ===
    // Remove the old incident_type column if it exists
    RemoveOldIncidentType = if List.Contains(Table.ColumnNames(AddIncidentTypeTags), "incident_type")
                           then Table.RemoveColumns(AddIncidentTypeTags, {"incident_type"})
                           else AddIncidentTypeTags,
    
    // Rename the new tags column to incident_type
    RenameIncidentTypeTags = Table.RenameColumns(RemoveOldIncidentType, {{"incident_type_tags", "incident_type"}}),
    
    // === ADD CALCULATED COLUMNS ===
    // Add CAD match indicator
    WithCADIndicator = Table.AddColumn(
        RenameIncidentTypeTags, 
        "has_cad_data", 
        each if Table.HasColumns(RenameIncidentTypeTags, {"case_number_cad"}) 
             then (if [case_number_cad] <> null and [case_number_cad] <> "" then "Yes" else "No")
             else "No", 
        type text
    ),
    
    // Add incident datetime if both date and time exist
    WithIncidentDateTime = if Table.HasColumns(WithCADIndicator, {"incident_date", "incident_time"})
                          then Table.AddColumn(WithCADIndicator, "incident_datetime", each 
                              try [incident_date] & [incident_time] otherwise null, type datetime)
                          else WithCADIndicator,
    
    // Add time of day visual category
    AddTimeOfDayVisual = Table.AddColumn(WithIncidentDateTime, "time_of_day_visual", each 
        let 
            incidentTime = [incident_time]
        in
        if incidentTime = null then "⏰ Unknown Time"
        else
            let 
                timeValue = if Value.Type(incidentTime) = type time then incidentTime
                           else if Value.Type(incidentTime) = type datetime then Time.From(incidentTime)
                           else try Time.FromText(Text.From(incidentTime)) otherwise null,
                hour = if timeValue <> null then Time.Hour(timeValue) else null
            in
            if hour = null then "⏰ Unknown Time"
            else if hour >= 6 and hour < 12 then "🌅 Morning (6am-12pm)"
            else if hour >= 12 and hour < 18 then "☀️ Afternoon (12pm-6pm)"  
            else if hour >= 18 and hour < 22 then "🌆 Evening (6pm-10pm)"
            else "🌙 Night (10pm-6am)", type text),
    
    // Add response time category (if CAD data available)
    AddResponseCategory = if Table.HasColumns(AddTimeOfDayVisual, {"time_response_minutes_cad"})
                         then Table.AddColumn(AddTimeOfDayVisual, "response_category", each
                             let responseMin = [time_response_minutes_cad] in
                             if responseMin = null then "No Data"
                             else if responseMin <= 3 then "🟢 Excellent"
                             else if responseMin <= 6 then "🟡 Good" 
                             else if responseMin <= 10 then "🟠 Average"
                             else "🔴 Slow", type text)
                         else AddTimeOfDayVisual,
    
    // Add crime type visual (emoji-enhanced)
    AddCrimeTypeVisual = Table.AddColumn(AddResponseCategory, "crime_type_visual", each
        let 
            incidentType = [incident_type] ?? ""
        in
        if Text.Contains(incidentType, "Burglary - Auto") then "🚗 Burglary-Auto"
        else if Text.Contains(incidentType, "Burglary - Residence") then "🏠 Burglary-Residence"
        else if Text.Contains(incidentType, "Burglary - Commercial") then "🏢 Burglary-Commercial"
        else if Text.Contains(incidentType, "Motor Vehicle Theft") then "🚗 Motor Vehicle Theft"
        else if Text.Contains(incidentType, "Robbery") then "💰 Robbery"
        else if Text.Contains(incidentType, "Sexual Offense") then "🚨 Sexual Offense"
        else if incidentType <> null and incidentType <> "" then "📋 " & incidentType
        else "❓ Other", type text),
    
    // === FINAL COLUMN ORDERING ===
    FinalColumnOrder = Table.ReorderColumns(AddCrimeTypeVisual, {
        "case_number", "incident_type", "crime_type_visual", "all_incidents", 
        "incident_date", "incident_time", "incident_datetime", "time_of_day_visual",
        "location", "block", "grid", "post", "period", "narrative", 
        "officer_of_record", "total_value_stolen", "has_cad_data"
    } & List.Difference(Table.ColumnNames(AddCrimeTypeVisual), {
        "case_number", "incident_type", "crime_type_visual", "all_incidents", 
        "incident_date", "incident_time", "incident_datetime", "time_of_day_visual",
        "location", "block", "grid", "post", "period", "narrative", 
        "officer_of_record", "total_value_stolen", "has_cad_data"
    }))

in
    FinalColumnOrder