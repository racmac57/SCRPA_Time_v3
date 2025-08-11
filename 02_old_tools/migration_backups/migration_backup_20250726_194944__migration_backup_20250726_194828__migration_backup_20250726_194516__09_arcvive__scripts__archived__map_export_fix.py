import os
import logging
from config import get_sql_pattern_for_crime
from excel_utils import get_excel_dates
from arcgis_utils import (
    connect_to_arcgis,
    get_layer_by_name,
    filter_layer,
    export_chart_image,
    delete_existing_chart
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def export_chart(crime_type, report_tag=None):
    print("✅ chart_export.py loaded successfully with Excel integration")

    # Determine report date
    from datetime import date
    report_date = report_tag if report_tag else date.today().strftime("%Y_%m_%d")
    logging.info("Looking for report due on: %s", report_date)

    # Get SQL pattern for crime
    pattern = get_sql_pattern_for_crime(crime_type)
    if not pattern:
        logging.error("No SQL pattern found for crime type: %s", crime_type)
        return

    logging.info("Using pattern for %s: %s", crime_type, pattern)

    # Connect to ArcGIS Pro
    project = connect_to_arcgis()
    if not project:
        logging.error("ArcGIS Pro connection failed.")
        return

    # Read 7-day and derived periods from Excel
    dates = get_excel_dates()
    logging.info("Corrected 7-Day period: %s to %s", dates['7DayStart'], dates['7DayEnd'])
    timestamp_dates = {
        '7-Day': f"{dates['7DayStart']} 00:00:00.000",
        '28-Day': f"{dates['28DayStart']} 00:00:00.000",
        'YTD': f"{dates['YTDStart']} 00:00:00.000"
    }
    logging.info("Using corrected timestamp dates: %s", timestamp_dates)

    sql_common = f"calltype LIKE '%{pattern}%' And disposition LIKE '%See Report%'"
    sql_filters = {
        '7-Day': f"{sql_common} And calldate >= timestamp '{timestamp_dates['7-Day']}' And calldate <= timestamp '{dates['7DayEnd']} 23:59:59.999'",
        '28-Day': f"{sql_common} And calldate >= timestamp '{timestamp_dates['28-Day']}'",
        'YTD': f"{sql_common} And calldate >= timestamp '{timestamp_dates['YTD']}'"
    }

    chart_data = {}
    for period in ['7-Day', '28-Day', 'YTD']:
        logging.info("📅 Processing %s data...", period)
        layer_name = f"{crime_type} {period}"
        layer = get_layer_by_name(project, layer_name)
        if not layer:
            logging.warning("❌ Layer not found: %s", layer_name)
            chart_data[period] = 0
            continue

        logging.info("🔎 %s SQL Filter (MATCHING MAP): %s", period, sql_filters[period])
        features = filter_layer(layer, sql_filters[period])
        chart_data[period] = len(features)
        logging.info("📊 %s features found: %d", period, len(features))

    # Chart export
    chart_folder = os.path.join(os.getcwd(), "temp_reports", f"C07W25_{report_date}_7Day", crime_type.replace(" ", "_"))
    os.makedirs(chart_folder, exist_ok=True)
    chart_path = os.path.join(chart_folder, f"{crime_type.replace(' ', '_')}_Chart.png")
    delete_existing_chart(chart_path)
    export_chart_image(chart_path, chart_data, crime_type, dates['7DayStart'], dates['7DayEnd'])
    print(f"✅ Chart saved with MATCHING SQL patterns: {chart_path}\n")

    logging.info("📊 Final Chart Data for %s:", crime_type)
    for k, v in chart_data.items():
        logging.info("  %s: %d incidents", k, v)
    logging.info("📅 7-Day period analyzed: %s to %s", dates['7DayStart'], dates['7DayEnd'])
