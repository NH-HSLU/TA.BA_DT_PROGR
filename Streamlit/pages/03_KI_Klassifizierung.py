'''
KI-gestützte BKP-Klassifizierung mit Anthropic Claude
Ermöglicht automatische Klassifizierung von Bauelementen mit Echtzeit-Monitoring.
'''

import streamlit as st
import pandas as pd
import sys
import os
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Füge Parent-Verzeichnis zum Path hinzu für Imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    # Use package-level lazy imports to avoid anthropic dependency issues
    from helpers_shared import eBKPHClassifier, TokenRateLimiter, batch_manager
    from helpers.sia_lho_102_config import get_level_config
    from helpers.sidebar_navigation import render_sidebar, render_page_header, render_divider, render_page_footer
    from helpers.notifications import toast, NotificationType
    from helpers.session_state import (
        init_session_state,
        get_state,
        set_state,
        DATA_CLASSIFICATION_RESULTS,
        DATA_PREPARED,
        DATA_ORIGINAL_UPLOADED,
        DATA_DEDUP_MAPPING,
        DATA_UNIQUE_ELEMENTS,
        PROC_API_RESPONSES,
        PROC_PROCESSING_LOG,
        PROC_TOTAL_COST,
        PROC_ACTIVE_TAB,
        CFG_API_KEY,
        CFG_COST_ESTIMATION_CONFIG,
        CFG_CLASSIFICATION_SETTINGS,
        CFG_FORCE_BATCH_API,
        UI_USE_PREPARED_DATA
    )
except ImportError as e:
    st.error(f"Module konnten nicht importiert werden: {e}")
    st.stop()

# Seitenkonfiguration
st.set_page_config(
    page_title="KI-BKP-Klassifizierung",
    page_icon="🤖",
    layout="wide"
)

# Initialize Session State
init_session_state()

# Render gemeinsame Sidebar
render_sidebar()




def estimate_cost(
    num_elements: int,
    batch_mode: bool = True,
    batch_size: int = 40,
    use_batch_api: bool = False,
    dedup_ratio: float = 1.0
) -> dict:
    """
    Schätzt die Kosten für die Klassifizierung mit eBKP-H (inkl. Deduplizierung).

    Args:
        num_elements: Anzahl zu klassifizierender Elemente
        batch_mode: Batch-Verarbeitung aktiviert
        batch_size: Elemente pro Batch (nur für Synchron-Modus)
        use_batch_api: Anthropic Batch API nutzen (50% günstiger)
        dedup_ratio: Deduplizierungs-Verhältnis (total_elements / unique_elements)
                     z.B. 10.0 = 1000 Elemente → 100 einzigartige

    Returns:
        Dict mit Kosten-Details inkl. Deduplizierungs-Ersparnis
    """
    # Claude Haiku Pricing (Stand Nov 2024)
    # Input: $0.80 / 1M tokens, Output: $4.00 / 1M tokens
    # eBKP-H System Prompt: ~3000 tokens (wird gecacht)

    # Deduplizierung berücksichtigen
    effective_elements = int(num_elements / dedup_ratio) if dedup_ratio > 0 else num_elements
    cost_saving_dedup_pct = (1 - 1/dedup_ratio) * 100 if dedup_ratio > 1 else 0

    if use_batch_api:
        # === BATCH API MODUS (50% RABATT) ===
        # Ein Request pro Element mit System Prompt Caching
        # Prompt Caching: ~30-50% Hit-Rate (konservativ: 40%)

        system_tokens = 3000  # System Prompt pro Request
        cache_hit_rate = 0.4  # Konservative Schätzung
        cached_system_tokens = system_tokens * 0.1  # 90% Ersparnis bei Cache Hit

        # Durchschnittliche System Prompt Kosten pro Element
        avg_system_tokens_per_element = (
            system_tokens * (1 - cache_hit_rate) +
            cached_system_tokens * cache_hit_rate
        )

        input_tokens = effective_elements * (avg_system_tokens_per_element + 50)  # System + Element
        output_tokens = effective_elements * 30  # Output pro Element

        # Batch API: 50% Rabatt auf Base-Preis
        batch_discount = 0.5
        input_cost = (input_tokens / 1_000_000) * 0.80 * batch_discount
        output_cost = (output_tokens / 1_000_000) * 4.00 * batch_discount

        num_requests = effective_elements  # Ein Request pro Element (dedupliziert)
        mode = "Batch API"

    elif batch_mode:
        # === SYNCHRON BATCH-MODUS ===
        # 30-50 Elemente pro Request mit Prompt Caching
        num_requests = max(1, (effective_elements + batch_size - 1) // batch_size)

        # Erster Request: Volle System Prompt Kosten
        first_request_input = 3000 + (batch_size * 50)
        first_request_output = batch_size * 30

        # Weitere Requests: Gecachter System Prompt (10% Kosten)
        cached_requests = num_requests - 1
        cached_input = cached_requests * (300 + (batch_size * 50))
        cached_output = cached_requests * (batch_size * 30)

        input_tokens = first_request_input + cached_input
        output_tokens = first_request_output + cached_output

        input_cost = (input_tokens / 1_000_000) * 0.80
        output_cost = (output_tokens / 1_000_000) * 4.00

        mode = "Synchron Batch"

    else:
        # === EINZELABFRAGEN (nicht empfohlen) ===
        input_tokens = 3000 + (effective_elements * 100)
        output_tokens = effective_elements * 50

        input_cost = (input_tokens / 1_000_000) * 0.80
        output_cost = (output_tokens / 1_000_000) * 4.00

        num_requests = effective_elements
        mode = "Einzeln"

    total_cost = input_cost + output_cost

    return {
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'input_cost': input_cost,
        'output_cost': output_cost,
        'total_cost': total_cost,
        'num_requests': num_requests,
        'mode': mode,
        'effective_elements': effective_elements,
        'original_elements': num_elements,
        'dedup_ratio': dedup_ratio,
        'cost_saving_dedup_pct': cost_saving_dedup_pct
    }


def add_log(message: str, level: str = "info"):
    """Fügt einen Eintrag zum Processing Log hinzu"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    get_state(PROC_PROCESSING_LOG).append({
        'timestamp': timestamp,
        'level': level,
        'message': message
    })


def add_api_response(request_num: int, element_info: str, response: str, parsed_result: dict):
    """Speichert eine API-Response für Echtzeit-Anzeige"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    get_state(PROC_API_RESPONSES).append({
        'timestamp': timestamp,
        'request_num': request_num,
        'element': element_info,
        'raw_response': response,
        'parsed_result': parsed_result
    })


def display_log():
    """Zeigt das Processing Log an (theme-aware)"""
    if get_state(PROC_PROCESSING_LOG):
        # Zeige Log-Einträge mit nativen Streamlit-Komponenten für Dark Mode Support
        for log_entry in get_state(PROC_PROCESSING_LOG):
            timestamp = log_entry.get('timestamp', '')
            message = log_entry.get('message', '')
            level = log_entry.get('level', 'info')

            # Icons für Level
            level_icons = {
                'info': 'ℹ️',
                'success': '✅',
                'warning': '⚠️',
                'error': '❌'
            }

            icon = level_icons.get(level, 'ℹ️')
            log_text = f"{icon} **{timestamp}** | {message}"

            # Zeige mit entsprechendem Streamlit-Widget (auto Dark Mode)
            if level == 'error':
                st.error(log_text, icon=icon)
            elif level == 'warning':
                st.warning(log_text, icon=icon)
            elif level == 'success':
                st.success(log_text, icon=icon)
            else:
                st.info(log_text, icon=icon)


# API-Key Prüfung
def get_api_key():
    """Holt den API-Key aus Session State oder Umgebungsvariable"""
    # Prüfe Session State zuerst
    if get_state(CFG_API_KEY):
        return get_state(CFG_API_KEY)
    # Fallback auf Umgebungsvariable
    return os.getenv('ANTHROPIC_API_KEY')


def map_classifications_back(
    df: pd.DataFrame,
    index_mapping: dict,
    classification_results: list
) -> pd.DataFrame:
    """
    Mappt Klassifizierungen von deduplizierten Elementen zurück auf Original-DataFrame.

    Args:
        df: Original DataFrame mit allen Elementen
        index_mapping: Dict {unique_idx: [original_indices]}
        classification_results: Liste von Klassifizierungsergebnissen für unique elements

    Returns:
        DataFrame mit BKP-Codes für alle Original-Elemente
    """
    # Create lookup: unique_idx -> classification
    classifications_by_unique_idx = {i: result for i, result in enumerate(classification_results)}

    # Initialize columns
    df['bkp_code'] = None
    df['bkp_description'] = None
    df['confidence'] = None

    # Map back to original elements
    for unique_idx, original_indices in index_mapping.items():
        if unique_idx in classifications_by_unique_idx:
            result = classifications_by_unique_idx[unique_idx]
            for orig_idx in original_indices:
                df.at[orig_idx, 'bkp_code'] = result.get('bkp_code')
                df.at[orig_idx, 'bkp_description'] = result.get('bkp_description')
                df.at[orig_idx, 'confidence'] = result.get('confidence')

    return df


# Page Header
render_page_header("🤖 KI-Klassifizierung", "Automatische BKP-Zuordnung mit Claude AI")

# API-Key Check
current_api_key = get_api_key()
if not current_api_key:
    st.error("⚠️ Kein API-Key konfiguriert!")
    st.info("Bitte gehen Sie zu **Einstellungen** und konfigurieren Sie Ihren Anthropic API-Key.")
    st.stop()
    st.markdown("---")

# Lade Klassifizierungs-Einstellungen aus Session State (mit Defaults)
settings = get_state(CFG_CLASSIFICATION_SETTINGS, {
    'use_batch': True,
    'batch_size': 40,
    'debug_mode': False,
    'confidence_threshold': 0.7,
    'model': 'claude-3-5-haiku-20241022',
    'bim_complexity': 'medium'
})
use_batch = settings['use_batch']
batch_size = settings['batch_size']
debug_mode = settings['debug_mode']
confidence_threshold = settings['confidence_threshold']
model = settings.get('model', 'claude-3-5-haiku-20241022')
bim_complexity = settings.get('bim_complexity', 'medium')

# Hinweis für User mit Link zu Einstellungen
st.info("⚙️ **Klassifizierungs-Einstellungen:** Batch-Modus, Modellauswahl und weitere Optionen können in der Seite **Einstellungen** angepasst werden.")

with st.sidebar:
    st.markdown("---")
    st.subheader("⚙️ Aktuelle Einstellungen")
    st.caption(f"Batch: {'✅' if use_batch else '❌'} (Größe: {batch_size})")
    st.caption(f"Debug: {'✅' if debug_mode else '❌'}")
    st.caption(f"Konfidenz: ≥{confidence_threshold:.0%}")
    if st.button("⚙️ Einstellungen ändern", width='stretch'):
        st.switch_page("pages/99_Einstellungen.py")

    st.markdown("---")

    # Kostenermittlungs-Status anzeigen
    st.subheader("📐 Kostenermittlung")

    if get_state(CFG_COST_ESTIMATION_CONFIG).get('selected'):
        config = get_state(CFG_COST_ESTIMATION_CONFIG)
        st.success(f"✅ {config['name']}")
        st.caption(f"Toleranz: ±{config['tolerance']}%")
        st.caption(f"Phase: {config['project_phase']}")
        st.caption(f"eBKP-Tiefe: {config['ebkp_depth']}")

        # Zeige verwendete Levels
        levels_str = ", ".join([str(l) for l in config['ebkp_levels']])
        st.caption(f"CSV Levels: {levels_str}")
    else:
        st.info("ℹ️ Keine Auswahl getroffen")
        st.caption("Standard: Level 1+2")
        if st.button("🏗️ Kostenermittlung wählen"):
            st.switch_page("pages/0.5_Kostenermittlung.py")

    st.markdown("---")

    # API Status prüfen
    st.subheader("🔑 API Status")
    api_key = get_api_key()
    if api_key:
        st.success("API Key aktiv ✅")
        masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
        st.caption(f"Key: {masked_key}")

        # Zeige Quelle
        if get_state(CFG_API_KEY):
            st.caption("Quelle: Session State")
        else:
            st.caption("Quelle: .env Datei")
    else:
        st.error("Kein API Key")
        st.info("→ Gehen Sie zu Einstellungen")

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

# Tabs für verschiedene Bereiche
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload & Klassifizierung", "📊 Ergebnisse", "🔍 KI Responses", "📝 Monitoring"])
with tab1:
    #TODO Hier funktioniert das Live-Update der API Response fast so wie ich es will. ich will es aber wie in einem Chat haben. Also dass die API Response direkt angezeigt wird, wenn sie reinkommt und nicht erst am Ende der Klassifizierung.
    #TODO Es wäre cool, wenn die API-Responses nicht gerade flöten gehen, wenn die Seite neu geladen oder gewechselt wird.

    # === BATCH-STATUS-PRÜFUNG (für gespeicherte Batches) ===
    with st.expander("📋 Gespeicherte Batch-Jobs prüfen", expanded=False):
        # JSONL-Upload für bereits heruntergeladene Batch-Ergebnisse
        st.markdown("**📤 Batch-Ergebnisse hochladen (JSONL)**")

        col_upload1, col_upload2 = st.columns([3, 1])

        with col_upload1:
            jsonl_file = st.file_uploader(
                "JSONL-Datei mit Batch-Ergebnissen",
                type=['jsonl'],
                help="Laden Sie die von Anthropic heruntergeladene JSONL-Datei hoch",
                key="jsonl_uploader"
            )

        with col_upload2:
            if jsonl_file and st.button("🔄 Verarbeiten", key="process_jsonl"):
                with st.spinner("Verarbeite JSONL-Datei..."):
                    try:
                        # JSONL parsen
                        import json

                        results = []
                        jsonl_content = jsonl_file.read().decode('utf-8')

                        for line in jsonl_content.splitlines():
                            if not line.strip():
                                continue

                            result_obj = json.loads(line)
                            results.append(result_obj)

                        # Nach custom_id sortieren
                        results.sort(key=lambda x: int(x['custom_id'].split('_')[1]))

                        # Ergebnisse extrahieren
                        formatted_results = []

                        skipped_errors = 0

                        for result_obj in results:
                            result_type = result_obj['result']['type']

                            # Ignoriere errored-Elemente
                            if result_type == 'errored':
                                skipped_errors += 1
                                continue

                            if result_type == 'succeeded':
                                message_content = result_obj['result']['message']['content'][0]['text']

                                # Parse Response
                                try:
                                    content = message_content.strip()
                                    start_idx = content.find('{')
                                    end_idx = content.rfind('}') + 1
                                    if start_idx >= 0 and end_idx > start_idx:
                                        content = content[start_idx:end_idx]

                                    result = json.loads(content)
                                    formatted_results.append({
                                        'bkp_code': result.get('code', 'UNKNOWN'),
                                        'bkp_description': result.get('desc', ''),
                                        'confidence': float(result.get('conf', 0.5))
                                    })
                                except (KeyError, ValueError, TypeError) as e:
                                    # Handle missing keys, invalid float conversion, or None values
                                    formatted_results.append({
                                        'bkp_code': 'ERROR',
                                        'bkp_description': f'Parse Error: {str(e)}',
                                        'confidence': 0.0
                                    })
                            else:
                                # Andere Status (canceled, expired) ebenfalls hinzufügen
                                formatted_results.append({
                                    'bkp_code': result_type.upper(),
                                    'bkp_description': f'Status: {result_type}',
                                    'confidence': 0.0
                                })

                        st.success(f"✅ {len(formatted_results)} Ergebnisse geladen!")

                        # Info über übersprungene Fehler
                        if skipped_errors > 0:
                            st.warning(f"⚠️ {skipped_errors} fehlerhafte Elemente wurden übersprungen (type: errored)")

                        # Ergebnisse als DataFrame speichern (ohne Original-CSV)
                        import pandas as pd
                        results_df = pd.DataFrame(formatted_results)
                        # Verwende dieselben Spaltennamen wie bei normaler Klassifizierung
                        results_df.columns = ['BKP_Code', 'BKP_Beschreibung', 'KI_Konfidenz']

                        set_state(DATA_CLASSIFICATION_RESULTS, results_df)

                        st.info("💡 Ergebnisse wurden in Session State geladen. "
                               "Wechseln Sie zum Tab 'Ergebnisse' für die Auswertung.")

                        # Zeige Vorschau
                        with st.expander("📊 Vorschau", expanded=True):
                            st.dataframe(results_df.head(10))

                    except Exception as e:
                        st.error(f"❌ Fehler beim Verarbeiten der JSONL-Datei: {str(e)}")

        st.divider()

        # Bestehende Batch-Jobs
        st.markdown("**🔄 Laufende Batch-Jobs**")
        pending = batch_manager.get_pending_batches()

        if pending:
            st.info(f"🔄 {len(pending)} Batch-Job(s) in Bearbeitung")

            for batch in pending:
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        st.write(f"**Batch ID:** `{batch['batch_id'][:20]}...`")
                        st.caption(f"Erstellt: {batch['created_at'][:19]}")

                    with col2:
                        st.metric("Elemente", batch['num_elements'])

                    with col3:
                        if st.button("🔍 Status prüfen", key=f"check_{batch['batch_id']}"):
                            with st.spinner("Lade Status..."):
                                try:
                                    # API Key aus Session State
                                    if not get_state(CFG_API_KEY):
                                        st.error("❌ Kein API-Key gefunden. Bitte in Einstellungen konfigurieren.")
                                        continue

                                    # Classifier initialisieren
                                    classifier = eBKPHClassifier(api_key=get_state(CFG_API_KEY))

                                    # Status abrufen
                                    status = classifier.client.messages.batches.retrieve(batch['batch_id'])

                                    if status.processing_status == "ended":
                                        # Ergebnisse laden
                                        results = classifier._download_batch_results(batch['batch_id'])
                                        batch_manager.update_batch_status(batch['batch_id'], "completed")

                                        st.success(f"✅ Batch abgeschlossen! {len(results)} Ergebnisse geladen")

                                        # Ergebnisse in Session State laden (TODO: DF rekonstruieren)
                                        st.info("💡 Ergebnisse wurden geladen. Feature zur DF-Rekonstruktion kommt noch.")

                                    else:
                                        progress = status.request_counts.succeeded / batch['num_elements']
                                        st.progress(progress)
                                        st.info(f"⏳ Status: {status.processing_status} "
                                               f"({status.request_counts.succeeded}/{batch['num_elements']} abgeschlossen)")

                                except Exception as e:
                                    st.error(f"❌ Fehler beim Abrufen: {str(e)}")
                                    batch_manager.update_batch_status(batch['batch_id'], "failed", error_message=str(e))

                    st.divider()
        else:
            st.info("Keine gespeicherten Batch-Jobs vorhanden")

    # ============================================================================
    # Prüfung auf vorbereitete Daten aus Daten-Vorbereitung
    # ============================================================================

    # Get prepared data usage state (already initialized by init_session_state)
    use_prepared_data = get_state(UI_USE_PREPARED_DATA, False)

    if get_state(DATA_PREPARED) is not None and not use_prepared_data:
        st.success("✅ **Vorbereitete Daten gefunden!**")

        prepared_df = get_state(DATA_PREPARED)
        original_df = get_state(DATA_ORIGINAL_UPLOADED)
        dedup_mapping = get_state(DATA_DEDUP_MAPPING)
        unique_elements = get_state(DATA_UNIQUE_ELEMENTS)

        dedup_ratio = len(original_df) / len(prepared_df) if len(prepared_df) > 0 else 0
        cost_saving_pct = (1 - 1/dedup_ratio) * 100 if dedup_ratio > 1 else 0

        st.info(f"""
        **Deduplizierte Daten aus "Daten Vorbereiten":**
        - Original: **{len(original_df):,}** Elemente
        - Einzigartig: **{len(prepared_df):,}** Elemente
        - Reduktion: **{dedup_ratio:.1f}x** ({cost_saving_pct:.1f}% Kostenersparnis)
        """.replace(',', "'"))

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Vorbereitete Daten verwenden", type="primary", width="stretch"):
                set_state(UI_USE_PREPARED_DATA, True)
                st.rerun()

        with col2:
            if st.button("🔄 Neue CSV hochladen", width="stretch"):
                set_state(DATA_PREPARED, None)
                set_state(DATA_DEDUP_MAPPING, None)
                set_state(DATA_UNIQUE_ELEMENTS, None)
                set_state(DATA_ORIGINAL_UPLOADED, None)
                set_state(UI_USE_PREPARED_DATA, False)
                st.rerun()

        st.divider()

    elif use_prepared_data:
        # Zeige Info dass vorbereitete Daten verwendet werden
        st.info("✅ **Vorbereitete Daten werden verwendet** - Fahren Sie mit der Klassifizierung fort")

        if st.button("🔄 Zurück zur Datenauswahl"):
            set_state(UI_USE_PREPARED_DATA, False)
            st.rerun()

        st.divider()

    # ============================================================================
    # CSV Upload (nur wenn keine vorbereiteten Daten verwendet werden)
    # ============================================================================

    if not use_prepared_data:
        st.subheader("CSV-Datei hochladen")

        uploaded_file = st.file_uploader(
            "Wählen Sie eine CSV-Datei",
            type=['csv'],
            help="CSV-Datei mit Spalten wie 'Typ', 'Kategorie', 'Familie', etc."
        )

        if uploaded_file:
            try:
                # CSV einlesen mit automatischer Encoding-Erkennung
                df = None
                encodings = ['utf-8-sig', 'latin1', 'iso-8859-1', 'cp1252']
    
                for encoding in encodings:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, sep=';', encoding=encoding)
                        st.success(f"✅ CSV geladen: {len(df)} Zeilen (Encoding: {encoding})")
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
    
                if df is None:
                    st.error("❌ Fehler: Konnte CSV-Datei mit keinem bekannten Encoding laden. "
                            "Bitte speichern Sie die Datei als UTF-8.")
                    st.stop()
    
                # Spalten-Mapping
                st.subheader("Spalten-Zuordnung")
                st.info("Ordnen Sie die CSV-Spalten den benötigten Feldern zu")
    
                col1, col2 = st.columns(2)
    
                # Hilfsfunktion für automatisches Spalten-Mapping (verwendet config.py Patterns)
                def auto_map_column(df_columns: list, field_name: str) -> str:
                    """
                    Findet automatisch passende Spalte basierend auf Patterns aus config.py

                    Args:
                        df_columns: Liste der verfügbaren Spalten
                        field_name: Gesuchtes Feld ('type', 'category', 'family', 'info')

                    Returns:
                        Spaltenname oder '' falls kein Match
                    """
                    from config import DataValidation

                    # Mapping zu config patterns
                    pattern_mapping = {
                        'type': DataValidation.TYPE_COLUMN_PATTERNS,
                        'category': DataValidation.CATEGORY_COLUMN_PATTERNS,
                        'family': DataValidation.FAMILY_COLUMN_PATTERNS,
                        'info': DataValidation.DESCRIPTION_COLUMN_PATTERNS
                    }

                    search_terms = pattern_mapping.get(field_name, [])

                    # Normalisiere Spaltennamen für besseren Match
                    for col in df_columns:
                        col_clean = col.lower().strip().replace('_', '').replace('-', '').replace(' ', '')
                        for term in search_terms:
                            term_clean = term.lower().replace(' ', '').replace('_', '').replace('-', '')
                            if term_clean in col_clean or col_clean in term_clean:
                                return col

                    return ''  # Kein Match
    
                available_columns = [''] + list(df.columns)
    
                # Automatisches Mapping anwenden
                auto_type = auto_map_column(df.columns.tolist(), 'type')
                auto_category = auto_map_column(df.columns.tolist(), 'category')
                auto_family = auto_map_column(df.columns.tolist(), 'family')
                auto_info = auto_map_column(df.columns.tolist(), 'info')
    
                # Zeige Info wenn Auto-Mapping erfolgreich
                if any([auto_type, auto_category, auto_family, auto_info]):
                    st.success("✅ Automatisches Spalten-Mapping angewendet")
    
                with col1:
                    type_column = st.selectbox(
                        "Element-Typ (Pflicht)",
                        available_columns,
                        index=available_columns.index(auto_type) if auto_type in available_columns else 0,
                        help="Spalte mit dem Element-Typ (z.B. 'Steckdose', 'Wand')"
                    )
    
                    category_column = st.selectbox(
                        "Kategorie (Optional)",
                        available_columns,
                        index=available_columns.index(auto_category) if auto_category in available_columns else 0,
                        help="Spalte mit der Revit-Kategorie"
                    )
    
                with col2:
                    family_column = st.selectbox(
                        "Familie (Optional)",
                        available_columns,
                        index=available_columns.index(auto_family) if auto_family in available_columns else 0,
                        help="Spalte mit dem Family-Namen"
                    )
    
                    info_column = st.selectbox(
                        "Zusatzinfo (Optional)",
                        available_columns,
                        index=available_columns.index(auto_info) if auto_info in available_columns else 0,
                        help="Weitere Beschreibungsspalte"
                    )

                # === VALIDIERUNG ===
                # Prüfe ob Pflichtfeld ausgewählt wurde
                if not type_column or type_column == '':
                    st.warning("⚠️ **Element-Typ ist ein Pflichtfeld!**")
                    st.info("Bitte wählen Sie eine Spalte für den Element-Typ aus, um fortzufahren.")
                    st.stop()

                # Validiere dass Spalte im DataFrame existiert
                if type_column not in df.columns:
                    st.error(f"❌ Spalte '{type_column}' nicht im DataFrame gefunden!")
                    st.stop()

                # Datenvorschau
                st.subheader("Datenvorschau")
                st.dataframe(df.head(10), width='stretch')

                # === MODUS-AUSWAHL ===
                st.markdown("---")
                st.subheader("🎯 Verarbeitungs-Modus")

                # type_column ist jetzt garantiert gültig
                num_elements = len(df)

                # Automatische Modus-Auswahl + manuelle Override-Option
                force_batch_api = get_state(CFG_FORCE_BATCH_API, False)
                use_batch_api = (num_elements >= 300) or force_batch_api

                # Info-Box zum gewählten Modus
                if use_batch_api:
                    reason = "automatisch ab 300 Elementen" if num_elements >= 300 else "manuell aktiviert (Einstellungen)"
                    st.info(
                        f"📦 **Batch API Modus** ({reason})\n\n"
                        f"✅ 50% Kostenersparnis\n"
                        f"✅ Keine Rate-Limits\n"
                        f"⏱ Geschätzte Wartezeit: {num_elements // 20}-{num_elements // 10} Minuten"
                    )

                    if num_elements < 300 and force_batch_api:
                        st.warning("⚠️ Batch API für < 300 Elemente: Längere Wartezeit für Kostenersparnis")

                else:
                    st.info(
                        f"⚡ **Synchron-Modus** ({num_elements} Elemente)\n\n"
                        f"✅ Schnellere Verarbeitung (~{(num_elements // batch_size + 1) * 3} Min)\n"
                        f"✅ Echtzeit-Feedback\n"
                        f"✅ Intelligentes Rate-Limiting"
                    )

                    if num_elements >= 200:
                        st.info("💡 **Tipp:** Ab 300 Elementen wird automatisch Batch API genutzt (50% günstiger). "
                               "Kann in Einstellungen auch für kleinere Datasets aktiviert werden.")

                # Kostenabschätzung
                #TODO kostenabschätzung grundlagen erstellen
                if type_column:
                    cost_estimate = estimate_cost(num_elements, use_batch, batch_size, use_batch_api)
    
                    st.markdown("---")
                    st.subheader("💰 Kostenabschätzung")
    
                    col1, col2, col3, col4, col5 = st.columns(5)
    
                    with col1:
                        st.metric("Elemente", num_elements)
    
                    with col2:
                        st.metric("API-Anfragen", cost_estimate['num_requests'])
    
                    with col3:
                        st.metric("Modus", cost_estimate['mode'])
    
                    with col4:
                        st.metric("Geschätzte Tokens",
                                 f"{cost_estimate['input_tokens'] + cost_estimate['output_tokens']:,}")
    
                    with col5:
                        st.metric("Geschätzte Kosten",
                                 f"${cost_estimate['total_cost']:.4f}")
    
                    # Kostenersparnis anzeigen bei Batch API
                    if use_batch_api:
                        sync_cost_estimate = estimate_cost(num_elements, use_batch, batch_size, use_batch_api=False)
                        savings = sync_cost_estimate['total_cost'] - cost_estimate['total_cost']
                        savings_percent = (savings / sync_cost_estimate['total_cost']) * 100
                        st.success(f"💰 **Kostenersparnis durch Batch API:** ${savings:.4f} ({savings_percent:.0f}%)")
    
                    st.caption(f"Input: {cost_estimate['input_tokens']:,} tokens (${cost_estimate['input_cost']:.4f}) | "
                              f"Output: {cost_estimate['output_tokens']:,} tokens (${cost_estimate['output_cost']:.4f})")
    
                    # Berechnungsgrundlagen Expander
                    with st.expander("ℹ️ Berechnungsgrundlagen", expanded=False):
                        st.markdown(f"""
                        ### 📊 Kostenberechnung
    
                        **Modell:** Claude 3.5 Haiku
                        - **Input:** $0.80 / 1M tokens
                        - **Output:** $4.00 / 1M tokens
    
                        **Prompt Caching (Kostenersparnis):**
                        - **Erster Request:** Volle System-Prompt-Kosten (~3,000 tokens)
                        - **Weitere Requests:** 90% günstiger (nur ~300 tokens durch Caching)
    
                        **Batch-Verarbeitung:**
                        - **Batch-Größe:** {batch_size} Elemente pro Request
                        - **Total Requests:** {cost_estimate['num_requests']}
                        - **Durchschnitt:** ${cost_estimate['total_cost']/num_elements:.6f} pro Element
    
                        **Token-Verteilung:**
                        - **Input:** {cost_estimate['input_tokens']:,} tokens (${cost_estimate['input_cost']:.4f})
                          - System Prompt: ~3,000 tokens (einmalig)
                          - Cached Prompts: ~300 tokens pro weiterer Request
                          - Element-Daten: ~50 tokens pro Element
                        - **Output:** {cost_estimate['output_tokens']:,} tokens (${cost_estimate['output_cost']:.4f})
                          - BKP-Code + Beschreibung: ~30 tokens pro Element
    
                        **Vergleich Batch vs. Einzeln:**
                        """)
    
                        # Berechne Einzelkosten zum Vergleich
                        single_estimate = estimate_cost(num_elements, False, 1)
    
                        st.markdown(f"""
                        - **Batch-Modus:** ${cost_estimate['total_cost']:.4f} ({num_elements} Elemente)
                        - **Einzeln:** ${single_estimate['total_cost']:.4f} (gleiche Elemente)
                        - **Ersparnis:** {(1 - cost_estimate['total_cost']/single_estimate['total_cost'])*100:.1f}%
    
                        💡 **Tipp:** Batch-Modus nutzt Prompt Caching optimal und spart bis zu 80% der Kosten!
                        """)
    
                        # Optional: Modell-Vergleich
                        if st.checkbox("Modell-Vergleich anzeigen"):
                            st.markdown("### 🏷️ Kostenvergleich Modelle")
    
                            models = {
                                'Haiku': {'input': 0.80, 'output': 4.00},
                                'Sonnet': {'input': 3.00, 'output': 15.00},
                                'Opus 4': {'input': 15.00, 'output': 75.00}
                            }
    
                            comparison_data = []
                            for model_name, pricing in models.items():
                                # Vereinfachte Berechnung
                                input_cost = (cost_estimate['input_tokens'] / 1_000_000) * pricing['input']
                                output_cost = (cost_estimate['output_tokens'] / 1_000_000) * pricing['output']
                                total = input_cost + output_cost
    
                                comparison_data.append({
                                    'Modell': model_name,
                                    'Kosten': f"${total:.4f}",
                                    'Pro Element': f"${total/num_elements:.6f}"
                                })
    
                            st.table(comparison_data)
    
                    # Klassifizierung starten
                    st.markdown("---")
    
                    if st.button("🚀 Klassifizierung starten", type="primary", width='stretch'):
                        # Log und API responses zurücksetzen
                        set_state(PROC_PROCESSING_LOG, [])
                        set_state(PROC_API_RESPONSES, [])  # Reset API responses
                        set_state(PROC_TOTAL_COST, cost_estimate['total_cost'])
    
                        add_log("Klassifizierung gestartet", "info")
                        add_log(f"Modus: {'Batch' if use_batch else 'Einzeln'}", "info")
                        add_log(f"{num_elements} Elemente zu klassifizieren", "info")
    
                        # Progress Bar und Live-Response-Container
                        progress_bar = st.progress(0)
                        status_text = st.empty()
    
                        # Live API Response Display Container
                        with st.expander("🔍 API Responses (Live)", expanded=True):
                            live_response_container = st.empty()
    
                        try:
                            # Classifier initialisieren mit API-Key aus Session State
                            add_log("eBKP-H Classifier initialisieren...", "info")
    
                            # API-Key holen
                            api_key = get_api_key()
    
                            # Hole max_levels aus Kostenermittlungs-Config (oder Default)
                            max_levels = [1, 2]  # Default
                            if get_state(CFG_COST_ESTIMATION_CONFIG).get('selected'):
                                max_levels = get_state(CFG_COST_ESTIMATION_CONFIG)['ebkp_levels']
                                add_log(f"Verwende eBKP Levels aus Kostenermittlung: {max_levels}", "info")
                            else:
                                add_log(f"Keine Kostenermittlung gewählt, verwende Standard-Levels: {max_levels}", "info")
    
                            # Classifier mit API-Key und max_levels initialisieren
                            classifier = eBKPHClassifier(api_key=api_key, max_levels=max_levels)
    
                            # Log-Datei für API-Responses erstellen
                            from datetime import datetime
                            log_filename = f"ebkp_classification_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                            log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Logs', log_filename)
                            os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
                            add_log(f"API-Response-Log wird gespeichert: {log_filename}", "info")

                            # Erstelle Element-Liste für Klassifizierung
                            all_elements = []
                            for _, row in df.iterrows():
                                elem = {
                                    'kategorie': row.get(category_column, '') if category_column else '',
                                    'typ': row.get(type_column, '') if type_column else '',
                                    'familie': row.get(family_column, '') if family_column else '',
                                    'zusatzinfo': row.get(info_column, '') if info_column else ''
                                }
                                all_elements.append(elem)

                            # Track element counts for deduplication
                            num_unique_elements = len(all_elements)  # Unique elements to classify
                            num_elements = len(df)  # Total elements in dataframe

                            add_log(f"Bereite {len(all_elements)} Elemente für Klassifizierung vor", "info")

                            results = []

                            if use_batch_api:
                                # === BATCH API MODUS ===
                                add_log("🚀 Batch API Modus aktiviert", "info")
                                add_log(f"{len(all_elements)} Elemente → Batch-Job erstellen", "info")

                                status_text.text(f"Erstelle Batch-Job mit {len(all_elements)} Elementen...")

                                # Batch-Job erstellen
                                batch_id, _ = classifier.classify_batch_api(
                                    all_elements,
                                    wait_for_completion=False
                                )
    
                                # Batch-Metadata speichern
                                batch_manager.save_batch_metadata(
                                    batch_id=batch_id,
                                    num_elements=num_unique_elements,  # Einzigartige Elemente
                                    csv_filename=uploaded_file.name
                                )
    
                                add_log(f"✅ Batch-Job erstellt: {batch_id}", "success")
    
                                # Nutzer-Auswahl: Jetzt warten oder später prüfen
                                st.success(f"✅ Batch-Job erstellt: `{batch_id}`")
    
                                col1, col2 = st.columns(2)
    
                                with col1:
                                    wait_now = st.button("⏳ Jetzt warten und Ergebnisse laden", key="wait_now", type="primary")
    
                                with col2:
                                    check_later = st.button("📌 Später prüfen (Session beenden)", key="check_later")
    
                                if wait_now:
                                    # OPTION 1: Synchrones Polling
                                    add_log("Warte auf Batch-Verarbeitung...", "info")
                                    status_text.text("Warte auf Batch-Verarbeitung (alle 10s prüfen)...")
    
                                    with st.spinner("Batch wird verarbeitet..."):
                                        while True:
                                            status = classifier.client.messages.batches.retrieve(batch_id)
    
                                            if status.processing_status == "ended":
                                                break
    
                                            # Progress anzeigen
                                            progress = status.request_counts.succeeded / num_unique_elements
                                            progress_bar.progress(progress)
                                            status_text.text(
                                                f"⏳ Verarbeitung läuft: {status.request_counts.succeeded}/{num_unique_elements} einzigartige Elemente "
                                                f"({progress:.0%})"
                                            )
    
                                            time.sleep(10)
    
                                        # Ergebnisse laden
                                        add_log("Lade Batch-Ergebnisse...", "info")
                                        status_text.text("Lade Ergebnisse...")
    
                                        batch_results = classifier._download_batch_results(batch_id)
    
                                        # Formatiere Ergebnisse für Kompatibilität
                                        results = [
                                            {
                                                'bkp_code': r['code'],
                                                'bkp_description': r['desc'],
                                                'confidence': r['conf'],
                                                'raw_response': f'{{"code": "{r["code"]}", "desc": "{r["desc"]}", "conf": {r["conf"]}}}'
                                            }
                                            for r in batch_results
                                        ]
    
                                        # Batch-Status aktualisieren
                                        batch_manager.update_batch_status(batch_id, "completed")
    
                                        add_log(f"✅ {len(results)} Ergebnisse geladen!", "success")
                                        progress_bar.progress(1.0)
                                        status_text.text("✅ Batch-Verarbeitung abgeschlossen!")
    
                                elif check_later:
                                    # OPTION 2: Batch-ID gespeichert
                                    add_log(f"Batch-ID {batch_id} gespeichert für späteren Abruf", "info")
                                    st.info(
                                        f"✅ Batch-ID `{batch_id}` wurde gespeichert.\n\n"
                                        f"Sie können diese Seite schließen und später mit dem Button "
                                        f"'Gespeicherte Batch-Jobs prüfen' oben zurückkehren."
                                    )
                                    st.stop()  # Verarbeitung hier beenden
    
                                else:
                                    # Noch keine Auswahl getroffen
                                    st.info("👆 Bitte wählen Sie eine Option oben")
                                    st.stop()
    
                            elif use_batch:
                                # Batch-Verarbeitung (mit deduplizierten Elementen)
                                add_log(f"Batch-Verarbeitung: {num_unique_elements} einzigartige Elemente, Batch-Größe {batch_size}", "info")
    
                                total_batches = (num_unique_elements + batch_size - 1) // batch_size
    
                                for batch_idx in range(0, num_unique_elements, batch_size):
                                    batch_end = min(batch_idx + batch_size, num_unique_elements)
    
                                    current_batch = (batch_idx // batch_size) + 1
                                    status_text.text(f"Verarbeite Batch {current_batch}/{total_batches} (einzigartige Elemente)...")

                                    # Verwende all_elements (aus CSV oder prepared data)
                                    batch_elements = all_elements[batch_idx:batch_end]
    
                                    # Batch klassifizieren (mit Debug-Modus und Logging)
                                    batch_results = classifier.classify_batch(
                                        batch_elements,
                                        debug=debug_mode,
                                        log_file=log_path
                                    )
    
                                    # Formatiere Ergebnisse für Kompatibilität mit bestehendem Code
                                    batch_results = [
                                        {
                                            'bkp_code': r['code'],
                                            'bkp_description': r['desc'],
                                            'confidence': r['conf'],
                                            'raw_response': f'{{"code": "{r["code"]}", "desc": "{r["desc"]}", "conf": {r["conf"]}}}'
                                        }
                                        for r in batch_results
                                    ]
    
                                    # Speichere API-Responses für jedes Element im Batch
                                    for elem_idx, (elem, result) in enumerate(zip(batch_elements, batch_results)):
                                        element_info = elem.get('typ', 'N/A')
                                        if elem.get('kategorie'):
                                            element_info += f" ({elem['kategorie']})"
    
                                        # Speichere Response
                                        add_api_response(
                                            request_num=batch_idx + elem_idx + 1,
                                            element_info=element_info,
                                            response=result.get('raw_response', 'N/A'),
                                            parsed_result={
                                                'bkp_code': result['bkp_code'],
                                                'bkp_description': result['bkp_description'],
                                                'confidence': result['confidence']
                                            }
                                        )
    
                                    results.extend(batch_results)
    
                                    # Progress aktualisieren (basierend auf einzigartigen Elementen)
                                    progress = (batch_end / num_unique_elements)
                                    progress_bar.progress(progress)
    
                                    # Live-Update: Zeige neueste Responses
                                    if get_state(PROC_API_RESPONSES):
                                        latest_responses = get_state(PROC_API_RESPONSES)[-5:]  # Zeige letzte 5
                                        live_response_container.markdown(
                                            f"**Letzte {len(latest_responses)} Responses:**\n\n" +
                                            "\n".join([
                                                f"- Request #{r['request_num']}: {r['parsed_result']['bkp_code']} "
                                                f"({r['parsed_result']['confidence']:.0%}) - {r['element'][:30]}..."
                                                for r in latest_responses
                                            ])
                                        )
    
                                    add_log(f"Batch {current_batch}/{total_batches} abgeschlossen "
                                           f"({len(batch_results)} Elemente)", "success")
    
                                    # Kurze Pause zwischen Batches
                                    time.sleep(0.5)
    
                            else:
                                # Einzelverarbeitung
                                add_log("Einzelverarbeitung gestartet", "info")
    
                                for idx, row in df.iterrows():
                                    status_text.text(f"Verarbeite Element {idx + 1}/{num_elements}...")
    
                                    # Klassifiziere Element
                                    result = classifier.classify_element(
                                        kategorie=row[category_column] if category_column else '',
                                        typ=row[type_column] if type_column else '',
                                        familie=row[family_column] if family_column else '',
                                        zusatzinfo=row[info_column] if info_column else '',
                                        debug=debug_mode
                                    )
    
                                    # Speichere API-Response
                                    element_info = row[type_column] if type_column else 'N/A'
                                    if category_column and row[category_column]:
                                        element_info += f" ({row[category_column]})"
    
                                    # Formatiere für Kompatibilität
                                    formatted_result = {
                                        'bkp_code': result['code'],
                                        'bkp_description': result['desc'],
                                        'confidence': result['conf'],
                                        'raw_response': f'{{"code": "{result["code"]}", "desc": "{result["desc"]}", "conf": {result["conf"]}}}'
                                    }
    
                                    add_api_response(
                                        request_num=idx + 1,
                                        element_info=element_info,
                                        response=formatted_result['raw_response'],
                                        parsed_result={
                                            'bkp_code': formatted_result['bkp_code'],
                                            'bkp_description': formatted_result['bkp_description'],
                                            'confidence': formatted_result['confidence']
                                        }
                                    )
    
                                    results.append(formatted_result)
    
                                    # Progress aktualisieren
                                    progress = ((idx + 1) / num_elements)
                                    progress_bar.progress(progress)
    
                                    # Live-Update: Zeige neueste Responses
                                    if (idx + 1) % 5 == 0 or idx == num_elements - 1:  # Update alle 5 Elemente
                                        latest_responses = get_state(PROC_API_RESPONSES)[-5:]
                                        live_response_container.markdown(
                                            f"**Letzte {len(latest_responses)} Responses:**\n\n" +
                                            "\n".join([
                                                f"- Request #{r['request_num']}: {r['parsed_result']['bkp_code']} "
                                                f"({r['parsed_result']['confidence']:.0%}) - {r['element'][:30]}..."
                                                for r in latest_responses
                                            ])
                                        )
    
                                    if (idx + 1) % 10 == 0:
                                        add_log(f"{idx + 1}/{num_elements} Elemente klassifiziert", "info")
    
                            # Check if deduplication mapping exists (from prepared data)
                            dedup_mapping = get_state(DATA_DEDUP_MAPPING)

                            if dedup_mapping is not None:
                                # Ergebnisse zu allen Original-Elementen mappen (via Deduplizierungs-Mapping)
                                add_log(f"🔄 Mappe {len(results)} Klassifizierungen auf {len(df)} Original-Elemente...", "info")

                                df = map_classifications_back(
                                    df=df,
                                    index_mapping=dedup_mapping,
                                    classification_results=results
                                )

                                # Rename columns to match expected format
                                df = df.rename(columns={
                                    'bkp_code': 'BKP_Code',
                                    'bkp_description': 'BKP_Beschreibung',
                                    'confidence': 'KI_Konfidenz'
                                })

                                add_log(f"✅ Mapping abgeschlossen: {len(df)} Elemente haben BKP-Codes", "success")
                            else:
                                # No deduplication - add results directly to dataframe
                                add_log(f"Füge Klassifizierungen direkt zu {len(df)} Elementen hinzu...", "info")

                                # Add classification results as new columns with correct names
                                df['BKP_Code'] = [r['bkp_code'] for r in results]
                                df['BKP_Beschreibung'] = [r['bkp_description'] for r in results]
                                df['KI_Konfidenz'] = [r['confidence'] for r in results]

                                add_log(f"✅ {len(df)} Elemente klassifiziert", "success")
    
                            # In Session State speichern
                            set_state(DATA_CLASSIFICATION_RESULTS, df)
    
                            progress_bar.progress(1.0)
                            status_text.text("Klassifizierung abgeschlossen!")
    
                            add_log(f"✅ Klassifizierung erfolgreich abgeschlossen", "success")
                            add_log(f"Durchschnittliche Konfidenz: {df['KI_Konfidenz'].mean():.1%}", "success")
                            add_log(f"📊 {len(get_state(PROC_API_RESPONSES))} API-Responses aufgezeichnet", "success")
                            add_log(f"📝 Detailliertes Log gespeichert: {log_filename}", "success")
    
                            # Live-Container Final Update
                            live_response_container.success(
                                f"✅ Klassifizierung abgeschlossen! {len(get_state(PROC_API_RESPONSES))} API-Responses aufgezeichnet.\n\n"
                                f"➡️ Wechseln Sie zum Tab **'KI Responses'** für Details."
                            )
    
                            # Success Message mit nächsten Schritten
                            st.success("✅ Klassifizierung erfolgreich abgeschlossen!")
    
                            # Download-Button für Log-Datei
                            if os.path.exists(log_path):
                                with open(log_path, 'r', encoding='utf-8') as f:
                                    log_content = f.read()
                                st.download_button(
                                    label="📥 API-Response-Log herunterladen",
                                    data=log_content,
                                    file_name=log_filename,
                                    mime="text/plain",
                                    help="Enthält alle API-Requests und Responses für Debugging"
                                )
    
                            toast("Klassifizierung erfolgreich abgeschlossen!", NotificationType.SUCCESS)
                            st.balloons()
    
                            # Automatischer Workflow-Hinweis
                            st.info("""
                            ### 🎉 Ihre Daten wurden klassifiziert!
    
                            **Nächste Schritte:**
                            1. **Ergebnisse prüfen** → Wechseln Sie zum Tab "Ergebnisse"
                            2. **KI Responses ansehen** → Tab "KI Responses" für Details
                            3. **Zur Auswertung** → Ihre Daten sind automatisch für die eBKP-H Auswertung verfügbar!
    
                            → Gehen Sie zur Seite **"eBKP Auswertung"** in der Seitenleiste links.
                            """)
    
                            # Direct Action Buttons
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("📊 Zu den Ergebnissen", type="primary", width='stretch'):
                                    set_state(PROC_ACTIVE_TAB, 1)  # Tab "Ergebnisse"
                                    st.rerun()
    
                            with col2:
                                # Verwende Link statt HTML-Button für bessere Dark Mode Kompatibilität
                                st.page_link("pages/06_eBKP_Auswertung.py", label="🔍 Zur eBKP-H Auswertung", icon="📊")
    
                        except Exception as e:
                            add_log(f"Fehler: {str(e)}", "error")
                            st.error(f"Fehler bei der Klassifizierung: {str(e)}")

            except Exception as e:
                st.error(f"Fehler beim Laden der CSV-Datei: {str(e)}")

        else:
            st.info("👆 Bitte laden Sie eine CSV-Datei hoch, um zu beginnen")

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                ### 📋 So geht's:

                1. **CSV hochladen**
                   - Datei mit Bauelementen
                   - OHNE BKP-Codes

                2. **Spalten zuordnen**
                   - Typ (Pflicht)
                   - Kategorie, Familie (optional)

                3. **Klassifizierung starten**
                   - Prüfen Sie die Kosten
                   - Klicken Sie auf "Starten"

                4. **Ergebnisse exportieren**
                   - Tab "Ergebnisse"
                   - Als CSV herunterladen
                """)

            with col2:
                st.markdown("""
                ### 🧪 Mit Testdaten starten:

                Nutzen Sie die Datei:
                **`muster_ki_klassifizierung.csv`**

                Diese Datei enthält:
                - 30 Bauelemente
                - Verschiedene Kategorien
                - Ohne BKP-Codes

                Perfekt zum Testen der KI!
                """)

    else:
        # ========================================================================
        # Using Prepared Data - Process and allow classification
        # ========================================================================

        st.subheader("Vorbereitete Daten klassifizieren")

        # Load prepared data from session state
        df = get_state(DATA_PREPARED)
        unique_elements = get_state(DATA_UNIQUE_ELEMENTS)

        if df is None or unique_elements is None:
            st.error("❌ Fehler: Vorbereitete Daten nicht gefunden!")
            st.info("Bitte gehen Sie zurück zur 'Daten Vorbereiten' Seite und bereiten Sie die Daten vor.")
            st.stop()

        st.success(f"✅ Vorbereitete Daten geladen: **{len(df)}** eindeutige Elemente")

        # Show data statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Eindeutige Elemente", len(df))
        with col2:
            original_df = get_state(DATA_ORIGINAL_UPLOADED)
            if original_df is not None:
                st.metric("Original-Zeilen", len(original_df))
        with col3:
            st.metric("Spalten", len(df.columns))

        # Show a preview of the data
        with st.expander("📋 Datenvorschau", expanded=True):
            st.dataframe(df.head(20), use_container_width=True)

        st.divider()

        # Classification settings
        st.subheader("⚙️ Klassifizierungs-Einstellungen")

        col1, col2 = st.columns(2)
        with col1:
            use_batch = st.checkbox("Batch-Verarbeitung (empfohlen)", value=True,
                                   help="Verarbeitet mehrere Elemente pro API-Call für bessere Effizienz")
        with col2:
            if use_batch:
                batch_size = st.slider("Batch-Größe", min_value=10, max_value=50, value=40,
                                      help="Anzahl Elemente pro Batch")
            else:
                batch_size = 1

        # Check for API key
        api_key = get_api_key()
        if not api_key:
            st.warning("⚠️ Kein API-Schlüssel konfiguriert!")
            st.info("Bitte gehen Sie zur Seite '⚙️ Einstellungen' und konfigurieren Sie Ihren Anthropic API-Schlüssel.")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.page_link("pages/99_Einstellungen.py", label="➡️ Zu den Einstellungen", icon="⚙️")
            st.stop()

        st.divider()

        # Cost estimation
        st.subheader("💰 Kostenabschätzung")
        num_elements = len(unique_elements)

        # Use the existing estimate_cost function
        cost_estimate = estimate_cost(num_elements, use_batch, batch_size)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Elemente", f"{num_elements:,}".replace(',', "'"))
        with col2:
            st.metric("Requests", cost_estimate['num_requests'])
        with col3:
            st.metric("Tokens", f"{cost_estimate['input_tokens'] + cost_estimate['output_tokens']:,}".replace(',', "'"))
        with col4:
            st.metric("Kosten", f"${cost_estimate['total_cost']:.4f}")

        st.caption(f"Input: {cost_estimate['input_tokens']:,} tokens | Output: {cost_estimate['output_tokens']:,} tokens")

        st.divider()

        # Classification button
        st.subheader("🚀 Klassifizierung starten")

        st.info("""
        ℹ️ **Hinweis:** Die Klassifizierung verwendet die vorbereiteten, deduplizierten Daten.
        Nach der Klassifizierung können die Ergebnisse automatisch auf alle Original-Elemente übertragen werden.
        """)

        if st.button("🤖 KI-Klassifizierung starten", type="primary", use_container_width=True):
            st.warning("⚠️ Die Klassifizierungslogik für vorbereitete Daten wird noch finalisiert.")
            st.info("""
            **Nächste Schritte:**
            1. Die Klassifizierung sollte die `unique_elements` aus Session State verwenden
            2. Nach der Klassifizierung müssen die Ergebnisse mit dem `dedup_mapping` auf die Original-Daten übertragen werden
            3. Die Ergebnisse werden dann in `classification_results` gespeichert

            Aktuell können Sie:
            - Die deduplizierten Daten als CSV herunterladen (auf Seite "Daten Vorbereiten")
            - Die CSV manuell auf dieser Seite hochladen und klassifizieren
            """)

def render_confidence_badge(confidence: float) -> str:
    """Zeigt Konfidenz als farbiges Badge"""
    if confidence >= 0.9:
        icon, color, label = "🟢", "#00cc00", "Sehr gut"
    elif confidence >= 0.7:
        icon, color, label = "🟡", "#ffcc00", "Gut"
    elif confidence >= 0.5:
        icon, color, label = "🟠", "#ff9900", "Mittel"
    else:
        icon, color, label = "🔴", "#ff3333", "Niedrig"

    return f"""
    <div style="
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 4px 12px;
        border-radius: 20px;
        background: {color}20;
        border: 1px solid {color};
        font-size: 0.85rem;
    ">
        <span>{icon}</span>
        <strong>{label}</strong>
        <span style="opacity: 0.7">{confidence:.0%}</span>
    </div>
    """


with tab2:
    st.subheader("📊 Klassifizierungs-Ergebnisse")

    if get_state(DATA_CLASSIFICATION_RESULTS) is not None:
        df_results = get_state(DATA_CLASSIFICATION_RESULTS)

        # Metriken
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Klassifizierte Elemente", len(df_results))

        with col2:
            avg_confidence = df_results['KI_Konfidenz'].mean()
            st.metric("Ø Konfidenz", f"{avg_confidence:.1%}")

        with col3:
            low_confidence = len(df_results[df_results['KI_Konfidenz'] < confidence_threshold])
            st.metric("Niedrige Konfidenz", low_confidence,
                     delta=f"{(low_confidence/len(df_results)*100):.1f}%",
                     delta_color="inverse")

        with col4:
            unique_codes = df_results['BKP_Code'].nunique()
            st.metric("Verschiedene BKP-Codes", unique_codes)

        # Konfidenz-Badge Visualisierung
        st.markdown("**Durchschnittliche Konfidenz:** " + render_confidence_badge(avg_confidence), unsafe_allow_html=True)

        st.markdown("---")

        # Visualisierungen
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Konfidenz-Verteilung")
            fig_conf = px.histogram(
                df_results,
                x='KI_Konfidenz',
                nbins=20,
                title='Verteilung der KI-Konfidenz',
                labels={'KI_Konfidenz': 'Konfidenz', 'count': 'Anzahl'}
            )
            fig_conf.add_vline(x=confidence_threshold, line_dash="dash", line_color="red",
                              annotation_text=f"Schwellenwert ({confidence_threshold})")
            st.plotly_chart(fig_conf, width='stretch')

        with col2:
            st.subheader("Top 10 BKP-Codes")
            bkp_counts = df_results['BKP_Code'].value_counts().head(10)
            fig_bkp = px.bar(
                x=bkp_counts.index,
                y=bkp_counts.values,
                title='Häufigste BKP-Codes',
                labels={'x': 'BKP Code', 'y': 'Anzahl'}
            )
            st.plotly_chart(fig_bkp, width='stretch')

        st.markdown("---")

        # === HIERARCHISCHE BKP-DARSTELLUNG ===
        st.subheader("🗂️ BKP-Hierarchie")

        # Hauptgruppen-Übersicht (Level 1)
        st.markdown("### 📊 Übersicht Hauptgruppen")

        # Extrahiere Hauptgruppe (erster Buchstabe)
        df_results['Hauptgruppe'] = df_results['BKP_Code'].str[0]

        # Gruppiere nach Hauptgruppe
        hauptgruppen = df_results.groupby('Hauptgruppe').agg({
            'BKP_Code': 'count',
            'KI_Konfidenz': 'mean'
        }).rename(columns={'BKP_Code': 'Anzahl', 'KI_Konfidenz': 'Ø Konfidenz'})

        # Zeige Hauptgruppen in Spalten
        num_groups = len(hauptgruppen)
        cols_per_row = 5
        rows = (num_groups + cols_per_row - 1) // cols_per_row

        for row in range(rows):
            cols = st.columns(cols_per_row)
            for i, col in enumerate(cols):
                idx = row * cols_per_row + i
                if idx < num_groups:
                    group = hauptgruppen.index[idx]
                    count = hauptgruppen.iloc[idx]['Anzahl']
                    conf = hauptgruppen.iloc[idx]['Ø Konfidenz']

                    with col:
                        st.metric(
                            f"Gruppe {group}",
                            f"{count} Elemente",
                            delta=f"{conf:.0%} Konfidenz"
                        )

        st.markdown("---")
        st.markdown("### 🔍 Detaillierte Hierarchie")
        st.caption("Klicken Sie auf die Gruppen, um die Hierarchie zu erkunden")

        # Funktion zum Parsen der BKP-Hierarchie
        def parse_bkp_hierarchy(df):
            """Erstellt eine hierarchische Struktur aus BKP-Codes"""
            hierarchy = {}

            for _, row in df.iterrows():
                code = row['BKP_Code']
                desc = row['BKP_Beschreibung']
                conf = row['KI_Konfidenz']

                # Parse Hierarchie-Levels
                # Level 1: A (Buchstabe)
                # Level 2: A01 (Buchstabe + 2 Ziffern)
                # Level 3: A01.02 (mit Punkt)
                # Level 4: A01.02.005 (mit zweitem Punkt)

                parts = code.split('.')

                # Level 1
                level1 = code[0]
                if level1 not in hierarchy:
                    hierarchy[level1] = {'count': 0, 'conf_sum': 0, 'children': {}}

                hierarchy[level1]['count'] += 1
                hierarchy[level1]['conf_sum'] += conf

                # Level 2 (falls vorhanden)
                if len(code) >= 3:
                    level2 = code[:3]  # z.B. "B03"
                    if level2 not in hierarchy[level1]['children']:
                        hierarchy[level1]['children'][level2] = {'count': 0, 'conf_sum': 0, 'children': {}}

                    hierarchy[level1]['children'][level2]['count'] += 1
                    hierarchy[level1]['children'][level2]['conf_sum'] += conf

                    # Level 3 (falls vorhanden)
                    if len(parts) >= 2:
                        level3 = parts[0]  # z.B. "B03.02"
                        if level3 not in hierarchy[level1]['children'][level2]['children']:
                            hierarchy[level1]['children'][level2]['children'][level3] = {
                                'count': 0, 'conf_sum': 0, 'items': []
                            }

                        hierarchy[level1]['children'][level2]['children'][level3]['count'] += 1
                        hierarchy[level1]['children'][level2]['children'][level3]['conf_sum'] += conf

                        # Level 4 (einzelne Codes)
                        hierarchy[level1]['children'][level2]['children'][level3]['items'].append({
                            'code': code,
                            'desc': desc,
                            'conf': conf
                        })

            return hierarchy

        # Erstelle Hierarchie
        hierarchy = parse_bkp_hierarchy(df_results)

        # Zeige Hierarchie mit Expanders
        for level1, level1_data in sorted(hierarchy.items()):
            avg_conf_l1 = level1_data['conf_sum'] / level1_data['count']

            with st.expander(
                f"**{level1}** - {level1_data['count']} Elemente (Ø {avg_conf_l1:.0%})",
                expanded=False
            ):
                # Level 2
                for level2, level2_data in sorted(level1_data['children'].items()):
                    avg_conf_l2 = level2_data['conf_sum'] / level2_data['count']

                    st.markdown(f"#### {level2} - {level2_data['count']} Elemente (Ø {avg_conf_l2:.0%})")

                    # Level 3
                    for level3, level3_data in sorted(level2_data['children'].items()):
                        avg_conf_l3 = level3_data['conf_sum'] / level3_data['count']

                        with st.expander(
                            f"  {level3} - {level3_data['count']} Elemente (Ø {avg_conf_l3:.0%})",
                            expanded=False
                        ):
                            # Level 4 (einzelne Codes)
                            for item in sorted(level3_data['items'], key=lambda x: x['code']):
                                conf_badge = render_confidence_badge(item['conf'])
                                st.markdown(
                                    f"- **{item['code']}**: {item['desc']} {conf_badge}",
                                    unsafe_allow_html=True
                                )

        st.markdown("---")

        # Qualitätskontrolle: Niedrige Konfidenz
        st.subheader("⚠️ Qualitätskontrolle")
        low_conf_df = df_results[df_results['KI_Konfidenz'] < confidence_threshold]

        if not low_conf_df.empty:
            st.warning(f"{len(low_conf_df)} Elemente haben eine Konfidenz unter {confidence_threshold:.0%}")
            st.dataframe(
                low_conf_df.style.background_gradient(subset=['KI_Konfidenz'], cmap='RdYlGn'),
                width='stretch'
            )
        else:
            st.success(f"✅ Alle Elemente haben eine Konfidenz über {confidence_threshold:.0%}")

        st.markdown("---")

        # Vollständige Ergebnisse
        st.subheader("📑 Vollständige Ergebnisse")
        st.dataframe(
            df_results.style.background_gradient(subset=['KI_Konfidenz'], cmap='RdYlGn'),
            width='stretch'
        )

        # Export
        st.markdown("---")
        st.subheader("💾 Export")

        col1, col2 = st.columns(2)

        with col1:
            csv_export = df_results.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button(
                label="📥 Als CSV herunterladen",
                data=csv_export,
                file_name=f"bkp_klassifiziert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width='stretch'
            )

        with col2:
            # Nur hochwertige Ergebnisse exportieren
            high_conf_df = df_results[df_results['KI_Konfidenz'] >= confidence_threshold]
            csv_high_conf = high_conf_df.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button(
                label=f"📥 Nur hohe Konfidenz (≥{confidence_threshold:.0%})",
                data=csv_high_conf,
                file_name=f"bkp_high_confidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width='stretch'
            )

    else:
        st.info("Noch keine Klassifizierung durchgeführt. Wechseln Sie zum Tab 'Upload & Klassifizierung'.")

with tab3:
    st.subheader("🔍 KI API Responses (Echtzeit)")

    if get_state(PROC_API_RESPONSES):
        st.info(f"💬 {len(get_state(PROC_API_RESPONSES))} API-Anfragen aufgezeichnet")

        # Anzeige-Optionen
        col1, col2 = st.columns([3, 1])

        with col1:
            show_mode = st.radio(
                "Ansicht",
                ["Neueste zuerst", "Älteste zuerst", "Nur Fehler"],
                horizontal=True
            )

        with col2:
            if st.button("🗑️ Responses löschen", width='stretch'):
                set_state(PROC_API_RESPONSES, [])
                st.rerun()

        st.markdown("---")

        # Responses anzeigen (no copy needed - only reading/iterating)
        responses = get_state(PROC_API_RESPONSES)

        if show_mode == "Neueste zuerst":
            responses = reversed(responses)
        elif show_mode == "Nur Fehler":
            responses = [r for r in responses if r['parsed_result'].get('bkp_code') in ['ERROR', 'PARSE_ERROR', 'UNKNOWN']]

        for idx, response in enumerate(responses):
            with st.expander(
                f"Request #{response['request_num']} | {response['timestamp']} | Element: {response['element'][:50]}...",
                expanded=(idx < 3)  # Erste 3 aufgeklappt
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**📤 Request Info:**")
                    st.text(f"Zeitstempel: {response['timestamp']}")
                    st.text(f"Request #: {response['request_num']}")
                    st.text(f"Element: {response['element']}")

                with col2:
                    st.markdown("**📥 Parsed Result:**")
                    result = response['parsed_result']

                    # Farbe je nach Ergebnis
                    if result.get('bkp_code') == 'ERROR':
                        st.error(f"❌ Error: {result.get('bkp_description', 'Unknown error')}")
                    elif result.get('confidence', 0) < 0.7:
                        st.warning(f"⚠️ BKP: {result.get('bkp_code')} (Konfidenz: {result.get('confidence', 0):.1%})")
                    else:
                        st.success(f"✅ BKP: {result.get('bkp_code')} (Konfidenz: {result.get('confidence', 0):.1%})")

                    st.text(f"Beschreibung: {result.get('bkp_description', 'N/A')}")

                st.markdown("**🔍 Raw API Response:**")
                st.code(response['raw_response'], language="json")

    else:
        st.info("Noch keine API-Responses aufgezeichnet. Starten Sie eine Klassifizierung im Tab 'Upload & Klassifizierung'.")

        st.markdown("""
        ### 💡 Was wird hier angezeigt?

        Dieser Tab zeigt alle API-Anfragen und -Antworten in Echtzeit:
        - **Request Info**: Zeitstempel und Element-Details
        - **Parsed Result**: Interpretiertes Ergebnis mit BKP-Code und Konfidenz
        - **Raw Response**: Unverarbeitete API-Antwort von Claude

        So können Sie die KI-Klassifizierung live nachvollziehen!
        """)

with tab4:
    st.subheader("📝 Processing Log")

    if get_state(PROC_PROCESSING_LOG):
        display_log()

        # Kostenübersicht
        if get_state(PROC_TOTAL_COST) > 0:
            st.markdown("---")
            st.subheader("💰 Kosten")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Geschätzte Kosten", f"${get_state(PROC_TOTAL_COST):.4f}")

            with col2:
                if get_state(DATA_CLASSIFICATION_RESULTS) is not None:
                    num_elements = len(get_state(DATA_CLASSIFICATION_RESULTS))
                    cost_per_element = get_state(PROC_TOTAL_COST) / num_elements if num_elements > 0 else 0
                    st.metric("Kosten pro Element", f"${cost_per_element:.6f}")

            with col3:
                st.metric("Währung", "USD")

        # Log Export
        st.markdown("---")
        if st.button("🗑️ Log löschen", type="secondary"):
            set_state(PROC_PROCESSING_LOG, [])
            st.rerun()

    else:
        st.info("Noch kein Processing Log vorhanden.")


# Footer
render_page_footer()
