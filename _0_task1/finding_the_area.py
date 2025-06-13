import json
import math
from typing import List, Tuple, Dict, Any

def load_cityjson(file_path: str) -> Dict[str, Any]:
    """Load CityJSON file and return the data structure."""
    with open(file_path, 'r') as f:
        return json.load(f)

def analyze_cityjson_structure(cityjson_data: Dict[str, Any]):
    """Analyze and print the structure of the CityJSON file."""
    print("=== CITYJSON STRUCTURE ANALYSIS ===")
    
    # Basic info
    print(f"CityJSON version: {cityjson_data.get('version', 'Unknown')}")
    print(f"Type: {cityjson_data.get('type', 'Unknown')}")
    
    # Vertices info
    vertices = cityjson_data.get('vertices', [])
    print(f"Total vertices: {len(vertices)}")
    
    # Transform info
    transform = cityjson_data.get('transform', {})
    if transform:
        print(f"Transform present: Scale={transform.get('scale', 'None')}, Translate={transform.get('translate', 'None')}")
    
    # City Objects analysis
    city_objects = cityjson_data.get('CityObjects', {})
    print(f"Total CityObjects: {len(city_objects)}")
    
    # Group by type and analyze geometry
    objects_by_type = {}
    lod_info = {}
    
    for obj_id, obj_data in city_objects.items():
        obj_type = obj_data.get('type', 'Unknown')
        
        if obj_type not in objects_by_type:
            objects_by_type[obj_type] = []
        objects_by_type[obj_type].append(obj_id)
        
        # Analyze geometries and LoDs
        geometries = obj_data.get('geometry', [])
        print(f"\nObject: {obj_id}")
        print(f"  Type: {obj_type}")
        print(f"  Geometries: {len(geometries)}")
        
        # Check for parent/children relationships
        if 'parents' in obj_data:
            print(f"  Parents: {obj_data['parents']}")
        if 'children' in obj_data:
            print(f"  Children: {obj_data['children']}")
        
        for i, geom in enumerate(geometries):
            geom_type = geom.get('type', 'Unknown')
            lod = geom.get('lod', 'Unknown')
            boundaries = geom.get('boundaries', [])
            
            print(f"    Geometry {i}: Type={geom_type}, LoD={lod}")
            
            # Count surfaces based on geometry type
            surface_count = 0
            if geom_type == 'Solid' and boundaries:
                # For Solid: boundaries are [shell][surface][ring][vertex]
                if len(boundaries) > 0:
                    surface_count = len(boundaries[0])  # surfaces in first shell
            elif geom_type in ['MultiSurface', 'CompositeSurface'] and boundaries:
                # For MultiSurface/CompositeSurface: boundaries are [surface][ring][vertex]
                surface_count = len(boundaries)
            
            print(f"      Surfaces: {surface_count}")
            
            # Track LoD information
            if lod not in lod_info:
                lod_info[lod] = []
            lod_info[lod].append({
                'object_id': obj_id,
                'object_type': obj_type,
                'geometry_type': geom_type,
                'surface_count': surface_count
            })
    
    print(f"\n=== OBJECTS BY TYPE ===")
    for obj_type, obj_list in objects_by_type.items():
        print(f"{obj_type}: {len(obj_list)} objects")
        for obj_id in obj_list[:3]:  # Show first 3
            print(f"  - {obj_id}")
        if len(obj_list) > 3:
            print(f"  ... and {len(obj_list) - 3} more")
    
    print(f"\n=== LOD ANALYSIS ===")
    for lod, geom_list in lod_info.items():
        print(f"LoD {lod}: {len(geom_list)} geometries")
        for geom_info in geom_list:
            print(f"  - {geom_info['object_id']} ({geom_info['object_type']}, {geom_info['geometry_type']}, {geom_info['surface_count']} surfaces)")

def transform_vertex(vertex: List[float], transform: Dict[str, Any]) -> Tuple[float, float, float]:
    """Apply transformation to a vertex coordinate."""
    scale = transform.get('scale', [1.0, 1.0, 1.0])
    translate = transform.get('translate', [0.0, 0.0, 0.0])
    
    return (
        vertex[0] * scale[0] + translate[0],
        vertex[1] * scale[1] + translate[1],
        vertex[2] * scale[2] + translate[2]
    )

def get_transformed_vertices(cityjson_data: Dict[str, Any]) -> List[Tuple[float, float, float]]:
    """Get all vertices with transformation applied."""
    vertices = cityjson_data['vertices']
    transform = cityjson_data.get('transform', {})
    
    if transform:
        return [transform_vertex(v, transform) for v in vertices]
    else:
        return [(v[0], v[1], v[2]) for v in vertices]

def calculate_polygon_area_2d(points: List[Tuple[float, float]]) -> float:
    """Calculate area of a 2D polygon using the shoelace formula."""
    if len(points) < 3:
        return 0.0
    
    area = 0.0
    n = len(points)
    
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    
    return abs(area) / 2.0

def calculate_3d_polygon_area(points: List[Tuple[float, float, float]]) -> float:
    """Calculate area of a 3D polygon using cross product method."""
    if len(points) < 3:
        return 0.0
    
    # Calculate area using cross product
    total_area = 0.0
    n = len(points)
    
    for i in range(n):
        j = (i + 1) % n
        k = (i + 2) % n
        
        # Vectors from point i to j and i to k
        v1 = (points[j][0] - points[i][0], points[j][1] - points[i][1], points[j][2] - points[i][2])
        v2 = (points[k][0] - points[i][0], points[k][1] - points[i][1], points[k][2] - points[i][2])
        
        # Cross product
        cross = (
            v1[1] * v2[2] - v1[2] * v2[1],
            v1[2] * v2[0] - v1[0] * v2[2],
            v1[0] * v2[1] - v1[1] * v2[0]
        )
        
        # Magnitude of cross product
        magnitude = math.sqrt(cross[0]**2 + cross[1]**2 + cross[2]**2)
        total_area += magnitude
    
    return total_area / 2.0

def analyze_geometry_surfaces(geometry: Dict[str, Any], vertices: List[Tuple[float, float, float]], obj_id: str) -> List[Dict[str, Any]]:
    """Analyze all surfaces in a geometry and return their semantic information."""
    geom_type = geometry['type']
    boundaries = geometry['boundaries']
    semantics = geometry.get('semantics', {})
    lod = geometry.get('lod', 'Unknown')
    surfaces_info = []
    
    # Debug print
    print(f"    Analyzing geometry: {geom_type}, LoD: {lod}")
    
    # Get semantic information if available
    surface_types = semantics.get('surfaces', [])
    surface_values = semantics.get('values', [])
    
    if geom_type == 'Solid':
        # For Solid: boundaries are [shell][surface][ring][vertex]
        if boundaries and len(boundaries) > 0:
            shell_idx = 0  # Usually just one shell
            shell = boundaries[shell_idx]
            
            print(f"      Solid has {len(shell)} surfaces")
            
            for surface_idx, surface in enumerate(shell):
                if surface:  # Check if surface exists
                    outer_ring = surface[0]  # Get outer boundary
                    if len(outer_ring) > 0:
                        surface_coords = [vertices[idx] for idx in outer_ring[:-1]]  # Exclude last duplicate vertex
                        
                        # Calculate area
                        area_2d = calculate_polygon_area_2d([(p[0], p[1]) for p in surface_coords])
                        area_3d = calculate_3d_polygon_area(surface_coords)
                        
                        # Get semantic information
                        semantic_type = "Unknown"
                        semantic_info = {}
                        
                        if (surface_values and len(surface_values) > shell_idx and 
                            len(surface_values[shell_idx]) > surface_idx):
                            semantic_idx = surface_values[shell_idx][surface_idx]
                            if semantic_idx is not None and semantic_idx < len(surface_types):
                                semantic_info = surface_types[semantic_idx]
                                semantic_type = semantic_info.get('type', 'Unknown')
                        
                        # Calculate average Z coordinate
                        avg_z = sum(p[2] for p in surface_coords) / len(surface_coords)
                        
                        surface_info = {
                            'surface_index': surface_idx,
                            'semantic_type': semantic_type,
                            'semantic_info': semantic_info,
                            'area_2d': area_2d,
                            'area_3d': area_3d,
                            'avg_z_coordinate': avg_z,
                            'vertex_count': len(surface_coords),
                            'coordinates': surface_coords,
                            'lod': lod
                        }
                        surfaces_info.append(surface_info)
    
    elif geom_type in ['MultiSurface', 'CompositeSurface']:
        # For MultiSurface/CompositeSurface: boundaries are [surface][ring][vertex]
        print(f"      {geom_type} has {len(boundaries)} surfaces")
        
        for surface_idx, surface in enumerate(boundaries):
            if surface:  # Check if surface exists
                outer_ring = surface[0]  # Get outer boundary
                if len(outer_ring) > 0:
                    surface_coords = [vertices[idx] for idx in outer_ring[:-1]]
                    
                    # Calculate area
                    area_2d = calculate_polygon_area_2d([(p[0], p[1]) for p in surface_coords])
                    area_3d = calculate_3d_polygon_area(surface_coords)
                    
                    # Get semantic information
                    semantic_type = "Unknown"
                    semantic_info = {}
                    
                    if (surface_values and surface_idx < len(surface_values)):
                        semantic_idx = surface_values[surface_idx]
                        if semantic_idx is not None and semantic_idx < len(surface_types):
                            semantic_info = surface_types[semantic_idx]
                            semantic_type = semantic_info.get('type', 'Unknown')
                    
                    # Calculate average Z coordinate
                    avg_z = sum(p[2] for p in surface_coords) / len(surface_coords)
                    
                    surface_info = {
                        'surface_index': surface_idx,
                        'semantic_type': semantic_type,
                        'semantic_info': semantic_info,
                        'area_2d': area_2d,
                        'area_3d': area_3d,
                        'avg_z_coordinate': avg_z,
                        'vertex_count': len(surface_coords),
                        'coordinates': surface_coords,
                        'lod': lod
                    }
                    surfaces_info.append(surface_info)
    
    return surfaces_info

def analyze_all_surfaces(cityjson_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Analyze all surfaces for all city objects."""
    vertices = get_transformed_vertices(cityjson_data)
    city_objects = cityjson_data.get('CityObjects', {})
    results = []
    
    print(f"\n=== ANALYZING {len(city_objects)} CITY OBJECTS ===")
    
    for obj_id, obj_data in city_objects.items():
        obj_type = obj_data.get('type', '')
        
        print(f"\nObject: {obj_id}")
        print(f"  Type: {obj_type}")
        
        # Analyze all geometries
        geometry_list = obj_data.get('geometry', [])
        print(f"  Geometries: {len(geometry_list)}")
        
        for geom_idx, geometry in enumerate(geometry_list):
            print(f"  Geometry {geom_idx}:")
            surfaces = analyze_geometry_surfaces(geometry, vertices, obj_id)
            
            for surface in surfaces:
                result = {
                    'object_id': obj_id,
                    'object_type': obj_type,
                    'geometry_index': geom_idx,
                    'geometry_type': geometry.get('type', 'Unknown'),
                    'lod': surface['lod'],
                    'surface_index': surface['surface_index'],
                    'semantic_type': surface['semantic_type'],
                    'semantic_info': surface['semantic_info'],
                    'area_2d': surface['area_2d'],
                    'area_3d': surface['area_3d'],
                    'avg_z_coordinate': surface['avg_z_coordinate'],
                    'vertex_count': surface['vertex_count']
                }
                
                # Add object attributes if available
                if 'attributes' in obj_data:
                    result['attributes'] = obj_data['attributes']
                
                results.append(result)
    
    return results

def save_results_to_csv(results: List[Dict[str, Any]], output_file: str):
    """Save results to CSV file."""
    import csv
    
    if not results:
        print("No surfaces found.")
        return
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'object_id', 'object_type', 'geometry_index', 'geometry_type', 'lod',
            'surface_index', 'semantic_type', 'area_2d', 'area_3d', 
            'avg_z_coordinate', 'vertex_count'
        ]
        
        # Add attribute columns if they exist
        if results and 'attributes' in results[0]:
            sample_attrs = results[0]['attributes']
            fieldnames.extend(sample_attrs.keys())
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            row = {
                'object_id': result['object_id'],
                'object_type': result['object_type'],
                'geometry_index': result['geometry_index'],
                'geometry_type': result['geometry_type'],
                'lod': result['lod'],
                'surface_index': result['surface_index'],
                'semantic_type': result['semantic_type'],
                'area_2d': result['area_2d'],
                'area_3d': result['area_3d'],
                'avg_z_coordinate': result['avg_z_coordinate'],
                'vertex_count': result['vertex_count']
            }
            
            # Add attributes if they exist
            if 'attributes' in result:
                row.update(result['attributes'])
            
            writer.writerow(row)

def print_summary(results: List[Dict[str, Any]]):
    """Print a summary of all surfaces found."""
    if not results:
        print("No surfaces found.")
        return
    
    # Group by object, LoD, and semantic type
    by_object = {}
    by_lod = {}
    semantic_totals = {}
    
    for result in results:
        obj_id = result['object_id']
        semantic_type = result['semantic_type']
        lod = result['lod']
        
        # By object
        if obj_id not in by_object:
            by_object[obj_id] = {}
        if semantic_type not in by_object[obj_id]:
            by_object[obj_id][semantic_type] = []
        by_object[obj_id][semantic_type].append(result)
        
        # By LoD
        if lod not in by_lod:
            by_lod[lod] = {}
        if semantic_type not in by_lod[lod]:
            by_lod[lod][semantic_type] = []
        by_lod[lod][semantic_type].append(result)
        
        # Count semantic types
        if semantic_type not in semantic_totals:
            semantic_totals[semantic_type] = {'count': 0, 'total_area_2d': 0}
        semantic_totals[semantic_type]['count'] += 1
        semantic_totals[semantic_type]['total_area_2d'] += result['area_2d']
    
    print("\n=== SURFACE ANALYSIS SUMMARY ===")
    print(f"Total surfaces found: {len(results)}")
    print(f"Total objects analyzed: {len(by_object)}")
    
    print("\n=== BY LOD ===")
    for lod, surfaces_by_type in by_lod.items():
        print(f"\nLoD {lod}:")
        for semantic_type, surfaces in surfaces_by_type.items():
            total_area = sum(s['area_2d'] for s in surfaces)
            print(f"  {semantic_type}: {len(surfaces)} surfaces, "
                  f"Area: {total_area:.2f} sq units")
    
    print("\n=== BY SEMANTIC TYPE ===")
    for semantic_type, info in semantic_totals.items():
        print(f"{semantic_type}: {info['count']} surfaces, "
              f"Total 2D area: {info['total_area_2d']:.2f} sq units")

def main():
    """Main function to analyze all surfaces in CityJSON."""
    # Configuration
    input_file = '_0_task1/buiding - Copie.json'  # Replace with your CityJSON file path
    output_file = '_0_task1/surface_analysis_enhanced.csv'
    
    try:
        # Load CityJSON data
        print(f"Loading CityJSON file: {input_file}")
        cityjson_data = load_cityjson(input_file)
        
        # Analyze structure first
        analyze_cityjson_structure(cityjson_data)
        
        # Analyze all surfaces
        print("\n" + "="*50)
        print("ANALYZING ALL SURFACES...")
        results = analyze_all_surfaces(cityjson_data)
        
        # Print summary
        print_summary(results)
        
        # Save to CSV
        if results:
            save_results_to_csv(results, output_file)
            print(f"\nDetailed results saved to: {output_file}")
        else:
            print("No surfaces found in the CityJSON file.")
            
    except FileNotFoundError:
        print(f"Error: Could not find the file '{input_file}'")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{input_file}'")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()