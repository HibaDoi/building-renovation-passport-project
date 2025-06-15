from simulation.simulation_script import BuildingEnergySimulator

# Initialize
simulator = BuildingEnergySimulator()
simulator.connect_openmodelica()
simulator.load_library("AixLib")
simulator.load_building_package()

# Simulate specific number of buildings
results = simulator.simulate_all_buildings(max_buildings=10)