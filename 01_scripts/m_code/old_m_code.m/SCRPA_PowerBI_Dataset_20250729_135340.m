let
    Source = Csv.Document(File.Contents("C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\SCRPA_ArcPy\06_Output\SCRPA_PowerBI_Dataset_20250729_135340.csv"),[Delimiter=",", Columns=18, Encoding=1252, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"ReportDate", type datetime}, {"CrimeType", type text}, {"Zone", type text}, {"Address", type text}, {"ReportNumber", type text}, {"Disposition", type text}, {"Hour", Int64.Type}, {"DayName", type text}, {"IsCleared", type logical}, {"Year", Int64.Type}, {"Month", Int64.Type}, {"MonthName", type text}, {"Quarter", Int64.Type}, {"WeekOfYear", Int64.Type}, {"DayOfMonth", Int64.Type}, {"DayOfYear", Int64.Type}, {"TimeCategory", type text}, {"CrimeCategory", type text}})
in
    #"Changed Type"