// Use your existing cycle query
let
    Source = Excel.Workbook(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Temporal\SCRPA_Cycle\7Day_28Day_Cycle_20250414.xlsx"), null, true),
    CycleData = Source{[Item="7Day_28Day_250414",Kind="Sheet"]}[Data],
    Headers = Table.PromoteHeaders(CycleData),
    Typed = Table.TransformColumnTypes(Headers,{
        {"Report_Due_Date", type date}, 
        {"7_Day_Start", type date}, 
        {"7_Day_End", type date}, 
        {"28_Day_Start", type date}, 
        {"28_Day_End", type date}
    })
in
    Typed