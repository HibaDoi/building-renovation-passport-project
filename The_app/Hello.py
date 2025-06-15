import streamlit as st

# Page configuration
st.set_page_config(
    page_title="PhD Position in 3D Geoinformation",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2c5aa0;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #2c5aa0;
        padding-bottom: 0.5rem;
    }
    .highlight-box {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2c5aa0;
        margin: 1rem 0;
    }
    .tech-link {
        background-color: #e8f4f8;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border-left: 3px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar with navigation
st.sidebar.title("📋 Navigation")
sections = [
    "🎯 Research Context",
    "🔬 Technical Focus",
    "💡 Innovation",
    "🌍 Impact",
    "🤝 Collaboration",
    "⭐ Significance",
    "🔗 Resources"
]

selected_section = st.sidebar.radio("Go to section:", sections)

# Main title
st.markdown('<h1 class="main-header">PhD Position in 3D Geoinformation for Building Renovation Passports and Energy Transition</h1>', unsafe_allow_html=True)

# Introduction banner
st.markdown("""
<div class="highlight-box">
    <h3>🏢 RenoDAT Project Overview</h3>
    <p><strong>"Accelerating Building RENOvation and Decarbonization Through DATa Integration"</strong></p>
    <p>A collaborative research initiative led by TU Delft, funded by the Dutch Research Council (NWO)</p>
</div>
""", unsafe_allow_html=True)

# Content based on sidebar selection
if "🎯 Research Context" in selected_section:
    st.markdown('<h2 class="section-header">🎯 Research Context and Objectives</h2>', unsafe_allow_html=True)
    st.markdown("""
    This PhD position addresses critical challenges in accelerating building renovation and decarbonization through advanced data integration within the RenoDAT project. The research focuses on developing innovative methodologies that bridge the gap between Building Information Models (BIM) and 3D geospatial data to support comprehensive Building Renovation Passports, essential tools for achieving climate goals through systematic housing renovation.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("🎯 **Primary Goal**: Accelerate building renovation rates to meet climate objectives")
    with col2:
        st.info("📊 **Focus Area**: Data-driven energy renovation of building stock")

elif "🔬 Technical Focus" in selected_section:
    st.markdown('<h2 class="section-header">🔬 Technical Focus Areas</h2>', unsafe_allow_html=True)
    
    st.markdown("The research centers on three primary technical domains:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🔄 Data Harmonization**
        - Spatial and non-spatial data integration
        - Public and private data source reconciliation
        - Standardized data pipelines
        """)
    
    with col2:
        st.markdown("""
        **🏗️ Semantic Data Models**
        - Industry Foundation Classes (IFC)
        - CityGML standards
        - Seamless BIM-GIS integration
        """)
    
    with col3:
        st.markdown("""
        **🏢 Building Envelope Extraction**
        - Automated conversion processes
        - Multiple Levels of Detail (LoD)
        - City-scale representations
        """)
    
    st.markdown("""
    <div class="tech-link">
        <strong>🔧 Key Tool:</strong> 
        <a href="https://github.com/jaspervdv/IFC_BuildingEnvExtractor" target="_blank">IFC BuildingEnvExtractor</a>
        - Converts detailed architectural models to city-scale representations
    </div>
    """, unsafe_allow_html=True)

elif "💡 Innovation" in selected_section:
    st.markdown('<h2 class="section-header">💡 Methodological Innovation</h2>', unsafe_allow_html=True)
    
    st.markdown("The project employs cutting-edge approaches including:")
    
    innovation_areas = [
        {
            "title": "🌐 Automated IFC Georeferencing",
            "description": "Accurate coordinate transformation between local building systems and global spatial reference frames",
            "tool": "IfcGref",
            "link": "https://ifcgref.bk.tudelft.nl/templates/guid.html"
        },
        {
            "title": "🔗 Semantic Mapping",
            "description": "BIM to 3D city model transformations with automated data conversion",
            "tool": "Advanced algorithms",
            "link": None
        },
        {
            "title": "🏗️ Data Infrastructure",
            "description": "Collection, management, and sharing solutions for building energy performance data",
            "tool": "Custom frameworks",
            "link": None
        }
    ]
    
    for area in innovation_areas:
        with st.expander(area["title"]):
            st.write(area["description"])
            if area["link"]:
                st.markdown(f"**Tool:** [{area['tool']}]({area['link']})")
            else:
                st.markdown(f"**Approach:** {area['tool']}")

elif "🌍 Impact" in selected_section:
    st.markdown('<h2 class="section-header">🌍 Expected Impact and Applications</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    This research directly contributes to the digitalization of the built environment by creating standardized data pipelines that streamline energy renovation processes.
    """)
    
    impact_metrics = [
        "📊 More transparent and accessible building energy data",
        "📋 Standardized Renovation Passport implementation",
        "⚡ Integration with energy simulation tools",
        "🔒 Enhanced data governance and privacy solutions"
    ]
    
    for metric in impact_metrics:
        st.success(metric)
    
    st.warning("**Key Challenge Addressed:** Critical data governance issues including ownership, privacy, and harmonization that currently limit data-driven renovation strategies")

elif "🤝 Collaboration" in selected_section:
    st.markdown('<h2 class="section-header">🤝 Collaborative Framework</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🏛️ Consortium Partners:**
        - Universities
        - Universities of applied sciences
        - Governmental organizations
        - Private companies
        """)
    
    with col2:
        st.markdown("""
        **💰 Funding:**
        - Dutch Research Council (NWO)
        - "Digitalisation of Energy Renovations in the Built Environment" framework
        """)
    
    st.info("This collaborative approach ensures research outcomes are grounded in practical implementation needs while advancing theoretical understanding of BIM-GIS integration for sustainable building renovation.")

elif "⭐ Significance" in selected_section:
    st.markdown('<h2 class="section-header">⭐ Research Significance</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    By tackling fundamental challenges in building data fragmentation and standardization, this research provides essential infrastructure for scaling energy-efficient renovation practices across the existing building stock, ultimately supporting broader climate objectives through enhanced data-driven decision-making in the built environment sector.
    """)
    
    st.markdown("""
    <div class="tech-link">
        <strong>📚 Research Foundation:</strong><br>
        • <a href="https://isprs-archives.copernicus.org/articles/XLVIII-4-W11-2024/111/2024/" target="_blank">BIM Legal Implementation Framework</a><br>
        • <a href="https://onlinelibrary.wiley.com/doi/full/10.1111/tgis.13296" target="_blank">Semantic Integration Methodologies</a>
    </div>
    """, unsafe_allow_html=True)

else:  # Resources section
    st.markdown('<h2 class="section-header">🔗 Key Resources and Tools</h2>', unsafe_allow_html=True)
    
    resources = [
        {
            "name": "IFC BuildingEnvExtractor",
            "description": "Automatic building envelope extraction from IFC models to CityJSON",
            "url": "https://github.com/jaspervdv/IFC_BuildingEnvExtractor",
            "type": "🛠️ Tool"
        },
        {
            "name": "IfcGref",
            "description": "IFC georeferencing and coordinate system transformation tool",
            "url": "https://ifcgref.bk.tudelft.nl/templates/guid.html",
            "type": "🌐 Web Tool"
        },
        {
            "name": "BIM Legal Implementation",
            "description": "Standard for Cadastral Registration of Apartment Complexes in 3D",
            "url": "https://isprs-archives.copernicus.org/articles/XLVIII-4-W11-2024/111/2024/",
            "type": "📄 Research Paper"
        },
        {
            "name": "GeoBIM Benchmark Study",
            "description": "Reference study of IFC software support and BIM-GIS integration",
            "url": "https://onlinelibrary.wiley.com/doi/full/10.1111/tgis.13296",
            "type": "📊 Study"
        }
    ]
    
    for resource in resources:
        with st.container():
            st.markdown(f"""
            <div class="tech-link">
                <strong>{resource['type']} {resource['name']}</strong><br>
                {resource['description']}<br>
                <a href="{resource['url']}" target="_blank">🔗 Access Resource</a>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""

""", unsafe_allow_html=True)
