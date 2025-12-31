'''
Daten-Zusammenführung
Führt klassifizierte deduplizierte Daten mit Original-Daten zusammen.
'''

import streamlit as st
import pandas as pd
import sys
import os

# Füge Parent-Verzeichnis zum Path hinzu für Imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from helpers.sidebar_navigation import render_sidebar, render_page_header, render_divider, render_page_footer
    from helpers.notifications import toast, NotificationType
    from helpers.session_state import (
        init_session_state,
        set_state,
        has_classification_results,
        DATA_CLASSIFICATION_RESULTS
    )
except ImportError as e:
    st.error(f"Module konnten nicht importiert werden: {e}")
    st.stop()

# Seitenkonfiguration
st.set_page_config(
    page_title="Daten Zusammenführen",
    page_icon="🔗",
    layout="wide"
)

# Initialize Session State
init_session_state()

# Render gemeinsame Sidebar
render_sidebar()

# Page Header
render_page_header("🔗 Daten Zusammenführen", "Klassifizierte und Original-Daten verbinden")

st.markdown("""
**Funktion:** Führt die klassifizierten deduplizierten Daten mit Ihren Original-Daten zusammen.

**Workflow:**
1. Klassifizierte deduplizierte Daten hochladen (mit BKP-Codes)
2. Original-Daten mit Mapping hochladen (`_Dedup_ID` Spalte)
3. Automatische Zusammenführung
4. Ergebnis überprüfen und zur Auswertung gehen
""")

render_divider("section")

# ============================================================================
# Upload Section
# ============================================================================

st.subheader("1️⃣ Daten hochladen")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Klassifizierte Daten**")
    classified_file = st.file_uploader(
        "Klassifizierte deduplizierte CSV",
        type=['csv'],
        key="classified",
        help="Die CSV-Datei mit BKP-Codes aus der KI-Klassifizierung"
    )

    if classified_file:
        st.success(f"✅ {classified_file.name}")

with col2:
    st.markdown("**Original-Daten mit Mapping**")
    original_file = st.file_uploader(
        "Original CSV mit _Dedup_ID",
        type=['csv'],
        key="original",
        help="Die CSV-Datei mit allen Original-Elementen und _Dedup_ID Spalte"
    )

    if original_file:
        st.success(f"✅ {original_file.name}")

# ============================================================================
# Zusammenführung durchführen
# ============================================================================

if classified_file and original_file:
    try:
        render_divider("section")
        st.subheader("2️⃣ Zusammenführung durchführen")

        # CSV einlesen mit automatischer Encoding-Erkennung
        encodings = ['utf-8-sig', 'latin1', 'iso-8859-1', 'cp1252']

        # Klassifizierte Daten einlesen
        df_classified = None
        for encoding in encodings:
            try:
                classified_file.seek(0)
                df_classified = pd.read_csv(classified_file, sep=';', encoding=encoding)
                st.success(f"✅ Klassifizierte Daten geladen: {len(df_classified)} Zeilen (Encoding: {encoding})")
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if df_classified is None:
            st.error("❌ Konnte klassifizierte Daten nicht laden")
            st.stop()

        # Original-Daten einlesen
        df_original = None
        for encoding in encodings:
            try:
                original_file.seek(0)
                df_original = pd.read_csv(original_file, sep=';', encoding=encoding)
                st.success(f"✅ Original-Daten geladen: {len(df_original)} Zeilen (Encoding: {encoding})")
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if df_original is None:
            st.error("❌ Konnte Original-Daten nicht laden")
            st.stop()

        # Validierung
        if '_Dedup_ID' not in df_original.columns:
            st.error("❌ Original-Daten haben keine `_Dedup_ID` Spalte! Bitte verwenden Sie die Datei aus 'Daten Vorbereiten'.")
            st.stop()

        required_columns = ['BKP_Code', 'BKP_Beschreibung', 'KI_Konfidenz']
        missing_columns = [col for col in required_columns if col not in df_classified.columns]
        if missing_columns:
            st.error(f"❌ Klassifizierte Daten fehlen folgende Spalten: {', '.join(missing_columns)}")
            st.stop()

        # Füge Index zu klassifizierten Daten hinzu (entspricht Dedup_ID)
        df_classified['_Dedup_ID'] = df_classified.index

        # Join durchführen
        st.info("🔄 Führe Daten zusammen...")

        # Merge über _Dedup_ID
        df_merged = df_original.merge(
            df_classified[['_Dedup_ID', 'BKP_Code', 'BKP_Beschreibung', 'KI_Konfidenz']],
            on='_Dedup_ID',
            how='left'
        )

        # Entferne _Dedup_ID Spalte (nicht mehr benötigt)
        df_merged = df_merged.drop(columns=['_Dedup_ID'])

        st.success(f"✅ Zusammenführung erfolgreich!")

        render_divider("section")

        # ============================================================================
        # Statistiken
        # ============================================================================

        st.subheader("3️⃣ Ergebnis-Statistiken")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Original-Elemente",
                f"{len(df_original):,}".replace(',', "'"),
                help="Anzahl Zeilen in Original-Daten"
            )

        with col2:
            st.metric(
                "Klassifizierte Typen",
                f"{len(df_classified):,}".replace(',', "'"),
                help="Anzahl deduplizierter Elemente mit BKP-Codes"
            )

        with col3:
            erfolg_rate = (df_merged['BKP_Code'].notna().sum() / len(df_merged)) * 100
            st.metric(
                "Erfolgsrate",
                f"{erfolg_rate:.1f}%",
                help="Prozent der Elemente mit BKP-Code"
            )

        with col4:
            avg_confidence = df_merged['KI_Konfidenz'].mean()
            st.metric(
                "Ø Konfidenz",
                f"{avg_confidence:.1%}",
                help="Durchschnittliche KI-Konfidenz"
            )

        # Detaillierte Statistiken
        with st.expander("📊 Detaillierte Statistiken"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**BKP-Code Verteilung:**")
                bkp_counts = df_merged['BKP_Code'].value_counts().head(10)
                st.dataframe(bkp_counts, width="stretch")

            with col2:
                st.markdown("**Konfidenz-Verteilung:**")
                conf_bins = pd.cut(df_merged['KI_Konfidenz'], bins=[0, 0.5, 0.7, 0.9, 1.0])
                conf_dist = conf_bins.value_counts().sort_index()
                st.dataframe(conf_dist, width="stretch")

        render_divider("section")

        # ============================================================================
        # Vorschau
        # ============================================================================

        st.subheader("4️⃣ Datenvorschau")

        st.dataframe(
            df_merged.head(100),
            width="stretch",
            height=400
        )

        if len(df_merged) > 100:
            st.info(f"ℹ️ Zeige die ersten 100 von {len(df_merged)} Zeilen")

        render_divider("section")

        # ============================================================================
        # Download und Weiter
        # ============================================================================

        st.subheader("5️⃣ Ergebnis speichern")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # Download zusammengeführte Daten
            csv_merged = df_merged.to_csv(sep=';', index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Zusammengeführte Daten herunterladen",
                data=csv_merged,
                file_name=f"klassifiziert_komplett_{original_file.name}",
                mime="text/csv",
                help=f"Alle {len(df_merged)} Elemente mit BKP-Codes",
                type="primary",
                width="stretch"
            )
            st.caption(f"{len(csv_merged) / 1024:.1f} KB")

        with col2:
            # In Session State speichern
            if st.button("💾 Für Auswertung speichern", width="stretch"):
                set_state(DATA_CLASSIFICATION_RESULTS, df_merged)
                toast("Daten in Session State gespeichert", NotificationType.SUCCESS)
                st.success("✅ Gespeichert!")

        with col3:
            # Link zur Auswertung
            if has_classification_results():
                st.page_link(
                    "pages/06_eBKP_Auswertung.py",
                    label="📊 Zur Auswertung",
                    icon="📊",
                    width="stretch"
                )
            else:
                st.button("📊 Zur Auswertung", width="stretch", disabled=True, help="Bitte erst speichern")

        st.info("""
        💡 **Nächste Schritte:**
        1. ✅ Daten zusammengeführt
        2. 💾 "Für Auswertung speichern" klicken
        3. 📊 Zur **"eBKP Auswertung"** gehen
        4. 🎉 Hierarchische Visualisierung mit Mengen ansehen
        """)

    except Exception as e:
        st.error(f"❌ Fehler beim Zusammenführen: {e}")
        import traceback
        with st.expander("🐛 Fehlerdetails"):
            st.code(traceback.format_exc())

else:
    st.info("👆 Bitte laden Sie beide CSV-Dateien hoch, um zu beginnen.")

    st.markdown("---")

    st.markdown("""
    ### 📋 Welche Dateien benötige ich?

    **1. Klassifizierte deduplizierte Daten:**
    - Aus der **"🤖 KI-Klassifizierung"** Seite
    - Enthält Spalten: `BKP_Code`, `BKP_Beschreibung`, `KI_Konfidenz`
    - Nur die einzigartigen Elemente

    **2. Original-Daten mit Mapping:**
    - Aus der **"📋 Daten Vorbereiten"** Seite
    - Button **"📥 Original mit Mapping"**
    - Enthält alle Original-Elemente + `_Dedup_ID` Spalte

    **So funktioniert's:**
    - Die `_Dedup_ID` verknüpft jedes Original-Element mit dem entsprechenden klassifizierten Element
    - Nach der Zusammenführung hat jedes Ihrer Original-Elemente einen BKP-Code
    """)

# Footer
render_page_footer()
