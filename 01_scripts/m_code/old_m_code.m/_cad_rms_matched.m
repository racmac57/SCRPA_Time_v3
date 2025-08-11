let
    RMSSource = _rms_data,
    CADSource = _cad_data,
    
    // Simple join - let Power Query handle duplicates automatically
    JoinedData = Table.NestedJoin(
        RMSSource, {"Case_Number"},
        CADSource, {"Case_Number"},
        "CAD_Match",
        JoinKind.LeftOuter
    ),
    
    // Expand only the CAD columns we want, with prefixes
    ExpandedData = Table.ExpandTableColumn(JoinedData, "CAD_Match", 
        {"Response_Type", "How_Reported", "Time_Of_Call", "Time_Dispatched", "Time_Out", "Time_In", "Time_Spent_Minutes", "Time_Response_Minutes", "Officer", "Disposition", "CAD_Notes_Cleaned"}, 
        {"CAD_Response_Type", "CAD_How_Reported", "CAD_Time_Of_Call", "CAD_Time_Dispatched", "CAD_Time_Out", "CAD_Time_In", "CAD_Time_Spent_Minutes", "CAD_Time_Response_Minutes", "CAD_Officer", "CAD_Disposition", "CAD_Notes_Cleaned"}
    ),
    
    // Add match indicator
    WithMatchIndicator = Table.AddColumn(ExpandedData, "Has_CAD_Data", each
        if [CAD_Officer] <> null then "Yes" else "No", type text)
in
    WithMatchIndicator