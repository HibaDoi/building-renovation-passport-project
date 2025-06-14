import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from buildingspy.io.outputfile import Reader

st.title("🏠 Renovation Dashboard")

# Charger le fichier .mat
r = Reader("Open_modula_maybe/simulation_results/NL_Building_0503100000000010_result.mat", "dymola")
var_names = r.varNames()
print("First 10 variables:", var_names[:10])
time, heat_pre  = r.values('multizone.PHeater[1]')
print(time)
print(heat_pre)

# 2) Convert seconds → month index (1 to 12)
seconds_per_year  = 365 * 24 * 3600
seconds_per_month = seconds_per_year / 12.0
time_months       = time / seconds_per_month

# 3) Build the Matplotlib figure
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(time_months, heat_pre, label="Pre-renovation Heating Power")
ax.set_xticks(np.arange(1, 13))
ax.set_xticklabels([
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
])
ax.set_xlabel("Month")
ax.set_ylabel("Heating Power (W)")
ax.set_title("Zone 1 Heating Power by Month (Pre-Renovation)")
ax.legend()
ax.grid(True)
plt.tight_layout()

# 4) Display in Streamlit
st.pyplot(fig)


# Get outdoor dry-bulb temperature
time, tout = r.values('multizone.weaBus.TDryBul')

# Scatter P_heater vs. (Tset − Tout)
_, tset = r.values("multizone.TSetHeat[1]")
deltaT = tset - tout

fig, ax = plt.subplots()
ax.scatter(deltaT, heat_pre, s=5, alpha=0.3)
ax.set_xlabel("ΔT = Tset − Tout (°C)")
ax.set_ylabel("Heating Power (W)")
ax.set_title("Heating Power vs. Temperature Difference")
st.pyplot(fig)