'''
Art der Kostenermittlung nach SIA LHO 102
Auswahl der Kostenermittlungsstufe, die BKP-Klassifizierungstiefe und Toleranz beeinflusst.
'''

import streamlit as st
import sys
import os
from datetime import datetime

# Füge Parent-Verzeichnis zum Path hinzu für Imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from Streamlit.helpers.sia_lho_102_config import (
    COST_ESTIMATION_LEVELS,
    get_level_config,
    format_tolerance,
    get_all_levels
)

# Seitenkonfiguration
st.set_page_config(
    page_title="Kostenermittlung",
    page_icon="🏗️",
    layout="wide"
)


def select_level(level: int):
    """Speichert ausgewähltes Level in Session State"""
    config = get_level_config(level)

    if config:
        st.session_state.cost_estimation_config = {
            'selected': True,
            'level': config['level'],
            'name': config['name'],
            'tolerance': config['tolerance'],
            'ebkp_depth': config['ebkp_depth'],
            'ebkp_levels': config['ebkp_levels'],
            'project_phase': config['project_phase'],
            'phase_code': config['phase_code'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        st.success(f"✅ Ausgewählt: {config['name']} ({format_tolerance(config['tolerance'])})")
        st.balloons()


# Haupttitel
st.markdown('<p style="font-size: 2.5rem; font-weight: bold; text-align: center;">🏗️ Art der Kostenermittlung</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.1rem; opacity: 0.7; margin-bottom: 2rem;">nach SIA LHO 102 Standard</p>', unsafe_allow_html=True)

st.markdown("---")

# Zeige aktuelle Auswahl (falls vorhanden)
if 'cost_estimation_config' in st.session_state and st.session_state.cost_estimation_config.get('selected'):
    config = st.session_state.cost_estimation_config

    st.success(f"**Aktuelle Auswahl:** {config['name']}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("⚖️ Toleranz", f"± {config['tolerance']}%")
    with col2:
        st.metric("🏗️ Projektphase", config['project_phase'])
    with col3:
        st.metric("📊 eBKP-Tiefe", config['ebkp_depth'])
    with col4:
        st.metric("📅 Phase", config['phase_code'])

    st.info("💡 Sie können Ihre Auswahl jederzeit ändern, indem Sie unten eine andere Stufe wählen.")
    st.markdown("---")

# Custom CSS für Card-Styling
st.markdown("""
<style>
.cost-card {
    padding: 0.8rem;
    border-radius: 0.5rem;
    margin: 0.3rem 0;
    text-align: center;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}
.cost-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.cost-card-selected {
    border: 2px solid #00cc00;
    box-shadow: 0 0 15px rgba(0,204,0,0.3);
}
.cost-card-level-1 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
.cost-card-level-2 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }
.cost-card-level-3 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; }
.cost-card-level-4 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; }
.cost-card-level-5 { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; }
.cost-card-level-6 { background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); color: white; }
.card-title { font-size: 0.95rem; font-weight: bold; margin-bottom: 0.3rem; }
.card-tolerance { font-size: 0.85rem; font-weight: bold; margin: 0.2rem 0; }
.card-phase { font-size: 0.75rem; opacity: 0.9; }
</style>
""", unsafe_allow_html=True)


# Hinweis zur Auswirkung
st.info("""
ℹ️ **Wichtig:** Die gewählte Kostenermittlungsart beeinflusst:
- **BKP-Klassifizierungstiefe**: Höhere Genauigkeit = detailliertere BKP-Codes (mehr Levels)
- **Qualitätsindikator**: Wird in Auswertungen angezeigt
- **Toleranzbereich**: Wird bei Kostenangaben berücksichtigt
""")

st.markdown("---")

# Auswahl der Stufen als Abo-Selector
st.header("📐 Wählen Sie Ihre Kostenermittlungsstufe")
st.caption("Klicken Sie auf eine Stufe, um Details zu sehen und auszuwählen")

# Prüfe welches Level aktuell ausgewählt ist
current_level = None
if 'cost_estimation_config' in st.session_state:
    current_level = st.session_state.cost_estimation_config.get('level')

# Alle 6 Levels nebeneinander als Abo-Selector
cols = st.columns(6)

for i, config in enumerate(COST_ESTIMATION_LEVELS):
    with cols[i]:
        is_selected = current_level == config['level']
        selected_class = " cost-card-selected" if is_selected else ""

        # Kürze den Namen für bessere Darstellung
        short_name = config['name'].replace('Schätzung des ', '').replace('Schätzung der ', '')

        card_html = f"""
        <div class="cost-card cost-card-level-{config['level']}{selected_class}">
            <div class="card-title" style="font-size: 1.1rem; line-height: 1.2; min-height: 2.5rem;">{short_name}</div>
            <div class="card-tolerance">{format_tolerance(config['tolerance'])}</div>
            <div class="card-phase" style="font-size: 0.7rem;">{config['phase_code']}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        if st.button("Wählen", key=f"btn_{config['level']}", use_container_width=True):
            st.session_state.selected_for_details = config['level']

st.markdown("---")

# Details-Bereich für ausgewählte Stufe
if 'selected_for_details' in st.session_state:
    st.markdown("---")
    selected_config = get_level_config(st.session_state.selected_for_details)

    if selected_config:
        st.subheader(f"📋 Details: {selected_config['name']}")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**{selected_config['emoji']} {selected_config['name']}**")
            st.markdown(f"**Projektphase:** {selected_config['project_phase']} ({selected_config['phase_code']})")
            st.markdown(f"**eBKP-Klassifizierungstiefe:** {selected_config['ebkp_depth']}")
            st.markdown(f"**Toleranz:** {format_tolerance(selected_config['tolerance'])}")
            st.markdown(f"**Beschreibung:** {selected_config['description']}")

            # Zeige welche CSV Levels verwendet werden
            levels_str = ", ".join([f"Level {l}" for l in selected_config['ebkp_levels']])
            st.caption(f"Verwendet eBKP-H CSV Levels: {levels_str}")

        with col2:
            is_currently_selected = current_level == selected_config['level']

            if is_currently_selected:
                st.success("✅ Aktuell gewählt")
                if st.button("🔄 Erneut bestätigen", key="confirm_current", use_container_width=True):
                    select_level(selected_config['level'])
            else:
                if st.button("✓ Diese Stufe wählen", key="select_from_details", type="primary", use_container_width=True):
                    select_level(selected_config['level'])
                    del st.session_state.selected_for_details
                    st.rerun()

st.markdown("---")

# Nächste Schritte
st.header("➡️ Nächste Schritte")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 1️⃣ Daten vorbereiten
    - Exportieren Sie Ihre Daten aus Revit
    - Speichern Sie als CSV
    """)

with col2:
    st.markdown("""
    ### 2️⃣ Klassifizieren
    - Gehen Sie zu **KI Klassifizierung**
    - Laden Sie Ihre CSV hoch
    - Starten Sie die Klassifizierung
    """)

with col3:
    st.markdown("""
    ### 3️⃣ Auswerten
    - Gehen Sie zu **eBKP-H Auswertung**
    - Prüfen Sie die Ergebnisse
    - Exportieren Sie Berichte
    """)

# Navigation Buttons
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏠 Zur Startseite", use_container_width=True):
        st.switch_page("streamlit_app.py")

with col2:
    if st.button("🤖 Zur KI Klassifizierung", use_container_width=True):
        st.switch_page("pages/2_KI_Klassifizierung.py")

with col3:
    if st.button("📊 Zur eBKP-H Auswertung", use_container_width=True):
        st.switch_page("pages/1_eBKP_Auswertung.py")

# Sidebar
with st.sidebar:
    st.header("ℹ️ Über SIA LHO 102")

    st.markdown("""
    Die SIA LHO 102 definiert verschiedene Stufen der Kostenermittlung
    während des Projektablaufs:

    - **TP11**: Strategische Planung
    - **TP21/22**: Vorstudie
    - **TP31**: Studium/Vorprojekt
    - **TP32/33**: Bauprojekt
    - **TP41, TP51-53**: Ausschreibung/Realisierung

    Jede Stufe hat eine definierte **Toleranz** und erfordert eine
    entsprechende **Detaillierungstiefe** der BKP-Klassifizierung.
    """)

    st.markdown("---")

    if 'cost_estimation_config' in st.session_state and st.session_state.cost_estimation_config.get('selected'):
        config = st.session_state.cost_estimation_config
        st.success(f"✅ {config['name']}")
        st.caption(f"Ausgewählt am: {config['timestamp']}")
    else:
        st.warning("⚠️ Noch keine Auswahl getroffen")
