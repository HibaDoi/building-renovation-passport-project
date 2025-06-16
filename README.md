# Building Renovation Passport Project

> **Note**: This project is currently under active development and reorganization. The structure and documentation are being improved to better reflect the comprehensive building renovation analysis pipeline.

## Overview

This project creates a **Building Renovation Passport** - A comprehensive digital tool that processes CityJSON building data from Delft City to generate detailed building performance simulations and renovation recommendations. The system combines advanced data extraction, thermal simulation modeling, and interactive visualization to support evidence-based building renovation decision-making.
![Dashboard Screenshot](images/image.png)
## What is a Building Renovation Passport?

A Building Renovation Passport is an evolution of traditional Energy Performance Certificates (EPCs) that provides:

- **Long-term renovation roadmap**: Step-by-step renovation planning with customized recommendations
- **Building information repository**: Centralized storage of all building-related data and documentation
- **Performance simulation**: Detailed thermal and energy analysis using industry-standard tools
- **Interactive visualization**: User-friendly dashboard for exploring renovation scenarios

## Project Workflow

### 🏗️ Step 1: CityJSON Data Extraction

Extract comprehensive building information from Delft City's CityJSON files, focusing on:

**Key Building Attributes:**

- `id` - Unique building identifier
- `year_built` - Construction year for age-based analysis
- `roof_type` - Roof classification (flat, sloped, etc.)
- `roof_h_typ` - Roof height type (standard, variable)
- `roof_h_min` / `roof_h_max` - Roof height range
- `ground_lvl` - Ground level for terrain alignment
- `volume_lod2` - Building volume at Level of Detail 2
- `footprint` - Ground floor area

**Technical Challenges:**

- Handling inconsistent or missing data in CityJSON files
- Ensuring data quality for accurate simulation inputs
- Managing large-scale urban building datasets

### 🔧 Step 2: Geometric Analysis & Processing

Python-based geometric analysis to derive additional building parameters:

- Floor area calculations from 3D geometry
- Floor number estimation based on building height and typology
- Building envelope analysis for thermal modeling
- Validation and correction of geometric inconsistencies

### 🏠 Step 3: TEASER Thermal Modeling

Integration with **TEASER** (Tool for Energy Analysis and Simulation for Efficient Retrofit):

- Generate detailed thermal building models
- Create physics-based simulation parameters
- Export models in Modelica format (`.mo` files)
- Define building archetypes based on construction year and type

### ⚡ Step 4: OpenModelica Simulation

Execute building performance simulations using OpenModelica:

- Process Modelica models (`.mo` files)
- Run dynamic thermal simulations
- Generate comprehensive results in MATLAB format (`.mat` files)
- Calculate energy consumption, heating/cooling loads, and comfort metrics

### 📊 Step 5: Interactive Dashboard & Results

Present results through a **Streamlit web application**:

- Interactive visualization of simulation results
- Building-by-building performance comparison
- Renovation scenario analysis and recommendations
- Export capabilities for renovation reports

**Cloud Infrastructure:**

- Secure data storage using Google Cloud/AWS
- Scalable processing for large building datasets
- API endpoints for third-party integration

## Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Data Processing** | Python | CityJSON parsing, geometric analysis |
| **Thermal Modeling** | TEASER | Building physics simulation setup |
| **Simulation Engine** | OpenModelica | Dynamic building performance simulation |
| **Frontend** | Streamlit | Interactive web dashboard |
| **Cloud Storage** | Google Cloud/AWS | Scalable data management |
| **3D Building Data** | CityJSON | Standardized city model format |

## Current Status

🚧 **Active Development**: The project is currently being restructured and organized for better maintainability and documentation.

**Completed Components:**

- ✅ CityJSON data extraction pipeline
- ✅ TEASER integration for thermal modeling
- ✅ OpenModelica simulation workflow
- ✅ Basic Streamlit dashboard
- ✅ Cloud storage integration

**In Progress:**

- 🔄 Code organization and modularization
- 🔄 Comprehensive documentation
- 🔄 Testing framework implementation
- 🔄 Performance optimization

## Installation & Setup

> **Note**: Detailed installation instructions will be provided as the project structure is finalized.

### Prerequisites

- Python 3.8+
- OpenModelica
- TEASER library
- Streamlit
- Cloud storage credentials (Google Cloud or AWS)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/HibaDoi/building-renovation-passport-project.git
cd building-renovation-passport-project

# Setup will be simplified in the upcoming reorganization
# Installation instructions coming soon...
```

## Use Cases & Applications

**For Building Owners:**

- Understand current building performance
- Plan cost-effective renovation strategies
- Prioritize improvements based on impact analysis
- Track renovation progress over time

**For Energy Consultants:**

- Generate detailed building performance reports
- Compare renovation scenarios quantitatively
- Support evidence-based recommendations
- Streamline audit and certification processes

**For Policy Makers:**

- Analyze building stock performance at city scale
- Support renovation incentive programs
- Monitor progress toward climate goals
- Inform building code and standard development

## Research Context

This project contributes to the broader field of **Building Renovation Passports** - an emerging concept in European building policy that aims to:

- Increase renovation rates across the EU building stock
- Support step-by-step deep renovations
- Remove barriers and lock-in effects
- Provide long-term renovation roadmaps for individual buildings

The approach builds on successful implementations in Germany ("Individueller Sanierungsfahrplan"), Flanders ("Woningpas"), and France ("Passeport Efficacité Énergétique").

## Contributing

The project welcomes contributions as it moves toward a more organized structure. Areas where contributions would be valuable:

- **Code Organization**: Help modularize and structure the codebase
- **Documentation**: Improve technical documentation and user guides
- **Testing**: Develop comprehensive test suites
- **Visualization**: Enhance dashboard features and user experience

## Future Roadmap

**Short Term:**

- Complete code reorganization and documentation
- Implement comprehensive testing framework
- Optimize performance for large datasets
- Enhance user interface and experience

**Long Term:**

- Integration with additional European city datasets
- Machine learning-based renovation recommendations
- Real-time monitoring and IoT integration
- Mobile application development
- API development for third-party tools

## Acknowledgments

- **Delft City** for providing comprehensive CityJSON building data
- **TEASER Development Team** for the robust building simulation framework
- **OpenModelica Community** for the open-source simulation platform
- **Building Performance Institute Europe (BPIE)** for renovation passport research
- **iBRoad Project** for building renovation roadmap methodologies

## Contact

For questions, collaboration opportunities, or technical support:

- **Repository**: [https://github.com/HibaDoi/building-renovation-passport-project](https://github.com/HibaDoi/building-renovation-passport-project)
- **Issues**: Please use GitHub Issues for bug reports and feature requests

---

