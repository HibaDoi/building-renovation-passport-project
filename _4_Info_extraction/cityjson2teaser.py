import json
import numpy as np
from shapely.geometry import Polygon

with open("_4_Renovation_Scenario_Stub/buiding.json") as f:
    cj = json.load(f)


city_objects = cj["CityObjects"]
buildings = {
    obj_id: obj
    for obj_id, obj in city_objects.items()
    if obj["type"] == "Building"
}

buildings_Part = {
    obj_id: obj
    for obj_id, obj in city_objects.items()
    if obj["type"] == "BuildingPart"
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
    
    data=city_objects[str(b_id)+"-0"]["geometry"]
    footprint = next((building_part['boundaries'] for building_part in data if building_part['lod'] == '1.2' and any(surface['type'] == 'GroundSurface' for surface in building_part['semantics']['surfaces'])), None)

    input(footprint)

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
with open("_4_Renovation_Scenario_Stub/for_teaser.json", "w") as f:
    json.dump(out, f, indent=2)

