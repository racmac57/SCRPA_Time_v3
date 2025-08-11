(Content as binary) =>
let
    Source = Excel.Workbook(Content, null, true),
    Sheet1_Sheet = Source{[Item="Sheet1",Kind="Sheet"]}[Data],
    PromoteHeaders = Table.PromoteHeaders(Sheet1_Sheet, [PromoteAllScalars=true]),
    HasCaseNumber = Table.HasColumns(PromoteHeaders, "Case Number"),
    AddCaseNumber = if HasCaseNumber then PromoteHeaders else Table.AddColumn(PromoteHeaders, "Case Number", each "Missing"),
    ReplaceNulls = Table.TransformColumns(AddCaseNumber, {
        {"Case Number", each if _ is null then "Null" else Text.From(_), type text}
    }),
    // Custom column: CASE_NUMBER_LENGTH
    AddCaseNumberLength = Table.AddColumn(ReplaceNulls, "CASE_NUMBER_LENGTH", each Text.Length([Case Number])),
    // Custom column: INC_DATE
    AddIncDate = Table.AddColumn(AddCaseNumberLength, "INC_DATE", each 
        if [Incident Date] = null then 
            (if [Incident Date_Between] = null then [Report Date] else [Incident Date_Between]) 
        else [Incident Date]),
    // Custom column: INC_TIME
    AddIncTime = Table.AddColumn(AddIncDate, "INC_TIME", each 
        if [Incident Time] = null then 
            (if [Incident Time_Between] = null then [Report Time] else [Incident Time_Between]) 
        else [Incident Time]),
    // Custom column: Start of Hour
    AddStartOfHour = Table.AddColumn(AddIncTime, "Start of Hour", each Time.StartOfHour([INC_TIME]), type time),
    // Custom column: Year
    AddYear = Table.AddColumn(AddStartOfHour, "Year", each Date.Year([INC_DATE]), Int64.Type),
    // Custom column: Month Name
    AddMonthName = Table.AddColumn(AddYear, "Month Name", each Date.MonthName([INC_DATE]), type text),
    // Custom column: Week of Year
    AddWeekOfYear = Table.AddColumn(AddMonthName, "Week of Year", each Date.WeekOfYear([INC_DATE]), Int64.Type),
    // Custom column: Week of Month
    AddWeekOfMonth = Table.AddColumn(AddWeekOfYear, "Week of Month", each Date.WeekOfMonth([INC_DATE]), Int64.Type),
    // Custom column: Day
    AddDay = Table.AddColumn(AddWeekOfMonth, "Day", each Date.Day([INC_DATE]), Int64.Type),
    // Custom column: Day of Year
    AddDayOfYear = Table.AddColumn(AddDay, "Day of Year", each Date.DayOfYear([INC_DATE]), Int64.Type),
    // Custom column: Day Name
    AddDayName = Table.AddColumn(AddDayOfYear, "Day Name", each Date.DayOfWeekName([INC_DATE]), type text),
    // Custom column: INC_DATE_AND_TIME
    AddIncDateTime = Table.AddColumn(AddDayName, "INC_DATE_AND_TIME", each 
        Text.Combine({Text.From([INC_DATE], "en-US"), Text.From([INC_TIME], "en-US")}, " "), type text),
    // Custom column: ALL_INCIDENTS
    AddAllIncidents = Table.AddColumn(AddIncDateTime, "ALL_INCIDENTS", each 
        Text.Combine(
            List.Select(
                {[Incident Type_1], [Incident Type_2], [Incident Type_3]},
                each _ <> null and _ <> ""
            ),
            ", "
        ), type text),
    // Custom column: StNumber
    AddStNumber = Table.AddColumn(AddAllIncidents, "StNumber", each 
        try Text.BeforeDelimiter([FullAddress], " ") otherwise null, type text),
    // Custom column: Location
    AddLocation = Table.AddColumn(AddStNumber, "Location", each 
        try Text.BetweenDelimiters([FullAddress], " ", ", ") otherwise [FullAddress], type text),
    // Custom column: Block
    AddBlock = Table.AddColumn(AddLocation, "Block", each 
        let
            // Check if StNumber is a directional word
            IsDirectional = List.Contains({"North", "South", "East", "West"}, [StNumber]),
            // Combine StNumber and Location for intersections if directional
            AdjustedLocation = 
                if IsDirectional and (Text.Contains([Location], "&") or Text.Contains([Location], " and ") or Text.Contains([Location], "/")) then
                    [StNumber] & " " & [Location]
                else
                    [Location],
            CustomColumn = 
                if Text.Contains(AdjustedLocation, "&") or Text.Contains(AdjustedLocation, " and ") or Text.Contains(AdjustedLocation, "/")) then
                    let
                        // Replace directional prefixes, preserving space
                        AbbreviatedLocation = 
                            Text.Replace(
                                Text.Replace(
                                    Text.Replace(
                                        Text.Replace(AdjustedLocation, "North ", "N "),
                                    "South ", "S "),
                                "East ", "E "),
                            "West ", "W ")
                    in
                        AbbreviatedLocation
                else if [StNumber] = null then
                    AdjustedLocation
                else
                    let
                        // Use full Location for standard address
                        StreetName = [Location],
                        BlockNumber = try Number.ToText(Number.IntegerDivide(Number.From([StNumber]), 100) * 100) & " Block" otherwise "0 Block",
                        // Apply abbreviations for standard addresses
                        AbbreviatedStreetName = 
                            Text.Replace(
                                Text.Replace(
                                    Text.Replace(StreetName, "Street", "St"), 
                                "Avenue", "Ave"), 
                            "Place", "Pl")
                    in
                        AbbreviatedStreetName & ", " & BlockNumber
        in
            CustomColumn, type text),
    // Custom column: Season
    AddSeason = Table.AddColumn(AddBlock, "Season", each 
        if List.Contains({"December", "January", "February"}, [Month Name]) then "Winter"
        else if List.Contains({"March", "April", "May"}, [Month Name]) then "Spring"
        else if List.Contains({"June", "July", "August"}, [Month Name]) then "Summer"
        else if List.Contains({"September", "October", "November"}, [Month Name]) then "Fall"
        else "Invalid Month", type text),
    // Custom column: Supplement Column
    AddSupplement = Table.AddColumn(AddSeason, "Supplement Column", each 
        if [CASE_NUMBER_LENGTH] = 9 then "Null"
        else if [CASE_NUMBER_LENGTH] = 10 then "Supplement"
        else "", type text),
    // Custom column: Due Date
    AddDueDate = Table.AddColumn(AddSupplement, "Due Date", each 
        Date.AddDays([INC_DATE], Number.Mod(2 - Date.DayOfWeek([INC_DATE]) + 7, 7)), type date),
    // Custom column: TOTAL_STOLEN_AMOUNT
    AddTotalStolenAmount = Table.AddColumn(AddDueDate, "TOTAL_STOLEN_AMOUNT", each 
        let
            text = [Narrative],
            splitByDollar = Text.Split(text, "$"),
            extractList = List.Transform(List.RemoveFirstN(splitByDollar, 1), each 
                try "$" & Text.BeforeDelimiter(_, ".", 2) otherwise ""),
            combinedText = Text.Combine(List.Select(extractList, each _ <> ""), " ")
        in
            combinedText, type text),
    // Custom column: SUSPECT IN NARRATIVE
    AddSuspectInNarrative = Table.AddColumn(AddTotalStolenAmount, "SUSPECT IN NARRATIVE", each 
        let
            text = [Narrative],
            lowerText = Text.Lower(text),
            splitBySuspect = Text.Split(lowerText, "suspect"),
            extractList = List.Transform(List.RemoveFirstN(splitBySuspect, 1), each "suspect" & Text.BeforeDelimiter(_, ".")),
            combinedText = Text.Combine(extractList, " ")
        in
            combinedText, type text),
    // Custom column: Vehicle1
    AddVehicle1 = Table.AddColumn(AddSuspectInNarrative, "Vehicle1", each 
        if [Reg State 1] <> null and [Registration 1] <> null and [Make1] <> null and [Model1] <> null then
            Text.Upper([Reg State 1]) & "-" & Text.Upper([Registration 1]) & ", " & [Make1] & ", " & [Model1]
        else if [Reg State 1] <> null and [Registration 1] <> null then
            Text.Upper([Reg State 1]) & "-" & Text.Upper([Registration 1])
        else if [Make1] <> null and [Model1] <> null then
            [Make1] & ", " & [Model1]
        else
            null, type text),
    // Custom column: Vehicle2
    AddVehicle2 = Table.AddColumn(AddVehicle1, "Vehicle2", each 
        if [Reg State 2] <> null and [Registration 2] <> null and [Make2] <> null and [Model2] <> null then
            Text.Upper([Reg State 2]) & "-" & Text.Upper([Registration 2]) & ", " & [Make2] & ", " & [Model2]
        else if [Reg State 2] <> null and [Registration 2] <> null then
            Text.Upper([Reg State 2]) & "-" & Text.Upper([Registration 2])
        else if [Make2] <> null and [Model2] <> null then
            [Make2] & ", " & [Model2]
        else
            null, type text),
    // Custom column: V1_V2
    AddV1V2 = Table.AddColumn(AddVehicle2, "V1_V2", each 
        let
            Combined1 = if [Reg State 1] <> null and [Registration 1] <> null and [Make1] <> null and [Model1] <> null then
                            "V1: " & Text.Upper([Reg State 1]) & "-" & Text.Upper([Registration 1]) & ", " & [Make1] & ", " & [Model1]
                        else if [Reg State 1] <> null and [Registration 1] <> null then
                            "V1: " & Text.Upper([Reg State 1]) & "-" & Text.Upper([Registration 1])
                        else if [Make1] <> null and [Model1] <> null then
                            "V1: " & [Make1] & ", " & [Model1]
                        else
                            null,
            Combined2 = if [Reg State 2] <> null and [Registration 2] <> null and [Make2] <> null and [Model2] <> null then
                            "V2: " & Text.Upper([Reg State 2]) & "-" & Text.Upper([Registration 2]) & ", " & [Make2] & ", " & [Model2]
                        else if [Reg State 2] <> null and [Registration 2] <> null then
                            "V2: " & Text.Upper([Reg State 2]) & "-" & Text.Upper([Registration 2])
                        else if [Make2] <> null and [Model2] <> null then
                            "V2: " & [Make2] & ", " & [Model2]
                        else
                            null,
            Result = if Combined1 <> null and Combined2 <> null then
                         Combined1 & " | " & Combined2
                     else if Combined1 <> null then
                         Combined1
                     else
                         Combined2
        in
            Result, type text),
    // Trim leading, trailing, and redundant spaces from all text columns
    TrimSpaces = Table.TransformColumns(AddV1V2, 
        let
            // Function to trim spaces
            TrimText = (text as any) as any =>
                if text is text and text <> null then
                    Text.Combine(
                        List.RemoveNulls(
                            List.Transform(
                                Text.Split(text, " "),
                                each if Text.Length(_) = 0 then null else _
                            )
                        ),
                        " "
                    )
                else
                    text
        in
            List.Transform(Table.ColumnNames(AddV1V2), each {_, TrimText})
    ),
    // Remove duplicate rows
    RemoveDuplicates = Table.Distinct(TrimSpaces)
in
    RemoveDuplicates