#!/usr/bin/env python3
"""
INSTALL IBPSA LIBRARY FOR OPENMODELICA
Quick script to install the missing IBPSA library
"""

def install_ibpsa_library():
    """Install IBPSA library using OpenModelica package manager"""
    
    try:
        from OMPython import OMCSessionZMQ
        
        omc = OMCSessionZMQ()
        print("✓ OMPython connected!")
        
        print("🔄 Installing IBPSA library...")
        print("This may take a few minutes...")
        
        # Install IBPSA using OpenModelica's package manager
        install_result = omc.sendExpression('installPackage(IBPSA, "3.0.0", exactMatch=true)')
        
        print(f"📦 Installation result: {install_result}")
        
        if install_result:
            print("✅ IBPSA installation successful!")
            
            # Verify installation
            print("🔍 Verifying installation...")
            
            # Try to load IBPSA
            load_result = omc.sendExpression("loadModel(IBPSA)")
            print(f"IBPSA load test: {load_result}")
            
            # Check if package is available
            ibpsa_available = omc.sendExpression("isPackage(IBPSA)")
            print(f"IBPSA package check: {'✓' if ibpsa_available else '✗'}")
            
            if ibpsa_available:
                print("🎉 IBPSA is now ready to use!")
                
                # Show available packages
                packages = omc.sendExpression("getPackages()")
                print(f"Available packages: {packages}")
                
                return True
            else:
                print("❌ IBPSA installation may have failed")
                return False
        else:
            print("❌ IBPSA installation failed")
            
            # Try alternative installation method
            print("🔄 Trying alternative installation...")
            alt_result = omc.sendExpression('installPackage(IBPSA)')
            print(f"Alternative installation result: {alt_result}")
            
            if alt_result:
                # Test the alternative installation
                load_result = omc.sendExpression("loadModel(IBPSA)")
                if load_result:
                    print("✅ Alternative installation successful!")
                    return True
            
            return False
            
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def quick_manual_ibpsa_install():
    """Provide manual installation instructions"""
    
    print("\n📋 MANUAL INSTALLATION OPTION:")
    print("=" * 50)
    print("If automatic installation fails, you can install manually:")
    print()
    print("1. Open OpenModelica OMEdit")
    print("2. Go to Tools → Package Manager")
    print("3. Search for 'IBPSA'")
    print("4. Click Install")
    print()
    print("OR use command line:")
    print("1. Open OMShell (OpenModelica Shell)")
    print("2. Type: installPackage(IBPSA)")
    print("3. Press Enter and wait")

if __name__ == "__main__":
    print("🎯 INSTALLING IBPSA LIBRARY FOR TEASER SIMULATIONS")
    print("=" * 60)
    
    success = install_ibpsa_library()
    
    if success:
        print("\n✅ SUCCESS! IBPSA is installed and ready!")
        print("🎯 Next step: Run your building simulation script again")
    else:
        print("\n❌ Automatic installation failed")
        quick_manual_ibpsa_install()
        print("\n🎯 After manual installation, run your simulation script again")