import json
import pprint

def debug_cityjson_structure(cityjson_file):
    """
    Debug CityJSON file structure to understand geometry organization
    """
    with open(cityjson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=== CITYJSON FILE STRUCTURE DEBUG ===\n")
    
    # Basic file info
    print(f"File version: {data.get('version', 'Unknown')}")
    print(f"Transform: {data.get('transform', 'None')}")
    print(f"Number of vertices: {len(data.get('vertices', []))}")
    print(f"Number of city objects: {len(data.get('cityObjects', {}))}")
    
    # Metadata
    if 'metadata' in data:
        print(f"\nMetadata:")
        pprint.pprint(data['metadata'])
    
    # Check a few vertices
    vertices = data.get('vertices', [])
    if vertices:
        print(f"\nFirst 3 vertices:")
        for i, vertex in enumerate(vertices[:3]):
            print(f"  Vertex {i}: {vertex}")
    
    # Analyze city objects
    print(f"\n=== CITY OBJECTS ANALYSIS ===")
    object_types = {}
    lod_info = {}
    geometry_types = {}
    
    for obj_id, city_object in data.get('cityObjects', {}).items():
        # Count object types
        obj_type = city_object.get('type', 'Unknown')
        object_types[obj_type] = object_types.get(obj_type, 0) + 1
        
        # Analyze geometries
        if 'geometry' in city_object:
            print(f"\nObject: {obj_id} (Type: {obj_type})")
            print(f"  Number of geometries: {len(city_object['geometry'])}")
            
            for i, geom in enumerate(city_object['geometry']):
                print(f"  Geometry {i}:")
                print(f"    Type: {geom.get('type', 'Unknown')}")
                print(f"    LOD: {geom.get('lod', 'No LOD specified')}")
                
                # Count LODs
                lod = geom.get('lod')
                if lod is not None:
                    lod_info[lod] = lod_info.get(lod, 0) + 1
                
                # Count geometry types
                geom_type = geom.get('type', 'Unknown')
                geometry_types[geom_type] = geometry_types.get(geom_type, 0) + 1
                
                # Show boundary structure
                boundaries = geom.get('boundaries', [])
                if boundaries:
                    print(f"    Boundaries structure:")
                    print(f"      Number of boundary elements: {len(boundaries)}")
                    if boundaries:
                        print(f"      First boundary type: {type(boundaries[0])}")
                        if isinstance(boundaries[0], list) and boundaries[0]:
                            print(f"      First boundary length: {len(boundaries[0])}")
                            if isinstance(boundaries[0][0], list):
                                print(f"      Nested structure depth: multiple levels")
                                # Show first few indices
                                if boundaries[0][0]:
                                    first_ring = boundaries[0][0][:5]  # First 5 vertex indices
                                    print(f"      First vertex indices: {first_ring}")
                            else:
                                first_indices = boundaries[0][:5]  # First 5 vertex indices
                                print(f"      First vertex indices: {first_indices}")
                
                # Show attributes if any
                attributes = city_object.get('attributes', {})
                if attributes:
                    print(f"    Attributes: {list(attributes.keys())}")
                
                print()  # Empty line for readability
                
                # Only show first object in detail to avoid too much output
                if i == 0:
                    break
        
        # Only analyze first few objects in detail
        if len([k for k in data['cityObjects'].keys() if k <= obj_id]) >= 3:
            print("... (showing first 3 objects only)")
            break
    
    print(f"\n=== SUMMARY ===")
    print(f"Object types found: {object_types}")
    print(f"LODs found: {lod_info}")
    print(f"Geometry types found: {geometry_types}")
    
    # Recommendations
    print(f"\n=== RECOMMENDATIONS ===")
    if not lod_info:
        print("⚠️  No LOD information found in geometries")
    if not any(geom_type in ['Solid', 'MultiSurface', 'CompositeSurface'] for geom_type in geometry_types.keys()):
        print("⚠️  No standard 3D geometry types found")
    
    return data

def show_sample_geometry_details(cityjson_file, max_objects=1):
    """
    Show detailed geometry structure for debugging
    """
    with open(cityjson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n=== DETAILED GEOMETRY STRUCTURE ===")
    
    count = 0
    for obj_id, city_object in data.get('cityObjects', {}).items():
        if 'geometry' in city_object and count < max_objects:
            print(f"\nDETAILED ANALYSIS FOR OBJECT: {obj_id}")
            for i, geom in enumerate(city_object['geometry']):
                print(f"\nGeometry {i} full structure:")
                pprint.pprint(geom, depth=4)  # Limit depth to avoid too much output
            count += 1

if __name__ == "__main__":
    # Replace with your actual file name
    cityjson_file = "buiding.json"  # Change this to your file
    
    # Debug the structure
    debug_cityjson_structure(cityjson_file)
    
    # Show detailed geometry (uncomment if needed)
    # show_sample_geometry_details(cityjson_file)