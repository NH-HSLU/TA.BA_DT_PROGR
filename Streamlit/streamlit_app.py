'''
BKP Datenverarbeitungs-Suite
Haupteinstiegspunkt für Multi-Page Streamlit App
'''

import streamlit as st
import os
import sys
from datetime import datetime

# Importiere lokale Helper
sys.path.insert(0, os.path.dirname(__file__))
from helpers.sidebar_navigation import render_sidebar, render_page_footer, render_divider, render_page_header
from helpers.ebkp_trivia import get_daily_fact
from helpers.session_state import (
    init_session_state,
    get_state,
    has_classification_results,
    DATA_CLASSIFICATION_RESULTS,
    CFG_COST_ESTIMATION_CONFIG
)

# Seitenkonfiguration
st.set_page_config(
    page_title="eBKP-H Suite",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
init_session_state()

# Render Sidebar
render_sidebar()

# Globales Stylesheet - Card-Design aus Kostenermittlung
st.markdown("""
<style>
    /* Haupttitel Styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .main-subtitle {
        text-align: center;
        font-size: 1.1rem;
        opacity: 0.7;
        margin-bottom: 2rem;
    }

    /* Card Container */
    .workflow-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem 0;
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
        color: white;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .workflow-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .workflow-card h3 {
        font-size: 1.3rem;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .workflow-card p {
        font-size: 0.95rem;
        opacity: 0.95;
        line-height: 1.5;
    }

    /* Card Farben (aus Kostenermittlung) */
    .card-purple { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .card-pink { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .card-cyan { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .card-green { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .card-orange { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .card-dark { background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); }

    /* Workflow Steps */
    .workflow-step {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .workflow-step h4 {
        margin: 0 0 0.5rem 0;
        color: #667eea;
    }

    /* Kompakte Info-Boxen */
    .info-box {
        padding: 0.8rem;
        border-radius: 0.3rem;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Haupttitel
render_page_header("🏗️ eBKP-H Suite", "Automatische BKP-Klassifizierung für BIM-Daten")

# Daily Fun Fact
st.info(f"💡 **Wussten Sie?** {get_daily_fact()}")

render_divider("section")

# Workflow-Cards (4 Hauptfunktionen)
st.markdown("### 🚀 Workflow")
# TODO falsche Pfade für die Seiten anpassen
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="workflow-card card-purple">
        <h3>1️⃣ Kostenermittlung</h3>
        <p>Projektphase wählen<br>SIA LHO 102<br>±10% bis ±30%</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("→ Starten", key="btn_cost", width='stretch'):
        st.switch_page("pages/01_Kostenermittlung.py")

with col2:
    st.markdown("""
    <div class="workflow-card card-cyan">
        <h3>2️⃣ KI-Klassifizierung</h3>
        <p>CSV hochladen<br>Automatisch klassifizieren<br>Claude AI</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("→ Starten", key="btn_classify", width='stretch'):
        st.switch_page("pages/03_KI_Klassifizierung.py")

with col3:
    st.markdown("""
    <div class="workflow-card card-green">
        <h3>3️⃣ BKP Bearbeiten</h3>
        <p>Codes überprüfen<br>Manuell korrigieren<br>Validieren</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("→ Starten", key="btn_edit", width='stretch'):
        st.switch_page("pages/04_eBKP_Bearbeiten.py")

with col4:
    st.markdown("""
    <div class="workflow-card card-orange">
        <h3>4️⃣ Auswertung</h3>
        <p>Hierarchie anzeigen<br>Kosten analysieren<br>Export</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("→ Starten", key="btn_eval", width='stretch'):
        st.switch_page("pages/06_eBKP_Auswertung.py")

# Workflow Progress Tracker
render_divider("section")
st.subheader("📊 Ihr Fortschritt")


def show_workflow_progress():
    """Visualisiert Workflow-Fortschritt mit zentralem Session State"""
    steps = [
        ("1️⃣ Kostenermittlung", CFG_COST_ESTIMATION_CONFIG),
        ("2️⃣ KI-Klassifizierung", DATA_CLASSIFICATION_RESULTS),
        ("3️⃣ BKP-Bearbeitung (optional)", DATA_CLASSIFICATION_RESULTS),
        ("4️⃣ Auswertung", DATA_CLASSIFICATION_RESULTS),
    ]

    def is_step_complete(key):
        """Prüft ob ein Workflow-Schritt abgeschlossen ist mit get_state"""
        value = get_state(key)
        if value is None:
            return False
        # Für DataFrames: Prüfe ob nicht leer
        if hasattr(value, 'empty'):
            return not value.empty
        # Für Dicts: Prüfe ob 'selected' key True ist
        if isinstance(value, dict):
            return value.get('selected', False)
        # Für andere Typen: Standard Boolean-Check
        return bool(value)

    completed = sum(1 for _, key in steps if is_step_complete(key))

    cols = st.columns(4)
    for i, ((name, key), col) in enumerate(zip(steps, cols)):
        with col:
            is_complete = is_step_complete(key)
            if is_complete:
                st.success(f"✅ {name.split()[0]}")
            else:
                st.info(f"○ {name.split()[0]}")

    progress = completed / len(steps)
    st.progress(progress, text=f"Workflow: {completed}/{len(steps)} Schritte abgeschlossen")


show_workflow_progress()

render_divider("section")

# Kompakte Info-Sektion
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 💡 eBKP-H")
    st.markdown("""
    Schweizer Standard für Baukostenstrukturierung mit 10.210 Codes über 5 Hierarchie-Levels.

    **Hauptgruppen:** A-G (Grundstück, Vorarbeiten, Rohbau, Technik, Ausbau, Umgebung, Nebenkosten)
    """)

with col2:
    st.markdown("### 🎯 Features")
    st.markdown("""
    - **Vollständiger Katalog**: Alle 10.210 eBKP-H Codes
    - **KI-Klassifizierung**: Claude 3.5 Haiku
    - **Validierung**: Gegen Schweizer Standard
    - **Flexibel**: 6 Kostenermittlungsstufen
    """)


# Footer
render_page_footer()
