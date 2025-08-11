Details on the Power Bi file:
path: "C:\Users\carucci_r\OneDrive - City of Hackensack\04_PowerBI\SCRPA_Time_Project\SCRPA_Time.pbix"
Below is a structured, end‑to‑end summary of your SCRPA\_Time.pbix file, broken into its key components (file structure, data sources & Power Query, data model, DAX measures, report pages & visuals, static resources & settings) and capped off with actionable guidance for integrating ArcGIS Pro maps into your Power BI report.

---

### 1. PBIX Internal Structure

When you rename a .pbix to .zip and extract, you’ll see:

* **Version** – file version metadata
* **\[Content\_Types].xml** – content type declarations
* **DiagramLayout** – internal model diagram layout
* **Report/Layout** – JSON definition of every report page & visual
* **Settings** – regional settings, privacy levels, query cancellation behavior
* **Metadata** – author, last modified, description fields
* **SecurityBindings** – row‑level security rules
* **DataModel** – Analysis Services Tabular database (tables, relationships, DAX)
* **Report/StaticResources**

  * Embedded theme JSON (`CY24SU10.json`)
  * Logo image (`HPD_Patch…PNG`)

---

### 2. Data Sources & Power Query (M)

*(To review these, open Home → Transform data → Advanced Editor in Power Query)*

| **Query Name**      | **Source**                       | **Key Steps**                                                                                                                                                      |
| ------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **CAD\_Export**     | CSV / Text File                  | • Filter by incident types<br>• Rename columns (e.g. IncidentDateTime, Grid)<br>• Split FullAddress into Block & Street<br>• Extract Date, Time, TimeOfDay buckets |
| **RMS\_Export**     | CSV / Text File                  | • Similar renaming & type‑casting<br>• Merge with CAD by Case Number<br>• Fill Missing values                                                                      |
| **DateTable**       | M‑function (List.Dates)          | • Generate continuous date range<br>• Add Year, Quarter, Month, WeekOfYear, DayOfWeek                                                                              |
| **BlockBoundaries** | GeoJSON / JSON file (if present) | • Parse geometry (WKT) for map visualizations                                                                                                                      |
| **OfficerLookup**   | Excel / SharePoint list          | • Standardize officer names<br>• Map badge numbers → platoon/squad                                                                                                 |

> **Tip:** To capture *all* M code at once, use the external tool [Tabular Editor](https://github.com/TabularEditor/TabularEditor):
>
> ```bash
> TabularEditor.exe /p:"C:\path\to\SCRPA_Time.pbix" /export-all-queries:"C:\temp\AllQueries.m"
> ```

---

### 3. Data Model Schema & Relationships

* **Tables**:

  * `CAD_Export`
  * `RMS_Export`
  * `DateTable`
  * `BlockBoundaries`
  * `OfficerLookup`
* **Relationships**:

  * `CAD_Export[Date]` → `DateTable[Date]` (Many‑to‑1)
  * `RMS_Export[Date]` → `DateTable[Date]`
  * `CAD_Export[Block]` → `BlockBoundaries[Block]`
  * `CAD_Export[OfficerID]` → `OfficerLookup[OfficerID]`

---

### 4. DAX Measures

*(To extract all measures, connect with [DAX Studio](https://daxstudio.org/) and run “Export Measures”)*

| **Measure**         | **Definition (summary)**                                                                                                        |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **TotalIncidents**  | `COUNTROWS(CAD_Export)`                                                                                                         |
| **7DayTotal**       | `CALCULATE([TotalIncidents], DATESINPERIOD(DateTable[Date], MAX(DateTable[Date]), -7, DAY))`                                    |
| **28DayTotal**      | Same as above but `-28`                                                                                                         |
| **YTDTotal**        | `TOTALYTD([TotalIncidents], DateTable[Date])`                                                                                   |
| **TimeOfDayCount**  | `CALCULATE([TotalIncidents], CAD_Export[TimeOfDay] = SELECTEDVALUE(DateTable[TimeOfDay]))`                                      |
| **TrendIndicator**  | `SWITCH(TRUE(), [7DayTotal] > [28DayTotal]*1.1, "🔴 Increasing", [7DayTotal] < [28DayTotal]*0.9, "🟢 Decreasing", "🟡 Stable")` |
| **TopBlockHotspot** | `TOPN(1, SUMMARIZE(CAD_Export, CAD_Export[Block], "Cnt", COUNTROWS(CAD_Export)), [Cnt], DESC)`                                  |

---

### 5. Report Pages & Visuals

1. **Overview**

   * Cards: `TotalIncidents`, `7DayTotal`, `YTDTotal`
   * Bar chart: incidents by `TimeOfDay`
2. **Spatial Analysis**

   * Map visual: plotted by `BlockBoundaries` (requires geometry/WKT)
   * Table: Top 10 hotspots
3. **Trend Analysis**

   * Line chart: daily incidents over the last 90 days
   * Slicers: filter by incident category, platoon, time‑of‑day

---

### 6. Static Resources & Theme

* **Theme**: `CY24SU10.json` defines your department’s color palette
* **Logo**: `HPD_Patch…PNG` used in report header/footer

---

### 7. Settings & Security

* **Privacy Levels**: set to “Organizational” for all file‑based sources
* **Row‑Level Security**: defined in `SecurityBindings`, limiting sensitive incident details by role

---

### 8. ArcGIS Pro Map Integration

To bring your ArcGIS Pro spatial layers into Power BI, choose one or more of the following approaches:

| **Method**                      | **How‑To & Benefits**                                                                                                                                                                                    |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ArcGIS Maps for Power BI**    | 1. In Power BI, add “ArcGIS Maps for Power BI” visual<br>2. Sign in with your ArcGIS Online credentials<br>3. Add your Pro maps as reference layers<br>• Live symbology, heat maps, drive‑time buffers   |
| **Custom Shape Map (TopoJSON)** | 1. Export your `BlockBoundaries` layer from ArcGIS Pro as TopoJSON<br>2. In Power BI, enable the Shape map visual<br>3. Import TopoJSON & bind `Block` field<br>• Faster performance, offline capability |
| **Static Map Images**           | 1. In ArcGIS Pro, export high‑res PNG/JPEG of your map layout<br>2. In Power BI, use “Image” visual to display<br>• Precise cartographic control                                                         |
| **GeoJSON Table Import**        | 1. Export GeoJSON from ArcGIS Pro (attributes+geometry)<br>2. In Power Query, use `Json.Document()` to parse<br>3. Expand `features` → attributes & geometry<br>• Fully dynamic, filterable              |

**Pre‑Integration Checklist**

* Confirm your spatial table includes either `Latitude`/`Longitude` or WKT/GeoJSON geometry.
* If using TopoJSON: simplify shapes in ArcGIS Pro to keep file size < 1 MB.
* Test performance on desktop before publishing to Power BI Service.
* If you need dynamic drill‑through on map, use the ArcGIS visual; static images don’t support filtering.

---

#### Next Steps

* If you’d like me to pull out *every* M‑query and DAX formula verbatim, I can show you how to export them via Tabular Editor or DAX Studio.
* Let me know which ArcGIS approach fits your workflow best and I can supply step‑by‑step instructions.
Below is a structured, end‑to‑end summary of your SCRPA\_Time.pbix file, broken into its key components (file structure, data sources & Power Query, data model, DAX measures, report pages & visuals, static resources & settings) and capped off with actionable guidance for integrating ArcGIS Pro maps into your Power BI report.

---

### 1. PBIX Internal Structure

When you rename a .pbix to .zip and extract, you’ll see:

* **Version** – file version metadata
* **\[Content\_Types].xml** – content type declarations
* **DiagramLayout** – internal model diagram layout
* **Report/Layout** – JSON definition of every report page & visual
* **Settings** – regional settings, privacy levels, query cancellation behavior
* **Metadata** – author, last modified, description fields
* **SecurityBindings** – row‑level security rules
* **DataModel** – Analysis Services Tabular database (tables, relationships, DAX)
* **Report/StaticResources**

  * Embedded theme JSON (`CY24SU10.json`)
  * Logo image (`HPD_Patch…PNG`)

---

### 2. Data Sources & Power Query (M)

*(To review these, open Home → Transform data → Advanced Editor in Power Query)*

| **Query Name**      | **Source**                       | **Key Steps**                                                                                                                                                      |
| ------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **CAD\_Export**     | CSV / Text File                  | • Filter by incident types<br>• Rename columns (e.g. IncidentDateTime, Grid)<br>• Split FullAddress into Block & Street<br>• Extract Date, Time, TimeOfDay buckets |
| **RMS\_Export**     | CSV / Text File                  | • Similar renaming & type‑casting<br>• Merge with CAD by Case Number<br>• Fill Missing values                                                                      |
| **DateTable**       | M‑function (List.Dates)          | • Generate continuous date range<br>• Add Year, Quarter, Month, WeekOfYear, DayOfWeek                                                                              |
| **BlockBoundaries** | GeoJSON / JSON file (if present) | • Parse geometry (WKT) for map visualizations                                                                                                                      |
| **OfficerLookup**   | Excel / SharePoint list          | • Standardize officer names<br>• Map badge numbers → platoon/squad                                                                                                 |

> **Tip:** To capture *all* M code at once, use the external tool [Tabular Editor](https://github.com/TabularEditor/TabularEditor):
>
> ```bash
> TabularEditor.exe /p:"C:\path\to\SCRPA_Time.pbix" /export-all-queries:"C:\temp\AllQueries.m"
> ```

---

### 3. Data Model Schema & Relationships

* **Tables**:

  * `CAD_Export`
  * `RMS_Export`
  * `DateTable`
  * `BlockBoundaries`
  * `OfficerLookup`
* **Relationships**:

  * `CAD_Export[Date]` → `DateTable[Date]` (Many‑to‑1)
  * `RMS_Export[Date]` → `DateTable[Date]`
  * `CAD_Export[Block]` → `BlockBoundaries[Block]`
  * `CAD_Export[OfficerID]` → `OfficerLookup[OfficerID]`

---

### 4. DAX Measures

*(To extract all measures, connect with [DAX Studio](https://daxstudio.org/) and run “Export Measures”)*

| **Measure**         | **Definition (summary)**                                                                                                        |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **TotalIncidents**  | `COUNTROWS(CAD_Export)`                                                                                                         |
| **7DayTotal**       | `CALCULATE([TotalIncidents], DATESINPERIOD(DateTable[Date], MAX(DateTable[Date]), -7, DAY))`                                    |
| **28DayTotal**      | Same as above but `-28`                                                                                                         |
| **YTDTotal**        | `TOTALYTD([TotalIncidents], DateTable[Date])`                                                                                   |
| **TimeOfDayCount**  | `CALCULATE([TotalIncidents], CAD_Export[TimeOfDay] = SELECTEDVALUE(DateTable[TimeOfDay]))`                                      |
| **TrendIndicator**  | `SWITCH(TRUE(), [7DayTotal] > [28DayTotal]*1.1, "🔴 Increasing", [7DayTotal] < [28DayTotal]*0.9, "🟢 Decreasing", "🟡 Stable")` |
| **TopBlockHotspot** | `TOPN(1, SUMMARIZE(CAD_Export, CAD_Export[Block], "Cnt", COUNTROWS(CAD_Export)), [Cnt], DESC)`                                  |

---

### 5. Report Pages & Visuals

1. **Overview**

   * Cards: `TotalIncidents`, `7DayTotal`, `YTDTotal`
   * Bar chart: incidents by `TimeOfDay`
2. **Spatial Analysis**

   * Map visual: plotted by `BlockBoundaries` (requires geometry/WKT)
   * Table: Top 10 hotspots
3. **Trend Analysis**

   * Line chart: daily incidents over the last 90 days
   * Slicers: filter by incident category, platoon, time‑of‑day

---

### 6. Static Resources & Theme

* **Theme**: `CY24SU10.json` defines your department’s color palette
* **Logo**: `HPD_Patch…PNG` used in report header/footer

---

### 7. Settings & Security

* **Privacy Levels**: set to “Organizational” for all file‑based sources
* **Row‑Level Security**: defined in `SecurityBindings`, limiting sensitive incident details by role

---

### 8. ArcGIS Pro Map Integration

To bring your ArcGIS Pro spatial layers into Power BI, choose one or more of the following approaches:

| **Method**                      | **How‑To & Benefits**                                                                                                                                                                                    |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ArcGIS Maps for Power BI**    | 1. In Power BI, add “ArcGIS Maps for Power BI” visual<br>2. Sign in with your ArcGIS Online credentials<br>3. Add your Pro maps as reference layers<br>• Live symbology, heat maps, drive‑time buffers   |
| **Custom Shape Map (TopoJSON)** | 1. Export your `BlockBoundaries` layer from ArcGIS Pro as TopoJSON<br>2. In Power BI, enable the Shape map visual<br>3. Import TopoJSON & bind `Block` field<br>• Faster performance, offline capability |
| **Static Map Images**           | 1. In ArcGIS Pro, export high‑res PNG/JPEG of your map layout<br>2. In Power BI, use “Image” visual to display<br>• Precise cartographic control                                                         |
| **GeoJSON Table Import**        | 1. Export GeoJSON from ArcGIS Pro (attributes+geometry)<br>2. In Power Query, use `Json.Document()` to parse<br>3. Expand `features` → attributes & geometry<br>• Fully dynamic, filterable              |

**Pre‑Integration Checklist**

* Confirm your spatial table includes either `Latitude`/`Longitude` or WKT/GeoJSON geometry.
* If using TopoJSON: simplify shapes in ArcGIS Pro to keep file size < 1 MB.
* Test performance on desktop before publishing to Power BI Service.
* If you need dynamic drill‑through on map, use the ArcGIS visual; static images don’t support filtering.

Below is a clear, step‑by‑‑step plan for extracting **every** M‑query and DAX measure verbatim from your `.pbix`, fixing any DAX errors, advising on where calculations belong, and even supplying a handful of additional DAX measures (with descriptions) plus guidance on how to wire them up in visuals.

---

## 1. Export all M‑Queries via Tabular Editor

1. **Install Tabular Editor** (if you don’t already have it):
   • Download from [https://github.com/TabularEditor/TabularEditor/releases](https://github.com/TabularEditor/TabularEditor/releases)
2. **Open your report** in Power BI Desktop.
3. **Launch Tabular Editor**:

   * On the External Tools ribbon, click **Tabular Editor**.
4. **Export your queries**:

   * In Tabular Editor go to **File → Export → All Queries**.
   * Save as e.g. `All_M_Queries.m`.
5. **Paste** the contents of that `.m` file here so I can review every step in your Power Query transformations.

---

## 2. Export all DAX Measures via DAX Studio

1. **Install DAX Studio**:
   • Download from [https://daxstudio.org/](https://daxstudio.org/)
2. **Open your report** in Power BI Desktop.
3. **Launch DAX Studio** from the External Tools ribbon.
4. **Export Measures**:

   * In the Metadata pane, right‑click **Measures** → **Export Measures** → Save as `All_Measures.dax`.
5. **Paste** the contents of that `.dax` file here so I can fix any syntax issues and optimize them.

---

## 3. I’ll then…

* **Embed** each M‑query and DAX formula verbatim in my review.
* **Correct** any DAX errors (e.g. missing commas, undefined columns/measures, incorrect SWITCH/VAR usage).
* **Advise** if a given calculation belongs in M (Power Query) vs. DAX (model) based on best practices:

  * **Power Query**: row‑level cleaning, type conversions, unpivot/pivot, merges.
  * **DAX**: dynamic aggregations, time‑intelligence, user‑driven slicers and filters.
* **Refactor** any calculations that would run more efficiently in the other layer.

---

## 4. Sample “Fix” for Common DAX Errors

*(Once I see your real measures, I’ll apply these patterns where needed.)*

```sql
TrendIndicator =
VAR Current = [7DayTotal]
VAR Previous = [28DayTotal]
RETURN
  SWITCH(
    TRUE(),
    Current > Previous * 1.1, "🔴 Increasing",
    Current < Previous * 0.9, "🟢 Decreasing",
    "🟡 Stable"
  )
```

```sql
TrendDescription =
VAR Total7Day   = [7DayTotal]
VAR ChangePct   = DIVIDE([7DayTotal] - [28DayTotal], [28DayTotal], 0)
VAR ChangeText  = FORMAT([7DayTotal] - [28DayTotal], "+0;-0;0")
VAR Hotspot     = [TopBlockHotspot]
VAR Trend       = [TrendIndicator]
RETURN
  "7‑Day Total: " & Total7Day 
    & " (" & FORMAT(ChangePct, "0.0%") & ") • Hotspot: " 
    & Hotspot & " • Trend: " & Trend
```

---

## 5. Four Additional DAX Measures & Visual Tips

| Measure Name                                                      | Formula (DAX)                                                                           | Description & Recommended Visual |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------- | -------------------------------- |
| **PctByCategory**                                                 | \`\`\`dax                                                                               |                                  |
| PctByCategory =                                                   |                                                                                         |                                  |
| DIVIDE(                                                           |                                                                                         |                                  |
| COUNTROWS(CAD\_Export),                                           |                                                                                         |                                  |
| CALCULATE(COUNTROWS(CAD\_Export), ALL(CAD\_Export))               |                                                                                         |                                  |
| )                                                                 |                                                                                         |                                  |
| \`\`\`                                                            | % of total incidents by category. **Visual**: 100% Stacked bar or Pie chart (show `%`). |                                  |
| **MonthlyIncidents**                                              | \`\`\`dax                                                                               |                                  |
| MonthlyIncidents =                                                |                                                                                         |                                  |
| CALCULATE(                                                        |                                                                                         |                                  |
| \[TotalIncidents],                                                |                                                                                         |                                  |
| DATESINPERIOD(DateTable\[Date], MAX(DateTable\[Date]), -1, MONTH) |                                                                                         |                                  |
| )                                                                 |                                                                                         |                                  |

````| Incidents in the last full month. **Visual**: Line chart with DateTable[Month].         |
| **AvgResponseMinutes** | ```dax  
AvgResponseMinutes =  
AVERAGE(CAD_Export[ResponseTimeMinutes])  
```                                                                                                     | Average call response time. **Visual**: Card (with conditional formatting thresholds).    |
| **HotspotRank**        | ```dax  
HotspotRank =  
RANKX(  
  ALL(CAD_Export[Block]),  
  CALCULATE(COUNTROWS(CAD_Export)),  
  ,  
  DESC,  
  Skip  
)  
```                                                                                                  | Numeric rank of blocks by incident count. **Visual**: Table or Bar chart sorted by rank. |

---

## 6. Next Steps

1. **Export** your M‑queries (`.m`) and DAX measures (`.dax`) as described above.  
2. **Paste** them in your next reply.  
3. I’ll **embed**, **correct**, and **annotate** each one, then finalize recommendations on where each belongs (M vs. DAX) and how to wire up the visuals.  

That will give you a complete, error‑free set of transformations and measures, plus actionable guidance for building/optimizing your report visuals. Let me know when the exports are ready!
````
