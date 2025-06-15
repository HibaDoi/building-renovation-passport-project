import streamlit as st
import geopandas as gpd
import pydeck as pdk
import os
import json

# 🔶 Import the shp 
shp_path = "E:/building-renovation-passport-project/_5_Web_Mini_Dashboard/u.shp"  

# 🔶 Read the shp with gpd
gdf = gpd.read_file(shp_path)

# 🔶 Drop instances that do not end with -0
gdf = gdf[gdf["object_id"].astype(str).str.endswith("-0")]

# 🔶 Clean object_id to remove '-0' for comparison
if isinstance(gdf["object_id"].iloc[0], list):
    gdf["object_id_clean"] = gdf["object_id"].apply(
        lambda x: x[0].replace("-0", "") if isinstance(x, list) and len(x) > 0 else "")
else:
    gdf["object_id_clean"] = gdf["object_id"].astype(str).str.replace("-0", "", regex=False)

gdf = gdf.to_crs(epsg=4326)

# Path to folder containing .mat files
results_folder = "Open_modula_maybe/simulation_results"

# Get all building IDs from the .mat filenames
if os.path.exists(results_folder):
    mat_files = [f for f in os.listdir(results_folder) if f.endswith("_result.mat")]
    building_ids = [f.replace("_result.mat", "").replace("NL_Building_", "NL.IMBAG.Pand.") for f in mat_files]
    filtered_gdf = gdf[gdf["object_id_clean"].isin(building_ids)]
else:
    st.warning(f"Results folder not found: {results_folder}. Using all buildings.")
    filtered_gdf = gdf

st.title("🏢 Building Renovation Passport - Interactive Map")
# Create two columns for split layout
col_map, col_details = st.columns([2, 1])  # Map takes 2/3, details take 1/3
with col_map:

    # Initialize session state
    if 'selected_building_id' not in st.session_state:
        st.session_state.selected_building_id = None
    if 'selected_coordinates' not in st.session_state:
        st.session_state.selected_coordinates = None

    st.header("🗺️ Interactive Map")

    try:
        import folium
        from streamlit_folium import st_folium
        
        # Create base map
        center_lat = filtered_gdf.geometry.centroid.y.mean()
        center_lon = filtered_gdf.geometry.centroid.x.mean()
        
        m = folium.Map(
            location=[center_lat, center_lon], 
            zoom_start=15,
            tiles='OpenStreetMap'
        )
        
        # Add each building as a clickable polygon
        for idx, row in filtered_gdf.iterrows():
            # Get building coordinates for click detection
            centroid = row.geometry.centroid
            
            # Add building polygon with custom properties for click detection
            geojson_feature = folium.GeoJson(
                row.geometry,
                popup=folium.Popup(
                    html=f"""
                    <div style='font-family: Arial; font-size: 12px; min-width: 200px;'>
                        <b>Building ID:</b> {row['object_id_clean']}<br>
                        <b>Original ID:</b> {row['object_id']}<br>
                        <b>Index:</b> {idx}<br>
                        <b>Coordinates:</b> {centroid.y:.6f}, {centroid.x:.6f}
                    </div>
                    """,
                    max_width=300
                ),
                tooltip=f"Click me! Building: {row['object_id_clean']}",
                style_function=lambda feature, building_id=row['object_id_clean']: {
                    'fillColor': '#ff6b6b' if st.session_state.selected_building_id == building_id else '#4ecdc4',
                    'color': '#2c3e50',
                    'weight': 2,
                    'fillOpacity': 0.7,
                    'opacity': 1
                }
            )
            
            # Add custom properties to the GeoJson for identification
            geojson_feature.add_child(folium.Tooltip(f"Building: {row['object_id_clean']}"))
            geojson_feature.add_to(m)
        
        # Display map and capture clicks
        map_data = st_folium(
            m, 
            key="building_map",
            width=800, 
            height=600,
            returned_objects=["last_object_clicked"]
        )
        
        # Process click events using coordinates
        clicked_building_id = None
        
        if map_data.get('last_object_clicked'):
            click_data = map_data['last_object_clicked']
            
            if click_data and 'lat' in click_data and 'lng' in click_data:
                click_lat = click_data['lat']
                click_lng = click_data['lng']
                
                # Find the closest building to the click
                from shapely.geometry import Point
                click_point = Point(click_lng, click_lat)
                
                min_distance = float('inf')
                closest_building = None
                
                for idx, row in filtered_gdf.iterrows():
                    if row.geometry.contains(click_point):
                        closest_building = row['object_id_clean']
                        break
                    else:
                        # Find closest centroid
                        centroid = row.geometry.centroid
                        distance = click_point.distance(centroid)
                        if distance < min_distance:
                            min_distance = distance
                            closest_building = row['object_id_clean']
                
                if closest_building:
                    clicked_building_id = closest_building
        
        # Update session state if we found a building
        if clicked_building_id:
            st.session_state.selected_building_id = clicked_building_id
            
            # Get building details
            selected_building = filtered_gdf[filtered_gdf['object_id_clean'] == clicked_building_id]
            if not selected_building.empty:
                building_info = selected_building.iloc[0]
                
                st.subheader(f"🏠 Selected Building: {clicked_building_id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Building Details:**")
                    st.write(f"- **Clean ID:** {building_info['object_id_clean']}")
                    st.write(f"- **Original ID:** {building_info['object_id']}")
                    
                with col2:
                    st.write("**Geometry Info:**")
                    centroid = building_info.geometry.centroid
                    st.write(f"- **Centroid:** ({centroid.y:.6f}, {centroid.x:.6f})")
                    st.write(f"- **Area:** {building_info.geometry.area:.8f}")
        
        # Show currently selected building
        if st.session_state.selected_building_id:
            st.info(f"🎯 **Currently Selected:** {st.session_state.selected_building_id}")
            if st.button("Clear Selection"):
                st.session_state.selected_building_id = None
                st.rerun()

    except ImportError:
        st.error("📦 **streamlit-folium not installed!**")
        st.code("pip install streamlit-folium", language="bash")
        st.info("Install the package above to enable interactive map functionality.")