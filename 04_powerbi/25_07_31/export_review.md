rms_data_standardized.csv
1. column headers are not lower case
2. incident_time is not hh:mm
3. time_of_day has character encoding mismatch
4. Location column has incorrect locations example: 128 Christopher Columbus Drive, Jersey City, NJ 07302, Hackensack, NJ, 07601
5. Grid and Post were not backfilled to add missing values fro the zone_grid_master.xlsx refrence
6. I think we should remove Incident_Type column.  This column should only be added to the CAD data. Once in the CAD data it can be combined with the rms data cad_rms_matched_standardized.csv
7. remove Crime_Category for the same reason as Incident_type.  it can be added to the cad_rms_matched_standardized.csv
8. Squad, Vehicle_1, Vehicle_2, and Vehicle_1_And_Vehicle_2 are not all capitalized as they should be.

all_crimes_standardized.csv
same issues and edits as rms_data_standardized.csv

cad_data_standardized.csv
1. the script should be pulling the most recent data from C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA. It appears that its pulling from C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD.
2. column headers are not lower case
3. Response_Type and Category Type (which is not in this file as it should be), should be mapped according to "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\10_Refrence_Files\CallType_Categories.xlsx" I found the issue the column "Incident" the raw CAD export in not in the file.
4. How_Reported is incorrectily showing 9-1-1 as a date.
5. Grid and Post columns are blank, is this due to changing the name of "PDZone" in the raw cad export to "Post"?
6. Time_Spent_Minutes and Time_Response_Minutes are missing the formatted version of the columns. Where Time_Spent_Minutes should be 0 Hrs. 00 Mins and time_response should be 00 Mins. 00 Secs.
7. CAD_Notes_Cleaned still has the username and the timestamp in the notes
8. missing username, timestamp columns 

cad_rms_matched_standardized.csv
1. why does this table have 300 records when the rms had 135? Is it due to unpivoting?
2. Column headers are not lower case
3. incident_time needs to be hh:mm
4. time_of_day has character encoding mismatch 
5. Grid and Post have missing values
6. Incident_Type is incorrect most likley due to taking the rms version of this column where the script is confussed as to which column (Incident Type_1, Incident Type_2, Incident Type_3) to use.  That is why the column should not be made in the RMS data only in the CAD.  the same is true for Response_Type.
7. I am unsure what Crime_Category is from. the coulmn should be Category Type and made from the cad export.
8. Squad, Vehicle_1, Vehicle_2, and Vehicle_1_And_Vehicle_2 are not all capitalized as they should be.
9. Response_Type_CAD and How_Reported_CAD are all null.
10. Grid_CAD and Post_CAD are all null
11. CAD_Notes_Cleaned_CAD has the username and time stampts. be sure to clean, trim and fix line breaks.
12. Time_Response_CAD should most likly be the formatted version of time_response 00 mins 00 secs
13. Time_Spent column is all "0"
14. Time_Response_Formatted is formatted 13.5 mins
shpuld be 00 mins 00 secs

