import json
import numpy as np
from shapely.geometry import Polygon

with open("_2_Harmonization\CityJSON/building_assigned_notextures.json") as f:
    cj = json.load(f)


city_objects = cj["CityObjects"]
buildings = {
    obj_id: obj
    for obj_id, obj in city_objects.items()
    if obj["type"] == "Building"
}


# global vertex list
vertices = np.array(cj["vertices"])  # shape (N, 3)

out = []

for b_id, b in buildings.items():
    attrs = b.get("attributes", {})
        # grab the bits you want
    roof_type    = attrs.get("b3_dak_type")
    roof_h_typ   = attrs.get("b3_h_dak_70p")
    roof_h_min   = attrs.get("b3_h_dak_min")
    roof_h_max   = attrs.get("b3_h_dak_max")
    ground_lvl   = attrs.get("b3_h_maaiveld")
    volume_lod2  = attrs.get("b3_volume_lod22")
    year_built   = attrs.get("oorspronkelijkbouwjaar")
    
        # extract first MultiSurface footprint
    # find the first MultiSurface footprint
    footprint = None
    for geom in b["geometry"]:
        # pick exactly LOD2 (or whichever LOD your file uses for footprints)
        lod = float(geom.get("lod", 0))
        if geom["type"] != "Solid" or lod < 1.0:
            continue

        # if there’s also a “purpose” field, you can be even more explicit:
        # if geom.get("purpose") not in ("Footprint","GroundSurface"): continue

        outer_ring = geom["boundaries"][0][0]
        coords3d   = [vertices[i] for i in outer_ring]
        footprint  = [(float(x),float(y)) for x,y,_ in coords3d]
        print(footprint)
        break

    out.append({
        "id":            b_id,
        "year_built":    year_built,
        "roof_type":     roof_type,
        "roof_h_typ":    roof_h_typ,
        "roof_h_min":    roof_h_min,
        "roof_h_max":    roof_h_max,
        "ground_lvl":    ground_lvl,
        "volume_lod2":   volume_lod2,
        "footprint":     footprint,

    })
   # write it out
with open("for_teaser.json", "w") as f:
    json.dump(out, f, indent=2)

