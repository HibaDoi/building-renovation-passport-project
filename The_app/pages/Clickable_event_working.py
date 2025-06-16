import streamlit as st
import geopandas as gpd
import pydeck as pdk
import tempfile
import os
import json
from google.cloud import storage
from google.oauth2 import service_account

# Set page configuration
st.set_page_config(
    page_title="Building Renovation Passport",
    page_icon="🏢",
    layout="wide"
)

# Initialize GCS client
@st.cache_resource
def init_gcs_client():
    """Initialize GCS client with credentials"""
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    bucket_name = "renodat"
    client = storage.Client(credentials=credentials)
    bucket = client.bucket(bucket_name)
    return client, bucket

# Load shapefile from GCS
@st.cache_data
def load_shapefile_from_gcs(blob_prefix, _bucket):
    """
    Load shapefile from GCS bucket
    blob_prefix should be the path without .shp extension
    """
    # Shapefile components
    extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg']
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download all shapefile components
        for ext in extensions:
            blob_name = f"{blob_prefix}{ext}"
            blob = _bucket.blob(blob_name)
            
            if blob.exists():
                local_path = os.path.join(temp_dir, f"temp{ext}")
                blob.download_to_filename(local_path)
        
        # Load the shapefile
        shp_path = os.path.join(temp_dir, "temp.shp")
        if os.path.exists(shp_path):
            gdf = gpd.read_file(shp_path)
            
            # Drop instances that do not end with -0
            gdf = gdf[gdf["object_id"].astype(str).str.endswith("-0")]
            
            # Clean object_id to remove '-0' for comparison
            if isinstance(gdf["object_id"].iloc[0], list):
                gdf["object_id_clean"] = gdf["object_id"].apply(
                    lambda x: x[0].replace("-0", "") if isinstance(x, list) and len(x) > 0 else "")
            else:
                gdf["object_id_clean"] = gdf["object_id"].astype(str).str.replace("-0", "", regex=False)
            
            gdf = gdf.to_crs(epsg=4326)
            return gdf
        else:
            st.error("Failed to download shapefile components")
            return None

# Get building IDs from .mat files in GCS
@st.cache_data
def get_building_ids_from_gcs(_client, _bucket, mat_prefix="simulation/"):
    """Get building IDs from .mat files stored in GCS"""
    try:
        mat_blobs = list(_client.list_blobs(_bucket, prefix=mat_prefix))
        mat_files = [blob.name for blob in mat_blobs if blob.name.endswith("_result.mat")]
        building_ids = []
        
        for f in mat_files:
            # Extract building ID from filename
            filename = f.split('/')[-1]  # Get just the filename
            if filename.startswith("NL_Building_"):
                # Convert from NL_Building_0503100000019674_result.mat to NL.IMBAG.Pand.0503100000019674
                building_id_number = filename.replace("_result.mat", "").replace("NL_Building_", "")
                full_building_id = f"NL.IMBAG.Pand.{building_id_number}"
                building_ids.append(full_building_id)
        
        st.info(f"🔍 Found {len(building_ids)} simulation files in GCS")
        if len(building_ids) > 0:
            st.write(f"Sample IDs: {building_ids[:3]}...")
        
        return building_ids, mat_files
    except Exception as e:
        st.error(f"Error accessing GCS bucket: {str(e)}")
        return [], []

def main():
    st.title("🏢 Building Renovation Passport - All Buildings Map")
    
    try:
        # Initialize GCS
        client, bucket = init_gcs_client()
        
        # Load ALL buildings from shapefile
        with st.spinner("Loading ALL building data from Google Cloud Storage..."):
            gdf = load_shapefile_from_gcs("shpp/u", bucket)
        
        if gdf is None:
            st.error("❌ Failed to load shapefile from Google Cloud Storage")
            st.stop()
        
        # Get building IDs that have simulation results
        with st.spinner("Checking simulation availability..."):
            simulation_building_ids, mat_files = get_building_ids_from_gcs(client, bucket)
        
        # Debug: Show some sample IDs for comparison
        st.write("🔍 **Debug Info:**")
        st.write(f"Sample shapefile IDs: {gdf['object_id_clean'].head(3).tolist()}")
        st.write(f"Sample simulation IDs: {simulation_building_ids[:3] if simulation_building_ids else 'None found'}")
        
        # Add simulation availability to the dataframe
        gdf['has_simulation'] = gdf['object_id_clean'].isin(simulation_building_ids)
        
        # Statistics
        total_buildings = len(gdf)
        buildings_with_sim = len(gdf[gdf['has_simulation']])
        coverage_percent = (buildings_with_sim / total_buildings * 100) if total_buildings > 0 else 0
        
        # Display statistics
        st.markdown("### 📊 Building Coverage Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Buildings", total_buildings)
        with col2:
            st.metric("With Simulations", buildings_with_sim)
        with col3:
            st.metric("Coverage", f"{coverage_percent:.1f}%")
        
        st.markdown("---")
        
        # Create two columns for split layout
        col_map, col_details = st.columns([2, 1])
        
        with col_map:
            # Initialize session state
            if 'selected_building_id' not in st.session_state:
                st.session_state.selected_building_id = None
        
            st.header("🗺️ Interactive Map - All Buildings")
            st.markdown("**Click on any building to see simulation availability**")
        
            try:
                import folium
                from streamlit_folium import st_folium
                
                # Create base map centered on all buildings
                center_lat = gdf.geometry.centroid.y.mean()
                center_lon = gdf.geometry.centroid.x.mean()
                
                m = folium.Map(
                    location=[center_lat, center_lon], 
                    zoom_start=14,
                    tiles='OpenStreetMap'
                )
                
                # Add ALL buildings to the map
                for idx, row in gdf.iterrows():
                    # Get building coordinates
                    centroid = row.geometry.centroid
                    has_simulation = row['has_simulation']
                    building_id = row['object_id_clean']
                    
                    # Determine color based on simulation availability and selection
                    if st.session_state.selected_building_id == building_id:
                        color = '#ff6b6b'  # Red for selected
                        status = "Selected"
                    elif has_simulation:
                        color = '#4ecdc4'  # Teal for buildings with simulation
                        status = "Has Simulation"
                    else:
                        color = '#95a5a6'  # Gray for buildings without simulation
                        status = "No Simulation"
                    
                    # Create popup content
                    popup_html = f"""
                    <div style='font-family: Arial; font-size: 12px; min-width: 250px; padding: 10px;'>
                        <h4 style='margin-top: 0; color: #2c3e50;'>🏢 Building Details</h4>
                        <hr style='margin: 5px 0;'>
                        <b>Building ID:</b> {building_id}<br>
                        <b>Original ID:</b> {row['object_id']}<br>
                        <b>Simulation Status:</b> <span style='color: {"green" if has_simulation else "red"}; font-weight: bold;'>
                            {'✅ Available' if has_simulation else '❌ Not Available'}
                        </span><br>
                        <b>Coordinates:</b> {centroid.y:.6f}, {centroid.x:.6f}<br>
                        <b>Building Area:</b> {row.geometry.area:.8f} sq units
                    </div>
                    """
                    
                    # Add building polygon
                    geojson_feature = folium.GeoJson(
                        row.geometry,
                        popup=folium.Popup(html=popup_html, max_width=300),
                        tooltip=f"🏢 {building_id} - {status}",
                        style_function=lambda feature, fill_color=color: {
                            'fillColor': fill_color,
                            'color': '#2c3e50',
                            'weight': 1,
                            'fillOpacity': 0.7,
                            'opacity': 1
                        }
                    )
                    
                    geojson_feature.add_to(m)
                
                # Add enhanced legend
                legend_html = f'''
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 200px; height: 140px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:12px; padding: 15px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.3);">
                <h4 style="margin-top: 0; color: #2c3e50;">🗺️ Map Legend</h4>
                <div style="margin: 8px 0;">
                    <span style="display: inline-block; width: 15px; height: 15px; background-color: #4ecdc4; margin-right: 8px;"></span>
                    <span>Has Simulation ({buildings_with_sim})</span>
                </div>
                <div style="margin: 8px 0;">
                    <span style="display: inline-block; width: 15px; height: 15px; background-color: #95a5a6; margin-right: 8px;"></span>
                    <span>No Simulation ({total_buildings - buildings_with_sim})</span>
                </div>
                <div style="margin: 8px 0;">
                    <span style="display: inline-block; width: 15px; height: 15px; background-color: #ff6b6b; margin-right: 8px;"></span>
                    <span>Selected Building</span>
                </div>
                <div style="margin-top: 10px; font-size: 10px; color: #666;">
                    Coverage: {coverage_percent:.1f}%
                </div>
                </div>
                '''
                m.get_root().html.add_child(folium.Element(legend_html))
                
                # Display map and capture clicks
                map_data = st_folium(
                    m, 
                    key="all_buildings_map",
                    width=800, 
                    height=600,
                    returned_objects=["last_object_clicked_popup"]
                )
                
                # Process click events - Fixed click detection
                clicked_building_id = None
                
                if map_data.get('last_object_clicked_popup'):
                    popup_data = map_data['last_object_clicked_popup']
                    if popup_data:
                        # Extract building ID from popup content
                        popup_content = str(popup_data)
                        # Look for building ID in the popup content
                        import re
                        match = re.search(r'Building ID:</b> (NL\.IMBAG\.Pand\.\d+)', popup_content)
                        if match:
                            clicked_building_id = match.group(1)
                
                # Fallback: use coordinate-based detection if popup method fails
                if not clicked_building_id and map_data.get('last_object_clicked'):
                    click_data = map_data['last_object_clicked']
                    
                    if click_data and 'lat' in click_data and 'lng' in click_data:
                        click_lat = click_data['lat']
                        click_lng = click_data['lng']
                        
                        # Find the building that was clicked
                        from shapely.geometry import Point
                        click_point = Point(click_lng, click_lat)
                        
                        # Check if click is inside any building
                        for idx, row in gdf.iterrows():
                            if row.geometry.contains(click_point):
                                clicked_building_id = row['object_id_clean']
                                break
                        
                        # If not inside any building, find the closest one
                        if not clicked_building_id:
                            min_distance = float('inf')
                            closest_building = None
                            
                            for idx, row in gdf.iterrows():
                                centroid = row.geometry.centroid
                                distance = click_point.distance(centroid)
                                if distance < min_distance:
                                    min_distance = distance
                                    closest_building = row['object_id_clean']
                            
                            if closest_building and min_distance < 0.001:  # Only if very close
                                clicked_building_id = closest_building
                
                # Update session state
                if clicked_building_id:
                    st.session_state.selected_building_id = clicked_building_id
                    st.rerun()
        
            except ImportError:
                st.error("📦 **streamlit-folium not installed!**")
                st.code("pip install streamlit-folium", language="bash")
                st.info("Install the package above to enable interactive map functionality.")
        
        with col_details:
            st.header("🔍 Building Inspector")
            
            if st.session_state.selected_building_id:
                building_id = st.session_state.selected_building_id
                
                # Get building data
                selected_building = gdf[gdf['object_id_clean'] == building_id]
                
                if not selected_building.empty:
                    building_data = selected_building.iloc[0]
                    has_simulation = building_data['has_simulation']
                    
                    st.markdown(f"### 🏢 Building: `{building_id}`")
                    
                    # Simulation status with prominent display
                    if has_simulation:
                        st.success("✅ **SIMULATION AVAILABLE**")
                        st.markdown("This building has energy simulation data!")
                        
                        # Find the simulation file
                        building_id_short = building_id.replace('NL.IMBAG.Pand.', '')
                        mat_file_pattern = f"NL_Building_{building_id_short}_result.mat"
                        matching_files = [f for f in mat_files if f.endswith(mat_file_pattern)]
                        
                        if matching_files:
                            st.info(f"📁 **File:** `{matching_files[0]}`")
                            
                            if st.button("🚀 Analyze Energy Data", key="analyze_btn"):
                                st.balloons()
                                st.success("Ready for energy analysis! 🎯")
                    else:
                        st.error("❌ **NO SIMULATION AVAILABLE**")
                        st.markdown("This building does not have energy simulation data.")
                    
                    # Building details
                    st.markdown("### 📋 Building Details")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Identification:**")
                        st.write(f"- **Clean ID:** {building_data['object_id_clean']}")
                        st.write(f"- **Original ID:** {building_data['object_id']}")
                    
                    with col2:
                        st.markdown("**Geometry:**")
                        centroid = building_data.geometry.centroid
                        st.write(f"- **Lat:** {centroid.y:.6f}")
                        st.write(f"- **Lng:** {centroid.x:.6f}")
                        st.write(f"- **Area:** {building_data.geometry.area:.8f}")
                    
                    # Try to load additional building properties
                    try:
                        building_info_blob = bucket.blob("for_teaser.json")
                        if building_info_blob.exists():
                            json_string = building_info_blob.download_as_text()
                            building_info_data = json.loads(json_string)
                            
                            # Find building info
                            building_props = None
                            if isinstance(building_info_data, list):
                                for building in building_info_data:
                                    if building.get('id') == building_id:
                                        building_props = building
                                        break
                            elif isinstance(building_info_data, dict):
                                building_props = building_info_data.get(building_id)
                            
                            if building_props:
                                st.markdown("### 🏗️ Building Properties")
                                
                                prop_col1, prop_col2 = st.columns(2)
                                with prop_col1:
                                    if 'year_built' in building_props:
                                        st.metric("Year Built", building_props['year_built'])
                                    if 'roof_type' in building_props:
                                        st.write(f"**Roof Type:** {building_props['roof_type'].title()}")
                                
                                with prop_col2:
                                    if 'roof_h_typ' in building_props:
                                        st.metric("Roof Height", f"{building_props['roof_h_typ']:.1f} m")
                                    if 'ground_lvl' in building_props:
                                        st.metric("Ground Level", f"{building_props['ground_lvl']:.1f} m")
                                
                                with st.expander("🔍 All Properties"):
                                    st.json(building_props)
                    except Exception as e:
                        st.info("ℹ️ Additional building properties not available")
                    
                    # Clear selection button
                    if st.button("🗑️ Clear Selection", key="clear_btn"):
                        st.session_state.selected_building_id = None
                        st.rerun()
                        
            else:
                st.info("👆 **Click on any building** in the map to inspect it!")
                st.markdown("### 🎯 Quick Stats")
                st.write(f"- **Total Buildings:** {total_buildings}")
                st.write(f"- **With Simulations:** {buildings_with_sim}")
                st.write(f"- **Without Simulations:** {total_buildings - buildings_with_sim}")
                st.write(f"- **Coverage:** {coverage_percent:.1f}%")
                
                # Show some example building IDs
                if buildings_with_sim > 0:
                    st.markdown("### 🏢 Buildings with Simulations (Sample)")
                    sample_buildings = gdf[gdf['has_simulation']]['object_id_clean'].head(5).tolist()
                    for i, building in enumerate(sample_buildings, 1):
                        st.write(f"{i}. `{building}`")
                    
                    if buildings_with_sim > 5:
                        st.write(f"... and {buildings_with_sim - 5} more")
    
    except Exception as e:
        st.error(f"❌ **Application Error:** {str(e)}")
        st.info("Please check your Google Cloud Storage configuration and credentials.")
        st.exception(e)  # This will show the full error traceback

if __name__ == "__main__":
    main()