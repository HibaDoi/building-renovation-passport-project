#!/usr/bin/env python3
"""
DEBUG WHAT'S WRONG WITH THE .MO FILES
Let's see exactly what's in your TEASER building model
"""

from pathlib import Path

def debug_mo_file_content(project_directory):
    """
    FOCUSED DEBUG - Only show essential info
    """
    
    print("🎯 FOCUSED DEBUGGING - ESSENTIAL INFO ONLY")
    print("=" * 50)
    
    project_path = Path(project_directory)
    
    # Find building directories
    building_dirs = [d for d in project_path.iterdir() 
                    if d.is_dir() and d.name.startswith("NL_Building_")]
    
    if not building_dirs:
        print("❌ No building directories found!")
        return
    
    # Take the first building for debugging
    test_building = building_dirs[0]
    building_name = test_building.name
    
    print(f"🏢 Testing: {building_name}")
    
    # Check the main building .mo file
    building_mo = test_building / f"{building_name}.mo"
    
    if building_mo.exists():
        try:
            with open(building_mo, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📊 FILE INFO:")
            print(f"   File size: {len(content)} characters")
            
            # FOCUSED DIAGNOSTIC CHECKS
            print(f"\n🔍 KEY DIAGNOSTICS:")
            print(f"   - Contains 'model': {'✓' if 'model' in content else '✗'}")
            print(f"   - Contains 'within': {'✓' if 'within' in content else '✗'}")
            print(f"   - Contains 'IBPSA': {'✓' if 'IBPSA' in content else '✗'}")
            print(f"   - Contains 'AixLib': {'✓' if 'AixLib' in content else '✗'}")
            print(f"   - Ends properly: {'✓' if content.strip().endswith(';') or f'end {building_name}' in content else '✗'}")
            
            # SHOW ONLY KEY LINES
            lines = content.split('\n')
            print(f"\n📋 IMPORTANT LINES ONLY:")
            key_lines = []
            for i, line in enumerate(lines):
                if line.strip() and any(keyword in line.lower() for keyword in ['within', 'model', 'extends', 'import', 'end']):
                    key_lines.append(f"   Line {i+1}: {line.strip()}")
                if len(key_lines) >= 10:  # Limit to first 10 key lines
                    break
            
            for line in key_lines:
                print(line)
            
            # Show first line and last line
            print(f"\n📌 FIRST LINE: {lines[0].strip()}")
            print(f"📌 LAST LINE: {lines[-1].strip()}")
            
        except Exception as e:
            print(f"❌ Could not read building file: {e}")
    else:
        print(f"❌ Building .mo file not found")
    
    # Quick check of package files
    package_mo = test_building / "package.mo"
    if package_mo.exists():
        try:
            with open(package_mo, 'r', encoding='utf-8') as f:
                pkg_content = f.read()
            print(f"\n📦 BUILDING package.mo: {len(pkg_content)} chars")
            print(f"   Content: {pkg_content.strip()}")
        except:
            print(f"❌ Could not read building package.mo")
    
    main_package = project_path / "package.mo"
    if main_package.exists():
        try:
            with open(main_package, 'r', encoding='utf-8') as f:
                main_content = f.read()
            print(f"\n📦 MAIN package.mo: {len(main_content)} chars")
            # Show just first 200 chars
            print(f"   Start: {main_content[:200]}...")
        except:
            print(f"❌ Could not read main package.mo")

def try_direct_openmodelica_test():
    """
    FOCUSED OpenModelica error test - only essential errors
    """
    
    print("\n🧪 OPENMODELICA ERROR TEST")
    print("=" * 40)
    
    try:
        from OMPython import OMCSessionZMQ
        
        omc = OMCSessionZMQ()
        print("✓ Connected to OpenModelica")
        
        # Load basic libraries
        omc.sendExpression("loadModel(Modelica)")
        omc.sendExpression("loadModel(IBPSA)")
        
        # Clear any previous errors
        omc.sendExpression("clearMessages()")
        
        # Try to load the problematic file
        building_path = r"_3_Pre_Ene_Sys_Mod\output\Project\NL_Building_0503100000000010\NL_Building_0503100000000010.mo"
        
        print(f"🎯 Loading: {Path(building_path).name}")
        
        # Test the load
        result = omc.sendExpression(f'loadFile("{building_path}")')
        print(f"Load result: {result}")
        
        # Get ONLY the essential error info
        errors = omc.sendExpression("getErrorString()")
        
        print(f"\n❌ ESSENTIAL ERRORS ONLY:")
        if errors:
            # Filter out warnings, show only errors
            error_lines = errors.split('\n')
            key_errors = []
            for line in error_lines:
                if 'Error:' in line or 'error:' in line:
                    key_errors.append(line.strip())
                elif 'Expected' in line or 'found' in line:
                    key_errors.append(line.strip())
            
            if key_errors:
                for error in key_errors[:5]:  # Show max 5 key errors
                    print(f"   {error}")
            else:
                print("   No critical errors found (might be warnings only)")
                print(f"   First few lines: {errors[:300]}...")
        else:
            print("   No errors reported")
        
        return len(key_errors) if 'key_errors' in locals() else 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

if __name__ == "__main__":
    project_dir = r"_3_Pre_Ene_Sys_Mod/output/Project"
    
    print("🎯 FOCUSED DEBUGGING - ESSENTIALS ONLY")
    print("=" * 50)
    
    # Debug file content (focused)
    debug_mo_file_content(project_dir)
    
    # Test with OpenModelica (focused)
    error_count = try_direct_openmodelica_test()
    
    print(f"\n🎯 SUMMARY:")
    if error_count == 0:
        print("✅ No critical errors found - might be library reference issue")
    elif error_count and error_count > 0:
        print(f"❌ Found {error_count} critical errors - syntax issues")
    else:
        print("❓ Could not determine error status")
    
    print(f"\n💡 READY FOR SOLUTION:")
    print("Share this focused output and I'll give you the exact fix!")