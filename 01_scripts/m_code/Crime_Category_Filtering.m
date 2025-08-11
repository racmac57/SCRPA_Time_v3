// =============================================================================
// CRIME CATEGORY FILTERING - CORRECTED VERSION
// Exact match with Python v8.5 functionality
// =============================================================================

let
    // Define the target crime patterns exactly as in Python v8.5
    FilterTargetCrimes = (data_table as table) as table =>
        let
            FilteredTable = Table.SelectRows(data_table, each
                let
                    // Case-insensitive text conversion with null handling
                    incidentType = Text.Upper([incident_type] ?? ""),
                    allIncidents = Text.Upper([all_incidents] ?? ""),
                    incident = Text.Upper([incident] ?? ""),
                    nibrsClass = Text.Upper([nibrs_classification] ?? "")
                in
                // Motor Vehicle Theft patterns
                Text.Contains(incidentType, "MOTOR VEHICLE THEFT") or
                Text.Contains(allIncidents, "MOTOR VEHICLE THEFT") or
                Text.Contains(incident, "MOTOR VEHICLE THEFT") or
                Text.Contains(incidentType, "AUTO THEFT") or
                Text.Contains(allIncidents, "AUTO THEFT") or
                Text.Contains(incident, "AUTO THEFT") or
                
                // Robbery patterns
                Text.Contains(incidentType, "ROBBERY") or
                Text.Contains(allIncidents, "ROBBERY") or
                Text.Contains(incident, "ROBBERY") or
                
                // Burglary – Auto patterns
                (Text.Contains(incidentType, "BURGLARY") and Text.Contains(incidentType, "AUTO")) or
                (Text.Contains(allIncidents, "BURGLARY") and Text.Contains(allIncidents, "AUTO")) or
                (Text.Contains(incident, "BURGLARY") and Text.Contains(incident, "AUTO")) or
                
                // Sexual offense patterns
                Text.Contains(incidentType, "SEXUAL") or
                Text.Contains(allIncidents, "SEXUAL") or
                Text.Contains(incident, "SEXUAL") or
                
                // Burglary – Commercial patterns
                (Text.Contains(incidentType, "BURGLARY") and Text.Contains(incidentType, "COMMERCIAL")) or
                (Text.Contains(allIncidents, "BURGLARY") and Text.Contains(allIncidents, "COMMERCIAL")) or
                (Text.Contains(incident, "BURGLARY") and Text.Contains(incident, "COMMERCIAL")) or
                
                // Burglary – Residence patterns
                (Text.Contains(incidentType, "BURGLARY") and Text.Contains(incidentType, "RESIDENCE")) or
                (Text.Contains(allIncidents, "BURGLARY") and Text.Contains(allIncidents, "RESIDENCE")) or
                (Text.Contains(incident, "BURGLARY") and Text.Contains(incident, "RESIDENCE"))
            )
        in
            FilteredTable,
    
    // COMPARATIVE VALIDATION FUNCTION
    ValidateFilteringResults = (originalTable as table, filteredTable as table, dataType as text) as record =>
        let
            originalCount = Table.RowCount(originalTable),
            filteredCount = Table.RowCount(filteredTable),
            reductionPercent = if originalCount > 0 then Number.Round((originalCount - filteredCount) / originalCount * 100, 2) else 0,
            categoryCounts = Table.Group(filteredTable, {"crime_category"}, {{"Count", each Table.RowCount(_), Int64.Type}}),
            validation = [
                DataType = dataType,
                OriginalRecords = originalCount,
                FilteredRecords = filteredCount,
                RecordsRemoved = originalCount - filteredCount,
                ReductionPercentage = reductionPercent,
                CategoryBreakdown = categoryCounts,
                FilterEffective = filteredCount > 0 and filteredCount < originalCount
            ]
        in
            validation,
    
    // MULTI-COLUMN FILTERING LOGIC THAT MATCHES PYTHON IMPLEMENTATION
    ApplyPythonStyleFiltering = (inputTable as table, dataSourceType as text) as table =>
        let
            FilterTargets = {
                "motor vehicle theft", 
                "robbery", 
                "burglary – auto", 
                "sexual", 
                "burglary – commercial", 
                "burglary – residence"
            },
            
            ResultTable = if dataSourceType = "CAD" then
                let
                    WithMatch = Table.AddColumn(inputTable, "python_style_match", each
                        let
                            responseType = Text.Lower([response_type] ?? ""),
                            responseTypeRaw = Text.Lower([response_type_raw] ?? ""),
                            disposition = Text.Lower([disposition] ?? "")
                        in
                            List.AnyTrue(List.Transform(FilterTargets, (target) =>
                                Text.Contains(responseType, target) or 
                                Text.Contains(responseTypeRaw, target) or
                                Text.Contains(disposition, target)
                            )), type logical)
                in
                    Table.SelectRows(WithMatch, each [python_style_match] = true)
            else if dataSourceType = "RMS" then
                let
                    WithMatch = Table.AddColumn(inputTable, "python_style_match", each
                        let
                            incidentType = Text.Lower([incident_type] ?? ""),
                            allIncidents = Text.Lower([all_incidents] ?? ""),
                            nibrsClass = Text.Lower([nibrs_classification] ?? "")
                        in
                            List.AnyTrue(List.Transform(FilterTargets, (target) =>
                                Text.Contains(incidentType, target) or 
                                Text.Contains(allIncidents, target) or
                                Text.Contains(nibrsClass, target)
                            )), type logical)
                in
                    Table.SelectRows(WithMatch, each [python_style_match] = true)
            else
                inputTable
        in
            ResultTable,
    
    // COMPREHENSIVE FILTERING ANALYSIS
    ComprehensiveFilterAnalysis = (inputTable as table, dataSourceType as text) as record =>
        let
            // Apply both filtering methods
            CategoryFiltered = if dataSourceType = "CAD" then FilterCADData(inputTable) else FilterRMSData(inputTable),
            PythonFiltered = ApplyPythonStyleFiltering(inputTable, dataSourceType),
            
            // Generate validation reports
            CategoryValidation = ValidateFilteringResults(inputTable, CategoryFiltered, dataSourceType & "_Category"),
            PythonValidation = ValidateFilteringResults(inputTable, PythonFiltered, dataSourceType & "_Python"),
            
            // Compare results
            CategoryCount = Table.RowCount(CategoryFiltered),
            PythonCount = Table.RowCount(PythonFiltered),
            MethodsAgree = CategoryCount = PythonCount,
            
            AnalysisResult = [
                InputRecords = Table.RowCount(inputTable),
                CategoryFilterResults = CategoryValidation,
                PythonFilterResults = PythonValidation,
                FilteringMethodsAgree = MethodsAgree,
                RecommendedOutput = if MethodsAgree then CategoryFiltered else PythonFiltered,
                ComparisonNotes = if MethodsAgree then "Both methods produce identical results" else "Methods differ - review filtering logic"
            ]
        in
            AnalysisResult,
    
            
    // Make function available to other queries
    FunctionTest = FilterTargetCrimes
in
    FunctionTest