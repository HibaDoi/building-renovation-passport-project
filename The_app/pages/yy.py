import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import os
from buildingspy.io.outputfile import Reader
import seaborn as sns
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import storage
from google.oauth2 import service_account
import tempfile
import os

# 🎨 Page Configuration
st.set_page_config(
    page_title="Unified Building Analytics",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
# Initialize GCS client
client = storage.Client(credentials=credentials)
bucket = client.bucket("renodat")
mat_blobs = client.list_blobs(
    bucket,
    prefix="simulation/",
)

# 🎨 Clean white theme CSS
st.markdown("""
<style>
    /* CSS Variables for white theme */
    :root {
        --primary-color: #4A90E2;
        --secondary-color: #7ED321;
        --accent-color: #F5A623;
        --danger-color: #D0021B;
        --text-primary: #2C3E50;
        --text-secondary: #7F8C8D;
        --text-muted: #95A5A6;
        --bg-primary: #FFFFFF;
        --bg-secondary: #F8F9FA;
        --bg-tertiary: #E9ECEF;
        --border-color: #DEE2E6;
        --shadow-sm: 0 2px 4px rgba(0,0,0,0.08);
        --shadow-md: 0 4px 8px rgba(0,0,0,0.1);
        --shadow-lg: 0 8px 16px rgba(0,0,0,0.15);
    }
    
    /* Main app background */
    .stApp {
        background-color: var(--bg-secondary);
    }
    
    /* Main content area */
    .main {
        padding: 0;
        background-color: var(--bg-secondary);
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-tertiary);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 10px;
    }
    
    /* Dashboard container */
    .dashboard-container {
        background: var(--bg-primary);
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
    }
    
    /* Dashboard title */
    .dashboard-title {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin: 2rem 0 3rem 0;
        color: var(--text-primary);
        position: relative;
    }
    
    .dashboard-title::after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        border-radius: 2px;
    }
    
    /* Metric cards */
    .metric-card {
        background: var(--bg-primary);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem;
        border: 1px solid var(--border-color);
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        box-shadow: var(--shadow-sm);
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
        border-color: var(--primary-color);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--primary-color);
        margin: 0.5rem 0;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 500;
    }
    
    /* Info boxes */
    .info-box {
        background: var(--bg-primary);
        color: var(--text-primary);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        position: relative;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-color);
        border-left: 4px solid var(--primary-color);
    }
    
    .info-box h4 {
        color: var(--text-primary);
        margin-bottom: 0.75rem;
        font-size: 1.2rem;
        font-weight: 600;
    }
    
    .info-box p {
        margin: 0.5rem 0;
        color: var(--text-secondary);
        line-height: 1.6;
    }
    
    .info-box strong {
        color: var(--primary-color);
        font-weight: 600;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-primary);
        border-right: 1px solid var(--border-color);
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding: 2rem 1rem;
    }
    
    /* Sidebar headers */
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-tertiary);
        border-radius: 8px;
        padding: 4px;
        gap: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-secondary);
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--bg-primary);
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--bg-primary);
        color: var(--primary-color);
        box-shadow: var(--shadow-sm);
    }
    
    /* Buttons */
    .stButton > button {
        background: var(--primary-color);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
    }
    
    .stButton > button:hover {
        background: #357ABD;
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }
    
    /* Select boxes and inputs */
    .stSelectbox > div > div, 
    .stMultiSelect > div > div {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
    }
    
    /* Radio buttons */
    .stRadio > div {
        background: var(--bg-tertiary);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
    
    /* Checkbox */
    .stCheckbox {
        color: var(--text-primary);
    }
    
    /* Dataframe */
    .dataframe {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Headers and text */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
    }
    
    p {
        color: var(--text-secondary);
    }
    
    /* Metrics in Streamlit */
    [data-testid="metric-container"] {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        padding: 1rem;
        border-radius: 8px;
        box-shadow: var(--shadow-sm);
    }
    
    /* Success/Error/Warning/Info boxes */
    .stAlert {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }
    
    /* Plotly charts background */
    .js-plotly-plot {
        background: var(--bg-primary);
        border-radius: 8px;
        box-shadow: var(--shadow-sm);
    }
</style>
""", unsafe_allow_html=True)

# 🏢 Dashboard Header
st.markdown('<h1 class="dashboard-title">🏢 Unified Building Performance Dashboard</h1>', unsafe_allow_html=True)

# Function to download file from GCS
@st.cache_data
def download_file_from_gcs(blob_name):
    """Download file from Google Cloud Storage to temporary location"""
    try:
        blob = bucket.blob(blob_name)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mat')
        blob.download_to_filename(temp_file.name)
        return temp_file.name
    except Exception as e:
        st.error(f"Error downloading {blob_name}: {str(e)}")
        return None

# Function to load building data
@st.cache_data
def load_building_data(file_path):
    """Load and process building simulation data"""
    try:
        r = Reader(file_path, "dymola")
        
        time, heat_power = r.values('multizone.PHeater[1]')
        time_temp, indoor_temp = r.values('multizone.TAir[1]')
        
        seconds_per_year = 365 * 24 * 3600
        seconds_per_month = seconds_per_year / 12.0
        time_months = time / seconds_per_month
        time_months_temp = time_temp / seconds_per_month
        
        if indoor_temp.max() > 100:
            indoor_temp = indoor_temp - 273.15
        
        df = pd.DataFrame({
            'Time_Months': time_months,
            'Heating_Power': heat_power,
            'Indoor_Temperature': np.interp(time_months, time_months_temp, indoor_temp)
        })
        
        return df, {
            'max_power': heat_power.max(),
            'avg_power': heat_power.mean(),
            'min_power': heat_power.min(),
            'annual_consumption': np.trapz(heat_power, time) / 3600 / 1000,
            'max_temp': indoor_temp.max(),
            'avg_temp': indoor_temp.mean(),
            'min_temp': indoor_temp.min(),
            'temp_range': indoor_temp.max() - indoor_temp.min()
        }
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

# Define clean color palettes for white background
CHART_COLORS = {
    'primary': ['#4A90E2', '#357ABD', '#1E5A8D', '#0F3F70'],
    'secondary': ['#7ED321', '#5FB304', '#4A8F00', '#366B00'],
    'accent': ['#F5A623', '#E09514', '#CC8400', '#B37300'],
    'mixed': ['#4A90E2', '#7ED321', '#F5A623', '#E94B3C', '#9B59B6']
}

# Plotly layout template for white background
def get_plot_layout(title="", height=400, is_subplot=False):
    layout = dict(
        height=height,
        margin=dict(l=60, r=30, t=60, b=40),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(color='#2C3E50', size=12, family='Arial, sans-serif'),
        legend=dict(
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#DEE2E6',
            borderwidth=1,
            font=dict(color='#2C3E50')
        ),
        hoverlabel=dict(
            bgcolor='white',
            font_size=14,
            font_family="Arial, sans-serif",
            font_color='#2C3E50',
            bordercolor='#DEE2E6'
        )
    )
    
    # Only add title if provided and not a subplot
    if title and not is_subplot:
        layout['title'] = dict(
            text=title,
            font=dict(size=18, color='#2C3E50', family='Arial, sans-serif'),
            x=0.5,
            xanchor='center'
        )
    
    # Only add axis properties if not a subplot
    if not is_subplot:
        layout['xaxis'] = dict(
            gridcolor='#E9ECEF',
            zerolinecolor='#DEE2E6',
            tickfont=dict(color='#2C3E50'),
            titlefont=dict(color='#2C3E50')
        )
        layout['yaxis'] = dict(
            gridcolor='#E9ECEF',
            zerolinecolor='#DEE2E6',
            tickfont=dict(color='#2C3E50'),
            titlefont=dict(color='#2C3E50')
        )
    
    return layout

# 📊 Sidebar Configuration
with st.sidebar:
    st.markdown("## 🎛️ Control Panel")
    
    # Building selection
    st.markdown("### 🏢 Building Selection")
    
    mat_files = [blob.name for blob in mat_blobs if blob.name.endswith(".mat")]

    if mat_files:
        # Create building mapping
        building_mapping = {}
        for file in mat_files:
            filename = os.path.basename(file)
            building_name = filename.replace('.mat', '').replace('_', ' ').title()
            building_mapping[building_name] = file
        
        # Analysis mode selection
        analysis_mode = st.radio(
            "📊 Analysis Mode",
            ["Single Building", "Compare Buildings", "All Buildings"],
            help="Choose your analysis approach"
        )
        
        if analysis_mode == "Single Building":
            selected_building = st.selectbox(
                "Choose a building:",
                list(building_mapping.keys()),
                help="Select one building to analyze in detail"
            )
            selected_buildings = [selected_building]
            
        elif analysis_mode == "Compare Buildings":
            selected_buildings = st.multiselect(
                "Select buildings to compare:",
                list(building_mapping.keys()),
                default=list(building_mapping.keys())[:2] if len(building_mapping) >= 2 else list(building_mapping.keys()),
                help="Choose 2-4 buildings for comparison"
            )
            
            if len(selected_buildings) > 4:
                st.warning("⚠️ Maximum 4 buildings for comparison")
                selected_buildings = selected_buildings[:4]
                
        else:  # All Buildings
            selected_buildings = list(building_mapping.keys())
            st.info(f"📊 Analyzing all {len(selected_buildings)} buildings")
        
        selected_files = [building_mapping[building] for building in selected_buildings]
        
    else:
        st.error("❌ No .mat files found!")
        selected_files = []
        selected_buildings = []
    
    st.markdown("---")
    
    # Visualization options
    st.markdown("### 🎨 Visualization Options")
    color_scheme = st.selectbox(
        "Color Scheme",
        ["Professional Blue", "Nature Green", "Warm Orange", "Mixed Colors"],
        index=0
    )
    
    color_map = {
        "Professional Blue": CHART_COLORS['primary'],
        "Nature Green": CHART_COLORS['secondary'],
        "Warm Orange": CHART_COLORS['accent'],
        "Mixed Colors": CHART_COLORS['mixed']
    }
    
    selected_colors = color_map[color_scheme]
    
    chart_height = st.slider("Chart Height", 300, 700, 450, step=50)
    show_animations = st.checkbox("Enable Animations", value=True)
    show_grid = st.checkbox("Show Grid Lines", value=True)

# Main dashboard content
if selected_files:
    # Load data for all selected buildings
    building_data = {}
    building_stats = {}
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, file in enumerate(selected_files):
        building_name = selected_buildings[i]
        
        status_text.text(f"🔄 Loading {building_name}...")
        progress_bar.progress((i + 1) / len(selected_files))
        
        # Download file from GCS
        local_file_path = download_file_from_gcs(file)
        
        if local_file_path:
            data, stats = load_building_data(local_file_path)
            if data is not None:
                building_data[building_name] = data
                building_stats[building_name] = stats
            
            # Clean up temporary file
            try:
                os.unlink(local_file_path)
            except:
                pass
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    if building_data:
        # OVERVIEW METRICS
        st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
        
        # Dynamic header
        if len(selected_buildings) == 1:
            st.markdown(f"## 🏢 {selected_buildings[0]} - Performance Analysis")
        else:
            st.markdown(f"## 📊 Portfolio Overview - {len(selected_buildings)} Buildings")
        
        # Metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total_buildings = len(building_data)
        total_consumption = sum(stats['annual_consumption'] for stats in building_stats.values())
        avg_consumption = total_consumption / total_buildings if total_buildings > 0 else 0
        peak_demand = max(stats['max_power'] for stats in building_stats.values()) if building_stats else 0
        avg_temp = np.mean([stats['avg_temp'] for stats in building_stats.values()]) if building_stats else 0
        
        metrics = [
            (col1, total_buildings, "Buildings", "🏢"),
            (col2, f"{total_consumption:,.0f}", "Total kWh", "⚡"),
            (col3, f"{avg_consumption:,.0f}", "Avg kWh", "📊"),
            (col4, f"{peak_demand:,.0f}", "Peak W", "📈"),
            (col5, f"{avg_temp:.1f}°C", "Avg Temp", "🌡️")
        ]
        
        for col, value, label, icon in metrics:
            with col:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">{icon} {label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # MAIN CONTENT TABS
        if len(selected_buildings) == 1:
            tabs = st.tabs(["📈 Performance", "📊 Analytics", "💡 Insights", "📅 Monthly"])
        else:
            tabs = st.tabs(["📈 Overview", "🔄 Comparison", "📊 Analytics", "🏆 Rankings"])
        
        # Single Building Analysis
        if len(selected_buildings) == 1:
            building_name = selected_buildings[0]
            data = building_data[building_name]
            stats = building_stats[building_name]
            
            with tabs[0]:  # Performance
                st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
                
                # Create subplots
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('Heating Power Consumption', 'Indoor Temperature'),
                    vertical_spacing=0.15,
                    row_heights=[0.5, 0.5]
                )
                
                # Power consumption
                fig.add_trace(
                    go.Scatter(
                        x=data['Time_Months'],
                        y=data['Heating_Power'],
                        mode='lines',
                        name='Power',
                        line=dict(color=selected_colors[0], width=3),
                        fill='tozeroy',
                        fillcolor=f'rgba({int(selected_colors[0][1:3], 16)}, {int(selected_colors[0][3:5], 16)}, {int(selected_colors[0][5:7], 16)}, 0.1)'
                    ),
                    row=1, col=1
                )
                
                # Temperature
                fig.add_trace(
                    go.Scatter(
                        x=data['Time_Months'],
                        y=data['Indoor_Temperature'],
                        mode='lines',
                        name='Temperature',
                        line=dict(color=selected_colors[1], width=3)
                    ),
                    row=2, col=1
                )
                
                # Add comfort zone
                fig.add_hrect(y0=20, y1=24, 
                            fillcolor="rgba(126, 211, 33, 0.1)", 
                            line_width=0,
                            row=2, col=1)
                
                # Update layout
                fig.update_xaxes(
                    tickvals=list(range(1, 13)),
                    ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)'
                )
                
                fig.update_yaxes(
                    gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)'
                )
                
                layout = get_plot_layout(f"{building_name} - Annual Performance", chart_height * 1.5, is_subplot=True)
                fig.update_layout(**layout)
                fig.update_layout(
                    title=dict(
                        text=f"{building_name} - Annual Performance",
                        font=dict(size=18, color='#2C3E50', family='Arial, sans-serif'),
                        x=0.5,
                        xanchor='center'
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tabs[1]:  # Analytics
                st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Scatter plot
                    fig_scatter = px.scatter(
                        data,
                        x='Indoor_Temperature',
                        y='Heating_Power',
                        color='Time_Months',
                        title='Temperature vs Power Correlation',
                        labels={'Indoor_Temperature': 'Temperature (°C)', 'Heating_Power': 'Power (W)'},
                        color_continuous_scale=['#E8F4FD', '#4A90E2']
                    )
                    
                    # Update layout for Plotly Express figure
                    fig_scatter.update_layout(
                        height=chart_height,
                        paper_bgcolor='white',
                        plot_bgcolor='white',
                        font=dict(color='#2C3E50', size=12, family='Arial, sans-serif'),
                        title=dict(
                            font=dict(size=18, color='#2C3E50', family='Arial, sans-serif'),
                            x=0.5,
                            xanchor='center'
                        ),
                        legend=dict(
                            bgcolor='rgba(255,255,255,0.9)',
                            bordercolor='#DEE2E6',
                            borderwidth=1,
                            font=dict(color='#2C3E50')
                        ),
                        hoverlabel=dict(
                            bgcolor='white',
                            font_size=14,
                            font_family="Arial, sans-serif",
                            font_color='#2C3E50',
                            bordercolor='#DEE2E6'
                        )
                    )
                    
                    # Update axes separately
                    fig_scatter.update_xaxes(
                        gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)',
                        zerolinecolor='#DEE2E6',
                        tickfont=dict(color='#2C3E50'),
                        title=dict(font=dict(color='#2C3E50'))
                    )
                    fig_scatter.update_yaxes(
                        gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)',
                        zerolinecolor='#DEE2E6',
                        tickfont=dict(color='#2C3E50'),
                        title=dict(font=dict(color='#2C3E50'))
                    )
                    
                    fig_scatter.update_traces(marker=dict(size=8, opacity=0.7))
                    
                    st.plotly_chart(fig_scatter, use_container_width=True)
                
                with col2:
                    # Distribution plot
                    fig_dist = go.Figure()
                    
                    fig_dist.add_trace(go.Histogram(
                        x=data['Heating_Power'],
                        name='Power Distribution',
                        marker_color=selected_colors[0],
                        opacity=0.7,
                        nbinsx=30
                    ))
                    
                    # Update layout directly
                    fig_dist.update_layout(
                        title=dict(
                            text='Power Distribution',
                            font=dict(size=18, color='#2C3E50', family='Arial, sans-serif'),
                            x=0.5,
                            xanchor='center'
                        ),
                        height=chart_height,
                        paper_bgcolor='white',
                        plot_bgcolor='white',
                        font=dict(color='#2C3E50', size=12, family='Arial, sans-serif'),
                        xaxis_title='Power (W)',
                        yaxis_title='Frequency',
                        legend=dict(
                            bgcolor='rgba(255,255,255,0.9)',
                            bordercolor='#DEE2E6',
                            borderwidth=1,
                            font=dict(color='#2C3E50')
                        ),
                        hoverlabel=dict(
                            bgcolor='white',
                            font_size=14,
                            font_family="Arial, sans-serif",
                            font_color='#2C3E50',
                            bordercolor='#DEE2E6'
                        )
                    )
                    
                    # Update axes
                    fig_dist.update_xaxes(
                        gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)',
                        zerolinecolor='#DEE2E6',
                        tickfont=dict(color='#2C3E50'),
                        titlefont=dict(color='#2C3E50')
                    )
                    fig_dist.update_yaxes(
                        gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)',
                        zerolinecolor='#DEE2E6',
                        tickfont=dict(color='#2C3E50'),
                        titlefont=dict(color='#2C3E50')
                    )
                    
                    st.plotly_chart(fig_dist, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tabs[2]:  # Insights
                st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
                
                # Key insights
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f'''
                    <div class="info-box">
                        <h4>🔥 Energy Performance</h4>
                        <p>• Annual Consumption: <strong>{stats['annual_consumption']:,.0f} kWh</strong></p>
                        <p>• Peak Demand: <strong>{stats['max_power']:,.0f} W</strong></p>
                        <p>• Average Load: <strong>{stats['avg_power']:,.0f} W</strong></p>
                        <p>• Load Factor: <strong>{(stats['avg_power']/stats['max_power']*100):.1f}%</strong></p>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f'''
                    <div class="info-box">
                        <h4>🌡️ Thermal Performance</h4>
                        <p>• Average Temperature: <strong>{stats['avg_temp']:.1f}°C</strong></p>
                        <p>• Temperature Range: <strong>{stats['temp_range']:.1f}°C</strong></p>
                        <p>• Min Temperature: <strong>{stats['min_temp']:.1f}°C</strong></p>
                        <p>• Max Temperature: <strong>{stats['max_temp']:.1f}°C</strong></p>
                    </div>
                    ''', unsafe_allow_html=True)
                
                # Efficiency metrics
                efficiency_score = (1 - (stats['annual_consumption'] / 50000)) * 100  # Assuming 50000 kWh as baseline
                comfort_score = 100 - (stats['temp_range'] * 2)  # Lower range = better comfort
                
                st.markdown(f'''
                <div class="info-box" style="margin-top: 2rem;">
                    <h4>🎯 Performance Scores</h4>
                    <p>• Energy Efficiency Score: <strong>{efficiency_score:.1f}/100</strong></p>
                    <p>• Thermal Comfort Score: <strong>{comfort_score:.1f}/100</strong></p>
                    <p>• Overall Rating: <strong>{(efficiency_score + comfort_score)/2:.1f}/100</strong></p>
                </div>
                ''', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tabs[3]:  # Monthly Analysis
                st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
                
                # Calculate monthly statistics
                monthly_data = []
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                for i in range(12):
                    month_start = i + 0.5
                    month_end = i + 1.5
                    mask = (data['Time_Months'] >= month_start) & (data['Time_Months'] < month_end)
                    if np.any(mask):
                        month_power = data[mask]['Heating_Power'].values
                        month_temp = data[mask]['Indoor_Temperature'].values
                        monthly_data.append({
                            'Month': months[i],
                            'Avg_Power': np.mean(month_power),
                            'Max_Power': np.max(month_power),
                            'Min_Power': np.min(month_power),
                            'Avg_Temp': np.mean(month_temp),
                            'Energy_kWh': np.trapz(month_power, dx=1) / 1000 * 24 * 30  # Approximate monthly energy
                        })
                
                monthly_df = pd.DataFrame(monthly_data)
                
                # Create monthly charts
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=('Monthly Energy Consumption', 'Monthly Average Power', 
                                   'Monthly Temperature', 'Power vs Temperature'),
                    specs=[[{"secondary_y": False}, {"type": "bar"}],
                           [{"secondary_y": False}, {"type": "scatter"}]],
                    vertical_spacing=0.15,
                    horizontal_spacing=0.12
                )
                
                # Monthly energy consumption
                fig.add_trace(
                    go.Bar(
                        x=monthly_df['Month'],
                        y=monthly_df['Energy_kWh'],
                        name='Energy',
                        marker_color=selected_colors[0],
                        marker_line_color='#2C3E50',
                        marker_line_width=1,
                        opacity=0.8
                    ),
                    row=1, col=1
                )
                
                # Monthly average power
                fig.add_trace(
                    go.Bar(
                        x=monthly_df['Month'],
                        y=monthly_df['Avg_Power'],
                        name='Avg Power',
                        marker_color=selected_colors[1],
                        marker_line_color='#2C3E50',
                        marker_line_width=1,
                        opacity=0.8
                    ),
                    row=1, col=2
                )
                
                # Monthly temperature
                fig.add_trace(
                    go.Scatter(
                        x=monthly_df['Month'],
                        y=monthly_df['Avg_Temp'],
                        mode='lines+markers',
                        name='Temperature',
                        line=dict(color=selected_colors[2], width=3),
                        marker=dict(size=10, color=selected_colors[2], 
                                   line=dict(color='#2C3E50', width=2))
                    ),
                    row=2, col=1
                )
                
                # Add comfort zone to temperature plot
                fig.add_hrect(y0=20, y1=24, 
                            fillcolor="rgba(126, 211, 33, 0.1)", 
                            line_width=0,
                            row=2, col=1)
                
                # Power vs Temperature scatter
                fig.add_trace(
                    go.Scatter(
                        x=monthly_df['Avg_Temp'],
                        y=monthly_df['Avg_Power'],
                        mode='markers+text',
                        name='Monthly Avg',
                        marker=dict(
                            size=monthly_df['Energy_kWh']/50,  # Size based on energy
                            color=list(range(12)),
                            colorscale=['#E8F4FD', '#4A90E2'],
                            showscale=True,
                            colorbar=dict(title="Month", thickness=15),
                            line=dict(color='#2C3E50', width=2)
                        ),
                        text=monthly_df['Month'],
                        textposition="top center"
                    ),
                    row=2, col=2
                )
                
                layout = get_plot_layout(f"{building_name} - Monthly Analysis", chart_height * 1.8, is_subplot=True)
                fig.update_layout(**layout)
                fig.update_layout(
                    title=dict(
                        text=f"{building_name} - Monthly Analysis",
                        font=dict(size=18, color='#2C3E50', family='Arial, sans-serif'),
                        x=0.5,
                        xanchor='center'
                    )
                )
                
                # Update axes
                fig.update_xaxes(gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)')
                fig.update_yaxes(gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)')
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Monthly summary table
                st.markdown("### 📊 Monthly Summary Statistics")
                monthly_display = monthly_df[['Month', 'Energy_kWh', 'Avg_Power', 'Avg_Temp']].copy()
                monthly_display['Energy_kWh'] = monthly_display['Energy_kWh'].round(0)
                monthly_display['Avg_Power'] = monthly_display['Avg_Power'].round(0)
                monthly_display['Avg_Temp'] = monthly_display['Avg_Temp'].round(1)
                
                st.dataframe(
                    monthly_display.style.background_gradient(
                        subset=['Energy_kWh', 'Avg_Power', 'Avg_Temp'],
                        cmap='Blues',
                        low=0.3,
                        high=0.7
                    ),
                    use_container_width=True
                )
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Multiple Buildings Analysis
        else:
            with tabs[0]:  # Overview
                st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
                
                # Create comparison charts
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=('Heating Power Profiles', 'Temperature Profiles', 
                                   'Annual Energy Consumption', 'Peak Power Demand'),
                    specs=[[{"secondary_y": False}, {"secondary_y": False}],
                           [{"type": "bar"}, {"type": "bar"}]],
                    vertical_spacing=0.15,
                    horizontal_spacing=0.12
                )
                
                # Power profiles
                for i, (building_name, data) in enumerate(building_data.items()):
                    fig.add_trace(
                        go.Scatter(
                            x=data['Time_Months'],
                            y=data['Heating_Power'],
                            mode='lines',
                            name=building_name,
                            line=dict(color=selected_colors[i % len(selected_colors)], width=2.5),
                            opacity=0.8
                        ),
                        row=1, col=1
                    )
                
                # Temperature profiles
                for i, (building_name, data) in enumerate(building_data.items()):
                    fig.add_trace(
                        go.Scatter(
                            x=data['Time_Months'],
                            y=data['Indoor_Temperature'],
                            mode='lines',
                            name=building_name,
                            line=dict(color=selected_colors[i % len(selected_colors)], width=2.5),
                            opacity=0.8,
                            showlegend=False
                        ),
                        row=1, col=2
                    )
                
                # Add comfort zone
                fig.add_hrect(y0=20, y1=24, 
                            fillcolor="rgba(126, 211, 33, 0.1)", 
                            line_width=0,
                            row=1, col=2)
                
                # Annual consumption bar chart
                consumption_data = [(name, stats['annual_consumption']) 
                                  for name, stats in building_stats.items()]
                consumption_data.sort(key=lambda x: x[1])
                
                fig.add_trace(
                    go.Bar(
                        x=[item[0] for item in consumption_data],
                        y=[item[1] for item in consumption_data],
                        name='Annual kWh',
                        marker=dict(
                            color=[item[1] for item in consumption_data],
                            colorscale=['#E8F4FD', '#4A90E2'],
                            line=dict(color='#2C3E50', width=1)
                        ),
                        showlegend=False
                    ),
                    row=2, col=1
                )
                
                # Peak power bar chart
                peak_data = [(name, stats['max_power']) 
                            for name, stats in building_stats.items()]
                peak_data.sort(key=lambda x: x[1])
                
                fig.add_trace(
                    go.Bar(
                        x=[item[0] for item in peak_data],
                        y=[item[1] for item in peak_data],
                        name='Peak Power',
                        marker=dict(
                            color=[item[1] for item in peak_data],
                            colorscale=['#FFE5B4', '#F5A623'],
                            line=dict(color='#2C3E50', width=1)
                        ),
                        showlegend=False
                    ),
                    row=2, col=2
                )
                
                # Update layout
                layout = get_plot_layout("Building Portfolio Overview", chart_height * 1.8, is_subplot=True)
                fig.update_layout(**layout)
                fig.update_layout(
                    title=dict(
                        text="Building Portfolio Overview",
                        font=dict(size=18, color='#2C3E50', family='Arial, sans-serif'),
                        x=0.5,
                        xanchor='center'
                    )
                )
                
                # Update x-axes for time series
                fig.update_xaxes(
                    tickvals=list(range(1, 13)),
                    ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    row=1, col=1
                )
                fig.update_xaxes(
                    tickvals=list(range(1, 13)),
                    ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    row=1, col=2
                )
                
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tabs[1]:  # Comparison
                st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
                
                # Create metrics comparison
                metrics_data = []
                for building_name, stats in building_stats.items():
                    metrics_data.append({
                        'Building': building_name,
                        'Annual_kWh': stats['annual_consumption'],
                        'Peak_Power_W': stats['max_power'],
                        'Avg_Power_W': stats['avg_power'],
                        'Avg_Temp_C': stats['avg_temp'],
                        'Temp_Range_C': stats['temp_range'],
                        'Load_Factor_%': (stats['avg_power']/stats['max_power']*100)
                    })
                
                metrics_df = pd.DataFrame(metrics_data)
                
                # Radar chart comparison
                if len(selected_buildings) <= 6:  # Limit radar chart to 6 buildings
                    fig_radar = go.Figure()
                    
                    # Normalize metrics for radar chart
                    metrics_to_plot = ['Annual_kWh', 'Peak_Power_W', 'Avg_Power_W', 'Load_Factor_%', 'Temp_Range_C']
                    normalized_df = metrics_df.copy()
                    
                    for metric in metrics_to_plot:
                        max_val = normalized_df[metric].max()
                        min_val = normalized_df[metric].min()
                        if max_val > min_val:
                            normalized_df[metric] = (normalized_df[metric] - min_val) / (max_val - min_val) * 100
                        else:
                            normalized_df[metric] = 50
                    
                    for i, building in enumerate(normalized_df['Building']):
                        values = [normalized_df.loc[normalized_df['Building'] == building, metric].values[0] 
                                 for metric in metrics_to_plot]
                        
                        fig_radar.add_trace(go.Scatterpolar(
                            r=values + [values[0]],  # Close the polygon
                            theta=['Energy', 'Peak Power', 'Avg Power', 'Load Factor', 'Temp Stability', 'Energy'],
                            fill='toself',
                            name=building,
                            line=dict(color=selected_colors[i % len(selected_colors)], width=2),
                            fillcolor=f'rgba({int(selected_colors[i % len(selected_colors)][1:3], 16)}, '
                                     f'{int(selected_colors[i % len(selected_colors)][3:5], 16)}, '
                                     f'{int(selected_colors[i % len(selected_colors)][5:7], 16)}, 0.2)'
                        ))
                    
                    # Update layout for radar chart
                    fig_radar.update_layout(
                        title=dict(
                            text="Multi-Metric Performance Comparison",
                            font=dict(size=18, color='#2C3E50', family='Arial, sans-serif'),
                            x=0.5,
                            xanchor='center'
                        ),
                        height=chart_height,
                        margin=dict(l=60, r=30, t=60, b=40),
                        paper_bgcolor='white',
                        font=dict(color='#2C3E50', size=12, family='Arial, sans-serif'),
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100],
                                gridcolor='#E9ECEF',
                                tickfont=dict(color='#2C3E50')
                            ),
                            angularaxis=dict(
                                gridcolor='#E9ECEF',
                                tickfont=dict(color='#2C3E50')
                            ),
                            bgcolor='white'
                        ),
                        legend=dict(
                            bgcolor='rgba(255,255,255,0.9)',
                            bordercolor='#DEE2E6',
                            borderwidth=1,
                            font=dict(color='#2C3E50')
                        ),
                        hoverlabel=dict(
                            bgcolor='white',
                            font_size=14,
                            font_family="Arial, sans-serif",
                            font_color='#2C3E50',
                            bordercolor='#DEE2E6'
                        )
                    )
                    
                    st.plotly_chart(fig_radar, use_container_width=True)
                
                # Comparison heatmap
                st.markdown("### 🔥 Performance Heatmap")
                
                # Prepare data for heatmap
                heatmap_metrics = ['Annual_kWh', 'Peak_Power_W', 'Avg_Power_W', 'Avg_Temp_C', 'Load_Factor_%']
                heatmap_data = metrics_df.set_index('Building')[heatmap_metrics]
                
                # Normalize for better visualization
                heatmap_normalized = (heatmap_data - heatmap_data.min()) / (heatmap_data.max() - heatmap_data.min())
                
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=heatmap_normalized.T.values,
                    x=heatmap_normalized.index,
                    y=['Annual Energy', 'Peak Power', 'Avg Power', 'Avg Temperature', 'Load Factor'],
                    colorscale='Blues',
                    text=heatmap_data.T.values.round(1),
                    texttemplate='%{text}',
                    textfont={"size": 10, "color": "#2C3E50"},
                    hoverongaps=False
                ))
                
                # Update layout directly
                fig_heatmap.update_layout(
                    title=dict(
                        text="Normalized Performance Metrics",
                        font=dict(size=18, color='#2C3E50', family='Arial, sans-serif'),
                        x=0.5,
                        xanchor='center'
                    ),
                    height=400,
                    paper_bgcolor='white',
                    plot_bgcolor='white',
                    font=dict(color='#2C3E50', size=12, family='Arial, sans-serif'),
                    legend=dict(
                        bgcolor='rgba(255,255,255,0.9)',
                        bordercolor='#DEE2E6',
                        borderwidth=1,
                        font=dict(color='#2C3E50')
                    ),
                    hoverlabel=dict(
                        bgcolor='white',
                        font_size=14,
                        font_family="Arial, sans-serif",
                        font_color='#2C3E50',
                        bordercolor='#DEE2E6'
                    )
                )
                
                # Update axes
                fig_heatmap.update_xaxes(
                    gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)',
                    zerolinecolor='#DEE2E6',
                    tickfont=dict(color='#2C3E50'),
                    titlefont=dict(color='#2C3E50')
                )
                fig_heatmap.update_yaxes(
                    gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)',
                    zerolinecolor='#DEE2E6',
                    tickfont=dict(color='#2C3E50'),
                    titlefont=dict(color='#2C3E50')
                )
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # Detailed comparison table
                st.markdown("### 📋 Detailed Metrics Comparison")
                
                # Format the dataframe for display
                display_df = metrics_df.copy()
                display_df['Annual_kWh'] = display_df['Annual_kWh'].round(0).astype(int)
                display_df['Peak_Power_W'] = display_df['Peak_Power_W'].round(0).astype(int)
                display_df['Avg_Power_W'] = display_df['Avg_Power_W'].round(0).astype(int)
                display_df['Avg_Temp_C'] = display_df['Avg_Temp_C'].round(1)
                display_df['Temp_Range_C'] = display_df['Temp_Range_C'].round(1)
                display_df['Load_Factor_%'] = display_df['Load_Factor_%'].round(1)
                
                # Rename columns for display
                display_df.columns = ['Building', 'Annual kWh', 'Peak W', 'Avg W', 'Avg °C', 'Range °C', 'Load %']
                
                st.dataframe(
                    display_df.style.background_gradient(
                        subset=['Annual kWh', 'Peak W', 'Avg W', 'Load %'],
                        cmap='Reds',
                        low=0.3,
                        high=0.7
                    ).background_gradient(
                        subset=['Range °C'],
                        cmap='Reds',
                        low=0.3,
                        high=0.7
                    ),
                    use_container_width=True
                )
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tabs[2]:  # Analytics
                st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
                
                # Combined correlation analysis
                all_data = []
                for building_name, data in building_data.items():
                    temp_data = data.copy()
                    temp_data['Building'] = building_name
                    all_data.append(temp_data)
                
                combined_df = pd.concat(all_data, ignore_index=True)
                
                # Create analytics visualizations
                col1, col2 = st.columns(2)
                
                with col1:
                    # Correlation scatter plot
                    fig_corr = px.scatter(
                        combined_df,
                        x='Indoor_Temperature',
                        y='Heating_Power',
                        color='Building',
                        title='Temperature vs Power Correlation (All Buildings)',
                        labels={'Indoor_Temperature': 'Temperature (°C)', 'Heating_Power': 'Power (W)'},
                        color_discrete_sequence=selected_colors,
                        opacity=0.6
                    )
                    
                    # Add trendline
                    fig_corr.add_trace(
                        go.Scatter(
                            x=combined_df['Indoor_Temperature'].sort_values(),
                            y=np.poly1d(np.polyfit(combined_df['Indoor_Temperature'], 
                                                   combined_df['Heating_Power'], 1))(combined_df['Indoor_Temperature'].sort_values()),
                            mode='lines',
                            name='Trend',
                            line=dict(color='#2C3E50', width=2, dash='dash')
                        )
                    )
                    
                    # Update layout for Plotly Express figure
                    fig_corr.update_layout(
                        height=chart_height,
                        paper_bgcolor='white',
                        plot_bgcolor='white',
                        font=dict(color='#2C3E50', size=12, family='Arial, sans-serif'),
                        title=dict(
                            font=dict(size=18, color='#2C3E50', family='Arial, sans-serif'),
                            x=0.5,
                            xanchor='center'
                        ),
                        legend=dict(
                            bgcolor='rgba(255,255,255,0.9)',
                            bordercolor='#DEE2E6',
                            borderwidth=1,
                            font=dict(color='#2C3E50')
                        ),
                        hoverlabel=dict(
                            bgcolor='white',
                            font_size=14,
                            font_family="Arial, sans-serif",
                            font_color='#2C3E50',
                            bordercolor='#DEE2E6'
                        )
                    )
                    
                    # Update axes separately
                    fig_corr.update_xaxes(
                        gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)',
                        zerolinecolor='#DEE2E6',
                        tickfont=dict(color='#2C3E50'),
                        titlefont=dict(color='#2C3E50')
                    )
                    fig_corr.update_yaxes(
                        gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)',
                        zerolinecolor='#DEE2E6',
                        tickfont=dict(color='#2C3E50'),
                        titlefont=dict(color='#2C3E50')
                    )
                    
                    st.plotly_chart(fig_corr, use_container_width=True)
                
                with col2:
                    # Distribution comparison
                    fig_dist = go.Figure()
                    
                    for i, (building_name, data) in enumerate(building_data.items()):
                        fig_dist.add_trace(go.Box(
                            y=data['Heating_Power'],
                            name=building_name,
                            marker_color=selected_colors[i % len(selected_colors)],
                            boxmean='sd'  # Show mean and standard deviation
                        ))
                    
                    # Update layout directly
                    fig_dist.update_layout(
                        title=dict(
                            text='Power Distribution by Building',
                            font=dict(size=18, color='#2C3E50', family='Arial, sans-serif'),
                            x=0.5,
                            xanchor='center'
                        ),
                        height=chart_height,
                        paper_bgcolor='white',
                        plot_bgcolor='white',
                        font=dict(color='#2C3E50', size=12, family='Arial, sans-serif'),
                        yaxis_title='Power (W)',
                        legend=dict(
                            bgcolor='rgba(255,255,255,0.9)',
                            bordercolor='#DEE2E6',
                            borderwidth=1,
                            font=dict(color='#2C3E50')
                        ),
                        hoverlabel=dict(
                            bgcolor='white',
                            font_size=14,
                            font_family="Arial, sans-serif",
                            font_color='#2C3E50',
                            bordercolor='#DEE2E6'
                        )
                    )
                    
                    # Update axes
                    fig_dist.update_xaxes(
                        gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)',
                        zerolinecolor='#DEE2E6',
                        tickfont=dict(color='#2C3E50'),
                        titlefont=dict(color='#2C3E50')
                    )
                    fig_dist.update_yaxes(
                        gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)',
                        zerolinecolor='#DEE2E6',
                        tickfont=dict(color='#2C3E50'),
                        titlefont=dict(color='#2C3E50')
                    )
                    
                    st.plotly_chart(fig_dist, use_container_width=True)
                
                # Time-based analysis
                st.markdown("### 📅 Seasonal Analysis")
                
                # Calculate seasonal averages
                seasons = {
                    'Winter': [12, 1, 2],
                    'Spring': [3, 4, 5],
                    'Summer': [6, 7, 8],
                    'Fall': [9, 10, 11]
                }
                
                seasonal_data = []
                for building_name, data in building_data.items():
                    for season, months in seasons.items():
                        mask = data['Time_Months'].apply(lambda x: int(x) in months)
                        if mask.any():
                            seasonal_data.append({
                                'Building': building_name,
                                'Season': season,
                                'Avg_Power': data[mask]['Heating_Power'].mean(),
                                'Avg_Temp': data[mask]['Indoor_Temperature'].mean()
                            })
                
                seasonal_df = pd.DataFrame(seasonal_data)
                
                # Seasonal comparison chart
                fig_seasonal = px.bar(
                    seasonal_df,
                    x='Season',
                    y='Avg_Power',
                    color='Building',
                    barmode='group',
                    title='Seasonal Average Power Consumption',
                    color_discrete_sequence=selected_colors
                )
                
                # Update layout for Plotly Express figure
                fig_seasonal.update_layout(
                    height=400,
                    paper_bgcolor='white',
                    plot_bgcolor='white',
                    font=dict(color='#2C3E50', size=12, family='Arial, sans-serif'),
                    title=dict(
                        font=dict(size=18, color='#2C3E50', family='Arial, sans-serif'),
                        x=0.5,
                        xanchor='center'
                    ),
                    legend=dict(
                        bgcolor='rgba(255,255,255,0.9)',
                        bordercolor='#DEE2E6',
                        borderwidth=1,
                        font=dict(color='#2C3E50')
                    ),
                    hoverlabel=dict(
                        bgcolor='white',
                        font_size=14,
                        font_family="Arial, sans-serif",
                        font_color='#2C3E50',
                        bordercolor='#DEE2E6'
                    )
                )
                
                # Update axes separately
                fig_seasonal.update_xaxes(
                    gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)',
                    zerolinecolor='#DEE2E6',
                    tickfont=dict(color='#2C3E50'),
                    titlefont=dict(color='#2C3E50')
                )
                fig_seasonal.update_yaxes(
                    gridcolor='#E9ECEF' if show_grid else 'rgba(0,0,0,0)',
                    zerolinecolor='#DEE2E6',
                    tickfont=dict(color='#2C3E50'),
                    titlefont=dict(color='#2C3E50')
                )
                
                st.plotly_chart(fig_seasonal, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tabs[3]:  # Rankings
                st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
                
                # Calculate rankings
                rankings = {}
                
                # Energy efficiency ranking (lower is better)
                energy_ranking = sorted(building_stats.items(), key=lambda x: x[1]['annual_consumption'])
                rankings['Energy Efficiency'] = [(b[0], i+1, f"{b[1]['annual_consumption']:,.0f} kWh") 
                                               for i, b in enumerate(energy_ranking)]
                
                # Peak demand ranking (lower is better)
                peak_ranking = sorted(building_stats.items(), key=lambda x: x[1]['max_power'])
                rankings['Peak Demand'] = [(b[0], i+1, f"{b[1]['max_power']:,.0f} W") 
                                         for i, b in enumerate(peak_ranking)]
                
                # Temperature stability ranking (lower range is better)
                temp_ranking = sorted(building_stats.items(), key=lambda x: x[1]['temp_range'])
                rankings['Temperature Stability'] = [(b[0], i+1, f"{b[1]['temp_range']:.1f}°C range") 
                                                    for i, b in enumerate(temp_ranking)]
                
                # Load factor ranking (higher is better)
                load_ranking = sorted(building_stats.items(), 
                                    key=lambda x: x[1]['avg_power']/x[1]['max_power'], 
                                    reverse=True)
                rankings['Load Factor'] = [(b[0], i+1, f"{(b[1]['avg_power']/b[1]['max_power']*100):.1f}%") 
                                         for i, b in enumerate(load_ranking)]
                
                # Display rankings
                col1, col2 = st.columns(2)
                
                with col1:
                    # Best performers
                    st.markdown("### 🏆 Top Performers")
                    
                    for category, ranking in list(rankings.items())[:2]:
                        winner = ranking[0]
                        st.markdown(f'''
                        <div class="info-box" style="border-left-color: #7ED321;">
                            <h4>🥇 {category} Champion</h4>
                            <p><strong>{winner[0]}</strong></p>
                            <p>Performance: <strong>{winner[2]}</strong></p>
                        </div>
                        ''', unsafe_allow_html=True)
                
                with col2:
                    # Areas for improvement
                    st.markdown("### 📈 Improvement Opportunities")
                    
                    for category, ranking in list(rankings.items())[2:]:
                        if len(ranking) > 1:
                            needs_improvement = ranking[-1]
                            st.markdown(f'''
                            <div class="info-box" style="border-left-color: #F5A623;">
                                <h4>⚠️ {category} - Needs Attention</h4>
                                <p><strong>{needs_improvement[0]}</strong></p>
                                <p>Current: <strong>{needs_improvement[2]}</strong></p>
                            </div>
                            ''', unsafe_allow_html=True)
                
                # Overall ranking table
                st.markdown("### 📊 Complete Rankings")
                
                # Create ranking dataframe
                ranking_data = []
                for building in building_stats.keys():
                    row = {'Building': building}
                    for category, ranking in rankings.items():
                        for b, rank, _ in ranking:
                            if b == building:
                                row[category] = rank
                                break
                    ranking_data.append(row)
                
                ranking_df = pd.DataFrame(ranking_data)
                ranking_df['Overall Score'] = ranking_df[list(rankings.keys())].mean(axis=1)
                ranking_df = ranking_df.sort_values('Overall Score')
                ranking_df['Overall Rank'] = range(1, len(ranking_df) + 1)
                
                # Display with color coding
                st.dataframe(
                    ranking_df.style.background_gradient(
                        subset=list(rankings.keys()) + ['Overall Score'],
                        cmap='RdYlGn_r',
                        low=0.3,
                        high=0.7
                    ).format({
                        'Overall Score': '{:.1f}',
                        **{col: '{:.0f}' for col in rankings.keys()}
                    }),
                    use_container_width=True
                )
                
                # Savings potential
                best_performer = energy_ranking[0]
                worst_performer = energy_ranking[-1]
                
                if len(energy_ranking) > 1:
                    potential_savings = worst_performer[1]['annual_consumption'] - best_performer[1]['annual_consumption']
                    percentage_savings = (potential_savings / worst_performer[1]['annual_consumption']) * 100
                    
                    st.markdown(f'''
                    <div class="info-box" style="margin-top: 2rem; border-left-color: #4A90E2;">
                        <h4>💰 Portfolio Optimization Potential</h4>
                        <p>If all buildings performed at the level of <strong>{best_performer[0]}</strong>:</p>
                        <p>• Total potential savings: <strong>{potential_savings * (len(building_stats) - 1):,.0f} kWh/year</strong></p>
                        <p>• Average improvement potential: <strong>{percentage_savings:.1f}%</strong></p>
                        <p>• Estimated cost savings: <strong>${potential_savings * 0.12 * (len(building_stats) - 1):,.0f}/year</strong> (at $0.12/kWh)</p>
                    </div>
                    ''', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)