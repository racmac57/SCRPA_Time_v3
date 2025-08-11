// 🕒 2025-07-23-06-00-00
// SCRPA_Time_v2/CAD_vs_RMS_MCode_Solutions
// Author: R. A. Carucci
// Purpose: Separate M Code solutions for CAD (single Incident column) vs RMS (multiple Incident Type columns)

// =============================================================================
// CAD EXPORT PROCESSING (Single "Incident" Column - NO UNPIVOTING NEEDED)
// =============================================================================

// ALL_CRIMES_CAD Query (Master for CAD exports)
let
    Source = Excel.Workbook(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\_EXPORTS\_LawSoft_EXPORT\CAD\latest_cad_export.xlsx"), null, true),
    Data = Source{[Item="Sheet1", Kind="Sheet"]}[Data],
    PromotedHeaders = Table.PromoteHeaders(Data, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders,{}, "en-US"),

    // Remove excluded case
    FilteredRows = Table.SelectRows(ChangedType, each ([Case Number] <> "25-057654")),

    // NO UNPIVOTING - CAD has single "Incident" column
    // Add case-insensitive crime categorization directly
    AddCrimeCategory = Table.AddColumn(FilteredRows, "Crime_Category", each
        let
            UpperIncident = Text.Upper([Incident] ?? "")
        in
            if Text.Contains(UpperIncident, "MOTOR VEHICLE THEFT") or Text.Contains(UpperIncident, "AUTO THEFT") or Text.Contains(UpperIncident, "MV THEFT") then "Motor Vehicle Theft"
            else if Text.Contains(UpperIncident, "BURGLARY") and (Text.Contains(UpperIncident, "AUTO") or Text.Contains(UpperIncident, "VEHICLE")) then "Burglary Auto"
            else if Text.Contains(UpperIncident, "BURGLARY") and Text.Contains(UpperIncident, "COMMERCIAL") then "Burglary Commercial"
            else if Text.Contains(UpperIncident, "BURGLARY") and Text.Contains(UpperIncident, "RESIDENCE") then "Burglary Residence"
            else if Text.Contains(UpperIncident, "ROBBERY") then "Robbery"
            else if Text.Contains(UpperIncident, "SEXUAL") then "Sexual Offenses"
            else "Other"
    ),

    // Add disposition filtering if column exists
    FinalFiltered = if Table.HasColumns(AddCrimeCategory, "Disposition") then
        Table.SelectRows(AddCrimeCategory, each Text.Contains(Text.Upper([Disposition] ?? ""), "SEE REPORT"))
    else
        AddCrimeCategory
in
    FinalFiltered

// CAD Child Queries (Reference ALL_CRIMES_CAD)
// Motor Vehicle Theft - CAD
let
    Source = ALL_CRIMES_CAD, // Reference CAD master query
    Filtered = Table.SelectRows(Source, each [Crime_Category] = "Motor Vehicle Theft")
in
    Filtered

// Burglary Auto - CAD
let
    Source = ALL_CRIMES_CAD,
    Filtered = Table.SelectRows(Source, each [Crime_Category] = "Burglary Auto")
in
    Filtered

// =============================================================================
// RMS EXPORT PROCESSING (Multiple "Incident Type_X" Columns - REQUIRES UNPIVOTING)
// =============================================================================

// ALL_CRIMES_RMS Query (Master for RMS exports)
let
    Source = Excel.Workbook(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\_EXPORTS\_LawSoft_EXPORT\RMS\latest_rms_export.xlsx"), null, true),
    Data = Source{[Item="Sheet1", Kind="Sheet"]}[Data],
    PromotedHeaders = Table.PromoteHeaders(Data, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders,{}, "en-US"),

    FilteredRows = Table.SelectRows(ChangedType, each ([Case Number] <> "25-057654")),

    // RMS has multiple incident columns - UNPIVOT REQUIRED
    // Note: Column names have SPACES not underscores: "Incident Type_1", "Incident Type_2", "Incident Type_3"
    IncidentColumns = {"Incident Type_1", "Incident Type_2", "Incident Type_3"},
    KeepColumns = Table.ColumnNames(FilteredRows),
    IdColumns = List.Difference(KeepColumns, IncidentColumns),

    // Verify incident columns exist before unpivoting
    ExistingIncidentCols = List.Intersect({IncidentColumns, Table.ColumnNames(FilteredRows)}),

    Unpivoted = if List.IsEmpty(ExistingIncidentCols) then
        error "No RMS incident type columns found. Expected: Incident Type_1, Incident Type_2, Incident Type_3"
    else
        Table.UnpivotOtherColumns(FilteredRows, IdColumns, "IncidentColumn", "IncidentType"),

    // Remove null/empty incident types
    CleanedIncidents = Table.SelectRows(Unpivoted, each [IncidentType] <> null and [IncidentType] <> ""),

    // Add case-insensitive crime categorization
    AddCrimeCategory = Table.AddColumn(CleanedIncidents, "Crime_Category", each
        let
            UpperIncident = Text.Upper([IncidentType] ?? "")
        in
            if Text.Contains(UpperIncident, "MOTOR VEHICLE THEFT") or Text.Contains(UpperIncident, "AUTO THEFT") or Text.Contains(UpperIncident, "MV THEFT") then "Motor Vehicle Theft"
            else if Text.Contains(UpperIncident, "BURGLARY") and (Text.Contains(UpperIncident, "AUTO") or Text.Contains(UpperIncident, "VEHICLE")) then "Burglary Auto"
            else if Text.Contains(UpperIncident, "BURGLARY") and Text.Contains(UpperIncident, "COMMERCIAL") then "Burglary Commercial"
            else if Text.Contains(UpperIncident, "BURGLARY") and Text.Contains(UpperIncident, "RESIDENCE") then "Burglary Residence"
            else if Text.Contains(UpperIncident, "ROBBERY") then "Robbery"
            else if Text.Contains(UpperIncident, "SEXUAL") then "Sexual Offenses"
            else "Other"
    ),

    FinalFiltered = if Table.HasColumns(AddCrimeCategory, "Disposition") then
        Table.SelectRows(AddCrimeCategory, each Text.Contains(Text.Upper([Disposition] ?? ""), "SEE REPORT"))
    else
        AddCrimeCategory
in
    FinalFiltered

// RMS Child Queries (Reference ALL_CRIMES_RMS)
// Motor Vehicle Theft - RMS
let
    Source = ALL_CRIMES_RMS, // Reference RMS master query
    Filtered = Table.SelectRows(Source, each [Crime_Category] = "Motor Vehicle Theft")
in
    Filtered

// =============================================================================
// UNIFIED APPROACH (Handles Both CAD and RMS in Single Query)
// =============================================================================

// ALL_CRIMES_UNIFIED Query (Detects data structure automatically)
let
    Source = Excel.Workbook(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\_EXPORTS\_LawSoft_EXPORT\current_export.xlsx"), null, true),
    Data = Source{[Item="Sheet1", Kind="Sheet"]}[Data],
    PromotedHeaders = Table.PromoteHeaders(Data, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders,{}, "en-US"),

    FilteredRows = Table.SelectRows(ChangedType, each ([Case Number] <> "25-057654")),

    // Detect data structure
    HasSingleIncident = Table.HasColumns(FilteredRows, "Incident"),
    HasMultipleIncidents = Table.HasColumns(FilteredRows, "Incident Type_1"),

    ProcessedData =
        if HasSingleIncident then
            // CAD Processing (no unpivoting)
            Table.AddColumn(FilteredRows, "IncidentType", each [Incident])
        else if HasMultipleIncidents then
            // RMS Processing (with unpivoting)
            let
                IncidentColumns = {"Incident Type_1", "Incident Type_2", "Incident Type_3"},
                IdColumns = List.Difference(Table.ColumnNames(FilteredRows), IncidentColumns),
                Unpivoted = Table.UnpivotOtherColumns(FilteredRows, IdColumns, "IncidentColumn", "IncidentType"),
                CleanedIncidents = Table.SelectRows(Unpivoted, each [IncidentType] <> null and [IncidentType] <> "")
            in
                CleanedIncidents
        else
            error "Unable to detect incident column structure. Expected either 'Incident' (CAD) or 'Incident Type_1/2/3' (RMS)",

    // Apply uniform crime categorization
    AddCrimeCategory = Table.AddColumn(ProcessedData, "Crime_Category", each
        let
            UpperIncident = Text.Upper([IncidentType] ?? "")
        in
            if Text.Contains(UpperIncident, "MOTOR VEHICLE THEFT") or Text.Contains(UpperIncident, "AUTO THEFT") or Text.Contains(UpperIncident, "MV THEFT") then "Motor Vehicle Theft"
            else if Text.Contains(UpperIncident, "BURGLARY") and (Text.Contains(UpperIncident, "AUTO") or Text.Contains(UpperIncident, "VEHICLE")) then "Burglary Auto"
            else if Text.Contains(UpperIncident, "BURGLARY") and Text.Contains(UpperIncident, "COMMERCIAL") then "Burglary Commercial"
            else if Text.Contains(UpperIncident, "BURGLARY") and Text.Contains(UpperIncident, "RESIDENCE") then "Burglary Residence"
            else if Text.Contains(UpperIncident, "ROBBERY") then "Robbery"
            else if Text.Contains(UpperIncident, "SEXUAL") then "Sexual Offenses"
            else "Other"
    ),

    FinalFiltered = if Table.HasColumns(AddCrimeCategory, "Disposition") then
        Table.SelectRows(AddCrimeCategory, each Text.Contains(Text.Upper([Disposition] ?? ""), "SEE REPORT"))
    else
        AddCrimeCategory
in
    FinalFiltered

// =============================================================================
// VALIDATION QUERIES
// =============================================================================

// CAD Validation Query
let
    Source = ALL_CRIMES_CAD,
    DataStructureCheck = #table(
        {"Check", "Result", "Status"},
        {
            {"Data Source", "CAD Export", "✅"},
            {"Incident Column", if Table.HasColumns(Source, "Incident") then "Found" else "Missing", if Table.HasColumns(Source, "Incident") then "✅" else "❌"},
            {"Total Records", Number.ToText(Table.RowCount(Source)), "ℹ️"},
            {"Motor Vehicle Theft", Number.ToText(Table.RowCount(Table.SelectRows(Source, each [Crime_Category] = "Motor Vehicle Theft"))), "ℹ️"},
            {"Burglary Auto", Number.ToText(Table.RowCount(Table.SelectRows(Source, each [Crime_Category] = "Burglary Auto"))), "ℹ️"},
            {"Robbery", Number.ToText(Table.RowCount(Table.SelectRows(Source, each [Crime_Category] = "Robbery"))), "ℹ️"}
        }
    )
in
    DataStructureCheck

// RMS Validation Query
let
    Source = ALL_CRIMES_RMS,
    DataStructureCheck = #table(
        {"Check", "Result", "Status"},
        {
            {"Data Source", "RMS Export", "✅"},
            {"Incident Type_1", if Table.HasColumns(Source, "Incident Type_1") then "Found" else "Missing", if Table.HasColumns(Source, "Incident Type_1") then "✅" else "❌"},
            {"Unpivoted Records", Number.ToText(Table.RowCount(Source)), "ℹ️"},
            {"Motor Vehicle Theft", Number.ToText(Table.RowCount(Table.SelectRows(Source, each [Crime_Category] = "Motor Vehicle Theft"))), "ℹ️"},
            {"Burglary Auto", Number.ToText(Table.RowCount(Table.SelectRows(Source, each [Crime_Category] = "Burglary Auto"))), "ℹ️"},
            {"Robbery", Number.ToText(Table.RowCount(Table.SelectRows(Source, each [Crime_Category] = "Robbery"))), "ℹ️"}
        }
    )
in
    DataStructureCheck

// =============================================================================
// IMPLEMENTATION NOTES
// =============================================================================
/*
KEY DIFFERENCES:

CAD EXPORT:
- Single "Incident" column
- NO unpivoting required
- Simpler, faster processing
- Direct filtering on [Incident] field

RMS EXPORT:
- Multiple "Incident Type_1", "Incident Type_2", "Incident Type_3" columns
- REQUIRES unpivoting to create [IncidentType] field
- More complex processing
- Column names have SPACES not underscores

RECOMMENDED APPROACH:
1. Use separate queries for CAD vs RMS if data sources are consistent
2. Use unified query if you need to switch between data sources
3. Always run validation queries first to verify structure
4. Test with small datasets before full refresh

TROUBLESHOOTING:
- Column name errors = Wrong data source approach
- Missing records = Check disposition filtering
- Performance issues = Consider date filtering before categorization
*/
