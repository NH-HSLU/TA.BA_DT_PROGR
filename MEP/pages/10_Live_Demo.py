'''
Folie 10: Live Demo
'''

import streamlit as st
import os
import sys
import subprocess

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
    render_gradient_card
)

# Page Init
init_slide_page("Live Demo")

# === SLIDE START ===
start_slide(
    "Live Demo",
    "Die eBKP-H+ Suite in Aktion",
    slide_number=10,
    total_slides=12
)

# Demo Button
st.markdown("### 🚀 Hauptanwendung starten")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    

    st.markdown("<br>", unsafe_allow_html=True)

    # Button zum Starten der App
    if st.button("🚀 eBKP-H⁺ starten", type="primary", use_container_width=True):
        # Pfad zur Hauptapp
        streamlit_app = os.path.abspath(os.path.join(parent_dir, '..', 'Streamlit', 'streamlit_app.py'))

        # Starte auf Port 8502 (da Präsentation auf 8501 läuft)
        try:
            subprocess.Popen(
                ['streamlit', 'run', streamlit_app, '--server.port', '8502'],
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            st.success("✅ App wird gestartet!")
            st.markdown("""
            <div style="text-align: center; padding: 1rem; background: rgba(67, 233, 123, 0.1); border-radius: 0.5rem; margin-top: 1rem;">
                <a href="http://localhost:8502" target="_blank" style="font-size: 1.2rem; color: #667eea; font-weight: bold;">
                    🔗 http://localhost:8502 öffnen
                </a>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Fehler beim Starten: {e}")
            st.markdown("""
            **Manueller Start:**
            ```bash
            cd Streamlit
            streamlit run streamlit_app.py --server.port 8502
            ```
            """)

render_divider()

# Demo-Szenarien
st.markdown("### 📋 Demo-Szenarien")

col1, col2, col3 = st.columns(3)

with col1:
    render_gradient_card(
        "Szenario 1",
        "<strong>CSV Upload</strong><br><br>"
        "1. Zur KI-Klassifizierung navigieren<br>"
        "2. Beispiel-CSV hochladen<br>"
        "3. Datenvorschau prüfen",
        "purple",
        "📤"
    )

with col2:
    render_gradient_card(
        "Szenario 2",
        "<strong>Klassifizierung</strong><br><br>"
        "1. API-Key eingeben<br>"
        "2. Klassifizierung starten<br>"
        "3. Fortschritt beobachten",
        "cyan",
        "🤖"
    )

with col3:
    render_gradient_card(
        "Szenario 3",
        "<strong>Auswertung</strong><br><br>"
        "1. Ergebnisse visualisieren<br>"
        "2. eBKP-Hierarchie erkunden<br>"
        "3. Als PDF exportieren",
        "green",
        "📊"
    )

render_divider()

# Screenshots / Features
st.markdown("### 🖼️ Hauptfunktionen")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Dashboard**
    - Workflow-Übersicht
    - Fortschrittsanzeige
    - Schnellzugriff auf alle Funktionen

    **KI-Klassifizierung**
    - Drag & Drop Upload
    - Batch-Verarbeitung
    - Live API-Monitoring
    """)

with col2:
    st.markdown("""
    **eBKP Bearbeiten**
    - Inline-Editing
    - Code-Validierung
    - Konfidenz-Filter

    **Auswertung**
    - Hierarchische Darstellung
    - Interaktive Charts
    - PDF/CSV Export
    """)

# === SLIDE END ===
end_slide()

# Navigation
render_slide_navigation(current_slide=10)
