#!/usr/bin/env python3
"""
FIX CIRCULAR REFERENCE IN BUILDING MODELS
The issue: within Project.NL_Building_0503100000000010; should be within Project;
"""

import os
import re
from pathlib import Path

def fix_circular_within_statements(project_directory):
    """
    Fix the circular within statements in building models
    """
    
    print("🔧 FIXING CIRCULAR WITHIN STATEMENTS")
    print("=" * 50)
    
    project_path = Path(project_directory)
    
    # Find all building directories
    building_dirs = [d for d in project_path.iterdir() 
                    if d.is_dir() and d.name.startswith("NL_Building_")]
    
    print(f"Found {len(building_dirs)} building directories")
    
    fixed_count = 0
    
    for building_dir in building_dirs:
        building_name = building_dir.name
        building_mo = building_dir / f"{building_name}.mo"
        
        if building_mo.exists():
            try:
                # Read the file
                with open(building_mo, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if it has the circular reference
                circular_pattern = f"within Project.{building_name};"
                
                if circular_pattern in content:
                    print(f"🔧 Fixing {building_name}")
                    
                    # Fix: Replace with correct within statement
                    fixed_content = content.replace(
                        circular_pattern,
                        "within Project;"
                    )
                    
                    # Write back the fixed content
                    with open(building_mo, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    
                    fixed_count += 1
                    print(f"   ✓ Fixed circular reference")
                else:
                    print(f"   - {building_name}: No circular reference found")
                
            except Exception as e:
                print(f"   ❌ Error fixing {building_name}: {e}")
    
    print(f"\n✅ Fixed {fixed_count} building models")
    return fixed_count

def verify_fixes(project_directory):
    """
    Verify that the fixes worked
    """
    
    print("\n🔍 VERIFYING FIXES")
    print("=" * 30)
    
    project_path = Path(project_directory)
    building_dirs = [d for d in project_path.iterdir() 
                    if d.is_dir() and d.name.startswith("NL_Building_")]
    
    # Test the first building
    test_building = building_dirs[0]
    building_name = test_building.name
    building_mo = test_building / f"{building_name}.mo"
    
    if building_mo.exists():
        with open(building_mo, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        for i, line in enumerate(lines[:10]):
            if 'within' in line.lower():
                print(f"   Line {i+1}: {line.strip()}")
                break
        
        # Quick diagnostic
        has_circular = f"within Project.{building_name};" in content
        has_correct = "within Project;" in content
        
        print(f"   Circular reference: {'❌' if not has_circular else '⚠️  Still present!'}")
        print(f"   Correct reference: {'✅' if has_correct else '❌'}")
        
        return has_correct and not has_circular
    
    return False

def test_openmodelica_after_fix(project_directory):
    """
    Test if OpenModelica can now load the fixed model
    """
    
    print("\n🧪 TESTING AFTER FIX")
    print("=" * 30)
    
    try:
        from OMPython import OMCSessionZMQ
        
        omc = OMCSessionZMQ()
        omc.sendExpression("loadModel(Modelica)")
        omc.sendExpression("loadModel(IBPSA)")
        
        # Clear previous errors
        omc.sendExpression("clearMessages()")
        
        # Try loading the main package
        project_path = Path(project_directory)
        main_package = project_path / "package.mo"
        
        print("🎯 Testing main package load...")
        main_result = omc.sendExpression(f'loadFile("{main_package}")')
        print(f"Main package result: {main_result}")
        
        if main_result:
            # Check what models are available
            models = omc.sendExpression("getClassNames(Project)")
            print(f"Available models in Project: {models}")
            
            # Try to find a building model
            if models:
                for model in models:
                    if isinstance(model, str) and "NL_Building_" in model:
                        print(f"🎯 Testing model: Project.{model}")
                        
                        # Test if model exists and can be checked
                        exists = omc.sendExpression(f"isModel(Project.{model})")
                        print(f"Model exists: {exists}")
                        
                        if exists:
                            # Try a quick model check
                            check = omc.sendExpression(f"checkModel(Project.{model})")
                            print(f"Model check: {'✅ OK' if check else '❌ Has issues'}")
                            
                            # Get any remaining errors
                            errors = omc.sendExpression("getErrorString()")
                            if errors and 'Error:' in errors:
                                print(f"Remaining errors: {errors[:200]}...")
                            else:
                                print("✅ No critical errors!")
                                return True
                        break
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    project_dir = r"_3_Pre_Ene_Sys_Mod/output/Project"
    
    print("🎯 FIXING CIRCULAR REFERENCE ISSUE")
    print("=" * 50)
    
    # Step 1: Fix the circular references
    fixed_count = fix_circular_within_statements(project_dir)
    
    if fixed_count > 0:
        # Step 2: Verify fixes
        verify_success = verify_fixes(project_dir)
        
        if verify_success:
            # Step 3: Test with OpenModelica
            test_success = test_openmodelica_after_fix(project_dir)
            
            if test_success:
                print("\n🎉 SUCCESS! Models should now work!")
                print("✅ Run your simulation script again")
            else:
                print("\n⚠️ Fixed circular reference, but other issues remain")
                print("💡 Still progress - try simulation again")
        else:
            print("\n❌ Fix verification failed")
    else:
        print("\n💡 No circular references found to fix")
        print("   The issue might be something else")
    
    print(f"\n🚀 NEXT STEP:")
    print(f"python teaser_simulation.py")