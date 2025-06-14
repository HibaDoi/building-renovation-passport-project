#!/usr/bin/env python3
"""
Script pour comparer l'environnement OMEdit vs OMPython
"""

from OMPython import OMCSessionZMQ
import os

def compare_environments():
    """Compare les environnements OMEdit et OMPython"""
    
    print("🔍 DIAGNOSTIC: Comparaison OMEdit vs OMPython")
    print("=" * 60)
    
    try:
        omc = OMCSessionZMQ()
        
        # 1. Version OpenModelica
        version = omc.sendExpression("getVersion()")
        print(f"📋 Version OpenModelica: {version}")
        
        # 2. Variables d'environnement importantes
        print("\n🌍 Variables d'environnement:")
        env_vars = ['MODELICAPATH', 'OPENMODELICAHOME', 'OPENMODELICALIBRARY']
        for var in env_vars:
            value = os.environ.get(var, 'NON DÉFINIE')
            print(f"   {var}: {value}")
        
        # 3. MODELICAPATH dans OMC
        modelica_path = omc.sendExpression("getModelicaPath()")
        print(f"   MODELICAPATH (OMC): {modelica_path}")
        
        # 4. Bibliothèques préchargées
        print("\n📚 Bibliothèques préchargées:")
        loaded_classes = omc.sendExpression("getClassNames()")
        if loaded_classes:
            for cls in loaded_classes[:10]:  # Premiers 10
                print(f"   - {cls}")
            if len(loaded_classes) > 10:
                print(f"   ... et {len(loaded_classes)-10} autres")
        
        # 5. Test de chargement AixLib
        print(f"\n🧪 Test de chargement AixLib:")
        aixlib_path = r"C:/AixLib-main/AixLib-main/AixLib/package.mo"
        
        if os.path.exists(aixlib_path):
            print(f"   ✅ Fichier AixLib existe: {aixlib_path}")
            result = omc.sendExpression(f'loadFile("{aixlib_path}")')
            print(f"   📤 Résultat loadFile: {result}")
            
            errors = omc.sendExpression("getErrorString()")
            if errors and errors.strip():
                print(f"   ⚠️  Erreurs/Avertissements: {errors[:200]}...")
            else:
                print(f"   ✅ Aucune erreur lors du chargement")
        else:
            print(f"   ❌ Fichier AixLib introuvable")
        
        # 6. Test de chargement du package TEASER
        print(f"\n🧪 Test de chargement package TEASER:")
        package_path = r"C:/Users/hp/TEASEROutput/Project/package.mo"
        
        if os.path.exists(package_path):
            print(f"   ✅ Fichier package existe: {package_path}")
            result = omc.sendExpression(f'loadFile("{package_path}")')
            print(f"   📤 Résultat loadFile: {result}")
            
            errors = omc.sendExpression("getErrorString()")
            if errors and errors.strip():
                print(f"   ⚠️  Erreurs/Avertissements: {errors[:300]}...")
            else:
                print(f"   ✅ Aucune erreur lors du chargement")
        else:
            print(f"   ❌ Fichier package introuvable")
        
        # 7. Vérification des classes du projet
        print(f"\n🏢 Classes du projet:")
        try:
            classes = omc.sendExpression("getClassNames(Project)")
            if classes:
                building_count = sum(1 for cls in classes if 'NL_Building_' in str(cls))
                print(f"   📊 Total classes: {len(classes)}")
                print(f"   🏠 Bâtiments (NL_Building_*): {building_count}")
                
                # Premier bâtiment pour test
                if building_count > 0:
                    first_building = None
                    for cls in classes:
                        if 'NL_Building_' in str(cls):
                            cls_name = str(cls).strip('"')
                            first_building = f"Project.{cls_name}"
                            break
                    
                    if first_building:
                        print(f"   🧪 Test du premier bâtiment: {first_building}")
                        # Test de vérification du modèle
                        check_result = omc.sendExpression(f'checkModel({first_building})')
                        print(f"   📋 Résultat checkModel: {check_result}")
            else:
                print(f"   ❌ Aucune classe trouvée dans le projet")
        except Exception as e:
            print(f"   ❌ Erreur lors de la vérification: {e}")
        
        # 8. Packages disponibles
        print(f"\n📦 Packages disponibles:")
        try:
            available = omc.sendExpression("getAvailablePackageVersions()")
            if available:
                # Chercher AixLib, SDF, Modelica_DeviceDrivers
                important_packages = ['AixLib', 'SDF', 'Modelica_DeviceDrivers', 'Modelica']
                for pkg in important_packages:
                    found = any(pkg in str(p) for p in available if p)
                    status = "✅" if found else "❌"
                    print(f"   {status} {pkg}")
        except Exception as e:
            print(f"   ❌ Erreur lors de la vérification des packages: {e}")
        
        omc.sendExpression("quit()")
        
    except Exception as e:
        print(f"❌ Erreur globale: {e}")

if __name__ == "__main__":
    compare_environments()