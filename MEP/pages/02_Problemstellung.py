'''
Folie 3: Problemstellung
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
    render_big_number,
    render_content_box
)

# Page Init
init_slide_page("Problemstellung")

# === SLIDE START ===
start_slide(
    "Problemstellung",
    "Warum brauchen wir automatische Klassifizierung?",
    slide_number=3,
    total_slides=12
)

# Herausforderungen
st.markdown("### ⚠️ Herausforderungen der manuellen Klassifizierung")

col1, col2 = st.columns(2)

with col1:
    render_content_box("""
    <ul>
        <li><strong>Zeitaufwand:</strong> Stunden bis Tage pro Projekt</li>
        <li><strong>Fehleranfälligkeit:</strong> Inkonsistente Zuordnungen</li>
        <li><strong>Expertenwissen:</strong> Erfahrung mit eBKP-H erforderlich</li>
    </ul>
    """, "Manuelle Probleme")

with col2:
    render_content_box("""
    <ul>
        <li><strong>Geschwindigkeit:</strong> Sekunden statt Stunden</li>
        <li><strong>Konsistenz:</strong> Einheitliche Klassifizierung</li>
        <li><strong>Skalierbarkeit:</strong> Beliebig viele Elemente</li>
    </ul>
    """, "KI-Lösung")

render_divider()

# Vergleichschart
st.markdown("### 📊 Zeitvergleich: Manuell vs. Automatisch")

# Plotly Bar Chart
fig = go.Figure()

kategorien = ['100 Elemente', '500 Elemente', '1000 Elemente', '5000 Elemente']
manuell_zeit = [30, 150, 300, 1500]  # Minuten
auto_zeit = [0.5, 2, 4, 15]  # Minuten

fig.add_trace(go.Bar(
    name='Manuell',
    x=kategorien,
    y=manuell_zeit,
    marker_color='#f5576c',
    text=[f'{t} min' for t in manuell_zeit],
    textposition='outside'
))

fig.add_trace(go.Bar(
    name='Automatisch (KI)',
    x=kategorien,
    y=auto_zeit,
    marker_color='#43e97b',
    text=[f'{t} min' for t in auto_zeit],
    textposition='outside'
))

fig.update_layout(
    barmode='group',
    title='',
    yaxis_title='Zeit (Minuten)',
    xaxis_title='Anzahl Bauelemente',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    height=400,
    margin=dict(t=50, b=50),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)'
)

fig.update_yaxes(type='log')  # Logarithmische Skala wegen grossem Unterschied

st.plotly_chart(fig, width="stretch")

st.caption("*Geschätzte Werte basierend auf durchschnittlicher Bearbeitungszeit")

# === SLIDE END ===
end_slide()

# Navigation
render_slide_navigation(current_slide=3)
