from buildingspy.io.outputfile import Reader
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend (no Qt)
import matplotlib.pyplot as plt
import numpy as np

import streamlit as st


# Path to your Dymola / OpenModelica result file
path = r"_5_Web_Mini_Dashboard/ResidentialBuilding_res.mat"

r = Reader(path, "dymola")               # second arg: "dymola" or "openmodelica"

# --- 1) Get list of variables ---------------------------------
var_names = r.varNames()
print("First 10 variables:", var_names[:10])

# --- 2) Fetch a time series -----------------------------------
# returns (time_vector, values)
t, T_z1 = r.values('multizone.zone[1].ROM.TAir')

# --- 3) Quick plot --------------------------------------------
plt.plot(t / 3600, T_z1)
plt.xlabel("Time [h]"); plt.ylabel("Zone-1 Air Temp [°C]")
plt.show()
