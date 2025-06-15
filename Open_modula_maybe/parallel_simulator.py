#!/usr/bin/env python3
"""
Flexible Parallel TEASER Simulator that can handle different package structures
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import re
import shutil
from multiprocessing import Pool, cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed
import json

try:
    from OMPython import OMCSessionZMQ
except ImportError:
    print("Error: OMPython is not installed.")
    sys.exit(1)

class FlexibleParallelSimulator:
    """Flexible parallel simulator that discovers models dynamically"""
    
    def __init__(self, package_path: str, aixlib_path: str, output_dir: str = None, 
                 n_workers: int = None):
        self.package_path = Path(package_path).resolve()
        self.aixlib_path = Path(aixlib_path).resolve()
        self.output_dir = Path(output_dir) if output_dir else self.package_path.parent / "simulation_results"
        self.n_workers = n_workers or min(cpu_count() - 1, 8)
        
        # Simulation parameters
        self.stop_time = 3.154e7  # 1 year
        self.tolerance = 1e-6
        self.solver = "dassl"
        
        self._setup_logging()
        self.building_models = []
        self.package_name = None
        
    def _setup_logging(self):
        """Configure logging"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logs_dir = self.output_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(logs_dir / 'parallel_simulation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('FlexibleSimulator')
    
    def discover_models_with_omc(self) -> List[str]:
        """Use OpenModelica to discover building models"""
        omc = None
        try:
            self.logger.info("🔍 Discovering models using OpenModelica...")
            omc = OMCSessionZMQ()
            
            # Load package
            package_str = str(self.package_path).replace('\\', '/')
            result = omc.sendExpression(f'loadFile("{package_str}")')
            if not result:
                self.logger.error("Failed to load package")
                return []
            
            # Get all loaded classes
            all_classes = omc.sendExpression('getClassNames()')
            if not all_classes:
                self.logger.error("No classes found")
                return []
            
            # Find package name
            self.package_name = str(all_classes[0]).split('.')[0] if all_classes else None
            self.logger.info(f"Package name: {self.package_name}")
            
            # Find building models
            building_models = []
            
            # Method 1: Look for NL_Building patterns
            for cls in all_classes:
                class_str = str(cls)
                if 'NL_Building' in class_str:
                    # Check if it's a model or package
                    restriction = omc.sendExpression(f'getClassRestriction({class_str})')
                    self.logger.debug(f"Class {class_str} has restriction: {restriction}")
                    
                    if 'model' in str(restriction).lower():
                        building_models.append(class_str)
                    elif 'package' in str(restriction).lower():
                        # Look inside the package for models
                        sub_classes = omc.sendExpression(f'getClassNames({class_str})')
                        if sub_classes:
                            for sub_cls in sub_classes:
                                sub_restriction = omc.sendExpression(f'getClassRestriction({sub_cls})')
                                if 'model' in str(sub_restriction).lower():
                                    building_models.append(str(sub_cls))
                                    break  # Take first model in package
            
            # Method 2: If no models found, try common patterns
            if not building_models and self.package_name:
                self.logger.info("Trying alternative patterns...")
                
                # Get direct children of main package
                direct_children = omc.sendExpression(f'getClassNames({self.package_name}, recursive=false)')
                if direct_children:
                    for child in direct_children:
                        child_str = str(child)
                        if 'NL_Building' in child_str:
                            # Try common model names
                            for model_suffix in ['', '.Building', '.building', '.BuildingModel']:
                                test_model = f"{self.package_name}.{child_str}{model_suffix}"
                                if omc.sendExpression(f'isModel({test_model})'):
                                    building_models.append(test_model)
                                    break
            
            self.logger.info(f"Found {len(building_models)} building models")
            return building_models
            
        except Exception as e:
            self.logger.error(f"Error discovering models: {e}")
            return []
        finally:
            if omc:
                try:
                    omc.sendExpression("quit()")
                except:
                    pass
    
    def load_models_from_file(self, models_file: str) -> List[str]:
        """Load building models from a text file"""
        try:
            with open(models_file, 'r') as f:
                models = [line.strip() for line in f if line.strip()]
            self.logger.info(f"Loaded {len(models)} models from {models_file}")
            return models
        except Exception as e:
            self.logger.error(f"Error loading models from file: {e}")
            return []
    
    def simulate_single_building(self, args: Tuple[str, int, int]) -> Dict:
        """Simulate a single building (worker process)"""
        model_name, worker_id, total_models = args
        building_id = model_name.split('.')[-1]
        
        # Check if already exists
        result_file = self.output_dir / f"{building_id}_result.mat"
        if result_file.exists():
            return {
                'building_id': building_id,
                'model_name': model_name,
                'success': True,
                'message': 'Already exists',
                'duration': 0,
                'worker_id': worker_id
            }
        
        start_time = time.time()
        omc = None
        
        try:
            # Setup worker directory
            worker_dir = self.output_dir / f"worker_{worker_id}"
            worker_dir.mkdir(exist_ok=True)
            
            # Initialize OMC
            omc = OMCSessionZMQ()
            omc.sendExpression(f'cd("{str(worker_dir).replace(chr(92), "/")}")')
            
            # Optimization flags
            omc.sendExpression('setCommandLineOptions("-d=-newInst,-showErrorMessages")')
            
            # Load libraries
            aixlib_str = str(self.aixlib_path).replace('\\', '/')
            package_str = str(self.package_path).replace('\\', '/')
            
            if not omc.sendExpression(f'loadFile("{aixlib_str}")'):
                raise Exception("Failed to load AixLib")
            
            if not omc.sendExpression(f'loadFile("{package_str}")'):
                raise Exception("Failed to load package")
            
            # Clear messages
            omc.sendExpression("clearMessages()")
            
            # Optimized simulation command
            sim_command = f'''simulate({model_name}, 
                                    stopTime={self.stop_time}, 
                                    numberOfIntervals=8760,
                                    tolerance={self.tolerance}, 
                                    method="{self.solver}",
                                    outputFormat="mat",
                                    fileNamePrefix="{building_id}",
                                    simflags="-emit_protected -lv=-LOG_STATS",
                                    cflags="-O3 -march=native")'''
            
            # Run simulation
            result = omc.sendExpression(sim_command)
            
            if result:
                # Find and move result file
                for ext in ['.mat', '_res.mat']:
                    potential_file = worker_dir / f"{building_id}{ext}"
                    if potential_file.exists():
                        shutil.move(str(potential_file), str(result_file))
                        duration = time.time() - start_time
                        return {
                            'building_id': building_id,
                            'model_name': model_name,
                            'success': True,
                            'message': f'Success in {duration:.1f}s',
                            'duration': duration,
                            'worker_id': worker_id
                        }
                
                return {
                    'building_id': building_id,
                    'model_name': model_name,
                    'success': False,
                    'message': 'Result file not found',
                    'duration': time.time() - start_time,
                    'worker_id': worker_id
                }
            else:
                error_msg = omc.sendExpression("getErrorString()")
                return {
                    'building_id': building_id,
                    'model_name': model_name,
                    'success': False,
                    'message': f'Simulation failed: {error_msg[:100]}',
                    'duration': time.time() - start_time,
                    'worker_id': worker_id
                }
                
        except Exception as e:
            return {
                'building_id': building_id,
                'model_name': model_name,
                'success': False,
                'message': f'Exception: {str(e)}',
                'duration': time.time() - start_time,
                'worker_id': worker_id
            }
        finally:
            if omc:
                try:
                    omc.sendExpression("quit()")
                except:
                    pass
    
    def run_parallel_simulations(self, models: List[str] = None, max_simulations: int = None):
        """Run simulations in parallel"""
        
        # Get models if not provided
        if not models:
            # Try to load from file first
            if (self.output_dir / "building_models.txt").exists():
                models = self.load_models_from_file(self.output_dir / "building_models.txt")
            
            # If no file, discover with OMC
            if not models:
                models = self.discover_models_with_omc()
        
        if not models:
            self.logger.error("No models to simulate")
            return {}
        
        # Save discovered models
        with open(self.output_dir / "discovered_models.txt", 'w') as f:
            for model in models:
                f.write(f"{model}\n")
        
        # Limit if requested
        if max_simulations:
            models = models[:max_simulations]
        
        self.logger.info(f"Starting parallel simulation of {len(models)} buildings")
        self.logger.info(f"Using {self.n_workers} worker processes")
        
        # Prepare worker arguments
        worker_args = [
            (model, i % self.n_workers, len(models)) 
            for i, model in enumerate(models)
        ]
        
        # Results
        results = {}
        successful = 0
        failed = 0
        completed = 0
        
        start_time = time.time()
        
        # Progress update function
        def update_progress():
            elapsed = time.time() - start_time
            rate = completed / elapsed if elapsed > 0 else 0
            eta = (len(models) - completed) / rate if rate > 0 else 0
            
            self.logger.info(
                f"Progress: {completed}/{len(models)} "
                f"({successful} success, {failed} failed) "
                f"Rate: {rate:.1f} buildings/s, ETA: {eta/60:.1f} minutes"
            )
        
        # Run in parallel
        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            future_to_model = {
                executor.submit(self.simulate_single_building, args): args[0] 
                for args in worker_args
            }
            
            for future in as_completed(future_to_model):
                try:
                    result = future.result(timeout=300)  # 5 min timeout
                    building_id = result['building_id']
                    results[building_id] = result
                    
                    if result['success']:
                        successful += 1
                    else:
                        failed += 1
                    
                    completed += 1
                    
                    if completed % 10 == 0:
                        update_progress()
                        
                except Exception as e:
                    model_name = future_to_model[future]
                    building_id = model_name.split('.')[-1]
                    results[building_id] = {
                        'building_id': building_id,
                        'model_name': model_name,
                        'success': False,
                        'message': f'Worker error: {str(e)}',
                        'duration': 0,
                        'worker_id': -1
                    }
                    failed += 1
                    completed += 1
        
        # Summary
        total_time = time.time() - start_time
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"SIMULATION COMPLETE")
        self.logger.info(f"Total: {len(models)} buildings")
        self.logger.info(f"Successful: {successful}")
        self.logger.info(f"Failed: {failed}")
        self.logger.info(f"Total time: {total_time/60:.1f} minutes")
        self.logger.info(f"Average rate: {len(models)/total_time:.2f} buildings/second")
        
        # Save results
        self._save_results(results)
        
        return results
    
    def _save_results(self, results: Dict):
        """Save results to files"""
        # CSV summary
        csv_file = self.output_dir / "simulation_results.csv"
        with open(csv_file, 'w') as f:
            f.write("Building_ID,Model_Name,Success,Duration_s,Message,Worker_ID\n")
            for building_id, result in results.items():
                success = "TRUE" if result['success'] else "FALSE"
                duration = f"{result['duration']:.2f}"
                message = result['message'].replace(',', ';')
                worker_id = result['worker_id']
                model_name = result['model_name']
                f.write(f"{building_id},{model_name},{success},{duration},{message},{worker_id}\n")
        
        # JSON detailed results
        json_file = self.output_dir / "simulation_results.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Results saved to: {csv_file} and {json_file}")


def main():
    """Main function"""
    
    # Configuration
    PACKAGE_PATH = r"C:/Users/hp/TEASEROutput/Project/package.mo"
    AIXLIB_PATH = r"C:/AixLib-main/AixLib-main/AixLib/package.mo"
    OUTPUT_DIR = r"Open_modula_maybe/simulation_results"
    
    # Check if models file exists
    models_file = Path("building_models.txt")
    
    print(f"🚀 Flexible Parallel TEASER Simulator")
    print(f"Package: {PACKAGE_PATH}")
    print(f"AixLib: {AIXLIB_PATH}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Workers: {cpu_count() - 1}")
    
    simulator = FlexibleParallelSimulator(
        package_path=PACKAGE_PATH,
        aixlib_path=AIXLIB_PATH,
        output_dir=OUTPUT_DIR
    )
    
    try:
        # If models file exists, use it
        if models_file.exists():
            print(f"\n📄 Loading models from {models_file}")
            models = simulator.load_models_from_file(models_file)
            results = simulator.run_parallel_simulations(models=models)
        else:
            print(f"\n🔍 Discovering models automatically...")
            results = simulator.run_parallel_simulations()
        
    except KeyboardInterrupt:
        print("\n⏹️ Simulation interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()