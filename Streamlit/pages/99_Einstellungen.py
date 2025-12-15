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

# Session State initialisieren
if 'api_key' not in st.session_state:
    # Versuche API Key aus Umgebungsvariable zu laden
    env_key = os.getenv('ANTHROPIC_API_KEY')
    st.session_state.api_key = env_key if env_key else ''

if 'api_key_validated' not in st.session_state:
    st.session_state.api_key_validated = False


def validate_api_key(api_key: str) -> dict:
    """
    Validiert einen API-Key durch Test-Anfrage

    Returns:
        dict mit 'valid', 'message', 'model'
    """
    if not api_key or len(api_key) < 10:
        return {
            'valid': False,
            'message': 'API-Key ist zu kurz oder leer',
            'model': None
        }

    if not api_key.startswith('sk-ant-'):
        return {
            'valid': False,
            'message': 'API-Key muss mit "sk-ant-" beginnen',
            'model': None
        }

    try:
        # Importiere BKPClassifier für Test
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
        from Helpers.BKP_Classifier import BKPClassifier

        # Temporär API-Key setzen
        original_key = os.getenv('ANTHROPIC_API_KEY')
        os.environ['ANTHROPIC_API_KEY'] = api_key

        try:
            # Test-Klassifizierung
            classifier = BKPClassifier()
            test_result = classifier.classify_element(
                element_type="Test Steckdose",
                debug=False
            )

            # Prüfe ob Antwort sinnvoll ist
            if test_result.get('bkp_code') and test_result.get('bkp_code') != 'ERROR':
                return {
                    'valid': True,
                    'message': f'API-Key erfolgreich validiert! (BKP: {test_result["bkp_code"]})',
                    'model': classifier.model
                }
            else:
                return {
                    'valid': False,
                    'message': 'API-Key funktioniert nicht korrekt',
                    'model': None
                }

        finally:
            # Stelle Original-Key wieder her
            if original_key:
                os.environ['ANTHROPIC_API_KEY'] = original_key
            elif 'ANTHROPIC_API_KEY' in os.environ:
                del os.environ['ANTHROPIC_API_KEY']

    except Exception as e:
        return {
            'valid': False,
            'message': f'Fehler bei Validierung: {str(e)}',
            'model': None
        }


# Haupttitel
st.title("⚙️ Einstellungen")
st.markdown("Konfigurieren Sie Ihre API-Keys und Einstellungen")
st.markdown("---")

# API-Key Verwaltung
st.header("🔑 Anthropic Claude API-Key")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    Für die KI-gestützte BKP-Klassifizierung benötigen Sie einen API-Key von Anthropic.

    **So erhalten Sie einen API-Key:**
    1. Besuchen Sie [console.anthropic.com](https://console.anthropic.com)
    2. Registrieren Sie sich oder melden Sie sich an
    3. Navigieren Sie zu "API Keys"
    4. Erstellen Sie einen neuen Key
    5. Kopieren Sie den Key und fügen Sie ihn hier ein
    """)

with col2:
    # Status-Anzeige
    if st.session_state.api_key and st.session_state.api_key_validated:
        st.success("✓ API-Key aktiv")
        st.metric("Status", "Konfiguriert")
    elif st.session_state.api_key:
        st.warning("⚠️ Nicht validiert")
        st.metric("Status", "Eingegeben")
    else:
        st.error("✗ Kein API-Key")
        st.metric("Status", "Nicht konfiguriert")

st.markdown("---")

# API-Key Eingabe
col1, col2 = st.columns([3, 1])

with col1:
    # Maskiere den Key bei der Anzeige
    current_key = st.session_state.api_key
    display_key = current_key if current_key else ""

    # Zeige maskierten Key wenn vorhanden
    if current_key and len(current_key) > 14:
        placeholder_text = f"{current_key[:10]}...{current_key[-4:]}"
    else:
        placeholder_text = "sk-ant-api03-..."

    api_key_input = st.text_input(
        "API-Key eingeben",
        value="",
        type="password",
        placeholder=placeholder_text,
        help="Ihr Anthropic API-Key (wird sicher im Session State gespeichert)"
    )

with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing

    if st.button("💾 Speichern", type="primary", use_container_width=True):
        if api_key_input:
            st.session_state.api_key = api_key_input
            st.session_state.api_key_validated = False
            st.success("API-Key gespeichert!")
            st.rerun()
        else:
            st.warning("Bitte geben Sie einen API-Key ein")

# Validierungs-Buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Key validieren", use_container_width=True, disabled=not st.session_state.api_key):
        with st.spinner("Validiere API-Key..."):
            result = validate_api_key(st.session_state.api_key)

            if result['valid']:
                st.session_state.api_key_validated = True
                st.success(result['message'])
                if result['model']:
                    st.info(f"Verwendetes Modell: `{result['model']}`")
            else:
                st.session_state.api_key_validated = False
                st.error(result['message'])

with col2:
    if st.button("🗑️ Key löschen", use_container_width=True, disabled=not st.session_state.api_key):
        st.session_state.api_key = ''
        st.session_state.api_key_validated = False
        st.info("API-Key gelöscht")
        st.rerun()

with col3:
    if st.button("📋 Key anzeigen", use_container_width=True, disabled=not st.session_state.api_key):
        st.code(st.session_state.api_key, language=None)

# Aktuelle Konfiguration
st.markdown("---")
st.subheader("📊 Aktuelle Konfiguration")

config_col1, config_col2 = st.columns(2)

with config_col1:
    st.markdown("**API-Key Status:**")
    if st.session_state.api_key:
        masked = f"{st.session_state.api_key[:10]}...{st.session_state.api_key[-4:]}"
        st.text(f"Key: {masked}")
        st.text(f"Länge: {len(st.session_state.api_key)} Zeichen")
        st.text(f"Validiert: {'✓ Ja' if st.session_state.api_key_validated else '✗ Nein'}")
    else:
        st.text("Kein API-Key konfiguriert")

with config_col2:
    st.markdown("**Umgebungsvariable:**")
    env_key = os.getenv('ANTHROPIC_API_KEY')
    if env_key:
        masked_env = f"{env_key[:10]}...{env_key[-4:]}"
        st.text(f"Key: {masked_env}")
        st.text(f"Quelle: .env Datei")
    else:
        st.text("Keine .env Konfiguration gefunden")

# Informationen
st.markdown("---")

with st.expander("ℹ️ Wichtige Informationen"):
    st.markdown("""
    ### Sicherheit

    - **Session State**: Der API-Key wird nur für die aktuelle Sitzung gespeichert
    - **Nicht persistent**: Nach Schließen des Browsers ist der Key gelöscht
    - **Lokal**: Keine Speicherung auf Server oder in Dateien
    - **Empfehlung**: Verwenden Sie die `.env` Datei für dauerhafte Konfiguration

    ### .env Datei verwenden (empfohlen)

    Für dauerhafte Konfiguration erstellen Sie eine `.env` Datei im Projektverzeichnis:

    ```
    ANTHROPIC_API_KEY=sk-ant-api03-...
    ```

    Die App lädt den Key automatisch beim Start.

    ### Kosten

    Die KI-Klassifizierung verwendet das Modell `claude-3-5-haiku-20241022`:
    - **Input**: $0.80 / 1M tokens
    - **Output**: $4.00 / 1M tokens
    - **Geschätzt**: ~$0.0001 pro Element (Einzeln), ~$0.00005 pro Element (Batch)

    ### Fehlerbehandlung

    Falls die Validierung fehlschlägt:
    1. Prüfen Sie, ob der Key mit `sk-ant-` beginnt
    2. Stellen Sie sicher, dass der Key aktiv ist
    3. Prüfen Sie Ihr Anthropic-Konto auf Credits
    4. Versuchen Sie einen neuen Key zu erstellen

    ### Support

    - **Anthropic Console**: [console.anthropic.com](https://console.anthropic.com)
    - **Dokumentation**: [docs.anthropic.com](https://docs.anthropic.com)
    - **Pricing**: [anthropic.com/pricing](https://www.anthropic.com/pricing)
    """)

# Weitere Einstellungen
st.markdown("---")
st.header("🔧 Weitere Einstellungen")

st.info("Weitere Konfigurationsoptionen werden hier in zukünftigen Versionen verfügbar sein.")

# Debug-Informationen (nur wenn API-Key vorhanden)
if st.session_state.api_key and st.checkbox("🐛 Debug-Informationen anzeigen"):
    st.subheader("Debug-Informationen")

    debug_info = {
        'API-Key vorhanden': bool(st.session_state.api_key),
        'API-Key Länge': len(st.session_state.api_key) if st.session_state.api_key else 0,
        'Validiert': st.session_state.api_key_validated,
        'Umgebungsvariable gesetzt': bool(os.getenv('ANTHROPIC_API_KEY')),
        'Python Version': sys.version.split()[0],
        'Working Directory': os.getcwd()
    }

    st.json(debug_info)
