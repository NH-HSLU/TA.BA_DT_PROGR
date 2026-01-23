'''
Art der Kostenermittlung nach SIA LHO 102
Auswahl der Kostenermittlungsstufe, die BKP-Klassifizierungstiefe und Toleranz beeinflusst.
'''

import streamlit as st
import sys
import os
from datetime import datetime

# Füge Parent-Verzeichnis zum Path hinzu für Imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from helpers.sia_lho_102_config import (
    COST_ESTIMATION_LEVELS,
    get_level_config,
    format_tolerance
)
from helpers.sidebar_navigation import render_sidebar, render_page_header, render_divider, render_page_footer
from helpers.notifications import toast, NotificationType
from helpers.session_state import (
    init_session_state,
    get_state,
    set_state,
    CFG_COST_ESTIMATION_CONFIG,
    UI_SELECTED_FOR_DETAILS
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from helpers_shared.ebkp_reference import load_ebkp_catalog, filter_by_levels

# Seitenkonfiguration
st.set_page_config(
    page_title="Kostenermittlung",
    page_icon="🏗️",
    layout="wide"
)

# Initialize Session State
init_session_state()

# Render Sidebar
render_sidebar()


def select_level(level: int):
    """Speichert ausgewähltes Level in Session State mit set_state"""
    config = get_level_config(level)

    if config:
        set_state(CFG_COST_ESTIMATION_CONFIG, {
            'selected': True,
            'level': config['level'],
            'name': config['name'],
            'tolerance': config['tolerance'],
            'ebkp_depth': config['ebkp_depth'],
            'ebkp_levels': config['ebkp_levels'],
            'project_phase': config['project_phase'],
            'phase_code': config['phase_code'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        st.success(f"✅ Ausgewählt: {config['name']} ({format_tolerance(config['tolerance'])})")
        toast(f"{config['name']} ausgewählt ({format_tolerance(config['tolerance'])})", NotificationType.SUCCESS)
        st.balloons()


# Haupttitel
render_page_header("🏗️ Art der Kostenermittlung", "nach SIA LHO 102 Standard")

render_divider("gradient")

# Zeige aktuelle Auswahl (falls vorhanden)
config = get_state(CFG_COST_ESTIMATION_CONFIG)
if config and config.get('selected'):

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
    render_divider("section")

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

.cost-card-level-1 { background: linear-gradient(135deg, #3b4ea3 0%, #543474 100%); color: white; }
.cost-card-level-2 { background: linear-gradient(135deg, #9c57a3 0%, #a33443 100%); color: white; }
.cost-card-level-3 { background: linear-gradient(135deg, #397bb6 0%, #00bbc5 100%); color: white; }
.cost-card-level-4 { background: linear-gradient(135deg, #32af5c 0%, #2ab69c 100%); color: white; }
.cost-card-level-5 { background: linear-gradient(135deg, #a13f5d 0%, #af9b28 100%); color: white; }
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

render_divider("thick")

# Auswahl der Stufen als Abo-Selector
st.header("📐 Wählen Sie Ihre Kostenermittlungsstufe")
st.caption("Klicken Sie auf eine Stufe, um Details zu sehen und auszuwählen")

# Prüfe welches Level aktuell ausgewählt ist
current_level = None
config = get_state(CFG_COST_ESTIMATION_CONFIG)
if config:
    current_level = config.get('level')

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
        if st.button("Wählen", key=f"btn_{config['level']}", width='stretch'):
            set_state(UI_SELECTED_FOR_DETAILS, config['level'])

render_divider("section")

# Details-Bereich für ausgewählte Stufe
selected_level = get_state(UI_SELECTED_FOR_DETAILS)
if selected_level:
    render_divider("dotted")
    selected_config = get_level_config(selected_level)

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

            # Zeige Beispiel-Codes für gewähltes Level
            st.markdown("---")
            st.markdown("**📚 Beispiel-Codes für diese Stufe:**")

            try:
                ebkp_catalog = load_ebkp_catalog()
                if not ebkp_catalog.empty:
                    filtered = filter_by_levels(ebkp_catalog, selected_config['ebkp_levels'])

                    if len(filtered) > 0:
                        # Zeige maximal 5 zufällige Beispiele
                        sample_size = min(5, len(filtered))
                        example_codes = filtered.sample(sample_size)

                        for _, row in example_codes.iterrows():
                            st.caption(f"• `{row['Code']}` - {row['Description']} (Level {row['Level']})")

                        st.caption(f"_Insgesamt {len(filtered)} Codes verfügbar für diese Stufe_")
                    else:
                        st.caption("Keine Codes für diese Levels gefunden")
                else:
                    st.caption("eBKP-H Katalog nicht verfügbar")
            except Exception as e:
                st.caption(f"Hinweis: Katalog konnte nicht geladen werden ({str(e)[:50]})")

        with col2:
            is_currently_selected = current_level == selected_config['level']

            if is_currently_selected:
                st.success("✅ Aktuell gewählt")
                if st.button("🔄 Erneut bestätigen", key="confirm_current", width='stretch'):
                    select_level(selected_config['level'])
            else:
                if st.button("✓ Diese Stufe wählen", key="select_from_details", type="primary", width='stretch'):
                    select_level(selected_config['level'])
                    set_state(UI_SELECTED_FOR_DETAILS, None)  # Clear details selection
                    st.rerun()

# Footer
render_page_footer()
