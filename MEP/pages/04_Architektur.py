'''
Folie 5: Technische Architektur
'''

import streamlit as st
import os
import sys
import plotly.graph_objects as go

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
init_slide_page("Architektur")

# === SLIDE START ===
start_slide(
    "Technische Architektur",
    "3-stufige Pipeline für BIM-Datenverarbeitung",
    slide_number=5,
    total_slides=12
)

# 3 Stufen
st.markdown("### 🏗️ Die drei Verarbeitungsstufen")

col1, col2, col3 = st.columns(3)

with col1:
    render_gradient_card(
        "1. Datenextraktion",
        "Revit → pyRevit Extension<br><br>"
        "• Bauelemente auslesen<br>"
        "• Eigenschaften extrahieren<br>"
        "• Export als CSV",
        "purple",
        "📤"
    )

with col2:
    render_gradient_card(
        "2. Datenverarbeitung",
        "Python Backend<br><br>"
        "• Deduplizierung<br>"
        "• KI-Klassifizierung<br>"
        "• Validierung",
        "cyan",
        "⚙️"
    )

with col3:
    render_gradient_card(
        "3. Visualisierung",
        "Streamlit Frontend<br><br>"
        "• Interaktives Dashboard<br>"
        "• Kostenanalyse<br>"
        "• Export (CSV/PDF)",
        "green",
        "📊"
    )

render_divider()

# Sankey Diagramm
st.markdown("### 🔄 Datenfluss-Diagramm")

fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=[
            "Revit BIM",           # 0
            "pyRevit Script",      # 1
            "CSV Export",          # 2
            "Streamlit Upload",    # 3
            "Deduplizierung",      # 4
            "Claude AI",           # 5
            "Klassifizierte Daten",# 6
            "Validierung",         # 7
            "Dashboard",           # 8
            "PDF Export",          # 9
            "CSV Export"           # 10
        ],
        color=[
            "#667eea",  # Revit
            "#764ba2",  # pyRevit
            "#4facfe",  # CSV
            "#00f2fe",  # Upload
            "#43e97b",  # Dedup
            "#38f9d7",  # AI
            "#fee140",  # Klassifiziert
            "#fa709a",  # Validierung
            "#f5576c",  # Dashboard
            "#667eea",  # PDF
            "#764ba2"   # CSV Out
        ]
    ),
    link=dict(
        source=[0, 1, 2, 3, 4, 5, 6, 7, 8, 8],
        target=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        value=[10, 10, 10, 10, 8, 8, 8, 8, 4, 4],
        color=[
            "rgba(102, 126, 234, 0.4)",
            "rgba(118, 75, 162, 0.4)",
            "rgba(79, 172, 254, 0.4)",
            "rgba(0, 242, 254, 0.4)",
            "rgba(67, 233, 123, 0.4)",
            "rgba(56, 249, 215, 0.4)",
            "rgba(254, 225, 64, 0.4)",
            "rgba(250, 112, 154, 0.4)",
            "rgba(245, 87, 108, 0.4)",
            "rgba(102, 126, 234, 0.4)"
        ]
    )
)])

fig.update_layout(
    title_text="",
    font_size=12,
    height=400,
    margin=dict(t=20, b=20, l=20, r=20)
)

st.plotly_chart(fig, use_container_width=True)

render_divider()

# Technologie-Stack Details
st.markdown("### 🛠️ Eingesetzte Technologien")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Frontend**
    - Streamlit 1.x
    - Plotly Charts
    - Custom CSS
    """)

with col2:
    st.markdown("""
    **Backend**
    - Python 3.x
    - Pandas
    - Anthropic SDK
    """)

with col3:
    st.markdown("""
    **Integration**
    - pyRevit (Revit API)
    - Claude AI (Haiku)
    - CSV/PDF Export
    """)

# === SLIDE END ===
end_slide()

# Navigation
render_slide_navigation(current_slide=5)
