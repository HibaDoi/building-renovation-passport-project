"""
Debug script to test OpenModelica connection and model loading
"""

import os
from pathlib import Path
from OMPython import OMCSessionZMQ

def debug_openmodelica():
    """Debug OpenModelica setup"""
    print("=== DEBUGGING OPENMODELICA SETUP ===")
    
    # Connect to OpenModelica
    try:
        omc = OMCSessionZMQ()
        version = omc.sendExpression("getVersion()")
        print(f"✓ OpenModelica version: {version}")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return
    
    # Check working directory
    cwd = omc.sendExpression("cd()")
    print(f"Current working directory: {cwd}")
    
    # Find your models
    model_path = Path("C:/Users/hp/TEASEROutput/Project/")
    if model_path.exists():
        print(f"✓ Model path exists: {model_path}")
        
        # List contents
        contents = list(model_path.iterdir())[:10]  # First 10 items
        print(f"Directory contents ({len(contents)} items shown):")
        for item in contents:
            print(f"  - {item.name} ({'folder' if item.is_dir() else 'file'})")
    else:
        print(f"✗ Model path not found: {model_path}")
        return
    
    # Try to load package
    package_file = model_path / "package.mo"
    if package_file.exists():
        print(f"✓ Package file exists: {package_file}")
        
        # Load package
        result = omc.sendExpression(f'loadFile("{package_file.absolute()}")')
        print(f"Load package result: {result}")
        
        # Get loaded classes
        classes = omc.sendExpression("getClassNames()")
        print(f"Loaded classes: {classes[:5]}...")  # First 5
        
    else:
        print(f"✗ Package file not found: {package_file}")
        return
    
    # Try a simple simulation
    print("\n=== TESTING SIMPLE SIMULATION ===")
    
    # Get first building model
    building_folders = [f for f in model_path.iterdir() 
                       if f.is_dir() and f.name.startswith("NL_Building_")]
    
    if building_folders:
        test_building = building_folders[0].name
        print(f"Testing with: {test_building}")
        
        # Check if model is valid first
        model_name = f"Project.{test_building}"
        check_result = omc.sendExpression(f'checkModel({model_name})')
        print(f"Model check result: {check_result}")
        
        # Get detailed error messages
        error_string = omc.sendExpression("getErrorString()")
        if error_string:
            print(f"Error details: {error_string}")
        
        # Try to simulate (short duration)
        sim_result = omc.sendExpression(f'''simulate({model_name}, 
            startTime=0, stopTime=86400, numberOfIntervals=24)''')
        
        print(f"Simulation result type: {type(sim_result)}")
        print(f"Simulation result: {sim_result}")
        
        # Get more error details after simulation attempt
        error_string = omc.sendExpression("getErrorString()")
        if error_string:
            print(f"Additional errors: {error_string}")
        
        # Check if result file was created
        if isinstance(sim_result, dict):
            result_file = sim_result.get('resultFile', '')
            messages = sim_result.get('messages', '')
            
            print(f"Result file: {result_file}")
            print(f"Messages: {messages}")
            
            if result_file and os.path.exists(result_file):
                print(f"✓ Result file exists: {result_file}")
            else:
                print(f"✗ Result file not found or empty")
                
                # Check current directory for .mat files
                current_dir = Path.cwd()
                mat_files = list(current_dir.glob("*.mat"))
                print(f"MAT files in current directory: {mat_files}")
        
        # Try to examine the model structure
        print(f"\n=== EXAMINING MODEL STRUCTURE ===")
        components = omc.sendExpression(f'getComponents({model_name})')
        print(f"Model components: {components[:3] if components else 'None'}...")  # First 3
        
        # Check model parameters
        parameters = omc.sendExpression(f'getParameters({model_name})')
        print(f"Model parameters: {parameters[:3] if parameters else 'None'}...")  # First 3
    
    print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_openmodelica()