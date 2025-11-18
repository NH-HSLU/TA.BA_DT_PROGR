# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a university project (TA.BA_DT_PROGR) focused on developing BIM data processing tools for architectural and electrical models. The primary workflow extracts building data from Revit using pyRevit extensions, exports to CSV, and visualizes the data in Streamlit dashboards with BKP (Baukostenplan - Swiss construction cost classification) integration.

**Final Goal**: Quantity takeoff with BKP classification focusing on architecture and electrical systems, with cost visualization by BKP or room. Includes quality checking of required attributes.

## Architecture

The project follows a three-stage pipeline:

1. **Data Extraction (pyRevit)**: Custom pyRevit extensions run inside Revit to extract element data (rooms, walls, ceilings, electrical components) and export to CSV
2. **Data Processing (Processors)**: Python modules that handle BKP assignment, data transformation, and PDF export
3. **Visualization (Streamlit)**: Interactive dashboards for data analysis, cost breakdown, and reporting

### Key Data Structure

The project uses a standardized data model for BIM elements:

```python
# Base class structure (see DOODLES branch: Klassen.py)
class class_ifc:
    - UID: str
    - ifcType: str
    - parent: optional parent element
    - children: list of child elements

# Specialized classes inherit from class_ifc:
- class_socket: Electrical outlets/switches with wall relationships
- class_wall: Wall elements with room relationships and socket lists
- class_room: Rooms with wall lists and metadata (name, area)
```

Elements are organized hierarchically: Room → Walls → Sockets/Electrical Elements

### Branch Structure

- **main**: Clean production branch with documentation only
- **develop**: Active development branch (currently empty, being restructured)
- **DOODLES**: Experimental branch with working implementations:
  - `DOODLES/`: Prototype scripts (IFC reading, Streamlit apps, class definitions)
  - `PyRevit_Extensions/Digital_Twin_PROGR.extension/`: pyRevit scripts for Revit integration
  - `DEVELOPMENT/`: Import and evaluation scripts
- **feature**: Feature development branch
- **ZP1**: Checkpoint 1 submission
- **jupyter_notebook**: Jupyter notebook experiments

## Development Environment

### Required Tools

- **Python 3.x** with virtual environment (`.venv`)
- **Git/GitHub** for version control
- **VS Code or PyCharm** as IDE
- **Revit** with pyRevit for data extraction

### Python Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt
```

**Core modules**:
- `ifcopenshell`: IFC/BIM file processing
- `streamlit`: Interactive dashboards
- `pandas`: Data manipulation
- `matplotlib`, `plotly`: Visualization
- `numpy`: Numerical operations
- `openpyxl`: Excel file handling

### Running the Application

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate    # Windows

# Run Streamlit dashboard (when implemented in develop/main)
streamlit run app.py

# For DOODLES branch implementations:
git checkout DOODLES
streamlit run DOODLES/streamlit_app.py
# or
streamlit run DOODLES/streamlit_Raumauswertung.py
```

### pyRevit Scripts

pyRevit extensions are located in `PyRevit_Extensions/Digital_Twin_PROGR.extension/` (DOODLES branch). Each script is a pushbutton that runs inside Revit:

**Key scripts**:
- `Raum_Auflistung`: Exports rooms with areas, finishes, and level data to CSV
- `Ceiling_Auswertung`: Ceiling analysis and export
- `Walls_Auswertung`: Wall analysis and export

**Standard pyRevit script structure**:
```python
from pyrevit import revit, DB, forms, script
import csv

doc = revit.doc
output = script.get_output()

# Collect elements using FilteredElementCollector
# Process and export to CSV
```

## Coding Standards

From CONTRIBUTING.md:

### File Naming
- Use `snake_case` for all files and folders
- Names should describe content: `ifc_einlesen.py`, `pdf_exportieren.py`

### Git Workflow
- **Commit messages**: Always in English (can use Copilot to generate)
- **Code comments and GitHub discussions**: Always in German
- **Feature branches**: Create from `features` branch, name as `features/feature_name`
- **Bug fixes**: Prefix with `[FIX]`
- **Pull requests**: Require review from at least one person before merging

### Code Style
- Follow PEP8 for Python code
- Write unit tests for new functions when possible

## Working with BKP Classification

BKP (Baukostenplan) is the Swiss construction cost classification system. The `Processors/BKP_zuordnen.py` module handles assignment of BKP codes to building elements.

**Typical BKP workflow**:
1. Extract elements from Revit (with pyRevit)
2. Assign BKP codes based on element type and properties
3. Group costs by BKP hierarchy for reporting

**Expected CSV columns from pyRevit exports**:
- Element properties: `Raumnummer`, `Raumname`, `Fläche (m²)`, `Ebene`
- Materials: `Wandmaterial`, `Deckenmaterial`
- BKP fields: `BKP_Code`, `BKP_Beschreibung`, `Kategorie` (assigned by processor)

## Project Context

This is an academic project for a Programming module (Digital Twin - Programming) at a Swiss university. Students work individually or in pairs to develop BIM-related tools using Python.

**Grading milestones**:
- ZP1 (Checkpoint 1): [Milestone ZP1](https://github.com/NH-HSLU/TA.BA_DT_PROGR/milestone/1)
- ZP2 (Checkpoint 2): [Milestone ZP2](https://github.com/NH-HSLU/TA.BA_DT_PROGR/milestone/2)
- MEP (Final Exam): [Milestone MEP](https://github.com/NH-HSLU/TA.BA_DT_PROGR/milestone/3)

## Important Notes

- The current working directory structure is being restructured from DOODLES to develop/main branches
- Most working implementations are currently in the DOODLES branch
- `app.py`, `Processors/`, and `Helpers/` directories in develop/main are mostly empty shells
- When adding functionality, check DOODLES branch for reference implementations
- IFC files are typically large - they are in `.gitignore` but some test files exist in DOODLES branch
- The `.env` file exists but is gitignored - may contain API keys for AI integration (see `Helpers/Anisotropic.py`)
