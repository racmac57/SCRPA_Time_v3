# chart_export.py

"""
Generates time-of-day bar+line charts for crime types, with explicit color mapping,
proper ordering of time bins, wrapped labels, and dual-axis formatting.
"""
import os
import sys
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt

from config import (
    get_crime_type_folder,
    get_standardized_filename
)


def load_chart_data(crime_type, report_date):
    """
    Stub for loading chart data. Replace with actual data source logic.
    Must return a DataFrame with columns: ['TimeOfDay', '7-Day', '28-Day', 'YTD'].
    """
    folder = get_crime_type_folder(crime_type, report_date.strftime("%Y_%m_%d"))
    file_name = f"{get_standardized_filename(crime_type)}_Stats.xlsx"
    path = os.path.join(folder, file_name)
    if os.path.exists(path):
        return pd.read_excel(path)
    # fallback zero-data frame
    bins = ["00:00-03:59", "04:00-07:59", "08:00-11:59", "12:00-15:59", "16:00-19:59", "20:00-23:59"]
    return pd.DataFrame({
        'TimeOfDay': bins,
        '7-Day': [0] * len(bins),
        '28-Day': [0] * len(bins),
        'YTD': [0] * len(bins)
    })


def export_chart(crime_type):
    """
    Export a time-of-day chart for the specified crime type.
    Expects load_chart_data() to return ['TimeOfDay', '7-Day', '28-Day', 'YTD'].
    """
    # determine report_date
    report_date = date.today()
    if len(sys.argv) > 1:
        try:
            report_date = date.fromisoformat(sys.argv[1].replace('_', '-'))
        except ValueError:
            pass
    date_str = report_date.strftime("%Y_%m_%d")

    # prepare output
    out_folder = get_crime_type_folder(crime_type, date_str)
    os.makedirs(out_folder, exist_ok=True)
    prefix = get_standardized_filename(crime_type)

    # load and organize data
    df = load_chart_data(crime_type, report_date)
    bins = [
        "00:00-03:59", "04:00-07:59",
        "08:00-11:59", "12:00-15:59",
        "16:00-19:59", "20:00-23:59"
    ]
    df['TOD'] = pd.Categorical(df['TimeOfDay'], categories=bins, ordered=True)
    df = df.sort_values('TOD')

    # plotting
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(df))
    width = 0.35

    ax.bar([i - width/2 for i in x], df['7-Day'], width=width,
           label='7-Day', color='seagreen', edgecolor='black')
    ax.bar([i + width/2 for i in x], df['28-Day'], width=width,
           label='28-Day', color='firebrick', edgecolor='black')

    ax2 = ax.twinx()
    ax2.plot(x, df['YTD'], marker='o', linestyle='-'
             , label='YTD', color='royalblue', linewidth=2)

    # axis formatting
    wrapped = [lbl.replace('-', '\n') for lbl in df['TimeOfDay']]
    ax.set_xticks(x)
    ax.set_xticklabels(wrapped, rotation=30, ha='right')
    ax.set_title(f"{crime_type} - Calls by Time of Day    {date_str}", fontsize=14, weight='bold')
    ax.set_xlabel("Time of Day", fontsize=12)
    ax.set_ylabel("Incident Count (7-Day & 28-Day)", fontsize=12)
    ax2.set_ylabel("Incident Count (YTD)", fontsize=12)

    # legends
    bar_legend = ax.legend(loc='upper left', title='Period')
    ax2.legend(loc='upper right')
    ax.add_artist(bar_legend)

    fig.tight_layout()

    out_path = os.path.join(out_folder, f"{prefix}_Chart.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return True

# map_export.py
"""
Exports 7-Day crime maps from ArcGIS Pro with Excel-based filtering.
Creates placeholders when no incidents exist.
"""
import os
import glob
import logging
from datetime import datetime, date
import arcpy
from PIL import Image, ImageDraw, ImageFont
from config import (
    APR_PATH,
    get_7day_period_dates,
    get_standardized_filename,
    get_crime_type_folder,
    get_sql_pattern_for_crime
)

logging.basicConfig(level=logging.INFO)

def validate_config():
    if not APR_PATH or not os.path.exists(APR_PATH):
        arcpy.AddError(f"Invalid APR_PATH: {APR_PATH}")
        return False
    return True


def build_sql_filter_7day_excel(crime_type, start_date, end_date):
    s_ts = f"{start_date:%Y-%m-%d} 00:00:00.000"
    e_ts = f"{end_date:%Y-%m-%d} 23:59:59.999"
    pattern = get_sql_pattern_for_crime(crime_type)
    cond = ' OR '.join(f"calltype LIKE '%{p}%'" for p in (pattern if isinstance(pattern, list) else [pattern]))
    return (
        f"{cond} AND disposition LIKE '%See Report%' "
        f"AND calldate >= timestamp '{s_ts}' "
        f"AND calldate <= timestamp '{e_ts}'"
    )

def create_placeholder_image(crime_type, output_path):
    width, height = 1148, 888
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype('arial.ttf', 48)
        text_font = ImageFont.truetype('arial.ttf', 32)
    except IOError:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    def center(text, font, y):
        w, _ = draw.textsize(text, font=font)
        draw.text(((width-w)//2, y), text, fill='black', font=font)

    center(crime_type, title_font, height//4)
    center('No incidents in 7-day period', text_font, height//2)
    img.save(output_path, 'PNG', dpi=(200,200))
    return True


def export_map_to_png(layout, out_folder, prefix):
    for f in glob.glob(os.path.join(out_folder, f"{prefix}_Map*.png")):
        os.remove(f)
    path = os.path.join(out_folder, f"{prefix}_Map.png")
    layout.exportToPNG(path, resolution=200)
    return os.path.exists(path)


def export_maps(crime_type, output_folder, args):
    if not validate_config():
        return False
    try:
        date_str = args[2]
        ref_date = datetime.strptime(date_str, '%Y_%m_%d').date()
    except Exception:
        ref_date = date.today()
        date_str = ref_date.strftime('%Y_%m_%d')

    folder = get_crime_type_folder(crime_type, date_str)
    prefix = get_standardized_filename(crime_type)

    aprx = arcpy.mp.ArcGISProject(APR_PATH)
    layout = aprx.listLayouts('Crime Report Legend')[0]
    m = layout.listElements('MAPFRAME_ELEMENT')[0].map

    orig_states = {lyr.name:{'vis':lyr.visible,'trans':lyr.transparency} for lyr in m.listLayers()}
    for lyr in m.listLayers(): lyr.visible = False
    for lyr in m.listLayers():
        if any(b in lyr.name for b in ['OpenStreetMap','Streets']):
            lyr.visible, lyr.transparency = True, 0

    start, end = get_7day_period_dates(ref_date)
    layer_name = f"{crime_type} 7-Day"
    target = next((lyr for lyr in m.listLayers() if lyr.name == layer_name), None)
    if not target:
        return create_placeholder_image(crime_type, os.path.join(folder, f"{prefix}_Map.png"))
    target.visible = True
    target.definitionQuery = build_sql_filter_7day_excel(crime_type, start, end)

    count = int(arcpy.GetCount_management(target).getOutput(0))
    if count == 0:
        for lyr in m.listLayers(): lyr.visible, lyr.transparency = orig_states[lyr.name]['vis'], orig_states[lyr.name]['trans']
        return create_placeholder_image(crime_type, os.path.join(folder, f"{prefix}_Map.png"))

    success = export_map_to_png(layout, folder, prefix)
    for lyr in m.listLayers(): lyr.visible, lyr.transparency = orig_states[lyr.name]['vis'], orig_states[lyr.name]['trans']
    return success
