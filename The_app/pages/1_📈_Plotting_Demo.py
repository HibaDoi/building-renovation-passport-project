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
gdf = gdf.to_crs(epsg=4326)
st.dataframe(gdf)


#🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶🔶



# 🔶 Step 4: Streamlit layout
st.title("Shapefile Viewer")

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
    
)

view_state = pdk.ViewState(
    latitude=52.001667,
    longitude=4.370000,
    zoom=14,
    pitch=0,
)

st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))
