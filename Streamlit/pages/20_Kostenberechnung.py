"""
Kostenberechnung basierend auf eBKP-H Klassifizierung und Kennwerten
"""

import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
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
        DATA_CLASSIFICATION_RESULTS,
        CFG_COST_ESTIMATION_CONFIG,
        has_classification_results
    )
except ImportError as e:
    st.error(f"Module konnten nicht importiert werden: {e}")
    st.stop()

# Seiten-Konfiguration
st.set_page_config(
    page_title="Kostenberechnung",
    page_icon="💰",
    layout="wide"
)

# Initialize Session State
init_session_state()

# Render gemeinsame Sidebar
render_sidebar()

st.title("💰 Kostenberechnung")
st.caption("Berechnung der Kosten basierend auf eBKP-H Klassifizierung und Kennwerten")

# Kennwerte-Dictionary basierend auf den Screenshots
# Format: {eBKP-H Code: {'kennwert': float, 'einheit': str}}
STANDARD_KENNWERTE = {
    # Hauptgruppen (Level 1)
    'A': {'kennwert': 116.94, 'einheit': 'CHF/m²'},
    'B': {'kennwert': 581.73, 'einheit': 'CHF/m²'},
    'C': {'kennwert': 469.77, 'einheit': 'CHF/m²'},
    'D': {'kennwert': 609.47, 'einheit': 'CHF/m²'},
    'E': {'kennwert': 259.38, 'einheit': 'CHF/m²'},
    'F': {'kennwert': 264.61, 'einheit': 'CHF/m²'},
    'G': {'kennwert': 532.32, 'einheit': 'CHF/m²'},
    'H': {'kennwert': 187.65, 'einheit': 'CHF/m²'},
    'I': {'kennwert': 484.68, 'einheit': 'CHF/m²'},
    'J': {'kennwert': 61.39, 'einheit': 'CHF/m²'},
    'V': {'kennwert': 17.67, 'einheit': '%'},
    'W': {'kennwert': 88.01, 'einheit': 'CHF/m²'},
    'Z': {'kennwert': 8.06, 'einheit': '%'},

    # Detaillierte Positionen (Level 2+)
    'A.1': {'kennwert': 20.53, 'einheit': 'CHF/m²'},
    'A.2': {'kennwert': 469.51, 'einheit': '%'},
    'B.1': {'kennwert': 29.21, 'einheit': 'CHF/m²'},
    'B.2': {'kennwert': 72.79, 'einheit': 'CHF/m²'},
    'B.3': {'kennwert': 18.33, 'einheit': 'CHF/m²'},
    'B.4': {'kennwert': 50.08, 'einheit': 'CHF/m²'},
    'B.5': {'kennwert': 21.40, 'einheit': 'CHF/m³'},
    'B.6': {'kennwert': 197.24, 'einheit': 'CHF/m³'},
    'B.8': {'kennwert': 28.44, 'einheit': 'CHF/m²'},
    'C.1': {'kennwert': 232.32, 'einheit': 'CHF/m²'},
    'C.2': {'kennwert': 156.41, 'einheit': 'CHF/m²'},
    'C.3': {'kennwert': 59.00, 'einheit': 'CHF/m²'},
    'C.4': {'kennwert': 147.93, 'einheit': 'CHF/m²'},
    'C.5': {'kennwert': 1.20, 'einheit': '%'},
    'D.1': {'kennwert': 158.22, 'einheit': 'CHF/m²'},
    'D.3': {'kennwert': 18.33, 'einheit': 'CHF/m²'},
    'D.4': {'kennwert': 11.78, 'einheit': 'CHF/m²'},
    'D.5': {'kennwert': 158.18, 'einheit': 'CHF/m²'},
    'D.6': {'kennwert': 94.11, 'einheit': 'CHF/m²'},
    'D.7': {'kennwert': 37.08, 'einheit': 'CHF/m³h'},
    'D.8': {'kennwert': 3254.30, 'einheit': 'CHF/St'},
    'D.9': {'kennwert': 53300.00, 'einheit': 'CHF/St'},
    'E.1': {'kennwert': 113.33, 'einheit': 'CHF/m²'},
    'E.2': {'kennwert': 71.22, 'einheit': 'CHF/m²'},
    'E.3': {'kennwert': 1101.77, 'einheit': 'CHF/m'},
    'F.1': {'kennwert': 94.15, 'einheit': 'CHF/m²'},
    'F.2': {'kennwert': 1777.77, 'einheit': 'CHF/m²'},
    'G.1': {'kennwert': 673.21, 'einheit': 'CHF/m²'},
    'G.2': {'kennwert': 100.37, 'einheit': 'CHF/m²'},
    'G.3': {'kennwert': 57.59, 'einheit': 'CHF/m²'},
    'G.4': {'kennwert': 44.71, 'einheit': 'CHF/m²'},
    'G.5': {'kennwert': 186.99, 'einheit': 'CHF/m²'},
    'G.6': {'kennwert': 25.41, 'einheit': 'CHF/m²'},
    'H.7': {'kennwert': 318.46, 'einheit': 'CHF/m²'},
    'I.1': {'kennwert': 122.12, 'einheit': 'CHF/m²'},
    'I.3': {'kennwert': 59.68, 'einheit': 'CHF/m²'},
    'I.4': {'kennwert': 235.42, 'einheit': 'CHF/m²'},
    'I.5': {'kennwert': 33.58, 'einheit': 'CHF/m²'},
    'I.6': {'kennwert': 124.39, 'einheit': 'CHF/m²'},
    'I.7': {'kennwert': 17.67, 'einheit': 'CHF/m²'},
    'J.1': {'kennwert': 61.39, 'einheit': 'CHF/m²'},
    'V.1': {'kennwert': 15.52, 'einheit': '%'},
    'V.3': {'kennwert': 2.15, 'einheit': '%'},
    'W.1': {'kennwert': 44.00, 'einheit': 'CHF/m²'},
    'W.2': {'kennwert': 22.00, 'einheit': 'CHF/m²'},
    'W.4': {'kennwert': 22.00, 'einheit': 'CHF/m²'},
    'Z.1': {'kennwert': 8.06, 'einheit': '%'},
}


def format_currency(value: float) -> str:
    """Formatiert Betrag als Schweizer Franken"""
    return f"{value:,.2f} CHF".replace(',', "'")


def format_tolerance(tolerance: int) -> str:
    """Formatiert Toleranz als Prozentangabe"""
    return f"± {tolerance}%"


def calculate_cost_with_tolerance(betrag: float, tolerance: int) -> tuple:
    """Berechnet Min/Max basierend auf Toleranz"""
    if tolerance == 0:
        return betrag, betrag
    tolerance_amount = betrag * (tolerance / 100)
    return betrag - tolerance_amount, betrag + tolerance_amount


def get_kennwert_for_code(ebkp_code: str) -> dict:
    """Holt Kennwert für einen eBKP-H Code oder gibt Standardwerte zurück"""
    # Exakte Übereinstimmung
    if ebkp_code in STANDARD_KENNWERTE:
        return STANDARD_KENNWERTE[ebkp_code]

    # Fallback: Standard CHF/m²
    return {'kennwert': 0.00, 'einheit': 'CHF/m²'}


def generate_pdf(df_cost, zwischensumme, total_betrag, min_betrag, max_betrag, tolerance, config_info=None):
    """Generiert PDF-Dokument der Kostenberechnung"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from io import BytesIO
        from datetime import datetime

        # PDF-Buffer erstellen
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)

        # Container für PDF-Elemente
        elements = []
        styles = getSampleStyleSheet()

        # Titelstil
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=1  # Zentriert
        )

        # Titel
        elements.append(Paragraph("Kostenberechnung eBKP-H", title_style))
        elements.append(Spacer(1, 0.5*cm))

        # Datum
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=1
        )
        elements.append(Paragraph(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}", date_style))
        elements.append(Spacer(1, 1*cm))

        # Kostenermittlungsinfo (falls vorhanden)
        if config_info:
            info_data = [
                ["Kostenermittlungsart:", config_info.get('name', 'N/A')],
                ["Toleranz:", f"± {config_info.get('tolerance', 0)}%"],
                ["Projektphase:", f"{config_info.get('project_phase', 'N/A')} ({config_info.get('phase_code', 'N/A')})"],
                ["eBKP-Tiefe:", config_info.get('ebkp_depth', 'N/A')]
            ]

            info_table = Table(info_data, colWidths=[5*cm, 10*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 1*cm))

        # Kostenzusammenfassung
        elements.append(Paragraph("Kostenzusammenfassung", styles['Heading2']))
        elements.append(Spacer(1, 0.3*cm))

        summary_data = [
            ["Position", "Betrag"],
            ["Zwischensumme (Baukosten)", format_currency(zwischensumme)],
            ["Gesamtkosten", format_currency(total_betrag)],
            ["Toleranzbereich", f"{format_currency(min_betrag)} - {format_currency(max_betrag)}"]
        ]

        summary_table = Table(summary_data, colWidths=[10*cm, 5*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#d4e6f1')),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 1.5*cm))

        # Detaillierte Positionen
        elements.append(Paragraph("Detaillierte Kostenberechnung", styles['Heading2']))
        elements.append(Spacer(1, 0.3*cm))

        # Filtere nur Positionen mit Betrag > 0
        df_with_costs = df_cost[df_cost['Betrag CHF'] > 0].copy()

        # Tabellendaten vorbereiten
        table_data = [["eBKP-H", "Beschreibung", "Menge", "Einheit", "Kennwert", "Betrag"]]

        for _, row in df_with_costs.iterrows():
            table_data.append([
                str(row['eBKP-H Code']),
                str(row['Beschreibung'])[:50],  # Kürze lange Beschreibungen
                f"{row['Menge']:.2f}",
                str(row['Einheit']),
                f"{row['Kennwert']:.2f}",
                format_currency(row['Betrag CHF'])
            ])

        # Erstelle Tabelle
        detail_table = Table(table_data, colWidths=[2*cm, 6*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        elements.append(detail_table)

        # Footer
        elements.append(Spacer(1, 2*cm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )
        elements.append(Paragraph(
            "Diese Kostenberechnung basiert auf Kennwerten und dient als Schätzung. "
            "Die tatsächlichen Kosten können abweichen.",
            footer_style
        ))

        # PDF generieren
        doc.build(elements)
        buffer.seek(0)
        return buffer

    except ImportError as e:
        st.error(f"❌ PDF-Export nicht verfügbar: {str(e)}")
        st.info("Bitte installieren Sie reportlab: `pip install reportlab`")
        return None
    except Exception as e:
        st.error(f"❌ Fehler bei PDF-Generierung: {str(e)}")
        return None


# Sidebar: Kostenermittlungs-Status
st.sidebar.header("📐 Kostenermittlung")

config = get_state(CFG_COST_ESTIMATION_CONFIG)
if config and config.get('selected'):
    st.sidebar.success(f"✓ {config['name']}")
    st.sidebar.caption(f"Toleranz: {format_tolerance(config['tolerance'])}")
    st.sidebar.caption(f"Phase: {config['project_phase']} ({config['phase_code']})")
    st.sidebar.caption(f"eBKP-Tiefe: {config['ebkp_depth']}")
    tolerance = config['tolerance']
else:
    st.sidebar.warning("⚠️ Keine Kostenermittlungsstufe ausgewählt")
    st.sidebar.caption("Standard: ±10% (Kostenvoranschlag)")
    tolerance = 10

st.sidebar.divider()
st.sidebar.info("💡 **Hinweis**: Kennwerte können in der Tabelle bearbeitet werden")

# Hauptbereich
# Datenquelle wählen: Session State oder Excel-Upload
st.subheader("📂 Datenquelle")

# Initialisiere Session State für Datenquelle
if 'cost_data_source' not in st.session_state:
    st.session_state.cost_data_source = "Session State (KI-Klassifizierung)"

data_source = st.radio(
    "Wählen Sie die Datenquelle:",
    options=["Session State (KI-Klassifizierung)", "Excel-Datei hochladen"],
    help="Nutzen Sie Session State für KI-klassifizierte Daten oder laden Sie eine vorhandene Excel-Datei hoch",
    index=0 if st.session_state.cost_data_source == "Session State (KI-Klassifizierung)" else 1,
    key="cost_data_source"
)

df_classified = None

if data_source == "Session State (KI-Klassifizierung)":
    # Prüfe ob classification_results vorhanden sind
    if not has_classification_results():
        st.warning("⚠️ Keine Klassifizierungsdaten im Session State vorhanden")
        st.info("Bitte führen Sie zuerst die eBKP-H Klassifizierung durch.")
        st.page_link("pages/03_KI_Klassifizierung.py", label="→ Zur KI Klassifizierung", icon="🤖")
        st.stop()

    # Lade classification_results
    df_classified = get_state(DATA_CLASSIFICATION_RESULTS).copy()
    st.success(f"✅ Daten aus Session State geladen: {len(df_classified)} Positionen")

else:
    # Datei-Upload (Excel oder CSV)
    st.info("📤 Laden Sie eine Excel- oder CSV-Datei mit eBKP-H Zuordnung hoch")

    with st.expander("ℹ️ Erwartetes Format", expanded=False):
        st.markdown("""
        Die Datei sollte mindestens folgende Spalten enthalten:
        - **eBKP-H Code**: z.B. "A", "C.1", "D.3"
        - **eBKP-H Beschreibung**: Beschreibung der Position
        - **Menge** (optional): Mengenangabe

        **Unterstützte Formate:**
        - Excel: `.xlsx`, `.xls`
        - CSV: `.csv` (Semikolon oder Komma als Trennzeichen)

        Weitere Spalten werden automatisch übernommen.
        """)

    uploaded_file = st.file_uploader(
        "Datei auswählen",
        type=['xlsx', 'xls', 'csv'],
        help="Unterstützte Formate: .xlsx, .xls, .csv"
    )

    if uploaded_file is not None:
        try:
            # Erkenne Dateityp und lese entsprechend
            file_extension = uploaded_file.name.split('.')[-1].lower()

            if file_extension in ['xlsx', 'xls']:
                # Lese Excel-Datei
                df_uploaded = pd.read_excel(uploaded_file)
            elif file_extension == 'csv':
                # Versuche verschiedene CSV-Trennzeichen
                try:
                    # Versuche zuerst Semikolon (Schweizer Standard)
                    df_uploaded = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig')
                except:
                    # Fallback auf Komma
                    uploaded_file.seek(0)  # Reset file pointer
                    df_uploaded = pd.read_csv(uploaded_file, sep=',', encoding='utf-8-sig')
            else:
                st.error(f"❌ Nicht unterstütztes Dateiformat: {file_extension}")
                st.stop()

            # Zeige Vorschau
            st.success(f"✅ Datei erfolgreich geladen: {len(df_uploaded)} Zeilen")

            with st.expander("📋 Datenvorschau", expanded=True):
                st.dataframe(df_uploaded.head(10), use_container_width=True)

            # Spaltennamen-Mapping für Flexibilität
            # Unterstütze sowohl "BKP_Code" als auch "eBKP-H Code"
            column_mapping = {}

            # Suche nach BKP-Code Spalte (verschiedene Varianten)
            code_columns = ['eBKP-H Code', 'BKP_Code', 'BKP Code', 'eBKP-H_Code']
            code_col = next((col for col in code_columns if col in df_uploaded.columns), None)

            if code_col:
                column_mapping[code_col] = 'eBKP-H Code'
            else:
                st.error(f"❌ Keine BKP-Code Spalte gefunden")
                st.info(f"Gesuchte Spaltennamen: {', '.join(code_columns)}")
                st.info(f"Gefundene Spalten: {', '.join(df_uploaded.columns.tolist())}")
                st.stop()

            # Suche nach BKP-Beschreibung Spalte (verschiedene Varianten)
            desc_columns = ['eBKP-H Beschreibung', 'BKP_Beschreibung', 'BKP Beschreibung', 'eBKP-H_Beschreibung', 'Beschreibung']
            desc_col = next((col for col in desc_columns if col in df_uploaded.columns), None)

            if desc_col:
                column_mapping[desc_col] = 'eBKP-H Beschreibung'
            else:
                st.error(f"❌ Keine BKP-Beschreibung Spalte gefunden")
                st.info(f"Gesuchte Spaltennamen: {', '.join(desc_columns)}")
                st.info(f"Gefundene Spalten: {', '.join(df_uploaded.columns.tolist())}")
                st.stop()

            # Umbenennen der Spalten
            df_classified = df_uploaded.rename(columns=column_mapping).copy()

            # Speichere in Session State
            st.session_state.uploaded_cost_data = df_classified.copy()
            st.session_state.uploaded_filename = uploaded_file.name

            st.info(f"✅ Spalten-Mapping: {code_col} → eBKP-H Code, {desc_col} → eBKP-H Beschreibung")

        except Exception as e:
            st.error(f"❌ Fehler beim Laden der Datei: {str(e)}")
            st.info("💡 Tipp: Stellen Sie sicher, dass die CSV-Datei UTF-8 codiert ist und Semikolon oder Komma als Trennzeichen verwendet.")
            st.stop()
    elif 'uploaded_cost_data' in st.session_state:
        # Verwende bereits hochgeladene Daten aus Session State
        df_classified = st.session_state.uploaded_cost_data.copy()

        col_info, col_clear = st.columns([4, 1])
        with col_info:
            st.success(f"✅ Gespeicherte Datei verwendet: {st.session_state.uploaded_filename} ({len(df_classified)} Zeilen)")
        with col_clear:
            if st.button("🗑️ Löschen", help="Gespeicherte Datei aus Session State entfernen"):
                del st.session_state.uploaded_cost_data
                del st.session_state.uploaded_filename
                st.rerun()

        with st.expander("📋 Datenvorschau", expanded=False):
            st.dataframe(df_classified.head(10), use_container_width=True)
    else:
        st.info("👆 Bitte wählen Sie eine Datei aus")
        st.stop()

# Prüfe ob Daten vorhanden sind
if df_classified is None or df_classified.empty:
    st.error("❌ Keine Daten zum Verarbeiten vorhanden")
    st.stop()

# Qualitätsindikator Banner
config = get_state(CFG_COST_ESTIMATION_CONFIG)
if config and config.get('selected'):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📐 Kostenermittlungsart", config['name'].split()[0])
    with col2:
        st.metric("⚖️ Toleranz", format_tolerance(config['tolerance']))
    with col3:
        st.metric("📋 Phase", config['phase_code'])
    with col4:
        st.metric("🎯 eBKP-Tiefe", config['ebkp_depth'])

st.divider()

# Vorbereitung der Kostentabelle
st.subheader("📊 Kostenberechnung mit Kennwerten")

# Prüfe welche Spalten vorhanden sind
required_columns = ['eBKP-H Code', 'eBKP-H Beschreibung']
if not all(col in df_classified.columns for col in required_columns):
    st.error("❌ Die erforderlichen Spalten fehlen in den Klassifizierungsdaten")
    st.info(f"Benötigt: {required_columns}")
    st.info(f"Vorhanden: {list(df_classified.columns)}")
    st.stop()

# Gruppiere nach eBKP-H Code und summiere Mengen
# Prüfe ob Menge-Spalte existiert
if 'Menge' not in df_classified.columns:
    df_classified['Menge'] = 0.0

# Ersetze NaN-Werte mit 0
df_classified['Menge'] = df_classified['Menge'].fillna(0.0)

# Zeige Info über Original-Daten
original_count = len(df_classified)

# Gruppiere nach eBKP-H Code und eBKP-H Beschreibung
grouped = df_classified.groupby(['eBKP-H Code', 'eBKP-H Beschreibung'], as_index=False).agg({
    'Menge': 'sum'
})

# Sortiere alphabetisch nach eBKP-H Code (A, B, C, etc.)
grouped = grouped.sort_values('eBKP-H Code')

# Info-Meldung
st.info(f"ℹ️ {original_count} Einzelpositionen wurden zu {len(grouped)} eBKP-H Positionen gruppiert und alphabetisch sortiert.")

# Erstelle Kostentabelle
cost_data = []

for idx, row in grouped.iterrows():
    ebkp_code = row['eBKP-H Code']
    beschreibung = row['eBKP-H Beschreibung']

    # Hole Kennwert
    kennwert_info = get_kennwert_for_code(ebkp_code)

    cost_data.append({
        'eBKP-H Code': ebkp_code,
        'Beschreibung': beschreibung,
        'Menge': float(row['Menge']),
        'Einheit': kennwert_info['einheit'],
        'Kennwert': float(kennwert_info['kennwert']),
        'Betrag CHF': 0.0  # Wird berechnet
    })

df_cost = pd.DataFrame(cost_data)

# Info-Box
with st.expander("ℹ️ Anleitung", expanded=False):
    st.markdown("""
    ### Wie funktioniert die Kostenberechnung?

    1. **Kennwerte**: Voreingestellte Kennwerte basieren auf Schweizer Bauökonomie-Standards
    2. **Menge anpassen**: Tragen Sie die Mengen für jede Position ein
    3. **Kennwert anpassen**: Bei Bedarf können Sie die Kennwerte überschreiben
    4. **Automatische Berechnung**: Betrag = Menge × Kennwert
    5. **Toleranzen**: Basierend auf der gewählten Kostenermittlungsstufe

    **Einheiten**:
    - CHF/m²: Kosten pro Quadratmeter
    - CHF/m³: Kosten pro Kubikmeter
    - CHF/m: Kosten pro Laufmeter
    - CHF/St: Kosten pro Stück
    - %: Prozentanteil
    """)

st.divider()

# Editierbare Tabelle
st.subheader("✏️ Mengen und Kennwerte bearbeiten")

# Konfiguriere Column-Config für bessere Darstellung
column_config = {
    'eBKP-H Code': st.column_config.TextColumn(
        'eBKP-H Code',
        width='small',
        disabled=True
    ),
    'Beschreibung': st.column_config.TextColumn(
        'Beschreibung',
        width='large',
        disabled=True
    ),
    'Menge': st.column_config.NumberColumn(
        'Menge',
        width='small',
        min_value=0.0,
        format="%.2f",
        help="Menge der Position (editierbar)"
    ),
    'Einheit': st.column_config.TextColumn(
        'Einheit',
        width='small',
        disabled=True
    ),
    'Kennwert': st.column_config.NumberColumn(
        'Kennwert',
        width='medium',
        min_value=0.0,
        format="%.2f",
        help="Kennwert für die Kostenberechnung (editierbar)"
    ),
    'Betrag CHF': st.column_config.NumberColumn(
        'Betrag CHF',
        width='medium',
        disabled=True,
        format="%.2f"
    ),
}

# Editierbare Tabelle
edited_df = st.data_editor(
    df_cost,
    column_config=column_config,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    key="cost_editor"
)

# Berechne Beträge
for idx in edited_df.index:
    menge = edited_df.loc[idx, 'Menge']
    kennwert = edited_df.loc[idx, 'Kennwert']
    einheit = edited_df.loc[idx, 'Einheit']

    # Berechnung basierend auf Einheit
    if '%' in einheit:
        # Prozentuale Positionen später auf Zwischensumme anwenden
        edited_df.loc[idx, 'Betrag CHF'] = 0.0
    else:
        edited_df.loc[idx, 'Betrag CHF'] = menge * kennwert

st.divider()

# Kostenzusammenfassung
st.subheader("💰 Kostenzusammenfassung")

# Berechne Zwischensumme (ohne %-Positionen)
zwischensumme = edited_df[~edited_df['Einheit'].str.contains('%', na=False)]['Betrag CHF'].sum()

# Berechne %-Positionen (V, Z) auf Zwischensumme
prozent_positionen = edited_df[edited_df['Einheit'].str.contains('%', na=False)]
prozent_betrag = 0.0

for idx, row in prozent_positionen.iterrows():
    prozent = row['Kennwert']
    betrag = zwischensumme * (prozent / 100)
    prozent_betrag += betrag
    edited_df.loc[idx, 'Betrag CHF'] = betrag

# Gesamtsumme
total_betrag = zwischensumme + prozent_betrag

# Berechne Min/Max mit Toleranz
min_betrag, max_betrag = calculate_cost_with_tolerance(total_betrag, tolerance)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "💵 Zwischensumme (Baukosten)",
        format_currency(zwischensumme),
        help="Summe aller Positionen ohne Planungskosten und Mehrwertsteuer"
    )

with col2:
    st.metric(
        "💰 Gesamtkosten",
        format_currency(total_betrag),
        help="Gesamtsumme inkl. Planungskosten (V) und Mehrwertsteuer (Z)"
    )

with col3:
    st.metric(
        "⚖️ Toleranzbereich",
        f"{format_currency(min_betrag)} - {format_currency(max_betrag)}",
        help=f"Kostenrahmen mit ±{tolerance}% Toleranz"
    )

# Detaillierte Aufschlüsselung
with st.expander("📋 Detaillierte Aufschlüsselung", expanded=False):
    st.markdown("### Positionen mit Beträgen")

    # Zeige nur Positionen mit Betrag > 0
    df_with_costs = edited_df[edited_df['Betrag CHF'] > 0].copy()
    df_with_costs['Betrag formatiert'] = df_with_costs['Betrag CHF'].apply(format_currency)

    st.dataframe(
        df_with_costs[['eBKP-H Code', 'Beschreibung', 'Menge', 'Einheit', 'Kennwert', 'Betrag formatiert']],
        use_container_width=True,
        hide_index=True
    )

st.divider()

# Export-Funktionen
st.subheader("💾 Export")

col1, col2, col3 = st.columns(3)

with col1:
    # CSV Export
    csv = edited_df.to_csv(index=False, encoding='utf-8-sig', sep=';', decimal=',')
    if st.download_button(
        label="📥 CSV herunterladen",
        data=csv,
        file_name="kostenberechnung_ebkp.csv",
        mime="text/csv",
        help="Export der Kostenberechnung im CSV-Format",
        use_container_width=True,
        key="download_csv"
    ):
        st.balloons()

with col2:
    # Excel Export
    try:
        from io import BytesIO
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment

        # Erstelle Excel-Datei
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            edited_df.to_excel(writer, sheet_name='Kostenberechnung', index=False)

            # Formatierung
            workbook = writer.book
            worksheet = writer.sheets['Kostenberechnung']

            # Header formatieren
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")

            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center')

            # Spaltenbreiten anpassen
            worksheet.column_dimensions['A'].width = 15
            worksheet.column_dimensions['B'].width = 50
            worksheet.column_dimensions['C'].width = 12
            worksheet.column_dimensions['D'].width = 12
            worksheet.column_dimensions['E'].width = 12
            worksheet.column_dimensions['F'].width = 15

        if st.download_button(
            label="📥 Excel herunterladen",
            data=buffer.getvalue(),
            file_name="kostenberechnung_ebkp.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Export der Kostenberechnung im Excel-Format",
            use_container_width=True,
            key="download_excel"
        ):
            st.balloons()
    except ImportError:
        st.info("Excel-Export nicht verfügbar (openpyxl nicht installiert)")

with col3:
    # PDF Export
    # Hole Kostenermittlungs-Config falls vorhanden
    config_info = get_state(CFG_COST_ESTIMATION_CONFIG)
    if config_info and not config_info.get('selected'):
        config_info = None

    pdf_buffer = generate_pdf(edited_df, zwischensumme, total_betrag, min_betrag, max_betrag, tolerance, config_info)

    if pdf_buffer:
        if st.download_button(
            label="📄 PDF herunterladen",
            data=pdf_buffer,
            file_name="kostenberechnung_ebkp.pdf",
            mime="application/pdf",
            help="Export der Kostenberechnung als professionelles PDF-Dokument",
            use_container_width=True,
            key="download_pdf"
        ):
            st.balloons()
    else:
        st.error("PDF-Export nicht verfügbar", icon="❌")

# Speichere bearbeitete Daten im Session State
if st.button("💾 Kostenberechnung speichern", type="primary", use_container_width=True):
    st.session_state.cost_calculation = edited_df.copy()
    st.session_state.cost_summary = {
        'zwischensumme': zwischensumme,
        'total': total_betrag,
        'min': min_betrag,
        'max': max_betrag,
        'tolerance': tolerance
    }
    st.success("✅ Kostenberechnung wurde gespeichert!")
    st.balloons()

# Footer
st.divider()
st.caption("💡 Hinweis: Diese Kostenberechnung basiert auf Kennwerten und dient als Schätzung. Die tatsächlichen Kosten können abweichen.")
