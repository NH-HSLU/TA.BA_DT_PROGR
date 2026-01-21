'''
Folie 4: eBKP-H Erklärung
'''

import streamlit as st
import os
import sys
import plotly.express as px
import pandas as pd

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
    render_content_box
)

# Page Init
init_slide_page("eBKP-H Erklärung")

# === SLIDE START ===
start_slide(
    "Was ist eBKP-H?",
    "Der Schweizer Standard für Baukostenstrukturierung",
    slide_number=4,
    total_slides=12
)

# Erklärung
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📋 Definition")
    st.markdown("""
    **eBKP-H** (elementbasierter Baukostenplan Hochbau) ist der Schweizer Standard
    zur Strukturierung von Baukosten nach Bauelementen.

    Er wird herausgegeben vom **CRB** (Schweizerische Zentralstelle für Baurationalisierung)
    und ist in der Schweizer Baubranche weit verbreitet.
    """)

    st.markdown("### 🏗️ Hauptgruppen")
    hauptgruppen = """
    | Code | Bezeichnung |
    |------|-------------|
    | **A** | Grundstück |
    | **B** | Vorbereitungsarbeiten |
    | **C** | Konstruktion Baukörper |
    | **D** | Technik |
    | **E** | Äussere Wandbekleidung |
    | **F** | Bedachung |
    | **G** | Ausbau |
    """
    st.markdown(hauptgruppen)

with col2:
    st.markdown("### 📊 Hierarchie-Struktur")

    # Treemap Daten
    data = {
        'labels': [
            'eBKP-H',
            'C - Konstruktion', 'D - Technik', 'G - Ausbau',
            'C1 - Fundation', 'C2 - Wände', 'C3 - Stützen',
            'D1 - Elektro', 'D2 - Heizung', 'D3 - Lüftung',
            'G1 - Bodenbeläge', 'G2 - Wandbeläge'
        ],
        'parents': [
            '',
            'eBKP-H', 'eBKP-H', 'eBKP-H',
            'C - Konstruktion', 'C - Konstruktion', 'C - Konstruktion',
            'D - Technik', 'D - Technik', 'D - Technik',
            'G - Ausbau', 'G - Ausbau'
        ],
        'values': [100, 30, 25, 20, 10, 12, 8, 10, 8, 7, 12, 8]
    }

    fig = px.treemap(
        data,
        names='labels',
        parents='parents',
        values='values',
        color_discrete_sequence=['#667eea', '#764ba2', '#4facfe', '#43e97b', '#fee140', '#f5576c']
    )

    fig.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        height=350
    )

    st.plotly_chart(fig, use_container_width=True)

render_divider()

# 5 Ebenen erklärt
st.markdown("### 🔢 Die 5 Hierarchie-Ebenen")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 0.5rem; color: white;">
        <div style="font-size: 2rem; font-weight: bold;">C</div>
        <div style="font-size: 0.8rem;">Ebene 1<br>Hauptgruppe</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                border-radius: 0.5rem; color: white;">
        <div style="font-size: 2rem; font-weight: bold;">C2</div>
        <div style="font-size: 0.8rem;">Ebene 2<br>Elementgruppe</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                border-radius: 0.5rem; color: white;">
        <div style="font-size: 2rem; font-weight: bold;">C2.1</div>
        <div style="font-size: 0.8rem;">Ebene 3<br>Element</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                border-radius: 0.5rem; color: white;">
        <div style="font-size: 2rem; font-weight: bold;">C2.1.1</div>
        <div style="font-size: 0.8rem;">Ebene 4<br>Teilelement</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                border-radius: 0.5rem; color: white;">
        <div style="font-size: 2rem; font-weight: bold;">C2.1.1.1</div>
        <div style="font-size: 0.8rem;">Ebene 5<br>Unterposition</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

render_content_box(
    "Beispiel: <strong>C2.1.1.1</strong> = Konstruktion → Wände aussen tragend → Wandkonstruktion → "
    "Mauerwerk → Backstein",
    "Hierarchie-Beispiel"
)

# === SLIDE END ===
end_slide()

# Navigation
render_slide_navigation(current_slide=4)
