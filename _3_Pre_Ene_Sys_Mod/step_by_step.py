from teaser.project import Project



# Step 1: Create project
prj = Project()
print("✅ Project created")
prj.name = "ArchetypeExample"




# Step 2: Create building
bldg = prj.add_residential(
    name="TestBuilding",
    year_of_construction=1988,
    number_of_floors=2,
    height_of_floors=3.0,
    net_leased_area=120.0,
    construction_data='iwu_heavy',
    geometry_data='iwu_single_family_dwelling'

)






# Step 5: Run calculation
try:
    prj.calc_all_buildings()
    print("✅ All buildings calculated via project")
except Exception as e:
    print(f"❌ Project calculation failed: {e}")



from pathlib import Path
import shutil

outdir = Path("teaser_out")
if outdir.exists():
    shutil.rmtree(outdir)
outdir.mkdir()

# 🔧 Créer le sous-dossier pour éviter l'erreur sur 'package.mo'
project_dir = outdir / prj.name
project_dir.mkdir(parents=True, exist_ok=True)


prj.export_aixlib(
    path=str(outdir),
    internal_id=None,
    report=True,
    export_vars={
        "HeatingDemands": ["*multizone.PHeater*", "*multizone.PHeatAHU"],
        "CoolingDemands": ["*multizone.PCooler*", "*multizone.PCoolAHU"],
        "Temperatures": ["*multizone.TAir*", "*multizone.TRad*"]
    }
)
print(f"✅ Export completed. Files saved to: {outdir.absolute()}")
