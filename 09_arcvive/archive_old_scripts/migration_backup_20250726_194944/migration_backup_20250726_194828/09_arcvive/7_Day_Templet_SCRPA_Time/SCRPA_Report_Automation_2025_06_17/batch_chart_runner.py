#🕒 2025-06-17-20-34-00
# SCRPA_Time/batch_run_charts.py
# Author: R. A. Carucci
# Purpose: Batch runner script to generate 7-day crime distribution bar charts for all configured crime types using a given report date.

import logging
from chart_export import generate_chart

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def run_all_charts(report_date_str):
    """
    Generate charts for all crime types for a given report date.
    """
    crime_types = [
        "Robbery",
        "MV Theft",
        "Burglary Auto",
        "Burglary Comm & Res",
        "Sexual Offenses"
    ]

    for crime_type in crime_types:
        try:
            logging.info(f"▶️ Generating chart for: {crime_type}")
            generate_chart(crime_type, report_date_str)
        except Exception as e:
            logging.error(f"❌ Failed to generate chart for {crime_type}: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python batch_run_charts.py <YYYY_MM_DD>")
        sys.exit(1)

    run_all_charts(sys.argv[1])
