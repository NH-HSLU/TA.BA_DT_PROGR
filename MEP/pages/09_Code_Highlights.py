'''
Folie 9: Code Highlights
'''

import streamlit as st
import os
import sys

# Pfad-Setup
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from helpers.presentation_helpers import (
    init_slide_page,
    start_slide,
    end_slide,
    render_slide_navigation,
    render_divider,
    render_code_block
)

# Page Init
init_slide_page("Code Highlights")

# === SLIDE START ===
start_slide(
    "Code Highlights",
    "Wichtige Implementierungsdetails",
    slide_number=9,
    total_slides=12
)

# Tabs für verschiedene Code-Beispiele
tab1, tab2, tab3 = st.tabs(["🤖 BKP Classifier", "📊 Session State", "🎨 UI Components"])

with tab1:
    st.markdown("### BKP Classifier - Kernlogik")
    render_code_block('''class BKPClassifier:
    """KI-gestützte eBKP-H Klassifizierung"""

    def __init__(self, api_key: str = None):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-haiku-20241022"

    def classify_element(
        self,
        element_type: str,
        category: str,
        additional_info: str = ""
    ) -> dict:
        """Klassifiziert ein einzelnes Bauelement"""

        prompt = f"""Klassifiziere nach eBKP-H:
        Typ: {element_type}
        Kategorie: {category}
        Info: {additional_info}

        Antwort als JSON: {{"code": "X1.2", "confidence": 0.95}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_response(response)''', "python", "Helpers/BKP_Classifier.py")

with tab2:
    st.markdown("### Session State Management")
    render_code_block('''# Zentrale Session State Keys
DATA_CLASSIFICATION_RESULTS = "data_classification_results"
DATA_PREPARED = "data_prepared"
CFG_API_KEY = "cfg_api_key"
CFG_API_KEY_VALIDATED = "cfg_api_key_validated"

def init_session_state():
    """Initialisiert alle Session State Variablen"""
    defaults = {
        DATA_CLASSIFICATION_RESULTS: None,
        DATA_PREPARED: None,
        CFG_API_KEY: None,
        CFG_API_KEY_VALIDATED: False,
    }

    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

def get_state(key: str, default=None):
    """Sichere Getter-Funktion"""
    return st.session_state.get(key, default)

def set_state(key: str, value):
    """Sichere Setter-Funktion"""
    st.session_state[key] = value''', "python", "helpers/session_state.py")

with tab3:
    st.markdown("### UI Components - Gradient Cards")
    render_code_block('''def render_gradient_card(
    title: str,
    content: str,
    color: str = "purple",
    icon: str = ""
):
    """Rendert eine Gradient-Card"""

    icon_html = f\'\'\'<span style="font-size: 2rem;
        display: block; margin-bottom: 0.5rem;">
        {icon}</span>\'\'\' if icon else ""

    st.markdown(f"""
    <div class="gradient-card card-{color}">
        {icon_html}
        <h3>{title}</h3>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)

# CSS für Cards
.gradient-card {
    padding: 1.5rem;
    border-radius: 0.75rem;
    color: white;
    transition: transform 0.2s;
}
.gradient-card:hover {
    transform: translateY(-4px);
}
.card-purple {
    background: linear-gradient(
        135deg, #667eea 0%, #764ba2 100%
    );
}''', "python", "helpers/sidebar_navigation.py")

render_divider()

# Architektur-Hinweise
st.markdown("### 📁 Projektstruktur")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ```
    Streamlit/
    ├── streamlit_app.py      # Entry Point
    ├── config.py             # Zentrale Config
    ├── pages/
    │   ├── 00_Dashboard.py
    │   ├── 03_KI_Klassifizierung.py
    │   └── ...
    └── helpers/
        ├── session_state.py
        ├── sidebar_navigation.py
        └── notifications.py
    ```
    """)

with col2:
    st.markdown("""
    **Design Patterns:**

    - **Centralized Config**: Alle Einstellungen in `config.py`
    - **Session State Keys**: Konstanten verhindern Tippfehler
    - **Shared Components**: DRY durch Helper-Module
    - **Idempotent Init**: `init_session_state()` mehrfach aufrufbar
    """)

# === SLIDE END ===
end_slide()

# Navigation
render_slide_navigation(current_slide=9)
