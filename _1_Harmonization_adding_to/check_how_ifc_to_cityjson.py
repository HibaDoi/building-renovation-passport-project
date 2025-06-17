# Basic approach using IfcOpenShell and cjio
import ifcopenshell
from cjio import cityjson

# Load IFC file
ifc_file = ifcopenshell.open('_1_Data_harvest\IFC_Model\Duplex_A_20110907.ifc')
# Process geometry and semantics
# Convert to CityJSON structure