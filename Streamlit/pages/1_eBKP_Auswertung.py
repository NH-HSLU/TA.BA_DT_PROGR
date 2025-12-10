'''
Streamlit App zur Visualisierung und Interaktion mit dem Datenverarbeitungsprozess.
Zeigt ausgewertete Daten nach eBKP-H gegliedert mit aufklappbaren Bereichen.
'''

import streamlit as st
import pandas as pd
import plotly.express as px

# Seitenkonfiguration
st.set_page_config(
    page_title="eBKP-H Auswertung",
    layout="wide",
    initial_sidebar_state="expanded"
)

# eBKP-H Hauptgruppen Definition
EBKP_HAUPTGRUPPEN = {
    'C': 'Bauwerk - Rohbau',
    'D': 'Bauwerk - Technik',
    'E': 'Bauwerk - Ausbau',
    'F': 'Umgebung',
    'G': 'Baunebenkosten'
}


def extract_bkp_hauptgruppe(bkp_code: str) -> str:
    """Extrahiert die Hauptgruppe aus dem BKP-Code (z.B. 'C' aus 'C1.1')"""
    if pd.isna(bkp_code) or not bkp_code:
        return 'Unbekannt'
    bkp_str = str(bkp_code).strip()
    if bkp_str and bkp_str[0].upper() in EBKP_HAUPTGRUPPEN:
        return bkp_str[0].upper()
    return 'Unbekannt'


def extract_bkp_untergruppe(bkp_code: str) -> str:
    """Extrahiert die Untergruppe aus dem BKP-Code (z.B. 'C1' aus 'C1.1')"""
    if pd.isna(bkp_code) or not bkp_code:
        return 'Unbekannt'
    bkp_str = str(bkp_code).strip()
    # Nimm alles bis zum ersten Punkt oder bis zu zwei Zeichen
    if '.' in bkp_str:
        return bkp_str.split('.')[0]
    elif len(bkp_str) >= 2:
        return bkp_str[:2]
    return bkp_str


def format_currency(value: float) -> str:
    """Formatiert einen Wert als Währung (CHF)"""
    return f"CHF {value:,.2f}".replace(',', "'")


def calculate_grouped_totals(df: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Berechnet Zwischentotale gruppiert nach einer Spalte"""
    if 'Kosten' in df.columns:
        grouped = df.groupby(group_column).agg({
            'Kosten': 'sum',
            group_column: 'count'
        }).rename(columns={group_column: 'Anzahl'})
    elif 'Fläche (m²)' in df.columns or 'Fläche' in df.columns:
        flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in df.columns else 'Fläche'
        grouped = df.groupby(group_column).agg({
            flaeche_col: 'sum',
            group_column: 'count'
        }).rename(columns={group_column: 'Anzahl', flaeche_col: 'Fläche Total (m²)'})
    else:
        grouped = df.groupby(group_column).size().reset_index(name='Anzahl')

    return grouped.reset_index()


def display_bkp_hierarchy(df: pd.DataFrame, hauptgruppe: str):
    """Zeigt die BKP-Hierarchie für eine Hauptgruppe an"""
    hauptgruppe_df = df[df['BKP_Hauptgruppe'] == hauptgruppe].copy()

    if hauptgruppe_df.empty:
        st.info(f"Keine Daten für Hauptgruppe {hauptgruppe}")
        return

    # Berechne Totale
    if 'Kosten' in hauptgruppe_df.columns:
        total = hauptgruppe_df['Kosten'].sum()
        st.metric("Zwischentotal", format_currency(total),
                 delta=f"{len(hauptgruppe_df)} Elemente")
    elif 'Fläche (m²)' in hauptgruppe_df.columns or 'Fläche' in hauptgruppe_df.columns:
        flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in hauptgruppe_df.columns else 'Fläche'
        total = hauptgruppe_df[flaeche_col].sum()
        st.metric("Zwischentotal Fläche", f"{total:,.2f} m²".replace(',', "'"),
                 delta=f"{len(hauptgruppe_df)} Elemente")
    else:
        st.metric("Anzahl Elemente", len(hauptgruppe_df))

    # Gruppiere nach Untergruppe
    untergruppen = hauptgruppe_df.groupby('BKP_Untergruppe')

    for untergruppe, ug_df in untergruppen:
        with st.expander(f"**{untergruppe}** - {len(ug_df)} Elemente", expanded=False):
            # Zeige BKP-Beschreibungen
            if 'BKP_Beschreibung' in ug_df.columns:
                beschreibungen = ug_df.groupby(['BKP_Code', 'BKP_Beschreibung'])

                for (code, beschr), beschr_df in beschreibungen:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{code}**: {beschr}")
                    with col2:
                        if 'Kosten' in beschr_df.columns:
                            kosten = beschr_df['Kosten'].sum()
                            st.write(f"*{format_currency(kosten)}*")
                        elif 'Fläche (m²)' in beschr_df.columns or 'Fläche' in beschr_df.columns:
                            flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in beschr_df.columns else 'Fläche'
                            flaeche = beschr_df[flaeche_col].sum()
                            st.write(f"*{flaeche:,.2f} m²*")
                        else:
                            st.write(f"*{len(beschr_df)} Stk.*")
            else:
                # Fallback: Zeige einfach die Codes
                codes = ug_df['BKP_Code'].value_counts()
                for code, count in codes.items():
                    st.write(f"**{code}**: {count} Elemente")

            # Detailtabelle
            with st.expander("📋 Details anzeigen", expanded=False):
                st.dataframe(ug_df, use_container_width=True, height=300)


# Haupttitel
st.title("📊 eBKP-H Kostenauswertung")

# Prüfe ob Daten aus KI-Klassifizierung vorhanden sind
auto_load_data = False
if 'classification_results' in st.session_state and st.session_state.classification_results is not None:
    auto_load_data = True
    st.success("✅ Daten aus KI-Klassifizierung automatisch geladen!")
    st.info("💡 Die Daten wurden direkt aus der KI-Klassifizierung übernommen. Sie können auch eine andere Datei hochladen.")

st.markdown("---")

# Sidebar für Upload und Filter
with st.sidebar:
    st.header("⚙️ Einstellungen")

    # Datenquelle wählen
    if auto_load_data:
        data_source = st.radio(
            "Datenquelle",
            ["🤖 Aus KI-Klassifizierung", "📁 Neue Datei hochladen"],
            help="Verwenden Sie Daten aus der KI oder laden Sie eine neue Datei hoch"
        )

        use_auto_data = (data_source == "🤖 Aus KI-Klassifizierung")
    else:
        use_auto_data = False
        st.info("💡 Keine automatischen Daten verfügbar")

    # File Upload (nur wenn nicht auto-load oder manuell gewählt)
    uploaded_file = None
    if not use_auto_data:
        uploaded_file = st.file_uploader(
            "CSV-Datei hochladen",
            type=['csv'],
            help="Laden Sie eine CSV-Datei mit BKP-zugeordneten Daten hoch"
        )

    st.markdown("---")
    st.markdown("""
    ### 💡 Hinweise
    - Die CSV-Datei sollte eine Spalte `BKP_Code` enthalten
    - Optional: `Kosten`, `Fläche (m²)`, `BKP_Beschreibung`
    - Daten werden automatisch nach eBKP-H gruppiert
    """)

# Hauptbereich - Daten laden
df = None

if use_auto_data:
    # Lade Daten aus Session State
    df = st.session_state.classification_results.copy()
    st.info(f"📊 {len(df)} Elemente aus KI-Klassifizierung geladen")

elif uploaded_file is not None:
    try:
        # CSV einlesen (versuche verschiedene Trennzeichen)
        try:
            df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig')
        except:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

        # Prüfe ob BKP_Code Spalte existiert
        if 'BKP_Code' not in df.columns:
            st.error("❌ Die CSV-Datei muss eine Spalte 'BKP_Code' enthalten!")
            st.stop()

        # Entferne Zeilen ohne BKP_Code
        df_original_len = len(df)
        df = df[df['BKP_Code'].notna()].copy()

        if len(df) == 0:
            st.error("❌ Keine gültigen BKP-Codes in der Datei gefunden!")
            st.stop()

        if df_original_len > len(df):
            st.warning(f"⚠️ {df_original_len - len(df)} Zeilen ohne BKP-Code wurden entfernt")

    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Datei: {str(e)}")
        st.exception(e)
        df = None

# Verarbeite Daten wenn vorhanden
if df is not None:
    try:
        # Extrahiere BKP-Hierarchie
        df['BKP_Hauptgruppe'] = df['BKP_Code'].apply(extract_bkp_hauptgruppe)
        df['BKP_Untergruppe'] = df['BKP_Code'].apply(extract_bkp_untergruppe)

        # Übersichts-Metriken
        st.subheader("📈 Übersicht")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Gesamt Elemente", len(df))

        with col2:
            unique_codes = df['BKP_Code'].nunique()
            st.metric("Verschiedene BKP-Codes", unique_codes)

        with col3:
            hauptgruppen_count = df['BKP_Hauptgruppe'].nunique()
            st.metric("Hauptgruppen", hauptgruppen_count)

        with col4:
            if 'Kosten' in df.columns:
                gesamtkosten = df['Kosten'].sum()
                st.metric("Gesamtkosten", format_currency(gesamtkosten))
            elif 'Fläche (m²)' in df.columns or 'Fläche' in df.columns:
                flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in df.columns else 'Fläche'
                gesamtflaeche = df[flaeche_col].sum()
                st.metric("Gesamtfläche", f"{gesamtflaeche:,.2f} m²".replace(',', "'"))

        st.markdown("---")

        # Visualisierung der Verteilung
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Verteilung nach Hauptgruppe")
            hauptgruppen_dist = df['BKP_Hauptgruppe'].value_counts().reset_index()
            hauptgruppen_dist.columns = ['Hauptgruppe', 'Anzahl']
            hauptgruppen_dist['Bezeichnung'] = hauptgruppen_dist['Hauptgruppe'].map(
                lambda x: EBKP_HAUPTGRUPPEN.get(x, 'Unbekannt')
            )

            fig1 = px.pie(
                hauptgruppen_dist,
                values='Anzahl',
                names='Bezeichnung',
                title='Elemente nach eBKP-H Hauptgruppe',
                hole=0.4
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("💰 Kosten/Mengen nach Hauptgruppe")

            if 'Kosten' in df.columns:
                kosten_dist = df.groupby('BKP_Hauptgruppe')['Kosten'].sum().reset_index()
                kosten_dist['Bezeichnung'] = kosten_dist['BKP_Hauptgruppe'].map(
                    lambda x: EBKP_HAUPTGRUPPEN.get(x, 'Unbekannt')
                )

                fig2 = px.bar(
                    kosten_dist,
                    x='Bezeichnung',
                    y='Kosten',
                    title='Kosten nach eBKP-H Hauptgruppe',
                    text_auto='.2s'
                )
                fig2.update_traces(texttemplate='CHF %{y:,.0f}', textposition='outside')
                st.plotly_chart(fig2, use_container_width=True)
            elif 'Fläche (m²)' in df.columns or 'Fläche' in df.columns:
                flaeche_col = 'Fläche (m²)' if 'Fläche (m²)' in df.columns else 'Fläche'
                flaeche_dist = df.groupby('BKP_Hauptgruppe')[flaeche_col].sum().reset_index()
                flaeche_dist['Bezeichnung'] = flaeche_dist['BKP_Hauptgruppe'].map(
                    lambda x: EBKP_HAUPTGRUPPEN.get(x, 'Unbekannt')
                )

                fig2 = px.bar(
                    flaeche_dist,
                    x='Bezeichnung',
                    y=flaeche_col,
                    title='Flächen nach eBKP-H Hauptgruppe',
                    text_auto='.2f'
                )
                fig2.update_traces(texttemplate='%{y:,.2f} m²', textposition='outside')
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Keine Kosten- oder Flächendaten verfügbar für Visualisierung")

        st.markdown("---")

        # eBKP-H Hauptgruppen mit aufklappbaren Bereichen
        st.subheader("🏗️ Detaillierte eBKP-H Gliederung")

        # Sortiere Hauptgruppen alphabetisch
        vorhandene_hauptgruppen = sorted(df['BKP_Hauptgruppe'].unique())

        for hauptgruppe in vorhandene_hauptgruppen:
            hauptgruppe_name = EBKP_HAUPTGRUPPEN.get(hauptgruppe, f'Gruppe {hauptgruppe}')

            with st.expander(
                f"**{hauptgruppe} - {hauptgruppe_name}**",
                expanded=(hauptgruppe == vorhandene_hauptgruppen[0])  # Erste Gruppe ausgeklappt
            ):
                display_bkp_hierarchy(df, hauptgruppe)

        st.markdown("---")

        # Rohdaten und Export
        with st.expander("📑 Rohdaten anzeigen", expanded=False):
            st.dataframe(df, use_container_width=True)

            # Export-Button
            csv_export = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button(
                label="📥 Daten als CSV herunterladen",
                data=csv_export,
                file_name="ebkp_auswertung.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Datei: {str(e)}")
        st.exception(e)

# Zeige Anleitung nur wenn keine Daten geladen wurden
if df is None:
    # Anleitung wenn keine Datei hochgeladen
    st.info("👆 Bitte laden Sie eine CSV-Datei hoch oder nutzen Sie die KI-Klassifizierung")

    with st.expander("📖 Anleitung & Anforderungen", expanded=True):
        st.markdown("""
        ### Wie verwenden Sie diese App?

        1. **CSV-Datei vorbereiten**:
           - Exportieren Sie Daten aus Revit mit pyRevit-Scripts
           - Stellen Sie sicher, dass die Datei eine `BKP_Code` Spalte enthält

        2. **Erforderliche Spalten**:
           - `BKP_Code` (Pflicht) - eBKP-H Code (z.B. C1.1, D2.3, E3.1)
           - `BKP_Beschreibung` (Optional) - Beschreibung des BKP-Codes
           - `Kosten` (Optional) - Kosten in CHF
           - `Fläche (m²)` oder `Fläche` (Optional) - Flächen in m²

        3. **App-Features**:
           - ✅ Automatische Gliederung nach eBKP-H Hauptgruppen
           - ✅ Aufklappbare Bereiche für jede Haupt- und Untergruppe
           - ✅ Automatische Berechnung von Zwischentotalen
           - ✅ Visuelle Auswertungen mit Diagrammen
           - ✅ Export der gefilterten Daten

        ### eBKP-H Hauptgruppen:
        - **C** - Bauwerk - Rohbau
        - **D** - Bauwerk - Technik
        - **E** - Bauwerk - Ausbau
        - **F** - Umgebung
        - **G** - Baunebenkosten
        """)

        # Beispieldaten
        st.markdown("### 📝 Beispiel CSV-Struktur:")
        st.code("""
BKP_Code;BKP_Beschreibung;Kosten;Fläche (m²)
C1.1;Baugrube;15000.00;120.5
C1.2;Fundamente;25000.00;85.3
D2.1;Sanitärinstallationen;8500.00;
D2.2;Heizungsinstallationen;12000.00;
E3.1;Bodenbeläge;6500.00;95.0
        """, language="csv")
