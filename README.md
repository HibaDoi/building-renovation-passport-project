#Step 1: Extracting Information from Delft City CityJSON for Simulation
The first step in the simulation process is to extract relevant building data from the CityJSON file of Delft City. The key attributes to be extracted include information about the building's structure, roof, and volume to enable accurate simulation. The most challenging part of this step is correctly identifying and extracting the following data for each building:

id: Unique identifier for the building.

year_built: The construction year of the building.

roof_type: Type of the roof (e.g., flat, sloped).

roof_h_typ: Type of roof height (e.g., standard, variable).

roof_h_min: Minimum height of the roof.

roof_h_max: Maximum height of the roof.

ground_lvl: Ground level of the building, which helps in aligning the building within the terrain.

volume_lod2: The building’s volume at Level of Detail 2, which includes basic geometric details.

footprint: The building’s footprint area on the ground.

Extracting these details from the CityJSON file ensures that we have accurate data for each building to proceed with the simulation in subsequent steps. Special attention is needed to handle inconsistencies or missing data that might arise during extraction.
