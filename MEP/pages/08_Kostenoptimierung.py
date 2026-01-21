'''
Folie 9: Kostenoptimierung
'''

import streamlit as st
import os
import sys
import plotly.graph_objects as go
import plotly.express as px

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
    render_big_number,
    render_content_box
)

# Page Init
init_slide_page("Kostenoptimierung")

# === SLIDE START ===
start_slide(
    "Kostenoptimierung",
    "Wie wir API-Kosten minimieren",
    slide_number=9,
    total_slides=13
)

# Token-Preise
st.markdown("### 💰 Claude API Preise (pro 1M Tokens)")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                border-radius: 0.75rem; color: white;">
        <div style="font-size: 0.9rem; opacity: 0.9;">Haiku 3.5</div>
        <div style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">$1.00</div>
        <div style="font-size: 0.8rem;">Input Tokens</div>
        <div style="font-size: 1.2rem; font-weight: bold; margin-top: 0.3rem;">$5.00</div>
        <div style="font-size: 0.8rem;">Output Tokens</div>
    </div>
    """, unsafe_allow_html=True)
    st.success("✓ Unsere Wahl")

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                border-radius: 0.75rem; color: white;">
        <div style="font-size: 0.9rem; opacity: 0.9;">Sonnet 3.5</div>
        <div style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">$3.00</div>
        <div style="font-size: 0.8rem;">Input Tokens</div>
        <div style="font-size: 1.2rem; font-weight: bold; margin-top: 0.3rem;">$15.00</div>
        <div style="font-size: 0.8rem;">Output Tokens</div>
    </div>
    """, unsafe_allow_html=True)
    st.info("3x teurer")

with col3:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 0.75rem; color: white;">
        <div style="font-size: 0.9rem; opacity: 0.9;">Opus 3</div>
        <div style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">$15.00</div>
        <div style="font-size: 0.8rem;">Input Tokens</div>
        <div style="font-size: 1.2rem; font-weight: bold; margin-top: 0.3rem;">$75.00</div>
        <div style="font-size: 0.8rem;">Output Tokens</div>
    </div>
    """, unsafe_allow_html=True)
    st.warning("15x teurer")

render_divider()

# Optimierungsstrategien
st.markdown("### 🎯 Unsere Optimierungsstrategien")

col1, col2 = st.columns(2)

with col1:
    # Pie Chart für Einsparungen
    labels = ['Regulärer Preis', 'Batch API (-50%)', 'Prompt Cache (-90%)', 'Deduplizierung']
    values = [100, 50, 10, 30]
    colors = ['#f5576c', '#fee140', '#43e97b', '#4facfe']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker_colors=colors,
        textinfo='label+percent',
        textposition='outside'
    )])

    fig.update_layout(
        title='Kostenverteilung mit Optimierungen',
        showlegend=False,
        height=350,
        margin=dict(t=50, b=20, l=20, r=20)
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:
    render_content_box("""
    <strong>1. Batch API (50% Rabatt)</strong><br>
    Asynchrone Verarbeitung für grosse Datenmengen<br><br>

    <strong>2. Prompt Caching (90% Rabatt)</strong><br>
    Wiederverwendung des System-Prompts<br><br>

    <strong>3. Deduplizierung</strong><br>
    Identische Elemente nur einmal klassifizieren<br><br>

    <strong>4. Kurze Prompts</strong><br>
    Minimale Token-Anzahl pro Request
    """, "Strategien")

render_divider()

# Rechenbeispiel
st.markdown("### 📊 Rechenbeispiel: 1000 Bauelemente")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Ohne Optimierung**")
    st.markdown("""
    - 1000 einzelne Requests
    - ~500 Tokens pro Request
    - **500'000 Input Tokens**
    - Kosten: **~$0.50**
    """)

with col2:
    st.markdown("**Mit Optimierung**")
    st.markdown("""
    - 300 unique Elemente (Deduplizierung)
    - Batch API + Prompt Caching
    - **~50'000 Input Tokens**
    - Kosten: **~$0.025** ✅
    """)

# Einsparung visualisieren
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    render_big_number("95%", "Kosteneinsparung möglich")

# === SLIDE END ===
end_slide()

# Navigation
render_slide_navigation(current_slide=9)
