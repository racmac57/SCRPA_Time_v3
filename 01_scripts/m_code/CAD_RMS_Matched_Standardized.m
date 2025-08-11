// 🕒 2025-08-05-Updated
// SCRPA_Time_v2/CAD_RMS_Matched_Standardized_Complete_Tag_Extractor
// Author: R. A. Carucci
// Purpose: Complete CAD_RMS_Matched_Standardized query with incident_type tag extraction and narrative fixes
// Updated to use 7-Day filtered version from final script output

let
    // === CONFIGURATION ===
    DataPath = "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\",
    
    // === DYNAMIC FILE DETECTION - Use 7-Day filtered version ===
    Source = Folder.Files(DataPath),
    
    // First try to find files with "7Day" and "cad_rms_matched_standardized" in the name
    FilteredFiles = Table.SelectRows(Source, each 
        Text.Contains([Name], "7Day") and Text.Contains([Name], "cad_rms_matched_standardized")
    ),
    SortedFiles = Table.Sort(FilteredFiles, {{"Date modified", Order.Descending}}),
    LatestFile = if Table.RowCount(SortedFiles) > 0 then SortedFiles{0}[Content] else null,
    
    // === FALLBACK: If 7-Day file not found, use any cad_rms_matched_standardized ===
    FallbackFiles = if LatestFile = null then 
        let
            CadRmsFiles = Table.SelectRows(Source, each Text.Contains([Name], "cad_rms_matched_standardized")),
            SortedCadRms = Table.Sort(CadRmsFiles, {{"Date modified", Order.Descending}})
        in
            if Table.RowCount(SortedCadRms) > 0 then SortedCadRms{0}[Content] else null
    else LatestFile,
    
    // === DATA LOADING ===
    Headers = Table.PromoteHeaders(Csv.Document(FallbackFiles, [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]), [PromoteAllScalars=true]),
    
    // === SAFE DATA TYPE CONVERSIONS ===
    ColumnNames = Table.ColumnNames(Headers),
    
    // Build type conversion list only for existing columns - UPDATED TO MATCH ACTUAL CSV STRUCTURE
    TypeConversions = List.Accumulate(
        {
            // Core RMS columns (always present)
            {"case_number", type text},
            {"incident_date", type text},  // Keep as text since it's mm/dd/yy format
            {"incident_time", type text},  // Keep as text since it's HH:MM:SS format
            {"time_of_day", type text},
            {"time_of_day_sort_order", type number},
            {"period", type text},
            {"season", type text},
            {"day_of_week", type text},
            {"day_type", type text},
            {"location", type text},
            {"block", type text},
            {"grid", type text},
            {"post", type number},
            {"incident_type", type text},
            {"all_incidents", type text},
            {"vehicle_1", type text},
            {"vehicle_2", type text},
            {"vehicle_1_and_vehicle_2", type text},
            {"narrative", type text},
            {"total_value_stolen", type number},
            {"squad", type text},
            {"officer_of_record", type text},
            {"nibrs_classification", type text},
            {"cycle_name", type text},
            {"case_status", type text},
            
            // CAD columns (may be present with _cad suffix)
            {"case_number_cad", type text},
            {"response_type_cad", type text},
            {"category_type_cad", type text},
            {"grid_cad", type text},
            {"post_cad", type number},
            {"response_type", type text},
            {"category_type", type text}
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
    
    // === ENHANCED INCIDENT_TYPE TAG EXTRACTION (if incident_type is null) ===
    AddIncidentTypeTags = Table.AddColumn(ForceFullNarrative, "incident_type_tags", each
        let 
            existingType = [incident_type],
            // Check if all_incidents column exists and get its value safely
            allIncidents = if Table.HasColumns(ForceFullNarrative, {"all_incidents"}) 
                          then try Text.Upper([all_incidents]) otherwise ""
                          else ""
        in
        // Use existing incident_type if available, otherwise extract from all_incidents
        if existingType <> null and existingType <> "" then existingType
        else
            let
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
                              try 
                                  let
                                      dateStr = [incident_date],
                                      timeStr = [incident_time],
                                      
                                      // Debug: Create a simple datetime string first
                                      dateTimeStr = if dateStr <> null and dateStr <> "" and timeStr <> null and timeStr <> "" then
                                          dateStr & " " & timeStr
                                      else null,
                                      
                                      // Try to parse the combined string
                                      result = if dateTimeStr <> null then
                                          try DateTime.FromText(dateTimeStr) otherwise null
                                      else null
                                  in
                                      result
                              otherwise null, type datetime)
                          else WithCADIndicator,
    
    // Add time of day visual category
    AddTimeOfDayVisual = Table.AddColumn(WithIncidentDateTime, "time_of_day_visual", each 
        let 
            incidentTime = [incident_time],
            timeOfDay = [time_of_day]
        in
        if timeOfDay <> null and timeOfDay <> "" then timeOfDay
        else if incidentTime = null then "⏰ Unknown Time"
        else
            let 
                timeValue = try Time.FromText(Text.From(incidentTime)) otherwise null,
                hour = if timeValue <> null then Time.Hour(timeValue) else null
            in
            if hour = null then "⏰ Unknown Time"
            else if hour >= 6 and hour < 12 then "🌅 Morning (6am-12pm)"
            else if hour >= 12 and hour < 18 then "☀️ Afternoon (12pm-6pm)"  
            else if hour >= 18 and hour < 22 then "🌆 Evening (6pm-10pm)"
            else "🌙 Night (10pm-6am)", type text),
    
    // Add crime type visual (emoji-enhanced)
    AddCrimeTypeVisual = Table.AddColumn(AddTimeOfDayVisual, "crime_type_visual", each
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
    
    // Add vehicle information summary
    AddVehicleSummary = Table.AddColumn(AddCrimeTypeVisual, "vehicle_summary", each
        let 
            vehicle1 = [vehicle_1] ?? "",
            vehicle2 = [vehicle_2] ?? "",
            vehicleCombined = [vehicle_1_and_vehicle_2] ?? ""
        in
        if vehicleCombined <> "" then vehicleCombined
        else if vehicle1 <> "" and vehicle2 <> "" then vehicle1 & " | " & vehicle2
        else if vehicle1 <> "" then vehicle1
        else if vehicle2 <> "" then vehicle2
        else "No Vehicle Info", type text),
    
    // Add NIBRS code extraction
    AddNIBRSCode = Table.AddColumn(AddVehicleSummary, "nibrs_code", each
        let 
            nibrsClass = [nibrs_classification] ?? ""
        in
        if Text.Contains(nibrsClass, "=") then 
            let parts = Text.Split(nibrsClass, "=")
            in if List.Count(parts) >= 2 then Text.Trim(parts{0}) else nibrsClass
        else nibrsClass, type text),
    
    // Add season emoji
    AddSeasonEmoji = Table.AddColumn(AddNIBRSCode, "season_visual", each
        let 
            season = [season] ?? ""
        in
        if Text.Contains(season, "Winter") then "❄️ Winter"
        else if Text.Contains(season, "Spring") then "🌸 Spring"
        else if Text.Contains(season, "Summer") then "☀️ Summer"
        else if Text.Contains(season, "Fall") or Text.Contains(season, "Autumn") then "🍂 Fall"
        else "📅 " & season, type text),
    
    // Add day type visual
    AddDayTypeVisual = Table.AddColumn(AddSeasonEmoji, "day_type_visual", each
        let 
            dayType = [day_type] ?? ""
        in
        if Text.Contains(dayType, "Weekend") then "🎉 Weekend"
        else if Text.Contains(dayType, "Weekday") then "💼 Weekday"
        else "📅 " & dayType, type text),
    
    // === FINAL COLUMN ORDERING ===
    FinalColumnOrder = Table.ReorderColumns(AddDayTypeVisual, {
        "case_number", "incident_type", "crime_type_visual", "all_incidents", 
        "incident_date", "incident_time", "incident_datetime", "time_of_day_visual",
        "location", "block", "grid", "post", "period", "season_visual", "day_of_week", "day_type_visual",
        "narrative", "officer_of_record", "squad", "total_value_stolen", "nibrs_classification", "nibrs_code",
        "vehicle_summary", "has_cad_data", "cycle_name", "case_status"
    } & List.Difference(Table.ColumnNames(AddDayTypeVisual), {
        "case_number", "incident_type", "crime_type_visual", "all_incidents", 
        "incident_date", "incident_time", "incident_datetime", "time_of_day_visual",
        "location", "block", "grid", "post", "period", "season_visual", "day_of_week", "day_type_visual",
        "narrative", "officer_of_record", "squad", "total_value_stolen", "nibrs_classification", "nibrs_code",
        "vehicle_summary", "has_cad_data", "cycle_name", "case_status"
    }))

in
    FinalColumnOrder