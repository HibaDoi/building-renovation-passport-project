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

# Initialize session state
if 'selected_building_id' not in st.session_state:
    st.session_state.selected_building_id = None
if 'selected_coordinates' not in st.session_state:
    st.session_state.selected_coordinates = None



# =============================================================================
# PYDECK IMPLEMENTATION WITH CLICK EVENTS
# =============================================================================
st.header("🌐 PyDeck Map with Click Events")

try:
    # Prepare data for PyDeck - need to flatten the dataframe for better performance
    pydeck_data = []
    
    for idx, row in filtered_gdf.iterrows():
        # Get polygon coordinates
        if row.geometry.geom_type == 'Polygon':
            coordinates = [list(row.geometry.exterior.coords)]
        elif row.geometry.geom_type == 'MultiPolygon':
            coordinates = [list(polygon.exterior.coords) for polygon in row.geometry.geoms]
        else:
            continue
            
        # Get centroid for positioning
        centroid = row.geometry.centroid
        
        # Create data entry
        pydeck_data.append({
            'object_id_clean': row['object_id_clean'],
            'object_id': row['object_id'],
            'coordinates': coordinates,
            'centroid_lat': centroid.y,
            'centroid_lon': centroid.x,
            'area': row.geometry.area,
            'is_selected': row['object_id_clean'] == st.session_state.selected_building_id
        })
    
    # Convert to DataFrame for PyDeck
    import pandas as pd
    pydeck_df = pd.DataFrame(pydeck_data)
    
    # Create dynamic colors based on selection
    def get_fill_color(row):
        if row['is_selected']:
            return [255, 107, 107, 180]  # Red for selected
        else:
            return [78, 205, 196, 140]   # Teal for unselected
    
    def get_line_color(row):
        if row['is_selected']:
            return [255, 255, 255, 255]  # White border for selected
        else:
            return [44, 62, 80, 255]     # Dark border for unselected
    
    # Apply colors
    pydeck_df['fill_color'] = pydeck_df.apply(get_fill_color, axis=1)
    pydeck_df['line_color'] = pydeck_df.apply(get_line_color, axis=1)
    
    # Create PyDeck layer with enhanced styling
    polygon_layer = pdk.Layer(
        'PolygonLayer',
        data=pydeck_df,
        get_polygon='coordinates',
        get_fill_color='fill_color',
        get_line_color='line_color',
        line_width_min_pixels=2,
        line_width_max_pixels=4,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 0, 100],  # Yellow highlight on hover
    )
    
    # Set the viewport location
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=15,
        pitch=0,
        bearing=0
    )
    
    # Enhanced tooltip with HTML formatting
    tooltip_config = {
        "html": """
        <div style='background-color: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.3);'>
            <h4 style='margin: 0; color: #2c3e50;'>🏢 Building Info</h4>
            <hr style='margin: 5px 0;'>
            <b>Building ID:</b> {object_id_clean}<br>
            <b>Original ID:</b> {object_id}<br>
            <b>Area:</b> {area:.6f}<br>
            <b>Coordinates:</b> {centroid_lat:.4f}, {centroid_lon:.4f}<br>
            <small style='color: #7f8c8d;'>Click to select this building</small>
        </div>
        """,
        "style": {
            "backgroundColor": "white",
            "color": "black"
        }
    }
    
    # Render the map with click event capture
    pydeck_map = pdk.Deck(
        layers=[polygon_layer],
        initial_view_state=view_state,
        tooltip=tooltip_config,
        map_style='mapbox://styles/mapbox/light-v9'  # Clean map style
    )
    
    # Display the map and capture events
    map_result = st.pydeck_chart(
        pydeck_map,
        use_container_width=True,
        selection_mode='single-object',
        on_select='rerun',
        key='pydeck_map'
    )
    
    # Debug section for PyDeck
    st.subheader("🔍 PyDeck Debug Information")
    
    with st.expander("🔧 PyDeck Map Events", expanded=True):
        if hasattr(map_result, 'selection') and map_result.selection:
            st.write("**Selection Data:**")
            st.json(map_result.selection)
            
            # Process the selection
            selection = map_result.selection
            if 'objects' in selection and len(selection['objects']) > 0:
                selected_obj = selection['objects'][0]
                
                if 'object_id_clean' in selected_obj:
                    selected_building_id = selected_obj['object_id_clean']
                    st.session_state.selected_building_id = selected_building_id
                    st.success(f"✅ PyDeck Selection: **{selected_building_id}**")
                    
                    # Show building details
                    st.subheader(f"🏠 Selected Building: {selected_building_id}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Building Details:**")
                        st.write(f"- **Clean ID:** {selected_obj.get('object_id_clean', 'N/A')}")
                        st.write(f"- **Original ID:** {selected_obj.get('object_id', 'N/A')}")
                        
                    with col2:
                        st.write("**Geometry Info:**")
                        st.write(f"- **Centroid:** ({selected_obj.get('centroid_lat', 0):.6f}, {selected_obj.get('centroid_lon', 0):.6f})")
                        st.write(f"- **Area:** {selected_obj.get('area', 0):.8f}")
        else:
            st.write("No selection data available. Click on a building to see selection info.")
    
    # Alternative approach using session state and manual click detection
    st.subheader("🎯 Manual Selection (Backup Method)")
    
    # Create a selectbox as backup
    building_options = ['None'] + list(filtered_gdf['object_id_clean'].unique())
    selected_from_dropdown = st.selectbox(
        "Select a building manually:",
        options=building_options,
        index=0 if not st.session_state.selected_building_id else 
              building_options.index(st.session_state.selected_building_id) if st.session_state.selected_building_id in building_options else 0
    )
    
    if selected_from_dropdown != 'None':
        st.session_state.selected_building_id = selected_from_dropdown
        st.success(f"✅ Manually selected: **{selected_from_dropdown}**")
    
    # Show currently selected building info
    if st.session_state.selected_building_id:
        st.info(f"🎯 **Currently Selected Building:** {st.session_state.selected_building_id}")
        
        if st.button("🔄 Clear PyDeck Selection"):
            st.session_state.selected_building_id = None
            st.rerun()
    
    # Statistics
    st.subheader("📊 Map Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Buildings", len(filtered_gdf))
    with col2:
        st.metric("Selected Building", st.session_state.selected_building_id or "None")
    with col3:
        if st.session_state.selected_building_id:
            selected_building = filtered_gdf[filtered_gdf['object_id_clean'] == st.session_state.selected_building_id]
            if not selected_building.empty:
                st.metric("Building Area", f"{selected_building.iloc[0].geometry.area:.6f}")
    
except Exception as e:
    st.error(f"PyDeck error: {e}")
    st.write("**Error details:**")
    import traceback
    st.code(traceback.format_exc())