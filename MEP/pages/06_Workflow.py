'''
Folie 7: Workflow
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
    render_divider
)

# Page Init
init_slide_page("Workflow")

# === SLIDE START ===
start_slide(
    "Anwendungs-Workflow",
    "Die 4 Hauptschritte in des Programms eBKP-H⁺",
    slide_number=7,
    total_slides=12
)

# CSS für Workflow Cards (ähnlich wie im Dashboard)
st.markdown("""
<style>
    .workflow-card {
        padding: 1.5rem;
        border-radius: 0.75rem;
        text-align: center;
        margin: 0.5rem 0;
        transition: transform 0.2s, box-shadow 0.2s;
        color: white;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .workflow-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    }
    .workflow-card h3 {
        font-size: 1.4rem;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .workflow-card p {
        font-size: 0.95rem;
        opacity: 0.95;
        line-height: 1.6;
    }
    .workflow-card .icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Workflow Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="workflow-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
        <div class="icon">📋</div>
        <h3>1. Kostenermittlung</h3>
        <p>
            Projektphase wählen<br>
            nach SIA LHO 102<br>
            <br>
            Genauigkeit:<br>
            ±10% bis ±30%
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="workflow-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
        <div class="icon">🤖</div>
        <h3>2. KI-Klassifizierung</h3>
        <p>
            CSV hochladen<br>
            Automatisch klassifizieren<br>
            <br>
            Mit Claude AI<br>
            (Haiku Modell)
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="workflow-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
        <div class="icon">✏️</div>
        <h3>3. BKP Bearbeiten</h3>
        <p>
            Codes überprüfen<br>
            Manuell korrigieren<br>
            <br>
            Gegen eBKP-H<br>
            Katalog validieren
        </p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="workflow-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
        <div class="icon">📊</div>
        <h3>4. Auswertung</h3>
        <p>
            Hierarchie anzeigen<br>
            Kosten analysieren<br>
            <br>
            Export als<br>
            CSV oder PDF
        </p>
    </div>
    """, unsafe_allow_html=True)

render_divider()

# Progress Flow
st.markdown("### 🔄 Typischer Ablauf")

st.markdown("""
<div style="display: flex; justify-content: center; align-items: center; gap: 0.5rem; flex-wrap: wrap; padding: 1rem;">
    <div style="background: #667eea; color: white; padding: 0.8rem 1.2rem; border-radius: 2rem; font-weight: 500;">
        CSV Upload
    </div>
    <div style="font-size: 1.5rem; color: #667eea;">→</div>
    <div style="background: #4facfe; color: white; padding: 0.8rem 1.2rem; border-radius: 2rem; font-weight: 500;">
        Deduplizierung
    </div>
    <div style="font-size: 1.5rem; color: #4facfe;">→</div>
    <div style="background: #43e97b; color: white; padding: 0.8rem 1.2rem; border-radius: 2rem; font-weight: 500;">
        KI-Klassifizierung
    </div>
    <div style="font-size: 1.5rem; color: #43e97b;">→</div>
    <div style="background: #fee140; color: #333; padding: 0.8rem 1.2rem; border-radius: 2rem; font-weight: 500;">
        Validierung
    </div>
    <div style="font-size: 1.5rem; color: #fee140;">→</div>
    <div style="background: #f5576c; color: white; padding: 0.8rem 1.2rem; border-radius: 2rem; font-weight: 500;">
        Export
    </div>
</div>
""", unsafe_allow_html=True)

render_divider()

# Optionale Schritte
st.markdown("### 📌 Optionale Funktionen")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("**Projektinformationen**\n\nBauherr, Projektname und Stammdaten erfassen")

with col2:
    st.info("**Manuelle Korrektur**\n\nNiedrige Konfidenzwerte manuell überprüfen")

with col3:
    st.info("**Kostenberechnung**\n\nMit Kennwerten aus dem eBKP-H Katalog")

# === SLIDE END ===
end_slide()

# Navigation
render_slide_navigation(current_slide=7)
