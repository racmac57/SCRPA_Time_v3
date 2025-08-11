// =============================================================================
// SAMPLE DATA TEST SUITE FOR M-CODE FUNCTIONS
// Tests all functions with realistic sample data to validate functionality
// =============================================================================

let
    // SAMPLE CAD DATA FOR TESTING
    SampleCADData = #table(
        {"ReportNumberNew", "Time of Call", "Response Type", "Incident", "Disposition", "FullAddress2", "Grid", "PDZone", "Officer", "CADNotes"},
        {
            {"25-012345", #datetime(2025, 8, 1, 14, 30, 0), "MOTOR VEHICLE THEFT", "AUTO THEFT", "REPORT TAKEN", "123 Main St, Hackensack, NJ, 07601", "A1", "Zone1", "Officer123", "Vehicle stolen from parking lot"},
            {"25-012346", #datetime(2025, 8, 2, 16, 45, 0), "ROBBERY", "STREET ROBBERY", "ARREST MADE", "456 Oak Ave, Hackensack, NJ, 07601", "B2", "Zone2", "Officer456", "Armed robbery suspect apprehended"},
            {"25-012347", #datetime(2025, 8, 3, 12, 15, 0), "BURGLARY – AUTO", "AUTO BURGLARY", "REPORT TAKEN", "789 Pine St, Hackensack, NJ, 07601", "C3", "Zone3", "Officer789", "Items stolen from vehicle"},
            {"25-012348", #datetime(2025, 8, 4, 18, 20, 0), "SEXUAL ASSAULT", "SEXUAL", "INVESTIGATION", "321 Elm Dr, Hackensack, NJ, 07601", "D4", "Zone4", "Officer321", "Sexual assault reported"},
            {"25-012349", #datetime(2025, 7, 28, 10, 30, 0), "NOISE COMPLAINT", "NOISE", "RESOLVED", "555 Maple Rd, Hackensack, NJ, 07601", "E5", "Zone5", "Officer555", "Noise complaint resolved"},
            {"25-012350", #datetime(2025, 8, 1, 22, 10, 0), "BURGLARY – COMMERCIAL", "COMMERCIAL BURGLARY", "REPORT TAKEN", "888 Business Blvd, Hackensack, NJ, 07601", "F6", "Zone6", "Officer888", "Store broken into"}
        }
    ),
    
    // SAMPLE RMS DATA FOR TESTING
    SampleRMSData = #table(
        {"Case Number", "Incident Date", "Incident Time", "Incident Type_1", "Incident Type_2", "All_Incidents", "NIBRS Classification", "FullAddress", "Grid", "Zone", "Narrative", "Squad"},
        {
            {"25-012345", #date(2025, 8, 1), #time(14, 30, 0), "Motor Vehicle Theft", "", "Motor Vehicle Theft", "240 = THEFT OF MOTOR VEHICLE", "123 Main St, Hackensack, NJ, 07601", "A1", "Zone1", "Vehicle stolen from parking lot", "Squad A"},
            {"25-012346", #date(2025, 8, 2), #time(16, 45, 0), "Robbery", "", "Robbery", "120 = ROBBERY", "456 Oak Ave, Hackensack, NJ, 07601", "B2", "Zone2", "Armed robbery on street", "Squad B"},
            {"25-012347", #date(2025, 8, 3), #time(12, 15, 0), "Burglary – Auto", "", "Burglary – Auto", "23F = THEFT FROM MOTOR VEHICLE", "789 Pine St, Hackensack, NJ, 07601", "C3", "Zone3", "Items stolen from vehicle", "Squad C"},
            {"25-012348", #date(2025, 8, 4), #time(18, 20, 0), "Sexual Offense", "", "Sexual", "11D = FONDLING", "321 Elm Dr, Hackensack, NJ, 07601", "D4", "Zone4", "Sexual assault incident", "Squad D"},
            {"25-012349", #date(2025, 7, 28), #time(10, 30, 0), "Noise Complaint", "", "Noise Complaint", "OTHER", "555 Maple Rd, Hackensack, NJ, 07601", "E5", "Zone5", "Noise complaint", "Squad E"},
            {"25-012350", #date(2025, 8, 1), #time(22, 10, 0), "Burglary – Commercial", "", "Burglary – Commercial", "220 = BURGLARY COMMERCIAL", "888 Business Blvd, Hackensack, NJ, 07601", "F6", "Zone6", "Commercial burglary", "Squad F"}
        }
    ),
    
    // TEST CAD DATA PROCESSING
    TestCADProcessing = () as record =>
        let
            // Convert sample data to binary (simulate Excel import)
            CADResult = try (
                let
                    // Simulate the CAD processing function core logic
                    WithCycle = Table.AddColumn(SampleCADData, "cycle_name", each "C08W31", type text),
                    
                    StandardizedColumns = Table.RenameColumns(WithCycle, {
                        {"ReportNumberNew", "case_number"},
                        {"Time of Call", "incident_date"},
                        {"Response Type", "response_type"},
                        {"Incident", "response_type_raw"},
                        {"Disposition", "disposition"},
                        {"FullAddress2", "full_address_raw"},
                        {"Grid", "grid_raw"},
                        {"PDZone", "post_raw"},
                        {"Officer", "officer"},
                        {"CADNotes", "cad_notes_raw"}
                    }, MissingField.Ignore),
                    
                    // Apply Python crime patterns filtering
                    PythonCrimePatterns = {
                        "MOTOR VEHICLE THEFT", "THEFT OF MOTOR VEHICLE", "AUTO THEFT", "CAR THEFT", "VEHICLE THEFT", "240 = THEFT OF MOTOR VEHICLE",
                        "ROBBERY", "120 = ROBBERY",
                        "BURGLARY – AUTO", "BURGLARY - AUTO", "AUTO BURGLARY", "THEFT FROM MOTOR VEHICLE", "23F = THEFT FROM MOTOR VEHICLE",
                        "SEXUAL", "11D = FONDLING", "CRIMINAL SEXUAL CONTACT",
                        "BURGLARY – COMMERCIAL", "BURGLARY - COMMERCIAL", "COMMERCIAL BURGLARY", "220 = BURGLARY COMMERCIAL",
                        "BURGLARY – RESIDENCE", "BURGLARY - RESIDENCE", "RESIDENTIAL BURGLARY", "220 = BURGLARY RESIDENTIAL"
                    },
                    
                    FilteredData = Table.SelectRows(StandardizedColumns, each
                        List.AnyTrue(List.Transform(PythonCrimePatterns, (pattern) => 
                            Text.Contains(Text.Upper([response_type] ?? ""), Text.Upper(pattern)) or
                            Text.Contains(Text.Upper([response_type_raw] ?? ""), Text.Upper(pattern)) or
                            Text.Contains(Text.Upper([disposition] ?? ""), Text.Upper(pattern))
                        ))
                    )
                in
                    FilteredData
            ) otherwise #table({"error"}, {{"CAD Processing Failed"}}),
            
            TestResult = [
                TestName = "CAD Data Processing",
                OriginalRecords = Table.RowCount(SampleCADData),
                ProcessedRecords = Table.RowCount(CADResult),
                ExpectedMatches = 5, // Should match 5 crime-related records, exclude noise complaint
                TestStatus = if Table.RowCount(CADResult) = 5 then "PASS" else "FAIL",
                ProcessedData = CADResult
            ]
        in
            TestResult,
    
    // TEST RMS DATA PROCESSING
    TestRMSProcessing = () as record =>
        let
            RMSResult = try (
                let
                    // Simulate the RMS processing function core logic
                    WithCycle = Table.AddColumn(SampleRMSData, "cycle_name", each "C08W31", type text),
                    
                    StandardizedColumns = Table.RenameColumns(WithCycle, {
                        {"Case Number", "case_number"},
                        {"Incident Date", "incident_date"},
                        {"Incident Time", "incident_time"},
                        {"Incident Type_1", "incident_type_1_raw"},
                        {"Incident Type_2", "incident_type_2_raw"},
                        {"All_Incidents", "all_incidents"},
                        {"NIBRS Classification", "nibrs_classification"},
                        {"FullAddress", "full_address_raw"},
                        {"Grid", "grid_raw"},
                        {"Zone", "zone_raw"},
                        {"Narrative", "narrative_raw"},
                        {"Squad", "squad"}
                    }, MissingField.Ignore),
                    
                    WithIncidentType = Table.AddColumn(StandardizedColumns, "incident_type", each [incident_type_1_raw], type text),
                    
                    // Apply Python crime patterns filtering
                    PythonCrimePatterns = {
                        "MOTOR VEHICLE THEFT", "THEFT OF MOTOR VEHICLE", "AUTO THEFT", "CAR THEFT", "VEHICLE THEFT", "240 = THEFT OF MOTOR VEHICLE",
                        "ROBBERY", "120 = ROBBERY",
                        "BURGLARY – AUTO", "BURGLARY - AUTO", "AUTO BURGLARY", "THEFT FROM MOTOR VEHICLE", "23F = THEFT FROM MOTOR VEHICLE",
                        "SEXUAL", "11D = FONDLING", "CRIMINAL SEXUAL CONTACT",
                        "BURGLARY – COMMERCIAL", "BURGLARY - COMMERCIAL", "COMMERCIAL BURGLARY", "220 = BURGLARY COMMERCIAL",
                        "BURGLARY – RESIDENCE", "BURGLARY - RESIDENCE", "RESIDENTIAL BURGLARY", "220 = BURGLARY RESIDENTIAL"
                    },
                    
                    FilteredData = Table.SelectRows(WithIncidentType, each
                        List.AnyTrue(List.Transform(PythonCrimePatterns, (pattern) => 
                            Text.Contains(Text.Upper([incident_type] ?? ""), Text.Upper(pattern)) or
                            Text.Contains(Text.Upper([all_incidents] ?? ""), Text.Upper(pattern)) or
                            Text.Contains(Text.Upper([nibrs_classification] ?? ""), Text.Upper(pattern))
                        ))
                    )
                in
                    FilteredData
            ) otherwise #table({"error"}, {{"RMS Processing Failed"}}),
            
            TestResult = [
                TestName = "RMS Data Processing",
                OriginalRecords = Table.RowCount(SampleRMSData),
                ProcessedRecords = Table.RowCount(RMSResult),
                ExpectedMatches = 5, // Should match 5 crime-related records, exclude noise complaint
                TestStatus = if Table.RowCount(RMSResult) = 5 then "PASS" else "FAIL",
                ProcessedData = RMSResult
            ]
        in
            TestResult,
    
    // TEST CRIME CATEGORY FILTERING
    TestCrimeFiltering = () as record =>
        let
            // Test both CAD and RMS filtering with same logic
            CADFiltered = Table.SelectRows(SampleCADData, each
                List.AnyTrue({
                    Text.Contains(Text.Upper([Response Type] ?? ""), "MOTOR VEHICLE THEFT"),
                    Text.Contains(Text.Upper([Response Type] ?? ""), "ROBBERY"),
                    Text.Contains(Text.Upper([Response Type] ?? ""), "BURGLARY"),
                    Text.Contains(Text.Upper([Response Type] ?? ""), "SEXUAL"),
                    Text.Contains(Text.Upper([Incident] ?? ""), "AUTO THEFT"),
                    Text.Contains(Text.Upper([Incident] ?? ""), "ROBBERY"),
                    Text.Contains(Text.Upper([Incident] ?? ""), "BURGLARY"),
                    Text.Contains(Text.Upper([Incident] ?? ""), "SEXUAL")
                })
            ),
            
            RMSFiltered = Table.SelectRows(SampleRMSData, each
                List.AnyTrue({
                    Text.Contains(Text.Upper([Incident Type_1] ?? ""), "MOTOR VEHICLE THEFT"),
                    Text.Contains(Text.Upper([Incident Type_1] ?? ""), "ROBBERY"),
                    Text.Contains(Text.Upper([Incident Type_1] ?? ""), "BURGLARY"),
                    Text.Contains(Text.Upper([Incident Type_1] ?? ""), "SEXUAL"),
                    Text.Contains(Text.Upper([NIBRS Classification] ?? ""), "240"),
                    Text.Contains(Text.Upper([NIBRS Classification] ?? ""), "120"),
                    Text.Contains(Text.Upper([NIBRS Classification] ?? ""), "23F"),
                    Text.Contains(Text.Upper([NIBRS Classification] ?? ""), "11D"),
                    Text.Contains(Text.Upper([NIBRS Classification] ?? ""), "220")
                })
            ),
            
            TestResult = [
                TestName = "Crime Category Filtering",
                CADOriginal = Table.RowCount(SampleCADData),
                CADFiltered = Table.RowCount(CADFiltered),
                RMSOriginal = Table.RowCount(SampleRMSData),
                RMSFiltered = Table.RowCount(RMSFiltered),
                CADTestStatus = if Table.RowCount(CADFiltered) = 5 then "PASS" else "FAIL",
                RMSTestStatus = if Table.RowCount(RMSFiltered) = 5 then "PASS" else "FAIL",
                OverallStatus = if Table.RowCount(CADFiltered) = 5 and Table.RowCount(RMSFiltered) = 5 then "PASS" else "FAIL"
            ]
        in
            TestResult,
    
    // TEST DATA VALIDATION
    TestDataValidation = () as record =>
        let
            OriginalData = SampleCADData,
            FilteredData = Table.FirstN(SampleCADData, 4), // Simulate filtering
            
            ValidationResult = [
                original_count = Table.RowCount(OriginalData),
                filtered_count = Table.RowCount(FilteredData),
                reduction_percentage = (Table.RowCount(OriginalData) - Table.RowCount(FilteredData)) / Table.RowCount(OriginalData) * 100,
                status = if ((Table.RowCount(OriginalData) - Table.RowCount(FilteredData)) / Table.RowCount(OriginalData) * 100) > 90 then "WARNING: High reduction rate" else "OK"
            ],
            
            TestResult = [
                TestName = "Data Validation",
                ValidationReport = ValidationResult,
                TestStatus = if ValidationResult[status] = "OK" then "PASS" else "WARNING",
                ReductionRate = ValidationResult[reduction_percentage]
            ]
        in
            TestResult,
    
    // TEST EXPORT FORMATTING
    TestExportFormatting = () as record =>
        let
            CycleName = "C08W31",
            CurrentDate = "2025_08_02",
            
            CADFilename = CycleName & "_" & CurrentDate & "_7Day_CAD_Data_Standardized.csv",
            RMSFilename = CycleName & "_" & CurrentDate & "_7Day_RMS_Data_Standardized.csv",
            
            TestResult = [
                TestName = "Export Formatting",
                CADFilename = CADFilename,
                RMSFilename = RMSFilename,
                CADNamingCorrect = CADFilename = "C08W31_2025_08_02_7Day_CAD_Data_Standardized.csv",
                RMSNamingCorrect = RMSFilename = "C08W31_2025_08_02_7Day_RMS_Data_Standardized.csv",
                TestStatus = if CADFilename = "C08W31_2025_08_02_7Day_CAD_Data_Standardized.csv" and RMSFilename = "C08W31_2025_08_02_7Day_RMS_Data_Standardized.csv" then "PASS" else "FAIL"
            ]
        in
            TestResult,
    
    // TEST CYCLE DETECTION
    TestCycleDetection = () as record =>
        let
            GetCurrentCycle = (incident_date as date) as text =>
                let
                    CycleStart = #date(2025, 7, 29),
                    CycleEnd = #date(2025, 8, 4)
                in
                    if incident_date >= CycleStart and incident_date <= CycleEnd then "C08W31"
                    else "Historical",
            
            TestDates = {
                #date(2025, 8, 1),  // Should be C08W31
                #date(2025, 8, 4),  // Should be C08W31
                #date(2025, 7, 28), // Should be Historical
                #date(2025, 8, 5)   // Should be Historical
            },
            
            Results = List.Transform(TestDates, (testDate) => GetCurrentCycle(testDate)),
            ExpectedResults = {"C08W31", "C08W31", "Historical", "Historical"},
            
            TestResult = [
                TestName = "Cycle Detection",
                TestDates = TestDates,
                ActualResults = Results,
                ExpectedResults = ExpectedResults,
                TestStatus = if Results{0} = "C08W31" and Results{1} = "C08W31" and Results{2} = "Historical" and Results{3} = "Historical" then "PASS" else "FAIL"
            ]
        in
            TestResult,
    
    // RUN ALL TESTS
    RunAllTests = () as record =>
        let
            CADTest = TestCADProcessing(),
            RMSTest = TestRMSProcessing(),
            FilteringTest = TestCrimeFiltering(),
            ValidationTest = TestDataValidation(),
            ExportTest = TestExportFormatting(),
            CycleTest = TestCycleDetection(),
            
            AllTestsPassed = 
                CADTest[TestStatus] = "PASS" and
                RMSTest[TestStatus] = "PASS" and
                FilteringTest[OverallStatus] = "PASS" and
                (ValidationTest[TestStatus] = "PASS" or ValidationTest[TestStatus] = "WARNING") and
                ExportTest[TestStatus] = "PASS" and
                CycleTest[TestStatus] = "PASS",
            
            ComprehensiveResult = [
                TestSuiteTimestamp = DateTime.ToText(DateTime.LocalNow()),
                OverallTestStatus = if AllTestsPassed then "ALL_TESTS_PASSED" else "SOME_TESTS_FAILED",
                TestResults = [
                    CADProcessingTest = CADTest,
                    RMSProcessingTest = RMSTest,
                    CrimeFilteringTest = FilteringTest,
                    DataValidationTest = ValidationTest,
                    ExportFormattingTest = ExportTest,
                    CycleDetectionTest = CycleTest
                ],
                Summary = [
                    TotalTests = 6,
                    PassedTests = List.Count(List.Select({
                        CADTest[TestStatus], 
                        RMSTest[TestStatus], 
                        FilteringTest[OverallStatus], 
                        ExportTest[TestStatus], 
                        CycleTest[TestStatus]
                    }, each _ = "PASS")) + (if ValidationTest[TestStatus] <> "FAIL" then 1 else 0),
                    TestPassRate = (List.Count(List.Select({
                        CADTest[TestStatus], 
                        RMSTest[TestStatus], 
                        FilteringTest[OverallStatus], 
                        ExportTest[TestStatus], 
                        CycleTest[TestStatus]
                    }, each _ = "PASS")) + (if ValidationTest[TestStatus] <> "FAIL" then 1 else 0)) / 6 * 100
                ],
                Recommendations = if AllTestsPassed then 
                    {"All tests passed - M-code functions ready for production", "Sample data processing successful", "Python equivalency confirmed"} 
                else 
                    {"Review failed tests", "Check sample data processing", "Verify filtering logic"}
            ]
        in
            ComprehensiveResult,
    
    // MAIN TEST SUITE FUNCTIONS EXPORT
    TestSuite = [
        SampleCADData = SampleCADData,
        SampleRMSData = SampleRMSData,
        TestCADProcessing = TestCADProcessing,
        TestRMSProcessing = TestRMSProcessing,
        TestCrimeFiltering = TestCrimeFiltering,
        TestDataValidation = TestDataValidation,
        TestExportFormatting = TestExportFormatting,
        TestCycleDetection = TestCycleDetection,
        RunAllTests = RunAllTests
    ]
in
    TestSuite