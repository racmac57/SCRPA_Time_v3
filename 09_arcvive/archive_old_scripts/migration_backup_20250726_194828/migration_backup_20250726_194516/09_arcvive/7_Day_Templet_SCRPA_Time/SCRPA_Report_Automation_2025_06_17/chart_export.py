#🕒 2025-06-17-22-18-00
# SCRPA_Time/chart_export.py
# Author: R. A. Carucci
# Purpose: Generate crime incident bar charts (7-Day, 28-Day, YTD) using ArcGIS layer filters built from flexible SQL patterns, count incidents, adjust chart layout dynamically, and auto-embed exported charts into PowerPoint templates.

import os
import logging
import arcpy
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from config import (
    get_sql_pattern_for_crime,
    get_7day_period_dates,
    get_28day_period_dates,
    get_ytd_period_dates,
    get_crime_type_folder,
    get_output_folder,
    log_incident_summary,
    embed_chart_into_ppt
)

def build_sql_filter(crime_type, date_range):
    start, end = date_range
    pattern = get_sql_pattern_for_crime(crime_type)

    base_filter = f"disposition LIKE '%See Report%' AND calldate BETWEEN date '{start}' AND date '{end}'"

    if not pattern:
        return base_filter

    if isinstance(pattern, list):
        condition = " OR ".join([f"calltype LIKE '%{p}%'" for p in pattern])
    else:
        condition = f"calltype LIKE '%{pattern}%'"

    return f"({condition}) AND {base_filter}"

def generate_chart(crime_type, report_date_str, period_label):
    report_date = datetime.strptime(report_date_str, "%Y_%m_%d").date()

    if period_label == "7-Day":
        date_range = get_7day_period_dates(report_date)
    elif period_label == "28-Day":
        date_range = get_28day_period_dates(report_date)
    elif period_label == "YTD":
        date_range = get_ytd_period_dates(report_date)
    else:
        logging.warning(f"❌ Unknown period: {period_label}")
        return

    sql = build_sql_filter(crime_type, date_range)
    logging.info(f"🔎 SQL Filter for {crime_type} ({period_label}): {sql}")

    aprx_path = r"C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\_25_SCRPA\\TIME_Based\\7_Day_Templet_SCRPA_Time\\7_Day_Templet_SCRPA_Time.aprx"
    aprx = arcpy.mp.ArcGISProject(aprx_path)
    map_obj = aprx.listMaps()[0]

    layer_name = f"{crime_type} {period_label}"
    lyr = next((l for l in map_obj.listLayers() if l.name == layer_name), None)
    if not lyr:
        logging.warning(f"❌ Layer not found: {layer_name}")
        return

    lyr.definitionQuery = sql
    features = [row for row in arcpy.da.SearchCursor(lyr, ["calldate"])]
    logging.info(f"📊 Features found: {len(features)}")

    hour_bins = {
        "00:00-03:59": 0, "04:00-07:59": 0, "08:00-11:59": 0,
        "12:00-15:59": 0, "16:00-19:59": 0, "20:00-23:59": 0
    }

    for (calldate,) in features:
        hour = calldate.hour
        if hour < 4:
            hour_bins["00:00-03:59"] += 1
        elif hour < 8:
            hour_bins["04:00-07:59"] += 1
        elif hour < 12:
            hour_bins["08:00-11:59"] += 1
        elif hour < 16:
            hour_bins["12:00-15:59"] += 1
        elif hour < 20:
            hour_bins["16:00-19:59"] += 1
        else:
            hour_bins["20:00-23:59"] += 1

    counts = list(hour_bins.values())
    labels = list(hour_bins.keys())
    max_count = max(counts)
    total = sum(counts)

    fig, ax = plt.subplots(figsize=(10, 6 if len(counts) <= 6 else 8))
    bars = ax.bar(labels, counts, color="steelblue")
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3, str(count), ha='center', va='bottom')

    ax.set_title(f"{crime_type} - {period_label} Distribution", pad=20)
    ax.set_ylabel("Number of Incidents")
    ax.set_ylim(top=max_count + 2)

    if max_count >= 6:
        ax.title.set_position([.5, 1.10])
        ax.legend([f"Total: {total}"], loc='upper right')
    else:
        ax.title.set_position([.5, 1.05])
        ax.legend([f"Total: {total}"], loc='best')

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    output_folder = get_crime_type_folder(crime_type, report_date_str)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    filename = os.path.join(output_folder, f"{crime_type.replace(' ', '_')}_{period_label.replace('-', '')}_Chart.png")
    plt.savefig(filename)
    plt.close()
    logging.info(f"✅ Saved chart to {filename}")

    log_incident_summary(crime_type, report_date_str, total, counts, labels, period_label)

    embed_chart_into_ppt(crime_type, period_label, filename)
    logging.info(f"📥 Embedded {period_label} chart into PowerPoint for {crime_type}")
