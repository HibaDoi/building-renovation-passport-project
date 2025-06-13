from pathlib import Path
from teaser.project import Project
import os

# 1) Create TEASER project
prj = Project()
prj.load_data = True
print("✅ Project created and data loaded")

# 2) Manual building creation with proper setup
from teaser.logic.buildingobjects.building import Building

bldg = Building(parent=prj)
bldg.name = "TestBuilding"
bldg.street_name = "Test Street"
bldg.city = "Test City"
bldg.year_of_construction = 2000
bldg.number_of_floors = 2
bldg.height_of_floors = 3.0
bldg.net_leased_area = 120.0

# Add to project
prj.buildings.append(bldg)
print("✅ Building created and added to project")
# See what methods are actually available


# 3) CRITICAL: Generate building archetype (creates thermal zones and elements)

try:
    # Set building type and calculate parameters
    bldg.type_of_building = "single_family_house"
    bldg.year_of_construction = 2020  # for new construction
    
    # Calculate building parameters based on the type
    bldg.calc_building_parameter()
    print("✅ Building parameters calculated")
except Exception as e:
    print(f"❌ Parameter calculation failed: {e}")
    
    # Try alternative approach - create thermal zones manually
    from teaser.logic.buildingobjects.thermalzone import ThermalZone
    
    # Create a thermal zone
    tz = ThermalZone(parent=bldg)
    tz.name = "Zone1"
    tz.area = 120.0
    tz.volume = 120.0 * 3.0  # area * height
    tz.infiltration_rate = 0.5  # air changes per hour
    
    # Add zone to building
    bldg.thermal_zones.append(tz)
    print("✅ Manual thermal zone created")

# 4) Calculate building parameters (ESSENTIAL for .txt generation)
try:
    # Try project-level calculation
    prj.calc_all_buildings()
    print("✅ All buildings calculated via project")
except Exception as e:
    print(f"Project calculation failed: {e}")
    
    # Try individual building calculation
    try:
        for building in prj.buildings:
            building.calc_building_parameter()
        print("✅ Building parameters calculated individually")
    except Exception as e2:
        print(f"Individual calculation failed: {e2}")
        
        # Try zone-level calculation
        try:
            for building in prj.buildings:
                for zone in building.thermal_zones:
                    zone.calc_zone_parameters()
            print("✅ Zone parameters calculated")
        except Exception as e3:
            print(f"Zone calculation failed: {e3}")

# 5) Verify building has thermal data before export
print(f"\nBuilding verification:")
print(f"- Building name: {bldg.name}")
print(f"- Number of thermal zones: {len(bldg.thermal_zones)}")
print(f"- Net leased area: {bldg.net_leased_area} m²")

if bldg.thermal_zones:
    zone = bldg.thermal_zones[0]
    print(f"- First zone name: {zone.name}")
    print(f"- Zone area: {zone.area} m²")

# 6) Export with detailed error handling
outdir = Path("teaser_out")
outdir.mkdir(exist_ok=True)

print(f"\n🔄 Starting export to: {outdir.absolute()}")

# Clear existing files
import shutil
if outdir.exists():
    shutil.rmtree(outdir)
    outdir.mkdir()

export_success = False

try:
    # Try exporting to a simpler path first
    simple_path = "C:/temp/teaser_test"
    os.makedirs(simple_path, exist_ok=True)
    
    prj.export_aixlib(
        building_model="BuildingModel",
        zone_model="ZoneModel", 
        corG=True,
        path=simple_path
    )
    print("✅ Export successful to simple path")
except Exception as e:
    print(f"❌ Simple export failed: {e}")

# 7) Detailed file check
print(f"\n📁 Checking generated files in: {outdir.absolute()}")

if outdir.exists():
    all_files = []
    for item in outdir.rglob("*"):
        if item.is_file():
            all_files.append(item)
            print(f"📄 {item.relative_to(outdir)} ({item.stat().st_size} bytes)")
        elif item.is_dir():
            print(f"📁 {item.relative_to(outdir)}/")
    
    # Specifically look for parameter files
    txt_files = [f for f in all_files if f.suffix == '.txt']
    mo_files = [f for f in all_files if f.suffix == '.mo']
    
    print(f"\n📊 Summary:")
    print(f"- Total files: {len(all_files)}")
    print(f"- .txt parameter files: {len(txt_files)}")
    print(f"- .mo model files: {len(mo_files)}")
    
    if txt_files:
        print(f"\n✅ Parameter files found:")
        for txt_file in txt_files:
            print(f"  - {txt_file.name}")
            # Show first few lines of the parameter file
            try:
                with open(txt_file, 'r') as f:
                    lines = f.readlines()[:5]
                    print(f"    Preview: {lines[0].strip()}" if lines else "    (empty file)")
            except:
                pass
    else:
        print(f"\n❌ No .txt parameter files generated!")
        print("This means thermal calculations weren't completed properly.")
        
        # Diagnostic information
        print(f"\nDiagnostic info:")
        print(f"- Project has {len(prj.buildings)} buildings")
        if prj.buildings:
            b = prj.buildings[0]
            print(f"- Building has {len(b.thermal_zones)} thermal zones")
            if b.thermal_zones:
                z = b.thermal_zones[0]
                print(f"- Zone has area: {getattr(z, 'area', 'Not set')}")
                print(f"- Zone has volume: {getattr(z, 'volume', 'Not set')}")

else:
    print("❌ Output directory not found!")

print(f"\n🎯 Process completed. Check the files in: {outdir.absolute()}")