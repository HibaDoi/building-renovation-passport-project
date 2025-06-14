#!/usr/bin/env python3
"""
Simulateur TEASER hybride - Combine parallélisation et stabilité
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import re
import shutil
import subprocess
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import json
import random

class HybridTeaserSimulator:
    """Simulateur TEASER hybride avec vraie parallélisation"""
    
    def __init__(self, package_path: str, aixlib_path: str, output_dir: str = None, 
                 num_parallel_omc: int = 4, simulation_time: float = None):
        self.package_path = Path(package_path).resolve()
        self.aixlib_path = Path(aixlib_path).resolve()
        self.output_dir = Path(output_dir) if output_dir else self.package_path.parent / "simulation_resultss"
        
        # Paramètres de simulation
        self.stop_time = simulation_time if simulation_time else 31536000  # 1 an par défaut
        self.tolerance = 1e-6
        self.solver = "dassl"
        
        # Parallélisation - limiter pour éviter les conflits OMC
        self.num_parallel_omc = min(num_parallel_omc, multiprocessing.cpu_count() // 2)
        
        self._setup_logging()
        self.package_name = self._get_package_name()
        
    def _setup_logging(self):
        """Configure le logging"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('HybridTeaserSimulator')
        self.logger.setLevel(logging.INFO)
        
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        log_file = self.output_dir / f'simulation_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _get_package_name(self) -> str:
        """Obtient le nom du package depuis le fichier"""
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
    
    def get_building_list(self) -> List[str]:
        """Obtient la liste des bâtiments via un processus séparé"""
        try:
            from OMPython import OMCSessionZMQ
            
            omc = OMCSessionZMQ()
            omc.sendExpression(f'loadFile("{self.aixlib_path.as_posix()}")')
            omc.sendExpression(f'loadFile("{self.package_path.as_posix()}")')
            
            classes = omc.sendExpression(f'getClassNames({self.package_name})')
            buildings = []
            
            if classes:
                for cls in classes:
                    class_name = str(cls).strip('"')
                    if class_name.startswith('NL_Building_'):
                        buildings.append(f"{self.package_name}.{class_name}")
            
            omc.sendExpression("quit()")
            return buildings
            
        except Exception as e:
            self.logger.error(f"Erreur obtention liste: {e}")
            return []
    
    def create_worker_script(self, worker_id: int, buildings: List[str]) -> Path:
        """Crée un script pour un worker qui simule plusieurs bâtiments"""
        
        script_path = self.output_dir / f"worker_{worker_id}.py"
        
        script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import json
from pathlib import Path
import shutil

# Configuration
WORKER_ID = {worker_id}
PACKAGE_PATH = r"{self.package_path}"
AIXLIB_PATH = r"{self.aixlib_path}"
OUTPUT_DIR = r"{self.output_dir}"
STOP_TIME = {self.stop_time}
TOLERANCE = {self.tolerance}
SOLVER = "{self.solver}"
BUILDINGS = {json.dumps(buildings)}

# Import OMPython
try:
    from OMPython import OMCSessionZMQ
except ImportError:
    print(f"Worker {{WORKER_ID}}: Erreur - OMPython non installé")
    sys.exit(1)

def simulate_worker_buildings():
    results = {{}}
    
    print(f"Worker {{WORKER_ID}}: Démarrage - {{len(BUILDINGS)}} bâtiments à simuler")
    
    try:
        # Attendre un délai aléatoire pour éviter les conflits de démarrage
        import random
        time.sleep(random.uniform(0.5, 2.0) * WORKER_ID)
        
        # Créer session OMC
        omc = OMCSessionZMQ()
        
        # Charger bibliothèques
        print(f"Worker {{WORKER_ID}}: Chargement des bibliothèques...")
        omc.sendExpression(f'loadFile("{{AIXLIB_PATH}}")')
        omc.sendExpression(f'loadFile("{{PACKAGE_PATH}}")')
        
        # Créer répertoire de travail unique pour ce worker
        work_dir = Path(OUTPUT_DIR) / f"work_worker_{{WORKER_ID}}_{{os.getpid()}}"
        work_dir.mkdir(parents=True, exist_ok=True)
        omc.sendExpression(f'cd("{{str(work_dir).replace(chr(92), "/")}}")')
        
        # Simuler chaque bâtiment assigné à ce worker
        for i, building in enumerate(BUILDINGS, 1):
            building_id = building.split('.')[-1]
            
            # Vérifier si déjà fait
            output_file = Path(OUTPUT_DIR) / f"{{building_id}}_result.mat"
            if output_file.exists():
                print(f"Worker {{WORKER_ID}}: [{{i}}/{{len(BUILDINGS)}}] {{building_id}} - Déjà complété")
                results[building_id] = {{"success": True, "time": 0, "skipped": True}}
                continue
            
            print(f"Worker {{WORKER_ID}}: [{{i}}/{{len(BUILDINGS)}}] Simulation {{building_id}}...")
            
            try:
                # Nettoyer
                omc.sendExpression("clearMessages()")
                
                # Simulation
                sim_command = f\'\'\'simulate({{building}}, 
                                        stopTime={{STOP_TIME}}, 
                                        tolerance={{TOLERANCE}}, 
                                        method="{{SOLVER}}",
                                        outputFormat="mat",
                                        fileNamePrefix="{{building_id}}")\'\'\'
                
                start = time.time()
                result = omc.sendExpression(sim_command)
                duration = time.time() - start
                
                # Chercher fichier résultat
                result_file = None
                for ext in ['.mat', '_res.mat']:
                    potential_file = work_dir / f"{{building_id}}{{ext}}"
                    if potential_file.exists():
                        result_file = potential_file
                        break
                
                if not result_file:
                    mat_files = list(work_dir.glob(f"{{building_id}}*.mat"))
                    if mat_files:
                        result_file = mat_files[0]
                
                # Copier résultat
                if result_file:
                    shutil.copy2(result_file, output_file)
                    results[building_id] = {{"success": True, "time": duration}}
                    print(f"Worker {{WORKER_ID}}: [OK] {{building_id}} en {{duration:.1f}}s")
                else:
                    messages = omc.sendExpression("getErrorString()")
                    results[building_id] = {{"success": False, "error": messages[:200]}}
                    print(f"Worker {{WORKER_ID}}: [FAIL] {{building_id}}")
                    
            except Exception as e:
                results[building_id] = {{"success": False, "error": str(e)}}
                print(f"Worker {{WORKER_ID}}: [ERROR] {{building_id}} - {{str(e)}}")
        
        # Nettoyer
        print(f"Worker {{WORKER_ID}}: Nettoyage...")
        omc.sendExpression("quit()")
        shutil.rmtree(work_dir, ignore_errors=True)
        
    except Exception as e:
        print(f"Worker {{WORKER_ID}}: Erreur globale - {{e}}")
    
    # Sauvegarder résultats
    results_file = Path(OUTPUT_DIR) / f"worker_{{WORKER_ID}}_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Worker {{WORKER_ID}}: Terminé - {{len(results)}} bâtiments traités")
    return results

if __name__ == "__main__":
    simulate_worker_buildings()
'''
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_path
    
    def run_hybrid_simulation(self, max_buildings: int = None) -> Dict[str, bool]:
        """Lance la simulation hybride avec vrais processus parallèles"""
        
        # Obtenir la liste des bâtiments
        self.logger.info("Obtention de la liste des bâtiments...")
        all_buildings = self.get_building_list()
        if not all_buildings:
            self.logger.error("Aucun bâtiment trouvé")
            return {}
        
        # Limiter si demandé
        if max_buildings:
            all_buildings = all_buildings[:max_buildings]
        
        # Filtrer les déjà complétés
        completed = set()
        for mat_file in self.output_dir.glob("*_result.mat"):
            building_id = mat_file.stem.replace("_result", "")
            completed.add(building_id)
        
        if completed:
            self.logger.info(f"{len(completed)} simulations déjà complétées")
            all_buildings = [b for b in all_buildings if b.split('.')[-1] not in completed]
        
        if not all_buildings:
            self.logger.info("Toutes les simulations sont déjà complétées!")
            return {}
        
        total_buildings = len(all_buildings)
        
        # Diviser le travail entre les workers
        buildings_per_worker = total_buildings // self.num_parallel_omc
        remainder = total_buildings % self.num_parallel_omc
        
        worker_assignments = []
        start_idx = 0
        
        for i in range(self.num_parallel_omc):
            count = buildings_per_worker + (1 if i < remainder else 0)
            if count > 0:
                worker_buildings = all_buildings[start_idx:start_idx + count]
                worker_assignments.append((i, worker_buildings))
                start_idx += count
        
        # Estimation du temps
        time_per_building = 85 if self.stop_time >= 31536000 else self.stop_time / 365000 * 85
        estimated_time = (total_buildings * time_per_building) / len(worker_assignments)
        
        self.logger.info(f"🚀 Simulation de {total_buildings} bâtiments avec {len(worker_assignments)} workers parallèles")
        self.logger.info(f"📊 Période simulée: {self.stop_time}s ({self.stop_time/86400:.1f} jours)")
        self.logger.info(f"⏱️  Temps estimé: {timedelta(seconds=int(estimated_time))}")
        self.logger.info(f"🔧 Répartition: ~{buildings_per_worker} bâtiments par worker")
        
        start_time = time.time()
        all_results = {}
        
        # Créer les scripts pour chaque worker
        self.logger.info("\nCréation des scripts workers...")
        worker_scripts = []
        for worker_id, buildings in worker_assignments:
            script_path = self.create_worker_script(worker_id, buildings)
            worker_scripts.append((worker_id, script_path, len(buildings)))
            self.logger.info(f"  Worker {worker_id}: {len(buildings)} bâtiments")
        
        # Lancer tous les workers en parallèle
        self.logger.info("\nLancement des workers...")
        processes = []
        
        for worker_id, script_path, num_buildings in worker_scripts:
            self.logger.info(f"  Démarrage worker {worker_id}...")
            
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            processes.append((worker_id, process, script_path))
        
        # Surveiller les processus
        self.logger.info("\nSimulations en cours...")
        self.logger.info("(Consultez les logs pour plus de détails)")
        
        completed_workers = 0
        while processes:
            time.sleep(10)  # Vérifier toutes les 10 secondes
            
            remaining_processes = []
            for worker_id, process, script_path in processes:
                if process.poll() is not None:
                    # Worker terminé
                    completed_workers += 1
                    self.logger.info(f"\n✓ Worker {worker_id} terminé (code: {process.returncode})")
                    
                    # Lire les résultats
                    results_file = self.output_dir / f"worker_{worker_id}_results.json"
                    if results_file.exists():
                        with open(results_file, 'r') as f:
                            worker_results = json.load(f)
                        
                        # Mettre à jour les résultats globaux
                        for building_id, result in worker_results.items():
                            all_results[building_id] = result['success']
                        
                        # Nettoyer
                        results_file.unlink()
                    
                    # Nettoyer le script
                    if script_path.exists():
                        script_path.unlink()
                else:
                    remaining_processes.append((worker_id, process, script_path))
            
            processes = remaining_processes
            
            if processes:
                elapsed = time.time() - start_time
                self.logger.info(f"  {len(processes)} workers actifs - Temps écoulé: {timedelta(seconds=int(elapsed))}")
        
        # Résumé final
        elapsed_time = time.time() - start_time
        successful = sum(1 for s in all_results.values() if s)
        failed = len(all_results) - successful
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"RÉSUMÉ FINAL: {successful} succès, {failed} échecs")
        self.logger.info(f"Temps total: {timedelta(seconds=int(elapsed_time))}")
        self.logger.info(f"Accélération: {estimated_time/elapsed_time:.1f}x par rapport au séquentiel")
        if len(all_results) > 0:
            self.logger.info(f"Temps moyen par bâtiment: {elapsed_time/len(all_results):.1f}s")
            self.logger.info(f"Taux de succès: {successful/len(all_results)*100:.1f}%")
        
        return all_results


def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulation TEASER hybride parallèle')
    parser.add_argument('--workers', type=int, default=4,
                       help='Nombre de workers parallèles (défaut: 4)')
    parser.add_argument('--time', type=float,
                       help='Durée de simulation en secondes (défaut: 31536000 = 1 an)')
    parser.add_argument('--max', type=int,
                       help='Nombre maximum de bâtiments à simuler (pour tests)')
    parser.add_argument('--output', type=str,
                       help='Répertoire de sortie personnalisé')
    
    args = parser.parse_args()
    
    # Configuration
    PACKAGE_PATH = r"C:/Users/hp/TEASEROutput/Project/package.mo"
    AIXLIB_PATH = r"C:/AixLib-main/AixLib-main/AixLib/package.mo"
    OUTPUT_DIR = args.output if args.output else r"Open_modula_maybe/simulation_resultss"
    
    # Vérifications
    if not Path(PACKAGE_PATH).exists():
        print(f"❌ Fichier package introuvable: {PACKAGE_PATH}")
        return
    
    if not Path(AIXLIB_PATH).exists():
        print(f"❌ Fichier AixLib introuvable: {AIXLIB_PATH}")
        return
    
    # Créer le simulateur
    simulator = HybridTeaserSimulator(
        package_path=PACKAGE_PATH,
        aixlib_path=AIXLIB_PATH,
        output_dir=OUTPUT_DIR,
        num_parallel_omc=args.workers,
        simulation_time=args.time
    )
    
    try:
        print("🚀 Démarrage simulation TEASER hybride parallèle...")
        print(f"Package: {PACKAGE_PATH}")
        print(f"AixLib: {AIXLIB_PATH}")
        print(f"Sortie: {OUTPUT_DIR}")
        print(f"Workers: {simulator.num_parallel_omc}")
        
        results = simulator.run_hybrid_simulation(max_buildings=args.max)
        
        if results:
            # Créer fichier résumé
            summary_file = Path(OUTPUT_DIR) / f"simulation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("RÉSUMÉ DES SIMULATIONS TEASER\n")
                f.write("=" * 50 + "\n\n")
                
                successful = []
                failed = []
                
                for building, success in sorted(results.items()):
                    if success:
                        successful.append(building)
                    else:
                        failed.append(building)
                
                f.write(f"SUCCÈS ({len(successful)}):\n")
                for building in successful:
                    f.write(f"  [OK] {building}\n")
                
                if failed:
                    f.write(f"\nÉCHECS ({len(failed)}):\n")
                    for building in failed:
                        f.write(f"  [FAIL] {building}\n")
                
                f.write(f"\nTotal: {len(successful)}/{len(results)} succès ")
                f.write(f"({len(successful)/len(results)*100:.1f}%)\n")
            
            print(f"\n📄 Résumé sauvegardé dans: {summary_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Simulation interrompue")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🏁 Fin du programme")


if __name__ == "__main__":
    main()