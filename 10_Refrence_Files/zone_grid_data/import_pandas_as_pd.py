import pandas as pd

# load CAD export
df = pd.read_excel(r"C:\…\SCRPA_CAD.xlsx")

# 1) delimiter
df["CleanAddress"] = df["FullAddress2"].str.replace(" & ", " / ")

# 2) suffix mapping
suffix_map = {
    "Street":"St","Avenue":"Ave","Road":"Rd","Place":"Pl",
    "Drive":"Dr","Court":"Ct","Boulevard":"Blvd"
}
for full, abbr in suffix_map.items():
    df["CleanAddress"] = df["CleanAddress"]\
      .str.replace(fr"\b{full}\b", abbr, regex=True)

# 3) casing & trim
df["CleanAddress"] = df["CleanAddress"].str.title().str.strip()

# Now merge on CleanAddress ⇄ CrossStreetName
