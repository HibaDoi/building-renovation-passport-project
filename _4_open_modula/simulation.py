#!/usr/bin/env python3
"""
YOUR SPECIFIC OPENMODELICA PYTHON WORKFLOW
Based on your actual TEASER export structure
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def analyze_your_teaser_export(export_directory):
    """
    Analyze your specific TEASER export structure
    
    Args:
        export_directory: Path to your TEASER export (where package.mo is located)
    """
    
    export_path = Path(export_directory)
    
    # Find package.mo (main package file)
    package_file = export_path / "package.mo"
    
    # Find building directories
    building_dirs = [d for d in export_path.iterdir() 
                    if d.is_dir() and d.name.startswith("NL_Building_")]
    
    print(f"📁 Export Directory: {export_path}")
    print(f"📦 Package file: {'✓' if package_file.exists() else '✗'}")
    print(f"🏢 Building directories found: {len(building_dirs)}")
    
    for building_dir in building_dirs:
        mo_files = list(building_dir.glob("*.mo"))
        print(f"  - {building_dir.name}: {len(mo_files)} .mo files")
    
    return building_dirs, package_file

def setup_ompython_for_your_models():
    """Setup OMPython specifically for your TEASER models"""
    
    try:
        from OMPython import OMCSessionZMQ
        
        omc = OMCSessionZMQ()
        print("✓ OMPython connected!")
        print(f"OpenModelica version: {omc.sendExpression('getVersion()')}")
        
        # Check OpenModelica installation path
        om_home = omc.sendExpression('getInstallationDirectoryPath()')
        print(f"OpenModelica path: {om_home}")
        
        # Load required libraries for TEASER models with better error handling
        print("Loading Modelica libraries...")
        
        # Try different approaches to load Modelica
        try:
            modelica_result = omc.sendExpression("loadModel(Modelica)")
            print(f"  - Modelica load result: {modelica_result}")
        except Exception as e:
            print(f"  - Modelica load error: {e}")
            
        try:
            aixlib_result = omc.sendExpression("loadModel(AixLib)")
            print(f"  - AixLib load result: {aixlib_result}")
        except Exception as e:
            print(f"  - AixLib load error: {e}")
            print("  - AixLib might not be installed. TEASER models may still work.")
        
        # Alternative: Try loading from specific paths
        print("\nTrying alternative library loading...")
        
        # Get library path
        lib_path = omc.sendExpression('getModelicaPath()')
        print(f"Modelica library path: {lib_path}")
        
        # Check what's actually available
        available_packages = omc.sendExpression("getPackages()")
        print(f"Available packages: {available_packages}")
        
        # Check if basic Modelica is working
        modelica_loaded = omc.sendExpression("isPackage(Modelica)")
        print(f"  - Modelica package available: {'✓' if modelica_loaded else '✗'}")
        
        # Don't fail if AixLib is not available - TEASER might export with different libraries
        return omc
        
    except ImportError:
        print("❌ OMPython not installed. Run: pip install OMPython")
        return None
    except Exception as e:
        print(f"❌ Failed to setup OMPython: {e}")
        return None

def simulate_your_teaser_building(omc, building_dir, package_path):
    """
    Simulate one of your TEASER buildings with better debugging
    
    Args:
        omc: OMPython session
        building_dir: Path to building directory (e.g., NL_Building_0503100000037018)
        package_path: Path to main package.mo file
    """
    
    building_name = building_dir.name
    print(f"\n🏢 Simulating: {building_name}")
    
    try:
        # Debug: Check what files are in the package directory
        print(f"Package path: {package_path}")
        print(f"Building directory: {building_dir}")
        
        # List files in building directory
        mo_files = list(building_dir.glob("*.mo"))
        print(f"Building .mo files: {[f.name for f in mo_files]}")
        
        # Load the main package first
        print("Loading package...")
        package_load = omc.sendExpression(f'loadFile("{package_path}")')
        print(f"Package load result: {package_load}")
        
        if not package_load:
            print("❌ Failed to load main package")
            errors = omc.sendExpression("getErrorString()")
            print(f"Package load errors: {errors}")
            return None
        
        # Try to load the specific building directory as well
        print(f"Loading building directory...")
        for mo_file in mo_files:
            print(f"  Loading: {mo_file.name}")
            file_load = omc.sendExpression(f'loadFile("{mo_file}")')
            print(f"  Result: {file_load}")
            if not file_load:
                errors = omc.sendExpression("getErrorString()")
                print(f"  Errors: {errors}")
        
        # Check what models are now available
        print("Checking available models...")
        models = omc.sendExpression("getClassNames()")
        print(f"All available models: {models}")
        
        # Try different model name variations
        possible_names = [
            building_name,  # NL_Building_0503100000000010
            f"Project.{building_name}",  # Project.NL_Building_0503100000000010
            building_name.replace("NL_Building_", ""),  # Just the number part
        ]
        
        model_name = None
        for name in possible_names:
            exists = omc.sendExpression(f"isModel({name})")
            print(f"Testing model name '{name}': {'✓' if exists else '✗'}")
            if exists:
                model_name = name
                break
        
        if not model_name:
            print("❌ No valid model name found")
            print("Let's try to find the correct model structure...")
            
            # Get detailed class information
            for model in models:
                if isinstance(model, str) and "Building" in model:
                    print(f"Found building-related model: {model}")
                    # Try to get more info about this model
                    info = omc.sendExpression(f"getClassInformation({model})")
                    print(f"  Info: {info}")
            
            return None
        
        print(f"✓ Using model: {model_name}")
        
        # Check model for errors
        print("Checking model...")
        check_result = omc.sendExpression(f"checkModel({model_name})")
        print(f"Model check result: {check_result}")
        
        # Get any errors
        errors = omc.sendExpression("getErrorString()")
        if errors:
            print(f"Model check errors: {errors}")
        
        # Set simulation parameters (shorter for testing)
        sim_params = {
            'startTime': 0,
            'stopTime': 3600,  # Just 1 hour for testing
            'numberOfIntervals': 60,  # Minute intervals
            'tolerance': 1e-4  # Relaxed tolerance
        }
        
        # Run simulation
        print("Starting simulation...")
        sim_command = f"""
        simulate({model_name}, 
                 startTime={sim_params['startTime']}, 
                 stopTime={sim_params['stopTime']}, 
                 numberOfIntervals={sim_params['numberOfIntervals']},
                 tolerance={sim_params['tolerance']})
        """
        
        sim_result = omc.sendExpression(sim_command)
        print(f"Simulation result: {sim_result}")
        
        # Get simulation errors
        sim_errors = omc.sendExpression("getErrorString()")
        if sim_errors:
            print(f"Simulation errors: {sim_errors}")
        
        # Check for result file - try different possible names
        possible_result_files = [
            f"{model_name}_res.mat",
            f"{building_name}_res.mat",
            f"{model_name.replace('.', '_')}_res.mat"
        ]
        
        result_file = None
        for rf in possible_result_files:
            if os.path.exists(rf):
                result_file = rf
                break
        
        if result_file:
            print(f"✓ Simulation completed! Result file: {result_file}")
            return result_file
        else:
            print("❌ No result file generated")
            print("Checking current directory for .mat files...")
            mat_files = list(Path(".").glob("*.mat"))
            print(f"Available .mat files: {[f.name for f in mat_files]}")
            return None
            
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        errors = omc.sendExpression("getErrorString()")
        if errors:
            print(f"OpenModelica errors: {errors}")
        return None

def quick_test_single_building(export_directory, building_name=None):
    """
    Quick test with one building from your export
    
    Args:
        export_directory: Your TEASER export directory
        building_name: Specific building to test (if None, uses first one)
    """
    
    print("🧪 QUICK TEST - Single Building Simulation")
    print("=" * 50)
    
    # Analyze export structure
    building_dirs, package_file = analyze_your_teaser_export(export_directory)
    
    if not building_dirs:
        print("❌ No building directories found!")
        return None
    
    # Select building to test
    if building_name:
        test_building = next((d for d in building_dirs if d.name == building_name), None)
        if not test_building:
            print(f"❌ Building {building_name} not found!")
            return None
    else:
        test_building = building_dirs[0]  # Use first building
    
    print(f"\n🎯 Testing building: {test_building.name}")
    
    # Setup OMPython
    omc = setup_ompython_for_your_models()
    if not omc:
        return None
    
    # Run simulation
    result_file = simulate_your_teaser_building(omc, test_building, package_file)
    
    if result_file:
        print(f"\n✅ Test successful! Result file: {result_file}")
        
        # Try to analyze results
        try:
            df = analyze_result_file(result_file)
            if df is not None:
                print("\n📊 Quick analysis:")
                print(df.describe())
                
                # Simple plot
                create_quick_plot(df, test_building.name)
                
            return df
        except Exception as e:
            print(f"⚠ Could not analyze results: {e}")
            print("But simulation completed successfully!")
            return result_file
    else:
        print("\n❌ Test failed")
        return None

def analyze_result_file(mat_file_path):
    """Analyze .mat result file from simulation"""
    
    try:
        import scipy.io
        
        print(f"Loading result file: {mat_file_path}")
        mat_data = scipy.io.loadmat(mat_file_path)
        
        # Print available variables
        variables = [key for key in mat_data.keys() if not key.startswith('_')]
        print(f"Available variables: {len(variables)}")
        
        # Look for common TEASER variables
        common_vars = ['time']
        teaser_vars = [v for v in variables if any(x in v.lower() 
                      for x in ['temp', 'load', 'heat', 'cool', 'air'])]
        
        print(f"Time-related variables: {[v for v in variables if 'time' in v.lower()]}")
        print(f"Temperature/Energy variables: {teaser_vars[:5]}...")  # Show first 5
        
        # Extract time and a few key variables
        if 'time' in mat_data:
            time = mat_data['time'].flatten()
            results = {'time_hours': time / 3600}  # Convert to hours
            
            # Add a few variables for analysis
            for var in teaser_vars[:3]:  # Take first 3 relevant variables
                if var in mat_data:
                    results[var] = mat_data[var].flatten()
            
            df = pd.DataFrame(results)
            return df
        else:
            print("❌ No time variable found in results")
            return None
            
    except ImportError:
        print("❌ scipy not available. Install with: pip install scipy")
        return None
    except Exception as e:
        print(f"❌ Failed to analyze results: {e}")
        return None

def create_quick_plot(df, building_name):
    """Create a quick plot of simulation results"""
    
    try:
        plt.figure(figsize=(12, 6))
        
        # Plot up to 3 variables (excluding time)
        plot_vars = [col for col in df.columns if col != 'time_hours'][:3]
        
        for i, var in enumerate(plot_vars):
            plt.subplot(1, len(plot_vars), i+1)
            plt.plot(df['time_hours'], df[var])
            plt.title(f'{var}')
            plt.xlabel('Time [hours]')
            plt.grid(True)
        
        plt.suptitle(f'Simulation Results - {building_name}')
        plt.tight_layout()
        
        plot_file = f'{building_name}_results.png'
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📈 Plot saved: {plot_file}")
        plt.show()
        
    except Exception as e:
        print(f"⚠ Could not create plot: {e}")

def run_all_your_buildings(export_directory):
    """
    Run simulations for all your buildings
    """
    
    print("🚀 BATCH SIMULATION - All Buildings")
    print("=" * 50)
    
    # Analyze structure
    building_dirs, package_file = analyze_your_teaser_export(export_directory)
    
    # Setup OMPython
    omc = setup_ompython_for_your_models()
    if not omc:
        return None
    
    results = {}
    successful = 0
    failed = 0
    
    for i, building_dir in enumerate(building_dirs):
        print(f"\n[{i+1}/{len(building_dirs)}] Processing: {building_dir.name}")
        
        try:
            result_file = simulate_your_teaser_building(omc, building_dir, package_file)
            if result_file:
                results[building_dir.name] = result_file
                successful += 1
                print(f"✅ Success: {building_dir.name}")
            else:
                failed += 1
                print(f"❌ Failed: {building_dir.name}")
                
        except Exception as e:
            failed += 1
            print(f"❌ Error in {building_dir.name}: {e}")
    
    print(f"\n📊 SUMMARY:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Results: {list(results.keys())}")
    
    return results

# =============================================================================
# USAGE EXAMPLES FOR YOUR SPECIFIC CASE
# =============================================================================

def diagnose_openmodelica_setup():
    """
    Comprehensive diagnosis of OpenModelica setup and TEASER export
    """
    print("🔍 DIAGNOSING OPENMODELICA SETUP")
    print("=" * 50)
    
    try:
        from OMPython import OMCSessionZMQ
        omc = OMCSessionZMQ()
        
        print("1️⃣ OPENMODELICA INFORMATION:")
        print(f"   Version: {omc.sendExpression('getVersion()')}")
        print(f"   Installation path: {omc.sendExpression('getInstallationDirectoryPath()')}")
        print(f"   Library path: {omc.sendExpression('getModelicaPath()')}")
        
        print("\n2️⃣ AVAILABLE LIBRARIES:")
        packages = omc.sendExpression("getPackages()")
        for pkg in packages:
            print(f"   - {pkg}")
        
        print("\n3️⃣ LIBRARY INSTALLATION CHECK:")
        # Check common TEASER-related libraries
        libraries_to_check = [
            "Modelica", "AixLib", "Buildings", "IDEAS", "IBPSA"
        ]
        
        for lib in libraries_to_check:
            try:
                result = omc.sendExpression(f"loadModel({lib})")
                status = "✓ Available" if result else "✗ Not found"
                print(f"   {lib}: {status}")
            except:
                print(f"   {lib}: ✗ Error loading")
        
        return omc
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        return None

def inspect_teaser_export_structure(export_directory):
    """
    Deep inspection of TEASER export structure
    """
    print(f"\n🔍 INSPECTING TEASER EXPORT: {export_directory}")
    print("=" * 50)
    
    export_path = Path(export_directory)
    
    print("1️⃣ DIRECTORY STRUCTURE:")
    for item in export_path.iterdir():
        if item.is_dir():
            mo_files = list(item.glob("*.mo"))
            print(f"   📁 {item.name}/ ({len(mo_files)} .mo files)")
            for mo_file in mo_files[:3]:  # Show first 3 files
                print(f"      - {mo_file.name}")
            if len(mo_files) > 3:
                print(f"      ... and {len(mo_files)-3} more")
        else:
            print(f"   📄 {item.name}")
    
    print("\n2️⃣ PACKAGE.MO CONTENT:")
    package_file = export_path / "package.mo"
    if package_file.exists():
        with open(package_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print("   First 500 characters:")
            print("   " + content[:500].replace('\n', '\n   '))
            
        # Look for package name and model references
        lines = content.split('\n')
        for line in lines[:20]:  # First 20 lines
            if 'package' in line.lower() or 'model' in line.lower():
                print(f"   Key line: {line.strip()}")
    else:
        print("   ❌ package.mo not found!")
        
    print("\n3️⃣ SAMPLE BUILDING MODEL:")
    building_dirs = [d for d in export_path.iterdir() 
                    if d.is_dir() and d.name.startswith("NL_Building_")]
    
    if building_dirs:
        sample_building = building_dirs[0]
        print(f"   Inspecting: {sample_building.name}")
        
        mo_files = list(sample_building.glob("*.mo"))
        for mo_file in mo_files:
            print(f"   📄 {mo_file.name}")
            # Read first few lines
            try:
                with open(mo_file, 'r', encoding='utf-8') as f:
                    first_lines = f.readlines()[:10]
                    for i, line in enumerate(first_lines):
                        if line.strip():
                            print(f"      L{i+1}: {line.strip()}")
                print("      ...")
                break  # Just show first .mo file
            except:
                print("      (Could not read file)")

# Add this to the main workflow
def main_workflow_for_your_export():
    """
    Main workflow specifically for your TEASER export with full diagnosis
    """
    
    # 🔧 MODIFY THIS PATH TO YOUR TEASER EXPORT DIRECTORY
    export_directory = r"_3_Pre_Ene_Sys_Mod/output/Project"  
    
    print("🎯 COMPREHENSIVE TEASER → OPENMODELICA DIAGNOSIS")
    print("=" * 60)
    
    # Step 1: Diagnose OpenModelica setup
    omc = diagnose_openmodelica_setup()
    if not omc:
        return None
    
    # Step 2: Inspect TEASER export structure
    inspect_teaser_export_structure(export_directory)
    
    # Step 3: Try the simulation with better debugging
    print("\n" + "=" * 60)
    print("🧪 ATTEMPTING SIMULATION WITH FULL DEBUGGING")
    
    # Continue with the existing workflow but with more info
    building_dirs, package_file = analyze_your_teaser_export(export_directory)
    
    if building_dirs:
        test_building = building_dirs[0]
        print(f"\n🎯 Testing building: {test_building.name}")
        
        result_file = simulate_your_teaser_building(omc, test_building, package_file)
        
        if result_file:
            print("\n✅ SUCCESS! Simulation completed.")
            return result_file
        else:
            print("\n📋 TROUBLESHOOTING SUGGESTIONS:")
            print("1. Check if AixLib is installed: https://github.com/RWTH-EBC/AixLib")
            print("2. Try exporting from TEASER with different library (Buildings instead of AixLib)")
            print("3. Manual check: Open OpenModelica OMEdit and try loading package.mo")
            print("4. Check TEASER export parameters - maybe try export_ibpsa() instead")
            return None
    else:
        print("❌ No building directories found!")
        return None

if __name__ == "__main__":
    # Run the main workflow
    results = main_workflow_for_your_export()