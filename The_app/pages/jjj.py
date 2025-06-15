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

# 🎨 Page Configuration
st.set_page_config(
    page_title="Unified Building Analytics",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 Custom CSS for beautiful styling
st.markdown("""
<style>
    /* Main background */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0rem 1rem;
    }
    
    /* Custom container */
    .dashboard-container {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    /* Title styling */
    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        margin-bottom: 1rem;
        background: linear-gradient(45deg, #fff, #e8f4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Metric cards - smaller */
    .metric-card-small {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.25rem;
        border: 1px solid rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(10px);
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card-small:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    
    .metric-value-small {
        font-size: 1.8rem;
        font-weight: bold;
        color: #fff;
        margin: 0.25rem 0;
    }
    
    .metric-label-small {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.8);
        text-transform: uppercase;
    }
    
    /* Compact info box */
    .info-box-compact {
        background: linear-gradient(135deg, #74b9ff, #0984e3);
        color: white;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #fff;
        font-size: 0.9rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border-radius: 8px;
        margin: 2px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# 🏢 Dashboard Header
st.markdown('<h1 class="dashboard-title">🏢 Unified Building Performance Dashboard</h1>', unsafe_allow_html=True)

# 📊 Sidebar Configuration - Compact
with st.sidebar:
    st.markdown("## 🎛️ Controls")
    
    # Building selection
    st.markdown("### 🏢 Building Selection")
    
    mat_folder = "Open_modula_maybe/simulation_results"
    
    if os.path.exists(mat_folder):
        mat_files = [f for f in os.listdir(mat_folder) if f.endswith(".mat")]
        
        if mat_files:
            # Create building mapping
            building_mapping = {}
            for file in mat_files:
                building_name = file.replace('.mat', '').replace('_', ' ').title()
                building_mapping[building_name] = file
            
            # Analysis mode selection
            analysis_mode = st.radio(
                "Analysis Mode:",
                ["Single Building", "Compare Buildings", "All Buildings"],
                help="Choose your analysis approach"
            )
            
            if analysis_mode == "Single Building":
                # Single dropdown selection
                selected_building = st.selectbox(
                    "Choose a building:",
                    list(building_mapping.keys()),
                    help="Select one building to analyze in detail"
                )
                selected_buildings = [selected_building]
                
            elif analysis_mode == "Compare Buildings":
                # Multi-select for comparison
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
    else:
        st.error(f"❌ Directory not found!")
        selected_files = []
        selected_buildings = []
    
    st.markdown("---")
    
    # Quick options
    st.markdown("### ⚙️ Options")
    show_all_metrics = st.checkbox("📊 All Metrics", value=True)
    color_theme = st.selectbox("🎨 Theme", ["Viridis", "Plasma", "Set3"], index=0)
    chart_height = st.slider("📏 Height", 300, 600, 400)

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

# Main dashboard content
if selected_files:
    
    # Load data for all selected buildings
    building_data = {}
    building_stats = {}
    
    for file in selected_files:
        file_path = os.path.join(mat_folder, file)
        building_name = list(building_mapping.keys())[list(building_mapping.values()).index(file)]
        
        data, stats = load_building_data(file_path)
        if data is not None:
            building_data[building_name] = data
            building_stats[building_name] = stats
    
    if building_data:
        
        # UNIFIED OVERVIEW SECTION
        st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
        
        # Dynamic header based on selection
        if len(selected_buildings) == 1:
            st.markdown(f"## 🏢 {selected_buildings[0]} - Detailed Analysis")
        elif len(selected_buildings) <= 4:
            st.markdown(f"## 🔄 Comparing {len(selected_buildings)} Buildings")
        else:
            st.markdown(f"## 📊 Portfolio Overview - {len(selected_buildings)} Buildings")
        
        # Quick Stats Row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total_buildings = len(building_data)
        total_consumption = sum(stats['annual_consumption'] for stats in building_stats.values())
        avg_consumption = total_consumption / total_buildings if total_buildings > 0 else 0
        peak_demand = max(stats['max_power'] for stats in building_stats.values()) if building_stats else 0
        avg_temp = np.mean([stats['avg_temp'] for stats in building_stats.values()]) if building_stats else 0
        
        with col1:
            st.markdown(f'''
            <div class="metric-card-small">
                <div class="metric-value-small">{total_buildings}</div>
                <div class="metric-label-small">Buildings</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'''
            <div class="metric-card-small">
                <div class="metric-value-small">{total_consumption:.0f}</div>
                <div class="metric-label-small">Total kWh</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3:
            st.markdown(f'''
            <div class="metric-card-small">
                <div class="metric-value-small">{avg_consumption:.0f}</div>
                <div class="metric-label-small">Avg kWh</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col4:
            st.markdown(f'''
            <div class="metric-card-small">
                <div class="metric-value-small">{peak_demand:.0f}</div>
                <div class="metric-label-small">Peak W</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col5:
            st.markdown(f'''
            <div class="metric-card-small">
                <div class="metric-value-small">{avg_temp:.1f}°C</div>
                <div class="metric-label-small">Avg Temp</div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SMART TABBED INTERFACE - Shows relevant tabs based on selection
        if len(selected_buildings) == 1:
            # Single building - focus on detailed analysis
            tab1, tab2, tab3 = st.tabs(["📈 Performance Details", "📊 Advanced Analytics", "💡 Insights"])
            
            # Single building detailed view
            building_name = selected_buildings[0]
            data = building_data[building_name]
            stats = building_stats[building_name]
            
            with tab1:
                st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
                
                # Individual building metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f'''
                    <div class="metric-card-small">
                        <div class="metric-value-small">{stats['max_power']:.0f}W</div>
                        <div class="metric-label-small">Peak Power</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f'''
                    <div class="metric-card-small">
                        <div class="metric-value-small">{stats['avg_power']:.0f}W</div>
                        <div class="metric-label-small">Avg Power</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f'''
                    <div class="metric-card-small">
                        <div class="metric-value-small">{stats['annual_consumption']:.0f}</div>
                        <div class="metric-label-small">Annual kWh</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f'''
                    <div class="metric-card-small">
                        <div class="metric-value-small">{stats['avg_temp']:.1f}°C</div>
                        <div class="metric-label-small">Avg Temp</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                # Detailed charts for single building
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_power = px.line(
                        data, 
                        x='Time_Months', 
                        y='Heating_Power',
                        title=f'🔥 {building_name} - Heating Power',
                        labels={'Time_Months': 'Month', 'Heating_Power': 'Power (W)'},
                        color_discrete_sequence=[px.colors.sequential.__dict__[color_theme][4]]
                    )
                    
                    fig_power.update_xaxes(
                        tickvals=list(range(1, 13)),
                        ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    )
                    fig_power.update_layout(height=chart_height, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_power, use_container_width=True)
                
                with col2:
                    fig_temp = px.line(
                        data, 
                        x='Time_Months', 
                        y='Indoor_Temperature',
                        title=f'🌡️ {building_name} - Temperature',
                        labels={'Time_Months': 'Month', 'Indoor_Temperature': 'Temperature (°C)'},
                        color_discrete_sequence=[px.colors.sequential.__dict__[color_theme][6]]
                    )
                    
                    fig_temp.add_hline(y=20, line_dash="dash", line_color="rgba(100,100,100,0.5)", annotation_text="20°C")
                    fig_temp.add_hline(y=24, line_dash="dash", line_color="rgba(100,100,100,0.5)", annotation_text="24°C")
                    
                    fig_temp.update_xaxes(
                        tickvals=list(range(1, 13)),
                        ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    )
                    fig_temp.update_layout(height=chart_height, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_temp, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tab2:
                st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
                
                # Single building correlation analysis
                fig_corr = px.scatter(
                    data,
                    x='Indoor_Temperature',
                    y='Heating_Power',
                    color='Time_Months',
                    title=f'🔄 {building_name} - Temperature vs Power Correlation',
                    labels={'Indoor_Temperature': 'Temperature (°C)', 'Heating_Power': 'Power (W)'},
                    color_continuous_scale=color_theme
                )
                fig_corr.update_layout(height=chart_height)
                st.plotly_chart(fig_corr, use_container_width=True)
                
                # Monthly breakdown
                monthly_data = []
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                for i in range(12):
                    month_start = i + 0.5
                    month_end = i + 1.5
                    mask = (data['Time_Months'] >= month_start) & (data['Time_Months'] < month_end)
                    if np.any(mask):
                        monthly_data.append({
                            'Month': months[i],
                            'Avg_Power': data[mask]['Heating_Power'].mean(),
                            'Avg_Temp': data[mask]['Indoor_Temperature'].mean()
                        })
                
                monthly_df = pd.DataFrame(monthly_data)
                
                if not monthly_df.empty:
                    fig_monthly = px.bar(
                        monthly_df,
                        x='Month',
                        y='Avg_Power',
                        title=f'📊 {building_name} - Monthly Average Power',
                        color='Avg_Power',
                        color_continuous_scale=color_theme
                    )
                    fig_monthly.update_layout(height=chart_height//1.5)
                    st.plotly_chart(fig_monthly, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tab3:
                st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
                
                # Single building insights
                peak_month_idx = monthly_df['Avg_Power'].idxmax() if not monthly_df.empty else 0
                low_month_idx = monthly_df['Avg_Power'].idxmin() if not monthly_df.empty else 0
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if not monthly_df.empty:
                        peak_month = monthly_df.iloc[peak_month_idx]['Month']
                        peak_power = monthly_df.iloc[peak_month_idx]['Avg_Power']
                        st.markdown(f'''
                        <div class="info-box-compact">
                            <h4>🔥 Peak Demand Period</h4>
                            <p><strong>{peak_month}</strong> shows highest demand</p>
                            <p>Average: <strong>{peak_power:.0f}W</strong></p>
                        </div>
                        ''', unsafe_allow_html=True)
                
                with col2:
                    if not monthly_df.empty:
                        low_month = monthly_df.iloc[low_month_idx]['Month']
                        low_power = monthly_df.iloc[low_month_idx]['Avg_Power']
                        st.markdown(f'''
                        <div class="info-box-compact">
                            <h4>❄️ Low Demand Period</h4>
                            <p><strong>{low_month}</strong> shows lowest demand</p>
                            <p>Average: <strong>{low_power:.0f}W</strong></p>
                        </div>
                        ''', unsafe_allow_html=True)
                
                # Performance summary
                st.markdown(f'''
                <div class="info-box-compact">
                    <h4>📋 {building_name} Performance Summary</h4>
                    <p>• Annual consumption: <strong>{stats['annual_consumption']:.0f} kWh</strong></p>
                    <p>• Temperature range: <strong>{stats['temp_range']:.1f}°C</strong> (Min: {stats['min_temp']:.1f}°C, Max: {stats['max_temp']:.1f}°C)</p>
                    <p>• Power efficiency: <strong>{stats['annual_consumption']/stats['avg_temp'] if stats['avg_temp'] > 0 else 0:.1f} kWh/°C</strong></p>
                </div>
                ''', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            # Multiple buildings - comparison and overview tabs
            tab1, tab2, tab3, tab4 = st.tabs(["📈 Performance Charts", "🔄 Comparison", "📊 Analytics", "🏆 Rankings"])
        
        # TAB 1: PERFORMANCE CHARTS (for multiple buildings)
        with tab1:
            st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
            
            # Side-by-side charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Heating Power Chart
                fig_power = go.Figure()
                colors = px.colors.qualitative.Set3 if color_theme == "Set3" else getattr(px.colors.sequential, color_theme)
                
                for i, (building_name, data) in enumerate(building_data.items()):
                    color = colors[i % len(colors)] if isinstance(colors, list) else colors[min(i * 2, len(colors) - 1)]
                    fig_power.add_trace(go.Scatter(
                        x=data['Time_Months'],
                        y=data['Heating_Power'],
                        mode='lines',
                        name=building_name,
                        line=dict(color=color, width=2)
                    ))
                
                fig_power.update_layout(
                    title='🔥 Heating Power Comparison',
                    xaxis_title='Month',
                    yaxis_title='Power (W)',
                    height=chart_height,
                    margin=dict(l=20, r=20, t=40, b=20),
                    xaxis=dict(
                        tickvals=list(range(1, 13)),
                        ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    ),
                    legend=dict(x=0, y=1, bgcolor="rgba(255,255,255,0.1)")
                )
                
                st.plotly_chart(fig_power, use_container_width=True)
            
            with col2:
                # Temperature Chart
                fig_temp = go.Figure()
                
                for i, (building_name, data) in enumerate(building_data.items()):
                    color = colors[i % len(colors)] if isinstance(colors, list) else colors[min(i * 2, len(colors) - 1)]
                    fig_temp.add_trace(go.Scatter(
                        x=data['Time_Months'],
                        y=data['Indoor_Temperature'],
                        mode='lines',
                        name=building_name,
                        line=dict(color=color, width=2)
                    ))
                
                # Add comfort zone
                fig_temp.add_hline(y=20, line_dash="dash", line_color="rgba(255,255,255,0.5)", annotation_text="20°C")
                fig_temp.add_hline(y=24, line_dash="dash", line_color="rgba(255,255,255,0.5)", annotation_text="24°C")
                
                fig_temp.update_layout(
                    title='🌡️ Temperature Comparison',
                    xaxis_title='Month',
                    yaxis_title='Temperature (°C)',
                    height=chart_height,
                    margin=dict(l=20, r=20, t=40, b=20),
                    xaxis=dict(
                        tickvals=list(range(1, 13)),
                        ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    ),
                    legend=dict(x=0, y=1, bgcolor="rgba(255,255,255,0.1)")
                )
                
                st.plotly_chart(fig_temp, use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # TAB 2: COMPARISON
        with tab2:
            st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
            
            if len(building_data) >= 2:
                # Performance metrics comparison
                metrics_data = []
                for building_name, stats in building_stats.items():
                    metrics_data.append({
                        'Building': building_name,
                        'Peak Power (W)': stats['max_power'],
                        'Avg Power (W)': stats['avg_power'],
                        'Annual kWh': stats['annual_consumption'],
                        'Avg Temp (°C)': stats['avg_temp']
                    })
                
                metrics_df = pd.DataFrame(metrics_data)
                
                # Side-by-side comparison charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # Bar chart comparison
                    fig_bar = px.bar(
                        metrics_df,
                        x='Building',
                        y='Annual kWh',
                        title='📊 Annual Consumption Comparison',
                        color='Annual kWh',
                        color_continuous_scale=color_theme,
                        height=chart_height//1.2
                    )
                    fig_bar.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col2:
                    # Radar chart for multi-metric comparison
                    fig_radar = go.Figure()
                    
                    # Normalize metrics for radar chart
                    normalized_df = metrics_df.copy()
                    for col in ['Peak Power (W)', 'Avg Power (W)', 'Annual kWh', 'Avg Temp (°C)']:
                        max_val = normalized_df[col].max()
                        if max_val > 0:
                            normalized_df[col] = normalized_df[col] / max_val * 100
                    
                    for i, building in enumerate(normalized_df['Building']):
                        fig_radar.add_trace(go.Scatterpolar(
                            r=[normalized_df.iloc[i]['Peak Power (W)'],
                               normalized_df.iloc[i]['Avg Power (W)'],
                               normalized_df.iloc[i]['Annual kWh'],
                               normalized_df.iloc[i]['Avg Temp (°C)']],
                            theta=['Peak Power', 'Avg Power', 'Annual kWh', 'Avg Temp'],
                            fill='toself',
                            name=building,
                            line_color=colors[i % len(colors)] if isinstance(colors, list) else colors[min(i * 2, len(colors) - 1)]
                        ))
                    
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100]
                            )),
                        title='🎯 Multi-Metric Comparison',
                        height=chart_height//1.2,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
                
                # Comparison table
                st.markdown("### 📋 Detailed Comparison")
                st.dataframe(metrics_df.set_index('Building'), use_container_width=True)
                
            else:
                st.info("📝 Select multiple buildings for comparison analysis")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # TAB 3: ANALYTICS
        with tab3:
            st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Correlation analysis
                if len(building_data) >= 1:
                    # Combine all building data for correlation
                    all_data = []
                    for building_name, data in building_data.items():
                        temp_data = data.copy()
                        temp_data['Building'] = building_name
                        all_data.append(temp_data)
                    
                    combined_df = pd.concat(all_data, ignore_index=True)
                    
                    fig_corr = px.scatter(
                        combined_df,
                        x='Indoor_Temperature',
                        y='Heating_Power',
                        color='Building',
                        title='🔄 Temperature vs Power Correlation',
                        labels={'Indoor_Temperature': 'Temperature (°C)', 'Heating_Power': 'Power (W)'},
                        color_discrete_sequence=px.colors.qualitative.Set3,
                        height=chart_height//1.2
                    )
                    fig_corr.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_corr, use_container_width=True)
            
            with col2:
                # Distribution analysis
                consumption_values = [stats['annual_consumption'] for stats in building_stats.values()]
                building_names = list(building_stats.keys())
                
                fig_dist = px.box(
                    y=consumption_values,
                    title='📈 Consumption Distribution',
                    labels={'y': 'Annual Consumption (kWh)'},
                    height=chart_height//1.2
                )
                fig_dist.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_dist, use_container_width=True)
            
            # Heatmap
            if len(building_data) >= 2:
                st.markdown("### 🔥 Performance Heatmap")
                
                heatmap_data = []
                for building_name, stats in building_stats.items():
                    heatmap_data.append([
                        stats['max_power'],
                        stats['avg_power'],
                        stats['annual_consumption'],
                        stats['avg_temp']
                    ])
                
                heatmap_df = pd.DataFrame(
                    heatmap_data,
                    columns=['Peak Power', 'Avg Power', 'Annual kWh', 'Avg Temp'],
                    index=list(building_stats.keys())
                )
                
                # Normalize for better visualization
                heatmap_normalized = heatmap_df.div(heatmap_df.max())
                
                fig_heatmap = px.imshow(
                    heatmap_normalized.T,
                    color_continuous_scale=color_theme,
                    title='🏢 Normalized Performance Heatmap',
                    labels=dict(x="Building", y="Metric", color="Normalized Value"),
                    height=300
                )
                fig_heatmap.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_heatmap, use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # TAB 4: RANKINGS
        with tab4:
            st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
            
            if len(building_data) >= 2:
                # Performance rankings
                col1, col2 = st.columns(2)
                
                with col1:
                    # Most efficient
                    best_efficiency = min(building_stats.items(), key=lambda x: x[1]['annual_consumption'])
                    st.markdown(f'''
                    <div class="info-box-compact">
                        <h4>🥇 Most Efficient Building</h4>
                        <p><strong>{best_efficiency[0]}</strong></p>
                        <p>Annual: <strong>{best_efficiency[1]['annual_consumption']:.0f} kWh</strong></p>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # Highest peak demand
                    highest_peak = max(building_stats.items(), key=lambda x: x[1]['max_power'])
                    st.markdown(f'''
                    <div class="info-box-compact">
                        <h4>⚡ Highest Peak Demand</h4>
                        <p><strong>{highest_peak[0]}</strong></p>
                        <p>Peak: <strong>{highest_peak[1]['max_power']:.0f} W</strong></p>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col2:
                    # Least efficient
                    worst_efficiency = max(building_stats.items(), key=lambda x: x[1]['annual_consumption'])
                    st.markdown(f'''
                    <div class="info-box-compact">
                        <h4>⚠️ Needs Improvement</h4>
                        <p><strong>{worst_efficiency[0]}</strong></p>
                        <p>Annual: <strong>{worst_efficiency[1]['annual_consumption']:.0f} kWh</strong></p>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # Best temperature control
                    best_temp = min(building_stats.items(), key=lambda x: x[1]['temp_range'])
                    st.markdown(f'''
                    <div class="info-box-compact">
                        <h4>🌡️ Best Temperature Control</h4>
                        <p><strong>{best_temp[0]}</strong></p>
                        <p>Range: <strong>{best_temp[1]['temp_range']:.1f}°C</strong></p>
                    </div>
                    ''', unsafe_allow_html=True)
                
                # Ranking table
                st.markdown("### 🏆 Complete Rankings")
                
                ranking_df = pd.DataFrame({
                    'Building': list(building_stats.keys()),
                    'Efficiency Rank': range(1, len(building_stats) + 1),
                    'Annual kWh': [stats['annual_consumption'] for stats in building_stats.values()],
                    'Peak Power (W)': [stats['max_power'] for stats in building_stats.values()],
                    'Avg Temp (°C)': [stats['avg_temp'] for stats in building_stats.values()]
                }).sort_values('Annual kWh')
                
                ranking_df['Efficiency Rank'] = range(1, len(ranking_df) + 1)
                
                st.dataframe(ranking_df.set_index('Efficiency Rank'), use_container_width=True)
                
                # Quick insights
                st.markdown("### 💡 Quick Insights")
                potential_savings = worst_efficiency[1]['annual_consumption'] - best_efficiency[1]['annual_consumption']
                st.markdown(f'''
                <div class="info-box-compact">
                    <h4>💰 Potential Savings</h4>
                    <p>If <strong>{worst_efficiency[0]}</strong> performed like <strong>{best_efficiency[0]}</strong>:</p>
                    <p><strong>{potential_savings:.0f} kWh/year</strong> could be saved</p>
                </div>
                ''', unsafe_allow_html=True)
            
            else:
                st.info("📝 Select multiple buildings to see rankings")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        st.error("❌ No valid building data could be loaded.")

else:
    # Compact welcome screen
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 15px; backdrop-filter: blur(10px);">
            <h2 style="color: white;">🏢 Unified Building Analytics</h2>
            <p style="color: rgba(255,255,255,0.8);">Select buildings from the sidebar to view comprehensive analytics</p>
            <div style="display: flex; justify-content: space-around; margin-top: 1rem;">
                <div style="color: rgba(255,255,255,0.9);">📈 Performance</div>
                <div style="color: rgba(255,255,255,0.9);">🔄 Comparison</div>
                <div style="color: rgba(255,255,255,0.9);">📊 Analytics</div>
                <div style="color: rgba(255,255,255,0.9);">🏆 Rankings</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Compact footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: rgba(255,255,255,0.6); padding: 0.5rem; font-size: 0.9rem;">'
    '🏢 Unified Building Dashboard | Streamlit + Plotly'
    '</div>', 
    unsafe_allow_html=True
)