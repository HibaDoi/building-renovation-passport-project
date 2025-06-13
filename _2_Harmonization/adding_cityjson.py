from pathlib import Path
from osgeo import gdal

pg_conn    = "PG:host=localhost port=5433 dbname=renodat user=postgres password=hibadoi"
src_file   = Path(r"_2_Harmonization/IFC_converted_Cityjson/ifc_to_cityjson.json")
table_name = "ifc_cityjson"          # ← NEW NAME HERE

assert src_file.exists()

gdal.VectorTranslate(
    pg_conn, str(src_file),
    format="PostgreSQL",
    layerName=table_name,
    layerCreationOptions=["GEOMETRY_NAME=geom"],
    accessMode="overwrite"
)

print("✅ Imported CityJSON into PostGIS table:", table_name)
