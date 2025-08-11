// Modified Power BI GeoJSON M Code Queries with Cycle Integration
// 🕒 2025-07-29-17-00-00
// Author: R. A. Carucci
// Purpose: Modified queries with dynamic cycle assignment using existing Cycle_Calendar query
// ✅ UPDATED: All column headers converted to lowercase with underscores (snake_case)

// ============================================================================
// QUERY 1: MV_Theft7d Query (Modified)
// ============================================================================

let
    // 1) Load GeoJSON
    Source = Json.Document(
        File.Contents(
            "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\08_json\\arcgis_pro_layers\\MV_Theft7d.geojson"
        )
    ),

    // 2) Convert root record to table and expand 'features'
    ConvertedToTable  = Table.FromRecords({ Source }),
    ExpandedFeatures  = Table.ExpandListColumn(ConvertedToTable, "features"),
    ExpandedGeomProps = Table.ExpandRecordColumn(
        ExpandedFeatures,
        "features",
        {"geometry","properties"},
        {"Geometry","Properties"}
    ),

    // 3) Extract WebMercator X/Y from coordinates
    AddWebMercatorX = Table.AddColumn(
        ExpandedGeomProps,
        "WebMercator_X",
        each try [Geometry][coordinates]{0} otherwise null,
        type number
    ),
    AddWebMercatorY = Table.AddColumn(
        AddWebMercatorX,
        "WebMercator_Y",
        each try [Geometry][coordinates]{1} otherwise null,
        type number
    ),

    // 4) Expand all properties
    ExpandedProps = Table.ExpandRecordColumn(
        AddWebMercatorY,
        "Properties",
        {
            "OBJECTID","callid","callcat","calltype","priority","description",
            "callsource","callerinfo","fulladdr","city","state","zip","locdesc",
            "beat","district","division","calldate","callyear","callmonth",
            "calldow","calldownum","callhour","dispatchdate","enroutedate",
            "arrivaldate","cleardate","dispatchtime","queuetime","traveltime",
            "cleartime","responsetime","agency","firstunit","unittotal",
            "disposition","comments","analystnotes","probname","probtype","x","y"
        },
        {
            "objectid","call_id","call_category","call_type","priority","description",
            "call_source","caller_info","full_address","city","state","zip",
            "location_description","beat","district","division","call_date_unix",
            "call_year","call_month","call_day_of_week","call_day_number","call_hour",
            "dispatch_date_unix","enroute_date_unix","arrival_date_unix","clear_date_unix",
            "dispatch_time_minutes","queue_time_minutes","travel_time_minutes",
            "clear_time_minutes","response_time_minutes","agency","first_unit",
            "unit_total","disposition","comments","analyst_notes","problem_name",
            "problem_type","x_fallback","y_fallback"
        }
    ),

    // 5) Convert UNIX‐epoch fields into datetimes
    AddedCallDate = Table.AddColumn(
        ExpandedProps,
        "call_date",
        each if [call_date_unix] <> null then
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[call_date_unix]/1000)
        else null,
        type datetime
    ),
    AddedDispatchDate = Table.AddColumn(
        AddedCallDate,
        "dispatch_date",
        each if [dispatch_date_unix] <> null then
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[dispatch_date_unix]/1000)
        else null,
        type datetime
    ),
    AddedEnrouteDate = Table.AddColumn(
        AddedDispatchDate,
        "enroute_date",
        each if [enroute_date_unix] <> null then
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[enroute_date_unix]/1000)
        else null,
        type datetime
    ),
    AddedClearDate = Table.AddColumn(
        AddedEnrouteDate,
        "clear_date",
        each if [clear_date_unix] <> null then
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[clear_date_unix]/1000)
        else null,
        type datetime
    ),

    // 6) Filter to incidents on or after December 31, 2024
    FilteredIncidents = Table.SelectRows(
        AddedClearDate,
        each [call_date] >= #datetime(2024, 12, 31, 0, 0, 0)
    ),

    // 7) Convert Web Mercator to Decimal Degrees
    AddedLongitude_DD = Table.AddColumn(
        FilteredIncidents,
        "longitude_dd",
        each [WebMercator_X] / 20037508.34 * 180,
        type number
    ),
    AddedLatitude_DD = Table.AddColumn(
        AddedLongitude_DD,
        "latitude_dd",
        each let y = [WebMercator_Y] / 20037508.34 * Number.PI
             in 180/Number.PI * (2 * Number.Atan(Number.Exp(y)) - Number.PI/2),
        type number
    ),

    // 8) Clean up Call_Type field
    AddedCleanCallType = Table.AddColumn(
        AddedLatitude_DD,
        "clean_call_type",
        each if [call_type] <> null and Text.Contains([call_type], " - 2C")
             then Text.BeforeDelimiter([call_type], " - 2C")
             else if [call_type] <> null
                  then [call_type]
                  else "Unknown",
        type text
    ),

    // === CYCLE INTEGRATION ===
    CycleTable = Cycle_Calendar,
    
    // Function to get cycle for any incident date
    GetCycle = (incidentDate as date) as text =>
        let
            MatchingCycle = Table.SelectRows(CycleTable, 
                each [#"7_Day_Start"] <= incidentDate and [#"7_Day_End"] >= incidentDate)
        in
            if Table.RowCount(MatchingCycle) > 0 
            then MatchingCycle{0}[Report_Name] 
            else "UNKNOWN",
    
    // Add cycle column to all records
    WithCycle = Table.AddColumn(AddedCleanCallType, "cycle_name", 
        each GetCycle(Date.From([call_date])), type text),

    // 9) Select and order final columns (SNAKE_CASE HEADERS)
    SelectedFinalColumns = Table.SelectColumns(
        WithCycle,
        {
            "objectid",
            "cycle_name",
            "call_id",
            "clean_call_type",
            "call_source",
            "full_address",
            "beat",
            "district",
            "call_date",
            "dispatch_date",
            "enroute_date",
            "clear_date",
            "response_time_minutes",
            "longitude_dd",
            "latitude_dd"
        }
    ),

    // 10) Ensure correct data types (SNAKE_CASE HEADERS)
    ChangedFinalTypes = Table.TransformColumnTypes(
        SelectedFinalColumns,
        {
            {"objectid", Int64.Type},
            {"cycle_name", type text},
            {"call_id", type text},
            {"clean_call_type", type text},
            {"call_source", type text},
            {"full_address", type text},
            {"beat", type text},
            {"district", type text},
            {"call_date", type datetime},
            {"dispatch_date", type datetime},
            {"enroute_date", type datetime},
            {"clear_date", type datetime},
            {"response_time_minutes", type number},
            {"longitude_dd", type number},
            {"latitude_dd", type number}
        }
    )
in
    ChangedFinalTypes

// Burglary_Auto_7d Query (Modified)

let
    // ─── 1) Load GeoJSON ───────────────────────────────────────────────────────
    Source = Json.Document(
        File.Contents(
            "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\08_json\\arcgis_pro_layers\\Burglary_Auto_7d.geojson"
        )
    ),

    // ─── 2) Expand features list ──────────────────────────────────────────────
    RootTable    = Table.FromRecords({ Source }),
    Features     = Table.ExpandListColumn(RootTable, "features"),
    ExpandedFeat = Table.ExpandRecordColumn(Features, "features", {"geometry","properties"}, {"Geometry","Properties"}),

    // ─── 3) Extract WebMercator X/Y from coordinates list ─────────────────────
    ExpandedGeom     = Table.ExpandRecordColumn(ExpandedFeat, "Geometry", {"coordinates"}, {"Coordinates"}),
    AddWebMercatorX  = Table.AddColumn(ExpandedGeom, "WebMercator_X", each try [Coordinates]{0} otherwise null, type number),
    AddWebMercatorY  = Table.AddColumn(AddWebMercatorX, "WebMercator_Y", each try [Coordinates]{1} otherwise null, type number),

    // ─── 4) Expand all properties ───────────────────────────────────────────────
    ExpandedProps = Table.ExpandRecordColumn(
        AddWebMercatorY,
        "Properties",
        {
            "OBJECTID","callid","callcat","calltype","priority","description","callsource","callerinfo",
            "fulladdr","city","state","zip","locdesc","beat","district","division","calldate",
            "callyear","callmonth","calldow","calldownum","callhour","dispatchdate",
            "enroutedate","arrivaldate","cleardate","dispatchtime","queuetime","traveltime",
            "cleartime","responsetime","agency","firstunit","unittotal","disposition",
            "comments","analystnotes","probname","probtype","x","y"
        },
        {
            "objectid","callid","callcat","calltype","priority","description","callsource","callerinfo",
            "fulladdr","city","state","zip","locdesc","beat","district","division","calldate",
            "callyear","callmonth","calldow","calldownum","callhour","dispatchdate",
            "enroutedate","arrivaldate","cleardate","dispatchtime","queuetime","traveltime",
            "cleartime","responsetime","agency","firstunit","unittotal","disposition",
            "comments","analystnotes","probname","probtype","x","y"
        }
    ),

    // ─── 5) Rename key fields ─────────────────────────────────────────────────
    RenamedCols = Table.RenameColumns(
        ExpandedProps,
        {
            {"calltype", "Clean_CallType"},
            {"callsource", "Call_Source"}
        }
    ),

    // ─── 6) Convert Mercator → Decimal Degrees ─────────────────────────────────
    AddLongitude = Table.AddColumn(
        RenamedCols,
        "Longitude_DD",
        each [WebMercator_X] / 20037508.34 * 180,
        type number
    ),
    AddLatitude = Table.AddColumn(
        AddLongitude,
        "Latitude_DD",
        each let y = [WebMercator_Y] / 20037508.34 * Number.PI
             in 180/Number.PI * (2*Number.Atan(Number.Exp(y)) - Number.PI/2),
        type number
    ),

    // ─── 7) Convert Unix-ms fields to datetime ─────────────────────────────────
    ConvertDates = Table.TransformColumns(
        AddLatitude,
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

    // ─── 8) Filter to incidents on or after 12/31/2024 ─────────────────────────
    FilteredIncidents = Table.SelectRows(
        RenamedDates,
        each [Call_Date] >= #datetime(2024, 12, 31, 0, 0, 0)
    ),

    // ─── 9) Compute response time (minutes) ────────────────────────────────────
    AddResponseMin = Table.AddColumn(
        FilteredIncidents,
        "Response_Time_Minutes",
        each if [responsetime] <> null then [responsetime] / 1000 / 60 else null,
        type number
    ),

    // === CYCLE INTEGRATION ===
    CycleTable = Cycle_Calendar,
    
    // Function to get cycle for any incident date
    GetCycle = (incidentDate as date) as text =>
        let
            MatchingCycle = Table.SelectRows(CycleTable, 
                each [#"7_Day_Start"] <= incidentDate and [#"7_Day_End"] >= incidentDate)
        in
            if Table.RowCount(MatchingCycle) > 0 
            then MatchingCycle{0}[Report_Name] 
            else "UNKNOWN",
    
    // Add cycle column to all records
    WithCycle = Table.AddColumn(AddResponseMin, "Cycle_Name", 
        each GetCycle(Date.From([Call_Date])), type text),

    // ─── 10) Final columns & ordering (LOWERCASE HEADERS) ──────────────────────────────────────────
    Final = Table.SelectColumns(
        WithCycle,
        {
            "objectid",
            "callid",
            "cycle_name",
            "clean_calltype",
            "call_source",
            "fulladdr",
            "beat",
            "district",
            "call_date",
            "dispatch_date",
            "enroute_date",
            "clear_date",
            "response_time_minutes",
            "longitude_dd",
            "latitude_dd"
        }
    )
in
    Final

// Burglary_Comm_Res_7d Query (Modified)

let
    // ─── 1) Load GeoJSON ───────────────────────────────────────────────────────
    Source = Json.Document(
        File.Contents(
            "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\08_json\\arcgis_pro_layers\\Burglary_Comm_Res_7d.geojson"
        )
    ),

    // ─── 2) Expand features list ──────────────────────────────────────────────
    RootTable    = Table.FromRecords({ Source }),
    Features     = Table.ExpandListColumn(RootTable, "features"),
    ExpandedFeat = Table.ExpandRecordColumn(Features, "features", {"geometry","properties"}, {"Geometry","Properties"}),

    // ─── 3) Extract WebMercator X/Y from coordinates ──────────────────────────
    AddWebMercatorX = Table.AddColumn(
        ExpandedFeat,
        "WebMercator_X",
        each try [Geometry][coordinates]{0} otherwise null,
        type number
    ),
    AddWebMercatorY = Table.AddColumn(
        AddWebMercatorX,
        "WebMercator_Y",
        each try [Geometry][coordinates]{1} otherwise null,
        type number
    ),

    // ─── 4) Expand all properties ───────────────────────────────────────────────
    ExpandedProps = Table.ExpandRecordColumn(
        AddWebMercatorY,
        "Properties",
        {
            "OBJECTID","callid","callcat","calltype","priority","description","callsource","callerinfo",
            "fulladdr","city","state","zip","locdesc","beat","district","division","calldate",
            "callyear","callmonth","calldow","calldownum","callhour","dispatchdate",
            "enroutedate","arrivaldate","cleardate","dispatchtime","queuetime","traveltime",
            "cleartime","responsetime","agency","firstunit","unittotal","disposition",
            "comments","analystnotes","probname","probtype","x","y"
        },
        {
            "objectid","callid","callcat","calltype","priority","description","callsource","callerinfo",
            "fulladdr","city","state","zip","locdesc","beat","district","division","calldate",
            "callyear","callmonth","calldow","calldownum","callhour","dispatchdate",
            "enroutedate","arrivaldate","cleardate","dispatchtime","queuetime","traveltime",
            "cleartime","responsetime","agency","firstunit","unittotal","disposition",
            "comments","analystnotes","probname","probtype","x","y"
        }
    ),

    // ─── 5) Rename key fields ─────────────────────────────────────────────────
    RenamedCols = Table.RenameColumns(
        ExpandedProps,
        {
            {"calltype",   "Clean_CallType"},
            {"callsource", "Call_Source"}
        }
    ),

    // ─── 6) Convert Mercator → Decimal Degrees ─────────────────────────────────
    AddLongitude = Table.AddColumn(
        RenamedCols,
        "Longitude_DD",
        each [WebMercator_X] / 20037508.34 * 180,
        type number
    ),
    AddLatitude = Table.AddColumn(
        AddLongitude,
        "Latitude_DD",
        each let y = [WebMercator_Y] / 20037508.34 * Number.PI
             in 180/Number.PI * (2*Number.Atan(Number.Exp(y)) - Number.PI/2),
        type number
    ),

    // ─── 7) Convert Unix-ms timestamps to datetime ─────────────────────────────
    ConvertedDates = Table.TransformColumns(
        AddLatitude,
        {
            {"calldate",    each if _ <> null then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,_/1000) else null, type datetime},
            {"dispatchdate",each if _ <> null then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,_/1000) else null, type datetime},
            {"enroutedate", each if _ <> null then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,_/1000) else null, type datetime},
            {"cleardate",   each if _ <> null then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,_/1000) else null, type datetime}
        }
    ),
    RenamedDates = Table.RenameColumns(
        ConvertedDates,
        {
            {"calldate",    "Call_Date"},
            {"dispatchdate","Dispatch_Date"},
            {"enroutedate", "Enroute_Date"},
            {"cleardate",   "Clear_Date"}
        }
    ),

    // ─── 8) Filter to incidents on or after 12/31/2024 ─────────────────────────
    FilteredIncidents = Table.SelectRows(
        RenamedDates,
        each [Call_Date] >= #datetime(2024, 12, 31, 0, 0, 0)
    ),

    // ─── 9) Compute response time in minutes ───────────────────────────────────
    AddResponseMin = Table.AddColumn(
        FilteredIncidents,
        "Response_Time_Minutes",
        each if [responsetime] <> null then [responsetime] / 1000 / 60 else null,
        type number
    ),

    // === CYCLE INTEGRATION ===
    CycleTable = Cycle_Calendar,
    
    // Function to get cycle for any incident date
    GetCycle = (incidentDate as date) as text =>
        let
            MatchingCycle = Table.SelectRows(CycleTable, 
                each [#"7_Day_Start"] <= incidentDate and [#"7_Day_End"] >= incidentDate)
        in
            if Table.RowCount(MatchingCycle) > 0 
            then MatchingCycle{0}[Report_Name] 
            else "UNKNOWN",
    
    // Add cycle column to all records
    WithCycle = Table.AddColumn(AddResponseMin, "Cycle_Name", 
        each GetCycle(Date.From([Call_Date])), type text),

    // ─── 10) Select and order final columns (LOWERCASE HEADERS) ────────────────────────────────────
    Final = Table.SelectColumns(
        WithCycle,
        {
            "objectid",
            "callid",
            "cycle_name",
            "clean_calltype",
            "call_source",
            "fulladdr",
            "beat",
            "district",
            "call_date",
            "dispatch_date",
            "enroute_date",
            "clear_date",
            "response_time_minutes",
            "longitude_dd",
            "latitude_dd"
        }
    )
in
    Final

// Robbery_7d Query (Modified)

let
    // 1) Load GeoJSON
    Source = Json.Document(
        File.Contents(
            "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\08_json\\arcgis_pro_layers\\Robbery_7d.geojson"
        )
    ),

    // 2) Convert root record to table and expand 'features'
    ConvertedToTable  = Table.FromRecords({ Source }),
    ExpandedFeatures  = Table.ExpandListColumn(ConvertedToTable, "features"),
    ExpandedGeomProps = Table.ExpandRecordColumn(
        ExpandedFeatures,
        "features",
        {"geometry","properties"},
        {"Geometry","Properties"}
    ),

    // 3) Extract WebMercator X/Y from coordinates
    AddWebMercatorX = Table.AddColumn(
        ExpandedGeomProps,
        "WebMercator_X",
        each try [Geometry][coordinates]{0} otherwise null,
        type number
    ),
    AddWebMercatorY = Table.AddColumn(
        AddWebMercatorX,
        "WebMercator_Y",
        each try [Geometry][coordinates]{1} otherwise null,
        type number
    ),

    // 4) Expand all properties from the JSON
    ExpandedProps = Table.ExpandRecordColumn(
        AddWebMercatorY,
        "Properties",
        {
            "OBJECTID","callid","callcat","calltype","priority","description",
            "callsource","callerinfo","fulladdr","city","state","zip","locdesc",
            "beat","district","division","calldate","callyear","callmonth",
            "calldow","calldownum","callhour","dispatchdate","enroutedate",
            "arrivaldate","cleardate","dispatchtime","queuetime","traveltime",
            "cleartime","responsetime","agency","firstunit","unittotal",
            "disposition","comments","analystnotes","probname","probtype","x","y"
        },
        {
            "objectid","call_id","call_category","call_type","priority","description",
            "call_source","caller_info","full_address","city","state","zip",
            "location_description","beat","district","division","call_date_unix",
            "call_year","call_month","call_day_of_week","call_day_number","call_hour",
            "dispatch_date_unix","enroute_date_unix","arrival_date_unix","clear_date_unix",
            "dispatch_time_minutes","queue_time_minutes","travel_time_minutes",
            "clear_time_minutes","response_time_minutes","agency","first_unit",
            "unit_total","disposition","comments","analyst_notes","problem_name",
            "problem_type","x_fallback","y_fallback"
        }
    ),

    // 5) Convert UNIX‐epoch fields into datetimes
    AddedCallDate = Table.AddColumn(
        ExpandedProps,
        "call_date",
        each if [call_date_unix] <> null 
             then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[call_date_unix]/1000)
             else null,
        type datetime
    ),
    AddedDispatchDate = Table.AddColumn(
        AddedCallDate,
        "dispatch_date",
        each if [dispatch_date_unix] <> null 
             then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[dispatch_date_unix]/1000)
             else null,
        type datetime
    ),
    AddedEnrouteDate = Table.AddColumn(
        AddedDispatchDate,
        "enroute_date",
        each if [enroute_date_unix] <> null 
             then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[enroute_date_unix]/1000)
             else null,
        type datetime
    ),
    AddedArrivalDate = Table.AddColumn(
        AddedEnrouteDate,
        "arrival_date",
        each if [arrival_date_unix] <> null 
             then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[arrival_date_unix]/1000)
             else null,
        type datetime
    ),
    AddedClearDate = Table.AddColumn(
        AddedArrivalDate,
        "clear_date",
        each if [clear_date_unix] <> null 
             then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[clear_date_unix]/1000)
             else null,
        type datetime
    ),

    // 6) Filter to incidents on or after 12/31/2024
    FilteredIncidents = Table.SelectRows(
        AddedClearDate,
        each [call_date] >= #datetime(2024, 12, 31, 0, 0, 0)
    ),

    // 7) Convert Web Mercator to Decimal Degrees
    AddedLongitude = Table.AddColumn(
        FilteredIncidents,
        "longitude_dd",
        each [WebMercator_X] / 20037508.34 * 180,
        type number
    ),
    AddedLatitude = Table.AddColumn(
        AddedLongitude,
        "latitude_dd",
        each let y = [WebMercator_Y] / 20037508.34 * Number.PI
             in 180/Number.PI * (2 * Number.Atan(Number.Exp(y)) - Number.PI/2),
        type number
    ),

    // 8) Clean up Call_Type field
    AddedCleanCallType = Table.AddColumn(
        AddedLatitude,
        "clean_call_type",
        each if [call_type] <> null and Text.Contains([call_type], " - 2C")
             then Text.BeforeDelimiter([call_type], " - 2C")
             else if [call_type] <> null then [call_type] else "Unknown",
        type text
    ),

    // === CYCLE INTEGRATION ===
    CycleTable = Cycle_Calendar,
    
    // Function to get cycle for any incident date
    GetCycle = (incidentDate as date) as text =>
        let
            MatchingCycle = Table.SelectRows(CycleTable, 
                each [#"7_Day_Start"] <= incidentDate and [#"7_Day_End"] >= incidentDate)
        in
            if Table.RowCount(MatchingCycle) > 0 
            then MatchingCycle{0}[Report_Name] 
            else "UNKNOWN",
    
    // Add cycle column to all records
    WithCycle = Table.AddColumn(AddedCleanCallType, "cycle_name", 
        each GetCycle(Date.From([call_date])), type text),

    // 9) Select and order final columns (SNAKE_CASE HEADERS)
    SelectedFinalColumns = Table.SelectColumns(
        WithCycle,
        {
            "objectid",
            "call_id",
            "cycle_name",
            "clean_call_type",
            "call_source",
            "full_address",
            "beat",
            "district",
            "call_date",
            "dispatch_date",
            "enroute_date",
            "clear_date",
            "response_time_minutes",
            "longitude_dd",
            "latitude_dd"
        }
    ),

    // 10) Ensure correct data types (SNAKE_CASE HEADERS)
    ChangedFinalTypes = Table.TransformColumnTypes(
        SelectedFinalColumns,
        {
            {"objectid", Int64.Type},
            {"call_id", type text},
            {"cycle_name", type text},
            {"clean_call_type", type text},
            {"call_source", type text},
            {"full_address", type text},
            {"beat", type text},
            {"district", type text},
            {"call_date", type datetime},
            {"dispatch_date", type datetime},
            {"enroute_date", type datetime},
            {"clear_date", type datetime},
            {"response_time_minutes", type number},
            {"longitude_dd", type number},
            {"latitude_dd", type number}
        }
    )
in
    ChangedFinalTypes

// Sexual_Offenses_7d Query (Modified)

let
    // 1) Load JSON source
    Source = Json.Document(
        File.Contents(
            "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\08_json\\arcgis_pro_layers\\Sexual_Offenses_7d.geojson"
        )
    ),

    // 2) Expand features
    #"Converted to Table"      = Table.FromRecords({ Source }),
    #"Expanded features"       = Table.ExpandListColumn(#"Converted to Table", "features"),
    #"Expanded features1"      = Table.ExpandRecordColumn(
                                    #"Expanded features",
                                    "features",
                                    {"geometry","properties"},
                                    {"features.geometry","features.properties"}
                                ),
    #"Expanded features.geometry" = Table.ExpandRecordColumn(
                                    #"Expanded features1",
                                    "features.geometry",
                                    {"coordinates"},
                                    {"features.geometry.coordinates"}
                                ),

    // 3) Split coordinates into WebMercator X/Y
    #"Split Coordinates"       = Table.SplitColumn(
                                    #"Expanded features.geometry",
                                    "features.geometry.coordinates",
                                    Splitter.SplitByNothing(),
                                    {"Longitude_Web_Mercator","Latitude_Web_Mercator"}
                                ),
    #"Changed Coord Types"     = Table.TransformColumnTypes(
                                    #"Split Coordinates",
                                    {{"Longitude_Web_Mercator", type number},{"Latitude_Web_Mercator", type number}}
                                ),

    // 4) Expand all properties
    #"Expanded features.properties" = Table.ExpandRecordColumn(
        #"Changed Coord Types",
        "features.properties",
        {
          "objectid","callid","callcat","calltype","priority","description","callsource","callerinfo",
          "fulladdr","city","state","zip","locdesc","beat","district","division","calldate",
          "callyear","callmonth","calldow","calldownum","callhour","dispatchdate","enroutedate",
          "arrivaldate","cleardate","dispatchtime","queuetime","traveltime","cleartime",
          "responsetime","agency","firstunit","unittotal","disposition","comments","analystnotes",
          "probname","probtype","x_fallback","y_fallback"
        },
        {
          "objectid","call_id","call_category","call_type","priority","description","call_source","caller_info",
          "full_address","city","state","zip","locdesc","beat","district","division","calldate",
          "callyear","callmonth","calldow","calldownum","callhour","dispatchdate","enroutedate",
          "arrivaldate","cleardate","dispatchtime","queuetime","traveltime","cleartime",
          "responsetime","agency","firstunit","unittotal","disposition","comments","analystnotes",
          "probname","probtype","x_fallback","y_fallback"
        }
    ),

    // 5) Convert Unix timestamps to datetimezone
    #"Added Call_Date"         = Table.AddColumn(
                                    #"Expanded features.properties",
                                    "call_date",
                                    each if [call_date_unix] <> null
                                         then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[call_date_unix]/1000)
                                         else null,
                                    type datetimezone
                                ),
    #"Added Dispatch_Date"     = Table.AddColumn(
                                    #"Added Call_Date",
                                    "dispatch_date",
                                    each if [dispatch_date_unix] <> null
                                         then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[dispatch_date_unix]/1000)
                                         else null,
                                    type datetimezone
                                ),
    #"Added Enroute_Date"      = Table.AddColumn(
                                    #"Added Dispatch_Date",
                                    "enroute_date",
                                    each if [enroutedate_unix] <> null
                                         then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[enroutedate_unix]/1000)
                                         else null,
                                    type datetimezone
                                ),
    #"Added Clear_Date"        = Table.AddColumn(
                                    #"Added Enroute_Date",
                                    "clear_date",
                                    each if [cleardate_unix] <> null
                                         then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[cleardate_unix]/1000)
                                         else null,
                                    type datetimezone
                                ),

    // 6) Filter to incidents on or after December 31, 2024
    #"Filtered Recent Incidents" = Table.SelectRows(
                                    #"Added Clear_Date",
                                    each [call_date] >= #datetimezone(2024,12,31,0,0,0,0,0)
                                ),

    // 7) Convert WebMercator to Decimal Degrees, with fallbacks
    #"Added Longitude_DD"      = Table.AddColumn(
                                    #"Filtered Recent Incidents",
                                    "longitude_dd",
                                    each if [Longitude_Web_Mercator] <> null
                                         then [Longitude_Web_Mercator] / 20037508.34 * 180
                                         else [x_fallback],
                                    type number
                                ),
    #"Added Latitude_DD"       = Table.AddColumn(
                                    #"Added Longitude_DD",
                                    "latitude_dd",
                                    each if [Latitude_Web_Mercator] <> null then
                                        let
                                            pi = 3.14159265359,
                                            y = [Latitude_Web_Mercator] / 20037508.34 * pi
                                        in 180/pi * (2*Number.Atan(Number.Exp(y)) - pi/2)
                                         else [y_fallback],
                                    type number
                                ),

    // 8) Enhance with categories
    #"Added Time_Of_Day_Category" = Table.AddColumn(
                                    #"Added Latitude_DD",
                                    "time_of_day_category",
                                    each let h = [callhour] in
                                        if h = null then "Unknown"
                                        else if h < 6 then "00:00-05:59 Overnight"
                                        else if h < 12 then "06:00-11:59 Morning"
                                        else if h < 18 then "12:00-17:59 Afternoon"
                                        else "18:00-23:59 Evening",
                                    type text
                                ),
    #"Added Response_Time_Category" = Table.AddColumn(
                                    #"Added Time_Of_Day_Category",
                                    "response_time_category",
                                    each let r = [responsetime] in
                                        if r = null then "Unknown"
                                        else if r <= 5 then "0-5 Min (Excellent)"
                                        else if r <= 10 then "5-10 Min (Good)"
                                        else if r <= 15 then "10-15 Min (Average)"
                                        else "15+ Min (Needs Attention)",
                                    type text
                                ),

    // 9) Clean up call type
    #"Added Clean_Call_Type"   = Table.AddColumn(
                                    #"Added Response_Time_Category",
                                    "clean_call_type",
                                    each if [call_type] <> null and Text.Contains([call_type]," - 2C")
                                         then Text.BeforeDelimiter([call_type]," - 2C")
                                         else if [call_type] <> null then [call_type] else "Unknown",
                                    type text
                                ),

    // === CYCLE INTEGRATION ===
    CycleTable = Cycle_Calendar,
    
    // Function to get cycle for any incident date
    GetCycle = (incidentDate as date) as text =>
        let
            MatchingCycle = Table.SelectRows(CycleTable, 
                each [#"7_Day_Start"] <= incidentDate and [#"7_Day_End"] >= incidentDate)
        in
            if Table.RowCount(MatchingCycle) > 0 
            then MatchingCycle{0}[Report_Name] 
            else "UNKNOWN",
    
    // Add cycle column to all records
    WithCycle = Table.AddColumn(#"Added Clean_Call_Type", "cycle_name", 
        each GetCycle(Date.From([call_date])), type text),

    // 10) Final selection and type enforcement (LOWERCASE HEADERS)
    #"Selected Final Columns"  = Table.SelectColumns(
                                    WithCycle,
                                    {
                                      "objectid","call_id","cycle_name","clean_call_type","call_source","full_address","beat",
                                      "district","call_date","call_year","call_month","call_day_of_week","call_hour",
                                      "time_of_day_category","dispatch_date","enroute_date","clear_date",
                                      "response_time_minutes","response_time_category","dispatch_time_minutes",
                                      "clear_time_minutes","first_unit","disposition","longitude_dd","latitude_dd"
                                    }
                                ),
    #"Changed Final Types"     = Table.TransformColumnTypes(
                                    #"Selected Final Columns",
                                    {
                                      {"objectid", Int64.Type},{"call_id", type text},{"cycle_name", type text},{"clean_call_type", type text},
                                      {"call_source", type text},{"full_address", type text},{"beat", type text},
                                      {"district", type text},{"call_date", type datetimezone},{"call_year", Int64.Type},
                                      {"call_month", Int64.Type},{"call_day_of_week", type text},{"call_hour", Int64.Type},
                                      {"time_of_day_category", type text},{"dispatch_date", type datetimezone},
                                      {"enroute_date", type datetimezone},{"clear_date", type datetimezone},
                                      {"response_time_minutes", type number},{"response_time_category", type text},
                                      {"dispatch_time_minutes", type number},{"clear_time_minutes", type number},
                                      {"first_unit", type text},{"disposition", type text},
                                      {"longitude_dd", type number},{"latitude_dd", type number}
                                    }
                                )
in
    #"Changed Final Types"
