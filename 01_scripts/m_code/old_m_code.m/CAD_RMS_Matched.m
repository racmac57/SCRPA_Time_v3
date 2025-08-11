// 🕒 2025-07-23-16-30-00
// Project: SCRPA_Time_v2/CAD_RMS_Matched_FIXED_Duration_Formatting
// Author: R. A. Carucci
// Purpose: Fixed duration formatting with proper error handling, plus CADNotes username/timestamp extraction and cleaning

let
    // 1) Load both datasets
    SourceRMS      = ALL_CRIMES,
    SourceCAD      = CAD_DATA,

    // 2) Rename conflicting columns BEFORE joining
    RMSRenamed     = Table.RenameColumns(
                       SourceRMS,
                       {
                         {"Grid", "RMS_Grid"},
                         {"Zone", "RMS_Zone"},
                         {"Officer of Record", "RMS_Officer"},
                         {"Block", "RMS_Block"}
                       },
                       MissingField.Ignore
                     ),
    CADRenamed     = Table.RenameColumns(
                       SourceCAD,
                       {
                         {"Grid", "CAD_Grid"},
                         {"PDZone", "CAD_Zone"},
                         {"Officer", "CAD_Officer"},
                         {"Block", "CAD_Block"},
                         {"Disposition", "CAD_Disposition"},
                         {"Response Type", "CAD_Response_Type"}
                       },
                       MissingField.Ignore
                     ),

    // 3) LEFT JOIN RMS with CAD on Case Number → ReportNumberNew
    JoinedData     = Table.Join(
                       RMSRenamed, {"Case Number"},
                       CADRenamed, {"ReportNumberNew"},
                       JoinKind.LeftOuter
                     ),

    // 4) Flag whether CAD data exists
    WithCADFlag    = Table.AddColumn(
                       JoinedData,
                       "Has_CAD_Data",
                       each if [ReportNumberNew] <> null then "Yes" else "No",
                       type text
                     ),

    // 5) Parse CADNotes into CAD_Username, CAD_Timestamp & CAD_Notes_Cleaned
    WithParsedCADNotes = Table.AddColumn(
      WithCADFlag,
      "CADNotes_Parsed",
      each let
        raw            = [CADNotes] ?? "",
        // split into lines and pick the first non‑empty header
        lines          = Text.Split(raw, "#(lf)"),
        nonEmptyLines  = List.Select(lines, each Text.Trim(_) <> ""),
        header         = if List.Count(nonEmptyLines)>0 then nonEmptyLines{0} else "",

        // 5a) Username = first underscore token or blank
        headerTokens   = Text.Split(Text.Trim(header), " "),
        userCandidates = List.Select(headerTokens, each Text.Contains(_, "_")),
        userRaw        = if List.Count(userCandidates)>0 then userCandidates{0} else "",
        CAD_Username   = if Text.Length(userRaw)>0
                         then Text.Combine(
                                List.Transform(Text.Split(userRaw, "_"), each Text.Proper(_)),
                                "_"
                              )
                         else null,

        // 5b) Timestamp = first date token + next token
        dateTokens     = List.Select(headerTokens, each Text.Contains(_, "/")),
        dateRaw        = if List.Count(dateTokens)>0 then dateTokens{0} else "",
        dateIndex      = if dateRaw<>"" then List.PositionOf(headerTokens, dateRaw) else -1,
        timeRaw        = if dateIndex>=0 and dateIndex < List.Count(headerTokens)-1
                         then headerTokens{dateIndex+1} else "",
        dtRaw          = if dateRaw<>"" and timeRaw<>"" then dateRaw & " " & timeRaw else "",
        dtParsed       = try DateTime.FromText(dtRaw) otherwise null,
        CAD_Timestamp  = if dtParsed<>null then DateTime.ToText(dtParsed,"MM/dd/yyyy HH:mm:ss") else null,

        // 5c) Remove header, dtRaw, userRaw from the full text
        combinedLines  = Text.Combine(lines, " "),
        withoutHdr     = Text.Replace(combinedLines, header, ""),
        withoutDt      = Text.Replace(withoutHdr, dtRaw, ""),
        withoutUser    = Text.Replace(withoutDt, userRaw, ""),

        // 5d) Tokenize & filter stray tokens
        toks           = Text.Split(Text.Trim(withoutUser), " "),
        keepTokens     = List.Select(toks, each let t=Text.Trim(_) in
                            t<>"" and
                            not (Text.Contains(t,"/") and Text.Contains(t,":")) and
                            not Text.StartsWith(t,"(") and
                            not Text.EndsWith(t,")") and
                            not Text.StartsWith(t,"#") and
                            Text.Lower(t)<>"cc" and
                            Text.Trim(Text.Remove(t,{"-","?"}))<>""
                          ),

        // 5e) Recombine & proper‑case narrative
        combined       = Text.Combine(keepTokens, " "),
        CAD_Notes_Cleaned = if Text.Length(combined)=0 then null else Text.Proper(combined)

      in
        [
          CAD_Username      = CAD_Username,
          CAD_Timestamp     = CAD_Timestamp,
          CAD_Notes_Cleaned = CAD_Notes_Cleaned
        ],
      type record
    ),

    // 6) Expand parsed record into three columns
    ExpandedCADNotes = Table.ExpandRecordColumn(
                         WithParsedCADNotes,
                         "CADNotes_Parsed",
                         {"CAD_Username","CAD_Timestamp","CAD_Notes_Cleaned"},
                         {"CAD_Username","CAD_Timestamp","CAD_Notes_Cleaned"}
                       ),

    // 7) FIXED Time_Spent Formatting
    WithTimeSpentFormatted = Table.AddColumn(
      ExpandedCADNotes,
      "Time_Spent_Formatted",
      each let m=[Time_Spent_Minutes] in
        if m=null then null else try
          let
            vm=Number.Round(Number.From(m),0),
            h=Number.IntegerDivide(vm,60),
            r=Number.Mod(vm,60)
          in
            if vm<=0 then "0 Mins"
            else if h=0 then Text.From(r)&" Mins"
            else if r=0 then Text.From(h)&" Hrs"
            else Text.From(h)&" Hrs "&Text.PadStart(Text.From(r),2,"0")&" Mins"
        otherwise "Invalid Time",
      type text
    ),
    WithTimeSpentFlag = Table.AddColumn(
      WithTimeSpentFormatted,
      "Time_Spent_Flag",
      each let m=[Time_Spent_Minutes] in
        if m=null then null else try
          let v=Number.From(m) in
            if v<5 then "Under 5 Minutes"
            else if v>300 then "Over 5 Hours"
            else "Normal"
        otherwise "Invalid",
      type text
    ),

    // 8) FIXED Time_Response Formatting
    WithTimeResponseFormatted = Table.AddColumn(
      WithTimeSpentFlag,
      "Time_Response_Formatted",
      each let m=[Time_Response_Minutes] in
        if m=null then null else try
          let
            totalSec=Number.Round(Number.From(m)*60,0),
            mins=Number.IntegerDivide(totalSec,60),
            secs=Number.Mod(totalSec,60)
          in
            if totalSec<=0 then "0 Secs"
            else if mins=0 then Text.From(secs)&" Secs"
            else if secs=0 then Text.From(mins)&" Mins"
            else Text.From(mins)&" Mins "&Text.PadStart(Text.From(secs),2,"0")&" Secs"
        otherwise "Invalid Time",
      type text
    ),
    WithTimeResponseFlag = Table.AddColumn(
      WithTimeResponseFormatted,
      "Time_Response_Flag",
      each let m=[Time_Response_Minutes] in
        if m=null then null else try
          let v=Number.From(m) in
            if v<=1 then "0-1 Minutes"
            else if v>10 then "Over 10 Minutes"
            else "Normal"
        otherwise "Invalid",
      type text
    ),

    // 9) Unified Grid / Zone & Enhanced Block
    WithUnifiedGrid = Table.AddColumn(
      WithTimeResponseFlag,
      "Grid",
      each if [CAD_Grid]<>null then [CAD_Grid] else [RMS_Grid],
      type text
    ),
    WithUnifiedZone = Table.AddColumn(
      WithUnifiedGrid,
      "Zone",
      each if [CAD_Zone]<>null then [CAD_Zone] else [RMS_Zone],
      type text
    ),
    WithEnhancedBlock = Table.AddColumn(
      WithUnifiedZone,
      "Enhanced_Block",
      each let
        rm=[RMS_Block],
        cb=[CAD_Block]
      in
        if (Text.Contains(rm??"","Check CAD Location Data") or Text.Contains(rm??"","Incomplete Address")) and cb<>null
        then cb else rm,
      type text
    ),

    // 10) Unified Officer
    WithUnifiedOfficer = Table.AddColumn(
      WithEnhancedBlock,
      "Officer",
      each if [CAD_Officer]<>null then [CAD_Officer] else [RMS_Officer],
      type text
    ),

    // 11) Select final columns
    FinalColumns = Table.SelectColumns(
      WithUnifiedOfficer,
      {
        "Case Number","ReportNumberNew","Incident_Date","Incident_Time",
        "IncidentType","ALL_INCIDENTS","Crime_Category","TimeOfDay","Period",
        "Officer","Grid","Zone","RMS_Block","CAD_Block","Enhanced_Block",
        "Has_CAD_Data",
        "Time_Response_Minutes","Time_Response_Formatted","Time_Response_Flag",
        "Time_Spent_Minutes","Time_Spent_Formatted","Time_Spent_Flag",
        "CADNotes","CAD_Notes_Cleaned","CAD_Username","CAD_Timestamp",
        "CAD_Disposition","CAD_Response_Type"
      }
    )
in
    FinalColumns