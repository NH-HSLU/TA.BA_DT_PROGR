'''
Folie 11: Zusammenfassung
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
    render_gradient_card,
    render_big_number
)

# Page Init
init_slide_page("Zusammenfassung")

# === SLIDE START ===
start_slide(
    "Zusammenfassung",
    "Was wir erreicht haben und was wir gelernt haben",
    slide_number=11,
    total_slides=12
)

# Erreichte Ziele
st.markdown("### ✅ Erreichte Ziele")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    - [x] **Automatische eBKP-Klassifizierung** mit Claude AI
    - [x] **Vollständiger Workflow** von Upload bis Export
    - [x] **Kostenoptimierte API-Nutzung** (Batch, Caching)
    - [x] **Validierung** gegen offiziellen eBKP-H Katalog
    """)

with col2:
    st.markdown("""
    - [x] **Benutzerfreundliches UI** mit Streamlit
    - [x] **Manuelle Korrekturmöglichkeit** für niedrige Konfidenz
    - [x] **Export-Funktionen** (CSV, PDF)
    - [x] **Session State Management** für Datenfluss
    """)

render_divider()

# Kennzahlen
st.markdown("### 📊 Projekt-Kennzahlen")

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_big_number("10'210", "eBKP-H Codes unterstützt")

with col2:
    render_big_number("13", "Streamlit Seiten")

with col3:
    render_big_number("~95%", "Kosteneinsparung möglich")

with col4:
    render_big_number("5", "Hierarchie-Ebenen")

render_divider()

# Lessons Learned
st.markdown("### 💡 Lessons Learned")

col1, col2 = st.columns(2)

with col1:
    render_gradient_card(
        "Technisch",
        "• Streamlit eignet sich hervorragend für Daten-Apps<br>"
        "• Session State ist essentiell für Multi-Page Apps<br>"
        "• Prompt Engineering macht einen grossen Unterschied<br>"
        "• Batch-Verarbeitung spart erheblich Kosten",
        "purple",
        "⚙️"
    )

with col2:
    render_gradient_card(
        "Prozess",
        "• Frühes Testen mit echten Daten wichtig<br>"
        "• Iterative Entwicklung funktioniert gut<br>"
        "• Dokumentation parallel zur Entwicklung<br>"
        "• Git-Workflow erleichtert Zusammenarbeit",
        "cyan",
        "📝"
    )

render_divider()

# Mögliche Erweiterungen
st.markdown("### 🔮 Mögliche Erweiterungen")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **IFC-Integration**

    Direktes Einlesen von IFC-Dateien ohne Umweg über Revit/CSV
    """)

with col2:
    st.info("""
    **Kostenberechnung**

    Integration von Kennwerten für automatische Kostenschätzung
    """)

with col3:
    st.info("""
    **ML Fine-Tuning**

    Training eines spezialisierten Modells für höhere Genauigkeit
    """)

# === SLIDE END ===
end_slide()

# Navigation
render_slide_navigation(current_slide=11)
