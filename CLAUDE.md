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
- **develop**: Active development branch with working Streamlit multi-page app
- **DOODLES**: Experimental branch with prototype implementations
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

# Run Streamlit multi-page app (develop branch)
.venv/bin/streamlit run Processors/streamlit_app.py  # macOS/Linux
# .venv\Scripts\streamlit run Processors/streamlit_app.py  # Windows

# Note: Use .venv/bin/streamlit to ensure correct Python environment
# App will be available at http://localhost:8501
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

## Streamlit Multi-Page App Architecture

The develop branch contains a fully functional Streamlit app with the following structure:

### App Entry Point
- **`Processors/streamlit_app.py`**: Landing page with project overview and quick-start guide

### Pages (in `Processors/pages/`)
1. **`1_eBKP_Auswertung.py`**: Hierarchical visualization of BKP-classified data
   - Auto-loads data from Session State (KI classification results)
   - Displays costs grouped by eBKP-H hierarchy with collapsible expanders
   - Interactive charts (pie, bar) and CSV export

2. **`2_KI_Klassifizierung.py`**: AI-powered BKP classification
   - Tab 1: Upload CSV and configure classification
   - Tab 2: View classification results
   - Tab 3: Real-time API response monitoring with live updates
   - Tab 4: Processing log
   - Batch processing with progress tracking
   - Results stored in `st.session_state.classification_results`
   - API responses captured with raw JSON for debugging

2.5. **`2.5_BKP_Bearbeiten.py`**: Manual BKP code editing (NEW)
   - Load classified data from Session State
   - Filter by confidence threshold or BKP groups
   - Inline editing with `st.data_editor()`
   - BKP code validation (format and known codes)
   - Save edited data back to Session State
   - Positioned between KI classification and eBKP evaluation in workflow

3. **`3_Einstellungen.py`**: API key management
   - Session State-based key storage (non-persistent)
   - API key validation with test classification
   - Fallback to `.env` file if available

### Session State Data Flow

The app uses Streamlit Session State for cross-page data sharing:

```python
# Set by KI Klassifizierung page:
st.session_state.classification_results = df  # Pandas DataFrame with BKP codes
st.session_state.api_responses = [...]        # List of API response logs with raw JSON
st.session_state.processing_log = [...]       # Processing events log
st.session_state.api_key = "sk-ant-..."       # User's API key
st.session_state.api_key_validated = True     # Validation status

# Modified by BKP Bearbeiten page:
# Updates classification_results with edited BKP codes

# Read by eBKP Auswertung page:
if 'classification_results' in st.session_state:
    df = st.session_state.classification_results
```

### Complete Workflow

1. **KI Klassifizierung** (`2_KI_Klassifizierung.py`)
   - Upload CSV without BKP codes
   - Classify with Claude AI
   - View live API responses during processing

2. **BKP Bearbeiten** (`2.5_BKP_Bearbeiten.py`) - OPTIONAL
   - Review classification results
   - Edit low-confidence codes
   - Validate BKP codes

3. **eBKP Auswertung** (`1_eBKP_Auswertung.py`)
   - Visualize data by BKP hierarchy
   - Export reports

### Example Data Files

- **`Processors/beispiel_daten.csv`**: Sample data WITH BKP codes (for testing visualization)
- **`Processors/muster_ki_klassifizierung.csv`**: Sample data WITHOUT BKP codes (for testing AI classification)

## AI Classification with Claude

The `Helpers/BKP_Classifier.py` module provides AI-powered BKP classification:

### Key Features
- Uses Claude 3.5 Haiku model for cost efficiency
- Supports single element and batch classification
- Token optimization through prompt caching and short prompts
- Returns BKP code, description, and confidence score

### Usage in Streamlit
```python
from Helpers.BKP_Classifier import BKPClassifier

classifier = BKPClassifier()

# Basic classification
result = classifier.classify_element(
    element_type="Steckdose T13",
    category="Electrical Fixtures"
)
# Returns: {'bkp_code': 'C13', 'bkp_description': 'Steckdosen', 'confidence': 0.95}

# With API details for debugging
result = classifier.classify_element(
    element_type="Steckdose T13",
    category="Electrical Fixtures",
    return_details=True
)
# Returns additional: 'raw_response', 'model', 'tokens'
```

### API Key Configuration
1. Via `.env` file (persistent): `ANTHROPIC_API_KEY=sk-ant-...`
2. Via Streamlit UI (Session State, non-persistent): Use Einstellungen page

## Important Notes

- **ALWAYS use `.venv/bin/streamlit`** on macOS/Linux to ensure correct Python environment
- pyRevit extensions are in `PyRevit_Extensions/` directory (merged from DOODLES branch)
- IFC files are typically large - they are in `.gitignore`
- The `.env` file is gitignored - never commit API keys
- German is used for UI text and comments, English for commit messages
