#!/usr/bin/env python3
"""
Script de simulation automatique TEASER avec corrections pour OpenModelica 1.25.0
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import re
import shutil

try:
    from OMPython import OMCSessionZMQ
except ImportError:
    print("Erreur: OMPython n'est pas installé.")
    sys.exit(1)

class TeaserSimulatorImproved:
    """Simulateur TEASER amélioré pour OpenModelica 1.25.0"""
    
    def __init__(self, package_path: str, aixlib_path: str, output_dir: str = None):
        self.package_path = Path(package_path).resolve()
        self.aixlib_path = Path(aixlib_path).resolve()
        self.output_dir = Path(output_dir) if output_dir else self.package_path.parent / "simulation_results"
        
        # Paramètres de simulation
        self.stop_time = 3.154e7  # 1 an
        self.tolerance = 1e-6
        self.solver = "dassl"
        
        self._setup_logging()
        self.omc = None
        self.package_name = None
        self.working_dir = None
        
    def _setup_logging(self):
        """Configure le logging"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('TeaserSimulator')
        self.logger.setLevel(logging.DEBUG)  # Changé à DEBUG pour plus de détails
        
        # Supprimer les anciens handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Handler fichier
        file_handler = logging.FileHandler(self.output_dir / 'simulation_log.txt', mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Handler console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def connect_omc(self) -> bool:
        """Connexion à OpenModelica avec configuration du répertoire de travail"""
        try:
            self.logger.info("Connexion à OpenModelica...")
            self.omc = OMCSessionZMQ()
            self.omc.sendExpression('setCommandLineOptions("-j=6")')
            version = self.omc.sendExpression("getVersion()")
            self.logger.info(f"OpenModelica version: {version}")
            
            # Définir le répertoire de travail
            self.working_dir = self.output_dir / "work"
            self.working_dir.mkdir(parents=True, exist_ok=True)
            
            # Changer le répertoire de travail d'OpenModelica
            self.omc.sendExpression(f'cd("{str(self.working_dir).replace(chr(92), "/")}")')
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur de connexion: {e}")
            return False
    
    def load_libraries(self) -> bool:
        """Charge toutes les bibliothèques avec gestion intelligente des versions"""
        try:
            self.logger.info("📚 Chargement des bibliothèques...")
            
            # 1. Ne pas charger Modelica explicitement - laisser OpenModelica gérer
            self.logger.info("Utilisation de la version Modelica par défaut d'OpenModelica")
            
            # 2. Charger AixLib
            self.logger.info(f"Chargement AixLib depuis: {self.aixlib_path}")
            aixlib_path_str = str(self.aixlib_path).replace('\\', '/')
            result_aixlib = self.omc.sendExpression(f'loadFile("{aixlib_path_str}")')
            if not result_aixlib:
                self.logger.error("Échec chargement AixLib")
                error_msg = self.omc.sendExpression("getErrorString()")
                self.logger.error(f"Erreur AixLib: {error_msg}")
                return False
            
            # 3. Charger le package TEASER
            self.logger.info(f"Chargement package TEASER depuis: {self.package_path}")
            teaser_path_str = str(self.package_path).replace('\\', '/')
            result_teaser = self.omc.sendExpression(f'loadFile("{teaser_path_str}")')
            if not result_teaser:
                self.logger.error("Échec chargement package TEASER")
                error_msg = self.omc.sendExpression("getErrorString()")
                self.logger.error(f"Erreur TEASER: {error_msg}")
                return False
            
            # 4. Obtenir le nom du package
            self.package_name = self._get_package_name()
            if not self.package_name:
                self.logger.error("Impossible de déterminer le nom du package")
                return False
            
            # 5. Vérifier que les modèles sont bien chargés
            classes = self.omc.sendExpression(f'getClassNames({self.package_name})')
            if not classes:
                self.logger.error(f"Package {self.package_name} vide ou non chargé")
                return False
            
            self.logger.info(f"✅ Bibliothèques chargées - {len(classes)} classes dans {self.package_name}")
            
            # 6. Nettoyer les messages d'avertissement
            self.omc.sendExpression("clearMessages()")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement bibliothèques: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def _get_package_name(self) -> str:
        """Obtient le nom du package depuis le fichier"""
        try:
            with open(self.package_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Rechercher le nom du package
            match = re.search(r'package\s+(\w+)', content)
            if match:
                return match.group(1)
            
            # Si pas trouvé, utiliser le nom du dossier parent
            return self.package_path.parent.name
            
        except Exception as e:
            self.logger.error(f"Erreur lecture package: {e}")
            return None
    
    def explore_package_structure(self):
        """Explore la structure du package pour debug"""
        try:
            self.logger.info("🔍 Exploration de la structure du package...")
            
            # Méthode 1: getClassNames récursif
            self.logger.info(f"Tentative 1: getClassNames({self.package_name}, recursive=false)")
            classes_direct = self.omc.sendExpression(f'getClassNames({self.package_name}, recursive=false)')
            if classes_direct:
                self.logger.info(f"Classes directes: {len(classes_direct)} trouvées")
                for i, cls in enumerate(classes_direct[:10]):  # Afficher les 10 premières
                    self.logger.info(f"  - {cls}")
                if len(classes_direct) > 10:
                    self.logger.info(f"  ... et {len(classes_direct) - 10} autres")
            
            # Méthode 2: getClassNames sans paramètres
            self.logger.info(f"\nTentative 2: getClassNames({self.package_name})")
            classes_all = self.omc.sendExpression(f'getClassNames({self.package_name})')
            if classes_all:
                # Compter les NL_Building
                nl_count = sum(1 for cls in classes_all if 'NL_Building_' in str(cls))
                self.logger.info(f"Total classes: {len(classes_all)}, dont {nl_count} contiennent 'NL_Building_'")
            
            # Méthode 3: Essayer getComponents
            self.logger.info(f"\nTentative 3: getComponents({self.package_name})")
            components = self.omc.sendExpression(f'getComponents({self.package_name})')
            if components:
                self.logger.info(f"Components: {len(components)} trouvés")
                for comp in components[:5]:
                    self.logger.info(f"  - {comp}")
            
        except Exception as e:
            self.logger.error(f"Erreur exploration: {e}")
    
    def get_building_models(self) -> List[str]:
        """Récupère les modèles de bâtiments en explorant l'intérieur des packages"""
        try:
            self.logger.info("🔍 Recherche des modèles de bâtiments...")
            
            # Obtenir toutes les classes du package principal
            classes = self.omc.sendExpression(f'getClassNames({self.package_name})')
            
            self.logger.info(f"Classes trouvées dans {self.package_name}: {len(classes) if classes else 0}")
            
            building_models = []
            nl_packages_found = 0
            
            if classes:
                for cls in classes:
                    class_name = str(cls).strip('"')
                    
                    # Ne prendre que les packages NL_Building_
                    if class_name.startswith('NL_Building_'):
                        nl_packages_found += 1
                        package_full_name = f"{self.package_name}.{class_name}"
                        
                        # Explorer l'intérieur du package pour trouver le modèle
                        if nl_packages_found <= 5:  # Debug sur les premiers
                            self.logger.info(f"\nExploration du package {class_name}:")
                            
                            # Obtenir les classes à l'intérieur du package building
                            sub_classes = self.omc.sendExpression(f'getClassNames({package_full_name})')
                            if sub_classes:
                                self.logger.info(f"  Sous-classes trouvées: {sub_classes}")
                                
                                # Chercher le modèle principal
                                for sub_cls in sub_classes:
                                    sub_class_name = str(sub_cls).strip('"')
                                    full_sub_name = f"{package_full_name}.{sub_class_name}"
                                    
                                    # Vérifier le type
                                    sub_type = self.omc.sendExpression(f'getClassRestriction({full_sub_name})')
                                    if nl_packages_found <= 5:
                                        self.logger.info(f"    - {sub_class_name}: {sub_type}")
                                    
                                    # Si c'est un model, l'ajouter
                                    if 'model' in str(sub_type).lower():
                                        building_models.append(full_sub_name)
                                        if nl_packages_found <= 5:
                                            self.logger.info(f"    ✓ Modèle trouvé: {full_sub_name}")
                                        break  # Prendre seulement le premier modèle
                        else:
                            # Pour les autres, chercher directement le modèle sans debug
                            sub_classes = self.omc.sendExpression(f'getClassNames({package_full_name})')
                            if sub_classes:
                                for sub_cls in sub_classes:
                                    sub_class_name = str(sub_cls).strip('"')
                                    full_sub_name = f"{package_full_name}.{sub_class_name}"
                                    sub_type = self.omc.sendExpression(f'getClassRestriction({full_sub_name})')
                                    if 'model' in str(sub_type).lower():
                                        building_models.append(full_sub_name)
                                        break
            
            self.logger.info(f"\nTrouvé {nl_packages_found} packages NL_Building_")
            self.logger.info(f"Trouvé {len(building_models)} modèles simulables")
            
            # Si aucun modèle trouvé avec cette méthode, essayer une approche plus simple
            if len(building_models) == 0:
                self.logger.warning("Aucun modèle trouvé dans les packages, tentative approche directe...")
                
                # Peut-être que le nom du modèle principal est standardisé
                standard_model_names = ['Building', 'building', 'BuildingModel', 'Model']
                
                for cls in classes[:10] if classes else []:  # Tester sur les 10 premiers
                    class_name = str(cls).strip('"')
                    if class_name.startswith('NL_Building_'):
                        package_full_name = f"{self.package_name}.{class_name}"
                        
                        # Essayer les noms standards
                        for model_name in standard_model_names:
                            test_name = f"{package_full_name}.{model_name}"
                            
                            # Vérifier si ce modèle existe
                            exists = self.omc.sendExpression(f'isModel({test_name})')
                            if exists:
                                building_models.append(test_name)
                                self.logger.info(f"Modèle trouvé par nom standard: {test_name}")
                                break
                
                # Si toujours rien, essayer de simuler directement les packages
                if len(building_models) == 0:
                    self.logger.warning("Aucun modèle trouvé, tentative simulation directe des packages...")
                    # Retourner les packages eux-mêmes
                    for cls in classes if classes else []:
                        class_name = str(cls).strip('"')
                        if class_name.startswith('NL_Building_'):
                            building_models.append(f"{self.package_name}.{class_name}")
            
            return building_models
            
        except Exception as e:
            self.logger.error(f"Erreur recherche modèles: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []
    
    def simulate_building(self, model_name: str) -> Tuple[bool, str]:
        """Simule un bâtiment avec gestion améliorée des chemins"""


        try:
            building_id = model_name.split('.')[-1]
                                # --- Sauter la simulation si un résultat existe déjà -------------------
            existing = self.output_dir / f"{building_id}_result.mat"
            if existing.exists():
                self.logger.info(f"⏩  Résultat déjà présent pour {building_id} – simulation ignorée")
                return True, "Existe déjà"
            # ----------------------------------------------------------------------
            
            self.logger.info(f"🚀 Simulation {building_id}...")
            
            # Nettoyer le répertoire de travail
            for file in self.working_dir.glob(f"{building_id}*"):
                try:
                    file.unlink()
                except:
                    pass
            
            # Nettoyer les messages
            self.omc.sendExpression("clearMessages()")
            
            # Commande de simulation
            sim_command = f'''simulate({model_name}, 
                                    stopTime={self.stop_time}, 
                                    tolerance={self.tolerance}, 
                                    method="{self.solver}",
                                    outputFormat="mat",
                                    fileNamePrefix="{building_id}")'''
            
            start_time = time.time()
            result = self.omc.sendExpression(sim_command)
            end_time = time.time()
            duration = end_time - start_time
            
            # Récupérer les messages
            messages = self.omc.sendExpression("getErrorString()")
            
            # Vérifier le résultat
            if result:
                result_str = str(result)
                
                # Chercher le fichier de résultat
                result_file = None
                for ext in ['.mat', '_res.mat']:
                    potential_file = self.working_dir / f"{building_id}{ext}"
                    if potential_file.exists():
                        result_file = potential_file
                        break
                
                if not result_file:
                    # Chercher avec un pattern plus large
                    mat_files = list(self.working_dir.glob(f"{building_id}*.mat"))
                    if mat_files:
                        result_file = mat_files[0]
                
                if result_file:
                    # Copier le fichier vers le dossier de sortie
                    output_file = self.output_dir / f"{building_id}_result.mat"
                    shutil.copy2(result_file, output_file)
                    return True, f"Succès en {duration:.1f}s - Fichier: {output_file.name}"
                else:
                    # Vérifier si c'est un problème de compatibilité mineur
                    if "fully compatible" in messages and "Error" not in messages:
                        return False, f"Simulation terminée mais fichier non trouvé (avertissements mineurs)"
                    else:
                        return False, f"Fichier résultat non trouvé - Messages: {messages[:200]}"
            else:
                return False, f"Échec simulation - {messages[:300] if messages else 'Pas de message'}"
            
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def run_all_simulations(self, max_simulations: int = None) -> Dict[str, bool]:
        """Lance toutes les simulations"""
        
        # Connexion
        if not self.connect_omc():
            return {}
        
        # Chargement des bibliothèques
        if not self.load_libraries():
            return {}
        
        # Récupération des modèles
        buildings = self.get_building_models()
        if not buildings:
            self.logger.error("Aucun modèle de bâtiment trouvé")
            return {}
        
        # Limiter le nombre de simulations si demandé
        if max_simulations:
            buildings = buildings[:max_simulations]
            self.logger.info(f"Limitation à {max_simulations} simulations pour test")
        
        # Simulations
        results = {}
        successful = 0
        failed = 0
        
        self.logger.info(f"🚀 Début des simulations de {len(buildings)} bâtiments")
        self.logger.info(f"Répertoire de travail: {self.working_dir}")
        self.logger.info(f"Répertoire de sortie: {self.output_dir}")
        
        for i, building in enumerate(buildings, 1):
            building_id = building.split('.')[-1]
            self.logger.info(f"\n[{i}/{len(buildings)}] {building_id}")
            
            success, message = self.simulate_building(building)
            results[building_id] = success
            
            if success:
                successful += 1
                self.logger.info(f"✅ {message}")
            else:
                failed += 1
                self.logger.error(f"❌ {message}")
            
            # Afficher un résumé intermédiaire tous les 10 bâtiments
            if i % 10 == 0:
                self.logger.info(f"--- Progression: {i}/{len(buildings)} - {successful} succès, {failed} échecs ---")
        
        # Résumé final
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"RÉSUMÉ FINAL: {successful} succès, {failed} échecs sur {len(buildings)} simulations")
        if len(buildings) > 0:
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
    OUTPUT_DIR = r"_4_Open_modula_simulation/simulation_results"
    
    # Vérifications
    if not Path(PACKAGE_PATH).exists():
        print(f"❌ Fichier package introuvable: {PACKAGE_PATH}")
        return
    
    if not Path(AIXLIB_PATH).exists():
        print(f"❌ Fichier AixLib introuvable: {AIXLIB_PATH}")
        return
    
    # Créer le simulateur
    simulator = TeaserSimulatorImproved(
        package_path=PACKAGE_PATH,
        aixlib_path=AIXLIB_PATH,
        output_dir=OUTPUT_DIR
    )
    
    try:
        print("🚀 Démarrage simulation TEASER...")
        print(f"Package: {PACKAGE_PATH}")
        print(f"AixLib: {AIXLIB_PATH}")
        print(f"Sortie: {OUTPUT_DIR}")
        
        # Pour tester, vous pouvez limiter le nombre de simulations
        # results = simulator.run_all_simulations(max_simulations=5)  # Pour tester avec 5 bâtiments
        results = simulator.run_all_simulations()  # Pour tout simuler
        
        if results:
            print("\n📊 RÉSULTATS DÉTAILLÉS:")
            for building, success in results.items():
                status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
                print(f"{building}: {status}")
            
            # Créer un fichier résumé
            summary_file = Path(OUTPUT_DIR) / "simulation_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("RÉSUMÉ DES SIMULATIONS TEASER\n")
                f.write("=" * 50 + "\n\n")
                for building, success in results.items():
                    status = "SUCCÈS" if success else "ÉCHEC"
                    f.write(f"{building}: {status}\n")
                
                successful = sum(1 for s in results.values() if s)
                total = len(results)
                f.write(f"\nTotal: {successful}/{total} succès ({successful/total*100:.1f}%)\n")
            
            print(f"\n📄 Résumé sauvegardé dans: {summary_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Simulation interrompue par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
    finally:
        simulator.cleanup()
        print("\n🏁 Fin du programme")

if __name__ == "__main__":
    main()