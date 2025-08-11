// =============================================================================
// COMPREHENSIVE DATA VALIDATION AND QC REPORTING FUNCTIONS
// =============================================================================

let
    // RECORD COUNT VALIDATION BETWEEN FILTERING APPROACHES
    ValidateRecordCounts = (originalTable as table, filteredTable as table, processName as text) as record =>
        let
            originalCount = Table.RowCount(originalTable),
            filteredCount = Table.RowCount(filteredTable),
            recordsRemoved = originalCount - filteredCount,
            removalRate = if originalCount > 0 then Number.Round(recordsRemoved / originalCount * 100, 2) else 0,
            
            validation = [
                ProcessName = processName,
                OriginalRecordCount = originalCount,
                FilteredRecordCount = filteredCount,
                RecordsRemoved = recordsRemoved,
                RemovalRatePercent = removalRate,
                FilterEffective = filteredCount > 0 and recordsRemoved > 0,
                QualityFlag = if removalRate > 90 then "HIGH_REMOVAL_RATE" 
                             else if removalRate < 1 then "LOW_REMOVAL_RATE"
                             else if filteredCount = 0 then "NO_RECORDS_REMAINING"
                             else "NORMAL"
            ]
        in
            validation,
    
    // COLUMN COMPLETENESS CHECKS
    AnalyzeColumnCompleteness = (inputTable as table) as table =>
        let
            columnNames = Table.ColumnNames(inputTable),
            totalRows = Table.RowCount(inputTable),
            
            completenessAnalysis = List.Transform(columnNames, (colName) =>
                let
                    column = Table.Column(inputTable, colName),
                    nonNullCount = List.Count(List.Select(column, each _ <> null and _ <> "")),
                    nullCount = totalRows - nonNullCount,
                    completenessPercent = if totalRows > 0 then Number.Round(nonNullCount / totalRows * 100, 2) else 0,
                    
                    analysis = [
                        ColumnName = colName,
                        TotalRows = totalRows,
                        NonNullCount = nonNullCount,
                        NullCount = nullCount,
                        CompletenessPercent = completenessPercent,
                        QualityStatus = if completenessPercent >= 95 then "EXCELLENT"
                                       else if completenessPercent >= 85 then "GOOD"
                                       else if completenessPercent >= 70 then "FAIR"
                                       else if completenessPercent >= 50 then "POOR"
                                       else "CRITICAL"
                    ]
                in
                    analysis
            ),
            
            completenessTable = #table(
                {"ColumnName", "TotalRows", "NonNullCount", "NullCount", "CompletenessPercent", "QualityStatus"},
                List.Transform(completenessAnalysis, (row) => {row[ColumnName], row[TotalRows], row[NonNullCount], row[NullCount], row[CompletenessPercent], row[QualityStatus]})
            )
        in
            completenessTable,
    
    // DATA QUALITY METRICS REPORTING
    GenerateDataQualityReport = (inputTable as table, tableName as text) as record =>
        let
            // Basic metrics
            totalRecords = Table.RowCount(inputTable),
            totalColumns = List.Count(Table.ColumnNames(inputTable)),
            
            // Completeness analysis
            completenessData = AnalyzeColumnCompleteness(inputTable),
            averageCompleteness = List.Average(Table.Column(completenessData, "CompletenessPercent")),
            
            // Critical columns check (assuming these exist based on data structure)
            criticalColumns = {"case_number", "incident_date", "incident_time", "location", "cycle_name"},
            criticalColumnStatus = List.Transform(criticalColumns, (colName) =>
                if List.Contains(Table.ColumnNames(inputTable), colName) then
                    let
                        column = Table.Column(inputTable, colName),
                        nonNullCount = List.Count(List.Select(column, each _ <> null and _ <> "")),
                        completeness = if totalRecords > 0 then Number.Round(nonNullCount / totalRecords * 100, 2) else 0
                    in
                        [ColumnName = colName, CompletenessPercent = completeness, Status = if completeness >= 95 then "PASS" else "FAIL"]
                else
                    [ColumnName = colName, CompletenessPercent = 0, Status = "MISSING"]
            ),
            
            // Duplicate detection
            duplicateCheck = if List.Contains(Table.ColumnNames(inputTable), "case_number") then
                let
                    distinctCaseNumbers = Table.RowCount(Table.Distinct(inputTable, {"case_number"})),
                    duplicateCount = totalRecords - distinctCaseNumbers
                in
                    [HasDuplicates = duplicateCount > 0, DuplicateCount = duplicateCount]
            else
                [HasDuplicates = false, DuplicateCount = 0],
            
            // Overall quality score
            qualityScore = List.Average({
                averageCompleteness / 100,
                if duplicateCheck[HasDuplicates] then 0.8 else 1.0,
                if List.Count(List.Select(criticalColumnStatus, each _[Status] = "PASS")) / List.Count(criticalColumns) then 1.0 else 0.5
            }) * 100,
            
            qualityReport = [
                TableName = tableName,
                GeneratedDateTime = DateTime.ToText(DateTime.LocalNow()),
                TotalRecords = totalRecords,
                TotalColumns = totalColumns,
                AverageCompletenessPercent = Number.Round(averageCompleteness, 2),
                OverallQualityScore = Number.Round(qualityScore, 2),
                QualityGrade = if qualityScore >= 90 then "A"
                              else if qualityScore >= 80 then "B"
                              else if qualityScore >= 70 then "C"
                              else if qualityScore >= 60 then "D"
                              else "F",
                CompletenessAnalysis = completenessData,
                CriticalColumnStatus = criticalColumnStatus,
                DuplicateAnalysis = duplicateCheck,
                Recommendations = if qualityScore < 80 then 
                    {"Review data sources for completeness", "Implement data cleaning procedures", "Validate critical column population"} 
                else 
                    {"Data quality is acceptable", "Continue monitoring"}
            ]
        in
            qualityReport,
    
    // COMPARATIVE ANALYSIS BETWEEN CAD AND RMS
    CompareCADvsRMS = (cadTable as table, rmsTable as table) as record =>
        let
            cadReport = GenerateDataQualityReport(cadTable, "CAD_Data"),
            rmsReport = GenerateDataQualityReport(rmsTable, "RMS_Data"),
            
            // Find common case numbers if both have case_number column
            commonCasesAnalysis = if List.Contains(Table.ColumnNames(cadTable), "case_number") and 
                                     List.Contains(Table.ColumnNames(rmsTable), "case_number") then
                let
                    cadCases = List.Distinct(Table.Column(cadTable, "case_number")),
                    rmsCases = List.Distinct(Table.Column(rmsTable, "case_number")),
                    commonCases = List.Intersect({cadCases, rmsCases}),
                    cadOnlyCases = List.Difference(cadCases, rmsCases),
                    rmsOnlyCases = List.Difference(rmsCases, cadCases)
                in
                    [
                        TotalCADCases = List.Count(cadCases),
                        TotalRMSCases = List.Count(rmsCases),
                        CommonCases = List.Count(commonCases),
                        CADOnlyCases = List.Count(cadOnlyCases),
                        RMSOnlyCases = List.Count(rmsOnlyCases),
                        OverlapPercent = if List.Count(cadCases) > 0 then Number.Round(List.Count(commonCases) / List.Count(cadCases) * 100, 2) else 0
                    ]
            else
                [Message = "Case number comparison not available"],
            
            comparison = [
                ComparisonDateTime = DateTime.ToText(DateTime.LocalNow()),
                CADQualityReport = cadReport,
                RMSQualityReport = rmsReport,
                CaseOverlapAnalysis = commonCasesAnalysis,
                QualityComparison = [
                    CADQualityScore = cadReport[OverallQualityScore],
                    RMSQualityScore = rmsReport[OverallQualityScore],
                    BetterQualitySource = if cadReport[OverallQualityScore] > rmsReport[OverallQualityScore] then "CAD" else "RMS",
                    QualityGap = Number.Abs(cadReport[OverallQualityScore] - rmsReport[OverallQualityScore])
                ]
            ]
        in
            comparison,
    
    // VALIDATION SUMMARY DASHBOARD
    CreateValidationDashboard = (validationResults as list) as record =>
        let
            totalValidations = List.Count(validationResults),
            passedValidations = List.Count(List.Select(validationResults, each _[QualityFlag] = "NORMAL")),
            passRate = if totalValidations > 0 then Number.Round(passedValidations / totalValidations * 100, 2) else 0,
            
            dashboard = [
                DashboardGenerated = DateTime.ToText(DateTime.LocalNow()),
                TotalValidations = totalValidations,
                PassedValidations = passedValidations,
                FailedValidations = totalValidations - passedValidations,
                OverallPassRate = passRate,
                ValidationResults = validationResults,
                SystemHealth = if passRate >= 90 then "HEALTHY"
                              else if passRate >= 75 then "WARNING"
                              else "CRITICAL",
                RecommendedActions = if passRate < 75 then 
                    {"Immediate data quality review required", "Check data processing pipelines", "Verify source data integrity"} 
                else if passRate < 90 then
                    {"Monitor data quality trends", "Review flagged processes"}
                else
                    {"System operating normally", "Continue routine monitoring"}
            ]
        in
            dashboard,
    
    // MAIN FUNCTIONS EXPORT
    ValidationFunctions = [
        ValidateRecordCounts = ValidateRecordCounts,
        AnalyzeColumnCompleteness = AnalyzeColumnCompleteness,
        GenerateDataQualityReport = GenerateDataQualityReport,
        CompareCADvsRMS = CompareCADvsRMS,
        CreateValidationDashboard = CreateValidationDashboard
    ]
in
    ValidationFunctions