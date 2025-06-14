"""
OpenModelica Building Energy Simulation Script
For Dutch Building Renovation Passport Project

This script simulates energy consumption for buildings exported from TEASER
using OpenModelica and the AixLib library.

Requirements:
- OpenModelica installed
- OMPython: pip install OMPython
- Your TEASER-exported AixLib models

Author: Building Renovation Passport Project
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import json
import time
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

try:
    from OMPython import OMCSessionZMQ
    print("✓ OMPython imported successfully")
except ImportError:
    print("✗ OMPython not found. Install with: pip install OMPython")
    sys.exit(1)

class BuildingEnergySimulator:
    """
    Class to handle OpenModelica simulations for building energy analysis
    """
    
    def __init__(self, modelica_path="C:/Users/hp/TEASEROutput/Project/"):
        """
        Initialize the simulator
        
        Args:
            modelica_path: Path to the exported AixLib models
        """
        self.modelica_path = Path(modelica_path)
        self.results_path = Path("simulation/result_simu")
        self.results_path.mkdir(exist_ok=True)
        
        # Initialize OpenModelica connection
        self.omc = None
        self.simulation_results = []
        
        # Simulation parameters
        self.start_time = 0  # Start of simulation (seconds)
        self.stop_time = 31536000  # 1 year in seconds (365*24*3600)
        self.step_size = 3600  # 1 hour steps
        
        print(f"Initialized simulator for models in: {self.modelica_path}")
        print(f"Results will be saved to: {self.results_path}")
    
    def connect_openmodelica(self):
        """Connect to OpenModelica"""
        try:
            print("Connecting to OpenModelica...")
            self.omc = OMCSessionZMQ()
            version = self.omc.sendExpression("getVersion()")
            print(f"✓ Connected to OpenModelica {version}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to OpenModelica: {e}")
            print("Make sure OpenModelica is installed and accessible")
            return False
    
    def load_library(self, library_name="AixLib"):
        """Load the required Modelica library"""
        try:
            print(f"Loading {library_name} library...")
            result = self.omc.sendExpression(f'loadModel({library_name})')
            if result:
                print(f"✓ {library_name} library loaded successfully")
                return True
            else:
                print(f"✗ Failed to load {library_name} library")
                return False
        except Exception as e:
            print(f"✗ Error loading library: {e}")
            return False
    
    def discover_building_models(self):
        """Discover all building models in the exported directory"""
        models = []
        
        if not self.modelica_path.exists():
            print(f"✗ Model path does not exist: {self.modelica_path}")
            return models
        
        # Look for building model folders (TEASER creates folders for each building)
        for item in self.modelica_path.iterdir():
            if item.is_dir() and item.name.startswith("NL_Building_") and item.name != "Resources":
                model_name = item.name
                package_file = item / "package.mo"
                if package_file.exists():
                    models.append({
                        'name': model_name,
                        'folder': item,
                        'package_file': package_file,
                        'full_name': f"Project.{model_name}"  # Qualified name for OpenModelica
                    })
        
        # Also check for direct .mo files (alternative export format)
        for mo_file in self.modelica_path.glob("*.mo"):
            if mo_file.name.startswith("NL_Building_") and mo_file.name != "package.mo":
                model_name = mo_file.stem
                models.append({
                    'name': model_name,
                    'file': mo_file,
                    'full_name': f"Project.{model_name}"
                })
        
        print(f"Found {len(models)} building models")
        for model in models[:3]:  # Show first 3 as examples
            print(f"  - {model['name']}")
        if len(models) > 3:
            print(f"  - ... and {len(models) - 3} more")
        
        return models
    
    def load_building_package(self):
        """Load the building package containing all models"""
        try:
            # First, try to load the main package
            main_package_file = self.modelica_path / "package.mo"
            if main_package_file.exists():
                print("Loading main building package...")
                result = self.omc.sendExpression(f'loadFile("{main_package_file.absolute()}")')
                if result:
                    print("✓ Main building package loaded")
                    
                    # Set working directory to the models path
                    self.omc.sendExpression(f'cd("{self.modelica_path.absolute()}")')
                    return True
            
            # Alternative: load individual building packages
            print("Loading individual building model packages...")
            models = self.discover_building_models()
            loaded = 0
            
            for model in models[:5]:  # Load first 5 models as test
                try:
                    if 'package_file' in model:
                        # Load building folder package
                        result = self.omc.sendExpression(f'loadFile("{model["package_file"].absolute()}")')
                    elif 'file' in model:
                        # Load direct .mo file
                        result = self.omc.sendExpression(f'loadFile("{model["file"].absolute()}")')
                    else:
                        continue
                        
                    if result:
                        loaded += 1
                        print(f"  ✓ Loaded {model['name']}")
                    else:
                        print(f"  ✗ Failed to load {model['name']}")
                        
                except Exception as e:
                    print(f"  ✗ Error loading {model['name']}: {e}")
            
            print(f"✓ Loaded {loaded} building models")
            return loaded > 0
            
        except Exception as e:
            print(f"✗ Error loading building models: {e}")
            return False
    
    def simulate_building(self, model_name, weather_file=None):
        """
        Simulate a single building model
        
        Args:
            model_name: Name of the building model
            weather_file: Path to weather file (optional)
        
        Returns:
            Dictionary with simulation results
        """
        print(f"Simulating {model_name}...")
        
        try:
            # Set simulation parameters
            sim_options = {
                'startTime': self.start_time,
                'stopTime': self.stop_time,
                'numberOfIntervals': int(self.stop_time / self.step_size),
                'tolerance': 1e-6,
                'method': 'dassl'
            }
            
            # Add weather file if provided
            if weather_file and os.path.exists(weather_file):
                # This depends on how your TEASER models are set up
                # You might need to modify the model or set parameters
                pass
            
            # Build simulation command
            sim_command = f'''simulate({model_name}, 
                startTime={sim_options['startTime']},
                stopTime={sim_options['stopTime']},
                numberOfIntervals={sim_options['numberOfIntervals']},
                tolerance={sim_options['tolerance']},
                method="{sim_options['method']}")'''
            
            print(f"Running simulation command: {sim_command}")
            
            # Run simulation
            result = self.omc.sendExpression(sim_command)
            
            if result and 'resultFile' in str(result):
                print(f"✓ Simulation completed for {model_name}")
                
                # Extract results
                result_file = str(result).split('"')[1] if '"' in str(result) else None
                
                if result_file and os.path.exists(result_file):
                    simulation_data = self.extract_results(result_file, model_name)
                    return simulation_data
                else:
                    print(f"⚠ Result file not found for {model_name}")
                    return None
            else:
                print(f"✗ Simulation failed for {model_name}")
                print(f"Result: {result}")
                return None
                
        except Exception as e:
            print(f"✗ Error simulating {model_name}: {e}")
            return None
    
    def extract_results(self, result_file, model_name):
        """Extract key results from simulation output"""
        try:
            # Read simulation results using OpenModelica's readSimulationResult
            variables_to_extract = [
                'time',
                'thermalZone.TAir',  # Indoor air temperature
                'thermalZone.phi_heating',  # Heating power
                'thermalZone.phi_cooling',  # Cooling power
                'weaBus.TDryBul',  # Outdoor temperature
            ]
            
            results = {}
            for var in variables_to_extract:
                try:
                    data = self.omc.sendExpression(f'readSimulationResult("{result_file}", {{{var}}})')
                    if data and len(data) > 0:
                        results[var] = np.array(data[0])
                except:
                    print(f"Could not extract {var} from {model_name}")
            
            # Calculate energy consumption
            if 'time' in results and 'thermalZone.phi_heating' in results:
                time_hours = results['time'] / 3600  # Convert to hours
                heating_power = results['thermalZone.phi_heating']  # Watts
                
                # Calculate annual energy consumption (kWh)
                if len(heating_power) > 1:
                    annual_heating = np.trapz(heating_power, time_hours) / 1000  # kWh
                else:
                    annual_heating = 0
                
                results['annual_heating_kwh'] = annual_heating
            
            # Calculate cooling energy similarly
            if 'time' in results and 'thermalZone.phi_cooling' in results:
                cooling_power = results['thermalZone.phi_cooling']
                if len(cooling_power) > 1:
                    annual_cooling = np.trapz(np.abs(cooling_power), time_hours) / 1000
                else:
                    annual_cooling = 0
                results['annual_cooling_kwh'] = annual_cooling
            
            # Calculate temperature statistics
            if 'thermalZone.TAir' in results:
                indoor_temp = results['thermalZone.TAir'] - 273.15  # Convert K to °C
                results['avg_indoor_temp_c'] = np.mean(indoor_temp)
                results['min_indoor_temp_c'] = np.min(indoor_temp)
                results['max_indoor_temp_c'] = np.max(indoor_temp)
            
            print(f"✓ Extracted results for {model_name}")
            return {
                'model_name': model_name,
                'simulation_time': datetime.now().isoformat(),
                'raw_data': results,
                'summary': {
                    'annual_heating_kwh': results.get('annual_heating_kwh', 0),
                    'annual_cooling_kwh': results.get('annual_cooling_kwh', 0),
                    'total_energy_kwh': results.get('annual_heating_kwh', 0) + results.get('annual_cooling_kwh', 0),
                    'avg_indoor_temp_c': results.get('avg_indoor_temp_c', None),
                }
            }
            
        except Exception as e:
            print(f"✗ Error extracting results for {model_name}: {e}")
            return None
    
    def simulate_all_buildings(self, max_buildings=10):
        """
        Simulate multiple buildings (limited number for testing)
        
        Args:
            max_buildings: Maximum number of buildings to simulate
        """
        print(f"\n=== STARTING BATCH SIMULATION ===")
        print(f"Simulating up to {max_buildings} buildings")
        
        models = self.discover_building_models()
        if not models:
            print("No building models found!")
            return
        
        # Limit number of simulations for testing
        models_to_simulate = models[:max_buildings]
        print(f"Selected {len(models_to_simulate)} buildings for simulation")
        
        results = []
        successful = 0
        failed = 0
        
        for i, model in enumerate(models_to_simulate):
            print(f"\n--- Simulating {i+1}/{len(models_to_simulate)}: {model['name']} ---")
            
            try:
                result = self.simulate_building(model['name'])
                if result:
                    results.append(result)
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"✗ Failed to simulate {model['name']}: {e}")
                failed += 1
        
        print(f"\n=== SIMULATION SUMMARY ===")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total: {len(models_to_simulate)}")
        
        if results:
            self.save_results(results)
            self.analyze_results(results)
        
        return results
    
    def save_results(self, results):
        """Save simulation results to files"""
        try:
            # Save detailed results as JSON
            results_file = self.results_path / f"simulation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Convert numpy arrays to lists for JSON serialization
            json_results = []
            for result in results:
                json_result = result.copy()
                if 'raw_data' in json_result:
                    raw_data = {}
                    for key, value in json_result['raw_data'].items():
                        if isinstance(value, np.ndarray):
                            raw_data[key] = value.tolist()
                        else:
                            raw_data[key] = value
                    json_result['raw_data'] = raw_data
                json_results.append(json_result)
            
            with open(results_file, 'w') as f:
                json.dump(json_results, f, indent=2)
            
            print(f"✓ Detailed results saved to: {results_file}")
            
            # Save summary as CSV
            summary_data = []
            for result in results:
                summary = result.get('summary', {})
                summary['model_name'] = result['model_name']
                summary_data.append(summary)
            
            df = pd.DataFrame(summary_data)
            csv_file = self.results_path / f"simulation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(csv_file, index=False)
            
            print(f"✓ Summary saved to: {csv_file}")
            
        except Exception as e:
            print(f"✗ Error saving results: {e}")
    
    def analyze_results(self, results):
        """Analyze and visualize simulation results"""
        try:
            print(f"\n=== RESULTS ANALYSIS ===")
            
            # Extract summary data
            summaries = [r.get('summary', {}) for r in results]
            df = pd.DataFrame(summaries)
            
            if df.empty:
                print("No summary data to analyze")
                return
            
            # Basic statistics
            print(f"Buildings simulated: {len(df)}")
            
            if 'total_energy_kwh' in df.columns:
                print(f"Average annual energy consumption: {df['total_energy_kwh'].mean():.1f} kWh")
                print(f"Total energy consumption: {df['total_energy_kwh'].sum():.1f} kWh")
                print(f"Min energy consumption: {df['total_energy_kwh'].min():.1f} kWh")
                print(f"Max energy consumption: {df['total_energy_kwh'].max():.1f} kWh")
            
            if 'avg_indoor_temp_c' in df.columns:
                valid_temps = df['avg_indoor_temp_c'].dropna()
                if not valid_temps.empty:
                    print(f"Average indoor temperature: {valid_temps.mean():.1f}°C")
            
            # Create visualizations
            self.create_visualizations(df)
            
        except Exception as e:
            print(f"✗ Error analyzing results: {e}")
    
    def create_visualizations(self, df):
        """Create visualization plots"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Building Energy Simulation Results', fontsize=16)
            
            # Energy consumption histogram
            if 'total_energy_kwh' in df.columns:
                axes[0,0].hist(df['total_energy_kwh'], bins=20, edgecolor='black')
                axes[0,0].set_title('Distribution of Annual Energy Consumption')
                axes[0,0].set_xlabel('Energy Consumption (kWh)')
                axes[0,0].set_ylabel('Number of Buildings')
            
            # Heating vs Cooling
            if 'annual_heating_kwh' in df.columns and 'annual_cooling_kwh' in df.columns:
                axes[0,1].scatter(df['annual_heating_kwh'], df['annual_cooling_kwh'])
                axes[0,1].set_title('Heating vs Cooling Energy')
                axes[0,1].set_xlabel('Heating Energy (kWh)')
                axes[0,1].set_ylabel('Cooling Energy (kWh)')
            
            # Indoor temperature distribution
            if 'avg_indoor_temp_c' in df.columns:
                valid_temps = df['avg_indoor_temp_c'].dropna()
                if not valid_temps.empty:
                    axes[1,0].hist(valid_temps, bins=15, edgecolor='black')
                    axes[1,0].set_title('Average Indoor Temperature Distribution')
                    axes[1,0].set_xlabel('Temperature (°C)')
                    axes[1,0].set_ylabel('Number of Buildings')
            
            # Energy consumption ranking
            if 'total_energy_kwh' in df.columns:
                top_consumers = df.nlargest(10, 'total_energy_kwh')
                axes[1,1].barh(range(len(top_consumers)), top_consumers['total_energy_kwh'])
                axes[1,1].set_title('Top 10 Energy Consumers')
                axes[1,1].set_xlabel('Energy Consumption (kWh)')
                axes[1,1].set_ylabel('Building Rank')
            
            plt.tight_layout()
            
            # Save plot
            plot_file = self.results_path / f"analysis_plots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.show()
            
            print(f"✓ Visualizations saved to: {plot_file}")
            
        except Exception as e:
            print(f"✗ Error creating visualizations: {e}")

def main():
    """Main simulation workflow"""
    print("=== DUTCH BUILDING ENERGY SIMULATION ===")
    print("Using OpenModelica and AixLib models from TEASER")
    
    # Initialize simulator
    simulator = BuildingEnergySimulator()
    
    # Connect to OpenModelica
    if not simulator.connect_openmodelica():
        return
    
    # Load required libraries
    if not simulator.load_library("AixLib"):
        print("Trying to continue without AixLib library...")
    
    # Load building models
    if not simulator.load_building_package():
        print("Could not load building models")
        return
    
    # Run simulations (start with a small number for testing)
    print("\n=== STARTING SIMULATIONS ===")
    results = simulator.simulate_all_buildings(max_buildings=5)  # Start with 5 buildings
    
    if results:
        print(f"\n✓ Simulation completed successfully!")
        print(f"Results saved in: {simulator.results_path}")
    else:
        print("\n✗ No successful simulations")

if __name__ == "__main__":
    main()