# your_streamlit_app.py
import streamlit as st
import geopandas as gpd
import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account
import tempfile
import os

# Page configuration
st.set_page_config(
    page_title="Building Renovation Passport", 
    page_icon="🏠",
    layout="wide"
)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_shapefile_from_gcs():
    """Load shapefile from Google Cloud Storage using Streamlit secrets"""
    
    try:
        # Create credentials from Streamlit secrets
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        
        # Initialize GCS client
        client = storage.Client(credentials=credentials)
        bucket = client.bucket("renodat")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Download all shapefile components
        extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.qmd']
        downloaded_files = []
        
        st.write("📥 Downloading shapefile components...")
        progress_bar = st.progress(0)
        
        for i, ext in enumerate(extensions):
            blob_name = f"shpp/u{ext}"
            blob = bucket.blob(blob_name)
            
            if blob.exists():
                local_path = os.path.join(temp_dir, f"u{ext}")
                blob.download_to_filename(local_path)
                downloaded_files.append(local_path)
                st.write(f"✅ Downloaded: {blob_name}")
            
            progress_bar.progress((i + 1) / len(extensions))
        
        # Read the shapefile
        shp_file = os.path.join(temp_dir, "u.shp")
        
        if os.path.exists(shp_file):
            gdf = gpd.read_file(shp_file)
            st.success(f"✅ Successfully loaded shapefile with {len(gdf)} features")
            return gdf
        else:
            st.error("❌ Shapefile (.shp) not found")
            return None
            
    except Exception as e:
        st.error(f"❌ Error loading shapefile: {e}")
        return None

def main():
    st.title("🏠 Building Renovation Passport Dashboard")
    st.markdown("*Data from Google Cloud Storage*")
    
    # Sidebar
    st.sidebar.header("📊 Controls")
    
    # Load the shapefile
    with st.spinner("Loading data from Google Cloud Storage..."):
        gdf = load_shapefile_from_gcs()
    
    if gdf is None:
        st.error("Failed to load data from GCS")
        st.stop()
    
    # Display basic information
    st.sidebar.success(f"✅ Loaded {len(gdf)} features")
    
    if len(gdf) > 0:
        st.sidebar.info(f"📐 Geometry: {gdf.geometry.geom_type.iloc[0]}")
        st.sidebar.info(f"🗺️ CRS: {gdf.crs}")
        
        # Show bounds
        bounds = gdf.total_bounds
        st.sidebar.write("**Geographic Bounds:**")
        st.sidebar.write(f"Min X: {bounds[0]:.6f}")
        st.sidebar.write(f"Min Y: {bounds[1]:.6f}")
        st.sidebar.write(f"Max X: {bounds[2]:.6f}")
        st.sidebar.write(f"Max Y: {bounds[3]:.6f}")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["🗺️ Map", "📊 Data", "📈 Analysis"])
    
    with tab1:
        st.subheader("Interactive Map")
        
        try:
            import folium
            from streamlit_folium import st_folium
            
            if len(gdf) > 0:
                # Create map
                bounds = gdf.total_bounds
                center_lat = (bounds[1] + bounds[3]) / 2
                center_lon = (bounds[0] + bounds[2]) / 2
                
                m = folium.Map(
                    location=[center_lat, center_lon],
                    zoom_start=10
                )
                
                # Add shapefile to map
                folium.GeoJson(
                    gdf.to_json(),
                    style_function=lambda feature: {
                        'fillColor': 'blue',
                        'color': 'black',
                        'weight': 2,
                        'fillOpacity': 0.6,
                    }
                ).add_to(m)
                
                # Display map
                st_folium(m, width=700, height=500)
            else:
                st.warning("No geographic data to display")
                
        except ImportError:
            st.warning("Install folium and streamlit-folium for map visualization")
            st.code("pip install folium streamlit-folium")
    
    with tab2:
        st.subheader("Attribute Data")
        
        # Show data table (without geometry for better display)
        if 'geometry' in gdf.columns:
            display_df = gdf.drop('geometry', axis=1)
        else:
            display_df = gdf
        
        if len(display_df) > 0:
            st.dataframe(display_df, use_container_width=True)
            
            # Download buttons
            col1, col2 = st.columns(2)
            
            with col1:
                csv_data = display_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv_data,
                    file_name="building_data.csv",
                    mime="text/csv"
                )
            
            with col2:
                if 'geometry' in gdf.columns:
                    geojson_data = gdf.to_json()
                    st.download_button(
                        label="📥 Download as GeoJSON",
                        data=geojson_data,
                        file_name="building_data.geojson",
                        mime="application/json"
                    )
        else:
            st.info("No attribute data available")
    
    with tab3:
        st.subheader("Data Analysis")
        
        if len(gdf) > 0:
            # Basic statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Features", len(gdf))
                st.metric("Total Columns", len(gdf.columns))
            
            with col2:
                if 'geometry' in gdf.columns:
                    # Calculate area if polygon
                    if gdf.geometry.geom_type.iloc[0] in ['Polygon', 'MultiPolygon']:
                        gdf_area = gdf.copy()
                        gdf_area['area'] = gdf_area.geometry.area
                        total_area = gdf_area['area'].sum()
                        st.metric("Total Area", f"{total_area:.2f}")
            
            # Show column info
            st.write("**Column Information:**")
            for col in gdf.columns:
                if col != 'geometry':
                    dtype = gdf[col].dtype
                    non_null = gdf[col].count()
                    st.write(f"• **{col}**: {dtype} ({non_null}/{len(gdf)} non-null)")
        else:
            st.info("No data to analyze")

if __name__ == "__main__":
    main()