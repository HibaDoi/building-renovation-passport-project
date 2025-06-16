import streamlit as st
import geopandas as gpd
import pydeck as pdk
import tempfile
import os 
import json
import matplotlib.pyplot as plt
import numpy as np
import fiona
from google.cloud import storage
from google.oauth2 import service_account

# Set page configuration
st.set_page_config(
    page_title="Building Map Dashboard",
    page_icon="🗺️",
    layout="wide"
)

credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
bucket_name="renodat"
client = storage.Client(credentials=credentials)
bucket = client.bucket(bucket_name)

def load_shapefile_from_gcs(blob_prefix,bucket):
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
            blob = bucket.blob(blob_name)
            
            if blob.exists():
                local_path = os.path.join(temp_dir, f"temp{ext}")
                blob.download_to_filename(local_path)
        
        # Load the shapefile
        shp_path = os.path.join(temp_dir, "temp.shp")
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
# def load_building_info(json_file_path):
#     """Load building information from JSON file"""
#     try:
#         with open(json_file_path, 'r', encoding='utf-8') as file:
#             building_data = json.load(file)
#         return building_data
#     except FileNotFoundError:
#         st.error(f"Building info file not found: {json_file_path}")
#         return None
#     except Exception as e:
#         st.error(f"Error loading building info: {str(e)}")
#         return None

def find_building_info(building_data, target_id):
    """Find specific building information by ID"""
    if isinstance(building_data, list):
        for building in building_data:
            if building.get('id') == target_id:
                return building
    elif isinstance(building_data, dict):
        if building_data.get('id') == target_id:
            return building_data
        # If it's a dict with building IDs as keys
        return building_data.get(target_id)
    return None

def display_building_info(building_info):
    """Display building information in a beautiful format"""
    if not building_info:
        st.warning("No information available for this building")
        return
    
    st.markdown("### 🏢 Building Information")
    
    # Create columns for organized display
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Basic Information")
        if 'id' in building_info:
            st.markdown(f"**Building ID:** `{building_info['id']}`")
        if 'year_built' in building_info:
            st.metric("Year Built", building_info['year_built'])
        if 'roof_type' in building_info:
            st.markdown(f"**Roof Type:** {building_info['roof_type'].title()}")
    
    with col2:
        st.markdown("#### 📐 Dimensions")
        if 'roof_h_typ' in building_info:
            st.metric("Typical Roof Height", f"{building_info['roof_h_typ']:.2f} m")
        if 'roof_h_max' in building_info:
            st.metric("Max Roof Height", f"{building_info['roof_h_max']:.2f} m")
        if 'ground_lvl' in building_info:
            st.metric("Ground Level", f"{building_info['ground_lvl']:.2f} m")
    
    # Additional details in expandable section
    with st.expander("🔍 Additional Details"):
        st.json(building_info)

# @st.cache_data
# def load_shapefile(shp_path):
#     """Load and process shapefile data"""
#     gdf = gpd.read_file(shp_path)
#     # Drop instances that do not end with -0
#     gdf = gdf[gdf["object_id"].astype(str).str.endswith("-0")]
    
#     # Clean object_id to remove '-0' for comparison
#     if isinstance(gdf["object_id"].iloc[0], list):
#         gdf["object_id_clean"] = gdf["object_id"].apply(
#             lambda x: x[0].replace("-0", "") if isinstance(x, list) and len(x) > 0 else "")
#     else:
#         gdf["object_id_clean"] = gdf["object_id"].astype(str).str.replace("-0", "", regex=False)
    
#     gdf = gdf.to_crs(epsg=4326)
#     return gdf

# @st.cache_data
def get_building_ids(mat_blobs):
    """Get building IDs from .mat files"""
    
    mat_files = [blob.name for blob in mat_blobs if blob.name.endswith(".mat")]
    building_ids = [f.replace("_result.mat", "").replace("NL_Building_", "NL.IMBAG.Pand.") for f in mat_files]
    return building_ids, mat_files


def load_json_from_gcs(blob_name,bucket):
    
    
    blob_name = f"{blob_name}{'.json'}"
    blob = bucket.blob(blob_name)
    json_string = blob.download_as_text()

    data = json.loads(json_string)
    return data
# Main App
def main():
    st.title("🗺️ Building Analysis Dashboard")
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["🗺️ Building Map", "📊 Energy Analysis"])
    
    with tab1:
        # Load shapefile from GCS
        gdf = load_shapefile_from_gcs( "shpp/u",bucket)
        
        
        if gdf is not None:
            # Path to building information JSON file
            building_data = load_json_from_gcs("for_teaser",bucket)
            
            
            # Path to folder containing .mat files
            mat_blobs = client.list_blobs(
                    bucket,
                    prefix="simulation/",
                )
            
            # Get all building IDs from the .mat filenames
            building_ids, mat_files = get_building_ids(mat_blobs)
            
            clean_building_ids = [bid.split('/')[-1] for bid in building_ids]
            
            # Filter only buildings that have corresponding .mat results
            filtered_gdf = gdf[gdf["object_id_clean"].isin(clean_building_ids
)]
            
            # Load building information
            # building_data = load_building_info(building_info_path)
            
            # Create layout with map and building info
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("🗺️ Building Map")
                
                # Display map using pydeck
                geojson = gdf.__geo_interface__  # Use all buildings, not just filtered ones
                
                # Add color property to each feature based on building ID
                target_building_id = "NL.IMBAG.Pand.0503100000019674"
                
                for feature in geojson['features']:
                    if feature['properties']['object_id_clean'] == target_building_id:
                        feature['properties']['color'] = [0, 255, 0, 120]  # Green for target building
                    else:
                        feature['properties']['color'] = [200, 30, 0, 90]  # Red for other buildings
                
                layer = pdk.Layer(
                    "GeoJsonLayer",
                    geojson,
                    stroked=True,
                    filled=True,
                    extruded=False,
                    get_fill_color="properties.color",
                    get_line_color=[255, 255, 255],
                    pickable=True,
                    auto_highlight=True
                )
                
                view_state = pdk.ViewState(
                    latitude=52.005278,
                    longitude=4.364722,
                    zoom=17,
                    pitch=0,
                )
                
                deck = pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip={"text": "Building ID: {object_id_clean}"}
                )
                
                map_data = st.pydeck_chart(deck)
            
            with col2:
                st.subheader("🏢 Target Building Details")
                
                if building_data:
                    # Find and display information for the target building
                    target_info = find_building_info(building_data, target_building_id)
                    display_building_info(target_info)
                else:
                    st.warning("📄 Could not load building data from the specified path")
                    st.info(f"**Expected path:** ``")
        
        else:
            st.error("❌ Failed to load shapefile from Google Cloud Storage")
    
    with tab2:
        st.subheader("📊 Heat Consumption Analysis")
        
        target_building_id = "NL.IMBAG.Pand.0503100000019674"
        file_path = next((s for s in mat_files
                   if s.endswith(f"{'0503100000019674'}.mat")), None)
        
        if True:
            try:
                from buildingspy.io.outputfile import Reader
                
                # Load .mat file
                r = Reader(file_path, "dymola")
                
                # Get heating power data
                time, heat_data = r.values('multizone.PHeater[1]')
                
                # Convert seconds to months
                seconds_per_year = 365 * 24 * 3600
                seconds_per_month = seconds_per_year / 12.0
                time_months = time / seconds_per_month
                
                # Create two columns for before/after comparison
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🔥 Pre-Renovation Heating")
                    
                    # Plot heating power
                    fig, ax = plt.subplots(figsize=(8, 5))
                    ax.plot(time_months, heat_data, label="Pre-renovation", color='red')
                    ax.set_xticks(np.arange(1, 13))
                    ax.set_xticklabels([
                        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                    ])
                    ax.set_xlabel("Month")
                    ax.set_ylabel("Heating Power (W)")
                    ax.set_title("Pre-Renovation Heating Power")
                    ax.legend()
                    ax.grid(True)
                    st.pyplot(fig)
                    
                    # Calculate and display metrics
                    total_consumption = np.trapz(heat_data, time) / 3600000  # Convert to kWh
                    max_power = np.max(heat_data)
                    avg_power = np.mean(heat_data)
                    
                    st.metric("Total Annual Consumption", f"{total_consumption:,.0f} kWh")
                    st.metric("Peak Power", f"{max_power:,.0f} W")
                    st.metric("Average Power", f"{avg_power:,.0f} W")
                
                with col2:
                    post_file_path = next((s for s in mat_files
                   if s.endswith(f"{'0503100000013392'}.mat")), None)
                    if os.path.exists(post_file_path):
                        st.markdown("#### 🌱 Post-Renovation Heating")
                        
                        # Load post-renovation data
                        r_post = Reader(post_file_path, "dymola")
                        time_post, heat_post = r_post.values('multizone.PHeater[1]')
                        time_months_post = time_post / seconds_per_month
                        
                        # Plot post-renovation heating
                        fig2, ax2 = plt.subplots(figsize=(8, 5))
                        ax2.plot(time_months_post, heat_post, label="Post-renovation", color='green')
                        ax2.set_xticks(np.arange(1, 13))
                        ax2.set_xticklabels([
                            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                        ])
                        ax2.set_xlabel("Month")
                        ax2.set_ylabel("Heating Power (W)")
                        ax2.set_title("Post-Renovation Heating Power")
                        ax2.legend()
                        ax2.grid(True)
                        st.pyplot(fig2)
                        
                        # Calculate post-renovation metrics
                        total_consumption_post = np.trapz(heat_post, time_post) / 3600000
                        max_power_post = np.max(heat_post)
                        avg_power_post = np.mean(heat_post)
                        
                        # Calculate savings
                        savings = total_consumption - total_consumption_post
                        savings_percent = (savings / total_consumption) * 100
                        
                        st.metric("Total Annual Consumption", f"{total_consumption_post:,.0f} kWh")
                        st.metric("Peak Power", f"{max_power_post:,.0f} W")
                        st.metric("Average Power", f"{avg_power_post:,.0f} W")
                        st.metric("Annual Savings", f"{savings:,.0f} kWh", f"{savings_percent:.1f}%")
                    
                    else:
                        st.info("📄 Post-renovation data not available")
                
                # Comparison chart if both files exist
                if os.path.exists(post_file_path):
                    st.markdown("#### 📊 Before vs After Comparison")
                    
                    fig3, ax3 = plt.subplots(figsize=(12, 6))
                    ax3.plot(time_months, heat_data, label="Pre-renovation", color='red', alpha=0.8)
                    ax3.plot(time_months_post, heat_post, label="Post-renovation", color='green', alpha=0.8)
                    ax3.set_xticks(np.arange(1, 13))
                    ax3.set_xticklabels([
                        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                    ])
                    ax3.set_xlabel("Month")
                    ax3.set_ylabel("Heating Power (W)")
                    ax3.set_title("Heating Power Comparison: Before vs After Renovation")
                    ax3.legend()
                    ax3.grid(True)
                    st.pyplot(fig3)
                    
            except Exception as e:
                st.error(f"Error loading energy data: {str(e)}")
                st.info("Make sure the buildingspy library is installed: `pip install buildingspy`")
        
        else:
            st.warning(f"No energy data found for building {target_building_id}")
            st.info(f"Expected file: {file_path}")
    
    # Footer
    st.markdown("---")
    st.markdown("**Building Analysis Dashboard** - Interactive map with detailed building information")

if __name__ == "__main__":
    main()