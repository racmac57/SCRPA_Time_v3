Update the script to address the following errors:
==========================================
   SCRPA Data Processing Pipeline
   Author: R. A. Carucci
==========================================

≡ƒÉì Python version:
Python 3.13.5

Please select processing mode:

1. ≡ƒº¬ Test Mode (Validate setup)
2. ≡ƒöì Validation Mode (Check data quality)
3. ≡ƒÜÇ Full Processing Mode (Process latest exports)
4. ≡ƒôü Process Specific File
5. ≡ƒöä Process CAD Only
6. ≡ƒôè Process RMS Only
7. Γ¥î Exit

Enter your choice (1-7): 3

≡ƒÜÇ Running Full Processing Mode...
==========================================
2025-07-27 16:31:33,677 - MasterProcessor - INFO - Logging initialized: C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\03_output\logs\master_processing_20250727_163133.log
2025-07-27 16:31:33,677 - INFO - Logging initialized: C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\03_output\logs\master_processing_20250727_163133.log
2025-07-27 16:31:33,681 - MasterProcessor - INFO - Master SCRPA Processor initialized
2025-07-27 16:31:33,681 - INFO - Master SCRPA Processor initialized
Running full processing mode...
2025-07-27 16:31:33,685 - MasterProcessor - INFO - ========================================
2025-07-27 16:31:33,685 - INFO - ========================================
2025-07-27 16:31:33,687 - MasterProcessor - INFO - STARTING COMPLETE SCRPA PROCESSING PIPELINE
2025-07-27 16:31:33,687 - INFO - STARTING COMPLETE SCRPA PROCESSING PIPELINE
2025-07-27 16:31:33,688 - MasterProcessor - INFO - ========================================
2025-07-27 16:31:33,688 - INFO - ========================================
2025-07-27 16:31:33,689 - MasterProcessor - INFO - Step 1: Auto-detecting data source and loading data
2025-07-27 16:31:33,689 - INFO - Step 1: Auto-detecting data source and loading data
2025-07-27 16:31:33,690 - MasterProcessor - INFO - Searching for latest auto export files
2025-07-27 16:31:33,690 - INFO - Searching for latest auto export files
2025-07-27 16:31:33,692 - MasterProcessor - INFO - Latest CAD file: 2025_07_25_13_24_20_ALL_CADS.xlsx
2025-07-27 16:31:33,692 - INFO - Latest CAD file: 2025_07_25_13_24_20_ALL_CADS.xlsx
2025-07-27 16:31:33,693 - MasterProcessor - INFO - Loading latest export: 2025_07_25_13_24_20_ALL_CADS.xlsx
2025-07-27 16:31:33,693 - INFO - Loading latest export: 2025_07_25_13_24_20_ALL_CADS.xlsx
2025-07-27 16:31:33,844 - INFO - Detected CAD structure (score: 5/5)
2025-07-27 16:31:33,847 - MasterProcessor - WARNING - 112 null values in Time of Call (unexpected for CAD exports)
2025-07-27 16:31:33,847 - WARNING - 112 null values in Time of Call (unexpected for CAD exports)
2025-07-27 16:31:33,848 - MasterProcessor - INFO - Removed column: cYear
2025-07-27 16:31:33,848 - INFO - Removed column: cYear
2025-07-27 16:31:33,849 - MasterProcessor - INFO - Removed column: cMonth
2025-07-27 16:31:33,849 - INFO - Removed column: cMonth
2025-07-27 16:31:33,850 - MasterProcessor - INFO - Removed column: DayofWeek
2025-07-27 16:31:33,850 - INFO - Removed column: DayofWeek
2025-07-27 16:31:33,851 - MasterProcessor - INFO - Detected CAD structure with 112 records
2025-07-27 16:31:33,851 - INFO - Detected CAD structure with 112 records
2025-07-27 16:31:33,853 - MasterProcessor - INFO - Step 2: Processing CAD data structure
2025-07-27 16:31:33,853 - INFO - Step 2: Processing CAD data structure
2025-07-27 16:31:33,854 - MasterProcessor - INFO - Processing CAD structure (no unpivoting needed)
2025-07-27 16:31:33,854 - INFO - Processing CAD structure (no unpivoting needed)
--- Logging error ---
Traceback (most recent call last):
  File "C:\Python313\Lib\logging\__init__.py", line 1154, in emit
    stream.write(msg + self.terminator)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python313\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 64: character maps to <undefined>
Call stack:
  File "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts\master_scrpa_processor.py", line 1373, in <module>
    main()
  File "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts\master_scrpa_processor.py", line 1354, in main
    final_df, stats = processor.process_complete_pipeline(
  File "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts\master_scrpa_processor.py", line 646, in process_complete_pipeline
    processed_df = self.process_by_data_source(df, data_source)
  File "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts\master_scrpa_processor.py", line 748, in process_by_data_source
    return self.process_cad_structure(df)
  File "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts\master_scrpa_processor.py", line 760, in process_cad_structure
    prepared_df = self.data_validator.prepare_cad_data(df)
  File "C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\01_scripts\actual_structure_python_validation.py", line 144, in prepare_cad_data
    logging.info(f"CAD disposition filtering: {original_count} → {len(df_clean)} records")
Message: 'CAD disposition filtering: 112 → 112 records'
Arguments: ()
2025-07-27 16:31:33,856 - INFO - CAD disposition filtering: 112 → 112 records
2025-07-27 16:31:33,862 - INFO - CAD data prepared: 112 records ready for processing
2025-07-27 16:31:33,864 - MasterProcessor - ERROR - PIPELINE FAILED: 'MasterSCRPAProcessor' object has no attribute 'response_map'
2025-07-27 16:31:33,864 - ERROR - PIPELINE FAILED: 'MasterSCRPAProcessor' object has no attribute 'response_map'

Processing failed: 'MasterSCRPAProcessor' object has no attribute 'response_map'
Check the log files in: C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\03_output\logs

==========================================
Γ¥î ERROR: Processing failed with error code 1

≡ƒöì Check log files for details:
   C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\03_output\logs\

≡ƒô₧ Common issues:
   - Missing Python packages: pip install pandas openpyxl pathlib
   - Export files not found in CAD/RMS directories
   - Incorrect file permissions
