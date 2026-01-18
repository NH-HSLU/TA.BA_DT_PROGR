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
        DATA_PROJEKT_DATEN,
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


def load_kennwerte_csv(uploaded_file) -> pd.DataFrame:
    """
    Lädt CSV-Datei mit Kennwerten

    Erwartete Spalten:
    - A: eBKP-H Code
    - B: Kostengruppe / Position
    - C: Kennwert Einheit
    - D: Kennwert tief CHF/Einheit
    - E: Kennwert mittel CHF/Einheit
    - F: Kennwert hoch CHF/Einheit
    - G: Anmerkungen
    """
    try:
        # Lese CSV mit Semikolon
        df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig')

        # Erwartete Spaltennamen
        expected_columns = [
            'eBKP-H Code',
            'Kostengruppe / Position',
            'Kennwert Einheit',
            'Kennwert tief CHF/Einheit',
            'Kennwert mittel CHF/Einheit',
            'Kennwert hoch CHF/Einheit',
            'Anmerkungen'
        ]

        # Prüfe ob alle Spalten vorhanden sind
        if list(df.columns) == expected_columns:
            # Filtere leere Zeilen (wo eBKP-H Code leer ist)
            df = df[df['eBKP-H Code'].notna() & (df['eBKP-H Code'] != '')]
            return df
        else:
            st.error("❌ CSV-Datei hat nicht die erwarteten Spalten")
            st.info(f"Erwartet: {expected_columns}")
            st.info(f"Gefunden: {list(df.columns)}")
            return None

    except Exception as e:
        st.error(f"❌ Fehler beim Laden der CSV-Datei: {str(e)}")
        return None


def aggregate_quantities_by_code(df: pd.DataFrame) -> dict:
    """
    Aggregiert Mengen aus klassifizierten Daten nach eBKP-H Code.

    Diese Funktion durchläuft die Modell-Daten einmalig und gruppiert
    alle Mengen nach ihrem eBKP-H Code. Dies ist deutlich effizienter
    als für jede Kostenplan-Position die gesamte Liste zu durchsuchen.

    Args:
        df: DataFrame mit klassifizierten Daten (enthält 'eBKP-H Code' und 'Menge')

    Returns:
        Dict[str, float]: Dictionary mit eBKP-H Code als Key und summierter Menge als Value

    Example:
        >>> df = pd.DataFrame({
        ...     'eBKP-H Code': ['C13.01', 'C13.01', 'D21.03'],
        ...     'Menge': [5.0, 3.0, 10.0]
        ... })
        >>> aggregate_quantities_by_code(df)
        {'C13.01': 8.0, 'D21.03': 10.0}
    """
    if df is None or df.empty:
        return {}

    if 'eBKP-H Code' not in df.columns:
        return {}

    # Entferne Zeilen mit leeren oder ungültigen eBKP-H Codes
    df_valid = df[df['eBKP-H Code'].notna() & (df['eBKP-H Code'] != '')]

    if df_valid.empty:
        return {}

    # Prüfe ob Menge-Spalte existiert
    if 'Menge' not in df_valid.columns:
        return {}

    # Entferne Zeilen mit ungültigen Mengen
    df_valid = df_valid[df_valid['Menge'].notna()]

    # Gruppiere nach eBKP-H Code und summiere Mengen - O(m) Operation!
    quantities = df_valid.groupby('eBKP-H Code')['Menge'].sum().to_dict()

    return quantities


def generate_pdf(df_cost, zwischensumme, total_betrag, min_betrag, max_betrag, tolerance, config_info=None, projekt_daten=None):
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

        # Projektinformationen (falls vorhanden)
        if projekt_daten:
            # Überschrift für Projektinformationen
            project_header_style = ParagraphStyle(
                'ProjectHeader',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=10,
                spaceBefore=5
            )
            elements.append(Paragraph("Projektinformationen", project_header_style))

            # Projektdaten-Tabelle
            project_data = [
                ["OBJEKT", ""],
                ["Projektname:", projekt_daten.objekt.projektname],
                ["Adresse:", projekt_daten.objekt.adresse],
                ["PLZ/Ort:", projekt_daten.objekt.plz_ort],
                ["", ""],
                ["BAUHERR", ""],
                ["Name:", projekt_daten.bauherr.name],
                ["Adresse:", projekt_daten.bauherr.adresse],
                ["PLZ/Ort:", projekt_daten.bauherr.plz_ort],
                ["", ""],
                ["BAUMANAGEMENT", ""],
                ["Firma:", projekt_daten.baumanagement.firma],
                ["Kontaktperson:", projekt_daten.baumanagement.kontaktperson],
                ["Adresse:", projekt_daten.baumanagement.adresse],
                ["PLZ/Ort:", projekt_daten.baumanagement.plz_ort],
            ]

            project_table = Table(project_data, colWidths=[5*cm, 12*cm])
            project_table.setStyle(TableStyle([
                # Überschriften (OBJEKT, BAUHERR, BAUMANAGEMENT)
                ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#366092')),
                ('BACKGROUND', (0, 5), (1, 5), colors.HexColor('#366092')),
                ('BACKGROUND', (0, 10), (1, 10), colors.HexColor('#366092')),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
                ('TEXTCOLOR', (0, 5), (1, 5), colors.whitesmoke),
                ('TEXTCOLOR', (0, 10), (1, 10), colors.whitesmoke),
                ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 5), (1, 5), 'Helvetica-Bold'),
                ('FONTNAME', (0, 10), (1, 10), 'Helvetica-Bold'),
                ('SPAN', (0, 0), (1, 0)),
                ('SPAN', (0, 5), (1, 5)),
                ('SPAN', (0, 10), (1, 10)),
                ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                ('ALIGN', (0, 5), (1, 5), 'CENTER'),
                ('ALIGN', (0, 10), (1, 10), 'CENTER'),

                # Datenzeilen
                ('BACKGROUND', (0, 1), (0, 3), colors.HexColor('#f0f0f0')),
                ('BACKGROUND', (0, 6), (0, 8), colors.HexColor('#f0f0f0')),
                ('BACKGROUND', (0, 11), (0, 14), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),

                # Trennlinien
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.grey),
                ('LINEBELOW', (0, 5), (-1, 5), 1, colors.grey),
                ('LINEBELOW', (0, 10), (-1, 10), 1, colors.grey),
                ('BOX', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            elements.append(project_table)
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

        # Filtere nur Positionen mit Betrag > 0 (keine Nullpositionen im PDF)
        df_with_costs = df_cost[df_cost['Betrag CHF'] > 0].copy()

        # Info-Text wenn Positionen gefiltert wurden
        total_positions = len(df_cost)
        positions_with_costs = len(df_with_costs)
        filtered_count = total_positions - positions_with_costs

        if filtered_count > 0:
            filter_info_style = ParagraphStyle(
                'FilterInfo',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                spaceAfter=10
            )
            elements.append(Paragraph(
                f"Angezeigt werden {positions_with_costs} von {total_positions} Positionen "
                f"({filtered_count} Positionen ohne Kosten wurden ausgeblendet)",
                filter_info_style
            ))

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


# ================================================================================
# SCHRITT 1: KENNWERTE-KOSTENPLAN IMPORTIEREN
# ================================================================================

st.header("📋 Schritt 1: Kostenplan mit Kennwerten importieren")

st.markdown("""
Laden Sie Ihre eigene Kostenplan-CSV-Datei mit Kennwerten hoch.
Diese Datei enthält alle eBKP-H Positionen mit den zugehörigen Kennwerten (tief, mittel, hoch).
""")

# File uploader für Kostenplan
kennwerte_file = st.file_uploader(
    "📤 Kostenplan CSV-Datei hochladen",
    type=['csv'],
    help="CSV-Datei mit eBKP-H Codes und Kennwerten (tief, mittel, hoch)",
    key="kennwerte_upload"
)

df_kennwerte = None
kennwerte_level = None

if kennwerte_file is not None:
    # Lade Kennwerte CSV
    df_kennwerte = load_kennwerte_csv(kennwerte_file)

    if df_kennwerte is not None:
        st.success(f"✅ Kostenplan erfolgreich geladen: {len(df_kennwerte)} Positionen")

        # Vorschau
        with st.expander("📊 Kostenplan Vorschau (erste 10 Zeilen)", expanded=False):
            st.dataframe(df_kennwerte.head(10), use_container_width=True)

        # Auswahl: Tief / Mittel / Hoch
        st.subheader("🎯 Kennwert-Niveau auswählen")

        # Default: Mittel (falls noch nicht gesetzt)
        if 'kennwerte_level' not in st.session_state:
            st.session_state.kennwerte_level = "mittel"

        kennwerte_level = st.session_state.kennwerte_level

        col1, col2, col3 = st.columns(3)

        with col1:
            button_type_tief = "primary" if kennwerte_level == "tief" else "secondary"
            if st.button("📉 Tief", use_container_width=True, type=button_type_tief, key="btn_tief"):
                st.session_state.kennwerte_level = "tief"
                st.rerun()
        with col2:
            button_type_mittel = "primary" if kennwerte_level == "mittel" else "secondary"
            if st.button("📊 Mittel", use_container_width=True, type=button_type_mittel, key="btn_mittel"):
                st.session_state.kennwerte_level = "mittel"
                st.rerun()
        with col3:
            button_type_hoch = "primary" if kennwerte_level == "hoch" else "secondary"
            if st.button("📈 Hoch", use_container_width=True, type=button_type_hoch, key="btn_hoch"):
                st.session_state.kennwerte_level = "hoch"
                st.rerun()

        st.info(f"🎯 Ausgewähltes Niveau: **{kennwerte_level.upper()}**")

        # Speichere in Session State
        st.session_state.df_kennwerte = df_kennwerte.copy()

elif 'df_kennwerte' in st.session_state:
    # Verwende gespeicherte Kennwerte
    df_kennwerte = st.session_state.df_kennwerte.copy()
    kennwerte_level = st.session_state.get('kennwerte_level', 'mittel')

    st.success(f"✅ Gespeicherter Kostenplan verwendet: {len(df_kennwerte)} Positionen")
    st.info(f"🎯 Ausgewähltes Niveau: **{kennwerte_level.upper()}**")

    col_info, col_clear = st.columns([4, 1])
    with col_clear:
        if st.button("🗑️ Kostenplan löschen", help="Gespeicherten Kostenplan entfernen"):
            del st.session_state.df_kennwerte
            if 'kennwerte_level' in st.session_state:
                del st.session_state.kennwerte_level
            st.rerun()
else:
    st.info("👆 Bitte laden Sie zuerst einen Kostenplan mit Kennwerten hoch")
    st.stop()

st.divider()

# ================================================================================
# SCHRITT 2: MODELL-DATEN LADEN (OPTIONAL)
# ================================================================================

st.header("📦 Schritt 2: Modell-Daten laden (optional)")

st.markdown("""
Laden Sie optional Daten aus dem BIM-Modell, um automatisch Mengen für die Kostenberechnung zu übernehmen.
Falls keine Modell-Daten vorhanden sind, können Sie die Mengen manuell eingeben.
""")

# Datenquelle wählen
if 'model_data_source' not in st.session_state:
    st.session_state.model_data_source = "Keine (Manuell)"

data_source = st.radio(
    "Modell-Datenquelle:",
    options=["Keine (Manuell)", "Session State (KI-Klassifizierung)", "Excel/CSV-Datei hochladen"],
    help="Wählen Sie, ob Sie Modell-Daten verwenden möchten oder alles manuell eingeben",
    key="model_data_source"
)

df_model_data = None

if data_source == "Session State (KI-Klassifizierung)":
    # Prüfe ob classification_results vorhanden sind
    if not has_classification_results():
        st.warning("⚠️ Keine Klassifizierungsdaten im Session State vorhanden")
        st.info("Bitte führen Sie zuerst die eBKP-H Klassifizierung durch oder wählen Sie eine andere Datenquelle.")
        st.page_link("pages/03_KI_Klassifizierung.py", label="→ Zur KI Klassifizierung", icon="🤖")
    else:
        # Lade classification_results
        df_model_data = get_state(DATA_CLASSIFICATION_RESULTS).copy()

        # Flexibles Spaltennamen-Mapping für eBKP-H Code
        # Spalte N (Index 13) oder verschiedene Varianten
        code_columns = ['BKP_Code', 'BKP Code', 'eBKP-H Code', 'eBKP-H_Code', 'eBKP_Code']
        code_col = None

        # Prüfe zuerst per Spaltenname
        for col_name in code_columns:
            if col_name in df_model_data.columns:
                code_col = col_name
                break

        # Falls nicht gefunden: Verwende Spalte N (Index 13)
        if code_col is None and len(df_model_data.columns) > 13:
            code_col = df_model_data.columns[13]
            st.info(f"📍 eBKP-H Code aus Spalte N (Index 13): '{code_col}'")

        # Umbenennen zu Standardname
        if code_col and code_col != 'eBKP-H Code':
            df_model_data = df_model_data.rename(columns={code_col: 'eBKP-H Code'})

        # Mapping für Beschreibung
        desc_columns = ['BKP_Beschreibung', 'BKP Beschreibung', 'eBKP-H Beschreibung', 'eBKP-H_Beschreibung']
        desc_col = next((col for col in desc_columns if col in df_model_data.columns), None)
        if desc_col and desc_col != 'eBKP-H Beschreibung':
            df_model_data = df_model_data.rename(columns={desc_col: 'eBKP-H Beschreibung'})

        # Flexibles Mapping für Menge - verschiedene mögliche Spaltennamen
        menge_columns = ['Menge', 'menge', 'Anzahl', 'Quantity', 'Amount', 'Fläche', 'Fläche (m²)', 'Area']
        menge_col = None
        for col_name in menge_columns:
            if col_name in df_model_data.columns:
                menge_col = col_name
                break

        # Falls Menge-Spalte gefunden: Umbenennen
        if menge_col and menge_col != 'Menge':
            df_model_data = df_model_data.rename(columns={menge_col: 'Menge'})
            st.info(f"📊 Menge-Spalte gefunden und umbenannt: '{menge_col}' → 'Menge'")
        elif menge_col is None:
            # Erstelle Menge-Spalte mit Wert 1 (Anzahl = 1 pro Element)
            df_model_data['Menge'] = 1.0
            st.warning("⚠️ Keine Menge-Spalte gefunden. Standard-Menge = 1 pro Element gesetzt.")

        st.success(f"✅ Daten aus Session State geladen: {len(df_model_data)} Positionen")

        with st.expander("📋 Modell-Daten Vorschau", expanded=False):
            st.dataframe(df_model_data.head(10), use_container_width=True)
            st.caption(f"**Verfügbare Spalten:** {', '.join(df_model_data.columns.tolist())}")

        # Aggregiere und zeige Statistiken über eBKP-H Codes
        quantities_preview = aggregate_quantities_by_code(df_model_data)
        if quantities_preview:
            st.success(f"✅ Mengen aus {len(df_model_data)} Elementen aggregiert")
            st.info(f"📊 {len(quantities_preview)} eindeutige eBKP-H Codes mit Mengen gefunden")

            with st.expander("🔍 Mengen-Übersicht (Top 10)", expanded=False):
                top_codes = sorted(quantities_preview.items(), key=lambda x: x[1], reverse=True)[:10]
                for code, qty in top_codes:
                    st.caption(f"• **{code}**: {qty:.2f}")

elif data_source == "Excel/CSV-Datei hochladen":
    # Datei-Upload
    uploaded_file = st.file_uploader(
        "📤 Excel- oder CSV-Datei mit Modell-Daten hochladen",
        type=['xlsx', 'xls', 'csv'],
        help="Datei mit eBKP-H Codes und Mengen aus dem BIM-Modell",
        key="model_data_upload"
    )

    if uploaded_file is not None:
        try:
            # Erkenne Dateityp
            file_extension = uploaded_file.name.split('.')[-1].lower()

            if file_extension in ['xlsx', 'xls']:
                df_model_data = pd.read_excel(uploaded_file)
            elif file_extension == 'csv':
                try:
                    df_model_data = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig')
                except:
                    uploaded_file.seek(0)
                    df_model_data = pd.read_csv(uploaded_file, sep=',', encoding='utf-8-sig')

            # Spaltennamen-Mapping
            if 'BKP_Code' in df_model_data.columns:
                df_model_data = df_model_data.rename(columns={'BKP_Code': 'eBKP-H Code'})
            if 'BKP_Beschreibung' in df_model_data.columns:
                df_model_data = df_model_data.rename(columns={'BKP_Beschreibung': 'eBKP-H Beschreibung'})

            st.success(f"✅ Modell-Datei erfolgreich geladen: {len(df_model_data)} Zeilen")

            with st.expander("📋 Modell-Daten Vorschau", expanded=False):
                st.dataframe(df_model_data.head(10), use_container_width=True)

            # Aggregiere und zeige Statistiken über eBKP-H Codes
            quantities_preview = aggregate_quantities_by_code(df_model_data)
            if quantities_preview:
                st.success(f"✅ Mengen aus {len(df_model_data)} Elementen aggregiert")
                st.info(f"📊 {len(quantities_preview)} eindeutige eBKP-H Codes mit Mengen gefunden")

                with st.expander("🔍 Mengen-Übersicht (Top 10)", expanded=False):
                    top_codes = sorted(quantities_preview.items(), key=lambda x: x[1], reverse=True)[:10]
                    for code, qty in top_codes:
                        st.caption(f"• **{code}**: {qty:.2f}")

        except Exception as e:
            st.error(f"❌ Fehler beim Laden der Datei: {str(e)}")
            df_model_data = None
    else:
        st.info("👆 Bitte laden Sie eine Datei hoch oder wählen Sie 'Keine (Manuell)'")

else:
    st.info("ℹ️ Keine Modell-Daten werden verwendet. Alle Mengen müssen manuell eingegeben werden.")

st.divider()

# ================================================================================
# SCHRITT 3: KOSTENBERECHNUNG
# ================================================================================

st.header("💰 Schritt 3: Kostenberechnung")

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
st.sidebar.info(f"🎯 Kennwert-Niveau: **{kennwerte_level.upper()}**")
st.sidebar.info("💡 **Hinweis**: Kennwerte und Mengen können in der Tabelle bearbeitet werden")

# Qualitätsindikator Banner
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

# Erstelle Kostenberechnungstabelle
st.subheader("📊 Kostenberechnungstabelle")

# Bestimme welche Kennwert-Spalte verwendet werden soll
kennwert_col = f"Kennwert {kennwerte_level} CHF/Einheit"

# Erstelle DataFrame mit ALLEN Positionen aus dem Kostenplan
cost_data = []

# OPTIMIERUNG: Aggregiere Mengen einmalig VOR der Schleife (O(m) statt O(n*m))
quantities_by_code = aggregate_quantities_by_code(df_model_data) if df_model_data is not None else {}

for idx, row in df_kennwerte.iterrows():
    ebkp_code = row['eBKP-H Code']
    beschreibung = row['Kostengruppe / Position']
    einheit = row['Kennwert Einheit'] if pd.notna(row['Kennwert Einheit']) else 'CHF/m²'
    kennwert = row[kennwert_col] if pd.notna(row[kennwert_col]) else 0.0
    anmerkung = row['Anmerkungen'] if pd.notna(row['Anmerkungen']) else ''

    # OPTIMIERUNG: Schneller Dictionary-Lookup statt DataFrame-Suche - O(1) statt O(m)
    menge = quantities_by_code.get(ebkp_code, 0.0)

    # Berechne Betrag
    betrag = 0.0
    if menge > 0 and kennwert > 0:
        if '%' not in str(einheit):
            betrag = menge * kennwert

    cost_data.append({
        'eBKP-H Code': ebkp_code,
        'Beschreibung': beschreibung,
        'Menge': float(menge),
        'Einheit': einheit,
        'Kennwert': float(kennwert),
        'Betrag CHF': float(betrag),
        'Pauschalpreis CHF': 0.0,  # Neue Spalte für Pauschalpreis
        'Anmerkung': anmerkung
    })

df_cost = pd.DataFrame(cost_data)

# Prüfe ob "Finanzbedarfs" gewählt wurde - dann nur Hauptgruppen anzeigen
is_finanzbedarfs = False
if config and config.get('selected'):
    kostenermittlungsart = config.get('name', '').lower()
    if 'finanzbedarfs' in kostenermittlungsart or 'finanzbedarf' in kostenermittlungsart:
        is_finanzbedarfs = True
        # Filtere nur Hauptgruppen (eBKP-H Codes ohne Punkt)
        df_cost = df_cost[~df_cost['eBKP-H Code'].astype(str).str.contains('.', regex=False)].copy()
        st.info(f"ℹ️ Finanzbedarfsermittlung: Es werden nur die {len(df_cost)} Hauptgruppen angezeigt")

# Validierung: Zeige Positionen ohne Modell-Daten
if quantities_by_code:
    # Finde Codes mit und ohne Daten
    codes_with_data = set(code for code, qty in quantities_by_code.items() if qty > 0)
    codes_in_kostenplan = set(df_cost['eBKP-H Code'].values)
    codes_without_data = codes_in_kostenplan - codes_with_data

    if codes_without_data:
        with st.expander(f"⚠️ {len(codes_without_data)} Kostenplan-Positionen ohne Modell-Daten", expanded=False):
            st.caption("Diese Positionen sind im Kostenplan vorhanden, haben aber keine zugeordneten Mengen aus den Modell-Daten:")
            for code in sorted(codes_without_data):
                desc = df_cost[df_cost['eBKP-H Code'] == code]['Beschreibung'].iloc[0]
                st.caption(f"• **{code}**: {desc}")
            st.info("💡 Diese Positionen haben Menge = 0. Sie können die Mengen manuell in der Tabelle unten eingeben.")

# Info-Box
with st.expander("ℹ️ Anleitung", expanded=False):
    st.markdown(f"""
    ### Wie funktioniert die Kostenberechnung?

    1. **Kostenplan**: {len(df_cost)} Positionen {('(nur Hauptgruppen)' if is_finanzbedarfs else '')} aus Ihrem Kostenplan werden angezeigt
    2. **Kennwert-Niveau**: Aktuell ausgewählt: **{kennwerte_level.upper()}**
    3. **Modell-Daten**: {'Daten aus ' + data_source + ' geladen' if df_model_data is not None else 'Keine Modell-Daten - manuelle Eingabe erforderlich'}
    4. **Menge anpassen**: Tragen Sie die Mengen für jede Position ein (falls nicht aus Modell übernommen)
    5. **Kennwert anpassen**: Bei Bedarf können Sie die Kennwerte überschreiben
    6. **Pauschalpreis**: Alternativ können Sie einen Pauschalpreis eingeben (überschreibt Menge × Kennwert)
    7. **Zeilen löschen**: Nicht benötigte Positionen können gelöscht werden
    8. **Automatische Berechnung**: Betrag = Menge × Kennwert (oder Pauschalpreis, falls eingegeben)
    9. **Toleranzen**: Basierend auf der gewählten Kostenermittlungsstufe (±{tolerance}%)

    **Einheiten**:
    - CHF/m²: Kosten pro Quadratmeter
    - CHF/m³: Kosten pro Kubikmeter
    - CHF/m: Kosten pro Laufmeter
    - CHF/St: Kosten pro Stück
    - %: Prozentanteil (wird auf Zwischensumme angewendet)
    - Pauschal: Fester Betrag
    """)

st.divider()

# Editierbare Tabelle oder kompakte Listenansicht
st.subheader("✏️ Kostenberechnung bearbeiten")

# Initialisiere oder aktualisiere Session State für bearbeitete Daten
# Prüfe ob sich die Kostenermittlungsstufe ODER die Modell-Daten geändert haben
num_quantities = len(quantities_by_code) if quantities_by_code else 0
total_quantity = sum(quantities_by_code.values()) if quantities_by_code else 0
current_filter_key = f"finanzbedarfs_{is_finanzbedarfs}_quantities_{num_quantities}_{total_quantity:.2f}"

if 'cost_filter_key' not in st.session_state or st.session_state.cost_filter_key != current_filter_key:
    # Filter oder Daten haben sich geändert - initialisiere neu mit aktuellen Mengen aus df_cost
    st.session_state.edited_cost_data = df_cost.copy()
    st.session_state.cost_filter_key = current_filter_key
    if num_quantities > 0:
        st.info(f"🔄 Tabelle mit neuen Modell-Daten aktualisiert: {num_quantities} eBKP-H Codes mit Mengen")

# Verwende gespeicherte Daten
edited_df = st.session_state.edited_cost_data.copy()

# Berechne Beträge INITIAL (berücksichtigt Pauschalpreis)
for idx in edited_df.index:
    pauschalpreis = edited_df.loc[idx, 'Pauschalpreis CHF']

    # Falls Pauschalpreis eingegeben: Verwende diesen
    if pauschalpreis > 0:
        edited_df.loc[idx, 'Betrag CHF'] = pauschalpreis
    else:
        # Sonst: Berechne aus Menge × Kennwert
        menge = edited_df.loc[idx, 'Menge']
        kennwert = edited_df.loc[idx, 'Kennwert']
        einheit = edited_df.loc[idx, 'Einheit']

        # Prozentuale Positionen später auf Zwischensumme anwenden
        if '%' in str(einheit):
            edited_df.loc[idx, 'Betrag CHF'] = 0.0
        else:
            edited_df.loc[idx, 'Betrag CHF'] = menge * kennwert

# Füge Stern (*) vor Hauptgruppen hinzu und erstelle Display-DataFrame
df_cost_display = edited_df.copy()
df_cost_display['Position'] = df_cost_display.apply(
    lambda row: f"*   {row['eBKP-H Code']}" if '.' not in str(row['eBKP-H Code']) else f"     {row['eBKP-H Code']}",
    axis=1
)

# Konfiguriere Column-Config - kompakte Darstellung wie im Screenshot
column_config = {
    'Position': st.column_config.TextColumn(
        'Position',
        width='small',
        disabled=True,
        help="eBKP-H Code (* = Hauptgruppe)"
    ),
    'Beschreibung': st.column_config.TextColumn(
        'Beschreibung',
        width='large',
        disabled=True,
        help="Kostengruppe / Position"
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
        disabled=True,
        help="Einheit"
    ),
    'Kennwert': st.column_config.NumberColumn(
        'Kennwert',
        width='small',
        min_value=0.0,
        format="%.2f CHF",
        help="Kennwert (editierbar)"
    ),
    'Betrag CHF': st.column_config.NumberColumn(
        'Betrag CHF',
        width='medium',
        disabled=True,
        format="%.2f",
        help="Berechnet: Menge × Kennwert"
    ),
    'Pauschalpreis CHF': st.column_config.NumberColumn(
        'Pauschalpreis',
        width='medium',
        min_value=0.0,
        format="%.2f",
        help="Optional: Pauschalpreis"
    ),
}

# Wähle Spalten für Anzeige
display_columns = ['Position', 'Beschreibung', 'Menge', 'Einheit', 'Kennwert', 'Betrag CHF', 'Pauschalpreis CHF']

# Editierbare Tabelle mit Lösch-Funktion
edited_df_display = st.data_editor(
    df_cost_display[display_columns],
    column_config=column_config,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",  # Ermöglicht Hinzufügen/Löschen von Zeilen
    key="cost_editor"
)

# Übertrage Änderungen zurück zu edited_df mit allen Spalten
# Behandle Fall wenn Zeilen gelöscht/hinzugefügt wurden
if len(edited_df_display) != len(edited_df):
    # Zeilen wurden geändert - rekonstruiere edited_df aus edited_df_display
    # Extrahiere eBKP-H Code aus Position-Spalte (entferne Stern und Leerzeichen)
    edited_df_display['eBKP-H Code'] = edited_df_display['Position'].str.replace('*', '').str.strip()

    # Füge fehlende Spalten aus df_cost wieder hinzu basierend auf eBKP-H Code
    edited_df = edited_df_display.copy()
    edited_df['Anmerkung'] = edited_df['eBKP-H Code'].map(
        df_cost.set_index('eBKP-H Code')['Anmerkung']
    ).fillna('')

    # Entferne Position-Spalte (wird nicht mehr benötigt)
    edited_df = edited_df.drop(columns=['Position'])
else:
    # Keine Zeilenänderungen - nur Werte übertragen
    edited_df['Menge'] = edited_df_display['Menge'].values
    edited_df['Kennwert'] = edited_df_display['Kennwert'].values
    edited_df['Pauschalpreis CHF'] = edited_df_display['Pauschalpreis CHF'].values

# Berechne Beträge NEU nach Bearbeitung
for idx in edited_df.index:
    pauschalpreis = edited_df.loc[idx, 'Pauschalpreis CHF']

    if pauschalpreis > 0:
        edited_df.loc[idx, 'Betrag CHF'] = pauschalpreis
    else:
        menge = edited_df.loc[idx, 'Menge']
        kennwert = edited_df.loc[idx, 'Kennwert']
        einheit = edited_df.loc[idx, 'Einheit']

        if '%' in str(einheit):
            edited_df.loc[idx, 'Betrag CHF'] = 0.0
        else:
            edited_df.loc[idx, 'Betrag CHF'] = menge * kennwert

# Speichere bearbeitete Daten zurück in Session State
st.session_state.edited_cost_data = edited_df.copy()

st.divider()

# Kostenzusammenfassung
st.subheader("💰 Kostenzusammenfassung")

# Berechne Zwischensumme (ohne %-Positionen)
zwischensumme = edited_df[~edited_df['Einheit'].astype(str).str.contains('%', na=False)]['Betrag CHF'].sum()

# Berechne %-Positionen (V, Z, etc.) auf Zwischensumme
prozent_positionen = edited_df[edited_df['Einheit'].astype(str).str.contains('%', na=False)]
prozent_betrag = 0.0

for idx, row in prozent_positionen.iterrows():
    pauschalpreis = row['Pauschalpreis CHF']

    if pauschalpreis > 0:
        # Pauschalpreis verwenden
        betrag = pauschalpreis
    else:
        # Prozentsatz auf Zwischensumme anwenden
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
        help="Summe aller Positionen ohne prozentuale Zuschläge"
    )

with col2:
    st.metric(
        "💰 Gesamtkosten",
        format_currency(total_betrag),
        help="Gesamtsumme inkl. aller Zuschläge (V, W, Z, etc.)"
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
        df_with_costs[['eBKP-H Code', 'Beschreibung', 'Menge', 'Einheit', 'Kennwert', 'Pauschalpreis CHF', 'Betrag formatiert']],
        use_container_width=True,
        hide_index=True
    )

st.divider()

# Visualisierungen
st.subheader("📊 Kostenvisualisierung")

# Nur Positionen mit Betrag > 0 für Visualisierung
df_viz = edited_df[edited_df['Betrag CHF'] > 0].copy()

if len(df_viz) > 0:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Kostenverteilung nach Hauptgruppen")

        # Extrahiere Hauptgruppe (erster Buchstabe des eBKP-H Codes)
        df_viz['Hauptgruppe'] = df_viz['eBKP-H Code'].astype(str).str[0]

        # Gruppiere nach Hauptgruppe
        hauptgruppen_kosten = df_viz.groupby('Hauptgruppe')['Betrag CHF'].sum().reset_index()
        hauptgruppen_kosten = hauptgruppen_kosten.sort_values('Betrag CHF', ascending=False)

        # Erstelle Pie Chart mit plotly
        import plotly.express as px

        fig_pie = px.pie(
            hauptgruppen_kosten,
            values='Betrag CHF',
            names='Hauptgruppe',
            title='',
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.4  # Donut Chart
        )

        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Betrag: CHF %{value:,.2f}<br>Anteil: %{percent}<extra></extra>'
        )

        fig_pie.update_layout(
            showlegend=True,
            height=400,
            margin=dict(t=20, b=20, l=20, r=20)
        )

        st.plotly_chart(fig_pie, use_container_width=True)

        # Legende mit Beträgen
        st.caption("**Hauptgruppen-Übersicht:**")
        for _, row in hauptgruppen_kosten.iterrows():
            prozent = (row['Betrag CHF'] / hauptgruppen_kosten['Betrag CHF'].sum()) * 100
            st.caption(f"• **{row['Hauptgruppe']}**: {format_currency(row['Betrag CHF'])} ({prozent:.1f}%)")

    with col2:
        st.markdown("#### Top 10 teuerste Positionen")

        # Top 10 teuerste Positionen
        top_10 = df_viz.nlargest(10, 'Betrag CHF')[['eBKP-H Code', 'Beschreibung', 'Betrag CHF']].copy()

        # Kürze lange Beschreibungen für bessere Lesbarkeit
        top_10['Beschreibung_kurz'] = top_10['Beschreibung'].astype(str).str[:30] + '...'
        top_10['Label'] = top_10['eBKP-H Code'].astype(str) + ' - ' + top_10['Beschreibung_kurz']

        # Erstelle Bar Chart mit plotly
        fig_bar = px.bar(
            top_10,
            x='Betrag CHF',
            y='Label',
            orientation='h',
            title='',
            color='Betrag CHF',
            color_continuous_scale='Blues',
            text='Betrag CHF'
        )

        fig_bar.update_traces(
            texttemplate='CHF %{text:,.0f}',
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Betrag: CHF %{x:,.2f}<extra></extra>'
        )

        fig_bar.update_layout(
            showlegend=False,
            height=400,
            xaxis_title="Betrag (CHF)",
            yaxis_title="",
            yaxis={'categoryorder': 'total ascending'},
            margin=dict(t=20, b=20, l=20, r=20),
            coloraxis_showscale=False
        )

        st.plotly_chart(fig_bar, use_container_width=True)

        # Zusätzliche Info
        total_top10 = top_10['Betrag CHF'].sum()
        anteil = (total_top10 / zwischensumme * 100) if zwischensumme > 0 else 0
        st.caption(f"💡 Die Top 10 Positionen machen **{anteil:.1f}%** der Baukosten aus ({format_currency(total_top10)})")

else:
    st.info("ℹ️ Keine Kostendaten für Visualisierung vorhanden. Bitte tragen Sie Mengen ein oder geben Sie Pauschalpreise an.")

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
            worksheet.column_dimensions['G'].width = 15
            worksheet.column_dimensions['H'].width = 30

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
    config_info = get_state(CFG_COST_ESTIMATION_CONFIG)
    if config_info and not config_info.get('selected'):
        config_info = None

    # Lade Projektdaten aus Session State
    projekt_daten = get_state(DATA_PROJEKT_DATEN)

    pdf_buffer = generate_pdf(edited_df, zwischensumme, total_betrag, min_betrag, max_betrag, tolerance, config_info, projekt_daten)

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
st.caption("💡 Hinweis: Diese Kostenberechnung basiert auf Kennwerten und dient als Schätzung. Die tatsächlichen Kosten können abweichen. Das Programm übernimmt keine Haftung für die Genauigkeit der Berechnungen.")

# Footer
render_page_footer()