# pages/energy_compare.py
import os, tempfile, traceback
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from google.cloud import storage
from google.oauth2 import service_account
from buildingspy.io.outputfile import Reader

# ───────────────────────────────────────────────
# 1. Connexion à ton bucket
@st.cache_resource
def get_bucket():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return storage.Client(credentials=creds).bucket("renodat")

bucket = get_bucket()

# ───────────────────────────────────────────────
# 2. Téléchargement ponctuel
def download_mat(gcs_path: str) -> str | None:
    blob = bucket.blob(gcs_path)
    if not blob.exists():
        st.error(f"❌ {gcs_path} introuvable"); return None
    tmp_dir = tempfile.mkdtemp()
    local = os.path.join(tmp_dir, "file.mat")
    blob.download_to_filename(local)
    return local

# ───────────────────────────────────────────────
# 3. Extraction de la puissance de chauffage
def heat_series(mat_path: str, var="multizone.PHeater[1]"):
    r = Reader(mat_path, "dymola")
    t, q = r.values(var)            # temps [s], puissance [W]
    t_month = t / ((365*24*3600)/12)
    return t_month, q

def annual_kwh(time_month, q_w):
    seconds = time_month * 30*24*3600
    return np.trapz(q_w, seconds) / 3.6e6

# ───────────────────────────────────────────────
# 4. Interface minimaliste
st.title("📊 Comparaison rapide de deux fichiers .mat")

path_a = st.text_input("Chemin GCS du fichier A", "before_after_insulation/with_insulation.mat")
path_b = st.text_input("Chemin GCS du fichier B", "before_after_insulation/without_insulation.mat")

if st.button("Comparer") and path_a and path_b:
    try:
        with st.spinner("Téléchargement & analyse…"):
            p_a = download_mat(path_a); p_b = download_mat(path_b)
            if not (p_a and p_b): st.stop()

            t_a, q_a = heat_series(p_a)
            t_b, q_b = heat_series(p_b)

        # ── Graphique
        fig, ax = plt.subplots(figsize=(9,5))
        ax.plot(t_a, q_a, lw=2, label=os.path.basename(path_a))
        ax.plot(t_b, q_b, lw=2, label=os.path.basename(path_b))
        ax.set_xticks(np.arange(1,13)); ax.set_xlabel("Mois")
        ax.set_ylabel("Puissance (W)")
        ax.set_title("Puissance de chauffage – comparaison")
        ax.grid(alpha=.3); ax.legend()
        st.pyplot(fig)

        # ── Indicateurs clés
        kwh_a, kwh_b = annual_kwh(t_a,q_a), annual_kwh(t_b,q_b)
        col1,col2,col3 = st.columns(3)
        with col1: st.metric("Conso A", f"{kwh_a:,.0f} kWh/an")
        with col2: st.metric("Conso B", f"{kwh_b:,.0f} kWh/an")
        with col3:
            sav = kwh_a - kwh_b; pct = sav/kwh_a*100 if kwh_a else 0
            st.metric("Économie", f"{sav:,.0f} kWh", f"{pct:.1f}%")

    except Exception as e:
        st.error(f"Erreur : {e}")
        st.text(traceback.format_exc())
