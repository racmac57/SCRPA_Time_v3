let
    // ─── 1) Load & expand GeoJSON with error handling ──────────────────────────
    Source = try Json.Document(
        File.Contents(
            "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\08_json\arcgis_pro_layers\Robbery_7d.geojson"
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
            
            // Extract X,Y coordinates from coordinates array (already in decimal degrees)
            #"Added Custom" = Table.AddColumn(
                #"Expanded features.geometry", 
                "Longitude DD", 
                each if [features.geometry.coordinates] <> null and List.Count([features.geometry.coordinates]) >= 2 
                     then [features.geometry.coordinates]{0} 
                     else null,
                type number
            ),
            #"Added Custom1" = Table.AddColumn(
                #"Added Custom", 
                "Latitude DD", 
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
            #"Added Incident Date" = Table.AddColumn(
                #"Added Call Date","Incident_Date",
                each Date.From([#"Call Date"]),
                type date
            ),
            #"Added Dispatch Date" = Table.AddColumn(
                #"Added Incident Date","Dispatch Date",
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
            
            // Add Period column with specified logic
            #"Added Period" = Table.AddColumn(
                #"Added Clear Date","Period",
                each
                    let
                        incidentDate = [Incident_Date],
                        today = Date.From(DateTime.LocalNow()),
                        daysDiff = if incidentDate <> null then Duration.Days(today - incidentDate) else 999
                    in
                        if daysDiff <= 7 then "7-Day"
                        else if daysDiff <= 28 then "28-Day" 
                        else if incidentDate <> null and Date.Year(incidentDate) = Date.Year(today) then "YTD"
                        else "Historical",
                type text
            ),
            
            // Add time categorization
            #"Added Time Of Day Category" = Table.AddColumn(
                #"Added Period","Time Of Day Category",
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
                  "Beat","District","Call Date","Incident_Date","Call Year","Call Month",
                  "Call Day Of Week","Call Hour","Time Of Day Category",
                  "Dispatch Date","Enroute Date","Clear Date",
                  "Response Time Minutes","Response Time Category",
                  "Dispatch Time Minutes","Clear Time Minutes",
                  "First Unit","Disposition","Longitude DD","Latitude DD","Period"
                }
            ),
            #"Changed Final Types" = Table.TransformColumnTypes(
                #"Selected Final Columns",
                {
                  {"OBJECTID", Int64.Type}, {"Call ID", type text}, {"Clean Call Type", type text},
                  {"Call Source", type text}, {"Full Address", type text}, {"Beat", type text},
                  {"District", type text}, {"Call Date", type datetime}, {"Incident_Date", type date},
                  {"Call Year", Int64.Type}, {"Call Month", Int64.Type}, {"Call Day Of Week", type text}, 
                  {"Call Hour", Int64.Type}, {"Time Of Day Category", type text}, {"Dispatch Date", type datetime},
                  {"Enroute Date", type datetime}, {"Clear Date", type datetime},
                  {"Response Time Minutes", type number}, {"Response Time Category", type text},
                  {"Dispatch Time Minutes", type number}, {"Clear Time Minutes", type number},
                  {"First Unit", type text}, {"Disposition", type text},
                  {"Longitude DD", type number}, {"Latitude DD", type number}, {"Period", type text}
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
            #"Incident_Date" = type date,
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
            #"Latitude DD" = type number,
            Period = type text

        ]),

    // ─── 4) Return processed data with Period column ───────────────────────────
    FinalResult = ProcessedData

in
    FinalResult