'''
BKP Datenverarbeitungs-Suite
Haupteinstiegspunkt für Multi-Page Streamlit App
'''

import streamlit as st
import os
from datetime import datetime

# Seitenkonfiguration
st.set_page_config(
    page_title="BKP Suite",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (theme-aware, no fixed colors)
st.markdown("""
    <style>
    .big-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        font-size: 1.1rem;
        opacity: 0.7;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Haupttitel
st.markdown('<p class="big-title">🏗️ BKP Datenverarbeitungs-Suite</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Automatische BKP-Klassifizierung & Visualisierung für BIM-Daten</p>', unsafe_allow_html=True)

st.markdown("---")

# Quick Start Cards
st.header("🚀 Schnellstart")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    ### 📊 Daten visualisieren
    Sie haben bereits BKP-klassifizierte Daten?

    **→ Gehen Sie zu "eBKP-H Auswertung"**

    - CSV hochladen
    - Kosten nach BKP analysieren
    - Berichte exportieren
    """)

with col2:
    st.success("""
    ### 🤖 KI-Klassifizierung
    Ihre Daten sind noch nicht klassifiziert?

    **→ Gehen Sie zu "KI Klassifizierung"**

    - CSV hochladen
    - Automatisch klassifizieren
    - BKP-Codes bearbeiten
    - Ergebnisse prüfen
    """)

with col3:
    st.warning("""
    ### ⚙️ Einrichten
    Erstmalige Nutzung der KI?

    **→ Gehen Sie zu "Einstellungen"**

    - API-Key eingeben
    - Key validieren
    - Los geht's!
    """)


st.markdown("---")

# Was ist eBKP-H?
st.header("💡 Was ist eBKP-H?")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
    Der **eBKP-H** (erweiterter Baukostenplan - Hochbau) ist der Schweizer Standard
    für die Strukturierung von Baukosten.

    **Hauptgruppen:**
    """)

    bkp_data = {
        "C": ("Bauwerk - Rohbau", "🏗️"),
        "D": ("Bauwerk - Technik", "⚡"),
        "E": ("Bauwerk - Ausbau", "🎨"),
        "F": ("Umgebung", "🌳"),
        "G": ("Baunebenkosten", "📋")
    }

    for code, (name, emoji) in bkp_data.items():
        st.markdown(f"**{emoji} {code}** - {name}")

with col2:
    st.info("""
    **Beispiel:**

    Eine **Steckdose** wird klassifiziert als:
    - Code: `C13`
    - Beschreibung: Elektroinstallationen - Steckdosen

    Dies ermöglicht:
    ✓ Kostenauswertung nach Gewerken
    ✓ Vergleich verschiedener Projekte
    ✓ Standardisierte Kommunikation
    """)

st.markdown("---")

# Workflow
st.header("🔄 So funktioniert's")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 1️⃣ Daten vorbereiten
    - Exportieren Sie Daten aus Revit
    - Als CSV speichern
    - Spalten: Typ, Kategorie, etc.
    """)

with col2:
    st.markdown("""
    ### 2️⃣ Klassifizieren
    **Option A:** Manuelle BKP-Zuordnung
    **Option B:** KI-Klassifizierung nutzen
    (schneller & automatisch)
    """)

with col3:
    st.markdown("""
    ### 3️⃣ Auswerten
    - Hierarchische Ansicht
    - Kosten nach BKP
    - Berichte exportieren
    """)

st.markdown("---")

# Testdaten
st.header("🧪 Testdaten verfügbar")

col1, col2 = st.columns(2)

with col1:
    st.success("""
    **📁 beispiel_daten.csv**

    40 Einträge mit BKP-Codes zum Testen der Visualisierung

    → Nutzen Sie diese für "eBKP-H Auswertung"
    """)

with col2:
    st.success("""
    **📁 muster_ki_klassifizierung.csv**

    30 Einträge OHNE BKP-Codes zum Testen der KI

    → Nutzen Sie diese für "KI Klassifizierung"
    """)

# Footer
st.markdown("---")
st.caption(f"BKP Datenverarbeitungs-Suite v1.0 | Letztes Update: {datetime.now().strftime('%d.%m.%Y')} | TA.BA_DT_PROGR")

# Sidebar
with st.sidebar:
    st.header("📍 Navigation")

    st.markdown("""
    **Hauptseiten:**
    - 🏠 Home (diese Seite)
    - 📊 eBKP-H Auswertung
    - 🤖 KI Klassifizierung
    - ⚙️ Einstellungen
    """)

    st.markdown("---")

    # Status
    st.subheader("📊 Status")

    # Testdaten
    example_files = {
        'beispiel_daten.csv': 'Processors/beispiel_daten.csv',
        'muster_ki_klassifizierung.csv': 'Processors/muster_ki_klassifizierung.csv'
    }

    for name, path in example_files.items():
        if os.path.exists(path):
            st.success(f"✓ {name}")
        else:
            st.warning(f"✗ {name}")

    st.markdown("---")

    # API Status
    st.subheader("🔑 API Status")

    # Prüfe Session State
    if 'api_key' in st.session_state and st.session_state.api_key:
        if st.session_state.get('api_key_validated', False):
            st.success("✓ API-Key aktiv")
        else:
            st.warning("⚠️ API-Key nicht validiert")
            st.caption("Gehen Sie zu Einstellungen")
    else:
        # Fallback auf Umgebungsvariable
        env_key = os.getenv('ANTHROPIC_API_KEY')
        if env_key:
            st.success("✓ API-Key (.env)")
        else:
            st.info("ℹ️ Kein API-Key")
            st.caption("Für KI-Features erforderlich")

    st.markdown("---")

    with st.expander("ℹ️ Hilfe"):
        st.markdown("""
        **Erste Schritte:**

        1. Testen Sie mit Beispieldaten
        2. Konfigurieren Sie API-Key (optional)
        3. Laden Sie eigene Daten hoch

        **Support:**
        - README.md
        - CLAUDE.md
        - Processors/README.md
        """)
