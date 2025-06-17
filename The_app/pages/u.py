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
import shutil
import traceback

# Set page configuration
st.set_page_config(
    page_title="Building Map Dashboard",
    page_icon="🗺️",
    layout="wide"
)

##################################################
# Improved Function to download file from GCS
@st.cache_data
def download_file_from_gcs(blob_name):
    """Download file from Google Cloud Storage to temporary location with better error handling"""
    try:
        blob = bucket.blob(blob_name)
        
        # Check if blob exists
        if not blob.exists():
            st.error(f"File {blob_name} does not exist in GCS bucket")
            return None
        
        # Get blob info
        blob.reload()  # Refresh blob metadata
        st.info(f"Found blob: {blob_name}, Size: {blob.size} bytes")
        
        # Create temp directory and file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, os.path.basename(blob_name))
        
        # Download the blob
        with open(temp_file_path, 'wb') as f:
            blob.download_to_file(f)
        
        # Verify download
        if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 0:
            
            return temp_file_path
        else:
            st.error("File download failed or file is empty")
            return None
            
    except Exception as e:
        st.error(f"Error downloading {blob_name}: {str(e)}")
        st.error(f"Error type: {type(e).__name__}")
        st.error(f"Full traceback: {traceback.format_exc()}")
        return None

#################################################
# Initialize GCS client and bucket
try:
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    bucket_name = "renodat"
    client = storage.Client(credentials=credentials)
    bucket = client.bucket(bucket_name)
    st.sidebar.success(f"✅ Connected to GCS bucket: {bucket_name}")
except Exception as e:
    st.sidebar.error(f"❌ Failed to connect to GCS: {str(e)}")
    st.stop()

def load_shapefile_from_gcs(blob_prefix, bucket):
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
                st.info(f"Downloaded {blob_name}")
            else:
                st.warning(f"Shapefile component {blob_name} not found")
        
        # Load the shapefile
        shp_path = os.path.join(temp_dir, "temp.shp")
        if not os.path.exists(shp_path):
            st.error("Main shapefile (.shp) not found")
            return None
            
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

def get_building_ids(mat_blobs):
    """Get building IDs from .mat files"""
    mat_files = [blob.name for blob in mat_blobs if blob.name.endswith(".mat")]
    building_ids = [f.replace("_result.mat", "").replace("NL_Building_", "NL.IMBAG.Pand.") for f in mat_files]
    return building_ids, mat_files

def load_json_from_gcs(blob_name, bucket):
    """Load JSON file from GCS bucket"""
    try:
        blob_name = f"{blob_name}.json"
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            st.error(f"JSON file {blob_name} does not exist in bucket")
            return None
            
        json_string = blob.download_as_text()
        data = json.loads(json_string)
        
        return data
    except Exception as e:
        st.error(f"Error loading JSON from {blob_name}: {str(e)}")
        return None

# Main App
def main():
    st.title("🗺️ Building Analysis Dashboard")
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["🗺️ Building Map", "📊 Energy Analysis"])
    
    with tab1:
        st.subheader("🗺️ Building Map Analysis")
        
        # Load shapefile from GCS
        try:
            gdf = load_shapefile_from_gcs("shpp/u", bucket)
        except Exception as e:
            st.error(f"Error loading shapefile: {str(e)}")
            gdf = None
        
        if gdf is not None:
            # Load building information JSON file
            building_data = load_json_from_gcs("for_teaser", bucket)
            
            # Get .mat files for building analysis
            try:
                mat_blobs = client.list_blobs(bucket, prefix="simulation/")
                building_ids, mat_files = get_building_ids(mat_blobs)
                clean_building_ids = [bid.split('/')[-1] for bid in building_ids]
                
                # Filter only buildings that have corresponding .mat results
                filtered_gdf = gdf[gdf["object_id_clean"].isin(clean_building_ids)]
                st.info(f"Found {len(filtered_gdf)} buildings with simulation results out of {len(gdf)} total buildings")
                
            except Exception as e:
                st.error(f"Error loading building simulation data: {str(e)}")
                filtered_gdf = gdf
            
            # Create layout with map and building info
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("🗺️ Interactive Building Map")
                
                # Display map using pydeck
                geojson = gdf.__geo_interface__
                
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
        
        else:
            st.error("❌ Failed to load shapefile from Google Cloud Storage")
    
    with tab2:
        st.subheader("📊 Heat Consumption Analysis")
        
        # Debug: List available blobs
        with st.expander("🔍 Debug: Available files in simulation/"):
            try:
                mat_blobs_list = list(client.list_blobs(bucket, prefix="simulation/"))
                st.write(f"Total files found: {len(mat_blobs_list)}")
                
                for i, blob in enumerate(mat_blobs_list[:10]):  # Show first 10
                    st.write(f"{i+1}. {blob.name} ({blob.size} bytes)")
                
                if len(mat_blobs_list) > 10:
                    st.write(f"... and {len(mat_blobs_list) - 10} more files")
                    
            except Exception as e:
                st.error(f"Error listing blobs: {str(e)}")

        # Find the specific file for pre-renovation
        building_id = "0503100000019674"
        target_filename = f"{building_id}_result.mat"

        try:
            # Filter to find your specific file
            mat_blobs_list = list(client.list_blobs(bucket, prefix="simulation/"))
            matching_blobs = [blob for blob in mat_blobs_list if blob.name.endswith(target_filename)]

            if matching_blobs:
                file_blob = matching_blobs[0]
                
                
                # Download the file to local temp location
                pre_file_path = download_file_from_gcs(file_blob.name)
                
                if pre_file_path and os.path.exists(pre_file_path):
                    try:
                        # Try to import buildingspy
                        try:
                            from buildingspy.io.outputfile import Reader
                        except ImportError:
                            st.error("❌ buildingspy library not found. Install it with: `pip install buildingspy`")
                            st.info("Alternative: You can manually install it in your environment")
                            return
                        
                        # Load .mat file
                        st.info(f"📂 Loading .mat file from: {os.path.basename(pre_file_path)}")
                        r = Reader(pre_file_path, "dymola")
                        
                        # Get available variables first for debugging
                        with st.expander("🔍 Debug: .mat file analysis"):
                            st.write("✅ File loaded successfully with buildingspy Reader")
                            st.write(f"📊 Attempting to read heating power data from variable: 'multizone.PHeater[1]'")
                        
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
                            ax.plot(time_months, heat_data, label="Pre-renovation", color='red', linewidth=2)
                            ax.set_xticks(np.arange(1, 13))
                            ax.set_xticklabels([
                                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                            ])
                            ax.set_xlabel("Month")
                            ax.set_ylabel("Heating Power (W)")
                            ax.set_title("Pre-Renovation Heating Power")
                            ax.legend()
                            ax.grid(True, alpha=0.3)
                            plt.tight_layout()
                            st.pyplot(fig)
                            
                            # Calculate and display metrics
                            total_consumption = np.trapz(heat_data, time) / 3600000  # Convert to kWh
                            max_power = np.max(heat_data)
                            avg_power = np.mean(heat_data)
                            
                            st.metric("Total Annual Consumption", f"{total_consumption:,.0f} kWh")
                            st.metric("Peak Power", f"{max_power:,.0f} W")
                            st.metric("Average Power", f"{avg_power:,.0f} W")
                        
                        with col2:
                            # Find the post-renovation file
                            post_building_id = "0503100000013392"
                            post_target_filename = f"{post_building_id}_result.mat"

                            # Filter to find post-renovation file
                            post_matching_blobs = [blob for blob in mat_blobs_list if blob.name.endswith(post_target_filename)]

                            if post_matching_blobs:
                                post_file_blob = post_matching_blobs[0]
                                
                                
                                # Download the post-renovation file
                                post_file_path = download_file_from_gcs(post_file_blob.name)
                                
                                if post_file_path and os.path.exists(post_file_path):
                                    try:
                                        # Load post-renovation data
                                        r_post = Reader(post_file_path, "dymola")
                                        time_post, heat_post = r_post.values('multizone.PHeater[1]')
                                        time_months_post = time_post / seconds_per_month
                                        
                                        # Plot post-renovation heating
                                        fig2, ax2 = plt.subplots(figsize=(8, 5))
                                        ax2.plot(time_months_post, heat_post, label="Post-renovation", color='green', linewidth=2)
                                        ax2.set_xticks(np.arange(1, 13))
                                        ax2.set_xticklabels([
                                            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                                        ])
                                        ax2.set_xlabel("Month")
                                        ax2.set_ylabel("Heating Power (W)")
                                        ax2.set_title("Post-Renovation Heating Power")
                                        ax2.legend()
                                        ax2.grid(True, alpha=0.3)
                                        plt.tight_layout()
                                        st.pyplot(fig2)
                                        
                                        # Calculate post-renovation metrics
                                        total_consumption_post = np.trapz(heat_post, time_post) / 3600000
                                        max_power_post = np.max(heat_post)
                                        avg_power_post = np.mean(heat_post)
                                        
                                        # Calculate savings
                                        savings = total_consumption - total_consumption_post
                                        savings_percent = (savings / total_consumption) * 100 if total_consumption > 0 else 0
                                        
                                        st.metric("Total Annual Consumption", f"{total_consumption_post:,.0f} kWh")
                                        st.metric("Peak Power", f"{max_power_post:,.0f} W")
                                        st.metric("Average Power", f"{avg_power_post:,.0f} W")
                                        st.metric("Annual Savings", f"{savings:,.0f} kWh", f"{savings_percent:.1f}%")
                                        
                                    except Exception as e:
                                        st.error(f"Error processing post-renovation data: {str(e)}")
                                    finally:
                                        # Clean up post-renovation temp file
                                        try:
                                            if post_file_path:
                                                os.unlink(post_file_path)
                                                temp_dir = os.path.dirname(post_file_path)
                                                if temp_dir.startswith('/tmp'):
                                                    shutil.rmtree(temp_dir, ignore_errors=True)
                                        except:
                                            pass
                                else:
                                    st.error("❌ Failed to download or access post-renovation file")
                            else:
                                st.info("📄 Post-renovation data not available for comparison")
                                
                        # Comparison chart if both files exist
                        if 'heat_post' in locals():
                            st.markdown("#### 📊 Before vs After Comparison")
                            
                            fig3, ax3 = plt.subplots(figsize=(12, 6))
                            ax3.plot(time_months, heat_data, label="Pre-renovation", color='red', alpha=0.8, linewidth=2)
                            ax3.plot(time_months_post, heat_post, label="Post-renovation", color='green', alpha=0.8, linewidth=2)
                            ax3.set_xticks(np.arange(1, 13))
                            ax3.set_xticklabels([
                                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                            ])
                            ax3.set_xlabel("Month")
                            ax3.set_ylabel("Heating Power (W)")
                            ax3.set_title("Heating Power Comparison: Before vs After Renovation")
                            ax3.legend()
                            ax3.grid(True, alpha=0.3)
                            plt.tight_layout()
                            st.pyplot(fig3)
                            
                            # Summary metrics
                            col_summary1, col_summary2, col_summary3 = st.columns(3)
                            with col_summary1:
                                st.metric("Energy Savings", f"{savings:,.0f} kWh/year")
                            with col_summary2:
                                st.metric("Percentage Reduction", f"{savings_percent:.1f}%")
                            with col_summary3:
                                peak_reduction = ((max_power - max_power_post) / max_power * 100) if max_power > 0 else 0
                                st.metric("Peak Power Reduction", f"{peak_reduction:.1f}%")
                            
                    except Exception as e:
                        st.error(f"❌ Error processing energy data: {str(e)}")
                        st.error(f"Full error details: {traceback.format_exc()}")
                    finally:
                        # Clean up temporary file
                        try:
                            if pre_file_path:
                                os.unlink(pre_file_path)
                                temp_dir = os.path.dirname(pre_file_path)
                                if temp_dir.startswith('/tmp'):
                                    shutil.rmtree(temp_dir, ignore_errors=True)
                        except Exception as cleanup_error:
                            st.warning(f"Could not clean up temporary file: {cleanup_error}")
                else:
                    st.error("❌ Failed to download pre-renovation file from GCS")
            else:
                st.warning(f"📂 No energy data found for building {building_id}")
                st.info(f"Expected file pattern: *{target_filename}")
                
                # Show what files are actually available
                available_files = [blob.name for blob in mat_blobs_list if blob.name.endswith('.mat')][:10]
                if available_files:
                    st.info("Available .mat files (first 10):")
                    for file in available_files:
                        st.write(f"- {file}")
                        
        except Exception as e:
            st.error(f"❌ Error in energy analysis: {str(e)}")
            st.error(f"Full traceback: {traceback.format_exc()}")
    
    # Footer
    st.markdown("---")
    st.markdown("**Building Analysis Dashboard** - Interactive map with detailed building information and energy analysis")
    
    # Sidebar info
    with st.sidebar:
        st.markdown("### 📊 Dashboard Info")
        st.info("This dashboard analyzes building data from Google Cloud Storage, including:")
        st.markdown("- 🗺️ Interactive building maps")
        st.markdown("- 🏢 Building details and metadata") 
        st.markdown("- 📈 Energy consumption analysis")
        st.markdown("- 🔄 Before/after renovation comparisons")

if __name__ == "__main__":
    main()