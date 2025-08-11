// 🕒 2025-08-05-Updated
// Query: TimeOfDaySort
// Updated to match the new time of day format from the script
let
    TimeOfDaySort = #table(
        type table [TimeOfDay = text, SortOrder = Int64.Type],
        {
            {"00:00-03:59 Early Morning", 1},
            {"04:00-07:59 Morning", 2},
            {"08:00-11:59 Morning Peak", 3},
            {"12:00-15:59 Afternoon", 4},
            {"16:00-19:59 Evening Peak", 5},
            {"20:00-23:59 Night", 6},
            {"Unknown", 99}
        }
    )
in
    TimeOfDaySort