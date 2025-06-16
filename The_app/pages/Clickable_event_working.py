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
        building_ids = [
            f.split('/')[-1].replace("_result.mat", "").replace("NL_Building_", "NL.IMBAG.Pand.") 
            for f in mat_files
        ]
        return building_ids, mat_files
    except Exception as e:
        st.error(f"Error accessing GCS bucket: {str(e)}")
        return [], []

def main():
    st.title("🏢 Building Renovation Passport - Interactive Map")
    
    try:
        # Initialize GCS
        client, bucket = init_gcs_client()
        
        # Load shapefile from GCS
        with st.spinner("Loading building data from Google Cloud Storage..."):
            gdf = load_shapefile_from_gcs("shpp/u", bucket)
        
        if gdf is None:
            st.error("❌ Failed to load shapefile from Google Cloud Storage")
            st.stop()
        
        # Get building IDs from .mat files in GCS
        with st.spinner("Loading simulation results from GCS..."):
            building_ids, mat_files = get_building_ids_from_gcs(client, bucket)
        
        if building_ids:
            # Filter GDF to only include buildings with simulation results
            clean_building_ids = [bid.split('/')[-1] for bid in building_ids]
            filtered_gdf = gdf[gdf["object_id_clean"].isin(clean_building_ids)]
            st.success(f"✅ Found {len(filtered_gdf)} buildings with simulation results")
        else:
            st.warning("⚠️ No simulation results found in GCS. Using all buildings.")
            filtered_gdf = gdf
        
        # Create two columns for split layout
        col_map, col_details = st.columns([2, 1])  # Map takes 2/3, details take 1/3
        
        with col_map:
            # Initialize session state
            if 'selected_building_id' not in st.session_state:
                st.session_state.selected_building_id = None
        
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
                    
                    # Determine if this building has simulation results
                    has_results = row['object_id_clean'] in clean_building_ids if building_ids else False
                    
                    # Add building polygon with custom properties for click detection
                    geojson_feature = folium.GeoJson(
                        row.geometry,
                        popup=folium.Popup(
                            html=f"""
                            <div style='font-family: Arial; font-size: 12px; min-width: 200px;'>
                                <b>Building ID:</b> {row['object_id_clean']}<br>
                                <b>Original ID:</b> {row['object_id']}<br>
                                <b>Has Simulation:</b> {'✅ Yes' if has_results else '❌ No'}<br>
                                <b>Coordinates:</b> {centroid.y:.6f}, {centroid.x:.6f}
                            </div>
                            """,
                            max_width=300
                        ),
                        tooltip=f"Building: {row['object_id_clean']} {'(Has Results)' if has_results else '(No Results)'}",
                        style_function=lambda feature, building_id=row['object_id_clean'], has_sim=has_results: {
                            'fillColor': (
                                '#ff6b6b' if st.session_state.selected_building_id == building_id 
                                else '#4ecdc4' if has_sim 
                                else '#95a5a6'
                            ),
                            'color': '#2c3e50',
                            'weight': 2,
                            'fillOpacity': 0.7,
                            'opacity': 1
                        }
                    )
                    
                    geojson_feature.add_to(m)
                
                # Add legend
                legend_html = '''
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 150px; height: 90px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:14px; padding: 10px">
                <p><b>Legend</b></p>
                <p><i class="fa fa-square fa-1x" style="color:#4ecdc4"></i> Has Results</p>
                <p><i class="fa fa-square fa-1x" style="color:#95a5a6"></i> No Results</p>
                <p><i class="fa fa-square fa-1x" style="color:#ff6b6b"></i> Selected</p>
                </div>
                '''
                m.get_root().html.add_child(folium.Element(legend_html))
                
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
                
                # Show currently selected building info
                if st.session_state.selected_building_id:
                    selected_building = filtered_gdf[
                        filtered_gdf['object_id_clean'] == st.session_state.selected_building_id
                    ]
                    
                    if not selected_building.empty:
                        building_info = selected_building.iloc[0]
                        
                        st.subheader(f"🏠 Selected: {st.session_state.selected_building_id}")
                        
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
                        
                        # Check if building has simulation results
                        has_simulation = building_info['object_id_clean'] in clean_building_ids
                        if has_simulation:
                            st.success("✅ This building has simulation results available!")
                        else:
                            st.info("ℹ️ No simulation results available for this building")
                
                # Show currently selected building in sidebar
                if st.session_state.selected_building_id:
                    st.info(f"🎯 **Currently Selected:** {st.session_state.selected_building_id}")
                    if st.button("Clear Selection"):
                        st.session_state.selected_building_id = None
                        st.rerun()
        
            except ImportError:
                st.error("📦 **streamlit-folium not installed!**")
                st.code("pip install streamlit-folium", language="bash")
                st.info("Install the package above to enable interactive map functionality.")
        
        with col_details:
            st.header("📊 Building Details")
            
            if st.session_state.selected_building_id:
                building_id = st.session_state.selected_building_id
                
                # Check if this building has results
                if building_id in clean_building_ids:
                    st.markdown("### 🔥 Energy Analysis Available")
                    
                    # Find the corresponding mat file
                    mat_file_pattern = f"NL_Building_{building_id.replace('NL.IMBAG.Pand.', '')}_result.mat"
                    matching_files = [f for f in mat_files if f.endswith(mat_file_pattern)]
                    
                    if matching_files:
                        st.success(f"📁 **Simulation File:** `{matching_files[0]}`")
                        
                        if st.button("🚀 View Energy Analysis", key="energy_btn"):
                            st.session_state.show_energy_tab = True
                            st.info("Switch to the Energy Analysis tab to view detailed results!")
                    else:
                        st.warning("Simulation file pattern not found")
                        
                    # Show building properties if available
                    try:
                        # Try to load building info from JSON
                        building_data_blob = bucket.blob("for_teaser.json")
                        if building_data_blob.exists():
                            json_string = building_data_blob.download_as_text()
                            building_data = json.loads(json_string)
                            
                            # Find building info
                            building_info = None
                            if isinstance(building_data, list):
                                for building in building_data:
                                    if building.get('id') == building_id:
                                        building_info = building
                                        break
                            elif isinstance(building_data, dict):
                                building_info = building_data.get(building_id)
                            
                            if building_info:
                                st.markdown("### 🏢 Building Properties")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if 'year_built' in building_info:
                                        st.metric("Year Built", building_info['year_built'])
                                    if 'roof_type' in building_info:
                                        st.write(f"**Roof Type:** {building_info['roof_type'].title()}")
                                
                                with col2:
                                    if 'roof_h_typ' in building_info:
                                        st.metric("Roof Height", f"{building_info['roof_h_typ']:.1f} m")
                                    if 'ground_lvl' in building_info:
                                        st.metric("Ground Level", f"{building_info['ground_lvl']:.1f} m")
                                
                                with st.expander("🔍 Full Building Data"):
                                    st.json(building_info)
                    except Exception as e:
                        st.warning(f"Could not load building properties: {str(e)}")
                        
                else:
                    st.info("ℹ️ **No simulation data available** for the selected building.")
                    st.write("Buildings with simulation results are shown in **teal** on the map.")
            else:
                st.info("👆 **Click on a building** in the map to see its details here.")
                
                # Show summary statistics
                st.markdown("### 📈 Summary")
                st.metric("Total Buildings", len(gdf))
                st.metric("Buildings with Results", len(filtered_gdf))
                
                if building_ids:
                    coverage = (len(filtered_gdf) / len(gdf)) * 100
                    st.metric("Coverage", f"{coverage:.1f}%")
    
    except Exception as e:
        st.error(f"❌ **Application Error:** {str(e)}")
        st.info("Please check your Google Cloud Storage configuration and credentials.")

if __name__ == "__main__":
    main()