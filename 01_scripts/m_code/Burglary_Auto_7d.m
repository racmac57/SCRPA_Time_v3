// 🕒 2025-08-02-15-35-00
// SCRPA_Time_v2/Complete_GeoJSON_Queries_Final_Drop_In_Ready
// Author: R. A. Carucci
// Purpose: All 5 GeoJSON queries with narrative truncation and time_of_day_visual fixes - Production Ready

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

    // ─── 5) Add quick date conversion for performance filtering ─────────────────
    AddQuickDate = Table.AddColumn(ExpandedProps, "call_date", each 
        try #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[calldate]/1000) otherwise null),
        
    // ─── 6) Filter to incidents on or after 12/31/2024 for performance ────────
    FilteredRecentGeo = Table.SelectRows(AddQuickDate, each 
        [call_date] >= #datetime(2024, 12, 31, 0, 0, 0)),

    // ─── 7) Rename key fields ─────────────────────────────────────────────────
    RenamedCols = Table.RenameColumns(
        FilteredRecentGeo,
        {
            {"calltype", "clean_call_type"},
            {"callsource", "call_source"}
        }
    ),

    // ─── 8) Filter to only "Burglary - Auto" incidents (case insensitive) ─────
    FilteredBurglaryAuto = Table.SelectRows(
        RenamedCols,
        each Text.Contains([clean_call_type], "Burglary - Auto", Comparer.OrdinalIgnoreCase)
    ),

    // ─── 9) Convert Mercator → Decimal Degrees ─────────────────────────────────
    AddLongitude = Table.AddColumn(
        FilteredBurglaryAuto,
        "longitude_dd",
        each [WebMercator_X] / 20037508.34 * 180,
        type number
    ),
    AddLatitude = Table.AddColumn(
        AddLongitude,
        "latitude_dd",
        each let y = [WebMercator_Y] / 20037508.34 * Number.PI
             in 180/Number.PI * (2*Number.Atan(Number.Exp(y)) - Number.PI/2),
        type number
    ),

    // ─── 10) Convert Unix-ms fields to datetime (call_date already exists from AddQuickDate)
    ConvertDates = Table.TransformColumns(
        AddLatitude,
        {
            {"dispatchdate",each if _ <> null then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,_/1000) else null, type datetime},
            {"enroutedate", each if _ <> null then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,_/1000) else null, type datetime},
            {"cleardate",   each if _ <> null then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,_/1000) else null, type datetime}
        }
    ),
    RenamedDates = Table.RenameColumns(
        ConvertDates,
        {
            {"dispatchdate","dispatch_date"},
            {"enroutedate", "enroute_date"},
            {"cleardate",   "clear_date"}
        }
    ),

    // ─── 11) Filter to incidents on or after 12/31/2024 ─────────────────────────
    FilteredIncidents = Table.SelectRows(
        RenamedDates,
        each [call_date] >= #datetime(2024, 12, 31, 0, 0, 0)
    ),

    // ─── 12) Compute response time (minutes) ────────────────────────────────────
    AddResponseMin = Table.AddColumn(
        FilteredIncidents,
        "response_time_minutes",
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
    WithCycle = Table.AddColumn(AddResponseMin, "cycle_name", 
        each GetCycle(Date.From([call_date])), type text),

    // ─── 13) Final columns & ordering (STANDARDIZED ORDER) ──────────────────────────────────────────
    Final = Table.SelectColumns(
        WithCycle,
        {
            "objectid",                    // 1st - ID field
            "cycle_name",                  // 2nd - Cycle information  
            "callid",                      // 3rd - Call identifier
            "clean_call_type",              // 4th - Call type
            "call_source",                 // 5th - Source
            "fulladdr",                    // 6th - Location (REQUIRED)
            "beat",                        // 7th - Beat/District
            "district",
            "call_date",                   // Date/Time fields
            "dispatch_date",
            "enroute_date", 
            "clear_date",
            "response_time_minutes",       // Performance metrics
            "longitude_dd",                // Coordinates
            "latitude_dd"
        }
    )
in
    Final