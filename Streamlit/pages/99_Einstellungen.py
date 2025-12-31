'''
Einstellungen und Konfiguration
API-Key-Verwaltung für Claude AI Integration
'''

import streamlit as st
import os
import sys

# Seitenkonfiguration
st.set_page_config(
    page_title="Einstellungen",
    page_icon="⚙️",
    layout="wide"
)

# Importiere gemeinsame Komponenten
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from helpers.sidebar_navigation import render_sidebar, render_page_header, render_divider, render_page_footer
from helpers.notifications import toast, NotificationType

# Session State initialisieren
if 'api_key' not in st.session_state:
    env_key = os.getenv('ANTHROPIC_API_KEY')
    st.session_state.api_key = env_key if env_key else ''

if 'api_key_validated' not in st.session_state:
    st.session_state.api_key_validated = False


def validate_api_key(api_key: str) -> dict:
    """Validiert einen API-Key durch Test-Anfrage"""
    if not api_key or len(api_key) < 10:
        return {'valid': False, 'message': 'API-Key ist zu kurz', 'model': None}

    if not api_key.startswith('sk-ant-'):
        return {'valid': False, 'message': 'Muss mit "sk-ant-" beginnen', 'model': None}

    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
        from Helpers.eBKP_H_Classifier import eBKPHClassifier

        original_key = os.getenv('ANTHROPIC_API_KEY')
        os.environ['ANTHROPIC_API_KEY'] = api_key

        try:
            classifier = eBKPHClassifier
            test_result = classifier.classify_element(element_type="Test Steckdose", debug=False)

            if test_result.get('bkp_code') and test_result.get('bkp_code') != 'ERROR':
                return {
                    'valid': True,
                    'message': f'Validiert! BKP: {test_result["bkp_code"]}',
                    'model': classifier.model
                }
            return {'valid': False, 'message': 'Key funktioniert nicht', 'model': None}

        finally:
            if original_key:
                os.environ['ANTHROPIC_API_KEY'] = original_key
            elif 'ANTHROPIC_API_KEY' in os.environ:
                del os.environ['ANTHROPIC_API_KEY']

    except Exception as e:
        return {'valid': False, 'message': f'Fehler: {str(e)[:50]}', 'model': None}


# Render Sidebar
render_sidebar()

# Page Header
render_page_header("⚙️ Einstellungen", "API-Key und Konfiguration")

# Stylesheet
st.markdown("""
<style>
    .settings-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Custom CSS für schönere Tabs
st.markdown("""
<style>
    /* Tab Container */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        padding: 0.5rem 0;
    }

    /* Einzelne Tabs */
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0.75rem 1.5rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
        border-radius: 0.5rem;
        border: 1px solid rgba(102, 126, 234, 0.2);
        font-weight: 500;
        transition: all 0.2s ease;
    }

    /* Tab Hover */
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-color: rgba(102, 126, 234, 0.4);
        transform: translateY(-2px);
    }

    /* Aktiver Tab */
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-color: transparent !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    /* Tab Panel (Content-Bereich) */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Status-Karten
col1, col2, col3 = st.columns(3)

with col1:
    if st.session_state.api_key and st.session_state.api_key_validated:
        st.success("✓ API-Key aktiv", icon="🔑")
    elif st.session_state.api_key:
        st.warning("⚠️ Nicht validiert", icon="🔑")
    else:
        st.error("✗ Kein API-Key", icon="🔑")

with col2:
    env_key = os.getenv('ANTHROPIC_API_KEY')
    if env_key:
        st.info("✓ .env Datei", icon="📄")
    else:
        st.info("Keine .env", icon="📄")

with col3:
    st.metric("Modell", "Claude 3.5 Haiku")

render_divider("section")

# API-Key Eingabe
st.subheader("🔑 API-Key Verwaltung")

col1, col2 = st.columns([3, 1])

with col1:
    current_key = st.session_state.api_key
    if current_key and len(current_key) > 14:
        placeholder = f"{current_key[:10]}...{current_key[-4:]}"
    else:
        placeholder = "sk-ant-api03-..."

    api_key_input = st.text_input(
        "API-Key",
        value="",
        type="password",
        placeholder=placeholder,
        help="Anthropic API-Key (Session State)"
    )

with col2:
    st.write("")
    st.write("")
    if st.button("💾 Speichern", type="primary", width='stretch'):
        if api_key_input:
            st.session_state.api_key = api_key_input
            st.session_state.api_key_validated = False
            st.success("Gespeichert!")
            toast("API-Key gespeichert", NotificationType.SUCCESS)
            st.rerun()

# Aktionen
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Validieren", width='stretch', disabled=not st.session_state.api_key):
        with st.spinner("Teste..."):
            result = validate_api_key(st.session_state.api_key)
            if result['valid']:
                st.session_state.api_key_validated = True
                st.success(result['message'])
                toast("API-Key erfolgreich validiert", NotificationType.SUCCESS)
            else:
                st.error(result['message'])
                toast("API-Key Validierung fehlgeschlagen", NotificationType.ERROR)

with col2:
    if st.button("🗑️ Löschen", width='stretch', disabled=not st.session_state.api_key):
        st.session_state.api_key = ''
        st.session_state.api_key_validated = False
        st.rerun()

with col3:
    if st.button("📋 Anzeigen", width='stretch', disabled=not st.session_state.api_key):
        st.code(st.session_state.api_key, language=None)

render_divider("section")

# Batch API Einstellungen
st.subheader("🚀 Batch API Einstellungen")

# Session State initialisieren
if 'force_batch_api' not in st.session_state:
    st.session_state.force_batch_api = False

if 'token_limit' not in st.session_state:
    st.session_state.token_limit = 50000

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Batch API Modus**")
    st.session_state.force_batch_api = st.checkbox(
        "Batch API auch für < 300 Elemente nutzen",
        value=st.session_state.get("force_batch_api", False),
        help="Aktivieren für maximale Kostenersparnis (50% günstiger), aber längere Wartezeiten. "
             "Standard: Nur ab 300 Elementen automatisch aktiviert."
    )

    if st.session_state.force_batch_api:
        st.info(
            "💡 **Batch API Modus aktiv**\n\n"
            "- 50% Kostenersparnis\n"
            "- Keine Rate-Limits\n"
            "- Längere Wartezeit (20-60 Min)\n"
            "- Batch-IDs werden gespeichert"
        )
    else:
        st.info(
            "⚡ **Automatik-Modus**\n\n"
            "- < 300 Elemente: Synchron (schnell)\n"
            "- ≥ 300 Elemente: Batch API (günstig)\n"
            "- Optimal für die meisten Projekte"
        )

with col2:
    st.markdown("**Rate-Limiting**")
    st.session_state.token_limit = st.number_input(
        "Token-Limit pro Minute",
        min_value=10000,
        max_value=500000,
        value=st.session_state.get("token_limit", 50000),
        step=10000,
        help="Max. Token pro Minute für synchrone API-Calls. "
             "Standard: 50.000 für Haiku. "
             "Bei höherem API-Tier kann dieses Limit erhöht werden."
    )

    # Berechne max. sichere Batch-Größe basierend auf Token-Limit
    tokens_per_batch = 6000  # Schätzung: 3000 (system) + 40*50 (input) + 40*30 (output)
    safe_batches_per_min = st.session_state.token_limit // tokens_per_batch
    safe_elements_per_min = safe_batches_per_min * 40

    st.metric(
        "Sichere Verarbeitung",
        f"{safe_elements_per_min} Elemente/Min",
        help=f"Bei aktuellen Settings können max. {safe_batches_per_min} Batches pro Minute verarbeitet werden"
    )

    if st.session_state.token_limit < 50000:
        st.warning("⚠️ Niedriges Limit: Längere Wartezeiten")
    elif st.session_state.token_limit > 100000:
        st.success("✅ Hohes Limit: Schnellere Verarbeitung")

render_divider("section")

# Klassifizierungs-Einstellungen
st.subheader("⚙️ Klassifizierungs-Einstellungen")

# Session State initialisieren
if 'classification_settings' not in st.session_state:
    st.session_state.classification_settings = {
        'use_batch': True,
        'batch_size': 40,
        'debug_mode': False,
        'confidence_threshold': 0.7,
        'model': 'claude-3-5-haiku-20241022',
        'bim_complexity': 'medium'
    }

settings = st.session_state.classification_settings

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Batch-Verarbeitung**")
    use_batch = st.toggle(
        "Batch-Modus aktivieren",
        value=settings['use_batch'],
        help="Mehrere Elemente gleichzeitig klassifizieren"
    )

    if use_batch:
        batch_size = st.slider(
            "Batch-Größe",
            min_value=20,
            max_value=50,
            value=settings['batch_size'],
            help="Elemente pro API-Request"
        )
    else:
        batch_size = settings['batch_size']

    st.markdown("**Erweitert**")
    debug_mode = st.toggle(
        "Debug-Modus",
        value=settings['debug_mode'],
        help="Detaillierte API-Responses anzeigen"
    )

with col2:
    st.markdown("**Qualität & Modell**")
    confidence_threshold = st.slider(
        "Konfidenz-Schwellenwert",
        min_value=0.0,
        max_value=1.0,
        value=settings['confidence_threshold'],
        step=0.05,
        help="Mindest-Konfidenz für Klassifizierung"
    )

    model = st.selectbox(
        "Claude Modell",
        options=[
            'claude-3-5-haiku-20241022',
            'claude-3-5-sonnet-20241022',
            'claude-opus-4-20250514'
        ],
        index=0,
        format_func=lambda x: {
            'claude-3-5-haiku-20241022': '🚀 Haiku (schnell, günstig)',
            'claude-3-5-sonnet-20241022': '⚡ Sonnet (ausgewogen)',
            'claude-opus-4-20250514': '🏆 Opus 4 (präzise, teuer)'
        }[x],
        help="Modellauswahl beeinflusst Qualität und Kosten"
    )

    bim_complexity = st.selectbox(
        "BIM-Modell Komplexität",
        options=['simple', 'medium', 'complex'],
        index=1,
        format_func=lambda x: {
            'simple': 'Einfach (Standardelemente)',
            'medium': 'Mittel (gemischte Elemente)',
            'complex': 'Komplex (spezielle Elemente)'
        }[x],
        help="Komplexität beeinflusst Prompt-Detailgrad"
    )

# Speichern Button
if st.button("💾 Einstellungen speichern", type="primary", width='stretch'):
    st.session_state.classification_settings = {
        'use_batch': use_batch,
        'batch_size': batch_size,
        'debug_mode': debug_mode,
        'confidence_threshold': confidence_threshold,
        'model': model,
        'bim_complexity': bim_complexity
    }
    toast("Klassifizierungs-Einstellungen gespeichert", NotificationType.SUCCESS)
    st.success("Einstellungen gespeichert!")

render_divider("section")

# Info-Tabs
st.subheader("📚 Informationen")

tab1, tab2, tab3 = st.tabs(["🔐 Sicherheit", "💰 Kosten", "📖 Setup"])

with tab1:
    st.markdown("""
    **Session State Storage:**
    - Nur für aktuelle Sitzung gespeichert
    - Nicht persistent (gelöscht nach Browser-Schließen)
    - Lokal, keine Server-Speicherung

    **Empfehlung:** `.env` Datei für dauerhafte Konfiguration
    """)

with tab2:
    st.markdown("""
    **Claude 3.5 Haiku Pricing:**
    - Input: $0.80 / 1M tokens
    - Output: $4.00 / 1M tokens

    **Geschätzte Kosten:**
    - Einzeln: ~$0.0001 / Element
    - Batch: ~$0.00005 / Element
    - 100 Elemente (Batch): ~$0.005
    """)

with tab3:
    st.markdown("""
    **API-Key erhalten:**
    1. [console.anthropic.com](https://console.anthropic.com) besuchen
    2. Registrieren/Anmelden
    3. API Keys → Neuen Key erstellen
    4. Key kopieren und hier einfügen

    **.env Datei (empfohlen):**
    ```
    ANTHROPIC_API_KEY=sk-ant-api03-...
    ```
    Im Projektverzeichnis erstellen.
    """)

# Debug (optional)
if st.checkbox("🐛 Debug-Info"):
    st.json({
        'API-Key vorhanden': bool(st.session_state.api_key),
        'Länge': len(st.session_state.api_key) if st.session_state.api_key else 0,
        'Validiert': st.session_state.api_key_validated,
        'Umgebungsvariable': bool(os.getenv('ANTHROPIC_API_KEY'))
    })


# Footer  
render_page_footer()
