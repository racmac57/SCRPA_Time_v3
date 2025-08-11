 import pandas as pd
  import numpy as np
  import logging
  import sys
  import argparse
  from pathlib import Path
  from datetime import datetime, timedelta
  from typing import Dict, List, Optional, Tuple, Union
  import warnings
  warnings.filterwarnings('ignore')

  # Import your existing validation and processing modules
  try:
      from actual_structure_python_validation import SCRPAActualDataValidator, DataSource
      from enhanced_cadnotes_processor import EnhancedCADNotesProcessor
      from unified_data_processor import UnifiedDataProcessor
      # Added the missing requests import
      import requests
  except ImportError as e:
      print(f"WARNING Import error: {e}")
      print("Make sure all your existing scripts are in the same directory")

  class MasterSCRPAProcessor:
      """
      Master processor that integrates all your existing scripts into a complete
      pipeline that replaces your complex Power BI M Code.
      """

      def __init__(self, project_path: str = None):
          """Initialize master processor with your actual export directory structure."""

          if project_path is None:
              self.project_path = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2")
          else:
              self.project_path = Path(project_path)

          # Your actual export directories
          self.export_dirs = {
              'cad_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_CAD\SCRPA"),
              'rms_exports': Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\05_EXPORTS\_RMS\SCRPA")
          }

          # Setup directory structure
          self.setup_directories()

          # Initialize logging
          self.setup_logging()

          # Initialize component processors
          self.data_validator = SCRPAActualDataValidator(str(self.project_path))
          self.cadnotes_processor = EnhancedCADNotesProcessor()

          # Processing statistics
          self.stats = {
              'processing_start_time': None,
              'data_source_detected': None,
              'total_input_records': 0,
              'total_output_records': 0,
              'cadnotes_processed': 0,
              'quality_score_avg': 0.0,
              'processing_duration': 0.0,
              'errors_encountered': []
          }

          # Category and Response Type mappings from CallType_Categories.xlsx
          self.category_map = {
              '1': 'Miscellaneous',
              '9-1-1 Call': 'Emergency Response',
              'A.C.O.R.N. Test': 'Administrative and Support',
              'A.T.R.A.': 'Special Operations and Tactical',
              'ABC Advisory Check': 'Regulatory and Ordinance',
              'ABC Inspection': 'Regulatory and Ordinance',
              'ABC Liquor License Applicant': 'Administrative and Support',
              'ABC Violation': 'Regulatory and Ordinance',
              'ALPR Analysis': 'Investigations and Follow-Ups',
              'ALPR Flag': 'Investigations and Follow-Ups',
              'Abandoned 9-1-1 Emergency': 'Emergency Response',
              'Abandoned 9-1-1Emergency': 'Miscellaneous',
              'Abandoned Auto': 'Traffic and Motor Vehicle',
              'Academy Assignment': 'Administrative and Support',
              'Active/Administratively Closed': 'Administrative and Support',
              'Administrative Assignment': 'Administrative and Support',
              'Aggravated Assault - 2C:12-1b': 'Criminal Incidents',
              'Aggravated Assault 2C:12-1b': 'Criminal Investigation',
              'Aggravated Sexual Assault - 2C:14-2a': 'Criminal Incidents',
              'Aiding Suicide - 2C:11-6': 'Criminal Incidents',
              'Alarm - Burglar': 'Emergency Response',
              'Alarm - Fire': 'Emergency Response',
              'Alarm - Other': 'Public Safety and Welfare',
              'Alarm - Panic': 'Emergency Response',
              'Alarm Ordinance': 'Regulatory and Ordinance',
              'Alcohol/School Property - 2C:33-16': 'Criminal Incidents',
              'Alcoholic Beverage - Hours of Sale': 'Regulatory and Ordinance',
              'Alcoholic Beverage - New Years Day Hours of Sale': 'Regulatory and Ordinance',
              'Alcoholic Beverage - Serving Underage': 'Regulatory and Ordinance',
              'Alcoholic Beverage - Sunday Hours of Sale': 'Regulatory and Ordinance',
              'Alcoholic Beverage - Unlicensed Bartender': 'Regulatory and Ordinance',
              'Animal Bite Incident': 'Public Safety and Welfare',
              'Animal Complaint': 'Regulatory and Ordinance',
              'Animal Cruelty': 'Regulatory and Ordinance',
              'Annoying Phone Calls - 2C:33-4a': 'Criminal Incidents',
              'Applicant ABC License': 'Administrative and Support',
              'Applicant AD Material License': 'Administrative and Support',
              'Applicant All Others': 'Administrative and Support',
              'Applicant City Employee': 'Administrative and Support',
              'Applicant Concealed Carry': 'Administrative and Support',
              'Applicant Firearm(s)': 'Administrative and Support',
              'Applicant Handicapped Permit': 'Administrative and Support',
              'Applicant Ice Cream Vendor': 'Administrative and Support',
              'Applicant Jewelry': 'Administrative and Support',
              'Applicant Landscaper': 'Administrative and Support',
              'Applicant Limo': 'Administrative and Support',
              'Applicant Peddling License': 'Administrative and Support',
              'Applicant Pistol Permit': 'Administrative and Support',
              'Applicant Police Auxiliary': 'Administrative and Support',
              'Applicant Police Officer': 'Administrative and Support',
              'Applicant Snow Removal': 'Administrative and Support',
              'Applicant Solicitor': 'Administrative and Support',
              'Applicant Spa Therapy': 'Administrative and Support',
              'Applicant Taxi': 'Administrative and Support',
              'Applicant Towing': 'Administrative and Support',
              'Applicant Vending License': 'Administrative and Support',
              'Arrest Process': 'Criminal Incidents',
              'Arrest and JV Complaints': 'Criminal Incidents',
              'Arson - 2C:17-1': 'Criminal Incidents',
              'Arson 2C:17-1': 'Criminal Investigation',
              'Assist Motorist': 'Assistance and Mutual Aid',
              'Assist Other Agency': 'Assistance and Mutual Aid',
              'Assist Own Agency (Backup)': 'Assistance and Mutual Aid',
              'Attempted Burglary - 2C:18-2': 'Criminal Incidents',
              'Attempted Burglary 2C:18-2': 'Criminal Investigation',
              'Aviation Accident': 'Emergency Response',
              'BOLO': 'Investigations and Follow-Ups',
              'Background Checks': 'Administrative and Support',
              'Bad Checks - 2C:21-5': 'Criminal Incidents',
              'Bad Checks 2C:21-5': 'Patrol and Prevention',
              'Bias Incident': 'Criminal Incidents',
              'Blocked Driveway': 'Traffic and Motor Vehicle',
              'Boating Incident': 'Public Safety and Welfare',
              'Bomb Scare': 'Emergency Response',
              'Breath Test - Refusal - 39:4-50.2': 'Traffic and Motor Vehicle',
              'Bribery - 2C:27-2': 'Criminal Incidents',
              'Burglar Tools - 2C:5-5': 'Criminal Incidents',
              'Burglary 2C:18-2': 'Criminal Investigation',
              'Burglary - Auto - 2C:18-2': 'Criminal Incidents',
              'Burglary - Commercial - 2C:18-2': 'Criminal Incidents',
              'Burglary - Commercial 2C: 18-2': 'Criminal Investigation',
              'Burglary - Residence - 2C:18-2': 'Criminal Incidents',
              'Burglary - Residence 2C:18-2': 'Criminal Investigation',
              'CCH / III Request': 'Administrative and Support',
              'CDS/Dist.; School Property - 2C:35-7': 'Criminal Incidents',
              'CDS/Distribution - 2C:35-5': 'Criminal Incidents',
              'CDS/Employing Juvenile - 2C:35-6': 'Juvenile-Related Incidents',
              'CDS/Possession: Influence 2C:35-10': 'Miscellaneous',
              'CDS/Possession: Influence - 2C:35-10': 'Criminal Incidents',
              'CDS: Obtain by Fraud - 2C:35-13': 'Criminal Incidents',
              'Canceled Call': 'Administrative and Support',
              'Canvassing / Peddling Permit': 'Administrative and Support',
              'Canvassing without Permit': 'Regulatory and Ordinance',
              'Car Seat Installation': 'Community Engagement',
              'Car Wash': 'Administrative and Support',
              'Carjacking 2C:15-2': 'Criminal Investigation',
              'Carjacking - 2C:15-2': 'Criminal Incidents',
              'Catalytic Converter Theft': 'Criminal Incidents',
              'Checked Road Conditions (Weather)': 'Traffic and Motor Vehicle',
              'Child Abuse - Title 9': 'Juvenile-Related Incidents',
              'Child Custody Dispute': 'Public Safety and Welfare',
              'Church Crossing': 'Community Engagement',
              'City Ordinance': 'Regulatory and Ordinance',
              'City Ordinance Warning': 'Regulatory and Ordinance',
              'Civil Defense Test': 'Administrative and Support',
              'Cleared-Arrest': 'Criminal Incidents',
              'Code Blue': 'Public Safety and Welfare',
              'Coffee Break': 'Administrative and Support',
              'Community Engagement - Community Policing': 'Community Engagement',
              'Community Engagement - Crime Prevention': 'Community Engagement',
              'Community Engagement - Crisis Intervention': 'Community Engagement',
              'Community Engagement - Emergency Response': 'Community Engagement',
              'Community Engagement - Online Engagement': 'Community Engagement',
              'Community Engagement - Public Education': 'Community Engagement',
              'Community Engagement - School Outreach': 'Community Engagement',
              'Community Engagement - Traffic Safety': 'Community Engagement',
              'Community Engagement - Victim Support': 'Community Engagement',
              'Compensation - 2C:27-4': 'Criminal Incidents',
              'Compensation/Public Servant - 2C:27-7': 'Criminal Incidents',
              'Complaint Signed': 'Criminal Incidents',
              'Compounding - 2C:29-4': 'Criminal Incidents',
              'Compulsory School Attend. - Title 18A:38-2': 'Juvenile-Related Incidents',
              'Computer Issue - Desktop': 'Administrative and Support',
              'Computer Issue - Vehicle': 'Administrative and Support',
              'Conditional Dismissal Process': 'Administrative and Support',
              'Conspiracy - 2C:5-2': 'Criminal Incidents',
              'Constable - Secured Park Facilities': 'Public Safety and Welfare',
              'Construction Hours': 'Regulatory and Ordinance',
              'Contempt of Court - 2C:29-9': 'Criminal Incidents',
              'Controlled Buy': 'Special Operations and Tactical',
              'Controlled CDS Purchase': 'Special Operations and Tactical',
              'Cooperative Arrest - Little Ferry': 'Assistance and Mutual Aid',
              'Cooperative Arrest - Maywood': 'Assistance and Mutual Aid',
              'Cooperative Arrest - Ridgefield Park': 'Assistance and Mutual Aid',
              'Cooperative Arrest - So. Hackensack': 'Assistance and Mutual Aid',
              'Counterfeit Money': 'Criminal Incidents',
              'Court - Federal': 'Administrative and Support',
              'Court - Municipal': 'Administrative and Support',
              'Court - Municipal Prisoner': 'Administrative and Support',
              'Court - Other Municipality': 'Administrative and Support',
              'Court - Superior': 'Administrative and Support',
              'Court Officer': 'Administrative and Support',
              'Court Order': 'Administrative and Support',
              'Courtesy Transport': 'Assistance and Mutual Aid',
              'Creating a Hazard - 2C:40-1': 'Criminal Incidents',
              'Credit Cards - Unlawful Use 2C:21-6': 'Miscellaneous',
              'Credit Cards - Unlawful Use - 2C:21-6': 'Criminal Incidents',
              'Credit Practices - 2C:21-19': 'Criminal Incidents',
              'Criminal Attempt - 2C:5-1': 'Criminal Incidents',
              'Criminal Coercion - 2C:13-5': 'Criminal Incidents',
              'Criminal Homicide - 2C:11-2': 'Criminal Incidents',
              'Criminal Mischief 2C:17-3': 'Criminal Investigation',
              'Criminal Mischief - 2C:17-3': 'Criminal Incidents',
              'Criminal Mischief - Graffiti - 2C:17-3': 'Criminal Incidents',
              'Criminal Mischief - Park - 2C:17-3': 'Criminal Incidents',
              'Criminal Mischief - School - 2C:17-3': 'Criminal Incidents',
              'Criminal Mischief - Vehicle - 2C:17-3': 'Criminal Incidents',
              'Criminal Restraint - 2C:13-2': 'Criminal Incidents',
              'Criminal Sexual Contact 2C:14-3a': 'Miscellaneous',
              'Criminal Sexual Contact - 2C:14-3a': 'Criminal Incidents',
              'Criminal Simulation - 2C:21-2': 'Criminal Incidents',
              'Criminal Trespass 2C:18-3': 'Miscellaneous',
              'Criminal Trespass - 2C:18-3': 'Criminal Incidents',
              'Cyber Harassment - 2C:33-4.1': 'Criminal Incidents',
              'Cyber Harassment 2C:33-4.1': 'Criminal Investigation',
              'D.O.A': 'Emergency Response',
              'D.P.W. Assist': 'Assistance and Mutual Aid',
              'DARE Assignment': 'Community Engagement',
              'DCPP (DYFS)': 'Juvenile-Related Incidents',
              'DNA Sample': 'Investigations and Follow-Ups',
              'Damage to Property: Threats - 2C:33-11': 'Criminal Incidents',
              'Dead Animal': 'Public Safety and Welfare',
              'Deceased Person/Sexual Pen. - 2C:34-5': 'Criminal Incidents',
              'Desecration/Venerated Obj. - 2C:33-9': 'Criminal Incidents',
              'Desk Coverage': 'Administrative and Support',
              'Detective Bureau Detail': 'Investigations and Follow-Ups',
              'Disabled Motor Vehicle': 'Traffic and Motor Vehicle',
              'Disarm a Law Enforcement Officer': 'Emergency Response',
              'Disarm a Law Enforcement Officer - Attempt': 'Emergency Response',
              'Discovery - Criminal': 'Investigations and Follow-Ups',
              'Discovery - Motor Vehicle': 'Investigations and Follow-Ups',
              'Discovery - Non Specific': 'Investigations and Follow-Ups',
              'Disorderly Conduct - 2C:33-2': 'Criminal Incidents',
              'Dispute': 'Public Safety and Welfare',
              'Disrupting Meet/Procession - 2C:33-8s': 'Criminal Incidents',
              'Disturbance': 'Public Safety and Welfare',
              'Docket â€" Drop Off': 'Administrative and Support',
              'Docket â– Pick up': 'Administrative and Support',
              'Dogs Defecating': 'Regulatory and Ordinance',
              'Dogs at Large': 'Regulatory and Ordinance',
              'Domestic Dispute': 'Criminal Investigation',
              'Domestic Violence 2C:25-21': 'Criminal Investigation',
              'Domestic Violence - 2C:25-21': 'Criminal Incidents',
              'Drinking in Public': 'Regulatory and Ordinance',
              'Driving While Intoxicated - 39:4-50': 'Traffic and Motor Vehicle',
              'Driving While Intoxicated 39:4-50': 'Miscellaneous',
              'Drug Paraphernalia - 2C:36-2': 'Criminal Incidents',
              'Duty to Warn': 'Miscellaneous',
              'Duty to Warn - Notification': 'Public Safety and Welfare',
              'E.D.P.': 'Miscellaneous',
              'ESU - Response': 'Special Operations and Tactical',
              'ESU - Targeted Patrol': 'Patrol and Prevention',
              'ESU - Training': 'Special Operations and Tactical',
              'Embezzlement': 'Criminal Incidents',
              'Emergency Access Card Use': 'Emergency Response',
              'Endangering Welfare - 2C:24-4': 'Criminal Incidents',
              'Endangering Welfare - 2C:24-7': 'Criminal Incidents',
              'Endangering Welfare - 2C:24-8': 'Criminal Incidents',
              'Enticing a Child - 2C:13-6': 'Juvenile-Related Incidents',
              'Escape - 2C:29-5': 'Criminal Incidents',
              'Escort - Money': 'Assistance and Mutual Aid',
              'Evidence Delivery': 'Investigations and Follow-Ups',
              'Evidence Retrieval': 'Investigations and Follow-Ups',
              'Evidence Tampering - 2C:28-6': 'Criminal Incidents',
              'Exceptionally Cleared/Closed': 'Administrative and Support',
              'Expungement': 'Administrative and Support',
              'FTO Documentation': 'Administrative and Support',
              'Facial Recognition Request': 'Investigations and Follow-Ups',
              'False Imprisonment - 2C:13-3': 'Criminal Incidents',
              'False Public Alarm - 2C:33-3': 'Criminal Incidents',
              'False Reports - 2C:28-4': 'Criminal Incidents',
              'False Swearing - 2C:28-2': 'Criminal Incidents',
              'Fear of Bodily Violence - 2C:33-10': 'Criminal Incidents',
              'Fencing - 2C:20-7.1': 'Criminal Incidents',
              'Field Contact/ Information': 'Investigations and Follow-Ups',
              'Fight - Armed': 'Emergency Response',
              'Fight - Unarmed': 'Emergency Response',
              'Fingerprints': 'Administrative and Support',
              'Fire': 'Emergency Response',
              'Fire Department Call': 'Assistance and Mutual Aid',
              'Fireworks Complaint': 'Regulatory and Ordinance',
              'Fish and Game Violation Title 23': 'Regulatory and Ordinance',
              'Food/Drug Tampering - 2C:40-17': 'Criminal Incidents',
              'Forgery 2C:21-1': 'Miscellaneous',
              'Forgery - 2C:21-1': 'Criminal Incidents',
              'Fraud': 'Criminal Incidents',
              'Fugitive from Justice': 'Criminal Incidents',
              'Funeral Escort': 'Assistance and Mutual Aid',
              'General Information': 'Administrative and Support',
              'General Investigation': 'Investigations and Follow-Ups',
              'Generated in Error': 'Administrative and Support',
              'Generator Test': 'Administrative and Support',
              'Gifts/Public Servant - 2C:27-6': 'Criminal Incidents',
              'Good Conduct Letter Request': 'Administrative and Support',
              'Group': 'Administrative and Support',
              'HAZ-MAT Incident': 'Emergency Response',
              'HQ Assignment': 'Administrative and Support',
              'Handle With Care - Notification': 'Emergency Response',
              'Harassment 2C:33-4': 'Criminal Investigation',
              'Harassment - 2C:33-4': 'Criminal Incidents',
              'Hazard - Pothole': 'Traffic and Motor Vehicle',
              'Hazard All Other': 'Public Safety and Welfare',
              'Hazardous Condition - Health / Welfare': 'Public Safety and Welfare',
              'Hazardous Condition - Sewer Call': 'Public Safety and Welfare',
              'Hazardous Road Condition - Flooding': 'Traffic and Motor Vehicle',
              'Hazardous Road Condition - General': 'Traffic and Motor Vehicle',
              'Hazardous Road Condition - Ice': 'Traffic and Motor Vehicle',
              'Hindering Apprehension - 2C:29-3': 'Criminal Incidents',
              'Homicide - 2C:11-2': 'Criminal Incidents',
              'Hostage Situation': 'Emergency Response',
              'Hypodermic/Possession - 2C:36-6': 'Criminal Incidents',
              'ICE Notification': 'Administrative and Support',
              'Identity Theft': 'Criminal Incidents',
              'Illegal Dumping': 'Regulatory and Ordinance',
              'Imitation CDS - 2C:35-11': 'Criminal Incidents',
              'Impersonating Public Servant - 2C:28-9': 'Criminal Incidents',
              'Implements for Escape - 2C:29-6': 'Criminal Incidents',
              'Improper Records': 'Administrative and Support',
              'Information': 'Administrative and Support',
              'Injured On Duty': 'Public Safety and Welfare',
              'Injury/Law Enforce. Animals - 2C:29-3.1': 'Criminal Incidents',
              'Insecure Building': 'Public Safety and Welfare',
              'Interception/Emerg. Comm. - 2C:33-21': 'Criminal Incidents',
              'Interference - 2C:29-1': 'Criminal Incidents',
              'Interference With Custody - 2C:13-4': 'Criminal Incidents',
              'Interference w/Transport. - 2C:33-14': 'Criminal Incidents',
              'Interference/Railway Signals - 2C:33-14.1': 'Criminal Incidents',
              'Intoxicated Person': 'Public Safety and Welfare',
              'Invasion of Privacy - Observing': 'Criminal Incidents',
              'Investigation - Follow-Up': 'Investigations and Follow-Ups',
              'Investigation-Follow up': 'Administrative and Support',
              'Juvenile Complaint (Criminal)': 'Juvenile-Related Incidents',
              'Juvenile Complaint (Non-Criminal)': 'Juvenile-Related Incidents',
              'Juvenile Complaint Signed': 'Juvenile-Related Incidents',
              'Juvenile Investigation': 'Juvenile-Related Incidents',
              'Kidnapping - 2C:13-1': 'Criminal Incidents',
              'Landlord / Tenant Dispute': 'Public Safety and Welfare',
              'Leaving Scene of an Acc. - 39:4-129': 'Traffic and Motor Vehicle',
              'Lewdness 2C:14-4': 'Miscellaneous',
              'Lewdness - 2C:14-4': 'Criminal Incidents',
              'License Plate-Lost/Stolen': 'Traffic and Motor Vehicle',
              'Lo-Jack Hit - Tracking Signal': 'Investigations and Follow-Ups',
              'Lock-Out Residence': 'Assistance and Mutual Aid',
              'Loitering/CDS Offense - 2C:33-2.1': 'Criminal Incidents',
              'M.V. Master Keys - 2C:5-6': 'Criminal Incidents',
              'Maintaining a Nuisance - 2C:33-12': 'Criminal Incidents',
              'Manslaughter - 2C:11-4': 'Criminal Incidents',
              'Sale of Cigarettes to Minors - 2A:170-51': 'Regulatory and Ordinance',
              'School Crossing': 'Community Engagement',
              'School Detail': 'Community Engagement',
              'Search Warrant Execution - CDW': 'Investigations and Follow-Ups',
              'Search Warrant Execution - Structure': 'Investigations and Follow-Ups',
              'Search Warrant Execution - Vehicle': 'Investigations and Follow-Ups',
              'Service - FERPO': 'Emergency Response',
              'Service - FRO': 'Criminal Incidents',
              'Service - Subpoena': 'Administrative and Support',
              'Service - Summons': 'Administrative and Support',
              'Service - TERPO': 'Emergency Response',
              'Service - TRO': 'Criminal Incidents',
              'Service of TRO / FRO': 'Administrative and Support',
              'Serving Alcohol to Minors - 2C:33-17': 'Regulatory and Ordinance',
              'Sex Offender - Address Verification': 'Investigations and Follow-Ups',
              'Sex Offender - General': 'Administrative and Support',
              'Sex Offender - Intent to Move': 'Investigations and Follow-Ups',
              'Service Documents': 'Administrative and Support',
              'Sex Offender - Serve Tier Papers': 'Administrative and Support',
              'Sex Offender - Travel': 'Administrative and Support',
              'Sex Offender Investigation': 'Investigations and Follow-Ups',
              'Sex Offender Registration': 'Administrative and Support',
              'Sex Offender Registration - Employment': 'Administrative and Support',
              'Sex Offender Registration - School Enrollment': 'Administrative and Support',
              'Sex Offender-Removal Order': 'Administrative and Support',
              'Sexual Assault 2C:14-2b': 'Criminal Investigation',
              'Sexual Assault - 2C:14-2b': 'Criminal Incidents',
              'Shooting': 'Emergency Response',
              'Shoplifting 2C:20-11': 'Criminal Investigation',
              'Shoplifting - 2C:20-11': 'Criminal Incidents',
              'Shopping Cart': 'Public Safety and Welfare',
              'Shots Fired Investigation': 'Emergency Response',
              'Simple Assault 2C:12-1a': 'Criminal Investigation',
              'Simple Assault - 2C:12-1a': 'Criminal Incidents',
              'Slugs - 2C:21-18': 'Criminal Incidents',
              'Smoking Prohibited': 'Regulatory and Ordinance',
              'Snow Plowed onto Public Street': 'Regulatory and Ordinance',
              'Snow Removal': 'Regulatory and Ordinance',
              'Special Assignment': 'Administrative and Support',
              'Stabbing': 'Emergency Response',
              'Stalking - 2C:12-10': 'Criminal Incidents',
              'Stationhouse Adjustment': 'Juvenile-Related Incidents',
              'Stolen Article': 'Criminal Incidents',
              'Stranded Party': 'Assistance and Mutual Aid',
              'Street Light': 'Public Safety and Welfare',
              'Structure Damage': 'Public Safety and Welfare',
              'Sudden Death Investigation': 'Emergency Response',
              'Suicidal party': 'Public Safety and Welfare',
              'Suicide': 'Emergency Response',
              'Summons': 'Criminal Incidents',
              'Surrender of Ammunition': 'Administrative and Support',
              'Surrender of Weapon': 'Administrative and Support',
              'Surrendered Firearm ID Card': 'Administrative and Support',
              'Surrendered License Plates': 'Administrative and Support',
              'Suspended Drivers License - 39:3-40': 'Traffic and Motor Vehicle',
              'Suspended Drivers License 39:3-40': 'Traffic and Motor Vehicle',
              'Suspended Registration 39:3-40': 'Traffic and Motor Vehicle',
              'Suspended Registration - 39:3-40': 'Traffic and Motor Vehicle',
              'Suspicious Activity Report': 'Investigations and Follow-Ups',
              'Suspicious Activity Submission': 'Investigations and Follow-Ups',
              'Suspicious Incident': 'Investigations and Follow-Ups',
              'Suspicious Item': 'Investigations and Follow-Ups',
              'Suspicious Person': 'Investigations and Follow-Ups',
              'Suspicious Vehicle': 'Investigations and Follow-Ups',
              'TAPS - Business': 'Public Safety and Welfare',
              'TAPS - ESU - Business': 'Special Operations and Tactical',
              'TAPS - ESU - Medical Facility': 'Special Operations and Tactical',
              'TAPS - ESU - Park': 'Special Operations and Tactical',
              'TAPS - ESU - Parking Garage': 'Special Operations and Tactical',
              'TAPS - ESU - Religious Facility': 'Special Operations and Tactical',
              'TAPS - ESU - School': 'Special Operations and Tactical',
              'TAPS - Housing': 'Public Safety and Welfare',
              'TAPS - Medical Facility': 'Public Safety and Welfare',
              'TAPS - Other': 'Public Safety and Welfare',
              'TAPS - Park': 'Public Safety and Welfare',
              'TAPS - Parking Garage': 'Public Safety and Welfare',
              'TAPS - Religious Facility': 'Public Safety and Welfare',
              'TAPS - School': 'Public Safety and Welfare',
              'TAS Alert - Stolen License Plate': 'Investigations and Follow-Ups',
              'TOT DCP&P': 'Juvenile-Related Incidents',
              'Tampering: Public Records 2C:28-7': 'Administrative and Support',
              'Tampering: Public Records - 2C:28-7': 'Criminal Incidents',
              'Targeted Area Patrol': 'Patrol and Prevention',
              'Task Assignment': 'Administrative and Support',
              'Temporary Parking': 'Traffic and Motor Vehicle',
              'Terroristic Threats 2C:12-3': 'Criminal Investigation',
              'Terroristic Threats - 2C:12-3': 'Criminal Incidents',
              'Theft 2C:20-3': 'Criminal Investigation',
              'Theft - 2C:20-3': 'Criminal Incidents',
              'Theft by Deception 2C:20-4': 'Criminal Investigation',
              'Theft by Deception - 2C:20-4': 'Criminal Incidents',
              'Theft by Extortion 2C:20-5': 'Criminal Investigation',
              'Theft by Extortion - 2C:20-5': 'Criminal Incidents',
              'Theft of Identity - 2C:21-17': 'Criminal Incidents',
              'Theft of Lost/Mislaid Property 2C:20-6': 'Criminal Investigation',
              'Theft of Lost/Mislaid Property - 2C:20-6': 'Criminal Incidents',
              'Theft of Services 2C:20-8': 'Criminal Investigation',
              'Theft of Services - 2C:20-8': 'Criminal Incidents',
              'Theft/Disposition - 2C:20-9': 'Criminal Incidents',
              'Time Check': 'Administrative and Support',
              'Traffic Bureau Report': 'Traffic and Motor Vehicle',
              'Traffic Detail': 'Traffic and Motor Vehicle',
              'Traffic Detail - Road Closure': 'Traffic and Motor Vehicle',
              'Traffic Enforcement Detail': 'Traffic and Motor Vehicle',
              'Traffic Hazard': 'Traffic and Motor Vehicle',
              'Traffic Light Malfunction': 'Traffic and Motor Vehicle',
              'Traffic Sign / Signal Malfunction': 'Traffic and Motor Vehicle',
              'Training': 'Administrative and Support',
              'Training Record': 'Administrative and Support',
              'Transportation': 'Administrative and Support',
              'Tree limb down': 'Public Safety and Welfare',
              'Truancy': 'Juvenile-Related Incidents',
              'U-Visa': 'Administrative and Support',
              'UAS Operation': 'Special Operations and Tactical',
              'Unauthorized Intercept./Comm. - 2C:33-22': 'Criminal Incidents',
              'Undercover Buy': 'Special Operations and Tactical',
              'Unfounded Incident': 'Administrative and Support',
              'Unfounded/Closed': 'Administrative and Support',
              'Uninsured Vehicle - 39:6b-2': 'Traffic and Motor Vehicle',
              'Unintentional Discharge': 'Emergency Response',
              'Unknown Investigation': 'Investigations and Follow-Ups',
              'Unlawful Possess./Weapons 2C:39-5': 'Criminal Investigation',
              'Unlawful Possess./Weapons - 2C:39-5': 'Emergency',
              'Unlawful Taking 2C:20-10': 'Miscellaneous',
              'Unlawful Taking - 2C:20-10': 'Criminal Incidents',
              'Unlawful Use Of 9-1-1 Sys. - 2C:33-3e': 'Criminal Incidents',
              'Unregistered Vehicle 39:3-4': 'Traffic and Motor Vehicle',
              'Unregistered Vehicle - 39:3-4': 'Traffic and Motor Vehicle',
              'Unsworn Falsification - 2C:28-3': 'Criminal Incidents',
              'Unwanted Person': 'Public Safety and Welfare',
              'Urinating in Public': 'Regulatory and Ordinance',
              'Utility Incident': 'Public Safety and Welfare',
              'Vacant House': 'Public Safety and Welfare',
              'Vacation': 'Administrative and Support',
              'Validation': 'Administrative and Support',
              'Vehicle Maintenance': 'Administrative and Support',
              'Vehicular Homicide - 2C:11-5': 'Criminal Incidents',
              'Vending Without Permit': 'Regulatory and Ordinance',
              'Violation of Court Order': 'Criminal Incidents',
              'Violation: TRO/ FRO 2C:29-9b': 'Traffic and Motor Vehicle',
              'Violation: TRO/ FRO - 2C:29-9b': 'Criminal Incidents',
              'Virtual - Patrol': 'Public Safety and Welfare',
              'Wagering/Official Action - 2C:30-3': 'Criminal Incidents',
              'Warning Issued': 'Administrative and Support',
              'Warrant Arrest': 'Criminal Incidents',
              'Warrant Recall': 'Administrative and Support',
              'Weapons - Unlawful Purposes - 2C:39-4': 'Criminal Incidents',
              'Weapons - Unlawful Purposes 2C:39-4': 'Criminal Investigation',
              'Weapons Seizure - 2C:25-21d': 'Criminal Incidents',
              'domestic Dispute': 'Criminal Investigation',
              'shoplifting 2C:20-11': 'Criminal Investigation',
              'simple Assault 2C:12-1a': 'Criminal Investigation',
              'targeted Area Patrol': 'Patrol and Prevention',
              'terroristic Threats 2C:12-3': 'Criminal Investigation'
          }

          # Response type mapping (initialized alongside category_map)
          self.response_map = {
              # Default response types for demonstration
              'Emergency Response': 'Emergency',
              'Criminal Investigation': 'Priority',
              'Criminal Incidents': 'Priority',
              'Traffic and Motor Vehicle': 'Routine',
              'Administrative and Support': 'Routine'
          }

          self.logger.info("Master SCRPA Processor initialized")

      def setup_directories(self):
          """Setup your actual project directory structure."""

          self.dirs = {
              'scripts': self.project_path / '01_scripts',
              'cad_exports': self.export_dirs['cad_exports'],
              'rms_exports': self.export_dirs['rms_exports'],
              'output': self.project_path / '03_output',
              'powerbi': self.project_path / '04_powerbi',
              'logs': self.project_path / '03_output' / 'logs',
              'reports': self.project_path / '03_output' / 'reports'
          }

          # Create output directories if they don't exist (don't create export dirs - they're managed by your system)
          for dir_name, dir_path in self.dirs.items():
              if dir_name not in ['cad_exports', 'rms_exports']:
                  dir_path.mkdir(parents=True, exist_ok=True)

          # Verify export directories exist
          if not self.dirs['cad_exports'].exists():
              self.logger.warning(f"CAD export directory not found: {self.dirs['cad_exports']}")
          if not self.dirs['rms_exports'].exists():
              self.logger.warning(f"RMS export directory not found: {self.dirs['rms_exports']}")

      def find_latest_export_file(self, export_type: str = "auto") -> Tuple[str, DataSource]:
          """Find the latest CAD or RMS export file from your actual export directories."""

          self.logger.info(f"Searching for latest {export_type} export files")

          latest_file = None
          detected_source = DataSource.UNKNOWN

          if export_type.lower() in ["auto", "cad"]:
              # Search CAD exports
              cad_files = list(self.dirs['cad_exports'].glob("*.xlsx"))
              if cad_files:
                  latest_cad = max(cad_files, key=lambda x: x.stat().st_mtime)
                  self.logger.info(f"Latest CAD file: {latest_cad.name}")
                  if export_type == "auto" or export_type.lower() == "cad":
                      latest_file = str(latest_cad)
                      detected_source = DataSource.CAD

          if export_type.lower() in ["auto", "rms"] and not latest_file:
              # Search RMS exports
              rms_files = list(self.dirs['rms_exports'].glob("*.xlsx"))
              if rms_files:
                  latest_rms = max(rms_files, key=lambda x: x.stat().st_mtime)
                  self.logger.info(f"Latest RMS file: {latest_rms.name}")
                  if export_type == "auto" or export_type.lower() == "rms":
                      latest_file = str(latest_rms)
                      detected_source = DataSource.RMS

          if export_type == "auto" and latest_file is None:
              # Compare both directories and pick the most recent
              all_files = []

              cad_files = list(self.dirs['cad_exports'].glob("*.xlsx"))
              rms_files = list(self.dirs['rms_exports'].glob("*.xlsx"))

              for f in cad_files:
                  all_files.append((f, DataSource.CAD))
              for f in rms_files:
                  all_files.append((f, DataSource.RMS))

              if all_files:
                  latest_file_info = max(all_files, key=lambda x: x[0].stat().st_mtime)
                  latest_file = str(latest_file_info[0])
                  detected_source = latest_file_info[1]
                  self.logger.info(f"Most recent file: {latest_file_info[0].name} ({detected_source.value})")

          if latest_file is None:
              raise FileNotFoundError(f"No export files found in {self.dirs['cad_exports']} or {self.dirs['rms_exports']}")

          return latest_file, detected_source

      def setup_logging(self):
          """Setup comprehensive logging system."""

          log_file = self.dirs['logs'] / f"master_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

          self.logger = logging.getLogger('MasterProcessor')
          self.logger.setLevel(logging.INFO)

          # Prevent duplicate handlers if script is re-run
          if self.logger.hasHandlers():
              self.logger.handlers.clear()

          # Disable propagation to prevent duplicate log entries
          self.logger.propagate = False

          # File handler for logging to a file with UTF-8 encoding
          fh = logging.FileHandler(log_file, encoding='utf-8')
          fh.setLevel(logging.INFO)

          # Console handler for logging to the console with UTF-8 encoding
          ch = logging.StreamHandler(sys.stdout)
          ch.setLevel(logging.INFO)

          # Create formatter and add it to the handlers
          formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
          fh.setFormatter(formatter)
          ch.setFormatter(formatter)

          # Add the handlers to the logger
          self.logger.addHandler(fh)
          self.logger.addHandler(ch)

          # Prevent duplicate log entries by disabling propagation
          self.logger.propagate = False

          # Ensure console I/O uses UTF-8 encoding for menu and "→" characters
          import io
          import sys
          if hasattr(sys.stdout, 'reconfigure'):
              sys.stdout.reconfigure(encoding='utf-8')
          if hasattr(sys.stderr, 'reconfigure'):
              sys.stderr.reconfigure(encoding='utf-8')

          self.logger.info(f"Logging initialized: {log_file}")

      def process_complete_pipeline(self, input_file: str = None,
                                  output_file: str = None, export_type: str = "auto") -> Tuple[pd.DataFrame, Dict]:
          """
          Run the complete SCRPA processing pipeline.
          This replaces all your complex M Code with clean, fast Python processing.
          """

          self.logger.info("========================================")
          self.logger.info("STARTING COMPLETE SCRPA PROCESSING PIPELINE")
          self.logger.info("========================================")

          self.stats['processing_start_time'] = datetime.now()

          try:
              # Step 1: Auto-detect and load data from your export directories
              df, data_source, structure_info = self.auto_detect_and_load_data(input_file, export_type)

              # Step 2: Process based on detected structure
              processed_df = self.process_by_data_source(df, data_source)

              # Step 3: Enhanced CADNotes processing
              enhanced_df = self.process_cadnotes_enhanced(processed_df)

              # Step 4: Add all derived columns (replaces M Code logic)
              final_df = self.add_all_enhancements(enhanced_df)

              # Step 5: Data quality validation and cleanup
              validated_df = self.validate_and_cleanup(final_df)

              # Step 6: Export for Power BI
              output_path = self.export_for_powerbi(validated_df, output_file)

              self.logger.info("========================================")
              self.logger.info("COMPLETE SCRPA PROCESSING PIPELINE FINISHED")
              self.logger.info(f"Output: {output_path}")
              self.logger.info("========================================")

              return validated_df, self.stats

          except Exception as e:
              self.logger.error(f"PIPELINE FAILED: {str(e)}")
              self.stats['errors_encountered'].append(str(e))
              raise

      def auto_detect_and_load_data(self, input_file: str = None, export_type: str = "auto") -> Tuple[pd.DataFrame, DataSource, Dict]:
          """Auto-detect data source and load using your actual export directories."""

          self.logger.info("Step 1: Auto-detecting data source and loading data")

          try:
              if input_file:
                  # Load specific file
                  self.logger.info(f"Loading specified file: {Path(input_file).name}")
                  df = pd.read_excel(input_file, engine='openpyxl')
                  data_source, structure_info = self.data_validator.detect_data_source(df)
              else:
                  # Find latest export file from your actual directories
                  latest_file, detected_source = self.find_latest_export_file(export_type)
                  self.logger.info(f"Loading latest export: {Path(latest_file).name}")

                  df = pd.read_excel(latest_file, engine='openpyxl')
                  data_source, structure_info = self.data_validator.detect_data_source(df)

                  # Verify detection matches file location
                  if detected_source != data_source:
                      self.logger.warning(f"File location suggests {detected_source.value} but structure detected as {data_source.value}")

              # New: Drop duplicates on ReportNumberNew/Case_Number
              id_col = 'ReportNumberNew' if 'ReportNumberNew' in df.columns else 'Case_Number' if 'Case_Number' in df.columns else None
              if id_col:
                  original_len = len(df)
                  df = df.drop_duplicates(subset=[id_col])
                  dupes_removed = original_len - len(df)
                  if dupes_removed > 0:
                      self.logger.info(f"Removed {dupes_removed} duplicates based on {id_col}")
              else:
                  self.logger.warning("No ID column found for duplicate removal (ReportNumberNew or Case_Number)")

              # New: Convert Time of Call from Excel serial to datetime if present
              if 'Time of Call' in df.columns:
                  def serial_to_datetime(serial):
                      if pd.isnull(serial):
                          return None
                      try:
                          return datetime(1899, 12, 30) + timedelta(days=serial)
                      except:
                          return None

                  df['Time of Call'] = df['Time of Call'].apply(serial_to_datetime)
                  # Fix: Convert to datetime series before strftime
                  df['Time of Call'] = pd.to_datetime(df['Time of Call'], errors='coerce')
                  # Format to mm/dd/yyyy hh:mm:ss
                  df['Time of Call'] = df['Time of Call'].dt.strftime('%m/%d/%Y %H:%M:%S')
                  # Check for nulls
                  null_count = df['Time of Call'].isnull().sum()
                  if null_count > 0:
                      self.logger.warning(f"{null_count} null values in Time of Call (unexpected for CAD exports)")

              # Remove unnecessary columns early
              columns_to_remove = ['cYear', 'cMonth', 'DayofWeek', 'case_number', 'Case_Number2', 'Day_Name', 'Month_Name', 'Year', 'Month', 'Day']
              for col in columns_to_remove:
                  if col in df.columns:
                      df = df.drop(columns=[col])
                      self.logger.info(f"Removed column: {col}")

              self.stats['total_input_records'] = len(df)

              self.logger.info(f"Detected {data_source.value} structure with {len(df)} records")
              return df, data_source, structure_info

          except Exception as e:
              self.logger.error(f"Failed to auto-detect and load data: {e}")
              raise

      def process_by_data_source(self, df: pd.DataFrame, data_source: DataSource) -> pd.DataFrame:
          """Process data based on detected source structure."""

          self.logger.info(f"Step 2: Processing {data_source.value} data structure")

          if data_source == DataSource.CAD:
              return self.process_cad_structure(df)
          elif data_source == DataSource.RMS:
              return self.process_rms_structure(df)
          else:
              raise ValueError(f"Unknown data source: {data_source}")

      def process_cad_structure(self, df: pd.DataFrame) -> pd.DataFrame:
          """Process CAD data structure (single Incident column)."""

          self.logger.info("Processing CAD structure (no unpivoting needed)")

          # Use your existing CAD preparation logic
          prepared_df = self.data_validator.prepare_cad_data(df)

          # Standardize column names for downstream processing
          if 'ReportNumberNew' in prepared_df.columns:
              prepared_df['Case_Number'] = prepared_df['ReportNumberNew']

          if 'Incident' in prepared_df.columns:
              prepared_df['IncidentType'] = prepared_df['Incident']

          # Trim IncidentType after ' - 2C'
          if 'IncidentType' in prepared_df.columns:
              prepared_df['IncidentType'] = prepared_df['IncidentType'].str.split(' - 2C').str[0]

          # Add category and response type from mapping
          if 'IncidentType' in prepared_df.columns:
              prepared_df['Category_Type'] = prepared_df['IncidentType'].map(self.category_map).fillna('Other')
              prepared_df['Response_Type'] = prepared_df['IncidentType'].map(self.response_map).fillna('Routine')

          # Add crime categorization
          prepared_df['Crime_Category'] = prepared_df['IncidentType'].apply(categorize_crime_type)

          # New: Map How Reported codes
          if 'How Reported' in prepared_df.columns:
              prepared_df['How Reported'] = prepared_df['How Reported'].replace('37135', '9-1-1')

          # Ensure 0 nulls in Response Type
          if 'Response Type' in prepared_df.columns:
              prepared_df['Response Type'] = prepared_df['Response Type'].fillna('Unknown')
              null_count = prepared_df['Response Type'].isnull().sum()
              if null_count > 0:
                  self.logger.warning(f"Unexpected {null_count} nulls in Response Type after fill")

          self.logger.info(f"CAD processing complete: {len(prepared_df)} records")
          return prepared_df

      def process_rms_structure(self, df: pd.DataFrame) -> pd.DataFrame:
          """Process RMS data structure (multiple Incident Type columns)."""

          self.logger.info("Processing RMS structure (unpivoting required)")

          # Use your existing RMS preparation logic
          prepared_df = self.data_validator.prepare_rms_data(df)

          # Standardize column names
          if 'Case Number' in prepared_df.columns:
              prepared_df['Case_Number'] = prepared_df['Case Number']

          if 'incident_text' in prepared_df.columns:
              prepared_df['IncidentType'] = prepared_df['incident_text']

          # Trim incident_text and IncidentType after ' - 2C'
          for col in ['incident_text', 'IncidentType']:
              if col in prepared_df.columns:
                  prepared_df[col] = prepared_df[col].str.split(' - 2C').str[0]

          # Adapt M code: Create ALL_INCIDENTS
          if all(col in prepared_df.columns for col in ['Incident Type_1', 'Incident Type_2', 'Incident Type_3']):
              prepared_df['ALL_INCIDENTS'] = prepared_df[['Incident Type_1', 'Incident Type_2', 'Incident Type_3']].apply(
                  lambda x: ' - '.join(x.dropna()), axis=1
              )
          else:
              prepared_df['ALL_INCIDENTS'] = prepared_df['IncidentType']

          # Add Period (before filtering)
          prepared_df = self.add_period_classification(prepared_df)

          # Filter out excluded case and Historical
          prepared_df = prepared_df[
              (prepared_df['Case_Number'] != '25-057654') &
              (prepared_df['Period'] != 'Historical')
          ]

          # Unpivot Incident Types
          if all(col in prepared_df.columns for col in ['Incident Type_1', 'Incident Type_2', 'Incident Type_3']):
              incident_cols = ['Incident Type_1', 'Incident Type_2', 'Incident Type_3']
              id_cols = [col for col in prepared_df.columns if col not in incident_cols]
              unpivoted = pd.melt(prepared_df, id_vars=id_cols, value_vars=incident_cols, var_name='IncidentColumn', value_name='IncidentType')
              unpivoted = unpivoted[unpivoted['IncidentType'].notnull() & (unpivoted['IncidentType'] != '')]
              prepared_df = unpivoted

          # Trim IncidentType after unpivot
          prepared_df['IncidentType'] = prepared_df['IncidentType'].str.split(' - 2C').str[0]

          # Add Crime_Category using individual and ALL_INCIDENTS
          prepared_df['Crime_Category'] = prepared_df.apply(lambda row: categorize_crime_type_combined(row['IncidentType'], row['ALL_INCIDENTS']), axis=1)

          # Remove duplicates by Case_Number
          prepared_df = prepared_df.drop_duplicates(subset=['Case_Number'])

          # Add category and response type from mapping
          if 'IncidentType' in prepared_df.columns:
              prepared_df['Category_Type'] = prepared_df['IncidentType'].map(self.category_map).fillna('Other')
              prepared_df['Response_Type'] = prepared_df['IncidentType'].map(self.response_map).fillna('Routine')

          # Ensure 0 nulls in Response Type
          if 'Response Type' in prepared_df.columns:
              prepared_df['Response Type'] = prepared_df['Response Type'].fillna('Unknown')
              null_count = prepared_df['Response Type'].isnull().sum()
              if null_count > 0:
                  self.logger.warning(f"Unexpected {null_count} nulls in Response Type after fill")

          self.logger.info(f"RMS processing complete: {len(prepared_df)} records")
          return prepared_df

      def process_cadnotes_enhanced(self, df: pd.DataFrame) -> pd.DataFrame:
          """Process CADNotes using enhanced processor."""

          self.logger.info("Step 3: Enhanced CADNotes processing")

          if 'CADNotes' in df.columns:
              # Clean CADNotes
              df['CADNotes'] = df['CADNotes'].apply(self.clean_text)
              enhanced_df = self.cadnotes_processor.process_cadnotes_dataframe(df, 'CADNotes')
              self.stats['cadnotes_processed'] = enhanced_df['CAD_Username'].notna().sum()
          else:
              self.logger.warning("No CADNotes column found, skipping CADNotes processing")
              enhanced_df = df.copy()
              # Add empty CADNotes columns for consistency
              enhanced_df['CAD_Username'] = None
              enhanced_df['CAD_Timestamp'] = None
              enhanced_df['CAD_Notes_Cleaned'] = None
              enhanced_df['CADNotes_Processing_Quality'] = 0.0

          # Clean Narrative if present
          if 'Narrative' in df.columns:
              df['Narrative'] = df['Narrative'].apply(self.clean_text)

          self.logger.info(f"CADNotes processing complete: {self.stats['cadnotes_processed']} notes processed")
          return enhanced_df

      def clean_text(self, text):
          """Comprehensive text cleaning for CADNotes and Narrative."""
          if pd.isna(text):
              return None

          text = str(text)
          # Replace line breaks with spaces
          text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
          # Replace multiple spaces
          while '  ' in text:
              text = text.replace('  ', ' ')
          # Clean control characters (Text.Clean equivalent - remove non-printable)
          text = ''.join(c for c in text if c.isprintable() or c.isspace())
          # Trim
          text = text.strip()
          # Replace special chars
          text = text.replace('â', "'").replace('â', '')
          return text if text else None

      def add_all_enhancements(self, df: pd.DataFrame) -> pd.DataFrame:
          """Add all derived columns that replace your M Code logic."""

          self.logger.info("Step 4: Adding derived columns (replaces M Code logic)")

          enhanced_df = df.copy()

          # Add cascading Incident_Date
          enhanced_df = self.add_incident_date(enhanced_df)

          # Add cascading Incident_Time
          enhanced_df = self.add_incident_time(enhanced_df)

          # Convert time columns
          for col in ['Time Dispatched', 'Time Out', 'Time In', 'incident_datetime']:
              if col in enhanced_df.columns:
                  enhanced_df[col] = pd.to_datetime(enhanced_df[col], errors='coerce').dt.strftime('%m/%d/%Y %H:%M:%S')

          # Convert durations
          for col in ['Time Spent', 'Time Response']:
              if col in enhanced_df.columns:
                  enhanced_df[col] = pd.to_timedelta(enhanced_df[col], errors='coerce')

          # HourMinuetsCalc to hh:mm
          if 'HourMinuetsCalc' in enhanced_df.columns:
              enhanced_df['HourMinuetsCalc'] = enhanced_df['HourMinuetsCalc'].apply(self.fraction_to_time)

          # Date/Time enhancements
          enhanced_df = self.add_datetime_enhancements(enhanced_df)

          # Address/Block enhancements
          enhanced_df = self.add_address_enhancements(enhanced_df)

          # Period classification
          enhanced_df = self.add_period_classification(enhanced_df)

          # Time formatting (response time, time spent)
          enhanced_df = self.add_time_formatting(enhanced_df)

          # Geographic enhancements (rename Zone to Post)
          enhanced_df = self.add_geographic_enhancements(enhanced_df)

          self.logger.info("All enhancements complete")
          return enhanced_df

      def add_incident_date(self, df: pd.DataFrame) -> pd.DataFrame:
          """Add Incident_Date with cascading logic."""
          date_cols = [col for col in df.columns if 'Incident Date' in col or 'Report Date' in col]
          if date_cols:
              df['Incident_Date'] = df.apply(lambda row: self.cascade_date(row), axis=1)
          return df

      def cascade_date(self, row):
          """Cascading logic for Incident_Date."""
          if 'Incident Date' in row and pd.notna(row['Incident Date']):
              return row['Incident Date']
          elif 'Incident Date_Between' in row and pd.notna(row['Incident Date_Between']):
              return row['Incident Date_Between']
          elif 'Report Date' in row and pd.notna(row['Report Date']):
              return row['Report Date']
          return None

      def add_incident_time(self, df: pd.DataFrame) -> pd.DataFrame:
          """Add Incident_Time with cascading logic."""
          time_cols = [col for col in df.columns if 'Incident Time' in col or 'Report Time' in col]
          if time_cols:
              df['Incident_Time'] = df.apply(lambda row: self.cascade_time(row), axis=1)
          else:
              df['Incident_Time'] = None  # Ensure column exists even if no source columns
          return df

      def cascade_time(self, row):
          """Cascading logic for Incident_Time."""
          if 'Incident Time' in row and pd.notna(row['Incident Time']):
              return row['Incident Time']
          elif 'Incident Time_Between' in row and pd.notna(row['Incident Time_Between']):
              return row['Incident Time_Between']
          elif 'Report Time' in row and pd.notna(row['Report Time']):
              return row['Report Time']
          return None

      def fraction_to_time(self, fraction):
          """Convert HourMinuetsCalc fraction to hh:mm."""
          if pd.isna(fraction):
              return None
          try:
              hours = int(fraction * 24)
              minutes = int((fraction * 24 - hours) * 60)
              return f"{hours:02d}:{minutes:02d}"
          except:
              return None

      def add_datetime_enhancements(self, df: pd.DataFrame) -> pd.DataFrame:
          """Add date/time derived columns."""

          # Incident_Date already added

          # Incident_Time already added

          # Add TimeOfDay from M code logic
          if 'Incident_Time' in df.columns:
              df['TimeOfDay'] = df['Incident_Time'].apply(self.calculate_time_of_day)
          else:
              df['TimeOfDay'] = "Unknown"

          return df

      def calculate_time_of_day(self, t):
          """Adapted from WithTimeOfDay M code."""
          if pd.isna(t):
              return "Unknown"
          if isinstance(t, str):
              t = datetime.strptime(t, '%H:%M:%S').time() if ':' in t else None
          if t is None:
              return "Unknown"

          if datetime.time(0,0,0) <= t < datetime.time(4,0,0):
              return "00:00–03:59 Early Morning"
          elif datetime.time(4,0,0) <= t < datetime.time(8,0,0):
              return "04:00–07:59 Morning"
          elif datetime.time(8,0,0) <= t < datetime.time(12,0,0):
              return "08:00–11:59 Morning Peak"
          elif datetime.time(12,0,0) <= t < datetime.time(16,0,0):
              return "12:00–15:59 Afternoon"
          elif datetime.time(16,0,0) <= t < datetime.time(20,0,0):
              return "16:00–19:59 Evening Peak"
          else:
              return "20:00–23:59 Night"

      def add_address_enhancements(self, df: pd.DataFrame) -> pd.DataFrame:
          """Add address and block enhancements. Addresses already conform to ArcGIS standards (single line with components)."""

          # Find address column
          address_col = None
          for col in ['address', 'Address', 'FullAddress', 'FullAddress2', 'Enhanced_FullAddress']:
              if col in df.columns:
                  address_col = col
                  break

          if address_col:
              df['Enhanced_Block'] = df[address_col].apply(calculate_enhanced_block)
          else:
              df['Enhanced_Block'] = 'Unknown Block'

          return df

      def add_period_classification(self, df: pd.DataFrame) -> pd.DataFrame:
          """Add period classification (7-Day, 28-Day, YTD, Historical)."""

          def classify_period(incident_date):
              if pd.isna(incident_date):
                  return 'Historical'

              try:
                  incident_dt = pd.to_datetime(incident_date)
                  today = pd.Timestamp.now().date()
                  days_diff = (today - incident_dt.date()).days

                  if days_diff <= 7:
                      return '7-Day'
                  elif days_diff <= 28:
                      return '28-Day'
                  elif incident_dt.year == today.year:
                      return 'YTD'
                  else:
                      return 'Historical'
              except:
                  return 'Historical'

          df['Period'] = df['Incident_Date'].apply(classify_period)
          return df

      def add_time_formatting(self, df: pd.DataFrame) -> pd.DataFrame:
          """Add formatted time columns for response time and time spent."""

          # Format response time
          if 'Time_Response_Minutes' in df.columns:
              df['Time_Response_Formatted'] = df['Time_Response_Minutes'].apply(format_response_time)

          # Format time spent
          if 'Time_Spent_Minutes' in df.columns:
              df['Time_Spent_Formatted'] = df['Time_Spent_Minutes'].apply(format_time_spent)

          return df

      def add_geographic_enhancements(self, df: pd.DataFrame) -> pd.DataFrame:
          """Add geographic enhancements (Grid, Zone, etc.)."""

          # Standardize Grid/Zone columns
          grid_cols = [col for col in df.columns if 'grid' in col.lower()]
          if grid_cols:
              df['Grid'] = df[grid_cols[0]]

          zone_cols = [col for col in df.columns if 'zone' in col.lower() or 'pdzone' in col.lower()]
          if zone_cols:
              # New: Convert PDZone to single-digit int, handling nulls
              df['PDZone'] = pd.to_numeric(df[zone_cols[0]], errors='coerce').astype('Int64')
              # Rename Zone to Post
              if 'Zone' in df.columns:
                  df = df.rename(columns={'Zone': 'Post'})

          # Standardize Officer column
          officer_cols = [col for col in df.columns if 'officer' in col.lower()]
          if officer_cols:
              df['Officer'] = df[officer_cols[0]]

          return df

      def validate_and_cleanup(self, df: pd.DataFrame) -> pd.DataFrame:
          """Final data validation and cleanup."""

          self.logger.info("Step 5: Data validation and cleanup")

          # Remove records with missing critical fields
          original_count = len(df)

          # Keep records with valid case numbers and incident types
          df = df[
              df['Case_Number'].notna() &
              (df['Case_Number'] != '') &
              df['IncidentType'].notna() &
              (df['IncidentType'] != '')
          ]

          # Calculate overall data quality score
          if 'CADNotes_Processing_Quality' in df.columns:
              self.stats['quality_score_avg'] = df['CADNotes_Processing_Quality'].mean()

          removed_count = original_count - len(df)
          if removed_count > 0:
              self.logger.warning(f"Removed {removed_count} records with missing critical fields")

          self.logger.info(f"Validation complete: {len(df)} clean records")
          return df

      def export_for_powerbi(self, df: pd.DataFrame, output_file: str = None) -> str:
          """Export clean data for Power BI consumption."""

          self.logger.info("Step 6: Exporting for Power BI")

          if output_file is None:
              output_file = self.dirs['powerbi'] / "enhanced_scrpa_data.csv"

          # Ensure the output directory exists
          Path(output_file).parent.mkdir(parents=True, exist_ok=True)

          df.to_csv(output_file, index=False, encoding='utf-8')

          self.logger.info(f"Data successfully exported to {output_file}")
          return str(output_file)

  # Helper functions for data processing
  def categorize_crime_type_combined(incident: str, all_incidents: str) -> str:
      """Adapted crime categorization using individual and combined."""
      incident_upper = str(incident).upper() if incident else ""
      all_upper = str(all_incidents).upper() if all_incidents else ""

      if "MOTOR VEHICLE THEFT" in incident_upper or "MOTOR VEHICLE THEFT" in all_upper:
          return "Motor Vehicle Theft"
      elif "ROBBERY" in incident_upper or "ROBBERY" in all_upper:
          return "Robbery"
      elif ("BURGLARY" in incident_upper and "AUTO" in incident_upper) or ("BURGLARY" in all_upper and "AUTO" in all_upper):
          return "Burglary – Auto"
      elif "SEXUAL" in incident_upper or "SEXUAL" in all_upper:
          return "Sexual Offenses"
      elif ("BURGLARY" in incident_upper and "COMMERCIAL" in incident_upper) or ("BURGLARY" in all_upper and "COMMERCIAL" in all_upper):
          return "Burglary – Commercial"
      elif ("BURGLARY" in incident_upper and "RESIDENCE" in incident_upper) or ("BURGLARY" in all_upper and "RESIDENCE" in all_upper):
          return "Burglary – Residence"
      else:
          return "Other"

  def categorize_crime_type(incident_type: str) -> str:
      """Categorize crime types using your exact patterns."""
      if pd.isna(incident_type):
          return 'Other'

      incident_upper = str(incident_type).upper()

      if any(term in incident_upper for term in ['MOTOR VEHICLE THEFT', 'AUTO THEFT', 'MV THEFT']):
          return 'Motor Vehicle Theft'
      elif 'BURGLARY' in incident_upper and ('AUTO' in incident_upper or 'VEHICLE' in incident_upper):
          return 'Burglary - Auto'
      elif 'BURGLARY' in incident_upper and 'COMMERCIAL' in incident_upper:
          return 'Burglary - Commercial'
      elif 'BURGLARY' in incident_upper and 'RESIDENCE' in incident_upper:
          return 'Burglary - Residence'
      elif 'ROBBERY' in incident_upper:
          return 'Robbery'
      elif 'SEXUAL' in incident_upper:
          return 'Sexual Offenses'
      else:
          return 'Other'

  def categorize_time_of_day(row) -> str:
      """Categorize time into day periods."""
      try:
          if 'Incident_Time' in row and pd.notna(row['Incident_Time']):
              time_val = row['Incident_Time']
              if isinstance(time_val, str):
                  hour = int(time_val.split(':')[0])
              else:
                  hour = time_val.hour
          else:
              return "Unknown"

          if 4 <= hour < 8:
              return "04:00–07:59 Morning"
          elif 8 <= hour < 12:
              return "08:00–11:59 Morning Peak"
          elif 12 <= hour < 16:
              return "12:00–15:59 Afternoon"
          elif 16 <= hour < 20:
              return "16:00–19:59 Evening Peak"
          else:
              return "20:00–03:59 Night"
      except:
          return "Unknown"

  def calculate_enhanced_block(address: str) -> str:
      """Calculate enhanced block from address."""
      if pd.isna(address) or not address:
          return "Incomplete Address - Check Location Data"

      try:
          address = str(address).strip()
          # Remove Hackensack suffix
          clean_addr = address.replace(", Hackensack, NJ, 07601", "").replace(", Hackensack, NJ", "")

          # Handle intersections
          if ' & ' in clean_addr:
              return clean_addr.strip()

          # Extract block number
          parts = clean_addr.split()
          if parts and parts[0].replace('-', '').isdigit():
              street_num = int(parts[0].replace('-', ''))
              street_name = ' '.join(parts[1:]).split(',')[0]
              block_num = (street_num // 100) * 100
              return f"{street_name}, {block_num} Block"
          else:
              street_name = clean_addr.split(',')[0]
              return f"{street_name}, Unknown Block"
      except:
          return "Incomplete Address - Check Location Data"

  def format_response_time(minutes) -> str:
      """Format response time in minutes to readable format."""
      if pd.isna(minutes):
          return None

      try:
          total_seconds = int(float(minutes) * 60)
          mins = total_seconds // 60
          secs = total_seconds % 60

          if mins == 0:
              return f"{secs} Secs"
          elif secs == 0:
              return f"{mins} Mins"
          else:
              return f"{mins} Mins {secs:02d} Secs"
      except:
          return "Invalid Time"

  def format_time_spent(minutes) -> str:
      """Format time spent in minutes to readable format."""
      if pd.isna(minutes):
          return None

      try:
          total_minutes = int(float(minutes))
          hours = total_minutes // 60
          remaining_mins = total_minutes % 60

          if hours == 0:
              return f"{remaining_mins} Mins"
          elif remaining_mins == 0:
              return f"{hours} Hrs"
          else:
              return f"{hours} Hrs {remaining_mins:02d} Mins"
      except:
          return "Invalid Time"


  def main():
      """Main execution function with command line interface."""

      parser = argparse.ArgumentParser(description="Master SCRPA Processor - Complete M Code Replacement")

      parser.add_argument('--input-file', '-i', type=str,
                         help='Specific input file to process (optional)')
      parser.add_argument('--output-file', '-o', type=str,
                         help='Output file path (optional)')
      parser.add_argument('--export-type', '-t', choices=['auto', 'cad', 'rms'], default='auto',
                         help='Type of export to process (auto, cad, or rms)')
      parser.add_argument('--mode', '-m', choices=['process', 'validate', 'test'], default='process',
                         help='Processing mode')
      parser.add_argument('--project-path', '-p', type=str,
                         help='Project path (uses default if not specified)')

      args = parser.parse_args()

      try:
          # Initialize processor
          processor = MasterSCRPAProcessor(args.project_path)

          if args.mode == 'test':
              # Test mode - validate processor components
              print("Running test mode...")

              # Test CADNotes processor
              cadnotes_test_passed = processor.cadnotes_processor.validate_against_examples()

              # Test file detection
              try:
                  latest_file, detected_source = processor.find_latest_export_file(args.export_type)
                  print(f"Latest file detection: {Path(latest_file).name} ({detected_source.value})")
                  file_detection_passed = True
              except Exception as e:
                  print(f"File detection failed: {e}")
                  file_detection_passed = False

              if cadnotes_test_passed and file_detection_passed:
                  print("All tests passed! Ready for processing.")
              else:
                  print("Some tests failed. Check configuration.")

          elif args.mode == 'validate':
              # Validation mode - run data validation only
              print("Running validation mode...")

              latest_file, detected_source = processor.find_latest_export_file(args.export_type)
              df = pd.read_excel(latest_file, engine='openpyxl')

              # results_df, quality_report = processor.data_validator.run_validation()

              # print("\nValidation Results:")
              # print(results_df.to_string(index=False))

          else:
              # Full processing mode
              print("Running full processing mode...")

              # Run complete pipeline
              final_df, stats = processor.process_complete_pipeline(
                  input_file=args.input_file,
                  output_file=args.output_file,
                  export_type=args.export_type
              )

              print("\nProcessing complete!")
              print("Final statistics:")
              for key, value in stats.items():
                  if not key.endswith('_time') and key != 'errors_encountered':
                      print(f"   {key.replace('_', ' ').title()}: {value}")

      except Exception as e:
          print(f"\nProcessing failed: {str(e)}")
          print(f"Check the log files in: C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\03_output\\logs")
          sys.exit(1)


  if __name__ == "__main__":
      main()

  actual_structure_python_validation.py:
  # 🕒 2025-07-23-06-00-00
  # SCRPA_Time_v2/actual_structure_validation.py
  # Author: R. A. Carucci
  # Purpose: Validation script for actual CAD (Incident column) vs RMS (Incident Type_X columns) structures based on real sample data

  import pandas as pd
  import numpy as np
  from pathlib import Path
  import logging
  from datetime import datetime
  from enum import Enum
  import re
  import warnings
  warnings.filterwarnings('ignore')

  class DataSource(Enum):
      CAD = "CAD"
      RMS = "RMS"
      UNKNOWN = "UNKNOWN"

  class SCRPAActualDataValidator:
      """
      Validates crime data based on actual CAD and RMS export structures
      CAD: ReportNumberNew, Incident, FullAddress2, Time of Call, Disposition
      RMS: Case Number, Incident Type_1, Incident Type_2, Incident Type_3
      """

      def __init__(self, data_path: str):
          self.data_path = Path(data_path)

          # Crime patterns based on actual CAD sample data format
          self.crime_patterns = {
              'motor_vehicle_theft': [
                  'MOTOR VEHICLE THEFT',
                  'AUTO THEFT',
                  'MV THEFT',
                  'VEHICLE THEFT'
              ],
              'burglary_auto': [
                  'BURGLARY.*AUTO',
                  'BURGLARY.*VEHICLE',
                  'AUTO.*BURGLARY'
              ],
              'burglary_commercial': [
                  'BURGLARY.*COMMERCIAL',
                  'COMMERCIAL.*BURGLARY'
              ],
              'burglary_residence': [
                  'BURGLARY.*RESIDENCE',
                  'BURGLARY.*RESIDENTIAL',
                  'RESIDENTIAL.*BURGLARY'
              ],
              'robbery': ['ROBBERY'],
              'sexual': ['SEXUAL']
          }

          # Configure logging
          log_filename = f'scrpa_validation_{datetime.now().strftime("%Y%m%d")}.log'

          # Clear any existing handlers to prevent duplicates
          for handler in logging.root.handlers[:]:
              logging.root.removeHandler(handler)

          # File handler with UTF-8 encoding
          file_handler = logging.FileHandler(log_filename, encoding='utf-8')
          file_handler.setLevel(logging.INFO)

          # Console handler with UTF-8 encoding
          console_handler = logging.StreamHandler()
          console_handler.setLevel(logging.INFO)

          # Create formatter
          formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
          file_handler.setFormatter(formatter)
          console_handler.setFormatter(formatter)

          # Configure root logger
          logging.basicConfig(
              level=logging.INFO,
              handlers=[file_handler, console_handler]
          )

          # Disable propagation to prevent duplicate log entries
          logging.getLogger().propagate = False

          # Ensure console I/O uses UTF-8 encoding for menu and "→" characters
          import sys
          if hasattr(sys.stdout, 'reconfigure'):
              sys.stdout.reconfigure(encoding='utf-8')
          if hasattr(sys.stderr, 'reconfigure'):
              sys.stderr.reconfigure(encoding='utf-8')

      def detect_data_source(self, df: pd.DataFrame) -> tuple[DataSource, dict]:
          """Detect data source and return structure info"""

          structure_info = {
              'columns_found': list(df.columns),
              'total_records': len(df),
              'key_columns': {}
          }

          # Check for CAD structure (based on actual sample)
          cad_indicators = {
              'ReportNumberNew': 'ReportNumberNew' in df.columns,
              'Incident': 'Incident' in df.columns,
              'FullAddress2': 'FullAddress2' in df.columns,
              'Time of Call': 'Time of Call' in df.columns,
              'Disposition': 'Disposition' in df.columns
          }

          # Check for RMS structure
          rms_indicators = {
              'Case Number': 'Case Number' in df.columns,
              'Incident Type_1': 'Incident Type_1' in df.columns,
              'Incident Type_2': 'Incident Type_2' in df.columns,
              'Incident Type_3': 'Incident Type_3' in df.columns
          }

          structure_info['cad_indicators'] = cad_indicators
          structure_info['rms_indicators'] = rms_indicators

          # Determine data source
          cad_score = sum(cad_indicators.values())
          rms_score = sum(rms_indicators.values())

          if cad_score >= 3:  # At least 3 key CAD columns present
              logging.info(f"Detected CAD structure (score: {cad_score}/5)")
              structure_info['detected_source'] = 'CAD'
              structure_info['confidence'] = 'High' if cad_score >= 4 else 'Medium'
              return DataSource.CAD, structure_info

          elif rms_score >= 2:  # At least 2 RMS incident columns present
              logging.info(f"Detected RMS structure (score: {rms_score}/4)")
              structure_info['detected_source'] = 'RMS'
              structure_info['confidence'] = 'High' if rms_score >= 3 else 'Medium'
              return DataSource.RMS, structure_info

          else:
              logging.warning("Unable to clearly identify data source structure")
              structure_info['detected_source'] = 'UNKNOWN'
              structure_info['confidence'] = 'Low'
              return DataSource.UNKNOWN, structure_info

      def prepare_cad_data(self, df: pd.DataFrame) -> pd.DataFrame:
          """Prepare CAD data using actual column structure"""

          # Validate required CAD columns
          required_cols = ['Incident', 'ReportNumberNew']
          missing_cols = [col for col in required_cols if col not in df.columns]
          if missing_cols:
              raise ValueError(f"Missing required CAD columns: {missing_cols}")

          # Create working copy
          df_clean = df.copy()

          # Standardize column names for processing
          df_clean['case_number'] = df_clean['ReportNumberNew']
          df_clean['incident_text'] = df_clean['Incident'].fillna('').astype(str)

          # Remove excluded cases
          excluded_cases = ['25-057654']
          df_clean = df_clean[~df_clean['case_number'].isin(excluded_cases)]

          # Apply disposition filtering if available
          if 'Disposition' in df_clean.columns:
              original_count = len(df_clean)
              df_clean = df_clean[
                  df_clean['Disposition'].str.contains('See Report', case=False, na=False)
              ]
              logging.info(f"CAD disposition filtering: {original_count} → {len(df_clean)} records")

          # Add address and time fields if available
          if 'FullAddress2' in df_clean.columns:
              df_clean['address'] = df_clean['FullAddress2']
          if 'Time of Call' in df_clean.columns:
              df_clean['incident_datetime'] = df_clean['Time of Call']

          logging.info(f"CAD data prepared: {len(df_clean)} records ready for processing")
          return df_clean

      def prepare_rms_data(self, df: pd.DataFrame) -> pd.DataFrame:
          """Prepare RMS data with unpivoting"""

          # Find available incident type columns
          incident_type_cols = [col for col in df.columns if col.startswith('Incident Type_')]
          if not incident_type_cols:
              raise ValueError("RMS data must have 'Incident Type_X' columns")

          logging.info(f"Found RMS incident columns: {incident_type_cols}")

          # Remove excluded cases
          if 'Case Number' in df.columns:
              excluded_cases = ['25-057654']
              df = df[~df['Case Number'].isin(excluded_cases)]

          # Unpivot incident type columns
          id_cols = [col for col in df.columns if col not in incident_type_cols]
          df_unpivoted = pd.melt(
              df,
              id_vars=id_cols,
              value_vars=incident_type_cols,
              var_name='incident_source_column',
              value_name='incident_text'
          )

          # Remove null/empty incident types
          df_unpivoted = df_unpivoted[
              df_unpivoted['incident_text'].notna() &
              (df_unpivoted['incident_text'] != '')
          ]

          # Standardize column names
          if 'Case Number' in df_unpivoted.columns:
              df_unpivoted['case_number'] = df_unpivoted['Case Number']

          logging.info(f"RMS unpivoting: {len(df)} → {len(df_unpivoted)} records")

          # Apply disposition filtering if available
          if 'Disposition' in df_unpivoted.columns:
              original_count = len(df_unpivoted)
              df_unpivoted = df_unpivoted[
                  df_unpivoted['Disposition'].str.contains('See Report', case=False, na=False)
              ]
              logging.info(f"RMS disposition filtering: {original_count} → {len(df_unpivoted)} records")

          return df_unpivoted

      def apply_crime_filters(self, df: pd.DataFrame, data_source: DataSource) -> dict:
          """Apply crime type filtering with enhanced pattern matching"""

          results = {}

          for crime_type, patterns in self.crime_patterns.items():

              # Create vectorized mask for all patterns
              masks = []
              for pattern in patterns:
                  if '.*' in pattern:
                      # Regex pattern
                      mask = df['incident_text'].str.upper().str.contains(
                          pattern.upper(), na=False, regex=True
                      )
                  else:
                      # Simple text contains
                      mask = df['incident_text'].str.upper().str.contains(
                          pattern.upper(), na=False, regex=False
                      )
                  masks.append(mask)

              # Combine all pattern masks with OR
              combined_mask = pd.Series([False] * len(df), index=df.index)
              for mask in masks:
                  combined_mask = combined_mask | mask

              # Apply special logic for burglary subtypes
              if crime_type == 'burglary_auto':
                  # Must contain BURGLARY and (AUTO or VEHICLE), but not COMMERCIAL or RESIDENCE
                  burglary_mask = df['incident_text'].str.upper().str.contains('BURGLARY', na=False)
                  auto_mask = (
                      df['incident_text'].str.upper().str.contains('AUTO', na=False) |
                      df['incident_text'].str.upper().str.contains('VEHICLE', na=False)
                  )
                  exclude_mask = (
                      df['incident_text'].str.upper().str.contains('COMMERCIAL', na=False) |
                      df['incident_text'].str.upper().str.contains('RESIDENCE', na=False)
                  )
                  combined_mask = burglary_mask & auto_mask & ~exclude_mask

              elif crime_type in ['burglary_commercial', 'burglary_residence']:
                  # Exclude auto burglaries
                  auto_exclude = (
                      df['incident_text'].str.upper().str.contains('AUTO', na=False) |
                      df['incident_text'].str.upper().str.contains('VEHICLE', na=False)
                  )
                  combined_mask = combined_mask & ~auto_exclude

              # Count results appropriately by data source
              if data_source == DataSource.RMS and 'case_number' in df.columns:
                  # For RMS, count unique case numbers to avoid duplicates
                  unique_count = df[combined_mask]['case_number'].nunique()
                  results[crime_type] = unique_count
                  logging.info(f"{data_source.value} {crime_type}: {unique_count} unique cases")
              else:
                  # For CAD, count total records
                  record_count = combined_mask.sum()
                  results[crime_type] = record_count
                  logging.info(f"{data_source.value} {crime_type}: {record_count} records")

          # Add total count
          if data_source == DataSource.RMS and 'case_number' in df.columns:
              results['total_records'] = df['case_number'].nunique()
          else:
              results['total_records'] = len(df)

          return results

      def validate_data_quality(self, df: pd.DataFrame, data_source: DataSource, structure_info: dict) -> dict:
          """Comprehensive data quality validation"""

          quality_report = {
              'data_source': data_source.value,
              'detection_confidence': structure_info.get('confidence', 'Unknown'),
              'total_records': len(df),
              'columns_detected': len(df.columns),
              'required_columns_present': True,
              'data_quality_issues': []
          }

          # Check case number availability
          case_col = 'case_number' if 'case_number' in df.columns else None
          if case_col:
              quality_report['null_case_numbers'] = df[case_col].isna().sum()
              quality_report['duplicate_case_numbers'] = df.duplicated(subset=[case_col]).sum()
          else:
              quality_report['data_quality_issues'].append('No case number column found')

          # Check incident data quality
          if 'incident_text' in df.columns:
              quality_report['null_incidents'] = df['incident_text'].isna().sum()
              quality_report['empty_incidents'] = (df['incident_text'] == '').sum()

              # Sample incident patterns for verification
              sample_incidents = df['incident_text'].dropna().head(10).tolist()
              quality_report['sample_incidents'] = sample_incidents
          else:
              quality_report['data_quality_issues'].append('No incident text column found')

          # Disposition data check
          if 'Disposition' in df.columns:
              see_report_count = df['Disposition'].str.contains('See Report', case=False, na=False).sum()
              quality_report['see_report_records'] = see_report_count
              quality_report['disposition_coverage'] = round(see_report_count / len(df) * 100, 2)
          else:
              quality_report['data_quality_issues'].append('No disposition column found')

          # Data source specific checks
          if data_source == DataSource.CAD:
              cad_specific = structure_info.get('cad_indicators', {})
              missing_cad_cols = [col for col, present in cad_specific.items() if not present]
              if missing_cad_cols:
                  quality_report['missing_cad_columns'] = missing_cad_cols

          elif data_source == DataSource.RMS:
              rms_specific = structure_info.get('rms_indicators', {})
              missing_rms_cols = [col for col, present in rms_specific.items() if not present]
              if missing_rms_cols:
                  quality_report['missing_rms_columns'] = missing_rms_cols

          return quality_report

      def run_validation(self, filename_pattern: str = "*.xlsx") -> tuple:
          """Run complete validation process"""

          logging.info("Starting SCRPA validation with actual data structures...")

          try:
              # Find and load data file
              matching_files = list(self.data_path.glob(filename_pattern))
              if not matching_files:
                  raise FileNotFoundError(f"No files matching '{filename_pattern}' in {self.data_path}")

              latest_file = max(matching_files, key=lambda x: x.stat().st_mtime)
              logging.info(f"Processing: {latest_file}")

              df = pd.read_excel(latest_file, engine='openpyxl')
              logging.info(f"Loaded {len(df)} records, {len(df.columns)} columns")

              # Detect data source
              data_source, structure_info = self.detect_data_source(df)
              if data_source == DataSource.UNKNOWN:
                  raise ValueError("Unable to identify data structure as CAD or RMS")

              # Prepare data based on source
              if data_source == DataSource.CAD:
                  prepared_df = self.prepare_cad_data(df)
              else:  # RMS
                  prepared_df = self.prepare_rms_data(df)

              # Run quality validation
              quality_report = self.validate_data_quality(prepared_df, data_source, structure_info)

              # Apply crime filtering
              crime_counts = self.apply_crime_filters(prepared_df, data_source)

              # Create summary results
              summary_data = []
              for crime_type, count in crime_counts.items():
                  if crime_type != 'total_records':
                      summary_data.append({
                          'Crime_Type': crime_type.replace('_', ' ').title(),
                          'Count': count,
                          'Data_Source': data_source.value,
                          'Percentage': round(count / crime_counts['total_records'] * 100, 2) if crime_counts['total_records'] > 0 else 0
                      })

              # Add total row
              summary_data.append({
                  'Crime_Type': 'TOTAL RECORDS',
                  'Count': crime_counts['total_records'],
                  'Data_Source': data_source.value,
                  'Percentage': 100.0
              })

              results_df = pd.DataFrame(summary_data)

              return results_df, quality_report, data_source, structure_info

          except Exception as e:
              logging.error(f"Validation failed: {str(e)}")
              raise

      def export_comprehensive_report(self, results_df: pd.DataFrame, quality_report: dict,
                                    data_source: DataSource, structure_info: dict):
          """Export comprehensive validation report"""

          timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
          output_file = self.data_path / f"SCRPA_Comprehensive_Report_{data_source.value}_{timestamp}.xlsx"

          with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

              # Crime type results
              results_df.to_excel(writer, sheet_name='Crime_Counts', index=False)

              # Data quality report
              quality_df = pd.DataFrame([quality_report]).T
              quality_df.columns = ['Value']
              quality_df.to_excel(writer, sheet_name='Data_Quality')

              # Structure analysis
              structure_df = pd.DataFrame([structure_info]).T
              structure_df.columns = ['Status']
              structure_df.to_excel(writer, sheet_name='Data_Structure')

              # Implementation recommendations
              if data_source == DataSource.CAD:
                  recommendations = [
                      "CAD EXPORT PROCESSING RECOMMENDATIONS",
                      "=====================================",
                      "",
                      "✅ CONFIRMED DATA STRUCTURE:",
                      "- Single 'Incident' column (no unpivoting needed)",
                      "- Case numbers in 'ReportNumberNew' column",
                      "- Addresses in 'FullAddress2' column",
                      "- Time data in 'Time of Call' column",
                      "- Disposition filtering available",
                      "",
                      "📋 M CODE IMPLEMENTATION:",
                      "1. Use ALL_CRIMES_CAD query (no unpivoting)",
                      "2. Reference [ReportNumberNew] for case numbers",
                      "3. Filter directly on [Incident] column",
                      "4. Apply Text.Upper() for case-insensitive matching",
                      "5. Include disposition filtering: 'See Report'",
                      "",
                      "⚡ PERFORMANCE ADVANTAGES:",
                      "- Faster processing (no unpivoting overhead)",
                      "- Simpler debugging and validation",
                      "- Direct alignment with ArcGIS Pro SQL",
                      "",
                      "⚠️ CRITICAL CORRECTIONS NEEDED:",
                      "- Change [Case Number] to [ReportNumberNew]",
                      "- Remove unpivoting logic from queries",
                      "- Add case-insensitive Text.Upper() filtering",
                      "- Verify disposition = 'See Report' filtering"
                  ]
              else:  # RMS
                  recommendations = [
                      "RMS EXPORT PROCESSING RECOMMENDATIONS",
                      "=====================================",
                      "",
                      "✅ CONFIRMED DATA STRUCTURE:",
                      "- Multiple 'Incident Type_1/2/3' columns (unpivoting required)",
                      "- Column names have SPACES not underscores",
                      "- Case numbers in 'Case Number' column",
                      "- Complex incident categorization supported",
                      "",
                      "📋 M CODE IMPLEMENTATION:",
                      "1. Use ALL_CRIMES_RMS query (with unpivoting)",
                      "2. Unpivot 'Incident Type_1', 'Incident Type_2', 'Incident Type_3'",
                      "3. Count unique [Case Number] values in child queries",
                      "4. Handle null/empty incident types after unpivot",
                      "",
                      "⚠️ PERFORMANCE CONSIDERATIONS:",
                      "- Slower processing due to unpivoting",
                      "- Larger memory usage after unpivot",
                      "- Must handle duplicate case counting",
                      "",
                      "🔧 KEY CORRECTIONS:",
                      "- Column names: 'Incident Type_1' (with space)",
                      "- Add validation before unpivoting",
                      "- Count unique case numbers, not total rows",
                      "- Verify disposition filtering post-unpivot"
                  ]

              rec_df = pd.DataFrame({'Recommendations': recommendations})
              rec_df.to_excel(writer, sheet_name='Implementation', index=False)

          logging.info(f"Comprehensive report exported: {output_file}")
          return output_file

  def main():
      """Main execution with enhanced reporting"""

      project_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"

      try:
          validator = SCRPAActualDataValidator(project_path)

          print("🔍 SCRPA Data Structure Validation")
          print("=" * 50)

          # Run comprehensive validation
          results_df, quality_report, data_source, structure_info = validator.run_validation()

          # Display results
          print(f"\n📊 RESULTS - {data_source.value} DATA STRUCTURE DETECTED")
          print("=" * 50)
          print(results_df.to_string(index=False))

          print(f"\n🔍 DATA QUALITY SUMMARY")
          print("=" * 30)
          for key, value in quality_report.items():
              if not key.endswith('_issues') and not key.endswith('_incidents'):
                  print(f"  {key.replace('_', ' ').title()}: {value}")

          # Highlight issues
          if quality_report.get('data_quality_issues'):
              print(f"\n⚠️  DATA QUALITY ISSUES:")
              for issue in quality_report['data_quality_issues']:
                  print(f"  - {issue}")

          # Export comprehensive report
          output_file = validator.export_comprehensive_report(
              results_df, quality_report, data_source, structure_info
          )

          print(f"\n📄 Detailed report saved: {output_file}")

          # Provide immediate next steps
          print(f"\n🎯 IMMEDIATE NEXT STEPS:")
          if data_source == DataSource.CAD:
              print("  1. Update Power BI to use ALL_CRIMES_CAD query")
              print("  2. Change [Case Number] to [ReportNumberNew] in filters")
              print("  3. Remove unpivoting logic from all child queries")
              print("  4. Test with sample data before full refresh")
          else:
              print("  1. Update Power BI to use ALL_CRIMES_RMS query")
              print("  2. Verify column names: 'Incident Type_1' (with space)")
              print("  3. Add unpivoting validation before processing")
              print("  4. Update child queries to count unique case numbers")

          print(f"\n✅ Validation completed successfully!")

      except Exception as e:
          print(f"\n❌ VALIDATION FAILED: {str(e)}")
          print("\nCheck the log file for detailed error information:")
          print(f"  {project_path}/scrpa_validation_{datetime.now().strftime('%Y%m%d')}.log")

  if __name__ == "__main__":
      main()