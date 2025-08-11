// Query: ALL_CRIMES_Fixed
let
    Source = Folder.Files("C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA"),
    FilteredExcel = Table.SelectRows(Source, each [Extension] = ".xlsx" and Record.FieldOrDefault([Attributes],"Hidden",false) <> true),
    Sorted = Table.Sort(FilteredExcel, {{"Date modified", Order.Descending}}),
    Latest = Table.FirstN(Sorted,1),

    Transform_File = (FileBinary as binary) =>
        let
            Raw = Excel.Workbook(FileBinary, null, true),
            FirstSheet = try Raw{[Item="Sheet1",Kind="Sheet"]}[Data]
                         otherwise try Raw{0}[Data]
                         otherwise Raw{[Kind="Sheet"]}[Data],
            Promoted = Table.PromoteHeaders(FirstSheet, [PromoteAllScalars=true]),
            RenamedFX = Table.RenameColumns(Promoted, {{"Fulladdress","FullAddress"},{"Case Number","CaseNumber"}}, MissingField.Ignore),
            CurrCols = Table.ColumnNames(RenamedFX),
            Pascal = List.Transform(
                CurrCols,
                each if Text.Contains(_, " ")
                     then Text.Combine(
                            List.Transform(
                              Text.SplitAny(Text.Replace(_, " ","_"), " _"),
                              each Text.Upper(Text.Start(_,1)) & Text.Lower(Text.End(_,Text.Length(_)-1))
                            ),
                            ""
                          )
                     else _
            ),
            RenamedPC = Table.RenameColumns(RenamedFX, List.Zip({CurrCols,Pascal}), MissingField.Ignore),
            EnsureCN = if Table.HasColumns(RenamedPC,"CaseNumber") then RenamedPC else Table.AddColumn(RenamedPC,"CaseNumber", each "Missing"),
            CleanCN = Table.TransformColumns(EnsureCN,{{"CaseNumber", each if _ = null then "Null" else Text.From(_), type text}}),
            CNLen = Table.AddColumn(CleanCN,"CaseNumberLength", each Text.Length([CaseNumber])),

            // Incident Date
            WithDate = Table.AddColumn(
                CNLen,
                "Incident_Date",
                each
                    if [IncidentDate] <> null then Date.From([IncidentDate])
                    else if [IncidentDateBetween] <> null then Date.From([IncidentDateBetween])
                    else if [ReportDate] <> null then Date.From([ReportDate])
                    else null,
                type date
            ),

            // Date Sort Key YYYYMMDD
            WithDateSortKey = Table.AddColumn(
                WithDate,
                "DateSortKey",
                each let d = [Incident_Date] in
                    if d <> null then
                        Date.Year(d) * 10000 + Date.Month(d) * 100 + Date.Day(d)
                    else null,
                Int64.Type
            ),

            // Incident Time
            WithTime = Table.AddColumn(
                WithDateSortKey,
                "Incident_Time",
                each
                    if [IncidentTime] <> null then Time.From(DateTime.Time([IncidentTime]))
                    else if [IncidentTimeBetween] <> null then Time.From(DateTime.Time([IncidentTimeBetween]))
                    else if [ReportTime] <> null then Time.From(DateTime.Time([ReportTime]))
                    else null,
                type time
            ),
            StartHour = Table.AddColumn(WithTime, "StartOfHour", each if [Incident_Time] <> null then Time.StartOfHour([Incident_Time]) else null, type time),

            // Time of Day bins
            TOD = Table.AddColumn(
                StartHour,
                "TimeOfDay",
                each let t = try Time.From([Incident_Time]) otherwise null in
                    if t = null then "Unknown"
                    else if t < #time(4,0,0) then "00:00–03:59 Early Morning"
                    else if t < #time(8,0,0) then "04:00–07:59 Morning"
                    else if t < #time(12,0,0) then "08:00–11:59 Morning Peak"
                    else if t < #time(16,0,0) then "12:00–15:59 Afternoon"
                    else if t < #time(20,0,0) then "16:00–19:59 Evening Peak"
                    else "20:00–23:59 Night",
                type text
            ),

            // Block
            Block = Table.AddColumn(
                TOD,
                "Block",
                each let
                    fa = [FullAddress] ?? "",
                    sn = try Number.FromText(Text.BeforeDelimiter(fa," ")) otherwise null,
                    loc = Text.Trim(Text.BeforeDelimiter(Text.AfterDelimiter(fa," "),","))
                in
                    if sn <> null then loc & ", " & Text.From(Number.IntegerDivide(sn,100)*100) & " Block"
                    else loc & ", Unknown Block",
                type text
            ),

            // Combined Incident Types
            AllInc = Table.AddColumn(Block, "ALL_INCIDENTS", each
                [IncidentType1]
                & (if [IncidentType2] <> null then " - "&[IncidentType2] else "")
                & (if [IncidentType3] <> null then " - "&[IncidentType3] else ""),
                type text
            ),

            // Period buckets
            Period = Table.AddColumn(
                AllInc,
                "Period",
                each let d = Duration.Days(Date.From(DateTime.LocalNow()) - [Incident_Date]) in
                    if d <= 7 then "7-Day"
                    else if d <= 28 then "28-Day"
                    else if Date.Year([Incident_Date]) = Date.Year(DateTime.LocalNow()) then "YTD"
                    else "Historical",
                type text
            ),

            // Crime Category
            CrimeCat = Table.AddColumn(
                Period,
                "Crime_Category",
                each let L = Text.Upper([ALL_INCIDENTS] ?? "") in
                    if Text.Contains(L,"MOTOR VEHICLE THEFT") then "Motor Vehicle Theft"
                    else if List.AnyTrue({Text.Contains(L,"BURGLARY - AUTO"),Text.Contains(L,"THEFT FROM MOTOR VEHICLE")}) then "Burglary Auto"
                    else if List.AnyTrue({Text.Contains(L,"BURGLARY - COMMERCIAL"),Text.Contains(L,"BURGLARY - RESIDENCE")}) then "Burglary - Comm & Res"
                    else if Text.Contains(L,"ROBBERY") then "Robbery"
                    else if List.AnyTrue({Text.Contains(L,"SEXUAL"),Text.Contains(L,"RAPE")}) then "Sexual Offenses"
                    else "Other",
                type text
            ),

            // Clean narrative
            CleanN = Table.TransformColumns(
                Table.TransformColumns(CrimeCat, {{"Narrative", Text.Trim, type text}}),
                {{"Narrative", Text.Clean, type text}}
            )
        in
            CleanN,

    // Invoke transform
    Invoked = Table.AddColumn(Latest, "Transformed", each Transform_File([Content]), type table),
    Expanded = Table.ExpandTableColumn(Invoked, "Transformed", Table.ColumnNames(Transform_File(Latest{0}[Content]))),

    // Final renames & types
    Renamed = Table.RenameColumns(
        Expanded,
        {
            {"CaseNumber","Case Number"},
            {"Incident_Date","Incident Date"},
            {"Incident_Time","Incident Time"},
            {"IncidentDateBetween","Incident Date_Between"},
            {"IncidentTimeBetween","Incident Time_Between"},
            {"ReportDate","Report Date"},
            {"ReportTime","Report Time"},
            {"IncidentType1","Incident Type_1"},
            {"IncidentType2","Incident Type_2"},
            {"IncidentType3","Incident Type_3"},
            {"Registration1","Registration 1"},
            {"RegState1","Reg State 1"},
            {"Registration2","Registration 2"},
            {"RegState2","Reg State 2"},
            {"CaseNumberLength","CASE_NUMBER_LENGTH"},
            {"ALL_INCIDENTS","ALL_INCIDENTS"},
            {"DateSortKey","Date Sort Key"}
        },
        MissingField.Ignore
    ),
    Typed = Table.TransformColumnTypes(
        Renamed,
        {
            {"CASE_NUMBER_LENGTH", Int64.Type},
            {"Incident Type_1", type text},
            {"Incident Type_2", type text},
            {"Incident Type_3", type text},
            {"Incident Date", type date},
            {"Incident Time", type time},
            {"Registration 1", type text},
            {"Registration 2", type text},
            {"Reg State 1", type text},
            {"Reg State 2", type text},
            {"Make1", type text},
            {"Make2", type text},
            {"Model1", type text},
            {"Model2", type text},
            {"Date Sort Key", Int64.Type}
        }
    ),
    CapRegs = Table.TransformColumns(
        Typed,
        {
            {"Registration 1", Text.Upper, type text},
            {"Registration 2", Text.Upper, type text},
            {"Make1", Text.Upper, type text},
            {"Make2", Text.Upper, type text},
            {"Model1", Text.Upper, type text},
            {"Model2", Text.Upper, type text},
            {"Reg State 1", Text.Upper, type text},
            {"Reg State 2", Text.Upper, type text}
        }
    ),
    CleanTypes = Table.TransformColumns(
        CapRegs,
        {
            {"Incident Type_1", each if _<>null then Text.BeforeDelimiter(_," - 2C") else _, type text},
            {"Incident Type_2", each if _<>null then Text.BeforeDelimiter(_," - 2C") else _, type text},
            {"Incident Type_3", each if _<>null then Text.BeforeDelimiter(_," - 2C") else _, type text}
        }
    ),
    Unpivoted = Table.Unpivot(CleanTypes, {"Incident Type_1","Incident Type_2","Incident Type_3"},"IncidentTypeNumber","IncidentType"),
    Distinct = Table.Distinct(Unpivoted, {"Case Number"})
in
    Distinct