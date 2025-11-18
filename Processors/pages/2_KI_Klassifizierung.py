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
    from Helpers.BKP_Classifier import BKPClassifier
except ImportError:
    st.error("BKP_Classifier konnte nicht importiert werden. Stellen Sie sicher, dass Helpers/BKP_Classifier.py existiert.")
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


def estimate_cost(num_elements: int, batch_mode: bool = True) -> dict:
    """Schätzt die Kosten für die Klassifizierung"""
    # Claude Haiku Pricing (Stand Nov 2024)
    # Input: $0.80 / 1M tokens, Output: $4.00 / 1M tokens
    # Geschätzte Tokens pro Element: ~100 input, ~50 output

    if batch_mode:
        # Batch ist effizienter: ~10 Elemente pro Request
        num_requests = max(1, num_elements // 10)
        input_tokens = num_requests * 500  # ~500 tokens pro Batch
        output_tokens = num_requests * 300  # ~300 tokens Output
    else:
        # Einzelabfragen
        input_tokens = num_elements * 100
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


def display_log():
    """Zeigt das Processing Log an"""
    if st.session_state.processing_log:
        log_df = pd.DataFrame(st.session_state.processing_log)

        # Färbe nach Level
        def color_level(row):
            colors = {
                'info': 'background-color: #e8f4f8',
                'success': 'background-color: #d4edda',
                'warning': 'background-color: #fff3cd',
                'error': 'background-color: #f8d7da'
            }
            return [colors.get(row['level'], '')] * len(row)

        styled_df = log_df.style.apply(color_level, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=300)


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
        help="Klassifiziert mehrere Elemente gleichzeitig für bessere Effizienz"
    )

    batch_size = 10
    if use_batch:
        batch_size = st.slider(
            "Batch-Größe",
            min_value=5,
            max_value=20,
            value=10,
            help="Anzahl Elemente pro API-Anfrage"
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
tab1, tab2, tab3 = st.tabs(["📤 Upload & Klassifizierung", "📊 Ergebnisse", "📝 Monitoring"])

with tab1:
    st.subheader("CSV-Datei hochladen")

    uploaded_file = st.file_uploader(
        "Wählen Sie eine CSV-Datei",
        type=['csv'],
        help="CSV-Datei mit Spalten wie 'Typ', 'Kategorie', 'Familie', etc."
    )

    if uploaded_file:
        try:
            # CSV einlesen
            try:
                df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig')
            except:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

            st.success(f"✓ CSV geladen: {len(df)} Zeilen")

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
                cost_estimate = estimate_cost(num_elements, use_batch)

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
                    # Log zurücksetzen
                    st.session_state.processing_log = []
                    st.session_state.total_cost = cost_estimate['total_cost']

                    add_log("Klassifizierung gestartet", "info")
                    add_log(f"Modus: {'Batch' if use_batch else 'Einzeln'}", "info")
                    add_log(f"{num_elements} Elemente zu klassifizieren", "info")

                    # Progress Bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    try:
                        # Classifier initialisieren mit API-Key aus Session State
                        add_log("BKPClassifier initialisieren...", "info")

                        # Setze API-Key temporär für Classifier
                        api_key = get_api_key()
                        original_key = os.getenv('ANTHROPIC_API_KEY')
                        os.environ['ANTHROPIC_API_KEY'] = api_key

                        classifier = BKPClassifier()

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
                                        'type': row[type_column] if type_column else '',
                                        'category': row[category_column] if category_column else None,
                                        'family': row[family_column] if family_column else None,
                                        'info': row[info_column] if info_column else None
                                    }
                                    batch_elements.append(elem)

                                # Batch klassifizieren
                                batch_results = classifier.classify_batch(batch_elements, debug=debug_mode)
                                results.extend(batch_results)

                                # Progress aktualisieren
                                progress = (batch_end / num_elements)
                                progress_bar.progress(progress)

                                add_log(f"Batch {current_batch}/{total_batches} abgeschlossen "
                                       f"({len(batch_results)} Elemente)", "success")

                                # Kurze Pause zwischen Batches
                                time.sleep(0.5)

                        else:
                            # Einzelverarbeitung
                            add_log("Einzelverarbeitung gestartet", "info")

                            for idx, row in df.iterrows():
                                status_text.text(f"Verarbeite Element {idx + 1}/{num_elements}...")

                                result = classifier.classify_element(
                                    element_type=row[type_column] if type_column else '',
                                    category=row[category_column] if category_column else None,
                                    family=row[family_column] if family_column else None,
                                    additional_info=row[info_column] if info_column else None,
                                    debug=debug_mode
                                )
                                results.append(result)

                                # Progress aktualisieren
                                progress = ((idx + 1) / num_elements)
                                progress_bar.progress(progress)

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

                        st.success("✓ Klassifizierung erfolgreich abgeschlossen!")
                        st.balloons()

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
