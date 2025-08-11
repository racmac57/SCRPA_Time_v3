// 🕒 2025-08-02-15-35-00
// SCRPA_Time_v2/Optimized_GeoJSON_Queries
// Author: R. A. Carucci
// Purpose: Optimized queries for compressed GeoJSON files with enhanced performance
// ✅ OPTIMIZED: Compressed files, reduced precision, essential properties only

// Robbery_7d Query (Optimized for Performance)

let
    // ─── 1) Load compressed GeoJSON (MUCH FASTER) ─────────────────────────────
    Source = Json.Document(
        Binary.Decompress(
            File.Contents(
                "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\08_json\\arcgis_pro_layers\\Robbery_7d.geojson.gz"
            ),
            Compression.GZip
        )
    ),

    // ─── 2) Expand features list ──────────────────────────────────────────────
    RootTable    = Table.FromRecords({ Source }),
    Features     = Table.ExpandListColumn(RootTable, "features"),
    ExpandedFeat = Table.ExpandRecordColumn(Features, "features", {"geometry","properties"}, {"Geometry","Properties"}),

    // ─── 3) Extract coordinates (already optimized precision) ─────────────────
    ExpandedGeom     = Table.ExpandRecordColumn(ExpandedFeat, "Geometry", {"coordinates"}, {"Coordinates"}),
    AddWebMercatorX  = Table.AddColumn(ExpandedGeom, "WebMercator_X", each try [Coordinates]{0} otherwise null, type number),
    AddWebMercatorY  = Table.AddColumn(AddWebMercatorX, "WebMercator_Y", each try [Coordinates]{1} otherwise null, type number),

    // ─── 4) Expand only essential properties (already filtered) ───────────────
    ExpandedProps = Table.ExpandRecordColumn(
        AddWebMercatorY,
        "Properties",
        {
            "OBJECTID","callid","calltype","callsource","fulladdr","beat","district",
            "calldate","dispatchdate","enroutedate","cleardate","responsetime"
        },
        {
            "objectid","callid","calltype","callsource","fulladdr","beat","district",
            "calldate","dispatchdate","enroutedate","cleardate","responsetime"
        }
    ),

    // ─── 5) Convert Unix-ms fields to datetime ─────────────────────────────────
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

    // ─── 6) EARLY FILTERING: Filter to incidents on or after 12/31/2024 ───────
    FilteredIncidents = Table.SelectRows(
        RenamedDates,
        each [Call_Date] >= #datetime(2024, 12, 31, 0, 0, 0)
    ),

    // ─── 7) EARLY FILTERING: Filter to "Robbery" incidents ───────────
    FilteredRobbery = Table.SelectRows(
        FilteredIncidents,
        each Text.Contains(Text.Upper([calltype]), "ROBBERY")
    ),

    // ─── 8) Convert Mercator → Decimal Degrees (ONLY FOR FILTERED DATA) ───────
    AddLongitude = Table.AddColumn(
        FilteredRobbery,
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

    // ─── 9) Compute response time (minutes) ────────────────────────────────────
    AddResponseMin = Table.AddColumn(
        AddLatitude,
        "Response_Time_Minutes",
        each if [responsetime] <> null then [responsetime] / 1000 / 60 else null,
        type number
    ),

    // ─── 10) Rename key fields ──────────────────────────────────────────────────
    RenamedCols = Table.RenameColumns(
        AddResponseMin,
        {
            {"calltype", "clean_calltype"},
            {"callsource", "call_source"}
        }
    ),

    // ─── 11) Add dynamic period calculation (like Python script) ───────────────
    WithPeriod = Table.AddColumn(
        RenamedCols, 
        "period", 
        each let
            incidentDate = [Call_Date],
            today = DateTime.LocalNow(),
            daysDiff = Duration.Days(today - incidentDate)
        in
            if daysDiff <= 7 then "7-Day"
            else if daysDiff <= 28 then "28-Day"
            else "YTD",
        type text
    ),

    // ─── 12) Add cycle_name using simplified calculation ───────────────────────
    WithCycle = Table.AddColumn(
        WithPeriod, 
        "cycle_name", 
        each let
            incidentDate = Date.From([Call_Date]),
            weekNum = Date.WeekOfYear(incidentDate),
            cycleNum = Number.IntegerDivide(weekNum - 1, 4) + 1,
            weekInCycle = Number.Mod(weekNum - 1, 4) + 1
        in
            "C" & Text.PadStart(Text.From(cycleNum), 2, "0") & "W" & Text.PadStart(Text.From(weekInCycle), 2, "0"),
        type text
    ),

    // ─── 13) Final columns & ordering ─────────────────────────────────────────
    Final = Table.SelectColumns(
        WithCycle,
        {
            "objectid",
            "callid",
            "cycle_name",
            "period",
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
            "Longitude_DD",
            "Latitude_DD"
        }
    )
in
    Final