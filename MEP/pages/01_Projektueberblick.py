'''
Folie 2: Projektübersicht
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
    render_badges
)

# Page Init
init_slide_page("Projektübersicht")

# === SLIDE START ===
start_slide(
    "Projektübersicht",
    "Was macht eBKP-H⁺ und für wen?",
    slide_number=2,
    total_slides=12
)

# Projektziel
st.markdown("### 🎯 Projektziel")
st.markdown("""
**1. pyrevit Plugin für automatische Bauteilauswertung  \n2. Automatische eBKP-H Klassifizierung von BIM-Daten** mittels Künstlicher Intelligenz (Claude AI)  \n**3. Kostenberechnung**
""")

render_divider()

# Features als Cards
st.markdown("### ✨ Hauptfunktionen eBKP-H⁺")

col1, col2 = st.columns(2)

with col1:
    render_gradient_card(
        "KI-Klassifizierung",
        "Automatische Zuordnung von BIM-Elementen zu eBKP-H Codes mittels Claude AI",
        "purple",
        "🤖"
    )
    render_gradient_card(
        "Datenvalidierung",
        "Prüfung gegen den eBKP-H Katalog mit 10.210 Codes",
        "green",
        "✅"
    )

with col2:
    render_gradient_card(
        "Kostenoptimierung",
        "Batch-Verarbeitung und Deduplizierung für minimale API-Kosten",
        "cyan",
        "💰"
    )
    render_gradient_card(
        "Export & Reporting",
        "CSV und PDF Export der klassifizierten Daten",
        "orange",
        "📊"
    )

render_divider()

# Zielgruppe und Tech Stack
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 👥 Zielgruppe")
    st.markdown("""
    - **Baumanagement** - Effiziente Massenermittlung und schnelle Kostenschätzungen
    - **BIM-Koordinatoren** - Datenqualitätssicherung
    """)

with col2:
    st.markdown("### 🛠️ Technologie-Stack")
    render_badges([
        ("Python", "primary"),
        ("Streamlit", "info"),
        ("Claude AI", "success"),
        ("Plotly", "warning"),
        ("pyRevit", "info")
    ])

# === SLIDE END ===
end_slide()

# Navigation
render_slide_navigation(current_slide=2)
