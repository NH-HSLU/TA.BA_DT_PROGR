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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from Helpers.eBKP_H_Classifier import eBKPHClassifier
    from Streamlit.helpers.sia_lho_102_config import get_level_config
except ImportError:
    st.error("Module konnten nicht importiert werden. Stellen Sie sicher, dass alle erforderlichen Dateien existieren.")
    st.stop()

# Seitenkonfiguration
st.set_page_config(
    page_title="KI-BKP-Klassifizierung",
    page_icon="🤖",
    layout="wide"
)

# Session State initialisieren
if 'classification_results' not in st.session_state:
    st.session_state.classification_results = None
if 'processing_log' not in st.session_state:
    st.session_state.processing_log = []
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0
if 'api_responses' not in st.session_state:
    st.session_state.api_responses = []
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0


def estimate_cost(num_elements: int, batch_mode: bool = True, batch_size: int = 40) -> dict:
    """Schätzt die Kosten für die Klassifizierung mit eBKP-H"""
    # Claude Haiku Pricing (Stand Nov 2024)
    # Input: $0.80 / 1M tokens, Output: $4.00 / 1M tokens
    # eBKP-H System Prompt: ~3000 tokens (wird gecacht, 90% günstiger nach erstem Call)

    if batch_mode:
        # Batch-Verarbeitung: 30-50 Elemente pro Request
        num_requests = max(1, (num_elements + batch_size - 1) // batch_size)

        # Erster Request: Volle System Prompt Kosten
        first_request_input = 3000 + (batch_size * 50)  # System Prompt + Batch
        first_request_output = batch_size * 30  # ~30 tokens pro Element Output

        # Weitere Requests: Gecachter System Prompt (10% Kosten)
        cached_requests = num_requests - 1
        cached_input = cached_requests * (300 + (batch_size * 50))  # Cached prompt + Batch
        cached_output = cached_requests * (batch_size * 30)

        input_tokens = first_request_input + cached_input
        output_tokens = first_request_output + cached_output
    else:
        # Einzelabfragen (nicht empfohlen)
        input_tokens = 3000 + (num_elements * 100)  # System Prompt + alle Elemente
        output_tokens = num_elements * 50

    input_cost = (input_tokens / 1_000_000) * 0.80
    output_cost = (output_tokens / 1_000_000) * 4.00
    total_cost = input_cost + output_cost

    return {
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'input_cost': input_cost,
        'output_cost': output_cost,
        'total_cost': total_cost,
        'num_requests': num_requests if batch_mode else num_elements
    }


def add_log(message: str, level: str = "info"):
    """Fügt einen Eintrag zum Processing Log hinzu"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.processing_log.append({
        'timestamp': timestamp,
        'level': level,
        'message': message
    })


def add_api_response(request_num: int, element_info: str, response: str, parsed_result: dict):
    """Speichert eine API-Response für Echtzeit-Anzeige"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    st.session_state.api_responses.append({
        'timestamp': timestamp,
        'request_num': request_num,
        'element': element_info,
        'raw_response': response,
        'parsed_result': parsed_result
    })


def display_log():
    """Zeigt das Processing Log an (theme-aware)"""
    if st.session_state.processing_log:
        # Zeige Log-Einträge mit nativen Streamlit-Komponenten für Dark Mode Support
        for log_entry in st.session_state.processing_log:
            timestamp = log_entry['timestamp']
            message = log_entry['message']
            level = log_entry['level']

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
    if 'api_key' in st.session_state and st.session_state.api_key:
        return st.session_state.api_key
    # Fallback auf Umgebungsvariable
    return os.getenv('ANTHROPIC_API_KEY')


# Haupttitel
st.title("🤖 KI-Klassifizierung")
st.markdown("Automatische BKP-Zuordnung mit Claude AI")

# API-Key Check
current_api_key = get_api_key()
if not current_api_key:
    st.error("⚠️ Kein API-Key konfiguriert!")
    st.info("Bitte gehen Sie zu **Einstellungen** und konfigurieren Sie Ihren Anthropic API-Key.")
    st.stop()

st.markdown("---")

# Sidebar für Einstellungen
with st.sidebar:
    st.header("⚙️ Einstellungen")

    # Batch-Modus
    use_batch = st.toggle(
        "Batch-Modus (empfohlen)",
        value=True,
        help="Klassifiziert mehrere Elemente gleichzeitig für bessere Effizienz und Kostenersparnis"
    )

    batch_size = 40
    if use_batch:
        batch_size = st.slider(
            "Batch-Größe",
            min_value=20,
            max_value=50,
            value=40,
            help="Anzahl Elemente pro API-Anfrage (30-50 empfohlen für eBKP-H)"
        )

    # Debug-Modus
    debug_mode = st.toggle(
        "Debug-Modus",
        value=False,
        help="Zeigt detaillierte API-Responses"
    )

    # Confidence Threshold
    confidence_threshold = st.slider(
        "Konfidenz-Schwellenwert",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.05,
        help="Elemente unter diesem Wert werden markiert"
    )

    st.markdown("---")

    # Kostenermittlungs-Status anzeigen
    st.subheader("📐 Kostenermittlung")

    if 'cost_estimation_config' in st.session_state and st.session_state.cost_estimation_config.get('selected'):
        config = st.session_state.cost_estimation_config
        st.success(f"✓ {config['name']}")
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
        st.success("API Key aktiv ✓")
        masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
        st.caption(f"Key: {masked_key}")

        # Zeige Quelle
        if 'api_key' in st.session_state and st.session_state.api_key:
            st.caption("Quelle: Session State")
        else:
            st.caption("Quelle: .env Datei")
    else:
        st.error("Kein API Key")
        st.info("→ Gehen Sie zu Einstellungen")

# Tabs für verschiedene Bereiche
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload & Klassifizierung", "📊 Ergebnisse", "🔍 KI Responses", "📝 Monitoring"])

with tab1:
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
                    st.success(f"✓ CSV geladen: {len(df)} Zeilen (Encoding: {encoding})")
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

            available_columns = [''] + list(df.columns)

            with col1:
                type_column = st.selectbox(
                    "Element-Typ (Pflicht)",
                    available_columns,
                    help="Spalte mit dem Element-Typ (z.B. 'Steckdose', 'Wand')"
                )

                category_column = st.selectbox(
                    "Kategorie (Optional)",
                    available_columns,
                    help="Spalte mit der Revit-Kategorie"
                )

            with col2:
                family_column = st.selectbox(
                    "Familie (Optional)",
                    available_columns,
                    help="Spalte mit dem Family-Namen"
                )

                info_column = st.selectbox(
                    "Zusatzinfo (Optional)",
                    available_columns,
                    help="Weitere Beschreibungsspalte"
                )

            # Datenvorschau
            st.subheader("Datenvorschau")
            st.dataframe(df.head(10), use_container_width=True)

            # Kostenabschätzung
            if type_column:
                num_elements = len(df)
                cost_estimate = estimate_cost(num_elements, use_batch, batch_size)

                st.markdown("---")
                st.subheader("💰 Kostenabschätzung")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Elemente", num_elements)

                with col2:
                    st.metric("API-Anfragen", cost_estimate['num_requests'])

                with col3:
                    st.metric("Geschätzte Tokens",
                             f"{cost_estimate['input_tokens'] + cost_estimate['output_tokens']:,}")

                with col4:
                    st.metric("Geschätzte Kosten",
                             f"${cost_estimate['total_cost']:.4f}")

                st.caption(f"Input: {cost_estimate['input_tokens']:,} tokens (${cost_estimate['input_cost']:.4f}) | "
                          f"Output: {cost_estimate['output_tokens']:,} tokens (${cost_estimate['output_cost']:.4f})")

                # Klassifizierung starten
                st.markdown("---")

                if st.button("🚀 Klassifizierung starten", type="primary", use_container_width=True):
                    # Log und API responses zurücksetzen
                    st.session_state.processing_log = []
                    st.session_state.api_responses = []  # Reset API responses
                    st.session_state.total_cost = cost_estimate['total_cost']

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
                        if 'cost_estimation_config' in st.session_state and st.session_state.cost_estimation_config.get('selected'):
                            max_levels = st.session_state.cost_estimation_config['ebkp_levels']
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

                        results = []

                        if use_batch:
                            # Batch-Verarbeitung
                            add_log(f"Batch-Verarbeitung mit Größe {batch_size}", "info")

                            total_batches = (num_elements + batch_size - 1) // batch_size

                            for batch_idx in range(0, num_elements, batch_size):
                                batch_end = min(batch_idx + batch_size, num_elements)
                                batch_df = df.iloc[batch_idx:batch_end]

                                current_batch = (batch_idx // batch_size) + 1
                                status_text.text(f"Verarbeite Batch {current_batch}/{total_batches}...")

                                # Elemente für Batch vorbereiten
                                batch_elements = []
                                for _, row in batch_df.iterrows():
                                    elem = {
                                        'kategorie': row[category_column] if category_column else '',
                                        'typ': row[type_column] if type_column else '',
                                        'familie': row[family_column] if family_column else '',
                                        'zusatzinfo': row[info_column] if info_column else ''
                                    }
                                    batch_elements.append(elem)

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

                                # Progress aktualisieren
                                progress = (batch_end / num_elements)
                                progress_bar.progress(progress)

                                # Live-Update: Zeige neueste Responses
                                if st.session_state.api_responses:
                                    latest_responses = st.session_state.api_responses[-5:]  # Zeige letzte 5
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
                                    latest_responses = st.session_state.api_responses[-5:]
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

                        # Ergebnisse zum DataFrame hinzufügen
                        df['BKP_Code'] = [r['bkp_code'] for r in results]
                        df['BKP_Beschreibung'] = [r['bkp_description'] for r in results]
                        df['KI_Konfidenz'] = [r['confidence'] for r in results]

                        # In Session State speichern
                        st.session_state.classification_results = df

                        progress_bar.progress(1.0)
                        status_text.text("Klassifizierung abgeschlossen!")

                        add_log(f"✓ Klassifizierung erfolgreich abgeschlossen", "success")
                        add_log(f"Durchschnittliche Konfidenz: {df['KI_Konfidenz'].mean():.1%}", "success")
                        add_log(f"📊 {len(st.session_state.api_responses)} API-Responses aufgezeichnet", "success")
                        add_log(f"📝 Detailliertes Log gespeichert: {log_filename}", "success")

                        # Live-Container Final Update
                        live_response_container.success(
                            f"✅ Klassifizierung abgeschlossen! {len(st.session_state.api_responses)} API-Responses aufgezeichnet.\n\n"
                            f"➡️ Wechseln Sie zum Tab **'KI Responses'** für Details."
                        )

                        # Success Message mit nächsten Schritten
                        st.success("✓ Klassifizierung erfolgreich abgeschlossen!")

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
                            if st.button("📊 Zu den Ergebnissen", type="primary", use_container_width=True):
                                st.session_state.active_tab = 1  # Tab "Ergebnisse"
                                st.rerun()

                        with col2:
                            # Verwende Link statt HTML-Button für bessere Dark Mode Kompatibilität
                            st.page_link("pages/1_eBKP_Auswertung.py", label="🔍 Zur eBKP-H Auswertung", icon="📊")

                    except Exception as e:
                        add_log(f"Fehler: {str(e)}", "error")
                        st.error(f"Fehler bei der Klassifizierung: {str(e)}")

            else:
                st.warning("⚠️ Bitte wählen Sie mindestens die 'Element-Typ' Spalte aus")

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

with tab2:
    st.subheader("📊 Klassifizierungs-Ergebnisse")

    if st.session_state.classification_results is not None:
        df_results = st.session_state.classification_results

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
            st.plotly_chart(fig_conf, use_container_width=True)

        with col2:
            st.subheader("Top 10 BKP-Codes")
            bkp_counts = df_results['BKP_Code'].value_counts().head(10)
            fig_bkp = px.bar(
                x=bkp_counts.index,
                y=bkp_counts.values,
                title='Häufigste BKP-Codes',
                labels={'x': 'BKP Code', 'y': 'Anzahl'}
            )
            st.plotly_chart(fig_bkp, use_container_width=True)

        st.markdown("---")

        # Qualitätskontrolle: Niedrige Konfidenz
        st.subheader("⚠️ Qualitätskontrolle")
        low_conf_df = df_results[df_results['KI_Konfidenz'] < confidence_threshold]

        if not low_conf_df.empty:
            st.warning(f"{len(low_conf_df)} Elemente haben eine Konfidenz unter {confidence_threshold:.0%}")
            st.dataframe(
                low_conf_df.style.background_gradient(subset=['KI_Konfidenz'], cmap='RdYlGn'),
                use_container_width=True
            )
        else:
            st.success(f"✓ Alle Elemente haben eine Konfidenz über {confidence_threshold:.0%}")

        st.markdown("---")

        # Vollständige Ergebnisse
        st.subheader("📑 Vollständige Ergebnisse")
        st.dataframe(
            df_results.style.background_gradient(subset=['KI_Konfidenz'], cmap='RdYlGn'),
            use_container_width=True
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
                use_container_width=True
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
                use_container_width=True
            )

    else:
        st.info("Noch keine Klassifizierung durchgeführt. Wechseln Sie zum Tab 'Upload & Klassifizierung'.")

with tab3:
    st.subheader("🔍 KI API Responses (Echtzeit)")

    if st.session_state.api_responses:
        st.info(f"💬 {len(st.session_state.api_responses)} API-Anfragen aufgezeichnet")

        # Anzeige-Optionen
        col1, col2 = st.columns([3, 1])

        with col1:
            show_mode = st.radio(
                "Ansicht",
                ["Neueste zuerst", "Älteste zuerst", "Nur Fehler"],
                horizontal=True
            )

        with col2:
            if st.button("🗑️ Responses löschen", use_container_width=True):
                st.session_state.api_responses = []
                st.rerun()

        st.markdown("---")

        # Responses anzeigen
        responses = st.session_state.api_responses.copy()

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
                        st.success(f"✓ BKP: {result.get('bkp_code')} (Konfidenz: {result.get('confidence', 0):.1%})")

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

    if st.session_state.processing_log:
        display_log()

        # Kostenübersicht
        if st.session_state.total_cost > 0:
            st.markdown("---")
            st.subheader("💰 Kosten")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Geschätzte Kosten", f"${st.session_state.total_cost:.4f}")

            with col2:
                if st.session_state.classification_results is not None:
                    num_elements = len(st.session_state.classification_results)
                    cost_per_element = st.session_state.total_cost / num_elements if num_elements > 0 else 0
                    st.metric("Kosten pro Element", f"${cost_per_element:.6f}")

            with col3:
                st.metric("Währung", "USD")

        # Log Export
        st.markdown("---")
        if st.button("🗑️ Log löschen", type="secondary"):
            st.session_state.processing_log = []
            st.rerun()

    else:
        st.info("Noch kein Processing Log vorhanden.")
