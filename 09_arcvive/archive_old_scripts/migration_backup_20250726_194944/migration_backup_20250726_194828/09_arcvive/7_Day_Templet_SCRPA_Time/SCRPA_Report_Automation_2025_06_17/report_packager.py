# 🕒 2025-05-27
# crime_report_tool/report_packager.py
# Author: R. Carucci
# Purpose: Package charts, maps, and records into a final PDF and ZIP
# Last updated: 2025-05-27

import os
import glob
import logging
from datetime import datetime
from fpdf import FPDF
from zipfile import ZipFile
import shutil
from pathlib import Path

# Import configuration for consistent file naming
try:
    from config import CHART_OUTPUT_DIR, get_sanitized_filename
except ImportError:
    logging.warning("Could not import configuration, using fallback values")
    CHART_OUTPUT_DIR = r"C:\GIS_Data\SCRPA\charts"
    
    def get_sanitized_filename(text):
        return text.replace(" ", "_").replace("&", "And").replace("/", "_")

class ReportPackager:
    """
    Class to handle packaging of crime reports into PDF and ZIP formats.
    """
    
    def __init__(self):
        self.temp_files = []  # Track temporary files for cleanup
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_temp_files()
    
    def cleanup_temp_files(self):
        """Clean up any temporary files created during processing."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logging.debug(f"🧹 Cleaned up temp file: {temp_file}")
            except Exception as e:
                logging.warning(f"⚠️ Could not clean up temp file {temp_file}: {e}")
        self.temp_files.clear()

def validate_dependencies():
    """
    Validate that required libraries are available.
    
    Returns:
        tuple: (is_valid, list_of_missing)
    """
    missing_deps = []
    
    try:
        import fpdf
    except ImportError:
        missing_deps.append("fpdf2 (install with: pip install fpdf2)")
    
    return len(missing_deps) == 0, missing_deps

def clean_old_reports(output_folder, crime_type):
    """
    Clean up old report files for the given crime type.
    
    Args:
        output_folder (str): Directory containing reports
        crime_type (str): Type of crime to clean reports for
        
    Returns:
        int: Number of files cleaned up
    """
    try:
        sanitized_crime = get_sanitized_filename(crime_type)
        patterns = [
            f"{sanitized_crime}_Report*.pdf",
            f"{sanitized_crime}_Report*.zip"
        ]
        
        cleaned_count = 0
        for pattern in patterns:
            pattern_path = os.path.join(output_folder, pattern)
            old_files = glob.glob(pattern_path)
            
            for file_path in old_files:
                try:
                    os.remove(file_path)
                    logging.info(f"🧹 Removed old report: {os.path.basename(file_path)}")
                    cleaned_count += 1
                except Exception as e:
                    logging.warning(f"⚠️ Could not remove old report {file_path}: {e}")
        
        return cleaned_count
        
    except Exception as e:
        logging.error(f"❌ Error during cleanup: {e}")
        return 0

def find_report_files(output_folder, crime_type):
    """
    Find all report files for a given crime type.
    
    Args:
        output_folder (str): Directory to search
        crime_type (str): Type of crime
        
    Returns:
        dict: Dictionary with file paths (keys: 'map', 'chart', 'table', 'chart_periods')
    """
    sanitized_crime = get_sanitized_filename(crime_type)
    
    files = {
        'map': os.path.join(output_folder, f"{sanitized_crime}_Map.png"),
        'table': os.path.join(output_folder, f"{sanitized_crime}_Records.csv"),
        'chart_periods': []
    }
    
    # Look for chart files (multiple periods)
    chart_patterns = [
        f"{sanitized_crime}_7_Day_Chart.png",
        f"{sanitized_crime}_28_Day_Chart.png", 
        f"{sanitized_crime}_YTD_Chart.png"
    ]
    
    # Check in both output folder and chart directory
    search_dirs = [output_folder, CHART_OUTPUT_DIR]
    
    for pattern in chart_patterns:
        found = False
        for search_dir in search_dirs:
            chart_path = os.path.join(search_dir, pattern)
            if os.path.exists(chart_path):
                files['chart_periods'].append(chart_path)
                found = True
                break
        
        if not found:
            logging.warning(f"⚠️ Chart file not found: {pattern}")
    
    # Log what was found
    for key, value in files.items():
        if key == 'chart_periods':
            logging.info(f"📊 Found {len(value)} chart files for {crime_type}")
        else:
            status = "✅ Found" if os.path.exists(value) else "❌ Missing"
            logging.info(f"{status}: {os.path.basename(value)}")
    
    return files

def create_pdf_report(crime_type, files, output_folder, args=None):
    """
    Create a PDF report with maps, charts, and data summary.
    
    Args:
        crime_type (str): Type of crime
        files (dict): Dictionary of file paths
        output_folder (str): Output directory
        args: Command line arguments (optional)
        
    Returns:
        tuple: (success, pdf_path)
    """
    try:
        sanitized_crime = get_sanitized_filename(crime_type)
        pdf_path = os.path.join(output_folder, f"{sanitized_crime}_Report.pdf")
        
        # Create PDF with better configuration
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # === TITLE PAGE ===
        pdf.add_page()
        pdf.set_font("Arial", "B", 20)
        
        # Title
        pdf.cell(0, 20, f"{crime_type} Analysis Report", ln=True, align='C')
        
        # Date
        pdf.set_font("Arial", "", 12)
        report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        pdf.cell(0, 10, f"Generated: {report_date}", ln=True, align='C')
        pdf.ln(10)
        
        # Summary section
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Report Contents:", ln=True)
        pdf.set_font("Arial", "", 11)
        
        content_summary = []
        if os.path.exists(files['map']):
            content_summary.append("• Geographic crime distribution map")
        if files['chart_periods']:
            content_summary.append(f"• Time analysis charts ({len(files['chart_periods'])} periods)")
        if os.path.exists(files['table']):
            content_summary.append("• Detailed incident records (CSV)")
        
        if not content_summary:
            content_summary.append("• No report components found")
        
        for item in content_summary:
            pdf.cell(0, 8, item, ln=True)
        
        # === MAP SECTION ===
        if os.path.exists(files['map']):
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Geographic Distribution", ln=True, align='C')
            pdf.ln(5)
            
            try:
                # Calculate image dimensions to fit page
                page_width = pdf.w - 20  # Account for margins
                pdf.image(files['map'], x=10, y=pdf.get_y(), w=page_width)
                logging.info("✅ Added map to PDF report")
            except Exception as e:
                pdf.set_font("Arial", "", 12)
                pdf.cell(0, 10, f"[Map Load Error: {str(e)}]", ln=True, align='C')
                logging.error(f"❌ Error adding map to PDF: {e}")
        
        # === CHARTS SECTION ===
        if files['chart_periods']:
            for i, chart_path in enumerate(files['chart_periods']):
                if os.path.exists(chart_path):
                    pdf.add_page()
                    
                    # Extract period from filename
                    filename = os.path.basename(chart_path)
                    if "7_Day" in filename:
                        period_name = "7-Day Analysis"
                    elif "28_Day" in filename:
                        period_name = "28-Day Analysis"
                    elif "YTD" in filename:
                        period_name = "Year-to-Date Analysis"
                    else:
                        period_name = f"Time Analysis {i+1}"
                    
                    pdf.set_font("Arial", "B", 16)
                    pdf.cell(0, 10, period_name, ln=True, align='C')
                    pdf.ln(5)
                    
                    try:
                        page_width = pdf.w - 20
                        pdf.image(chart_path, x=10, y=pdf.get_y(), w=page_width)
                        logging.info(f"✅ Added chart to PDF: {os.path.basename(chart_path)}")
                    except Exception as e:
                        pdf.set_font("Arial", "", 12)
                        pdf.cell(0, 10, f"[Chart Load Error: {str(e)}]", ln=True, align='C')
                        logging.error(f"❌ Error adding chart to PDF: {e}")
        
        # === DATA SECTION ===
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Data Summary", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", "", 12)
        if os.path.exists(files['table']):
            pdf.cell(0, 10, "• Detailed incident records are included in the ZIP archive", ln=True)
            
            # Try to get basic CSV stats
            try:
                import pandas as pd
                df = pd.read_csv(files['table'])
                pdf.cell(0, 8, f"• Total incidents in dataset: {len(df)}", ln=True)
                if 'Period' in df.columns:
                    period_counts = df['Period'].value_counts()
                    for period, count in period_counts.items():
                        pdf.cell(0, 8, f"  - {period}: {count} incidents", ln=True)
            except Exception as e:
                logging.warning(f"⚠️ Could not read CSV stats: {e}")
                pdf.cell(0, 8, "• CSV file statistics unavailable", ln=True)
        else:
            pdf.cell(0, 10, "• No detailed incident records available", ln=True)
        
        # Save PDF
        pdf.output(pdf_path)
        logging.info(f"✅ PDF report created: {pdf_path}")
        
        return True, pdf_path
        
    except Exception as e:
        logging.error(f"❌ Error creating PDF report: {e}")
        return False, None

def create_zip_archive(crime_type, files, pdf_path, output_folder):
    """
    Create ZIP archive containing all report components.
    
    Args:
        crime_type (str): Type of crime
        files (dict): Dictionary of file paths
        pdf_path (str): Path to PDF report
        output_folder (str): Output directory
        
    Returns:
        tuple: (success, zip_path)
    """
    try:
        sanitized_crime = get_sanitized_filename(crime_type)
        zip_path = os.path.join(output_folder, f"{sanitized_crime}_Report.zip")
        
        with ZipFile(zip_path, 'w') as zipf:
            files_added = 0
            
            # Add PDF report
            if pdf_path and os.path.exists(pdf_path):
                zipf.write(pdf_path, arcname=os.path.basename(pdf_path))
                files_added += 1
                logging.info(f"📦 Added to ZIP: {os.path.basename(pdf_path)}")
            
            # Add map
            if os.path.exists(files['map']):
                zipf.write(files['map'], arcname=os.path.basename(files['map']))
                files_added += 1
                logging.info(f"📦 Added to ZIP: {os.path.basename(files['map'])}")
            
            # Add charts
            for chart_path in files['chart_periods']:
                if os.path.exists(chart_path):
                    zipf.write(chart_path, arcname=os.path.basename(chart_path))
                    files_added += 1
                    logging.info(f"📦 Added to ZIP: {os.path.basename(chart_path)}")
            
            # Add CSV data
            if os.path.exists(files['table']):
                zipf.write(files['table'], arcname=os.path.basename(files['table']))
                files_added += 1
                logging.info(f"📦 Added to ZIP: {os.path.basename(files['table'])}")
        
        if files_added > 0:
            # Get ZIP file size for logging
            zip_size = os.path.getsize(zip_path)
            logging.info(f"✅ ZIP archive created: {zip_path} ({files_added} files, {zip_size:,} bytes)")
            return True, zip_path
        else:
            logging.warning(f"⚠️ No files were added to ZIP archive")
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return False, None
            
    except Exception as e:
        logging.error(f"❌ Error creating ZIP archive: {e}")
        return False, None

def package_report(crime_type, output_folder, args=None):
    """
    Main function to package charts, maps, and records into PDF and ZIP.
    
    Args:
        crime_type (str): Type of crime to package
        output_folder (str): Directory containing report components
        args: Command line arguments (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logging.info(f"📦 Starting report packaging for: {crime_type}")
        
        # Validate dependencies
        deps_valid, missing_deps = validate_dependencies()
        if not deps_valid:
            logging.error(f"❌ Missing dependencies: {missing_deps}")
            return False
        
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Clean up old reports
        cleaned_count = clean_old_reports(output_folder, crime_type)
        if cleaned_count > 0:
            logging.info(f"🧹 Cleaned up {cleaned_count} old report files")
        
        # Find all report files
        files = find_report_files(output_folder, crime_type)
        
        # Check if we have any files to package
        has_files = (os.path.exists(files['map']) or 
                    len(files['chart_periods']) > 0 or 
                    os.path.exists(files['table']))
        
        if not has_files:
            logging.warning(f"⚠️ No report components found for {crime_type}")
            return False
        
        # Create PDF report
        pdf_success, pdf_path = create_pdf_report(crime_type, files, output_folder, args)
        
        if not pdf_success:
            logging.error(f"❌ Failed to create PDF report for {crime_type}")
            return False
        
        # Create ZIP archive if requested or if args indicate archiving
        create_archive = True  # Default to creating archive
        if args and hasattr(args, 'archive'):
            create_archive = args.archive
        elif args and isinstance(args, list) and len(args) > 3:
            # If args is a list (from main.py), check export_reports_flag
            create_archive = True  # Default behavior
        
        if create_archive:
            zip_success, zip_path = create_zip_archive(crime_type, files, pdf_path, output_folder)
            if not zip_success:
                logging.warning(f"⚠️ Failed to create ZIP archive for {crime_type}")
                # Don't return False here - PDF creation was successful
        
        logging.info(f"✅ Report packaging completed successfully for {crime_type}")
        return True
        
    except Exception as e:
        logging.error(f"❌ Critical error in package_report for {crime_type}: {e}")
        return False

# For standalone testing
if __name__ == "__main__":
    # Set up basic logging for standalone testing
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Test with sample data
    test_crime_type = "Burglary"
    test_output_folder = r"C:\temp\test_reports"
    
    print(f"Testing report packaging for: {test_crime_type}")
    success = package_report(test_crime_type, test_output_folder)
    
    if success:
        print("✅ Report packaging test completed successfully")
    else:
        print("❌ Report packaging test failed")