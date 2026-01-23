'''
Folie 13: Fragen
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
    get_base_css,
    render_divider,
    get_logo_html
)

# Page Init
init_slide_page("Fragen")

# Basis CSS + Custom CSS für diese Folie
st.markdown(get_base_css(), unsafe_allow_html=True)
st.markdown("""
<style>
    .big-question {
        font-size: 10rem;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
        margin-bottom: 0.5rem;
    }

    .thank-you {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1.5rem;
    }

    .contact-info {
        text-align: center;
        font-size: 1rem;
        line-height: 1.8;
        opacity: 0.8;
    }

    .github-link {
        display: inline-block;
        padding: 0.6rem 1.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-decoration: none;
        border-radius: 2rem;
        font-weight: 500;
        margin-top: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .github-link:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Foliennummer
st.markdown('<div class="slide-number">12 / 12</div>', unsafe_allow_html=True)

# Grosses Fragezeichen
st.markdown('<div class="big-question">?</div>', unsafe_allow_html=True)

# Vielen Dank
st.markdown('<div class="thank-you">Vielen Dank für Ihre Aufmerksamkeit!</div>', unsafe_allow_html=True)

render_divider()

# Kontakt & Links
st.markdown("""
<div class="contact-info">
    <strong>Nicole Hitz & Orlando Bassi</strong><br>
    TA.BA_DT_PROGR_MM - Digital Twin Programmieren<br>
    Hochschule Luzern - Technik & Architektur<br>
    <br>
    <a href="https://github.com/NH-HSLU/TA.BA_DT_PROGR" target="_blank" class="github-link">
        📂 GitHub Repository
    </a>
</div>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Logo am Ende
streamlit_dir = os.path.join(parent_dir, '..', 'Streamlit')
logo_hell = os.path.join(streamlit_dir, "Logo_hell.png")
logo_dunkel = os.path.join(streamlit_dir, "Logo_dunkel.png")

logo_html = get_logo_html(logo_hell, logo_dunkel, max_width="180px")
st.markdown(logo_html, unsafe_allow_html=True)

# Navigation (nur zurück)
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("← Zurück", key="nav_prev", width="stretch"):
        st.switch_page("pages/11_Zusammenfassung.py")

with col2:
    st.markdown("""
    <div class="nav-info" style="text-align: center;">
        ● Folie 12 von 12 - Ende ●
    </div>
    """, unsafe_allow_html=True)

with col3:
    if st.button("🏠 Zum Anfang", key="nav_home", width="stretch"):
        st.switch_page("praesentation_app.py")
