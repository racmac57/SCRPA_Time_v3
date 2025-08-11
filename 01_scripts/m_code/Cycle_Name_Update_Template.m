// =============================================================================
// CYCLE NAME UPDATE TEMPLATE
// Add this logic to your file that contains JoinedData and FinalData steps
// =============================================================================

/*
STEP 1: Add this step BEFORE the final FinalData step:
*/

let
    // Replace 'JoinedData' with the actual previous step in your query if different
    AddCycleName = Table.AddColumn(JoinedData, "cycle_name", each
        let
            incident_date = try [incident_date] otherwise null
        in
            if incident_date = null then "Historical"
            else if incident_date >= #date(2025, 7, 29) and incident_date <= #date(2025, 8, 4) then "C08W31"
            else "Historical", type text),

    FinalData = Table.SelectColumns(AddCycleName, {
        "call_id", 
        "case_number", 
        "cycle_name",           // <- cycle_name now included as 3rd column
        "crime_type_visual", 
        "incident_type", 
        "all_incidents",
        "call_date", 
        "time_of_day_visual", 
        "response_minutes", 
        "response_category",
        "longitude_dd", 
        "latitude_dd", 
        "beat", 
        "location", 
        "narrative", 
        "disposition_geo",
        "cad_call_type", 
        "full_address_geo", 
        "total_value_stolen"
    })
in
    FinalData

// =============================================================================
// IMPLEMENTATION NOTES:
// =============================================================================

/*
1. CYCLE LOGIC MATCHES PYTHON IMPLEMENTATION:
   - Current cycle: C08W31 (2025-07-29 to 2025-08-04)
   - All other dates: "Historical"
   - Null dates: "Historical"

2. COLUMN ORDERING:
   - cycle_name is positioned as 3rd column after call_id and case_number
   - Maintains all existing columns in the selection

3. ERROR HANDLING:
   - Uses "try [incident_date] otherwise null" for safe date extraction
   - Handles null incident_date gracefully

4. INTEGRATION:
   - Replace "JoinedData" with your actual previous step name
   - Ensure incident_date column exists in your data structure
   - Update any subsequent references from JoinedData to AddCycleName
*/

// Example of complete integration in your existing file structure:
/*
let
    // ... your existing steps ...
    
    // Your existing data processing steps here
    SomeProcessingStep = YourExistingLogic,
    
    // ADD THIS STEP (replace JoinedData with your actual previous step name):
    AddCycleName = Table.AddColumn(SomeProcessingStep, "cycle_name", each
        let
            incident_date = try [incident_date] otherwise null
        in
            if incident_date = null then "Historical"
            else if incident_date >= #date(2025, 7, 29) and incident_date <= #date(2025, 8, 4) then "C08W31"
            else "Historical", type text),
    
    // UPDATE YOUR FINAL STEP TO USE AddCycleName:
    FinalData = Table.SelectColumns(AddCycleName, {
        "call_id", "case_number", "cycle_name", "crime_type_visual", "incident_type", "all_incidents",
        "call_date", "time_of_day_visual", "response_minutes", "response_category",
        "longitude_dd", "latitude_dd", "beat", "location", "narrative", "disposition_geo",
        "cad_call_type", "full_address_geo", "total_value_stolen"
    })
in
    FinalData
*/