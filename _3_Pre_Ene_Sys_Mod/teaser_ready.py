import json
import math
from teaser.project import Project
def map_building_to_teaser(building_data, prj):
    """
    Map Dutch building data to TEASER add_residential parameters
    
    Args:
        building_data: Dictionary containing building information from JSON
        prj: TEASER project object
    """
    
    # Extract data from your building dictionary
    b_id = building_data["id"]
    year_built = building_data["year_built"]
    roof_type = building_data["roof_type"]
    roof_h_typ = building_data["roof_h_typ"]
    roof_h_min = building_data["roof_h_min"] 
    roof_h_max = building_data["roof_h_max"]
    ground_lvl = building_data["ground_lvl"]
    volume_lod2 = building_data["volume_lod2"]
    footprint = building_data["footprint"]
    footprint_area = building_data["footprint_area_m2"]
    
    # VALIDATION: Skip buildings that are too small or have invalid data
    if not footprint_area or footprint_area < 10:  # Skip very small buildings
        raise ValueError(f"Building {b_id}: Footprint area too small ({footprint_area}m²) - minimum 10m² required")
    
    if not year_built or year_built < 1800 or year_built > 2025:
        raise ValueError(f"Building {b_id}: Invalid construction year ({year_built})")
    
    if not roof_h_typ or roof_h_typ <= 0:
        raise ValueError(f"Building {b_id}: Invalid roof height ({roof_h_typ}m)")
    
    # Calculate building height more accurately for Dutch data
    # Use roof_h_typ (typical roof height) as main building height reference
    building_height = roof_h_typ - ground_lvl if roof_h_typ and ground_lvl else None
    
    # For Dutch buildings, use typical floor heights (2.7-3.0m)
    typical_floor_height = 2.8  # Typical for Dutch residential
    if building_height and building_height > 0:
        number_of_floors = max(1, round(building_height / typical_floor_height))
        height_of_floors = max(2.5, building_height / number_of_floors)  # Minimum 2.5m floor height
    else:
        # Fallback: use volume and footprint to estimate
        if volume_lod2 and footprint_area and footprint_area > 0:
            estimated_height = volume_lod2 / footprint_area
            number_of_floors = max(1, round(estimated_height / typical_floor_height))
            height_of_floors = max(2.5, estimated_height / number_of_floors)
        else:
            # Final fallback
            number_of_floors = 1 if footprint_area < 50 else 2
            height_of_floors = 2.8
    
    # Ensure reasonable limits
    number_of_floors = min(10, max(1, number_of_floors))  # Between 1-10 floors
    height_of_floors = min(5.0, max(2.5, height_of_floors))  # Between 2.5-5.0m
    
    # Calculate net leased area for Dutch buildings
    # Dutch residential efficiency factor is typically 85-90%
    gross_floor_area = footprint_area * number_of_floors
    net_leased_area = gross_floor_area * 0.87  # 87% efficiency for Dutch residential
    
    # Ensure minimum area for TEASER (very small buildings cause issues)
    net_leased_area = max(20.0, net_leased_area)  # Minimum 20m² net area
    
    # Determine construction data type based on Dutch building periods
    # Also avoid problematic years that don't have database entries
    if year_built < 1945:
        construction_data = 'iwu_heavy'  # Pre-war construction
    elif year_built < 1975:
        construction_data = 'iwu_heavy'  # Post-war reconstruction period  
    elif year_built < 1992:
        construction_data = 'iwu_heavy'  # Before major insulation standards
    elif year_built < 2010:
        construction_data = 'iwu_light'  # Modern construction
    else:
        # Years after 2010 might not have database entries, use closest available
        construction_data = 'iwu_light'
        year_built = min(year_built, 2009)  # Cap at 2009 to avoid database issues
    
    # Determine geometry data based on Dutch building characteristics
    # Small buildings (<50m²) are likely single dwellings or small units
    # Larger buildings might be apartments or larger homes
    if footprint_area < 50:
        geometry_data = 'iwu_single_family_dwelling'
    elif footprint_area < 150:
        geometry_data = 'iwu_single_family_dwelling'
    else:
        geometry_data = 'iwu_single_family_dwelling'  # Adjust if multi-family option exists
    
    # Create building name from Dutch BAG ID
    # Extract readable part from "NL.IMBAG.Pand.XXXXXXXXX"
    bag_id = b_id.split('.')[-1] if '.' in b_id else b_id
    name = f"NL_Building_{bag_id}"
    
    # Add residential building to TEASER project with error handling
    try:
        prj.add_residential(
            construction_data=construction_data,
            geometry_data=geometry_data,
            name=name,
            year_of_construction=int(year_built),
            number_of_floors=int(number_of_floors),
            height_of_floors=float(height_of_floors),
            net_leased_area=float(net_leased_area)
        )
    except Exception as e:
        raise ValueError(f"Failed to add building {name} to TEASER: {str(e)}")
    
    return {
        'building_id': b_id,
        'construction_data': construction_data,
        'geometry_data': geometry_data,
        'name': name,
        'year_of_construction': int(year_built),
        'number_of_floors': int(number_of_floors),
        'height_of_floors': float(height_of_floors),
        'net_leased_area': float(net_leased_area),
        'calculated_from': {
            'original_footprint_area': footprint_area,
            'estimated_building_height': building_height,
            'roof_height_range': f"{roof_h_min}-{roof_h_max}" if roof_h_min and roof_h_max else None,
            'gross_floor_area': gross_floor_area,
            'validation_passed': True
        }
    }

# Example usage for a single building
def process_single_building(building_data, prj):
    """Process a single building from your data format"""
    result = map_building_to_teaser(building_data, prj)
    print(f"Added building {result['name']} to TEASER project")
    return result

# Function to process JSON file with Dutch building data
def process_buildings_from_json(json_file_path, prj):
    """
    Process buildings from JSON file and add them to TEASER project
    
    Args:
        json_file_path: Path to JSON file containing building data
        prj: TEASER project object
    
    Returns:
        List of results for each processed building
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            buildings_data = json.load(file)
        
        results = []
        successful_buildings = 0
        failed_buildings = 0
        
        for building in buildings_data:
            try:
                result = map_building_to_teaser(building, prj)
                results.append(result)
                successful_buildings += 1
                print(f"✓ Added {result['name']} - Year: {result['year_of_construction']}, "
                      f"Floors: {result['number_of_floors']}, Area: {result['net_leased_area']:.1f}m²")
            except ValueError as e:
                failed_buildings += 1
                print(f"⚠ Skipped building {building.get('id', 'unknown')}: {e}")
            except Exception as e:
                failed_buildings += 1
                print(f"✗ Error processing building {building.get('id', 'unknown')}: {e}")
        
        print(f"\nSummary: {successful_buildings} buildings added successfully, {failed_buildings} failed")
        return results
        
    except FileNotFoundError:
        print(f"Error: Could not find file {json_file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file_path}")
        return []

# Function to analyze your building data before processing
def analyze_buildings_json(json_file_path):
    """
    Analyze the building data to understand characteristics before processing
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            buildings_data = json.load(file)
        
        print(f"Total buildings: {len(buildings_data)}")
        
        # Analyze year distribution
        years = [b.get('year_built') for b in buildings_data if b.get('year_built')]
        if years:
            print(f"Year range: {min(years)} - {max(years)}")
        
        # Analyze area distribution
        areas = [b.get('footprint_area_m2') for b in buildings_data if b.get('footprint_area_m2')]
        if areas:
            print(f"Footprint area range: {min(areas):.1f} - {max(areas):.1f} m²")
            print(f"Average footprint area: {sum(areas)/len(areas):.1f} m²")
        
        # Analyze roof types
        roof_types = [b.get('roof_type') for b in buildings_data if b.get('roof_type')]
        from collections import Counter
        roof_type_counts = Counter(roof_types)
        print("Roof types:", dict(roof_type_counts))
        
        return buildings_data
        
    except Exception as e:
        print(f"Error analyzing JSON: {e}")
        return []

# WHAT IS 'prj'? 
# prj = TEASER Project object - this is the main container for all your buildings

# YOU NEED TO CREATE IT FIRST:


# Create a new TEASER project
prj = Project()  # This creates an empty project
prj.name = "renodat"  # Give it a name



# COMPLETE EXAMPLE OF HOW TO USE EVERYTHING:



def complete_workflow_example():
    """Complete example showing how to use everything together"""
    
    # STEP 1: Create TEASER project (this is what 'prj' is!)
    prj = Project()
    prj.name = "renodat"
    
    print(f"Created project: {prj.name}")
    print(f"Initial number of buildings: {len(prj.buildings)}")
    
    # STEP 2: Load your JSON data
    json_file_path = "your_buildings.json"  # Path to your JSON file
    
    # STEP 3: Analyze the data (optional)
    print("\n--- Analyzing building data ---")
    buildings_data = analyze_buildings_json(json_file_path)
    
    # STEP 4: Process all buildings and add them to the project
    print("\n--- Adding buildings to TEASER project ---")
    results = process_buildings_from_json(json_file_path, prj)
    
    print(f"\nFinal number of buildings in project: {len(prj.buildings)}")
    
    # STEP 5: Now you can use the project for energy simulation
    # Generate building models
    prj.calc_all_buildings()
    
    # Export to various formats
    prj.export_aixlib()  # Export to Modelica
    prj.export_annex60()  # Export to IBPSA library
    
    # Save the project
    prj.save_project(file_name="dutch_buildings", path="_3_Pre_Ene_Sys_Mod/output/")
    
    return prj, results

# SIMPLE STEP-BY-STEP USAGE:

# Step 1: Import TEASER and create project
from teaser.project import Project
prj = Project()

# Step 2: Use the functions with your project
results = process_buildings_from_json('_2_Info_extraction/for_teaser.json', prj)

# Step 3: Your buildings are now in prj.buildings
print(f"Added {len(prj.buildings)} buildings to project")

# Step 4: Generate energy models
prj.calc_all_buildings()

# Step 5: Export or save
prj.export_aixlib()

