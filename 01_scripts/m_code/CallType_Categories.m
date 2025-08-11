// CallType_Categories Query (CORRECTED WITH COLUMN DETECTION)
let
    // === CONFIGURATION ===
    FilePath = "C:\Users\carucci_r\OneDrive - City of Hackensack\09_Reference\Classifications\CallTypes\CallType_Categories.xlsx",
    
    // === SAFE DATA LOADING WITH ERROR HANDLING ===
    Source = Excel.Workbook(File.Contents(FilePath), null, true),
    Sheet = Source{[Item="Sheet1",Kind="Sheet"]}[Data],
    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),
    
    // === COLUMN DETECTION AND MAPPING ===
    ColumnNames = Table.ColumnNames(Headers),
    
    // Try to detect the correct column names (case-insensitive)
    CallTypeColumn = List.First(List.Select(ColumnNames, each Text.Contains(Text.Upper(_), "CALL") or Text.Contains(Text.Upper(_), "INCIDENT"))),
    CategoryColumn = List.First(List.Select(ColumnNames, each Text.Contains(Text.Upper(_), "CATEGORY") or Text.Contains(Text.Upper(_), "TYPE"))),
    ResponseColumn = List.First(List.Select(ColumnNames, each Text.Contains(Text.Upper(_), "RESPONSE") or Text.Contains(Text.Upper(_), "PRIORITY"))),
    
    // === DYNAMIC COLUMN RENAMING ===
    RenamedColumns = Table.RenameColumns(Headers, {
        {CallTypeColumn ?? ColumnNames{0}, "CallType"},
        {CategoryColumn ?? ColumnNames{1}, "Category"}, 
        {ResponseColumn ?? ColumnNames{2}, "ResponseType"}
    }),
    
    // === DATA TYPE CONVERSIONS ===
    TypedData = Table.TransformColumnTypes(RenamedColumns, {
        {"CallType", type text},
        {"Category", type text},
        {"ResponseType", type text}
    }),
    
    // === DATA CLEANING ===
    CleanedData = Table.TransformColumns(TypedData, {
        {"CallType", Text.Trim},
        {"Category", Text.Trim},
        {"ResponseType", Text.Trim}
    })

in
    CleanedData