// 🕒 2025-08-06-10-15-00
// SCRPA_Time_v2/[CRIME_TYPE]_7Day_Production_Template
// Author: R. A. Carucci
// Purpose: Template M Code for [CRIME_TYPE] filtering with proper period calculation
// 
// INSTRUCTIONS FOR USE:
// 1. Replace [CRIME_TYPE] in header and file path
// 2. Update CrimeTypePatterns with relevant patterns
// 3. Update StatuteReferences with relevant NJ statutes
// 4. Update CrimeCategoryName with proper category name
// 5. Update GeoJSON file path to match crime type
// 6. Update validation message with crime type name

let
    // ─── CRIME TYPE CONFIGURATION ─────────────────────────────────────────────────────────
    // CHANGE THESE SETTINGS FOR EACH CRIME TYPE:
    CrimeTypePatterns = {
        "PATTERN1", "PATTERN2", "PATTERN3"  // Replace with crime-specific patterns
    },
    StatuteReferences = {
        "2C:XX-X"  // Replace with relevant statute references
    },
    CrimeCategoryName = "[CRIME_TYPE]",  // Replace with proper category name
    GeoJSONFilePath = "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\08_json\\arcgis_pro_layers\\[CRIME_TYPE]_7d.geojson",  // Update path
    ValidationMessage = "No [CRIME_TYPE] incidents found. Verify date range and crime type patterns."  // Update message

    // Load GeoJSON
    Source = Json.Document(
        File.Contents(GeoJSONFilePath)
    ),

    // Expand features list
    RootTable    = Table.FromRecords({ Source }),
    Features     = Table.ExpandListColumn(RootTable, "features"),
    ExpandedFeat = Table.ExpandRecordColumn(Features, "features", {"geometry","properties"}, {"Geometry","Properties"}),

    // Extract WebMercator X/Y from coordinates list
    ExpandedGeom     = Table.ExpandRecordColumn(ExpandedFeat, "Geometry", {"coordinates"}, {"Coordinates"}),
    AddWebMercatorX  = Table.AddColumn(ExpandedGeom, "WebMercator_X", each try [Coordinates]{0} otherwise null, type number),
    AddWebMercatorY  = Table.AddColumn(AddWebMercatorX, "WebMercator_Y", each try [Coordinates]{1} otherwise null, type number),

    // Expand only essential properties
    ExpandedProps = Table.ExpandRecordColumn(
        AddWebMercatorY,
        "Properties",
        {
            "OBJECTID","callid","calltype","callsource","fulladdr","beat","district",
            "calldate","dispatchdate","enroutedate","cleardate","responsetime",
            "description","probname"
        },
        {
            "objectid","callid","calltype","callsource","fulladdr","beat","district",
            "calldate","dispatchdate","enroutedate","cleardate","responsetime",
            "description","probname"
        }
    ),

    // Convert Unix-ms fields to datetime
    ConvertDates = Table.TransformColumns(
        ExpandedProps,
        {
            {"calldate",    each if _ <> null then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,_/1000) else null, type datetime},
            {"dispatchdate",each if _ <> null then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,_/1000) else null, type datetime},
            {"enroutedate", each if _ <> null then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,_/1000) else null, type datetime},
            {"cleardate",   each if _ <> null then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,_/1000) else null, type datetime}
        }
    ),
    RenamedDates = Table.RenameColumns(
        ConvertDates,
        {
            {"calldate",    "Call_Date"},
            {"dispatchdate","Dispatch_Date"},
            {"enroutedate", "Enroute_Date"},
            {"cleardate",   "Clear_Date"}
        }
    ),

    // Enhanced Date Filtering with Period Calculation
    AddPeriod = Table.AddColumn(
        RenamedDates,
        "Period_Calculated",
        each let
            call_date = [Call_Date],
            // Fixed cycle dates from Python script (C08W31)
            cycle_start_7day = #datetime(2025, 7, 30, 0, 0, 0),
            cycle_end_7day = #datetime(2025, 8, 5, 23, 59, 59),
            cycle_start_28day = #datetime(2025, 7, 9, 0, 0, 0)
        in
            if call_date = null then "Unknown"
            else if call_date >= cycle_start_7day and call_date <= cycle_end_7day then "7-Day"
            else if call_date >= cycle_start_28day and call_date < cycle_start_7day then "28-Day"
            else if Date.Year(call_date) = 2025 and call_date < cycle_start_28day then "YTD"
            else "Historical",
        type text
    ),

    // Enhanced Crime Type Filtering (Multiple Patterns)
    // UPDATE THIS SECTION WITH CRIME-SPECIFIC PATTERNS:
    FilteredCrimeType = Table.SelectRows(
        AddPeriod,
        each let
            call_type = Text.Upper([calltype] ?? ""),
            description = Text.Upper([description] ?? ""),
            probname = Text.Upper([probname] ?? "")
        in
            // Multiple pattern matching for [CRIME_TYPE]
            // Add your crime-specific patterns here:
            List.AnyTrue(List.Transform(CrimeTypePatterns, each Text.Contains(call_type, Text.Upper(_)))) or
            List.AnyTrue(List.Transform(StatuteReferences, each Text.Contains(call_type, Text.Upper(_)))) or
            // Check description field as backup
            List.AnyTrue(List.Transform(CrimeTypePatterns, each Text.Contains(description, Text.Upper(_)))) or
            // Check problem name field as backup
            List.AnyTrue(List.Transform(CrimeTypePatterns, each Text.Contains(probname, Text.Upper(_))))
    ),

    // Convert Web Mercator to Decimal Degrees (CORRECTED)
    AddLongitude = Table.AddColumn(
        FilteredCrimeType,
        "Longitude_DD",
        each if [WebMercator_X] <> null then 
            let
                // Convert from Web Mercator (EPSG:3857) to WGS84 decimal degrees
                x_normalized = [WebMercator_X] / 20037508.34,
                longitude = x_normalized * 180
            in
                // Validate longitude is within reasonable bounds for Hackensack, NJ
                if longitude >= -75 and longitude <= -73 then longitude else null
        else null,
        type number
    ),
    AddLatitude = Table.AddColumn(
        AddLongitude,
        "Latitude_DD", 
        each if [WebMercator_Y] <> null then
            let
                // Convert from Web Mercator (EPSG:3857) to WGS84 decimal degrees
                y_normalized = [WebMercator_Y] / 20037508.34,
                lat_radians = 2 * Number.Atan(Number.Exp(y_normalized * Number.PI)) - Number.PI/2,
                latitude = lat_radians * 180 / Number.PI
            in
                // Validate latitude is within reasonable bounds for Hackensack, NJ
                if latitude >= 40.5 and latitude <= 41.5 then latitude else null
        else null,
        type number
    ),

    // Compute response time (minutes)
    AddResponseMin = Table.AddColumn(
        AddLatitude,
        "Response_Time_Minutes",
        each if [responsetime] <> null then [responsetime] / 1000 / 60 else null,
        type number
    ),

    // Add Enhanced Analysis Columns
    AddTimeOfDay = Table.AddColumn(
        AddResponseMin,
        "TimeOfDay",
        each let
            call_hour = if [Call_Date] <> null then Time.Hour(DateTime.Time([Call_Date])) else null
        in
            if call_hour = null then "Unknown"
            else if call_hour < 4 then "00:00–03:59 Early Morning"
            else if call_hour < 8 then "04:00–07:59 Morning"  
            else if call_hour < 12 then "08:00–11:59 Morning Peak"
            else if call_hour < 16 then "12:00–15:59 Afternoon"
            else if call_hour < 20 then "16:00–19:59 Evening Peak"
            else "20:00–23:59 Night",
        type text
    ),

    AddResponseTimeDisplay = Table.AddColumn(
        AddTimeOfDay,
        "Response_Time_Display",
        each let
            minutes = [Response_Time_Minutes]
        in
            if minutes = null or minutes = 0 then "Unknown"
            else if minutes < 1 then Text.From(Number.Round(minutes * 60, 0)) & " seconds"
            else Text.From(Number.Round(minutes, 1)) & " min",
        type text
    ),

    AddCrimeCategory = Table.AddColumn(
        AddResponseTimeDisplay,
        "Crime_Category", 
        each CrimeCategoryName,
        type text
    ),

    AddCycleName = Table.AddColumn(
        AddCrimeCategory,
        "cycle_name",
        each "C08W31",  // Matches Python script cycle
        type text
    ),

    // Rename key fields
    RenamedCols = Table.RenameColumns(
        AddCycleName,
        {
            {"calltype", "clean_calltype"},
            {"callsource", "call_source"}
        }
    ),

    // Final Column Selection and Ordering
    Final = Table.SelectColumns(
        RenamedCols,
        {
            "objectid",
            "callid", 
            "cycle_name",
            "Period_Calculated",
            "Crime_Category",
            "clean_calltype",
            "call_source",
            "fulladdr",
            "beat",
            "district",
            "Call_Date",
            "Dispatch_Date", 
            "Enroute_Date",
            "Clear_Date",
            "Response_Time_Minutes",
            "Response_Time_Display",
            "TimeOfDay",
            "Longitude_DD",
            "Latitude_DD",
            "WebMercator_X",
            "WebMercator_Y"
        }
    ),

    // Rename period column to match expected format
    RenamedFinal = Table.RenameColumns(
        Final,
        {{"Period_Calculated", "period"}}
    ),

    // Data Validation and Error Handling
    ValidationResult = let
        row_count = Table.RowCount(RenamedFinal),
        coord_count = Table.RowCount(Table.SelectRows(RenamedFinal, each [Longitude_DD] <> null and [Latitude_DD] <> null)),
        coord_percentage = if row_count > 0 then coord_count / row_count else 0
    in
        if row_count = 0 then
            #table({"Message"}, {{ValidationMessage}})
        else if coord_percentage < 0.8 then
            Table.AddColumn(RenamedFinal, "Coordinate_Warning", each 
                if [Longitude_DD] = null or [Latitude_DD] = null then "Missing/Invalid Coordinates" else null, type text)
        else
            RenamedFinal

in
    ValidationResult 