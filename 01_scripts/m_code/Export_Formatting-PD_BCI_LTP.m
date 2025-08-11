// =============================================================================
// EXPORT FORMATTING WITH CYCLE-BASED FILENAME GENERATION
// =============================================================================

let
    // CYCLE-BASED FILENAME GENERATION FUNCTION
    GenerateCycleFilename = (cycleName as text, dataType as text, optional customSuffix as text) as text =>
        let
            currentDate = Date.ToText(Date.From(DateTime.LocalNow()), "yyyy_MM_dd"),
            suffix = if customSuffix <> null then customSuffix else "7Day_Data_Standardized",
            filename = cycleName & "_" & currentDate & "_" & suffix & ".csv"
        in
            filename,
    
    // STANDARDIZED COLUMN ORDERING FUNCTION
    StandardizeColumnOrder = (inputTable as table, dataSourceType as text) as table =>
        let
            // Define standard column orders for different data types
            CADColumnOrder = {
                "case_number",
                "cycle_name",
                "incident_date",
                "incident_time",
                "response_type",
                "how_reported",
                "location",
                "block",
                "grid",
                "post",
                "time_dispatched",
                "time_out",
                "time_in",
                "time_spent_minutes",
                "time_response_minutes",
                "officer",
                "disposition",
                "cad_notes_cleaned"
            },
            
            RMSColumnOrder = {
                "case_number",
                "cycle_name",
                "incident_date",
                "incident_time",
                "time_of_day",
                "period",
                "location",
                "block",
                "grid",
                "post",
                "all_incidents",
                "incident_type",
                "narrative",
                "total_value_stolen",
                "total_value_recovered",
                "squad",
                "officer_of_record",
                "nibrs_classification"
            },
            
            // Select appropriate column order
            targetOrder = if dataSourceType = "CAD" then CADColumnOrder else RMSColumnOrder,
            
            // Get available columns from input table
            availableColumns = Table.ColumnNames(inputTable),
            
            // Filter target order to only include available columns
            orderedColumns = List.Select(targetOrder, (col) => List.Contains(availableColumns, col)),
            
            // Add any additional columns not in the standard order
            additionalColumns = List.Select(availableColumns, (col) => not List.Contains(targetOrder, col)),
            
            finalColumnOrder = List.Combine({orderedColumns, additionalColumns}),
            
            // Reorder the table
            reorderedTable = Table.SelectColumns(inputTable, finalColumnOrder)
        in
            reorderedTable,
    
    // EXPORT PATH MANAGEMENT FUNCTION
    GenerateExportPath = (basePath as text, cycleName as text, dataType as text) as record =>
        let
            // Clean and validate base path
            cleanBasePath = Text.Replace(Text.Replace(basePath, "/", "\"), "\\", "\"),
            
            // Ensure base path ends with backslash
            normalizedBasePath = if Text.EndsWith(cleanBasePath, "\") then cleanBasePath else cleanBasePath & "\",
            
            // Create cycle-specific subdirectory
            cycleDirectory = normalizedBasePath & cycleName & "\",
            
            // Generate filename
            filename = GenerateCycleFilename(cycleName, dataType),
            
            // Full export path
            fullPath = cycleDirectory & filename,
            
            pathInfo = [
                BasePath = normalizedBasePath,
                CycleDirectory = cycleDirectory,
                Filename = filename,
                FullPath = fullPath,
                DataType = dataType,
                CycleName = cycleName,
                GeneratedDateTime = DateTime.ToText(DateTime.LocalNow())
            ]
        in
            pathInfo,
    
    // COMPREHENSIVE EXPORT PREPARATION FUNCTION  
    PrepareForExport = (inputTable as table, dataSourceType as text, exportBasePath as text) as record =>
        let
            // Ensure cycle_name column exists
            tableWithCycle = if List.Contains(Table.ColumnNames(inputTable), "cycle_name") then
                inputTable
            else
                Table.AddColumn(inputTable, "cycle_name", each "C25W31", type text),
            
            // Get cycle name from first row
            cycleName = if Table.RowCount(tableWithCycle) > 0 then
                Table.FirstN(tableWithCycle, 1){0}[cycle_name]
            else
                "C25W31",
            
            // Standardize column order with cycle_name as 2nd column
            orderedTable = StandardizeColumnOrder(tableWithCycle, dataSourceType),
            
            // Generate export path information
            exportInfo = GenerateExportPath(exportBasePath, cycleName, dataSourceType),
            
            // Add export metadata to each row
            tableWithExportInfo = Table.AddColumn(orderedTable, "export_metadata", each
                [
                    ExportPath = exportInfo[FullPath],
                    ExportDateTime = DateTime.ToText(DateTime.LocalNow()),
                    RecordCount = Table.RowCount(orderedTable),
                    DataSourceType = dataSourceType
                ], type record),
            
            exportPreparation = [
                PreparedTable = orderedTable,
                ExportInformation = exportInfo,
                TableWithMetadata = tableWithExportInfo,
                RecordCount = Table.RowCount(orderedTable),
                ColumnCount = List.Count(Table.ColumnNames(orderedTable)),
                DataSourceType = dataSourceType,
                CycleName = cycleName,
                ReadyForExport = Table.RowCount(orderedTable) > 0
            ]
        in
            exportPreparation,
    
    // BATCH EXPORT PREPARATION FOR MULTIPLE TABLES
    PrepareBatchExport = (tableList as list, exportBasePath as text) as record =>
        let
            // Process each table in the list
            processedTables = List.Transform(tableList, (tableInfo) =>
                let
                    tableName = tableInfo[TableName],
                    tableData = tableInfo[TableData],
                    dataType = tableInfo[DataType],
                    
                    prepared = PrepareForExport(tableData, dataType, exportBasePath)
                in
                    [
                        TableName = tableName,
                        DataType = dataType,
                        OriginalTable = tableData,
                        PreparedExport = prepared
                    ]
            ),
            
            // Generate batch summary
            totalRecords = List.Sum(List.Transform(processedTables, (t) => t[PreparedExport][RecordCount])),
            successfulPreparations = List.Count(List.Select(processedTables, (t) => t[PreparedExport][ReadyForExport])),
            
            batchInfo = [
                BatchProcessedDateTime = DateTime.ToText(DateTime.LocalNow()),
                TotalTables = List.Count(processedTables),
                SuccessfulPreparations = successfulPreparations,
                FailedPreparations = List.Count(processedTables) - successfulPreparations,
                TotalRecordsForExport = totalRecords,
                ProcessedTables = processedTables,
                BatchReadyForExport = successfulPreparations = List.Count(processedTables)
            ]
        in
            batchInfo,
    
    // EXPORT VALIDATION FUNCTION
    ValidateExportReadiness = (preparedExport as record) as record =>
        let
            table = preparedExport[PreparedTable],
            exportInfo = preparedExport[ExportInformation],
            
            validationChecks = [
                HasData = Table.RowCount(table) > 0,
                HasCycleColumn = List.Contains(Table.ColumnNames(table), "cycle_name"),
                HasValidCycleName = if Table.RowCount(table) > 0 then 
                    Table.FirstN(table, 1){0}[cycle_name] <> null and Table.FirstN(table, 1){0}[cycle_name] <> ""
                else false,
                HasValidPath = exportInfo[FullPath] <> null and exportInfo[FullPath] <> "",
                CycleNameFormat = if Table.RowCount(table) > 0 then
                    let cycleName = Table.FirstN(table, 1){0}[cycle_name] in
                    Text.StartsWith(cycleName, "C") and Text.Contains(cycleName, "W")
                else false
            ],
            
            validationResult = [
                ValidationDateTime = DateTime.ToText(DateTime.LocalNow()),
                AllChecksPass = validationChecks[HasData] and validationChecks[HasCycleColumn] and 
                               validationChecks[HasValidCycleName] and validationChecks[HasValidPath] and 
                               validationChecks[CycleNameFormat],
                ValidationChecks = validationChecks,
                ExportRecommendation = if validationChecks[HasData] and validationChecks[HasCycleColumn] and 
                                         validationChecks[HasValidCycleName] and validationChecks[HasValidPath] and 
                                         validationChecks[CycleNameFormat] then
                    "READY_FOR_EXPORT"
                else if not validationChecks[HasData] then
                    "NO_DATA_TO_EXPORT"
                else if not validationChecks[HasCycleColumn] then
                    "MISSING_CYCLE_COLUMN"
                else if not validationChecks[HasValidCycleName] then
                    "INVALID_CYCLE_NAME"
                else
                    "VALIDATION_FAILED",
                Issues = List.Select(Record.FieldNames(validationChecks), (field) => 
                    if Record.Field(validationChecks, field) = false then field else null)
            ]
        in
            validationResult,
    
    // MAIN FUNCTIONS EXPORT
    ExportFunctions = [
        GenerateCycleFilename = GenerateCycleFilename,
        StandardizeColumnOrder = StandardizeColumnOrder,
        GenerateExportPath = GenerateExportPath,
        PrepareForExport = PrepareForExport,
        PrepareBatchExport = PrepareBatchExport,
        ValidateExportReadiness = ValidateExportReadiness
    ]
in
    ExportFunctions