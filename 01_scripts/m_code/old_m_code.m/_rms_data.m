let
    Source = Folder.Files("C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA"),
    FilteredFiles = Table.SelectRows(Source, each [Extension] = ".xlsx" and Record.FieldOrDefault([Attributes],"Hidden",false) <> true),
    SortedFiles = Table.Sort(FilteredFiles, {{"Date modified", Order.Descending}}),
    LatestFile = Table.FirstN(SortedFiles, 1),
    TransformedData = Table.AddColumn(LatestFile, "RMS_Data", each Transform_RMS_File([Content])),
    ExpandedData = Table.ExpandTableColumn(TransformedData, "RMS_Data", {"Case_Number", "Incident_Date", "Incident_Time", "Time_Of_Day", "Period", "Location", "Block", "Grid", "Post", "All_Incidents", "Incident_Type", "Narrative", "Total_Value_Stolen", "Total_Value_Recovered", "Squad", "Officer_Of_Record", "NIBRS_Classification"}),
    FinalData = Table.SelectColumns(ExpandedData, {"Case_Number", "Incident_Date", "Incident_Time", "Time_Of_Day", "Period", "Location", "Block", "Grid", "Post", "All_Incidents", "Incident_Type", "Narrative", "Total_Value_Stolen", "Total_Value_Recovered", "Squad", "Officer_Of_Record", "NIBRS_Classification"})
in
    FinalData