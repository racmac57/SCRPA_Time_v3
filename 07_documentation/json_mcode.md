"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\Burglary_Auto_7d.geojson"
let
    // ─── 1) Load & expand JSON with error handling ──────────────────────────
    Source = try Json.Document(
        File.Contents(
            "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\burg_auto_7d.json"
        )
    ) otherwise null,
    
    // Check if JSON loaded successfully and has features
    HasFeatures = Source <> null and Record.HasFields(Source, "features") and List.Count(Source[features]) > 0,
    
    ProcessedData = if HasFeatures then
        let
            // Convert source to table and expand
            #"Converted to Table" = Table.FromRecords({ Source }),
            
            // Expand CRS (optional, can skip if not needed)
            #"Expanded crs" = if Record.HasFields(Source, "crs") then
                Table.ExpandRecordColumn(
                    #"Converted to Table", "crs", {"type","properties"}, {"crs.type","crs.properties"}
                )
            else #"Converted to Table",
            
            // Expand features list
            #"Expanded features" = Table.ExpandListColumn(#"Expanded crs", "features"),
            
            // Expand each feature record
            #"Expanded features1" = Table.ExpandRecordColumn(
                #"Expanded features",
                "features",
                {"type","id","geometry","properties"},
                {"features.type","features.id","features.geometry","features.properties"}
            ),
            
            // Expand geometry (coordinates for mapping)
            #"Expanded features.geometry" = Table.ExpandRecordColumn(
                #"Expanded features1",
                "features.geometry",
                {"type","coordinates"},
                {"features.geometry.type","features.geometry.coordinates"}
            ),
            
            // Extract X,Y coordinates from coordinates array
            #"Added Custom" = Table.AddColumn(
                #"Expanded features.geometry", 
                "Longitude Web Mercator", 
                each if [features.geometry.coordinates] <> null and List.Count([features.geometry.coordinates]) >= 2 
                     then [features.geometry.coordinates]{0} 
                     else null,
                type number
            ),
            #"Added Custom1" = Table.AddColumn(
                #"Added Custom", 
                "Latitude Web Mercator", 
                each if [features.geometry.coordinates] <> null and List.Count([features.geometry.coordinates]) >= 2 
                     then [features.geometry.coordinates]{1} 
                     else null,
                type number
            ),
            
            // Remove the original coordinates column
            #"Removed Columns" = Table.RemoveColumns(#"Added Custom1",{"features.geometry.coordinates"}),
            
            // Expand properties with all available fields
            #"Expanded features.properties" = Table.ExpandRecordColumn(
                #"Removed Columns",
                "features.properties",
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
                  "OBJECTID","Call ID","Call Category","Call Type","Priority","Description",
                  "Call Source","Caller Info","Full Address","City","State","Zip",
                  "Location Description","Beat","District","Division","Call Date Unix",
                  "Call Year","Call Month","Call Day Of Week","Call Day Number","Call Hour",
                  "Dispatch Date Unix","Enroute Date Unix","Arrival Date Unix","Clear Date Unix",
                  "Dispatch Time Minutes","Queue Time Minutes","Travel Time Minutes",
                  "Clear Time Minutes","Response Time Minutes","Agency","First Unit",
                  "Unit Total","Disposition","Comments","Analyst Notes","Problem Name",
                  "Problem Type","Longitude","Latitude"
                }
            ),

            // ─── 2) Standard transforms ──────────────────────────────────────────────
            #"Added Call Date" = Table.AddColumn(
                #"Expanded features.properties","Call Date",
                each if [#"Call Date Unix"] <> null then 
                    #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[#"Call Date Unix"]/1000)
                else null,
                type datetime
            ),
            #"Added Dispatch Date" = Table.AddColumn(
                #"Added Call Date","Dispatch Date",
                each if [#"Dispatch Date Unix"] <> null then
                    #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[#"Dispatch Date Unix"]/1000)
                else null,
                type datetime
            ),
            #"Added Enroute Date" = Table.AddColumn(
                #"Added Dispatch Date","Enroute Date",
                each if [#"Enroute Date Unix"] <> null then
                    #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[#"Enroute Date Unix"]/1000)
                else null,
                type datetime
            ),
            #"Added Clear Date" = Table.AddColumn(
                #"Added Enroute Date","Clear Date",
                each if [#"Clear Date Unix"] <> null then
                    #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[#"Clear Date Unix"]/1000)
                else null,
                type datetime
            ),
            
            // Convert Web Mercator to Decimal Degrees for mapping
            #"Added Longitude DD" = Table.AddColumn(
                #"Added Clear Date","Longitude DD",
                each if [#"Longitude Web Mercator"] <> null then
                    [#"Longitude Web Mercator"]/20037508.34*180
                else null,
                type number
            ),
            #"Added Latitude DD" = Table.AddColumn(
                #"Added Longitude DD","Latitude DD",
                each if [#"Latitude Web Mercator"] <> null then
                    let
                        pi = 3.14159265359,
                        y = [#"Latitude Web Mercator"]/20037508.34*pi
                    in 180/pi*(2*Number.Atan(Number.Exp(y)) - pi/2)
                else null,
                type number
            ),
            
            // Add time categorization
            #"Added Time Of Day Category" = Table.AddColumn(
                #"Added Latitude DD","Time Of Day Category",
                each let h=[#"Call Hour"] in
                    if h<6 then "00:00-05:59 Overnight"
                    else if h<12 then "06:00-11:59 Morning"
                    else if h<18 then "12:00-17:59 Afternoon"
                    else "18:00-23:59 Evening",
                type text
            ),
            #"Added Response Time Category" = Table.AddColumn(
                #"Added Time Of Day Category","Response Time Category",
                each if [#"Response Time Minutes"] <> null then
                    let r=[#"Response Time Minutes"] in
                        if r<=5 then "0-5 Minutes (Excellent)"
                        else if r<=10 then "5-10 Minutes (Good)"
                        else if r<=15 then "10-15 Minutes (Average)"
                        else "15+ Minutes (Needs Attention)"
                else "Unknown",
                type text
            ),
            #"Added Clean Call Type" = Table.AddColumn(
                #"Added Response Time Category","Clean Call Type",
                each if [#"Call Type"] <> null then
                    if Text.Contains([#"Call Type"]," - 2C")
                         then Text.BeforeDelimiter([#"Call Type"]," - 2C")
                         else [#"Call Type"]
                else null,
                type text
            ),

            // ─── 3) Final columns & types ────────────────────────────────────────────
            #"Selected Final Columns" = Table.SelectColumns(
                #"Added Clean Call Type",
                {
                  "OBJECTID","Call ID","Clean Call Type","Call Source","Full Address",
                  "Beat","District","Call Date","Call Year","Call Month",
                  "Call Day Of Week","Call Hour","Time Of Day Category",
                  "Dispatch Date","Enroute Date","Clear Date",
                  "Response Time Minutes","Response Time Category",
                  "Dispatch Time Minutes","Clear Time Minutes",
                  "First Unit","Disposition","Longitude DD","Latitude DD"
                }
            ),
            #"Changed Final Types" = Table.TransformColumnTypes(
                #"Selected Final Columns",
                {
                  {"OBJECTID", Int64.Type}, {"Call ID", type text}, {"Clean Call Type", type text},
                  {"Call Source", type text}, {"Full Address", type text}, {"Beat", type text},
                  {"District", type text}, {"Call Date", type datetime}, {"Call Year", Int64.Type},
                  {"Call Month", Int64.Type}, {"Call Day Of Week", type text}, {"Call Hour", Int64.Type},
                  {"Time Of Day Category", type text}, {"Dispatch Date", type datetime},
                  {"Enroute Date", type datetime}, {"Clear Date", type datetime},
                  {"Response Time Minutes", type number}, {"Response Time Category", type text},
                  {"Dispatch Time Minutes", type number}, {"Clear Time Minutes", type number},
                  {"First Unit", type text}, {"Disposition", type text},
                  {"Longitude DD", type number}, {"Latitude DD", type number}
                }
            )
        in
            #"Changed Final Types"
    else
        // Return empty table with proper schema if no data
        Table.FromRecords({}, type table [
            OBJECTID = Int64.Type,
            #"Call ID" = type text,
            #"Clean Call Type" = type text,
            #"Call Source" = type text,
            #"Full Address" = type text,
            Beat = type text,
            District = type text,
            #"Call Date" = type datetime,
            #"Call Year" = Int64.Type,
            #"Call Month" = Int64.Type,
            #"Call Day Of Week" = type text,
            #"Call Hour" = Int64.Type,
            #"Time Of Day Category" = type text,
            #"Dispatch Date" = type datetime,
            #"Enroute Date" = type datetime,
            #"Clear Date" = type datetime,
            #"Response Time Minutes" = type number,
            #"Response Time Category" = type text,
            #"Dispatch Time Minutes" = type number,
            #"Clear Time Minutes" = type number,
            #"First Unit" = type text,
            Disposition = type text,
            #"Longitude DD" = type number,
            #"Latitude DD" = type number;

        ]),

    // ─── 4) Cycle filtering - ONLY 7-Day Period ───────────────────────────────
    TodayDate = DateTime.Date(DateTime.LocalNow()),
    
    // Define fallback cycle dates (last 7 days)
    CycleResult = 
        let
            StartDate = Date.AddDays(TodayDate, -7),
            EndDate = TodayDate
        in
            [Start = StartDate, End = EndDate, Type = "Fallback"],
    
    // Apply 7-day filtering
    FinalResult = if HasFeatures then
        let
            Filtered7Day = Table.SelectRows(
                ProcessedData, 
                each let cd = Date.From([#"Call Date"]) in
                    cd >= CycleResult[Start] and cd <= CycleResult[End]
            ),
            AddedPeriod = Table.AddColumn(
                Filtered7Day,
                "Period",
                each "7-Day (" & CycleResult[Type] & ")",
                type text
            )
        in
            AddedPeriod
    else 
        ProcessedData

in
    FinalResult
	
"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\Burglary_Comm_Res_7d.geojson"
// 🕒 2025-07-29-18-00-00
// SCRPA_Time_v2/Burglary_Commercial_Residential
// Author: R. A. Carucci
// Purpose: Process burglary commercial/residential JSON data with address-based mapping for ArcGIS

let
    Source = Json.Document(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\burg_com_res_7d.json")),
    #"Converted to Table" = Table.FromRecords({Source}),
    #"Expanded crs" = Table.ExpandRecordColumn(#"Converted to Table", "crs", {"type", "properties"}, {"crs.type", "crs.properties"}),
    #"Expanded crs.properties" = Table.ExpandRecordColumn(#"Expanded crs", "crs.properties", {"name"}, {"crs.properties.name"}),
    #"Expanded features" = Table.ExpandListColumn(#"Expanded crs.properties", "features"),
    #"Expanded features1" = Table.ExpandRecordColumn(#"Expanded features", "features", {"type", "id", "geometry", "properties"}, {"features.type", "features.id", "features.geometry", "features.properties"}),
    #"Expanded features.geometry" = Table.ExpandRecordColumn(#"Expanded features1", "features.geometry", {"type", "coordinates"}, {"features.geometry.type", "features.geometry.coordinates"}),
    #"Split Column" = Table.SplitColumn(#"Expanded features.geometry", "features.geometry.coordinates", each _, {"Longitude_Web_Mercator", "Latitude_Web_Mercator"}),
    #"Expanded features.properties" = Table.ExpandRecordColumn(#"Split Column", "features.properties", 
        {"OBJECTID", "callid", "callcat", "calltype", "priority", "description", "callsource", "callerinfo", "fulladdr", "city", "state", "zip", "locdesc", "beat", "district", "division", "calldate", "callyear", "callmonth", "calldow", "calldownum", "callhour", "dispatchdate", "enroutedate", "arrivaldate", "cleardate", "dispatchtime", "queuetime", "traveltime", "cleartime", "responsetime", "agency", "firstunit", "unittotal", "disposition", "comments", "analystnotes", "probname", "probtype", "x", "y"}, 
        {"OBJECTID", "Call_ID", "Call_Category", "Call_Type", "Priority", "Description", "Call_Source", "Caller_Info", "Full_Address", "City", "State", "Zip", "Location_Description", "Beat", "District", "Division", "Call_Date_Unix", "Call_Year", "Call_Month", "Call_Day_Of_Week", "Call_Day_Number", "Call_Hour", "Dispatch_Date_Unix", "Enroute_Date_Unix", "Arrival_Date_Unix", "Clear_Date_Unix", "Dispatch_Time_Minutes", "Queue_Time_Minutes", "Travel_Time_Minutes", "Clear_Time_Minutes", "Response_Time_Minutes", "Agency", "First_Unit", "Unit_Total", "Disposition", "Comments", "Analyst_Notes", "Problem_Name", "Problem_Type", "Longitude", "Latitude"}),
    
    // ✅ CONVERT UNIX TIMESTAMPS TO READABLE DATES  
    #"Added Call_Date" = Table.AddColumn(#"Expanded features.properties", "Call_Date", each 
        if [Call_Date_Unix] <> null then 
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Call_Date_Unix]/1000)
        else null, type datetime),
    
    #"Added Dispatch_Date" = Table.AddColumn(#"Added Call_Date", "Dispatch_Date", each 
        if [Dispatch_Date_Unix] <> null then 
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Dispatch_Date_Unix]/1000)
        else null, type datetime),
    
    #"Added Clear_Date" = Table.AddColumn(#"Added Dispatch_Date", "Clear_Date", each 
        if [Clear_Date_Unix] <> null then 
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Clear_Date_Unix]/1000)
        else null, type datetime),
    
    // ✅ CLEAN AND CATEGORIZE CALL TYPES
    #"Added Clean_Call_Type" = Table.AddColumn(#"Added Clear_Date", "Clean_Call_Type", each
        if [Call_Type] <> null then 
            if Text.Contains([Call_Type], " - 2C") then
                Text.BeforeDelimiter([Call_Type], " - 2C")
            else [Call_Type]
        else "Unknown", type text),
    
    #"Added Burglary_Category" = Table.AddColumn(#"Added Clean_Call_Type", "Burglary_Category", each
        let callType = Text.Upper([Clean_Call_Type] ?? "") in
        if Text.Contains(callType, "COMMERCIAL") then "Commercial"
        else if Text.Contains(callType, "RESIDENCE") then "Residential"
        else if Text.Contains(callType, "AUTO") then "Auto"
        else "Other", type text),
    
    // ✅ ADD TIME AND RESPONSE ANALYSIS
    #"Added Time_Of_Day_Category" = Table.AddColumn(#"Added Burglary_Category", "Time_Of_Day_Category", each
        let hour = [Call_Hour] in
        if hour = null then "Unknown"
        else if hour >= 0 and hour < 6 then "00:00-05:59 Overnight"
        else if hour >= 6 and hour < 12 then "06:00-11:59 Morning"
        else if hour >= 12 and hour < 18 then "12:00-17:59 Afternoon"
        else "18:00-23:59 Evening", type text),
    
    #"Added Response_Time_Category" = Table.AddColumn(#"Added Time_Of_Day_Category", "Response_Time_Category", each
        let response = [Response_Time_Minutes] in
        if response = null then "Unknown"
        else if response <= 5 then "0-5 Minutes (Excellent)"
        else if response <= 10 then "5-10 Minutes (Good)"
        else if response <= 15 then "10-15 Minutes (Average)"
        else "15+ Minutes (Needs Attention)", type text),
    
    // ✅ CREATE MAPPING ADDRESS (For ArcGIS Location Field)
    #"Added Mapping_Address" = Table.AddColumn(#"Added Response_Time_Category", "Mapping_Address", each
        let 
            addr = Text.Trim([Full_Address] ?? ""),
            // Ensure address has city, state, zip for better geocoding
            hasCity = Text.Contains(Text.Upper(addr), "HACKENSACK"),
            hasState = Text.Contains(Text.Upper(addr), ", NJ"),
            hasZip = Text.Contains(addr, "07601")
        in
            if addr = "" then "Address Unknown"
            else if hasCity and hasState and hasZip then addr
            else if hasCity and hasState then addr & ", 07601"
            else if hasCity then addr & ", NJ, 07601"
            else addr & ", Hackensack, NJ, 07601", type text),
    
    // ✅ ADD LOCATION COORDINATES (Keep for backup/analysis)
    #"Added Location_Coordinates" = Table.AddColumn(#"Added Mapping_Address", "Location_Coordinates", each
        if [Longitude] <> null and [Latitude] <> null then
            Text.From([Latitude]) & "," & Text.From([Longitude])
        else null, type text),
    
    // ✅ FINAL COLUMN SELECTION
    #"Selected Final Columns" = Table.SelectColumns(#"Added Location_Coordinates", {
        "OBJECTID",
        "Call_ID", 
        "Clean_Call_Type",
        "Burglary_Category",
        "Call_Source",
        "Full_Address",
        "Mapping_Address",
        "Location_Coordinates",
        "Beat",
        "District", 
        "Call_Date",
        "Call_Year",
        "Call_Month", 
        "Call_Day_Of_Week",
        "Call_Hour",
        "Time_Of_Day_Category",
        "Dispatch_Date",
        "Clear_Date",
        "Response_Time_Minutes",
        "Response_Time_Category",
        "Dispatch_Time_Minutes",
        "Clear_Time_Minutes",
        "First_Unit",
        "Disposition",
        "Longitude",
        "Latitude"
    }),
    
    // ✅ FINAL DATA TYPE CONVERSIONS
    #"Changed Final Types" = Table.TransformColumnTypes(#"Selected Final Columns", {
        {"OBJECTID", Int64.Type}, 
        {"Call_ID", type text}, 
        {"Clean_Call_Type", type text}, 
        {"Burglary_Category", type text}, 
        {"Call_Source", type text}, 
        {"Full_Address", type text}, 
        {"Mapping_Address", type text}, 
        {"Location_Coordinates", type text}, 
        {"Beat", type text}, 
        {"District", type text}, 
        {"Call_Date", type datetime}, 
        {"Call_Year", Int64.Type}, 
        {"Call_Month", Int64.Type}, 
        {"Call_Day_Of_Week", type text}, 
        {"Call_Hour", Int64.Type}, 
        {"Time_Of_Day_Category", type text}, 
        {"Dispatch_Date", type datetime}, 
        {"Clear_Date", type datetime}, 
        {"Response_Time_Minutes", type number}, 
        {"Response_Time_Category", type text}, 
        {"Dispatch_Time_Minutes", type number}, 
        {"Clear_Time_Minutes", type number}, 
        {"First_Unit", type text}, 
        {"Disposition", type text}, 
        {"Longitude", type number}, 
        {"Latitude", type number}
    })
in
    #"Changed Final Types"
	
"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\City_Boundaries.geojson"
let
    Source = Json.Document(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\city_boundried.json")),
    #"Converted to Table" = Table.FromRecords({Source}),
    #"Expanded crs" = Table.ExpandRecordColumn(#"Converted to Table", "crs", {"type", "properties"}, {"crs.type", "crs.properties"}),
    #"Expanded crs.properties" = Table.ExpandRecordColumn(#"Expanded crs", "crs.properties", {"name"}, {"crs.properties.name"}),
    #"Expanded features" = Table.ExpandListColumn(#"Expanded crs.properties", "features"),
    #"Expanded features1" = Table.ExpandRecordColumn(#"Expanded features", "features", {"type", "id", "geometry", "properties"}, {"features.type", "features.id", "features.geometry", "features.properties"}),
    #"Expanded features.properties" = Table.ExpandRecordColumn(#"Expanded features1", "features.properties", {"OBJECTID", "MUN", "COUNTY", "MUN_LABEL", "MUN_TYPE", "NAME", "GNIS_NAME", "GNIS", "SSN", "MUN_CODE", "CENSUS2020", "ACRES", "SQ_MILES", "POP2020", "POP2010", "POP2000", "POP1990", "POP1980", "POPDEN2020", "POPDEN2010", "POPDEN2000", "POPDEN1990", "POPDEN1980", "Shape__Area", "Shape__Length"}, {"features.properties.OBJECTID", "features.properties.MUN", "features.properties.COUNTY", "features.properties.MUN_LABEL", "features.properties.MUN_TYPE", "features.properties.NAME", "features.properties.GNIS_NAME", "features.properties.GNIS", "features.properties.SSN", "features.properties.MUN_CODE", "features.properties.CENSUS2020", "features.properties.ACRES", "features.properties.SQ_MILES", "features.properties.POP2020", "features.properties.POP2010", "features.properties.POP2000", "features.properties.POP1990", "features.properties.POP1980", "features.properties.POPDEN2020", "features.properties.POPDEN2010", "features.properties.POPDEN2000", "features.properties.POPDEN1990", "features.properties.POPDEN1980", "features.properties.Shape__Area", "features.properties.Shape__Length"}),
    #"Changed Type" = Table.TransformColumnTypes(#"Expanded features.properties",{{"type", type text}, {"crs.type", type text}, {"crs.properties.name", type text}, {"features.type", type text}, {"features.id", Int64.Type}, {"features.geometry", type any}, {"features.properties.OBJECTID", Int64.Type}, {"features.properties.MUN", type text}, {"features.properties.COUNTY", type text}, {"features.properties.MUN_LABEL", type text}, {"features.properties.MUN_TYPE", type text}, {"features.properties.NAME", type text}, {"features.properties.GNIS_NAME", type text}, {"features.properties.GNIS", Int64.Type}, {"features.properties.SSN", Int64.Type}, {"features.properties.MUN_CODE", Int64.Type}, {"features.properties.CENSUS2020", Int64.Type}, {"features.properties.ACRES", type number}, {"features.properties.SQ_MILES", type number}, {"features.properties.POP2020", Int64.Type}, {"features.properties.POP2010", Int64.Type}, {"features.properties.POP2000", Int64.Type}, {"features.properties.POP1990", Int64.Type}, {"features.properties.POP1980", Int64.Type}, {"features.properties.POPDEN2020", Int64.Type}, {"features.properties.POPDEN2010", Int64.Type}, {"features.properties.POPDEN2000", Int64.Type}, {"features.properties.POPDEN1990", Int64.Type}, {"features.properties.POPDEN1980", Int64.Type}, {"features.properties.Shape__Area", type number}, {"features.properties.Shape__Length", type number}})
in
    #"Changed Type"
	
"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\MV_Theft7d.geojson"
// 🕒 2025-07-29
// SCRPA_Time_v2/MASTER_TEMPLATE_JSON_Crime_Data_Processing
// Author: R. A. Carucci
// Purpose: Definitive template to clean and standardize JSON crime data.
// FIX V2: Corrects the #datetimezone function call to resolve date errors.

let
    // ❗ IMPORTANT: Change the file path here for each new query
    Source = Json.Document(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\mv_theft_7d.json")),
    
    #"Converted to Table" = Table.FromRecords({Source}),
    #"Expanded features" = Table.ExpandListColumn(#"Converted to Table", "features"),
    
    // Correctly parse the [lon, lat] coordinates array
    #"Expanded features1" = Table.ExpandRecordColumn(#"Expanded features", "features", {"geometry", "properties"}, {"features.geometry", "features.properties"}),
    #"Expanded features.geometry" = Table.ExpandRecordColumn(#"Expanded features1", "features.geometry", {"coordinates"}, {"features.geometry.coordinates"}),
    #"Split Coordinates" = Table.SplitColumn(#"Expanded features.geometry", "features.geometry.coordinates", each _, {"Longitude_Web_Mercator", "Latitude_Web_Mercator"}),

    #"Expanded features.properties" = Table.ExpandRecordColumn(#"Split Coordinates", "features.properties", 
        {"OBJECTID", "callid", "callcat", "calltype", "priority", "description", "callsource", "callerinfo", "fulladdr", "city", "state", "zip", "locdesc", "beat", "district", "division", "calldate", "callyear", "callmonth", "calldow", "calldownum", "callhour", "dispatchdate", "enroutedate", "arrivaldate", "cleardate", "dispatchtime", "queuetime", "traveltime", "cleartime", "responsetime", "agency", "firstunit", "unittotal", "disposition", "comments", "analystnotes", "probname", "probtype", "x", "y"}, 
        {"OBJECTID", "Call_ID", "Call_Category", "Call_Type", "Priority", "Description", "Call_Source", "Caller_Info", "Full_Address", "City", "State", "Zip", "Location_Description", "Beat", "District", "Division", "Call_Date_Unix", "Call_Year", "Call_Month", "Call_Day_Of_Week", "Call_Day_Number", "Call_Hour", "Dispatch_Date_Unix", "Enroute_Date_Unix", "Arrival_Date_Unix", "Clear_Date_Unix", "Dispatch_Time_Minutes", "Queue_Time_Minutes", "Travel_Time_Minutes", "Clear_Time_Minutes", "Response_Time_Minutes", "Agency", "First_Unit", "Unit_Total", "Disposition", "Comments", "Analyst_Notes", "Problem_Name", "Problem_Type", "x_fallback", "y_fallback"}),
    
    // ✅ CONVERT UNIX TIMESTAMPS TO READABLE DATES (CORRECTED)
    #"Added Call_Date" = Table.AddColumn(#"Expanded features.properties", "Call_Date", each 
        if [Call_Date_Unix] <> null then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[Call_Date_Unix]/1000) else null, type datetimezone),
    
    #"Added Dispatch_Date" = Table.AddColumn(#"Added Call_Date", "Dispatch_Date", each 
        if [Dispatch_Date_Unix] <> null then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[Dispatch_Date_Unix]/1000) else null, type datetimezone),
    
    #"Added Enroute_Date" = Table.AddColumn(#"Added Dispatch_Date", "Enroute_Date", each 
        if [Enroute_Date_Unix] <> null then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[Enroute_Date_Unix]/1000) else null, type datetimezone),
    
    #"Added Clear_Date" = Table.AddColumn(#"Added Enroute_Date", "Clear_Date", each 
        if [Clear_Date_Unix] <> null then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[Clear_Date_Unix]/1000) else null, type datetimezone),
    
    // ✅ CONVERT WEB MERCATOR COORDINATES TO WGS84 (Decimal Degrees)
    #"Added Longitude_DD" = Table.AddColumn(#"Added Clear_Date", "Longitude_DD", each 
        if [Longitude_Web_Mercator] <> null then 
            [Longitude_Web_Mercator] / 20037508.34 * 180
        else [x_fallback], type number),
    
    #"Added Latitude_DD" = Table.AddColumn(#"Added Longitude_DD", "Latitude_DD", each 
        if [Latitude_Web_Mercator] <> null then 
            let 
                pi = 3.14159265359,
                mercatorY = [Latitude_Web_Mercator] / 20037508.34 * pi
            in
                180 / pi * (2 * Number.Atan(Number.Exp(mercatorY)) - pi/2)
        else [y_fallback], type number),
    
    // ✅ ADD ENHANCED FIELDS FOR ANALYSIS
    #"Added Time_Of_Day_Category" = Table.AddColumn(#"Added Latitude_DD", "Time_Of_Day_Category", each
        let hour = [Call_Hour] in
        if hour = null then "Unknown"
        else if hour >= 0 and hour < 6 then "00:00-05:59 Overnight"
        else if hour >= 6 and hour < 12 then "06:00-11:59 Morning"
        else if hour >= 12 and hour < 18 then "12:00-17:59 Afternoon"
        else "18:00-23:59 Evening", type text),
    
    #"Added Response_Time_Category" = Table.AddColumn(#"Added Time_Of_Day_Category", "Response_Time_Category", each
        let response = [Response_Time_Minutes] in
        if response = null then "Unknown"
        else if response <= 5 then "0-5 Min (Excellent)"
        else if response <= 10 then "5-10 Min (Good)"
        else if response <= 15 then "10-15 Min (Average)"
        else "15+ Min (Needs Attention)", type text),
    
    #"Added Clean_Call_Type" = Table.AddColumn(#"Added Response_Time_Category", "Clean_Call_Type", each
        if [Call_Type] <> null then 
            if Text.Contains([Call_Type], " - 2C") then
                Text.BeforeDelimiter([Call_Type], " - 2C")
            else [Call_Type]
        else "Unknown", type text),
    
    // ✅ FINAL COLUMN SELECTION AND STANDARDIZATION
    #"Selected Final Columns" = Table.SelectColumns(#"Added Clean_Call_Type", {
        "OBJECTID", "Call_ID", "Clean_Call_Type", "Call_Source", "Full_Address", "Beat",
        "District", "Call_Date", "Call_Year", "Call_Month", "Call_Day_Of_Week", "Call_Hour",
        "Time_Of_Day_Category", "Dispatch_Date", "Enroute_Date", "Clear_Date",
        "Response_Time_Minutes", "Response_Time_Category", "Dispatch_Time_Minutes",
        "Clear_Time_Minutes", "First_Unit", "Disposition", "Longitude_DD", "Latitude_DD"
    }),
    
    // ✅ FINAL DATA TYPE CONVERSIONS
    #"Changed Final Types" = Table.TransformColumnTypes(#"Selected Final Columns", {
        {"OBJECTID", Int64.Type}, {"Call_ID", type text}, {"Clean_Call_Type", type text},
        {"Call_Source", type text}, {"Full_Address", type text}, {"Beat", type text},
        {"District", type text}, {"Call_Date", type datetimezone}, {"Call_Year", Int64.Type},
        {"Call_Month", Int64.Type}, {"Call_Day_Of_Week", type text}, {"Call_Hour", Int64.Type},
        {"Time_Of_Day_Category", type text}, {"Dispatch_Date", type datetimezone},
        {"Enroute_Date", type datetimezone}, {"Clear_Date", type datetimezone},
        {"Response_Time_Minutes", type number}, {"Response_Time_Category", type text},
        {"Dispatch_Time_Minutes", type number}, {"Clear_Time_Minutes", type number},
        {"First_Unit", type text}, {"Disposition", type text}, {"Longitude_DD", type number},
        {"Latitude_DD", type number}
    })
in
    #"Changed Final Types"
	
"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\Robbery_7d.geojson"
// 🕒 2025-07-29-17-45-00
// SCRPA_Time_v2/Improved_JSON_Crime_Data_Processing
// Author: R. A. Carucci
// Purpose: Clean and standardize JSON crime data for ArcGIS mapping with proper column naming

let
    Source = Json.Document(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\robbery7d.json")),
    #"Converted to Table" = Table.FromRecords({Source}),
    
    // ✅ Expand 'features' list directly to handle JSON structure variations
    #"Expanded features" = Table.ExpandListColumn(#"Converted to Table", "features"),
    
    #"Expanded features1" = Table.ExpandRecordColumn(#"Expanded features", "features", {"geometry", "properties"}, {"features.geometry", "features.properties"}),
    #"Expanded features.geometry" = Table.ExpandRecordColumn(#"Expanded features1", "features.geometry", {"x", "y"}, {"features.geometry.x", "features.geometry.y"}),
    #"Expanded features.properties" = Table.ExpandRecordColumn(#"Expanded features.geometry", "features.properties", 
        {"OBJECTID", "callid", "callcat", "calltype", "priority", "description", "callsource", "callerinfo", "fulladdr", "city", "state", "zip", "locdesc", "beat", "district", "division", "calldate", "callyear", "callmonth", "calldow", "calldownum", "callhour", "dispatchdate", "enroutedate", "arrivaldate", "cleardate", "dispatchtime", "queuetime", "traveltime", "cleartime", "responsetime", "agency", "firstunit", "unittotal", "disposition", "comments", "analystnotes", "probname", "probtype", "x", "y"}, 
        {"OBJECTID", "Call_ID", "Call_Category", "Call_Type", "Priority", "Description", "Call_Source", "Caller_Info", "Full_Address", "City", "State", "Zip", "Location_Description", "Beat", "District", "Division", "Call_Date_Unix", "Call_Year", "Call_Month", "Call_Day_Of_Week", "Call_Day_Number", "Call_Hour", "Dispatch_Date_Unix", "Enroute_Date_Unix", "Arrival_Date_Unix", "Clear_Date_Unix", "Dispatch_Time_Minutes", "Queue_Time_Minutes", "Travel_Time_Minutes", "Clear_Time_Minutes", "Response_Time_Minutes", "Agency", "First_Unit", "Unit_Total", "Disposition", "Comments", "Analyst_Notes", "Problem_Name", "Problem_Type", "Longitude", "Latitude"}),
    
    // ✅ STANDARDIZE COLUMN NAMES TO PascalCase_With_Underscores
    #"Renamed Coordinates" = Table.RenameColumns(#"Expanded features.properties", {
        {"features.geometry.x", "Longitude_Web_Mercator"},
        {"features.geometry.y", "Latitude_Web_Mercator"}
    }),
    
    // ✅ CONVERT UNIX TIMESTAMPS TO READABLE DATES
    #"Added Call_Date" = Table.AddColumn(#"Renamed Coordinates", "Call_Date", each 
        if [Call_Date_Unix] <> null then 
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Call_Date_Unix]/1000)
        else null, type datetime),
    
    #"Added Dispatch_Date" = Table.AddColumn(#"Added Call_Date", "Dispatch_Date", each 
        if [Dispatch_Date_Unix] <> null then 
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Dispatch_Date_Unix]/1000)
        else null, type datetime),
    
    #"Added Enroute_Date" = Table.AddColumn(#"Added Dispatch_Date", "Enroute_Date", each 
        if [Enroute_Date_Unix] <> null then 
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Enroute_Date_Unix]/1000)
        else null, type datetime),
    
    #"Added Clear_Date" = Table.AddColumn(#"Added Enroute_Date", "Clear_Date", each 
        if [Clear_Date_Unix] <> null then 
            #datetime(1970,1,1,0,0,0) + #duration(0,0,0,[Clear_Date_Unix]/1000)
        else null, type datetime),
    
    // ✅ CONVERT WEB MERCATOR COORDINATES TO WGS84 (Decimal Degrees)
    #"Added Longitude_DD" = Table.AddColumn(#"Added Clear_Date", "Longitude_DD", each 
        if [Longitude_Web_Mercator] <> null then 
            [Longitude_Web_Mercator] / 20037508.34 * 180
        else [Longitude], type number),
    
    #"Added Latitude_DD" = Table.AddColumn(#"Added Longitude_DD", "Latitude_DD", each 
        if [Latitude_Web_Mercator] <> null then 
            let 
                pi = 3.14159265359,
                mercatorY = [Latitude_Web_Mercator] / 20037508.34 * pi
            in
                180 / pi * (2 * Number.Atan(Number.Exp(mercatorY)) - pi/2)
        else [Latitude], type number),
    
    // ✅ ADD ENHANCED FIELDS FOR ANALYSIS
    #"Added Time_Of_Day_Category" = Table.AddColumn(#"Added Latitude_DD", "Time_Of_Day_Category", each
        let hour = [Call_Hour] in
        if hour = null then "Unknown"
        else if hour >= 0 and hour < 6 then "00:00-05:59 Overnight"
        else if hour >= 6 and hour < 12 then "06:00-11:59 Morning"
        else if hour >= 12 and hour < 18 then "12:00-17:59 Afternoon"
        else "18:00-23:59 Evening", type text),
    
    #"Added Response_Time_Category" = Table.AddColumn(#"Added Time_Of_Day_Category", "Response_Time_Category", each
        let response = [Response_Time_Minutes] in
        if response = null then "Unknown"
        else if response <= 5 then "0-5 Minutes (Excellent)"
        else if response <= 10 then "5-10 Minutes (Good)"
        else if response <= 15 then "10-15 Minutes (Average)"
        else "15+ Minutes (Needs Attention)", type text),
    
    #"Added Clean_Call_Type" = Table.AddColumn(#"Added Response_Time_Category", "Clean_Call_Type", each
        if [Call_Type] <> null then 
            if Text.Contains([Call_Type], " - 2C") then
                Text.BeforeDelimiter([Call_Type], " - 2C")
            else [Call_Type]
        else "Unknown", type text),
    
    // ✅ FINAL COLUMN SELECTION AND STANDARDIZATION
    #"Selected Final Columns" = Table.SelectColumns(#"Added Clean_Call_Type", {
        "OBJECTID",
        "Call_ID", 
        "Clean_Call_Type",
        "Call_Source",
        "Full_Address",
        "Beat",
        "District", 
        "Call_Date",
        "Call_Year",
        "Call_Month", 
        "Call_Day_Of_Week",
        "Call_Hour",
        "Time_Of_Day_Category",
        "Dispatch_Date",
        "Enroute_Date", 
        "Clear_Date",
        "Response_Time_Minutes",
        "Response_Time_Category",
        "Dispatch_Time_Minutes",
        "Clear_Time_Minutes",
        "First_Unit",
        "Disposition",
        "Longitude_DD",
        "Latitude_DD"
    }),
    
    // ✅ FINAL DATA TYPE CONVERSIONS
    #"Changed Final Types" = Table.TransformColumnTypes(#"Selected Final Columns", {
        {"OBJECTID", Int64.Type}, 
        {"Call_ID", type text}, 
        {"Clean_Call_Type", type text}, 
        {"Call_Source", type text}, 
        {"Full_Address", type text}, 
        {"Beat", type text}, 
        {"District", type text}, 
        {"Call_Date", type datetime}, 
        {"Call_Year", Int64.Type}, 
        {"Call_Month", Int64.Type}, 
        {"Call_Day_Of_Week", type text}, 
        {"Call_Hour", Int64.Type}, 
        {"Time_Of_Day_Category", type text}, 
        {"Dispatch_Date", type datetime}, 
        {"Enroute_Date", type datetime}, 
        {"Clear_Date", type datetime}, 
        {"Response_Time_Minutes", type number}, 
        {"Response_Time_Category", type text}, 
        {"Dispatch_Time_Minutes", type number}, 
        {"Clear_Time_Minutes", type number}, 
        {"First_Unit", type text}, 
        {"Disposition", type text}, 
        {"Longitude_DD", type number}, 
        {"Latitude_DD", type number}
    })
in
    #"Changed Final Types"
	
"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\Sexual_Offenses_7d.geojson"
// 🕒 2025-07-29
// SCRPA_Time_v2/MASTER_TEMPLATE_JSON_Crime_Data_Processing
// Author: R. A. Carucci
// Purpose: Definitive template to clean and standardize JSON crime data.
// FIX V3: Correctly parses the 'coordinates' array and date/time values.

let
    // Using the file path for the provided JSON data
    Source = Json.Document(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\sexoffytd.json")),
    
    #"Converted to Table" = Table.FromRecords({Source}),
    #"Expanded features" = Table.ExpandListColumn(#"Converted to Table", "features"),
    
    // ✅ Correctly parse the [lon, lat] coordinates array
    #"Expanded features1" = Table.ExpandRecordColumn(#"Expanded features", "features", {"geometry", "properties"}, {"features.geometry", "features.properties"}),
    #"Expanded features.geometry" = Table.ExpandRecordColumn(#"Expanded features1", "features.geometry", {"coordinates"}, {"features.geometry.coordinates"}),
    #"Split Coordinates" = Table.SplitColumn(#"Expanded features.geometry", "features.geometry.coordinates", each _, {"Longitude_Web_Mercator", "Latitude_Web_Mercator"}),

    // ✅ Expand all properties from the JSON file
    #"Expanded features.properties" = Table.ExpandRecordColumn(#"Split Coordinates", "features.properties", 
        {"OBJECTID", "callid", "callcat", "calltype", "priority", "description", "callsource", "callerinfo", "fulladdr", "city", "state", "zip", "locdesc", "beat", "district", "division", "calldate", "callyear", "callmonth", "calldow", "calldownum", "callhour", "dispatchdate", "enroutedate", "arrivaldate", "cleardate", "dispatchtime", "queuetime", "traveltime", "cleartime", "responsetime", "agency", "firstunit", "unittotal", "disposition", "comments", "analystnotes", "probname", "probtype", "x", "y"}, 
        {"OBJECTID", "Call_ID", "Call_Category", "Call_Type", "Priority", "Description", "Call_Source", "Caller_Info", "Full_Address", "City", "State", "Zip", "Location_Description", "Beat", "District", "Division", "Call_Date_Unix", "Call_Year", "Call_Month", "Call_Day_Of_Week", "Call_Day_Number", "Call_Hour", "Dispatch_Date_Unix", "Enroute_Date_Unix", "Arrival_Date_Unix", "Clear_Date_Unix", "Dispatch_Time_Minutes", "Queue_Time_Minutes", "Travel_Time_Minutes", "Clear_Time_Minutes", "Response_Time_Minutes", "Agency", "First_Unit", "Unit_Total", "Disposition", "Comments", "Analyst_Notes", "Problem_Name", "Problem_Type", "x_fallback", "y_fallback"}),
    
    // ✅ Convert Unix timestamps to readable dates
    #"Added Call_Date" = Table.AddColumn(#"Expanded features.properties", "Call_Date", each 
        if [Call_Date_Unix] <> null then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[Call_Date_Unix]/1000) else null, type datetimezone),
    
    #"Added Dispatch_Date" = Table.AddColumn(#"Added Call_Date", "Dispatch_Date", each 
        if [Dispatch_Date_Unix] <> null then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[Dispatch_Date_Unix]/1000) else null, type datetimezone),
    
    #"Added Enroute_Date" = Table.AddColumn(#"Added Dispatch_Date", "Enroute_Date", each 
        if [Enroute_Date_Unix] <> null then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[Enroute_Date_Unix]/1000) else null, type datetimezone),
    
    #"Added Clear_Date" = Table.AddColumn(#"Added Enroute_Date", "Clear_Date", each 
        if [Clear_Date_Unix] <> null then #datetimezone(1970,1,1,0,0,0,0,0) + #duration(0,0,0,[Clear_Date_Unix]/1000) else null, type datetimezone),
    
    // ✅ Convert Web Mercator coordinates to WGS84 (Decimal Degrees)
    #"Added Longitude_DD" = Table.AddColumn(#"Added Clear_Date", "Longitude_DD", each 
        if [Longitude_Web_Mercator] <> null then 
            [Longitude_Web_Mercator] / 20037508.34 * 180
        else [x_fallback], type number),
    
    #"Added Latitude_DD" = Table.AddColumn(#"Added Longitude_DD", "Latitude_DD", each 
        if [Latitude_Web_Mercator] <> null then 
            let 
                pi = 3.14159265359,
                mercatorY = [Latitude_Web_Mercator] / 20037508.34 * pi
            in
                180 / pi * (2 * Number.Atan(Number.Exp(mercatorY)) - pi/2)
        else [y_fallback], type number),
    
    // ✅ Add enhanced fields for analysis
    #"Added Time_Of_Day_Category" = Table.AddColumn(#"Added Latitude_DD", "Time_Of_Day_Category", each
        let hour = [Call_Hour] in
        if hour = null then "Unknown"
        else if hour >= 0 and hour < 6 then "00:00-05:59 Overnight"
        else if hour >= 6 and hour < 12 then "06:00-11:59 Morning"
        else if hour >= 12 and hour < 18 then "12:00-17:59 Afternoon"
        else "18:00-23:59 Evening", type text),
    
    #"Added Response_Time_Category" = Table.AddColumn(#"Added Time_Of_Day_Category", "Response_Time_Category", each
        let response = [Response_Time_Minutes] in
        if response = null then "Unknown"
        else if response <= 5 then "0-5 Min (Excellent)"
        else if response <= 10 then "5-10 Min (Good)"
        else if response <= 15 then "10-15 Min (Average)"
        else "15+ Min (Needs Attention)", type text),
    
    #"Added Clean_Call_Type" = Table.AddColumn(#"Added Response_Time_Category", "Clean_Call_Type", each
        if [Call_Type] <> null then 
            if Text.Contains([Call_Type], " - 2C") then
                Text.BeforeDelimiter([Call_Type], " - 2C")
            else [Call_Type]
        else "Unknown", type text),
    
    // ✅ Final column selection and standardization
    #"Selected Final Columns" = Table.SelectColumns(#"Added Clean_Call_Type", {
        "OBJECTID", "Call_ID", "Clean_Call_Type", "Call_Source", "Full_Address", "Beat",
        "District", "Call_Date", "Call_Year", "Call_Month", "Call_Day_Of_Week", "Call_Hour",
        "Time_Of_Day_Category", "Dispatch_Date", "Enroute_Date", "Clear_Date",
        "Response_Time_Minutes", "Response_Time_Category", "Dispatch_Time_Minutes",
        "Clear_Time_Minutes", "First_Unit", "Disposition", "Longitude_DD", "Latitude_DD"
    }),
    
    // ✅ Final data type conversions
    #"Changed Final Types" = Table.TransformColumnTypes(#"Selected Final Columns", {
        {"OBJECTID", Int64.Type}, {"Call_ID", type text}, {"Clean_Call_Type", type text},
        {"Call_Source", type text}, {"Full_Address", type text}, {"Beat", type text},
        {"District", type text}, {"Call_Date", type datetimezone}, {"Call_Year", Int64.Type},
        {"Call_Month", Int64.Type}, {"Call_Day_Of_Week", type text}, {"Call_Hour", Int64.Type},
        {"Time_Of_Day_Category", type text}, {"Dispatch_Date", type datetimezone},
        {"Enroute_Date", type datetimezone}, {"Clear_Date", type datetimezone},
        {"Response_Time_Minutes", type number}, {"Response_Time_Category", type text},
        {"Dispatch_Time_Minutes", type number}, {"Clear_Time_Minutes", type number},
        {"First_Unit", type text}, {"Disposition", type text}, {"Longitude_DD", type number},
        {"Latitude_DD", type number}
    })
in
    #"Changed Final Types"