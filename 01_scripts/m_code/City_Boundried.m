let
    // ─── 1) Load GeoJSON ───────────────────────────────────────────────────────
    Source = Json.Document(
        File.Contents(
            "C:\\Users\\carucci_r\\OneDrive - City of Hackensack\\01_DataSources\\SCRPA_Time_v2\\08_json\\arcgis_pro_layers\\City_Boundaries.geojson"
        )
    ),

    // ─── 2) Promote to table and expand features ───────────────────────────────
    RootTable    = Table.FromRecords({ Source }),
    Features     = Table.ExpandListColumn(RootTable, "features"),
    ExpandedFeat = Table.ExpandRecordColumn(Features, "features", {"properties"}, {"Properties"}),

    // ─── 3) Expand only the property fields you need ───────────────────────────
    ExpandedProps = Table.ExpandRecordColumn(
        ExpandedFeat,
        "Properties",
        {
            "OBJECTID",
            "MUN",
            "COUNTY",
            "MUN_LABEL",
            "Shape__Area",
            "Shape__Length"
        },
        {
            "OBJECTID",
            "MUN",
            "COUNTY",
            "MUN_LABEL",
            "Shape__Area",
            "Shape__Length"
        }
    ),

    // ─── 4) Select and order final columns ─────────────────────────────────────
    Final = Table.SelectColumns(
        ExpandedProps,
        {
            "OBJECTID",
            "MUN",
            "COUNTY",
            "MUN_LABEL",
            "Shape__Area",
            "Shape__Length"
        }
    ),
    #"Filtered Rows" = Table.SelectRows(Final, each ([MUN] = "HACKENSACK CITY"))
in

    #"Filtered Rows"