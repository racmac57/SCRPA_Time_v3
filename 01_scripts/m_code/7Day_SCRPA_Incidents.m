// 🕒 2025-08-05-Updated
// SCRPA_Time_v2/7Day_SCRPA_Incidents
// Author: R. A. Carucci
// Purpose: Load 7-Day SCRPA Incidents data with all columns from CAD-RMS matched data
// Updated to work with final script output format

let
    // === CONFIGURATION ===
    DataPath = "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\",
    
    // === DYNAMIC FILE DETECTION ===
    Source = Folder.Files(DataPath),
    FilteredFiles = Table.SelectRows(Source, each Text.Contains([Name], "7Day_SCRPA_Incidents")),
    SortedFiles = Table.Sort(FilteredFiles, {{"Date modified", Order.Descending}}),
    LatestFile = if Table.RowCount(SortedFiles) > 0 then SortedFiles{0}[Content] else null,
    
    // === DATA LOADING ===
    LoadedData = if LatestFile <> null then 
        let
            CsvData = Csv.Document(LatestFile, [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
            Headers = Table.PromoteHeaders(CsvData, [PromoteAllScalars=true])
        in Headers
    else
        #table({"Message"}, {{"No 7-Day SCRPA file found"}}),
    
    // === DATA TYPE CONVERSIONS ===
    TypedData = if Table.HasColumns(LoadedData, {"case_number"}) then
        Table.TransformColumnTypes(LoadedData, {
            // Core RMS columns - UPDATED TO MATCH ACTUAL CSV STRUCTURE
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
        })
    else LoadedData,
    
    // === ADD CALCULATED COLUMNS ===
    // Add incident datetime if both date and time exist
    WithIncidentDateTime = if Table.HasColumns(TypedData, {"incident_date", "incident_time"})
                          then Table.AddColumn(TypedData, "incident_datetime", each 
                              try 
                                  let
                                      dateStr = [incident_date],
                                      timeStr = [incident_time],
                                      // Convert mm/dd/yy to yyyy-mm-dd format
                                      dateParts = Text.Split(dateStr, "/"),
                                      year = if List.Count(dateParts) >= 3 then 
                                                 if Number.From(dateParts{2}) < 50 then "20" & dateParts{2} else "19" & dateParts{2}
                                             else null,
                                      month = if List.Count(dateParts) >= 2 then dateParts{0} else null,
                                      day = if List.Count(dateParts) >= 2 then dateParts{1} else null,
                                      formattedDate = if year <> null and month <> null and day <> null 
                                                      then year & "-" & Text.PadStart(month, 2, "0") & "-" & Text.PadStart(day, 2, "0")
                                                      else null,
                                      // Combine date and time
                                      dateTimeStr = if formattedDate <> null and timeStr <> null 
                                                   then formattedDate & "T" & timeStr
                                                   else null
                                  in
                                      if dateTimeStr <> null then DateTime.FromText(dateTimeStr) else null
                              otherwise null, type datetime)
                          else TypedData,
    
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
    
    // Add CAD match indicator
    WithCADIndicator = Table.AddColumn(
        AddDayTypeVisual, 
        "has_cad_data", 
        each if Table.HasColumns(AddDayTypeVisual, {"case_number_cad"}) 
             then (if [case_number_cad] <> null and [case_number_cad] <> "" then "Yes" else "No")
             else "No", 
        type text
    )

in
    WithCADIndicator