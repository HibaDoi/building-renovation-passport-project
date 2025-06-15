import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import os
from buildingspy.io.outputfile import Reader

st.title("🏠 Renovation Dashboard")

# 1️⃣ Select a .mat file from folder
mat_folder = "Open_modula_maybe/simulation_results"
mat_files = [f for f in os.listdir(mat_folder) if f.endswith(".mat")]

selected_file = st.selectbox("Choose a result file:", mat_files)

if selected_file:
    file_path = os.path.join(mat_folder, selected_file)

    # 2️⃣ Load .mat file
    r = Reader(file_path, "dymola")
    # After r = Reader(file_path, "dymola")
    all_vars = r.varNames()        # returns a Python list
    st.write(f"{len(all_vars)} variables found")
    st.write(all_vars)        # show the first 40 to keep the page short
    try:
        time, heat_pre = r.values('multizone.PHeater[1]')

        # Convert seconds to months
        seconds_per_year  = 365 * 24 * 3600
        seconds_per_month = seconds_per_year / 12.0
        time_months       = time / seconds_per_month

        # Plot heating power over months
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
        st.pyplot(fig)



    except Exception as e:
        st.error(f"Error reading data: {e}")