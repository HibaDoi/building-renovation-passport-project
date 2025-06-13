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

# Global vertex list
vertices = np.array(cj["vertices"])  # shape (N, 3)

# Get CityJSON transform parameters
transform = cj.get("transform", {})
scale = transform.get("scale", [1.0, 1.0, 1.0])
translate = transform.get("translate", [0.0, 0.0, 0.0])

def transform_vertices(vertex_indices, vertices, scale, translate):
    """Apply CityJSON transform to vertices"""
    # Handle both flat lists and nested lists
    if isinstance(vertex_indices[0], list):
        # Nested structure - flatten it
        flat_indices = []
        for ring in vertex_indices:
            flat_indices.extend(ring)
        vertex_indices = flat_indices
    
    coords = vertices[vertex_indices]
    # Apply scale and translate
    transformed = coords * np.array(scale) + np.array(translate)
    return transformed

def calculate_footprint_area(footprint_boundaries, vertices, scale, translate):
    """Calculate area of footprint polygon"""
    if not footprint_boundaries:
        return None
    
    try:
        # Handle nested boundary structure
        # footprint_boundaries might be: [[[0,1,2,3,0]]] or [[0,1,2,3,0]]
        boundary_ring = footprint_boundaries
        
        # Navigate through nested lists to find the actual vertex indices
        while isinstance(boundary_ring, list) and len(boundary_ring) > 0 and isinstance(boundary_ring[0], list):
            boundary_ring = boundary_ring[0]
        
        # Now boundary_ring should be a list of vertex indices like [0,1,2,3,0]
        if not boundary_ring or len(boundary_ring) < 4:  # Need at least 4 points for a closed polygon
            return None
        
        # Get coordinates for these vertex indices
        coords = vertices[boundary_ring]
        
        # Apply CityJSON transform
        transformed_coords = coords * np.array(scale) + np.array(translate)
        
        # Create polygon using only X,Y coordinates (ignore Z)
        polygon_coords = transformed_coords[:, :2]  # Take only X,Y
        
        # Create Shapely polygon (remove last point if it's the same as first - closed ring)
        if len(polygon_coords) >= 3:
            if np.allclose(polygon_coords[0], polygon_coords[-1]):
                polygon_coords = polygon_coords[:-1]  # Remove duplicate closing point
            
            if len(polygon_coords) >= 3:
                polygon = Polygon(polygon_coords)
                if polygon.is_valid:
                    return polygon.area
                else:
                    # Try to fix invalid polygon
                    polygon = polygon.buffer(0)
                    if polygon.is_valid:
                        return polygon.area
        
        return None
            
    except Exception as e:
        print(f"Error calculating area: {e}")
        return None

out = []

for b_id, b in buildings.items():
    attrs = b.get("attributes", {})
    
    # Grab the attributes you want
    roof_type = attrs.get("b3_dak_type")
    roof_h_typ = attrs.get("b3_h_dak_70p")
    roof_h_min = attrs.get("b3_h_dak_min")
    roof_h_max = attrs.get("b3_h_dak_max")
    ground_lvl = attrs.get("b3_h_maaiveld")
    volume_lod2 = attrs.get("b3_volume_lod22")
    year_built = attrs.get("oorspronkelijkbouwjaar")
    
    # Extract first MultiSurface footprint
    footprint = None
    footprint_area = None
    
    try:
        # Check if building part exists
        building_part_id = str(b_id) + "-0"
        if building_part_id in city_objects:
            data = city_objects[building_part_id]["geometry"]
            
            # Find the first MultiSurface footprint with GroundSurface
            for building_part in data:
                if (building_part.get('lod') == '1.2' and 
                    'semantics' in building_part and 
                    'surfaces' in building_part['semantics']):
                    
                    surfaces = building_part['semantics']['surfaces']
                    if any(surface.get('type') == 'GroundSurface' for surface in surfaces):
                        footprint = building_part['boundaries']
                        break
            
            # Calculate footprint area if found
            if footprint:
                # Try to find ground surface area more directly
                # footprint is typically structured as boundaries for each surface
                for boundary_set in footprint:
                    area = calculate_footprint_area(boundary_set, vertices, scale, translate)
                    if area is not None:
                        footprint_area = area
                        break
                
                # If still no area found, try the first available boundary
                if footprint_area is None and len(footprint) > 0:
                    footprint_area = calculate_footprint_area(footprint[0], vertices, scale, translate)
    
    except Exception as e:
        print(f"Error processing building {b_id}: {e}")
        footprint = None
        footprint_area = None
    
    out.append({
        "id": b_id,
        "year_built": year_built,
        "roof_type": roof_type,
        "roof_h_typ": roof_h_typ,
        "roof_h_min": roof_h_min,
        "roof_h_max": roof_h_max,
        "ground_lvl": ground_lvl,
        "volume_lod2": volume_lod2,
        "footprint": footprint,
        "footprint_area_m2": footprint_area,  # Added area in square meters
    })

# Write it out
with open("_4_Renovation_Scenario_Stub/for_teaser.json", "w") as f:
    json.dump(out, f, indent=2)

print(f"Processed {len(out)} buildings")
print("Sample areas:")
for item in out[:5]:  # Show first 5 areas
    if item["footprint_area_m2"]:
        print(f"Building {item['id']}: {item['footprint_area_m2']:.2f} m²")