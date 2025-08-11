CAD_RMS_Matched_Standardized M Code:

let
    // === CONFIGURATION ===
    DataPath = "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi\cad_rms_matched_standardized.csv",
    
    // === DATA LOADING ===
    Source = Csv.Document(File.Contents(DataPath), [Delimiter=",", Columns=42, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    
    // === DATA TYPE CONVERSIONS ===
    TypedData = Table.TransformColumnTypes(Headers, {
        // RMS Columns
        {"case_number", type text},
        {"incident_date", type date},
        {"incident_time", type time},
        {"time_of_day", type text},
        {"time_of_day_sort_order", Int64.Type},
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
        {"total_value_recovered", type number},
        {"squad", type text},
        {"officer_of_record", type text},
        {"nibrs_classification", type text},
        
        // CAD Columns (with _cad suffix)
        {"case_number_cad", type text},
        {"response_type_cad", type text},
        {"category_type_cad", type text},
        {"how_reported_cad", type text},
        {"location_cad", type text},
        {"block_cad", type text},
        {"grid_cad", type text},
        {"post_cad", type number},
        {"time_of_call_cad", type datetime},
        {"time_dispatched_cad", type datetime},
        {"time_out_cad", type datetime},
        {"time_in_cad", type datetime},
        {"time_spent_minutes_cad", type number},
        {"time_response_minutes_cad", type number},
        {"time_spent_formatted_cad", type text},
        {"time_response_formatted_cad", type text},
        {"officer_cad", type text},
        {"disposition_cad", type text},
        {"response_type", type text},
        {"time_response_formatted", type text}
    }),
    
    // === DATA QUALITY ENHANCEMENTS ===
    CleanedData = Table.TransformColumns(TypedData, {
        // Handle null values in key fields
        {"incident_type", each if _ = null or _ = "" then "Unknown" else _},
        {"period", each if _ = null or _ = "" then "Unknown" else _},
        {"location", each if _ = null or _ = "" then "Unknown Location" else _},
        
        // Clean CAD response times (remove negatives)
        {"time_response_minutes_cad", each if _ < 0 then null else _},
        {"time_spent_minutes_cad", each if _ < 0 then null else _}
    }),
    
    // === CALCULATED COLUMNS ===
    EnhancedData = Table.AddColumn(CleanedData, "has_cad_data", each if [case_number_cad] <> null and [case_number_cad] <> "" then "Yes" else "No", type text),
    FinalData = Table.AddColumn(EnhancedData, "incident_datetime", each [incident_date] & [incident_time], type datetime)

in
    FinalData
	
CallType_Categories M Code:

let
    // === CONFIGURATION ===
    FilePath = "C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Classifications\CallTypes\CallType_Categories.xlsx",
    
    // === DATA LOADING ===
    Source = Excel.Workbook(File.Contents(FilePath), null, true),
    Sheet = Source{[Item="Sheet1",Kind="Sheet"]}[Data],
    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),
    
    // === DATA TYPE CONVERSIONS ===
    TypedData = Table.TransformColumnTypes(Headers, {
        {"CallType", type text},
        {"Category", type text},
        {"ResponseType", type text},
        {"Priority", type text}
    }),
    
    // === DATA CLEANING ===
    CleanedData = Table.TransformColumns(TypedData, {
        {"CallType", Text.Trim},
        {"Category", Text.Trim},
        {"ResponseType", Text.Trim}
    })

in
    CleanedData
	
Diagnostic_Query M Code:
Source	Columns
CSV Columns	case_number, incident_date, incident_time, time_of_day, time_of_day_sort_order, period, season, day_of_week, day_type, location, block, grid, post, incident_type, all_incidents, vehicle_1, vehicle_2, vehicle_1_and_vehicle_2, narrative, total_value_stolen, total_value_recovered, squad, officer_of_record, nibrs_classification, case_number_cad, response_type_cad, category_type_cad, how_reported_cad, location_cad, block_cad, grid_cad, post_cad, time_of_call_cad, time_dispatched_cad, time_out_cad, time_in_cad, time_spent_minutes_cad, time_response_minutes_cad, time_spent_formatted_cad, time_response_formatted_cad, officer_cad, disposition_cad
Excel Columns	Incident, Category Type, Response Type

GeoJSON Queries:
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
            "OBJECTID","callid","callcat","calltype","priority","description","callsource","callerinfo",
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

    // ─── 10) Final columns & ordering ──────────────────────────────────────────
    Final = Table.SelectColumns(
        AddResponseMin,
        {
            "OBJECTID",
            "callid",
            "Clean_CallType",
            "Call_Source",
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
	
// 🕒 2025-07-29-18-00-00
// SCRPA_Time_v2/Burglary_Commercial_Residential
// Author: R. A. Carucci
// Purpose: Process burglary commercial/residential JSON data with address-based mapping for ArcGIS
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
            "OBJECTID","callid","callcat","calltype","priority","description","callsource","callerinfo",
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

    // ─── 10) Select and order final columns ────────────────────────────────────
    Final = Table.SelectColumns(
        AddResponseMin,
        {
            "OBJECTID",
            "callid",
            "Clean_CallType",
            "Call_Source",
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
	
let
    // ─── 1) Load GeoJSON ───────────────────────────────────────────────────────
    Source = Json.Document(
        File.Contents(
            "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\08_json\\arcgis_pro_layers\\City_Boundaries.geojson"
        )
    ),

    // ─── 2) Promote to table and expand features ───────────────────────────────
    RootTable    = Table.FromRecords({ Source }),
    Features     = Table.ExpandListColumn(RootTable, "features"),
    ExpandedFeat = Table.ExpandRecordColumn(Features, "features", {"properties"}, {"Properties"}),

    // ─── 3) Expand only the property fields you need ───────────────────────────
    ExpandedProps = Table.ExpandRecordColumn(
        ExpandedFeat,
        "Properties",
        {
            "OBJECTID",
            "MUN",
            "COUNTY",
            "MUN_LABEL",
            "Shape__Area",
            "Shape__Length"
        },
        {
            "OBJECTID",
            "MUN",
            "COUNTY",
            "MUN_LABEL",
            "Shape__Area",
            "Shape__Length"
        }
    ),

    // ─── 4) Select and order final columns ─────────────────────────────────────
    Final = Table.SelectColumns(
        ExpandedProps,
        {
            "OBJECTID",
            "MUN",
            "COUNTY",
            "MUN_LABEL",
            "Shape__Area",
            "Shape__Length"
        }
    )
in
    Final
	
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
            "OBJECTID","Call_ID","Call_Category","Call_Type","Priority","Description",
            "Call_Source","Caller_Info","Full_Address","City","State","Zip",
            "Location_Description","Beat","District","Division","Call_Date_Unix",
            "Call_Year","Call_Month","Call_Day_Of_Week","Call_Day_Number","Call_Hour",
            "Dispatch_Date_Unix","Enroute_Date_Unix","Arrival_Date_Unix","Clear_Date_Unix",
            "Dispatch_Time_Minutes","Queue_Time_Minutes","Travel_Time_Minutes",
            "Clear_Time_Minutes","Response_Time_Minutes","Agency","First_Unit",
            "Unit_Total","Disposition","Comments","Analyst_Notes","Problem_Name",
            "Problem_Type","X_Fallback","Y_Fallback"
        }
    ),

    // 5) Convert UNIX‐epoch fields into datetimes
    AddedCallDate = Table.AddColumn(
        ExpandedProps,
        "Call_Date",
        each if [Call_Date_Unix] <> null then
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Call_Date_Unix]/1000)
        else null,
        type datetime
    ),
    AddedDispatchDate = Table.AddColumn(
        AddedCallDate,
        "Dispatch_Date",
        each if [Dispatch_Date_Unix] <> null then
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Dispatch_Date_Unix]/1000)
        else null,
        type datetime
    ),
    AddedEnrouteDate = Table.AddColumn(
        AddedDispatchDate,
        "Enroute_Date",
        each if [Enroute_Date_Unix] <> null then
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Enroute_Date_Unix]/1000)
        else null,
        type datetime
    ),
    AddedClearDate = Table.AddColumn(
        AddedEnrouteDate,
        "Clear_Date",
        each if [Clear_Date_Unix] <> null then
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Clear_Date_Unix]/1000)
        else null,
        type datetime
    ),

    // 6) Filter to incidents on or after December 31, 2024
    FilteredIncidents = Table.SelectRows(
        AddedClearDate,
        each [Call_Date] >= #datetime(2024, 12, 31, 0, 0, 0)
    ),

    // 7) Convert Web Mercator to Decimal Degrees
    AddedLongitude_DD = Table.AddColumn(
        FilteredIncidents,
        "Longitude_DD",
        each [WebMercator_X] / 20037508.34 * 180,
        type number
    ),
    AddedLatitude_DD = Table.AddColumn(
        AddedLongitude_DD,
        "Latitude_DD",
        each let y = [WebMercator_Y] / 20037508.34 * Number.PI
             in 180/Number.PI * (2 * Number.Atan(Number.Exp(y)) - Number.PI/2),
        type number
    ),

    // 8) Clean up Call_Type field
    AddedCleanCallType = Table.AddColumn(
        AddedLatitude_DD,
        "Clean_Call_Type",
        each if [Call_Type] <> null and Text.Contains([Call_Type], " - 2C")
             then Text.BeforeDelimiter([Call_Type], " - 2C")
             else if [Call_Type] <> null
                  then [Call_Type]
                  else "Unknown",
        type text
    ),

    // 9) Select and order final columns
    SelectedFinalColumns = Table.SelectColumns(
        AddedCleanCallType,
        {
            "OBJECTID",
            "Call_ID",
            "Clean_Call_Type",
            "Call_Source",
            "Full_Address",
            "Beat",
            "District",
            "Call_Date",
            "Dispatch_Date",
            "Enroute_Date",
            "Clear_Date",
            "Response_Time_Minutes",
            "Longitude_DD",
            "Latitude_DD"
        }
    ),

    // 10) Ensure correct data types
    ChangedFinalTypes = Table.TransformColumnTypes(
        SelectedFinalColumns,
        {
            {"OBJECTID", Int64.Type},
            {"Call_ID", type text},
            {"Clean_Call_Type", type text},
            {"Call_Source", type text},
            {"Full_Address", type text},
            {"Beat", type text},
            {"District", type text},
            {"Call_Date", type datetime},
            {"Dispatch_Date", type datetime},
            {"Enroute_Date", type datetime},
            {"Clear_Date", type datetime},
            {"Response_Time_Minutes", type number},
            {"Longitude_DD", type number},
            {"Latitude_DD", type number}
        }
    )
in
    ChangedFinalTypes
	
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
            "OBJECTID","Call_ID","Call_Category","Call_Type","Priority","Description",
            "Call_Source","Caller_Info","Full_Address","City","State","Zip",
            "Location_Description","Beat","District","Division","Call_Date_Unix",
            "Call_Year","Call_Month","Call_Day_Of_Week","Call_Day_Number","Call_Hour",
            "Dispatch_Date_Unix","Enroute_Date_Unix","Arrival_Date_Unix","Clear_Date_Unix",
            "Dispatch_Time_Minutes","Queue_Time_Minutes","Travel_Time_Minutes",
            "Clear_Time_Minutes","Response_Time_Minutes","Agency","First_Unit",
            "Unit_Total","Disposition","Comments","Analyst_Notes","Problem_Name",
            "Problem_Type","X_Fallback","Y_Fallback"
        }
    ),

    // 5) Convert UNIX‐epoch fields into datetimes
    AddedCallDate = Table.AddColumn(
        ExpandedProps,
        "Call_Date",
        each if [Call_Date_Unix] <> null 
             then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Call_Date_Unix]/1000)
             else null,
        type datetime
    ),
    AddedDispatchDate = Table.AddColumn(
        AddedCallDate,
        "Dispatch_Date",
        each if [Dispatch_Date_Unix] <> null 
             then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Dispatch_Date_Unix]/1000)
             else null,
        type datetime
    ),
    AddedEnrouteDate = Table.AddColumn(
        AddedDispatchDate,
        "Enroute_Date",
        each if [Enroute_Date_Unix] <> null 
             then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Enroute_Date_Unix]/1000)
             else null,
        type datetime
    ),
    AddedArrivalDate = Table.AddColumn(
        AddedEnrouteDate,
        "Arrival_Date",
        each if [Arrival_Date_Unix] <> null 
             then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Arrival_Date_Unix]/1000)
             else null,
        type datetime
    ),
    AddedClearDate = Table.AddColumn(
        AddedArrivalDate,
        "Clear_Date",
        each if [Clear_Date_Unix] <> null 
             then #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Clear_Date_Unix]/1000)
             else null,
        type datetime
    ),

    // 6) Filter to incidents on or after 12/31/2024
    FilteredIncidents = Table.SelectRows(
        AddedClearDate,
        each [Call_Date] >= #datetime(2024, 12, 31, 0, 0, 0)
    ),

    // 7) Convert Web Mercator to Decimal Degrees
    AddedLongitude = Table.AddColumn(
        FilteredIncidents,
        "Longitude_DD",
        each [WebMercator_X] / 20037508.34 * 180,
        type number
    ),
    AddedLatitude = Table.AddColumn(
        AddedLongitude,
        "Latitude_DD",
        each let y = [WebMercator_Y] / 20037508.34 * Number.PI
             in 180/Number.PI * (2 * Number.Atan(Number.Exp(y)) - Number.PI/2),
        type number
    ),

    // 8) Clean up Call_Type field
    AddedCleanCallType = Table.AddColumn(
        AddedLatitude,
        "Clean_Call_Type",
        each if [Call_Type] <> null and Text.Contains([Call_Type], " - 2C")
             then Text.BeforeDelimiter([Call_Type], " - 2C")
             else if [Call_Type] <> null then [Call_Type] else "Unknown",
        type text
    ),

    // 9) Select and order final columns
    SelectedFinalColumns = Table.SelectColumns(
        AddedCleanCallType,
        {
            "OBJECTID",
            "Call_ID",
            "Clean_Call_Type",
            "Call_Source",
            "Full_Address",
            "Beat",
            "District",
            "Call_Date",
            "Dispatch_Date",
            "Enroute_Date",
            "Clear_Date",
            "Response_Time_Minutes",
            "Longitude_DD",
            "Latitude_DD"
        }
    ),

    // 10) Ensure correct data types
    ChangedFinalTypes = Table.TransformColumnTypes(
        SelectedFinalColumns,
        {
            {"OBJECTID", Int64.Type},
            {"Call_ID", type text},
            {"Clean_Call_Type", type text},
            {"Call_Source", type text},
            {"Full_Address", type text},
            {"Beat", type text},
            {"District", type text},
            {"Call_Date", type datetime},
            {"Dispatch_Date", type datetime},
            {"Enroute_Date", type datetime},
            {"Clear_Date", type datetime},
            {"Response_Time_Minutes", type number},
            {"Longitude_DD", type number},
            {"Latitude_DD", type number}
        }
    )
in
    ChangedFinalTypes
	
// 🕒 2025-07-29
// SCRPA_Time_v2/MASTER_TEMPLATE_JSON_Crime_Data_Processing
// Author: R. A. Carucci
// Purpose: Definitive template to clean and standardize JSON crime data.
// FIX V3: Correctly parses the 'coordinates' array and date/time values.
// Added filter to include only incidents on or after December 31, 2024.

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
          "OBJECTID","callid","callcat","calltype","priority","description","callsource","callerinfo",
          "fulladdr","city","state","zip","locdesc","beat","district","division","calldate",
          "callyear","callmonth","calldow","calldownum","callhour","dispatchdate","enroutedate",
          "arrivaldate","cleardate","dispatchtime","queuetime","traveltime","cleartime",
          "responsetime","agency","firstunit","unittotal","disposition","comments","analystnotes",
          "probname","probtype","x_fallback","y_fallback"
        },
        {
          "OBJECTID","Call_ID","Call_Category","Call_Type","Priority","Description","Call_Source","Caller_Info",
          "Full_Address","City","State","Zip","Location_Description","Beat","District","Division","Call_Date_Unix",
          "Call_Year","Call_Month","Call_Day_Of_Week","Call_Day_Number","Call_Hour","Dispatch_Date_Unix",
          "Enroute_Date_Unix","Arrival_Date_Unix","Clear_Date_Unix","Dispatch_Time_Minutes",
          "Queue_Time_Minutes","Travel_Time_Minutes","Clear_Time_Minutes","Response_Time_Minutes",
          "Agency","First_Unit","Unit_Total","Disposition","Comments","Analyst_Notes",
          "Problem_Name","Problem_Type","x_fallback","y_fallback"
        }
    ),

    // 5) Convert Unix timestamps to datetimezone
    #"Added Call_Date"         = Table.AddColumn(
                                    #"Expanded features.properties",
                                    "Call_Date",
                                    each if [Call_Date_Unix] <> null
                                         then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[Call_Date_Unix]/1000)
                                         else null,
                                    type datetimezone
                                ),
    #"Added Dispatch_Date"     = Table.AddColumn(
                                    #"Added Call_Date",
                                    "Dispatch_Date",
                                    each if [Dispatch_Date_Unix] <> null
                                         then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[Dispatch_Date_Unix]/1000)
                                         else null,
                                    type datetimezone
                                ),
    #"Added Enroute_Date"      = Table.AddColumn(
                                    #"Added Dispatch_Date",
                                    "Enroute_Date",
                                    each if [Enroute_Date_Unix] <> null
                                         then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[Enroute_Date_Unix]/1000)
                                         else null,
                                    type datetimezone
                                ),
    #"Added Clear_Date"        = Table.AddColumn(
                                    #"Added Enroute_Date",
                                    "Clear_Date",
                                    each if [Clear_Date_Unix] <> null
                                         then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[Clear_Date_Unix]/1000)
                                         else null,
                                    type datetimezone
                                ),

    // 6) Filter to incidents on or after December 31, 2024
    #"Filtered Recent Incidents" = Table.SelectRows(
                                    #"Added Clear_Date",
                                    each [Call_Date] >= #datetimezone(2024,12,31,0,0,0,0,0)
                                ),

    // 7) Convert WebMercator to Decimal Degrees, with fallbacks
    #"Added Longitude_DD"      = Table.AddColumn(
                                    #"Filtered Recent Incidents",
                                    "Longitude_DD",
                                    each if [Longitude_Web_Mercator] <> null
                                         then [Longitude_Web_Mercator] / 20037508.34 * 180
                                         else [x_fallback],
                                    type number
                                ),
    #"Added Latitude_DD"       = Table.AddColumn(
                                    #"Added Longitude_DD",
                                    "Latitude_DD",
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
                                    "Time_Of_Day_Category",
                                    each let h = [Call_Hour] in
                                        if h = null then "Unknown"
                                        else if h < 6 then "00:00-05:59 Overnight"
                                        else if h < 12 then "06:00-11:59 Morning"
                                        else if h < 18 then "12:00-17:59 Afternoon"
                                        else "18:00-23:59 Evening",
                                    type text
                                ),
    #"Added Response_Time_Category" = Table.AddColumn(
                                    #"Added Time_Of_Day_Category",
                                    "Response_Time_Category",
                                    each let r = [Response_Time_Minutes] in
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
                                    "Clean_Call_Type",
                                    each if [Call_Type] <> null and Text.Contains([Call_Type]," - 2C")
                                         then Text.BeforeDelimiter([Call_Type]," - 2C")
                                         else if [Call_Type] <> null then [Call_Type] else "Unknown",
                                    type text
                                ),

    // 10) Final selection and type enforcement
    #"Selected Final Columns"  = Table.SelectColumns(
                                    #"Added Clean_Call_Type",
                                    {
                                      "OBJECTID","Call_ID","Clean_Call_Type","Call_Source","Full_Address","Beat",
                                      "District","Call_Date","Call_Year","Call_Month","Call_Day_Of_Week","Call_Hour",
                                      "Time_Of_Day_Category","Dispatch_Date","Enroute_Date","Clear_Date",
                                      "Response_Time_Minutes","Response_Time_Category","Dispatch_Time_Minutes",
                                      "Clear_Time_Minutes","First_Unit","Disposition","Longitude_DD","Latitude_DD"
                                    }
                                ),
    #"Changed Final Types"     = Table.TransformColumnTypes(
                                    #"Selected Final Columns",
                                    {
                                      {"OBJECTID", Int64.Type},{"Call_ID", type text},{"Clean_Call_Type", type text},
                                      {"Call_Source", type text},{"Full_Address", type text},{"Beat", type text},
                                      {"District", type text},{"Call_Date", type datetimezone},{"Call_Year", Int64.Type},
                                      {"Call_Month", Int64.Type},{"Call_Day_Of_Week", type text},{"Call_Hour", Int64.Type},
                                      {"Time_Of_Day_Category", type text},{"Dispatch_Date", type datetimezone},
                                      {"Enroute_Date", type datetimezone},{"Clear_Date", type datetimezone},
                                      {"Response_Time_Minutes", type number},{"Response_Time_Category", type text},
                                      {"Dispatch_Time_Minutes", type number},{"Clear_Time_Minutes", type number},
                                      {"First_Unit", type text},{"Disposition", type text},
                                      {"Longitude_DD", type number},{"Latitude_DD", type number}
                                    }
                                )
in
    #"Changed Final Types"
