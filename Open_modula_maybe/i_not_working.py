#!/usr/bin/env python3
"""
Script de simulation automatique TEASER avec TOUTES les corrections
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import re

try:
    from OMPython import OMCSessionZMQ
except ImportError:
    print("Erreur: OMPython n'est pas installé.")
    sys.exit(1)

class TeaserSimulatorFixed:
    """Simulateur TEASER avec toutes les corrections"""
    
    def __init__(self, package_path: str, aixlib_path: str, output_dir: str = None):
        self.package_path = Path(package_path)
        self.aixlib_path = Path(aixlib_path)
        self.output_dir = Path(output_dir) if output_dir else self.package_path.parent / "simulation_results"
        
        # Paramètres de simulation
        self.stop_time = 3.154e7  # 1 an
        self.tolerance = 1e-6
        self.solver = "dassl"
        
        self._setup_logging()
        self.omc = None
        self.package_name = None
        
    def _setup_logging(self):
        """Configure le logging"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('TeaserSimulatorFixed')
        self.logger.setLevel(logging.INFO)
        
        # Supprimer les anciens handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Handler fichier
        file_handler = logging.FileHandler(self.output_dir / 'simulation_log.txt', mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Handler console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def connect_omc(self) -> bool:
        """Connexion à OpenModelica"""
        try:
            self.logger.info("Connexion à OpenModelica...")
            self.omc = OMCSessionZMQ()
            
            version = self.omc.sendExpression("getVersion()")
            self.logger.info(f"OpenModelica version: {version}")
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur de connexion: {e}")
            return False
    
    def install_missing_packages(self) -> bool:
        """Installe les packages manquants"""
        try:
            self.logger.info("🔧 Installation des packages manquants...")
            
            # Installation SDF
            self.logger.info("📦 Installation SDF...")
            result_sdf = self.omc.sendExpression('installPackage(SDF, "0.4.2", exactMatch=false)')
            if result_sdf:
                self.logger.info("✅ SDF installé")
            else:
                self.logger.warning("⚠️ Échec installation SDF")
            
            # Installation Modelica_DeviceDrivers
            self.logger.info("📦 Installation Modelica_DeviceDrivers...")
            result_mdd = self.omc.sendExpression('installPackage(Modelica_DeviceDrivers, "2.1.1", exactMatch=false)')
            if result_mdd:
                self.logger.info("✅ Modelica_DeviceDrivers installé")
            else:
                self.logger.warning("⚠️ Échec installation Modelica_DeviceDrivers")
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur installation packages: {e}")
            return False
    
    def load_libraries(self) -> bool:
        """Charge toutes les bibliothèques avec corrections de versions"""
        try:
            self.logger.info("📚 Chargement des bibliothèques avec versions compatibles...")
            
            # 1. Chargement Modelica 4.0.0 spécifiquement (compatible avec AixLib)
            self.logger.info("Chargement Modelica 4.0.0...")
            modelica_result = self.omc.sendExpression('loadModel(Modelica, {"4.0.0"})')
            if not modelica_result:
                self.logger.warning("Échec Modelica 4.0.0, tentative version par défaut...")
                self.omc.sendExpression('loadModel(Modelica)')
            else:
                self.logger.info("✅ Modelica 4.0.0 chargé")
            
            # 2. Chargement AixLib
            self.logger.info(f"Chargement AixLib: {self.aixlib_path}")
            result_aixlib = self.omc.sendExpression(f'loadFile("{self.aixlib_path}")')
            if not result_aixlib:
                self.logger.error("Échec chargement AixLib")
                return False
            
            # 3. Chargement package TEASER
            self.logger.info(f"Chargement package TEASER: {self.package_path}")
            result_teaser = self.omc.sendExpression(f'loadFile("{self.package_path}")')
            if not result_teaser:
                self.logger.error("Échec chargement package TEASER")
                return False
            
            # 4. CORRECTION CRUCIALE: Conversion AixLib
            self.logger.info("🔄 Application conversion AixLib...")
            conversion_result = self.omc.sendExpression('convertPackageToLibrary(Project, AixLib, "2.1.2")')
            if conversion_result:
                self.logger.info("✅ Conversion AixLib appliquée")
            else:
                self.logger.warning("⚠️ Problème conversion AixLib - on continue quand même")
            
            # 5. Nettoyage des erreurs de compatibilité
            self.logger.info("🧹 Nettoyage des messages d'avertissement...")
            self.omc.sendExpression("clearMessages()")
            
            # 6. Obtenir nom du package
            self.package_name = self._get_package_name()
            if not self.package_name:
                self.logger.error("Impossible de déterminer le nom du package")
                return False
            
            # 7. Vérification finale
            classes = self.omc.sendExpression(f'getClassNames({self.package_name})')
            if not classes:
                self.logger.error(f"Package {self.package_name} vide")
                return False
            
            self.logger.info(f"✅ Toutes les bibliothèques chargées - {len(classes)} classes")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement bibliothèques: {e}")
            return False
    
    def _get_package_name(self) -> str:
        """Obtient le nom du package"""
        try:
            with open(self.package_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            match = re.search(r'package\s+(\w+)', content)
            if match:
                return match.group(1)
            
            return self.package_path.parent.name
            
        except Exception as e:
            self.logger.error(f"Erreur lecture package: {e}")
            return None
    
    def get_building_models(self) -> List[str]:
        """Récupère les modèles de bâtiments"""
        try:
            self.logger.info("🔍 Recherche des modèles de bâtiments...")
            
            classes = self.omc.sendExpression(f'getClassNames({self.package_name})')
            
            buildings = []
            if classes:
                for cls in classes:
                    class_name = str(cls).strip('"')
                    if class_name.startswith('NL_Building_'):
                        buildings.append(f"{self.package_name}.{class_name}")
            
            self.logger.info(f"Trouvé {len(buildings)} modèles de bâtiments")
            return buildings
            
        except Exception as e:
            self.logger.error(f"Erreur recherche modèles: {e}")
            return []
    
    def simulate_building(self, model_name: str) -> Tuple[bool, str]:
        """Simule un bâtiment avec gestion d'erreurs améliorée"""
        try:
            building_id = model_name.split('.')[-1]
            output_file = self.output_dir / f"{building_id}_result.mat"
            
            self.logger.info(f"🚀 Simulation {building_id}...")
            
            # Nettoyage des messages d'erreur précédents
            self.omc.sendExpression("clearMessages()")
            
            # Vérification préalable du modèle
            check_result = self.omc.sendExpression(f'checkModel({model_name})')
            if "Error" in str(check_result):
                return False, f"Erreur dans checkModel: {check_result[:200]}"
            
            # Simulation avec gestion d'erreurs améliorée
            sim_command = f'''simulate({model_name}, 
                                    stopTime={self.stop_time}, 
                                    tolerance={self.tolerance}, 
                                    method="{self.solver}",
                                    outputFormat="mat",
                                    fileNamePrefix="{building_id}_result")'''
            
            start_time = time.time()
            result = self.omc.sendExpression(sim_command)
            end_time = time.time()
            
            # Récupération des messages après simulation
            messages = self.omc.sendExpression("getErrorString()")
            
            # Vérification résultat - recherche de succès même avec avertissements
            if result and ('SimulationResult' in str(result) or 'resultFile' in str(result)):
                # Vérification du fichier de résultat
                source_file = Path(f"{building_id}_result.mat")
                if source_file.exists():
                    source_file.rename(output_file)
                    duration = end_time - start_time
                    return True, f"Succès en {duration:.1f}s - {output_file}"
                else:
                    return False, f"Fichier résultat non généré - {messages[:200] if messages else 'Aucun message'}"
            else:
                # Vérification si c'est juste des avertissements de compatibilité
                if messages and "fully compatible" in messages and "Error" not in messages:
                    # Peut-être que ça a fonctionné malgré les avertissements
                    source_file = Path(f"{building_id}_result.mat")
                    if source_file.exists():
                        source_file.rename(output_file)
                        duration = end_time - start_time
                        return True, f"Succès avec avertissements en {duration:.1f}s"
                
                return False, f"Échec - {messages[:300] if messages else 'Pas de message d erreur'}"
            
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def run_all_simulations(self) -> Dict[str, bool]:
        """Lance toutes les simulations avec corrections"""
        
        # Étape 1: Connexion
        if not self.connect_omc():
            return {}
        
        # Étape 2: Installation packages manquants
        self.install_missing_packages()
        
        # Étape 3: Chargement bibliothèques
        if not self.load_libraries():
            return {}
        
        # Étape 4: Récupération des modèles
        buildings = self.get_building_models()
        if not buildings:
            self.logger.error("Aucun modèle trouvé")
            return {}
        
        # Étape 5: Simulations
        results = {}
        successful = 0
        failed = 0
        
        self.logger.info(f"🚀 Début simulations de {len(buildings)} bâtiments")
        
        for i, building in enumerate(buildings, 1):
            building_id = building.split('.')[-1]
            self.logger.info(f"[{i}/{len(buildings)}] {building_id}")
            
            success, message = self.simulate_building(building)
            results[building_id] = success
            
            if success:
                successful += 1
                self.logger.info(f"✅ {message}")
            else:
                failed += 1
                self.logger.error(f"❌ {message}")
        
        # Résumé
        self.logger.info("=" * 60)
        self.logger.info(f"RÉSUMÉ: {successful} succès, {failed} échecs")
        self.logger.info(f"Taux de succès: {successful/len(buildings)*100:.1f}%")
        
        return results
    
    def cleanup(self):
        """Nettoyage"""
        if self.omc:
            try:
                self.omc.sendExpression("quit()")
            except:
                pass

def main():
    """Fonction principale"""
    
    # Configuration
    PACKAGE_PATH = r"C:/Users/hp/TEASEROutput/Project/package.mo"
    AIXLIB_PATH = r"C:/AixLib-main/AixLib-main/AixLib/package.mo"
    OUTPUT_DIR = r"Open_modula_maybe/simulation_results"
    
    # Vérifications
    if not Path(PACKAGE_PATH).exists():
        print(f"❌ Fichier package introuvable: {PACKAGE_PATH}")
        return
    
    if not Path(AIXLIB_PATH).exists():
        print(f"❌ Fichier AixLib introuvable: {AIXLIB_PATH}")
        return
    
    # Simulation
    simulator = TeaserSimulatorFixed(
        package_path=PACKAGE_PATH,
        aixlib_path=AIXLIB_PATH,
        output_dir=OUTPUT_DIR
    )
    
    try:
        print("🚀 Démarrage simulation TEASER avec toutes les corrections...")
        results = simulator.run_all_simulations()
        
        if results:
            print("\n📊 RÉSULTATS DÉTAILLÉS:")
            for building, success in results.items():
                status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
                print(f"{building}: {status}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Simulation interrompue")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        simulator.cleanup()

if __name__ == "__main__":
    main()