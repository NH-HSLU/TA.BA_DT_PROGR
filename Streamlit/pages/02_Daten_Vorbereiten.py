'''
Daten-Vorbereitung und Deduplizierung
Bereitet CSV-Daten für die KI-Klassifizierung vor durch Deduplizierung identischer Element-Kombinationen.
'''

import streamlit as st
import pandas as pd
import sys
import os
from typing import Tuple, List, Dict

# Füge Parent-Verzeichnis zum Path hinzu für Imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from helpers.sidebar_navigation import render_sidebar, render_page_header, render_divider, render_page_footer
    from helpers.notifications import toast, NotificationType
    from helpers.session_state import (
        init_session_state,
        get_state,
        set_state,
        DATA_PREPARED,
        DATA_DEDUP_MAPPING,
        DATA_UNIQUE_ELEMENTS,
        DATA_ORIGINAL_UPLOADED
    )
except ImportError as e:
    st.error(f"Module konnten nicht importiert werden: {e}")
    st.stop()

# Seitenkonfiguration
st.set_page_config(
    page_title="Daten Vorbereiten",
    page_icon="📋",
    layout="wide"
)

# Initialize Session State
init_session_state()

# Render gemeinsame Sidebar
render_sidebar()


# ============================================================================
# Deduplizierungs-Helper-Funktionen
# ============================================================================

def deduplicate_elements(df: pd.DataFrame, dedup_columns: list) -> Tuple[pd.DataFrame, Dict, List[Dict]]:
    """
    Dedupliziert Elemente basierend auf Kombination von Spalten.

    Args:
        df: Original DataFrame mit allen Elementen
        dedup_columns: Liste der Spalten für Deduplizierung

    Returns:
        Tuple von:
        - unique_df: DataFrame mit nur einzigartigen Kombinationen
        - index_mapping: Dict {unique_index: [original_row_indices]}
        - unique_elements: List[Dict] für Klassifizierer
    """
    # Erstelle temporäre Dedup-ID Spalte
    df_copy = df.copy()
    df_copy['_dedup_key'] = df_copy[dedup_columns].fillna('').astype(str).agg('|'.join, axis=1)

    # Gruppiere nach Dedup-Key
    grouped = df_copy.groupby('_dedup_key')

    # Index-Mapping erstellen
    index_mapping = {}
    unique_elements = []
    unique_rows = []

    for unique_idx, (key, group) in enumerate(grouped):
        # Speichere Original-Indices
        index_mapping[unique_idx] = group.index.tolist()

        # Nehme erste Zeile als Repräsentant
        first_row = group.iloc[0]
        unique_rows.append(first_row)

        # Element-Dict für Klassifizierer erstellen
        unique_elements.append({
            'kategorie': first_row.get('Kategorie', ''),
            'typ': first_row.get('Typ', ''),
            'familie': first_row.get('Familie', ''),
            'zusatzinfo': first_row.get('Zusatzinfo', '')
        })

    unique_df = pd.DataFrame(unique_rows)

    # Logging
    dedup_ratio = len(df) / len(unique_df) if len(unique_df) > 0 else 0

    return unique_df, index_mapping, unique_elements


# ============================================================================
# Page Header
# ============================================================================

render_page_header("📋 Daten Vorbereiten", "Deduplizierung für Kostenoptimierung")

st.markdown("""
**Funktion:** Findet einzigartige Element-Kombinationen in Ihren Daten, um API-Kosten zu reduzieren.

**Workflow:**
1. CSV-Datei hochladen
2. Deduplizierungs-Spalten auswählen
3. Deduplizierung durchführen
4. Statistiken überprüfen
5. Weiter zur KI-Klassifizierung
""")

render_divider("section")


# ============================================================================
# Prepared Data Detection
# ============================================================================

# Check if prepared data already exists in session state
has_prepared_data = False
"""(
    get_state(DATA_PREPARED) is not None and
    get_state(DATA_ORIGINAL_UPLOADED) is not None
)"""

if has_prepared_data and not get_state('UI_RELOAD_PREPARED_DATA', False):
    # Show option to use existing prepared data
    st.success("✅ **Vorbereitete Daten gefunden!**")

    prepared_df = get_state(DATA_PREPARED)
    original_df = get_state(DATA_ORIGINAL_UPLOADED)

    st.markdown("""
    Sie haben bereits vorbereitete Daten in Ihrer aktuellen Sitzung.
    Wählen Sie eine der folgenden Optionen:
    """)

    # Show statistics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Eindeutige Elemente", f"{len(prepared_df):,}".replace(',', "'"))
    with col2:
        st.metric("Original-Zeilen", f"{len(original_df):,}".replace(',', "'"))

    # Button to use prepared data
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("✅ Vorbereitete Daten verwenden", type="primary", use_container_width=True):
            set_state('UI_RELOAD_PREPARED_DATA', True)
            st.rerun()
    with col_b:
        if st.button("🔄 Neue CSV hochladen", use_container_width=True):
            # Clear prepared data and reload page
            set_state(DATA_PREPARED, None)
            set_state(DATA_ORIGINAL_UPLOADED, None)
            set_state(DATA_DEDUP_MAPPING, None)
            set_state(DATA_UNIQUE_ELEMENTS, None)
            set_state('UI_RELOAD_PREPARED_DATA', None)
            toast("Vorbereitete Daten gelöscht", NotificationType.INFO)
            st.rerun()

    # Stop here - don't show file uploader
    st.stop()


# ============================================================================
# CSV Upload
# ============================================================================

st.subheader("1️⃣ CSV-Datei hochladen")

# Check if we're using prepared data or fresh upload
using_prepared_data = get_state('UI_RELOAD_PREPARED_DATA', False)

if not using_prepared_data:
    # Show file uploader for fresh CSV upload
    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Wählen Sie eine CSV-Datei",
            type=['csv'],
            help="CSV-Export aus pyRevit mit Spalten: Kategorie, Familie, Typ, etc."
        )

    with col2:
        if uploaded_file:
            st.success("✅ Datei geladen")
            file_size = uploaded_file.size / 1024  # KB
            st.metric("Dateigröße", f"{file_size:.1f} KB")
else:
    # Using prepared data - simulate upload workflow
    uploaded_file = "prepared_data"  # Dummy value to trigger workflow
    st.info("📋 **Vorbereitete Daten werden geladen...**")

if uploaded_file is not None:
    try:
        # Check if we're loading from prepared data or fresh upload
        if using_prepared_data:
            # Load from session state
            df = get_state(DATA_ORIGINAL_UPLOADED)
            if df is None:
                st.error("❌ Fehler: Keine vorbereiteten Daten gefunden.")
                st.stop()
            st.success(f"✅ Vorbereitete Daten geladen: **{len(df)}** Zeilen, **{len(df.columns)}** Spalten")

            # Clear the reload flag so subsequent reruns behave normally
            set_state('UI_RELOAD_PREPARED_DATA', None)

            # Set a default filename for downloads
            file_name_base = "vorbereitete_daten.csv"
        else:
            # Fresh CSV upload - read from file
            df = None
            encodings = ['utf-8-sig', 'latin1', 'iso-8859-1', 'cp1252']

            for encoding in encodings:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=';', encoding=encoding)
                    st.success(f"✅ CSV erfolgreich geladen: **{len(df)}** Zeilen, **{len(df.columns)}** Spalten (Encoding: {encoding})")
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue

            if df is None:
                st.error("❌ Fehler: Konnte CSV-Datei mit keinem bekannten Encoding laden. "
                        "Bitte speichern Sie die Datei als UTF-8.")
                st.stop()

            # Speichere Original-Daten (only for fresh uploads)
            set_state(DATA_ORIGINAL_UPLOADED, df.copy())

            # Set filename for downloads
            file_name_base = uploaded_file.name

        render_divider("section")

        # ============================================================================
        # Spalten-Auswahl für Deduplizierung
        # ============================================================================

        st.subheader("2️⃣ Deduplizierungs-Spalten auswählen")

        st.markdown("""
        Wählen Sie die Spalten, die eine **einzigartige Element-Kombination** definieren.
        Elemente mit identischen Werten in diesen Spalten werden dedupliziert.
        """)

        # Standard-Spalten für Deduplizierung
        available_columns = df.columns.tolist()
        default_columns = ['Kategorie', 'Familie', 'Typ']
        optional_columns = ['Schichtaufbau', 'Zusatzinfo', 'Dicke_mm']

        # Filtere nur vorhandene Spalten
        default_dedup = [col for col in default_columns if col in available_columns]
        optional_dedup = [col for col in optional_columns if col in available_columns]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Basis-Spalten (empfohlen):**")
            selected_base = st.multiselect(
                "Basis-Spalten auswählen",
                options=default_dedup,
                default=default_dedup,
                help="Diese Spalten definieren die Basis-Identität eines Elements"
            )

        with col2:
            st.markdown("**Zusätzliche Spalten (optional):**")
            selected_optional = st.multiselect(
                "Zusätzliche Spalten auswählen",
                options=optional_dedup,
                default=[col for col in ['Schichtaufbau'] if col in available_columns],
                help="Zusätzliche Unterscheidungsmerkmale für feinere Deduplizierung"
            )

        dedup_columns = selected_base + selected_optional

        if not dedup_columns:
            st.warning("⚠️ Bitte wählen Sie mindestens eine Spalte für die Deduplizierung aus.")
        else:
            st.info(f"🔍 **Deduplizierung nach:** {', '.join(dedup_columns)}")

        render_divider("section")

        # ============================================================================
        # Deduplizierung durchführen
        # ============================================================================

        st.subheader("3️⃣ Deduplizierung durchführen")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("🚀 Deduplizierung starten", type="primary", disabled=not dedup_columns, width="stretch"):
                with st.spinner("Dedupliziere Daten..."):
                    # Deduplizierung durchführen
                    unique_df, index_mapping, unique_elements = deduplicate_elements(
                        df.copy(),
                        dedup_columns=dedup_columns
                    )

                    # In Session State speichern
                    set_state(DATA_PREPARED, unique_df)
                    set_state(DATA_DEDUP_MAPPING, index_mapping)
                    set_state(DATA_UNIQUE_ELEMENTS, unique_elements)

                    toast("Deduplizierung erfolgreich!", NotificationType.SUCCESS)
                    st.rerun()

        with col2:
            if get_state(DATA_PREPARED) is not None:
                if st.button("🗑️ Zurücksetzen", width="stretch"):
                    set_state(DATA_PREPARED, None)
                    set_state(DATA_DEDUP_MAPPING, None)
                    set_state(DATA_UNIQUE_ELEMENTS, None)
                    toast("Daten zurückgesetzt", NotificationType.INFO)
                    st.rerun()

        # ============================================================================
        # Statistiken anzeigen
        # ============================================================================

        if get_state(DATA_PREPARED) is not None:
            render_divider("section")

            st.subheader("4️⃣ Deduplizierungs-Statistiken")

            unique_df = get_state(DATA_PREPARED)
            dedup_ratio = len(df) / len(unique_df) if len(unique_df) > 0 else 0
            cost_saving_pct = (1 - 1/dedup_ratio) * 100 if dedup_ratio > 1 else 0

            # Metriken in 4 Spalten
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Original Elemente",
                    f"{len(df):,}".replace(',', "'"),
                    help="Anzahl Zeilen in Original-CSV"
                )

            with col2:
                st.metric(
                    "Einzigartige Elemente",
                    f"{len(unique_df):,}".replace(',', "'"),
                    delta=f"-{len(df) - len(unique_df):,}".replace(',', "'"),
                    delta_color="normal",
                    help="Anzahl einzigartiger Kombinationen"
                )

            with col3:
                st.metric(
                    "Reduktionsfaktor",
                    f"{dedup_ratio:.1f}x",
                    help="Verhältnis: Original / Einzigartig"
                )

            with col4:
                st.metric(
                    "Kostenersparnis",
                    f"{cost_saving_pct:.1f}%",
                    help="Geschätzte API-Kostenersparnis"
                )

            # Erfolgs-Nachricht
            if dedup_ratio > 1:
                st.success(f"""
                ✅ **Deduplizierung erfolgreich!**

                - **{len(df):,}** Original-Elemente → **{len(unique_df):,}** einzigartige Elemente
                - **{dedup_ratio:.1f}x** weniger API-Calls
                - **{cost_saving_pct:.1f}%** Kostenersparnis

                Die Daten sind bereit für die KI-Klassifizierung.
                """.replace(',', "'"))
            else:
                st.info("ℹ️ Keine Duplikate gefunden. Alle Elemente sind einzigartig.")

            render_divider("section")

            # ============================================================================
            # Download deduplizierte Daten
            # ============================================================================

            st.subheader("5️⃣ Deduplizierte Daten herunterladen")

            st.markdown("""
            **Laden Sie die deduplizierten Daten herunter** und nutzen Sie sie direkt in der KI-Klassifizierung.
            Die CSV enthält nur die einzigartigen Element-Kombinationen.
            """)

            col1, col2, col3 = st.columns(3)

            with col1:
                # Download deduplizierte Daten
                csv_unique = unique_df.to_csv(sep=';', index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Deduplizierte Daten",
                    data=csv_unique,
                    file_name=f"dedupliziert_{file_name_base}",
                    mime="text/csv",
                    help=f"CSV mit {len(unique_df)} einzigartigen Elementen für KI-Klassifizierung",
                    type="primary",
                    width="stretch"
                )
                st.caption(f"{len(csv_unique) / 1024:.1f} KB")

            with col2:
                # Erstelle Original-Daten mit Mapping-ID
                df_with_mapping = df.copy()

                # Füge Mapping-ID hinzu (welches unique Element gehört zu welcher Original-Zeile)
                mapping_ids = [None] * len(df)
                for unique_idx, original_indices in get_state(DATA_DEDUP_MAPPING).items():
                    for orig_idx in original_indices:
                        mapping_ids[orig_idx] = unique_idx

                df_with_mapping['_Dedup_ID'] = mapping_ids
                csv_original = df_with_mapping.to_csv(sep=';', index=False, encoding='utf-8-sig')

                st.download_button(
                    label="📥 Original mit Mapping",
                    data=csv_original,
                    file_name=f"original_mapping_{file_name_base}",
                    mime="text/csv",
                    help=f"Original-Daten ({len(df)} Zeilen) mit Dedup-ID zum späteren Zusammenführen",
                    width="stretch"
                )
                st.caption(f"{len(csv_original) / 1024:.1f} KB")

            with col3:
                # Erstelle Mapping-Tabelle als separate CSV
                mapping_data = []
                for unique_idx, original_indices in get_state(DATA_DEDUP_MAPPING).items():
                    mapping_data.append({
                        'Dedup_ID': unique_idx,
                        'Anzahl_Original': len(original_indices),
                        'Original_Indices': ','.join(map(str, original_indices))
                    })

                mapping_df_export = pd.DataFrame(mapping_data)
                csv_mapping = mapping_df_export.to_csv(sep=';', index=False, encoding='utf-8-sig')

                st.download_button(
                    label="📥 Mapping-Tabelle",
                    data=csv_mapping,
                    file_name=f"mapping_{file_name_base}",
                    mime="text/csv",
                    help="Mapping zwischen Dedup-IDs und Original-Zeilen",
                    width="stretch"
                )
                st.caption(f"{len(csv_mapping) / 1024:.1f} KB")

            st.info("""
            💡 **Download-Erklärung:**

            **1️⃣ Deduplizierte Daten** (Primary Button)
            - Enthält nur die **{0:,}** einzigartigen Element-Kombinationen
            - Nutzen Sie diese CSV für die **KI-Klassifizierung**
            - Spart {1:.1f}% API-Kosten

            **2️⃣ Original mit Mapping**
            - Alle **{2:,}** Original-Elemente + `_Dedup_ID` Spalte
            - Nutzen Sie diese später zum Zusammenführen der Klassifizierungen
            - Behält alle Original-Daten

            **3️⃣ Mapping-Tabelle**
            - Zeigt welche Dedup-ID zu wie vielen Original-Elementen gehört
            - Nützlich für Debugging und Statistiken

            ---

            **Workflow:**
            1. Laden Sie **"Deduplizierte Daten"** herunter
            2. Gehen Sie zur **"🤖 KI-Klassifizierung"**
            3. Klassifizieren Sie die deduplizierte CSV
            4. Nach der Klassifizierung können Sie die Ergebnisse mit **"Original mit Mapping"** zusammenführen
            """.format(len(unique_df), cost_saving_pct, len(df)))

            render_divider("section")

            # ============================================================================
            # Vorschau der deduplizierten Daten
            # ============================================================================

            st.subheader("6️⃣ Vorschau deduplizierte Daten")

            tab1, tab2, tab3 = st.tabs(["📊 Einzigartige Elemente", "📋 Original-Daten", "🔗 Mapping-Statistik"])

            with tab1:
                st.markdown(f"**{len(unique_df)} einzigartige Element-Kombinationen:**")
                st.dataframe(
                    unique_df.head(100),
                    width="stretch",
                    height=400
                )

                if len(unique_df) > 100:
                    st.info(f"ℹ️ Zeige die ersten 100 von {len(unique_df)} Zeilen")

            with tab2:
                st.markdown(f"**{len(df)} Original-Elemente:**")
                st.dataframe(
                    df.head(100),
                    width="stretch",
                    height=400
                )

                if len(df) > 100:
                    st.info(f"ℹ️ Zeige die ersten 100 von {len(df)} Zeilen")

            with tab3:
                st.markdown("**Mapping-Statistik:** Wie viele Original-Elemente gehören zu jeder einzigartigen Kombination?")

                # Berechne Verteilung
                mapping_counts = [len(indices) for indices in get_state(DATA_DEDUP_MAPPING).values()]
                mapping_df = pd.DataFrame({
                    'Anzahl Original-Elemente': mapping_counts
                })

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Durchschnitt", f"{sum(mapping_counts) / len(mapping_counts):.1f}")
                    st.metric("Maximum", f"{max(mapping_counts)}")

                with col2:
                    st.metric("Minimum", f"{min(mapping_counts)}")
                    st.metric("Median", f"{sorted(mapping_counts)[len(mapping_counts)//2]}")

                # Histogramm
                import plotly.express as px
                fig = px.histogram(
                    mapping_df,
                    x='Anzahl Original-Elemente',
                    nbins=50,
                    title="Verteilung: Wie oft kommt jede einzigartige Kombination vor?"
                )
                st.plotly_chart(fig, width="stretch")

            render_divider("section")

            # ============================================================================
            # Weiter zur Klassifizierung
            # ============================================================================

            st.subheader("7️⃣ Weiter zur KI-Klassifizierung")

            st.markdown("""
            **Workflow:**
            1. ✅ Deduplizierte Daten heruntergeladen (Schritt 5)
            2. ➡️ Zur **"🤖 KI-Klassifizierung"** Seite gehen
            3. 📤 Deduplizierte CSV dort hochladen
            4. 🤖 Klassifizierung durchführen
            5. 📊 Ergebnisse mit Original-Daten zusammenführen
            """)

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.page_link(
                    "pages/02_KI_Klassifizierung.py",
                    label="➡️ Zur KI-Klassifizierung",
                    icon="🤖",
                    width="stretch"
                )

    except Exception as e:
        st.error(f"❌ Fehler beim Laden der CSV-Datei: {e}")
        st.info("💡 Stellen Sie sicher, dass die CSV-Datei das richtige Format hat (Semikolon-separiert, UTF-8-Kodierung)")

else:
    st.info("👆 Laden Sie eine CSV-Datei hoch, um zu beginnen.")

# Footer
render_page_footer()
