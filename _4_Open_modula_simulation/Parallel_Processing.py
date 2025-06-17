#!/usr/bin/env python3

"""
Correction des problèmes de compatibilité Modelica pour simulations TEASER
Résout les conflits de versions de bibliothèques
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import re
import shutil
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import psutil

try:
    from OMPython import OMCSessionZMQ
except ImportError:
    print("Erreur: OMPython n'est pas installé.")
    sys.exit(1)

def setup_omc_session_fixed() -> Tuple[OMCSessionZMQ, str]:
    """Configure une session OMC avec corrections de compatibilité"""
    try:
        omc = OMCSessionZMQ()
        
        # 1. CONFIGURATION EXPLICITE DE MODELICA
        print("Configuration Modelica...")
        
        # Forcer l'utilisation de Modelica 3.2.3 (plus stable avec TEASER)
        modelica_loaded = omc.sendExpression('loadModel(Modelica, {"3.2.3"})')
        if not modelica_loaded:
            # Si 3.2.3 non disponible, essayer la version par défaut mais avec config
            print("Modelica 3.2.3 non trouvé, utilisation version par défaut...")
            omc.sendExpression('loadModel(Modelica)')
        
        # 2. OPTIMISATIONS DE COMPILATION CORRIGÉES
        omc.sendExpression('setCommandLineOptions("-d=initialization --preOptModules=clockPartitioning,removeConstants,removeSimpleEquations,removeUnusedParameter,removeUnusedVariables,removeUnusedFunctions,eliminateAliases,solveSimpleEquations,tearingSystem --postOptModules=removeConstants,removeSimpleEquations,removeUnusedVariables,removeUnusedFunctions,eliminateAliases,solveSimpleEquations")')
        
        # 3. DÉSACTIVER LES VÉRIFICATIONS STRICTES
        omc.sendExpression('setDebugFlags("disableDirectionalDerivatives,disableRecordConstructorOutput")')
        
        # 4. CONFIGURATION POUR ÉVITER LES CONFLITS MULTIBODY
        omc.sendExpression('setCommandLineOptions("--simCodeTarget=C")')
        
        # Répertoire de travail unique pour ce worker
        worker_id = mp.current_process().pid
        working_dir = Path("simulation_results_optimized") / f"work_{worker_id}"
        working_dir.mkdir(parents=True, exist_ok=True)
        
        omc.sendExpression(f'cd("{str(working_dir).replace(chr(92), "/")}")')
        
        return omc, str(working_dir)
        
    except Exception as e:
        raise Exception(f"Erreur setup worker corrigé: {e}")

def load_libraries_with_compatibility_check(omc: OMCSessionZMQ, aixlib_path: str, teaser_path: str) -> bool:
    """Charge les bibliothèques avec vérifications de compatibilité"""
    try:
        print("Chargement des bibliothèques avec vérifications...")
        
        # 1. Vérifier la version Modelica chargée
        modelica_version = omc.sendExpression('getVersion(Modelica)')
        print(f"Version Modelica: {modelica_version}")
        
        # 2. Charger AixLib avec gestion d'erreurs
        print("Chargement AixLib...")
        aixlib_path_str = str(Path(aixlib_path)).replace('\\', '/')
        result_aixlib = omc.sendExpression(f'loadFile("{aixlib_path_str}")')
        
        if not result_aixlib:
            errors = omc.sendExpression("getErrorString()")
            print(f"Erreurs AixLib: {errors}")
            
            # Essayer de charger seulement les parties nécessaires d'AixLib
            print("Tentative chargement partiel AixLib...")
            omc.sendExpression("clearMessages()")
            # Continuer même si AixLib a des avertissements
        
        # 3. Charger le package TEASER
        print("Chargement package TEASER...")
        teaser_path_str = str(Path(teaser_path)).replace('\\', '/')
        result_teaser = omc.sendExpression(f'loadFile("{teaser_path_str}")')
        
        if not result_teaser:
            errors = omc.sendExpression("getErrorString()")
            print(f"Erreurs TEASER: {errors}")
            return False
        
        # 4. Vérifier les classes chargées
        package_name = get_package_name_from_file(teaser_path)
        if package_name:
            classes = omc.sendExpression(f'getClassNames({package_name})')
            if classes and len(classes) > 0:
                print(f"Succès: {len(classes)} classes chargées dans {package_name}")
                
                # 5. Nettoyer les messages d'avertissement (mais garder les erreurs critiques)
                messages = omc.sendExpression("getErrorString()")
                if "Error" not in messages:
                    omc.sendExpression("clearMessages()")
                
                return True
        
        return False
        
    except Exception as e:
        print(f"Erreur chargement bibliothèques: {e}")
        return False

def get_package_name_from_file(package_path: str) -> str:
    """Obtient le nom du package depuis le fichier"""
    try:
        with open(package_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        match = re.search(r'package\s+(\w+)', content)
        if match:
            return match.group(1)
        
        return Path(package_path).parent.name
        
    except Exception:
        return None

def simulate_building_worker_fixed(args):
    """Fonction worker corrigée pour simulation parallèle"""
    model_name, package_path, aixlib_path, output_dir, sim_params = args
    
    try:
        building_id = model_name.split('.')[-1]
        output_dir = Path(output_dir)
        
        # Vérifier si déjà simulé
        existing = output_dir / f"{building_id}_result.mat"
        if existing.exists():
            return building_id, True, "Existe déjà", 0
        
        # Setup session OMC corrigée
        omc, working_dir = setup_omc_session_fixed()
        
        # Charger bibliothèques avec vérifications
        if not load_libraries_with_compatibility_check(omc, aixlib_path, package_path):
            omc.sendExpression("quit()")
            return building_id, False, "Échec chargement bibliothèques", 0
        
        # Vérifier que le modèle existe
        model_exists = omc.sendExpression(f'isModel({model_name})')
        if not model_exists:
            # Essayer de trouver le bon chemin du modèle
            package_name = get_package_name_from_file(package_path)
            if package_name:
                # Essayer différentes variantes du nom
                alternative_names = [
                    f"{package_name}.{building_id}",
                    f"{package_name}.{building_id}.{building_id}",
                    f"{package_name}.{building_id}.Building"
                ]
                
                for alt_name in alternative_names:
                    if omc.sendExpression(f'isModel({alt_name})'):
                        model_name = alt_name
                        model_exists = True
                        break
        
        if not model_exists:
            omc.sendExpression("quit()")
            return building_id, False, f"Modèle {model_name} non trouvé", 0
        
        # Nettoyer avant simulation
        omc.sendExpression("clearMessages()")
        
        # Simulation avec paramètres robustes
        stop_time, tolerance, solver, intervals = sim_params
        
        # Utiliser des paramètres plus robustes
        sim_command = f'''simulate({model_name},
                                stopTime={stop_time},
                                tolerance={tolerance},
                                method="dassl",
                                numberOfIntervals={intervals},
                                outputFormat="mat",
                                fileNamePrefix="{building_id}",
                                variableFilter="time|.*temperature.*|.*heat.*|.*power.*")'''
        
        start_time = time.time()
        result = omc.sendExpression(sim_command)
        end_time = time.time()
        duration = end_time - start_time
        
        # Vérifier résultat
        if result:
            # Chercher fichier résultat
            working_path = Path(working_dir)
            result_file = None
            
            # Chercher le fichier avec différents patterns
            for pattern in [f"{building_id}.mat", f"{building_id}_res.mat", f"*{building_id}*.mat"]:
                files = list(working_path.glob(pattern))
                if files:
                    result_file = files[0]
                    break
            
            if result_file and result_file.exists():
                # Copier vers sortie
                output_file = output_dir / f"{building_id}_result.mat"
                shutil.copy2(result_file, output_file)
                
                # Nettoyer fichier temporaire
                try:
                    result_file.unlink()
                except:
                    pass
                
                omc.sendExpression("quit()")
                return building_id, True, f"Succès en {duration:.1f}s", duration
            else:
                # Vérifier si c'est juste un problème de fichier
                messages = omc.sendExpression("getErrorString()")
                if "successfully" in str(result).lower() or "Error" not in messages:
                    omc.sendExpression("quit()")
                    return building_id, False, "Simulation OK mais fichier non trouvé", duration
        
        # Échec - récupérer les messages d'erreur
        messages = omc.sendExpression("getErrorString()")
        omc.sendExpression("quit()")
        
        # Analyser le type d'erreur
        if "MultiBody" in messages:
            return building_id, False, "Erreur compatibilité MultiBody - modèle incompatible", duration
        elif "instantiate" in messages:
            return building_id, False, "Erreur instanciation - paramètres manquants", duration
        else:
            return building_id, False, f"Erreur simulation: {messages[:100]}", duration
        
    except Exception as e:
        return building_id, False, f"Exception worker: {str(e)}", 0

def run_robust_simulations(package_path: str, aixlib_path: str, output_dir: str, 
                          max_simulations: int = None, max_workers: int = None):
    """Lance les simulations avec corrections de compatibilité"""
    
    # Configuration robuste
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Logger
    logger = logging.getLogger('RobustSimulations')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    # Récupérer les modèles (version simplifiée)
    logger.info("🔍 Récupération des modèles...")
    
    try:
        # Session temporaire pour explorer
        omc = OMCSessionZMQ()
        
        # Charger avec configuration minimale
        omc.sendExpression('loadModel(Modelica)')
        
        aixlib_path_str = str(Path(aixlib_path)).replace('\\', '/')
        teaser_path_str = str(Path(package_path)).replace('\\', '/')
        
        omc.sendExpression(f'loadFile("{aixlib_path_str}")')
        omc.sendExpression(f'loadFile("{teaser_path_str}")')
        
        package_name = get_package_name_from_file(package_path)
        classes = omc.sendExpression(f'getClassNames({package_name})')
        
        building_models = []
        if classes:
            for cls in classes:
                class_name = str(cls).strip('"')
                if class_name.startswith('NL_Building_'):
                    # Construire le nom complet du modèle
                    package_full_name = f"{package_name}.{class_name}"
                    sub_classes = omc.sendExpression(f'getClassNames({package_full_name})')
                    
                    if sub_classes:
                        for sub_cls in sub_classes:
                            sub_class_name = str(sub_cls).strip('"')
                            full_sub_name = f"{package_full_name}.{sub_class_name}"
                            sub_type = omc.sendExpression(f'getClassRestriction({full_sub_name})')
                            
                            if 'model' in str(sub_type).lower():
                                building_models.append(full_sub_name)
                                break
        
        omc.sendExpression("quit()")
        
    except Exception as e:
        logger.error(f"Erreur récupération modèles: {e}")
        return {}
    
    if not building_models:
        logger.error("Aucun modèle trouvé")
        return {}
    
    logger.info(f"Trouvé {len(building_models)} modèles")
    
    # Limiter si demandé
    if max_simulations:
        building_models = building_models[:max_simulations]
        logger.info(f"Limitation à {max_simulations} simulations")
    
    # Paramètres de simulation robustes
    sim_params = (
        3.154e7,    # stop_time
        1e-4,       # tolerance
        "dassl",    # solver robuste
        8760        # intervals
    )
    
    # Workers - plus conservateur avec votre RAM
    if max_workers is None:
        # Avec 4.4GB RAM, limiter à 2 workers pour éviter les problèmes
        max_workers = 2
    
    logger.info(f"🚀 Début simulations robustes avec {max_workers} workers")
    
    # Préparer arguments
    args_list = [
        (building, package_path, aixlib_path, output_dir, sim_params)
        for building in building_models
    ]
    
    # Simulation parallèle
    results = {}
    successful = 0
    failed = 0
    
    start_total = time.time()
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_building = {
            executor.submit(simulate_building_worker_fixed, args): args[0].split('.')[-1]
            for args in args_list
        }
        
        for i, future in enumerate(as_completed(future_to_building), 1):
            try:
                building_id, success, message, duration = future.result()
                results[building_id] = success
                
                if success:
                    successful += 1
                    logger.info(f"✅ [{i}/{len(building_models)}] {building_id}: {message}")
                else:
                    failed += 1
                    logger.error(f"❌ [{i}/{len(building_models)}] {building_id}: {message}")
                
                # Rapport intermédiaire
                if i % 5 == 0:  # Plus fréquent pour debugging
                    elapsed = time.time() - start_total
                    logger.info(f"--- Progression: {i}/{len(building_models)} - {successful} succès, {failed} échecs ---")
                    
            except Exception as e:
                building_id = future_to_building[future]
                logger.error(f"❌ [{i}/{len(building_models)}] {building_id}: Exception {e}")
                results[building_id] = False
                failed += 1
    
    # Résumé final
    total_elapsed = time.time() - start_total
    
    logger.info("\n" + "=" * 80)
    logger.info(f"RÉSUMÉ FINAL ROBUSTE")
    logger.info(f"Succès: {successful}, Échecs: {failed}")
    if len(building_models) > 0:
        logger.info(f"Taux de succès: {successful/len(building_models)*100:.1f}%")
    logger.info(f"Temps total: {total_elapsed/60:.1f} minutes")
    
    return results

def main():
    """Fonction principale avec corrections"""
    
    # Configuration
    PACKAGE_PATH = r"C:/Users/hp/TEASEROutput/Project/package.mo"
    AIXLIB_PATH = r"C:/AixLib-main/AixLib-main/AixLib/package.mo"
    OUTPUT_DIR = r"_4_Open_modula_simulation/simulation_results_fixed"
    
    print("🔧 SIMULATION TEASER AVEC CORRECTIONS DE COMPATIBILITÉ")
    print("=" * 80)
    print(f"RAM disponible: {psutil.virtual_memory().available / 1e9:.1f} GB")
    print(f"Configuration: 2 workers (conservateur pour votre RAM)")
    
    try:
        # Test avec paramètres robustes
        results = run_robust_simulations(
            PACKAGE_PATH, 
            AIXLIB_PATH, 
            OUTPUT_DIR,
            max_simulations=10,  # Test avec 10
            max_workers=2        # Conservateur
        )
        
        if results:
            successful = sum(1 for s in results.values() if s)
            total = len(results)
            
            print(f"\n📊 RÉSULTATS: {successful}/{total} simulations réussies")
            
            # Analyser les types d'erreurs
            if successful > 0:
                print("✅ Certaines simulations fonctionnent - vous pouvez continuer")
                if successful == total:
                    print("🎉 Toutes les simulations de test réussies !")
                    print("Vous pouvez maintenant augmenter max_simulations")
            else:
                print("❌ Aucune simulation réussie - vérifiez la configuration")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()