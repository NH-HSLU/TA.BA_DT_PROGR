'''
Folie 6: Datenfluss
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
    render_code_block,
    render_content_box
)

# Page Init
init_slide_page("Datenfluss")

# === SLIDE START ===
start_slide(
    "Datenfluss",
    "Von Revit bis zum fertigen Report",
    slide_number=6,
    total_slides=12
)

# Flow Diagram mit Plotly
st.markdown("### 📊 Pipeline-Übersicht")

# Erstelle ein horizontales Flow-Diagramm
fig = go.Figure()

# Positionen
x_pos = [0, 1, 2, 3, 4, 5]
y_pos = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
labels = ['Revit\nBIM-Modell', 'pyRevit\nExport', 'CSV\nDatei', 'Streamlit\nUpload', 'Claude AI\nKlassifizierung', 'Export\nPDF/CSV']
colors = ['#667eea', '#764ba2', '#4facfe', '#43e97b', '#fee140', '#f5576c']

# Nodes
for i, (x, y, label, color) in enumerate(zip(x_pos, y_pos, labels, colors)):
    fig.add_trace(go.Scatter(
        x=[x], y=[y],
        mode='markers+text',
        marker=dict(size=80, color=color, line=dict(color='white', width=2)),
        text=[label],
        textposition='middle center',
        textfont=dict(color='white', size=11),
        hoverinfo='text',
        hovertext=label.replace('\n', ' ')
    ))

# Pfeile zwischen Nodes
for i in range(len(x_pos) - 1):
    fig.add_annotation(
        x=x_pos[i+1] - 0.15, y=y_pos[i],
        ax=x_pos[i] + 0.15, ay=y_pos[i],
        xref='x', yref='y', axref='x', ayref='y',
        showarrow=True,
        arrowhead=2,
        arrowsize=1.5,
        arrowwidth=2,
        arrowcolor='#667eea'
    )

fig.update_layout(
    showlegend=False,
    xaxis=dict(visible=False, range=[-0.5, 5.5]),
    yaxis=dict(visible=False, range=[0, 1]),
    height=250,
    margin=dict(l=20, r=20, t=20, b=20),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)'
)

st.plotly_chart(fig, width="stretch")

render_divider()

# CSV Struktur
st.markdown("### 📄 CSV-Datenstruktur")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Input CSV (aus Revit)**")
    render_code_block('''Typ,Familie,Fläche,Raum
Wand,Aussenwand 30cm,45.2,Wohnzimmer
Decke,Betondecke,28.5,Wohnzimmer
Fenster,Holz-Alu 2-fach,3.2,Wohnzimmer
Steckdose,T13 3-fach,0.02,Küche''', "csv", "beispiel_input.csv")

with col2:
    st.markdown("**Output CSV (klassifiziert)**")
    render_code_block('''Typ,Familie,Fläche,Raum,eBKP_Code,Konfidenz
Wand,Aussenwand 30cm,45.2,Wohnzimmer,C2.1,0.95
Decke,Betondecke,28.5,Wohnzimmer,C4.1,0.92
Fenster,Holz-Alu 2-fach,3.2,Wohnzimmer,E1.2,0.88
Steckdose,T13 3-fach,0.02,Küche,D5.2,0.91''', "csv", "beispiel_output.csv")

render_divider()

# Verarbeitungsschritte
st.markdown("### ⚙️ Verarbeitungsschritte im Detail")

steps = [
    ("1️⃣ Upload", "CSV-Datei hochladen und validieren"),
    ("2️⃣ Deduplizierung", "Identische Elemente zusammenfassen (Token sparen)"),
    ("3️⃣ Batch-Bildung", "Elemente in optimale Gruppen aufteilen"),
    ("4️⃣ KI-Klassifizierung", "Claude AI ordnet eBKP-Codes zu"),
    ("5️⃣ Validierung", "Codes gegen eBKP-H Katalog prüfen"),
    ("6️⃣ Re-Expansion", "Deduplizierte Ergebnisse zurückmappen"),
    ("7️⃣ Export", "PDF oder CSV generieren")
]

cols = st.columns(len(steps))
for col, (title, desc) in zip(cols, steps):
    with col:
        st.markdown(f"""
        <div style="text-align: center; padding: 0.5rem;">
            <div style="font-size: 1.5rem; margin-bottom: 0.3rem;">{title.split()[0]}</div>
            <div style="font-size: 0.75rem; opacity: 0.8;">{title.split(maxsplit=1)[1]}</div>
        </div>
        """, unsafe_allow_html=True)

# === SLIDE END ===
end_slide()

# Navigation
render_slide_navigation(current_slide=6)
