#!/usr/bin/env python3
"""
AUTOMATIC AIXLIB INSTALLER FOR OPENMODELICA
===========================================

This script automatically downloads and installs AixLib for OpenModelica
"""

import os
import zipfile
import requests
from pathlib import Path
import tempfile

def download_aixlib(install_directory=None):
    """
    Automatically download AixLib from GitHub
    
    Args:
        install_directory: Where to install AixLib (default: temp directory)
    """
    
    print("📦 DOWNLOADING AIXLIB FROM GITHUB")
    print("=" * 50)
    
    # GitHub release URL for AixLib
    github_url = "https://github.com/RWTH-EBC/AixLib/archive/refs/heads/master.zip"
    
    if install_directory is None:
        install_directory = Path.home() / "OpenModelica" / "Libraries"
        install_directory.mkdir(parents=True, exist_ok=True)
    
    install_path = Path(install_directory)
    
    try:
        print(f"📍 Download URL: {github_url}")
        print(f"📂 Install location: {install_path}")
        
        # Download the ZIP file
        print("⬇️ Downloading AixLib...")
        response = requests.get(github_url, stream=True)
        response.raise_for_status()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_zip_path = temp_file.name
        
        print("✅ Download completed!")
        
        # Extract the ZIP file
        print("📂 Extracting AixLib...")
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(install_path)
        
        # Find the extracted folder (usually AixLib-master)
        extracted_folders = [d for d in install_path.iterdir() 
                           if d.is_dir() and 'aixlib' in d.name.lower()]
        
        if extracted_folders:
            aixlib_path = extracted_folders[0]
            print(f"✅ AixLib extracted to: {aixlib_path}")
            
            # Check if package.mo exists
            package_mo = aixlib_path / "package.mo"
            if package_mo.exists():
                print(f"✅ Found package.mo: {package_mo}")
                return aixlib_path
            else:
                print(f"❌ package.mo not found in {aixlib_path}")
                return None
        else:
            print("❌ Could not find extracted AixLib folder")
            return None
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None
    
    finally:
        # Clean up temporary file
        if 'temp_zip_path' in locals():
            try:
                os.unlink(temp_zip_path)
            except:
                pass

def install_aixlib_in_openmodelica(aixlib_path):
    """
    Install AixLib in OpenModelica using OMPython
    
    Args:
        aixlib_path: Path to AixLib directory containing package.mo
    """
    
    print("\n🔧 INSTALLING AIXLIB IN OPENMODELICA")
    print("=" * 50)
    
    try:
        from OMPython import OMCSessionZMQ
        
        omc = OMCSessionZMQ()
        print("✅ Connected to OpenModelica")
        
        # Load AixLib
        package_mo_path = aixlib_path / "package.mo"
        print(f"📦 Loading AixLib from: {package_mo_path}")
        
        load_result = omc.sendExpression(f'loadFile("{package_mo_path}")')
        print(f"Load result: {load_result}")
        
        if load_result:
            # Verify AixLib is loaded
            is_loaded = omc.sendExpression("isPackage(AixLib)")
            if is_loaded:
                print("✅ AixLib successfully installed!")
                
                # Get AixLib version info
                try:
                    version_info = omc.sendExpression("getVersion(AixLib)")
                    print(f"📋 AixLib version: {version_info}")
                except:
                    print("📋 AixLib loaded (version info not available)")
                
                return True
            else:
                print("❌ AixLib package not recognized")
                return False
        else:
            print("❌ Failed to load AixLib")
            errors = omc.sendExpression("getErrorString()")
            if errors:
                print(f"Errors: {errors}")
            return False
            
    except ImportError:
        print("❌ OMPython not available")
        return False
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def test_aixlib_installation():
    """
    Test if AixLib is working with a simple model
    """
    
    print("\n🧪 TESTING AIXLIB INSTALLATION")
    print("=" * 50)
    
    try:
        from OMPython import OMCSessionZMQ
        
        omc = OMCSessionZMQ()
        
        # Test basic AixLib functionality
        tests = [
            ("Load Modelica", "loadModel(Modelica)"),
            ("Load AixLib", "loadModel(AixLib)"),
            ("Check AixLib package", "isPackage(AixLib)"),
            ("List AixLib subpackages", "getPackages(AixLib)")
        ]
        
        results = {}
        for test_name, command in tests:
            try:
                result = omc.sendExpression(command)
                results[test_name] = result
                status = "✅" if result else "❌"
                print(f"{status} {test_name}: {result}")
            except Exception as e:
                results[test_name] = f"Error: {e}"
                print(f"❌ {test_name}: Error - {e}")
        
        # Overall assessment
        if results.get("Check AixLib package"):
            print("\n🎉 AIXLIB INSTALLATION SUCCESSFUL!")
            print("You can now use AixLib with your TEASER models!")
            return True
        else:
            print("\n❌ AixLib installation needs troubleshooting")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def complete_aixlib_setup():
    """
    Complete AixLib setup process
    """
    
    print("🚀 COMPLETE AIXLIB SETUP FOR TEASER")
    print("=" * 60)
    
    # Step 1: Download AixLib
    aixlib_path = download_aixlib()
    if not aixlib_path:
        print("❌ Failed to download AixLib")
        return False
    
    # Step 2: Install in OpenModelica
    install_success = install_aixlib_in_openmodelica(aixlib_path)
    if not install_success:
        print("❌ Failed to install AixLib in OpenModelica")
        return False
    
    # Step 3: Test installation
    test_success = test_aixlib_installation()
    if not test_success:
        print("❌ AixLib installation test failed")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS! AIXLIB IS NOW READY FOR TEASER!")
    print("=" * 60)
    print("✅ AixLib downloaded and installed")
    print("✅ OpenModelica can access AixLib")
    print("✅ Ready to simulate TEASER models")
    
    print("\n📋 NEXT STEPS:")
    print("1. Go back to your TEASER → OpenModelica simulation script")
    print("2. Run it again - AixLib should now be available")
    print("3. Your building simulations should work!")
    
    return True

def manual_installation_guide():
    """
    Provide manual installation instructions
    """
    
    print("📖 MANUAL AIXLIB INSTALLATION GUIDE")
    print("=" * 50)
    
    print("""
    If the automatic installation doesn't work, follow these manual steps:
    
    1️⃣ DOWNLOAD AIXLIB:
       • Go to: https://github.com/RWTH-EBC/AixLib
       • Click "Code" → "Download ZIP"
       • Extract to C:\\AixLib-master\\
    
    2️⃣ INSTALL IN OPENMODELICA:
       • Open OMEdit (OpenModelica Connection Editor)
       • Go to File → Load Library
       • Navigate to C:\\AixLib-master\\
       • Select "package.mo"
       • Click "Open"
    
    3️⃣ VERIFY INSTALLATION:
       • In OMEdit, check if "AixLib" appears in the Libraries Browser
       • You should see AixLib with various subpackages
    
    4️⃣ TEST WITH PYTHON:
       • Run your simulation script again
       • AixLib should now be available
    
    🔧 TROUBLESHOOTING:
       • If OMEdit won't open: Check OpenModelica installation
       • If package.mo won't load: Try downloading a different AixLib version
       • If still doesn't work: Try the IBPSA export method instead
    """)

if __name__ == "__main__":
    # Run the complete setup
    success = complete_aixlib_setup()
    
    if not success:
        print("\n" + "=" * 60)
        print("⚠️  AUTOMATIC INSTALLATION FAILED")
        manual_installation_guide()
        
        print("\nALTERNATIVE: Use IBPSA export instead")
        print("Change your TEASER export to: prj.export_ibpsa()")