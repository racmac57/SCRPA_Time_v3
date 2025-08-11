// 🕒 2025-07-23-06-00-00
// SCRPA_Time_v2/PowerBI_MCode_Fixed_Queries
// Author: R. A. Carucci
// Purpose: Fixed M Code queries with case-insensitive filtering and proper unpivot handling

// =============================================================================
// MAIN ALL_CRIMES QUERY (Master - Reference this in all child queries)
// =============================================================================
let
    // Load from your CAD export file
    Source = Excel.Workbook(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\_EXPORTS\_LawSoft_EXPORT\CAD\latest_cad_export.xlsx"), null, true),
    Data = Source{[Item="Sheet1", Kind="Sheet"]}[Data],
    PromotedHeaders = Table.PromoteHeaders(Data, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders,{}, "en-US"),
    
    // Remove excluded case (as per your current logic)
    FilteredRows = Table.SelectRows(ChangedType, each ([Case Number] <> "25-057654")),
    
    // Unpivot incident types - adjust column names based on your actual data
    IncidentColumns = {"Incident_Type_1", "Incident_Type_2", "Incident_Type_3"}, // Adjust these names
    KeepColumns = Table.ColumnNames(FilteredRows),
    IdColumns = List.Difference(KeepColumns, IncidentColumns),
    
    Unpivoted = Table.UnpivotOtherColumns(FilteredRows, IdColumns, "IncidentColumn", "IncidentType"),
    
    // Remove null/empty incident types
    CleanedIncidents = Table.SelectRows(Unpivoted, each [IncidentType] <> null and [IncidentType] <> ""),
    
    // Add case-insensitive crime categorization
    AddCrimeCategory = Table.AddColumn(CleanedIncidents, "Crime_Category", each
        let
            UpperIncident = Text.Upper([IncidentType])
        in
            if Text.Contains(UpperIncident, "MOTOR VEHICLE THEFT") or Text.Contains(UpperIncident, "AUTO THEFT") or Text.Contains(UpperIncident, "MV THEFT") then "Motor Vehicle Theft"
            else if Text.Contains(UpperIncident, "BURGLARY") and (Text.Contains(UpperIncident, "AUTO") or Text.Contains(UpperIncident, "VEHICLE")) then "Burglary Auto"
            else if Text.Contains(UpperIncident, "BURGLARY - COMMERCIAL") then "Burglary Commercial"
            else if Text.Contains(UpperIncident, "BURGLARY - RESIDENCE") then "Burglary Residence"
            else if Text.Contains(UpperIncident, "ROBBERY") then "Robbery"
            else if Text.Contains(UpperIncident, "SEXUAL") then "Sexual Offenses"
            else "Other"
    ),
    
    // Add disposition filtering (if Disposition column exists)
    FinalFiltered = if Table.HasColumns(AddCrimeCategory, "Disposition") then
        Table.SelectRows(AddCrimeCategory, each Text.Contains(Text.Upper([Disposition] ?? ""), "SEE REPORT"))
    else
        AddCrimeCategory
in
    FinalFiltered

// =============================================================================
// MOTOR VEHICLE THEFT QUERY (Fixed)
// =============================================================================
let
    Source = ALL_CRIMES, // Reference the unpivoted master query
    Filtered = Table.SelectRows(Source, each [Crime_Category] = "Motor Vehicle Theft")
in
    Filtered

// =============================================================================
// BURGLARY AUTO QUERY (Fixed)
// =============================================================================
let
    Source = ALL_CRIMES, // Reference the unpivoted master query
    Filtered = Table.SelectRows(Source, each [Crime_Category] = "Burglary Auto")
in
    Filtered

// =============================================================================
// BURGLARY COMMERCIAL/RESIDENTIAL QUERY (Fixed)
// =============================================================================
let
    Source = ALL_CRIMES, // Reference the unpivoted master query
    Filtered = Table.SelectRows(Source, each 
        [Crime_Category] = "Burglary Commercial" or [Crime_Category] = "Burglary Residence"
    )
in
    Filtered

// =============================================================================
// ROBBERY QUERY (Fixed)
// =============================================================================
let
    Source = ALL_CRIMES, // Reference the unpivoted master query
    Filtered = Table.SelectRows(Source, each [Crime_Category] = "Robbery")
in
    Filtered

// =============================================================================
// SEXUAL OFFENSES QUERY (Fixed)
// =============================================================================
let
    Source = ALL_CRIMES, // Reference the unpivoted master query
    Filtered = Table.SelectRows(Source, each [Crime_Category] = "Sexual Offenses")
in
    Filtered

// =============================================================================
// ALTERNATIVE: DIRECT TEXT FILTERING (If you prefer more control)
// =============================================================================

// Motor Vehicle Theft - Direct Text Filtering
let
    Source = ALL_CRIMES,
    Filtered = Table.SelectRows(Source, each 
        let
            UpperIncident = Text.Upper([IncidentType] ?? "")
        in
            Text.Contains(UpperIncident, "MOTOR VEHICLE THEFT") or
            Text.Contains(UpperIncident, "AUTO THEFT") or
            Text.Contains(UpperIncident, "MV THEFT")
    )
in
    Filtered

// Burglary Auto - Direct Text Filtering  
let
    Source = ALL_CRIMES,
    Filtered = Table.SelectRows(Source, each
        let
            UpperIncident = Text.Upper([IncidentType] ?? "")
        in
            Text.Contains(UpperIncident, "BURGLARY") and
            (Text.Contains(UpperIncident, "AUTO") or Text.Contains(UpperIncident, "VEHICLE"))
    )
in
    Filtered

// Burglary Commercial/Residential - Direct Text Filtering
let
    Source = ALL_CRIMES,
    Filtered = Table.SelectRows(Source, each
        let
            UpperIncident = Text.Upper([IncidentType] ?? "")
        in
            (Text.Contains(UpperIncident, "BURGLARY - COMMERCIAL") or 
             Text.Contains(UpperIncident, "BURGLARY - RESIDENCE")) and
            not (Text.Contains(UpperIncident, "AUTO") or Text.Contains(UpperIncident, "VEHICLE"))
    )
in
    Filtered

// Robbery - Direct Text Filtering
let
    Source = ALL_CRIMES,
    Filtered = Table.SelectRows(Source, each
        Text.Contains(Text.Upper([IncidentType] ?? ""), "ROBBERY")
    )
in
    Filtered

// Sexual Offenses - Direct Text Filtering
let
    Source = ALL_CRIMES,
    Filtered = Table.SelectRows(Source, each
        Text.Contains(Text.Upper([IncidentType] ?? ""), "SEXUAL")
    )
in
    Filtered

// =============================================================================
// VALIDATION QUERY - Compare Counts Before/After Filtering
// =============================================================================
let
    Source = ALL_CRIMES,
    
    // Count total records
    TotalCount = Table.RowCount(Source),
    
    // Count by crime category
    MotorVehicleCount = Table.RowCount(Table.SelectRows(Source, each [Crime_Category] = "Motor Vehicle Theft")),
    BurglaryAutoCount = Table.RowCount(Table.SelectRows(Source, each [Crime_Category] = "Burglary Auto")),
    BurglaryCommCount = Table.RowCount(Table.SelectRows(Source, each [Crime_Category] = "Burglary Commercial")),
    BurglaryResCount = Table.RowCount(Table.SelectRows(Source, each [Crime_Category] = "Burglary Residence")),
    RobberyCount = Table.RowCount(Table.SelectRows(Source, each [Crime_Category] = "Robbery")),
    SexualCount = Table.RowCount(Table.SelectRows(Source, each [Crime_Category] = "Sexual Offenses")),
    
    // Create validation table
    ValidationTable = #table(
        {"Crime_Type", "Count", "Percentage"},
        {
            {"Total Records", TotalCount, 100.0},
            {"Motor Vehicle Theft", MotorVehicleCount, Number.Round(MotorVehicleCount / TotalCount * 100, 2)},
            {"Burglary Auto", BurglaryAutoCount, Number.Round(BurglaryAutoCount / TotalCount * 100, 2)},
            {"Burglary Commercial", BurglaryCommCount, Number.Round(BurglaryCommCount / TotalCount * 100, 2)},
            {"Burglary Residence", BurglaryResCount, Number.Round(BurglaryResCount / TotalCount * 100, 2)},
            {"Robbery", RobberyCount, Number.Round(RobberyCount / TotalCount * 100, 2)},
            {"Sexual Offenses", SexualCount, Number.Round(SexualCount / TotalCount * 100, 2)},
            {"Other", TotalCount - MotorVehicleCount - BurglaryAutoCount - BurglaryCommCount - BurglaryResCount - RobberyCount - SexualCount, 0}
        }
    )
in
    ValidationTable

// =============================================================================
// IMPLEMENTATION NOTES
// =============================================================================
/*
1. UPDATE COLUMN NAMES: 
   - Adjust "Incident_Type_1", "Incident_Type_2", "Incident_Type_3" to match your actual column names
   - Update "Case Number" and "Disposition" column names if different

2. FILE PATH:
   - Update the file path in ALL_CRIMES query to point to your actual CAD export location

3. TESTING APPROACH:
   - Start with ALL_CRIMES query first
   - Verify the unpivot works correctly 
   - Test one filtered query at a time
   - Run the validation query to check counts

4. DISPOSITION FILTERING:
   - The master query includes disposition filtering if the column exists
   - Remove the disposition filter section if not needed

5. TROUBLESHOOTING:
   - If columns don't exist, queries will show errors in Power BI
   - Use Data -> Transform Data to preview results
   - Check Applied Steps to see where errors occur

6. PERFORMANCE:
   - These queries will be slower due to unpivoting
   - Consider adding date range filtering to reduce data volume
   - Use incremental refresh if processing large datasets
*/