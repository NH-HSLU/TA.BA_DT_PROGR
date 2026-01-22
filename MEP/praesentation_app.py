'''
MEP Präsentation - Titelfolie
eBKP-H+ BIM Kostenklassifizierung
'''

import streamlit as st
import os
import sys

# Pfad-Setup für Imports
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from helpers.presentation_helpers import get_base_css, get_logo_html

# Seitenkonfiguration
st.set_page_config(
    page_title="MEP Präsentation - eBKP-H⁺",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS
st.markdown(get_base_css(), unsafe_allow_html=True)

# Zusätzliches CSS für Titelfolie
st.markdown("""
<style>
    .title-slide-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 1rem 0 0.5rem 0;
    }

    .title-slide-subtitle {
        font-size: 1.2rem;
        text-align: center;
        opacity: 0.8;
        margin-bottom: 1.5rem;
    }

    .title-slide-info {
        text-align: center;
        opacity: 0.7;
        font-size: 0.95rem;
        line-height: 1.7;
    }

    .title-slide-authors {
        font-size: 1.05rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Foliennummer
st.markdown('<div class="slide-number">1 / 12</div>', unsafe_allow_html=True)

# Logo (aus Streamlit-Ordner)
streamlit_dir = os.path.join(current_dir, '..', 'Streamlit')
logo_hell = os.path.join(streamlit_dir, "Logo_hell.png")
logo_dunkel = os.path.join(streamlit_dir, "Logo_dunkel.png")

# Logo anzeigen
logo_html = get_logo_html(logo_hell, logo_dunkel, max_width="300px")
st.markdown(logo_html, unsafe_allow_html=True)

# Titel
st.markdown("""
<div class="title-slide-title">eBKP-H⁺ BIM Kostenklassifizierung</div>
<div class="title-slide-subtitle">Automatische eBKP-H Klassifizierung von BIM-Daten mit KI inkl. Kostenberechnung</div>
""", unsafe_allow_html=True)

# Info
st.markdown("""
<div class="title-slide-info">
    <div class="title-slide-authors">
        <strong>Nicole Hitz & Orlando Bassi</strong>
    </div>
    <br>
    TA.BA_DT_PROGR_MM - Digital Twin Programmieren<br>
    Hochschule Luzern - Technik & Architektur<br>
    <br>
    Modulendprüfung - 27. Januar 2026
</div>
""", unsafe_allow_html=True)

# Navigation / Start Button
st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("▶ Präsentation starten", type="primary", width="stretch"):
        st.switch_page("pages/01_Projektueberblick.py")
