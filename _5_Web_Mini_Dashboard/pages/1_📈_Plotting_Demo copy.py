import streamlit as st
import geopandas as gpd
import pydeck as pdk
import os 
# 🔶import the shp import 
shp_path = "E:/building-renovation-passport-project/_5_Web_Mini_Dashboard/u.shp"  

# 🔶 read the shp with gpd
gdf = gpd.read_file(shp_path)
# 🔶 drop istance that do not end with -0
gdf = gdf[gdf["object_id"].astype(str).str.endswith("-0")]

# 🔶 Clean object_id to remove '-0' for comparison
if isinstance(gdf["object_id"].iloc[0], list):
    gdf["object_id_clean"] = gdf["object_id"].apply(
        lambda x: x[0].replace("-0", "") if isinstance(x, list) and len(x) > 0 else "")
else:
    gdf["object_id_clean"] = gdf["object_id"].astype(str).str.replace("-0", "", regex=False)
gdf = gdf.to_crs(epsg=4326)

# 🔶 drop geometry colum from gdf 
# st.dataframe(gdf.drop(columns='geometry'))

#🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶

# Path to folder containing .mat files
results_folder = "Open_modula_maybe/simulation_results"

# Get all building IDs from the .mat filenames
mat_files = [f for f in os.listdir(results_folder) if f.endswith("_result.mat")]
building_ids = [f.replace("_result.mat", "").replace("NL_Building_", "NL.IMBAG.Pand.") for f in mat_files]
print(building_ids)
# 🔶 Step 4: Streamlit layout
st.title("Shapefile Viewer")
# Filter only buildings that have corresponding .mat results
filtered_gdf = gdf[gdf["object_id_clean"].isin(building_ids)]

# 🔶 Step 5: Display map using pydeck
geojson = gdf.__geo_interface__

layer = pdk.Layer(
    "GeoJsonLayer",
    geojson,
    stroked=True,
    filled=True,
    extruded=False,
    get_fill_color=[200, 30, 0, 90],
    get_line_color=[255, 255, 255],
    pickable=True,          # ← active le picking
    auto_highlight=True     # ← fait briller la feature survolée

    
)

view_state = pdk.ViewState(
    latitude=52.001667,
    longitude=4.370000,
    zoom=14,
    pitch=0,
)



# st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))


# 3️⃣ Deck + tooltip facultatif
deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"text": "Building ID: {object_id_clean}"}  # {name} doit exister dans les properties
)

# 4️⃣ Affichage + capture du clic
event = st.pydeck_chart(
    deck,
    on_select="rerun",            # relance l’appli quand on clique
    selection_mode="single-object",
    key="map"                     # clé pour conserver l’état
)

# 5️⃣ Afficher le nom du bâtiment sélectionné
if event and event.selection and event.selection.objects:
    selected = event.selection.objects["object_id_clean"][0]   # couche « buildings »
    st.success(f"Bâtiment sélectionné : {selected['name']}")