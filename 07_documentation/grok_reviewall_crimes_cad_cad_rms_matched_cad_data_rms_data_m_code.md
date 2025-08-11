Master Data Quality Analysis for CAD_RMS_Matched, CAD_DATA, and ALL_CRIMES
This document consolidates the data quality analysis for three datasets: CAD_RMS_Matched, CAD_DATA, and ALL_CRIMES, based on the provided Power Query M code and Excel files (CAD_DATA.xlsx, ALL_CRIMES.xlsx). Each section includes a column list with five representative samples per column and a detailed data quality check addressing missing/null/empty values, unexpected formats or data types, and outliers or suspicious values. The analysis assumes CAD_RMS_Matched has 130 rows (from ALL_CRIMES, with 87 rows matched to CAD_DATA), CAD_DATA has 156 rows, and ALL_CRIMES has 130 rows (including one empty row).
1. CAD_RMS_Matched Dataset
Column List and Samples
The CAD_RMS_Matched dataset, defined by the Power Query M code, contains 61 columns, merging all unique columns from ALL_CRIMES (43 columns) and CAD_DATA (22 columns), with unified columns (Grid, Zone, Officer, Enhanced_Block) and derived columns (e.g., Has_CAD_Data). Samples are drawn from rows with both RMS and CAD data (e.g., rows 21, 28, 101, 122, 125 from ALL_CRIMES, corresponding to rows 25, 34, 122, 145, 150 in CAD_DATA), reflecting transformations like address enhancement and text normalization.



Column Name
Description (Inferred)
Sample 1
Sample 2
Sample 3
Sample 4
Sample 5



Case Number
Unique identifier from RMS, format "25-XXXXXX".
25-009657
25-013106
25-050281
25-058451
25-060143


ReportNumberNew
CAD report number, matches Case Number or null.
25-009657
25-013106
25-050281
25-058451
25-060143


Incident_Date
Derived date from RMS Incident Date, Incident Date_Between, or Report Date.
45691
45705
45826
45851
45855


Incident_Time
Derived time from RMS Incident Time, Incident Time_Between, or Report Time (decimal).
0.7708333333333334
0.39716435185185184
0.3854166666666667
0.5543865740740741
0.6875


Incident Date_Between
RMS incident range start date (Excel serial date).
45692
null
null
null
null


Incident Time_Between
RMS incident range start time (decimal).
0.7916666666666666
null
null
null
0.7083333333333334


Report Date
RMS report filing date (Excel serial date).
45692
45705
45826
45851
45856


Report Time
RMS report filing time (decimal).
0.5302314814814815
0.39716435185185184
0.4654166666666667
0.5543865740740741
0.6609375


Incident Type_1
RMS primary incident with legal code.
Motor Vehicle Theft - 2C:20-3
Motor Vehicle Theft - 2C:20-3
Burglary - Residence - 2C:18-2
Burglary - Residence - 2C:18-2
Robbery - 2C:15-1


Incident Type_2
RMS secondary incident (null if none).
null
null
null
null
null


Incident Type_3
RMS tertiary incident (null if none).
null
null
null
null
null


Enhanced_FullAddress
Unified address, prefers RMS_FullAddress unless missing/incomplete, then CAD_FullAddress.
55 Midtown Bridge Approach, Hackensack, NJ, 07601
30 Prospect Avenue, Hackensack, NJ, 07601
259 Park Street, Hackensack, NJ, 07601
210 Main Street, Hackensack, NJ, 07601
65 Court Street, Hackensack, NJ, 07601


RMS_FullAddress
Original RMS full address.
55 Midtown Bridge Approach, Hackensack, NJ, 07601
30 Prospect Avenue, Hackensack, NJ, 07601
259 Park Street, Hackensack, NJ, 07601
210 Main Street, Hackensack, NJ, 07601
65 Court Street, Hackensack, NJ, 07601


CAD_FullAddress
Original CAD full address (FullAddress2).
55 Midtown Bridge Approach, Hackensack, NJ, 07601
30 Prospect Avenue, Hackensack, NJ, 07601
259 Park Street, Hackensack, NJ, 07601
210 Main Street, Hackensack, NJ, 07601
65 Court Street, Hackensack, NJ, 07601


RMS_Grid
RMS grid code.
H1
G4
H2
H1
E1


CAD_Grid
CAD grid code.
H1
G4
H2
H1
E1


Grid
Unified grid, prefers CAD_Grid if non-null.
H1
G4
H2
H1
E1


RMS_Zone
RMS zone number.
8
7
8
8
5


CAD_Zone
CAD zone number (PDZone).
8
7
8
8
5


Zone
Unified zone, prefers CAD_Zone if non-null.
8
7
8
8
5


RMS_Narrative
RMS incident description.
I responded to the listed location on a reported motor vehicle theft...
On February 17, 2025 I responded to 300 Atlantic Street...
I responded to police headquarters on a report of a burglary...
I responded to the listed location on a reported burglary into a storage unit...
On July 18th, 2025 at approximately 15:30 hours...


CADNotes
Raw CAD notes with usernames/timestamps.
- antista_ma - 2/4/2025 12:44:03 PM
- deleon_a - 2/17/2025 9:35:46 AM
- knapp_j - 6/18/2025 11:10:12 AM
- sosa_c - 7/13/2025 1:19:16 PM
null


CAD_Notes_Cleaned
Cleaned CAD notes, proper-cased.
null
null
null
null
null


CAD_Username
Extracted CAD username, proper-cased.
Antista_Ma
Deleon_A
Knapp_J
Sosa_C
null


CAD_Timestamp
Extracted CAD timestamp (MM/dd/yyyy HH:mm:ss).
02/04/2025 12:44:03
02/17/2025 09:35:46
06/18/2025 11:10:12
07/13/2025 13:19:16
null


RMS_Total_Value_Stolen
RMS stolen value (USD).
null
null
null
1200
null


RMS_Total_Value_Recover
RMS recovered value (USD).
null
null
null
null
null


Registration 1
RMS first vehicle registration, upper-cased.
AM82732
Z53RVG
null
null
null


Make1
RMS first vehicle make, upper-cased.
RAM
HONDA
null
null
null


Model1
RMS first vehicle model, upper-cased.
PROMASTER
ACC
null
null
null


Reg State 1
RMS first vehicle state, upper-cased.
AZ
NJ
null
null
null


Registration 2
RMS second vehicle registration, upper-cased.
null
null
null
null
null


Make2
RMS second vehicle make, upper-cased.
null
null
null
null
null


Model2
RMS second vehicle model, upper-cased.
null
null
null
null
null


Reg State 2
RMS second vehicle state, upper-cased.
null
null
null
null
null


Reviewed By
RMS reviewer name/ID, proper-cased.
Deleon_A
Deleon_A
Knapp_J
Knapp_J
Dominguez_L


CompleteCalc
RMS status indicator.
Complete
Complete
Complete
Complete
Complete


RMS_Officer
RMS officer (title, name, ID).
P.O. Micah Gibson 365
P.O. Anzour Marza 356
P.O. Micah Gibson 365
P.O. Nart Marza 321
SPO. Aster Abueg 817


CAD_Officer
CAD officer (title, name, ID).
P.O. Micah Gibson 365
P.O. Anzour Marza 356
P.O. Micah Gibson 365
P.O. Nart Marza 321
SPO. Aster Abueg 817


Officer
Unified officer, prefers CAD_Officer.
P.O. Micah Gibson 365
P.O. Anzour Marza 356
P.O. Micah Gibson 365
P.O. Nart Marza 321
SPO. Aster Abueg 817


RMS_Squad
RMS squad assignment, upper-cased.
A3
A3
A4
A1
null


RMS_Det_Assigned
RMS assigned detective.
Det. Matthew DeBonis 325
Det. Demetrius Carroll 133
Det. Matthew Dogali 338
Det. Gunther Lara-Nunez 351
Det. Matthew DeBonis 325


RMS_Case_Status
RMS case status.
Complaint Signed
Active/Administratively Closed
Unfounded / Closed
Active Investigation
Active Investigation


RMS_NIBRS_Classification
RMS NIBRS code and description.
240 = Theft of Motor Vehicle
240 = Theft of Motor Vehicle
220 = Burglary/Breaking & Entering
null
null


RMS_TimeOfDay
RMS time period category.
16:00–19:59 Evening Peak
08:00–11:59 Morning Peak
08:00–11:59 Morning Peak
12:00–15:59 Afternoon
16:00–19:59 Evening Peak


RMS_TimeOfDay_SortOrder
RMS time period sort order (1–6).
5
3
3
4
5


RMS_Date_SortKey
RMS date sort key (YYYYMMDD).
20250203
20250217
20250618
20250713
20250717


RMS_Block
RMS block-level address.
Midtown Bridge Approach, 0 Block
Prospect Avenue, 0 Block
Park Street, 200 Block
Main Street, 200 Block
Court Street, 0 Block


CAD_Block
CAD block-level address.
Midtown Bridge Approach, 0 Block
Prospect Avenue, 0 Block
Park Street, 200 Block
Main Street, 200 Block
Court Street, 0 Block


Enhanced_Block
Block derived from Enhanced_FullAddress.
Midtown Bridge Approach, 0 Block
Prospect Avenue, 0 Block
Park Street, 200 Block
Main Street, 200 Block
Court Street, 0 Block


RMS_ALL_INCIDENTS
RMS comma-separated incident types.
Motor Vehicle Theft
Motor Vehicle Theft
Burglary - Residence
Burglary - Residence
Robbery


RMS_Vehicle_1
RMS first vehicle details.
AZ - AM82732, RAM/PROMASTER
NJ - Z53RVG, HONDA/ACC
null
null
null


RMS_Vehicle_2
RMS second vehicle details.
null
null
null
null
null


RMS_Vehicle_1_and_Vehicle_2
RMS combined vehicle details.
null
null
null
null
null


RMS_Period
RMS reporting period.
YTD
YTD
YTD
28-Day
7-Day


RMS_IncidentType
RMS simplified primary incident type.
Motor Vehicle Theft
Motor Vehicle Theft
Burglary - Residence
Burglary - Residence
Robbery


RMS_Crime_Category
RMS broader crime category.
Motor Vehicle Theft
Motor Vehicle Theft
Burglary – Commercial/Residence
Burglary – Commercial/Residence
Robbery


Has_CAD_Data
Flag for CAD data presence ("Yes" or "No").
Yes
Yes
Yes
Yes
Yes


Time_Response_Minutes
CAD response time in minutes (decimal).
40.55
7.15
23.17
25.05
2.9


Time_Response_Formatted
CAD formatted response time.
40 Mins 33 Secs
7 Mins 09 Secs
23 Mins 10 Secs
25 Mins 03 Secs
2 Mins 54 Secs


Time_Response_Flag
CAD response time category.
Over 10 Minutes
Normal
Over 10 Minutes
Over 10 Minutes
Normal


Time_Spent_Minutes
CAD time spent on scene (decimal).
67.43
63.85
55.48
66.92
51.95


Time_Spent_Formatted
CAD formatted time spent.
1 Hrs 07 Mins
1 Hrs 04 Mins
55 Mins
1 Hrs 07 Mins
52 Mins


Time_Spent_Flag
CAD time spent category.
Normal
Normal
Normal
Normal
Normal


CAD_How_Reported
CAD reporting method.
Phone
Phone
Phone
Phone
Walk-In


CAD_Time_of_Call
CAD call timestamp (Excel serial date).
45692.53023148148
45705.39716435185
45826.46486111111
45851.55438657408
45856.6609375


CAD_cYear
CAD incident year.
2025
2025
2025
2025
2025


CAD_cMonth
CAD incident month.
February
February
June
July
July


CAD_HourMinuetsCalc
CAD incident time (decimal).
0.5298611111111111
0.39652777777777776
0.46458333333333335
0.5541666666666667
0.6604166666666667


CAD_DayofWeek
CAD day of the week.
Tuesday
Monday
Wednesday
Sunday
Friday


CAD_Time_Dispatched
CAD dispatch timestamp (Excel serial date).
45692.558391203704
45705.40212962963
45826.48094907407
45851.57178240741
45856.66295138889


CAD_Time_Out
CAD officer departure timestamp (Excel serial date).
45692.56013888889
45705.4047337963
45826.481944444444
45851.57775462963
45856.67564814815


CAD_Time_In
CAD officer arrival timestamp (Excel serial date).
45692.60696759259
45705.44907407407
45826.520474537036
45851.62422453704
45856.71172453704


CAD_Time_Spent
CAD time spent (Excel time format).
12/31/1899 1:07:26 AM
12/31/1899 1:03:51 AM
12/31/1899 12:55:29 AM
12/31/1899 1:06:55 AM
12/31/1899 12:51:57 AM


CAD_Time_Response
CAD response time (Excel time format).
12/31/1899 12:43:04 AM
12/31/1899 12:10:54 AM
12/31/1899 12:24:36 AM
12/31/1899 12:33:39 AM
12/31/1899 12:21:11 AM


CAD_Disposition
CAD outcome.
See Report
Complete
See Report
See Report
See Report


CAD_Response_Type
CAD response type ("Routine", "Emergency").
Routine
Routine
Emergency
Emergency
Emergency


Data Quality Check for CAD_RMS_Matched

Missing/Null/Empty Values:
Low Null Counts: Case Number, Incident_Date, Incident_Time, RMS_Grid, RMS_Zone, RMS_Squad, RMS_Det_Assigned (0.77–3.08% null).
Moderate Null Counts: ReportNumberNew, CAD_FullAddress, CAD_Grid, CAD_Zone, CAD_Officer, CAD_Time_of_Call, CAD_cYear, CAD_cMonth, CAD_HourMinuetsCalc, CAD_DayofWeek, CAD_Time_Dispatched, CAD_Time_Out, CAD_Time_In, CAD_Time_Spent, CAD_Time_Response, CAD_Disposition (33.08% null for 43 RMS-only rows), CAD_How_Reported, CAD_Response_Type (38.46% null, including 7 CAD rows), CADNotes, CAD_Username, CAD_Timestamp (59.23% null, including 34 CAD rows), Time_Response_Minutes, Time_Response_Formatted, Time_Response_Flag, Time_Spent_Minutes, Time_Spent_Formatted, Time_Spent_Flag (47.69% null, including 19 CAD rows with zero times).
High Null Counts: Incident Date_Between (67.69%), Incident Time_Between (69.23%), Incident Type_2 (65.38%), Incident Type_3 (88.46%), RMS_Total_Value_Stolen (74.62%), RMS_Total_Value_Recover (100%), Registration 1/Make1/Model1/Reg State 1 (70.77%), Registration 2/Make2/Model2/Reg State 2, RMS_Vehicle_1, RMS_Vehicle_2, RMS_Vehicle_1_and_Vehicle_2 (99.23%), CAD_Notes_Cleaned (~76.92%, due to sparse CAD notes).


Unexpected Formats or Data Types:
RMS_FullAddress: Row 120 ("Charles Street & , Hackensack, NJ, 07601") is incomplete, resolved by Enhanced_FullAddress.
RMS_Block: Row 120 ("Incomplete Address - Check Location Data") is non-standard, resolved by Enhanced_Block.
Make1: Row 24 has string "null" instead of empty/null, affecting RMS_Vehicle_1.
CAD_How_Reported: "37135" in 45 CAD rows (28.85% of CAD_DATA) resembles an Excel serial date, likely an import error.
All other columns align with expected types: strings (text fields), integers (dates, zones), decimals (times), Excel time format (CAD time fields).


Outliers or Suspicious Values:
RMS_Total_Value_Stolen: Outliers: $400,000 (row 130, luxury vehicle), $17,000 (row 4, tools) (mean: 2860.61, std dev: 6969.14, threshold >21,777.56).
RMS_Total_Value_Recover: 100% null, suspicious if recovery data expected.
Time_Response_Minutes: Outliers: 323.33 (row 90), 86.55 (row 112) (mean: 8.92, std dev: 14.56, threshold >52.6).
Time_Spent_Minutes: Outliers: 479.02 (row 149), 245.5 (row 140) (mean: 47.38, std dev: 59.87, threshold >226.99).
CAD_Time_Dispatched/Out/In: Identical timestamps in some rows (e.g., row 114) indicate incomplete data for canceled calls.
Row 107: Entirely empty, a significant data entry error.
Row 120: Incomplete RMS_FullAddress/RMS_Block, resolved by CAD data.



2. CAD_DATA Dataset
Column List and Samples
The CAD_DATA.xlsx dataset contains 22 columns and 156 rows, capturing CAD system data such as incident details, officer assignments, and response times. Samples are drawn from rows 25, 34, 122, 145, and 150.



Column Name
Description (Inferred)
Sample 1
Sample 2
Sample 3
Sample 4
Sample 5



ReportNumberNew
Report identifier, format "25-XXXXXX".
25-009657
25-013106
25-050281
25-058451
25-060143


Incident
Incident type with legal code.
Motor Vehicle Theft - 2C:20-3
Motor Vehicle Theft - 2C:20-3
Burglary - Residence - 2C:18-2
Burglary - Residence - 2C:18-2
Robbery - 2C:15-1


How Reported
Reporting method (e.g., Phone, Walk-In).
Phone
Phone
Phone
Phone
Walk-In


FullAddress2
Full address (street, city, ZIP).
55 Midtown Bridge Approach, Hackensack, NJ, 07601
30 Prospect Avenue, Hackensack, NJ, 07601
259 Park Street, Hackensack, NJ, 07601
210 Main Street, Hackensack, NJ, 07601
65 Court Street, Hackensack, NJ, 07601


PDZone
Police zone number.
8
7
8
8
5


Grid
Grid location code.
H1
G4
H2
H1
E1


Time of Call
Call timestamp (Excel serial date).
45692.53023148148
45705.39716435185
45826.46486111111
45851.55438657408
45856.6609375


cYear
Incident year.
2025
2025
2025
2025
2025


cMonth
Incident month.
February
February
June
July
July


HourMinuetsCalc
Incident time (decimal).
0.5298611111111111
0.39652777777777776
0.46458333333333335
0.5541666666666667
0.6604166666666667


DayofWeek
Day of the week.
Tuesday
Monday
Wednesday
Sunday
Friday


Time Dispatched
Dispatch timestamp (Excel serial date).
45692.558391203704
45705.40212962963
45826.48094907407
45851.57178240741
45856.66295138889


Time Out
Officer departure timestamp (Excel serial date).
45692.56013888889
45705.4047337963
45826.481944444444
45851.57775462963
45856.67564814815


Time In
Officer arrival timestamp (Excel serial date).
45692.60696759259
45705.44907407407
45826.520474537036
45851.62422453704
45856.71172453704


Time Spent
Time spent on scene (Excel time format).
12/31/1899 1:07:26 AM
12/31/1899 1:03:51 AM
12/31/1899 12:55:29 AM
12/31/1899 1:06:55 AM
12/31/1899 12:51:57 AM


Time Response
Response time (Excel time format).
12/31/1899 12:43:04 AM
12/31/1899 12:10:54 AM
12/31/1899 12:24:36 AM
12/31/1899 12:33:39 AM
12/31/1899 12:21:11 AM


Officer
Assigned officer (title, name, ID).
P.O. Micah Gibson 365
P.O. Anzour Marza 356
P.O. Micah Gibson 365
P.O. Nart Marza 321
SPO. Aster Abueg 817


Disposition
Incident outcome (e.g., See Report).
See Report
Complete
See Report
See Report
See Report


Response Type
Response type (Routine, Emergency).
Routine
Routine
Emergency
Emergency
Emergency


CADNotes
Raw CAD notes with usernames/timestamps.
- antista_ma - 2/4/2025 12:44:03 PM
- deleon_a - 2/17/2025 9:35:46 AM
- knapp_j - 6/18/2025 11:10:12 AM
- sosa_c - 7/13/2025 1:19:16 PM
null


Time_Response_Minutes
Response time in minutes (decimal).
40.55
7.15
23.17
25.05
2.9


Time_Spent_Minutes
Time spent on scene in minutes (decimal).
67.43
63.85
55.48
66.92
51.95


Block
Block-level address.
Midtown Bridge Approach, 0 Block
Prospect Avenue, 0 Block
Park Street, 200 Block
Main Street, 200 Block
Court Street, 0 Block


Data Quality Check for CAD_DATA

Missing/Null/Empty Values:
All columns are complete except:
PDZone, Grid: 26 nulls each (16.67%), aligning with incomplete location data.
Response Type: 7 nulls (4.49%), mostly in early rows.
CADNotes: 34 nulls (21.79%), expected when no notes are recorded.
Time_Response_Minutes, Time_Spent_Minutes: 19 zeros each (12.18%), aligning with "Canceled" dispositions.




Unexpected Formats or Data Types:
How Reported: "37135" in 45 rows (28.85%) resembles an Excel serial date, likely an import error. Expected values: "Phone", "Walk-In", "Radio", "Other - See Notes".
All other columns align with expected types: strings (e.g., Incident, Officer), integers (cYear), decimals (time fields), Excel time format (Time Spent, Time Response).


Outliers or Suspicious Values:
Time_Response_Minutes: Outliers: 323.33 (row 90), 86.55 (row 112) (mean: 8.92, std dev: 14.56, threshold >52.6). Zeros (19 rows) align with "Canceled" calls.
Time_Spent_Minutes: Outliers: 479.02 (row 149), 245.5 (row 140) (mean: 47.38, std dev: 59.87, threshold >226.99). Zeros (19 rows) align with "Canceled" calls.
Time Dispatched/Out/In: Identical timestamps in some rows (e.g., row 114) indicate incomplete data for canceled calls.
How Reported: "37135" is a clear error, not a valid reporting method.



3. ALL_CRIMES Dataset
Column List and Samples
The ALL_CRIMES.xlsx dataset contains 43 columns and 130 rows, capturing RMS data such as incident details, vehicle information, and case statuses. Samples are drawn from rows 21, 28, 101, 122, and 125.



Column Name
Description (Inferred)
Sample 1
Sample 2
Sample 3
Sample 4
Sample 5



Case Number
Unique identifier, format "25-XXXXXX".
25-009657
25-013106
25-050281
25-058451
25-060143


Incident Date
Incident date (Excel serial date).
45691
45705
45826
45851
45855


Incident Time
Incident time (decimal).
0.7708333333333334
0.39716435185185184
0.3854166666666667
0.5543865740740741
0.6875


Incident Date_Between
Incident range start date (Excel serial date).
45692
null
null
null
null


Incident Time_Between
Incident range start time (decimal).
0.7916666666666666
null
null
null
0.7083333333333334


Report Date
Report filing date (Excel serial date).
45692
45705
45826
45851
45856


Report Time
Report filing time (decimal).
0.5302314814814815
0.39716435185185184
0.4654166666666667
0.5543865740740741
0.6609375


Incident Type_1
Primary incident with legal code.
Motor Vehicle Theft - 2C:20-3
Motor Vehicle Theft - 2C:20-3
Burglary - Residence - 2C:18-2
Burglary - Residence - 2C:18-2
Robbery - 2C:15-1


Incident Type_2
Secondary incident (null if none).
null
null
null
null
null


Incident Type_3
Tertiary incident (null if none).
null
null
null
null
null


FullAddress
Full address (street, city, ZIP).
55 Midtown Bridge Approach, Hackensack, NJ, 07601
30 Prospect Avenue, Hackensack, NJ, 07601
259 Park Street, Hackensack, NJ, 07601
210 Main Street, Hackensack, NJ, 07601
65 Court Street, Hackensack, NJ, 07601


Grid
Grid code.
H1
G4
H2
H1
E1


Zone
Zone number.
8
7
8
8
5


Narrative
Incident description.
I responded to the listed location on a reported motor vehicle theft...
On February 17, 2025 I responded to 300 Atlantic Street...
I responded to police headquarters on a report of a burglary...
I responded to the listed location on a reported burglary into a storage unit...
On July 18th, 2025 at approximately 15:30 hours...


Total Value Stolen
Stolen value (USD).
null
null
null
1200
null


Total Value Recover
Recovered value (USD).
null
null
null
null
null


Registration 1
First vehicle registration.
AM82732
Z53RVG
null
null
null


Make1
First vehicle make.
RAM
HONDA
null
null
null


Model1
First vehicle model.
PROMASTER
ACC
null
null
null


Reg State 1
First vehicle registration state.
AZ
NJ
null
null
null


Registration 2
Second vehicle registration.
null
null
null
null
null


Reg State 2
Second vehicle registration state.
null
null
null
null
null


Make2
Second vehicle make.
null
null
null
null
null


Model2
Second vehicle model.
null
null
null
null
null


Reviewed By
Reviewer name/ID.
Deleon_A
Deleon_A
Knapp_J
Knapp_J
Dominguez_L


CompleteCalc
Status indicator.
Complete
Complete
Complete
Complete
Complete


Officer of Record
Officer (title, name, ID).
P.O. Micah Gibson 365
P.O. Anzour Marza 356
P.O. Micah Gibson 365
P.O. Nart Marza 321
SPO. Aster Abueg 817


Squad
Squad assignment.
A3
A3
A4
A1
null


Det_Assigned
Assigned detective.
Det. Matthew DeBonis 325
Det. Demetrius Carroll 133
Det. Matthew Dogali 338
Det. Gunther Lara-Nunez 351
Det. Matthew DeBonis 325


Case_Status
Case status.
Complaint Signed
Active/Administratively Closed
Unfounded / Closed
Active Investigation
Active Investigation


NIBRS Classification
NIBRS code and description.
240 = Theft of Motor Vehicle
240 = Theft of Motor Vehicle
220 = Burglary/Breaking & Entering
null
null


Incident_Date
Duplicate incident date (Excel serial date).
45691
45705
45826
45851
45855


Incident_Time
Duplicate incident time (decimal).
0.7708333333333334
0.39716435185185184
0.3854166666666667
0.5543865740740741
0.6875


TimeOfDay
Time period category.
16:00–19:59 Evening Peak
08:00–11:59 Morning Peak
08:00–11:59 Morning Peak
12:00–15:59 Afternoon
16:00–19:59 Evening Peak


TimeOfDay_SortOrder
Time period sort order (1–6).
5
3
3
4
5


Date_SortKey
Date sort key (YYYYMMDD).
20250203
20250217
20250618
20250713
20250717


Block
Block-level address.
Midtown Bridge Approach, 0 Block
Prospect Avenue, 0 Block
Park Street, 200 Block
Main Street, 200 Block
Court Street, 0 Block


ALL_INCIDENTS
Comma-separated incident types.
Motor Vehicle Theft
Motor Vehicle Theft
Burglary - Residence
Burglary - Residence
Robbery


Vehicle_1
First vehicle details.
AZ - AM82732, RAM/PROMASTER
NJ - Z53RVG, HONDA/ACC
null
null
null


Vehicle_2
Second vehicle details.
null
null
null
null
null


Vehicle_1_and_Vehicle_2
Combined vehicle details.
null
null
null
null
null


Period
Reporting period (YTD, 28-Day, 7-Day).
YTD
YTD
YTD
28-Day
7-Day


IncidentType
Simplified primary incident type.
Motor Vehicle Theft
Motor Vehicle Theft
Burglary - Residence
Burglary - Residence
Robbery


Crime_Category
Broader crime category.
Motor Vehicle Theft
Motor Vehicle Theft
Burglary – Commercial/Residence
Burglary – Commercial/Residence
Robbery


Data Quality Check for ALL_CRIMES

Missing/Null/Empty Values:
Low Null Counts: Case Number, Incident Date, Incident_Time, Grid, Squad, Det_Assigned (0.77% null, row 107 or 125), Zone (3.08%, rows 103, 120, 127–129).
High Null Counts: Incident Date_Between (67.69%), Incident Time_Between (69.23%), Incident Type_2 (65.38%), Incident Type_3 (88.46%), Total Value Stolen (74.62%), Total Value Recover (100%), Registration 1/Make1/Model1/Reg State 1 (70.77%), Registration 2/Make2/Model2/Reg State 2, Vehicle_1, Vehicle_2, Vehicle_1_and_Vehicle_2 (99.23%), NIBRS Classification (27.69%, rows 94–104, 109–131).


Unexpected Formats or Data Types:
FullAddress: Row 120 ("Charles Street & , Hackensack, NJ, 07601") is incomplete.
Block: Row 120 ("Incomplete Address - Check Location Data") is non-standard.
Make1: Row 24 has string "null" instead of empty/null, affecting Vehicle_1.
All other columns align with expected types: strings (text fields), integers (dates, zones), decimals (times).


Outliers or Suspicious Values:
Total Value Stolen: Outliers: $400,000 (row 130), $17,000 (row 4) (mean: 2860.61, std dev: 6969.14, threshold >21,777.56).
Total Value Recover: 100% null, suspicious if recovery data expected.
Row 107: Entirely empty, a significant data entry error.
Row 120: Incomplete FullAddress and Block are suspicious, resolved in CAD_RMS_Matched by CAD data.



Summary

CAD_RMS_Matched: Combines 61 columns, effectively unifying overlapping fields (Grid, Zone, Officer) and enhancing addresses (Enhanced_FullAddress, Enhanced_Block). Key issues: row 107 (empty), row 120 (incomplete address), "37135" in CAD_How_Reported, high null counts in vehicle and recovery fields, and outliers in time/value fields.
CAD_DATA: 22 columns, with issues in "37135" for How Reported, high nulls in PDZone/Grid (16.67%) and CADNotes (21.79%), and outliers in time fields.
ALL_CRIMES: 43 columns, with issues in row 107 (empty), row 120 (incomplete address), "null" in Make1 (row 24), and high null counts in vehicle/recovery fields.
Common Issues: Row 107's emptiness, row 120's incomplete address (resolved in CAD_RMS_Matched), and "37135" in CAD_How_Reported suggest data entry/import errors. Outliers in time/value fields are plausible but extreme, warranting review.
